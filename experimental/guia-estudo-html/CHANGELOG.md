# Changelog — guia-estudo-html (experimental)

Skill sem versão: fica em `experimental/`, fora dos catálogos (ver o `README.md` da pasta `experimental/` da loja).
Cada entrada leva a data e o motivo.

## 2026-11-22 — entrada no repositório

**Origem:** um guia de estudo de 9 aulas de outro projeto, com 31 bugs corrigidos e 17 sensores Playwright. A skill generaliza o roteiro de aula, a linguagem simples, o kit (`estudo.css`, `quiz.js`, `diagramas.js`, `textos.js`) e a bancada, sem o assunto do guia de origem. Os sensores ganharam nomes genéricos e leem só o contrato de marcação, não o texto visível.

**Conferido em:** Playwright 1.58.0, Chromium headless, WSL2. Um curso-modelo de duas aulas passa em `rodar-tudo.sh`, e `sabotar.py` derruba cada sensor na sua cópia.

**Estado do método: estrutura conferida, aprendizado ainda não medido.** Os sensores e a revisão de conteúdo conferem os blocos, o termo antes do uso, o quiz que se resolve pela aula e o funcionamento da página. Ninguém mediu se uma pessoa aprendeu pelo curso. Esse fim ficou como verificação humana.

**Regra de promoção para `plugins/`:** o primeiro curso feito com esta skill num projeto diferente do de origem registra aqui o que a pessoa aprendeu e o que falhou. A subida depende desse registro e da decisão do autor. Antes dela, siga "Promover para `plugins/`" no `README.md` da pasta `experimental/`.

## 2026-11-23 — fecha os itens menores adiados

**Motivo:** a execução da skill deixou itens menores para depois, e a revisão final cobriu só parte deles. Cada linha abaixo diz o defeito e o que mudou.

- `scripts/conferir-dois.py`: 429 e 5xx do Crossref valem uma nova tentativa e, se persistem, rc 2 com a mensagem "indisponivel". Antes contavam como FALHA do DOI. A pontuação `:` e `-` no fim do DOI sai, e o comentário no regex diz que DOI com parênteses não tem suporte.
- Os 17 sensores: uma exceção (página que não existe, `goto` que falha) vira uma linha `FAIL erro do sensor: ...` e rc 1, em vez de um traceback sem linha FAIL. Medido: o Chromium fecha sozinho na saída, então não sobra processo. `desenho-cortado-no-notebook` também acusa o Mermaid que não desenhou a 390 px. `tempo-das-aulas` diz qual condição falhou (cabeçalho sem número, índice sem número, cabeçalho diferente do índice, ou fora da conta). `rotulo-das-caixas-sem-contraste` usa o limite 0.03928 dos outros três sensores de contraste; o resultado não muda, porque nenhum byte de cor cai entre 0.03928 e 0.04045.
