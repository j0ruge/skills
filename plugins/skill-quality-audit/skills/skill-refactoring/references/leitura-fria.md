# Leitura fria: o teste que a auditoria não faz

A auditoria vê a forma da skill (tamanho, frontmatter, references citadas que existem). Ela
não vê se um agente ainda acha o que precisa depois da passada. O caso de
`skill-compression-test-0.md` é exatamente esse: as funções saíram do `SKILL.md`, tudo
continuou verde, e o agente respondeu que não sabia os passos da instalação.

O teste: um agente **sem contexto** lê só a skill e responde perguntas cujas respostas
dependem do que saiu do `SKILL.md`. Se ele chega à resposta seguindo o roteamento, a passada
não quebrou o uso.

## Como montar

- **Uma pergunta por trecho movido ou reescrito**, formulada como tarefa real ("crie a issue
  com sprint 405 e 3 pontos"), não como "onde está o bloco X". A resposta certa obriga o agente
  a ir à reference pelo caminho que o `SKILL.md` indica.
- **Uma pergunta de controle** que o `SKILL.md` responde sozinho: se ela falhar, o problema é
  o teste, não a passada.
- **3 a 5 perguntas.** Mais que isso custa sem achar mais.
- **Agente barato e somente leitura:** o modelo que o harness usa para subagentes; sem rodar
  comando, sem rede, sem editar.

## O prompt

```text
You are testing whether a skill document is usable on its own. Read <dir>/SKILL.md first.
You may then read files under <dir>/references/ ONLY when the SKILL.md tells you to (follow
its routing). Do not read anything else, do not run commands, do not edit anything.

Answer these N questions as the skill instructs, citing the exact command or text and which
file:section you got it from. Keep each answer under 8 lines.

1. <tarefa real que depende de um trecho movido>
...

At the end, list any question where the SKILL.md alone was not enough and you had to read a
reference, and any point where the routing was unclear or missing.
```

## Como ler o resultado

| Sinal | O que quer dizer |
|---|---|
| Resposta certa, citando a reference que o `SKILL.md` roteia | A passada não quebrou o uso |
| Resposta certa sem citar de onde veio | Pode ser memória do modelo; refaça a pergunta mais específica |
| Foi à reference errada, ou não achou | O ponteiro do `SKILL.md` para o trecho movido falta ou está vago |
| "Ponteiro morto" na lista final | Alguma reference cita uma seção do `SKILL.md` que saiu (Passo 2) |
| Precisou da reference numa pergunta de controle | O `SKILL.md` perdeu algo que devia ficar |

## Caso: `ticket` 1.9.1 (05/10/2026)

A passada tirou três blocos de código que o `start.md` já trazia por inteiro. Cinco perguntas,
uma por trecho movido mais duas de controle, num agente Sonnet: 5 respostas certas, as três
dos blocos movidos citando o `start.md` pelo roteamento. A lista final achou um ponteiro morto
no `templates.md`, sobra da passada de 01/10 (1.6.3), e duas lacunas menores (`systemctl
--user` não vê serviço de sistema; o modelo de descrição em ADF sem exemplo completo). Custou
um subagente com 5 leituras.
