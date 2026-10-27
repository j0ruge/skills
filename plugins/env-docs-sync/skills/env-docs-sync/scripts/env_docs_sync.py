#!/usr/bin/env python3
"""env-docs-sync: mantém os arquivos .env* de um repositório espelhados numa Página de ambientes.

Este arquivo tem três camadas, nesta ordem:

1. **Núcleo puro.** Config, Varredura, hash, Bloco de arquivo, plano de operações, estado e a
   Página de ambientes inteira. Não abre rede, não chama o backend de documentação nem o ssh.
   Relógio, sha do commit, conteúdo dos ambientes remotos e o leitor do corpo atual entram por
   parâmetro.
2. **Adaptadores.** Nesta versão só existe o `DestinoDiretorio`, um destino local para teste e
   inspeção. O destino `kb`, a fonte ssh e a entrada do hook chegam depois e se encaixam pelas
   mesmas costuras: `Destino` (ler_corpo/escrever) e o mapa `atuais` de `planejar`.
3. **CLI mínima** (`validate`, `scan`, `plan`, `sync --to-dir`, `render-page`).

Regra de segredo, em todas as camadas: nenhum valor de arquivo .env* vai para stdout, stderr,
mensagem de erro, `repr` ou estado. O valor só vai para o corpo do Bloco de arquivo, que é o destino.
Só biblioteca padrão; Python 3.11+.
"""
from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import html
import json
import os
import re
import string
import subprocess
import sys
import tempfile
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


# ---------------------------------------------------------------------------------------------
# CLI mínima
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


def _remotos_ignorados(config):
    remotos = [a for a in AMBIENTES if a in config["environments"] and a != "development"]
    if remotos:
        print(f"ambientes remotos ignorados nesta versão: {', '.join(remotos)} (Sync remoto ainda não existe)")


def _cmd_sync(args):
    raiz, config = _contexto(args)
    quando, commit = _agora(args.now), _commit(args.commit, raiz)
    estado = carregar_estado(args.state)
    destino = DestinoDiretorio(args.to_dir)
    operacoes = planejar(estado, {"development": _locais(raiz, config)}, sincronizado_em=quando,
                         commit=commit, ler_corpo=destino.ler_corpo)
    _remotos_ignorados(config)
    if not operacoes:
        print("nada a sincronizar")
        return 0
    resultado = aplicar(estado, operacoes, destino, quando=quando)
    for op in resultado.aplicadas:
        print(f"aplicado: {op.resumo()}")
    if resultado.aplicadas:
        gravar_estado(args.state, resultado.estado)
    if resultado.falhou is not None:
        detalhe = str(resultado.erro) if isinstance(resultado.erro, ErroEnvDocs) else type(resultado.erro).__name__
        print(f"env-docs-sync: falhou em {resultado.falhou.resumo()}: {detalhe}", file=sys.stderr)
        return 1
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
        description="env-docs-sync (núcleo): Varredura, plano e Página de ambientes. Nunca imprime valores.")
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
    sync = comando("sync", "aplica o plano de development num destino de diretório", _cmd_sync,
                   estado=True, relogio=True)
    sync.add_argument("--to-dir", required=True, help="destino local de teste (o destino kb chega depois)")
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
