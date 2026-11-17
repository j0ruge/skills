# Changelog — `prompt-cache-audit`

## [0.1.1] — 2026-11-17

### Trocar o effort não invalida o cache em todo modelo

- A 0.1.0 dizia que modelo, effort e modo rápido têm cada um o próprio cache. Para o effort isso não vale nos modelos
  mais novos, em que a troca mantém o cache. O item 4 de "O que decidir" agora separa os casos e aponta a seção
  "Actions that invalidate the cache" da página de cache do Claude Code, lida em 2026-11-17, em vez de fixar a lista
  de modelos.
- Achado ao conferir na própria página as afirmações da 0.1.0 sobre terceiros, o que não tinha sido feito antes de
  publicar.

## [0.1.0] — 2026-11-17

### Primeira versão: medir o cache de prompt antes de mexer nele

- `scripts/cache_audit.py` lê os transcritos locais do Claude Code e mostra, por modelo, quanto da entrada veio do
  cache; por conversa principal e por subagente, o TTL das escritas, as quedas de cache pela causa (pausa de mais de
  1h, pausa de 5 min a 1h, troca de modelo, prefixo mudado) e o tamanho do contexto por pedido.
- A conta do TTL: o script diz se trocar 5 min por 1h compensa, pelo limiar de reescrita, com os multiplicadores
  como opção de linha de comando.
- O roteiro para o código que chama a API direto: achar as chamadas, medir pelos campos de `usage`, separar o
  estável do variável, procurar o que invalida em silêncio e fechar com a conta em dinheiro.
- A skill começa por separar os dois tráfegos: o aviso de taxa de acerto baixa fala da API direta, não do Claude
  Code.
