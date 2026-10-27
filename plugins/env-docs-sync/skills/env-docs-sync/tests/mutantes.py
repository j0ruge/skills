#!/usr/bin/env python3
"""Mutantes dos guardas do script: cada um troca um trecho de `scripts/env_docs_sync.py` numa cópia do
plugin inteiro, e a suíte tem de ficar vermelha. Rodado à mão depois de mexer num guarda; não entra no
`unittest discover`.

    python3 -B tests/mutantes.py            # todos
    python3 -B tests/mutantes.py M28 M31    # só esses

Antes dos mutantes, roda a suíte sem nenhum (o controle): vermelha, sai 2, porque todo mutante
sairia morto sem provar nada. Sai 0 quando todos morrem e 1 com a lista dos vivos, de um trecho que
não está mais no script (aí o guarda mudou, e o mutante precisa ser refeito) ou de um mutante que
não compila. O que só estourou o prazo conta como morto (um laço infinito é o caso), mas a linha
final o nomeia, porque carga na máquina também estoura. A cópia é do plugin inteiro porque os testes leem o `hooks/hooks.json` e o sensor
anti-marca varre `SKILL.parent.parent`: com só a pasta da skill, ele varreria a pasta temporária
inteira. Cobre os mutantes da seção CI/CD, das seções derivadas, da versão do Codex e dos guardas da
revisão de código antes da publicação; os dos incrementos anteriores, listados em
`references/safety.md`, foram rodados à mão.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPO_DA_SUITE = 300

MUTANTES = [
    ("M1 lista de fluxo crua", 'return ", ".join(_escalar(item) for item in valor[1:-1].split(",") if item.strip())',
     "return valor"),
    ("M2 runs-on em qualquer profundidade", "    for k in _filhos(linhas, j):\n        chave, valor = _chave_yaml(linhas[k][1])\n        if chave == \"runs-on\":",
     "    for k in range(j + 1, len(linhas)):\n        chave, valor = _chave_yaml(linhas[k][1])\n        if chave == \"runs-on\":"),
    ("M3 comentário fica", "return (valor[:casou.start()] if casou else valor).strip()", "return valor.strip()"),
    ("M4 nome do gh sem validar", "            and _RE_NOME_DE_VARIAVEL.fullmatch(item[\"name\"]) for item in dados):",
     "            for item in dados):"),
    ("M5 rc do gh ignorado", "    if resultado.returncode != 0:\n        raise ErroEnvDocs(f\"gh {' '.join(args[:2])}",
     "    if False:\n        raise ErroEnvDocs(f\"gh {' '.join(args[:2])}"),
    ("M6 nome do workflow sem escape", "(_esc(wf.nome), f\"<code>", "(wf.nome, f\"<code>"),
    ("M7 gh sem exigir janela", "obrigatorias = _CAMPOS_TOPO + ((\"remote_check_every\",) if tem_ssh or tem_gh else ())",
     "obrigatorias = _CAMPOS_TOPO + ((\"remote_check_every\",) if tem_ssh else ())"),
    ("M8 h2 repetido aceito", "if any(len(v) != 1 for v in fixos.values()) or not (",
     "if any(len(v) < 1 for v in fixos.values()) or not ("),
    ("M9 sufixo não comparado", "and (_normalizado(depois_a) == _normalizado(depois_n))", ""),
    ("M10 ids bkmrk contam", "return re.sub(r\">\\s+<\", \"><\", html.unescape(_RE_ID_BKMRK.sub(\"\", fragmento))).strip()",
     "return re.sub(r\">\\s+<\", \"><\", html.unescape(fragmento)).strip()"),
    ("M11 entradas sem workflows", "                    parte(f\"workflow {arquivo.name}\", arquivo.read_bytes())",
     "                    pass"),
    ("M12 janela em todo gatilho", "    if olhar_janela and ci is not None and ci[\"secrets\"] == \"gh\":",
     "    if ci is not None and ci[\"secrets\"] == \"gh\":"),
    ("M13 janela nunca", "    if olhar_janela and ci is not None and ci[\"secrets\"] == \"gh\":",
     "    if False:"),
    ("M14 destino chamado com hash igual", "escreveu = anterior.get(\"sha256\") != sha and destino.escrever_derivadas",
     "escreveu = destino.escrever_derivadas"),
    ("M15 falha carimba", "        return dict(estado), None, _detalhe(erro)\n    novo = copy.deepcopy(dict(estado))",
     "        ci_cd, sha = \"\", \"0\" * 64\n    novo = copy.deepcopy(dict(estado))"),
    ("M16 sem trava nas derivadas", "        self.conferir_permissao()\n        atual = self._html()\n        nova = pagina_de_ambientes(",
     "        atual = self._html()\n        nova = pagina_de_ambientes("),
    ("M17 replace sem conferir antes", "        if derivadas_conferem(atual, nova):\n            return False\n        marca",
     "        marca"),
    ("M18 seções sem rstrip", "        secoes = secoes.rstrip()  #", "        secoes = secoes  #"),
    ("M19 workflow editado não vigiado", "        if rel == NOME_DA_CONFIG or _e_workflow(rel, config):", "        if False:"),
    ("M20 derivadas mesmo com bloco que falhou", "    if derivadas is not None and resultado.falhou is None:",
     "    if derivadas is not None:"),
    ("M21 estado aceita derived qualquer", "            falha(\"derived\")", "            pass"),
    ("M22 status sem derivadas", "        linhas.append((\"página\", \"seções derivadas\",", "        [].append((\"página\", \"seções derivadas\","),
    ("M23 migrate sem derived no estado", "        estado[\"derived\"] = {\"inputs_sha256\": entradas_derivadas(raiz, config), \"checked_at\": _carimbo(quando),",
     "        _ = {\"inputs_sha256\": entradas_derivadas(raiz, config), \"checked_at\": _carimbo(quando),"),
    ("M24 yml em qualquer pasta", "            and rel.rsplit(\"/\", 1)[0] == Path(ci[\"workflows\"]).as_posix().rstrip(\"/\"))", ")"),
    ("M25 releitura das derivadas ignorada", "        if not derivadas_conferem(self._html(), nova):\n            raise ErroEnvDocs(\"releitura: as seções derivadas",
     "        if False:\n            raise ErroEnvDocs(\"releitura: as seções derivadas"),
    ("M26 ci null lê workflows", "    if ci is not None and ci[\"workflows\"] is not None:\n        base = Path(raiz)",
     "    if ci is not None or True:\n        base = Path(raiz) / \".github/workflows\"\n    if False:\n        base = Path(raiz)"),
    ("M27 gh chamado sem ci.secrets", "    nomes = nomes_do_gh(raiz, ctx) if ci[\"secrets\"] == \"gh\" else None",
     "    nomes = nomes_do_gh(raiz, ctx)"),
    ("M28 versão nunca avisa", "    if versao not in CODEX_MEDIDOS:", "    if False:"),
    ("M29 só a primeira versão medida", "    if versao not in CODEX_MEDIDOS:", "    if versao != CODEX_MEDIDOS[0]:"),
    ("M30 aviso cita só a primeira", '_MEDIDOS = " e no ".join(CODEX_MEDIDOS)', "_MEDIDOS = CODEX_MEDIDOS[0]"),
    ("M31 sem o 0.165.0", 'CODEX_MEDIDOS = ("0.164.0", "0.165.0")', 'CODEX_MEDIDOS = ("0.164.0",)'),
    ("M32 git que falha vira worktree", "    if saida is None:\n        raise ErroEnvDocs(\"o git não respondeu",
     "    if saida is None:\n        return False\n        raise ErroEnvDocs(\"o git não respondeu"),
    ("M33 aviso do git vira silêncio", "    except ErroEnvDocs as erro:\n        return [f\"aviso — {raiz.name}: não deu para decidir",
     "    except ErroEnvDocs as erro:\n        return [] and [f\"aviso — {raiz.name}: não deu para decidir"),
    ("M34 os.walk sem onerror", "os.walk(raiz, followlinks=False, onerror=_ao_listar(raiz))", "os.walk(raiz, followlinks=False)"),
    ("M35 callout por substring no escrever", "bool(_RE_CALLOUT_AUSENTE.search(atual)) == (op.acao",
     "(\"ausente desde\" in atual) == (op.acao"),
    ("M36 callout por substring no bloco_confere", "return bool(_RE_CALLOUT_AUSENTE.search(corpo)) and texto",
     "return \"ausente desde\" in corpo and texto"),
    ("M37 _commit com os GIT_* herdados", "    sha = (_git(raiz, \"rev-parse\", \"HEAD\") or \"\").strip()",
     "    sha = subprocess.run([\"git\", \"-C\", str(raiz), \"rev-parse\", \"HEAD\"], capture_output=True,\n"
     "                         text=True).stdout.strip()"),
    ("M38 subpasta que sumiu levanta", "FileNotFoundError) and os.path.normpath(erro.filename) != os.path.normpath(raiz):\n            return",
     "FileNotFoundError) and os.path.normpath(erro.filename) != os.path.normpath(raiz):\n            pass"),
    ("M39 raiz que sumiu passa", "FileNotFoundError) and os.path.normpath(erro.filename) != os.path.normpath(raiz):",
     "FileNotFoundError):"),
    ("M40 dica do exclude sem /**", "ponha `{rel}/**` em `exclude`", "ponha `{rel}` em `exclude`"),
    ("M41 dica do exclude na raiz", 'dica = "" if rel == "." else f"', 'dica = f"'),
    ("M42 dica com o caminho absoluto", "rel = Path(os.path.relpath(erro.filename, raiz)).as_posix()",
     "rel = erro.filename"),
]


def _suite(antes=None, depois=None):
    """Roda a suíte numa cópia do plugin inteiro, com o mutante aplicado quando `antes` vem.

    Devolve (estado, última linha do unittest), com estado `verde`, `vermelho`, `estourou`,
    `ALVO NÃO ACHADO` ou `NÃO COMPILA`."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(SKILL.parent.parent, Path(tmp) / "env-docs-sync", ignore=shutil.ignore_patterns("__pycache__"))
        copia = Path(tmp) / "env-docs-sync" / "skills" / "env-docs-sync"
        if antes is not None:
            script = copia / "scripts" / "env_docs_sync.py"
            texto = script.read_text(encoding="utf-8")
            if texto.count(antes) != 1:
                return "ALVO NÃO ACHADO", f"{texto.count(antes)}x"
            mutado = texto.replace(antes, depois)
            try:
                compile(mutado, str(script), "exec")
            except SyntaxError as erro:
                return "NÃO COMPILA", f"{erro.msg}, linha {erro.lineno}"
            script.write_text(mutado, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"], cwd=copia,
                               capture_output=True, text=True, timeout=TEMPO_DA_SUITE)
        except subprocess.TimeoutExpired:
            return "estourou", f"a suíte passou de {TEMPO_DA_SUITE} s"
        return ("verde" if r.returncode == 0 else "vermelho"), (r.stderr.strip().splitlines() or ["?"])[-1]


def rodar(antes, depois):
    """Aplica um mutante numa cópia e roda a suíte; devolve `morto`, `morto?` (só estourou o prazo),
    `VIVO`, `ALVO NÃO ACHADO` ou `NÃO COMPILA`. Mutante que quebra a sintaxe derruba o import de todo módulo de teste: a suíte fica
    vermelha sem que nenhum teste tenha olhado o guarda, por isso ele não conta como morto."""
    estado, detalhe = _suite(antes, depois)
    # estourar o prazo conta como morto (um laço infinito é o caso), mas com `?`: carga na máquina também estoura
    rotulo = {"vermelho": "morto", "estourou": "morto?", "verde": "VIVO"}.get(estado, estado)
    return f"{rotulo} ({detalhe})"


def main(argv):
    """Roda o controle e os mutantes pedidos (todos, sem argumento); 0 quando todos morrem."""
    escolhidos = [m for m in MUTANTES if not argv or m[0].split()[0] in argv]
    desconhecidos = set(argv) - {m[0].split()[0] for m in MUTANTES}
    if desconhecidos:
        print(f"mutante desconhecido: {', '.join(sorted(desconhecidos))}", file=sys.stderr)
        return 2
    # Controle: sem mutante, a suíte tem de passar; senão todo mutante sairia morto sem provar nada.
    estado, detalhe = _suite()
    if estado != "verde":
        print(f"controle: a suíte sem mutante não passou ({estado}: {detalhe}); nenhum mutante conta",
              file=sys.stderr)
        return 2
    vivos, por_prazo = [], []
    for nome, antes, depois in escolhidos:
        estado = rodar(antes, depois)
        if not estado.startswith("morto"):
            vivos.append(nome)
        elif estado.startswith("morto?"):
            por_prazo.append(nome.split()[0])
        print(f"{nome}: {estado}", flush=True)
    prazo = f" ({len(por_prazo)} só por prazo: {', '.join(por_prazo)})" if por_prazo else ""
    print(f"\n{len(escolhidos) - len(vivos)}/{len(escolhidos)} mortos{prazo}; vivos: {vivos or '-'}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
