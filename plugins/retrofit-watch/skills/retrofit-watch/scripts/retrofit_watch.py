#!/usr/bin/env python3
"""retrofit-watch: ao fim do turno em que uma skill nossa trabalhou, pede ao Claude a retro dela.

Registrado em hooks/hooks.json:
  Stop                         -> retrofit_watch.py stop
  SessionStart (resume|fork)   -> retrofit_watch.py baseline

"Nossa" = skill do marketplace chewiesoft-marketplace (j0ruge/skills; retrofit modo full, o
argumento é o nome do PLUGIN) ou skill versionada em git num repo de dono conhecido (modo lean).
Terceiros, skills fora do git e as do Hermes ficam de fora.

"Kit" = produto nosso que não é skill, reconhecido pelo binário (padrão: `sdd`, o kit de
~/repos/sdd_agents). O binário resolvido no PATH aponta o repo; contam como trabalho do kit o
comando `/<kit>-*`, o subagente `<kit>-*` e o próprio binário no Bash. A lição vai para o
TODO.md do repo do kit, não para o /retrofit-skill.

Controle por ambiente:
  RETROFIT_WATCH=off     desliga
  RETROFIT_WATCH=force   roda mesmo em sessão desassistida (testes com claude -p)
Config opcional em ~/.claude/retrofit-watch.json: owners, include, exclude, deny_roots, kits.

Estado em ${CLAUDE_PLUGIN_DATA}/sessions/<session_id>.json (offset do transcript e contadores).
Nunca grava texto do assistente. Qualquer erro interno vai para <data>/errors.log e sai com 0.
Só biblioteca padrão.
"""
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MARKETPLACE = "chewiesoft-marketplace"
DEFAULT_OWNERS = ("j0ruge", "jrc-brasil", "chewiesoft")
ALWAYS_EXCLUDED = {"retrofit-skill", "retrofit-watch", "skill-quality-audit"}
DEFAULT_KITS = ("sdd",)
MAX_REVIEWS = 2
FIRST_REVIEW_WORK = 5
SECOND_REVIEW_FRICTION = 2
STATE_TTL_SECONDS = 14 * 24 * 3600
GIT_TIMEOUT = 2

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


class Context:
    def __init__(self, home=None, data_dir=None):
        self.home = Path(os.path.realpath(home or os.environ.get("HOME") or Path.home()))
        data = data_dir or os.environ.get("CLAUDE_PLUGIN_DATA") or self.home / ".claude/plugins/data/retrofit-watch"
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
        return [os.path.realpath(r) for r in roots]

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

def _git(args, cwd):
    try:
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              timeout=GIT_TIMEOUT)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _full(plugin, skill, ctx):
    if plugin in ctx.excluded or skill in ctx.excluded:
        return None
    label = plugin if skill in (plugin, None) else f"{plugin} ({skill})"
    return {"key": f"full:{plugin}", "mode": "full", "arg": plugin, "label": label, "repo": None}


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
    top = _git(["rev-parse", "--show-toplevel"], os.path.dirname(os.path.realpath(exe)))
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
    real = os.path.realpath(path)
    name = os.path.basename(real.rstrip("/"))
    if name in ctx.config.get("include", []):
        top = _git(["rev-parse", "--show-toplevel"], real)
        return _lean(name, top)
    if name in ctx.excluded:
        return None
    home = str(ctx.home)
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
    top = _git(["rev-parse", "--show-toplevel"], real)
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
        self._lock = open(self.lock_path, "w")
        fcntl.flock(self._lock, fcntl.LOCK_EX)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data, self.is_new = None, True
        if not isinstance(self.data, dict):
            self.data, self.is_new = None, True
        if self.data is None:
            self.data = {"created": time.time()}
        for key, default in (("offset", 0), ("skills", {}), ("current", None), ("classified", {}),
                             ("pending", []), ("done", [])):
            self.data.setdefault(key, default)
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
        fcntl.flock(self._lock, fcntl.LOCK_UN)
        self._lock.close()
        return False


# --- transcript --------------------------------------------------------------------------------

def read_delta(path, offset):
    """Bytes novos do transcript até a última linha completa. Devolve (bytes, novo_offset)."""
    size = os.path.getsize(path)
    if offset > size:
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
    def __init__(self, state, ctx):
        self.st = state
        self.ctx = ctx
        self.last_tool = None

    def _watch(self, info):
        if info is None:
            self.st["current"] = None
            return
        key = info["key"]
        entry = self.st["skills"].setdefault(key, dict(info, reviews=0, work=0, friction=0))
        if key in self.st["done"]:
            entry["reviews"] = MAX_REVIEWS
        self.st["current"] = key

    def _bump(self, field):
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
        """O registro no TODO.md do kit é o retrofit dele: a retro daquele kit não volta."""
        real = os.path.realpath(path or "")
        for key, entry in self.st["skills"].items():
            if entry["mode"] == "kit" and real == os.path.join(entry["repo"], "TODO.md"):
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

    def invocation(self, name, args):
        plugin = name.split(":", 1)[0]
        if plugin == "retrofit-skill":
            self._retrofit_ran(args)
            self.st["current"] = None
        elif ":" not in name and kit_of(name, self.ctx):
            self.kit(kit_of(name, self.ctx))
        elif ":" in name:
            info = classify_plugin(plugin, self.ctx)
            if info is not None:
                self._watch(info)
            elif self.ctx.installed_marketplaces(plugin):
                self.st["current"] = None

    def skill_path(self, path):
        cache = self.st["classified"]
        if path not in cache:
            cache[path] = classify_path(path, self.ctx)
        self._watch(cache[path])

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
                if block.get("type") == "text" and DEVIATION_RE.search(block.get("text", "")):
                    self._bump("friction")
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                self.last_tool = name
                tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
                if name == "Skill":
                    self.invocation(str(tool_input.get("skill", "")), tool_input.get("args", ""))
                elif name not in NON_WORK_TOOLS:
                    self.tool_use(name, tool_input)
                    self._bump("work")
        elif kind == "user":
            if d.get("isMeta"):
                if isinstance(content, list):
                    for block in content:
                        text = block.get("text", "") if isinstance(block, dict) else ""
                        if block.get("type") == "text" and text.startswith(BASE_PREFIX):
                            self.skill_path(text[len(BASE_PREFIX):].split("\n", 1)[0].strip())
                return
            if isinstance(content, str):
                command = CMD_RE.search(content)
                if command:
                    args = ARGS_RE.search(content)
                    self.invocation(command.group(1), args.group(1) if args else "")
                else:
                    self.user_text(content)
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result" and block.get("is_error"):
                        self._bump("friction")
                    elif block.get("type") == "text":
                        self.user_text(block.get("text", ""))

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
        return (f"o `{entry['label']}` (repo {os.path.basename(entry['repo'])}; {entry['work']} chamadas, "
                f"{entry['friction']} sinais de atrito) → registrar como achado em `{todo}`, no formato "
                "e com a catraca do próprio kit")
    if entry["mode"] == "full":
        where = "marketplace j0ruge/skills, modo full"
    else:
        where = f"versionada em {os.path.basename(entry['repo'] or '?')}, modo lean"
    return f"a skill `{entry['label']}` ({where}; {entry['work']} chamadas, {entry['friction']} sinais de atrito) → {cmd}"


def build_output(entries):
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
    return {
        "systemMessage": f"retrofit-watch: retro de {names} pedida ao Claude (RETROFIT_WATCH=off desliga)",
        "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text},
    }


def attended():
    mode = os.environ.get("RETROFIT_WATCH", "").lower()
    if mode == "off":
        return False
    if mode == "force":
        return True
    flag = os.environ.get("CLAUDE_CODE_SESSION_ATTENDED")
    if flag is not None:
        return flag == "1"
    entry = os.environ.get("CLAUDE_CODE_ENTRYPOINT")
    return entry is None or entry == "cli"


def record_metric(ctx, payload, pending):
    line = {"ts": int(time.time()), "session": payload.get("session_id"), "skills": pending,
            "outcome": "none" if NO_LESSONS_RE.search(payload.get("last_assistant_message") or "") else "lessons"}
    with open(ctx.data_dir / "metrics.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")


def cmd_stop(payload, ctx):
    if not attended():
        return None
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        return None
    with State(ctx, payload.get("session_id")) as state:
        st = state.data
        chunk, new_offset = read_delta(transcript, st["offset"])
        st["offset"] = new_offset
        if payload.get("stop_hook_active"):
            if st["pending"]:
                record_metric(ctx, payload, st["pending"])
                st["pending"] = []
            state.save()
            return None
        markers = MARKERS + tuple(kit.encode() for kit in ctx.kits)
        if not st["skills"] and not any(marker in chunk for marker in markers):
            state.save()
            return None
        scanner = Scanner(st, ctx)
        scanner.scan(chunk)
        if waiting_for_user(payload, scanner.last_tool):
            state.save()
            return None
        ready = [e for e in st["skills"].values() if eligible(e)]
        if not ready:
            state.save()
            return None
        output = build_output(ready)
        for entry in ready:
            entry["reviews"] += 1
            entry["work"] = entry["friction"] = 0
        st["pending"] = [e["label"] for e in ready]
        state.save()
        return output


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
        print("Uso: retrofit_watch.py stop|baseline  (lê o JSON do hook no stdin)")
        return 0
    ctx = None
    try:
        ctx = Context()
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        handler = {"stop": cmd_stop, "baseline": cmd_baseline}.get(argv[0] if argv else "")
        if handler is None:
            return 0
        output = handler(payload, ctx)
        if output:
            sys.stdout.write(json.dumps(output, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 — hook de conveniência nunca derruba a sessão
        try:
            log_dir = ctx.data_dir if ctx else Path.home() / ".claude/plugins/data/retrofit-watch"
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "errors.log", "a", encoding="utf-8") as fh:
                fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {type(exc).__name__}: {exc}\n")
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
