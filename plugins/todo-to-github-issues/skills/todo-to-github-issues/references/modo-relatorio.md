# Relatório de achados (`ACHADOS-*.md`)

Leia antes do primeiro plano de um relatório. `$S` é o `scripts/todo_issues.py` desta skill (seção
*Comando* do `SKILL.md`).

Um arquivo com seções `### N. <título>` entra no **modo relatório** sozinho (`--format` força) —
menos um `TODO*.md`, que é sempre o backlog: sem o marcador ele vai para a recusa do sensor, e um
com marcador continua backlog mesmo com uma categoria `### 1. …`.
Relatório é fotografia datada, não backlog: quase tudo nele já fechou, e o que segue aberto foi
roteado a algum lugar que já tem issue. Por isso a unidade é a **seção**, nunca as linhas
`- [ ]` de dentro dela, e o status sai da **tabela de roteamento** (primeira tabela cuja coluna 1
é `#`, com uma coluna `Desfecho`/`Status` e, se houver, `Evidência`).

| Linha do plano | Significa | O que fazer |
|---|---|---|
| `CREATE closed` | o desfecho começa com `RESOLVIDO`/`RESOLVED`/`FIXED` | `--apply` cria a issue **e a fecha** como concluída, com desfecho e commits no topo |
| `LINK?` | achado aberto e sem destino | descubra a issue que já o acompanha (em geral, o espelho do `TODO.md`) e passe `--link N=<issue>`; só use `--open-unlinked` se não houver nenhuma |
| `COMMENT` | `--link` dado | `--apply` comenta **uma vez** na issue, com o texto em `<details>` |
| `CLOSE` | resolvido no relatório, issue aberta | `--apply` fecha (é o que sobra de uma queda entre criar e fechar) |

Seção sem número (uma "observação") entra por `--link "<começo do título>=<issue>"`; o prefixo
tem de casar com exatamente um cabeçalho. `--close-orphans` não existe neste modo: nada sai de um
relatório.

```bash
python3 $S --file ACHADOS-x.md                                     # plano
python3 $S --file ACHADOS-x.md --apply --limit 1                   # canário, SEM --link
python3 $S --file ACHADOS-x.md --apply --link 6=153 --link "Uma obs=155"
```
