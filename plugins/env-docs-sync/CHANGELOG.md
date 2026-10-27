# Changelog — env-docs-sync

## [0.1.0] — em construção

Primeiro incremento: o esqueleto do plugin e o núcleo puro, com testes offline. Ainda não há hook,
destino kb nem Sync remoto, e o plugin ainda não está no catálogo da loja.

### Por quê

A página que documenta os ambientes de um projeto, com o conteúdo dos `.env*`, é mantida à mão e
envelhece: arquivos novos ficam de fora, valores mudam e ninguém atualiza. O plugin vai manter a
página sozinho, a partir de gatilhos do Claude Code e do Codex. O núcleo vem primeiro, sem rede,
para que hook, destino e ssh se encaixem por injeção e sejam testados um a um.

### Added

- **`scripts/env_docs_sync.py`, núcleo puro** (só biblioteca padrão):
  - config validada campo a campo, com todos os erros de uma vez e sem default silencioso;
  - Varredura por `include`/`exclude`, com piso de exclusão fixo, poda de outro checkout e
    symlink só para dentro da raiz;
  - sha256 dos bytes;
  - Bloco de arquivo (`<pre>` com o conteúdo escapado e a linha "sincronizado em … · commit …"),
    o inverso dele para conferir o hash relido, e o callout "ausente desde";
  - plano de operações `criar`/`trocar`/`marcar_ausente` em ordem fixa, que ignora ambiente não
    lido na rodada;
  - aplicação que para na primeira falha e registra só o que o destino aceitou;
  - estado 0600, atômico, que só aceita hashes e carimbos;
  - a Página de ambientes inteira a partir do template, para a migração por `replace`.
- **CLI mínima:** `validate`, `scan`, `plan`, `sync --to-dir` (destino local de teste) e
  `render-page`. Nenhum subcomando imprime valor.
- **`assets/ambientes-template.html`**: o template genérico da Página de ambientes.
- **`assets/env-docs.example.json`**: uma config fictícia completa.
- **`references/config.md`**: o schema da config, campo a campo, e o formato do estado.
- **`tests/`** (unittest, sem rede):
  - config, Varredura, Bloco de arquivo, plano, estado, página e CLI;
  - o canário, que chega ao destino e a nenhum outro lugar;
  - o sensor que reprova marcas da empresa de origem no pacote, provado vermelho numa cópia
    sabotada.
