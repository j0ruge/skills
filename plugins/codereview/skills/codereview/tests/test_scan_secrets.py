#!/usr/bin/env python3
"""Testes do scripts/scan_secrets.py (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_scan_secrets.py

Os scanners externos só podem ver as linhas que o diff acrescenta. Até a 2.13.0
eles varriam a pasta do repo inteira: num PR que só mudava `app.py`, um `.env`
ignorado pelo git saía como achado e forçava a nota F, e num repo grande o
gitleaks estourava os 60 s (medido em 2026-10-07). Os testes com o gitleaks de
verdade são pulados quando ele não está no PATH; os do filtro de escopo usam um
scanner simulado e valem sem ele.

O token de teste é gerado na hora: nenhum literal com cara de credencial fica
neste arquivo.
"""
import hashlib
import json
import os
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "scan_secrets.py"
sys.path.insert(0, str(SCRIPT.parent))
import scan_secrets  # noqa: E402

TEM_GITLEAKS = shutil.which("gitleaks") is not None


def token_falso() -> str:
    """Um PAT do GitHub com o formato certo e valor aleatório."""
    alfabeto = string.ascii_letters + string.digits
    return "ghp_" + "".join(secrets.choice(alfabeto) for _ in range(36))


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


class RepoComPR(unittest.TestCase):
    """Repo descartável com um commit base; cada teste monta o PR por cima dele."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test-scan-secrets-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "teste@example.com")
        git(self.repo, "config", "user.name", "teste")
        (self.repo / ".gitignore").write_text(".env\n")
        (self.repo / "app.py").write_text("print('ola')\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "base")

    def commit_pr(self):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "pr")

    def scan(self, *opcoes: str) -> dict:
        """Como a Fase A manda: o diff no stdin, a partir da raiz do repo."""
        diff = git(self.repo, "diff", "HEAD~1...HEAD", "--unified=0")
        out = subprocess.run([sys.executable, str(SCRIPT), *opcoes], input=diff, cwd=self.repo,
                             capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def do_gitleaks(self, res: dict) -> list[tuple[str, int]]:
        self.assertIn("gitleaks", res["scanners"], res["errors"])   # rodou de fato
        return [(f["file"], f["line"]) for f in res["findings"] if f["source"] == "gitleaks"]

    def pr_com_token_na_linha_3(self) -> None:
        (self.repo / "sub").mkdir()
        (self.repo / "sub" / "cfg.py").write_text(f'import os\n\nx = "{token_falso()}"\n')
        self.commit_pr()


@unittest.skipUnless(TEM_GITLEAKS, "gitleaks fora do PATH")
class TestGitleaksVeSoODiff(RepoComPR):

    def test_segredo_fora_do_diff_nao_entra(self):
        (self.repo / ".env").write_text(f"GITHUB_TOKEN={token_falso()}\n")   # ignorado e fora do PR
        (self.repo / "app.py").write_text("print('ola')\nprint('tchau')\n")
        self.commit_pr()
        self.assertEqual(self.do_gitleaks(self.scan()), [])

    def test_segredo_no_diff_sai_com_arquivo_e_linha(self):
        self.pr_com_token_na_linha_3()
        self.assertEqual(self.do_gitleaks(self.scan()), [("sub/cfg.py", 3)])

    def test_gitleaksignore_do_repo_continua_valendo(self):
        (self.repo / ".gitleaksignore").write_text("sub/cfg.py:github-pat:3\n")
        self.pr_com_token_na_linha_3()
        self.assertEqual(self.do_gitleaks(self.scan()), [])

    def test_gitleaks_toml_do_repo_continua_valendo(self):
        (self.repo / ".gitleaks.toml").write_text(
            "[extend]\nuseDefault = true\n\n[allowlist]\npaths = ['''sub/cfg\\.py''']\n")
        self.pr_com_token_na_linha_3()
        self.assertEqual(self.do_gitleaks(self.scan()), [])


@unittest.skipUnless(TEM_GITLEAKS, "gitleaks fora do PATH")
class TestTypedHashManifest(RepoComPR):
    """O hash tipado evita falso positivo sem excluir o próprio manifesto do scan."""

    def _manifest(self, typed: bool, canary: bool = False) -> Path:
        """Monta os dados do zero; o eventual canário só existe no repo descartável."""
        source = self.repo / "artifacts/api-index.json"
        source.parent.mkdir()
        source.write_text(json.dumps({"kind": "fixture"}) + "\n")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        record = {"sha256": digest} if typed else digest
        data = {"artifacts/api-index.json": record}
        if canary:
            data["probe"] = token_falso()
        manifest = self.repo / "hashes.json"
        manifest.write_text(json.dumps(data, indent=2) + "\n")
        return manifest

    def test_original_hash_reproduces_false_positive(self):
        manifest = self._manifest(typed=False)
        digest = json.loads(manifest.read_text())["artifacts/api-index.json"]
        self.assertEqual(digest, hashlib.sha256(
            (self.repo / "artifacts/api-index.json").read_bytes()).hexdigest())
        self.commit_pr()
        result = self.scan()
        self.assertEqual(result["errors"], [])
        self.assertIn("gitleaks", result["scanners"])
        self.assertEqual([(f["file"], f["kind"]) for f in result["findings"]
                          if f["source"] == "gitleaks"], [("hashes.json", "generic-api-key")])

    def test_typed_hash_passes_without_allowlist(self):
        self._manifest(typed=True)
        self.commit_pr()
        result = self.scan()
        self.assertEqual(result["errors"], [])
        self.assertIn("gitleaks", result["scanners"])
        self.assertEqual(result["findings"], [])

    def test_canary_in_same_typed_manifest_is_still_detected(self):
        self._manifest(typed=True, canary=True)
        self.commit_pr()
        result = self.scan()
        self.assertEqual(result["errors"], [])
        self.assertIn("gitleaks", result["scanners"])
        self.assertEqual([(f["file"], f["kind"]) for f in result["findings"]
                          if f["source"] == "gitleaks"], [("hashes.json", "github-pat")])


class TestQuantoLeu(RepoComPR):
    """O scan diz quanto leu, e a entrada vazia não passa por limpa.

    Até a 2.18.6, `printf '' | scan_secrets.sh` saía com 0 achados, `errors: []` e rc 0, e o
    relatório leria PASS. Um pathspec que o zsh não divide (`-- $P`) entrega o diff vazio sem
    erro nenhum (medido em 2026-10-18).
    """

    def rodar_stdin(self, entrada: str) -> dict:
        out = subprocess.run([sys.executable, str(SCRIPT), "--no-external"], input=entrada,
                             capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def test_entrada_vazia_e_erro(self):
        res = self.rodar_stdin("")
        self.assertEqual(res["scanned"], {"files": 0, "added_lines": 0})
        self.assertEqual(len(res["errors"]), 1)
        self.assertTrue(res["errors"][0].startswith("empty input:"), res["errors"])

    def test_entrada_so_com_espacos_tambem(self):
        self.assertTrue(self.rodar_stdin("\n \n")["errors"][0].startswith("empty input:"))

    def test_conta_cada_arquivo_do_diff_e_as_linhas_acrescentadas(self):
        (self.repo / "app.py").write_text("")   # só remoção: arquivo do diff sem linha `+`
        (self.repo / "novo.py").write_text("a = 1\nb = 2\n")
        (self.repo / "logo.bin").write_bytes(b"\x00\x01")   # binário: `diff --git` sem `+++`
        self.commit_pr()
        res = self.scan("--no-external")
        self.assertEqual(res["scanned"], {"files": 3, "added_lines": 2})
        self.assertEqual(res["errors"], [])

    def test_diff_sem_cabecalho_git_conta_pelo_mais_mais_mais(self):
        diff = "+++ b/a.py\n@@ -0,0 +1,2 @@\n+x\n+y\n+++ /dev/null\n@@ -1 +0,0 @@\n-z\n"
        self.assertEqual(scan_secrets.scan_diff(diff).scanned, {"files": 2, "added_lines": 2})


class TestSenhaInterpoladaNaConnectionString(unittest.TestCase):
    """A senha de uma connection string que é só a interpolação de uma variável é lida na hora de rodar.

    Até a 2.27.33 a exceção do `${…}` olhava o casamento inteiro, que começa no esquema, e nunca
    a senha: o `DATABASE_URL` de um compose, com a senha vinda do `.env`, saía CRITICAL e forçava a
    nota F sem segredo nenhum (medido em 2026-11-09, num monorepo privado). O esquema e a
    URL são montados aqui na hora, para que este arquivo não carregue a forma que o padrão procura.
    """

    ESQUEMA = "postgres" + "ql"

    def achados(self, senha: str) -> list:
        """Varre um diff de uma linha de compose com a senha dada e devolve só os achados desse padrão."""
        url = f"{self.ESQUEMA}://app:{senha}@db:5432/app"
        diff = f"diff --git a/c.yml b/c.yml\n--- /dev/null\n+++ b/c.yml\n@@ -0,0 +1 @@\n+  DATABASE_URL: {url}\n"
        return [f for f in scan_secrets.scan_diff(diff).findings if f.kind == "Credentialed Connection String"]

    @staticmethod
    def aleatoria() -> str:
        """Uma senha nova a cada chamada, para nenhum literal ficar neste arquivo."""
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

    def test_senha_que_e_interpolacao_nao_vira_achado(self):
        formas = ("${APP_DB_PASSWORD}", "${APP_DB_PASSWORD:?defina-no-env}", "${APP_DB_PASSWORD:-}", "<senha>")
        for forma in formas:
            with self.subTest(forma):
                self.assertEqual(self.achados(forma), [])

    def test_canario_com_senha_literal_segue_achado(self):
        # Sem este, um conserto que desligasse o padrão passaria nos casos acima.
        senha = self.aleatoria()
        achados = self.achados(senha)
        self.assertEqual(len(achados), 1)
        self.assertEqual(achados[0].severity, "CRITICAL")
        self.assertNotIn(senha, achados[0].snippet)

    def test_padrao_nao_vazio_e_senha_escrita_na_linha(self):
        # `${X:-valor}` cai no valor quando a variável falta: é uma senha literal no arquivo. Até a
        # 2.27.33 ela saía achado (porque nada ali era julgado), e o conserto não pode calá-la.
        for forma in (f"${{APP_DB_PASSWORD:-{self.aleatoria()}}}", f"${{APP_DB_PASSWORD-{self.aleatoria()}}}"):
            with self.subTest(forma):
                self.assertEqual(len(self.achados(forma)), 1)


class TestLeituraEmTempoDeExecucao(unittest.TestCase):
    """Variável de shell sem chaves e expressão Jinja como valor inteiro são leitura em tempo de execução.

    Até a 2.27.38 só a forma com chaves era isenta: num repositório de playbooks, 8 das 10 linhas
    acusadas liam a senha de uma variável e forçaram a nota F sem credencial nenhuma (medido em
    2026-11-12). A linha é montada aqui na hora, para este arquivo não carregar a forma procurada.
    """

    CHAVE = "DB_" + "PASS" + "WORD"

    def achados(self, valor: str, caminho: str = "tasks/main.yml") -> list:
        """Varre um diff de uma linha `CHAVE=<valor>` no caminho dado e devolve os achados do padrão."""
        diff = (f"diff --git a/{caminho} b/{caminho}\n--- /dev/null\n+++ b/{caminho}\n"
                f"@@ -0,0 +1 @@\n+    {self.CHAVE}={valor}\n")
        return [f for f in scan_secrets.scan_diff(diff).findings if f.kind == "Generic Password"]

    @staticmethod
    def aleatoria() -> str:
        """Um valor novo a cada chamada, para nenhum literal ficar neste arquivo."""
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

    def test_variavel_de_ambiente_sem_chaves_nao_vira_achado(self):
        self.assertEqual(self.achados('"$APP_DB_SENHA"'), [])

    def test_variavel_minuscula_so_e_isenta_em_arquivo_de_shell(self):
        self.assertEqual(self.achados('"$senha_lida"', "scripts/roda.sh"), [])
        self.assertEqual(self.achados('"$senha_lida"', "bin/roda"), [])
        # Fora de shell, cifrão e letras minúsculas podem ser a própria senha.
        self.assertEqual(len(self.achados('"$senha_lida"', "config/app.json")), 1)

    def test_aspas_simples_nao_expandem_no_shell(self):
        self.assertEqual(len(self.achados("'$APP_DB_SENHA'", "scripts/roda.sh")), 1)

    def test_expressao_jinja_inteira_nao_vira_achado(self):
        for forma in ("'{{ senha_do_banco }}'", '"{{ item.senha | quote }}"', "'{{senha}}'"):
            with self.subTest(forma):
                self.assertEqual(self.achados(forma), [])

    def test_padrao_literal_dentro_do_jinja_segue_achado(self):
        # O valor de reserva está escrito na linha, como no `${X:-valor}`.
        forma = "'{{ senha | default(\"" + self.aleatoria() + "\") }}'"
        self.assertEqual(len(self.achados(forma)), 1)

    def test_literal_com_cifrao_ou_chaves_no_meio_segue_achado(self):
        for forma in (f'"${self.aleatoria()}-{self.aleatoria()}"', f'"{self.aleatoria()}$APP_DB_SENHA"',
                      f'"x{{{{ {self.aleatoria()} }}}}y"'):
            with self.subTest(forma):
                self.assertEqual(len(self.achados(forma)), 1)

    def test_canario_literal_segue_achado(self):
        senha = self.aleatoria()
        achados = self.achados(f'"{senha}"')
        self.assertEqual(len(achados), 1)
        self.assertNotIn(senha, achados[0].snippet)


class TestDiffForaDoAscii(unittest.TestCase):
    """O stdin do Windows (cp1252 com surrogateescape) e os cabeçalhos `+++` com TAB e com aspas."""

    def rodar(self, diff: bytes, *opcoes: str) -> dict:
        ambiente = {**os.environ, "PYTHONIOENCODING": "cp1252:surrogateescape"}
        out = subprocess.run([sys.executable, str(SCRIPT), *opcoes], input=diff, capture_output=True,
                             env=ambiente, cwd=tempfile.gettempdir())
        self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8", "replace")[-300:])
        return json.loads(out.stdout.decode("utf-8"))

    def test_letra_que_cp1252_nao_tem_nao_derruba_a_varredura(self):
        for letra in ("Á", "Í", "Ð", "א"):
            with self.subTest(letra):
                diff = f"diff --git a/x.md b/x.md\n--- /dev/null\n+++ b/x.md\n@@ -0,0 +1 @@\n+{letra}\n".encode("utf-8")
                saida = self.rodar(diff)
                self.assertEqual(saida["errors"], [])
                self.assertEqual(saida["scanned"]["added_lines"], 1)

    def test_achado_em_arquivo_fora_do_cp1252_sai_em_utf8(self):
        # Pelo stdin em cp1252 a letra faz ida e volta e o print não cai; pelo --diff ela chega de verdade.
        linha = f'token = "{token_falso()}"'
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "x.diff"
            arquivo.write_bytes(f"diff --git a/x.md b/x.md\n+++ b/\u1e25.md\n@@ -0,0 +1 @@\n+{linha}\n".encode("utf-8"))
            saida = self.rodar(b"", "--diff", str(arquivo), "--no-external")
        self.assertEqual(saida["findings"][0]["file"], "\u1e25.md")

    def test_caminho_com_espaco_perde_o_tab(self):
        diff = "+++ b/pasta com espaço/x y.md\t\n@@ -0,0 +1 @@\n+oi\n"
        self.assertEqual(list(scan_secrets.iter_added_lines(diff)), [("pasta com espaço/x y.md", 1, "oi")])

    def test_caminho_entre_aspas_e_do_arquivo_certo(self):
        diff = ('+++ b/antes.md\n@@ -0,0 +1 @@\n+a\n'
                '+++ "b/ARQUEOL\\303\\223GICOS \\"x\\".md"\t\n@@ -0,0 +1 @@\n+b\n')
        self.assertEqual(list(scan_secrets.iter_added_lines(diff)),
                         [("antes.md", 1, "a"), ('ARQUEOLÓGICOS "x".md', 1, "b")])

    def test_base_le_o_diff_em_utf8(self):
        feito = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with mock.patch.object(scan_secrets.subprocess, "run", return_value=feito) as run:
            scan_secrets.get_diff_text(scan_secrets.parse_args(["--base", "main"]))
        self.assertEqual(run.call_args.kwargs.get("encoding"), "utf-8")
        self.assertEqual(run.call_args.kwargs.get("errors"), "replace")

    def test_escape_que_o_git_nao_emite_nao_derruba_a_varredura(self):
        # Uma linha acrescentada `++ "b/..."` vira `+++ "b/..."` no diff e é lida como cabeçalho.
        for caminho in ("\\\u1e25.md", "\\777.md", "x\\"):
            with self.subTest(caminho):
                diff = f'diff --git a/x b/x\n+++ "b/{caminho}"\n@@ -0,0 +1 @@\n+oi\n'.encode("utf-8")
                saida = self.rodar(diff)
                self.assertEqual(saida["scanned"]["added_lines"], 1)
                self.assertEqual(saida["errors"], [])

    def test_caminho_com_nul_avisa_que_os_externos_nao_rodaram(self):
        diff = b'diff --git a/x b/x\n+++ "b/x\\000.md"\n@@ -0,0 +1 @@\n+oi\n'
        saida = self.rodar(diff)
        self.assertEqual(saida["scanned"]["added_lines"], 1)
        self.assertTrue(any("external scanners" in e for e in saida["errors"]), saida["errors"])


class TestMaterializar(unittest.TestCase):

    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="test-materializar-"))
        self.addCleanup(shutil.rmtree, self.pasta, True)

    def test_cada_linha_no_numero_dela(self):
        diff = "+++ b/a/b.py\n@@ -0,0 +3,2 @@\n+linha3\n+linha4\n"
        escopo = scan_secrets.materialize_added_lines(diff, str(self.pasta))
        self.assertEqual(escopo, {"a/b.py": {3, 4}})
        self.assertEqual((self.pasta / "a" / "b.py").read_text().splitlines(),
                         ["", "", "linha3", "linha4"])

    def test_caminho_que_sai_da_pasta_nao_e_gravado(self):
        diff = ("+++ b/../fora.py\n@@ -0,0 +1 @@\n+x\n"
                "+++ b//tmp/absoluto.py\n@@ -0,0 +1 @@\n+y\n")
        self.assertEqual(scan_secrets.materialize_added_lines(diff, str(self.pasta)), {})
        self.assertFalse((self.pasta.parent / "fora.py").exists())


class TestFiltroDeEscopo(unittest.TestCase):
    """Scanner simulado: o que vier de fora das linhas acrescentadas não entra."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="test-escopo-")
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.escopo = {"app.py": {2}}

    def rodar(self, funcao, saida: str):
        resultado = scan_secrets.ScanResult()
        feito = subprocess.CompletedProcess([], 1, stdout=saida, stderr="")
        with mock.patch.object(scan_secrets.shutil, "which", return_value="/bin/scanner"), \
                mock.patch.object(scan_secrets.subprocess, "run", return_value=feito) as run:
            funcao(resultado)
        return resultado, run

    def test_gitleaks_roda_na_pasta_do_escopo_e_filtra(self):
        saida = json.dumps([
            {"File": ".env", "StartLine": 1, "RuleID": "github-pat", "Description": "d"},
            {"File": "app.py", "StartLine": 5, "RuleID": "github-pat", "Description": "d"},
            {"File": "app.py", "StartLine": 2, "RuleID": "github-pat", "Description": "d"},
        ])
        res, run = self.rodar(
            lambda r: scan_secrets.run_gitleaks(".", self.pasta, self.escopo, r), saida)
        self.assertEqual([(f.file, f.line) for f in res.findings], [("app.py", 2)])
        args, kwargs = run.call_args
        self.assertEqual(kwargs["cwd"], self.pasta)
        self.assertEqual(args[0][args[0].index("--source") + 1], ".")

    def test_ggshield_recebe_a_pasta_do_escopo_e_filtra(self):
        def entidade(nome, linha):
            return {"filename": f"{self.pasta}/{nome}", "incidents": [
                {"type": "t", "occurrences": [{"line_start": linha, "matches": [{"match": "m"}]}]}]}
        saida = json.dumps({"entities_with_incidents": [entidade("outro.py", 1),
                                                        entidade("app.py", 2)]})
        res, run = self.rodar(
            lambda r: scan_secrets.run_ggshield(self.pasta, self.escopo, r), saida)
        self.assertEqual([(f.file, f.line) for f in res.findings], [("app.py", 2)])
        self.assertIn(self.pasta, run.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
