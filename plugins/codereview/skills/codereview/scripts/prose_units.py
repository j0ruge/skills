#!/usr/bin/env python3
"""
prose_units.py — as unidades de prosa em volta de cada linha mudada de um intervalo do git.

A rodada de verificação do codereview não relê o arquivo inteiro: lê, em volta de cada hunk, a
unidade que o contém (o parágrafo, o item de lista com as continuações, a linha da tabela, o bloco
cercado; em código, o bloco de comentário). Este script calcula esse escopo a partir do diff, para
que ele não dependa do julgamento da sessão.

    python3 scripts/prose_units.py --repo DIR --base SHA --head SHA

Imprime um JSON com o tipo de cada arquivo (DOCS, DOC_ONLY ou CODE), as unidades com as linhas
mudadas de cada uma e os identificadores entre crases das linhas `+`, e sai com rc 0. Erro do git
sai com rc 2 e a mensagem no stderr.

Só biblioteca padrão. Não grava arquivo nenhum.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path, PurePosixPath

# ---------------------------------------------------------------------------
# Linhas mudadas, pelo diff -U0.
# ---------------------------------------------------------------------------

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<inicio>\d+)(?:,(?P<qtd>\d+))? @@")
_ESCAPE_GIT = {"a": b"\a", "b": b"\b", "t": b"\t", "n": b"\n", "v": b"\v", "f": b"\f", "r": b"\r"}


def _sem_aspas(caminho: str) -> str:
    """Caminho sem as aspas e os escapes em C que o git põe quando ele tem caractere especial."""
    if len(caminho) < 2 or caminho[0] != '"' or caminho[-1] != '"':
        return caminho
    saida = bytearray()
    for i, parte in enumerate(re.split(r"\\([0-3][0-7]{2}|.)", caminho[1:-1])):
        if i % 2 == 0:
            saida += parte.encode("utf-8")
        elif len(parte) == 3:
            saida.append(int(parte, 8))
        else:
            saida += _ESCAPE_GIT.get(parte, parte.encode("utf-8"))
    return saida.decode("utf-8", "replace")


def _caminho_do_cabecalho(resto: str, prefixo: str) -> str | None:
    """Caminho de um `--- a/x` ou `+++ b/x`; None para /dev/null.

    O git põe um TAB depois de caminho com espaço.
    """
    caminho = _sem_aspas(resto.rstrip("\t"))
    if caminho == "/dev/null":
        return None
    return caminho[len(prefixo):] if caminho.startswith(prefixo) else caminho


def _caminho_do_diff_git(resto: str) -> str | None:
    """Caminho de um `diff --git a/x b/x` sem `---`/`+++` (binário, só modo): as metades são iguais."""
    meio = (len(resto) - 1) // 2
    if resto[meio:meio + 1] != " ":
        return None
    antes, depois = _sem_aspas(resto[:meio]), _sem_aspas(resto[meio + 1:])
    if antes.startswith("a/") and depois.startswith("b/") and antes[2:] == depois[2:]:
        return depois[2:]
    return None


def _blocos(texto: str) -> list[list[str]]:
    """Um bloco por arquivo do diff, cada um começando no `diff --git`.

    Corta em "\\n", e não com splitlines: um form feed ou um \\r dentro de uma linha do arquivo
    abriria uma linha falsa, que poderia começar com `diff --git`. Pelo mesmo motivo, o texto tem de
    vir de bytes decodificados, e não do modo texto do subprocess, que troca o \\r por "\\n".
    """
    blocos: list[list[str]] = []
    for linha in texto.split("\n"):
        if linha.startswith("diff --git "):
            blocos.append([linha])
        elif blocos:
            blocos[-1].append(linha)
    return blocos


def _inicio_dos_hunks(bloco: list[str]) -> int:
    """Índice do primeiro `@@` do bloco (o tamanho do bloco, se não houver hunk).

    Antes dele vem o cabeçalho; depois dele, toda linha do arquivo começa com `+`, `-`, espaço ou
    `\\`, e uma linha que começa com `@@` só pode ser outro hunk. Por isso um `+++` acrescentado ao
    arquivo nunca é lido como cabeçalho.
    """
    return next((i for i, linha in enumerate(bloco) if linha.startswith("@@")), len(bloco))


def _arquivo_do_bloco(bloco: list[str]) -> tuple[str | None, dict]:
    """(caminho no head, {"added", "removed_at", "status"}) de um bloco do diff -U0."""
    fim_do_cabecalho = _inicio_dos_hunks(bloco)
    status, novo, velho, renomeado = "M", None, None, None
    for linha in bloco[1:fim_do_cabecalho]:
        if linha.startswith("new file mode"):
            status = "A"
        elif linha.startswith("deleted file mode"):
            status = "D"
        elif linha.startswith("rename to "):
            status, renomeado = "R", _sem_aspas(linha[len("rename to "):])
        elif linha.startswith("--- "):
            velho = _caminho_do_cabecalho(linha[4:], "a/")
        elif linha.startswith("+++ "):
            novo = _caminho_do_cabecalho(linha[4:], "b/")
    added: list[int] = []
    removed_at: list[int] = []
    for linha in bloco[fim_do_cabecalho:]:
        m = _HUNK_RE.match(linha)
        if not m:
            continue
        inicio = int(m["inicio"])
        qtd = 1 if m["qtd"] is None else int(m["qtd"])
        if qtd:
            added.extend(range(inicio, inicio + qtd))
        else:  # hunk que só apaga: `inicio` é a linha do head antes do corte
            removed_at.append(max(inicio + 1, 1))
    caminho = novo or renomeado or velho or _caminho_do_diff_git(bloco[0][len("diff --git "):])
    return caminho, {"added": added, "removed_at": removed_at, "status": status}


def _git(repo: Path, *args: str) -> bytes:
    """Saída do git em bytes. Erro sobe como subprocess.CalledProcessError, com o stderr em bytes."""
    return subprocess.run(["git", "-P", "-C", str(repo), *args], capture_output=True, check=True).stdout


def _diff_por_arquivo(repo: Path, base: str, head: str) -> dict[str, tuple[dict, list[str]]]:
    """Por caminho no head: (o que changed_lines devolve dele, o bloco dele no diff -U0)."""
    # Os prefixos, a cor e o diff externo vêm explícitos porque a config do usuário muda os três.
    # O --end-of-options impede que um sha começado por `-` vire opção (um --output gravaria arquivo).
    # A saída vem em bytes: em modo texto, o subprocess troca um \r solto numa linha do arquivo por
    # "\n", e o resto da linha viraria uma linha do diff (até um `diff --git` de arquivo fantasma).
    texto = _git(
        repo, "diff", "-U0", "--find-renames", "--no-color", "--no-ext-diff",
        "--src-prefix=a/", "--dst-prefix=b/", "--end-of-options", f"{base}...{head}", "--",
    ).decode("utf-8", "replace")
    arquivos: dict[str, tuple[dict, list[str]]] = {}
    for bloco in _blocos(texto):
        caminho, info = _arquivo_do_bloco(bloco)
        if caminho is not None:
            arquivos[caminho] = (info, bloco)
    return arquivos


def changed_lines(repo: Path, base: str, head: str) -> dict[str, dict]:
    """Por caminho no head: {"added": [...], "removed_at": [...], "status": "M"|"A"|"D"|"R"}.

    `added` são as linhas `+` no head. `removed_at` é, para cada hunk sem linha `+`, a linha do head
    logo depois do corte (mínimo 1); num corte no fim do arquivo ela passa da última linha. Arquivo
    apagado sai pelo caminho que tinha na base; renomeado, pelo caminho novo. Erro do git sobe como
    subprocess.CalledProcessError, com o stderr em bytes.
    """
    return {caminho: info for caminho, (info, _) in _diff_por_arquivo(repo, base, head).items()}


# ---------------------------------------------------------------------------
# Unidades de Markdown.
# ---------------------------------------------------------------------------

_CERCA_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_TITULO_RE = re.compile(r"^\s*#{1,6}(?:\s|$)")
_MARCADOR_RE = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])(?:\s|$)")


def _recuo(linha: str) -> int:
    linha = linha.expandtabs(4)
    return len(linha) - len(linha.lstrip())


def _blocos_cercados(linhas: list[str]) -> dict[int, tuple[int, int]]:
    """Índice (0-indexado) de cada linha de bloco cercado → (início, fim) do bloco, com as cercas.

    A cerca fecha com o mesmo caractere, em número igual ou maior; sem ela, o bloco vai até o fim.
    """
    blocos: dict[int, tuple[int, int]] = {}
    i = 0
    while i < len(linhas):
        m = _CERCA_RE.match(linhas[i])
        if not m:
            i += 1
            continue
        cerca = m.group(1)
        fecha = re.compile(rf"^\s*{re.escape(cerca[0])}{{{len(cerca)},}}\s*$")
        fim = next((j for j in range(i + 1, len(linhas)) if fecha.match(linhas[j])), len(linhas) - 1)
        for j in range(i, fim + 1):
            blocos[j] = (i, fim)
        i = fim + 1
    return blocos


class _Documento:
    """As linhas de um Markdown e o que se sabe delas, para achar a unidade de cada alvo."""

    def __init__(self, linhas: list[str]):
        self.linhas = linhas
        self.cercados = _blocos_cercados(linhas)
        self._fim_do_item: dict[int, int] = {}

    def vazia(self, i: int) -> bool:
        return not self.linhas[i].strip()

    def tabela(self, i: int) -> bool:
        return self.linhas[i].lstrip().startswith("|")

    def titulo(self, i: int) -> bool:
        return bool(_TITULO_RE.match(self.linhas[i]))

    def marcador(self, i: int) -> bool:
        return i not in self.cercados and bool(_MARCADOR_RE.match(self.linhas[i]))

    def citacao(self, i: int) -> bool:
        return self.linhas[i].lstrip().startswith(">")

    def fim_do_item(self, i: int) -> int:
        """Última linha do item que começa no marcador `i`.

        O item para antes do próximo marcador de recuo menor ou igual ao dele, ou antes de uma linha
        em branco cuja próxima linha não vazia tenha recuo menor ou igual ao dele (num item sem
        recuo, é a linha sem recuo). Linhas de bloco cercado não param o item.
        """
        if i not in self._fim_do_item:
            recuo, fim = _recuo(self.linhas[i]), len(self.linhas) - 1
            for j in range(i + 1, len(self.linhas)):
                if j in self.cercados:
                    continue
                if self.marcador(j) and _recuo(self.linhas[j]) <= recuo:
                    fim = j - 1
                    break
                if self.vazia(j):
                    seguinte = next((k for k in range(j + 1, len(self.linhas)) if not self.vazia(k)), None)
                    if seguinte is None or _recuo(self.linhas[seguinte]) <= recuo:
                        fim = j - 1
                        break
            self._fim_do_item[i] = fim
        return self._fim_do_item[i]

    def item(self, i: int) -> tuple[int, int] | None:
        """O item mais interno que contém a linha `i`: o marcador mais próximo acima cujo item a cobre."""
        for m in range(i, -1, -1):
            if self.marcador(m) and self.fim_do_item(m) >= i:
                return (m, self.fim_do_item(m))
        return None

    def contiguas(self, i: int, cabe: Callable[[int], bool]) -> tuple[int, int]:
        """O trecho contíguo em volta de `i` cujas linhas satisfazem `cabe`."""
        inicio, fim = i, i
        while inicio > 0 and cabe(inicio - 1):
            inicio -= 1
        while fim + 1 < len(self.linhas) and cabe(fim + 1):
            fim += 1
        return (inicio, fim)

    def de_paragrafo(self, i: int) -> bool:
        return not (self.vazia(i) or i in self.cercados or self.titulo(i) or self.tabela(i)
                    or self.marcador(i))

    def unidade(self, i: int) -> tuple[int, int] | None:
        """(início, fim), 0-indexados, da unidade da linha `i`; None num documento sem texto."""
        if i in self.cercados:
            return self.cercados[i]
        if i >= len(self.linhas) or self.vazia(i):
            # Linha em branco (ou depois do fim, onde cai o corte no fim do arquivo): a unidade da
            # linha não vazia anterior; se não houver, a da seguinte.
            anterior = next((j for j in range(min(i, len(self.linhas)) - 1, -1, -1) if not self.vazia(j)), None)
            if anterior is not None:
                return self.unidade(anterior)
            seguinte = next((j for j in range(i + 1, len(self.linhas)) if not self.vazia(j)), None)
            return None if seguinte is None else self.unidade(seguinte)
        if self.tabela(i) or self.titulo(i):
            return (i, i)
        item = self.item(i)
        if item is not None:
            return item
        if self.citacao(i):
            return self.contiguas(i, self.citacao)
        return self.contiguas(i, self.de_paragrafo)


def markdown_units(lines: list[str], targets: list[int]) -> list[tuple[int, int]]:
    """Intervalos (início, fim), 1-indexados e inclusivos, das unidades que contêm os alvos.

    Saem em ordem e sem repetição: uma unidade que cabe inteira dentro de outra da saída (o sub-item
    dentro do item pai) não sai de novo. Alvo menor que 1 é ignorado.
    """
    doc = _Documento(lines)
    achadas = {doc.unidade(alvo - 1) for alvo in targets if alvo >= 1}
    achadas.discard(None)
    unidades = sorted((inicio + 1, fim + 1) for inicio, fim in achadas)
    return [u for u in unidades
            if not any(o != u and o[0] <= u[0] and u[1] <= o[1] for o in unidades)]


# ---------------------------------------------------------------------------
# Comentário em código, tipo do arquivo e identificadores.
# ---------------------------------------------------------------------------

_EXTENSOES_DE_DOC = (".md", ".txt")
_PREFIXOS_DE_COMENTARIO = {
    **dict.fromkeys((".cs", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".c", ".h", ".cpp",
                     ".swift", ".kt"), ("//", "/*", "*", "*/")),
    **dict.fromkeys((".py", ".sh", ".rb", ".yml", ".yaml", ".toml"), ("#",)),
    **dict.fromkeys((".lua", ".sql"), ("--",)),
}
_CRASES_RE = re.compile(r"`([^`]+)`")


def _extensao(caminho: str) -> str:
    return PurePosixPath(caminho).suffix.lower()


def comment_units(lines: list[str], targets: list[int], path: str) -> list[tuple[int, int]]:
    """Intervalos (início, fim), 1-indexados e inclusivos, dos blocos de comentário que contêm os alvos.

    Linha de comentário é a que, sem o recuo, começa com um prefixo da extensão de `path`; o bloco é
    o trecho contíguo delas. Alvo fora de comentário (a linha logo depois de um corte, uma linha em
    branco, o corte no fim do arquivo) cai no bloco da linha de cima, como a linha em branco do
    Markdown; se ela também não é comentário, o alvo fica sem unidade. Saem em ordem e sem repetição.
    """
    prefixos = _PREFIXOS_DE_COMENTARIO.get(_extensao(path))
    if prefixos is None:
        return []

    def comentario(i: int) -> bool:
        return 0 <= i < len(lines) and lines[i].lstrip().startswith(prefixos)

    achadas: set[tuple[int, int]] = set()
    for alvo in targets:
        i = alvo - 1 if comentario(alvo - 1) else alvo - 2
        if not comentario(i):
            continue
        inicio, fim = i, i
        while comentario(inicio - 1):
            inicio -= 1
        while comentario(fim + 1):
            fim += 1
        achadas.add((inicio + 1, fim + 1))
    return sorted(achadas)


def _tipo(caminho: str, bloco: list[str] | None) -> str:
    """DOCS, DOC_ONLY ou CODE de um arquivo, pelo bloco dele no diff -U0 (None: fora do diff)."""
    extensao = _extensao(caminho)
    if extensao in _EXTENSOES_DE_DOC:
        return "DOCS"
    prefixos = _PREFIXOS_DE_COMENTARIO.get(extensao)
    if prefixos is None or bloco is None:
        return "CODE"
    mudadas = [linha[1:] for linha in bloco[_inicio_dos_hunks(bloco):] if linha.startswith(("+", "-"))]
    # Sem linha mudada (só o modo, renomeação pura, binário), nada mostra que o diff é só comentário,
    # e o arquivo segue o fluxo de código.
    if mudadas and all(not m.strip() or m.lstrip().startswith(prefixos) for m in mudadas):
        return "DOC_ONLY"
    return "CODE"


def file_kind(repo: Path, base: str, head: str, path: str) -> str:
    """"DOCS", "DOC_ONLY" ou "CODE" do arquivo `path` (caminho no head) no intervalo base...head.

    `.md` e `.txt` são DOCS. Extensão com prefixo de comentário conhecido é DOC_ONLY quando o diff -U0
    tem linha `+` ou `-` e toda linha `+` e `-` é comentário ou vazia; docstring entre aspas triplas
    não é comentário. O resto é CODE.
    """
    arquivo = _diff_por_arquivo(repo, base, head).get(path)
    return _tipo(path, None if arquivo is None else arquivo[1])


def identifiers(lines: list[str], added: list[int]) -> list[str]:
    """Trechos entre crases das linhas `added` (1-indexadas), com 3 caracteres ou mais, sem
    repetição, na ordem em que aparecem no arquivo."""
    achados: dict[str, None] = {}
    for n in sorted(set(added)):
        if 1 <= n <= len(lines):
            for trecho in _CRASES_RE.findall(lines[n - 1]):
                trecho = trecho.strip()
                if len(trecho) >= 3:
                    achados.setdefault(trecho)
    return list(achados)


# ---------------------------------------------------------------------------
# Saída JSON.
# ---------------------------------------------------------------------------

def _commit(repo: Path, revisao: str) -> str:
    """O sha do commit da revisão."""
    return _git(repo, "rev-parse", "--verify", "--end-of-options", f"{revisao}^{{commit}}").decode().strip()


def _linhas_no_head(repo: Path, head: str, caminho: str) -> list[str]:
    """As linhas do arquivo no commit `head`, e não na árvore de trabalho, que pode estar em outro commit.

    Corta só em "\\n", como o git conta as linhas (um \\r solto não abre linha); o "\\n" final não abre
    linha.
    """
    linhas = _git(repo, "cat-file", "blob", f"{head}:{caminho}").decode("utf-8", "replace").split("\n")
    if linhas[-1] == "":
        linhas.pop()
    return linhas


def _unidades_com_mudancas(
        linhas: list[str], info: dict,
        unidades_de: Callable[[list[str], list[int]], list[tuple[int, int]]]) -> list[dict]:
    """As unidades, cada uma com o `changed`: as linhas acrescentadas e os cortes que caem nela.

    Um alvo pertence à unidade que contém a unidade dele. O corte logo depois de um parágrafo ou de um
    bloco de comentário, ou no fim do arquivo, fica fora do intervalo da unidade a que pertence, e
    entra no `changed` pela linha mais próxima dentro dela.
    """
    alvos = sorted(set(info["added"]) | set(info["removed_at"]))
    unidades = unidades_de(linhas, alvos)
    mudadas: dict[tuple[int, int], set[int]] = {unidade: set() for unidade in unidades}
    for alvo in alvos:
        for inicio, fim in unidades_de(linhas, [alvo]):
            dona = next(u for u in unidades if u[0] <= inicio and fim <= u[1])
            mudadas[dona].add(min(max(alvo, dona[0]), dona[1]))
    return [{"start": inicio, "end": fim, "changed": sorted(mudadas[(inicio, fim)])}
            for inicio, fim in unidades]


def _escopo(repo: Path, base: str, head: str) -> dict:
    """O escopo da rodada de verificação no intervalo base...head, na forma do JSON do CLI."""
    # Resolvidos uma vez: o JSON diz o commit lido, e um `HEAD` que ande no meio não mistura commits.
    base, head = _commit(repo, base), _commit(repo, head)
    arquivos = []
    for caminho, (info, bloco) in _diff_por_arquivo(repo, base, head).items():
        tipo = _tipo(caminho, bloco)
        unidades: list[dict] = []
        nomes: list[str] = []
        if tipo != "CODE" and info["status"] != "D":
            linhas = _linhas_no_head(repo, head, caminho)
            unidades_de = markdown_units if tipo == "DOCS" else partial(comment_units, path=caminho)
            unidades = _unidades_com_mudancas(linhas, info, unidades_de)
            nomes = identifiers(linhas, info["added"])
        arquivos.append({"path": caminho, "kind": tipo, "status": info["status"],
                         "units": unidades, "identifiers": nomes})
    return {
        "base": base, "head": head, "files": arquivos,
        "totals": {
            "prose_files": sum(f["kind"] != "CODE" and f["status"] != "D" for f in arquivos),
            "code_files": sum(f["kind"] == "CODE" for f in arquivos),
            "units": sum(len(f["units"]) for f in arquivos),
            "unit_lines": sum(u["end"] - u["start"] + 1 for f in arquivos for u in f["units"]),
        },
    }


def _json(escopo: dict) -> str:
    """O escopo em JSON, um arquivo por linha: com indent, cada unidade ocuparia sete linhas."""
    arquivos = ",\n".join("  " + json.dumps(f, ensure_ascii=False) for f in escopo["files"])
    lista = f"[\n{arquivos}\n ]" if arquivos else "[]"
    return (f'{{"base": {json.dumps(escopo["base"])}, "head": {json.dumps(escopo["head"])},\n'
            f' "files": {lista},\n'
            f' "totals": {json.dumps(escopo["totals"])}}}')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print, as JSON, the prose unit around each changed line of BASE...HEAD.")
    parser.add_argument("--repo", required=True, type=Path, help="Repository directory.")
    parser.add_argument("--base", required=True,
                        help="Base revision (the merge base is taken, as in BASE...HEAD).")
    parser.add_argument("--head", required=True,
                        help="Head revision; files are read from it, not from the working tree.")
    args = parser.parse_args(argv)
    try:
        escopo = _escopo(args.repo, args.base, args.head)
    except subprocess.CalledProcessError as erro:
        mensagem = erro.stderr.decode("utf-8", "replace").strip()
        print(f"prose_units.py: `{' '.join(erro.cmd)}` failed (rc {erro.returncode}): {mensagem}",
              file=sys.stderr)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")  # caminho ou identificador fora do cp1252 derrubaria o print
    print(_json(escopo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
