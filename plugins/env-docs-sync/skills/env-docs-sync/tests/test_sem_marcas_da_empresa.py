"""Sensor anti-vazamento (C1): o pacote é público e não pode citar a empresa de origem nem a rede dela.

Os padrões são montados para não casar com o próprio texto deste arquivo, e por isso o sensor
varre o pacote inteiro, inclusive os testes, sem lista de exceção. O teste da fixture sabotada
prova que ele fica vermelho: um sensor que nunca reprova não é sensor.
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from support import PLUGIN

MARCADORES = {
    "rede-privada": re.compile(r"192\.168\."),
    "dominio-da-empresa": re.compile(r"j[r]cbrasil", re.IGNORECASE),
    "sigla-da-empresa": re.compile(r"(?<![A-Za-z0-9])j[r]c(?![A-Za-z0-9])", re.IGNORECASE),
}
IGNORAR = {"__pycache__"}


def encontrar_marcadores(raiz):
    """[(caminho relativo, linha, marcador)] de cada ocorrência; a linha 0 é o próprio caminho."""
    raiz = Path(raiz)
    achados = []
    for arquivo in sorted(raiz.rglob("*")):
        rel = arquivo.relative_to(raiz)
        if IGNORAR & set(rel.parts) or not arquivo.is_file():
            continue
        linhas = [(0, rel.as_posix())]
        texto = arquivo.read_bytes().decode("utf-8", errors="replace")
        linhas += list(enumerate(texto.splitlines(), start=1))
        for numero, linha in linhas:
            for nome, padrao in MARCADORES.items():
                if padrao.search(linha):
                    achados.append((rel.as_posix(), numero, nome))
    return achados


class SemMarcasDaEmpresa(unittest.TestCase):
    def test_pacote_real_esta_limpo(self):
        self.assertTrue((PLUGIN / ".claude-plugin" / "plugin.json").is_file(), PLUGIN)
        self.assertEqual(encontrar_marcadores(PLUGIN), [])

    def test_fixture_sabotada_fica_vermelha(self):
        sabotagens = {
            # Montadas em tempo de execução para este arquivo continuar limpo.
            "rede-privada": ("assets/env-docs.example.json", "host = " + "192" + ".168.10.20"),
            "dominio-da-empresa": ("references/config.md", "https://kb." + "".join(["j", "r", "c", "brasil"]).upper() + ".net"),
            "sigla-da-empresa": ("SKILL.md", "documentado pela " + "J" + "RC" + "-Brasil"),
        }
        for nome, (alvo, injecao) in sabotagens.items():
            with self.subTest(marcador=nome), tempfile.TemporaryDirectory() as tmp:
                copia = Path(tmp) / "pacote"
                shutil.copytree(PLUGIN, copia, ignore=shutil.ignore_patterns("__pycache__"))
                arquivo = copia / "skills" / "env-docs-sync" / alvo
                arquivo.write_text(arquivo.read_text(encoding="utf-8") + "\n" + injecao + "\n", encoding="utf-8")
                self.assertIn(nome, {m for _, _, m in encontrar_marcadores(copia)})

    def test_nome_de_arquivo_tambem_e_varrido(self):
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "pacote"
            shutil.copytree(PLUGIN, copia, ignore=shutil.ignore_patterns("__pycache__"))
            (copia / ("notas-" + "j" + "rc" + ".md")).write_text("limpo\n", encoding="utf-8")
            self.assertEqual([(linha, m) for _, linha, m in encontrar_marcadores(copia)], [(0, "sigla-da-empresa")])


if __name__ == "__main__":
    unittest.main()
