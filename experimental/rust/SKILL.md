---
name: rust
description: Use when working on Rust applications or libraries with Cargo, choosing a project toolchain, preparing a reproducible build, or validating Rust changes. Applies independently of the UI framework.
---

# Rust — projeto e verificação

Trabalhe com a toolchain e o grafo de dependências do projeto. Distinga
compilação, testes e comportamento observado do artefato.

## Reconhecer o projeto

Leia instruções locais, `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml` ou
`rust-toolchain` e `.cargo/config.toml`, quando presentes. Identifique pacote,
workspace, targets, features e comandos usados pelo projeto. Em pasta sem
manifesto, registre essa ausência antes de sugerir comandos de build.

Verificações iniciais, sem instalar nem criar projeto:

```bash
command -v rustc cargo rustup
rustc --version
cargo --version
```

Se houver rustup, confira `rustup show active-toolchain`. Dentro de projeto com
toolchain fixada, os proxies podem tentar baixá-la: numa fase restrita a leitura,
inspecione primeiro o pin e as toolchains instaladas. Ter executáveis no PATH
não prova compatibilidade com as dependências ou disponibilidade de linker e
bibliotecas nativas.

Se o pin ainda precisa ser instalado, conclua essa instalação antes de disparar
proxies ou consultas rustup concorrentes no mesmo projeto. Eles também podem
iniciar downloads. Para falhas de resolução/build observadas, consulte
[build e toolchain](references/build-compatibility.md).

Se o grafo incluir crates com build nativo, confira ferramentas e headers
separadamente: compilador C/C++, `pkg-config`, CMake/Clang quando requeridos, e
pacotes `-dev` da distribuição. Um runtime instalado não comprova ambiente de
compilação. Inspecione primeiro; instale só no escopo de execução autorizado,
guiado pelo manifesto e erro real, sem copiar o setup de um produto inteiro.

Em diretório existente, preserve arquivos. Quando a criação estiver autorizada,
escolha conscientemente o diretório, nome do pacote e gestão de Git antes de
usar `cargo init` ou `cargo new`.

## Dependências reproduzíveis

`Cargo.toml` declara dependências; `Cargo.lock` registra a resolução exata e é
mantido pelo Cargo. Em aplicações, versionar o lockfile torna a resolução
reproduzível. Use a versão resolvida para consultar APIs, inclusive dependências
Git. [Cargo Book](https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html).

Se o lockfile ainda não existir, sua geração pertence ao bootstrap autorizado.
Depois, `--locked` impede resolução diferente da registrada. Não executar
`cargo update` ou trocar toolchain apenas para contornar um erro sem identificar
a incompatibilidade. Registrar versão, target e features relevantes no handoff.

## Escolher a evidência

| Verificação | O que demonstra |
|---|---|
| `cargo fmt --check` | Formatação compatível com rustfmt |
| `cargo check --locked` | Checagem de tipos; não comprova linkedição final |
| `cargo clippy --locked --all-targets -- -D warnings` | Análise estática dos targets selecionados |
| `cargo test --locked` | Testes selecionados pelo Cargo, incluindo doctests aplicáveis |
| `cargo build --locked --release` | Produção do artefato no perfil release |
| Executar o binário e percorrer seu fluxo | Comportamento no ambiente observado |

Adapte pacote/features/targets ao escopo e à convenção do repo. Não ativar
`--all-features` por reflexo: features podem representar alternativas. Rode os
checks exigidos e os afetados; não repita toda a matriz sem motivo novo.
[Semântica de cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html).

## Entregar ou retomar

Registre comandos realmente executados, resultados, limitações e próximo passo.
Se o usuário pediu somente planejamento, esses comandos ficam como aceite
futuro, não como resultados. Domínio testado não comprova persistência ou UI;
esses riscos exigem evidência própria.

Para GPUI, complemente com `$gpui` se disponível. Não impor GPUI, DDD, servidor,
CI remoto ou um fluxo de aprovação a outros projetos Rust.
