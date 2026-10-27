#!/usr/bin/env python3
"""Valida a configuração de hooks do Claude Code (e do Codex CLI) contra a referência oficial.

Uso:
  python3 lint_hooks.py <hooks.json|settings.json> [--plugin-json <plugin.json>] [--host claude|codex|both]

Aceita o hooks.json de plugin ({"description", "hooks": {...}}) e o settings.json
(chave "hooks"). Com --plugin-json, também confere o manifesto do plugin.

Checa: evento existe; tipo de handler suportado no evento; campos obrigatórios por tipo;
matcher em evento sem suporte (ignorado em silêncio); `if` fora de evento de ferramenta
(o hook nunca roda); `once` fora de frontmatter de skill (ignorado); placeholder sem aspas na
forma shell; Stop/SubagentStop sem guarda de `stop_hook_active` no script referenciado;
`"hooks": "./hooks"` (diretório) no plugin.json, que quebra `claude plugin install`.

Com --host codex (ou both, para um hooks.json que serve aos dois), também confere o contrato do
Codex: evento entre os do config (CODEX_EVENTS); `args` (o Codex não tem e ignora a chave, então o
command roda sem os argumentos); `if` (ignorado: o hook roda em toda chamada do matcher); type
`http` (não existe lá); `prompt`/`agent` (lidos e pulados); timeout inteiro; chave de topo além de
`description` e `hooks` (o arquivo é recusado); `${CLAUDE_PROJECT_DIR}` e `CLAUDE_PLUGIN_OPTION_*`
(o Codex não define); `once` (ignorado).

Fonte: https://code.claude.com/docs/en/hooks (lido em 2026-09-30, Claude Code 2.1.283) e, para o
Codex, codex-rs/config/src/hook_config.rs e hooks/src/engine/discovery.rs na tag rust-v0.164.0.
Exit: 0 sem erro (avisos permitidos), 1 com erro, 2 uso inválido. Só biblioteca padrão.
"""
import json
import os
import re
import sys

ALL_TYPES = {"command", "http", "mcp_tool", "prompt", "agent"}
EVENTS_ALL_TYPES = {
    "PermissionDenied", "PostToolBatch", "PostToolUse", "PostToolUseFailure", "PreToolUse",
    "Stop", "SubagentStop", "TaskCompleted", "TaskCreated", "TeammateIdle",
    "UserPromptExpansion", "UserPromptSubmit",
}
EVENTS_NO_MODEL = {
    "ConfigChange", "CwdChanged", "DirectoryAdded", "Elicitation", "ElicitationResult",
    "FileChanged", "InstructionsLoaded", "MessageDisplay", "Notification", "PostCompact",
    "PostModelSwitch", "PreCompact", "PreModelSwitch", "SessionEnd", "StopFailure",
    "SubagentStart", "WorktreeCreate", "WorktreeRemove",
}
SUPPORTED_TYPES = {e: ALL_TYPES for e in EVENTS_ALL_TYPES}
SUPPORTED_TYPES.update({e: {"command", "http", "mcp_tool"} for e in EVENTS_NO_MODEL})
SUPPORTED_TYPES["PermissionRequest"] = {"command", "http", "mcp_tool", "prompt"}
SUPPORTED_TYPES["SessionStart"] = {"command", "mcp_tool"}
SUPPORTED_TYPES["Setup"] = {"command", "mcp_tool"}

NO_MATCHER = {
    "UserPromptSubmit", "PostToolBatch", "Stop", "TeammateIdle", "TaskCreated", "TaskCompleted",
    "WorktreeCreate", "WorktreeRemove", "MessageDisplay", "CwdChanged",
}
TOOL_EVENTS = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest",
               "PermissionDenied"}
REQUIRED = {"command": "command", "http": "url", "mcp_tool": "tool", "prompt": "prompt",
            "agent": "prompt"}
PLACEHOLDER = re.compile(
    r"\$\{(CLAUDE_PLUGIN_ROOT|CLAUDE_PLUGIN_DATA|CLAUDE_PROJECT_DIR|PLUGIN_ROOT|PLUGIN_DATA)\}")
# O Codex substitui as duas formas na string do command (hooks/src/engine/discovery.rs).
ROOT_PLACEHOLDERS = ("${CLAUDE_PLUGIN_ROOT}", "${PLUGIN_ROOT}")
STOP_EVENTS = {"Stop", "SubagentStop"}
# Token de path num command: corta em espaço, aspas, `=` de flag e operadores de shell.
PATH_TOKEN = re.compile(r"[^\s\"'=;&|()]+")

# Codex CLI 0.164.0: HookEventsToml, MatcherGroup e HookHandlerConfig em
# codex-rs/config/src/hook_config.rs (tag rust-v0.164.0).
CODEX_EVENTS = {
    "PreModelRequest", "PostModelRequest", "PreToolUse", "PermissionRequest", "PostToolUse",
    "PreCompact", "PostCompact", "SessionStart", "SessionEnd", "UserPromptSubmit",
    "SubagentStart", "SubagentStop", "Stop", "Interrupt",
}
CODEX_UNDOCUMENTED = {"PreModelRequest", "PostModelRequest"}
CODEX_NO_MATCHER = {"UserPromptSubmit", "Stop", "Interrupt"}
CODEX_TOP_KEYS = {"description", "hooks"}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self._add(self.errors, f"ERRO   {where}: {msg}")

    def warn(self, where, msg):
        self._add(self.warnings, f"AVISO  {where}: {msg}")

    @staticmethod
    def _add(lines, line):
        # Com --host both, a forma e a guarda de Stop são conferidas pelos dois hosts.
        if line not in lines:
            lines.append(line)


def unquoted_placeholder(cmd):
    """True se algum placeholder aparece fora de aspas duplas (forma shell)."""
    for match in PLACEHOLDER.finditer(cmd):
        before = cmd[:match.start()]
        if before.count('"') % 2 == 0:
            return True
    return False


def script_paths(handler, plugin_root):
    """Paths do plugin no handler: (arquivos achados, paths que não existem, citou o placeholder)."""
    command, args = handler.get("command"), handler.get("args")
    parts = [command] if isinstance(command, str) else []
    if isinstance(args, list):
        parts += [a for a in args if isinstance(a, str)]
    found, missing, cited = [], [], False
    for part in parts:
        for token in PATH_TOKEN.findall(part):
            root = next((r for r in ROOT_PLACEHOLDERS if token.startswith(r)), None)
            if root is None:
                continue
            cited = True
            if plugin_root:
                path = token.replace(root, plugin_root, 1)
                if os.path.isfile(path):
                    found.append(path)
                elif not os.path.isdir(path):
                    missing.append(path)
    return found, missing, cited


def check_placeholder(rep, where, handler, exec_ok):
    command = handler.get("command")
    if "args" not in handler and isinstance(command, str) and unquoted_placeholder(command):
        hint = "use aspas duplas ou a forma exec (args)" if exec_ok else "ponha aspas duplas"
        rep.warn(where, f"placeholder sem aspas na forma shell; {hint}")


def check_stop_guard(rep, where, event, handler, plugin_root):
    if event not in STOP_EVENTS:
        return
    found, missing, cited = script_paths(handler, plugin_root)
    if cited and not plugin_root:
        rep.warn(where, "guarda de stop_hook_active não conferida: o placeholder só resolve com o "
                 "lint rodando no hooks/hooks.json do plugin")
    for path in found:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError as exc:
            rep.warn(where, f"não li {os.path.basename(path)} ({exc.strerror}): guarda de "
                     "stop_hook_active não conferida")
            continue
        if "stop_hook_active" not in text:
            rep.warn(where, f"{os.path.basename(path)} não menciona stop_hook_active (risco de loop)")
    for path in missing:
        rep.warn(where, f"{path} não existe: guarda de stop_hook_active não conferida")


def each_group(rep, event, groups):
    """Acusa a forma errada de um evento, igual nos dois hosts, e devolve os grupos bons."""
    if not isinstance(groups, list):
        rep.err(event, "precisa ser uma lista de grupos {matcher, hooks}")
        return
    for gi, group in enumerate(groups):
        where = f"{event}[{gi}]"
        if not isinstance(group, dict):
            rep.err(where, "grupo precisa ser um objeto")
            continue
        handlers = group.get("hooks")
        if not isinstance(handlers, list) or not handlers:
            rep.err(where, "falta a lista 'hooks' com pelo menos um handler")
            continue
        yield where, group, handlers


def lint_handler(rep, where, event, handler, plugin_root, exec_ok=True):
    if not isinstance(handler, dict):
        rep.err(where, "handler precisa ser um objeto")
        return
    htype = handler.get("type")
    if htype not in ALL_TYPES:
        rep.err(where, f"type {htype!r} inválido (use {sorted(ALL_TYPES)})")
        return
    allowed = SUPPORTED_TYPES.get(event, set())
    if htype not in allowed:
        rep.err(where, f"type {htype!r} não é suportado em {event} (aceita {sorted(allowed)})")
    field = REQUIRED[htype]
    if not handler.get(field):
        rep.err(where, f"type {htype!r} exige o campo {field!r}")
    if "if" in handler and event not in TOOL_EVENTS:
        rep.err(where, f"'if' só vale em eventos de ferramenta; em {event} o hook nunca roda")
    if handler.get("once"):
        rep.warn(where, "'once' só é respeitado em frontmatter de skill; aqui é ignorado")
    if "timeout" in handler and not isinstance(handler["timeout"], (int, float)):
        rep.err(where, "timeout precisa ser número (segundos)")
    if htype != "command":
        return
    command = handler.get("command")
    if command and not isinstance(command, str):
        rep.err(where, "command precisa ser texto")
    if "args" in handler and not isinstance(handler["args"], list):
        rep.err(where, "args precisa ser uma lista")
        return
    if not isinstance(command, str):
        return
    check_placeholder(rep, where, handler, exec_ok)
    check_stop_guard(rep, where, event, handler, plugin_root)


def lint_codex_handler(rep, where, event, handler, plugin_root):
    # O que vale nos dois hosts vai sem o prefixo, para o --host both imprimir uma vez só.
    neutral = where[len("codex:"):]
    if not isinstance(handler, dict):
        rep.err(where, "handler precisa ser um objeto")
        return
    htype = handler.get("type")
    if htype not in {"command", "mcp_tool", "prompt", "agent"}:
        rep.err(where, f"o Codex não conhece type {htype!r} (aceita command, mcp_tool, prompt, agent)")
        return
    if htype in {"prompt", "agent"}:
        rep.warn(where, f"o Codex lê o handler {htype!r} e pula: ele nunca roda lá")
        return
    if htype == "mcp_tool":
        for field in ("server", "tool"):
            if not handler.get(field):
                rep.err(where, f"no Codex, mcp_tool exige {field!r}")
    if "timeout" in handler and (isinstance(handler["timeout"], bool)
                                 or not isinstance(handler["timeout"], int)):
        rep.err(where, "no Codex, timeout é inteiro em segundos")
    if "if" in handler:
        rep.warn(where, "o Codex ignora 'if': o hook roda em toda chamada que casar o matcher")
    if handler.get("once"):
        rep.warn(neutral, "'once' só é respeitado em frontmatter de skill; aqui é ignorado")
    if htype != "command":
        return
    if "args" in handler:
        rep.err(where, "o Codex não tem 'args' e ignora a chave: o command roda sem os argumentos; "
                "use a forma shell com o placeholder entre aspas, que serve aos dois hosts")
    command = handler.get("command")
    if not command:
        rep.err(neutral, "type 'command' exige o campo 'command'")
        return
    if not isinstance(command, str):
        rep.err(neutral, "command precisa ser texto")
        return
    if "${CLAUDE_PROJECT_DIR}" in command:
        rep.warn(where, "o Codex não define CLAUDE_PROJECT_DIR; lá o comando roda no cwd da sessão")
    if "CLAUDE_PLUGIN_OPTION_" in command:
        rep.warn(where, "o Codex não define CLAUDE_PLUGIN_OPTION_*; lá a variável chega vazia")
    check_placeholder(rep, neutral, handler, exec_ok=False)
    # SubagentStop também traz stop_hook_active no Codex
    # (hooks/schema/generated/subagent-stop.command.input.schema.json, rust-v0.164.0).
    check_stop_guard(rep, neutral, event, handler, plugin_root)


def lint_codex(rep, data, plugin_root):
    extra = sorted(set(data) - CODEX_TOP_KEYS)
    if extra:
        rep.err("codex", f"o hooks.json do Codex só aceita description e hooks no topo (deny_unknown_fields); "
                f"sobra {extra}")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        rep.err("hooks", "precisa ser um objeto {Evento: [grupos]}")
        return
    for event, groups in hooks.items():
        if event not in CODEX_EVENTS:
            rep.err(f"codex:{event}", f"o Codex não tem esse evento (são {len(CODEX_EVENTS)} no config "
                    "da 0.164.0)")
            continue
        if event in CODEX_UNDOCUMENTED:
            rep.warn(f"codex:{event}",
                     "evento existe no código do Codex, mas não na doc: pode mudar sem aviso")
        for where, group, handlers in each_group(rep, event, groups):
            if group.get("matcher") not in (None, "", "*") and event in CODEX_NO_MATCHER:
                rep.warn(f"codex:{where}", f"o Codex ignora o matcher em {event}")
            for hi, handler in enumerate(handlers):
                lint_codex_handler(rep, f"codex:{where}.hooks[{hi}]", event, handler, plugin_root)


def lint_hooks(rep, hooks, plugin_root, exec_ok=True):
    if not isinstance(hooks, dict):
        rep.err("hooks", "precisa ser um objeto {Evento: [grupos]}")
        return
    for event, groups in hooks.items():
        if event not in SUPPORTED_TYPES:
            rep.err(event, f"evento desconhecido (confira a grafia; são {len(SUPPORTED_TYPES)} eventos)")
            continue
        for where, group, handlers in each_group(rep, event, groups):
            if group.get("matcher") not in (None, "", "*") and event in NO_MATCHER:
                rep.warn(where, f"{event} não tem matcher; o valor {group['matcher']!r} é ignorado")
            for hi, handler in enumerate(handlers):
                lint_handler(rep, f"{where}.hooks[{hi}]", event, handler, plugin_root, exec_ok)


def lint_plugin_json(rep, path):
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError) as exc:
        rep.err(path, f"não li o plugin.json: {exc}")
        return
    if not isinstance(manifest, dict):
        rep.err("plugin.json", "precisa ser um objeto JSON")
        return
    value = manifest.get("hooks")
    if isinstance(value, str) and not value.endswith(".json"):
        rep.err("plugin.json", f'"hooks": {value!r} aponta um diretório e quebra `claude plugin install` '
                "(hooks: Invalid input); remova (hooks/hooks.json é descoberto sozinho) ou use o arquivo")
    agents = manifest.get("agents")
    if isinstance(agents, str) and not agents.endswith(".md"):
        rep.err("plugin.json", f'"agents": {agents!r} (diretório) quebra a instalação; use lista de arquivos')


def option(argv, name, default):
    """Valor depois de `name`; None quando a opção veio sem valor (uso inválido)."""
    if name not in argv:
        return default
    i = argv.index(name) + 1
    return argv[i] if i < len(argv) and not argv[i].startswith("--") else None


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    path = argv[0]
    plugin_json = option(argv, "--plugin-json", "")
    host = option(argv, "--host", "claude")
    if None in (plugin_json, host):
        print("ERRO   --plugin-json e --host pedem um valor", file=sys.stderr)
        return 2
    if host not in {"claude", "codex", "both"}:
        print("ERRO   --host aceita claude, codex ou both", file=sys.stderr)
        return 2
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"ERRO   {path}: JSON inválido ou ilegível: {exc}")
        return 1
    if not isinstance(data, dict):
        print(f"ERRO   {path}: precisa ser um objeto JSON com a chave 'hooks'")
        return 1
    rep = Report()
    plugin_root = None
    if os.path.basename(os.path.dirname(os.path.abspath(path))) == "hooks":
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    if "hooks" not in data:
        rep.err(path, "sem chave 'hooks' (settings.json e hooks.json usam {\"hooks\": {...}})")
    else:
        if host in {"claude", "both"}:
            lint_hooks(rep, data["hooks"], plugin_root, exec_ok=host == "claude")
        if host in {"codex", "both"}:
            lint_codex(rep, data, plugin_root)
    if plugin_json:
        lint_plugin_json(rep, plugin_json)
    for line in rep.errors + rep.warnings:
        print(line)
    print(f"{len(rep.errors)} erro(s), {len(rep.warnings)} aviso(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
