"""Plano de operações: o que muda vira criar/trocar/marcar_ausente, na ordem certa, e o resto fica quieto."""
import copy
import unittest

from support import CANARIO, QUANDO, eds


def estado_com(**ambientes):
    estado = eds.estado_vazio()
    estado["environments"] = copy.deepcopy(ambientes)
    return estado


def sincronizado(dados):
    return {"sha256": eds.hash_sha256(dados), "synced_at": "2026-10-01T09:00:00-03:00"}


def ausente(dados):
    return {"sha256": eds.hash_sha256(dados), "absent_since": "2026-10-01"}


class Planejar(unittest.TestCase):
    def planejar(self, estado, atuais, ler_corpo=None):
        return eds.planejar(estado, atuais, sincronizado_em=QUANDO, commit="abc1234",
                            ler_corpo=ler_corpo)

    def test_nada_mudou_plano_vazio(self):
        estado = estado_com(development={".env": sincronizado(b"A=1\n")})
        self.assertEqual(self.planejar(estado, {"development": {".env": b"A=1\n"}}), [])

    def test_arquivo_novo_vira_criar(self):
        [op] = self.planejar(eds.estado_vazio(), {"development": {".env": b"A=1\n"}})
        self.assertEqual((op.ambiente, op.caminho, op.acao, op.sha256),
                         ("development", ".env", "criar", eds.hash_sha256(b"A=1\n")))
        self.assertEqual(op.corpo, eds.bloco_de_arquivo(b"A=1\n", sincronizado_em=QUANDO, commit="abc1234"))
        self.assertEqual(op.sob, "[development]")

    def test_arquivo_mudado_vira_trocar(self):
        estado = estado_com(development={".env": sincronizado(b"A=1\n")})
        [op] = self.planejar(estado, {"development": {".env": b"A=2\n"}})
        self.assertEqual((op.acao, op.sha256), ("trocar", eds.hash_sha256(b"A=2\n")))
        self.assertEqual(eds.conteudo_do_bloco(op.corpo), "A=2\n")

    def test_arquivo_sumido_vira_marcar_ausente_e_mantem_o_bloco(self):
        antigo = eds.bloco_de_arquivo(b"A=1\n", sincronizado_em=QUANDO, commit="abc1234")
        lidos = []

        def ler_corpo(ambiente, caminho):
            lidos.append((ambiente, caminho))
            return antigo

        estado = estado_com(development={".env": sincronizado(b"A=1\n"), ".env.local": sincronizado(b"B=1\n")})
        [op] = self.planejar(estado, {"development": {".env.local": b"B=1\n"}}, ler_corpo)
        self.assertEqual((op.caminho, op.acao, op.sha256), (".env", "marcar_ausente", None))
        self.assertEqual(op.corpo, eds.marcar_ausente(antigo, QUANDO.date()))
        self.assertEqual(lidos, [("development", ".env")])

    def test_marcar_ausente_sem_leitor_do_corpo_e_erro(self):
        estado = estado_com(development={".env": sincronizado(b"A=1\n")})
        with self.assertRaises(eds.ErroEnvDocs):
            self.planejar(estado, {"development": {}})

    def test_ausente_que_continua_ausente_nao_gera_nada(self):
        estado = estado_com(development={".env": ausente(b"A=1\n")})
        self.assertEqual(self.planejar(estado, {"development": {}}), [])

    def test_ausente_que_volta_troca_mesmo_com_hash_igual(self):
        estado = estado_com(development={".env": ausente(b"A=1\n")})
        [op] = self.planejar(estado, {"development": {".env": b"A=1\n"}})
        self.assertEqual(op.acao, "trocar")
        self.assertNotIn("ausente desde", op.corpo)

    def test_ambiente_fora_da_rodada_fica_intocado(self):
        estado = estado_com(development={".env": sincronizado(b"A=1\n")},
                            staging={"infra/.env": sincronizado(b"S=1\n")})
        self.assertEqual(self.planejar(estado, {"development": {".env": b"A=1\n"}}), [])

    def test_ordem_ambientes_e_caminhos(self):
        atuais = {
            "production": {"z/.env": b"1", "a/.env": b"2"},
            "development": {"packages/web/.env": b"3", ".env.local": b"4", ".env": b"5"},
            "staging": {"infra/.env": b"6"},
        }
        ops = self.planejar(eds.estado_vazio(), atuais)
        self.assertEqual([(op.ambiente, op.caminho) for op in ops], [
            ("development", ".env"), ("development", ".env.local"), ("development", "packages/web/.env"),
            ("staging", "infra/.env"), ("production", "a/.env"), ("production", "z/.env")])

    def test_commit_so_entra_no_development(self):
        ops = self.planejar(eds.estado_vazio(), {"development": {".env": b"1"}, "staging": {"i/.env": b"2"}})
        self.assertIn("commit abc1234", ops[0].corpo)
        self.assertNotIn("commit", ops[1].corpo)

    def test_ambiente_desconhecido_e_erro(self):
        with self.assertRaises(eds.ErroEnvDocs):
            self.planejar(eds.estado_vazio(), {"homolog": {".env": b"1"}})

    def test_caminho_que_escapa_da_raiz_e_erro(self):
        with self.assertRaises(eds.ErroEnvDocs):
            self.planejar(eds.estado_vazio(), {"development": {"../fora/.env": b"1"}})

    def test_erro_de_conteudo_cita_o_caminho_e_nao_o_valor(self):
        with self.assertRaises(eds.ErroEnvDocs) as ctx:
            self.planejar(eds.estado_vazio(), {"development": {".env": CANARIO.encode() + b"\xff"}})
        self.assertIn(".env", str(ctx.exception))
        self.assertNotIn(CANARIO, str(ctx.exception))

    def test_repr_da_operacao_nao_mostra_o_corpo(self):
        [op] = self.planejar(eds.estado_vazio(), {"development": {".env": f"S={CANARIO}\n".encode()}})
        self.assertIn(CANARIO, op.corpo)
        self.assertNotIn(CANARIO, repr(op))
        self.assertNotIn(CANARIO, op.resumo())

    def test_diferencas_trabalha_so_com_hashes(self):
        estado = estado_com(development={".env": sincronizado(b"A=1\n")})
        mudancas = eds.diferencas(estado, {"development": {".env": eds.hash_sha256(b"A=2\n"),
                                                           "b/.env": eds.hash_sha256(b"B")}})
        self.assertEqual([(m.caminho, m.acao) for m in mudancas], [(".env", "trocar"), ("b/.env", "criar")])


class RegistrarEAplicar(unittest.TestCase):
    def setUp(self):
        self.criar = eds.Operacao("development", ".env", "criar", eds.hash_sha256(b"A=1\n"), corpo="<pre>x</pre>")

    def test_registrar_criar_guarda_hash_e_carimbo(self):
        antes = eds.estado_vazio()
        depois = eds.registrar_operacao(antes, self.criar, quando=QUANDO)
        self.assertEqual(depois["environments"]["development"][".env"],
                         {"sha256": eds.hash_sha256(b"A=1\n"), "synced_at": "2026-10-27T14:05:00-03:00"})
        self.assertEqual(antes, eds.estado_vazio(), "registrar_operacao não pode mexer no estado recebido")

    def test_registrar_ausente_guarda_o_ultimo_hash_e_a_data(self):
        estado = estado_com(development={".env": sincronizado(b"A=1\n")})
        op = eds.Operacao("development", ".env", "marcar_ausente", None, corpo="<p>x</p>")
        depois = eds.registrar_operacao(estado, op, quando=QUANDO)
        self.assertEqual(depois["environments"]["development"][".env"],
                         {"sha256": eds.hash_sha256(b"A=1\n"), "absent_since": "2026-10-27"})

    def test_aplicar_para_na_primeira_falha_e_registra_so_o_que_foi(self):
        trocar = eds.Operacao("development", ".env.local", "trocar", eds.hash_sha256(b"B"), corpo="<pre>y</pre>")
        escritas = []

        class Destino:
            def ler_corpo(self, ambiente, caminho):
                return None

            def escrever(self, op):
                if op.caminho == ".env.local":
                    raise eds.ErroEnvDocs("destino fora do ar")
                escritas.append(op.caminho)

        resultado = eds.aplicar(eds.estado_vazio(), [self.criar, trocar], Destino(), quando=QUANDO)
        self.assertEqual(escritas, [".env"])
        self.assertEqual(resultado.aplicadas, [self.criar])
        self.assertEqual(resultado.falhou, trocar)
        self.assertIsInstance(resultado.erro, eds.ErroEnvDocs)
        self.assertEqual(list(resultado.estado["environments"]["development"]), [".env"])


if __name__ == "__main__":
    unittest.main()
