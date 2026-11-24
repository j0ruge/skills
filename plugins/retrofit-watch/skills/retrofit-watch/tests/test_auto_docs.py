"""Testes de contrato do modo autônomo (Tarefa 11): a documentação que a sessão do dono lê presa ao código.

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py
Só leitura de arquivos do próprio repositório: nenhum teste toca a rede, o git ou o `claude`.
Lidos aqui: a `SKILL.md`, a `references/modo-autonomo.md` (o `rw_auto.REFERENCE`, que o texto do hook
cita), a `references/criteria.md`, o agente `agents/retrofit-reviewer.md` e, quando existe, a
`plugins/retrofit-skill/references/modo-autonomo.md` (Tarefa 12).
"""
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
PLUGIN_DIR = SKILL_DIR.parents[1]
STORE_ROOT = PLUGIN_DIR.parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import retrofit_watch as rw  # noqa: E402
import rw_auto  # noqa: E402
import rw_gate  # noqa: E402
import rw_store  # noqa: E402

SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE = rw_auto.REFERENCE
CRITERIA = rw_auto.CRITERIA
AGENT = PLUGIN_DIR / "agents" / "retrofit-reviewer.md"
EXECUTOR_REFERENCE = STORE_ROOT / "plugins" / "retrofit-skill" / "references" / "modo-autonomo.md"

# Os tetos da SKILL.md (brief da Tarefa 11).
SKILL_MAX_LINES = 250
SKILL_MAX_CHARS = 20000
# As duas perguntas da segunda passada (spec 5.4, com a redação do brief da Tarefa 11).
DIFF_QUESTIONS = (
    "a mudança acrescenta uma regra que repete ou contradiz uma já escrita, em vez de corrigir a frase que errou?",
    "o diff faz só o que as lições dizem?",
)
# A proibição do passo 9 (I1) e a precedência da colheita no agente (I4), na rodada de correção 1.
REVIEWER_FILES_RULE = "Nunca grave nem corrija `veredito.json` ou `anonimato.json`: só o revisor os grava."
HARVEST_RULE = ("A regra da colheita vale primeiro: um termo que é um nome da colheita é `privado`, mesmo quando "
                "também é um identificador de código.")
CITED = re.compile(r"retrofit_watch\.py\s+([a-z][a-z-]*)")
# O `queue` é a linha de comando da fila das sessões headless; o `main` o trata antes do CLI_USAGE.
QUEUE = "queue"


def read(path):
    return path.read_text(encoding="utf-8")


def hook_verbs():
    """Os verbos que o hooks.json do plugin registra (o último argumento de cada comando)."""
    data = json.loads(read(PLUGIN_DIR / "hooks" / "hooks.json"))
    return {hook["args"][-1] for groups in data["hooks"].values() for group in groups for hook in group["hooks"]}


def known_verbs():
    return set(rw.CLI_USAGE) | {QUEUE} | hook_verbs()


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
    """As linhas de tabela Markdown, como listas de células sem as bordas; sem o cabeçalho e o separador."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"\|[\s:|-]+\|", line):
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows[1:] if rows else rows


def json_blocks(text):
    """Os blocos ```json do texto, já lidos."""
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S)]


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise AssertionError("sem frontmatter")
    out = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def all_reasons():
    out = []
    for group in (rw_auto.LESSON_REASONS, rw_auto.OWNER_REASONS, rw_auto.AGENT_REASONS, rw_gate.GATE_REASONS):
        out += [r for r in group if r not in out]
    return out


class SubcommandTest(unittest.TestCase):

    def test_every_cited_subcommand_exists(self):
        docs = [SKILL_MD, REFERENCE, CRITERIA, AGENT] + ([EXECUTOR_REFERENCE] if EXECUTOR_REFERENCE.exists() else [])
        known = known_verbs()
        for path in docs:
            for verb in CITED.findall(read(path)):
                self.assertIn(verb, known, f"{path.name} cita `retrofit_watch.py {verb}`, que não existe")

    def test_every_subcommand_is_documented(self):
        text = read(REFERENCE)
        for verb in rw.CLI_USAGE:
            self.assertRegex(text, rf"retrofit_watch\.py {re.escape(verb)}\b", f"`{verb}` ausente da referência")


class FormatTest(unittest.TestCase):

    def test_format_keys_are_documented(self):
        lessons = [b for b in json_blocks(read(REFERENCE)) if set(b) == {"id", "licoes"} and b["licoes"]
                   and set(b["licoes"][0]) == rw_auto.LICAO_KEYS]
        self.assertTrue(lessons, "a referência não tem o exemplo do licoes.json com as chaves de LICAO_KEYS")
        self.assertEqual(set(lessons[0]["licoes"][0]["evidencia"]), rw_auto.EVIDENCIA_KEYS)
        blocks = json_blocks(read(AGENT))
        verdicts = [b for b in blocks if set(b) == {"id", "base", "licoes"}]
        self.assertTrue(verdicts, "o agente não tem o exemplo do veredito.json")
        self.assertEqual(set(verdicts[0]["licoes"][0]), rw_auto.PARECER_KEYS)
        anonymity = [b for b in blocks if set(b) == rw_auto.ANONIMATO_KEYS]
        self.assertTrue(anonymity, "o agente não tem o exemplo do anonimato.json com as chaves de ANONIMATO_KEYS")
        self.assertEqual(set(anonymity[0]["termos"][0]), rw_auto.TERMO_KEYS)

    def test_formats_table_places_each_file(self):
        rows = {row[0].strip("`"): row for row in table_rows(section(read(REFERENCE), "Formatos"))}
        for name in ("pedido.json", "licoes.json", "veredito.json"):
            self.assertEqual(rows[name][1], "`<dados>/auto/<id>/`", name)
        for name in ("retrofit.json", "termos-novos.json", "anonimato.json", "aprovado.json"):
            self.assertEqual(rows[name][1], "`<dados>/auto/<id>/<lote>/`", name)
        self.assertEqual(rows["colheita.txt"][1], "`<dados>/`")
        keys = set(re.findall(r"`([a-z_]+)`", rows["termos-novos.json"][3]))
        self.assertEqual(keys, {"patch", "termos"} | rw_store.TERM_KEYS)

    def test_every_reason_code_is_explained(self):
        rows = [row for row in table_rows(section(read(REFERENCE), "8.")) if row[0].startswith("`")]
        codes = [row[0].strip("`") for row in rows]
        self.assertEqual(sorted(codes), sorted(all_reasons()))
        for row in rows:
            code = row[0].strip("`")
            self.assertTrue(row[1] and row[3], f"`{code}` sem o que quer dizer ou sem a saída")
            self.assertEqual(row[2], "sim" if code in rw_gate.OVERRIDABLE else "não", code)


class RuleTest(unittest.TestCase):

    def test_owner_word_rule_is_written_where_it_matters(self):
        step = section(read(REFERENCE), "6.").strip()
        self.assertTrue(step.startswith(rw_auto.OWNER_WORD_RULE), "a frase não abre o passo dos segurados")
        self.assertIn(rw_auto.OWNER_WORD_RULE, section(read(SKILL_MD), "Modo autônomo"))

    def test_owner_lines_match_the_gate(self):
        step = section(read(REFERENCE), "5.")
        marks = {"PLG": "<plugin>", "VER": "X.Y.Z", "SHA": "<sha>", "MOT": "<motivo>", "RAM": "<ramo>"}
        lines = ({"resultado": "publicado", "plugin": "PLG", "versao": "VER", "commit": "SHA", "instalacao": "ok"},
                 {"resultado": "segurado", "plugin": "PLG", "motivo": "MOT", "ramo": "RAM"})
        for line in lines:
            text = rw_gate.phrase(line).encode("ascii").decode("unicode_escape")
            for mark, placeholder in marks.items():
                text = text.replace(mark, placeholder)
            self.assertIn(f"`{text}`", step)

    def test_publish_exit_codes_are_explained(self):
        step = section(read(REFERENCE), "5.")
        self.assertIn("run_in_background", step)
        codes = {row[0] for row in table_rows(step)}
        self.assertEqual(codes, {"0", "1", "2", "3", "4"})

    def test_lock_wait_matches_the_gate(self):
        text = read(REFERENCE)
        wait = f"{rw_gate.PUBLISH_LOCK_WAIT} s"
        self.assertIn(f"até {wait}", section(text, "4."))
        trava = next(row for row in table_rows(section(text, "8.")) if row[0] == "`trava`")
        self.assertIn(wait, trava[1])


def flat(text):
    """O texto com cada sequência de espaços, quebras e recuos trocada por um espaço: a quebra de linha
    da prosa não decide o teste."""
    return " ".join(text.split())


class FixRoundTest(unittest.TestCase):
    """As frases da rodada de correção 1 da Tarefa 11 (I1 a I6)."""

    def test_session_never_writes_the_reviewer_files(self):
        self.assertIn(REVIEWER_FILES_RULE, flat(section(read(REFERENCE), "9.")))

    def test_missing_reviewer_file_retries_once_then_stops(self):
        text = read(REFERENCE)
        for title in ("2.", "4."):
            step = flat(section(text, title))
            self.assertIn("despache o revisor de novo, uma vez", step, title)
            self.assertIn("deixe o pedido aberto", step, title)
        self.assertIn("volte ao passo 2", flat(section(text, "3.")))
        self.assertIn("volte ao passo 2", flat(section(text, "O aviso de startup")))

    def test_large_term_list_rule_is_in_both(self):
        self.assertIn("Nunca aceite um veredito só para a lista inteira.", flat(section(read(REFERENCE), "4.")))
        self.assertIn("Nunca dê um veredito só para a lista inteira.", flat(section(read(AGENT), "Segunda passada")))

    def test_harvest_rule_wins_in_the_agent(self):
        text = flat(section(read(AGENT), "Segunda passada"))
        self.assertIn(HARVEST_RULE, text)
        self.assertLess(text.index(HARVEST_RULE), text.index("um identificador de código, um nome de arquivo"))
        self.assertIn("Um nome da colheita é `privado`, mesmo quando também é um identificador.",
                      flat(section(read(REFERENCE), "4.")))

    def test_cover_location_format_matches_code(self):
        self.assertIn("`coberta` aceita só `caminho:N`", flat(section(read(AGENT), "Primeira passada")))
        self.assertIsNotNone(rw_auto.LOCATION.fullmatch("plugins/x/SKILL.md:42"))
        for wrong in ("plugins/x/SKILL.md:42-45", "plugins/x/SKILL.md:42 porque"):
            self.assertIsNone(rw_auto.LOCATION.fullmatch(wrong), wrong)

    def test_name_fix_keeps_list_and_message(self):
        step = flat(section(read(REFERENCE), "6."))
        self.assertIn("commit -a --amend --no-edit", step)
        self.assertIn("com a mudança da lista dentro dele", step)
        self.assertIn("o executor (o despacho do passo 4)", step)

    def test_executor_redispatch_is_defined(self):
        self.assertIn("com a tarefa da correção no lugar do `--auto`", flat(section(read(REFERENCE), "4.")))
        self.assertIn("despacho do executor fora do passo 4", flat(section(read(REFERENCE), "8.")))

    def test_behind_notice_says_where_the_lote_is(self):
        text = flat(section(read(REFERENCE), "O aviso de startup"))
        self.assertIn("última linha `publicado` de cada plugin em `<dados>/autonomo.jsonl`", text)


class ReviewerTest(unittest.TestCase):

    def test_reviewer_asks_the_two_diff_questions(self):
        text = read(AGENT)
        for question in DIFF_QUESTIONS:
            self.assertIn(question, text)
        self.assertIn("`regra_repetida`", text)
        self.assertIn("`fora_das_licoes`", text)

    def test_reviewer_writes_where_the_formats_say(self):
        text = read(AGENT)
        self.assertIn("Grave `<dados>/auto/<id>/veredito.json`", section(text, "Primeira passada"))
        self.assertIn("Grave `<dados>/auto/<id>/<lote>/anonimato.json`", section(text, "Segunda passada"))

    def test_reviewer_frontmatter(self):
        meta = frontmatter(read(AGENT))
        self.assertEqual(meta["name"], AGENT.stem)
        self.assertEqual(meta["tools"], "Read, Grep, Glob, Bash")
        self.assertEqual(meta["model"], "opus")
        self.assertTrue(meta["description"].isascii() and meta["description"], "a description é em inglês")

    def test_dispatch_names_model_and_effort(self):
        text = read(REFERENCE)
        plugin = json.loads(read(PLUGIN_DIR / ".claude-plugin" / "plugin.json"))["name"]
        reviewer = section(text, "2.")
        self.assertIn(f'subagent_type: "{plugin}:{frontmatter(read(AGENT))["name"]}"', reviewer)
        self.assertIn('model: "opus"', reviewer)
        self.assertIn('effort: "xhigh"', reviewer)
        executor = section(text, "4.")
        self.assertIn('subagent_type: "general-purpose"', executor)
        self.assertIn('model: "opus"', executor)
        self.assertIn('effort: "medium"', executor)


class SkillTest(unittest.TestCase):

    def test_skill_budget_and_routing(self):
        text = read(SKILL_MD)
        self.assertLess(len(text.splitlines()), SKILL_MAX_LINES)
        self.assertLess(len(text), SKILL_MAX_CHARS)
        # Cada parágrafo, e cada linha de tabela, que cita a referência diz quando lê-la.
        blocks = []
        for paragraph in re.split(r"\n\s*\n", text):
            blocks += paragraph.splitlines() if paragraph.lstrip().startswith("|") else [paragraph]
        routes = [b for b in blocks if "references/modo-autonomo.md" in b]
        self.assertTrue(routes, "a SKILL.md não cita references/modo-autonomo.md")
        for route in routes:
            self.assertTrue("pedido autônomo" in route and "segurados" in route,
                            f"a citação da referência não diz quando ler: {route!r}")


if __name__ == "__main__":
    unittest.main()
