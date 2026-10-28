# Caso: Magic: The Gathering Arena abre e fecha (2026-10-23)

**Ambiente:** Ubuntu 24.04.5, Intel UHD Graphics 770 (ADL-S GT1, Mesa 25.2.8), X11/GNOME.
Lutris 0.5.18 → 0.5.22 (deb do GitHub). Runner wine com a versão padrão "GE-Proton (Latest)",
que resolveu para o GE-Proton11-11 via `umu-run` 1.4.4 com o runtime steamrt4. MTGA cliente
0.1.14589, Unity 6000.3.14f1.

**Script do Lutris:** `magic-the-gathering-arena-latest-modern`. Baixa o `MTGAInstaller.exe`
oficial de 64 bits, instala só a fonte `arial` pelo winetricks e traz `wine: dxvk: false`. Os
outros dois scripts instalam `dotnet48` (lento); o "manually-updated" ainda prende o jogo num
`.msi` de versão fixa.

## Sintoma

"Dá um sinal e para": a janela pisca e fecha em ~10 s, sempre.

## Evidência, em ordem

1. O `MTGAInstall.log` do launcher mostra "On current version already. Launching MTGA!": o
   launcher funciona e quem morre é o `MTGA.exe`.
2. O `Player.log` termina em `[Subsystems] Discovering subsystems …` seguido de `Crash!!!`. Os
   módulos carregados são `d3d11.dll`, `dxgi.dll`, `wined3d.dll` e `libvkd3d-*.dll`, sem
   `d3d12.dll`. Então o jogo estava no wined3d e morreu na sonda de D3D12.
3. O `MTGA.exe` direto pelo `umu-run`, com `PROTON_USE_WINED3D=1` e o mesmo `PROTONPATH`,
   **abriu**: passou pelo `D3D12 Device Filter`, caiu para o D3D11 (`Direct3D 11.0 [level 11.1]`,
   renderer Mesa Intel), conectou no Front Door e começou a baixar assets.
4. No prefixo, `d3d12core.dll` virou symlink para `~/.local/share/lutris/runtime/vkd3d/v2.14/`,
   e havia `d3d12.dll.orig` e `d3d12core.dll.orig`: o Lutris estava injetando a vkd3d dele.
5. O teste direto com o `WINEDLLOVERRIDES` do Lutris (`d3d12,d3d12core,nvapi,nvapi64=n`)
   **reproduziu o crash** em ~6 s.
6. No código, `is_proton_path(umu-run)` dá `False`, e por isso os managers atuam. Detalhe em
   `lutris-umu-dll-managers.md`.

## Correção aplicada

Na seção `wine:` raiz do yml do jogo: `dxvk_nvapi: false` e `vkd3d: false` (o `dxvk: false`
continuou). Pelo Lutris, o jogo abriu em ~14 s e continuou de pé depois de 46 s, baixando assets.
O Lutris devolveu o `d3d12core.dll` original sozinho.

## Também resolvido no caminho

- `i386 libGL.so.1 missing` → `libgl1:i386`. `i386 libgnutls.so.30 missing` →
  `libgnutls30t64:i386`.
- Aviso do Battle.net sobre protobuf → `python3-protobuf`.

## Em aberto

- Durante a instalação, quando o instalador ainda usava DXVK, apareceram 15 linhas
  `Presenter: vkWaitForPresentKHR failed: VK_ERROR_DEVICE_LOST`. A instalação terminou mesmo
  assim. Isso não foi investigado; se for testar o DXVK do Proton nesse jogo e nessa GPU,
  comece por aí.
- Não ficou isolado se a causa é o override de `d3d12`, o de `nvapi` ou os dois.

## Erros do agente que viraram regra na SKILL.md

- Um teste com `timeout 60` encerrou o jogo que já estava funcionando, e o usuário entendeu que
  o bug tinha voltado.
- Um `pkill -f 'MTGA.exe'` casou com o próprio shell do agente e o matou (exit 144).
- O `! sudo …` falhou por falta de TTY; o `pkexec` resolveu.

## Episódio 2 (2026-10-27): "tentei rodar e nada aconteceu"

Mesma máquina, kernel 7.0.0-38, `apparmor` 4.0.1-0ubuntu0.24.04.9. A correção do episódio 1
continuava no yml. A máquina tinha reiniciado em 26/10.

1. O `diagnose.sh` mostrou o `Player.log` de 23/10 e o `lutris.log` com três tentativas de 27/10
   (`Game still running … very short time`). O `MTGAInstall.log` também parou em 23/10: nem o
   launcher foi chamado.
2. O Lutris tinha sido aberto pelo menu do GNOME. A saída do umu estava no
   `journalctl --user`: `pressure-vessel-wrap: E: … bwrap: setting up uid map: Permission denied`,
   e `Child … exited with wait status: 1` cerca de 1 s depois do lançamento.
3. O `srt-bwrap` do runtime, rodado sozinho com `--unshare-user --ro-bind / / true`, reproduziu o
   erro (`rc=1`), e o `/usr/bin/bwrap` também. Valor do sysctl: `kernel.apparmor_restrict_unprivileged_userns = 1`.
4. No boot anterior (`journalctl -b -1`), em 23/10, o mesmo container subia (`Child … exited with
   wait status: 0`). O reboot de 26/10 ficou entre o "funcionava" e o "quebrou".
5. Correção escolhida pelo usuário: o perfil `umu-srt-bwrap` do AppArmor
   (`umu-bwrap-userns-apparmor.md`). O `srt-bwrap` passou a dar `rc=0`. Pelo Lutris, o jogo subiu
   em `Direct3D 11.0 [level 11.1]`, conectou no Front Door e rodou das 20:46:49 às 21:29:09 até o
   usuário fechar. O journal registrou `Child … exited with wait status: 0`, e o `Player.log`
   terminou em `Input System module state changed to: Shutdown`.

**Em aberto:** não ficou registrado quem desligou a restrição antes do reboot. Não há rastro no
journal do boot anterior, no histórico do shell, nem no `/etc/sysctl.d` (o `50-cursor.conf` traz a
linha comentada).
