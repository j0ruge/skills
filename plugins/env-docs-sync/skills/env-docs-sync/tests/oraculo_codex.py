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
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "codex-hooks-list-dourado.json"


def montar_loja(pasta: Path, dourado: dict) -> str:
    """Monta em `<pasta>/market` a loja com o pacote dourado da fixture; devolve o caminho da loja."""
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
    """O ambiente mínimo do codex: só HOME, PATH, USER e LANG, com o CODEX_HOME descartável."""
    env = {k: os.environ[k] for k in ("HOME", "PATH", "USER", "LANG") if k in os.environ}
    return {**env, "CODEX_HOME": str(home), "TERM": "dumb"}


def codex(home: Path, *args):
    """Roda um subcomando do codex no CODEX_HOME descartável; rc != 0 encerra com o fim do stderr."""
    r = subprocess.run(["codex", *args], env=ambiente(home), capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=120)
    if r.returncode != 0:
        raise SystemExit(f"codex {' '.join(args[:3])}: rc {r.returncode}\n{r.stderr[-800:]}")


def hooks_list(home: Path, cwd: Path) -> dict:
    """{key: currentHash} dos hooks de plugin, pelo JSON-RPC por linha do `codex app-server`."""
    proc = subprocess.Popen(["codex", "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, env=ambiente(home), text=True, bufsize=1)

    # Uma linha por vez numa fila: o readline sozinho bloquearia sem prazo num app-server que não
    # responde, que é justamente o que uma versão nova do Codex pode fazer.
    linhas = queue.Queue()

    def ler():
        for linha in proc.stdout:
            linhas.put(linha)
        linhas.put(None)

    threading.Thread(target=ler, daemon=True).start()

    def enviar(obj):
        """Manda uma mensagem JSON-RPC, uma por linha."""
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def esperar(ident, limite=60):
        """A resposta com este id, ou SystemExit quando o prazo acaba ou o app-server sai."""
        fim = time.time() + limite
        while (restante := fim - time.time()) > 0:
            try:
                linha = linhas.get(timeout=restante)
            except queue.Empty:
                break
            if linha is None:
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
        try:
            proc.stdin.close()
        except OSError:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    if "error" in resposta:
        raise SystemExit(f"hooks/list: {json.dumps(resposta['error'])}")
    return {h["key"]: h.get("currentHash") for bloco in resposta["result"]["data"] for h in bloco["hooks"]
            if h.get("source") == "plugin" or h.get("pluginId")}


def main(argv) -> int:
    """Monta, instala e compara; 0 quando todo hook da fixture bate com o `hooks/list`, 1 senão."""
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
    r = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=30)
    versao = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "codex-cli de versão desconhecida"
    for chave in diferentes:
        print(f"DIFERENTE {chave}\n  fixture: {esperados.get(chave)}\n  codex:   {vistos.get(chave)}")
    print(f"{versao}: {len(esperados) - len(diferentes)}/{len(esperados)} hooks iguais à fixture "
          f"({fixture.name}); {len(vistos)} vistos pelo hooks/list")
    if not esperados or not vistos:
        # 0/0 não confere nada: fixture sem hook ou um hooks/list que não mostra hook de plugin
        print(f"nada comparado: a fixture declara {len(esperados)} hook(s) e o hooks/list mostrou {len(vistos)}")
        return 1
    return 1 if diferentes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
