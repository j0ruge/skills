# Changelog — release

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
