# Extrair uma lib de um workspace

## Antes

- **Há um segundo consumidor?** Sem ele, a lib fica no workspace: cada ajuste de API viraria release.
- **A lib já tem fronteira?** Um teste que reprova import de qualquer consumidor e saída da própria
  pasta. Se não tem, ele vem antes da extração, ainda no workspace.
- **Onde moram as libs.** Com uma segunda lib à vista, um repositório de bibliotecas em npm workspaces
  (`packages/<lib>`) custa uma pasta por lib nova; um repositório por lib repete gate, script de
  release e configuração, e as cópias divergem.

## Com o histórico

O `git blame` de cada linha deve levar ao commit que explica o porquê. Num clone **descartável** do
repositório de origem:

```bash
git clone <origem> extracao && cd extracao
# sem rede, do checkout local: git clone -q --no-local --branch <branch> --single-branch <checkout> extracao
printf '%s\n' 'regex:(?<![\w/])#([0-9]+)==><dono>/<origem>#\1' > ../mensagens.txt
git filter-repo --path packages/shared/<lib>/ \
  --path-rename packages/shared/<lib>/:packages/<lib>/ \
  --replace-message ../mensagens.txt
git log --format=%s                     # confira as mensagens reescritas
```

Uma execução faz as três coisas: guarda só os commits que tocam a lib, move a pasta para o lugar do
repositório novo e reescreve cada `#123` para `<dono>/<origem>#123`, porque no repositório novo `#123`
apontaria para uma issue que não existe ali. Medido em 2026-10-16 num repositório de prova: de três
commits, os dois da lib ficaram, com as mensagens reescritas, e o que só mexia no app saiu. O repositório
de origem não é tocado.

A regex pega `#N` em qualquer posição que não venha depois de letra, dígito, `_` ou `/`, e preserva o
que está em volta: `(#387)` vira `(<dono>/<origem>#387)`, e `PR #175` vira `PR <dono>/<origem>#175`.
Uma referência já qualificada (`<dono>/<origem>#9`) não é tocada, nem `#` de URL (`x.html#3`):
conferido em 2026-10-16 com o `re` do Python, que é o motor do `--replace-message`.

A primeira versão desta receita só reescrevia `\(#N\)`, e na extração real (**medido** em
2026-10-16, `sales_quote` → `jrc-libs`) duas das quatro referências estavam fora de parênteses
("review do PR #175", "no PR #178"). Elas teriam continuado como links para issues do repositório
novo, sem erro nenhum.

O clone a partir do checkout local, com `--no-local`, dispensa a rede, e o `filter-repo` o aceita como
clone novo. O `filter-repo` também apaga o remoto `origin` do clone (`git remote -v` sai vazio), o que
impede um push de volta à origem por engano. O push para o repositório novo vai para um remoto
acrescentado à mão (**medido**, mesma extração).

O commit de entrada cita o sha de origem, porque os commits extraídos ganham sha novo. Faça-o com um
`README.md` na raiz, **fora** de `packages/<lib>`: assim `git log -- packages/<lib>` continua contando
só os commits da origem, e a contagem serve de check.

### Antes do push

O histórico inteiro vai para outro repositório, com outro controle de acesso. Confira cinco coisas no
clone, antes de qualquer push:

```bash
# 1. os commits da lib, todos e só eles: o mesmo número dos dois lados
git log --oneline -- packages/<lib> | wc -l
git -C <origem> log --oneline <sha> -- packages/shared/<lib> | wc -l
# 2. nenhuma referência solta (vazio), e as reescritas contadas
git log --format=%B | grep -nE '(^|[^A-Za-z0-9_/])#[0-9]+'
git log --format=%B | grep -c '<dono>/<origem>#'
# 3. a árvore é a da origem: os dois hashes iguais
git rev-parse HEAD:packages/<lib>
git -C <origem> rev-parse <sha>:packages/shared/<lib>
# 4. nenhuma credencial em nenhum commit: lista arquivos, não conteúdo
for c in $(git rev-list --all); do
  git grep -IlE 'BEGIN (RSA |EC )?PRIVATE KEY|"private_key"|private_key_id|AIza[0-9A-Za-z_-]{35}|ghp_[0-9A-Za-z]{36}' "$c" -- .
done | sort -u
# 5. a lib instala e testa sozinha, fora do workspace da origem
mkdir ../prova && git archive HEAD packages/<lib> | tar -x -C ../prova
(cd ../prova/packages/<lib> && npm install && npm run typecheck && npm test)
```

- **O hash da árvore (3)** compara todos os arquivos de uma vez. Ele prova que o `filter-repo` não
  perdeu nem alterou nada, o que a contagem de commits não prova.
- **A varredura (4) se classifica lendo cada achado, nunca pela contagem.** Ajuste os padrões ao que a
  lib manuseia. Contagem alta não é vazamento, e contagem zero só diz que os padrões não casaram. Leia
  cada arquivo listado antes de concluir, e não imprima a linha inteira de um achado que pode ser
  real: o terminal também é registro. Um segredo apagado da origem num commit antigo viaja junto com
  o histórico.
- **A instalação isolada (5)** pega a dependência que a lib só tinha por estar no workspace: a
  `devDependency` içada da raiz, o `tsconfig` ou a configuração de teste de lá. Ela roda antes de
  existir o monorepo novo, a partir do `git archive`, para não deixar `package-lock.json` nem
  `node_modules` no clone.

Na extração real (**medido** em 2026-10-16), o resultado foi o seguinte:

- 11 commits dos dois lados e 4 referências reescritas.
- Árvores iguais.
- A varredura listou 28 pares de commit e arquivo, em 4 arquivos de teste. Todos eram marcadores falsos
  (`MIIsegredo`, `MIIfalso`) ou pares de chave gerados por `generateKeyPairSync` dentro do teste.
- A lib passou sozinha, com TypeScript 5.9.3: 169 testes verdes e 26 pulados, que eram o smoke que pede
  credencial.

## A cópia que fica na origem

Enquanto a origem não troca a cópia do workspace pelo pacote, o mesmo código mora em dois lugares. Um
conserto urgente feito na cópia antiga não chega à lib, e vice-versa. Congele a cópia antiga com um
`README.md` na pasta ("congelada; a fonte é `<repo>`, tag `<pacote>-vX.Y.Z`; conserto vai primeiro
para lá") e registre a troca no backlog da origem, com dono. Se a origem está em produção, a troca
segue o processo dela, com staging antes, e nunca de carona noutra mudança.

O README avisa; quem prova que ninguém mexeu é um sensor. Anote o sha da origem no momento da extração
e, antes de cada release da lib e antes da troca na origem, confira:

```bash
git -C <origem> fetch -q origin
git -C <origem> log --oneline <sha-da-extração>..origin/<branch-principal> -- packages/shared/<lib>
```

A saída tem de vir vazia. Qualquer commit ali é um conserto que a lib ainda não tem, e ele entra na lib
antes da release. Medido em 2026-10-16 num repositório de prova: um commit na pasta depois do sha base
aparece na contagem, e uma pasta intocada sai com zero.

## As decisões

As decisões da lib costumam estar em ADRs da origem, misturadas com o produto de lá. No repositório
novo, escreva ADRs próprias com só a parte genérica, citando as da origem como fonte. Uma para a
forma de distribuir e versionar todas as libs, e uma por lib. As da origem ficam lá como histórico.

## A primeira versão

Se o código já roda em produção na origem, a primeira release é `1.0.0`. O formato gravado (como a lib
persiste os dados) entra no contrato, e um teste lê uma fixture nesse formato. Mudar o formato não
quebra tipo nenhum e deixa ilegíveis os dados que a origem já gravou.
