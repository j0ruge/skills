# Changelog: skill-quality-audit

## [0.4.0] - 2026-09-29 - entra no marketplace com as irmãs

**Motivação:** a família vira o plugin `skill-quality-audit` do marketplace, que passa a ser a
fonte oficial; o harness Hermes do autor lê essa cópia por `skills.external_dirs`.

**O que foi feito:**

- Descrição no padrão do marketplace (função e gatilho nos primeiros 60 chars, linha
  `Triggers —`, até 350); decisão 2 atualizada e decisões 11 e 12 em `fontes-e-decisoes.md`.
- E1: sem bloco `metadata` (o instalador do Cursor o remove), vínculo ausente vira INFO em vez de
  AVISO. Testes `TestFamiliaNoPlugin` (2 casos, 38 no total): as quatro no layout de plugin se
  acham sem Hermes, e a irmã sem `metadata` não reprova `--strict`.
- `SKILL.md`: parágrafo sobre as quatro no mesmo plugin; portabilidade aponta o marketplace como
  fonte; o gate G1 descrito como gate local de um harness Hermes.
- `assets/trigger-evals.json` anonimizado, com um caso novo de entrada no marketplace.

**Como reverter:** `git revert` do commit que traz esta entrada.

> As entradas abaixo são da cópia no harness de origem, antes do marketplace; os commits que
> elas citam estão no repositório de lá.

## 2026-09-29 - v0.3.0: segue o padrão que audita (autor, validador oficial, gotchas da sessão)

**Commit:** registrado no commit que traz esta entrada (ver `git log -- skills/devops/skill-quality-audit`).

**Motivação:** revisão da própria skill contra a spec agentskills.io e as lições da correção de
93 skills do Hermes e 20 do marketplace (2026-09-28). Faltavam `metadata.author`, o validador
oficial nunca rodava (G2 sempre SKIP), os gotchas não tinham as correções da sessão e dois falsos
positivos seguiam abertos (A1 em lista de mappings, B6 em `__pycache__` ignorado pelo git).

**O que foi feito:**

- Frontmatter com `metadata.author: JorUge` e `metadata.version`.
- G2: sem `skills-ref`/`agentskills` no PATH, roda `uvx --from skills-ref==0.1.1 agentskills`;
  `--no-uvx`/`SQA_NO_UVX` desliga.
- A1: o parser lê lista de mappings (ex.: `required_credential_files`).
- B6: lixo ignorado pelo git vira INFO.
- "Erros comuns" com 5 linhas novas (campos funcionais do Hermes no topo, `$HERMES_HOME/scripts`,
  C2 em contrato de subagente, SKIP do G2, `__pycache__`); F1 da `matriz-avaliacao.md` resolvido.
- Testes: `TestLicoesDe20260928` (3 casos, 36 no total); suíte hermética com `SQA_NO_UVX=1`.
- `checks.md` (A1, B6, G2) e `fontes-e-decisoes.md` (decisões 9 e 10).

**Como reverter:** `git revert` do commit.

## 2026-09-28 - v0.2.2: placeholders `{X}/`/`${X}/` e módulos Python sem shebang

**Commit:** registrado no commit que traz esta entrada (ver `git log -- skills/devops/skill-quality-audit`).

**Motivação:** falsos positivos achados na correção das skills do marketplace: script citado
como `{SKILL_DIR}/scripts/x.py` virava órfão (B2), e módulo importado por outro script (sem
`__main__`, sem argparse, modo 644) levava AVISO B7 por falta de shebang e INFO F3 por falta de
`--help`.

**O que foi feito:** o normalizador aceita `{X}/`, `${X}/` e `$X/` como raiz da skill quando a
variável tem SKILL no nome (`SKILL_DIR`, `CLAUDE_SKILL_DIR`); a primeira versão aceitava qualquer
variável e transformava `$HERMES_HOME/scripts/x.sh`, que é o harness, em B2 falso (corrigido no
mesmo dia, com teste);
`is_module()` isenta módulos Python do shebang (B7) e do `--help` (F3). Testes
`TestPlaceholdersEModulos`; `checks.md` atualizado.

**Como reverter:** `git revert` do commit.

## 2026-09-28 - v0.2.1: A4 separa campo funcional do Hermes de campo morto

**Commit:** registrado no commit que traz esta entrada (ver `git log -- skills/devops/skill-quality-audit`).

**Motivação:** depois da normalização das skills do JorUge, o A4 restante era só `platforms`, que
fica no topo de propósito (o Hermes filtra por SO só por ele). Um AVISO sem correção possível
treina a ignorar o A4 inteiro.

**O que foi feito:** `HERMES_TOP_FIELDS` (`platforms`, `required_credential_files`,
`required_environment_variables`, `prerequisites`) sai do AVISO e vira INFO no A4; os demais
campos fora da spec continuam AVISO. Teste `TestCamposHermesNoTopo`; `checks.md` atualizado.

**Como reverter:** `git revert` do commit.

## 2026-09-28 - v0.2.0: checks de boas práticas do agentskills.io (A8, F1 a F4)

**Commit:** registrado no commit que traz esta entrada (ver `git log -- skills/devops/skill-quality-audit`).

**Motivação:** a skill cobria o texto normativo da spec (A1 a A7, C1 a C3), mas não as páginas de
autoria do agentskills.io (best practices, using-scripts, evaluating-skills), lidas nesta
data. Faltavam sensores para `metadata` texto→texto, "diga quando ler cada
reference", seção de gotchas, script interativo ou sem `--help` e ausência de evals.

**O que foi feito:**

- `scripts/audit_skill_quality.py`: A8 (`metadata` precisa ser mapa; valor que não é texto vira
  AVISO, `metadata.hermes` vira INFO); F1 (reference sem condição de leitura), F2 (sem gotchas),
  F3 (AVISO para `input()`/`getpass()` pela AST ou `read -p`; INFO sem `--help`), F4 (sem evals).
  A4 agora sugere `metadata.author` e `metadata.version`.
- `tests/`: classe `TestBoasPraticas`, 5 casos (29 no total, todos OK).
- `references/checks.md`: linha A8 e seção F. `references/fontes-e-decisoes.md`: reconferência
  da spec e do `validator.py` em 2026-09-28 e decisões 7 (autor em `metadata.author`,
  `platforms` fica no topo) e 8 (boas práticas como INFO).
- `SKILL.md`: cita F1 a F4 e diz quando ler `checks.md` e `fontes-e-decisoes.md`.

**Como reverter:** `git revert` do commit; a v0.1.0 continua funcional sozinha.

## 2026-09-23 - v0.1.0: criação inicial

**Commit:** pendente (não commitado nesta sessão; registrar o hash quando houver).

**Motivação:** as skills `skill-self-containment`, `skill-claim-check` e `skill-refactoring`
cobriam estrutura, veracidade e tamanho, mas nenhuma dizia em que ordem aplicá-las, quem decide
cada parte, quando parar, nem como relatar. Faltava uma porta de entrada única, portátil, capaz
de rodar mesmo num harness sem as três.

**O que foi feito:**

- `SKILL.md` com modos simples, completa e reparo (somente leitura por padrão), sequência fixa
  de 5 fases, tabela de interfaces com as irmãs e regras anti-loop (só esta skill sequencia;
  teto de 2 ciclos de reparo).
- `scripts/audit_skill_quality.py`: auditoria determinística, só biblioteca padrão, somente
  leitura, checks A1 a G2, saída texto ou JSON, `rc` 0/1/2, gates externos opcionais com SKIP.
- `tests/test_audit_skill_quality.py`: casos válidos, inválidos, cópia fria e paridade dos
  padrões de afirmação com a irmã `skill-claim-check`.
- References: `checks.md`, `fluxo-completo.md`, `contrato-relatorio.md`, `matriz-avaliacao.md`,
  `fontes-e-decisoes.md`; asset `trigger-evals.json`.

**Revisão adversarial (mesmo dia, antes de commit):** revisor em sessão nova achou 1 bloqueante
e 12 menores. Corrigidos: B4 não via path entre crases; parser engolia o frontmatter com aspas
seguidas de comentário e aceitava `: ` em valor sem aspas (agora ERRO A1); `SKILL.md` fora de
UTF-8 passava (agora ERRO A1); G2 não achava o comando `agentskills` do pacote PyPI; A5 virou
ERRO; B1 enxerga subpastas; B3 mede profundidade (reference com `../scripts` deixa de ser falso
positivo; `scripts/` entram como AVISO); blocos `~~~` fora do D1; timeouts viram AVISO; teste
frio exige `env -u HERMES_HOME`; delegação em modo somente leitura explicitada; descrição trocada
por "Use when auditar skills contra spec, autocontenção e claims." (60 chars). Cada bug virou
teste (8 novos). Registrado, não corrigido: G1 repete achado local (documentado em `checks.md`).

**Verificação:** `python3 tests/test_audit_skill_quality.py` rc=0 em Python 3.11.15 e 3.12.3
(2026-09-23); cópia fria com `env -u HERMES_HOME`: `--family` rc=0 com irmãs em SKIP.

**Como reverter:** remover o diretório `skills/devops/skill-quality-audit/` (mover para a
lixeira com `trash` ou `gio trash`) e as linhas desta skill no índice do harness. As irmãs continuam
funcionando sozinhas; só perdem o ponteiro para a porta de entrada.
