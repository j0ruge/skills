# Estado e execução nativa — GPUI 0.2.2/component 0.5.1

## Encerrar após a última janela no X11

`cx.quit()` síncrono dentro de `on_window_closed` provocou `RefCell already
borrowed` em X11Client::with_common (client.rs:1388). O backtrace passou por
Window::on_close e App::flush_effects. `App::defer` ainda executou no mesmo flush
e não resolveu. Agendar pelo executor em outro ciclo encerrou com exit 0:

```rust
use gpui::App;

pub fn quit_after_last_window(cx: &mut App) {
    cx.on_window_closed(|cx| {
        if cx.windows().is_empty() {
            cx.spawn(async |cx| {
                let _ = cx.update(|cx| cx.quit());
            })
            .detach();
        }
    })
    .detach();
}
```

Registrar uma vez na inicialização. A reprodução e o replay foram nativos no
Ubuntu 24.04/X11 com GPUI 0.2.2. Não generalizar o problema a todos os backends.
Para impedir fechamento durante escrita, `Window::on_window_should_close`
permite retornar false; o callback final de quit já é tarde para cancelar.

## InputState e feedback da aplicação

`InputState::set_value` também emite `InputEvent::Change`. Se o adapter limpa
feedback em todo Change, a limpeza programática após um commit pode apagar o
próprio aviso de sucesso. Compare o valor recebido com o draft confirmado:
eco idêntico preserva o feedback; nova digitação pode limpá-lo. Foi reproduzido
na janela e protegido por teste puro de transição RED/GREEN. Reutilizar a
Entity do campo continua necessário; não recriá-la em render.

## Linhas virtualizadas e títulos longos

Altura fixa não restringe largura intrínseca. Em `uniform_list`, uma linha sem
largura disponível definida pode crescer com o título e esconder os botões.
O replay confirmou `.w_full().min_w_0()` na linha e `.flex_1().min_w_0()` no
texto truncado, preservando as ações. Testar conteúdo longo permitido pelo
produto e tamanho mínimo de janela; não transformar o limite deste exemplo
em regra de domínio de outros aplicativos.

## Instrumento nativo e dispositivo real

No X11, aguarde `IsViewable` antes de mover/capturar uma janela recém-criada.
Confirme o ID ativo; não reative uma janela já ativa a cada tecla. `wmctrl`
envia pedidos assíncronos e uma consulta logo depois pode anteceder a confirmação
do gerenciador. Separe ação e observação quando o canal não estabilizar.

Quando o loader Vulkan oferece esse diagnóstico, iniciar **o próprio processo
alvo** com `VK_LOADER_DEBUG=driver` pode revelar a linha `vkCreateDevice` seguida
de `Using <device> with driver <library>`. Distinguir essa escolha da lista de
dispositivos enumerados. Isso foi conferido no processo release observado;
não inferir escolha apenas de vulkaninfo nem prometer desempenho pela GPU.

Fontes: GPUI 0.2.2 src/app.rs, src/window.rs e platform/linux/x11/client.rs;
component 0.5.1 input/state.rs; build Rust 1.97.0 e jornadas nativas em
2026-11-12. Evidências da aplicação que originou as sondas em
`/home/joruge/repos/rust_gpui/docs/stack.md` e `docs/qa/reports/2026-11-12-full.md`.
