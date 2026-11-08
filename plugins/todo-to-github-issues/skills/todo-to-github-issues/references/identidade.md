# Identidade: por que o script faz assim

Leia antes de mudar a chave, o hash, a busca das issues ou o corpo que o script escreve, e quando
um corpo de issue sair diferente do item.

- **A chave é só o título** (`<!-- todo-key -->` no corpo). Âncora `arquivo:linha` fica de fora
  porque o número da linha muda a toda hora, e cada mudança viraria uma issue nova. O preço disso:
  **renomear o título cria uma issue nova e deixa a antiga órfã**. O plano marca o par como
  `RENAME?` e imprime o comando que copia a chave nova para a issue antiga. Número que muda vai no
  corpo, não no título.
- **As issues existentes vêm de `gh issue list`, nunca de `--search`.** O índice de busca do
  GitHub pode atrasar (não medido aqui), e uma segunda rodada logo depois de uma queda criaria duplicatas.
- **O `todo-hash` cobre título, seção e texto, e deixa os links de fora.** Assim um commit novo em
  `HEAD` não reescreve 98 issues só porque o sha do permalink mudou.
- **Cada issue sabe de que arquivo veio** (`<!-- todo-src -->`, ou o link do rodapé nas antigas).
  Sem isso, rodar com `--file` num segundo arquivo lia **todo** o espelho do primeiro como órfão,
  e um `--close-orphans` o fecharia inteiro.
- **O corpo sai literal**: o texto do item, desquebrado em parágrafos, porque numa issue cada
  quebra simples vira `<br>`. A âncora e todo link relativo viram links para o sha em `HEAD`, e
  todo `@nome` fora de bloco de código ganha um espaço de largura zero depois da arroba: sem isso,
  `` `@codex review` `` citado num achado fez o conector do Codex responder na issue (crase não
  protege: bot lê o texto cru). Com o arquivo sujo ou com `HEAD` fora do remoto, o script avisa e gera
  links sem número de linha. O símbolo que a âncora designa (`` `arq:N` (`símbolo`) ``) fica na linha
  **Âncora:**; até a 2.5.0 ele abria o parágrafo seguinte (kit sdd #255, 2026-10-15), e o
  `update_kind` lê esse corpo antigo como o de hoje, ou cada issue dele voltaria `UPDATE (text)`.
