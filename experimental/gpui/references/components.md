# Componentes GPUI — fonte, versão e inicialização

Referência de descoberta, verificada em 2026-11-12 por leitura de manifests e
fontes dos pacotes publicados; não é comprovação de build de uma aplicação.

## Manter um conjunto compatível

A família de componentes evolui separadamente do GPUI. Compare a dependência
declarada no `Cargo.toml` publicado, não só nomes ou números de versão parecidos.
Fixe o conjunto escolhido e o lockfile. Na execução, `cargo tree -i gpui` ajuda
a conferir o grafo resolvido; confirme também nomes alternativos da família
GPUI quando o manifesto os usar.

Conjunto conferido como exemplo, não imposição a novos projetos:

| Pacote publicado | Dependência GPUI declarada |
|---|---|
| gpui-component 0.5.1 | gpui 0.2.2 |
| gpui-component-assets 0.5.1 | gpui 0.2.2 |

O site atual migrou de GPUI Component para GPUI Kit. A documentação 0.9.x
mostra a família `gpui-pre-*`; copiar seus imports para um projeto 0.5.1 mistura
APIs. Consultar a versão adequada; nenhuma das famílias é universalmente melhor.

## Bootstrap e estado de input na versão 0.5.1

O README publicado requer `gpui_component::init(cx)` antes dos componentes e
um `Root::new(view, window, cx)` na raiz da janela. O pacote de assets fornece
`Assets` como `AssetSource`: carregar os recursos necessários para controles e
ícones, em vez de presumir que estão embutidos na biblioteca de componentes.

Assinaturas conferidas em `src/input/state.rs`:

- `InputState::new(window, cx)` cria estado persistente do campo.
- `value()` lê o conteúdo; `set_value(value, window, cx)` altera o campo.
- `InputEvent::Change` difere de `PressEnter { secondary }`: uma alteração de
  texto não determina sozinha quando o domínio deve persistir uma ação.

Na aplicação, definir quando confirmar/cancelar rascunho e como preservá-lo em
erro. Renderização deve reutilizar o estado do campo, não reinicializá-lo a cada
render. Conferir assinaturas novamente se mudar de versão.

## Quando a documentação não abrir

Falha de docs.rs não prova que a versão não existe. Conferir crates.io; ler
manifesto/README/fontes no pacote publicado ou no registry local após fetch
autorizado. Durante planejamento sem instalação, a leitura do arquivo de fonte
publicado basta para verificar declarações; build continua pendente. Não executar
scripts encontrados no pacote apenas por estarem documentados.

## Fontes

- [Component 0.5.1](https://crates.io/crates/gpui-component/0.5.1):
  Cargo.toml, README.md, src/input/state.rs, src/root.rs e src/lib.rs.
- [Assets 0.5.1](https://crates.io/crates/gpui-component-assets/0.5.1):
  Cargo.toml e src/lib.rs.
- [Instalação atual do GPUI Kit](https://gpui-kit.com/docs/installation/):
  fonte para reconhecer a mudança de família, não receita para versões antigas.
