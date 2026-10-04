#!/usr/bin/env python3
"""Auditoria estrutural determinística de Agent Skills (somente leitura).

Audita uma ou mais skills (ou a família padrão) contra a spec Agent Skills,
autocontenção, progressive disclosure e sinais de afirmação factual. Nunca
escreve arquivo e nunca executa código da skill auditada: scripts são checados
com compile() e `bash -n`. Gates externos (audit-skill.sh do Hermes e
skills-ref) rodam só se encontrados; ausentes viram [SKIP], nunca falha.

Códigos de saída: 0 = sem erro | 1 = erro (ou aviso com --strict) | 2 = uso inválido.
Significado de cada check: references/checks.md da skill skill-quality-audit.
"""
from __future__ import annotations

import ast
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent
FAMILY = ["skill-quality-audit", "skill-self-containment", "skill-claim-check", "skill-refactoring"]

# Campos de topo aceitos pelo skills-ref (validator.py, ALLOWED_FIELDS).
SPEC_FIELDS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
# Campos que o Hermes só lê no topo: movê-los desliga a função (filtro por SO, credenciais,
# pré-requisitos). Viram INFO no A4: o skills-ref reprova, mas não há correção a fazer.
# Validador de referência via uvx quando não está no PATH. Reconferir a versão com:
#   python3 -m pip index versions skills-ref   (ou https://pypi.org/project/skills-ref/)
SKILLS_REF_PIN = "skills-ref==0.1.1"
HERMES_TOP_FIELDS = {"platforms", "required_credential_files", "required_environment_variables", "prerequisites"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME, MAX_DESC, MAX_COMPAT = 64, 1024, 500
MAX_LINES = 500          # spec Agent Skills: SKILL.md abaixo de 500 linhas
INFO_LINES = 400         # heurística local (skill-refactoring): re-comprimir acima disto
WARN_CHARS = 20000       # heurística local (skill-refactoring): +20K chars
REF_TOC_LINES = 300      # skill-creator: reference > 300 linhas pede sumário

ERRO, AVISO, INFO, SKIP, OK = "ERRO", "AVISO", "INFO", "SKIP", "OK"

# --- Padrões de afirmação factual: vendorizados de skill-claim-check -------------
# (scripts/listar-afirmacoes.sh). Manter idênticos; o teste de paridade em
# tests/ compara as linhas apontadas quando a irmã está presente.
CLAIM_PATTERNS = [
    ("número/limite",
     r"\b\d{1,3}(?:[.,]\d{3})+\b|\b\d+\s?(?:k|KB|MB|GB|chars?|caracteres|linhas|ms|s|min|tokens)\b",
     "de onde sai esse número? o sistema calcula? -> descreva a derivação"),
    ("caminho absoluto",
     r"(?<![\w`])/(?:home|Users|opt|srv|var)/[\w./-]+",
     "existe em outra máquina? -> caminho relativo ou $HERMES_HOME"),
    ("versão fixa",
     r"\bv?\d+\.\d+(?:\.\d+)?\b",
     "validado quando? -> cite o comando que mostra a versão"),
    ("absoluto sobre terceiro",
     r"\b(sempre|nunca)\b\s+\w+",
     "você controla o outro lado? -> diga o que foi OBSERVADO, e quando"),
]

# --- Citação de arquivos próprios: mesma âncora do audit-skill.sh --------------
RE_REF = re.compile(r"(?<![\w/~.-])(?:\./)?references/((?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.md)(?![A-Za-z0-9._-])")
RE_ASSET = re.compile(r"(?<![\w/~.-])(?:\./)?assets/((?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.[A-Za-z0-9]+)(?![A-Za-z0-9._-])")
RE_SCR = re.compile(r"(?<![\w/~.-])(?:\./)?scripts/([A-Za-z0-9._-]+\.[A-Za-z0-9]+)(?![A-Za-z0-9._-])")
RE_ESCAPE = re.compile(r"\S*(?<!\.)\.\./\S*")
RE_FENCE = re.compile(r"^\s*(```|~~~)")
RE_MACHINE = re.compile(r"(?<![\w~$])/(?:home|Users)/[A-Za-z0-9._-]+/|\b[A-Za-z]:\\Users\\[A-Za-z0-9._-]+")
RE_HERMES = re.compile(r"~/\.hermes|\$HERMES_HOME|\$\{HERMES_HOME")
# Boas práticas agentskills.io (best-practices, using-scripts, evaluating-skills), checks F1 a F4.
RE_GOTCHAS = re.compile(r"^#{1,4}\s*.*\b(gotchas?|armadilhas?|pitfalls?|pegadinhas?|erros comuns|"
                        r"cuidados|antipadr[õo]es|anti-?patterns?|common mistakes)\b", re.I | re.M)
RE_WHEN = re.compile(r"\b(quando|se|caso|antes|depois|ao|para|sempre que|só|when|if|before|after|for|only)\b", re.I)
RE_INTERACTIVE = {".sh": re.compile(r"(?<![\w-])read\s+(?:-[a-zA-Z]*\s+)*-[a-zA-Z]*p\b"),
                  ".bash": re.compile(r"(?<![\w-])read\s+(?:-[a-zA-Z]*\s+)*-[a-zA-Z]*p\b")}
RE_HELP = re.compile(r"argparse|click|typer|--help|-h\b|usage|Uso:", re.I)
RE_TOC = re.compile(r"^#{1,3}\s*(sum[aá]rio|[ií]ndice|conte[uú]do|contents|table of contents)\b", re.I | re.M)


# ============================ frontmatter (subconjunto YAML) =====================
class FM:
    """Resultado do parser: dados, chaves em flow style e construções não suportadas."""

    def __init__(self):
        self.data: dict = {}
        self.flow: list[str] = []
        self.problems: list[str] = []
        self.errors: list[str] = []   # YAML que PyYAML e strictyaml recusam


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _next_content(lines, i):
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        i += 1
    return i


def _unquote(s: str, fm: FM, where: str):
    s = s.strip()
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        try:
            return json.loads(s)
        except ValueError:
            return s[1:-1]
    if s.startswith("'") and s.endswith("'") and len(s) >= 2:
        return s[1:-1].replace("''", "'")
    if s[:1] in ("&", "*", "!"):
        fm.problems.append(f"{where}: âncora/alias/tag YAML não suportado")
    return re.sub(r"\s+#.*$", "", s)


def _flow_items(raw: str, fm: FM, where: str):
    inner = raw.strip()[1:-1]
    return [_unquote(x, fm, where) for x in inner.split(",") if x.strip()]


def _block_scalar(lines, i, parent_indent, style):
    buf, block_indent = [], None
    while i < len(lines):
        line = lines[i]
        if line.strip() and _indent(line) <= parent_indent:
            break
        if line.strip() and block_indent is None:
            block_indent = _indent(line)
        buf.append(line[block_indent:] if block_indent is not None and line.strip() else "")
        i += 1
    while buf and not buf[-1]:
        buf.pop()
    if style.startswith("|"):
        text = "\n".join(buf)
    else:
        paras, cur = [], []
        for b in buf:
            if b:
                cur.append(b.strip())
            else:
                paras.append(" ".join(cur))
                cur = []
        paras.append(" ".join(cur))
        text = "\n".join(p for p in paras if p)
    return text, i


def _value(rest, lines, i, indent, fm: FM, key_path):
    where = ".".join(key_path)
    if rest in ("|", "|-", "|+", ">", ">-", ">+"):
        return _block_scalar(lines, i, indent, rest)
    if rest.startswith("[") or rest.startswith("{"):
        closer = "]" if rest.startswith("[") else "}"
        raw = rest
        while not raw.rstrip().endswith(closer) and i < len(lines):
            raw += " " + lines[i].strip()
            i += 1
        fm.flow.append(where)
        if closer == "]":
            return _flow_items(raw, fm, where), i
        fm.problems.append(f"{where}: mapping em flow style não interpretado")
        return raw, i
    quoted = re.match(r"""^("(?:[^"\\]|\\.)*"|'(?:[^']|'')*')\s*(?:#.*)?$""", rest)
    if quoted:  # aspas numa linha, com ou sem comentário depois
        return _unquote(quoted.group(1), fm, where), i
    if rest[:1] in ('"', "'"):
        raw = rest
        while i < len(lines) and not raw.rstrip().endswith(rest[0]):
            raw += " " + lines[i].strip()
            i += 1
        return _unquote(raw, fm, where), i
    val = _unquote(rest, fm, where)
    while i < len(lines) and lines[i].strip() and _indent(lines[i]) > indent \
            and not lines[i].lstrip().startswith("#"):
        val += " " + lines[i].strip()  # scalar plano em várias linhas
        i += 1
    if re.search(r":\s", val) or val.rstrip().endswith(":"):
        fm.errors.append(f"{where}: valor sem aspas contém ': ' (YAML inválido para PyYAML e strictyaml)")
    return val, i


def _list(lines, i, indent, fm: FM, key_path):
    out = []
    while True:
        i = _next_content(lines, i)
        if i >= len(lines) or _indent(lines[i]) != indent or not lines[i].lstrip().startswith("-"):
            return out, i
        item = lines[i].strip()[1:].strip()
        if re.match(r"^[\w.-]+\s*:(\s|$)", item):
            # Lista de mappings (ex.: required_credential_files: - path: x / description: y):
            # o "- " vira indentação e o item é lido como mapping na coluna da primeira chave.
            after_dash = lines[i].lstrip()[1:]
            col = _indent(lines[i]) + 1 + len(after_dash) - len(after_dash.lstrip())
            sub = list(lines)
            sub[i] = " " * col + after_dash.lstrip()
            val, i = _mapping(sub, i, col, fm, key_path)
            out.append(val)
            continue
        i += 1
        val, i = _value(item, lines, i, indent, fm, key_path) if item else ("", i)
        out.append(val)


def _mapping(lines, i, indent, fm: FM, key_path):
    out = {}
    while True:
        i = _next_content(lines, i)
        if i >= len(lines):
            return out, i
        line = lines[i]
        ind = _indent(line)
        if "\t" in line[: ind + 1]:
            fm.problems.append(f"linha {i + 2} do frontmatter: TAB na indentação")
        if ind < indent:
            return out, i
        if ind > indent:
            fm.problems.append(f"linha {i + 2} do frontmatter: indentação inesperada")
            i += 1
            continue
        m = re.match(r"""^(?:"([^"]+)"|'([^']+)'|([^\s:#][^:]*?))\s*:(?:\s+(.*))?$""", line.strip())
        if not m:
            fm.problems.append(f"linha {i + 2} do frontmatter: não é 'chave: valor'")
            i += 1
            continue
        key = m.group(1) or m.group(2) or m.group(3)
        rest = (m.group(4) or "").strip()
        i += 1
        path = key_path + [key]
        if key in out:
            fm.problems.append(f"{'.'.join(path)}: chave duplicada")
        if rest:
            out[key], i = _value(rest, lines, i, indent, fm, path)
            continue
        j = _next_content(lines, i)
        if j < len(lines) and lines[j].lstrip().startswith("-") and _indent(lines[j]) >= indent:
            out[key], i = _list(lines, j, _indent(lines[j]), fm, path)
        elif j < len(lines) and _indent(lines[j]) > indent:
            out[key], i = _mapping(lines, j, _indent(lines[j]), fm, path)
        else:
            out[key] = ""


def parse_frontmatter(text: str):
    """Devolve (FM, corpo, erro). Suporta o subconjunto de YAML usado em SKILL.md."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, "SKILL.md não começa com frontmatter '---'"
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            fm = FM()
            fm.data, _ = _mapping(lines[1:end], 0, 0, fm, [])
            return fm, "\n".join(lines[end + 1:]), None
    return None, text, "frontmatter sem '---' de fechamento"


# ================================== auditoria ====================================
class Report:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.findings: list[dict] = []
        self.related: list[str] = []
        self.has_metadata = False  # instalador do Cursor remove o bloco metadata (e o related_skills)
        self.claims: list[dict] = []

    def add(self, level, check_id, msg):
        self.findings.append({"level": level, "id": check_id, "msg": msg})

    def count(self, level):
        return sum(1 for f in self.findings if f["level"] == level)


def outside_code(text: str):
    """(nº da linha, linha) fora de blocos ``` : ali o comando é o sensor."""
    fence = None
    for n, line in enumerate(text.splitlines(), 1):
        m = RE_FENCE.match(line)
        if m and fence is None:
            fence = m.group(1)
            continue
        if m and m.group(1) == fence:
            fence = None
            continue
        if fence is None:
            yield n, line


def read(p: Path, rep=None, check_id=None) -> str:
    """UTF-8 estrito: arquivo inválido vira ERRO (PyYAML, strictyaml e audit-skill.sh falham nele)."""
    data = p.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        if rep is not None:
            rep.add(ERRO, check_id, f"{p.relative_to(rep.path)} não é UTF-8 válido (byte {e.start})")
        return data.decode("utf-8", errors="replace")


def escaping(text: str, depth: int):
    """Paths com mais '../' seguidos do que a profundidade do arquivo dentro da skill."""
    out = set()
    for m in RE_ESCAPE.finditer(text):
        core = m.group(0).strip("`'\"()[]<>,;")
        if "://" in core:
            continue
        j = core.find("../")
        ups = 0
        while core.startswith("../", j):
            ups, j = ups + 1, j + 3
        if ups > depth:
            out.add(core)
    return sorted(out)


def own_prefix_normalizer(skill_name: str):
    proprio = re.compile(r"[^\s`\"'()\[\]]*/" + re.escape(skill_name) + r"/(?=(?:references|scripts|assets)/)")
    # Placeholders da raiz da skill: <dir>/, {{dir}}/, SKILL_DIR/ e variável com SKILL no nome
    # ({SKILL_DIR}/, ${CLAUDE_SKILL_DIR}/, $SKILL_DIR/). $HERMES_HOME/scripts/ é o harness, não a skill.
    placeholder = re.compile(r"(?<![\w/~.-])(?:<[^>\s]+>|\{\{[^}\s]+\}\}|\$?\{[A-Za-z0-9_]*SKILL[A-Za-z0-9_]*\}"
                             r"|\$[A-Za-z0-9_]*SKILL[A-Za-z0-9_]*|(?<!\$)(?<!\{)[A-Z][A-Z0-9_]{3,})/(?=(?:references|scripts|assets)/)")
    return lambda t: placeholder.sub("", proprio.sub("", t))


def find_skill(name: str, roots):
    for root in roots:
        for cand in (root / name, *root.glob(f"*/{name}")):
            if (cand / "SKILL.md").is_file():
                return cand
    return None


def check_frontmatter(rep: Report, fm: FM, args, roots):
    d = fm.data
    for p in fm.errors:
        rep.add(ERRO, "A1", f"frontmatter inválido: {p}")
    for p in fm.problems:
        rep.add(AVISO, "A1", f"frontmatter fora do subconjunto suportado: {p}")
    name = d.get("name")
    if not isinstance(name, str) or not name.strip():
        rep.add(ERRO, "A2", "campo 'name' ausente ou vazio")
    else:
        name = name.strip()
        if len(name) > MAX_NAME or not NAME_RE.match(name):
            rep.add(ERRO, "A2", f"name '{name}' fora da spec (a-z, 0-9, hífen simples, até {MAX_NAME})")
        if name != rep.path.name:
            rep.add(ERRO, "A2", f"name '{name}' difere do diretório '{rep.path.name}'")
    desc = d.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.add(ERRO, "A3", "campo 'description' ausente ou vazio")
    else:
        dl = len(desc.strip())
        if dl > MAX_DESC:
            rep.add(ERRO, "A3", f"description com {dl} chars > {MAX_DESC} (spec)")
        elif args.desc_budget and dl > args.desc_budget:
            rep.add(INFO, "A3", f"description com {dl} chars: índices que cortam em {args.desc_budget} "
                                f"mostram só '{desc.strip()[:args.desc_budget - 3]}...' (confira se o gatilho vem primeiro)")
    extra = sorted(set(d) - SPEC_FIELDS - HERMES_TOP_FIELDS)
    if extra:
        rep.add(AVISO, "A4", f"campos de topo fora da spec {extra}: skills-ref reprova; mover para metadata "
                             "(author e version viram metadata.author e metadata.version, em texto)")
    functional = sorted(set(d) & HERMES_TOP_FIELDS)
    if functional:
        rep.add(INFO, "A4", f"campos de topo fora da spec {functional} ficam: o Hermes só os lê no topo "
                            "(skills-ref reprova; custo aceito)")
    for key in fm.flow:
        rep.add(ERRO, "A5", f"'{key}' em flow style ([...] ou {{...}}): strictyaml/skills-ref rejeita; usar lista em bloco")
    compat = d.get("compatibility")
    if compat is not None and (not isinstance(compat, str) or not 1 <= len(compat) <= MAX_COMPAT):
        rep.add(ERRO, "A6", f"compatibility precisa ser texto de 1 a {MAX_COMPAT} chars")
    meta = d.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        rep.add(ERRO, "A8", "metadata precisa ser um mapa (spec: chaves e valores em texto)")
    elif isinstance(meta, dict):
        nested = sorted(k for k, v in meta.items() if not isinstance(v, str))
        foreign = [k for k in nested if k != "hermes"]
        if foreign:
            rep.add(AVISO, "A8", f"metadata com valor que não é texto em {foreign}: spec pede mapa texto->texto")
        if "hermes" in nested:
            rep.add(INFO, "A8", "metadata.hermes aninhado: convenção do Hermes, fora do texto da spec "
                                "(skills-ref aceita porque converte para texto)")
    rep.has_metadata = isinstance(meta, dict)
    hermes = meta.get("hermes") if isinstance(meta, dict) else None
    related = hermes.get("related_skills") if isinstance(hermes, dict) else None
    if isinstance(related, str):
        related = [r.strip() for r in related.strip("[]").split(",") if r.strip()]
    rep.related = [str(r) for r in related] if isinstance(related, list) else []
    missing = [r for r in rep.related if find_skill(r, roots) is None]
    if missing:
        rep.add(INFO, "A7", f"related_skills não encontradas neste harness (ok se a skill roda sozinha): {missing}")


def git_ignored(d: Path, rels: list) -> set:
    """Quais caminhos (relativos a d) o git ignora. Fora de repositório git, ou sem git: nenhum."""
    git = shutil.which("git")
    if not rels or git is None:
        return set()
    try:
        proc = subprocess.run([git, "-C", str(d), "check-ignore", "--stdin"], input="\n".join(rels),
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return set()
    # rc 0 = algum ignorado; 1 = nenhum; 128 = não é repositório (tratado como nenhum)
    return {l.strip() for l in proc.stdout.splitlines() if l.strip()} if proc.returncode == 0 else set()


def is_module(p: Path, src: str) -> bool:
    """Módulo Python importado por outro script: sem __main__, sem argparse e sem bit de execução."""
    return (p.suffix == ".py" and "__main__" not in src and "argparse" not in src
            and not os.access(p, os.X_OK))


def check_files(rep: Report, skill_md: str, args):
    d = rep.path
    norm = own_prefix_normalizer(rep.name)
    md_norm = norm(skill_md)
    ref_dir = d / "references"
    ref_files = sorted(ref_dir.rglob("*.md")) if ref_dir.is_dir() else []
    refs_text = {p.relative_to(ref_dir).as_posix(): read(p, rep, "B1") for p in ref_files}

    for sub, rx in (("references", RE_REF), ("assets", RE_ASSET)):
        folder = d / sub
        cited = set(rx.findall(md_norm))
        existing = {p.relative_to(folder).as_posix() for p in folder.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts} if folder.is_dir() else set()
        if sub == "references":
            existing = {e for e in existing if e.endswith(".md")}
        gone = sorted(cited - existing)
        if gone and folder.is_dir():
            rep.add(ERRO, "B1", f"{sub}/ citado no SKILL.md e ausente: {gone}")
        elif gone:
            rep.add(AVISO, "B1", f"{sub}/ citado mas o diretório não existe (exemplo didático ou skill quebrada?): {gone}")
        orphan = sorted(existing - cited)
        if orphan:
            rep.add(AVISO, "B1", f"{sub}/ órfão (existe e o SKILL.md não cita): {orphan}")

    scr_dir = d / "scripts"
    all_text = norm(skill_md + "\n" + "\n".join(refs_text.values()))
    scr_existing = {p.name for p in scr_dir.iterdir() if p.is_file() and p.suffix != ".pyc"} if scr_dir.is_dir() else set()
    scr_cited = set(RE_SCR.findall(all_text))
    for s in scr_existing:
        if re.search(r"(?<![\w/~.-])" + re.escape(s) + r"(?![A-Za-z0-9._-])", all_text):
            scr_cited.add(s)
    concrete = {s for s in scr_cited - scr_existing if not re.search(r"[<>{}*]", s)}
    if concrete:
        rep.add(AVISO, "B2", f"scripts/ citado e ausente (confira se é exemplo): {sorted(concrete)}")
    if scr_existing - scr_cited:
        rep.add(AVISO, "B2", f"scripts/ órfão (não citado no SKILL.md nem em references): {sorted(scr_existing - scr_cited)}")

    texts = {"SKILL.md": skill_md, **{f"references/{k}": v for k, v in refs_text.items()}}
    for label, text in texts.items():
        esc = escaping(text, label.count("/"))
        if esc:
            rep.add(ERRO, "B3", f"path relativo escapando da skill em {label}: {esc[:5]}")
    code_files = [p for sub in ("scripts", "tests") if (d / sub).is_dir()
                  for p in sorted((d / sub).rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    for p in code_files:
        label = p.relative_to(d).as_posix()
        texts[label] = read(p)
        esc = escaping(texts[label], label.count("/")) if label.startswith("scripts/") else []
        if esc:
            rep.add(AVISO, "B3", f"{label} sobe acima da skill (se a base for o diretório do script): {esc[:5]}")
    # tests/ fica fora do B4: fixtures usam paths de exemplo de propósito.
    machine = sorted(label for label, text in texts.items()
                     if not label.startswith("tests/") and RE_MACHINE.search(text))
    if machine:
        rep.add(AVISO, "B4", f"path absoluto de máquina (/home/<user>, /Users/<user>) em: {machine}")
    hermes = sum(len(RE_HERMES.findall(t)) for t in texts.values())
    if hermes:
        rep.add(INFO, "B4", f"{hermes} menção(ões) a ~/.hermes ou $HERMES_HOME: dependência do harness "
                            "Hermes, legítima só para infra compartilhada documentada")

    # Num plugin de marketplace (<plugin>/skills/<skill>/ com <plugin>/.claude-plugin/plugin.json) o
    # CHANGELOG versionado é o do plugin, e um segundo dentro da skill partiria o histórico em dois.
    # Sem o manifesto, um CHANGELOG solto dois níveis acima não conta.
    plugin = d.parent.parent
    plugin_cl = plugin / "CHANGELOG.md"
    if (d / "CHANGELOG.md").is_file():
        pass
    elif (plugin / ".claude-plugin" / "plugin.json").is_file() and plugin_cl.is_file():
        rep.add(OK, "B5", f"CHANGELOG no nível do plugin: {plugin_cl}")
    else:
        rep.add(INFO if args.no_changelog_required else ERRO, "B5", "CHANGELOG.md ausente")
    junk = sorted(str(p.relative_to(d)) for p in d.rglob("*")
                  if p.name in ("__pycache__", ".DS_Store") or p.suffix == ".pyc")
    ignored = git_ignored(d, junk)
    if [j for j in junk if j not in ignored]:
        rep.add(AVISO, "B6", f"lixo versionável: {[j for j in junk if j not in ignored][:5]}")
    elif junk:
        rep.add(INFO, "B6", f"lixo local ignorado pelo git (não vai para o repositório): {junk[:3]}")

    bash = shutil.which("bash")
    for p in code_files:
        rel = str(p.relative_to(d))
        src = texts[rel]
        if p.suffix == ".py":
            try:
                compile(src, rel, "exec")
            except SyntaxError as e:
                rep.add(ERRO, "B7", f"{rel}: SyntaxError linha {e.lineno}: {e.msg}")
        elif p.suffix in (".sh", ".bash"):
            if bash is None:
                rep.add(SKIP, "B7", f"{rel}: bash indisponível, sintaxe não verificada")
            else:
                try:
                    proc = subprocess.run([bash, "-n", str(p)], capture_output=True, text=True, timeout=30)
                except subprocess.TimeoutExpired:
                    rep.add(AVISO, "B7", f"{rel}: bash -n não terminou em 30s")
                    continue
                if proc.returncode != 0:
                    rep.add(ERRO, "B7", f"{rel}: bash -n falhou: {proc.stderr.strip()[:160]}")
        if rel.startswith("scripts/") and p.suffix in (".py", ".sh", ".bash") and not src.startswith("#!") \
                and not is_module(p, src):
            rep.add(AVISO, "B7", f"{rel}: sem shebang")
    return refs_text


def check_disclosure(rep: Report, skill_md: str, refs_text: dict):
    n_lines = len(skill_md.splitlines())
    if n_lines > MAX_LINES:
        rep.add(ERRO, "C1", f"SKILL.md com {n_lines} linhas > {MAX_LINES} (spec): aplicar progressive disclosure")
    elif n_lines > INFO_LINES:
        rep.add(INFO, "C1", f"SKILL.md com {n_lines} linhas: acima de {INFO_LINES}, considerar re-comprimir")
    if len(skill_md) > WARN_CHARS:
        rep.add(AVISO, "C1", f"SKILL.md com {len(skill_md)} chars > {WARN_CHARS} (heurística local)")
    for name, text in refs_text.items():
        chained = sorted(set(RE_REF.findall(own_prefix_normalizer(rep.name)(text))) - {name})
        if chained:
            rep.add(AVISO, "C2", f"references/{name} cita {chained}: cadeia com mais de 1 nível a partir do SKILL.md")
        n = len(text.splitlines())
        head = "\n".join(text.splitlines()[:40])
        if n > REF_TOC_LINES and not RE_TOC.search(head) and head.count("](#") < 3:
            rep.add(AVISO, "C3", f"references/{name} tem {n} linhas e nenhum sumário no início")


def interactive(suffix: str, src: str) -> bool:
    """Python: chamada real a input()/getpass() pela AST (regex em string não conta). Shell: read -p fora de comentário."""
    if suffix == ".py":
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
                if name in ("input", "getpass"):
                    return True
        return False
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    return bool(RE_INTERACTIVE[suffix].search(code))


def check_practices(rep: Report, skill_md: str):
    """Boas práticas do agentskills.io: sinais para julgamento, nunca reprovam sozinhos."""
    d = rep.path
    body = "\n".join(line for _n, line in outside_code(skill_md))
    vague = []
    lines = body.splitlines()
    for i, line in enumerate(lines):
        cited = RE_REF.findall(own_prefix_normalizer(rep.name)(line))
        # A frase pode começar na linha anterior (parágrafo quebrado).
        context = (lines[i - 1] if i and lines[i - 1].strip() else "") + " " + line
        if cited and not RE_WHEN.search(re.sub(r"`[^`]*`|references/\S+", " ", context)):
            vague.extend(cited)
    if vague:
        rep.add(INFO, "F1", f"reference citada sem dizer quando ler: {sorted(set(vague))[:6]} "
                            "(best practices: 'leia X se/quando Y', não 'veja references/')")
    if not RE_GOTCHAS.search(skill_md):
        rep.add(INFO, "F2", "sem seção de gotchas/armadilhas/erros comuns no SKILL.md "
                            "(best practices: costuma ser o conteúdo de maior valor)")
    scr_dir = d / "scripts"
    scripts = [p for p in sorted(scr_dir.rglob("*")) if p.is_file() and p.suffix in (".py", *RE_INTERACTIVE)
               and "__pycache__" not in p.parts] if scr_dir.is_dir() else []
    for p in scripts:
        rel = p.relative_to(d).as_posix()
        src = read(p)
        if interactive(p.suffix, src):
            rep.add(AVISO, "F3", f"{rel}: prompt interativo (input/getpass/read -p); agente não responde "
                                 "a stdin: usar flag ou variável de ambiente")
        if not RE_HELP.search(src) and not is_module(p, src):
            rep.add(INFO, "F3", f"{rel}: sem --help/usage aparente (using-scripts: --help é a interface do agente)")
    evals = [p for p in (d / "evals" / "evals.json", *sorted((d / "assets").glob("*eval*.json"))) if p.is_file()]
    if not evals:
        rep.add(INFO, "F4", "sem evals (evals/evals.json ou assets/*eval*.json): gatilho e comportamento "
                            "não têm caso de teste")


def check_claims(rep: Report, skill_md: str, refs_text: dict, list_claims: bool):
    files = {"SKILL.md": skill_md, **{f"references/{k}": v for k, v in refs_text.items()}}
    for label, text in files.items():
        for n, line in outside_code(text):
            for kind, pattern, question in CLAIM_PATTERNS:
                if re.search(pattern, line):
                    rep.claims.append({"file": label, "line": n, "kind": kind,
                                       "question": question, "text": line.strip()[:100]})
                    break
    if rep.claims:
        hint = "" if list_claims else " (listar: --claims)"
        rep.add(INFO, "D1", f"{len(rep.claims)} trecho(s) com cara de afirmação factual{hint}: "
                            "cada um precisa de sensor, derivação ou data (skill-claim-check)")


def check_external(rep: Report, args):
    if args.external == "off":
        return
    gate = Path(args.audit_skill_sh) if args.audit_skill_sh else None
    hermes_home = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
    gate = gate or hermes_home / "scripts" / "audit-skill.sh"
    try:
        rel = rep.path.resolve().relative_to((hermes_home / "skills").resolve())
    except ValueError:
        rel = None
    if not gate.is_file():
        rep.add(SKIP, "G1", f"audit-skill.sh indisponível em {gate}: gate local não rodou")
    elif rel is None:
        rep.add(SKIP, "G1", "skill fora de $HERMES_HOME/skills: audit-skill.sh não se aplica")
    else:
        env = dict(os.environ, HERMES_HOME=str(hermes_home))
        try:
            proc = subprocess.run(["bash", str(gate), str(rel)], capture_output=True, text=True, env=env, timeout=120)
        except subprocess.TimeoutExpired:
            proc = None
            rep.add(AVISO, "G1", f"audit-skill.sh {rel} não terminou em 120s")
        if proc is None:
            pass
        elif proc.returncode == 0:
            rep.add(OK, "G1", f"audit-skill.sh {rel} rc=0")
        else:
            tail = " | ".join(l.strip() for l in proc.stdout.splitlines() if l.strip().startswith("-"))[:240]
            rep.add(ERRO, "G1", f"audit-skill.sh {rel} rc={proc.returncode}: {tail}")
    # O repositório oficial instala `skills-ref`; o pacote skills-ref do PyPI instala `agentskills`.
    # Sem nenhum dos dois, `uvx` roda o pacote com versão fixada (using-scripts: pin de versão).
    ref = shutil.which("skills-ref") or shutil.which("agentskills")
    uvx = None if ref or args.no_uvx else shutil.which("uvx")
    if ref is None and uvx is None:
        rep.add(SKIP, "G2", "skills-ref/agentskills indisponível no PATH e sem uvx: vale a validação local A1 a A6")
        return
    cmd = [ref] if ref else [uvx, "-q", "--from", SKILLS_REF_PIN, "agentskills"]
    name = Path(ref).name if ref else f"uvx {SKILLS_REF_PIN}"
    try:
        proc = subprocess.run([*cmd, "validate", str(rep.path)], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        rep.add(AVISO, "G2", f"{name} validate não terminou em 120s")
        return
    level = OK if proc.returncode == 0 else ERRO
    rep.add(level, "G2", f"{name} validate rc={proc.returncode}: {(proc.stdout + proc.stderr).strip()[:240]}")


def check_family(reports: list, found: dict):
    by_name = {r.name: r for r in reports}
    hub = by_name.get(FAMILY[0])
    # Sem bloco metadata o vínculo não tem onde ser declarado (o instalador do Cursor o remove):
    # INFO, porque a irmã segue ligada pelo corpo e pela vizinhança de pastas.
    def e1(rep, msg):
        if rep.has_metadata:
            rep.add(AVISO, "E1", msg)
        else:
            rep.add(INFO, "E1", msg + " (sem bloco metadata: vínculo só pelo corpo do SKILL.md)")
    for name in FAMILY[1:]:
        if name not in found:
            continue
        if hub and name not in hub.related:
            e1(hub, f"related_skills não lista a irmã presente '{name}'")
        member = by_name.get(name)
        if member and FAMILY[0] not in member.related:
            e1(member, f"related_skills não aponta para a porta de entrada '{FAMILY[0]}'")


def audit(path: Path, args, roots) -> Report:
    rep = Report(path)
    md_path = path / "SKILL.md"
    if not md_path.is_file():
        rep.add(ERRO, "A1", "SKILL.md ausente")
        return rep
    text = read(md_path, rep, "A1")
    fm, _body, err = parse_frontmatter(text)
    if err:
        rep.add(ERRO, "A1", err)
    else:
        check_frontmatter(rep, fm, args, [*roots, path.parent, path.parent.parent])
    refs_text = check_files(rep, text, args)
    check_disclosure(rep, text, refs_text)
    check_practices(rep, text)
    check_claims(rep, text, refs_text, args.claims)
    check_external(rep, args)
    return rep


def skills_roots(args):
    roots = [Path(p) for p in args.skills_root] if args.skills_root else [SELF_DIR.parent, SELF_DIR.parent.parent]
    hermes = os.environ.get("HERMES_HOME")
    if not args.skills_root and hermes and (Path(hermes) / "skills").is_dir():
        roots.append(Path(hermes) / "skills")
    return roots


def render_text(reports, skipped, rc, list_claims):
    out = []
    for name, why in skipped:
        out.append(f"[SKIP] E0 membro da família '{name}' {why}")
    for r in reports:
        out.append(f"\n== {r.name} ({r.path}) ==")
        order = {ERRO: 0, AVISO: 1, INFO: 2, SKIP: 3, OK: 4}
        for f in sorted(r.findings, key=lambda f: (order[f["level"]], f["id"])):
            out.append(f"  [{f['level']}] {f['id']} {f['msg']}")
        if list_claims:
            for c in r.claims:
                out.append(f"    {c['file']}:L{c['line']} [{c['kind']}] {c['text']}")
                out.append(f"        -> {c['question']}")
        out.append(f"  resumo: {r.count(ERRO)} erro(s), {r.count(AVISO)} aviso(s), {r.count(INFO)} info, "
                   f"{r.count(SKIP)} skip")
    total_e = sum(r.count(ERRO) for r in reports)
    total_w = sum(r.count(AVISO) for r in reports)
    out.append(f"\n== Resultado: {len(reports)} skill(s) | {total_e} erro(s) | {total_w} aviso(s) | rc={rc} ==")
    return "\n".join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog="audit_skill_quality.py",
        description="Auditoria estrutural somente leitura de Agent Skills (spec, autocontenção, "
                    "progressive disclosure, sinais de afirmação). Nunca escreve e nunca executa "
                    "código da skill auditada.",
        epilog="rc: 0 = sem erro | 1 = erro (ou aviso com --strict) | 2 = uso inválido. "
               "Exemplo: python3 scripts/audit_skill_quality.py ../minha-skill --claims")
    p.add_argument("skill_dirs", nargs="*", metavar="SKILL_DIR", help="diretório de uma skill (contém SKILL.md)")
    p.add_argument("--family", action="store_true",
                   help=f"auditar a família padrão ({', '.join(FAMILY)}); irmã ausente vira [SKIP]")
    p.add_argument("--skills-root", action="append", metavar="DIR",
                   help="onde procurar irmãs e related_skills (repetível). Padrão: pastas acima desta "
                        "skill e $HERMES_HOME/skills, se existir")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--claims", action="store_true", help="listar cada trecho com cara de afirmação factual")
    p.add_argument("--strict", action="store_true", help="aviso também reprova (rc=1)")
    p.add_argument("--desc-budget", type=int, default=60, metavar="N",
                   help="chars que o índice de skills mostra (Hermes: 60); 0 desliga a nota A3")
    p.add_argument("--no-changelog-required", action="store_true",
                   help="CHANGELOG.md ausente vira info (harness sem essa regra)")
    p.add_argument("--external", choices=("auto", "off"), default="auto",
                   help="auto: rodar audit-skill.sh e skills-ref se encontrados; off: não rodar")
    p.add_argument("--no-uvx", action="store_true", default=bool(os.environ.get("SQA_NO_UVX")),
                   help=f"no G2, não usar uvx ({SKILLS_REF_PIN}) quando skills-ref/agentskills não está no "
                        "PATH (padrão também pela variável SQA_NO_UVX)")
    p.add_argument("--audit-skill-sh", metavar="PATH",
                   help="caminho do gate audit-skill.sh (padrão: $HERMES_HOME/scripts/audit-skill.sh)")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.skill_dirs and not args.family:
        parser.print_usage(sys.stderr)
        print("erro: informe SKILL_DIR ou --family", file=sys.stderr)
        return 2
    if args.desc_budget < 0:
        print("erro: --desc-budget precisa ser >= 0", file=sys.stderr)
        return 2
    targets = []
    for raw in args.skill_dirs:
        p = Path(raw).expanduser()
        if not p.is_dir():
            print(f"erro: diretório não encontrado: {raw}", file=sys.stderr)
            return 2
        targets.append(p.resolve())
    roots = skills_roots(args)
    skipped, found = [], {}
    if args.family:
        for name in FAMILY:
            hit = SELF_DIR if name == SELF_DIR.name else find_skill(name, roots)
            if hit is None:
                skipped.append((name, f"não encontrado em {[str(r) for r in roots]}"))
            else:
                found[name] = hit.resolve()
                if hit.resolve() not in targets:
                    targets.append(hit.resolve())
    reports = [audit(t, args, roots) for t in targets]
    if args.family:
        check_family(reports, found)
    failing = sum(r.count(ERRO) for r in reports) + (sum(r.count(AVISO) for r in reports) if args.strict else 0)
    rc = 1 if failing else 0
    if args.format == "json":
        print(json.dumps({
            "skills": [{"name": r.name, "path": str(r.path), "related_skills": r.related,
                        "findings": r.findings, "claims": r.claims} for r in reports],
            "skipped_family": [{"name": n, "reason": w} for n, w in skipped],
            "summary": {"skills": len(reports), "errors": sum(r.count(ERRO) for r in reports),
                        "warnings": sum(r.count(AVISO) for r in reports), "rc": rc},
        }, ensure_ascii=False, indent=2))
    else:
        print(render_text(reports, skipped, rc, args.claims))
    return rc


if __name__ == "__main__":
    sys.exit(main())
