#!/usr/bin/env python3
"""env-docs-sync: mantém os arquivos .env* de um repositório espelhados numa Página de ambientes.

Este arquivo tem cinco camadas, nesta ordem:

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
4. **Instalação no Codex.** A chave, o hash da declaração e a impressão do pacote que o Codex confere,
   e a edição cirúrgica do `config.toml` que grava o trust.
5. **CLI** (`init`, `validate`, `scan`, `plan`, `sync`, `status`, `migrate`, `install`, `render-page`,
   `hook`).

Regra de segredo, em todas as camadas: nenhum valor de arquivo .env* vai para stdout, stderr,
mensagem de erro, `repr` ou estado. O valor só vai para o corpo do Bloco de arquivo, que é o destino.
Só biblioteca padrão; Python 3.11+.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import difflib
import fcntl
import functools
import hashlib
import html
import json
import os
import re
import socket
import stat
import string
import subprocess
import sys
import tempfile
import time
import tomllib
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
_CAMPOS_TOPO = ("doc", "values", "include", "exclude", "environments", "run", "ci")
_CAMPOS_CI = ("workflows", "secrets")


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
    tem_gh = isinstance(dados, dict) and isinstance(dados.get("ci"), dict) and dados["ci"].get("secrets") == "gh"
    obrigatorias = _CAMPOS_TOPO + (("remote_check_every",) if tem_ssh or tem_gh else ())
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

    ci = dados.get("ci")
    if ci is not None and c.objeto(ci, "config.ci", _CAMPOS_CI):
        pasta = ci.get("workflows")
        if "workflows" in ci and pasta is not None and (
                not isinstance(pasta, str) or not pasta.strip() or not caminho_relativo_valido(pasta)):
            c.erro("config.ci.workflows", "precisa ser null ou uma pasta relativa à raiz, com /, sem ..")
        if "secrets" in ci and ci["secrets"] not in (None, "gh"):
            c.erro("config.ci.secrets", "precisa ser null ou \"gh\" (os nomes pelo GitHub CLI)")

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


INCLUDE_INICIAL = ("**/.env", "**/.env.*")
WORKFLOWS_DO_GITHUB = ".github/workflows"


def config_inicial(raiz, hostname: str) -> dict:
    """A `.env-docs.json` do `init`: development pela Varredura e pelo hostname; o que só a pessoa sabe
    (destino, página, papéis, servidor e domínio) fica null, e o `validate` lista cada um. Com
    `.github/workflows`, liga a seção CI/CD com os nomes pelo `gh`, e com ela a janela de 24 h."""
    pastas = sorted({str(Path(c).parent) for c in varredura(raiz, list(INCLUDE_INICIAL), [])})
    onde = ", ".join("raiz" if pasta == "." else pasta for pasta in pastas)
    github = (Path(raiz) / WORKFLOWS_DO_GITHUB).is_dir()
    return {
        "doc": {"backend": "kb", "cli": None, "python": None, "target": None, "page_id": None, "allowed_roles": None},
        "values": "full",
        **({"remote_check_every": "24h"} if github else {}),
        "include": list(INCLUDE_INICIAL),
        "exclude": [],
        "environments": {"development": {
            "source": "local", "machine": hostname, "server": None, "domain": None,
            "where": f"checkout principal: {onde}" if onde else "checkout principal",
            "source_of_truth": f"checkout principal em {hostname}",
        }},
        "ci": {"workflows": WORKFLOWS_DO_GITHUB, "secrets": "gh"} if github else None,
        "run": [],
    }


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

    obrigatorias = {"version", "environments", "remote_checked_at"}
    if not isinstance(estado, dict) or not obrigatorias <= set(estado) <= obrigatorias | {"derived"}:
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
    if "derived" in estado:
        derivadas = estado["derived"]
        if (not isinstance(derivadas, dict) or set(derivadas) != {"inputs_sha256", "sha256", "checked_at"}
                or not all(isinstance(derivadas[k], str) and _RE_HEX64.fullmatch(derivadas[k])
                           for k in ("inputs_sha256", "sha256"))
                or not _e_carimbo(derivadas["checked_at"])):
            falha("derived")


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

    def escrever(self, op: Operacao) -> bool | None:
        """Escreve, ou levanta. `False` diz "o destino já tinha isto, nada foi escrito"."""


@dataclass
class ResultadoSync:
    estado: dict
    aplicadas: list
    """As operações aceitas pelo destino, escritas ou não; todas entram no estado."""
    falhou: Operacao | None = None
    erro: BaseException | None = None
    sem_escrita: list = field(default_factory=list)
    """As aceitas que o destino não precisou escrever (já tinha o conteúdo)."""


def aplicar(estado: Mapping, operacoes, destino: Destino, *, quando: datetime,
            ao_aceitar: Callable[[dict], None] | None = None) -> ResultadoSync:
    """Escreve cada operação no destino, em ordem, e registra só as que o destino aceitou.

    Para na primeira falha: o estado devolvido não tem a operação que falhou nem as seguintes,
    e o próximo gatilho tenta de novo. `ao_aceitar(estado parcial)` roda depois de cada operação
    aceita: o hook grava ali, para um timeout do host no meio da rodada não perder o que já foi.
    """
    atual, aplicadas, sem_escrita = dict(estado), [], []
    for op in operacoes:
        try:
            escreveu = destino.escrever(op)
        except Exception as erro:  # o adaptador decide o tipo; quem chama relata sem valores
            return ResultadoSync(atual, aplicadas, op, erro, sem_escrita)
        atual = registrar_operacao(atual, op, quando=quando)
        aplicadas.append(op)
        if escreveu is False:
            sem_escrita.append(op)
        if ao_aceitar is not None:
            ao_aceitar(atual)
    return ResultadoSync(atual, aplicadas, sem_escrita=sem_escrita)


# ---------------------------------------------------------------------------------------------
# CI/CD: os workflows do repositório, lidos sem PyYAML
# ---------------------------------------------------------------------------------------------
# O leitor entende só o que a seção mostra: o `name` do topo e, em cada job de `jobs`, o `runs-on`
# e o `environment`. Ele anda por indentação e olha apenas a chave no nível dos filhos diretos do
# job, então um `runs-on:` dentro de um passo, de um script ou de `on:` não conta. Forma que ele não
# entende vira `?`, nunca um palpite.

@dataclass(frozen=True)
class JobDoCi:
    id: str
    runs_on: str | None
    """`a, b` para lista; o texto como está para escalar ou expressão; `?` para forma não lida;
    None para job sem `runs-on` (workflow reusável)."""
    environment: str | None


@dataclass(frozen=True)
class WorkflowDoCi:
    arquivo: str
    nome: str
    jobs: tuple


_RE_CHAVE_YAML = re.compile(r"""([A-Za-z0-9_.-]+|"[^"]*"|'[^']*')\s*:(?:\s+(.*))?$""")
_RE_COMENTARIO_YAML = re.compile(r"\s#")


def _linhas_yaml(texto: str) -> list[tuple[int, str]]:
    """(indentação, conteúdo) de cada linha que não é vazia nem só comentário."""
    linhas = []
    for bruta in texto.splitlines():
        conteudo = bruta.lstrip(" ")
        if conteudo.strip() and not conteudo.startswith("#"):
            linhas.append((len(bruta) - len(conteudo), conteudo.rstrip()))
    return linhas


def _chave_yaml(conteudo: str) -> tuple[str | None, str]:
    casou = _RE_CHAVE_YAML.match(conteudo)
    if not casou:
        return None, ""
    return casou.group(1).strip("\"'"), casou.group(2) or ""


def _escalar(valor: str) -> str:
    """O escalar sem aspas e sem o comentário do fim (` #` fora de aspas)."""
    valor = valor.strip()
    if valor[:1] in ("'", '"'):
        fim = valor.find(valor[0], 1)
        if fim > 0:
            return valor[1:fim]
    casou = _RE_COMENTARIO_YAML.search(valor)
    return (valor[:casou.start()] if casou else valor).strip()


def _filhos(linhas, i) -> list[int]:
    """Os índices dos filhos diretos da linha `i`: as linhas mais indentadas logo abaixo dela, no
    nível do primeiro filho."""
    fim = i + 1
    while fim < len(linhas) and linhas[fim][0] > linhas[i][0]:
        fim += 1
    if fim == i + 1:
        return []
    nivel = linhas[i + 1][0]
    return [j for j in range(i + 1, fim) if linhas[j][0] == nivel]


def _lista(linhas, k) -> list[str] | None:
    """Os itens de uma lista de bloco sob a chave da linha `k` (mais indentada ou no mesmo nível)."""
    filhos = _filhos(linhas, k)
    if not filhos:
        filhos = []
        for j in range(k + 1, len(linhas)):
            if linhas[j][0] != linhas[k][0] or not linhas[j][1].startswith("- "):
                break
            filhos.append(j)
    itens = [linhas[j][1] for j in filhos]
    if not itens or not all(item.startswith("- ") for item in itens):
        return None
    return [_escalar(item[2:]) for item in itens]


def _valor_runs_on(linhas, k, valor: str) -> str:
    valor = _escalar(valor)
    if valor.startswith("{"):
        return "?"
    if valor.startswith("["):
        if not valor.endswith("]"):
            return "?"
        return ", ".join(_escalar(item) for item in valor[1:-1].split(",") if item.strip())
    if valor:
        return valor
    itens = _lista(linhas, k)
    return ", ".join(itens) if itens else "?"


def _valor_environment(linhas, k, valor: str) -> str:
    valor = _escalar(valor)
    if valor:
        return valor
    for j in _filhos(linhas, k):
        chave, resto = _chave_yaml(linhas[j][1])
        if chave == "name" and _escalar(resto):
            return _escalar(resto)
    return "?"


def _ler_job(linhas, j, job_id: str) -> JobDoCi:
    runs_on = environment = None
    for k in _filhos(linhas, j):
        chave, valor = _chave_yaml(linhas[k][1])
        if chave == "runs-on":
            runs_on = _valor_runs_on(linhas, k, valor)
        elif chave == "environment":
            environment = _valor_environment(linhas, k, valor)
    return JobDoCi(job_id, runs_on, environment)


def ler_workflow(texto: str, arquivo: str) -> WorkflowDoCi:
    """O nome do workflow (o `arquivo`, sem `name`) e os jobs, na ordem do arquivo."""
    linhas, nome, jobs = _linhas_yaml(texto), arquivo, []
    for i, (indentacao, conteudo) in enumerate(linhas):
        if indentacao:
            continue
        chave, valor = _chave_yaml(conteudo)
        if chave == "name" and _escalar(valor):
            nome = _escalar(valor)
        elif chave == "jobs" and not _escalar(valor):
            for j in _filhos(linhas, i):
                job_id, _ = _chave_yaml(linhas[j][1])
                if job_id is not None:
                    jobs.append(_ler_job(linhas, j, job_id))
    return WorkflowDoCi(arquivo, nome, tuple(jobs))


def workflows_do_repo(raiz, pasta: str) -> list[WorkflowDoCi]:
    """Os `*.yml` e `*.yaml` do topo de `pasta` (o GitHub não lê subpastas), em ordem de nome."""
    base = Path(raiz) / pasta
    if not base.is_dir():
        return []
    rel = Path(pasta).as_posix().rstrip("/")
    return [ler_workflow(p.read_text(encoding="utf-8", errors="replace"), f"{rel}/{p.name}")
            for p in sorted(base.iterdir()) if p.suffix in (".yml", ".yaml") and p.is_file()]


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


def _tabela(cabecalho, linhas) -> str:
    """Tabela com as células já em html (quem chama escapa)."""
    return ("<table>\n<thead><tr>" + "".join(f"<th>{c}</th>" for c in cabecalho) + "</tr></thead>\n<tbody>\n"
            + "\n".join("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas)
            + "\n</tbody>\n</table>")


def _codigos(nomes) -> str:
    return ", ".join(f"<code>{_esc(n)}</code>" for n in nomes) or "—"


def secao_ci_cd(ci: Mapping | None, workflows, nomes) -> str:
    """A seção CI/CD: um job por linha (workflow, arquivo, job, runs-on, environment) e os nomes dos
    segredos e variáveis por escopo. `workflows` e `nomes` já lidos; aqui não há E/S."""
    if ci is None:
        return "<p>Sem CI/CD declarado (<code>ci: null</code> na <code>.env-docs.json</code>).</p>"
    partes = ["<h3>Workflows</h3>"]
    if ci["workflows"] is None:
        partes.append("<p>Workflows não declarados (<code>ci.workflows: null</code>).</p>")
    elif not workflows:
        partes.append(f"<p>Nenhum workflow em <code>{_esc(ci['workflows'])}</code>.</p>")
    else:
        partes.append(_tabela(("Workflow", "Arquivo", "Job", "runs-on", "Environment"), [
            (_esc(wf.nome), f"<code>{_esc(wf.arquivo)}</code>", _esc(job.id), _esc(job.runs_on or "—"),
             _esc(job.environment or "—"))
            for wf in workflows for job in wf.jobs]))
    partes.append("<h3>Segredos e variáveis (só nomes)</h3>")
    if ci["secrets"] is None:
        partes.append("<p>Nomes não consultados (<code>ci.secrets: null</code>).</p>")
    elif nomes is None:
        raise ErroEnvDocs("ci.secrets declarado, mas os nomes não foram lidos")
    else:
        partes.append(_tabela(("Escopo", "Segredos", "Variáveis"), [
            (_esc(n.escopo), _codigos(n.segredos), _codigos(n.variaveis)) for n in nomes]))
    return "\n".join(partes)


def carregar_template(caminho=TEMPLATE_PADRAO) -> str:
    return Path(caminho).read_text(encoding="utf-8")


def pagina_de_ambientes(config: Mapping, blocos: Mapping[str, Mapping[str, str]], *, ci_cd: str,
                        template: str | None = None, secoes: str | None = None) -> str:
    """A Página de ambientes inteira, do template, para o `replace`. `blocos`: {ambiente: {caminho: corpo}};
    `ci_cd`: a seção já renderizada (`ci_cd_do_repo`), porque ela sai do disco e do gh. `secoes`, quando
    vem, entra no lugar das Seções de ambiente como está (as da página atual, ao refazer só as derivadas)."""
    configurados = config["environments"]
    sobra = sorted(set(blocos) - set(configurados))
    if sobra:
        raise ErroEnvDocs(f"blocos de ambiente não configurado: {', '.join(sobra)}")
    modelo = string.Template(carregar_template() if template is None else template)
    faltam = PLACEHOLDERS - set(modelo.get_identifiers())  # get_identifiers/is_valid: Python 3.11+
    if faltam or not modelo.is_valid():
        raise ErroEnvDocs(f"template inválido; placeholders ausentes: {', '.join(sorted(faltam)) or '-'}")
    if secoes is None:
        secoes = "\n".join(secao_de_ambiente(a, blocos.get(a, {})) for a in AMBIENTES if a in configurados)
    else:
        secoes = secoes.rstrip()  # o template já põe a quebra antes da CI/CD; sem isto, cada volta soma uma
    try:
        return modelo.substitute(
            allowed_roles=_esc(", ".join(config["doc"]["allowed_roles"])),
            environments_table=tabela_de_ambientes(config),
            environment_sections=secoes,
            ci_cd=ci_cd,
            run=secao_como_rodar(config),
        )
    except (KeyError, ValueError) as erro:
        raise ErroEnvDocs(f"template inválido: placeholder desconhecido {erro}") from None


# ---------------------------------------------------------------------------------------------
# Seções derivadas: o que na página não é Bloco de arquivo
# ---------------------------------------------------------------------------------------------
# A intro com os papéis, a tabela de Ambientes, a CI/CD e o Como rodar saem da config, dos workflows
# e dos nomes do gh. O `section-set` só troca o corpo de um h3, então elas são refeitas por `replace`
# da página inteira, levando as Seções de ambiente da página atual como estão.

_RE_H2 = re.compile(r"<h2\b[^>]*>(.*?)</h2\s*>", re.S | re.I)
_RE_ID_BKMRK = re.compile(r'\s+id="bkmrk-[^"]*"')


def partes_da_pagina(pagina: str) -> tuple[str, str, str]:
    """(antes das Seções de ambiente, as Seções de ambiente, a partir do h2 CI/CD). A página precisa ter
    os h2 Ambientes, CI/CD e Como rodar, um de cada, nessa ordem; senão é ErroEnvDocs."""
    h2 = [(casou.start(), _texto_de_heading(casou.group(1))) for casou in _RE_H2.finditer(pagina)]
    fixos = {nome: [ini for ini, texto in h2 if texto == nome] for nome in ("Ambientes", "CI/CD", "Como rodar")}
    if any(len(v) != 1 for v in fixos.values()) or not (
            fixos["Ambientes"][0] < fixos["CI/CD"][0] < fixos["Como rodar"][0]):
        raise ErroEnvDocs("a página não segue o template (h2 Ambientes, CI/CD e Como rodar, um de cada); "
                          "rode `migrate`")
    fim = fixos["CI/CD"][0]
    secoes = [ini for ini, texto in h2 if texto in {f"[{a}]" for a in AMBIENTES} and fixos["Ambientes"][0] < ini < fim]
    ini = secoes[0] if secoes else fim
    return pagina[:ini], pagina[ini:fim], pagina[fim:]


def _normalizado(fragmento: str) -> str:
    """Sem os ids `bkmrk-` que o BookStack põe, com as entidades resolvidas e sem espaço entre tags."""
    return re.sub(r">\s+<", "><", html.unescape(_RE_ID_BKMRK.sub("", fragmento))).strip()


def derivadas_conferem(atual: str, nova: str) -> bool:
    """As seções derivadas de `atual` (relida do destino) são as de `nova`? As Seções de ambiente não
    contam. Página fora do template não confere."""
    try:
        antes_a, _, depois_a = partes_da_pagina(atual)
    except ErroEnvDocs:
        return False
    antes_n, _, depois_n = partes_da_pagina(nova)
    return (_normalizado(antes_a) == _normalizado(antes_n)) and (_normalizado(depois_a) == _normalizado(depois_n))


def pagina_das_derivadas(config: Mapping, ci_cd: str) -> str:
    """A página só com as derivadas (Seções de ambiente vazias): o que o estado guarda por hash."""
    return pagina_de_ambientes(config, {}, ci_cd=ci_cd, secoes="")


def entradas_derivadas(raiz, config: Mapping) -> str:
    """sha256 do que as derivadas leem do disco: versão, template, config e os workflows de
    `ci.workflows`. Barato (sem gh): é o que o hook compara a cada gatilho."""
    soma = hashlib.sha256()

    def parte(rotulo: str, dados: bytes):
        soma.update(f"{rotulo}\0{len(dados)}\0".encode("utf-8") + dados)

    parte("versão", __version__.encode("utf-8"))
    parte("template", carregar_template().encode("utf-8"))
    parte("config", json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    ci = config["ci"]
    if ci is not None and ci["workflows"] is not None:
        base = Path(raiz) / ci["workflows"]
        if base.is_dir():
            for arquivo in sorted(base.iterdir()):
                if arquivo.suffix in (".yml", ".yaml") and arquivo.is_file():
                    parte(f"workflow {arquivo.name}", arquivo.read_bytes())
    return soma.hexdigest()


def derivadas_devidas(config: Mapping, estado: Mapping, entradas: str, agora: datetime, *,
                      olhar_janela: bool) -> bool:
    """Refazer as derivadas neste gatilho? Sim se o estado não as tem ou se as entradas do disco mudaram.
    Com `olhar_janela` (a SessionStart) e `ci.secrets: "gh"`, também quando a última consulta ao gh
    passou de `remote_check_every`: os nomes mudam fora do repositório."""
    anterior = estado.get("derived")
    if not anterior or anterior["inputs_sha256"] != entradas:
        return True
    ci = config["ci"]
    if olhar_janela and ci is not None and ci["secrets"] == "gh":
        return _vencido(anterior["checked_at"], intervalo_em_segundos(config["remote_check_every"]), agora)
    return False


@dataclass(frozen=True)
class PedidoDeDerivadas:
    entradas: str
    ler_ci_cd: Callable[[], str]
    """Lê os workflows e o gh só quando a rodada chega às derivadas."""


def aplicar_derivadas(estado: Mapping, config: Mapping, destino: "Destino", pedido: PedidoDeDerivadas,
                      quando: datetime) -> tuple[dict, str | None, str | None]:
    """(novo estado, "escrita" | "já no destino" | None, aviso | None). Hash igual ao do estado: nem
    chama o destino. Falha (gh, trava, página fora do template): aviso, e o estado delas não muda."""
    try:
        ci_cd = pedido.ler_ci_cd()
        sha = hash_sha256(pagina_das_derivadas(config, ci_cd).encode("utf-8"))
        anterior = estado.get("derived") or {}
        escreveu = anterior.get("sha256") != sha and destino.escrever_derivadas(config, ci_cd) is not False
    except Exception as erro:  # o adaptador decide o tipo; o aviso não carrega valor
        return dict(estado), None, _detalhe(erro)
    novo = copy.deepcopy(dict(estado))
    novo["derived"] = {"inputs_sha256": pedido.entradas, "sha256": sha, "checked_at": _carimbo(quando)}
    return novo, ("escrita" if escreveu else "já no destino"), None


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

    def ler_derivadas(self) -> str | None:
        arquivo = self.pasta / "derivadas.html"
        return arquivo.read_text(encoding="utf-8") if arquivo.is_file() else None

    def conferir_derivadas(self, config, ci_cd) -> bool | None:
        atual = self.ler_derivadas()
        return None if atual is None else atual == pagina_das_derivadas(config, ci_cd)

    def escrever_derivadas(self, config, ci_cd) -> bool:
        nova = pagina_das_derivadas(config, ci_cd)
        if self.ler_derivadas() == nova:
            return False
        _gravar_privado(self.pasta / "derivadas.html", nova)
        return True


# ---------------------------------------------------------------------------------------------
# Adaptador kb: a CLI de um BookStack, por subprocesso, com a trava de permissão
# ---------------------------------------------------------------------------------------------

KB_TIMEOUT = 90
"""Segundos para cada chamada da CLI kb (ela mesma repete 429/5xx e espera a persistência)."""
LIMITE_CHANGELOG = 180
"""O `changelog` de uma revisão do BookStack aceita até 180 caracteres (registro da API, v26.09)."""
_RE_HEADING_HTML = re.compile(r"<h([1-6])\b([^>]*)>(.*?)</h\1\s*>", re.S | re.I)


class ErroDePermissao(ErroEnvDocs):
    """A página é visível além de `doc.allowed_roles`: nada se escreve (o destino precisa ser menos
    exposto que a origem)."""


def permissao_restrita(dados, permitidos) -> list[str]:
    """[] quando só papéis de `permitidos` veem a página; senão, os motivos (nomes de papel, sem valor).

    Falha fechado: herdar do livro (`inheriting` diferente de false) não prova restrição; o fallback
    precisa ter `view` false; e todo papel em `role_permissions` com `view` diferente de false
    precisa estar em `permitidos`, comparado pelo `role.display_name`.
    """
    motivos = []
    if not isinstance(dados, Mapping):
        return ["a resposta de permissões não é um objeto"]
    fallback, papeis = dados.get("fallback_permissions"), dados.get("role_permissions")
    if not isinstance(fallback, Mapping):
        motivos.append("a resposta não traz fallback_permissions")
    elif fallback.get("inheriting") is not False:
        motivos.append("a página herda as permissões (inheriting): a restrição não está provada")
    elif fallback.get("view") is not False:
        motivos.append("o fallback (todos os outros papéis) tem view")
    if not isinstance(papeis, list):
        motivos.append("a resposta não traz role_permissions")
        return motivos
    extras = set()
    for item in papeis:
        if not isinstance(item, Mapping):
            extras.add("item ilegível")
            continue
        if item.get("view") is False:
            continue
        papel = item.get("role") if isinstance(item.get("role"), Mapping) else {}
        nome = papel.get("display_name")
        if nome not in permitidos:
            extras.add(nome if isinstance(nome, str) else f"role_id {item.get('role_id')}")
    if extras:
        motivos.append("papéis fora de doc.allowed_roles com view: " + ", ".join(sorted(extras)))
    return motivos


def _texto_de_heading(fragmento: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragmento))).strip()


def corpo_da_secao(pagina: str, sob: str, titulo: str) -> str | None:
    """O corpo do h3 `titulo` dentro do h2 `sob`: do fim do `<h3>` até o próximo heading de nível ≤ 3.

    O casamento é pelo texto exato do heading (sem tags, entidades resolvidas, espaços colapsados),
    a mesma regra do `section-set` do kb. None se o h2 ou o h3 não existem; repetido é erro.
    """
    heads = [(m.start(), m.end(), int(m.group(1)), _texto_de_heading(m.group(3)))
             for m in _RE_HEADING_HTML.finditer(pagina or "")]
    h2s = [h for h in heads if h[2] == 2 and h[3] == sob]
    if not h2s:
        return None
    if len(h2s) > 1:
        raise ErroEnvDocs(f"a página tem {len(h2s)} h2 {sob!r}")
    fim_h2 = next((h[0] for h in heads if h[0] > h2s[0][0] and h[2] <= 2), len(pagina))
    h3s = [h for h in heads if h[2] == 3 and h2s[0][1] <= h[0] < fim_h2 and h[3] == titulo]
    if not h3s:
        return None
    if len(h3s) > 1:
        raise ErroEnvDocs(f"a página tem {len(h3s)} h3 {titulo!r} sob {sob!r}")
    fim = next((h[0] for h in heads if h[0] > h3s[0][0] and h[2] <= 3), len(pagina))
    return pagina[h3s[0][1]:fim]


def bloco_confere(op: Operacao, corpo: str | None) -> bool:
    """O bloco relido é o que a operação mandou? Pelo hash do conteúdo do `<pre>`; no `marcar_ausente`,
    pelo callout e pelo conteúdo antigo mantido."""
    if corpo is None:
        return False
    texto = conteudo_do_bloco(corpo)
    if op.acao == "marcar_ausente":
        return "ausente desde" in corpo and texto == conteudo_do_bloco(op.corpo)
    return texto is not None and hash_sha256(texto.encode("utf-8")) == op.sha256


def _expandir(caminho: str, ambiente: Mapping[str, str]) -> str:
    if caminho == "~" or caminho.startswith("~/"):
        return (ambiente.get("HOME") or str(Path.home())) + caminho[1:]
    return caminho


def _erro_do_kb(resultado: ResultadoComando) -> str:
    """O erro da CLI kb (`{"error": {code, message, backup?}}` no stderr), sem ecoar outra coisa."""
    try:
        erro = json.loads(resultado.stderr.decode("utf-8"))["error"]
        code, mensagem, backup = erro.get("code"), str(erro.get("message", ""))[:240], erro.get("backup")
    except (UnicodeDecodeError, ValueError, KeyError, TypeError, AttributeError):
        return f"rc {resultado.returncode}, sem o JSON de erro do kb no stderr"
    texto = f"rc {resultado.returncode}, {code}: {mensagem}"
    if backup:
        texto += f"; a escrita pode ter ocorrido (backup do kb: {backup})"
    return texto


class DestinoKb:
    """O Destino `kb`: `kb page section-set` para cada Bloco de arquivo, com o corpo pelo stdin.

    Antes da primeira escrita, confere as permissões da página (`permissao_restrita`); depois de cada
    escrita, relê a página e confere o bloco (`bloco_confere`). Só então o estado pode ser gravado.
    A CLI e o python vêm de `doc.cli` e `doc.python` (com `~`), o alvo de `doc.target`.
    """

    def __init__(self, config: Mapping, ctx: "Contexto", *, commit: str | None = None):
        doc = config["doc"]
        self.page_id, self.target = str(doc["page_id"]), doc["target"]
        self.permitidos = frozenset(doc["allowed_roles"])
        self.base = [_expandir(doc["python"], ctx.ambiente), _expandir(doc["cli"], ctx.ambiente)]
        self.ctx, self.commit = ctx, commit
        self._permissao_conferida = False
        self._html_fixo = None

    def _kb(self, *args, entrada: bytes | None = None, aceitos=(0,)):
        resultado = self.ctx.runner([*self.base, *args, "--target", self.target], env=self.ctx.ambiente,
                                    timeout=KB_TIMEOUT, entrada=entrada)
        if resultado.returncode not in aceitos:
            raise ErroEnvDocs(f"kb {args[0]} {args[1]}: {_erro_do_kb(resultado)}")
        try:
            return resultado.returncode, json.loads(resultado.stdout.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ErroEnvDocs(f"kb {args[0]} {args[1]}: a saída não é JSON (rc {resultado.returncode})") from None

    def conferir_permissao(self) -> None:
        if self._permissao_conferida:
            return
        _, dados = self._kb("content-permissions", "read", "page", self.page_id)
        motivos = permissao_restrita(dados, self.permitidos)
        if motivos:
            raise ErroDePermissao(f"a página {self.page_id} é visível além de doc.allowed_roles "
                                  f"({'; '.join(motivos)}); nada foi escrito")
        self._permissao_conferida = True

    def _html(self) -> str:
        if self._html_fixo is not None:
            return self._html_fixo
        _, pagina = self._kb("pages", "read", self.page_id)
        if not isinstance(pagina, dict) or not isinstance(pagina.get("raw_html", pagina.get("html")), str):
            raise ErroEnvDocs(f"kb pages read {self.page_id}: a página veio sem html")
        return pagina.get("raw_html") or pagina.get("html") or ""

    def fixar_leitura(self) -> None:
        """Lê a página uma vez e serve o `ler_corpo` dessa cópia (o `status`, que só lê)."""
        self._html_fixo = None
        self._html_fixo = self._html()

    def ler_corpo(self, ambiente, caminho):
        return corpo_da_secao(self._html(), f"[{ambiente}]", caminho)

    def _changelog(self, op: Operacao) -> str:
        if op.acao == "marcar_ausente":
            marca = "ausente"
        elif op.ambiente == "development" and self.commit:
            marca = commit_curto(self.commit)
        else:
            marca = f"sha256:{op.sha256[:12]}"
        return f"env-docs-sync: [{op.ambiente}] {op.caminho} @ {marca}"[:LIMITE_CHANGELOG]

    def escrever(self, op: Operacao) -> None:
        """Confere a trava, pula o bloco que a página já tem e escreve pelo `section-set`.

        Pular: se o `<pre>` relido já tem o hash do arquivo (e o callout "ausente" bate com a ação),
        não há escrita. Sem isso, outro host (que tem o próprio estado) ou um estado perdido
        reescreveria o bloco só pela linha "sincronizado em", criando uma revisão sem mudança.
        `--create` em toda ação: o h3 que falta na página (apagado à mão, página migrada) volta, e o
        kb só troca quando o h3 existe. O corpo vai pelo stdin, nunca em argv.
        """
        self.conferir_permissao()
        atual = self.ler_corpo(op.ambiente, op.caminho)
        if bloco_confere(op, atual) and ("ausente desde" in atual) == (op.acao == "marcar_ausente"):
            return False
        self._kb("page", "section-set", self.page_id, f"--heading={op.caminho}", f"--under={op.sob}",
                 "--create", "--stdin", f"--changelog={self._changelog(op)}", "--apply",
                 entrada=op.corpo.encode("utf-8"))
        if not bloco_confere(op, self.ler_corpo(op.ambiente, op.caminho)):
            raise ErroEnvDocs(f"releitura: o bloco {op.ambiente} {op.caminho} na página não confere com o "
                              "enviado; o estado não muda")
        return True

    def conferir_derivadas(self, config, ci_cd) -> bool:
        return derivadas_conferem(self._html(), pagina_das_derivadas(config, ci_cd))

    def escrever_derivadas(self, config, ci_cd) -> bool:
        """Refaz as seções derivadas por `replace`, com as Seções de ambiente da página atual como estão.
        Já iguais (relidas e normalizadas): `False`, sem escrita. Passa pela trava e relê depois."""
        self.conferir_permissao()
        atual = self._html()
        nova = pagina_de_ambientes(config, {}, ci_cd=ci_cd, secoes=partes_da_pagina(atual)[1])
        if derivadas_conferem(atual, nova):
            return False
        marca = hash_sha256(pagina_das_derivadas(config, ci_cd).encode("utf-8"))[:12]
        self.substituir_pagina(nova, aplicar=True, changelog=f"env-docs-sync: seções derivadas @ sha256:{marca}")
        if not derivadas_conferem(self._html(), nova):
            raise ErroEnvDocs("releitura: as seções derivadas da página não conferem com as enviadas; "
                              "o estado não muda")
        return True

    def substituir_pagina(self, pagina: str, *, aplicar: bool, changelog: str):
        """`kb page replace` com a página inteira pelo stdin. Sem `aplicar`, o dry-run do kb (rc 4)."""
        self.conferir_permissao()
        args = ["page", "replace", self.page_id, "--html=@-", f"--confirm={self.page_id}",
                f"--changelog={changelog[:LIMITE_CHANGELOG]}"] + (["--apply"] if aplicar else [])
        return self._kb(*args, entrada=pagina.encode("utf-8"), aceitos=(0,) if aplicar else (4,))


def destino_da_config(config: Mapping, raiz: Path, ctx: "Contexto") -> Destino:
    """A fábrica padrão: o Destino do `doc.backend` da config."""
    backend = config["doc"]["backend"]
    if backend == "kb":
        return DestinoKb(config, ctx, commit=_commit(None, raiz))
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


def rodar_comando(argv, *, env: Mapping[str, str], timeout: float, entrada: bytes | None = None,
                  cwd: Path | None = None) -> ResultadoComando:
    """O runner padrão: argv sem shell, ambiente explícito, stdin = `entrada` (ou /dev/null).

    Timeout e programa ausente viram ErroEnvDocs, sem ecoar argv nem saída. Os testes injetam outro
    runner com a mesma assinatura. `cwd` só o `gh` usa: ele acha o repositório pela pasta.
    """
    opcoes = {"input": entrada} if entrada is not None else {"stdin": subprocess.DEVNULL}
    try:
        saida = subprocess.run(list(argv), env=dict(env), capture_output=True, timeout=timeout, cwd=cwd, **opcoes)
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
# Fonte gh: os nomes dos segredos e das variáveis do CI (nunca valores; o GitHub não os devolve)
# ---------------------------------------------------------------------------------------------

GH_TIMEOUT = 30


@dataclass(frozen=True)
class NomesDoCi:
    escopo: str
    """`repositório` ou o nome de um environment do GitHub."""
    segredos: tuple
    variaveis: tuple


def _gh(ctx: "Contexto", raiz, *args) -> str:
    resultado = ctx.runner(["gh", *args], env=ctx.ambiente, timeout=GH_TIMEOUT, cwd=Path(raiz))
    if resultado.returncode != 0:
        raise ErroEnvDocs(f"gh {' '.join(args[:2])}: rc {resultado.returncode} (o `gh auth status` vale "
                          "para este repositório?)")
    try:
        return resultado.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroEnvDocs(f"gh {' '.join(args[:2])}: saída ilegível") from None


def _nomes(texto: str, onde: str) -> tuple:
    try:
        dados = json.loads(texto)
    except ValueError:
        raise ErroEnvDocs(f"{onde}: a saída não é JSON") from None
    if not isinstance(dados, list) or not all(
            isinstance(item, dict) and isinstance(item.get("name"), str)
            and _RE_NOME_DE_VARIAVEL.fullmatch(item["name"]) for item in dados):
        raise ErroEnvDocs(f"{onde}: a saída não é uma lista de nomes")
    return tuple(sorted(item["name"] for item in dados))


def nomes_do_gh(raiz, ctx: "Contexto") -> list[NomesDoCi]:
    """Os nomes do repositório e de cada environment, pelo `gh` rodado na raiz. Falha é erro: quem
    chama não escreve a seção, para um `gh` sem login não apagar os nomes da página."""
    def escopo(nome, *env):
        return NomesDoCi(nome,
                         _nomes(_gh(ctx, raiz, "secret", "list", *env, "--json", "name"), "gh secret list"),
                         _nomes(_gh(ctx, raiz, "variable", "list", *env, "--json", "name"), "gh variable list"))

    saida = _gh(ctx, raiz, "api", "repos/{owner}/{repo}/environments", "--paginate", "--jq",
                ".environments[].name")
    ambientes = sorted({linha.strip() for linha in saida.splitlines() if linha.strip()})
    for nome in ambientes:
        if nome.startswith("-") or any(ord(ch) < 32 for ch in nome):
            raise ErroEnvDocs("gh api environments: nome de environment inválido")
    return [escopo("repositório")] + [escopo(nome, "--env", nome) for nome in ambientes]


def ci_cd_do_repo(raiz, config: Mapping, ctx: "Contexto") -> str:
    """A seção CI/CD do repositório: os workflows de `ci.workflows` e, com `ci.secrets: "gh"`, os nomes."""
    ci = config["ci"]
    if ci is None:
        return secao_ci_cd(None, None, None)
    workflows = workflows_do_repo(raiz, ci["workflows"]) if ci["workflows"] is not None else None
    nomes = nomes_do_gh(raiz, ctx) if ci["secrets"] == "gh" else None
    return secao_ci_cd(ci, workflows, nomes)


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
        if rel == NOME_DA_CONFIG or _e_workflow(rel, config):
            return True  # entrada das seções derivadas
    return False


def _e_workflow(rel: str, config) -> bool:
    ci = config["ci"]
    return (ci is not None and ci["workflows"] is not None and rel.endswith((".yml", ".yaml"))
            and rel.rsplit("/", 1)[0] == Path(ci["workflows"]).as_posix().rstrip("/"))


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
    sem_escrita: list = field(default_factory=list)
    derivadas: str | None = None
    """"escrita", "já no destino" ou None (não pedidas, ou falharam: ver `aviso_derivadas`)."""
    aviso_derivadas: str | None = None

    @property
    def mudou_estado(self) -> bool:
        return bool(self.aplicadas or self.carimbados or self.derivadas)

    @property
    def escritas(self) -> list:
        """As aplicadas que o destino escreveu de fato (sem as que ele já tinha)."""
        puladas = {id(op) for op in self.sem_escrita}
        return [op for op in self.aplicadas if id(op) not in puladas]


def rodada(estado: Mapping, config: Mapping, raiz: Path, *, remotos, ctx: Contexto, quando: datetime,
           commit: str | None, montar_destino: Callable[[], Destino],
           ao_aceitar: Callable[[dict], None] | None = None,
           derivadas: PedidoDeDerivadas | None = None) -> tuple[dict, Rodada]:
    """Uma rodada de sync: lê development (Varredura) e os `remotos` (ssh), planeja e aplica.

    Devolve (novo estado, Rodada). Quem chama grava o estado se `Rodada.mudou_estado`. Ambiente
    remoto que falhou ao ler fica fora de `atuais` (intocado, não vira ausente). O carimbo
    `remote_checked_at` só vai para o ambiente lido sem nenhuma operação pendente, para a falha de
    escrita ser tentada de novo no próximo gatilho e não só depois da janela. Com `derivadas`, depois dos
    blocos e no mesmo destino, refaz as seções derivadas, se nenhum bloco falhou.
    """
    atuais = {"development": _locais(raiz, config)}
    lidos, avisos = ler_remotos(config, remotos, ctx)
    atuais.update(lidos)
    mudancas = diferencas(estado, {ambiente: _hashes(arquivos) for ambiente, arquivos in atuais.items()})
    if not mudancas and derivadas is None:
        return carimbar_remotos(estado, lidos, quando), Rodada(avisos_remotos=avisos, carimbados=list(lidos))
    sem_pendencia = [a for a in lidos if a not in {m.ambiente for m in mudancas}]
    try:
        destino = montar_destino()
    except ErroEnvDocs as erro:
        return (carimbar_remotos(estado, sem_pendencia, quando),
                Rodada(pendentes=mudancas, erro_do_destino=erro, avisos_remotos=avisos, carimbados=sem_pendencia))
    operacoes = planejar(estado, atuais, sincronizado_em=quando, commit=commit, ler_corpo=destino.ler_corpo)
    resultado = aplicar(estado, operacoes, destino, quando=quando, ao_aceitar=ao_aceitar)
    pendentes = operacoes[len(resultado.aplicadas):]
    prontos = [a for a in lidos if a not in {op.ambiente for op in pendentes}]
    r = Rodada(resultado.aplicadas, pendentes, resultado.falhou, resultado.erro, None, avisos, prontos,
               resultado.sem_escrita)
    novo = resultado.estado
    if derivadas is not None and resultado.falhou is None:
        novo, r.derivadas, r.aviso_derivadas = aplicar_derivadas(novo, config, destino, derivadas, quando)
    return carimbar_remotos(novo, prontos, quando), r


def _linhas_da_rodada(nome: str, r: Rodada) -> list[str]:
    linhas = [f"aviso — {nome}: {aviso}. O ambiente fica como estava; o próximo gatilho tenta de novo."
              for aviso in r.avisos_remotos]
    if r.erro_do_destino is not None:
        linhas.append(f"aviso — {nome}: {r.erro_do_destino}. Pendente: {_listar(r.pendentes)}. "
                      "O estado não mudou; o próximo gatilho tenta de novo.")
    if r.escritas:
        linhas.append(f"Página de ambientes atualizada ({nome}) — {_listar(r.escritas)}")
    if r.derivadas == "escrita":
        linhas.append(f"Página de ambientes atualizada ({nome}) — seções derivadas (Ambientes, CI/CD, Como rodar)")
    if r.aviso_derivadas is not None:
        linhas.append(f"aviso — {nome}: seções derivadas não atualizadas ({r.aviso_derivadas}). "
                      "O próximo gatilho tenta de novo.")
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
    entradas, janela = entradas_derivadas(raiz, config), gatilho.evento == "SessionStart"
    if (not remotos_devidos(config, estado, gatilho, ctx.agora())
            and not diferencas(estado, {"development": _hashes(_locais(raiz, config))})
            and not derivadas_devidas(config, estado, entradas, ctx.agora(), olhar_janela=janela)):
        return []

    with trava_do_repo(raiz, pasta, ctx.espera_da_trava):
        estado = carregar_estado(arquivo)  # outro processo pode ter sincronizado enquanto esperávamos
        quando = ctx.agora()
        pedido = (PedidoDeDerivadas(entradas, lambda: ci_cd_do_repo(raiz, config, ctx))
                  if derivadas_devidas(config, estado, entradas, quando, olhar_janela=janela) else None)
        novo, r = rodada(estado, config, raiz, remotos=remotos_devidos(config, estado, gatilho, quando), ctx=ctx,
                         quando=quando, commit=_commit(None, raiz),
                         montar_destino=lambda: ctx.fabrica_destino(config, raiz, ctx),
                         ao_aceitar=lambda parcial: gravar_estado(arquivo, parcial), derivadas=pedido)
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
# Instalação no Codex: o trust dos hooks do plugin, gravado no config.toml do CODEX_HOME
# ---------------------------------------------------------------------------------------------
# O Codex só roda o hook de plugin que tem trust em `[hooks.state."<chave>"]`. A chave, o hash da
# declaração e a impressão do pacote saem do codex-rs na tag rust-v0.164.0 (arquivo e linha em
# references/hosts.md §4) e foram conferidos contra o `currentHash` do `hooks/list` do app-server
# (tests/fixtures/codex-hooks-list-dourado.json).

CODEX_MEDIDOS = ("0.164.0", "0.165.0")
"""Versões do codex-cli em que o hash bateu com o próprio Codex: o 0.164.0 pela leitura do código e
pela fixture, e cada versão seguinte pelo tests/oraculo_codex.py."""

NOME_DO_PLUGIN = "env-docs-sync"

CODEX_EVENTOS = {
    "PreModelRequest": "pre_model_request",
    "PostModelRequest": "post_model_request",
    "PreToolUse": "pre_tool_use",
    "PermissionRequest": "permission_request",
    "PostToolUse": "post_tool_use",
    "PreCompact": "pre_compact",
    "PostCompact": "post_compact",
    "SessionStart": "session_start",
    "SessionEnd": "session_end",
    "UserPromptSubmit": "user_prompt_submit",
    "SubagentStart": "subagent_start",
    "SubagentStop": "subagent_stop",
    "Stop": "stop",
    "Interrupt": "interrupt",
}
"""Evento do hooks.json → rótulo da chave, na ordem em que o Codex percorre os eventos."""

_CODEX_SEM_MATCHER = frozenset({"PreModelRequest", "PostModelRequest", "UserPromptSubmit", "Stop", "Interrupt"})
_CODEX_TIMEOUT_CURTO = frozenset({"SessionEnd", "Interrupt"})  # padrão 1 s, teto 3 s; os outros, 600 s
_CAMPOS_DO_HANDLER = frozenset({"type", "command", "commandWindows", "command_windows", "timeout", "async",
                                "statusMessage"})
_CAMPOS_DO_GRUPO = frozenset({"matcher", "hooks"})
_LIXO_DO_PACOTE = ("__pycache__", ".venv")
_RE_HASH = re.compile(r"sha256:[0-9a-f]{64}")
_CAMPOS_DO_TRUST = ("trusted_hash", "trusted_content_hash")


def _erro_de_forma(onde: str, problema: str) -> ErroEnvDocs:
    return ErroEnvDocs(f"a forma do hook mudou em {onde}: {problema}. O hash do trust só modela handler "
                       f"`command` com {', '.join(sorted(_CAMPOS_DO_HANDLER))}; aprove em /hooks no Codex")


def _handler_normalizado(evento: str, handler, onde: str) -> dict:
    """O handler como o Codex o guarda antes de hashear: `commandWindows` fora, timeout com o padrão."""
    if not isinstance(handler, dict):
        raise _erro_de_forma(onde, "o handler não é objeto")
    if handler.get("type") != "command":
        raise _erro_de_forma(onde, f"type {handler.get('type')!r}")
    sobra = sorted(set(handler) - _CAMPOS_DO_HANDLER)
    if sobra:
        raise _erro_de_forma(onde, f"campo {', '.join(sobra)}")
    comando, timeout = handler.get("command"), handler.get("timeout")
    assincrono, status = handler.get("async", False), handler.get("statusMessage")
    if not isinstance(comando, str) or not comando.strip():
        raise _erro_de_forma(onde, "command vazio ou ausente (o Codex pula o handler)")
    if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 0):
        raise _erro_de_forma(onde, "timeout que não é inteiro sem sinal")
    janelas = handler.get("commandWindows", handler.get("command_windows"))
    if not isinstance(assincrono, bool) or any(v is not None and not isinstance(v, str) for v in (status, janelas)):
        raise _erro_de_forma(onde, "async, statusMessage ou commandWindows do tipo errado")
    if evento in _CODEX_TIMEOUT_CURTO:
        timeout = min(max(1 if timeout is None else timeout, 1), 3)
    else:
        timeout = max(600 if timeout is None else timeout, 1)
    normal = {"type": "command", "command": comando, "timeout": timeout, "async": assincrono}
    if status is not None:
        normal["statusMessage"] = status
    return normal


def _hash_da_declaracao(evento: str, matcher, handler: dict) -> str:
    """`hook_hash` do Codex: a identidade {event_name, matcher, hooks: [handler]} sem os None, em JSON
    com as chaves ordenadas e sem espaços, no sha256 (`version_for_toml`)."""
    identidade = {"event_name": CODEX_EVENTOS[evento], "hooks": [handler]}
    if matcher is not None:
        identidade["matcher"] = matcher
    texto = json.dumps(identidade, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hooks_do_pacote(raiz, plugin_id: str) -> list[tuple[str, str]]:
    """[(chave do `[hooks.state]`, hash da declaração)] de cada handler do `hooks/hooks.json` do pacote,
    na ordem do Codex. Recusa, em vez de errar o hash, qualquer forma que a função não modela."""
    arquivo = Path(raiz) / "hooks" / "hooks.json"
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        raise ErroEnvDocs(f"hooks.json do pacote ilegível em {arquivo} ({type(erro).__name__})") from None
    if not isinstance(dados, dict) or set(dados) - {"description", "hooks"} or not isinstance(dados.get("hooks"), dict):
        raise _erro_de_forma(str(arquivo), "o topo não é {description, hooks}")
    desconhecidos = sorted(set(dados["hooks"]) - set(CODEX_EVENTOS))
    if desconhecidos:
        raise _erro_de_forma(str(arquivo), f"evento que o Codex não tem: {', '.join(desconhecidos)}")
    saida = []
    for evento, rotulo in CODEX_EVENTOS.items():
        grupos = dados["hooks"].get(evento, [])
        if not isinstance(grupos, list):
            raise _erro_de_forma(evento, "o evento não é lista")
        for g, grupo in enumerate(grupos):
            if not isinstance(grupo, dict) or set(grupo) - _CAMPOS_DO_GRUPO or not isinstance(grupo.get("hooks"), list):
                raise _erro_de_forma(f"{evento}[{g}]", "o grupo não é {matcher, hooks}")
            matcher = grupo.get("matcher")
            if matcher is not None and not isinstance(matcher, str):
                raise _erro_de_forma(f"{evento}[{g}]", "matcher que não é texto")
            if evento in _CODEX_SEM_MATCHER:
                matcher = None  # o Codex descarta o matcher destes eventos antes de hashear
            for h, handler in enumerate(grupo["hooks"]):
                normal = _handler_normalizado(evento, handler, f"{evento}[{g}].hooks[{h}]")
                saida.append((f"{plugin_id}:hooks/hooks.json:{rotulo}:{g}:{h}",
                              _hash_da_declaracao(evento, matcher, normal)))
    return saida


def impressao_do_pacote(raiz) -> str:
    """`plugin_content_hash` do Codex: sha256 de "codex-plugin-bundle-v1" e de cada entrada da pasta,
    em pré-ordem com os nomes em ordem de bytes. Pula `__pycache__`, `.venv`, `*.pyc` e `*.egg-info`."""
    raiz = Path(raiz)
    if not stat.S_ISDIR(os.lstat(raiz).st_mode):
        raise ErroEnvDocs(f"o pacote instalado não é pasta: {raiz}")
    impressao = hashlib.sha256(b"codex-plugin-bundle-v1")
    pendentes = [raiz]
    while pendentes:
        caminho = pendentes.pop()
        relativo = "" if caminho == raiz else caminho.relative_to(raiz).as_posix()
        nome = caminho.name if relativo else ""
        if nome in _LIXO_DO_PACOTE or nome.endswith((".pyc", ".egg-info")):
            continue
        bruto = os.fsencode(relativo)
        impressao.update(len(bruto).to_bytes(8, "little") + bruto)
        modo = os.lstat(caminho).st_mode
        if stat.S_ISDIR(modo):
            impressao.update(b"directory")
            filhos = sorted(os.listdir(caminho), key=os.fsencode)
            pendentes.extend(caminho / filho for filho in reversed(filhos))
        elif stat.S_ISREG(modo):
            dados = caminho.read_bytes()
            impressao.update(b"file" + len(dados).to_bytes(8, "little") + dados)
        else:
            raise ErroEnvDocs(f"o pacote tem symlink ou arquivo especial em {relativo}: o Codex recusa a "
                              "impressão e pula os hooks do plugin")
    return "sha256:" + impressao.hexdigest()


@dataclass(frozen=True)
class PluginNoCodex:
    plugin_id: str
    versao: str
    raiz: Path
    ligado: bool


def plugin_no_codex(codex_home, config: Mapping, nome: str = NOME_DO_PLUGIN) -> PluginNoCodex:
    """O pacote instalado em `plugins/cache/<loja>/<nome>/<versão>/` com a entrada `[plugins."<id>"]` no
    config.toml. Mais de uma loja ou de uma versão é recusa, não escolha."""
    cache = Path(codex_home) / "plugins" / "cache"
    achados = []
    if cache.is_dir():
        for loja in sorted(cache.iterdir()):
            if (loja / nome).is_dir():
                versoes = sorted(p for p in (loja / nome).iterdir() if p.is_dir() and not p.name.startswith("."))
                if versoes:
                    achados.append((loja.name, versoes))
    instrucao = f"instale com `codex plugin add {nome}@<loja>` e rode de novo"
    if not achados:
        raise ErroEnvDocs(f"{nome} não está instalado no Codex em {codex_home} (nada em plugins/cache); {instrucao}")
    if len(achados) > 1:
        raise ErroEnvDocs(f"{nome} está instalado por mais de uma loja ({', '.join(l for l, _ in achados)}); "
                          "deixe uma só com `codex plugin remove`")
    loja, versoes = achados[0]
    plugin_id = f"{nome}@{loja}"
    if len(versoes) > 1:
        raise ErroEnvDocs(f"{plugin_id} tem mais de uma versão no cache ({', '.join(v.name for v in versoes)}); "
                          f"reinstale com `codex plugin add {plugin_id}`")
    entrada = config.get("plugins", {}).get(plugin_id) if isinstance(config.get("plugins"), dict) else None
    if not isinstance(entrada, dict):
        raise ErroEnvDocs(f"{plugin_id} não está instalado: o pacote está no cache, mas o config.toml não tem "
                          f'[plugins."{plugin_id}"]; {instrucao}')
    return PluginNoCodex(plugin_id, versoes[0].name, versoes[0], entrada.get("enabled") is not False)


def _ler_toml(texto: str) -> dict:
    try:
        return tomllib.loads(texto)
    except tomllib.TOMLDecodeError as erro:  # a mensagem é fixa + linha e coluna; não ecoa valor
        raise ErroEnvDocs(f"config.toml inválido ({erro}); nada foi gravado") from None


def _com_quebra_no_fim(texto: str) -> str:
    nl = "\r\n" if "\r\n" in texto else "\n"
    return texto + nl if texto and not texto.endswith("\n") else texto


def _linha_do_cabecalho(linhas, chave: str) -> int | None:
    citada = re.escape(chave)
    padrao = re.compile(rf"\[\s*hooks\s*\.\s*state\s*\.\s*(?:\"{citada}\"|'{citada}')\s*\](?:\s*#.*)?")
    return next((i for i, linha in enumerate(linhas) if padrao.fullmatch(linha.strip())), None)


def editar_trust(texto: str, desejado: Mapping[str, Mapping[str, str]]) -> str:
    """O config.toml com `desejado` ({chave: {campo: hash}}) no `[hooks.state]`, editado como texto.

    Troca a linha do campo dentro da tabela `[hooks.state."<chave>"]` ou acrescenta o que falta; sem a
    tabela, acrescenta a tabela no fim. O resto do arquivo fica byte a byte. Confere o resultado
    relendo o TOML: se ele não for o antigo mais `desejado`, recusa (trust em tabela inline ou chave
    pontuada, que a edição não cobre)."""
    for campos in desejado.values():
        if any(not isinstance(v, str) or not _RE_HASH.fullmatch(v) for v in campos.values()):
            raise ErroEnvDocs("valor fora do formato de hash (sha256:<64 hex>); nada foi gravado")
    antes = _ler_toml(texto)
    nl = "\r\n" if "\r\n" in texto else "\n"
    linhas = _com_quebra_no_fim(texto).splitlines(keepends=True)
    estado = antes.get("hooks", {}).get("state", {}) if isinstance(antes.get("hooks"), dict) else {}
    for chave, campos in desejado.items():
        atual = estado.get(chave) if isinstance(estado, dict) else None
        faltam = {c: v for c, v in campos.items() if not (isinstance(atual, dict) and atual.get(c) == v)}
        if not faltam:
            continue
        inicio = _linha_do_cabecalho(linhas, chave)
        if inicio is None:
            linhas += ([nl] if linhas else []) + [f'[hooks.state."{chave}"]{nl}']
            linhas += [f'{campo} = "{valor}"{nl}' for campo, valor in campos.items()]
            continue
        fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].lstrip().startswith("[")), len(linhas))
        for campo, valor in faltam.items():
            nova = f'{campo} = "{valor}"{nl}'
            achada = next((i for i in range(inicio + 1, fim) if re.match(rf"\s*{campo}\s*=", linhas[i])), None)
            if achada is not None:
                linhas[achada] = nova
            else:
                ultima = max((i for i in range(inicio, fim) if linhas[i].strip()), default=inicio)
                linhas.insert(ultima + 1, nova)
                fim += 1
    novo = "".join(linhas)
    if novo == _com_quebra_no_fim(texto):
        return texto
    esperado = copy.deepcopy(antes)
    try:
        tabela = esperado.setdefault("hooks", {}).setdefault("state", {})
        for chave, campos in desejado.items():
            tabela.setdefault(chave, {}).update(campos)
        confere = tomllib.loads(novo) == esperado
    except (AttributeError, TypeError, tomllib.TOMLDecodeError):
        confere = False
    if not confere:
        raise ErroEnvDocs("o trust deste config.toml está numa forma que a edição não cobre (tabela inline ou "
                          "chave pontuada); nada foi gravado. Aprove os hooks em /hooks no Codex")
    return novo


@dataclass(frozen=True)
class InstalacaoCodex:
    plugin: PluginNoCodex
    config: Path
    conteudo: str
    chaves: tuple[str, ...]
    mudam: tuple[str, ...]
    antes: bytes = field(repr=False)
    depois: str = field(repr=False)


def planejar_instalacao(codex_home) -> InstalacaoCodex:
    """O que o `install --codex` gravaria: a chave e os dois hashes de cada hook do pacote instalado."""
    config = Path(codex_home) / "config.toml"
    try:
        bruto = config.read_bytes()
    except FileNotFoundError:
        raise ErroEnvDocs(f"{NOME_DO_PLUGIN} não está instalado no Codex em {codex_home}: {config} não existe") from None
    try:
        texto = bruto.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroEnvDocs(f"{config} não é UTF-8; nada foi gravado") from None
    dados = _ler_toml(texto)
    plugin = plugin_no_codex(codex_home, dados)
    hooks = hooks_do_pacote(plugin.raiz, plugin.plugin_id)
    conteudo = impressao_do_pacote(plugin.raiz)
    desejado = {chave: {"trusted_hash": decl, "trusted_content_hash": conteudo} for chave, decl in hooks}
    estado = dados.get("hooks", {}).get("state", {}) if isinstance(dados.get("hooks"), dict) else {}
    estado = estado if isinstance(estado, dict) else {}
    mudam = tuple(chave for chave, campos in desejado.items()
                  if not isinstance(estado.get(chave), dict) or any(estado[chave].get(c) != v for c, v in campos.items()))
    return InstalacaoCodex(plugin, config, conteudo, tuple(desejado), mudam, bruto, editar_trust(texto, desejado))


def linhas_da_mudanca(antes: str, depois: str, nome: str) -> list[str]:
    """O diff sem contexto do config.toml. Só aparecem linhas do trust; qualquer outra sai omitida, para
    um valor do config.toml (um token de MCP, por exemplo) nunca chegar à tela."""
    nosso = re.compile(rf'(?:\[hooks\.state\."[^"]+"\]|(?:{"|".join(_CAMPOS_DO_TRUST)}) = "sha256:[^"]*")?')
    saida = []
    for linha in difflib.unified_diff(_com_quebra_no_fim(antes).splitlines(), depois.splitlines(),
                                      fromfile=nome, tofile=f"{nome} (com o trust)", n=0, lineterm=""):
        if linha[:1] in "+-" and not linha.startswith(("+++", "---")) and not nosso.fullmatch(linha[1:]):
            linha = linha[0] + "<linha omitida: não é do trust>"
        saida.append(linha)
    return saida


_MEDIDOS = " e no ".join(CODEX_MEDIDOS)


def aviso_da_versao_do_codex(env: Mapping[str, str], executar=rodar_comando) -> str | None:
    """Aviso quando o codex do PATH não é a versão em que o hash foi medido (ou não roda)."""
    try:
        resultado = executar(["codex", "--version"], env=env, timeout=10)
    except ErroEnvDocs as erro:
        return f"{erro}: a versão do Codex não foi conferida (o hash foi medido no codex-cli {_MEDIDOS})"
    partes = resultado.stdout.decode("utf-8", errors="replace").split()
    versao = partes[-1] if resultado.returncode == 0 and partes else None
    if versao is None:
        return f"codex --version não respondeu: a versão não foi conferida (o hash foi medido no {_MEDIDOS})"
    if versao not in CODEX_MEDIDOS:
        return (f"este é o codex-cli {versao}, e o hash foi medido no {_MEDIDOS}: depois do --apply, confira "
                "em /hooks que os hooks do env-docs-sync aparecem confiados")
    return None


def _copia_de_seguranca(config: Path, bruto: bytes) -> Path:
    carimbo = datetime.now().strftime("%Y%m%dT%H%M%S")
    for n in range(100):
        copia = config.with_name(f"{config.name}.env-docs-sync-{carimbo}{f'-{n}' if n else ''}.bak")
        try:
            descritor = os.open(copia, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(descritor, "wb") as saida:
            saida.write(bruto)
            saida.flush()
            os.fsync(saida.fileno())
        return copia
    raise ErroEnvDocs(f"não achei nome livre para a cópia de {config}; nada foi gravado")


def aplicar_instalacao(plano: InstalacaoCodex) -> Path:
    """Grava o config.toml: cópia antes, temporário com o mesmo modo, os.replace no arquivo real (um
    config.toml que é symlink continua symlink). Recusa se o arquivo mudou desde o plano."""
    real = plano.config.resolve()
    modo = stat.S_IMODE(os.stat(real).st_mode)
    copia = _copia_de_seguranca(plano.config, plano.antes)
    descritor, temporario = tempfile.mkstemp(dir=real.parent, prefix=f".{real.name}.", suffix=".tmp")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="") as saida:
            os.fchmod(saida.fileno(), modo)
            saida.write(plano.depois)
            saida.flush()
            os.fsync(saida.fileno())
        if real.read_bytes() != plano.antes:
            raise ErroEnvDocs(f"{plano.config} mudou durante a instalação; nada foi gravado (rode de novo)")
        os.replace(temporario, real)
    except BaseException:
        if os.path.exists(temporario):
            os.unlink(temporario)
        raise
    return copia


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
    entradas = entradas_derivadas(raiz, config)
    pedido = (PedidoDeDerivadas(entradas, lambda: ci_cd_do_repo(raiz, config, Contexto()))
              if args.remote or derivadas_devidas(config, estado, entradas, quando, olhar_janela=False) else None)
    novo, r = rodada(estado, config, raiz, remotos=remotos, ctx=Contexto(), quando=quando, commit=commit,
                     montar_destino=lambda: _destino_da_cli(args, config, raiz), derivadas=pedido)
    for aviso in r.avisos_remotos:
        print(f"env-docs-sync: aviso — {aviso}; o ambiente fica como estava", file=sys.stderr)
    for op in r.escritas:
        print(f"aplicado: {op.resumo()}")
    for op in r.sem_escrita:
        print(f"já no destino: {op.resumo()}")
    if r.derivadas is not None:
        print(f"{'aplicado' if r.derivadas == 'escrita' else 'já no destino'}: seções derivadas")
    if r.aviso_derivadas is not None:
        print(f"env-docs-sync: aviso — seções derivadas não atualizadas: {r.aviso_derivadas}", file=sys.stderr)
    if r.mudou_estado:
        gravar_estado(args.state, novo)
    if r.erro_do_destino is not None:
        raise r.erro_do_destino
    if r.falhou is not None:
        print(f"env-docs-sync: falhou em {r.falhou.resumo()}: {_detalhe(r.erro)}", file=sys.stderr)
        return 1
    if not r.aplicadas and r.derivadas is None and r.aviso_derivadas is None:
        print("nada a sincronizar")
    return 1 if r.avisos_remotos or r.aviso_derivadas else 0


def _destino_da_cli(args, config, raiz):
    """`--to-dir` (destino de diretório, para teste) ou o Destino de `doc.backend`."""
    if args.to_dir:
        return DestinoDiretorio(args.to_dir)
    if config["doc"]["backend"] == "kb":
        return DestinoKb(config, Contexto(), commit=_commit(getattr(args, "commit", None), raiz))
    return destino_da_config(config, raiz, Contexto())


def _cmd_status(args):
    raiz, config = _contexto(args)
    destino = _destino_da_cli(args, config, raiz)
    if isinstance(destino, DestinoKb):
        destino.fixar_leitura()  # uma leitura da página serve todos os blocos
    atuais, avisos = {"development": _locais(raiz, config)}, []
    if args.remote:
        lidos, avisos = ler_remotos(config, _remotos(config), Contexto())
        atuais.update(lidos)
    linhas = status_dos_arquivos(atuais, destino)
    try:
        conferem = destino.conferir_derivadas(config, ci_cd_do_repo(raiz, config, Contexto()))
        linhas.append(("página", "seções derivadas",
                       "ausente" if conferem is None else ("ok" if conferem else "diverge")))
    except ErroEnvDocs as erro:
        avisos.append(f"seções derivadas: {erro}")
    for ambiente, caminho, situacao in linhas:
        print(f"{situacao}\t{ambiente}\t{caminho}")
    contagem = {s: sum(1 for *_, x in linhas if x == s) for s in ("ok", "diverge", "ausente")}
    print(f"{contagem['ok']} ok, {contagem['diverge']} diverge, {contagem['ausente']} ausente")
    for aviso in avisos:
        print(f"env-docs-sync: aviso — {aviso}; o ambiente não foi conferido", file=sys.stderr)
    if contagem["ok"] != len(linhas):
        return 3
    return 1 if avisos else 0


def _cmd_migrate(args):
    """A Página de ambientes inteira, renderizada do template, publicada por `kb page replace`.

    Lê todos os ambientes (development e os ssh): sem um deles, a página nova perderia blocos, e a
    migração não sai. Passa pela mesma trava de permissão. Sem `--apply`, só o dry-run do kb (rc 4).
    Com `--state`, grava o estado com o que foi publicado.
    """
    raiz, config = _contexto(args)
    if config["doc"]["backend"] != "kb":
        raise ErroEnvDocs("migrate só existe para o backend kb")
    quando, commit = _agora(args.now), _commit(args.commit, raiz)
    ctx = Contexto()
    atuais = {"development": _locais(raiz, config)}
    lidos, avisos = ler_remotos(config, _remotos(config), ctx)
    for aviso in avisos:
        print(f"env-docs-sync: aviso — {aviso}", file=sys.stderr)
    if avisos:
        raise ErroEnvDocs("migração cancelada: a página nova precisa de todos os ambientes; nada foi enviado")
    atuais.update(lidos)
    blocos = {}
    for ambiente, arquivos in atuais.items():
        for caminho, dados in arquivos.items():
            try:
                blocos.setdefault(ambiente, {})[caminho] = bloco_de_arquivo(
                    dados, sincronizado_em=quando, commit=commit if ambiente == "development" else None)
            except ErroEnvDocs as erro:
                raise ErroEnvDocs(f"{ambiente} {caminho}: {erro}") from None
    marca = commit_curto(commit) if commit else f"{quando:%Y-%m-%d %H:%M}"
    destino = DestinoKb(config, ctx, commit=commit)
    ci_cd = ci_cd_do_repo(raiz, config, ctx)
    pagina = pagina_de_ambientes(config, blocos, ci_cd=ci_cd)
    rc, saida = destino.substituir_pagina(pagina, aplicar=args.apply,
                                          changelog=f"env-docs-sync: migração ao template @ {marca}")
    contagem = sum(len(a) for a in atuais.values())
    if not args.apply:
        print(f"dry-run (nada enviado; use --apply): {contagem} bloco(s) em {len(atuais)} ambiente(s)")
        print(json.dumps(saida, ensure_ascii=False, sort_keys=True))
        return 4
    print(f"página {destino.page_id} publicada: {contagem} bloco(s) em {len(atuais)} ambiente(s)")
    print(json.dumps(saida, ensure_ascii=False, sort_keys=True))
    if args.state:
        estado = estado_vazio()
        for ambiente, arquivos in atuais.items():
            estado["environments"][ambiente] = {c: {"sha256": hash_sha256(d), "synced_at": _carimbo(quando)}
                                                for c, d in arquivos.items()}
        estado["derived"] = {"inputs_sha256": entradas_derivadas(raiz, config), "checked_at": _carimbo(quando),
                             "sha256": hash_sha256(pagina_das_derivadas(config, ci_cd).encode("utf-8"))}
        gravar_estado(args.state, carimbar_remotos(estado, lidos, quando))
    return 0


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


def _cmd_init(args):
    """Escreve a `.env-docs.json` inicial; nunca sobrescreve. Lista os arquivos da Varredura e o que falta."""
    raiz = Path(args.root)
    arquivo = raiz / ".env-docs.json"
    config = config_inicial(raiz, socket.gethostname())
    try:
        descritor = os.open(arquivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        raise ErroEnvDocs(f"{arquivo} já existe; edite à mão (o init não sobrescreve)") from None
    with os.fdopen(descritor, "w", encoding="utf-8") as saida:
        saida.write(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    arquivos = varredura(raiz, config["include"], config["exclude"])
    print(f"gravado {arquivo}: {len(arquivos)} arquivo(s) na Varredura")
    for caminho in arquivos:
        print(f"  {caminho}")
    try:
        validar_config(config)
    except ErroDeConfig as erro:
        print("a preencher (o validate recusa até lá):")
        for linha in erro.erros:
            print(f"  {linha}")
    print("staging e production entram à mão, com source ssh, host e files (references/config.md)")
    return 0


def _cmd_install(args):
    """Grava no config.toml do Codex o trust dos hooks do plugin instalado. Sem `--apply`, mostra o diff
    exato e sai 4; com `--apply`, faz cópia e grava; já confiado, sai 0 sem tocar o arquivo."""
    home = Path(args.codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    aviso = aviso_da_versao_do_codex(dict(os.environ))
    if aviso:
        print(f"env-docs-sync: aviso — {aviso}", file=sys.stderr)
    plano = planejar_instalacao(home)
    plugin = plano.plugin
    print(f"plugin {plugin.plugin_id} {plugin.versao} em {plugin.raiz}")
    print(f"conteúdo do pacote: {plano.conteudo}")
    print(f"{len(plano.chaves)} hook(s): {len(plano.mudam)} a confiar, {len(plano.chaves) - len(plano.mudam)} já confiado(s)")
    if not plugin.ligado:
        print(f"env-docs-sync: aviso — {plugin.plugin_id} está desligado no config.toml (enabled = false); "
              "o trust vale quando você ligar", file=sys.stderr)
    if not plano.mudam:
        print("nada a mudar: o config.toml já confia nestes hooks com este conteúdo")
        return 0
    for linha in linhas_da_mudanca(plano.antes.decode("utf-8"), plano.depois, str(plano.config)):
        print(linha)
    if not args.apply:
        print("dry-run: nada gravado; rode de novo com --apply")
        return 4
    copia = aplicar_instalacao(plano)
    print(f"cópia do config.toml anterior: {copia}")
    print(f"gravado: {len(plano.mudam)} hook(s) confiado(s) em {plano.config}. Confira em /hooks numa sessão "
          "do Codex. Um update do plugin muda o conteúdo e pede este comando de novo")
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
    _gravar_privado(args.out, pagina_de_ambientes(config, blocos, ci_cd=ci_cd_do_repo(raiz, config, Contexto())))
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

    init = sub.add_parser("init", help="escreve a .env-docs.json inicial (nunca sobrescreve)")
    init.add_argument("--root", default=".", help="raiz do repositório (padrão: .)")
    init.set_defaults(funcao=_cmd_init)
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
    migrate = comando("migrate", "publica a Página de ambientes inteira (kb page replace), com a trava; "
                      "sem --apply, dry-run (rc 4)", _cmd_migrate, relogio=True)
    migrate.add_argument("--state", help="grava aqui o estado do que foi publicado (só com --apply)")
    migrate.add_argument("--apply", action="store_true", help="publica de verdade (sem isto: dry-run do kb)")
    install = sub.add_parser("install", help="grava no config.toml do Codex o trust dos hooks do plugin "
                             "instalado; sem --apply, o diff exato (rc 4)")
    install.add_argument("--codex", action="store_true", required=True,
                         help="o host (só o Codex precisa: no Claude Code, o plugin instalado já roda)")
    install.add_argument("--codex-home", help="padrão: $CODEX_HOME ou ~/.codex")
    install.add_argument("--apply", action="store_true", help="grava de verdade, com cópia antes")
    install.set_defaults(funcao=_cmd_install)
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
