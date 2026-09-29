# Estudo de caso: refatoração de uma skill de monitoramento (Jun a Jul/2026)

A skill operava um sistema de terceiro por API e por scripts próprios. Movido do corpo do `SKILL.md` em 2026-09-23 para manter o gatilho da skill por
família e o corpo como workflow. Os números são medições daquela época, não limites.

## Métricas

| Métrica | Antes | Após refatoração | Um mês depois |
|---|---|---|---|
| Linhas SKILL.md | 1.677 | 240 | 235 |
| Chars SKILL.md | 72.663 | 9.849 | 11.593 |
| Arquivos references/ | 0 | 8 | 13 |
| Scripts operacionais | 1 (poller) | 3 | 4 |
| Lições de sanitização | ❌ | ✅ | ✅ + incidentes reais |

Skills crescem depois da refatoração (novas lições, novos scripts); aqui o crescimento veio de
lições de incidentes reais. Na sua skill, meça com `wc -l -c SKILL.md` antes e depois.

## Regras de script que vieram deste caso (API de terceiro)

Específicas do domínio; não são regra geral de refatoração. Conferir na documentação da versão
da API em uso antes de reaproveitar.

- Lote por chamada, com o tamanho medido naquela API e versão (não reaproveitar o número sem
  medir de novo).
- Fallback para consulta direta ao banco quando o usuário da API não tem permissão para a
  leitura.
- Scripts que desativam recursos ganham um modo pós-ação (ex.: `--post-action`) para limpar o
  estado residual que a ação principal não fecha.
- Credenciais: só por variável de ambiente ou `.env`, nunca no script nem em argumento.
