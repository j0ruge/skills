# Instalar e atualizar o Lutris e os pré-requisitos (Ubuntu/Debian)

## Atualizar pela release do GitHub

O repositório do Ubuntu 24.04 parou no Lutris 0.5.18. As releases novas saem como `.deb` em
https://github.com/lutris/lutris/releases (em 2026-10-23, a mais recente era a v0.5.22, de
2026-02-25).

```bash
gh api repos/lutris/lutris/releases --jq '.[0:3][] | {tag: .tag_name, date: .published_at, assets: [.assets[].name]}'
D=$(mktemp -d)   # diretório próprio e vazio para o download (dado não confiável)
gh release download <tag> -R lutris/lutris -p 'lutris_*_all.deb' -D "$D"
dpkg-deb -I "$D"/lutris_*_all.deb | sed -n '/Depends/,/Recommends/p'   # confira as deps
```

A instalação usa o `apt` com o caminho do arquivo, para ele resolver as dependências. A
instalação precisa de root; veja a próxima seção.

## Root sem TTY: `pkexec`

O `! sudo …` do Claude Code e os comandos do agente não têm terminal, e o `sudo` falha com "a
terminal is required". Numa sessão gráfica com agente polkit (o GNOME Shell já é um), use:

```bash
pkexec sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get install -y /caminho/lutris_X_all.deb python3-protobuf'
```

O `pkexec` limpa o env, por isso o `DEBIAN_FRONTEND` vai dentro do `sh -c`. O comando bloqueia
até o usuário digitar a senha na janela, então use um timeout longo.

## Pré-requisitos de 32 bits

O Wine e o Proton usam partes de 32 bits mesmo em jogo de 64. O próprio Lutris avisa ao abrir:
`i386 libGL.so.1 missing` e `i386 libgnutls.so.30 missing`.

```bash
dpkg --print-foreign-architectures          # vazio = i386 não habilitado
dpkg --add-architecture i386 && apt-get update
apt-get install -y mesa-vulkan-drivers:i386 libgl1-mesa-dri:i386 libgl1:i386 libgnutls30t64:i386
```

- **`libgl1-mesa-dri:i386` não traz o `libGL.so.1`.** Ele vem do `libgl1:i386`.
- **No Ubuntu 24.04 o pacote é `libgnutls30t64`** (transição de `time_t` 64 bits). Um
  `apt-get install libgnutls30:i386` funciona por causa do Provides, mas o
  `dpkg -l libgnutls30:i386` diz "não encontrado". Confira por `dpkg -l | grep gnutls30.*i386`.
- **GPU NVIDIA:** troque o Mesa pelos pacotes `libnvidia-gl-<versão>:i386` do driver instalado.
  Esse caso não foi testado aqui.

## Escolher o script de instalação

Liste os scripts disponíveis e compare antes de instalar (dependências do winetricks, `dxvk`,
instalador de 32 ou 64 bits, versão fixa ou "latest"):

```bash
curl -s https://lutris.net/api/installers/<slug-do-jogo> | python3 -I -c '
import json,sys
for i in json.load(sys.stdin)["results"]:
    print(i["slug"], "|", i["version"], "|", i["runner"], "|", i["updated_at"])'
```

Prefira o script que baixa o instalador oficial "latest" e tem menos winetricks. O `dotnet48`,
por exemplo, leva muitos minutos e nem sempre é necessário. Desconfie de script com `.msi` de
versão fixa: o jogo fica preso nela. Abra o instalador com
`setsid nohup lutris lutris:install/<slug-do-script> > log 2>&1 &`, guardando o stdout, que é o
único lugar onde a saída do Wine aparece.

## Avisos que não são problema

- `Error while completing task … create_shortcut … FileNotFoundError … .desktop` no fim da
  instalação: o atalho na área de trabalho falha, mas o jogo fica instalado.
- `Proton: Error: unable to use parent for game drive, path` durante a instalação: inofensivo.
- `pv-locale-gen: Missing locale en_US.UTF-8`: o container do umu gera o locale sozinho.
