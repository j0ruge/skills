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
  O clone só fica disponível após a validação final. Se a plataforma ou o sistema
  de arquivos não oferecer movimentação sem substituição, o setup recusa a instalação.
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
  Um arquivo apenas ignorado não impede o avanço se não precisar ser sobrescrito.
  O resultado fica em `<dados>/live/<dono>/<repo>.json`.

## Preparação e selo

A lição local leva o mesmo `repo` do pedido e o nome da skill em `plugin` e
`skill`. A triagem não mistura origens. Se outro repo ou a loja disputar o
mesmo nome, a lição posterior fica segurada. O `prepare` busca a `main`
no clone dedicado, localiza a pasta rastreada da skill e grava `repo`, `pasta` e
`origin_id` em `retrofit.json`. A impressão digital vem do pedido e vincula o
lote à origem da sessão. Uma troca de destino exige um novo pedido.
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

Depois do selo o revisor grava `diff.json` para o patch da skill. `publish` confere a
revisão e executa o pre-push do repo no worktree, com o mesmo SHA e refs do push.
Antes de buscar ou publicar, confere o destino efetivo do Git, inclusive reescritas
de URL e `pushurl`. O slug sozinho não distingue servidores, transportes ou caminhos.
Sem prova da janela v2, o gate verde deixa o lote em `auto-dry` e conserva o remoto.
O dono pode liberar esse motivo com `approve <id> <lote>`. A permissão vale para o
patch segurado, que inclui todos os arquivos alterados do lote. As exclusões das listas
da loja valem apenas no fluxo full. Emenda que altera o patch exige nova revisão e
aprovação quando aplicável.

Depois do push, o registro preserva o SHA mesmo quando `local/ci` ou o avanço do clone
falham. A porta indica ao `gh` o servidor da origem conferida. Uma porta explícita de
SSH continua valendo para o Git, mas não é repassada à API de status. Uma porta
HTTPS explícita não padrão fica na URL absoluta da API (`/api/v3/repos/…/statuses/…`).
O argumento `--hostname` do `gh` identifica o servidor sem porta.
Rode `publish` novamente para concluir esses efeitos sem repetir o push.
Em sessões assistidas, o startup lança o avanço em segundo plano. Se não conseguir
iniciar o processo, avisa na mesma sessão e registra o erro em `errors.log`,
mesmo se o avanço anterior tiver sido bem-sucedido. Os avisos de resultado são
separados por slug completo, mesmo que dois repos impliquem o mesmo destino de clone.
Registro ausente não gera aviso. Um registro presente que o startup não consegue
ler ou interpretar gera aviso de registro inválido para aquele repo.

Na retro manual de repo listado, a edição também fica no worktree do clone dedicado.
O push pelo pre-push exige confirmação direta do dono. Após o push, o executor
registra `local/ci` no SHA confirmado e avança o clone.
