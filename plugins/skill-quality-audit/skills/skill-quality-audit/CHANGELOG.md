# Changelog: skill-quality-audit

## [0.7.0] - 2026-10-20 - campo de topo aceito quando toda plataforma do plugin o lê

**Motivação:** a `release` 2.0.0 (Claude Code e Cursor) põe `disable-model-invocation: true` no
topo, para só rodar chamada pelo nome. O Claude Code e o Cursor leem esse campo só ali (doc do
Cursor: "only included when explicitly invoked via `/skill-name`"). Mesmo assim ela saía com ERRO
G2 e AVISO A4: desde a 0.5.0, campo do Claude Code só era custo aceito em plugin `["claude-code"]`.

**O que foi feito:**

- **A4 e G2:** o aceito é a interseção das listas das plataformas do `plugin.json`
  (`TOP_FIELDS_BY_PLATFORM`; `CURSOR_TOP_FIELDS` é `paths`, `disable-model-invocation`, `icon`,
  `color`). Para Claude Code + Cursor, isso dá `disable-model-invocation` e `paths`. O
  `argument-hint` segue AVISO ali, porque o Cursor o ignora. Plataforma sem lista conhecida não
  aceita nada. Só `claude-code` continua como antes. A mensagem INFO do A4 diz as plataformas.
- **Três testes novos** (54 no total), dois RED antes do código. Quatro sabotagens deixam testes
  vermelhos: união em vez de interseção, plataforma desconhecida ignorada, Cursor sem o campo e G2
  sem a lista.
- **Medido nas 31 skills do marketplace** (script do `HEAD` contra o novo): a única diferença é a
  `release`, que vai de A4 AVISO + G2 ERRO para A4 INFO + G2 INFO.
- O `scripts/validate-versions.py` do marketplace usa a mesma regra e as mesmas listas.
- `references/checks.md` (linha do A4), `references/fontes-e-decisoes.md` (a doc do Cursor nas
  fontes e a decisão 13) e a linha de *Erros comuns* do `SKILL.md`.

**Como reverter:** `git revert` do commit que traz esta entrada.

## [0.6.0] - 2026-10-18 - C2 de contrato de subagente vira INFO

**Motivação:** a tabela *Erros comuns* já mandava não "corrigir" C2 em reference que é contrato
de subagente, mas o script seguia dando AVISO. Na `codereview` (marketplace, 2.20.0), os 3 C2 eram
exatamente esse caso, as citações `{SKILL_DIR}/references/...` de `per-file-agent.md`,
`sweep-agent.md` e `detection-passes.md`, que os agentes Sonnet leem sozinhos; o aviso que nunca
devia ser seguido virava ruído em toda auditoria dela.

**O que foi feito:**

- **C2:** a citação pela raiz da skill numa variável com SKILL no nome (`{SKILL_DIR}/`,
  `${CLAUDE_SKILL_DIR}/`, `$SKILL_DIR/`; `RE_ROOT_REF`) sai do AVISO e vira INFO "contrato de
  subagente". Um arquivo citado também na forma relativa (`references/x.md`) segue AVISO.
- **Quatro testes novos** (`TestC2ContratoDeSubagente`, 51 no total), dois RED antes do código; três
  sabotagens (não tirar a raiz do relativo, não descontar o relativo do contrato, contrato como
  AVISO) deixam testes vermelhos.
- **Medido nas 30 skills do marketplace** (script do `HEAD` contra o novo, `--external off`): 101
  achados nos dois; a única diferença são os 3 C2 da `codereview`, de AVISO para INFO.
- `references/checks.md` (linha do C2) e a linha do C2 em *Erros comuns* do `SKILL.md`.
- **Dívida de changelog fechada:** o `metadata.version` dizia 0.5.0 e o primeiro cabeçalho daqui
  era 0.4.0 (divergência pela regra da `skill-claim-check` 0.5.1). As entradas 0.5.0 e 0.4.1 abaixo
  apontam para o CHANGELOG do plugin, onde o texto está.

**Como reverter:** `git revert` do commit que traz esta entrada.

## [0.5.0] - 2026-10-04 - campo de topo do Claude Code é custo aceito em plugin só `claude-code`

Registrada só no CHANGELOG do plugin (`plugins/skill-quality-audit/CHANGELOG.md`, seção 0.5.0).

## [0.4.1] - 2026-10-04 - o B5 acha o CHANGELOG do plugin

Registrada só no CHANGELOG do plugin (`plugins/skill-quality-audit/CHANGELOG.md`, seção 0.4.1).

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
