# Referências ativas na limpeza

Ao mover, renomear ou remover um arquivo, inclusive via Lixeira, identifique
quem depende do caminho atual. Quando houver uma cópia a preservar, verifique
seu conteúdo no destino. Se uma nota, configuração ou script usa o caminho
atual, confira também como esse consumidor encontra o arquivo.

1. Busque pelo caminho e pelo nome nos consumidores relevantes. Use a busca
   da aplicação ou uma busca literal como `rg -n -F --`. Abra as ocorrências
   e confirme quais resolvem para o item em questão. Menções no histórico e
   arquivos homônimos podem apontar para outro lugar.
2. Preserve as referências que precisam continuar funcionando. Mantenha o
   caminho original ou atualize o consumidor dentro do escopo autorizado.
   Se nenhuma opção estiver disponível, preserve esse item e informe o vínculo.
   Quando o pedido incluir retirar o vínculo, confira que ele saiu da fonte.
3. Depois da mudança, valide a partir do consumidor, usando a mesma forma de
   resolução. Um hash igual confirma os bytes da cópia. A referência só volta
   a funcionar quando o consumidor consegue abrir o destino que ela aponta.

Compare conteúdo no destino também em limpezas sem referências identificadas.
Nomes e status como “backup concluído” ou “PR mesclada” podem descrever
artefatos diferentes. Arquivos com nomes diferentes podem ter o mesmo conteúdo.
