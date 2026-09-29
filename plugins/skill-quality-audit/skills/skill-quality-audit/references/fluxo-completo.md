# Fluxo completo: comandos, entradas, saídas e fallback

Variáveis usadas abaixo (exemplos, não caminhos fixos):

- `SQA`: diretório desta skill (onde está este arquivo, um nível acima).
- `ALVO`: diretório da skill auditada.
- `BASE`: diretório temporário para baseline, por exemplo `$(mktemp -d)`.

## Fase 0: escopo e modo

1. Listar as skills-alvo e o modo (simples, completa, reparo).
2. Reparo só com autorização explícita e allowlist de arquivos. Sem isso, seguir somente leitura.
3. Conferir versionamento do alvo: `git -C "$ALVO" check-ignore -v .` devolve `rc=1` se não
   ignorado, `rc=0` com a regra culpada se ignorado, `rc=128` fora de Git. Diretório ignorado
   perde a edição em silêncio.
4. Procurar skill com o mesmo nome antes de criar ou copiar:
   `find <raiz-das-skills> -name SKILL.md -path '*/<nome>/*'`.

## Fase 1: baseline estrutural e autocontenção

```bash
find "$ALVO" -type f | sort > "$BASE/arquivos.txt"
find "$ALVO" -type f -exec sha256sum {} + | sort -k2 > "$BASE/hashes.txt"
wc -l "$ALVO/SKILL.md"
python3 "$SQA/scripts/audit_skill_quality.py" "$ALVO" --format json > "$BASE/antes.json"; echo "rc=$?"
```

Saída: `antes.json` (achados A, B, C, G por ID) e hashes. Guardar antes de editar qualquer coisa:
é o que separa dívida pré-existente de regressão nova na fase 5.

Com `skill-self-containment` presente, ela decide o que vendorizar e o que é exceção legítima.
Sem ela, checklist B:

- [ ] Todo arquivo citado existe dentro da skill; todo arquivo presente é citado.
- [ ] Nenhum path sobe para fora da skill; nenhum path de máquina de usuário.
- [ ] Dependência externa só se for credencial fora do repo, infra compartilhada do harness
      documentada, skill irmã opcional ou URL oficial de download.
- [ ] Scripts de uso da skill vivem em `scripts/` dela; estado e testes também ficam dentro.
- [ ] `CHANGELOG.md` presente quando o harness exige.

## Fase 2: claims

```bash
python3 "$SQA/scripts/audit_skill_quality.py" "$ALVO" --claims --external off
```

Para cada trecho listado, um veredito numa tabela `arquivo:linha | afirmação | veredito | sensor`:
`tem sensor` (comando, `arquivo:símbolo` ou URL), `derivar` (descrever a fórmula em vez do valor),
`datar` (fato volátil ganha data e comando de medição), `remover`. A lista é heurística: afirmações
sem número também contam (comportamento, "a flag X existe"), então ler o corpo inteiro.

Com `skill-claim-check` presente, ela é a dona dos vereditos. Sem ela, checklist D:

- [ ] Todo número, limite, path, flag, versão ou comportamento tem sensor, fonte ou fórmula.
- [ ] Fato volátil tem data e proveniência.
- [ ] Nenhuma resposta negativa apoiada só em ausência na documentação.
- [ ] Claims sobre ferramentas externas não são mais fortes que a evidência local.

## Fase 3: progressive disclosure

Entrar só com achado C1, C2 ou C3, ou com inventário, incidente ou caso de uma instância no
corpo do `SKILL.md`. Com `skill-refactoring` presente, ela decide entre extrair para references
e comprimir por estrutura. Sem ela, checklist C:

- [ ] `SKILL.md` é índice leve com o workflow default; detalhe em references focadas.
- [ ] References a um nível do `SKILL.md`, cada uma citada com o momento de ler.
- [ ] Reference acima de 300 linhas tem sumário.
- [ ] Narrativa essencial (como e quando encadear passos) fica no `SKILL.md`; não trocar por
      funções soltas.

## Fase 4: integração e portabilidade

1. Vínculos: `python3 "$SQA/scripts/audit_skill_quality.py" --family` e ler os achados E1.
   `related_skills` em lista de bloco (não `[a, b]`): o Hermes lê as duas formas, o
   `skills-ref` só aceita a de bloco.
2. Teste frio: a skill sozinha, sem irmãs e sem o home do harness.

```bash
FRIO=$(mktemp -d)
cp -r "$ALVO" "$FRIO/"
env -u HERMES_HOME HOME="$FRIO" python3 "$SQA/scripts/audit_skill_quality.py" \
  "$FRIO/$(basename "$ALVO")" --external off; echo "rc=$?"
```

Para testar a própria `skill-quality-audit` fria, copiar `SQA` e chamar o script da cópia com
`--family`: irmãs ausentes precisam sair como `[SKIP]` com `rc=0`.

## Fase 5: verificação final

```bash
python3 "$SQA/scripts/audit_skill_quality.py" "$ALVO" --format json > "$BASE/depois.json"; echo "rc=$?"
find "$ALVO" -type f -exec sha256sum {} + | sort -k2 | diff "$BASE/hashes.txt" -
```

- Achado presente em `antes.json` e em `depois.json`: dívida pré-existente. Achado só em
  `depois.json`: regressão nova, bloqueia a conclusão.
- Script novo ou alterado: rodar no interpretador real `--help`, um caso válido e um inválido,
  sem envio, publicação, exclusão ou alteração externa; registrar comando, `rc` e observação.
- Releitura adversarial: afirmação sem sensor, reference órfã, loop entre skills, dependência
  oculta de irmã, instrução que edita sem autorização.
- Arquivos alterados dentro da allowlist: `git status --short` ou a comparação de hashes.

## Modo reparo

1. Só com autorização e allowlist. Cada correção é um patch pequeno; conhecimento válido fica.
2. Cada skill alterada ganha entrada no `CHANGELOG.md`: data, motivação, resumo e como reverter.
   Hash de commit só se o commit existir.
3. Teto: 2 ciclos (corrigir, fase 5) por skill. Persistiu, parar e relatar.
4. Nada fora da allowlist muda, inclusive índices do harness, que só mudam se estiverem nela.
