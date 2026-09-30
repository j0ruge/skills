#!/usr/bin/env python3
"""TEMPLATE de command hook do Claude Code (só biblioteca padrão).

Troque os pontos marcados com AJUSTE. Contrato:
- entrada: um JSON no stdin (campos comuns + campos do evento);
- saída: exit code e, opcionalmente, UM objeto JSON no stdout;
- stderr com exit 0 só vai para o debug log.

Duas políticas de falha (escolha uma em FAIL_CLOSED):
- hook de conveniência (lembrete, contexto, métrica): exceção → exit 0, nada no stdout.
- hook de política (gate): exceção → exit 2, com o motivo no stderr (a ação é bloqueada).
"""
import json
import os
import sys
import tempfile

FAIL_CLOSED = False  # AJUSTE: True só para gate de política
DATA_DIR = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser("~/.claude/hook-data/AJUSTE-nome")


def emit(obj):
    """Escreve o único objeto JSON do stdout."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))


def add_context(event, text):
    """Informação para o Claude (SessionStart, UserPrompt*, Pre/PostToolUse*, Stop...)."""
    emit({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}})


def save_json(path, obj):
    """Grava estado de forma atômica (temporário + os.replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


def handle(payload):
    event = payload.get("hook_event_name")

    if event == "Stop" and payload.get("stop_hook_active"):
        return 0  # já estamos numa continuação pedida por um Stop hook: não peça de novo

    # AJUSTE: filtro barato primeiro (saia com 0 e sem saída quando não há o que fazer).
    # AJUSTE: lógica do hook. Exemplos de saída:
    #   add_context(event, "O alvo de deploy desta pasta é staging.")
    #   emit({"systemMessage": "aviso para o usuário (o Claude não vê)"})
    #   sys.stderr.write("motivo do bloqueio\n"); return 2        # bloquear (eventos que bloqueiam)
    return 0


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        return handle(payload)
    except Exception as exc:  # noqa: BLE001 — a política de falha decide
        if FAIL_CLOSED:
            sys.stderr.write(f"hook falhou e bloqueou por segurança: {exc}\n")
            return 2
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(os.path.join(DATA_DIR, "errors.log"), "a", encoding="utf-8") as fh:
                fh.write(f"{type(exc).__name__}: {exc}\n")
        except OSError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
