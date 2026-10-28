# umu não sobe o container: AppArmor barra o user namespace do bwrap

O `umu-run` roda o Proton dentro do container do Steam Runtime (`steamrt3`/`steamrt4`), e quem monta
o container é o `srt-bwrap` (bubblewrap) do próprio runtime. Ele precisa criar um user namespace sem
privilégio. No Ubuntu 24.04 o pacote `apparmor` liga `kernel.apparmor_restrict_unprivileged_userns = 1`
(arquivo `/usr/lib/sysctl.d/10-apparmor.conf`, conferido com `dpkg -S` no `apparmor`
4.0.1-0ubuntu0.24.04.9). Com isso, só cria o namespace o programa que tem um perfil do AppArmor com a
permissão `userns`, e o `srt-bwrap` do umu não tem.

## Sinal

- Para o usuário, "nada acontece": o Lutris marca o jogo como rodando e para em ~1 s, sem janela.
- O `lutris.log` traz só `Game still running … Stopping` e `The game has run for a very short time`,
  o que não diz nada.
- O log do jogo e o do launcher (`Player.log`, `MTGAInstall.log`…) **não ganham data nova**, porque
  o jogo nunca foi chamado.
- Na saída do umu (`journalctl --user -t net.lutris.Lutris.desktop`, ver `onde-ficam-os-logs.md`):

  ```
  pressure-vessel-wrap[…]: E: Processo filho concluiu com código 1: bwrap: setting up uid map: Permission denied
  [umu.umu_run:744] DEBUG: Child … exited with wait status: 1
  ```

**Pista de "funcionava e parou sozinho":** a restrição é o padrão. Se ela estava desligada só em
memória (`sysctl -w`), o reboot a religa. Compare `journalctl --list-boots` com a data da última
vez que o jogo abriu.

## Teste inofensivo (não abre janela, não grava nada)

```bash
for b in ~/.local/share/umu/steamrt*/pressure-vessel/libexec/steam-runtime-tools-0/srt-bwrap; do
  "$b" --unshare-user --ro-bind / / true && echo "ok  $b" || echo "FALHA  $b"
done
sysctl kernel.apparmor_restrict_unprivileged_userns
```

`FALHA` com `setting up uid map: Permission denied` confirma a causa. O `diagnose.sh` já roda isso.

## Correção: escolha do usuário, porque mexe numa proteção do sistema

| Opção | Comando | Custo |
|---|---|---|
| **Perfil só para o bwrap do umu** (recomendada) | o perfil abaixo, instalado com `pkexec` | O caminho fica no `$HOME`, então um programa do usuário que gravasse um binário ali herdaria a liberação. O resto do sistema continua protegido. |
| Desligar a restrição de vez | `kernel.apparmor_restrict_unprivileged_userns = 0` em `/etc/sysctl.d/20-apparmor.conf` (o nome que o próprio `10-apparmor.conf` sugere) e `pkexec sysctl --system` | Tira a proteção de todo o sistema. |
| Só até o próximo reboot | `pkexec sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` | Volta a quebrar no reboot. |

Perfil (no formato do `/etc/apparmor.d/steam` que o Ubuntu já traz):

```
# /etc/apparmor.d/umu-srt-bwrap
abi <abi/4.0>,
include <tunables/global>

profile umu-srt-bwrap @{HOME}/.local/share/umu/**/srt-bwrap flags=(unconfined) {
  userns,

  # Site-specific additions and overrides. See local/README for details.
  include if exists <local/umu-srt-bwrap>
}
```

O `**` cobre o `steamrt3`, o `steamrt4` e as próximas versões do runtime. Escreva o perfil no
scratchpad, valide sem carregar (`apparmor_parser -Q -K <arquivo>`, que roda sem root) e instale:

```bash
pkexec sh -c 'install -m 644 -o root -g root <arquivo> /etc/apparmor.d/umu-srt-bwrap \
  && apparmor_parser -r /etc/apparmor.d/umu-srt-bwrap'
```

O perfil sobrevive ao reboot, porque o `apparmor.service` (habilitado, `ExecStart=/lib/apparmor/apparmor.systemd
reload`) carrega todo o `/etc/apparmor.d`. Depois, rode o teste inofensivo de novo (tem que dar `ok`)
e valide pelo Lutris, como no passo 6 do `SKILL.md`. O `/usr/bin/bwrap` do sistema continua barrado
(`rc=1`, medido), porque o perfil não cobre ele, e mesmo assim o jogo abriu: o umu usou o `srt-bwrap`.

Caso de origem: `caso-mtg-arena-2026-10.md`, episódio 2.
