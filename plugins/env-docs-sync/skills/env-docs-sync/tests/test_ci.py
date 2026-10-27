"""A seção CI/CD: o leitor de workflow (sem PyYAML), os nomes do gh e a renderização."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import CANARIO, SCRIPT, config_exemplo, criar_arvore, eds, gh_falso

CD = """\
# comentário de topo
name: cd-staging

on:
  push:
    branches: [develop]
    runs-on: isto-nao-e-job

env:
  runs-on: nem-isto

jobs:
  build:
    runs-on: [self-hosted, staging]
    steps:
      - run: |
          echo "runs-on: dentro-do-script"
        runs-on: nem-isto-no-passo
  preflight:
    # runs-on: comentado
    runs-on: ubuntu-latest   # comentário no fim
  deploy:
    needs: [build]
    runs-on: "self-hosted"
    environment: staging
"""


class LerWorkflow(unittest.TestCase):
    def jobs(self, texto):
        return [(j.id, j.runs_on, j.environment) for j in eds.ler_workflow(texto, "w.yml").jobs]

    def test_nome_jobs_runs_on_e_environment_na_ordem_do_arquivo(self):
        wf = eds.ler_workflow(CD, ".github/workflows/cd-staging.yml")
        self.assertEqual(wf.nome, "cd-staging")
        self.assertEqual(wf.arquivo, ".github/workflows/cd-staging.yml")
        self.assertEqual([(j.id, j.runs_on, j.environment) for j in wf.jobs], [
            ("build", "self-hosted, staging", None),
            ("preflight", "ubuntu-latest", None),
            ("deploy", "self-hosted", "staging"),
        ])

    def test_sem_name_o_nome_e_o_arquivo(self):
        self.assertEqual(eds.ler_workflow("jobs:\n  a:\n    runs-on: x\n", "ci/w.yml").nome, "ci/w.yml")

    def test_runs_on_em_lista_de_bloco(self):
        texto = "jobs:\n  a:\n    runs-on:\n      - self-hosted\n      - 'linux'\n    steps: []\n"
        self.assertEqual(self.jobs(texto), [("a", "self-hosted, linux", None)])

    def test_runs_on_em_lista_de_bloco_no_nivel_da_chave(self):
        texto = "jobs:\n  a:\n    runs-on:\n    - self-hosted\n    - linux\n    environment: e\n"
        self.assertEqual(self.jobs(texto), [("a", "self-hosted, linux", "e")])

    def test_runs_on_em_mapa_de_fluxo_vira_interrogacao(self):
        self.assertEqual(self.jobs("jobs:\n  a:\n    runs-on: { group: g }\n"), [("a", "?", None)])

    def test_environment_em_mapa_usa_o_name(self):
        texto = ("jobs:\n  a:\n    runs-on: x\n    environment:\n      url: https://exemplo.invalid\n"
                 "      name: production\n")
        self.assertEqual(self.jobs(texto), [("a", "x", "production")])

    def test_expressao_fica_como_esta(self):
        texto = "jobs:\n  a:\n    runs-on: ${{ matrix.os }}\n"
        self.assertEqual(self.jobs(texto), [("a", "${{ matrix.os }}", None)])

    def test_forma_que_o_leitor_nao_entende_vira_interrogacao(self):
        texto = "jobs:\n  a:\n    runs-on:\n      group: grandes\n      labels: [big]\n"
        self.assertEqual(self.jobs(texto), [("a", "?", None)])

    def test_job_reusavel_sem_runs_on(self):
        texto = "jobs:\n  a:\n    uses: ./.github/workflows/outro.yml\n  b:\n    runs-on: x\n"
        self.assertEqual(self.jobs(texto), [("a", None, None), ("b", "x", None)])

    def test_indentacao_de_quatro(self):
        texto = "name: w\njobs:\n    a:\n        runs-on: x\n        environment: e\n    b:\n        runs-on: y\n"
        self.assertEqual(self.jobs(texto), [("a", "x", "e"), ("b", "y", None)])

    def test_sem_jobs(self):
        self.assertEqual(self.jobs("name: vazio\non: push\n"), [])

    def test_aspas_e_comentario_no_nome(self):
        self.assertEqual(eds.ler_workflow('name: "CI # não é comentário"  # é\njobs: {}\n', "w").nome,
                         "CI # não é comentário")


class WorkflowsDoRepo(unittest.TestCase):
    def test_le_yml_e_yaml_do_topo_da_pasta_em_ordem(self):
        with tempfile.TemporaryDirectory() as raiz:
            criar_arvore(raiz, {
                ".github/workflows/b.yaml": "name: b\njobs:\n  j:\n    runs-on: x\n",
                ".github/workflows/a.yml": "name: a\njobs: {}\n",
                ".github/workflows/notas.md": "name: nao\n",
                ".github/workflows/sub/c.yml": "name: c\n",
            })
            wfs = eds.workflows_do_repo(Path(raiz), ".github/workflows")
        self.assertEqual([(w.arquivo, w.nome) for w in wfs],
                         [(".github/workflows/a.yml", "a"), (".github/workflows/b.yaml", "b")])

    def test_pasta_ausente_e_lista_vazia(self):
        with tempfile.TemporaryDirectory() as raiz:
            self.assertEqual(eds.workflows_do_repo(Path(raiz), ".github/workflows"), [])


class GhFalso:
    """Responde por argv; guarda (argv, cwd) de cada chamada. O stderr leva o canário."""

    def __init__(self, respostas, rc=None):
        self.respostas, self.rc, self.chamadas = respostas, rc or {}, []

    def __call__(self, argv, *, env, timeout, entrada=None, cwd=None):
        chave = " ".join(argv[1:])
        self.chamadas.append((chave, cwd))
        if chave not in self.respostas:
            raise AssertionError(f"chamada inesperada: {chave}")
        return eds.ResultadoComando(self.rc.get(chave, 0), self.respostas[chave].encode(), b"stderr " + CANARIO.encode())


AMBIENTES_GH = "api repos/{owner}/{repo}/environments --paginate --jq .environments[].name"
RESPOSTAS_GH = {
    "secret list --json name": '[{"name": "REPO_B"}, {"name": "REPO_A"}]',
    "variable list --json name": '[{"name": "RUNNER"}]',
    AMBIENTES_GH: "staging\nproduction\n",
    "secret list --env production --json name": '[{"name": "DB_PASS"}]',
    "variable list --env production --json name": "[]",
    "secret list --env staging --json name": '[{"name": "SSH_KEY"}, {"name": "DB_PASS"}]',
    "variable list --env staging --json name": "[]",
}


class NomesDoGh(unittest.TestCase):
    def nomes(self, runner, raiz=Path("/repo")):
        return eds.nomes_do_gh(raiz, eds.Contexto(runner=runner, ambiente={"PATH": "/bin"}))

    def test_repositorio_e_cada_environment_em_ordem_com_nomes_ordenados(self):
        gh = GhFalso(RESPOSTAS_GH)
        self.assertEqual(self.nomes(gh), [
            eds.NomesDoCi("repositório", ("REPO_A", "REPO_B"), ("RUNNER",)),
            eds.NomesDoCi("production", ("DB_PASS",), ()),
            eds.NomesDoCi("staging", ("DB_PASS", "SSH_KEY"), ()),
        ])
        self.assertEqual({cwd for _, cwd in gh.chamadas}, {Path("/repo")})

    def test_falha_do_gh_e_erro_sem_ecoar_o_stderr(self):
        gh = GhFalso(RESPOSTAS_GH, rc={"secret list --env staging --json name": 1})
        with self.assertRaises(eds.ErroEnvDocs) as ctx:
            self.nomes(gh)
        self.assertIn("gh secret list", str(ctx.exception))
        self.assertNotIn(CANARIO, str(ctx.exception))

    def test_saida_que_nao_e_lista_de_nomes_e_erro(self):
        for saida in ("não é json", '{"name": "A"}', '[{"nome": "A"}]', '[{"name": "<b>A</b>"}]'):
            with self.subTest(saida=saida):
                with self.assertRaises(eds.ErroEnvDocs):
                    self.nomes(GhFalso({**RESPOSTAS_GH, "variable list --json name": saida}))

    def test_sem_environments(self):
        gh = GhFalso({**RESPOSTAS_GH, AMBIENTES_GH: ""})
        self.assertEqual([n.escopo for n in self.nomes(gh)], ["repositório"])


WORKFLOWS = [
    eds.WorkflowDoCi(".github/workflows/cd.yml", "cd <prod>", (
        eds.JobDoCi("build", "self-hosted, staging", None),
        eds.JobDoCi("deploy", "self-hosted, production", "production"),
    )),
    eds.WorkflowDoCi(".github/workflows/reuso.yml", "reuso", (eds.JobDoCi("chama", None, None),)),
]
NOMES = [eds.NomesDoCi("repositório", ("A", "B"), ()), eds.NomesDoCi("production", ("DB_PASS",), ("URL",))]
CI = {"workflows": ".github/workflows", "secrets": "gh"}


class SecaoCiCd(unittest.TestCase):
    def test_uma_linha_por_job_com_escape(self):
        secao = eds.secao_ci_cd(CI, WORKFLOWS, NOMES)
        self.assertIn("<h3>Workflows</h3>", secao)
        self.assertIn("<tr><td>cd &lt;prod&gt;</td><td><code>.github/workflows/cd.yml</code></td><td>build</td>"
                      "<td>self-hosted, staging</td><td>—</td></tr>", secao)
        self.assertIn("<td>deploy</td><td>self-hosted, production</td><td>production</td></tr>", secao)
        self.assertIn("<td>chama</td><td>—</td><td>—</td></tr>", secao)

    def test_nomes_por_escopo_nunca_valores(self):
        secao = eds.secao_ci_cd(CI, WORKFLOWS, NOMES)
        self.assertIn("<h3>Segredos e variáveis (só nomes)</h3>", secao)
        self.assertIn("<tr><td>repositório</td><td><code>A</code>, <code>B</code></td><td>—</td></tr>", secao)
        self.assertIn("<tr><td>production</td><td><code>DB_PASS</code></td><td><code>URL</code></td></tr>", secao)

    def test_sem_ci_declarado(self):
        self.assertIn("ci: null", eds.secao_ci_cd(None, None, None))

    def test_nenhum_workflow_e_segredos_nao_consultados(self):
        secao = eds.secao_ci_cd({"workflows": ".github/workflows", "secrets": None}, [], None)
        self.assertIn("Nenhum workflow em <code>.github/workflows</code>", secao)
        self.assertIn("ci.secrets: null", secao)
        self.assertNotIn("<table>", secao)

    def test_workflows_nao_declarados(self):
        secao = eds.secao_ci_cd({"workflows": None, "secrets": "gh"}, None, NOMES)
        self.assertIn("ci.workflows: null", secao)
        self.assertIn("<code>DB_PASS</code>", secao)


class CiCdDoRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        criar_arvore(self.raiz, {".github/workflows/cd.yml": "name: cd\njobs:\n  deploy:\n    runs-on: x\n"})

    def tearDown(self):
        self.tmp.cleanup()

    def ci_cd(self, ci, runner):
        cfg = config_exemplo()
        cfg["ci"] = ci
        return eds.ci_cd_do_repo(self.raiz, cfg, eds.Contexto(runner=runner, ambiente={"PATH": "/bin"}))

    def test_workflows_do_disco_e_nomes_do_gh(self):
        secao = self.ci_cd(CI, GhFalso(RESPOSTAS_GH))
        self.assertIn("<td>cd</td><td><code>.github/workflows/cd.yml</code></td><td>deploy</td><td>x</td>", secao)
        self.assertIn("<code>SSH_KEY</code>", secao)

    def test_sem_gh_declarado_nao_chama_o_gh(self):
        gh = GhFalso({})
        secao = self.ci_cd({"workflows": ".github/workflows", "secrets": None}, gh)
        self.assertEqual(gh.chamadas, [])
        self.assertIn("<td>deploy</td>", secao)

    def test_ci_nulo_nao_le_nada(self):
        gh = GhFalso({})
        self.assertIn("ci: null", self.ci_cd(None, gh))
        self.assertEqual(gh.chamadas, [])


class RenderPageComCi(unittest.TestCase):
    """`render-page` pela CLI, com um `gh` falso no PATH: a seção sai dos workflows e do gh."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.raiz, self.saida, self.bin = base / "repo", base / "pagina.html", base / "bin"
        criar_arvore(self.raiz, {".env": f"P={CANARIO}\n",
                                 ".github/workflows/cd.yml": "name: cd\njobs:\n  deploy:\n    runs-on: x\n"})
        (self.raiz / ".env-docs.json").write_text(json.dumps(config_exemplo()), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def render(self, rc):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "render-page", "--root", str(self.raiz),
                            "--out", str(self.saida)], capture_output=True, text=True,
                           env={**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}"})
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)
        return r

    def test_secao_ci_cd_com_workflows_e_nomes(self):
        gh_falso(self.bin, RESPOSTAS_GH)
        self.render(0)
        pagina = self.saida.read_text(encoding="utf-8")
        secao = pagina.split("<h2>CI/CD</h2>", 1)[1].split("<h2>", 1)[0]
        self.assertIn("<td>deploy</td><td>x</td>", secao)
        self.assertIn("<tr><td>staging</td><td><code>DB_PASS</code>, <code>SSH_KEY</code></td><td>—</td></tr>", secao)
        self.assertNotIn("a gerar", pagina)

    def test_gh_que_falha_nao_grava_a_pagina(self):
        gh_falso(self.bin, {})
        r = self.render(1)
        self.assertIn("gh", r.stderr)
        self.assertFalse(self.saida.exists())


if __name__ == "__main__":
    unittest.main()
