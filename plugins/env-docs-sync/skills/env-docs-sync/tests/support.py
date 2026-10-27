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
