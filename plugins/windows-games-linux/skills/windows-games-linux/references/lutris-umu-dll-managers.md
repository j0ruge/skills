# Lutris injeta DLLs próprias num prefixo Proton (umu)

Verificado em **Lutris 0.5.22** (deb do GitHub, 2026-02-25), runner wine com a versão padrão
**"GE-Proton (Latest)"**, em 2026-10-23. Confira de novo se a versão do Lutris for outra, com o
sensor do fim deste arquivo.

## O mecanismo

O Lutris tem "DLL managers" que colocam no prefixo as versões **dele** das DLLs gráficas:

| Manager | Opção na seção `wine:` | DLLs | Runtime do Lutris |
|---|---|---|---|
| DXVK | `dxvk` | d3d9, d3d10core, d3d11, dxgi | `~/.local/share/lutris/runtime/dxvk/` |
| VKD3D (vkd3d-proton) | `vkd3d` | d3d12, d3d12core | `~/.local/share/lutris/runtime/vkd3d/` |
| DXVK-NVAPI | `dxvk_nvapi` | nvapi, nvapi64 | `~/.local/share/lutris/runtime/dxvk-nvapi/` |
| D3D Extras, dgVoodoo2 | `d3d_extras`, `dgvoodoo2` | d3dx*, d3dcompiler_* / ddraw… | — |

Para habilitar, o manager **renomeia a DLL do prefixo para `.orig` e cria um symlink** para a do
runtime, e acrescenta `<dll>=n` (somente nativa) ao `WINEDLLOVERRIDES`. Para desabilitar, apaga o
symlink e devolve o `.orig`.

O Proton **gerencia as próprias DLLs**: copia DXVK e vkd3d-proton, ou as do wined3d com
`PROTON_USE_WINED3D=1`, sempre que muda a config do prefixo (o arquivo `config_info`). Por isso
cada manager declara `proton_compatible = False`, e `runners/wine.py:get_dll_managers()` o
desliga quando `proton.is_proton_path(self.get_executable())` é verdadeiro.

**O furo:** com a versão "GE-Proton (Latest)", `get_executable()` devolve o caminho do
`umu-run` (`~/.local/share/lutris/runtime/umu/umu-run`), e `is_proton_path()` só reconhece
caminhos **dentro** de um diretório de Proton. Com isso, `is_proton_path(umu-run)` é `False`, a
trava não dispara, e os managers ligados por padrão (`vkd3d`, `dxvk_nvapi`) atuam sobre um
prefixo que o Proton também está gerenciando.

## Como isso derruba o jogo

- O script de instalação manda `dxvk: false`, e o Lutris exporta `PROTON_USE_WINED3D=1`: o
  Proton coloca d3d11/dxgi do **wined3d** e o `d3d12.dll` builtin do Wine.
- Ao mesmo tempo, o VKD3D do Lutris troca `d3d12.dll`/`d3d12core.dll` por symlinks para a
  vkd3d-proton dele (v2.14 em 2026-10, mais velha que a do GE-Proton) e força `d3d12=n`,
  `d3d12core=n`. O DXVK-NVAPI força `nvapi=n` e `nvapi64=n`.
- Quem sonda D3D12 na inicialização, como o Unity 6 com seu "D3D12 Device Filter", morre nessa
  mistura. O `Player.log` termina em `[Subsystems] Discovering subsystems …` e logo depois
  vem `Crash!!!`. O `d3d12.dll` nem aparece entre os módulos carregados, porque a carga falhou.
- O Proton às vezes sobrescreve o symlink do `d3d12.dll` (quando o `config_info` muda), e às
  vezes não. Por isso o estado das DLLs varia entre execuções, e o sintoma parece intermitente.

## Prova (A/B) feita no caso de origem

1. Pelo Lutris: crash em ~10 s.
2. `MTGA.exe` direto pelo `umu-run`, com o mesmo `PROTONPATH` e `PROTON_USE_WINED3D=1`: **abre**,
   conecta e baixa assets.
3. O mesmo teste direto, acrescentando só
   `WINEDLLOVERRIDES='d3d12,d3d12core,nvapi,nvapi64=n;winemenubuilder='`: **crash em ~6 s**.
4. Com `vkd3d: false` e `dxvk_nvapi: false` na config do jogo, pelo Lutris: **abre** e continua de
   pé. O Lutris também desfez sozinho o symlink de `d3d12core.dll` e devolveu o `.orig`.

Não ficou isolado se basta o `d3d12` ou o `nvapi` sozinho, porque os dois foram desligados
juntos.

## Correção

Na config do jogo, `~/.local/share/lutris/games/<slug>-<id>.yml`, seção `wine:` do nível raiz
(não a de dentro de `script:`), com backup antes:

```yaml
wine:
  dxvk: false        # ou true, mas escolha explicitamente
  dxvk_nvapi: false
  vkd3d: false
```

Pela interface, o caminho é: botão direito no jogo → Configurar → Opções do runner → desligar
"Enable VKD3D" e "Enable DXVK-NVAPI". O mesmo vale para `dxvk` se você quiser o DXVK **do
Proton**: deixe o `dxvk` do Lutris desligado e não exporte `PROTON_USE_WINED3D`. Isso exige
acrescentar `PROTON_USE_WINED3D: "0"` em `system: env:`, porque o Lutris exporta `=1` sempre
que `dxvk: false`. Essa variante não foi testada.

O **D3D Extras** (`d3d_extras`) também atua: no caso de origem ele trocou 46 `d3dx*`/
`d3dcompiler_*` durante a instalação. O `diagnose.sh` conta esses `.orig`. Desligá-lo
(`d3d_extras: false`) faz sentido pela mesma lógica, mas não foi testado e não foi necessário
para o MTG Arena abrir.

Alternativa sem tocar nos managers: escolher no runner uma versão **explícita** de Proton (por
exemplo, `GE-Proton11-11`) em vez de "GE-Proton (Latest)". Aí `get_executable()` devolve um
caminho dentro do diretório do Proton e a trava funciona. Pelo código, deve resolver; ainda não
foi testado em jogo.

## Sensor: o furo ainda existe nesta versão do Lutris?

```bash
python3 -I -c "
import sys; sys.path.insert(0,'/usr/lib/python3/dist-packages')
from lutris.util.wine import proton
u = proton.get_umu_path(); print(u, 'is_proton_path =', proton.is_proton_path(u))"
```

`False` significa que o furo está presente: os managers vão atuar em prefixo Proton quando o
runner usar "GE-Proton (Latest)". Em 2026-10-23 não havia issue sobre isso em `lutris/lutris`
(busca por `umu vkd3d` e `is_proton_path umu`).
