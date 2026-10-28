# Onde ficam os logs (da camada de fora para a de dentro)

`$P` é o prefixo do jogo (o `game.prefix` da config, por exemplo `~/Games/<slug>`). Dentro do
umu/Proton o usuário Windows é **`steamuser`**, não o `$USER` do Linux.

| Camada | Arquivo | O que procurar |
|---|---|---|
| Lutris (cliente) | `~/.cache/lutris/lutris.log` (gira em `.1`…`.4`) | Avisos de inicialização (`i386 … missing`), início e parada do jogo. **Não traz** a saída do Wine. |
| Lutris → umu (saída do jogo) | O stdout do processo `lutris` que lançou o jogo, ou "Mostrar logs" na interface. Com o Lutris aberto pelo menu do GNOME, esse stdout vai para o journal: `journalctl --user -t net.lutris.Lutris.desktop --since <hora>`, inclusive as linhas do `pressure-vessel-wrap`. O journal guarda os boots anteriores (`-b -1`), e dá para comparar com a última vez que funcionou | Rode `lutris lutris:install/<slug>` ou `lutris lutris:rungameid/<id>` com stdout redirecionado para arquivo. Com `UMU_LOG=1`, que o Lutris já exporta, o umu imprime o env completo em linhas `DEBUG:` (é dali que se tira o `WINEDLLOVERRIDES` real). |
| umu / Proton | mesmo stdout; crash do Proton em `/tmp/umu_crashreports` | `Proton: Upgrading prefix`, `Executable is …`, `ProtonFixes …`. `bwrap: setting up uid map: Permission denied` = o container nem subiu (`umu-bwrap-userns-apparmor.md`) |
| DXVK | stdout (`err:   Presenter: …`); arquivos `.log` ao lado do exe se `DXVK_LOG_PATH` estiver definido | `VK_ERROR_DEVICE_LOST` = travamento ou reset da GPU |
| Estado do prefixo | `$P/config_info` (o que o Proton aplicou), `$P/version`, `$P/tracked_files` | A linha `True/False` do `use_wined3d`; mudanças nesse arquivo fazem o Proton recopiar as DLLs |
| DLLs gráficas | `$P/drive_c/windows/system32/{d3d9,d3d11,d3d12,d3d12core,dxgi,nvapi64}.dll` | `ls -la`: symlink para `~/.local/share/lutris/runtime/...` = injetada pelo Lutris; `*.orig` = o Lutris trocou a original |
| Launcher do jogo | Pasta do launcher, ex.: `.../MTGA/MTGALauncher/Logs/MTGAInstall.log` | Se o launcher chegou a chamar o exe do jogo ("Launching …") |
| Unity (jogo) | `$P/drive_c/users/steamuser/AppData/LocalLow/<Empresa>/<Produto>/Player.log` (+ `Player-prev.log`) | Última linha antes de `Crash!!!`; bloco `Direct3D:` / `Renderer:` quando o gráfico sobe |
| Unity (crash) | `$P/drive_c/users/steamuser/AppData/Local/Temp/<Empresa>/<Produto>/Crashes/Crash_<data-UTC>/` (`crash.dmp` + cópia do `Player.log`) | A lista de módulos: `wined3d.dll` presente = wined3d; ausência de `d3d12.dll` com crash na sonda = falha ao carregar o d3d12 |
| Kernel / GPU | `journalctl -k` e `dmesg` (podem exigir grupo `adm` ou root) | `i915 … GPU HANG`, `reset` |

## Pegadinhas de leitura

- **Log do jogo mais velho que o último lançamento = o jogo nem foi chamado.** Compare a data do
  `Player.log` (ou do log do launcher) com a última `Started initial process` do journal. Se o log
  for mais velho, o jogo morreu antes de ser chamado (Lutris, umu ou container), e mexer na config
  gráfica não adianta. O `diagnose.sh` faz essa comparação.

- **Os horários das pastas `Crash_*` do Unity estão em UTC.** Converta antes de cruzar com o
  `lutris.log`, que fica na hora local.
- **`Game still running … Stopping …` no `lutris.log` não é a causa.** Ele aparece quando o
  processo que o Lutris monitora termina, e jogos com launcher (o launcher chama o jogo e sai)
  produzem isso sempre.
- **O `Player.log` é sobrescrito a cada execução** (a anterior vira `Player-prev.log`). Copie-o
  antes de testar de novo, senão a evidência some.
- **O `lutris -b <script> <jogo>` falhou** com "No valid game (…) provided" na ordem
  `-b caminho lutris:rungameid/1`. Em vez de exportar o script, tire o env das linhas `DEBUG:`
  do umu.
