---
name: skill-claim-check
description: "Garante que o que uma skill afirma continue verdade. Número, limite, path, flag ou versão ganham sensor, derivação ou data; ausência na doc não prova; skill fora do git é trabalho perdido. Fase 2 da skill-quality-audit. Triggers — editar SKILL.md, escrever reference, documentar limite, skill desatualizada, fato que apodreceu, afirmação sem fonte."
metadata:
  author: JorUge
  version: "0.4.0"
  hermes:
    tags:
      - skills
      - claims
      - sensores
      - veracidade
    related_skills:
      - skill-quality-audit
      - skill-self-containment
      - skill-refactoring
---

# Claim check — o que uma skill afirma precisa continuar verdade

Uma skill não é código: é um conjunto de **afirmações sobre um sistema**. Código
que envelhece quebra e alguém percebe. Afirmação que envelhece continua legível,
continua plausível, e é obedecida — errada — até que alguém tropece no assunto
por outro motivo.

Esta skill cobre a **veracidade** do que você escreve. As vizinhas cobrem o resto:

| Preocupação | Onde |
|---|---|
| Processo: intenção → rascunho → eval → melhoria | skill `skill-creator` |
| Estrutura: ≤500L, refs/scripts citados, paths que escapam da skill, CHANGELOG | script da skill `skill-quality-audit` (auditoria simples) |
| **Veracidade e durabilidade das afirmações** | **esta skill** |
| Autocontenção: dependências externas, portabilidade | skill `skill-self-containment` |
| Auditoria completa: ordem das fases, reparo autorizado, relatório | skill `skill-quality-audit` (porta de entrada; esta skill é a fase 2 dela) |

## As seis regras

### 1. Toda afirmação factual nomeia seu sensor

Número, caminho, limite, flag, versão ou comportamento vêm acompanhados de
**como reconferir**: um comando, um `arquivo.py:símbolo`, ou uma URL.

Sem sensor, quem lê daqui a seis meses tem duas opções ruins: acreditar (e talvez
errar) ou reinvestigar do zero (e o custo que a skill existia para evitar volta
inteiro). Com sensor, a terceira opção existe: conferir em segundos.

Se você não consegue nomear o sensor, isso é informação — provavelmente você não
sabe o fato tão bem quanto parecia. **Descreva o sensor em vez do valor.**

### 2. Prefira a derivação ao valor

Quando o sistema **calcula** algo, descreva o cálculo. Um resultado de medição
vira constante chumbada e apodrece na primeira mudança de código.

> ❌ *"Cada arquivo de contexto é limitado a 20.000 caracteres."*
>
> ✅ *"O cap vem de `_get_context_file_max_chars` (`agent/prompt_builder.py`):
> `context_file_max_chars` do config vence; senão `context_length × 4 × 0.06`,
> limitado a [20k, 500k]. Sensor: `grep TRUNCATED` no log."*

O caso real (2026-08-28, código do Hermes Agent, que é aberto): a primeira forma estava
escrita numa reference da skill `hermes-agent`. Os 20.000 são o **piso**, não o cap — para a janela em uso o cap
real passava de 60 mil. Quase apararam um `AGENTS.md` de 27 KB por causa de um
truncamento que não estava acontecendo. A segunda forma teria sobrevivido, porque
descreve o mecanismo em vez do resultado de uma medição.

O sinal de alerta é você **medir** para escrever. Se mediu, a skill deve dizer o
que você mediu, quando, e com qual comando — ou, melhor, descrever a fórmula.

### 3. Ausência não é prova

Um recurso não estar na skill **não** é evidência de que não existe. Skill é
recorte, não inventário.

Antes de qualquer resposta negativa — *"o Hermes não tem isso"*, *"essa flag não
existe"* — vá ao sensor. É barato e evita a pior categoria de erro: negar com
confiança algo que existe, apoiado num documento que só não mencionava.

Skills que documentam sistema de terceiro devem carregar uma seção curta de
**Escopo & Verificação** com os alvos concretos (o `--help`, o arquivo-fonte, a
URL dos docs), para quem ler saber onde confirmar sem perguntar.

### 4. Skill não versionada não é skill

Antes de escrever, confirme que o diretório está sob controle de versão:

```bash
git -C <repo> check-ignore -v <caminho/da/skill>   # exit 1 = OK, não ignorado
```

Um diretório ignorado transforma edição em trabalho perdido: nenhum erro, nenhum
aviso, e o `git status` fica limpo justamente porque nada está sendo visto.

O caso real (2026-08-28): `.gitignore` com `hermes-agent/` — **sem barra
inicial**. Padrão sem âncora casa em **qualquer profundidade**, então a regra
escrita para o código-fonte na raiz também engolia
`skills/autonomous-ai-agents/hermes-agent/`, a skill que o `CLAUDE.md` declara
fonte de verdade. Todas as correções feitas nela nunca foram commitadas. O mesmo
padrão comeu o `assets/<template>.md` de outra skill.

Rode o comando acima antes de commitar; a fase 0 da auditoria completa da `skill-quality-audit`
faz a mesma checagem.

### 5. Fato volátil leva data e proveniência

Contagens, tamanhos, versões de terceiro e "hoje o comportamento é X" mudam sem
avisar. Escreva **quando** e **como** foi medido:

> *"medido em 2026-08-28: 1.280 linhas na tabela `pedidos` — `SELECT COUNT(*) FROM pedidos`"*

Isso não é burocracia: é o que permite a quem lê decidir se confia ou remede, sem
ter que descobrir sozinho que o número tem seis meses.

### 6. “Script funcional” exige execução segura

Auditoria estrutural (`audit_skill_quality.py`, gate do harness), `git check-ignore` e validação documental provam propriedades estruturais; não provam que um script executa o comportamento que a skill afirma. Para qualquer script novo ou alterado, valide o artefato no seu interpretador real, confira a permissão de execução quando o executor depender dela e exercite pelo menos um caso válido e um caso inválido sem envio, publicação, exclusão ou alteração externa.

Para um script shell:

```bash
bash -n scripts/<meu-script>.sh
if [ -x scripts/<meu-script>.sh ]; then echo EXECUTAVEL; else echo "🔴 sem bit executável"; exit 1; fi
scripts/<meu-script>.sh --caso-valido   # esperado: saída/rc documentados
scripts/<meu-script>.sh --caso-invalido # esperado: recusa explícita, normalmente rc != 0
```

Para um script Python:

```bash
python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])' scripts/<meu-script>.py   # sem gravar __pycache__
python3 scripts/<meu-script>.py --caso-valido
python3 scripts/<meu-script>.py --caso-invalido
```

Em wrappers híbridos, valide cada camada separadamente: `bash -n` só valida o shell e não detecta sintaxe inválida em Python embutido; o `ast.parse` não valida o fluxo shell. Se o teste precisar de uma fonte externa, prefira fixture, sandbox, `--dry-run` ou uma consulta read-only. Para teste temporário, use arquivo com prefixo identificável, registre `rc` e resultado observado e remova-o ao finalizar.

**Sensor do claim:** comando executado + `rc` + artefato observado. “Compilou”, “passou no audit” ou “o scheduler aceitou” não substituem a execução do caminho principal e do caso negativo.

## Cheiros de apodrecimento, e o conserto

| Cheiro | Por que apodrece | Conserto |
|---|---|---|
| Número redondo sem fonte (*"o limite é 20.000"*) | o sistema pode derivar, e você congelou | descreva a derivação (regra 2) |
| Caminho absoluto de uma máquina (`/home/<user>/...`) | não existe na próxima | caminho relativo à skill, ou variável do harness (`$HERMES_HOME`, `${CLAUDE_SKILL_DIR}`) |
| Versão fixa (*"funciona na v1.3.22"*) | vira falso em silêncio | *"validado na v1.3.22; confira com `<cmd> --version`"* |
| *"sempre"* / *"nunca"* sobre sistema de terceiro | você não controla o outro lado | diga o que **foi observado**, quando, e como reconferir |
| Passo a passo sem comando de verificação | quem segue não sabe se deu certo | acrescente o sensor do resultado esperado |
| Lista fechada que o sistema gera (tabelas, campos) | nasce desatualizada | aponte o comando que lista, não a lista |

## Ferramenta

`scripts/listar-afirmacoes.sh <dir-da-skill>` varre `SKILL.md` e
`references/*.md` e imprime, com número de linha, os trechos com cara de
afirmação factual — números com unidade, caminhos absolutos, versões, flags.
A `skill-quality-audit` tem o mesmo scanner (`--claims`, check D1), com paridade
de linhas coberta pelo teste dela.

Ela **não reprova nada**: é lista para julgamento, não gate. Muitos achados serão
legítimos. O valor está em olhar cada um e perguntar *"qual é o sensor disto?"* —
a pergunta que esta skill inteira existe para provocar.

```bash
bash scripts/listar-afirmacoes.sh <dir-da-skill>         # qualquer layout ou harness
bash scripts/listar-afirmacoes.sh devops/minha-skill     # layout <cat>/<skill> do Hermes, sob $HERMES_HOME/skills
bash scripts/listar-afirmacoes.sh --help
```

## Checklist antes de commitar uma skill

1. `git check-ignore -v <dir>` → exit 1 (não ignorado)
2. Auditoria simples da `skill-quality-audit` (`audit_skill_quality.py <dir>`) → `rc=0`; sem ela
   instalada, o gate estrutural do seu harness ou o checklist final da `skill-self-containment`
3. `listar-afirmacoes.sh` rodado, e cada afirmação tem sensor ou virou derivação
4. Fatos voláteis com data e comando de medição
5. Se a skill documenta sistema de terceiro: tem seção de Escopo & Verificação
6. Para cada script novo/alterado: validar o interpretador real (`bash -n` ou `ast.parse` do Python)
7. Se o executor exigir: confirmar `test -x`; testar um caso válido e um inválido em modo seguro
8. Em wrapper híbrido: validar shell e linguagem embutida separadamente
9. Registrar comando, `rc` e artefato observado; limpar temporários

## Erros comuns

| Erro | Correção |
|---|---|
| Tratar a saída do `listar-afirmacoes.sh` como reprovação | é lista para julgamento; muitos achados são legítimos, a pergunta é "qual é o sensor?" |
| Escrever o valor que você mediu | descrever a fórmula ou o mecanismo (regra 2); se tiver que ficar o valor, com data e comando (regra 5) |
| Negar um recurso porque a skill não o menciona | ir ao sensor antes (regra 3) |
| "Passou na auditoria" como prova de que o script funciona | auditoria prova estrutura; executar caso válido e inválido (regra 6) |
| Editar skill num diretório que o git ignora | `git check-ignore -v` antes da primeira edição (regra 4) |

## Avaliar esta skill

Casos de gatilho (deve e não deve disparar, com quase-acertos das irmãs) em
`assets/trigger-evals.json`, no formato de eval set do `skill-creator`. Antes de rodar com LLM,
leia os critérios na matriz de avaliação da `skill-quality-audit`.

## Relação com outras skills

As quatro vêm no mesmo plugin (`skill-quality-audit`) e se acham como pastas vizinhas.

- **`skill-quality-audit`**: auditoria da skill inteira (estrutura, afirmações, tamanho e
  vínculos, nessa ordem) ou de várias skills. Esta skill é a fase 2 dela: vindo de lá, dê os
  vereditos e devolva o controle.
- **`skill-self-containment`**: caminho absoluto e dependência externa, um dos cheiros de
  apodrecimento, são o assunto dela.
- **`skill-refactoring`**: ao mover texto para references, as afirmações vão junto e continuam
  precisando de sensor.

## Aplicando a si mesma

As afirmações desta skill têm sensor: o cap dinâmico está em
`agent/prompt_builder.py`, função `_get_context_file_max_chars`; o padrão de
gitignore se confirma com `git check-ignore -v`; os checks estruturais estão no
`checks.md` das references da `skill-quality-audit`. Os dois casos reais são de
2026-08-28 e estão no histórico do `CHANGELOG.md` desta skill.

Se algum destes ponteiros não resolver mais, é esta skill que apodreceu — e o
conserto é o mesmo que ela pede de todo mundo.
