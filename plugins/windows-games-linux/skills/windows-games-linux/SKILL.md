---
name: windows-games-linux
description: "Diagnose and fix Windows games on Linux run through Lutris, umu, Proton or Wine: find the layer where the game dies, A/B-launch it outside Lutris, read Unity/Proton logs, fix the game config. Catches Lutris injecting its own VKD3D/NVAPI into Proton prefixes. Triggers — game closes on launch, Lutris, Proton, Wine, umu, DXVK, VKD3D, i386 libs."
license: MIT
compatibility: Linux. Verificado em Ubuntu 24.04 (X11/GNOME, Intel/Mesa) com Lutris 0.5.22, umu-launcher 1.4.4 e GE-Proton11-11 em 2026-10-23. Scripts em bash e python3; diagnose.sh importa os módulos Python do próprio Lutris (/usr/lib/python3/dist-packages).
metadata:
  author: JorUge
  version: "1.0.0"
  hermes:
    tags:
      - Gaming
      - Lutris
      - Proton
      - Wine
      - umu
      - DXVK
      - VKD3D
      - Unity
---

# Jogos Windows no Linux (Lutris · umu · Proton · Wine)

Um jogo Windows no Linux passa por quatro camadas, e cada uma pode derrubá-lo:
**Lutris** (monta env e DLLs) → **umu-run** (container steamrt) → **Proton/Wine** (traduz a API)
→ **o jogo** (launcher, engine, gráfico). O trabalho é achar **em qual camada** ele morre antes
de mexer em qualquer coisa. Chute de configuração, como ligar e desligar DXVK até funcionar, gasta
tempo e esconde a causa.

## Armadilhas ao testar (leia antes do primeiro teste)

- **Cada teste abre o jogo na tela do usuário.** Avise antes ("vai abrir e fechar, sou eu
  testando"). Um teste que você encerra parece, para quem está olhando, o bug voltando.
- **No teste final, não mate o jogo.** Se o jogo abriu pelo caminho real (o Lutris), deixe-o
  aberto para o usuário.
- **Para encerrar um processo de teste, use `pkill -x <nome.exe>`, nunca `pkill -f`.** O `-f` casa
  com a linha de comando do seu próprio shell, que contém o mesmo nome, e mata a sessão. O `comm`
  do processo é truncado em 15 caracteres.
- **`sudo` não funciona pelo `!` do Claude Code**, porque não há TTY. Use `pkexec sh -c '…'`: o
  GNOME abre a janela de senha. Detalhes em `references/instalar-atualizar-lutris.md`.

## Fluxo

1. **Coletar o estado** com um comando só:
   `scripts/diagnose.sh <parte-do-slug>` (ex.: `magic`). O script é somente leitura e mostra a
   versão do Lutris, a config do jogo, o runner efetivo, o estado das DLLs gráficas no prefixo
   (symlink, `.orig`, origem), os logs de crash e o que faltar de i386.
2. **Achar onde o jogo morre.** Leia o log da camada mais funda que chegou a escrever algo. A
   tabela de onde cada log fica está em `references/onde-ficam-os-logs.md`. Num jogo Unity, a
   última linha do `Player.log` antes de `Crash!!!` e a lista de módulos carregados dizem qual
   API gráfica estava em uso (`wined3d.dll` = wined3d; `d3d11.dll` sem `wined3d.dll` = DXVK).
3. **Teste A/B fora do Lutris.** Rode o `.exe` do jogo direto pelo umu com
   `scripts/ab-launch.sh`, com o mesmo `PROTONPATH` e o mesmo modo gráfico. Ele responde
   `RUNNING`, `CRASH` ou `EXITED`.
   - **Funciona direto e quebra pelo Lutris:** a culpa é do env ou das DLLs que o Lutris injeta.
     Vá para `references/lutris-umu-dll-managers.md`.
   - **Quebra nos dois:** o problema está no Proton, no driver ou no jogo. Troque **uma**
     variável por vez (`--wined3d` ↔ DXVK, versão do Proton, `--overrides`).
4. **Isolar a variável.** Some ao teste direto, uma por vez, as diferenças do env do Lutris (o
   `WINEDLLOVERRIDES`, os `PROTON_*` e os `DXVK_*` que ele exporta aparecem no log do umu com
   `UMU_LOG=1`) até reproduzir o crash. A variável que fez quebrar é a causa.
5. **Corrigir na config do jogo**, `~/.local/share/lutris/games/<slug>-<id>.yml`, seção `wine:`.
   Faça backup antes. Prefira a config do jogo à global do runner, porque o efeito fica restrito
   a esse jogo.
6. **Validar pelo caminho real:** `lutris lutris:rungameid/<id>` (o id está em `pga.db`, e o
   `diagnose.sh` mostra) e confirmar que o jogo passa do ponto onde morria **e continua de pé**
   depois de uns 30 s. Depois rode de novo o `diagnose.sh` para ver as DLLs no estado esperado.

## Sintoma → causa conhecida

| Sintoma | Causa provável | Onde está o detalhe |
|---|---|---|
| Abre e fecha em 5–15 s pelo Lutris, mas roda direto pelo umu | Lutris ≥0.5.20 com runner "GE-Proton (Latest)" injeta DXVK/VKD3D/NVAPI próprios num prefixo Proton | `references/lutris-umu-dll-managers.md` |
| Unity: `Crash!!!` logo após `[Subsystems] Discovering subsystems` | Sonda de D3D12 quebrando (mistura de vkd3d com dxgi do wined3d ou override `d3d12=n`) | idem |
| Lutris avisa `i386 libGL.so.1 missing` / `libgnutls.so.30 missing` | Faltam libs de 32 bits; no Ubuntu 24.04 o pacote é `libgnutls30t64:i386` | `references/instalar-atualizar-lutris.md` |
| `Battle.net source is unavailable … protobuf` ao abrir o Lutris | Falta `python3-protobuf` (só aviso) | idem |
| Ícone na área de trabalho falha no fim da instalação (`FileNotFoundError … .desktop`) | Bug cosmético do Lutris; o jogo instala mesmo assim | idem |
| `lutris.log`: `Game still running … Stopping` | Normal em jogos com launcher que chama o jogo e sai; não é a causa | `references/onde-ficam-os-logs.md` |

## Casos registrados

- **MTG Arena, Intel UHD 770, Lutris 0.5.22, GE-Proton11-11, out/2026:**
  `references/caso-mtg-arena-2026-10.md`. Contém a sequência de evidências, os comandos e o que
  ficou em aberto.

Ao resolver um jogo novo com causa nova, registre o caso em `references/caso-<jogo>-<aaaa-mm>.md`,
acrescente a linha na tabela acima e anote no `CHANGELOG.md` do plugin.
