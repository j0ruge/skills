# Segredo: por onde passa o conteúdo de um `.env*`

O plugin existe para levar segredo a uma página, e isso inverte a regra de sempre dos hooks
("não toque em `.env`"). Aqui ela vira desenho: cada superfície por onde algo sai do processo tem
uma regra e um teste que prova a regra com um canário (`CANARIO_7c1d`), um valor sintético que pode
chegar ao destino e a nenhum outro lugar. Leia antes de mudar qualquer caminho por onde passa
conteúdo. Uma rota nova precisa de uma linha nesta tabela e de um teste.

| Superfície | Regra | Teste |
|---|---|---|
| payload do hook | o payload de edição traz o arquivo (`tool_input.content`, `new_string`, `originalFile`, as linhas `+` do patch). O hook usa só o caminho e o comando, e não loga o stdin | `test_hook.Hook.test_canario_fora_de_mensagem_log_e_estado` (payload envenenado) |
| conteúdo lido | vem do disco, depois da edição, e nunca do payload | `test_hook.Hook.test_bash_refaz_a_varredura_sem_interpretar_o_comando` |
| `systemMessage` e stdout | só raiz, ambiente, caminho, ação e avisos | os testes do canário em `test_hook` e `test_cli` |
| stderr e mensagem de erro | erro esperado (`ErroEnvDocs`) tem mensagem sem valor; erro inesperado sai só com o tipo, porque a mensagem dele pode carregar dados | `test_hook.Hook.test_excecao_inesperada_sai_so_com_o_tipo` |
| estado | só o sha256 do arquivo inteiro e carimbos. Hash de um valor curto isolado se quebra por força bruta. `validar_estado` recusa o resto sem ecoar o valor recusado | `test_estado` |
| `repr` | o corpo da operação fica fora do `repr` (`field(repr=False)`) | `test_plano` |
| argv | conteúdo de arquivo e senha nunca vão em argv, que o `ps` mostra a outros usuários. O conteúdo remoto chega pelo stdout do `ssh`; a senha de `auth_env` vai em `SSHPASS` no ambiente do filho, e a variável original sai desse ambiente | `test_remoto.ComandoSsh`, e `test_remoto.ProcessoReal`, que lê o `/proc/<pid>/cmdline` do `sshpass` e do `ssh` (programas falsos num processo real) e confere pelo sha256 que a senha chegou ao `SSHPASS` |
| stderr do ssh | nunca é mostrado: pode citar o servidor e, num `cat` errado, trechos de arquivo. O aviso traduz só o rc (`motivo_ssh`) | `test_remoto.FalhaDeRede.test_motivo_por_codigo_de_saida` |
| ambiente remoto que falhou | fica fora da rodada; não vira `ausente`, porque um `ausente` falso apagaria o bloco certo da página | `test_remoto.FalhaDeRede` |
| arquivos locais | estado, página renderizada e blocos do destino de diretório são 0600, gravados atomicamente | `test_estado`, `test_cli` |
| destino | tem que ser menos exposto que a origem: o adaptador kb recusa escrever em página visível a papel fora de `doc.allowed_roles` | (adaptador kb, que ainda não existe) |
| fixtures | os payloads são capturas reais de um `.env` **sintético**, anonimizadas. O probe grava o stdin cru: capturar contra um `.env` real grava o segredo em disco | `test_sem_marcas_da_empresa` (pacote público) |

## Falha

Toda falha do hook sai com exit 0 e um aviso, e o estado fica intacto para o próximo gatilho
tentar de novo. "Intacto" quer dizer: só entra no estado a operação que o destino aceitou
(`aplicar` para na primeira falha). `test_falha_do_destino_mantem_o_estado_intacto` compara o
arquivo de estado byte a byte, e `test_falha_no_meio_grava_so_o_que_o_destino_aceitou` confere que
só a operação aceita entrou.

## Mutantes

Uma suíte que passa com o guarda quebrado não prova o guarda. Cada mutante abaixo, aplicado numa
cópia do script, deixou a suíte vermelha (2026-10-27):

- **hook:** filtro de worktree desligado, máquina sempre aceita, `stop_hook_active` ignorado,
  filtro de edição aceitando qualquer arquivo, estado gravado sem o destino aceitar, `status`
  sempre `ok`, corpo da operação na mensagem e trava desligada;
- **Sync remoto:** senha em argv (`sshpass -p`), variável original deixada no filho, janela
  ignorada, carimbo em ambiente que falhou, falha virando ausente, host sem borda, gatilho sem
  exigir a ferramenta ssh, `--` tirado de antes do host, `BatchMode=yes` tirado, `~/` dentro das
  aspas, rc ≠ 0 aceito e limite de tamanho tirado.
