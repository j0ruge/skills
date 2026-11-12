# Compatibilidade de build e instalação da toolchain

## Pin ausente e comandos concorrentes

Proxies Cargo/Rust e consultas rustup dentro de diretório com pin ausente podem
iniciar a preparação da mesma toolchain. Serialize a instalação antes dos checks.
Foi observado conflito no rename de `.partial` do clippy ao preparar 1.97.0 em
paralelo; a instalação sequencial completou. Isso não autoriza trocar o pin.

Se uma toolchain já instalada tem exatamente o mesmo `rustc --version`/commit,
`cargo +<toolchain>` pode permitir um fetch/build provisório enquanto a instalação
termina. Registre a alternativa e confirme depois o comando normal com o pin;
não confunda uma versão disponível com a instalação nomeada concluída.

## Erro em dependência transitiva

Leia o erro e use `cargo tree --locked -i <pacote>` para localizar a cadeia.
Um lock recém-gerado pode resolver uma dependência indireta incompatível com
uma crate antiga, mesmo com versões diretas exatas. Faça ajuste localizado no
lock apenas após identificar a incompatibilidade, e repita o build afetado.

Exemplo verificado, sem impor versões a outros projetos: GPUI 0.2.2 trouxe
gpui_http_client → zed-async-tar 0.5.0-zed → xattr 0.2.3. O build Linux falhou
com `libc 0.2.191` por `libc::ENOATTR` ausente. Resolver somente libc para
0.2.189 com `cargo update -p libc --precise 0.2.189` permitiu compilar o mesmo
grafo. Não se editou o registry nem se adicionou dependência direta sem uso.
Reavaliar esse ajuste ao atualizar a cadeia; não é um pin universal.

Fontes: manifests e fonte publicados dessas versões; erro E0425 e build release
posterior em Rust 1.97.0/Ubuntu 24.04 x86_64; [remoção upstream](https://github.com/rust-lang/libc/issues/1356).
