#!/usr/bin/env python3
"""Oráculo do trust do Codex: confere a fixture dourada (e o algoritmo do `install --codex`) contra o
próprio Codex. Rodado à mão a cada versão nova do codex-cli; não entra no `unittest discover`.

    python3 tests/oraculo_codex.py <pasta nova, fora do /tmp> [--fixture <json>]

1. monta em `<pasta>/market` a loja com o pacote dourado da fixture (`arquivos`, inclusive o lixo
   que a impressão do pacote pula);
2. instala o pacote num CODEX_HOME novo, `<pasta>/home`, com `codex plugin marketplace add` e
   `codex plugin add` (só `model` no `config.toml`; nenhuma credencial é lida);
3. pergunta o `hooks/list` ao `codex app-server` e compara o `currentHash` de cada hook de plugin
   com `declaracoes` + `conteudo` da fixture.

Sai 0 quando tudo bate e 1 com o que mudou: aí releia o codex-rs da versão nova, ajuste o algoritmo
(`references/hosts.md` §4) e refaça a fixture. O Codex recusa os binários auxiliares com o
CODEX_HOME sob /tmp, daí a pasta fora dele.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "codex-hooks-list-dourado.json"


def montar_loja(pasta: Path, dourado: dict) -> str:
    plugin, loja = dourado["plugin_id"].split("@")
    raiz = pasta / "market" / "plugins" / plugin
    for rel, texto in dourado["arquivos"].items():
        alvo = raiz / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(texto, encoding="utf-8")
    catalogo = {"name": loja, "interface": {"displayName": loja},
                "plugins": [{"name": plugin, "source": {"source": "local", "path": f"./plugins/{plugin}"},
                             "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                             "category": "development"}]}
    for sub in (".agents/plugins", ".claude-plugin"):
        (pasta / "market" / sub).mkdir(parents=True, exist_ok=True)
        (pasta / "market" / sub / "marketplace.json").write_text(json.dumps(catalogo), encoding="utf-8")
    return str(pasta / "market")


def ambiente(home: Path) -> dict:
    env = {k: os.environ[k] for k in ("HOME", "PATH", "USER", "LANG") if k in os.environ}
    return {**env, "CODEX_HOME": str(home), "TERM": "dumb"}


def codex(home: Path, *args):
    r = subprocess.run(["codex", *args], env=ambiente(home), capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=120)
    if r.returncode != 0:
        raise SystemExit(f"codex {' '.join(args[:3])}: rc {r.returncode}\n{r.stderr[-800:]}")


def hooks_list(home: Path, cwd: Path) -> dict:
    """{key: currentHash} dos hooks de plugin, pelo JSON-RPC por linha do `codex app-server`."""
    proc = subprocess.Popen(["codex", "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, env=ambiente(home), text=True, bufsize=1)

    def enviar(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def esperar(ident, limite=60):
        fim = time.time() + limite
        while time.time() < fim:
            linha = proc.stdout.readline()
            if not linha:
                break
            try:
                msg = json.loads(linha)
            except ValueError:
                continue
            if msg.get("id") == ident:
                return msg
        raise SystemExit(f"codex app-server: sem resposta para o id {ident}")

    try:
        enviar({"method": "initialize", "id": 1, "params": {
            "clientInfo": {"name": "env_docs_sync_oraculo", "title": "oráculo", "version": "0.0.1"},
            "capabilities": {"experimentalApi": True}}})
        esperar(1)
        enviar({"method": "initialized"})
        enviar({"method": "hooks/list", "id": 2, "params": {"cwds": [str(cwd)]}})
        resposta = esperar(2)
    finally:
        proc.stdin.close()
        proc.terminate()
    if "error" in resposta:
        raise SystemExit(f"hooks/list: {json.dumps(resposta['error'])}")
    return {h["key"]: h.get("currentHash") for bloco in resposta["result"]["data"] for h in bloco["hooks"]
            if h.get("source") == "plugin" or h.get("pluginId")}


def main(argv) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    pasta = Path(argv[0]).expanduser().resolve()
    fixture = Path(argv[argv.index("--fixture") + 1]) if "--fixture" in argv else FIXTURE
    if pasta.exists() and any(pasta.iterdir()):
        raise SystemExit(f"{pasta}: precisa ser uma pasta nova ou vazia")
    if str(pasta).startswith("/tmp/"):
        raise SystemExit("o Codex recusa os binários auxiliares com CODEX_HOME sob /tmp; use outra pasta")
    dourado = json.loads(fixture.read_text(encoding="utf-8"))
    home = pasta / "home"
    home.mkdir(parents=True)
    (home / "config.toml").write_text('model = "gpt-5"\n', encoding="utf-8")
    loja = montar_loja(pasta, dourado)
    codex(home, "plugin", "marketplace", "add", loja, "--json")
    codex(home, "plugin", "add", dourado["plugin_id"], "--json")
    vistos = hooks_list(home, pasta)
    esperados = {chave: f"{declaracao}/{dourado['conteudo']}" for chave, declaracao in dourado["declaracoes"].items()}
    diferentes = sorted(k for k in esperados.keys() | vistos.keys() if esperados.get(k) != vistos.get(k))
    versao = subprocess.run(["codex", "--version"], capture_output=True, text=True).stdout.strip()
    for chave in diferentes:
        print(f"DIFERENTE {chave}\n  fixture: {esperados.get(chave)}\n  codex:   {vistos.get(chave)}")
    print(f"{versao}: {len(esperados) - len(diferentes)}/{len(esperados)} hooks iguais à fixture "
          f"({fixture.name}); {len(vistos)} vistos pelo hooks/list")
    return 1 if diferentes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
