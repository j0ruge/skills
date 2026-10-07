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
import json
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

    def scan(self) -> dict:
        """Como a Fase A manda: o diff no stdin, a partir da raiz do repo."""
        diff = git(self.repo, "diff", "HEAD~1...HEAD", "--unified=0")
        out = subprocess.run([sys.executable, str(SCRIPT)], input=diff, cwd=self.repo,
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
