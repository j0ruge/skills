"""Testes de contrato do modo autônomo do /retrofit-skill (Tarefa 12).

Rodar: python3 plugins/retrofit-skill/tests/test_modo_autonomo.py
Só leitura de arquivos do próprio repositório: nenhum teste toca a rede, o git ou o `claude`.
Lidos aqui: o comando `commands/retrofit-skill.md`, a `references/modo-autonomo.md` (o que o executor
do retrofit-watch lê), o `CHANGELOG.md`, o `plugin.json`, o `marketplace.json` e o `README.md` da loja.
Quando a `retrofit-watch` está no mesmo repositório, os nomes das fases e os tetos saem do fonte dela
(`rw_store.PHASES`, `rw_gate.SKILL_MAX_LINES`, `rw_gate.SKILL_MAX_CHARS`), e o `SQA` da referência se
compara com o `rw_gate.AUDITOR`, sem importar os módulos.
"""
import ast
import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent
STORE_ROOT = PLUGIN_DIR.parents[1]
NAME = PLUGIN_DIR.name

COMMAND = PLUGIN_DIR / "commands" / "retrofit-skill.md"
REFERENCE = PLUGIN_DIR / "references" / "modo-autonomo.md"
CHANGELOG = PLUGIN_DIR / "CHANGELOG.md"
PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE = STORE_ROOT / ".claude-plugin" / "marketplace.json"
README = STORE_ROOT / "README.md"
WATCH_SCRIPTS = STORE_ROOT / "plugins" / "retrofit-watch" / "skills" / "retrofit-watch" / "scripts"

# A versão que trouxe o modo autônomo. Os quatro lugares ficam iguais entre si e nunca abaixo dela:
# um bump futuro (inclusive de um retrofit autônomo) não pode reprovar este teste.
MODE_VERSION = "0.11.0"
FAMILY = ("skill-claim-check", "skill-self-containment", "skill-refactoring")
ANCHORS = (
    "retrofit.json",
    "veredito.json",
    "seal <id> <lote> --licoes",
    "--fases",
    '--trailer "Retrofit-Mode: autonomous"',
    "um trailer `Retrofit-Mode`, uma vez",
    "executor-recusou",
    "no máximo 2 ciclos",
)
PROHIBITION = re.compile(r"\b(nunca|não|nenhum|nenhuma|sem)\b", re.I)
# Publicar é qualquer push (`git push`, `git -C <worktree> push`, "o push" em prosa) e qualquer `claude plugin`.
PUBLISH = re.compile(r"\bpush\b|claude plugin", re.I)
# Na frase de publicação, a negação vem antes do push; "sem" não conta ("push sem esperar a porta").
NEGATION = re.compile(r"\b(nunca|não|nenhum|nenhuma)\b", re.I)
# A outra forma aceita diz de quem é a publicação: "o push ... são da porta".
GATE_OWNS = re.compile(r"\b(é|são) da porta\b")
NAMES = (
    "`<REPO>` do comando é o `<worktree>`. O PASSO 0 não procura o repo nem pergunta.",
    "`RS=<worktree>/plugins/retrofit-skill`",
)
SQA_LINE = re.compile(r"`SQA=\$Q/([^`]+)`")
Q_PREFIX = "plugins/skill-quality-audit/skills/"


def read(path):
    return path.read_text(encoding="utf-8")


def paragraphs(text):
    """Os blocos de texto separados por linha em branco."""
    return [block for block in re.split(r"\n\s*\n", text) if block.strip()]


def sentences(text):
    """As frases do texto, com as quebras de linha e os marcadores de lista trocados por espaço."""
    flat = re.sub(r"\s*\n\s*(?:- )?", " ", text)
    return [s for s in re.split(r"(?<=[.:])\s+", flat) if s.strip()]


def publish_offenders(text):
    """As frases que falam de push ou de `claude plugin` sem proibir: nenhuma negação antes da primeira
    menção, e a frase não diz que a coisa é da porta."""
    out = []
    for s in sentences(text):
        hit = PUBLISH.search(s)
        if hit and not NEGATION.search(s[:hit.start()]) and not GATE_OWNS.search(s):
            out.append(s)
    return out


def list_items(text):
    """Os itens de lista (`- `), cada um com as linhas de continuação, cortados também na linha em branco."""
    return [item for block in paragraphs(text) for item in re.split(r"\n(?=\s*- )", block)]


def section(text, title):
    """O corpo da seção cujo título começa com `title`, até o próximo título do mesmo nível ou acima."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"(#+) (.*)", line)
        if m and m.group(2).startswith(title):
            level = len(m.group(1))
            body = []
            for nxt in lines[i + 1:]:
                h = re.match(r"(#+) ", nxt)
                if h and len(h.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    raise AssertionError(f"seção {title!r} ausente")


def table_rows(text):
    """As linhas de tabela Markdown, como listas de células sem as bordas; sem o separador."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"\|[\s:|-]+\|", line):
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def source_constant(path, name):
    """O valor literal de `name = ...` no fonte `path`, lido pela AST, sem importar o módulo."""
    for node in ast.parse(read(path)).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} ausente de {path.name}")


def frontmatter_version(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise AssertionError("sem frontmatter")
    found = re.search(r"^metadata:\n(?:[ \t]+.*\n)*?[ \t]+version:[ \t]*(\S+)", m.group(1) + "\n", re.M)
    if not found:
        raise AssertionError("sem metadata.version no frontmatter")
    return found.group(1)


def as_tuple(version):
    return tuple(int(x) for x in version.split("."))


class CommandTest(unittest.TestCase):

    def test_command_routes_to_the_reference(self):
        text = read(COMMAND)
        self.assertTrue("--auto <dir do lote>" in text, "o comando não diz a sintaxe `--auto <dir do lote>`")
        routes = [s for s in sentences(text) if "`<worktree>/plugins/retrofit-skill/references/modo-autonomo.md`" in s]
        self.assertTrue(routes, "o comando não cita a referência pelo caminho no worktree")
        self.assertTrue(any("antes de editar" in s.lower() for s in routes),
                        "a frase que cita a referência não diz quando ler (antes de editar)")
        body = section(text, "Modo autônomo")
        lines = [line for line in body.splitlines() if line.strip()]
        self.assertLessEqual(len(lines), 20, "a seção *Modo autônomo* passa de 20 linhas")
        said = sentences(body)
        for anchors, what in ((("Só vale no modo completo",), "só vale no modo completo"),
                              (("Exige", "retrofit.json", "veredito.json"), "exige os dois arquivos"),
                              (("veredito.json", "confirmação do passo 3"), "o veredito confirma"),
                              (("para antes do push",), "o fluxo para antes do push"),
                              (("`<REPO>` é o `worktree` do `retrofit.json`",), "`<REPO>` é o worktree"),
                              (("o PASSO 0 não procura o repo nem pergunta",), "o PASSO 0 não procura")):
            self.assertTrue(any(all(a in s for a in anchors) for s in said),
                            f"a seção *Modo autônomo* não diz que {what}")

    def test_step_3_has_the_exception(self):
        found = [p for p in paragraphs(read(COMMAND)) if "Espere minha confirmação" in p]
        self.assertEqual(len(found), 1, "o parágrafo de \"Espere minha confirmação\" não é único")
        self.assertIn("modo autônomo", found[0].lower(), "o passo 3 não tem a exceção do modo autônomo")

    def test_step_4_leaves_push_and_store_to_the_gate(self):
        text = read(COMMAND)
        for anchor in ("Push pra origin/main", "Depois do push, a loja e a sessão"):
            found = [item for item in list_items(text) if anchor in item]
            self.assertEqual(len(found), 1, f"o item {anchor!r} não é único")
            self.assertRegex(found[0], r"modo autônomo[^.]*da porta",
                             f"o item {anchor!r} não diz que, no modo autônomo, ele é da porta")


class ReferenceTest(unittest.TestCase):

    def test_reference_has_the_spec_anchors(self):
        text = read(REFERENCE)
        for anchor in ANCHORS:
            self.assertIn(anchor, text, f"a referência não tem {anchor!r}")
        coauthor = [line for line in text.splitlines() if "Co-Authored-By" in line]
        self.assertTrue(coauthor, "a referência não cita o `Co-Authored-By`")
        for line in coauthor:
            self.assertRegex(line, PROHIBITION, f"`Co-Authored-By` fora de uma proibição: {line!r}")

    def test_audit_phases_match_the_gate(self):
        text = read(REFERENCE)
        rows = table_rows(section(text, "4. A auditoria"))
        self.assertTrue(rows and rows[0] == ["Quando", "O que roda", "Nome em `--fases`"],
                        "a tabela da auditoria falta")
        phases = {}
        for row in rows[1:]:
            name = row[-1].strip("`")
            if name != "—":
                phases[name] = " ".join(row)
        for skill in FAMILY:
            self.assertIn(f"`{skill}`", text, f"a referência não cita `{skill}`")
        self.assertIn("`version:`", phases.get("claim-check", ""),
                      "a linha `claim-check` não diz que a linha `version:` não conta")
        refactoring = phases.get("refactoring", "")
        self.assertIn("cruza", refactoring, "a linha `refactoring` não diz que o gatilho é cruzar o teto")
        self.assertNotIn("passa de", refactoring, "a linha `refactoring` diz \"passa de\", não \"cruza\"")
        if not WATCH_SCRIPTS.is_dir():
            self.skipTest("retrofit-watch fora deste repositório")
        self.assertEqual(set(phases), source_constant(WATCH_SCRIPTS / "rw_store.py", "PHASES"))
        lines = re.search(r"~(\d+) linhas", refactoring)
        chars = re.search(r"~(\d+) mil caracteres", refactoring)
        self.assertTrue(lines and chars, "a linha `refactoring` não tem os dois tetos")
        self.assertEqual(int(lines.group(1)), source_constant(WATCH_SCRIPTS / "rw_gate.py", "SKILL_MAX_LINES"))
        self.assertEqual(int(chars.group(1)) * 1000,
                         source_constant(WATCH_SCRIPTS / "rw_gate.py", "SKILL_MAX_CHARS"))

    def test_reference_never_says_publish(self):
        self.assertEqual(publish_offenders(read(REFERENCE)), [], "publicação fora de uma proibição")

    def test_publish_check_catches_the_sabotaged_lines(self):
        target = "origin HEAD:" + "main"
        sabotaged = (
            f"Depois, rode `git -C <worktree> push {target}`.",
            f"Rode `git push {target}` sem esperar a porta.",
            "Faça o push para o origin/main.",
            f"Rode `git push {target}`, não espere.",
            f"Sem esperar a porta, rode `git push {target}`.",
            "Rode `claude plugin update` no fim.",
        )
        for line in sabotaged:
            self.assertEqual(publish_offenders(line), [line], f"o cheque deixou passar: {line!r}")
        allowed = (
            "Não faça nenhum push e não rode nenhum comando `claude plugin`.",
            "O push e a atualização da loja são da porta.",
        )
        for line in allowed:
            self.assertEqual(publish_offenders(line), [], f"o cheque recusou uma proibição: {line!r}")

    def test_reference_names_repo_sqa_and_rs(self):
        text = read(REFERENCE)
        for name in NAMES:
            self.assertIn(name, text, f"a lista de nomes não tem {name!r}")
        sqa = SQA_LINE.search(text)
        self.assertTrue(sqa, "a lista de nomes não tem o `SQA`")
        path = Q_PREFIX + sqa.group(1)
        self.assertTrue((STORE_ROOT / path).is_file(), f"o `SQA` não existe no repositório: {path}")
        if not WATCH_SCRIPTS.is_dir():
            self.skipTest("retrofit-watch fora deste repositório")
        gate = re.search(r'^AUDITOR = Path\("([^"]+)"\)', read(WATCH_SCRIPTS / "rw_gate.py"), re.M)
        self.assertTrue(gate, "AUDITOR ausente de rw_gate.py")
        self.assertEqual(path, gate.group(1), "o `SQA` da referência não é o auditor que a porta roda")


class VersionTest(unittest.TestCase):

    def test_the_four_places_agree_at_0_11_0_or_later(self):
        version = json.loads(read(PLUGIN_JSON))["version"]
        self.assertGreaterEqual(as_tuple(version), as_tuple(MODE_VERSION))
        self.assertEqual(frontmatter_version(read(COMMAND)), version, "metadata.version do comando")
        block = [p for p in json.loads(read(MARKETPLACE))["plugins"] if p["name"] == NAME]
        self.assertEqual(len(block), 1, "o bloco do plugin no marketplace.json não é único")
        self.assertEqual(block[0]["version"], version, "a versão do bloco no marketplace.json")
        rows = [row for row in table_rows(read(README)) if row and row[0] == f"**{NAME}**"]
        cells = [row[1] for row in rows if row[1] not in ("✓", "—")]
        self.assertEqual(cells, [version], "a versão da linha do README")
        entries = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", read(CHANGELOG), re.M)
        self.assertTrue(entries and entries[0] == version, "a primeira entrada do CHANGELOG não é a versão")
        self.assertIn(MODE_VERSION, entries, f"o CHANGELOG não tem a entrada {MODE_VERSION}")


if __name__ == "__main__":
    unittest.main()
