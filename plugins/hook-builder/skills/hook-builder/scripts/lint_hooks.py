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
Codex: evento entre os 14 do config; `args` (o Codex não tem e ignora a chave, então o command roda
sem os argumentos); `if` (ignorado: o hook roda em toda chamada do matcher); type `http` (não
existe lá); `prompt`/`agent` (lidos e pulados); timeout inteiro; chave de topo além de
`description` e `hooks` (o arquivo é recusado); `${CLAUDE_PROJECT_DIR}` (o Codex não define).

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
PLACEHOLDER = re.compile(r"\$\{(CLAUDE_PLUGIN_ROOT|CLAUDE_PLUGIN_DATA|CLAUDE_PROJECT_DIR|PLUGIN_ROOT|PLUGIN_DATA)\}")

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
        self.errors.append(f"ERRO   {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"AVISO  {where}: {msg}")


def unquoted_placeholder(cmd):
    """True se algum placeholder aparece fora de aspas duplas (forma shell)."""
    for match in PLACEHOLDER.finditer(cmd):
        before = cmd[:match.start()]
        if before.count('"') % 2 == 0:
            return True
    return False


def script_paths(handler, plugin_root):
    parts = [handler.get("command", "")] + [a for a in handler.get("args", []) if isinstance(a, str)]
    found = []
    for part in parts:
        for token in re.findall(r"[^\s\"']+", part):
            if "${CLAUDE_PLUGIN_ROOT}" in token and plugin_root:
                path = token.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)
                if os.path.isfile(path):
                    found.append(path)
    return found


def lint_handler(rep, where, event, handler, plugin_root):
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
    if htype == "command" and "args" not in handler and unquoted_placeholder(handler.get("command", "")):
        rep.warn(where, "placeholder sem aspas na forma shell; use aspas duplas ou a forma exec (args)")
    if htype == "command" and "args" in handler and not isinstance(handler["args"], list):
        rep.err(where, "args precisa ser uma lista")
    if htype == "command" and event in {"Stop", "SubagentStop"}:
        for path in script_paths(handler, plugin_root):
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if "stop_hook_active" not in text:
                rep.warn(where, f"{os.path.basename(path)} não menciona stop_hook_active (risco de loop)")


def lint_codex_handler(rep, where, event, handler, plugin_root):
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
    if htype != "command":
        return
    if "args" in handler:
        rep.err(where, "o Codex não tem 'args' e ignora a chave: o command roda sem os argumentos; "
                "use a forma shell com o placeholder entre aspas, que serve aos dois hosts")
    command = handler.get("command", "")
    if "${CLAUDE_PROJECT_DIR}" in command:
        rep.warn(where, "o Codex não define CLAUDE_PROJECT_DIR; lá o comando roda no cwd da sessão")
    if "args" not in handler and unquoted_placeholder(command):
        rep.warn(where, "placeholder sem aspas na forma shell; ponha aspas duplas")
    if event == "Stop":
        for path in script_paths(handler, plugin_root):
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if "stop_hook_active" not in text:
                rep.warn(where, f"{os.path.basename(path)} não menciona stop_hook_active (risco de loop)")


def lint_codex(rep, data, plugin_root):
    extra = sorted(set(data) - CODEX_TOP_KEYS)
    if extra:
        rep.err("codex", f"o hooks.json do Codex só aceita description e hooks no topo (deny_unknown_fields); "
                f"sobra {extra}")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    for event, groups in hooks.items():
        where_event = f"codex:{event}"
        if event not in CODEX_EVENTS:
            rep.err(where_event, "o Codex não tem esse evento (são 14 no config da 0.164.0)")
            continue
        if event in CODEX_UNDOCUMENTED:
            rep.warn(where_event, "evento existe no código do Codex, mas não na doc: pode mudar sem aviso")
        if not isinstance(groups, list):
            continue
        for gi, group in enumerate(groups):
            where = f"{where_event}[{gi}]"
            if not isinstance(group, dict):
                continue
            if group.get("matcher") not in (None, "", "*") and event in CODEX_NO_MATCHER:
                rep.warn(where, f"o Codex ignora o matcher em {event}")
            for hi, handler in enumerate(group.get("hooks") or []):
                lint_codex_handler(rep, f"{where}.hooks[{hi}]", event, handler, plugin_root)


def lint_hooks(rep, hooks, plugin_root):
    if not isinstance(hooks, dict):
        rep.err("hooks", "precisa ser um objeto {Evento: [grupos]}")
        return
    for event, groups in hooks.items():
        if event not in SUPPORTED_TYPES:
            rep.err(event, "evento desconhecido (confira a grafia; são 33 eventos)")
            continue
        if not isinstance(groups, list):
            rep.err(event, "precisa ser uma lista de grupos {matcher, hooks}")
            continue
        for gi, group in enumerate(groups):
            where = f"{event}[{gi}]"
            if not isinstance(group, dict):
                rep.err(where, "grupo precisa ser um objeto")
                continue
            if group.get("matcher") not in (None, "", "*") and event in NO_MATCHER:
                rep.warn(where, f"{event} não tem matcher; o valor {group['matcher']!r} é ignorado")
            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                rep.err(where, "falta a lista 'hooks' com pelo menos um handler")
                continue
            for hi, handler in enumerate(handlers):
                lint_handler(rep, f"{where}.hooks[{hi}]", event, handler, plugin_root)


def lint_plugin_json(rep, path):
    try:
        manifest = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        rep.err(path, f"não li o plugin.json: {exc}")
        return
    value = manifest.get("hooks")
    if isinstance(value, str) and not value.endswith(".json"):
        rep.err("plugin.json", f'"hooks": {value!r} aponta um diretório e quebra `claude plugin install` '
                "(hooks: Invalid input); remova (hooks/hooks.json é descoberto sozinho) ou use o arquivo")
    agents = manifest.get("agents")
    if isinstance(agents, str) and not agents.endswith(".md"):
        rep.err("plugin.json", f'"agents": {agents!r} (diretório) quebra a instalação; use lista de arquivos')


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    path = argv[0]
    plugin_json = argv[argv.index("--plugin-json") + 1] if "--plugin-json" in argv else None
    host = argv[argv.index("--host") + 1] if "--host" in argv and argv.index("--host") + 1 < len(argv) else "claude"
    if host not in {"claude", "codex", "both"}:
        print("ERRO   --host aceita claude, codex ou both", file=sys.stderr)
        return 2
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERRO   {path}: JSON inválido ou ilegível: {exc}")
        return 1
    rep = Report()
    plugin_root = None
    if os.path.basename(os.path.dirname(os.path.abspath(path))) == "hooks":
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    if "hooks" not in data:
        rep.err(path, "sem chave 'hooks' (settings.json e hooks.json usam {\"hooks\": {...}})")
    else:
        if host in {"claude", "both"}:
            lint_hooks(rep, data["hooks"], plugin_root)
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
