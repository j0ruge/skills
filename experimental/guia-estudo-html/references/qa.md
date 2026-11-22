# Método de QA

O QA de um curso tem duas partes: os sensores, que medem a página, e a revisão de conteúdo, que lê cada aula. O aprendizado em si não se mede aqui: ele vai para a verificação humana.

## 1. Um sensor por defeito

1. Escreva o sensor depois de reproduzir o defeito. Ele lê só o contrato de `marcacao.md`.
2. **Prove que ele falha.** Desfaça a correção numa cópia do curso-modelo e rode o sensor nela: tem de sair 1. O `scripts/sabotar.py` faz isso por caso, no `assets/curso-modelo` da skill. Sensor que nunca falhou não prova nada.
3. Rode o sensor na página corrigida: tem de sair 0.
4. Sensor novo entra em `scripts/sensores/` e, se mede só aulas, no `case` do `rodar-tudo.sh` e no `sabotar.py`.

## 2. A prova que decide um status vai escrita no bug

Pasta temporária some. Por isso o comando, a saída curta e os números ficam no próprio arquivo do bug, na seção Verification: "13 PASS, rc 0" ou "FAIL 0002-…: menor texto 7,7 px, rc 1".

## 3. O reteste refaz a reprodução como a pessoa que estuda

O sensor passar não fecha o bug. Refaça o caminho da pessoa: o aparelho, a largura, o toque ou o mouse, a rede ruim. Procure o efeito colateral da correção. Um conserto de diagrama no celular criou um defeito no notebook; um conserto por seletor com nome deixou de fora o link que não casava com o nome. Cada efeito achado vira um bug novo.

## 4. Quem corrige preenche a seção Fix, bug a bug

Preencha a seção Fix logo que o bug fecha, com a causa, a correção e o teste. Preencher no fim da sessão perde a causa.

## 5. Modelo curto de bug

Um arquivo por bug, `BUG-<AAAAMMDD>-<nome>.md`, na pasta do relatório do curso:

```
# BUG-<AAAAMMDD>-<nome>
Status: open | fixed | verified

## Summary
O que a pessoa vê, em que aparelho, e o que perde.

## Repro
Passos que repetem o defeito.

## Fix
- Causa: o sintoma e a causa, em duas frases.
- Correção: o que mudou, em que arquivo.
- Teste de regressão: o sensor, e a saída com a correção desfeita.

## Verification
- Reteste: data, quem (qual pessoa e aparelho), comando.
- Saída: o que o comando imprimiu, com os números.
- Resultado: pass ou fail.
```

O status anda em três passos: `open` quando o defeito é achado, `fixed` quando a Fix está escrita e o sensor passa, `verified` quando o reteste da seção 3 passa.

## 6. Revisão de conteúdo, uma passada por aula

O agente lê cada aula na ordem em que a pessoa lê e confere:

1. Cada regra de `linguagem-simples.md`, na ordem do arquivo.
2. Cada bloco de `roteiro-da-aula.md`: o bloco existe, na ordem, com a marcação certa.
3. O quiz se resolve só com o que a aula e as aulas anteriores ensinaram. O porquê de cada opção certa tem fonte.
4. Cada número tem fonte e localização (`span.fonte`).
5. Uma frase simplificada ainda diz o que a fonte diz. A síntese que junta duas fontes se confere contra as duas.

Cada achado vira um bug, no modelo da seção 5, com a aula e o trecho.

## 7. O aprendizado fica para a verificação humana

A revisão confere a **estrutura**: os blocos existem, o termo vem antes do uso, o quiz se resolve. Ela não prova que alguém aprendeu. O relatório termina com "Verificação humana necessária", e cada item diz o que a pessoa confere e como:

- Estudar uma aula e, no dia seguinte, explicar o conteúdo com as próprias palavras, sem abrir a página.
- Refazer o quiz numa aba nova, dois a quatro dias depois, e anotar o que errou.
- Dizer em qual aparelho e em qual rede estudou, e o que atrapalhou.

O resultado do primeiro curso de outro projeto vai para o `CHANGELOG.md` da skill (regra de promoção).

## 8. Os comandos

```
bash scripts/preparar.sh <bancada nova>
bash scripts/rodar-tudo.sh <bancada> <pasta do curso>
python3 scripts/sabotar.py assets/curso-modelo <pasta nova> --bancada <bancada>
```

O `rodar-tudo.sh` mede o curso da pessoa. Rode o `sabotar.py` só no `assets/curso-modelo` da skill, depois de mudar um sensor ou o kit. Diante de outro curso, ele sai 2 e diz qual caso não achou o seu texto.

A bancada e as capturas ficam fora de qualquer repositório e fora do `/tmp`, que o WSL apaga ao reiniciar. Cada execução do `rodar-tudo.sh` grava numa pasta própria, `<bancada>/execucoes/<data-hora>-<pid>/`, com `resumo.txt`.
