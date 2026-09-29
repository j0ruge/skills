# Skill Compression — Teste 0 (Karpathy Loop)

**Data:** 2026-07-11
**Contexto:** Primeiro experimento do Loop Karpathy no harness do autor (Hermes Agent). Duas iterações: v1 (extração pura) falhou, v2 (compressão estrutural) funcionou.

> **Nota de verificação (2026-09-23):** registro histórico. Na CLI atual (`hermes skills --help`)
> não existe `rebuild`, e `hermes skills check` verifica atualização de skills instaladas pelo hub,
> não se uma skill funciona. Para validar uma skill hoje: a skill `skill-quality-audit` (estrutura);
> para o comportamento, rodar um prompt real com a skill carregada.

## v1 — Extração de Funções (❌ FALHOU)

**Alvo:** skill de instalação de agente de segurança (738 linhas)
**Abordagem:** Extrair funções reutilizáveis (`check_venv_and_deps`, `run_agent_install`, `validate_os_compatibility`, `report_status`) para um arquivo separado (~120 linhas) e manter só referências no SKILL.md.

**Resultado:** o agente respondeu que não tinha informação sobre quais passos de instalação o ambiente exigia — perdeu completamente o conhecimento sobre a instalação.

**Causa raiz:** Skills carregam contexto via exemplos + instruções de **como e quando** usar cada bloco. Extrair funções removeu a narrativa de execução — o modelo ficou com verbos soltos sem saber encadeá-los.

**Rollback:** Revertido com `git stash pop` + `python -m hermes.bootstrap` (antes de `hermes skills rebuild`).

## v2 — Compressão Estrutural (✅ FUNCIONOU)

**Alvo:** skill de troubleshooting do agente (758 linhas)
**Abordagem:** Converter bash blocks longos com comentários e parágrafos descritivos para **tabelas Markdown**. Pitfalls preservados integralmente.

**Resultado:** 758 → 569 linhas (-24.9%). `hermes skills check` passou. Skill funcional.

**Técnica detalhada por seção:**
| Seção | Antes | Depois | Técnica |
|-------|-------|--------|---------|
| A (Audit) | ~77 linhas, 7 bash blocks | ~20, 1 tabela | Comandos + descrições → células |
| B (Secure Ops) | ~64 linhas, regras em bullet longo | ~24, tabela única | 6 regras + 4 pitfalls → tabela |
| C (Health Check) | ~59 linhas, 5 bash blocks | ~18, tabela | Passos com descrições → tabela |
| D (Update Audit) | ~88 linhas, fases com descrições | ~32, tabela | 7 fases c/ bash blocks → tabela |

## Lições para skills futuras

1. **Nunca extrair funções** — o contexto narrativo é mais importante que código enxuto
2. **Compressão por tabelas é o caminho** — mantém contexto, reduz linhas, legível
3. **Pitfalls são sagrados** — carregam experiência prática, não comprimir
4. **Seções separáveis comprimem melhor** — skills monolíticas são mais difíceis
5. **Merge de skills relacionados** pode ser melhor que compressão pura (ex: agente de segurança + firewall + monitor = skill único de segurança)
