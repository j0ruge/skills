#!/usr/bin/env python3
"""
prose_units.py — as unidades de prosa em volta de cada linha mudada de um intervalo do git.

A rodada de verificação do codereview não relê o arquivo inteiro: lê, em volta de cada hunk, a
unidade que o contém (o parágrafo, o item de lista com as continuações, a linha da tabela, o bloco
cercado). Este script calcula esse escopo a partir do diff, para que ele não dependa do julgamento
da sessão.

Só biblioteca padrão. Não grava arquivo nenhum.
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from pathlib import Path

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


def _arquivo_do_bloco(bloco: list[str]) -> tuple[str | None, dict]:
    """(caminho no head, {"added", "removed_at", "status"}) de um bloco do diff -U0.

    Antes do primeiro `@@` vem o cabeçalho; depois dele, toda linha do arquivo começa com `+`, `-`,
    espaço ou `\\`, e uma linha que começa com `@@` só pode ser outro hunk. Por isso um `+++`
    acrescentado ao arquivo nunca é lido como cabeçalho.
    """
    fim_do_cabecalho = next((i for i, linha in enumerate(bloco) if linha.startswith("@@")), len(bloco))
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


def changed_lines(repo: Path, base: str, head: str) -> dict[str, dict]:
    """Por caminho no head: {"added": [...], "removed_at": [...], "status": "M"|"A"|"D"|"R"}.

    `added` são as linhas `+` no head. `removed_at` é, para cada hunk sem linha `+`, a linha do head
    logo depois do corte (mínimo 1); num corte no fim do arquivo ela passa da última linha. Arquivo
    apagado sai pelo caminho que tinha na base; renomeado, pelo caminho novo. Erro do git sobe como
    subprocess.CalledProcessError, com o stderr em bytes.
    """
    # Os prefixos, a cor e o diff externo vêm explícitos porque a config do usuário muda os três.
    # O --end-of-options impede que um sha começado por `-` vire opção (um --output gravaria arquivo).
    # A saída vem em bytes: em modo texto, o subprocess troca um \r solto numa linha do arquivo por
    # "\n", e o resto da linha viraria uma linha do diff (até um `diff --git` de arquivo fantasma).
    texto = subprocess.run(
        ["git", "-P", "-C", str(repo), "diff", "-U0", "--find-renames", "--no-color", "--no-ext-diff",
         "--src-prefix=a/", "--dst-prefix=b/", "--end-of-options", f"{base}...{head}", "--"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8", "replace")
    mudadas: dict[str, dict] = {}
    for bloco in _blocos(texto):
        caminho, info = _arquivo_do_bloco(bloco)
        if caminho is not None:
            mudadas[caminho] = info
    return mudadas


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
