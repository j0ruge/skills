"""Sync remoto: leitura por ssh (chave ou sshpass -e), gatilho por host citado, janela da SessionStart.

O ssh é falso em dois níveis: um runner injetado, que registra argv e ambiente de cada chamada, e
scripts `ssh`/`sshpass` falsos no PATH, num processo real, que gravam o próprio /proc/<pid>/cmdline.
A senha é um canário: tem que chegar ao `SSHPASS` do filho e a nenhum argv, saída ou estado.
"""
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from support import CANARIO, MAQUINA, QUANDO_ISO, config_exemplo, criar_repo, eds, fixture, rodar_cli
from test_hook import AGORA, DestinoEspiao

SENHA = "SENHA_CANARIO_93ab"
STAGING, PRODUCAO = "deploy@staging.internal.example", "deploy@db.internal.example"


def config_com_remotos(maquina=MAQUINA):
    cfg = config_exemplo()
    cfg["environments"]["development"]["machine"] = maquina
    cfg["ci"]["secrets"] = None  # sem gh: estes testes são do ssh; o gh tem os dele em test_ci e test_derivadas
    return cfg


class SshFalso:
    """Runner injetável: devolve o conteúdo por host, ou falha com o rc dado."""

    def __init__(self, conteudos=None, rc=0):
        self.conteudos = conteudos if conteudos is not None else {
            STAGING: f"STAGING_KEY={CANARIO}_stg\n".encode(), PRODUCAO: f"PROD_KEY={CANARIO}_prd\n".encode()}
        self.rc, self.chamadas = rc, []

    def __call__(self, argv, *, env, timeout, entrada=None):
        self.chamadas.append((list(argv), dict(env)))
        host = argv[argv.index("--") + 1]
        if self.rc:
            return eds.ResultadoComando(self.rc, b"", b"ssh: connect to host: Connection timed out")
        return eds.ResultadoComando(0, self.conteudos[host], b"")

    def hosts(self):
        return [argv[argv.index("--") + 1] for argv, _ in self.chamadas]


class ComandoSsh(unittest.TestCase):
    def test_chave_usa_batchmode_sem_sshpass(self):
        amb = config_com_remotos()["environments"]["staging"]
        argv, env = eds.comando_ssh(amb, "/srv/app/infra/staging/.env", {"PATH": "/bin"})
        self.assertEqual(argv[0], "ssh")
        self.assertIn("BatchMode=yes", argv)
        self.assertIn(f"ConnectTimeout={eds.SSH_CONNECT_TIMEOUT}", argv)
        self.assertEqual(argv[-3:], ["--", STAGING, "cat -- '/srv/app/infra/staging/.env'"])
        self.assertNotIn("SSHPASS", env)

    def test_senha_vai_no_ambiente_do_filho_nunca_no_argv(self):
        amb = config_com_remotos()["environments"]["production"]
        argv, env = eds.comando_ssh(amb, "~/app/infra/prod/.env", {"PATH": "/bin", "EXAMPLE_SSH_PASSWORD": SENHA})
        self.assertEqual(argv[:3], ["sshpass", "-e", "ssh"])
        # BatchMode=yes ou NumberOfPasswordPrompts=1 fazem a senha errada sair 255 (medido), igual à rede fora.
        self.assertIn("BatchMode=no", argv)
        self.assertFalse(any(parte.startswith("NumberOfPasswordPrompts") for parte in argv))
        self.assertFalse(any(SENHA in parte for parte in argv))
        self.assertEqual(env["SSHPASS"], SENHA)
        self.assertNotIn("EXAMPLE_SSH_PASSWORD", env, "o filho recebe a senha só em SSHPASS")
        self.assertEqual(argv[-1], "cat -- ~/'app/infra/prod/.env'")

    def test_auth_env_sem_a_variavel_falha_sem_rodar(self):
        amb = config_com_remotos()["environments"]["production"]
        with self.assertRaises(eds.ErroEnvDocs) as ctx:
            eds.comando_ssh(amb, "~/x/.env", {"PATH": "/bin"})
        self.assertIn("EXAMPLE_SSH_PASSWORD", str(ctx.exception))

    def test_aspas_remotas_no_shell_de_verdade(self):
        casos = {"/srv/a b/.env": "/srv/a b/.env", "~/app/it's.env": "/casa/app/it's.env",
                 "/x/$(touch y)`z`.env": "/x/$(touch y)`z`.env", "~/": "/casa/"}
        for remoto, esperado in casos.items():
            with self.subTest(remoto):
                citado = eds.aspas_remotas(remoto)
                saida = subprocess.run(["sh", "-c", f"printf '%s' {citado}"], capture_output=True, text=True,
                                       env={"HOME": "/casa", "PATH": os.environ["PATH"]}).stdout
                self.assertEqual(saida, esperado)


class HostCitado(unittest.TestCase):
    def test_matriz(self):
        positivos = [
            "ssh deploy@staging.internal.example 'cat /srv/app/.env'",
            "scp ./x staging.internal.example:/tmp/",
            "sshpass -e ssh deploy@staging.internal.example true",
            "rsync -av infra/ deploy@staging.internal.example:/srv/app/",
            "/usr/bin/ssh -p 2222 staging.internal.example",
            "cd /tmp && ssh staging.internal.example",
        ]
        negativos = [
            "echo staging.internal.example",
            "ssh other.example",
            "ssh staging.internal.example.evil",
            "ssh-keygen -R staging.internal.example",
            "ssh xstaging.internal.example",
            "",
        ]
        for comando in positivos:
            with self.subTest(positivo=comando):
                self.assertTrue(eds.host_citado(comando, STAGING))
        for comando in negativos:
            with self.subTest(negativo=comando):
                self.assertFalse(eds.host_citado(comando, STAGING))

    def test_ip_e_alias(self):
        self.assertTrue(eds.host_citado("ssh root@192.0.2.6 ls", "root@192.0.2.6"))
        self.assertFalse(eds.host_citado("ssh root@192.0.2.60 ls", "root@192.0.2.6"))
        self.assertTrue(eds.host_citado("scp a staging-box:b", "staging-box"))
        self.assertTrue(eds.host_citado("ssh [2001:db8::1] ls", "deploy@[2001:db8::1]"))


class BaseRemoto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.dados = base / "dados"
        self.raiz = criar_repo(base / "repo", {".env": "LOCAL=1\n"}, config=config_com_remotos())
        self.destino = DestinoEspiao(base / "destino")
        self.ssh = SshFalso()
        self.agora = AGORA
        self.saidas = []

    def tearDown(self):
        self.tmp.cleanup()

    def hook(self, payload, **troca):
        opcoes = dict(hostname=lambda: MAQUINA, agora=lambda: self.agora,
                      fabrica_destino=lambda c, r, x: self.destino, pasta_de_estado=self.dados,
                      ambiente={"PATH": "/bin", "EXAMPLE_SSH_PASSWORD": SENHA}, runner=self.ssh)
        opcoes.update(troca)
        resposta = eds.executar_hook(json.dumps(payload), eds.Contexto(**opcoes))
        self.saidas.append(eds.saida_do_hook(resposta) + "\n".join(resposta.log))
        return resposta

    def estado(self):
        return eds.carregar_estado(eds.arquivo_de_estado(self.raiz, self.dados))


class GatilhoPorHost(BaseRemoto):
    def test_bash_que_cita_o_host_le_so_aquele_ambiente(self):
        for nome in ("claude-posttooluse-bash-ssh.json", "codex-posttooluse-bash-ssh.json"):
            with self.subTest(nome):
                self.ssh.chamadas.clear()
                self.hook(fixture(nome, self.raiz))
                self.assertEqual(self.ssh.hosts(), [STAGING])
        self.assertIn(("staging", "criar", "infra/staging/.env"), self.destino.escritas)
        self.assertNotIn("production", {a for a, *_ in self.destino.escritas})
        estado = self.estado()
        self.assertEqual(set(estado["remote_checked_at"]), {"staging"})
        self.assertNotIn("production", estado["environments"])

    def test_bash_sem_host_nao_chama_ssh(self):
        self.hook(fixture("codex-posttooluse-bash-ssh.json", self.raiz, tool_input={"command": "ls -la"}))
        self.assertEqual(self.ssh.chamadas, [])

    def test_edicao_e_stop_nao_chamam_ssh(self):
        self.hook(fixture("claude-posttooluse-edit-env.json", self.raiz))
        self.hook(fixture("claude-stop.json", self.raiz))
        self.assertEqual(self.ssh.chamadas, [])

    def test_mesmo_conteudo_remoto_nao_escreve_mas_carimba(self):
        bash = fixture("claude-posttooluse-bash-ssh.json", self.raiz)
        self.hook(bash)
        escritas = len(self.destino.escritas)
        self.agora = AGORA + timedelta(minutes=5)
        resposta = self.hook(bash)
        self.assertEqual(len(self.destino.escritas), escritas)
        self.assertIsNone(resposta.mensagem)
        self.assertEqual(self.estado()["remote_checked_at"]["staging"], (AGORA + timedelta(minutes=5)).isoformat())


class Janela(BaseRemoto):
    def test_segunda_sessionstart_dentro_da_janela_nao_chama_ssh(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.assertEqual(sorted(self.ssh.hosts()), sorted([STAGING, PRODUCAO]))
        self.agora = AGORA + timedelta(hours=23, minutes=59)
        self.hook(fixture("codex-sessionstart.json", self.raiz))
        self.assertEqual(len(self.ssh.chamadas), 2, "dentro de remote_check_every, sem ssh")
        self.agora = AGORA + timedelta(hours=24)
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.assertEqual(len(self.ssh.chamadas), 4, "janela vencida, ssh de novo")

    def test_bash_ignora_a_janela(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.hook(fixture("claude-posttooluse-bash-ssh.json", self.raiz))
        self.assertEqual(self.ssh.hosts()[-1], STAGING)
        self.assertEqual(len(self.ssh.chamadas), 3)

    def test_carimbo_no_futuro_conta_como_vencido(self):
        arquivo = eds.arquivo_de_estado(self.raiz, self.dados)
        estado = eds.estado_vazio()
        estado["remote_checked_at"] = {"staging": "2099-01-01T00:00:00+00:00", "production": "2026-10-25"}
        eds.gravar_estado(arquivo, estado)
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.assertEqual(sorted(self.ssh.hosts()), sorted([STAGING, PRODUCAO]))


class FalhaDeRede(BaseRemoto):
    def test_rede_fora_avisa_omite_e_tenta_de_novo(self):
        self.ssh.rc = 255
        resposta = self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.assertIn("aviso", resposta.mensagem)
        self.assertIn("staging", resposta.mensagem)
        self.assertIn("production", resposta.mensagem)
        estado = self.estado()  # o development local sincronizou; os remotos ficaram de fora
        self.assertEqual(set(estado["environments"]), {"development"})
        self.assertEqual(estado["remote_checked_at"], {})
        self.agora = AGORA + timedelta(minutes=1)
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.assertEqual(len(self.ssh.chamadas), 4, "sem carimbo, a SessionStart seguinte tenta de novo")

    def test_falha_depois_de_sucesso_nao_marca_ausente(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        antes = self.estado()["environments"]["staging"]
        self.ssh.rc = 255
        self.agora = AGORA + timedelta(days=2)
        resposta = self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.assertIn("aviso", resposta.mensagem)
        self.assertEqual(self.estado()["environments"]["staging"], antes)
        self.assertNotIn("marcar_ausente", {acao for _, acao, _ in self.destino.escritas})

    def test_motivo_por_codigo_de_saida(self):
        for rc, trecho in ((255, "conexão ou autenticação"), (5, "senha"), (6, "chave do host"),
                           (1, "ausente ou ilegível"), (42, "rc 42")):
            with self.subTest(rc=rc):
                self.assertIn(trecho, eds.motivo_ssh(rc, sshpass=rc in (5, 6)))

    def test_auth_env_ausente_vira_aviso_sem_ssh_para_aquele_ambiente(self):
        resposta = self.hook(fixture("claude-sessionstart.json", self.raiz), ambiente={"PATH": "/bin"})
        self.assertEqual(self.ssh.hosts(), [STAGING])
        self.assertIn("EXAMPLE_SSH_PASSWORD", resposta.mensagem)
        self.assertNotIn("production", self.estado()["environments"])

    def test_arquivo_remoto_grande_demais(self):
        self.ssh.conteudos[STAGING] = b"X" * (eds.LIMITE_REMOTO + 1)
        resposta = self.hook(fixture("claude-posttooluse-bash-ssh.json", self.raiz))
        self.assertIn("grande demais", resposta.mensagem)
        self.assertNotIn("staging", self.estado()["environments"])

    def test_rodar_comando_traduz_timeout_e_programa_ausente(self):
        with self.assertRaises(eds.ErroEnvDocs) as erro:
            eds.rodar_comando(["sleep", "5"], env={"PATH": os.environ["PATH"]}, timeout=0.2)
        self.assertIn("tempo esgotado", str(erro.exception))
        with self.assertRaises(eds.ErroEnvDocs) as erro:
            eds.rodar_comando(["/nao/existe/ssh"], env={}, timeout=5)
        self.assertIn("não encontrado", str(erro.exception))

    def test_programa_ausente_no_hook_vira_aviso(self):
        def sem_ssh(argv, **opcoes):
            return eds.rodar_comando(["/nao/existe/" + argv[0], *argv[1:]], **opcoes)
        resposta = self.hook(fixture("claude-posttooluse-bash-ssh.json", self.raiz), runner=sem_ssh)
        self.assertIn("não encontrado", resposta.mensagem)
        self.assertNotIn("staging", self.estado()["environments"])


class CanarioRemoto(BaseRemoto):
    def test_senha_e_conteudo_fora_de_argv_saida_e_estado(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        self.ssh.rc = 5
        self.agora = AGORA + timedelta(days=2)
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        for argv, env in self.ssh.chamadas:
            self.assertFalse(any(SENHA in parte or CANARIO in parte for parte in argv))
        prod = [env for argv, env in self.ssh.chamadas if PRODUCAO in argv]
        self.assertTrue(prod and all(env.get("SSHPASS") == SENHA for env in prod), "controle: a senha chegou")
        for saida in self.saidas:
            self.assertNotIn(SENHA, saida)
            self.assertNotIn(CANARIO, saida)
        texto = eds.arquivo_de_estado(self.raiz, self.dados).read_text(encoding="utf-8")
        self.assertNotIn(SENHA, texto)
        self.assertNotIn(CANARIO, texto)
        self.assertIn(f"{CANARIO}_prd", self.destino.ler_corpo("production", "infra/prod/.env"))


FAKE_SSHPASS = """#!/bin/sh
tr '\\0' ' ' < /proc/$$/cmdline > "$EDS_SAIDA/sshpass.cmdline"
printf '%s' "$SSHPASS" | sha256sum | cut -d' ' -f1 > "$EDS_SAIDA/sshpass.sha"
[ "$1" = "-e" ] && shift
exec "$@"
"""
FAKE_SSH = """#!/bin/sh
n=$(ls "$EDS_SAIDA" | grep -c '^ssh\\.cmdline')
tr '\\0' ' ' < /proc/$$/cmdline > "$EDS_SAIDA/ssh.cmdline.$n"
tr '\\0' ' ' < /proc/$PPID/cmdline > "$EDS_SAIDA/pai.cmdline.$n"
for a in "$@"; do last=$a; done
printf 'REMOTO=%s\\n' "$(printf '%s' "$last" | sha256sum | cut -c1-8)"
"""


class ProcessoReal(unittest.TestCase):
    """O argv que o `ps` mostra (/proc/<pid>/cmdline) do sshpass e do ssh de verdade, com programas falsos."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.bin, self.saida, self.dados = base / "bin", base / "saida", base / "dados"
        for d in (self.bin, self.saida):
            d.mkdir()
        for nome, texto in (("sshpass", FAKE_SSHPASS), ("ssh", FAKE_SSH)):
            (self.bin / nome).write_text(texto, encoding="utf-8")
            (self.bin / nome).chmod(0o755)
        self.raiz = criar_repo(base / "repo", {".env": "LOCAL=1\n"}, config=config_com_remotos())
        self.ambiente = {"PATH": f"{self.bin}:{os.environ['PATH']}", "HOME": str(base),
                         "EXAMPLE_SSH_PASSWORD": SENHA, "EDS_SAIDA": str(self.saida)}

    def tearDown(self):
        self.tmp.cleanup()

    def test_cmdline_sem_senha_e_sshpass_recebe_pelo_ambiente(self):
        destino = DestinoEspiao(Path(self.tmp.name) / "destino")
        ctx = eds.Contexto(hostname=lambda: MAQUINA, agora=lambda: AGORA, fabrica_destino=lambda c, r, x: destino,
                           pasta_de_estado=self.dados, ambiente=self.ambiente)
        resposta = eds.executar_hook(json.dumps(fixture("claude-sessionstart.json", self.raiz)), ctx)
        self.assertIn("staging", resposta.mensagem)
        self.assertIn("production", resposta.mensagem)
        linhas = {p.name: p.read_text(encoding="utf-8") for p in self.saida.iterdir()}
        self.assertIn("sshpass.cmdline", linhas)
        self.assertEqual(sum(1 for n in linhas if n.startswith("ssh.cmdline")), 2)
        for nome, texto in linhas.items():
            self.assertNotIn(SENHA, texto, nome)
        self.assertIn("sshpass -e ssh", linhas["sshpass.cmdline"])
        self.assertEqual(linhas["sshpass.sha"].strip(), hashlib.sha256(SENHA.encode()).hexdigest())
        self.assertIsNotNone(destino.ler_corpo("production", "infra/prod/.env"))
        self.assertNotIn(SENHA, eds.saida_do_hook(resposta))

    def test_cli_sync_remote_e_status_remote(self):
        estado = Path(self.tmp.name) / "estado.json"
        destino = Path(self.tmp.name) / "destino"
        env = {**os.environ, **self.ambiente}
        def cli(*args):
            return subprocess.run(["python3", "-B", str(eds.__file__), *map(str, args)], capture_output=True,
                                  text=True, env=env)
        r = cli("sync", "--root", self.raiz, "--state", estado, "--now", QUANDO_ISO, "--commit", "abc1234",
                "--to-dir", destino, "--remote")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("staging criar infra/staging/.env", r.stdout)
        self.assertIn("production criar infra/prod/.env", r.stdout)
        self.assertEqual(set(json.loads(estado.read_text())["remote_checked_at"]), {"staging", "production"})
        self.assertEqual(stat.S_IMODE(estado.stat().st_mode), 0o600)
        r = cli("status", "--root", self.raiz, "--to-dir", destino, "--remote")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ok\tstaging\tinfra/staging/.env", r.stdout)
        self.assertIn("ok\tproduction\tinfra/prod/.env", r.stdout)
        bloco = destino / "staging" / "infra" / "staging" / ".env.html"
        bloco.write_text(bloco.read_text(encoding="utf-8").replace("REMOTO=", "REMOTX="), encoding="utf-8")
        r = cli("status", "--root", self.raiz, "--to-dir", destino, "--remote")
        self.assertEqual(r.returncode, 3)
        self.assertIn("diverge\tstaging\tinfra/staging/.env", r.stdout)
        for saida in (r.stdout, r.stderr):
            self.assertNotIn(SENHA, saida)

    def test_cli_sync_remote_com_rede_fora_sai_1_sem_marcar_ausente(self):
        (self.bin / "ssh").write_text("#!/bin/sh\nexit 255\n", encoding="utf-8")
        estado = Path(self.tmp.name) / "estado.json"
        env = {**os.environ, **self.ambiente}
        r = subprocess.run(["python3", "-B", str(eds.__file__), "sync", "--root", str(self.raiz), "--state", str(estado),
                            "--now", QUANDO_ISO, "--commit", "abc1234", "--to-dir", str(Path(self.tmp.name) / "d"),
                            "--remote"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("staging", r.stderr)
        self.assertEqual(set(json.loads(estado.read_text())["environments"]), {"development"})


class SyncSemRemote(unittest.TestCase):
    def test_sync_sem_remote_avisa_que_os_remotos_ficaram_de_fora(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = criar_repo(Path(tmp) / "repo", {".env": "A=1\n"}, config=config_com_remotos())
            r = rodar_cli("sync", "--root", raiz, "--state", Path(tmp) / "e.json", "--now", QUANDO_ISO,
                          "--commit", "abc1234", "--to-dir", Path(tmp) / "d")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("fora desta rodada: staging, production (use --remote)", r.stdout)


if __name__ == "__main__":
    unittest.main()
