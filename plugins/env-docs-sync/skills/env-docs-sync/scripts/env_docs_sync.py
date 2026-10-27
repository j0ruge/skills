#!/usr/bin/env python3
"""env-docs-sync: mantém os arquivos .env* de um repositório espelhados numa Página de ambientes.

Este arquivo tem três camadas, nesta ordem:

1. **Núcleo puro.** Config, Varredura, hash, Bloco de arquivo, plano de operações, estado e a
   Página de ambientes inteira. Não abre rede, não chama o backend de documentação nem o ssh.
   Relógio, sha do commit, conteúdo dos ambientes remotos e o leitor do corpo atual entram por
   parâmetro.
2. **Adaptadores.** O `DestinoDiretorio`, um destino local para teste e inspeção, e a fábrica que
   escolhe o destino por `doc.backend`. Todos se encaixam pelas mesmas costuras: `Destino`
   (ler_corpo/escrever) e o mapa `atuais` de `planejar`.
3. **Entrada do hook.** Lê o payload do Claude Code ou do Codex CLI, acha a raiz pelo git, aplica o
   filtro do Checkout da verdade, refaz a Varredura e sincroniza sob trava, com o estado por
   repositório na pasta de dados do plugin. Sempre sai com 0.
4. **CLI** (`validate`, `scan`, `plan`, `sync`, `status`, `render-page`, `hook`).

Regra de segredo, em todas as camadas: nenhum valor de arquivo .env* vai para stdout, stderr,
mensagem de erro, `repr` ou estado. O valor só vai para o corpo do Bloco de arquivo, que é o destino.
Só biblioteca padrão; Python 3.11+.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import functools
import hashlib
import html
import json
import os
import re
import socket
import string
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Mapping, Protocol

__version__ = "0.1.0"

AMBIENTES = ("development", "staging", "production")
"""Ambientes conhecidos, na ordem da página e do plano."""

ACOES = ("criar", "trocar", "marcar_ausente")

EXCLUDE_PADRAO = (
    "**/.git/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/graphify-out/**",
    "**/test-results/**",
    "**/playwright-report/**",
    "**/.worktrees/**",
    "**/.claude/worktrees/**",
    "**/.env-docs.json",
)
"""Piso do exclude: vale sempre, somado ao `exclude` da config. Uma pasta com `.git` próprio
(worktree, submódulo, clone aninhado) também fica de fora, seja qual for o nome dela."""

TEMPLATE_PADRAO = Path(__file__).resolve().parent.parent / "assets" / "ambientes-template.html"
PLACEHOLDERS = frozenset({"allowed_roles", "environments_table", "environment_sections", "ci_cd", "run"})
ESTADO_VERSAO = 1


class ErroEnvDocs(Exception):
    """Erro esperado do env-docs-sync. A mensagem nunca carrega valor de arquivo .env*."""


class ErroDeConfig(ErroEnvDocs):
    """Config inválida. `erros` traz todos os problemas achados, um por item, com o caminho JSON."""

    def __init__(self, erros):
        self.erros = list(erros)
        super().__init__("; ".join(self.erros))


class ErroDeEstado(ErroEnvDocs):
    """Estado ilegível ou com algo além de hashes e carimbos."""


# ---------------------------------------------------------------------------------------------
# Config (.env-docs.json)
# ---------------------------------------------------------------------------------------------

_RE_INTERVALO = re.compile(r"([1-9][0-9]*)([mhd])")
_SEGUNDOS = {"m": 60, "h": 3600, "d": 86400}
_RE_NOME_DE_VARIAVEL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_RE_HOST = re.compile(r"[A-Za-z0-9_.@:\[\]][A-Za-z0-9_.@:\[\]-]*")

_CAMPOS_DOC = ("backend", "cli", "python", "target", "page_id", "allowed_roles")
_CAMPOS_AMBIENTE = ("source", "server", "domain", "where", "source_of_truth")
_CAMPOS_LOCAL = _CAMPOS_AMBIENTE + ("machine",)
_CAMPOS_SSH = _CAMPOS_AMBIENTE + ("host", "auth_env", "files")
_CAMPOS_TOPO = ("doc", "values", "include", "exclude", "environments", "run")


def intervalo_em_segundos(texto) -> int:
    """`remote_check_every` ("30m", "24h", "2d") em segundos."""
    casou = _RE_INTERVALO.fullmatch(texto) if isinstance(texto, str) else None
    if not casou:
        raise ErroDeConfig(["config.remote_check_every: use um inteiro positivo seguido de m, h ou d (ex.: 24h)"])
    return int(casou.group(1)) * _SEGUNDOS[casou.group(2)]


def caminho_relativo_valido(caminho) -> bool:
    """Caminho relativo à raiz, com `/`, sem `..`, `.`, segmento vazio, barra invertida ou controle."""
    if not isinstance(caminho, str) or not caminho or caminho.startswith("/"):
        return False
    if "\\" in caminho or any(ord(c) < 32 for c in caminho):
        return False
    return all(parte not in ("", ".", "..") for parte in caminho.split("/"))


class _Coletor:
    def __init__(self):
        self.erros = []

    def erro(self, onde, mensagem):
        self.erros.append(f"{onde}: {mensagem}")

    def objeto(self, valor, onde, obrigatorias, opcionais=()):
        if not isinstance(valor, dict):
            self.erro(onde, "precisa ser um objeto")
            return False
        for chave in obrigatorias:
            if chave not in valor:
                self.erro(f"{onde}.{chave}", "campo obrigatório ausente")
        for chave in valor:
            if chave not in obrigatorias and chave not in opcionais:
                self.erro(f"{onde}.{chave}", "chave desconhecida")
        return True

    def texto(self, obj, chave, onde):
        if chave in obj and (not isinstance(obj[chave], str) or not obj[chave].strip()):
            self.erro(f"{onde}.{chave}", "precisa ser um texto não vazio")

    def padroes(self, obj, chave, onde, vazio_ok):
        if chave not in obj:
            return
        valor = obj[chave]
        if not isinstance(valor, list) or (not valor and not vazio_ok):
            self.erro(f"{onde}.{chave}", "precisa ser uma lista" + ("" if vazio_ok else " não vazia") + " de padrões")
            return
        for i, padrao in enumerate(valor):
            if not caminho_relativo_valido(padrao):
                self.erro(f"{onde}.{chave}[{i}]", "padrão precisa ser relativo à raiz, com /, sem .. nem \\")


def validar_config(dados) -> dict:
    """Valida a config inteira e devolve o próprio dicionário. Junta todos os erros num ErroDeConfig."""
    c = _Coletor()
    tem_ssh = isinstance(dados, dict) and isinstance(dados.get("environments"), dict) and any(
        isinstance(a, dict) and a.get("source") == "ssh" for a in dados["environments"].values())
    obrigatorias = _CAMPOS_TOPO + (("remote_check_every",) if tem_ssh else ())
    if not c.objeto(dados, "config", obrigatorias, ("remote_check_every",)):
        raise ErroDeConfig(c.erros)

    doc = dados.get("doc")
    if "doc" in dados and c.objeto(doc, "config.doc", _CAMPOS_DOC):
        if "backend" in doc and doc["backend"] != "kb":
            c.erro("config.doc.backend", "backend não suportado; o único nesta versão é \"kb\"")
        for chave in ("cli", "python", "target"):
            c.texto(doc, chave, "config.doc")
        if "page_id" in doc:
            pid = doc["page_id"]
            if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
                c.erro("config.doc.page_id", "precisa ser um inteiro positivo")
        if "allowed_roles" in doc:
            papeis = doc["allowed_roles"]
            if (not isinstance(papeis, list) or not papeis
                    or any(not isinstance(p, str) or not p.strip() for p in papeis)):
                c.erro("config.doc.allowed_roles", "precisa ser uma lista não vazia de nomes de papel")
            elif len(set(papeis)) != len(papeis):
                c.erro("config.doc.allowed_roles", "papel repetido")

    if "values" in dados and dados["values"] != "full":
        c.erro("config.values", "o único modo nesta versão é \"full\" (conteúdo integral na página restrita)")
    if "remote_check_every" in dados:
        try:
            intervalo_em_segundos(dados["remote_check_every"])
        except ErroDeConfig as erro:
            c.erros.extend(erro.erros)
    c.padroes(dados, "include", "config", vazio_ok=False)
    c.padroes(dados, "exclude", "config", vazio_ok=True)

    ambientes = dados.get("environments")
    if "environments" in dados and c.objeto(ambientes, "config.environments", ("development",), AMBIENTES[1:]):
        for nome, amb in ambientes.items():
            if nome in AMBIENTES:
                _validar_ambiente(c, nome, amb)

    if "run" in dados:
        if not isinstance(dados["run"], list):
            c.erro("config.run", "precisa ser uma lista")
        else:
            for i, item in enumerate(dados["run"]):
                onde = f"config.run[{i}]"
                if c.objeto(item, onde, ("label", "command")):
                    c.texto(item, "label", onde)
                    c.texto(item, "command", onde)

    if c.erros:
        raise ErroDeConfig(c.erros)
    return dados


def _validar_ambiente(c, nome, amb):
    onde = f"config.environments.{nome}"
    local = nome == "development"
    if not c.objeto(amb, onde, _CAMPOS_LOCAL if local else _CAMPOS_SSH):
        return
    for chave in _CAMPOS_AMBIENTE + (("machine",) if local else ("host",)):
        c.texto(amb, chave, onde)
    if "source" in amb:
        esperado = "local" if local else "ssh"
        if amb["source"] != esperado:
            c.erro(f"{onde}.source", f"precisa ser \"{esperado}\" nesta versão")
    if local:
        return
    if isinstance(amb.get("host"), str) and amb["host"].strip() and not _RE_HOST.fullmatch(amb["host"]):
        c.erro(f"{onde}.host", "host inválido (sem espaço e sem começar por -)")
    if "auth_env" in amb and amb["auth_env"] is not None:
        if not isinstance(amb["auth_env"], str) or not _RE_NOME_DE_VARIAVEL.fullmatch(amb["auth_env"]):
            c.erro(f"{onde}.auth_env", "precisa ser null (chave ssh) ou o NOME de uma variável de ambiente")
    if "files" in amb:
        arquivos = amb["files"]
        if not isinstance(arquivos, dict) or not arquivos:
            c.erro(f"{onde}.files", "precisa ser um objeto não vazio {caminho na página: caminho remoto}")
            return
        for rel, remoto in arquivos.items():
            if not caminho_relativo_valido(rel):
                c.erro(f"{onde}.files", f"chave {rel!r} precisa ser um caminho relativo, com /, sem ..")
            if (not isinstance(remoto, str) or not remoto.startswith(("/", "~/"))
                    or any(ord(ch) < 32 for ch in remoto)):
                c.erro(f"{onde}.files", f"o caminho remoto de {rel!r} precisa começar por / ou ~/")


def _sem_chave_duplicada(origem):
    def hook(pares):
        obj = {}
        for chave, valor in pares:
            if chave in obj:
                raise ErroDeConfig([f"{origem}: chave duplicada {chave!r}"])
            obj[chave] = valor
        return obj
    return hook


def carregar_config(caminho) -> dict:
    """Lê e valida a `.env-docs.json`. Arquivo ausente, JSON inválido ou chave duplicada são erro."""
    caminho = Path(caminho)
    try:
        texto = caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ErroDeConfig([f"{caminho}: arquivo não encontrado"]) from None
    try:
        dados = json.loads(texto, object_pairs_hook=_sem_chave_duplicada(str(caminho)))
    except json.JSONDecodeError as erro:
        raise ErroDeConfig([f"{caminho}: JSON inválido na linha {erro.lineno}, coluna {erro.colno}: {erro.msg}"]) from None
    return validar_config(dados)


# ---------------------------------------------------------------------------------------------
# Varredura e hash
# ---------------------------------------------------------------------------------------------

def _glob_para_regex(padrao: str) -> str:
    partes, i, n = [], 0, len(padrao)
    while i < n:
        if padrao.startswith("**/", i):
            partes.append("(?:.*/)?")
            i += 3
        elif padrao.startswith("**", i):
            partes.append(".*")
            i += 2
        elif padrao[i] == "*":
            partes.append("[^/]*")
            i += 1
        elif padrao[i] == "?":
            partes.append("[^/]")
            i += 1
        elif padrao[i] == "[" and "]" in padrao[i + 2:]:
            fim = padrao.index("]", i + 2)
            classe = padrao[i + 1:fim]
            if classe.startswith("!"):
                classe = "^" + classe[1:]
            partes.append("[" + classe.replace("\\", "\\\\") + "]")
            i = fim + 1
        else:
            partes.append(re.escape(padrao[i]))
            i += 1
    return "".join(partes)


@functools.lru_cache(maxsize=256)
def _compilar(padrao: str) -> re.Pattern:
    return re.compile(_glob_para_regex(padrao), re.DOTALL)


def casa_padrao(caminho: str, padroes) -> bool:
    """O caminho relativo casa com algum padrão? `**/` = zero ou mais pastas; `*` e `?` não cruzam `/`."""
    return any(_compilar(p).fullmatch(caminho) for p in padroes)


def varredura(raiz, include, exclude) -> list[str]:
    """Os arquivos sob `raiz` que casam com `include` e não com `exclude` + EXCLUDE_PADRAO.

    Devolve caminhos relativos com `/`, em ordem. Não desce em pasta excluída nem em pasta que
    tenha `.git` próprio (outro checkout). Symlink de arquivo entra só se o alvo estiver dentro da
    raiz; symlink de pasta não é seguido.
    """
    raiz = Path(raiz)
    raiz_real = raiz.resolve()
    exclusoes = (*EXCLUDE_PADRAO, *exclude)
    podas = tuple(p[:-3] for p in exclusoes if p.endswith("/**"))
    achados = []
    for pasta, subpastas, arquivos in os.walk(raiz, followlinks=False):
        rel_pasta = Path(pasta).relative_to(raiz).as_posix()
        prefixo = "" if rel_pasta == "." else rel_pasta + "/"
        subpastas[:] = sorted(
            d for d in subpastas
            if not casa_padrao(prefixo + d, podas) and not os.path.lexists(os.path.join(pasta, d, ".git")))
        for nome in arquivos:
            rel = prefixo + nome
            if not casa_padrao(rel, include) or casa_padrao(rel, exclusoes):
                continue
            completo = Path(pasta) / nome
            if completo.is_symlink():
                alvo = completo.resolve()
                if not alvo.is_relative_to(raiz_real) or not alvo.is_file():
                    continue
            elif not completo.is_file():
                continue
            achados.append(rel)
    return sorted(achados)


def hash_sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def ler_arquivos(raiz, caminhos) -> dict[str, bytes]:
    """{caminho relativo: bytes} lidos do disco (a fonte depois da edição, nunca o payload do hook)."""
    raiz = Path(raiz)
    return {rel: (raiz / rel).read_bytes() for rel in caminhos}


# ---------------------------------------------------------------------------------------------
# Bloco de arquivo
# ---------------------------------------------------------------------------------------------

_RE_COMMIT = re.compile(r"[0-9a-f]{7,40}")
_RE_CALLOUT_AUSENTE = re.compile(
    r'<p\b[^>]*\bclass="callout danger"[^>]*>\s*ausente desde \d{4}-\d{2}-\d{2}\b.*?</p>\n?', re.DOTALL)


def commit_curto(sha: str) -> str:
    if not isinstance(sha, str) or not _RE_COMMIT.fullmatch(sha):
        raise ErroEnvDocs("commit precisa ser um sha hexadecimal minúsculo de 7 a 40 caracteres")
    return sha[:7]


def _texto(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroEnvDocs("conteúdo não é UTF-8") from None


def bloco_de_arquivo(conteudo, *, sincronizado_em: datetime, commit: str | None) -> str:
    """O corpo do Bloco de arquivo (sem o h3): o `<pre>` com o conteúdo integral e a linha ⓘ.

    É exatamente o que vai no stdin do `section-set`. `commit` é o sha do Checkout da verdade;
    None omite o trecho (ambiente remoto).
    """
    texto = _texto(conteudo)
    meta = f"ⓘ sincronizado em {sincronizado_em:%Y-%m-%d %H:%M}"
    if commit is not None:
        meta += f" · commit {commit_curto(commit)}"
    return (f'<pre><code class="language-bash">{html.escape(texto, quote=False)}</code></pre>\n'
            f"<p>{meta}</p>")


class _ExtratorDeBloco(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fase = "antes"
        self.partes = []

    def handle_starttag(self, tag, attrs):
        if self.fase == "antes" and tag == "pre":
            self.fase = "pre"
        elif self.fase == "pre" and tag == "code":
            self.fase = "dentro"

    def handle_endtag(self, tag):
        if self.fase == "dentro" and tag in ("code", "pre"):
            self.fase = "depois"
        elif self.fase == "pre" and tag == "pre":
            self.fase = "sem_code"

    def handle_data(self, data):
        if self.fase == "dentro":
            self.partes.append(data)


def conteudo_do_bloco(corpo: str) -> str | None:
    """O inverso de `bloco_de_arquivo`: o texto do primeiro `<pre><code>`, sem escape.

    None se não houver um `<pre><code>` fechado. Tolera atributos que o destino acrescenta (ids).
    Serve para conferir o hash do bloco relido.
    """
    extrator = _ExtratorDeBloco()
    extrator.feed(corpo)
    extrator.close()
    return "".join(extrator.partes) if extrator.fase == "depois" else None


def callout_ausente(desde: date) -> str:
    return (f'<p class="callout danger">ausente desde {desde:%Y-%m-%d}: o arquivo não existe mais na '
            "Fonte da verdade; o bloco abaixo é a última versão sincronizada.</p>")


def marcar_ausente(corpo: str | None, desde: date) -> str:
    """O corpo atual com o callout "ausente desde" no topo. Mantém o bloco e troca um callout anterior."""
    resto = _RE_CALLOUT_AUSENTE.sub("", corpo or "").lstrip("\n")
    callout = callout_ausente(desde)
    return f"{callout}\n{resto}" if resto else callout


# ---------------------------------------------------------------------------------------------
# Plano de operações
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Mudanca:
    """O que mudou num (ambiente, caminho), decidido só por hashes."""
    ambiente: str
    caminho: str
    acao: str
    sha256: str | None

    def resumo(self) -> str:
        """Uma linha segura para log: ambiente, ação, caminho e o início do hash. Nunca o conteúdo."""
        sufixo = f" sha256:{self.sha256[:12]}" if self.sha256 else ""
        return f"{self.ambiente} {self.acao} {self.caminho}{sufixo}"


@dataclass(frozen=True)
class Operacao(Mudanca):
    """Uma Mudanca com o corpo pronto para o destino. O corpo carrega valores: fica fora do repr."""
    corpo: str = field(default="", repr=False)

    @property
    def sob(self) -> str:
        """O h2 da Seção de ambiente, no formato do `--under` do section-set."""
        return f"[{self.ambiente}]"


def _conferir_ambiente(ambiente):
    if ambiente not in AMBIENTES:
        raise ErroEnvDocs(f"ambiente desconhecido: {ambiente!r} (conhecidos: {', '.join(AMBIENTES)})")


def _conferir_caminho(ambiente, caminho):
    if not caminho_relativo_valido(caminho):
        raise ErroEnvDocs(f"{ambiente}: caminho inválido (precisa ser relativo, com /, sem ..)")


def diferencas(estado: Mapping, hashes_atuais: Mapping[str, Mapping[str, str]]) -> list[Mudanca]:
    """Compara o estado com os hashes atuais. Só os ambientes presentes em `hashes_atuais` contam.

    Ambiente ausente do mapa não foi lido nesta rodada (ssh fora do ar, fora da janela) e fica
    intocado. Ordem: development → staging → production; caminhos em ordem (sorted).
    """
    for ambiente in hashes_atuais:
        _conferir_ambiente(ambiente)
    anteriores = estado.get("environments", {})
    mudancas = []
    for ambiente in AMBIENTES:
        if ambiente not in hashes_atuais:
            continue
        atuais, antes = hashes_atuais[ambiente], anteriores.get(ambiente, {})
        for caminho in sorted(set(atuais) | set(antes)):
            _conferir_caminho(ambiente, caminho)
            entrada = antes.get(caminho)
            if caminho in atuais:
                sha = atuais[caminho]
                if entrada is None:
                    mudancas.append(Mudanca(ambiente, caminho, "criar", sha))
                elif "absent_since" in entrada or entrada.get("sha256") != sha:
                    mudancas.append(Mudanca(ambiente, caminho, "trocar", sha))
            elif "absent_since" not in entrada:
                mudancas.append(Mudanca(ambiente, caminho, "marcar_ausente", None))
    return mudancas


def planejar(estado: Mapping, atuais: Mapping[str, Mapping[str, bytes]], *, sincronizado_em: datetime,
             commit: str | None, ler_corpo: Callable[[str, str], str | None] | None = None) -> list[Operacao]:
    """As operações para levar o destino ao estado de `atuais`, com o corpo pronto. Vazio se nada mudou.

    `atuais`: {ambiente: {caminho: bytes}} lidos da Fonte da verdade de cada ambiente checado nesta
    rodada. `commit` vale só para development (o Checkout da verdade). `ler_corpo(ambiente, caminho)`
    devolve o corpo atual no destino; é exigido só quando algum arquivo sumiu, porque o bloco antigo
    fica na página sob o callout.
    """
    hashes = {amb: {c: hash_sha256(d) for c, d in arquivos.items()} for amb, arquivos in atuais.items()}
    operacoes = []
    for m in diferencas(estado, hashes):
        if m.acao == "marcar_ausente":
            if ler_corpo is None:
                raise ErroEnvDocs(f"{m.ambiente} {m.caminho}: marcar_ausente precisa de ler_corpo "
                                  "(o bloco antigo fica na página)")
            corpo = marcar_ausente(ler_corpo(m.ambiente, m.caminho), sincronizado_em)
        else:
            try:
                corpo = bloco_de_arquivo(atuais[m.ambiente][m.caminho], sincronizado_em=sincronizado_em,
                                         commit=commit if m.ambiente == "development" else None)
            except ErroEnvDocs as erro:
                raise ErroEnvDocs(f"{m.ambiente} {m.caminho}: {erro}") from None
        operacoes.append(Operacao(m.ambiente, m.caminho, m.acao, m.sha256, corpo=corpo))
    return operacoes


# ---------------------------------------------------------------------------------------------
# Estado: só hashes e carimbos
# ---------------------------------------------------------------------------------------------

_RE_HEX64 = re.compile(r"[0-9a-f]{64}")
_RE_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")
_RE_CARIMBO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?")


def estado_vazio() -> dict:
    return {"version": ESTADO_VERSAO, "environments": {}, "remote_checked_at": {}}


def _carimbo(quando: datetime) -> str:
    return quando.isoformat(timespec="seconds")


def validar_estado(estado) -> None:
    """Recusa qualquer coisa além de hashes e carimbos. A mensagem nunca ecoa o valor recusado."""
    def falha(onde):
        raise ErroDeEstado(f"estado inválido em {onde}: o estado só guarda hashes sha256 e carimbos")

    if not isinstance(estado, dict) or set(estado) != {"version", "environments", "remote_checked_at"}:
        falha("topo")
    if estado["version"] != ESTADO_VERSAO:
        falha("version")
    if not isinstance(estado["environments"], dict):
        falha("environments")
    for ambiente, arquivos in estado["environments"].items():
        if ambiente not in AMBIENTES or not isinstance(arquivos, dict):
            falha("environments")
        for caminho, entrada in arquivos.items():
            onde = f"environments.{ambiente}"
            if not caminho_relativo_valido(caminho) or not isinstance(entrada, dict):
                falha(onde)
            sha = entrada.get("sha256")
            if set(entrada) == {"sha256", "synced_at"}:
                ok = isinstance(sha, str) and _RE_HEX64.fullmatch(sha) and _e_carimbo(entrada["synced_at"])
            elif set(entrada) == {"sha256", "absent_since"}:
                ok = ((sha is None or (isinstance(sha, str) and _RE_HEX64.fullmatch(sha)))
                      and isinstance(entrada["absent_since"], str) and _RE_DATA.fullmatch(entrada["absent_since"]))
            else:
                ok = False
            if not ok:
                falha(f"{onde}.{caminho}")
    checados = estado["remote_checked_at"]
    if not isinstance(checados, dict):
        falha("remote_checked_at")
    for ambiente, quando in checados.items():
        if ambiente not in AMBIENTES or not _e_carimbo(quando):
            falha("remote_checked_at")


def _e_carimbo(valor) -> bool:
    return isinstance(valor, str) and bool(_RE_CARIMBO.fullmatch(valor) or _RE_DATA.fullmatch(valor))


def _gravar_privado(caminho, texto: str) -> None:
    """Gravação atômica em 0600 (temporário na mesma pasta + os.replace); a pasta nasce 0700."""
    caminho = Path(caminho)
    caminho.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descritor, temporario = tempfile.mkstemp(dir=caminho.parent, prefix=f".{caminho.name}.", suffix=".tmp")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as saida:
            os.fchmod(saida.fileno(), 0o600)
            saida.write(texto)
            saida.flush()
            os.fsync(saida.fileno())
        os.replace(temporario, caminho)
    except BaseException:
        if os.path.exists(temporario):
            os.unlink(temporario)
        raise


def carregar_estado(caminho) -> dict:
    """O estado gravado, ou um estado vazio se o arquivo não existe. Ilegível ou fora do formato: erro."""
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
    except FileNotFoundError:
        return estado_vazio()
    try:
        estado = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise ErroDeEstado(f"estado ilegível: JSON inválido na linha {erro.lineno}") from None
    validar_estado(estado)
    return estado


def gravar_estado(caminho, estado) -> None:
    """Valida (só hashes e carimbos) e grava em 0600, atomicamente."""
    validar_estado(estado)
    _gravar_privado(caminho, json.dumps(estado, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def registrar_operacao(estado: Mapping, op: Operacao, *, quando: datetime) -> dict:
    """Novo estado com a operação aplicada (não altera o recebido). Grave só depois de o destino confirmar."""
    novo = copy.deepcopy(dict(estado))
    arquivos = novo.setdefault("environments", {}).setdefault(op.ambiente, {})
    if op.acao == "marcar_ausente":
        anterior = arquivos.get(op.caminho, {}).get("sha256")
        arquivos[op.caminho] = {"sha256": anterior, "absent_since": f"{quando:%Y-%m-%d}"}
    else:
        arquivos[op.caminho] = {"sha256": op.sha256, "synced_at": _carimbo(quando)}
    return novo


class Destino(Protocol):
    """Porta do destino da documentação. O adaptador kb (I3) e o DestinoDiretorio a implementam."""

    def ler_corpo(self, ambiente: str, caminho: str) -> str | None: ...

    def escrever(self, op: Operacao) -> None: ...


@dataclass
class ResultadoSync:
    estado: dict
    aplicadas: list
    falhou: Operacao | None = None
    erro: BaseException | None = None


def aplicar(estado: Mapping, operacoes, destino: Destino, *, quando: datetime) -> ResultadoSync:
    """Escreve cada operação no destino, em ordem, e registra só as que o destino aceitou.

    Para na primeira falha: o estado devolvido não tem a operação que falhou nem as seguintes,
    e o próximo gatilho tenta de novo.
    """
    atual, aplicadas = dict(estado), []
    for op in operacoes:
        try:
            destino.escrever(op)
        except Exception as erro:  # o adaptador decide o tipo; quem chama relata sem valores
            return ResultadoSync(atual, aplicadas, op, erro)
        atual = registrar_operacao(atual, op, quando=quando)
        aplicadas.append(op)
    return ResultadoSync(atual, aplicadas)


# ---------------------------------------------------------------------------------------------
# Página de ambientes (inteira, para a migração por replace)
# ---------------------------------------------------------------------------------------------

def _esc(texto: str) -> str:
    return html.escape(texto, quote=False)


def tabela_de_ambientes(config: Mapping) -> str:
    cabecalho = "".join(f"<th>{c}</th>" for c in
                        ("Ambiente", "Servidor", "Domínio", "Onde vive o .env", "Fonte da verdade"))
    linhas = []
    for ambiente in AMBIENTES:
        dados = config["environments"].get(ambiente)
        if dados is None:
            continue
        celulas = [ambiente, dados["server"], dados["domain"], dados["where"], dados["source_of_truth"]]
        linhas.append("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in celulas) + "</tr>")
    return ("<table>\n<thead><tr>" + cabecalho + "</tr></thead>\n<tbody>\n"
            + "\n".join(linhas) + "\n</tbody>\n</table>")


def secao_de_ambiente(ambiente: str, blocos: Mapping[str, str]) -> str:
    """O h2 `[ambiente]` e, em ordem de caminho, um h3 por arquivo seguido do corpo do bloco."""
    partes = [f"<h2>[{ambiente}]</h2>"]
    for caminho in sorted(blocos):
        _conferir_caminho(ambiente, caminho)
        partes += [f"<h3>{_esc(caminho)}</h3>", blocos[caminho]]
    return "\n".join(partes)


def secao_como_rodar(config: Mapping) -> str:
    if not config["run"]:
        return "<p>Nenhum comando declarado em <code>run</code> na <code>.env-docs.json</code>.</p>"
    return "\n".join(f'<p><strong>{_esc(item["label"])}</strong></p>\n'
                     f'<pre><code class="language-bash">{_esc(item["command"])}</code></pre>'
                     for item in config["run"])


def secao_ci_cd(conteudo: str | None = None) -> str:
    if conteudo is not None:
        return conteudo
    return ("<p><em>a gerar</em>: esta versão do env-docs-sync ainda não gera a seção "
            "(nomes dos segredos do CI e runs-on dos workflows).</p>")


def carregar_template(caminho=TEMPLATE_PADRAO) -> str:
    return Path(caminho).read_text(encoding="utf-8")


def pagina_de_ambientes(config: Mapping, blocos: Mapping[str, Mapping[str, str]], *,
                        template: str | None = None, ci_cd: str | None = None) -> str:
    """A Página de ambientes inteira, do template, para o `replace`. `blocos`: {ambiente: {caminho: corpo}}."""
    configurados = config["environments"]
    sobra = sorted(set(blocos) - set(configurados))
    if sobra:
        raise ErroEnvDocs(f"blocos de ambiente não configurado: {', '.join(sobra)}")
    modelo = string.Template(carregar_template() if template is None else template)
    faltam = PLACEHOLDERS - set(modelo.get_identifiers())  # get_identifiers/is_valid: Python 3.11+
    if faltam or not modelo.is_valid():
        raise ErroEnvDocs(f"template inválido; placeholders ausentes: {', '.join(sorted(faltam)) or '-'}")
    secoes = "\n".join(secao_de_ambiente(a, blocos.get(a, {})) for a in AMBIENTES if a in configurados)
    try:
        return modelo.substitute(
            allowed_roles=_esc(", ".join(config["doc"]["allowed_roles"])),
            environments_table=tabela_de_ambientes(config),
            environment_sections=secoes,
            ci_cd=secao_ci_cd(ci_cd),
            run=secao_como_rodar(config),
        )
    except (KeyError, ValueError) as erro:
        raise ErroEnvDocs(f"template inválido: placeholder desconhecido {erro}") from None


# ---------------------------------------------------------------------------------------------
# Adaptador de teste: destino em diretório
# ---------------------------------------------------------------------------------------------

class DestinoDiretorio:
    """Destino local para teste e inspeção: `<pasta>/<ambiente>/<caminho>.html`, 0600 cada."""

    def __init__(self, pasta):
        self.pasta = Path(pasta)

    def _arquivo(self, ambiente, caminho) -> Path:
        _conferir_ambiente(ambiente)
        _conferir_caminho(ambiente, caminho)
        return self.pasta / ambiente / f"{caminho}.html"

    def ler_corpo(self, ambiente, caminho):
        arquivo = self._arquivo(ambiente, caminho)
        return arquivo.read_text(encoding="utf-8") if arquivo.is_file() else None

    def escrever(self, op):
        _gravar_privado(self._arquivo(op.ambiente, op.caminho), op.corpo)


def destino_da_config(config: Mapping, raiz: Path, ctx: "Contexto") -> Destino:
    """A fábrica padrão: o Destino do `doc.backend` da config."""
    backend = config["doc"]["backend"]
    if backend == "kb":
        raise ErroEnvDocs("adaptador kb ainda não implementado nesta versão; nada foi escrito")
    raise ErroEnvDocs(f"backend sem adaptador: {backend!r}")


# ---------------------------------------------------------------------------------------------
# Processo filho (ssh, e o backend do destino) e a fonte ssh do Sync remoto
# ---------------------------------------------------------------------------------------------

SSH_CONNECT_TIMEOUT = 10
"""Segundos para o ssh desistir de conectar (`-o ConnectTimeout`)."""
SSH_TIMEOUT = 30
"""Segundos para cada leitura remota inteira (conexão + `cat`)."""
LIMITE_REMOTO = 1 << 20
"""Um `.env` remoto acima de 1 MiB é erro de config (caminho apontando outro arquivo), não conteúdo."""
FERRAMENTAS_SSH = ("ssh", "scp", "sshpass", "rsync")
_RE_FERRAMENTA_SSH = re.compile(r"(?<![\w.-])(?:" + "|".join(FERRAMENTAS_SSH) + r")(?![\w.-])")


@dataclass(frozen=True)
class ResultadoComando:
    returncode: int
    stdout: bytes = field(default=b"", repr=False)
    stderr: bytes = field(default=b"", repr=False)


def rodar_comando(argv, *, env: Mapping[str, str], timeout: float, entrada: bytes | None = None) -> ResultadoComando:
    """O runner padrão: argv sem shell, ambiente explícito, stdin = `entrada` (ou /dev/null).

    Timeout e programa ausente viram ErroEnvDocs, sem ecoar argv nem saída. Os testes injetam outro
    runner com a mesma assinatura.
    """
    opcoes = {"input": entrada} if entrada is not None else {"stdin": subprocess.DEVNULL}
    try:
        saida = subprocess.run(list(argv), env=dict(env), capture_output=True, timeout=timeout, **opcoes)
    except subprocess.TimeoutExpired:
        raise ErroEnvDocs(f"{Path(argv[0]).name}: tempo esgotado ({timeout:g} s)") from None
    except FileNotFoundError:
        raise ErroEnvDocs(f"{Path(argv[0]).name}: programa não encontrado") from None
    except OSError as erro:
        raise ErroEnvDocs(f"{Path(argv[0]).name}: não rodou ({type(erro).__name__})") from None
    return ResultadoComando(saida.returncode, saida.stdout, saida.stderr)


def aspas_remotas(caminho: str) -> str:
    """O caminho remoto citado para o shell do servidor. `~/` fica fora das aspas, para expandir lá."""
    def citar(texto):
        return "'" + texto.replace("'", "'\\''") + "'"
    if caminho.startswith("~/"):
        resto = caminho[2:]
        return "~/" + citar(resto) if resto else "~/"
    return citar(caminho)


def comando_ssh(ambiente_cfg: Mapping, remoto: str, ambiente_do_processo: Mapping[str, str]):
    """(argv, env) para ler `remoto` do host do ambiente, só leitura (`cat`).

    `auth_env` null: chave, com `BatchMode=yes` (nunca pergunta nada). `auth_env` com um nome:
    `sshpass -e`, com a senha em `SSHPASS` no ambiente do filho, nunca em argv (que o `ps` mostra).
    A variável original sai do ambiente do filho. `--` antes do host impede que ele vire opção.
    """
    env = dict(ambiente_do_processo)
    tempo = ["-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}"]
    alvo = ["--", ambiente_cfg["host"], "cat -- " + aspas_remotas(remoto)]
    variavel = ambiente_cfg.get("auth_env")
    if variavel is None:
        return ["ssh", "-o", "BatchMode=yes", *tempo, *alvo], env
    senha = env.pop(variavel, None)
    if not senha:
        raise ErroEnvDocs(f"a variável {variavel} (auth_env) não está definida no ambiente; sem senha, "
                          "o ambiente não foi lido")
    env["SSHPASS"] = senha
    # Medido (sshpass 1.09, OpenSSH 9.6p1): BatchMode=yes desliga o prompt e tudo sai 255; com
    # NumberOfPasswordPrompts=1, senha errada também sai 255. Com o padrão, o sshpass vê o 2º prompt,
    # desiste depois de uma tentativa e sai 5, o que separa "senha errada" de "rede fora".
    return ["sshpass", "-e", "ssh", "-o", "BatchMode=no", *tempo, *alvo], env


def motivo_ssh(rc: int, *, sshpass: bool) -> str:
    """O motivo legível de um rc do ssh/sshpass, sem a saída de erro (que pode citar o servidor)."""
    if sshpass and rc == 5:
        return "senha recusada pelo servidor, sshpass rc 5"
    if sshpass and rc == 6:
        return "chave do host desconhecida (conecte uma vez à mão para aceitá-la), sshpass rc 6"
    if rc == 255:
        return "conexão ou autenticação ssh falhou, rc 255"
    if rc == 1:
        return "arquivo remoto ausente ou ilegível, rc 1"
    return f"rc {rc}"


def ler_remoto(nome: str, ambiente_cfg: Mapping, ctx: "Contexto") -> dict[str, bytes]:
    """{caminho na página: bytes} de um ambiente ssh. Qualquer falha levanta: o ambiente inteiro fica
    de fora desta rodada (não vira ausente), e o próximo gatilho tenta de novo."""
    arquivos = {}
    for rel, remoto in sorted(ambiente_cfg["files"].items()):
        argv, env = comando_ssh(ambiente_cfg, remoto, ctx.ambiente)
        resultado = ctx.runner(argv, env=env, timeout=SSH_TIMEOUT)
        if resultado.returncode != 0:
            raise ErroEnvDocs(f"{nome}: a leitura de {rel} por ssh falhou "
                              f"({motivo_ssh(resultado.returncode, sshpass=argv[0] == 'sshpass')})")
        if len(resultado.stdout) > LIMITE_REMOTO:
            raise ErroEnvDocs(f"{nome}: {rel} remoto é grande demais (> {LIMITE_REMOTO} bytes); confira o caminho")
        arquivos[rel] = resultado.stdout
    return arquivos


def ler_remotos(config: Mapping, ambientes, ctx: "Contexto") -> tuple[dict, list[str]]:
    """({ambiente: {caminho: bytes}} dos que leram, [avisos]). Quem falhou fica fora do mapa."""
    lidos, avisos = {}, []
    for nome in ambientes:
        try:
            lidos[nome] = ler_remoto(nome, config["environments"][nome], ctx)
        except ErroEnvDocs as erro:
            avisos.append(str(erro) if str(erro).startswith(f"{nome}:") else f"{nome}: {erro}")
    return lidos, avisos


def host_citado(comando: str, host: str) -> bool:
    """O comando do shell usa ssh, scp, sshpass ou rsync E cita o host (com ou sem `usuario@`)?

    Não interpreta o comando: procura a ferramenta como palavra e o nome do host com borda, para
    `host.example` não casar `host.example.evil` nem `192.0.2.6` casar `192.0.2.60`.
    """
    if not isinstance(comando, str) or not _RE_FERRAMENTA_SSH.search(comando):
        return False
    nome = host.rsplit("@", 1)[-1].strip("[]")
    return bool(nome) and re.search(r"(?<![\w.-])" + re.escape(nome) + r"(?![\w-]|\.\w)", comando) is not None


def _remotos(config: Mapping) -> list[str]:
    return [a for a in AMBIENTES if a != "development" and a in config["environments"]]


def _vencido(carimbo: str | None, intervalo: int, agora: datetime) -> bool:
    if carimbo is None:
        return True
    quando = datetime.fromisoformat(carimbo)
    if quando.tzinfo is None:
        quando = quando.astimezone()
    return quando > agora or (agora - quando).total_seconds() >= intervalo


def remotos_devidos(config: Mapping, estado: Mapping, gatilho, agora: datetime) -> list[str]:
    """Os ambientes ssh a ler neste gatilho: no PostToolUse `Bash`, os do host citado; na
    SessionStart, os cuja última leitura boa passou de `remote_check_every`. Os outros, nenhum."""
    remotos = _remotos(config)
    if not remotos:
        return []
    if gatilho.evento == "PostToolUse" and gatilho.comando is not None:
        return [a for a in remotos if host_citado(gatilho.comando, config["environments"][a]["host"])]
    if gatilho.evento == "SessionStart":
        intervalo = intervalo_em_segundos(config["remote_check_every"])
        checados = estado.get("remote_checked_at", {})
        return [a for a in remotos if _vencido(checados.get(a), intervalo, agora)]
    return []


def carimbar_remotos(estado: Mapping, ambientes, quando: datetime) -> dict:
    """Novo estado com `remote_checked_at` = `quando` nos ambientes dados (lidos e sem pendência)."""
    novo = copy.deepcopy(dict(estado))
    for ambiente in ambientes:
        novo.setdefault("remote_checked_at", {})[ambiente] = _carimbo(quando)
    return novo


# ---------------------------------------------------------------------------------------------
# Entrada do hook: gatilho, Checkout da verdade, estado por repositório, trava
# ---------------------------------------------------------------------------------------------

NOME_DA_CONFIG = ".env-docs.json"
EVENTOS_DO_HOOK = ("PostToolUse", "Stop", "SessionStart")
FERRAMENTAS_DE_EDICAO = ("Write", "Edit")
"""As do Claude Code. No Codex, a edição chega como `apply_patch`, que o matcher `Write|Edit` casa
por alias; `MultiEdit` não existe no Claude Code 2.1.309."""
MARCADORES_DO_PATCH = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")
ESPERA_DA_TRAVA = 30.0
_VARIAVEIS_DO_GIT = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


class TravaOcupada(ErroEnvDocs):
    """Outro processo segura a trava do repositório além da espera."""


@dataclass(frozen=True)
class Gatilho:
    """O que o hook usa do payload. O conteúdo do arquivo, que o payload também traz, fica de fora.

    `caminhos` (absolutos) só nas ferramentas de edição; None pede a Varredura completa da raiz do
    `cwd`. `comando` só no shell.
    """
    evento: str
    cwd: Path
    caminhos: tuple | None = None
    comando: str | None = None


def caminhos_do_patch(patch: str, cwd: Path) -> list[Path]:
    """Os caminhos das linhas `*** Add/Update/Delete File:` e `*** Move to:` de um `apply_patch`.

    O Codex 0.164.0 manda o caminho absoluto; relativo é resolvido contra o `cwd`.
    """
    caminhos = []
    for linha in patch.splitlines():
        for marcador in MARCADORES_DO_PATCH:
            if linha.startswith(marcador) and linha[len(marcador):].strip():
                bruto = linha[len(marcador):].strip()
                caminhos.append(Path(bruto) if os.path.isabs(bruto) else Path(cwd) / bruto)
    return caminhos


def ler_gatilho(payload) -> Gatilho | None:
    """O Gatilho do payload, ou None quando o payload não pede nada (inclusive Stop com
    `stop_hook_active`, a guarda de loop). Nunca lê o conteúdo que o payload carrega."""
    if not isinstance(payload, dict):
        return None
    evento, cwd = payload.get("hook_event_name"), payload.get("cwd")
    if evento not in EVENTOS_DO_HOOK or not isinstance(cwd, str) or not os.path.isabs(cwd):
        return None
    cwd = Path(cwd)
    if evento == "Stop":
        return None if payload.get("stop_hook_active") else Gatilho(evento, cwd)
    if evento == "SessionStart":
        return Gatilho(evento, cwd)
    ferramenta, entrada = payload.get("tool_name"), payload.get("tool_input")
    if not isinstance(entrada, dict):
        return None
    if ferramenta in FERRAMENTAS_DE_EDICAO:
        caminho = entrada.get("file_path")
        if not isinstance(caminho, str) or not caminho:
            return None
        return Gatilho(evento, cwd, caminhos=(Path(caminho) if os.path.isabs(caminho) else cwd / caminho,))
    comando = entrada.get("command")
    if not isinstance(comando, str):
        return None
    if ferramenta == "apply_patch":
        caminhos = caminhos_do_patch(comando, cwd)
        return Gatilho(evento, cwd, caminhos=tuple(caminhos)) if caminhos else None
    if ferramenta == "Bash":
        return Gatilho(evento, cwd, comando=comando)
    return None


def _git(pasta, *args) -> str | None:
    env = {k: v for k, v in os.environ.items() if k not in _VARIAVEIS_DO_GIT}
    try:
        saida = subprocess.run(["git", "-C", str(pasta), *args], capture_output=True, text=True,
                               timeout=10, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return saida.stdout if saida.returncode == 0 else None


def raiz_do_repositorio(pasta) -> Path | None:
    """A raiz do checkout que contém `pasta` (a 1ª pasta existente subindo, se ela sumiu), ou None."""
    pasta = Path(pasta)
    while not pasta.is_dir():
        if pasta.parent == pasta:
            return None
        pasta = pasta.parent
    saida = (_git(pasta, "rev-parse", "--show-toplevel") or "").strip()
    return Path(saida) if saida else None


def checkout_da_verdade(pasta) -> bool:
    """`pasta` está num checkout principal, não num worktree? (`--git-dir` == `--git-common-dir`)

    O `--path-format=absolute` (git 2.31+) é obrigatório: sem ele, numa subpasta do checkout
    principal o `--git-common-dir` sai relativo e o checkout parece worktree.
    """
    saida = _git(pasta, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    linhas = saida.splitlines() if saida else []
    return len(linhas) == 2 and os.path.realpath(linhas[0]) == os.path.realpath(linhas[1])


def maquina_confere(maquina: str, hostname: str) -> bool:
    """O hostname bate com `environments.development.machine`? Sem caixa; aceita o nome curto."""
    esperado, real = maquina.strip().lower(), hostname.strip().lower()
    return bool(esperado) and esperado in (real, real.split(".", 1)[0])


def pasta_de_estado(ambiente: Mapping[str, str]) -> Path:
    """Onde o estado mora: `CLAUDE_PLUGIN_DATA` (Claude Code e Codex), `PLUGIN_DATA` (Codex) ou,
    fora de um hook de plugin, `$XDG_STATE_HOME/env-docs-sync` (padrão `~/.local/state/env-docs-sync`).
    Valor vazio ou relativo não conta."""
    for chave in ("CLAUDE_PLUGIN_DATA", "PLUGIN_DATA"):
        valor = ambiente.get(chave) or ""
        if os.path.isabs(valor):
            return Path(valor)
    xdg = ambiente.get("XDG_STATE_HOME") or ""
    if not os.path.isabs(xdg):
        xdg = str(Path(ambiente.get("HOME") or Path.home()) / ".local" / "state")
    return Path(xdg) / "env-docs-sync"


def arquivo_de_estado(raiz, pasta) -> Path:
    """Um arquivo por repositório: `<pasta>/repos/<sha256 do caminho absoluto da raiz>.json`."""
    return Path(pasta) / "repos" / f"{hash_sha256(str(Path(raiz).resolve()).encode('utf-8'))}.json"


@contextlib.contextmanager
def trava_do_repo(raiz, pasta, espera: float = ESPERA_DA_TRAVA):
    """`flock` exclusivo por repositório, ao lado do arquivo de estado. Duas sessões, ou o PostToolUse
    e o Stop do mesmo turno, nunca sincronizam o mesmo repositório ao mesmo tempo."""
    arquivo = arquivo_de_estado(raiz, pasta).with_suffix(".lock")
    arquivo.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descritor = os.open(arquivo, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        limite = time.monotonic() + espera
        while True:
            try:
                fcntl.flock(descritor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= limite:
                    raise TravaOcupada("outro sync deste repositório ainda roda; "
                                       "o próximo gatilho tenta de novo") from None
                time.sleep(0.05)
        yield
    finally:
        os.close(descritor)  # fechar solta a trava


def _agora_local() -> datetime:
    return datetime.now().astimezone()


@dataclass
class Contexto:
    """O que o hook usa do mundo, injetável nos testes."""
    hostname: Callable[[], str] = socket.gethostname
    agora: Callable[[], datetime] = _agora_local
    fabrica_destino: Callable[..., Destino] = destino_da_config
    pasta_de_estado: Path | None = None
    """None: resolve por `pasta_de_estado(ambiente)`."""
    ambiente: Mapping[str, str] = field(default_factory=lambda: dict(os.environ))
    """O ambiente dos processos filhos (ssh, backend) e de onde sai a senha de `auth_env`."""
    espera_da_trava: float = ESPERA_DA_TRAVA
    runner: Callable[..., ResultadoComando] = rodar_comando


@dataclass
class RespostaHook:
    mensagem: str | None = None
    """O `systemMessage`: caminhos, ações e avisos. Nunca valores."""
    log: list = field(default_factory=list)
    """Linhas para o stderr (o debug log do host)."""


def saida_do_hook(resposta: RespostaHook) -> str:
    """O stdout do hook: só o objeto JSON, em ASCII (o locale do host pode não ser UTF-8), ou nada."""
    return json.dumps({"systemMessage": resposta.mensagem}) if resposta.mensagem else ""


def _hashes(arquivos: Mapping[str, bytes]) -> dict[str, str]:
    return {caminho: hash_sha256(dados) for caminho, dados in arquivos.items()}


def _listar(itens) -> str:
    """`development: .env (criar), app/.env (trocar)` — ambiente, caminho e ação; nunca o corpo."""
    por_ambiente = {}
    for item in itens:
        por_ambiente.setdefault(item.ambiente, []).append(f"{item.caminho} ({item.acao})")
    return "; ".join(f"{amb}: {', '.join(itens)}" for amb, itens in por_ambiente.items())


def _algum_vigiado(raiz: Path, editados, config) -> bool:
    """Algum caminho editado é um arquivo da Varredura (casa `include`, não casa o exclude)?"""
    raiz_real = Path(os.path.realpath(raiz))
    exclusoes = (*EXCLUDE_PADRAO, *config["exclude"])
    for caminho in editados:
        real = Path(os.path.realpath(caminho.parent)) / caminho.name
        try:
            rel = real.relative_to(raiz_real).as_posix()
        except ValueError:
            continue
        if casa_padrao(rel, config["include"]) and not casa_padrao(rel, exclusoes):
            return True
    return False


def _raizes(gatilho: Gatilho) -> list[tuple[Path, list | None]]:
    """[(raiz, caminhos editados nela)]. Edição: a raiz de cada arquivo, que pode não ser a do `cwd`.
    Shell, Stop e SessionStart: a raiz do `cwd`, com Varredura completa (caminhos None)."""
    if gatilho.caminhos is None:
        raiz = raiz_do_repositorio(gatilho.cwd)
        return [(raiz, None)] if raiz else []
    grupos = {}
    for caminho in gatilho.caminhos:
        raiz = raiz_do_repositorio(caminho.parent)
        if raiz:
            grupos.setdefault(raiz, []).append(caminho)
    return list(grupos.items())


def _detalhe(erro: BaseException) -> str:
    """A mensagem de um erro esperado (que nunca carrega valor); de um inesperado, só o tipo."""
    if isinstance(erro, ErroEnvDocs):
        return str(erro)
    if isinstance(erro, OSError):
        return f"erro de E/S ({type(erro).__name__})"
    return f"erro inesperado ({type(erro).__name__})"


@dataclass
class Rodada:
    """O que uma rodada de sync fez. Nada aqui carrega valor de arquivo."""
    aplicadas: list = field(default_factory=list)
    pendentes: list = field(default_factory=list)
    falhou: Operacao | None = None
    erro: BaseException | None = None
    erro_do_destino: ErroEnvDocs | None = None
    avisos_remotos: list = field(default_factory=list)
    carimbados: list = field(default_factory=list)

    @property
    def mudou_estado(self) -> bool:
        return bool(self.aplicadas or self.carimbados)


def rodada(estado: Mapping, config: Mapping, raiz: Path, *, remotos, ctx: Contexto, quando: datetime,
           commit: str | None, montar_destino: Callable[[], Destino]) -> tuple[dict, Rodada]:
    """Uma rodada de sync: lê development (Varredura) e os `remotos` (ssh), planeja e aplica.

    Devolve (novo estado, Rodada). Quem chama grava o estado se `Rodada.mudou_estado`. Ambiente
    remoto que falhou ao ler fica fora de `atuais` (intocado, não vira ausente). O carimbo
    `remote_checked_at` só vai para o ambiente lido sem nenhuma operação pendente, para a falha de
    escrita ser tentada de novo no próximo gatilho e não só depois da janela.
    """
    atuais = {"development": _locais(raiz, config)}
    lidos, avisos = ler_remotos(config, remotos, ctx)
    atuais.update(lidos)
    mudancas = diferencas(estado, {ambiente: _hashes(arquivos) for ambiente, arquivos in atuais.items()})
    if not mudancas:
        return carimbar_remotos(estado, lidos, quando), Rodada(avisos_remotos=avisos, carimbados=list(lidos))
    sem_pendencia = [a for a in lidos if a not in {m.ambiente for m in mudancas}]
    try:
        destino = montar_destino()
    except ErroEnvDocs as erro:
        return (carimbar_remotos(estado, sem_pendencia, quando),
                Rodada(pendentes=mudancas, erro_do_destino=erro, avisos_remotos=avisos, carimbados=sem_pendencia))
    operacoes = planejar(estado, atuais, sincronizado_em=quando, commit=commit, ler_corpo=destino.ler_corpo)
    resultado = aplicar(estado, operacoes, destino, quando=quando)
    pendentes = operacoes[len(resultado.aplicadas):]
    prontos = [a for a in lidos if a not in {op.ambiente for op in pendentes}]
    return (carimbar_remotos(resultado.estado, prontos, quando),
            Rodada(resultado.aplicadas, pendentes, resultado.falhou, resultado.erro, None, avisos, prontos))


def _linhas_da_rodada(nome: str, r: Rodada) -> list[str]:
    linhas = [f"aviso — {nome}: {aviso}. O ambiente fica como estava; o próximo gatilho tenta de novo."
              for aviso in r.avisos_remotos]
    if r.erro_do_destino is not None:
        linhas.append(f"aviso — {nome}: {r.erro_do_destino}. Pendente: {_listar(r.pendentes)}. "
                      "O estado não mudou; o próximo gatilho tenta de novo.")
    if r.aplicadas:
        linhas.append(f"Página de ambientes atualizada ({nome}) — {_listar(r.aplicadas)}")
    if r.falhou is not None:
        linhas.append(f"aviso — {nome}: falhou em {r.falhou.ambiente} {r.falhou.caminho} ({_detalhe(r.erro)}). "
                      f"Pendente: {_listar(r.pendentes)}. O estado dessas operações não mudou; o próximo "
                      "gatilho tenta de novo.")
    return linhas


def sincronizar_repo(raiz: Path, gatilho: Gatilho, editados, ctx: Contexto) -> list[str]:
    """Uma raiz, um gatilho: as linhas do `systemMessage` (vazio = calado).

    Calado quando: sem config; fora do Checkout da verdade (worktree ou outra máquina); edição que
    não toca arquivo da Varredura; nada mudou e nenhum ambiente remoto está devido. O estado só é
    gravado com o que o destino aceitou e com o carimbo dos remotos lidos sem pendência.
    """
    caminho_config = raiz / NOME_DA_CONFIG
    if not caminho_config.is_file() or not checkout_da_verdade(raiz):
        return []
    try:
        config = carregar_config(caminho_config)
    except ErroDeConfig as erro:
        return [f"aviso — {raiz.name}: {NOME_DA_CONFIG} inválida ({len(erro.erros)} erro(s), o 1º: "
                f"{erro.erros[0]}); rode `env_docs_sync.py validate`. Nada foi sincronizado."]
    if not maquina_confere(config["environments"]["development"]["machine"], ctx.hostname()):
        return []
    if editados is not None and not _algum_vigiado(raiz, editados, config):
        return []
    pasta = ctx.pasta_de_estado or pasta_de_estado(ctx.ambiente)
    arquivo = arquivo_de_estado(raiz, pasta)
    estado = carregar_estado(arquivo)
    if (not remotos_devidos(config, estado, gatilho, ctx.agora())
            and not diferencas(estado, {"development": _hashes(_locais(raiz, config))})):
        return []

    with trava_do_repo(raiz, pasta, ctx.espera_da_trava):
        estado = carregar_estado(arquivo)  # outro processo pode ter sincronizado enquanto esperávamos
        quando = ctx.agora()
        novo, r = rodada(estado, config, raiz, remotos=remotos_devidos(config, estado, gatilho, quando), ctx=ctx,
                         quando=quando, commit=_commit(None, raiz),
                         montar_destino=lambda: ctx.fabrica_destino(config, raiz, ctx))
        if r.mudou_estado:
            gravar_estado(arquivo, novo)
    return _linhas_da_rodada(raiz.name, r)


def executar_hook(texto: str, ctx: Contexto | None = None) -> RespostaHook:
    """O hook inteiro, sem E/S de processo: payload em texto → resposta. Nunca levanta."""
    ctx = ctx or Contexto()
    try:
        payload = json.loads(texto)
    except (ValueError, RecursionError):
        return RespostaHook(log=["env-docs-sync: o stdin do hook não é JSON; ignorado"])
    gatilho = ler_gatilho(payload)
    if gatilho is None:
        return RespostaHook()
    linhas = []
    for raiz, editados in _raizes(gatilho):
        try:
            linhas += sincronizar_repo(raiz, gatilho, editados, ctx)
        except Exception as erro:  # hook de conveniência: avisa e sai 0; a mensagem não carrega valor
            linhas.append(f"aviso — {raiz.name}: {_detalhe(erro)}. O próximo gatilho tenta de novo.")
    return RespostaHook(mensagem="env-docs-sync: " + "\n".join(linhas) if linhas else None)


def status_dos_arquivos(atuais: Mapping[str, Mapping[str, bytes]], destino: Destino) -> list[tuple[str, str, str]]:
    """[(ambiente, caminho, situação)]: `ok` (hash do bloco relido = hash do arquivo), `diverge` ou
    `ausente` (o destino não tem o bloco). Só hashes: nenhum valor sai daqui."""
    linhas = []
    for ambiente in AMBIENTES:
        for caminho in sorted(atuais.get(ambiente, {})):
            corpo = destino.ler_corpo(ambiente, caminho)
            texto = conteudo_do_bloco(corpo) if corpo is not None else None
            if corpo is None:
                situacao = "ausente"
            elif texto is not None and hash_sha256(texto.encode("utf-8")) == hash_sha256(atuais[ambiente][caminho]):
                situacao = "ok"
            else:
                situacao = "diverge"
            linhas.append((ambiente, caminho, situacao))
    return linhas


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def _agora(texto):
    if texto is None:
        return datetime.now().astimezone()
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        raise ErroDeConfig([f"--now: data inválida {texto!r} (use ISO 8601)"]) from None


def _commit(texto, raiz):
    if texto is not None:
        commit_curto(texto)
        return texto
    try:
        saida = subprocess.run(["git", "-C", str(raiz), "rev-parse", "HEAD"], capture_output=True,
                               text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    sha = saida.stdout.strip()
    return sha if saida.returncode == 0 and _RE_COMMIT.fullmatch(sha) else None


def _contexto(args):
    raiz = Path(args.root)
    config = carregar_config(Path(args.config) if args.config else raiz / ".env-docs.json")
    return raiz, config


def _locais(raiz, config):
    return ler_arquivos(raiz, varredura(raiz, config["include"], config["exclude"]))


def _cmd_validate(args):
    _, config = _contexto(args)
    print(f"config ok: page_id={config['doc']['page_id']} · ambientes: {', '.join(config['environments'])}")
    return 0


def _cmd_scan(args):
    raiz, config = _contexto(args)
    caminhos = varredura(raiz, config["include"], config["exclude"])
    for caminho, dados in ler_arquivos(raiz, caminhos).items():
        print(f"development\t{caminho}\tsha256:{hash_sha256(dados)[:12]}")
    print(f"{len(caminhos)} arquivo(s) na Varredura de {raiz}")
    return 0


def _cmd_plan(args):
    raiz, config = _contexto(args)
    estado = carregar_estado(args.state)
    hashes = {"development": {c: hash_sha256(d) for c, d in _locais(raiz, config).items()}}
    mudancas = diferencas(estado, hashes)
    for m in mudancas:
        print(m.resumo())
    print(f"{len(mudancas)} mudança(s)" if mudancas else "nada a sincronizar")
    return 0


def _cmd_sync(args):
    raiz, config = _contexto(args)
    quando, commit = _agora(args.now), _commit(args.commit, raiz)
    estado = carregar_estado(args.state)
    remotos = _remotos(config) if args.remote else []
    if remotos == [] and _remotos(config):
        print(f"ambientes remotos fora desta rodada: {', '.join(_remotos(config))} (use --remote)")
    novo, r = rodada(estado, config, raiz, remotos=remotos, ctx=Contexto(), quando=quando, commit=commit,
                     montar_destino=lambda: _destino_da_cli(args, config, raiz))
    for aviso in r.avisos_remotos:
        print(f"env-docs-sync: aviso — {aviso}; o ambiente fica como estava", file=sys.stderr)
    for op in r.aplicadas:
        print(f"aplicado: {op.resumo()}")
    if r.mudou_estado:
        gravar_estado(args.state, novo)
    if r.erro_do_destino is not None:
        raise r.erro_do_destino
    if r.falhou is not None:
        print(f"env-docs-sync: falhou em {r.falhou.resumo()}: {_detalhe(r.erro)}", file=sys.stderr)
        return 1
    if not r.aplicadas:
        print("nada a sincronizar")
    return 1 if r.avisos_remotos else 0


def _destino_da_cli(args, config, raiz):
    """`--to-dir` (destino de diretório, para teste) ou o Destino de `doc.backend`."""
    if args.to_dir:
        return DestinoDiretorio(args.to_dir)
    return destino_da_config(config, raiz, Contexto())


def _cmd_status(args):
    raiz, config = _contexto(args)
    destino = _destino_da_cli(args, config, raiz)
    atuais, avisos = {"development": _locais(raiz, config)}, []
    if args.remote:
        lidos, avisos = ler_remotos(config, _remotos(config), Contexto())
        atuais.update(lidos)
    linhas = status_dos_arquivos(atuais, destino)
    for ambiente, caminho, situacao in linhas:
        print(f"{situacao}\t{ambiente}\t{caminho}")
    contagem = {s: sum(1 for *_, x in linhas if x == s) for s in ("ok", "diverge", "ausente")}
    print(f"{contagem['ok']} ok, {contagem['diverge']} diverge, {contagem['ausente']} ausente")
    for aviso in avisos:
        print(f"env-docs-sync: aviso — {aviso}; o ambiente não foi conferido", file=sys.stderr)
    if contagem["ok"] != len(linhas):
        return 3
    return 1 if avisos else 0


def _cmd_hook(args):
    """Sempre sai 0: um hook de conveniência nunca derruba nem prende a sessão (Stop + exit 2 = loop)."""
    try:
        texto = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        resposta = executar_hook(texto)
        saida = saida_do_hook(resposta)
        if saida:
            print(saida)
        for linha in resposta.log:
            print(linha, file=sys.stderr)
    except Exception as erro:  # nem a E/S do processo derruba o hook; só o tipo, nunca a mensagem
        print(f"env-docs-sync: erro inesperado no hook ({type(erro).__name__})", file=sys.stderr)
    return 0


def _cmd_render_page(args):
    raiz, config = _contexto(args)
    quando, commit = _agora(args.now), _commit(args.commit, raiz)
    locais = _locais(raiz, config)
    blocos = {"development": {}}
    for caminho, dados in locais.items():
        try:
            blocos["development"][caminho] = bloco_de_arquivo(dados, sincronizado_em=quando, commit=commit)
        except ErroEnvDocs as erro:
            raise ErroEnvDocs(f"development {caminho}: {erro}") from None
    _gravar_privado(args.out, pagina_de_ambientes(config, blocos))
    com_blocos = sum(1 for b in blocos.values() if b)
    print(f"página gravada em {args.out}: {com_blocos} ambiente(s) com blocos, {len(locais)} bloco(s)")
    return 0


def _parser():
    parser = argparse.ArgumentParser(
        prog="env_docs_sync.py",
        description="env-docs-sync: Varredura, plano, sync, status e a entrada do hook. Nunca imprime valores.")
    parser.add_argument("--version", action="version", version=f"env-docs-sync {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    def comando(nome, ajuda, funcao, estado=False, relogio=False):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("--root", default=".", help="raiz do repositório (padrão: .)")
        p.add_argument("--config", help="padrão: <root>/.env-docs.json")
        if estado:
            p.add_argument("--state", required=True, help="arquivo de estado (só hashes; gravado 0600)")
        if relogio:
            p.add_argument("--now", help="relógio injetado, ISO 8601 (padrão: agora)")
            p.add_argument("--commit", help="sha do Checkout da verdade (padrão: git rev-parse HEAD)")
        p.set_defaults(funcao=funcao)
        return p

    comando("validate", "valida a .env-docs.json", _cmd_validate)
    comando("scan", "Varredura: caminhos e hash curto", _cmd_scan)
    comando("plan", "mudanças desde o último sync (só caminhos e hashes)", _cmd_plan, estado=True)
    sync = comando("sync", "aplica o plano de development no destino", _cmd_sync,
                   estado=True, relogio=True)
    sync.add_argument("--to-dir", help="destino de diretório, para teste (padrão: o de doc.backend)")
    sync.add_argument("--remote", action="store_true",
                      help="também lê por ssh os ambientes remotos (Sync remoto), sem olhar a janela")
    status = comando("status", "hash do bloco relido no destino x hash do arquivo (rc 3 se algo diverge)",
                     _cmd_status)
    status.add_argument("--to-dir", help="destino de diretório, para teste (padrão: o de doc.backend)")
    status.add_argument("--remote", action="store_true", help="também confere os ambientes remotos (ssh)")
    hook = sub.add_parser("hook", help="entrada do hook do Claude Code e do Codex CLI (payload no stdin; sai 0)")
    hook.set_defaults(funcao=_cmd_hook)
    render = comando("render-page", "grava a Página de ambientes inteira (0600) para o replace",
                     _cmd_render_page, relogio=True)
    render.add_argument("--out", required=True, help="arquivo HTML de saída (0600)")
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.funcao(args)
    except ErroDeConfig as erro:
        for linha in erro.erros:
            print(f"env-docs-sync: {linha}", file=sys.stderr)
        return 2
    except ErroEnvDocs as erro:
        print(f"env-docs-sync: {erro}", file=sys.stderr)
        return 1
    except OSError as erro:
        print(f"env-docs-sync: erro de E/S ({type(erro).__name__}) em {erro.filename}", file=sys.stderr)
        return 1
    except Exception as erro:  # mensagem genérica: a de uma exceção inesperada pode carregar dados
        print(f"env-docs-sync: erro inesperado ({type(erro).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
