#!/usr/bin/env python3
"""retrofit-watch: ao fim do turno em que uma skill nossa trabalhou, pede ao Claude a retro dela.

Registrado em hooks/hooks.json:
  Stop                         -> retrofit_watch.py stop
  SessionStart (resume|fork)   -> retrofit_watch.py baseline
  SessionStart (startup)       -> retrofit_watch.py pending   (aviso de startup: retro adiada, modo autônomo)
Linha de comando: retrofit_watch.py queue [--done ID...]   (a fila das sessões headless)
                  retrofit_watch.py triage|held|hold|approve|discard ...   (modo autônomo, rw_auto.py)
                  retrofit_watch.py harvest|prepare|seal ...   (a loja do modo autônomo, rw_store.py)
                  retrofit_watch.py publish <id> <lote>   (a porta de publicação, rw_gate.py)

"Nossa" = skill do marketplace chewiesoft-marketplace (j0ruge/skills; retrofit modo full, o
argumento é o nome do PLUGIN) ou skill versionada em git num repo de dono conhecido (modo lean).
Terceiros, skills fora do git e as do Hermes ficam de fora.

"Kit" = produto nosso que não é skill, reconhecido pelo binário (padrão: `sdd`, o kit de
~/repos/sdd_agents). O binário resolvido no PATH aponta o repo; contam como trabalho do kit o
comando `/<kit>-*`, o subagente `<kit>-*` e o próprio binário no Bash. A lição vai para o
TODO.md do repo do kit (ou o do worktree ligado onde a missão do kit roda), não para o /retrofit-skill.

Controle por ambiente:
  RETROFIT_WATCH=off     desliga
  RETROFIT_WATCH=force   pede a retro mesmo em sessão desassistida (testes com claude -p)
Config opcional em ~/.claude/retrofit-watch.json: owners, include, exclude, deny_roots, kits,
unattended ("queue", o padrão, ou "off"). O modo autônomo (rw_auto.py) lê estas chaves:
  mode              "manual" (o padrão), "auto" ou "auto-dry" (faz tudo e para na porta, sem push)
  manual            plugins ou skills que ficam sempre no modo manual
  store             o clone de trabalho da loja; sem ela, o "auto" não vale (motivo sem-loja)
  auto_limits       os tetos, padrão {"per_skill": 2, "per_session": 3}
  harvest_roots     onde a colheita procura repos git, padrão ["~/repos"], profundidade 2
  private_sources   denylists locais da colheita, lidas e nunca copiadas para repo
O fluxo do modo autônomo está em references/modo-autonomo.md. A porta extrai um tar com o filtro
"data" do tarfile: ela precisa do Python 3.12, ou de uma versão com esse filtro (PEP 706).

Sessão desassistida (claude -p, fase do sdd run): nada volta para a sessão; com atrito, grava uma
linha em <data>/queue.jsonl (fora de qualquer repo) para a retro numa sessão com o humano. O
`"entrypoint":"cli"` do transcript vence o ambiente: com ele, a retro vem ao vivo, não vai para a fila.
Estado em ${CLAUDE_PLUGIN_DATA}/sessions/<session_id>.json (offset do transcript e contadores).
Sem CLAUDE_PLUGIN_DATA (o `queue` rodado à mão), <data> é a única ~/.claude/plugins/data/retrofit-watch-*;
sem ela, ou com mais de uma, o `queue` sai 1 em vez de responder uma fila vazia.
Nunca grava texto do assistente. Qualquer erro interno vai para <data>/errors.log e sai com 0.
Só biblioteca padrão. Roda em Linux, macOS e Windows (lá o `python3` do PATH, sem fcntl).
"""
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt

MARKETPLACE = "chewiesoft-marketplace"
DEFAULT_OWNERS = ("j0ruge", "chewiesoft")
ALWAYS_EXCLUDED = {"retrofit-skill", "retrofit-watch", "skill-quality-audit"}
DEFAULT_KITS = ("sdd",)
MAX_REVIEWS = 2
MAX_SKILL_MESSAGES = 64
MAX_SKILL_CALL_IDS = 1024
MAX_LEGACY_RECORD_BYTES = 2 * 1024 * 1024
FIRST_REVIEW_WORK = 5
SECOND_REVIEW_FRICTION = 2
STATE_TTL_SECONDS = 14 * 24 * 3600
QUEUE_FILE = "queue.jsonl"
GIT_TIMEOUT = 2
LOCK_POLL = 0.5
# O transcript grava em cada registro de onde a sessão veio: `cli` na interativa, `sdk-cli` no
# `claude -p` (medido em 2026-11-02: 69 sessões com retro ao vivo e 12 entradas interativas da fila
# com `cli`, as 26 entradas de fase do `sdd run` com `sdk-cli`).
ENTRYPOINT_RE = re.compile(rb'"entrypoint":\s*"([^"]+)"')

BASE_PREFIX = "Base directory for this skill: "
INTERRUPT = "[Request interrupted by user"
MARKERS = (BASE_PREFIX.encode(), b'"name":"Skill"', b"<command-name>")
NON_WORK_TOOLS = {"Skill", "AskUserQuestion", "TodoWrite", "ExitPlanMode", "EnterPlanMode", "ToolSearch",
                  "TaskCreate", "TaskUpdate", "TaskList", "TaskGet"}
WAIT_TOOLS = {"AskUserQuestion", "ExitPlanMode"}
CMD_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
CORRECTION_START = re.compile(r"^\s*(n[aã]o\b|errado|na verdade|pare\b|wrong|actually|stop\b)", re.I)
CORRECTION_ANY = re.compile(r"\b(de novo|again)\b", re.I)
# O Claude narrando que a realidade não bate com a instrução: é o pitfall contornado sem erro de
# ferramenta (E2E de 2026-09-30: path errado na skill, achado por `find`, zero is_error).
DEVIATION_RE = re.compile(
    r"doesn['’]t exist|does not exist|not in the expected|not where|no such file|instead of"
    r"|n[aã]o existe|n[aã]o encontrei|em vez de|ao inv[eé]s de|no lugar de|n[aã]o est[aá] onde", re.I)
NO_LESSONS_RE = re.compile(r"sem li[cç][oõ]es novas|no new lessons", re.I)
# Modo autônomo (rw_auto.py; spec 5.2 e 5.10). O padrão é `manual`: quem instala a loja pública
# não recebe o modo autônomo.
AUTO_MODES = ("manual", "auto", "auto-dry")
DEFAULT_AUTO_LIMITS = {"per_skill": 2, "per_session": 3}
DEFAULT_HARVEST_ROOTS = ("~/repos",)


class Context:
    def __init__(self, home=None, data_dir=None):
        self.home = Path(os.path.realpath(home or os.environ.get("HOME") or Path.home()))
        data = data_dir or os.environ.get("CLAUDE_PLUGIN_DATA")
        self.data_candidates = []
        if not data:
            # Fora do hook (o `queue` à mão) não há CLAUDE_PLUGIN_DATA. O Claude Code cria a pasta como
            # `<plugin>-<loja>`; o nome sem a loja nunca existiu, e lê-lo respondia `[]` com 38 retros
            # na fila (2026-11-02). Ambíguo ou ausente, o `queue` recusa (cmd_queue).
            base = self.home / ".claude/plugins/data"
            self.data_candidates = sorted(base.glob("retrofit-watch-*"))
            data = self.data_candidates[0] if len(self.data_candidates) == 1 else base / "retrofit-watch"
        self.data_dir = Path(data)
        self.config = self._load_config()
        self._installed = None

    def _load_config(self):
        try:
            cfg = json.loads((self.home / ".claude/retrofit-watch.json").read_text(encoding="utf-8"))
            return cfg if isinstance(cfg, dict) else {}
        except (OSError, ValueError):
            return {}

    @property
    def owners(self):
        return {o.lower() for o in self.config.get("owners", DEFAULT_OWNERS)}

    @property
    def excluded(self):
        return ALWAYS_EXCLUDED | set(self.config.get("exclude", []))

    @property
    def kits(self):
        return tuple(k for k in self.config.get("kits", DEFAULT_KITS) if isinstance(k, str) and k)

    @property
    def deny_roots(self):
        roots = [self.home / ".agents", self.home / ".hermes"]
        roots += [Path(os.path.expanduser(r)) for r in self.config.get("deny_roots", [])]
        return [_slashed(os.path.realpath(r)) for r in roots]

    # --- modo autônomo (rw_auto.py) ------------------------------------------------------------
    # Todo `~` destas chaves resolve pelo `self.home`, nunca pelo HOME real: os testes montam um
    # HOME fixture, e o código do modo autônomo não pode ler o diretório de verdade.

    def _home_path(self, raw):
        raw = str(raw)
        if raw == "~":
            return self.home
        if raw.startswith("~/") or raw.startswith("~" + os.sep):
            return self.home / raw[2:]
        return Path(raw)

    def _paths(self, key, default):
        value = self.config.get(key, default)
        if not isinstance(value, list):
            value = default
        return [self._home_path(p) for p in value if isinstance(p, str) and p]

    @property
    def mode(self):
        """`manual` (o padrão), `auto` ou `auto-dry`. Qualquer outro valor é `manual`."""
        mode = self.config.get("mode", "manual")
        return mode if mode in AUTO_MODES else "manual"

    @property
    def manual(self):
        """Plugins ou skills que ficam sempre no modo manual."""
        value = self.config.get("manual", [])
        return {m for m in value if isinstance(m, str)} if isinstance(value, list) else set()

    @property
    def auto_limits(self):
        limits = dict(DEFAULT_AUTO_LIMITS)
        cfg = self.config.get("auto_limits")
        if isinstance(cfg, dict):
            for key in limits:
                if isinstance(cfg.get(key), int) and not isinstance(cfg.get(key), bool):
                    limits[key] = cfg[key]
        return limits

    @property
    def harvest_roots(self):
        return self._paths("harvest_roots", list(DEFAULT_HARVEST_ROOTS))

    @property
    def private_sources(self):
        return self._paths("private_sources", [])

    @property
    def store(self):
        """O clone de trabalho da loja: um diretório com `.git` cujo marketplace.json tem o nome da
        loja. Senão, None. Lê arquivo e não chama o git: o hook tem 10 s."""
        raw = self.config.get("store")
        if not isinstance(raw, str) or not raw:
            return None
        path = self._home_path(raw)
        try:
            if not (path / ".git").exists():
                return None
            manifest = json.loads((path / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
            return path if isinstance(manifest, dict) and manifest.get("name") == MARKETPLACE else None
        except (OSError, ValueError):
            return None

    def installed_marketplaces(self, plugin):
        if self._installed is None:
            self._installed = {}
            try:
                data = json.loads((self.home / ".claude/plugins/installed_plugins.json").read_text())
                for key in data.get("plugins", {}):
                    name, _, mkt = key.partition("@")
                    self._installed.setdefault(name, set()).add(mkt)
            except (OSError, ValueError, AttributeError):
                pass
        return self._installed.get(plugin, set())


# --- classificação -----------------------------------------------------------------------------

def _slashed(path):
    """A classificação compara paths com `/`; no Windows o realpath devolve `C:\\Users\\...`."""
    return path.replace(os.sep, "/")


def _git(args, cwd):
    try:
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              timeout=GIT_TIMEOUT)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _toplevel(cwd):
    """Raiz do repo no formato do SO: o git do Windows responde `C:/x`, e o realpath com que ela é
    comparada (o TODO.md do kit) vem `C:\\x`."""
    top = _git(["rev-parse", "--show-toplevel"], cwd)
    return os.path.normpath(top) if top else None


def _common_dir(top):
    """O `.git` comum: o checkout principal e cada worktree ligado do mesmo repo respondem igual.
    Relativo ao `top` quando é o principal; nunca `--path-format`, que git velho ecoa de volta."""
    out = _git(["rev-parse", "--git-common-dir"], top)
    return os.path.normcase(os.path.realpath(os.path.join(top, out))) if out else None


def kit_worktrees(repo):
    """Os outros worktrees do repo do kit, que existem no disco. A missão do kit roda num deles, e
    a sessão pode ter o cwd no checkout principal (lote 6 do sdd, 2026-10-08): o cwd não diz qual."""
    out = _git(["worktree", "list", "--porcelain"], repo) or ""
    tops = [os.path.normpath(line[len("worktree "):]) for line in out.splitlines() if line.startswith("worktree ")]
    here = os.path.realpath(repo)
    return [t for t in tops if os.path.isdir(t) and os.path.realpath(t) != here]


def _full(plugin, skill, ctx):
    if plugin in ctx.excluded or skill in ctx.excluded:
        return None
    label = plugin if skill in (plugin, None) else f"{plugin} ({skill})"
    # `skills`: as skills do plugin que a sessão carregou (vazia no plugin só de comandos); a lista
    # `manual` da config vale por plugin ou por skill (rw_auto.why_manual).
    return {"key": f"full:{plugin}", "mode": "full", "arg": plugin, "label": label, "repo": None,
            "skills": [skill] if skill else []}


def _lean(name, repo):
    return {"key": f"lean:{repo}:{name}", "mode": "lean", "arg": name, "label": name, "repo": repo}


def _owned(top, ctx):
    """O `origin` do repo é de um dono nosso?"""
    origin = _git(["remote", "get-url", "origin"], top) or ""
    owner = re.search(r"[:/]([^/:]+)/[^/]+?(?:\.git)?/?$", origin)
    return bool(owner) and owner.group(1).lower() in ctx.owners


def kit_of(name, ctx):
    """`sdd`, `sdd-plan` e `sdd-planner` são do kit `sdd`; o resto não é de kit nenhum."""
    for kit in ctx.kits:
        if name == kit or name.startswith(kit + "-"):
            return kit
    return None


def classify_kit(kit, ctx):
    """Repo do kit pelo binário no PATH (o symlink de ~/.hermes/bin leva ao clone). None = não vigiar."""
    if kit in ctx.excluded:
        return None
    exe = shutil.which(kit)
    if not exe:
        return None
    top = _toplevel(os.path.dirname(os.path.realpath(exe)))
    if not top or not _owned(top, ctx):
        return None
    return {"key": f"kit:{top}", "mode": "kit", "arg": kit, "label": f"kit {kit}", "repo": top}


def classify_plugin(plugin, ctx):
    """Classifica pelo nome `plugin:x` (serve para plugin só de comandos, que não grava path)."""
    if MARKETPLACE in ctx.installed_marketplaces(plugin):
        return _full(plugin, None, ctx)
    return None


def classify_path(path, ctx):
    """Dono da skill a partir do path da linha 'Base directory'. None = não vigiar."""
    real = _slashed(os.path.realpath(path))
    name = os.path.basename(real.rstrip("/"))
    if name in ctx.config.get("include", []):
        top = _toplevel(real)
        return _lean(name, top)
    if name in ctx.excluded:
        return None
    home = _slashed(str(ctx.home))
    cached = re.match(re.escape(home) + r"/\.claude/plugins/(cache|marketplaces)/([^/]+)/(.+)$", real)
    if cached:
        kind, marketplace, rest = cached.groups()
        if marketplace != MARKETPLACE:
            return None
        if kind == "cache":
            plugin = rest.split("/")[0]
        else:
            found = re.match(r"plugins/([^/]+)/", rest)
            plugin = found.group(1) if found else None
        return _full(plugin, name, ctx) if plugin else None
    if any(real == root or real.startswith(root + "/") for root in ctx.deny_roots) or "/.agents/skills/" in real + "/":
        return None
    top = _toplevel(real)
    if not top:
        return None
    in_plugin = re.search(r"/plugins/([^/]+)/(?:skills|commands)/", real + "/")
    if in_plugin:
        try:
            manifest = json.loads(Path(top, ".claude-plugin/marketplace.json").read_text())
            if manifest.get("name") == MARKETPLACE:
                return _full(in_plugin.group(1), name, ctx)
        except (OSError, ValueError):
            pass
    try:
        locked = json.loads(Path(top, "skills-lock.json").read_text()).get("skills", {})
        if name in locked:
            return None
    except (OSError, ValueError, AttributeError):
        pass
    rel = os.path.relpath(os.path.join(real, "SKILL.md"), top)
    if _git(["ls-files", "--error-unmatch", "--", rel], top) is None:
        return None
    if not _owned(top, ctx):
        return None
    return _lean(name, top)


# --- estado ------------------------------------------------------------------------------------

def _lock(path, timeout=None):
    """Abre `path` e espera a trava exclusiva: flock no Unix; no Windows, msvcrt sobre o 1º byte (pode
    passar do fim do arquivo vazio). O LK_LOCK desiste em ~10 s com OSError, que vai ao errors.log.

    Com `timeout` (segundos), tenta sem bloquear a cada LOCK_POLL e levanta OSError no prazo; `timeout=0`
    tenta uma vez só."""
    fh = open(path, "a")
    if timeout is None:
        if fcntl:
            fcntl.flock(fh, fcntl.LOCK_EX)
        else:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        return fh
    deadline = time.monotonic() + timeout
    while True:
        try:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return fh
        except OSError:
            left = deadline - time.monotonic()
            if left <= 0:
                fh.close()
                raise
            time.sleep(min(LOCK_POLL, left))


def _unlock(fh):
    try:
        if fcntl:
            fcntl.flock(fh, fcntl.LOCK_UN)
        else:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        fh.close()


class State:
    def __init__(self, ctx, session_id):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
        self.dir = ctx.data_dir / "sessions"
        self.path = self.dir / f"{safe}.json"
        self.lock_path = self.dir / f"{safe}.lock"
        self.data = None
        self.is_new = False

    def __enter__(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = _lock(self.lock_path)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data, self.is_new = None, True
        if not isinstance(self.data, dict):
            self.data, self.is_new = None, True
        if self.data is None:
            self.data = {"created": time.time()}
        self.legacy = "skill_calls" not in self.data and self.data.get("offset", 0) > 0
        for key, default in (("offset", 0), ("skills", {}), ("current", None), ("classified", {}),
                             ("pending", []), ("done", []), ("current_origin", None),
                             ("skill_message", None), ("skill_calls", {}), ("retired_skill_calls", []),
                             ("skill_correlation_lost", False), ("pending_slash", None)):
            self.data.setdefault(key, default)
        if not isinstance(self.data["retired_skill_calls"], list):
            self.data["retired_skill_calls"] = []
        for key in ("uncorrelated_skill_calls", "overflow_skill_calls"):
            if not isinstance(self.data.get(key), dict):
                self.data[key] = {}
        origin = self.data["current_origin"]
        if (not isinstance(origin, list) or len(origin) != 2
                or not all(map(Scanner._transcript_id, origin))):
            self.data["current_origin"] = origin = None
        self.data.setdefault("current_call", origin[1] if origin else None)
        if not isinstance(self.data.get("slash_prior_calls"), list):
            # Sem a ordem gravada, não presumir que uma chamada pendente é posterior ao slash.
            self.data["slash_prior_calls"] = list(self.data["skill_calls"]) if self.data["pending_slash"] else []
        if "attribution_closed" not in self.data:
            # Na 0.4.0, caminho sem dono encerrava a atribuição, mas kit sem dono não.
            self.data["attribution_closed"] = self.data["current"] is None and (
                bool(self.data["skills"]) or any(info is None and not path.startswith("kit:")
                                                 for path, info in self.data["classified"].items()))
        if "skill_message_order" not in self.data:
            messages = (self.data["skill_message"], *self.data["skill_calls"].values())
            self.data["skill_message_order"] = list(dict.fromkeys(m for m in messages if m))
        if "skill_call_history" not in self.data:
            calls = self.data["skill_calls"]
            # Estados intermediários não registravam a origem dos IDs consumidos ou ambíguos.
            history = {call: [] for call, message in calls.items() if message is False}
            for call in history:
                del calls[call]
            active = self.data["skill_message"]
            for call in self.data.pop("failed_skill_calls", []):
                history[call] = [active] if active else []
            self.data["skill_call_history"] = history
        return self

    def save(self):
        fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=".tmp-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh)
        os.replace(tmp, self.path)
        if self.is_new:
            self._cleanup()

    def _cleanup(self):
        cutoff = time.time() - STATE_TTL_SECONDS
        for old in self.dir.glob("*.json"):
            try:
                if old.stat().st_mtime < cutoff:
                    old.unlink()
                    old.with_suffix(".lock").unlink(missing_ok=True)
            except OSError:
                pass

    def __exit__(self, *exc):
        _unlock(self._lock)
        return False


# --- transcript --------------------------------------------------------------------------------

def read_delta(path, offset, *, rewind=True):
    """Bytes novos do transcript até a última linha completa. Devolve (bytes, novo_offset)."""
    size = os.path.getsize(path)
    if rewind and offset > size:
        offset = 0
    with open(path, "rb") as fh:
        fh.seek(offset)
        data = fh.read()
    cut = data.rfind(b"\n")
    if cut < 0:
        return b"", offset
    return data[:cut + 1], offset + cut + 1


def end_offset(path):
    try:
        return read_delta(path, 0)[1]
    except OSError:
        return 0


class Scanner:
    _legacy_replay = False

    def __init__(self, state, ctx):
        self.st = state
        self.ctx = ctx
        self.last_tool = None
        # Verdadeiro enquanto um pedido autônomo está aberto: o próprio fluxo não conta como
        # trabalho nem atrito de skill nenhuma (spec 5.10, D13). Quem decide é o cmd_stop.
        self.silent = False
        self._bound_skill_correlation()

    def _clear_skill_correlation(self):
        self.st["skill_calls"].clear()
        self.st["skill_message_order"].clear()
        self.st["skill_call_history"].clear()
        self.st["retired_skill_calls"].clear()

    def _prune_skill_correlation(self, confirmed=None):
        calls = self.st["skill_calls"]
        order = self.st["skill_message_order"]
        history = self.st["skill_call_history"]
        previous = self.st["skill_message"]
        advanced = confirmed is not None and confirmed != previous
        if advanced:
            cutoff = order.index(confirmed)
            older = set(order[:cutoff])
            retired = self.st["retired_skill_calls"]
            retired.extend(call for call, message in calls.items() if message in older)
            retired.extend(call for call, owners in history.items()
                           if owners and all(owner in older for owner in owners))
            self.st["retired_skill_calls"] = retired[-MAX_SKILL_CALL_IDS:]
            del order[:cutoff]
            self.st["skill_message"] = confirmed
        # Uma posição sem vínculo só interessa à carga ativa ou a uma disputa com pendência posterior.
        pending = set(calls.values())
        while order and order[-1] != self.st["skill_message"] and order[-1] not in pending:
            order.pop()
        live = set(order)
        if advanced:
            self.st["skill_calls"] = {call: message for call, message in calls.items() if message in live}
        for call, owners in list(history.items()):
            retained = [message for message in owners if message in live]
            # Um dono retido não resolve a colisão com uma chamada sem origem.
            if (not owners or owners[0] is None) and (retained or not (advanced and previous)):
                history[call] = [None, *retained] if retained else []
            elif retained:
                history[call] = retained
            else:
                del history[call]

    def _bound_skill_correlation(self):
        if (len(self.st["skill_message_order"]) > MAX_SKILL_MESSAGES
                or len(self.st["skill_calls"]) + len(self.st["skill_call_history"]) > MAX_SKILL_CALL_IDS):
            # Preservar a prova de reuso sem consumir a capacidade reservada às chamadas novas.
            retired = filter(self._transcript_id, self.st["retired_skill_calls"])
            retained = (*self.st["skill_calls"], *self.st["skill_call_history"], *retired)
            self.st["overflow_skill_calls"] = dict.fromkeys(retained[:2 * MAX_SKILL_CALL_IDS + 1])
            self._clear_skill_correlation()
            self.st["current_origin"] = None
            self.st["skill_correlation_lost"] = True

    def _watch(self, info, origin=None, *, call_id=None, preserve_slash=False):
        if origin:
            self._prune_skill_correlation(origin[0])
        if info is None:
            current = self.st["current_origin"]
            # O caminho ainda pode excluir a própria chamada reconhecida pelo nome.
            if origin and current and origin[0] == current[0] and origin[1] != current[1]:
                return
            if origin is None:
                self._clear_skill_correlation()
            self.st["current"] = None
            self.st["current_origin"] = None
            self.st["current_call"] = None
            self.st["attribution_closed"] = True
            if not preserve_slash:
                self.st["pending_slash"] = None
                self.st["slash_prior_calls"] = []
            return
        key = info["key"]
        entry = self.st["skills"].setdefault(key, dict(info, reviews=0, work=0, friction=0))
        if "skills" in info:
            # Lista nova, nunca a do cache de classificação. Estado antigo não tem a chave.
            have = list(entry.get("skills") or [])
            entry["skills"] = have + [s for s in info["skills"] if s not in have]
        if key in self.st["done"]:
            entry["reviews"] = MAX_REVIEWS
        self.st["current"] = key
        self.st["current_origin"] = origin
        self.st["current_call"] = call_id
        self.st["attribution_closed"] = False

    def _bump(self, field):
        if self.silent:
            return
        entry = self.st["skills"].get(self.st.get("current") or "")
        if entry is not None:
            entry[field] += 1

    def _retrofit_ran(self, args):
        target = (args or "").strip().split()
        if not target:
            return
        done = self.st["done"]
        for key, entry in self.st["skills"].items():
            if entry["arg"] == target[0]:
                entry["reviews"] = MAX_REVIEWS
                if key not in done:
                    done.append(key)
        if f"full:{target[0]}" not in done:
            done.append(f"full:{target[0]}")

    def kit(self, kit):
        cache = self.st["classified"]
        if f"kit:{kit}" not in cache:
            cache[f"kit:{kit}"] = classify_kit(kit, self.ctx)
        info = cache[f"kit:{kit}"]
        if info is not None:
            self._watch(info)

    def kit_todo_written(self, path):
        """O registro no TODO.md do kit é o retrofit dele: a retro daquele kit não volta. Vale o
        TODO.md da raiz de qualquer worktree do mesmo repo, onde a missão do kit escreve."""
        real = os.path.realpath(path or "")
        if os.path.basename(real) != "TODO.md":
            return
        top = None
        for key, entry in self.st["skills"].items():
            if entry["mode"] != "kit":
                continue
            if real != os.path.join(entry["repo"], "TODO.md"):
                if top is None:
                    top = _toplevel(os.path.dirname(real)) or ""
                if (not top or real != os.path.join(top, "TODO.md")
                        or _common_dir(top) != _common_dir(entry["repo"])):
                    continue
            entry["reviews"] = MAX_REVIEWS
            if key not in self.st["done"]:
                self.st["done"].append(key)

    def tool_use(self, name, tool_input):
        """Agent `<kit>-*` e o binário do kit no Bash passam a vigiar o kit antes de contar."""
        if name == "Agent":
            kit = kit_of(str(tool_input.get("subagent_type", "")), self.ctx)
            if kit:
                self.kit(kit)
        elif name == "Bash":
            command = str(tool_input.get("command", ""))
            for kit in self.ctx.kits:
                if re.search(rf"(?:^|[;&|(])\s*(?:\S*/)?{re.escape(kit)}\s", command + " "):
                    self.kit(kit)
                    break
        elif name in ("Edit", "Write"):
            self.kit_todo_written(tool_input.get("file_path"))

    def invocation(self, name, args, origin=None, *, call_id=None):
        plugin = name.split(":", 1)[0]
        if plugin == "retrofit-skill":
            self._retrofit_ran(args)
            self._watch(None)
        elif ":" not in name and kit_of(name, self.ctx):
            self.kit(kit_of(name, self.ctx))
        elif ":" in name:
            info = classify_plugin(plugin, self.ctx)
            if info is not None:
                self._watch(info, origin, call_id=call_id)
            elif self.ctx.installed_marketplaces(plugin):
                self._watch(None, origin)

    @staticmethod
    def _transcript_id(value):
        if isinstance(value, str) and value and not any(c.isspace() for c in value):
            return value
        return None

    def _skill_origin(self, message_id, call_id):
        if self.st["skill_correlation_lost"]:
            return None
        message_id = self._transcript_id(message_id)
        if self.st["skill_message"] is None:
            # Já vimos uma chamada, ainda que nenhuma carga tenha sido reconhecida.
            self.st["skill_message"] = ""
        if call_id is None:
            return None
        if call_id in self.st["slash_prior_calls"]:
            self.st["slash_prior_calls"].remove(call_id)
        retired = self.st["retired_skill_calls"]
        if call_id in retired:
            retired.remove(call_id)
        messages = self.st["skill_message_order"]
        if message_id and message_id not in messages:
            messages.append(message_id)
        calls = self.st["skill_calls"]
        history = self.st["skill_call_history"]
        if call_id in calls or call_id in history:
            # A marca sem origem é [] sozinha e None antes dos donos durante a disputa.
            unowned = call_id in calls and calls[call_id] is None
            owners = history.get(call_id)
            known = dict.fromkeys((*(owners or ()), calls.pop(call_id, None), message_id))
            retained = [owner for owner in known if owner]
            if message_id is None or unowned or owners == [] or (owners and owners[0] is None):
                retained.insert(0, None)
            history[call_id] = retained
            self._prune_skill_correlation()
            return None
        calls[call_id] = message_id
        return [message_id, call_id] if message_id else None

    def skill_path(self, path, source):
        cache = self.st["classified"]
        if path not in cache:
            cache[path] = classify_path(path, self.ctx)
        info = cache[path]
        source = self._transcript_id(source)
        if source is not None and source in self.st["retired_skill_calls"]:
            return
        # Um metadado de chamada descartada ou ambígua não pode reabrir a atribuição.
        # Uma externa sem vínculo continua encerrando-a, inclusive no estado legado.
        conservative = self.st["attribution_closed"] or self.st["skill_correlation_lost"]
        unlinked = False if source and (self.st["skill_message"] is not None or conservative) else None
        calls = self.st["skill_calls"]
        message_id = calls.get(source, unlinked)
        if message_id is False and info is not None:
            return
        # Sem vínculo não há prova de nova carga após o encerramento. O slash digitado
        # é explícito e pode iniciar outra atribuição, mas só para a skill que ele nomeia.
        if source is None and info is not None and conservative:
            plugin, _, name = (self.st["pending_slash"] or "").rpartition(":")
            if name not in info.get("skills", [info["arg"]]) or (plugin and plugin != info["arg"]):
                return
        # O replay não pode supor que a intenção sobreviveu com a regra nova.
        if source is None and (info is not None or self._legacy_replay):
            self.st["pending_slash"] = None
            self.st["slash_prior_calls"] = []
        call_id = source if source in calls else None
        preserve_slash = call_id is None or call_id in self.st["slash_prior_calls"]
        self._watch(info, [message_id, source] if message_id else None, call_id=call_id,
                    preserve_slash=preserve_slash)
        self._retire_skill_call(source)
        return True

    def _retire_skill_call(self, call_id):
        calls = self.st["skill_calls"]
        if call_id in calls:
            message = calls.pop(call_id)
            self.st["skill_call_history"][call_id] = [message] if message else []
            self._prune_skill_correlation()

    def user_text(self, text):
        if text.startswith(INTERRUPT):
            self._bump("friction")
        elif not text.startswith("<") and (CORRECTION_START.search(text) or CORRECTION_ANY.search(text)):
            self._bump("friction")

    def entry(self, d):
        kind = d.get("type")
        msg = d.get("message") if isinstance(d.get("message"), dict) else {}
        content = msg.get("content")
        if kind == "assistant" and isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                text = block.get("text")
                if block.get("type") == "text" and isinstance(text, str) and DEVIATION_RE.search(text):
                    self._bump("friction")
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                self.last_tool = name
                tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
                if name == "Skill":
                    call_id = self._transcript_id(block.get("id"))
                    origin = self._skill_origin(msg.get("id"), call_id)
                    if self.st["skill_correlation_lost"]:
                        # Sem janela, o registro serve só para o ID direto, sem expulsar IDs já vistos.
                        seen = self.st["uncorrelated_skill_calls"]
                        new_id = (call_id is not None and call_id not in seen
                                  and len(seen) < MAX_SKILL_CALL_IDS)
                        if new_id:
                            seen[call_id] = True
                        unique = (new_id and call_id != self.st["current_call"]
                                  and call_id not in self.st["overflow_skill_calls"])
                    else:
                        unique = call_id in self.st["skill_calls"]
                    if not unique:
                        if call_id == self.st["current_call"]:
                            self.st["current_call"] = None
                        call_id = None
                    self.invocation(str(tool_input.get("skill", "")), tool_input.get("args", ""), origin,
                                    call_id=call_id)
                    self._bound_skill_correlation()
                elif name not in NON_WORK_TOOLS:
                    self.tool_use(name, tool_input)
                    self._bump("work")
        elif kind == "user":
            if d.get("isMeta"):
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        text = block.get("text")
                        if block.get("type") == "text" and isinstance(text, str) and text.startswith(BASE_PREFIX):
                            self.skill_path(text[len(BASE_PREFIX):].split("\n", 1)[0].strip(),
                                            d.get("sourceToolUseID"))
                return
            if isinstance(content, str):
                command = CMD_RE.search(content)
                if command:
                    args = ARGS_RE.search(content)
                    self.st["pending_slash"] = command.group(1)
                    self.st["slash_prior_calls"] = list(self.st["skill_calls"])
                    self.invocation(command.group(1), args.group(1) if args else "")
                else:
                    self.user_text(content)
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result" and block.get("is_error"):
                        call_id = self._transcript_id(block.get("tool_use_id"))
                        self._retire_skill_call(call_id)
                        if call_id is not None and call_id == self.st["current_call"]:
                            self.st["current"] = None
                            self.st["current_origin"] = None
                            self.st["current_call"] = None
                            self.st["attribution_closed"] = True
                        self._bump("friction")
                    elif block.get("type") == "text" and isinstance(block.get("text"), str):
                        self.user_text(block["text"])

    def scan(self, chunk):
        for raw in chunk.split(b"\n"):
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            if isinstance(entry, dict):
                self.entry(entry)


def recover_legacy_correlation(path, st, ctx):
    remaining = st["offset"]
    was_closed = st["attribution_closed"]
    st["attribution_closed"] = was_closed or st["current"] is None
    replay = dict(st, skills={}, current=None, classified=st["classified"].copy(), done=[],
                  retired_skill_calls=[], slash_prior_calls=[], uncorrelated_skill_calls={},
                  skill_calls={}, skill_message_order=[], skill_call_history={}, attribution_closed=False)
    owner = None
    ambiguous = False
    common_retired = set()
    unseen_cached_paths = set(st["classified"])
    proved_owner = False

    class ReplayScanner(Scanner):
        _legacy_replay = True
        first_cached_path = False

        def _skill_origin(self, message_id, call_id):
            # Reuso no prefixo invalida a prova antiga, mesmo se o replay aposentar o ID de novo.
            common_retired.discard(call_id)
            return super()._skill_origin(message_id, call_id)

        def skill_path(self, path, source):
            nonlocal ambiguous, proved_owner
            info = st["classified"].get(path)
            compatible = isinstance(info, dict) and info.get("key") == st["current"]
            # A 0.4.0 podia aceitar este metadado mesmo se o replay rejeitar seu ID.
            if compatible:
                proved_owner = False
            self.first_cached_path = path in unseen_cached_paths
            unseen_cached_paths.discard(path)
            if not super().skill_path(path, source) and compatible:
                # Um dono possível sem origem aceita invalida a prova de antiguidade.
                ambiguous = True
                common_retired.clear()
            self.first_cached_path = False

        def _watch(self, info, origin=None, **kwargs):
            nonlocal owner, ambiguous, proved_owner
            super()._watch(info, origin, **kwargs)
            if info is not None and info["key"] == st["current"]:
                candidate = (tuple(origin or ()), self.st["current_call"])
                retired = self.st["retired_skill_calls"] if origin else ()
                if owner is None and not ambiguous:
                    common_retired.update(retired)
                elif owner != candidate:
                    ambiguous = True
                    proved_owner = False
                    common_retired.intersection_update(retired)
                # Um caminho exclusivo e já salvo comprova que este metadado foi lido.
                if self.first_cached_path and origin:
                    proved_owner = True
                owner = candidate

    scanner = ReplayScanner(replay, ctx)
    scanner.silent = True
    try:
        with open(path, "rb") as fh:
            if os.fstat(fh.fileno()).st_size < remaining:
                st["legacy_prefix_truncated"] = True
                return
            while remaining:
                limit = min(remaining, MAX_LEGACY_RECORD_BYTES)
                line = fh.readline(limit)
                if not line.endswith(b"\n"):
                    if len(line) < limit:
                        st["legacy_prefix_truncated"] = True
                    # Registro sem quebra dentro do limite: não importar reconstrução parcial.
                    return
                remaining -= len(line)
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    return
                if not isinstance(entry, dict):
                    return
                scanner.entry(entry)
    except OSError:
        return
    cache_matches = replay["classified"] == st["classified"]
    # Um Stop ativo na 0.4.0 podia avançar o offset sem observar a carga mais recente.
    if ambiguous and not (proved_owner and cache_matches):
        st["retired_skill_calls"] = [call for call in replay["retired_skill_calls"] if call in common_retired]
        return
    # A leitura serve para recuperar vínculos, sem substituir a atribuição gravada pela 0.4.0.
    if replay["current"] != st["current"] or (was_closed and not replay["attribution_closed"]):
        return
    # O cache legado confirma se a origem reconstruída corresponde à carga que foi observada.
    if cache_matches:
        for key in ("current_origin", "current_call", "pending_slash", "slash_prior_calls"):
            st[key] = replay[key]
    for key in ("attribution_closed", "skill_message", "skill_calls", "skill_message_order",
                "skill_call_history", "retired_skill_calls", "skill_correlation_lost", "uncorrelated_skill_calls",
                "overflow_skill_calls"):
        st[key] = replay[key]


# --- decisão e mensagem ------------------------------------------------------------------------

def eligible(entry):
    if entry["reviews"] >= MAX_REVIEWS or entry["work"] < 1:
        return False
    if entry["reviews"] == 0:
        return entry["friction"] >= 1 or entry["work"] >= FIRST_REVIEW_WORK
    return entry["friction"] >= SECOND_REVIEW_FRICTION


def waiting_for_user(payload, last_tool):
    last = (payload.get("last_assistant_message") or "").rstrip()
    return last.endswith("?") or last_tool in WAIT_TOOLS or payload.get("permission_mode") == "plan"


def describe(entry):
    cmd = f"`/retrofit-skill:retrofit-skill {entry['arg']}`"
    if entry["mode"] == "kit":
        todo = os.path.join(entry["repo"], "TODO.md")
        text = (f"o `{entry['label']}` (repo {os.path.basename(entry['repo'])}; {entry['work']} chamadas, "
                f"{entry['friction']} sinais de atrito) → registrar como achado em `{todo}`, no formato "
                "e com a catraca do próprio kit")
        others = kit_worktrees(entry["repo"])
        if others:
            names = ", ".join(f"`{os.path.join(t, 'TODO.md')}`" for t in others)
            text += (f" — ou, se a sessão trabalhou numa missão do kit num worktree ligado, no TODO.md dele "
                     f"({names}): o checkout acima é o que o binário do PATH resolve, e escrever nele com "
                     "uma corrida de alvo em voo a para (KIT-TOUCHED no sdd)")
        return text
    if entry["mode"] == "full":
        where = "marketplace j0ruge/skills, modo full"
    else:
        where = f"versionada em {os.path.basename(entry['repo'] or '?')}, modo lean"
    return f"a skill `{entry['label']}` ({where}; {entry['work']} chamadas, {entry['friction']} sinais de atrito) → {cmd}"


def build_output(entries, auto_text=None, reasons=None):
    """O pedido de retro. `entries` são as entradas do texto manual (a lista pode ficar vazia
    quando todas foram ao modo autônomo). `auto_text` é o bloco do pedido autônomo
    (rw_auto.auto_text); com as duas partes, cada bloco leva o rótulo e a lista das suas skills.
    `reasons` são os motivos por extenso de uma entrada que o modo autônomo mandou ao manual.
    Sem os dois argumentos novos, a saída é a de antes do modo autônomo, byte a byte. A linha ao
    dono do pedido autônomo fica com o cmd_stop, que conhece o id do pedido."""
    if not entries:
        return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": auto_text or ""}}
    skills = "; ".join(describe(e) for e in entries)
    label = entries[0]["label"] if len(entries) == 1 else "<skill>"
    text = (
        f"retrofit-watch: nesta sessão trabalhou {skills}. Antes de encerrar, faça a retro: "
        "liste só lições desta sessão no escopo da skill ou do kit — pitfall (uma instrução da skill falhou ou "
        "estava errada, ou faltou um aviso) ou melhoria (faltou passo ou gatilho) —, cada uma com a "
        "evidência (comando ou erro) e o padrão de falha que a skill evitaria; diga o que resolveu ou "
        "marque \"sem correção verificada\". Lição que só vale neste projeto vai para memória ou "
        f"CLAUDE.md, não para a skill. Se nenhuma houver, responda só \"retro {label}: sem lições "
        "novas\". Se houver, termine perguntando se deve executar a ação indicada (com pitfall sem "
        "correção verificada, proponha investigar antes). Não execute nada agora e não cite valores "
        "de segredo."
    )
    names = ", ".join(e["label"] for e in entries)
    message = f"retrofit-watch: retro de {names} pedida ao Claude (RETROFIT_WATCH=off desliga)"
    if reasons:
        message += " — modo manual: " + "; ".join(reasons)
    if auto_text:
        text = f"[modo manual: {names}] {text}\n\n{auto_text}"
    return {
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text},
    }


def session_mode(ctx):
    """`off`, `attended` (pede a retro agora) ou `queue` (sessão desassistida: grava na fila)."""
    mode = os.environ.get("RETROFIT_WATCH", "").lower()
    if mode == "off":
        return "off"
    if mode == "force":
        return "attended"
    flag = os.environ.get("CLAUDE_CODE_SESSION_ATTENDED")
    if flag is not None:
        attended = flag == "1"
    else:
        entry = os.environ.get("CLAUDE_CODE_ENTRYPOINT")
        attended = entry is None or entry == "cli"
    if attended:
        return "attended"
    return "off" if str(ctx.config.get("unattended", "queue")).lower() == "off" else "queue"


# --- fila das sessões desassistidas ------------------------------------------------------------
# Uma fase headless (`sdd run`, cron) não tem quem responda à retro, e devolver contexto a ela
# compraria um turno pago e um escritor a mais no checkout. Por isso ela só grava, FORA de
# qualquer repo (o diretório de dados do plugin), e a retro acontece depois, numa sessão com o
# humano. Só entra com atrito: trabalho sem atrito numa sessão que já acabou quase sempre dá
# "sem lições novas", e reler o transcript para descobrir isso custa caro.

def _queue_lock(ctx):
    ctx.data_dir.mkdir(parents=True, exist_ok=True)
    return _lock(ctx.data_dir / "queue.lock")


def read_queue(ctx):
    try:
        lines = (ctx.data_dir / QUEUE_FILE).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    items = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get("id"):
            items.append(item)
    return items


def enqueue(ctx, payload, entries, entrypoint=None):
    session = payload.get("session_id") or "unknown"
    label = os.environ.get("GIT_REFLOG_ACTION", "")
    cwd = payload.get("cwd") or os.getcwd()
    item = {
        "id": f"{session}:{int(time.time() * 1000)}",
        "ts": int(time.time()),
        "session": session,
        "transcript": payload.get("transcript_path"),
        "cwd": cwd,
        "repo": _toplevel(cwd) if os.path.isdir(cwd) else None,
        "phase": label if label.startswith("sdd:") else None,
        "skills": [{k: e.get(k) for k in ("label", "mode", "arg", "repo", "work", "friction")} for e in entries],
        # O que o gate viu. Oito sessões interativas chegaram aqui com o ambiente dizendo desassistida,
        # por causa não identificada; com isto gravado, o próximo caso traz a causa.
        "gate": {"attended_env": os.environ.get("CLAUDE_CODE_SESSION_ATTENDED"),
                 "entrypoint_env": os.environ.get("CLAUDE_CODE_ENTRYPOINT"),
                 "entrypoint_transcript": entrypoint},
    }
    lock = _queue_lock(ctx)
    try:
        with open(ctx.data_dir / QUEUE_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    finally:
        _unlock(lock)


def drain(ctx, ids):
    """Tira da fila as entradas de `ids` e devolve os ids que de fato saíram."""
    lock = _queue_lock(ctx)
    try:
        items = read_queue(ctx)
        keep = [item for item in items if item["id"] not in ids]
        fd, tmp = tempfile.mkstemp(dir=ctx.data_dir, prefix=".tmp-queue-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(item, ensure_ascii=False) + "\n" for item in keep)
        os.replace(tmp, ctx.data_dir / QUEUE_FILE)
        return {item["id"] for item in items if item["id"] in ids}
    finally:
        _unlock(lock)


def record_metric(ctx, payload, pending):
    line = {"ts": int(time.time()), "session": payload.get("session_id"), "skills": pending,
            "outcome": "none" if NO_LESSONS_RE.search(payload.get("last_assistant_message") or "") else "lessons"}
    with open(ctx.data_dir / "metrics.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")


def log_error(ctx, exc):
    try:
        log_dir = ctx.data_dir if ctx else Path.home() / ".claude/plugins/data/retrofit-watch"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "errors.log", "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {type(exc).__name__}: {exc}\n")
    except OSError:
        pass


def _close_flow(auto, ctx, st):
    """Fecha o pedido autônomo aberto quando o fluxo acabou. Devolve True quando fechou."""
    try:
        if auto.flow_finished(ctx, st["auto_open"]):
            st.pop("auto_open", None)
            return True
    except Exception as exc:  # noqa: BLE001
        log_error(ctx, exc)
    return False


def cmd_stop(payload, ctx):
    mode = session_mode(ctx)
    if mode == "off" and os.environ.get("RETROFIT_WATCH", "").lower() == "off":
        return None  # o `off` da config cala só a sessão desassistida: decide depois do transcript
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        return None
    with State(ctx, payload.get("session_id")) as state:
        st = state.data
        if state.legacy:
            recover_legacy_correlation(transcript, st, ctx)
        chunk, new_offset = read_delta(transcript, st["offset"], rewind=not st.get("legacy_prefix_truncated"))
        if new_offset > st["offset"]:
            st.pop("legacy_prefix_truncated", None)
        st["offset"] = new_offset
        found = None
        for found in ENTRYPOINT_RE.finditer(chunk):
            pass
        if found:
            st["entrypoint"] = found.group(1).decode("utf-8", "replace")
        if mode in ("queue", "off") and st.get("entrypoint") == "cli":
            mode = "attended"  # o ambiente disse desassistida numa sessão interativa (ver o gate da fila)
        if mode == "off":
            state.save()
            return None
        # O modo autônomo só existe na sessão assistida e só se carrega fora do `manual`. Qualquer
        # falha nele vai ao errors.log e o hook segue com o texto manual (auto = None).
        auto = None
        silent = False
        if mode == "attended" and ctx.mode != "manual":
            try:
                import rw_auto as auto
                silent = auto.flow_open(st)
            except Exception as exc:  # noqa: BLE001
                log_error(ctx, exc)
                auto, silent = None, False
        if payload.get("stop_hook_active"):
            if st["pending"]:
                record_metric(ctx, payload, st["pending"])
                st["pending"] = []
            if silent:
                _close_flow(auto, ctx, st)
            state.save()
            return None
        markers = MARKERS + tuple(kit.encode() for kit in ctx.kits)
        # O erro pode chegar em outro Stop, sem o marcador da chamada no trecho novo.
        if not st["skills"] and not (st["skill_calls"] and b'"is_error"' in chunk) and not any(
                marker in chunk for marker in markers):
            state.save()
            return None
        scanner = Scanner(st, ctx)
        scanner.silent = silent
        scanner.scan(chunk)
        # O fechamento se confere depois da varredura: o trecho escrito pelo fluxo não conta.
        if silent and not _close_flow(auto, ctx, st):
            state.save()
            return None
        if mode == "attended" and waiting_for_user(payload, scanner.last_tool):
            state.save()
            return None
        ready = [e for e in st["skills"].values() if eligible(e)]
        if mode == "queue":
            ready = [e for e in ready if e["friction"] >= 1]
        if not ready:
            state.save()
            return None
        if mode == "queue":
            enqueue(ctx, payload, ready, st.get("entrypoint"))
            output = None
        else:
            output = None
            if auto is not None:
                try:
                    auto_entries, manual, reasons = auto.split(ctx, payload, ready, st.get("entrypoint"))
                    if auto_entries:
                        pedido = auto.open_request(ctx, payload, auto_entries)
                        output = build_output(manual, auto.auto_text(ctx, pedido, auto_entries), reasons)
                        output["systemMessage"] = "\n".join(
                            m for m in (auto.auto_message(pedido, auto_entries), output.get("systemMessage")) if m)
                        st["auto_open"] = {"id": pedido["id"], "ts": pedido["ts"]}
                    else:
                        output = build_output(manual, reasons=reasons)
                except Exception as exc:  # noqa: BLE001
                    log_error(ctx, exc)
                    output = None
            if output is None:
                output = build_output(ready)
            st["pending"] = [e["label"] for e in ready]
        for entry in ready:
            entry["reviews"] += 1
            entry["work"] = entry["friction"] = 0
        state.save()
        return output


def queue_notice(ctx):
    """O segmento da fila das sessões headless, ou None."""
    items = read_queue(ctx)
    if not items:
        return None
    labels = sorted({s.get("label") for item in items for s in item.get("skills", []) if s.get("label")})
    noun = "retro pendente" if len(items) == 1 else "retros pendentes"
    return f"{len(items)} {noun} de sessões headless ({', '.join(labels)}) — /retrofit-watch:retrofit-watch pendentes"


# Os segmentos do aviso de startup, na ordem da linha: (módulo, função). None é a fila de hoje, daqui.
NOTICES = ((None, "queue_notice"), ("rw_auto", "held_notice"), ("rw_auto", "orphan_notice"),
           ("rw_auto", "behind_notice"), ("rw_store", "criterion_notice"))


def cmd_pending(payload, ctx):
    """SessionStart `startup`: uma linha para o humano, nunca para o contexto. Junta com ` · ` a fila de
    hoje, os retrofits segurados, os órfãos, os publicados com a cópia instalada atrás e o critério da
    v2. Cada segmento roda no seu `try` (M11): a exceção vai ao errors.log, e os outros saem."""
    if session_mode(ctx) != "attended":
        return None
    parts = []
    for module, name in NOTICES:
        try:
            source = sys.modules[__name__] if module is None else importlib.import_module(module)
            text = getattr(source, name)(ctx)
        except Exception as exc:  # noqa: BLE001 — um segmento não apaga o aviso dos outros
            log_error(ctx, exc)
            continue
        if text:
            parts.append(text)
    return {"systemMessage": "retrofit-watch: " + " · ".join(parts)} if parts else None


def data_dir_problem(ctx):
    """A recusa quando a pasta de dados não existe ou é ambígua, ou None. Responder `[]` ou
    "gravei" nesses casos esconde os dados de verdade."""
    if len(ctx.data_candidates) > 1:
        return ("retrofit-watch: mais de uma pasta de dados: "
                + ", ".join(str(p) for p in ctx.data_candidates)
                + ". Defina CLAUDE_PLUGIN_DATA com a certa.\n")
    if not ctx.data_dir.is_dir():
        return (f"retrofit-watch: a pasta de dados não existe: {ctx.data_dir}. Sem ela não há "
                "fila para ler; defina CLAUDE_PLUGIN_DATA com a pasta do plugin em "
                "~/.claude/plugins/data/.\n")
    return None


def cmd_queue(argv, ctx):
    """`queue` lista a fila em JSON; `queue --done ID...` tira as entradas já retradas.

    Sai 1, sem tocar em nada, quando a pasta de dados não existe ou é ambígua, e quando um id do
    `--done` não está na fila: responder `[]` ou "tirei" nesses casos esconde a fila de verdade.
    """
    problem = data_dir_problem(ctx)
    if problem:
        sys.stderr.write(problem)
        return 1
    if argv[:1] == ["--done"]:
        ids = set(argv[1:])
        removed = drain(ctx, ids)
        sys.stderr.write(f"retrofit-watch: {len(removed)} entrada(s) tirada(s) da fila em {ctx.data_dir}.\n")
        missing = sorted(ids - removed)
        if missing:
            sys.stderr.write("retrofit-watch: não estavam na fila: " + ", ".join(missing) + "\n")
            return 1
        return 0
    items = read_queue(ctx)
    for item in items:
        item["transcript_exists"] = bool(item.get("transcript")) and os.path.isfile(item["transcript"])
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


# Os verbos do registro do modo autônomo (rw_auto.py) e quantos argumentos posicionais cada um leva.
CLI_USAGE = {
    "triage": ("triage <id>", 1),
    "held": ("held", 0),
    "hold": ("hold <id> <item> <motivo>", 3),
    "approve": ("approve <id> <lote>", 2),
    "discard": ("discard <id> <item>|--retro [--motivo M]", 2),
    # Os verbos da loja (rw_store.py) conferem as próprias opções: aridade None.
    "prepare": ("prepare <id> <lote> [--redo]", None),
    "seal": ("seal <id> <lote> --licoes L1,L2 [--fases a,b]", None),
    "harvest": ("harvest", None),
    # A porta de publicação (rw_gate.py) também confere os próprios argumentos.
    "publish": ("publish <id> <lote>", None),
}


def cli(argv, ctx):
    """Os verbos do modo autônomo. Imprimem JSON em ASCII (o stdout do Windows é cp1252).

    rc 0 certo, 1 recusado, 2 uso, pasta de dados ausente ou ambígua, ou arquivo do fluxo fora do
    formato (rw_auto.Malformed). Os erros vão ao stderr, sem traceback. Os verbos da loja (`harvest`,
    `prepare`, `seal`) vão ao rw_store.cli, que também dá 2 em StoreError e OSError. O `publish` vai ao
    rw_gate.cli: 0 publicado e instalado, 1 segurado, 2 uso, 3 erro, 4 publicado com a instalação falha."""
    problem = data_dir_problem(ctx)
    if problem:
        sys.stderr.write(problem)
        return 2
    verb, args, kwargs = argv[0], list(argv[1:]), {}
    if verb == "publish":
        import rw_gate
        return rw_gate.cli(args, ctx)
    if CLI_USAGE[verb][1] is None:
        import rw_store
        return rw_store.cli(verb, args, ctx)
    import rw_auto as auto
    if verb == "discard" and len(args) == 4 and args[2] == "--motivo":
        kwargs["motivo"] = args.pop()
        args.pop()
    # `discard <id> --retro` fecha a retro inteira (item 14): o `--retro` ocupa o lugar do item.
    retro = verb == "discard" and len(args) == 2 and args[1] == "--retro"
    usage, arity = CLI_USAGE[verb]
    if len(args) != arity:
        sys.stderr.write(f"retrofit-watch: uso: retrofit_watch.py {usage}\n")
        return 2
    try:
        if verb == "triage":
            result = auto.triage(ctx, *args)
        elif verb == "held":
            result = auto.held(ctx)
        elif verb == "hold":
            result = auto.hold_item(ctx, *args)
        elif verb == "approve":
            result = json.loads(auto.approve(ctx, *args).read_text(encoding="utf-8"))
        elif retro:
            result = auto.discard_retro(ctx, args[0], **kwargs)
        else:
            result = auto.discard(ctx, *args, **kwargs)
    except auto.Malformed as exc:
        sys.stderr.write(f"retrofit-watch: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


def cmd_baseline(payload, ctx):
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        return None
    with State(ctx, payload.get("session_id")) as state:
        if state.is_new:
            state.data["offset"] = end_offset(transcript)
            state.save()
    return None


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        print("Uso: retrofit_watch.py stop|baseline|pending  (lê o JSON do hook no stdin)")
        print("     retrofit_watch.py queue [--done ID...]  (fila das sessões headless)")
        for verb, (usage, arity) in CLI_USAGE.items():
            where = ("a porta, rw_gate.py" if verb == "publish"
                     else "a loja, rw_store.py" if arity is None else "rw_auto.py")
            print(f"     retrofit_watch.py {usage}  (modo autônomo: {where})")
        return 0
    if argv and argv[0] == "queue":
        return cmd_queue(argv[1:], Context())
    if argv and argv[0] in CLI_USAGE:
        return cli(argv, Context())
    ctx = None
    try:
        ctx = Context()
        # O Claude Code manda UTF-8; no Windows o stdin do Python é cp1252 e `ç` chegaria `Ã§`.
        raw = sys.stdin.buffer.read().decode("utf-8")
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        handler = {"stop": cmd_stop, "baseline": cmd_baseline, "pending": cmd_pending}.get(argv[0] if argv else "")
        if handler is None:
            return 0
        output = handler(payload, ctx)
        if output:
            # ASCII com \uXXXX: o `→` não existe em cp1252, o stdout do Python no Windows.
            sys.stdout.write(json.dumps(output))
    except Exception as exc:  # noqa: BLE001 — hook de conveniência nunca derruba a sessão
        log_error(ctx, exc)
    return 0


# Rodado como script, este módulo é o `__main__`: sem isto, o `import retrofit_watch` dos módulos
# novos (rw_*.py) carregaria uma segunda cópia, com outro estado.
sys.modules.setdefault("retrofit_watch", sys.modules[__name__])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
