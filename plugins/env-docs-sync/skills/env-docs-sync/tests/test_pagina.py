"""Página de ambientes inteira (para a migração por replace): ordem, tabela e seções saídas da config."""
import re
import unittest

from support import QUANDO, TEMPLATE, config_exemplo, eds


def bloco(texto):
    return eds.bloco_de_arquivo(texto, sincronizado_em=QUANDO, commit="abc1234")


class Pagina(unittest.TestCase):
    def setUp(self):
        self.cfg = config_exemplo()
        self.blocos = {
            "development": {"packages/api/.env": bloco("API=1\n"), ".env": bloco("RAIZ=1\n")},
            "staging": {"infra/staging/.env": bloco("STG=1\n")},
        }

    def pagina(self, **kw):
        return eds.pagina_de_ambientes(self.cfg, self.blocos, **kw)

    def test_ordem_das_secoes(self):
        pagina = self.pagina()
        marcos = ["<h2>Ambientes</h2>", "<h2>[development]</h2>", "<h3>.env</h3>",
                  "<h3>packages/api/.env</h3>", "<h2>[staging]</h2>", "<h3>infra/staging/.env</h3>",
                  "<h2>[production]</h2>", "<h2>CI/CD</h2>", "<h2>Como rodar</h2>"]
        posicoes = [pagina.find(m) for m in marcos]
        self.assertNotIn(-1, posicoes, dict(zip(marcos, posicoes)))
        self.assertEqual(posicoes, sorted(posicoes))

    def test_bloco_fica_logo_abaixo_do_seu_h3(self):
        pagina = self.pagina()
        self.assertIn("<h3>.env</h3>\n" + self.blocos["development"][".env"], pagina)

    def test_intro_e_callout_de_pagina_restrita_e_gerada(self):
        pagina = self.pagina()
        self.assertTrue(pagina.startswith("<p>Este artigo aborda os diferentes ambientes"))
        callout = re.search(r'<p class="callout warning">(.*?)</p>', pagina, re.S).group(1)
        self.assertIn("platform-team, Admin", callout)
        self.assertIn("env-docs-sync", callout)
        self.assertIn("histórico de revisões", callout)

    def test_tabela_sai_da_config_com_escape(self):
        self.cfg["environments"]["production"]["where"] = "~/app/<prod>/.env"
        pagina = self.pagina()
        tabela = re.search(r"<table>.*?</table>", pagina, re.S).group(0)
        for cabecalho in ("Ambiente", "Servidor", "Domínio", "Onde vive o .env", "Fonte da verdade"):
            self.assertIn(f"<th>{cabecalho}</th>", tabela)
        for ambiente, dados in self.cfg["environments"].items():
            with self.subTest(ambiente=ambiente):
                self.assertIn(f"<td>{ambiente}</td>", tabela)
                self.assertIn(dados["server"], tabela)
                self.assertIn(dados["domain"], tabela)
        self.assertIn("~/app/&lt;prod&gt;/.env", tabela)
        linhas = re.findall(r"<tr><td>(\w+)</td>", tabela)
        self.assertEqual(linhas, ["development", "staging", "production"])

    def test_como_rodar_sai_da_config(self):
        self.cfg["run"].append({"label": "Testes & lint", "command": "npm test && npm run lint"})
        pagina = self.pagina()
        secao = pagina.split("<h2>Como rodar</h2>", 1)[1]
        self.assertIn("Instalar as dependências", secao)
        self.assertIn("npm ci", secao)
        self.assertIn("Testes &amp; lint", secao)
        self.assertIn("npm test &amp;&amp; npm run lint", secao)

    def test_ci_cd_fica_a_gerar(self):
        secao = self.pagina().split("<h2>CI/CD</h2>", 1)[1].split("<h2>", 1)[0]
        self.assertIn("a gerar", secao)

    def test_nenhum_placeholder_sobra(self):
        self.assertIsNone(re.search(r"\$\{?[a-z_]+", self.pagina()))

    def test_so_ambientes_configurados(self):
        del self.cfg["environments"]["production"]
        self.assertNotIn("[production]", self.pagina())

    def test_bloco_de_ambiente_nao_configurado_e_erro(self):
        del self.cfg["environments"]["staging"]
        with self.assertRaises(eds.ErroEnvDocs):
            self.pagina()

    def test_template_sem_placeholder_obrigatorio_e_erro(self):
        template = TEMPLATE.read_text(encoding="utf-8").replace("$environment_sections", "")
        with self.assertRaises(eds.ErroEnvDocs):
            self.pagina(template=template)

    def test_template_padrao_e_o_asset(self):
        self.assertEqual(eds.carregar_template(), TEMPLATE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
