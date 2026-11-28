# Clone dedicado e lote de skill local

A cópia em uso fica em `<live_dir>/<repo>` e segue a `main`. O checkout de
desenvolvimento continua separado. `lean_auto` lista os slugs `dono/repo`
autorizados. O dono precisa estar em `owners` e o diretório padrão é
`~/.local/share/skills-live`.

- `retrofit_watch.py live-setup <dono/repo> [--url URL]` clona a `main` sem substituir
  o destino, mesmo se um diretório vazio surgir durante a instalação.
  A recusa também vale se o nome do clone já foi usado por outro dono.
  Se a clonagem ou a trava falhar, o comando descarta a cópia temporária. A recusa
  na validação final deixa o clone pendente e preserva seus arquivos. Corrija a
  causa e repita o setup com a mesma origem para terminar a validação.
  Na validação final, inclusive na retomada, o destino precisa ser o mesmo clone,
  estar na `main`, declarar a origem pedida, resolver para essa mesma origem no Git
  e ter a trava de commit efetiva no worktree principal. O setup confere a trava
  depois de consultar o ramo. Se o arquivo simbólico `.git/HEAD` mudar durante
  a validação, a cópia fica pendente. Uma mudança de commit dentro da `main` pode
  preservar esse arquivo. O comando não troca o ramo
  nem remove arquivos para concluir a validação. Se a plataforma ou o sistema
  de arquivos não oferecer movimentação sem substituição, o setup recusa a instalação.
  O setup e a elegibilidade exigem que `.git/HEAD` aponte diretamente para
  `refs/heads/main`, sem passar por outra referência simbólica. A própria
  `refs/heads/main` precisa ser direta e resolver para um commit. O Git faz essa
  consulta local, inclusive para refs empacotadas. No hook, a elegibilidade e
  a medição da janela compartilham três segundos. Se o prazo se esgotar na triagem,
  a entrada segue no fluxo manual. Uma janela inconclusiva mantém o ensaio.
  O setup reconfere a ref ao
  liberar a cópia e mantém a pendência se ela deixar de ser direta ou legível.
  A URL precisa corresponder ao slug. Sem `--url`, usa HTTPS do GitHub.
  O clone declara a origem autorizada. Em `github.com` nas portas padrão,
  HTTPS e as formas SSH podem representar o mesmo repo. Nos demais servidores,
  use a mesma URL Git efetiva no checkout e no clone. Um caminho relativo em SCP
  não equivale ao caminho absoluto de uma URI SSH. O slug da lista continua normalizado.
- A trava de commit é local ao worktree principal. Os worktrees de lote herdam
  o `core.hooksPath` comum. Se o repo usa um diretório versionado de hooks,
  configure-o na config comum do clone, por exemplo `git config --local core.hooksPath .githooks`.
- `retrofit_watch.py live-advance [<dono/repo>]` busca e avança com `--ff-only`.
  Sem argumento, tenta os repos listados. Confere o ramo e a árvore antes e
  depois do fetch. Ramo errado, árvore suja ou divergência conservam o HEAD.
  A atualização aponta para `refs/heads/main`, exige o SHA anterior esperado e
  mantém a trava do índice enquanto atualiza os arquivos.
  Se a nova conferência antes da busca encontrar outro ramo, grava
  `fora-da-main` sem buscar nem alterar refs.
  Se não conseguir ler HEAD ou a ref da main nessa conferência, grava `erro`
  com o detalhe `HEAD do clone ilegível` ou `refs/heads/main do clone ilegível`,
  respectivamente, também sem buscar nem alterar refs.
  Um arquivo apenas ignorado não impede o avanço se não precisar ser sobrescrito.
  Se `.git/rw-live-advance` permanecer após um erro, confira os SHAs, as travas,
  o índice e os arquivos do clone antes de remover a pendência e repetir. A pasta
  preserva o índice anterior e o diagnóstico local da tentativa.
  O resultado fica em `<dados>/live/<dono>/<repo>.json`.

## Preparação e selo

A lição local leva o mesmo `repo` do pedido e o nome da skill em `plugin` e
`skill`. A triagem não mistura origens. Se outro repo ou a loja disputar o
mesmo nome, a lição posterior fica segurada. O Stop confere localmente se a origem
do checkout ainda corresponde à identidade registrada com a evidência. O pedido
privado grava essa identidade em `origin_id` e o caminho rastreado em `skill_path`.
O `prepare` busca a `main` no clone dedicado, exige um `SKILL.md` regular no
caminho relativo exato do pedido e grava `repo`, `pasta` e `origin_id` em
`retrofit.json`. A porta reconfere esse caminho na base da publicação.
Uma troca de origem ou um pedido privado antigo sem caminho exige um novo pedido
ou resolução manual.
O ramo e o worktree pertencem a esse clone.

No lote privado, o executor usa apenas as lições do lote e o veredito.
Trabalha no `worktree` indicado e altera somente `pasta`. Registra uma entrada
datada no `CHANGELOG.md` da skill, sem bump de versão nem mudança de catálogo.
Faz um commit com o trailer `Retrofit-Mode: autonomous`, sem coautoria, e roda
`retrofit_watch.py seal <id> <lote> --licoes <n,...> [--fases <fases>]`. O selo
registra o patch e verifica segredo e caminho com usuário. Identidade e e-mail
legítimos do repo privado não reprovam essa verificação. O executor não publica.

A preparação não troca os links existentes. A adoção fica com o dono do repo,
após verificar o estado local e concluir a validação da publicação.

## Ensaio, publicação e aviso de startup

Depois do selo o revisor grava `diff.json` para o patch da skill. `publish` confere
os achados do mesmo relatório cujo patch validou. A verificação de segredo e caminho
e o cálculo do patch usam o mesmo par de commits fixado pelo rebase. O pre-push do
repo roda no worktree com o mesmo SHA e refs do push. Se o executável mudar
desde o ensaio, a porta aguarda um novo ensaio.
Antes de buscar ou publicar, confere o destino efetivo do Git, inclusive reescritas
de URL e `pushurl`. O slug sozinho não distingue servidores, transportes ou caminhos.
Sem prova da janela v2, o gate verde deixa o lote em `auto-dry` e conserva o remoto.
Só publicações que descendem dos reverts marcados no histórico Git da loja entram
na nova janela. Um revert em histórico independente mantém o ensaio enquanto a
ordem das publicações não puder ser comprovada. A medição usa refs locais e exige
uma varredura completa dos blobs selecionados.
O dono pode liberar esse motivo com `approve <id> <lote>`. A permissão vale para o
patch segurado, que inclui todos os arquivos alterados do lote e as posições das
edições. As exclusões das listas da loja, inclusive na verificação de segredo, valem
apenas no fluxo full. Uma emenda ou um rebase que desloque as edições exige nova
revisão e aprovação quando aplicável.

Depois do push, o registro preserva o SHA mesmo quando `local/ci` ou o avanço do clone
falham. O `local/ci` informa a última linha do pre-push real ou indica que a
saída ficou indisponível na retomada. A porta indica ao `gh` o servidor da origem conferida. Uma porta explícita de
SSH continua valendo para o Git, mas não é repassada à API de status. Uma porta
HTTPS explícita não padrão fica na URL absoluta da API (`/api/v3/repos/…/statuses/…`).
O argumento `--hostname` do `gh` identifica o servidor sem porta.
Resolva qualquer pendência do clone e rode `publish` novamente para concluir
esses efeitos sem repetir o push.
Em sessões assistidas, o startup lança o avanço em segundo plano. Se não conseguir
iniciar o processo, avisa na mesma sessão e registra o erro em `errors.log`,
mesmo se o avanço anterior tiver sido bem-sucedido. Os avisos de resultado são
separados por slug completo, mesmo que dois repos impliquem o mesmo destino de clone.
Registro ausente não gera aviso. Um registro presente que o startup não consegue
ler ou interpretar gera aviso de registro inválido para aquele repo.

Na retro manual de repo listado, a edição também fica no worktree do clone dedicado.
O push pelo pre-push exige confirmação direta do dono. Após o push, o executor
registra `local/ci` no SHA confirmado e avança o clone.
