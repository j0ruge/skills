# Changelog — release

## [2.0.3] — 2026-10-22

A entrada textual da invocação é explícita quando o host não substitui `$ARGUMENTS`, inclusive no Codex. Preserva o bloco para os hosts que fazem a substituição e a checagem de entrada vazia.

## [2.0.2] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Política Codex em agents/openai.yaml preserva a invocação explícita; o campo de topo é mantido para Claude/Cursor: aviso local para Codex, mas `G2 ERRO` e retorno 1 no auditor com validação externa estrita. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [2.0.1] — 2026-10-20

### Fixed

- **O passo 5 com `--path` listava o diretório inteiro.** O `[-- $PATH_FILTER]` vinha depois de um
  `-- <manifesto>` que já estava no comando. O git lê tudo depois do primeiro `--` como pathspec e
  soma os caminhos, então o segundo não filtrava. Medido em 2026-10-20:
  `git diff --stat A B -- package.json -- scripts` listou 16 arquivos de `scripts/`. Agora o
  passo 5 prefixa cada manifesto (`P=${PATH_FILTER:+${PATH_FILTER%/}/}`, `-- "${P}package.json"`).
  Medido no zsh e no bash, com e sem barra no fim do `--path`, saiu só o `package.json` do pacote.
- **Três trechos descreviam o método de contribuidores abandonado.** São a regra 7, a nota do
  template e o comentário do bloco do passo 3. Eles falavam em busca por e-mail e membros da org, mas
  o passo 3 usa a API de commits desde o `ed7ce32`, cuja mensagem diz que aquela abordagem falhava.
  O fallback por membros da org que a 1.3.0 cita nunca foi comando, e não volta como prosa.
- **O objetivo ainda mandava cobrir "desde a última tag do repositório",** a leitura que a 1.4.0
  corrigiu no passo 2. Agora diz "desde a release anterior da mesma série de tags (a história
  inteira na primeira)".
- **O `$NOTES_FILE` do passo 7 nunca era definido.** Agora é um `mktemp` fora do repo, que respeita
  a restrição de não mexer em arquivo do projeto.

### Changed

Prompt-audit (`/claude-api prompt-audit`, alvo Opus 5.5 e Fable 5.1). O relatório e o diff ficam
fora do repo, em `~/.claude/handoff/prompt-audit-2026-09-03/prompt-audit/release.{md,diff}`.

- Os três `**DO NOT**` em caixa alta viram duas restrições ditas em tom normal, sem perder nenhuma.
- A narrativa do passo 2 e o comentário do laço de contribuidores deixam o passado e a data ("the
  old …", "ran ONCE", "measured 2026-10-20") e ficam só com a razão. A evidência está na entrada 1.4.0
  abaixo.
- As frases sobre `$PATH_FILTER` (parse dos argumentos e passo 3) dizem que o passo 3 o acrescenta e
  o passo 5 o usa como prefixo.

Ficaram de fora, como flags do relatório sem medição: o `NEVER` da regra 7, que tem razão e uma falha
demonstrada na 1.1.0, o "Execute **in parallel**" e o "gh 2.85 has no isLatest". Também ficou de
fora o ruído `no matches found` do `ls *.csproj` no zsh do passo 1, em que o fallback funciona.

## [2.0.0] — 2026-10-20

### Changed

- **De comando a skill.** `commands/release.md` vira `skills/release/SKILL.md` (por `git mv`; o
  corpo é o da 1.4.0, salvo "This command" → "This skill"). A invocação continua
  `/release:release`, e no Cursor o nome continua `release`. O `plugin.json` troca `commands` por
  `skills`. O motivo é a régua: um plugin só de comandos fica fora do auditor da
  `skill-quality-audit` (o retrofit da 1.4.0 rodou com `[SKIP]`), e agora ele mede esta skill como
  mede as outras.
- **`disable-model-invocation: true`, decisão do dono.** Comando não dispara sozinho, mas skill
  dispara pela description, e o passo 7 cria tag e release sem perguntar. Com o campo, a skill só
  roda chamada pelo nome, como o comando de antes. O campo fica no topo do frontmatter porque o
  Claude Code e o Cursor só o leem ali (a doc do Cursor: "When `true`, the skill is only included
  when explicitly invoked via `/skill-name`"). **Exceção declarada:** o mesmo campo dá ERRO G2
  (`skills-ref==0.1.1 validate`: "Unexpected fields in frontmatter") e AVISO A4 na
  `skill-quality-audit`, e um WARNING no `validate-versions`. Os dois só aceitam o campo como custo
  quando o plugin declara apenas `claude-code`, por causa do upload para claude.ai e para a API, que
  seguem o `skills-ref`. Este plugin vai ao Claude Code e ao Cursor, que leem o campo, e o
  marketplace não publica no claude.ai. Ensinar isso ao auditor fica como tarefa separada. O
  `compatibility` explica o campo.
- **Description nova, a mesma nos três lugares** (`SKILL.md`, `plugin.json`, `marketplace.json`),
  com 345 chars e `Triggers —`, e dizendo o que a 1.4.0 trouxe (série de tags, primeira release,
  edição da versão já publicada). A `cursor_description` do `install.py` sai, porque a entrada
  passa a `source_type: "skill"` e copia o `SKILL.md`. Ela ainda descrevia a 1.3.0.
- **README.** A tabela de plataformas diz "Skill (runs only when invoked)". O bloco do `release`
  diz como ele é invocado. No modo Cursor, o exemplo "Cria a release 2.1.0 com notas de versao"
  sai da lista de pedidos por contexto, porque com o campo ele não dispara mais, e vira uma frase
  com a invocação pelo nome.

Teste frio: o `_install_from_skill_dir` gera um `release/SKILL.md` só, com o frontmatter em YAML
válido (`name`, `description`, `disable-model-invocation`, `compatibility`, sem `metadata`). No
corpo, o bloco `$ARGUMENTS` sai, como na adaptação do comando.

Dívida que a auditoria aponta e esta versão não toca (INFO):

- **F2:** sem seção de gotchas. As lições da 1.4.0 estão nos passos 2, 3 e 7.
- **F4:** sem evals. Com o campo, não há gatilho a medir, mas o comportamento segue sem caso de
  teste.
- **D1:** 7 trechos marcados. São a versão e a description, exemplos de entrada e o caso medido, que
  já está datado.

## [1.4.0] — 2026-10-20

### Fixed

- **A versão já publicada por outra ferramenta ganhava uma segunda tag.** O passo 2 tomava como
  `LAST_TAG` a maior tag do repo (`git tag -l --sort=-version:refname | head -1`), e o passo 7 criava
  `v$NEW_VERSION` sem perguntar. Medido em 2026-10-20 num monorepo com tags `<pacote>-v<versão>`,
  cujo `release.sh` acabara de publicar `object-storage-v1.0.0` com o tarball: o `head -1` devolveu
  a própria tag, com 0 commits depois dela, e o passo 7 teria criado `v1.0.0` no mesmo commit, uma
  segunda release sem o artefato que viraria a "Latest". Agora o passo 2 lê os prefixos em uso
  (`v`, `<pacote>-v`), monta `TAG="$TAG_PREFIX$NEW_VERSION"` e, com a tag já existente, o passo 7
  **edita** as notas dela (`gh release edit --notes-file`), levando o que o corpo já tinha (uma linha
  de checksum, por exemplo), em vez de criar outra.
- **A primeira release abortava.** "Sem tags, aborte" virou o intervalo da história inteira até a
  tag (`git hash-object -t tree /dev/null` como base do `git diff`). Na release acima, 75 commits e
  93 arquivos.
- **Contribuidores vazios no zsh.** O `for sha in $COMMIT_SHAS` rodava uma volta só (o zsh não
  divide variável sem aspas), com todos os shas juntos na URL, e o `2>/dev/null` escondia o erro:
  0 contribuidores, rc 0. Medido em 2026-10-20 com o passo 3 literal sobre 3 commits: zsh, 1 volta;
  bash, 3. Agora é `git log … | while read -r sha`, medido nos dois shells (`@j0ruge` sobre 75 commits).

### Changed

- O `LAST_TAG` vem de `git describe --match "${TAG_PREFIX}[0-9]*" --exclude "$TAG"`: a tag anterior
  da mesma série, alcançável a partir do fim do intervalo. Medido num repo com as séries `v` e `api-v`:
  `v1.2.0` → `v1.1.0..HEAD`; a edição de `v1.1.0` → `v1.0.0..v1.1.0`; `api-v0.3.0` → `api-v0.2.0..HEAD`.
  Os passos 3 e 5 usam `"$LOG_RANGE"` e `"$DIFF_FROM" "$END"` no lugar de `$LAST_TAG..HEAD`.
- Zero commits no intervalo para o comando: não há o que lançar.
- Quando o `CLAUDE.md` ou o `AGENTS.md` do projeto reserva a release a uma pessoa, essa regra vence
  o "sem pedir confirmação" do passo 7.
- O `gh` 2.85 não tem `isLatest` no `--json` do `gh release view` ("Unknown JSON field"): o passo 2
  usa o `gh release list`, que mostra a coluna Latest.

## [1.3.0] — 2026-04-01

### Changed

- Resolução de contribuidores passa a usar a GitHub commits API e, quando o autor não
  resolve por ela, faz fallback por cross-reference de org membership — entrega usernames
  reais do GitHub em vez de depender do nome de autor do git.

## [1.2.0] — 2026-03-25

### Added

- **Multi-stack project detection** — auto-detects project name from `.sln`, `.csproj`, `package.json`, `Cargo.toml`, `go.mod` (priority order)
- **`--path` filter** — filter commits/diffs to a subdirectory for monorepo component releases (e.g., `1.0.0 --path LicenceManager/`)
- **Multi-stack dependency detection** — detects dependency changes from `*.csproj`/`Directory.Build.props` (C#), `package.json` (Node), `go.mod` (Go), `Cargo.toml` (Rust), `pyproject.toml`/`requirements.txt` (Python)
- Quality rule #8: path filter scoping for commits and file changes

### Changed

- Release target branch now uses current branch (`git branch --show-current`) instead of hardcoded `main`
- Dependencies template section is now language-agnostic (removed hardcoded "Node.js, TypeScript")
- Description updated to mention multi-stack support

## [1.1.0] — 2026-03-25

### Fixed

- **Contributors listed wrong usernames** — git author names (`JorUge`, `Jorge Ferrari`) don't match GitHub usernames (`j0ruge`). Now resolves via `gh api` email lookup instead of `git log --format="%aN"`
- Exclude bot accounts (`noreply@anthropic.com`) from contributors list
- Same person with multiple git author names no longer appears as multiple contributors

### Changed

- Contributors section now uses `gh api /search/users?q=EMAIL` to resolve actual GitHub usernames
- Added quality rule #7: contributors must be resolved GitHub usernames, never fabricated

## [1.0.0] — 2026-03-16

### Added

- Initial release of the `release` plugin
- Automated GitHub Release creation via `gh CLI`
- Categorized release notes from git history (conventional commits)
- Dynamic project name detection (package.json or git directory name)
- PT-BR release notes with emoji-categorized sections
- Dependency diff analysis from package.json changes
- PR and contributor aggregation
