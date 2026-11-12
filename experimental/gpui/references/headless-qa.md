# QA nativo em display isolado

Use este roteiro quando a automação disputar a sessão gráfica de alguém ou quando
captura/OCR contradisser o resultado da ação. Headless aqui significa executar a
janela GPUI real em outro servidor gráfico; não é teste de DOM.

## Preparar o ambiente

1. Inventarie o servidor virtual, autenticação X11, gerenciador de janelas quando
   necessário, driver Vulkan e as ferramentas de entrada/captura do teste.
   No ensaio, Xvfb/xauth, Openbox e lavapipe já estavam instalados; essa presença
   não deve ser presumida em outra máquina.
2. Crie um display exclusivo, como `xvfb-run -a`, com tela suficiente para conter a
   janela e sem listener TCP. O driver de QA e o aplicativo herdam esse DISPLAY;
   teclado e mouse não são enviados à sessão em uso.
3. Remova `WAYLAND_DISPLAY` da execução X11 e heranças de seleção de driver que
   contrariem o ICD escolhido. Descubra o arquivo de lavapipe instalado em vez de
   fixar um sufixo de arquitetura. `VK_ICD_FILENAMES` funcionou no ensaio; confira
   o loader efetivo. Uma lista de dispositivos de vulkaninfo não prova o do app.
4. Inicie o gerenciador dentro desse display se o roteiro depender de ativação,
   foco ou navegação por Tab. O driver deve recusar execução fora do servidor
   virtual previsto; não substituir uma falha do ambiente por ações no desktop.
5. Use fixtures fora dos dados pessoais, fixe a identidade do binário por hash e
   associe PID, janela, DISPLAY e logs à mesma execução. Finalize os processos
   criados pelo teste, inclusive em falha, e preserve as evidências necessárias.

Se o ambiente não executar a janela, registre bloqueio e o teste restante. Não
converta ausência de execução em Pass. Um probe de ambiente também não comprova
que a aplicação abriu, aceitou entrada, persistiu ou encerrou corretamente.

## Provar a ação antes de julgar a captura

Confirme as pré-condições da jornada: formulário desenhado, alvo de foco correto,
operação confirmada e estado final esperado. Uma tecla enviada não prova que o
widget a recebeu. Aguarde um marcador positivo da interface e confira o efeito
no domínio ou no adaptador da fixture quando a jornada exigir igualdade de dados.

OCR de um campo sob o cursor não é um comparador exato: o cursor pode ser lido
como caractere. Acentos também variam na captura; um teste reconheceu está como
este e falhou sem defeito na aplicação. Escolha um trecho estável do rótulo para
reconhecer a tela e use o efeito confirmado da ação para comprovar o dado. Não
altere a aplicação para satisfazer um falso negativo do instrumento.

Um caso negativo tem controle positivo: depois de mostrar que a seleção oculta
não recebe uma ação, prove que uma entrada visível ainda consegue gerar o efeito
esperado. A contagem de jornadas executadas precisa corresponder às selecionadas;
resultado vazio ou erro de ferramenta não significa aprovação.

## Evidência e limites

Verificado em 2026-11-12: Ubuntu 24.04/X11, Rust 1.97.0, GPUI 0.2.2 e component
0.5.1. A janela abriu em Xvfb, criou uma tarefa e saiu com código 0. O loader do
próprio processo registrou llvmpipe com libvulkan_lvp.so. O controle passou em
seis jornadas de foco e quatro de erro inicial; sabotagens independentes das
proteções de foco fizeram suas jornadas falharem. A mesma rota funcionou com
heranças inválidas de Wayland/driver removidas pelo wrapper.

Esse ensaio funcional não certifica latência, FPS, GPU física, Wayland ou outros
sistemas. A preferência por headless como padrão pertence às instruções do
usuário/projeto; a receita acima oferece o mecanismo e sua comprovação.
