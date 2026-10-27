#!/usr/bin/env python3
"""Probe hook: grava o payload (stdin) e o ambiente reais de um evento (Claude Code ou Codex CLI).

Dois modos:
  --print-config EVENTO[,EVENTO...] DIR [--matcher M] [--host codex]
      Imprime um JSON de settings pronto para `claude --settings '<json>'`, com um
      hook deste script em cada EVENTO, gravando em DIR. Com --host codex, imprime um
      hooks.json do Codex (forma shell, porque o Codex não tem `args`) para gravar em
      $CODEX_HOME/hooks.json.
  --capture DIR
      Modo hook: lê o stdin, grava DIR/stdin-<evento>-<n>.json e DIR/env-<evento>-<n>.txt.
      Sai sempre com exit 0 e stdout vazio, para não interferir na sessão.

Grava as variáveis CLAUDE*, CODEX* e PLUGIN_*. Valores de variáveis com TOKEN, SECRET, KEY ou
PASSWORD no nome são gravados como <redacted>. Num Codex lançado de dentro do Claude Code, as
CLAUDE* vêm herdadas do processo pai: não leia como se o Codex as definisse.

O stdin é gravado CRU. O PostToolUse de Write/Edit traz o conteúdo do arquivo (tool_input.content,
tool_response.originalFile) e o apply_patch do Codex traz as linhas do patch: capture só com
arquivo sintético, nunca com um .env ou chave de verdade.
Só biblioteca padrão.
"""
import json
import os
import re
import shlex
import sys
import time

SENSITIVE = re.compile(r"TOKEN|SECRET|KEY|PASSWORD|SOCKET", re.I)


def print_config(events, out_dir, matcher=None, host="claude"):
    script = os.path.abspath(__file__)
    python = sys.executable or "python3"
    if host == "codex":
        command = " ".join(shlex.quote(part) for part in
                           (python, script, "--capture", os.path.abspath(out_dir)))
        handler = {"type": "command", "command": command, "timeout": 10}
    else:
        handler = {"type": "command", "command": python,
                   "args": [script, "--capture", os.path.abspath(out_dir)], "timeout": 10}
    group = {"hooks": [handler]}
    if matcher:
        group["matcher"] = matcher
    config = {"hooks": {event: [group] for event in events.split(",") if event}}
    if host == "codex":
        config = {"description": "hook-builder probe", **config}
    print(json.dumps(config))
    return 0


def capture(out_dir):
    raw = sys.stdin.read()
    try:
        event = json.loads(raw).get("hook_event_name", "unknown")
    except (ValueError, AttributeError):
        event = "unparsed"
    os.makedirs(out_dir, exist_ok=True)
    stamp = f"{int(time.time() * 1000)}-{os.getpid()}"
    with open(os.path.join(out_dir, f"stdin-{event}-{stamp}.json"), "w", encoding="utf-8") as fh:
        fh.write(raw)
    lines = []
    for key in sorted(os.environ):
        if key.startswith(("CLAUDE", "CODEX", "PLUGIN_")):
            value = "<redacted>" if SENSITIVE.search(key) else os.environ[key]
            lines.append(f"{key}={value}")
    with open(os.path.join(out_dir, f"env-{event}-{stamp}.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if len(argv) >= 3 and argv[0] == "--print-config":
        matcher = argv[argv.index("--matcher") + 1] if "--matcher" in argv else None
        host = (argv[argv.index("--host") + 1] if "--host" in argv[:-1] else
                "" if "--host" in argv else "claude")
        if host not in ("claude", "codex"):
            print("--host aceita claude ou codex", file=sys.stderr)
            return 2
        return print_config(argv[1], argv[2], matcher, host)
    if len(argv) == 2 and argv[0] == "--capture":
        try:
            return capture(argv[1])
        except Exception:  # probe nunca derruba a sessão
            return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
