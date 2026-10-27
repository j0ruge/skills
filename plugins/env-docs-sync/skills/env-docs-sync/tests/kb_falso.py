#!/usr/bin/env python3
"""Um `kb` falso para os testes do adaptador: a CLI de BookStack que o plugin chama por subprocesso.

Guarda a página num JSON (caminho em `KB_FALSO_ESTADO`) e emula, com os códigos de saída e o JSON da
CLI real (`references/kb-cli.md` §3–5 do kb, lido em 2026-10-27):

- `pages read <id>`: o registro da página, com `raw_html`, `html` e `revision_count`;
- `content-permissions read page <id>`: `role_permissions[]` + `fallback_permissions{}`;
- `page section-set <id> --heading=H --under=U [--create] --stdin [--changelog=C] [--apply]`: troca o
  corpo do h3, ou cria h3 + corpo na ordem alfabética; corpo igual = `changed: false`, sem revisão;
- `page replace <id> --html @- --confirm <id> [--changelog=C] [--apply]`.

Como o BookStack, acrescenta `id="bkmrk-N"` aos blocos guardados. Botões de teste no estado:
`falhar` ({subcomando: [rc, code, message, backup]}), `sabotar` (1 byte a mais no corpo ou na página guardada) e
`chamadas` (cada argv recebido, sem o stdin). É independente do plugin de propósito: não importa nada
dele, para o teste não confirmar o próprio código.
"""
import html
import json
import os
import re
import sys

HEADING = re.compile(r"<h([1-6])\b([^>]*)>(.*?)</h\1\s*>", re.S | re.I)


def texto(fragmento):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragmento))).strip()


def headings(pagina):
    return [{"nivel": int(m.group(1)), "texto": texto(m.group(3)), "ini": m.start(), "fim": m.end()}
            for m in HEADING.finditer(pagina)]


def com_ids(fragmento, estado):
    def troca(m):
        estado["proximo_id"] = estado.get("proximo_id", 0) + 1
        return f'<{m.group(1)} id="bkmrk-{estado["proximo_id"]}"'
    return re.sub(r"<(p|pre|h3|table)(?=[\s>])(?![^>]*\bid=)", troca, fragmento)


def sem_ids(fragmento):
    return re.sub(r' id="bkmrk-[^"]*"', "", fragmento)


def erro(code, message, rc, backup=None):
    corpo = {"code": code, "message": message}
    if backup:
        corpo["backup"] = backup
    print(json.dumps({"error": corpo}), file=sys.stderr)
    return rc


def opcao(args, nome):
    for a in args:
        if a.startswith(nome + "="):
            return a[len(nome) + 1:]
    return None


def section_set(estado, args, corpo):
    pagina, sob, titulo = estado["html"], opcao(args, "--under"), opcao(args, "--heading")
    heads = headings(pagina)
    h2 = [h for h in heads if h["nivel"] == 2 and h["texto"] == sob]
    if len(h2) != 1:
        return erro("usage", f"h2 não encontrado: {sob!r}", 2)
    lo = h2[0]["fim"]
    hi = next((h["ini"] for h in heads if h["ini"] > h2[0]["ini"] and h["nivel"] <= 2), len(pagina))
    irmaos = [h for h in heads if h["nivel"] == 3 and lo <= h["ini"] < hi]
    achados = [h for h in irmaos if h["texto"] == titulo]
    if not achados and "--create" not in args:
        return erro("usage", f"heading não encontrado: {titulo!r} sob {sob!r}", 2)
    if achados:
        h3 = achados[0]
        ini = h3["fim"]
        fim = next((h["ini"] for h in heads if h["ini"] > h3["ini"] and h["nivel"] <= 3), len(pagina))
        mudou = sem_ids(pagina[ini:fim]).strip() != corpo.strip()
        novo, pos_corpo = pagina[:ini] + com_ids(corpo, estado) + pagina[fim:], ini
        criado = False
    else:
        depois = [h for h in irmaos if h["texto"] > titulo]
        pos = depois[0]["ini"] if depois else hi
        novo = pagina[:pos] + com_ids(f"<h3>{html.escape(titulo, quote=False)}</h3>" + corpo, estado) + pagina[pos:]
        mudou, criado, pos_corpo = True, True, pos
    if "--apply" not in args:
        print(json.dumps({"dry_run": True, "changed": mudou, "created": criado}))
        return 4
    if mudou:
        if estado.get("sabotar"):  # 1 byte a mais dentro do <code> do bloco guardado
            novo = novo[:pos_corpo] + novo[pos_corpo:].replace("</code>", "X</code>", 1)
        estado["html"] = novo
        estado["revision_count"] += 1
        estado.setdefault("changelogs", []).append(opcao(args, "--changelog"))
    print(json.dumps({"id": estado["id"], "name": "pagina", "revision_count": estado["revision_count"],
                      "backup": "/snap/x.json" if mudou else None, "changed": mudou, "heading": titulo,
                      "under": sob, "created": criado, "section": {"sha_after": "0" * 12}}))
    return 0


def replace(estado, args, corpo):
    if opcao(args, "--confirm") != str(estado["id"]):
        return erro("usage", "replace exige --confirm", 2)
    mudou = sem_ids(estado["html"]).strip() != corpo.strip()
    if "--apply" not in args:
        print(json.dumps({"dry_run": True, "changed": mudou, "units": {"lost": 3, "new": 5, "kept": 1},
                          "page": {"bytes_before": len(estado["html"]), "bytes_after": len(corpo)}}))
        return 4
    if mudou:
        estado["html"] = com_ids(corpo, estado)
        if estado.get("sabotar"):  # 1 byte a mais no fim da página guardada
            estado["html"] += "X"
        estado["revision_count"] += 1
        estado.setdefault("changelogs", []).append(opcao(args, "--changelog"))
    print(json.dumps({"id": estado["id"], "revision_count": estado["revision_count"], "changed": mudou,
                      "sha_normalized": "0" * 12, "backup": None}))
    return 0


def main(argv):
    caminho = os.environ["KB_FALSO_ESTADO"]
    with open(caminho, encoding="utf-8") as f:
        estado = json.load(f)
    estado.setdefault("chamadas", []).append(argv)
    args = [a for a in argv if a not in ("--target", estado.get("target", "staging"))]
    corpo = sys.stdin.read() if ("--stdin" in args or "--html=@-" in args) else ""
    chave = " ".join(args[:2])
    try:
        if chave in estado.get("falhar", {}):
            rc, code, message, backup = estado["falhar"][chave]
            return erro(code, message, rc, backup)
        if args[:2] == ["pages", "read"]:
            print(json.dumps({"id": estado["id"], "name": "pagina", "editor": "wysiwyg", "raw_html": estado["html"],
                              "html": estado["html"], "revision_count": estado["revision_count"]}))
            return 0
        if args[:3] == ["content-permissions", "read", "page"]:
            print(json.dumps(estado["permissoes"]))
            return 0
        if args[:2] == ["page", "section-set"]:
            return section_set(estado, args, corpo)
        if args[:2] == ["page", "replace"]:
            return replace(estado, args, corpo)
        return erro("usage", f"comando desconhecido: {chave}", 2)
    finally:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estado, f)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
