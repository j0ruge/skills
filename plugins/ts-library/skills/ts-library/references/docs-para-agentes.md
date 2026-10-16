# Documentação para agentes

## Onde ela mora

**Dentro do pacote**, no `files`: `README.md` e `AGENTS.md`. O agente que trabalha no consumidor lê a
documentação da versão **instalada** em `node_modules/<pacote>/`, e não a da branch principal da lib,
que pode estar à frente. É o padrão de pacotes como o `next` (documentação em
`node_modules/next/dist/docs/` e um `AGENTS.md` no projeto apontando para ela) e os `@mysten/*`
(`docs/llms-index.md` em cada pacote).

O `llms.txt` é convenção de **site** (um índice na raiz do domínio). Ele não substitui a documentação
no pacote.

O consumidor fecha o circuito com uma linha no `CLAUDE.md` (ou `AGENTS.md`) dele: "antes de mexer em
storage, leia `node_modules/@org/object-storage/AGENTS.md`".

## `README.md`: para quem decide usar

1. o que a lib faz, em uma frase, e o que ela **não** faz;
2. instalação, com a forma de distribuição da organização;
3. o contrato: cada operação, o que devolve e o que lança;
4. uma tabela por implementação ou driver: o que cada um garante e o que não garante;
5. as variáveis de ambiente, com o que acontece quando faltam;
6. os erros, com o `code` estável de cada um (a tabela é comparada com o tipo exportado por teste);
7. exemplos em blocos `typescript` que compilam na `typecheck`;
8. como o consumidor roda a suíte de contrato contra o próprio adapter.

## `AGENTS.md`: para quem vai escrever código com ela

Curto, em regras, **cada uma com o porquê**. Um agente segue melhor uma regra cujo motivo entende, e
sabe quando ela não se aplica. Do caso medido (uma lib de storage sobre Google Drive):

- nunca dar default à variável que escolhe o driver: um default silencioso grava dado de produção no
  disco do container;
- guardar o `handle` que a gravação devolve: no Drive, a busca por key logo após gravar falhou 9 em 10
  vezes, e a leitura pelo handle, 0 em 10;
- nunca compor nem interpretar o `handle`: ele é do driver e muda com ele;
- o purge definitivo só para objeto descartável: no Drive, o delete normal vai para a lixeira e é a
  janela de recuperação;
- traduzir o erro da lib na borda da aplicação, pelo `code`;
- não chamar o storage dentro de uma transação do banco: a chamada lenta prende a conexão do pool.

## Erros com código estável

Toda classe de erro carrega `readonly code` de uma união exportada (`OBJECT_NOT_FOUND`,
`STORAGE_UNAVAILABLE`…). Agente e consumidor tratam pelo `code`, nunca pela mensagem, que muda. A
mensagem cita o valor ofensor e a forma esperada, e nunca o valor de um segredo.

## O que não fazer

Uma skill separada que ensina a **API** da lib é uma segunda cópia da documentação, presa à versão da
skill e não à instalada, e diverge. A skill fala de **como fazer libs**. A API mora no pacote.
