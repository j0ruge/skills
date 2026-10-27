#!/usr/bin/env python3
"""Probe hook: grava o payload (stdin) e o ambiente reais de um evento (Claude Code ou Codex CLI).

Dois modos:
  --print-config EVENTO[,EVENTO...] DIR [--matcher M] [--host codex]
      Imprime um JSON de settings pronto para `claude --settings '<json>'`, com um
      hook deste script em cada EVENTO, gravando em DIR. Com --host codex, imprime um
      hooks.json do Codex (forma shell POSIX, porque o Codex não tem `args`) para gravar em
      $CODEX_HOME/hooks.json. No Windows, o Codex usa `commandWindows`, que este modo não gera.
  --capture DIR
      Modo hook: lê o stdin, grava DIR/stdin-<evento>-<n>.json e DIR/env-<evento>-<n>.txt
      (arquivos 0600; o DIR que ele cria sai 0700, e um DIR que já existe fica como está).
      Sai sempre com exit 0 e stdout vazio, para não interferir na sessão; uma falha vai para o
      stderr, que aparece no debug log do host.

Grava as variáveis CLAUDE*, CODEX* e PLUGIN_*. Valores de variáveis com TOKEN, SECRET, KEY,
PASSW, PASSPHRASE, AUTH, CRED, COOKIE, PRIVATE ou SOCKET no nome são gravados como <redacted>. Num Codex
lançado de dentro do Claude Code, as CLAUDE* vêm herdadas do processo pai: não leia como se o
Codex as definisse.

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

SENSITIVE = re.compile(r"TOKEN|SECRET|KEY|PASSW|PASSPHRASE|AUTH|CRED|COOKIE|PRIVATE|SOCKET", re.I)


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


def write_private(path, text):
    """O stdin cru pode trazer o conteúdo de um arquivo editado: só o dono lê."""
    # O_EXCL: o nome é único por chamada, e um symlink plantado nele faz a escrita falhar.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)


def capture(out_dir):
    raw = sys.stdin.read()
    try:
        event = json.loads(raw).get("hook_event_name", "unknown")
    except (ValueError, AttributeError):
        event = "unparsed"
    event = re.sub(r"[^A-Za-z0-9_-]", "_", str(event))
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    stamp = f"{int(time.time() * 1000)}-{os.getpid()}"
    write_private(os.path.join(out_dir, f"stdin-{event}-{stamp}.json"), raw)
    lines = []
    for key in sorted(os.environ):
        if key.startswith(("CLAUDE", "CODEX", "PLUGIN_")):
            value = "<redacted>" if SENSITIVE.search(key) else os.environ[key]
            lines.append(f"{key}={value}")
    write_private(os.path.join(out_dir, f"env-{event}-{stamp}.txt"), "\n".join(lines) + "\n")
    return 0


def option(argv, name, default):
    """Valor depois de `name`; None quando a opção veio sem valor (uso inválido)."""
    if name not in argv:
        return default
    i = argv.index(name) + 1
    return argv[i] if i < len(argv) and not argv[i].startswith("--") else None


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if len(argv) >= 3 and argv[0] == "--print-config":
        matcher = option(argv, "--matcher", "")
        host = option(argv, "--host", "claude")
        if matcher is None:
            print("--matcher pede um valor", file=sys.stderr)
            return 2
        if host not in ("claude", "codex"):
            print("--host aceita claude ou codex", file=sys.stderr)
            return 2
        return print_config(argv[1], argv[2], matcher, host)
    if len(argv) == 2 and argv[0] == "--capture":
        try:
            return capture(argv[1])
        except Exception as exc:  # probe nunca derruba a sessão, mas não falha calado
            print(f"capture_payload: captura falhou: {exc!r}", file=sys.stderr)
            return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
