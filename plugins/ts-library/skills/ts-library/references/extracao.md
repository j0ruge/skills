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
printf 'regex:\\(#([0-9]+)\\)==>(<dono>/<origem>#\\1)\n' > ../mensagens.txt
git filter-repo --path packages/shared/<lib>/ \
  --path-rename packages/shared/<lib>/:packages/<lib>/ \
  --replace-message ../mensagens.txt
git log --format=%s                     # confira as mensagens reescritas
```

Uma execução faz as três coisas: guarda só os commits que tocam a lib, move a pasta para o lugar do
repositório novo e reescreve `(#123)` para `(<dono>/<origem>#123)`, porque no repositório novo `#123`
apontaria para uma issue que não existe ali. Medido em 2026-10-16 num repositório de prova: de três
commits, os dois da lib ficaram, com as mensagens reescritas, e o que só mexia no app saiu. O commit de
entrada cita o sha de origem, porque os commits extraídos ganham sha novo. O repositório de origem não
é tocado.

## A cópia que fica na origem

Enquanto a origem não troca a cópia do workspace pelo pacote, o mesmo código mora em dois lugares. Um
conserto urgente feito na cópia antiga não chega à lib, e vice-versa. Congele a cópia antiga com um
`README.md` na pasta ("congelada; a fonte é `<repo>`, tag `<pacote>-vX.Y.Z`; conserto vai primeiro
para lá") e registre a troca no backlog da origem, com dono. Se a origem está em produção, a troca
segue o processo dela, com staging antes, e nunca de carona noutra mudança.

## As decisões

As decisões da lib costumam estar em ADRs da origem, misturadas com o produto de lá. No repositório
novo, escreva ADRs próprias com só a parte genérica, citando as da origem como fonte. Uma para a
forma de distribuir e versionar todas as libs, e uma por lib. As da origem ficam lá como histórico.

## A primeira versão

Se o código já roda em produção na origem, a primeira release é `1.0.0`. O formato gravado (como a lib
persiste os dados) entra no contrato, e um teste lê uma fixture nesse formato. Mudar o formato não
quebra tipo nenhum e deixa ilegíveis os dados que a origem já gravou.
