"""A .env-docs.json: o exemplo vale, e cada campo faltando ou errado vira erro claro, nunca default."""
import tempfile
import unittest
from pathlib import Path

from support import EXEMPLO, config_exemplo, eds


class ConfigValida(unittest.TestCase):
    def test_exemplo_completo_e_valido(self):
        cfg = eds.carregar_config(EXEMPLO)
        self.assertEqual(cfg["doc"]["backend"], "kb")
        self.assertEqual(list(cfg["environments"]), ["development", "staging", "production"])

    def test_auth_env_nulo_e_chave_ssh(self):
        cfg = config_exemplo()
        self.assertIsNone(cfg["environments"]["staging"]["auth_env"])
        eds.validar_config(cfg)

    def test_sem_ambiente_remoto_dispensa_remote_check_every(self):
        cfg = config_exemplo()
        del cfg["environments"]["staging"], cfg["environments"]["production"], cfg["remote_check_every"]
        eds.validar_config(cfg)

    def test_exclude_e_run_podem_ser_listas_vazias(self):
        cfg = config_exemplo()
        cfg["exclude"], cfg["run"] = [], []
        eds.validar_config(cfg)

    def test_intervalo_em_segundos(self):
        self.assertEqual(eds.intervalo_em_segundos("24h"), 86400)
        self.assertEqual(eds.intervalo_em_segundos("30m"), 1800)
        self.assertEqual(eds.intervalo_em_segundos("2d"), 172800)
        for ruim in ("24", "0h", "h", "1.5h", "-1h", 24):
            with self.subTest(ruim=ruim), self.assertRaises(eds.ErroDeConfig):
                eds.intervalo_em_segundos(ruim)


class ConfigInvalida(unittest.TestCase):
    def erros(self, cfg):
        with self.assertRaises(eds.ErroDeConfig) as ctx:
            eds.validar_config(cfg)
        return ctx.exception.erros

    def assertErro(self, cfg, trecho):
        erros = self.erros(cfg)
        self.assertTrue(any(trecho in e for e in erros), f"{trecho!r} não está em {erros}")

    def test_campo_de_topo_ausente_e_erro_nao_default(self):
        for campo in ("doc", "values", "include", "exclude", "environments", "run"):
            with self.subTest(campo=campo):
                cfg = config_exemplo()
                del cfg[campo]
                self.assertErro(cfg, f"config.{campo}: campo obrigatório ausente")

    def test_campo_ausente_em_doc(self):
        for campo in ("backend", "cli", "python", "target", "page_id", "allowed_roles"):
            with self.subTest(campo=campo):
                cfg = config_exemplo()
                del cfg["doc"][campo]
                self.assertErro(cfg, f"config.doc.{campo}: campo obrigatório ausente")

    def test_campo_ausente_nos_ambientes(self):
        casos = [("development", "machine"), ("development", "where"), ("staging", "host"),
                 ("staging", "auth_env"), ("staging", "files"), ("production", "source_of_truth")]
        for ambiente, campo in casos:
            with self.subTest(ambiente=ambiente, campo=campo):
                cfg = config_exemplo()
                del cfg["environments"][ambiente][campo]
                self.assertErro(cfg, f"config.environments.{ambiente}.{campo}: campo obrigatório ausente")

    def test_remote_check_every_obrigatorio_com_ambiente_ssh(self):
        cfg = config_exemplo()
        del cfg["remote_check_every"]
        self.assertErro(cfg, "config.remote_check_every: campo obrigatório ausente")

    def test_tipos_e_valores_errados(self):
        casos = [
            (("doc", "page_id"), "12", "config.doc.page_id"),
            (("doc", "page_id"), True, "config.doc.page_id"),
            (("doc", "page_id"), 0, "config.doc.page_id"),
            (("doc", "allowed_roles"), [], "config.doc.allowed_roles"),
            (("doc", "allowed_roles"), ["a", "a"], "config.doc.allowed_roles"),
            (("doc", "backend"), "wiki", "config.doc.backend"),
            (("doc", "cli"), "", "config.doc.cli"),
            (("values",), "keys", "config.values"),
            (("remote_check_every",), "amanhã", "config.remote_check_every"),
            (("include",), [], "config.include"),
            (("include",), "**/.env", "config.include"),
        ]
        for caminho, valor, onde in casos:
            with self.subTest(onde=onde, valor=valor):
                cfg = config_exemplo()
                alvo = cfg
                for chave in caminho[:-1]:
                    alvo = alvo[chave]
                alvo[caminho[-1]] = valor
                self.assertErro(cfg, onde)

    def test_chave_desconhecida(self):
        cfg = config_exemplo()
        cfg["exlude"] = []
        self.assertErro(cfg, "config.exlude: chave desconhecida")
        cfg = config_exemplo()
        cfg["environments"]["development"]["files"] = {}
        self.assertErro(cfg, "config.environments.development.files: chave desconhecida")

    def test_ambiente_fora_dos_tres(self):
        cfg = config_exemplo()
        cfg["environments"]["homolog"] = cfg["environments"]["staging"]
        self.assertErro(cfg, "config.environments.homolog")

    def test_development_obrigatorio_e_local(self):
        cfg = config_exemplo()
        del cfg["environments"]["development"]
        self.assertErro(cfg, "config.environments.development: campo obrigatório ausente")
        cfg = config_exemplo()
        cfg["environments"]["development"]["source"] = "ssh"
        self.assertErro(cfg, "config.environments.development.source")

    def test_ambiente_remoto_precisa_de_ssh_e_files_validos(self):
        casos = [
            ("source", "local", "config.environments.staging.source"),
            ("files", {}, "config.environments.staging.files"),
            ("files", {"../fora/.env": "/srv/.env"}, "config.environments.staging.files"),
            ("files", {"/abs/.env": "/srv/.env"}, "config.environments.staging.files"),
            ("files", {"infra/.env": "relativo/.env"}, "config.environments.staging.files"),
            ("host", "-oProxyCommand=touch", "config.environments.staging.host"),
            ("host", "dois hosts", "config.environments.staging.host"),
            ("auth_env", "MINHA SENHA", "config.environments.staging.auth_env"),
        ]
        for campo, valor, onde in casos:
            with self.subTest(campo=campo, valor=valor):
                cfg = config_exemplo()
                cfg["environments"]["staging"][campo] = valor
                self.assertErro(cfg, onde)

    def test_padroes_precisam_ser_relativos(self):
        for campo, valor in (("include", ["/etc/*"]), ("exclude", ["../x/**"]), ("exclude", ["a\\b"])):
            with self.subTest(campo=campo, valor=valor):
                cfg = config_exemplo()
                cfg[campo] = valor
                self.assertErro(cfg, f"config.{campo}")

    def test_itens_de_run(self):
        cfg = config_exemplo()
        cfg["run"] = [{"label": "sem comando"}]
        self.assertErro(cfg, "config.run[0].command: campo obrigatório ausente")

    def test_varios_erros_de_uma_vez(self):
        cfg = config_exemplo()
        del cfg["doc"]["page_id"]
        cfg["values"] = "keys"
        erros = self.erros(cfg)
        self.assertGreaterEqual(len(erros), 2)
        with self.assertRaises(eds.ErroDeConfig) as ctx:
            eds.validar_config(cfg)
        self.assertIn("config.doc.page_id", str(ctx.exception))
        self.assertIn("config.values", str(ctx.exception))

    def test_config_precisa_ser_objeto(self):
        self.assertErro([], "config: precisa ser um objeto")


class ConfigArquivo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.tmp.name) / ".env-docs.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_json_invalido(self):
        self.caminho.write_text("{", encoding="utf-8")
        with self.assertRaises(eds.ErroDeConfig) as ctx:
            eds.carregar_config(self.caminho)
        self.assertIn("JSON inválido", str(ctx.exception))

    def test_chave_duplicada(self):
        self.caminho.write_text('{"values": "full", "values": "full"}', encoding="utf-8")
        with self.assertRaises(eds.ErroDeConfig) as ctx:
            eds.carregar_config(self.caminho)
        self.assertIn("duplicada", str(ctx.exception))

    def test_arquivo_ausente(self):
        with self.assertRaises(eds.ErroDeConfig) as ctx:
            eds.carregar_config(self.caminho)
        self.assertIn("não encontrado", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
