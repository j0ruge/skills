# Changelog — `windows-games-linux`

## [1.1.0] — 2026-10-27

### O container do umu não sobe: AppArmor barra o user namespace do bwrap

Segundo episódio do MTG Arena. O usuário relatou "tentei rodar e nada aconteceu", com a correção
da 1.0.0 ainda no yml. O `diagnose.sh` mostrou o `Player.log` de 23/10 e o `lutris.log` com as
tentativas de 27/10, mas não comparou as duas datas. O erro real só estava no journal do usuário,
porque o Lutris tinha sido aberto pelo menu do GNOME:
`pressure-vessel-wrap: … bwrap: setting up uid map: Permission denied`. O Ubuntu 24.04 liga
`kernel.apparmor_restrict_unprivileged_userns=1` (`/usr/lib/sysctl.d/10-apparmor.conf`, pacote
`apparmor`), e o `srt-bwrap` do runtime do umu não tem perfil com `userns`. Em 23/10 o mesmo
container subia. O reboot de 26/10 ficou no meio.

- **`references/umu-bwrap-userns-apparmor.md` (nova):** o sinal, um teste inofensivo
  (`srt-bwrap --unshare-user --ro-bind / / true`), as três correções com o custo de cada uma (o
  usuário escolhe, porque mexem numa proteção do sistema) e o perfil `umu-srt-bwrap`, que foi o
  escolhido. O `srt-bwrap` foi de `rc=1` para `rc=0`, e o jogo rodou 42 min pelo Lutris até o
  usuário fechar.
- **`scripts/diagnose.sh`:** seção nova com o último lançamento do jogo no journal (umu,
  `bwrap:`, `Child … exited`) e um ALERTA quando o `Player.log` é mais velho que esse lançamento.
  Em "Sistema", o valor do sysctl e o teste de userns em cada `srt-bwrap` achado. Testados o
  `rc` 0/1/2 e os ramos ALERTA e FALHA (isolados, com arquivos falsos). Com `-g`, o
  `journalctl -n` sem `-r` devolveu linhas fora de ordem e sem o boot atual, e por isso a busca
  usa `-r`.
- **`references/onde-ficam-os-logs.md`:** a saída do umu também vai para
  `journalctl --user -t net.lutris.Lutris.desktop`, que guarda os boots anteriores (`-b -1`).
  Pegadinha nova: o log do jogo mais velho que o último lançamento quer dizer que o jogo nem foi
  chamado.
- **`SKILL.md`:** uma linha na tabela de sintomas, uma frase no passo 2 e o 2º episódio na lista
  de casos. A `description` não mudou.
- **`references/caso-mtg-arena-2026-10.md`:** o episódio 2 com as evidências em ordem. Fica em
  aberto quem tinha desligado a restrição antes do reboot.

## [1.0.1] — 2026-10-23

### Afirmações conferidas por sensor (auditoria pós-publicação)

A `skill-quality-audit` deu `rc=0` na 1.0.0 (0 erros, 0 avisos, `skills-ref` 0.1.1 válido), mas
a revisão das 26 afirmações do `--claims`, cada uma conferida com um sensor real, achou uma falsa e
cinco sem derivação. Todas foram escritas na sessão de criação.

- **Corrigido:** `references/instalar-atualizar-lutris.md` (e a 1.0.0 deste CHANGELOG) dizia que o
  Ubuntu 24.04 "parou no Lutris 0.5.18". O `apt-cache policy lutris` mostra `0.5.14-2` em
  `noble/multiverse`. A 0.5.18 da máquina de origem tinha vindo de um `.deb` instalado à mão. A
  reference agora diz como o `apt-cache policy` revela isso.
- **Confirmado e com sensor no texto:** a vkd3d-proton v2.14 do Lutris é mais velha que a do
  GE-Proton11-11 (GitHub compare: 1330 commits à frente, 0 atrás). O furo vale da 0.5.20 à 0.5.22:
  o sha256 da `get_executable()` é igual nas duas tags e o `is_proton_path` também. Execução
  testada só na 0.5.22, e o texto diz isso.
- **Derivação e proveniência:** "15 caracteres" ganha a fonte (`TASK_COMM_LEN` = 16 com o nulo,
  `man 5 proc_pid_comm`; conferido com `prctl` → `comm` de 15). O "5–15 s" virou o observado
  (6 a 14 s), os "30 s" estão marcados como heurística, o `config_info` cita o bloco `prefix_info`
  do script `proton`, e o "dotnet48 leva muitos minutos" virou o aviso do próprio script.
- **F1:** cada reference citada no `SKILL.md` diz quando ser lida ("antes de corrigir", "ao
  instalar", "se o jogo for Unity…").

## [1.0.0] — 2026-10-23

Primeira versão. Nasceu de um caso real: o MTG Arena abria e fechava em ~10 s pelo Lutris 0.5.22 com o
GE-Proton11-11 via umu numa Intel UHD 770 (Ubuntu 24.04), e rodava normalmente quando lançado direto pelo umu.

- **`SKILL.md`:** o fluxo por camadas (Lutris → umu → Proton/Wine → jogo): coletar, achar onde o jogo morre,
  teste A/B fora do Lutris, isolar uma variável por vez, corrigir na config do jogo e validar pelo Lutris, sem
  derrubar o jogo no teste final. Traz também a tabela de sintoma → causa e as regras de teste: avisar o
  usuário, `pkill -x` em vez de `pkill -f` (o `-f` casou com o shell do agente) e `pkexec` no lugar de
  `sudo` sem TTY.
- **`references/lutris-umu-dll-managers.md`:** com a versão "GE-Proton (Latest)", `get_executable()` devolve o
  `umu-run`, e `is_proton_path(umu-run)` é `False`. Com isso os managers DXVK/VKD3D/NVAPI/D3D Extras do Lutris
  (`proton_compatible = False`) atuam num prefixo que o Proton também gerencia. A referência traz a prova A/B
  (`WINEDLLOVERRIDES='d3d12,d3d12core,nvapi,nvapi64=n'` reproduz o crash em ~6 s), a correção
  (`vkd3d: false`, `dxvk_nvapi: false` na seção `wine:` do jogo) e um sensor de uma linha para versões futuras.
- **`references/onde-ficam-os-logs.md`:** onde fica cada log por camada (`steamuser` no prefixo, `Player.log` e
  `Crashes/` do Unity com horário em UTC, `config_info` do Proton) e por que `Game still running … Stopping`
  não é a causa.
- **`references/instalar-atualizar-lutris.md`:** atualizar pelo `.deb` do GitHub (o Ubuntu 24.04 parou na 0.5.18),
  `pkexec` sem TTY, os pacotes i386 (`libgl1:i386` traz o `libGL.so.1`; no 24.04 o gnutls é `libgnutls30t64`)
  e a escolha do script de instalação pela API do lutris.net.
- **`references/caso-mtg-arena-2026-10.md`:** as evidências em ordem e o que ficou em aberto (`VK_ERROR_DEVICE_LOST`
  do DXVK na instalação; a causa não foi separada entre `d3d12` e `nvapi`).
- **`scripts/diagnose.sh`:** retrato somente leitura de config, runner efetivo, `config_info`, DLLs gráficas
  (symlink/`.orig`), logs do Unity, módulos gráficos de cada crash e pacotes i386. Testado no caso real.
- **`scripts/ab-launch.sh`:** lança o `.exe` direto pelo umu e devolve RUNNING, CRASH, EXITED ou TIMEOUT. Se
  o jogo já estiver aberto, recusa o teste (rc 3). Testados o `--dry-run` e essa trava. O laço de veredito
  foi validado à mão no caso de origem, não pelo script.
