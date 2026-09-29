# Contrato do relatório de auditoria

O relatório tem sempre estas seções, nesta ordem. Seção sem conteúdo diz "nada a relatar";
não some. Todo número traz a origem (comando e `rc`, ou arquivo e linha).

```markdown
# Auditoria de skills: <escopo> (<AAAA-MM-DD>)

## 1. Escopo e modo
- Skills: <lista de diretórios>
- Modo: simples | completa | reparo (autorização: "<frase do usuário>", allowlist: <arquivos>)

## 2. Fontes e limitações
- <fonte>: <URL ou arquivo>, consultada em <data>; <o que foi usado>
- Gates indisponíveis: <G1/G2 SKIP e motivo>
- Limitações: <rede, permissões, o que não foi verificado>

## 3. Diagnóstico por skill
| Skill | Critério | Antes | Depois | Evidência |
|---|---|---|---|---|
| <nome> | A/B/C/D/E | <achado ou "ok"> | <achado ou "ok"> | <comando, rc> |

## 4. Arquivos alterados
- <path>: <resumo em uma linha> (vazio no modo somente leitura)

## 5. Testes executados
| Comando | rc | Observado |
|---|---|---|

## 6. Dívida pré-existente e divergências
- Dívida (estava no baseline): <achado>
- Regressão nova (só depois): <achado> ou "nenhuma"
- Divergência entre fontes: <fonte A diz X, fonte B diz Y, decisão tomada>

## 7. Escopo e Definition of Done
- Arquivos fora da allowlist alterados: <nenhum | lista>
- Commit: <hash> | "não feito: <motivo>"
- DoD: <cada critério, cumprido ou não, com a evidência>
```

## Regras de preenchimento

- **Antes/depois vem do baseline da fase 1**, não da memória. Sem baseline, a coluna "Antes"
  diz "sem baseline" e nenhuma afirmação de "sem regressão" é feita.
- **SKIP não é OK.** Gate que não rodou aparece na seção 2 com o motivo.
- **Reportar o que rodou.** "Corrigi o path" é afirmação; "`audit_skill_quality.py` rc=0,
  achado B3 sumiu" é evidência.
- **Dívida fora do escopo** é relatada, não corrigida: diga onde está e o sensor que a mostra.
