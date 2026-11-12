---
name: gpui
description: Use when planning, building, or checking a native Rust desktop interface with GPUI, especially when adapting Zed examples, selecting compatible GPUI APIs, or validating a Linux graphical session. Not for ordinary web interfaces or configuring the Zed editor.
---

# GPUI — compatibilidade e evidência nativa

GPUI é um framework de interface acelerada por GPU. Compatibilidade da API,
compilação e interação na janela são verificações distintas.

## Fixar a referência certa

Leia manifesto e lockfile. Identifique versão/revisão e features antes de copiar
exemplos. Consulte documentação e fontes dessa mesma versão; exemplos da branch
principal do Zed podem divergir da crate publicada. Se ainda não há projeto,
registre a versão como candidata, sem declarar compatibilidade demonstrada.

Se usar biblioteca de componentes, leia
[compatibilidade de componentes](references/components.md) antes de escolher
versões ou copiar seu bootstrap. Ela registra fontes conferidas e limites.

Pontos de conferência ao adaptar um snippet: imports e traits de `prelude`,
inicialização da aplicação, assinatura de `open_window`, IDs dos elementos,
listeners, foco, entrada de texto e notificação de mudanças.

Exemplo de diferença documentada: a closure de `App::open_window` recebe janela
e contexto na versão 0.2.2. Um tutorial com apenas `|cx|` precisa de adaptação,
não apenas de `cargo add`. Isso não fixa 0.2.2 como versão obrigatória.
[API versionada](https://docs.rs/gpui/0.2.2/gpui/struct.App.html#method.open_window).

`cx.notify()` notifica mudanças ao framework; não é uma medição de frames nem
uma ordem de renderização imediata comprovada na GPU.

Para encerramento X11, eco de eventos do input, largura de linhas virtualizadas
e diagnóstico do dispositivo Vulkan, leia
[estado e execução nativa](references/state-and-x11.md). Os exemplos são
verificados em GPUI 0.2.2/component 0.5.1 e não fixam versões para outros projetos.

## Verificar o ambiente gráfico

No Linux, registre sistema, sessão, display e Vulkan separadamente da toolchain:

```bash
cat /etc/os-release
printf 'DISPLAY=%s\nWAYLAND_DISPLAY=%s\nXDG_SESSION_TYPE=%s\n' \
  "$DISPLAY" "$WAYLAND_DISPLAY" "$XDG_SESSION_TYPE"
if command -v vulkaninfo >/dev/null 2>&1; then
  vulkaninfo --summary
fi
```

GPU física e renderizador de software podem aparecer juntos. Esse inventário
não identifica sozinho o dispositivo escolhido pelo aplicativo. Dependências
nativas devem vir da versão utilizada e dos erros observados; a lista de build
do Zed inteiro não é automaticamente a lista mínima de uma aplicação GPUI.

## Projetar o experimento

Confirme a atividade que o usuário quer experimentar. Um contador de tutorial
não especifica entrada textual, persistência ou regras de uma aplicação real.
Entidades GPUI organizam estado do framework; não as confundir automaticamente
com entidades de domínio. Isole regras testáveis da apresentação na medida
necessária ao projeto.

## Escolher a evidência

| Questão | Evidência adequada |
|---|---|
| A API compila? | Build com versão, features e toolchain registradas |
| A interface funciona? | Jornada na janela nativa, teclado/mouse e captura |
| O autosave preservou dados? | Reabrir e conferir pela interface; testar falhas de I/O isoladamente |
| O desempenho atende? | Medição com perfil, carga, hardware, dispositivo e critério explícitos |

Testes DOM/Playwright não exercitam uma janela GPUI. Ferramentas X11 como
`xdotool` e captura de janela são opções quando a sessão permite; sua presença
no PATH não prova acesso à janela. Em outro backend, escolha ferramenta
compatível ou registre a verificação humana pendente.

Se QA estiver solicitado, adaptar suas jornadas à superfície nativa. Comprovar
o build examinado; registrar resultados e limitações. Um teste de lógica verde
não substitui a janela. “120 FPS” permanece hipótese até ser medido.

## Armadilhas da automação

Leia [QA headless](references/headless-qa.md) quando automatizar uma sessão gráfica
compartilhada ou quando o OCR contradisser a ação. O roteiro separa display virtual,
renderizador escolhido e resultado funcional; a preferência de cada usuário fica
nas instruções do seu projeto.

Fontes: [GPUI](https://gpui.rs/), [API 0.2.2](https://docs.rs/gpui/0.2.2/gpui/),
[build Linux do Zed](https://zed.dev/docs/development/linux).
Para toolchain e Cargo, complementar com `$rust` quando disponível.
