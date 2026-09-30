#!/usr/bin/env python3
"""Roda um command hook contra uma fixture JSON e confere exit code e saída.

Uso:
  python3 hook_test.py '<comando do hook>' fixture.json [opções]

Opções:
  --expect-exit N              exit esperado (padrão 0)
  --expect-json-key a.b.c      stdout é JSON e tem essa chave (repetível)
  --expect-json-value a.b=V    stdout é JSON e a chave vale V (string; repetível)
  --expect-no-output           stdout vazio (hook que decide "nada a fazer")
  --expect-stdout-contains S   stdout contém S (repetível)
  --expect-stderr-contains S   stderr contém S (repetível)
  --env K=V                    variável extra no ambiente do hook (repetível)
  --timeout S                  segundos (padrão 30)

O comando roda em shell (`sh -c`), como a forma shell do Claude Code. Os placeholders
${CLAUDE_PLUGIN_ROOT}, ${CLAUDE_PLUGIN_DATA} e ${CLAUDE_PROJECT_DIR} são exportados se vierem
em --env.
Exit: 0 passou, 1 falhou, 2 uso inválido. Só biblioteca padrão.
"""
import json
import os
import subprocess
import sys


def dig(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return False, None
        obj = obj[part]
    return True, obj


def parse_args(argv):
    if len(argv) < 2:
        return None
    opts = {"cmd": argv[0], "fixture": argv[1], "exit": 0, "keys": [], "values": [],
            "no_output": False, "contains": [], "err_contains": [], "env": {}, "timeout": 30}
    i = 2
    try:
        while i < len(argv):
            flag = argv[i]
            if flag == "--expect-exit":
                opts["exit"] = int(argv[i + 1]); i += 2
            elif flag == "--expect-json-key":
                opts["keys"].append(argv[i + 1]); i += 2
            elif flag == "--expect-json-value":
                key, _, val = argv[i + 1].partition("=")
                opts["values"].append((key, val)); i += 2
            elif flag == "--expect-no-output":
                opts["no_output"] = True; i += 1
            elif flag == "--expect-stdout-contains":
                opts["contains"].append(argv[i + 1]); i += 2
            elif flag == "--expect-stderr-contains":
                opts["err_contains"].append(argv[i + 1]); i += 2
            elif flag == "--env":
                key, _, val = argv[i + 1].partition("=")
                opts["env"][key] = val; i += 2
            elif flag == "--timeout":
                opts["timeout"] = float(argv[i + 1]); i += 2
            else:
                return None
    except (IndexError, ValueError):
        return None
    return opts


def main(argv):
    opts = parse_args(argv)
    if opts is None:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        with open(opts["fixture"], encoding="utf-8") as fh:
            payload = fh.read()
        json.loads(payload)
    except (OSError, ValueError) as exc:
        print(f"fixture inválida: {exc}", file=sys.stderr)
        return 2

    env = dict(os.environ, **opts["env"])
    try:
        proc = subprocess.run(["sh", "-c", opts["cmd"]], input=payload, capture_output=True,
                              text=True, env=env, timeout=opts["timeout"])
    except subprocess.TimeoutExpired:
        print(f"FAIL  timeout de {opts['timeout']}s (no Claude Code o hook seria cancelado)")
        return 1

    failures = []
    out, err = proc.stdout.strip(), proc.stderr
    if proc.returncode != opts["exit"]:
        failures.append(f"exit {proc.returncode}, esperado {opts['exit']}")
    if opts["no_output"] and out:
        failures.append(f"stdout deveria estar vazio: {out[:200]!r}")
    parsed = None
    if opts["keys"] or opts["values"]:
        if not (out.startswith("{") and out.endswith("}")):
            failures.append("stdout não é um objeto JSON (precisa começar com { e terminar com })")
        else:
            try:
                parsed = json.loads(out)
            except ValueError as exc:
                failures.append(f"stdout não parseia como JSON: {exc}")
    if parsed is not None:
        for key in opts["keys"]:
            if not dig(parsed, key)[0]:
                failures.append(f"chave ausente no JSON: {key}")
        for key, val in opts["values"]:
            found, got = dig(parsed, key)
            if not found or str(got) != val:
                failures.append(f"{key} = {got!r}, esperado {val!r}")
    for text in opts["contains"]:
        if text not in proc.stdout:
            failures.append(f"stdout não contém {text!r}")
    for text in opts["err_contains"]:
        if text not in err:
            failures.append(f"stderr não contém {text!r}")

    label = os.path.basename(opts["fixture"])
    if failures:
        print(f"FAIL  {label}")
        for item in failures:
            print(f"      - {item}")
        if err.strip():
            print(f"      stderr: {err.strip()[:400]}")
        return 1
    print(f"PASS  {label}  (exit {proc.returncode}, stdout {len(out)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
