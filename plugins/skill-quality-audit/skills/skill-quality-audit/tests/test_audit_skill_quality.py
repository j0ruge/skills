#!/usr/bin/env python3
"""Testes do scripts/audit_skill_quality.py (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_audit_skill_quality.py

Cada teste monta fixtures num diretório temporário e roda o script como
subprocesso, com HOME e HERMES_HOME apontando para o temporário, para provar
que nada depende de paths da máquina onde a skill foi escrita.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "audit_skill_quality.py"

VALID_SKILL_MD = textwrap.dedent("""\
    ---
    name: {name}
    description: >-
      Use when testar o auditor com uma skill valida.
    metadata:
      hermes:
        tags:
          - teste
        related_skills:
          - outra-skill
    ---

    # Skill de teste

    Leia `references/guia.md` quando precisar do detalhe.
    Rode `python3 scripts/ferramenta.py --help`.
    """)


def make_skill(root, name, skill_md=None, files=None, changelog=True):
    d = Path(root) / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(skill_md if skill_md is not None else VALID_SKILL_MD.format(name=name),
                                encoding="utf-8")
    if changelog:
        (d / "CHANGELOG.md").write_text("# Changelog\n\n## 2026-01-01 - criacao\n", encoding="utf-8")
    default_files = {
        "references/guia.md": "# Guia\n\nDetalhe.\n",
        "scripts/ferramenta.py": "#!/usr/bin/env python3\nprint('ok')\n",
    }
    for rel, content in (files if files is not None else default_files).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return d


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sqa-test-")
        self.tmp = Path(self._tmp.name)
        self.env = dict(os.environ)
        self.env["HOME"] = str(self.tmp / "home")
        self.env["HERMES_HOME"] = str(self.tmp / "hermes-vazio")
        self.env.pop("PYTHONDONTWRITEBYTECODE", None)
        self.env["SQA_NO_UVX"] = "1"  # hermético: G2 via uvx baixaria o pacote; o teste de uvx usa binário falso

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, *args, script=SCRIPT):
        proc = subprocess.run([sys.executable, str(script), *map(str, args)],
                              capture_output=True, text=True, env=self.env, timeout=120)
        return proc.returncode, proc.stdout + proc.stderr


class TestUso(Base):
    def test_help_rc0(self):
        rc, out = self.run_script("--help")
        self.assertEqual(rc, 0, out)
        self.assertIn("--family", out)

    def test_sem_argumentos_rc2(self):
        rc, out = self.run_script()
        self.assertEqual(rc, 2, out)

    def test_caminho_inexistente_rc2(self):
        rc, out = self.run_script(self.tmp / "nao-existe")
        self.assertEqual(rc, 2, out)

    def test_diretorio_sem_skill_md_rc1(self):
        (self.tmp / "vazia").mkdir()
        rc, out = self.run_script(self.tmp / "vazia", "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("A1", out)


class TestSkillValida(Base):
    def test_valida_rc0(self):
        d = make_skill(self.tmp / "skills", "skill-ok")
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("[ERRO]", out)

    def test_json(self):
        d = make_skill(self.tmp / "skills", "skill-ok")
        rc, out = self.run_script(d, "--external", "off", "--format", "json")
        self.assertEqual(rc, 0, out)
        data = json.loads(out)
        self.assertEqual(data["summary"]["rc"], 0)
        self.assertEqual(data["skills"][0]["name"], "skill-ok")

    def test_related_skills_lidas_do_bloco(self):
        d = make_skill(self.tmp / "skills", "skill-ok")
        rc, out = self.run_script(d, "--external", "off", "--format", "json")
        data = json.loads(out)
        self.assertEqual(data["skills"][0]["related_skills"], ["outra-skill"])

    def test_orcamento_de_descricao(self):
        md = VALID_SKILL_MD.format(name="skill-desc").replace(
            "Use when testar o auditor com uma skill valida.",
            "Use when testar o auditor com uma descricao bem mais longa que sessenta caracteres.")
        d = make_skill(self.tmp / "skills", "skill-desc", skill_md=md)
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 0, out)
        self.assertIn("A3", out)
        rc, out = self.run_script(d, "--external", "off", "--desc-budget", "0")
        self.assertNotIn("A3", out)

    def test_strict_transforma_aviso_em_falha(self):
        d = make_skill(self.tmp / "skills", "skill-orfa", files={
            "references/guia.md": "# Guia\n",
            "references/orfa.md": "# Orfa\n",
            "scripts/ferramenta.py": "#!/usr/bin/env python3\nprint('ok')\n",
        })
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 0, out)
        self.assertIn("orfa.md", out)
        rc, out = self.run_script(d, "--external", "off", "--strict")
        self.assertEqual(rc, 1, out)


class TestSkillInvalida(Base):
    def test_varios_defeitos_rc1(self):
        md = textwrap.dedent("""\
            ---
            name: Nome-Errado
            description: Use when testar defeitos.
            tags: [a, b]
            ---

            # Defeituosa

            Veja `references/ausente.md` e `../fora/da/skill.md`.
            """)
        d = make_skill(self.tmp / "skills", "skill-ruim", skill_md=md, changelog=False, files={
            "references/guia.md": "# Guia\n",
            "scripts/quebrado.py": "#!/usr/bin/env python3\ndef x(:\n",
        })
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 1, out)
        for check_id in ("A2", "A4", "A5", "B1", "B3", "B5", "B7"):
            self.assertIn(check_id, out, f"{check_id} ausente na saída:\n{out}")

    def test_sem_frontmatter_rc1(self):
        d = make_skill(self.tmp / "skills", "skill-sem-fm", skill_md="# Sem frontmatter\n")
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("A1", out)

    def test_changelog_opcional(self):
        d = make_skill(self.tmp / "skills", "skill-sem-cl", changelog=False)
        rc, _ = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 1)
        rc, out = self.run_script(d, "--external", "off", "--no-changelog-required")
        self.assertEqual(rc, 0, out)

    def _plugin(self, manifest=True, changelog=True):
        """Layout de marketplace: <plugin>/skills/<skill>/, com o CHANGELOG no nível do plugin."""
        plugin = self.tmp / "plugins" / "meu-plugin"
        d = make_skill(plugin / "skills", "skill-do-plugin", changelog=False)
        if manifest:
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin" / "plugin.json").write_text('{"name": "meu-plugin"}\n', encoding="utf-8")
        if changelog:
            (plugin / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0] - criacao\n", encoding="utf-8")
        return d

    def test_changelog_no_nivel_do_plugin_vale(self):
        rc, out = self.run_script(self._plugin(), "--external", "off")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("CHANGELOG.md ausente", out)
        self.assertIn("B5", out)  # o OK diz onde achou, para o leitor conferir

    def test_changelog_solto_acima_sem_manifesto_nao_vale(self):
        rc, out = self.run_script(self._plugin(manifest=False), "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("CHANGELOG.md ausente", out)

    def test_plugin_sem_changelog_continua_ausente(self):
        rc, out = self.run_script(self._plugin(changelog=False), "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("CHANGELOG.md ausente", out)


class TestRevisaoAdversarial(Base):
    """Casos vindos da revisão adversarial de 2026-09-23."""

    def fm(self, name, extra_fm="", corpo="# Corpo\n"):
        return (f"---\nname: {name}\ndescription: Use when testar.\n{extra_fm}---\n\n{corpo}")

    def test_b4_path_de_maquina_entre_crases(self):
        md = self.fm("skill-b4", corpo="Rode `/home/fulano/.hermes/scripts/x.sh`.\n")
        d = make_skill(self.tmp / "skills", "skill-b4", skill_md=md, files={})
        rc, out = self.run_script(d, "--external", "off")
        self.assertIn("B4 path absoluto de máquina", out)

    def test_aspas_seguidas_de_comentario(self):
        md = "---\ndescription: \"Use when testar.\" # nota\nname: skill-aspas\n---\n\n# Corpo\n"
        d = make_skill(self.tmp / "skills", "skill-aspas", skill_md=md, files={})
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("A2", out)

    def test_dois_pontos_em_valor_plano_e_yaml_invalido(self):
        md = "---\nname: skill-colon\ndescription: Use when: testar\n---\n\n# Corpo\n"
        d = make_skill(self.tmp / "skills", "skill-colon", skill_md=md, files={})
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("A1", out)

    def test_skill_md_nao_utf8(self):
        d = make_skill(self.tmp / "skills", "skill-latin1", files={})
        (d / "SKILL.md").write_bytes(self.fm("skill-latin1", corpo="Configura\xe7\xe3o\n")
                                     .encode("latin-1"))
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("UTF-8", out)

    def test_g2_aceita_binario_agentskills_do_pypi(self):
        d = make_skill(self.tmp / "skills", "skill-ok")
        bindir = self.tmp / "bin"
        bindir.mkdir()
        fake = bindir / "agentskills"
        fake.write_text("#!/bin/sh\necho \"Valid skill: $2\"\n", encoding="utf-8")
        fake.chmod(0o755)
        self.env["PATH"] = str(bindir) + os.pathsep + "/usr/bin" + os.pathsep + "/bin"
        rc, out = self.run_script(d, "--audit-skill-sh", self.tmp / "nao-existe.sh")
        self.assertEqual(rc, 0, out)
        self.assertIn("[OK] G2", out)

    def test_reference_aninhada_ausente(self):
        md = self.fm("skill-sub", corpo="Leia `references/sub/ausente.md` e `references/guia.md`.\n")
        d = make_skill(self.tmp / "skills", "skill-sub", skill_md=md,
                       files={"references/guia.md": "# Guia\n"})
        rc, out = self.run_script(d, "--external", "off")
        self.assertEqual(rc, 1, out)
        self.assertIn("sub/ausente.md", out)

    def test_b3_escape_em_script_e_relativo_interno_em_reference(self):
        md = self.fm("skill-esc", corpo="Leia `references/guia.md`. Rode `scripts/run.sh`.\n")
        d = make_skill(self.tmp / "skills", "skill-esc", skill_md=md, files={
            "references/guia.md": "Veja `../scripts/run.sh` (continua dentro da skill).\n",
            "scripts/run.sh": "#!/bin/sh\n. ../../outra-skill/lib.sh\n",
        })
        rc, out = self.run_script(d, "--external", "off")
        self.assertTrue(any("B3" in l and "scripts/run.sh" in l for l in out.splitlines()), out)
        self.assertNotIn("em references/guia.md", out)

    def test_bloco_til_nao_conta_como_afirmacao(self):
        md = self.fm("skill-til", corpo="~~~bash\necho 20.000 linhas\n~~~\n")
        d = make_skill(self.tmp / "skills", "skill-til", skill_md=md, files={})
        rc, out = self.run_script(d, "--external", "off", "--claims", "--format", "json")
        self.assertEqual(json.loads(out)["skills"][0]["claims"], [])


class TestPortabilidade(Base):
    def copiar_sozinha(self):
        destino = self.tmp / "outro-harness" / "skills" / "skill-quality-audit"
        shutil.copytree(SKILL_DIR, destino, ignore=shutil.ignore_patterns("__pycache__"))
        return destino

    def test_familia_sem_irmas_rc0(self):
        destino = self.copiar_sozinha()
        rc, out = self.run_script("--family", "--external", "off",
                                  script=destino / "scripts" / "audit_skill_quality.py")
        self.assertEqual(rc, 0, out)
        self.assertIn("[SKIP]", out)
        self.assertNotIn(str(SKILL_DIR), out)  # a cópia não aponta para a origem

    def test_autoauditoria_da_copia_rc0(self):
        destino = self.copiar_sozinha()
        rc, out = self.run_script(destino, "--external", "off",
                                  script=destino / "scripts" / "audit_skill_quality.py")
        self.assertEqual(rc, 0, out)

    def test_gates_externos_ausentes_viram_skip(self):
        d = make_skill(self.tmp / "skills", "skill-ok")
        self.env["PATH"] = str(self.tmp / "bin-vazio") + os.pathsep + "/usr/bin" + os.pathsep + "/bin"
        rc, out = self.run_script(d, "--external", "auto", "--no-uvx",
                                  "--audit-skill-sh", self.tmp / "nao-existe.sh")
        self.assertEqual(rc, 0, out)
        self.assertIn("G1", out)
        self.assertIn("[SKIP]", out)


class TestParidadeClaims(Base):
    """Os padrões de D1 são vendorizados de skill-claim-check. Se a irmã estiver
    presente neste harness, as linhas apontadas precisam ser as mesmas."""

    def localizar_irma(self):
        for raiz in (SKILL_DIR.parent, SKILL_DIR.parent.parent):
            for cand in (raiz / "skill-claim-check", *raiz.glob("*/skill-claim-check")):
                script = cand / "scripts" / "listar-afirmacoes.sh"
                if script.is_file():
                    return script
        return None

    def test_mesmas_linhas_que_listar_afirmacoes(self):
        irma = self.localizar_irma()
        if irma is None or shutil.which("bash") is None:
            self.skipTest("skill-claim-check ausente neste harness: paridade não verificável")
        md = textwrap.dedent("""\
            ---
            name: skill-claims
            description: Use when testar paridade.
            ---

            O limite é 20.000 caracteres.
            Fica em /home/fulano/projeto.
            Validado na v1.3.22.
            O servidor sempre responde rápido.
            Linha neutra sem afirmação.

            ```bash
            echo 20.000 /home/fulano v1.2
            ```

            ~~~
            echo 30.000 caracteres
            ~~~
            Depois do bloco: 500 linhas.
            """)
        d = make_skill(self.tmp / "skills", "skill-claims", skill_md=md)
        rc_irma = subprocess.run(["bash", str(irma), str(d)], capture_output=True, text=True,
                                 env=self.env, timeout=60)
        self.assertEqual(rc_irma.returncode, 0, rc_irma.stdout + rc_irma.stderr)
        linhas_irma = sorted(int(t[1:]) for t in rc_irma.stdout.split() if t[:1] == "L" and t[1:].isdigit())
        rc, out = self.run_script(d, "--external", "off", "--claims", "--format", "json")
        self.assertEqual(rc, 0, out)
        claims = json.loads(out)["skills"][0]["claims"]
        linhas_nossas = sorted(c["line"] for c in claims if c["file"] == "SKILL.md")
        self.assertEqual(linhas_nossas, linhas_irma)


class TestBoasPraticas(Base):
    """A8 e F1 a F4: boas práticas do agentskills.io (sinais, não reprovam sozinhos)."""

    def ids(self, d):
        rc, out = self.run_script(d, "--external", "off", "--format", "json")
        findings = json.loads(out)["skills"][0]["findings"]
        return rc, {(f["level"], f["id"]) for f in findings}, findings

    def test_skill_valida_so_gera_info(self):
        d = make_skill(self.tmp / "skills", "skill-boa")
        rc, ids, _ = self.ids(d)
        self.assertEqual(rc, 0)
        self.assertIn(("INFO", "A8"), ids)   # metadata.hermes aninhado
        self.assertIn(("INFO", "F2"), ids)   # fixture não tem gotchas
        self.assertIn(("INFO", "F4"), ids)   # nem evals
        self.assertNotIn(("INFO", "F1"), ids)  # "Leia ... quando precisar" diz quando ler

    def test_reference_sem_condicao_e_gotchas_e_evals(self):
        md = VALID_SKILL_MD.replace("Leia `references/guia.md` quando precisar do detalhe.",
                                    "Detalhe: `references/guia.md`.") + "\n## Gotchas\n\n- algo.\n"
        d = make_skill(self.tmp / "skills", "skill-f1", skill_md=md.format(name="skill-f1"),
                       files={"references/guia.md": "# Guia\n", "scripts/ferramenta.py": "#!/usr/bin/env python3\n",
                              "evals/evals.json": "{}"})
        _, ids, _ = self.ids(d)
        self.assertIn(("INFO", "F1"), ids)
        self.assertNotIn(("INFO", "F2"), ids)
        self.assertNotIn(("INFO", "F4"), ids)

    def test_script_interativo_e_sem_help(self):
        files = {"references/guia.md": "# Guia\n",
                 "scripts/ferramenta.py": "#!/usr/bin/env python3\nnome = input('nome? ')\n",
                 "scripts/outro.sh": "#!/usr/bin/env bash\n# read -p em comentario nao conta\nread -r -p 'ok? ' x\n"}
        md = VALID_SKILL_MD + "Também `scripts/outro.sh`.\n"
        d = make_skill(self.tmp / "skills", "skill-f3", skill_md=md.format(name="skill-f3"), files=files)
        rc, ids, findings = self.ids(d)
        self.assertEqual(rc, 0)
        f3 = [f["msg"] for f in findings if f["id"] == "F3" and f["level"] == "AVISO"]
        self.assertEqual(len(f3), 2, f3)
        rc_strict, _ = self.run_script(d, "--external", "off", "--strict")
        self.assertEqual(rc_strict, 1)

    def test_regex_em_string_nao_e_prompt(self):
        files = {"references/guia.md": "# Guia\n",
                 "scripts/ferramenta.py": "#!/usr/bin/env python3\nimport argparse\nPADRAO = r'input\\s*\\('\n"}
        d = make_skill(self.tmp / "skills", "skill-regex", files=files)
        _, ids, _ = self.ids(d)
        self.assertNotIn(("AVISO", "F3"), ids)
        self.assertNotIn(("INFO", "F3"), ids)

    def test_metadata_nao_texto_fora_do_hermes(self):
        md = VALID_SKILL_MD.replace("metadata:\n", "metadata:\n  author: JorUge\n  extra:\n    - a\n")
        d = make_skill(self.tmp / "skills", "skill-a8", skill_md=md.format(name="skill-a8"))
        _, ids, findings = self.ids(d)
        self.assertIn(("AVISO", "A8"), ids)
        self.assertTrue(any("extra" in f["msg"] for f in findings if f["id"] == "A8"))


class TestCamposHermesNoTopo(Base):
    def test_platforms_no_topo_e_info_e_version_no_topo_e_aviso(self):
        md = VALID_SKILL_MD.replace("metadata:\n", "platforms:\n  - linux\nversion: 1.0.0\nmetadata:\n")
        d = make_skill(self.tmp / "skills", "skill-topo", skill_md=md.format(name="skill-topo"))
        rc, out = self.run_script(d, "--external", "off", "--format", "json")
        f = json.loads(out)["skills"][0]["findings"]
        a4 = {(x["level"], "platforms" in x["msg"], "version" in x["msg"]) for x in f if x["id"] == "A4"}
        self.assertIn(("INFO", True, False), a4)
        self.assertIn(("AVISO", False, True), a4)


class TestPlaceholdersEModulos(Base):
    def test_script_citado_por_placeholder_de_raiz_nao_e_orfao(self):
        md = VALID_SKILL_MD.format(name="skill-ph") + \
            "Rode `python3 {SKILL_DIR}/scripts/util.py` e `${CLAUDE_SKILL_DIR}/scripts/outro.sh`.\n"
        files = {"references/guia.md": "# Guia\n",
                 "scripts/ferramenta.py": "#!/usr/bin/env python3\nimport argparse\n",
                 "scripts/util.py": "#!/usr/bin/env python3\nimport argparse\n",
                 "scripts/outro.sh": "#!/usr/bin/env bash\n# --help\n"}
        d = make_skill(self.tmp / "skills", "skill-ph", skill_md=md, files=files)
        rc, out = self.run_script(d, "--external", "off")
        self.assertNotIn("B2", out, out)

    def test_hermes_home_scripts_nao_e_raiz_da_skill(self):
        md = VALID_SKILL_MD.format(name="skill-hh") + "Gate: `bash $HERMES_HOME/scripts/audit-skill.sh x` e `${HERMES_HOME}/scripts/y.sh`.\n"
        d = make_skill(self.tmp / "skills", "skill-hh", skill_md=md)
        rc, out = self.run_script(d, "--external", "off")
        self.assertNotIn("B2", out, out)

    def test_modulo_importado_nao_precisa_de_shebang(self):
        files = {"references/guia.md": "# Guia\n",
                 "scripts/ferramenta.py": "#!/usr/bin/env python3\nimport argparse\nimport lib\n",
                 "scripts/lib.py": "def f():\n    return 1\n"}
        md = VALID_SKILL_MD + "O `scripts/lib.py` é importado pela ferramenta.\n"
        d = make_skill(self.tmp / "skills", "skill-mod", skill_md=md.format(name="skill-mod"), files=files)
        rc, out = self.run_script(d, "--external", "off")
        self.assertNotIn("sem shebang", out, out)
        self.assertNotIn("F3", out, out)


class TestLicoesDe20260928(Base):
    """Falsos positivos achados ao corrigir 93 skills do Hermes e 20 do marketplace."""

    def test_lista_de_mappings_no_frontmatter_e_lida(self):
        md = ("---\nname: skill-lm\ndescription: Use when testar.\nplatforms:\n  - linux\n"
              "required_credential_files:\n  - path: token.json\n    description: token OAuth\n"
              "  - path: outro.json\n    description: outro\nmetadata:\n  hermes:\n"
              "    related_skills:\n      - irma\n---\n\n# Corpo\n")
        d = make_skill(self.tmp / "skills", "skill-lm", skill_md=md, files={})
        rc, out = self.run_script(d, "--external", "off", "--format", "json")
        sk = json.loads(out)["skills"][0]
        ids = {(f["level"], f["id"]) for f in sk["findings"]}
        self.assertNotIn(("AVISO", "A1"), ids, out)
        self.assertIn(("INFO", "A4"), ids)            # platforms/required_credential_files ficam no topo
        self.assertEqual(sk["related_skills"], ["irma"])  # o parser voltou ao nível certo depois da lista

    def test_g2_usa_uvx_com_versao_fixada(self):
        d = make_skill(self.tmp / "skills", "skill-uvx")
        bindir = self.tmp / "bin-uvx"
        bindir.mkdir()
        fake = bindir / "uvx"
        fake.write_text("#!/bin/sh\necho \"args: $*\"\n", encoding="utf-8")
        fake.chmod(0o755)
        self.env["PATH"] = str(bindir) + os.pathsep + "/usr/bin" + os.pathsep + "/bin"
        self.env.pop("SQA_NO_UVX", None)
        rc, out = self.run_script(d, "--audit-skill-sh", self.tmp / "nao-existe.sh")
        self.assertIn("[OK] G2 uvx skills-ref==", out)
        self.assertIn("--from skills-ref==", out)
        rc, out = self.run_script(d, "--no-uvx", "--audit-skill-sh", self.tmp / "nao-existe.sh")
        self.assertIn("[SKIP] G2", out)

    def test_pycache_ignorado_pelo_git_nao_e_aviso(self):
        git = shutil.which("git")
        if git is None:
            self.skipTest("git ausente")
        repo = self.tmp / "repo"
        d = make_skill(repo / "skills", "skill-git")
        (d / "scripts" / "__pycache__").mkdir()
        (d / "scripts" / "__pycache__" / "x.pyc").write_bytes(b"\0")
        subprocess.run([git, "init", "-q", str(repo)], check=True)
        (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        rc, out = self.run_script(d, "--external", "off")
        self.assertNotIn("[AVISO] B6", out, out)
        self.assertIn("[INFO] B6", out)
        (repo / ".gitignore").write_text("", encoding="utf-8")
        rc, out = self.run_script(d, "--external", "off")
        self.assertIn("[AVISO] B6", out, out)


IRMA_MD = textwrap.dedent("""\
    ---
    name: {name}
    description: Use when testar a familia.
    {metadata}---

    # Irmã de teste

    Porta de entrada da auditoria: skill `skill-quality-audit`.
    """)
COM_VINCULO = "metadata:\n  hermes:\n    related_skills:\n      - skill-quality-audit\n"


class TestFamiliaNoPlugin(Base):
    """As quatro no mesmo plugin (plugins/<p>/skills/<skill>) se acham como pastas vizinhas."""

    def montar_plugin(self, metadata_irmas=COM_VINCULO):
        skills = self.tmp / "plugins" / "skill-quality-audit" / "skills"
        shutil.copytree(SKILL_DIR, skills / "skill-quality-audit",
                        ignore=shutil.ignore_patterns("__pycache__"))
        for irma in ("skill-self-containment", "skill-claim-check", "skill-refactoring"):
            make_skill(skills, irma, IRMA_MD.format(name=irma, metadata=metadata_irmas), files={})
        return skills / "skill-quality-audit" / "scripts" / "audit_skill_quality.py"

    def test_as_quatro_se_acham_sem_hermes(self):
        script = self.montar_plugin()
        rc, out = self.run_script("--family", "--external", "off", "--strict", script=script)
        self.assertEqual(rc, 0, out)
        self.assertIn("4 skill(s)", out)
        self.assertNotIn("E0", out)
        self.assertNotIn("[AVISO] E1", out)
        # Na cópia instalada pelo Cursor a própria porta de entrada vem sem metadata (E1 vira INFO).
        if "\nmetadata:" in (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"):
            self.assertNotIn("E1", out)

    def test_irma_sem_metadata_e1_vira_info(self):
        # O instalador do Cursor remove o bloco metadata; o vínculo fica só no corpo.
        script = self.montar_plugin(metadata_irmas="")
        rc, out = self.run_script("--family", "--external", "off", "--strict", script=script)
        self.assertEqual(rc, 0, out)
        self.assertIn("[INFO] E1", out)
        self.assertNotIn("[AVISO] E1", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
