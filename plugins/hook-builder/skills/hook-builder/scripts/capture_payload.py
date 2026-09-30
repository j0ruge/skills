#!/usr/bin/env python3
"""Probe hook: grava o payload (stdin) e o ambiente CLAUDE_* reais de um evento.

Dois modos:
  --print-config EVENTO[,EVENTO...] DIR [--matcher M]
      Imprime um JSON de settings pronto para `claude --settings '<json>'`, com um
      hook deste script em cada EVENTO, gravando em DIR.
  --capture DIR
      Modo hook: lê o stdin, grava DIR/stdin-<evento>-<n>.json e DIR/env-<evento>-<n>.txt.
      Sai sempre com exit 0 e stdout vazio, para não interferir na sessão.

Valores de variáveis com TOKEN, SECRET, KEY ou PASSWORD no nome são gravados como <redacted>.
Só biblioteca padrão.
"""
import json
import os
import re
import sys
import time

SENSITIVE = re.compile(r"TOKEN|SECRET|KEY|PASSWORD|SOCKET", re.I)


def print_config(events, out_dir, matcher=None):
    script = os.path.abspath(__file__)
    handler = {"type": "command", "command": sys.executable or "python3",
               "args": [script, "--capture", os.path.abspath(out_dir)], "timeout": 10}
    group = {"hooks": [handler]}
    if matcher:
        group["matcher"] = matcher
    print(json.dumps({"hooks": {event: [group] for event in events.split(",") if event}}))
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
        if key.startswith("CLAUDE"):
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
        return print_config(argv[1], argv[2], matcher)
    if len(argv) == 2 and argv[0] == "--capture":
        try:
            return capture(argv[1])
        except Exception:  # probe nunca derruba a sessão
            return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
