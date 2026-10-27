"""Apoio comum dos testes: caminhos do pacote, o script como módulo e a CLI por subprocesso."""
import copy
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TESTES = Path(__file__).resolve().parent
SKILL = TESTES.parent
PLUGIN = SKILL.parent.parent
SCRIPT = SKILL / "scripts" / "env_docs_sync.py"
EXEMPLO = SKILL / "assets" / "env-docs.example.json"
TEMPLATE = SKILL / "assets" / "ambientes-template.html"

# Valor sintético que faz o papel de segredo: pode chegar ao destino, nunca a stdout, stderr ou estado.
CANARIO = "CANARIO_7c1d"
QUANDO = datetime(2026, 10, 27, 14, 5, tzinfo=timezone(timedelta(hours=-3)))
QUANDO_ISO = "2026-10-27T14:05:00-03:00"

sys.path.insert(0, str(SCRIPT.parent))
import env_docs_sync as eds  # noqa: E402


def config_exemplo():
    return copy.deepcopy(json.loads(EXEMPLO.read_text(encoding="utf-8")))


def criar_arvore(raiz, arquivos):
    for rel, dados in arquivos.items():
        alvo = Path(raiz) / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(dados, str):
            dados = dados.encode("utf-8")
        alvo.write_bytes(dados)


def rodar_cli(*args, cwd=None):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


FIXTURES = TESTES / "fixtures"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"
RAIZ_DAS_FIXTURES = "/home/user/my-project"
MAQUINA = "estacao-teste"


def git(raiz, *args):
    return subprocess.run(["git", "-C", str(raiz), *map(str, args)], capture_output=True, text=True, check=True)


def criar_repo(raiz, arquivos, *, config=None):
    """Repo git real com um commit, os arquivos dados e, se `config` vier, a `.env-docs.json`."""
    Path(raiz).mkdir(parents=True, exist_ok=True)
    git(raiz, "init", "-q", "-b", "main")
    criar_arvore(raiz, {"app.txt": "texto qualquer\n", **arquivos})
    git(raiz, "add", "app.txt")
    git(raiz, "-c", "user.name=teste", "-c", "user.email=teste@example.invalid", "commit", "-q", "-m", "init")
    if config is not None:
        (Path(raiz) / ".env-docs.json").write_text(json.dumps(config), encoding="utf-8")
    return Path(raiz)


def config_so_development(maquina=MAQUINA):
    """O exemplo sem os ambientes remotos (sem ssh) e com a máquina dada."""
    cfg = config_exemplo()
    del cfg["environments"]["staging"], cfg["environments"]["production"], cfg["remote_check_every"]
    cfg["environments"]["development"]["machine"] = maquina
    return cfg


def fixture(nome, raiz=None, **trocas):
    """O payload capturado, com a raiz anonimizada trocada pela raiz real do teste e campos trocados."""
    texto = (FIXTURES / nome).read_text(encoding="utf-8")
    if raiz is not None:
        texto = texto.replace(RAIZ_DAS_FIXTURES, str(raiz))
    dados = json.loads(texto)
    dados.update(trocas)
    return dados


def comando_do_hook():
    """O `command` de todos os handlers do hooks.json (são iguais; o teste de config confere)."""
    dados = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    return {h["command"] for grupos in dados["hooks"].values() for g in grupos for h in g["hooks"]}
