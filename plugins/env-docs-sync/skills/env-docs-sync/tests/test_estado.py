"""Estado: arquivo 0600, gravação atômica, e só hashes e carimbos (o validador recusa qualquer outra coisa)."""
import json
import os
import re
import stat
import tempfile
import unittest
from pathlib import Path

from support import CANARIO, QUANDO, eds

HEX64 = re.compile(r"[0-9a-f]{64}")
CARIMBO = re.compile(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)?)?")


def folhas(valor):
    if isinstance(valor, dict):
        for v in valor.values():
            yield from folhas(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from folhas(v)
    else:
        yield valor


class Estado(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.tmp.name) / "dados" / "estado" / "repo.json"

    def tearDown(self):
        self.tmp.cleanup()

    def estado_sincronizado(self):
        atuais = {"development": {".env": f"DB_PASSWORD={CANARIO}\n".encode(), ".env.example": b"DB_PASSWORD=\n"}}
        estado = eds.estado_vazio()
        for op in eds.planejar(estado, atuais, sincronizado_em=QUANDO, commit="abc1234"):
            self.assertIn(op.acao, ("criar",))
            estado = eds.registrar_operacao(estado, op, quando=QUANDO)
        return estado

    def test_grava_0600_em_pasta_criada_0700(self):
        eds.gravar_estado(self.caminho, self.estado_sincronizado())
        self.assertEqual(stat.S_IMODE(self.caminho.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.caminho.parent.stat().st_mode), 0o700)

    def test_so_hashes_e_carimbos_nunca_o_valor(self):
        eds.gravar_estado(self.caminho, self.estado_sincronizado())
        texto = self.caminho.read_text(encoding="utf-8")
        self.assertNotIn(CANARIO, texto)
        dados = json.loads(texto)
        for folha in folhas(dados["environments"]):
            with self.subTest(folha=folha):
                self.assertTrue(HEX64.fullmatch(folha) or CARIMBO.fullmatch(folha), folha)

    def test_ida_e_volta(self):
        estado = self.estado_sincronizado()
        estado["remote_checked_at"]["staging"] = "2026-10-27T14:05:00-03:00"
        eds.gravar_estado(self.caminho, estado)
        self.assertEqual(eds.carregar_estado(self.caminho), estado)

    def test_recusa_valor_que_nao_e_hash_sem_ecoar_o_valor(self):
        estado = eds.estado_vazio()
        estado["environments"]["development"] = {".env": {"sha256": CANARIO, "synced_at": "2026-10-27"}}
        with self.assertRaises(eds.ErroDeEstado) as ctx:
            eds.gravar_estado(self.caminho, estado)
        self.assertNotIn(CANARIO, str(ctx.exception))
        self.assertFalse(self.caminho.exists())

    def test_recusa_chave_extra_na_entrada(self):
        estado = self.estado_sincronizado()
        estado["environments"]["development"][".env"]["content"] = "x"
        with self.assertRaises(eds.ErroDeEstado):
            eds.gravar_estado(self.caminho, estado)

    def test_recusa_chave_extra_no_topo_e_ambiente_desconhecido(self):
        for mexer in (lambda e: e.__setitem__("values", {}),
                      lambda e: e["environments"].__setitem__("homolog", {}),
                      lambda e: e["remote_checked_at"].__setitem__("staging", CANARIO)):
            estado = eds.estado_vazio()
            mexer(estado)
            with self.subTest(estado=list(estado)), self.assertRaises(eds.ErroDeEstado) as ctx:
                eds.validar_estado(estado)
            self.assertNotIn(CANARIO, str(ctx.exception))

    def test_ausente_carrega_estado_vazio(self):
        self.assertEqual(eds.carregar_estado(self.caminho), eds.estado_vazio())

    def test_corrompido_e_erro(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text("{", encoding="utf-8")
        with self.assertRaises(eds.ErroDeEstado):
            eds.carregar_estado(self.caminho)

    def test_regrava_arquivo_0644_como_0600_sem_temporario_sobrando(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text(json.dumps(eds.estado_vazio()), encoding="utf-8")
        os.chmod(self.caminho, 0o644)
        eds.gravar_estado(self.caminho, self.estado_sincronizado())
        self.assertEqual(stat.S_IMODE(self.caminho.stat().st_mode), 0o600)
        self.assertEqual(sorted(p.name for p in self.caminho.parent.iterdir()), ["repo.json"])


if __name__ == "__main__":
    unittest.main()
