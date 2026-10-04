# Changelog — `windows-disk-cleanup`

## [0.1.0] — 2026-10-04

Primeira versão, extraída de uma sessão real de limpeza em três discos (C:, E:, J:) conduzida com Kaizen
(PDCA, Gemba por artefato, passo reversível primeiro, poka-yoke). O C: foi de 7,8 para 71 GB livres e o E:
de 13,4 para 65 GB, com o usuário autorizando cada rodada. As 38 lições da sessão viraram o corpo da skill.

### Added
- `SKILL.md`: contrato com o usuário (somente leitura até a autorização, autorização **por rodada**), fluxo em 7
  passos e rodadas da mais segura para a que exige decisão, tabela das armadilhas mais caras, formato do relatório.
- `references/`: `measurement.md` (cobertura, hardlinks, I/O por processo para explicar o disco que enche),
  `catalog.md` (onde o espaço vai e como recuperar cada tipo), `google-drive.md` (limite → reinício → confirmação
  no log → limpeza), `wsl-docker.md` (medir dentro do vhdx; ler um vhdx antigo com 7-Zip), `safe-deletion.md`
  (manifesto, renomear antes, apagar a partir de lista, peculiaridades do Claude Code no Windows).
- `scripts/`: `scan.ps1` (inventário em C#, conta ocultos e de sistema, imprime a cobertura), `dups.ps1`
  (duplicatas por SHA256 completo com desconto de hardlink pelo ID físico NTFS), `zipverify.ps1` (zip × pasta por
  CRC32), `refs-scan.ps1` (referências a uma pasta com controle positivo), `room-check.ps1`, `delete-from-list.sh`,
  `drivefs-status.py` (banco do Drive lido no lugar), `recyclebin-list.ps1`, `steam-games.ps1`,
  `vscode-obsolete.ps1`, `summarize.ps1` e `selftest.ps1`, com 10 casos sabotados que precisam passar antes de
  confiar nas sondas.

### Evidência
- `selftest.ps1`: 10/10 PASS no Windows 10 (PowerShell 7). Na primeira rodada, o teste do `delete-from-list.sh`
  falhou: chamado do PowerShell, `bash` era o do WSL (`System32\bash.exe`), onde `/c/...` não existe. Agora o
  selftest procura o Git Bash explicitamente e copia o script para fora do caminho UNC.
- Os listadores (`recyclebin-list`, `steam-games`, `vscode-obsolete`, `drivefs-status`) rodaram na máquina real;
  o teste pegou e corrigiu a biblioteca Steam duplicada (`c:/...` × `C:\...`) e a linha de capacidade do Drive
  perdida na rotação do log.
- Afirmação corrigida antes de publicar: `uv cache prune` **não** tem `--dry-run` (uv 0.11.29, `--help` conferido).
- `skill-quality-audit` 0.4.0, auditoria completa. Baseline `rc=1` (1 erro, 3 avisos) → final `rc=0`, 0 erro, 0 aviso,
  com o comando documentado no `CLAUDE.md` (`--external off --no-changelog-required --desc-budget 0`). O validador
  oficial `skills-ref==0.1.1` (via `uvx`) deu `Valid skill`. O teste frio (cópia isolada da pasta) deu `rc=0` e o
  selftest 10/10.
  - B5 (CHANGELOG na pasta da skill) segue a convenção do repo: o CHANGELOG fica no plugin, como no `wsl-windows-onboarding`.
  - Claims (fase 2): números medidos ganharam data e proveniência (2026-10), o limite de 10 GB do Drive virou
    derivação (≤ 20% do espaço livre, o teto documentado), e o `SKILL.md` ganhou "Scope & verification".
- Regra 6 (caso inválido executado): quatro scripts saíam verdes com entrada errada (`vscode-obsolete` com editor
  inexistente, `zipverify` com zip inexistente, `scan` com raiz inexistente, `delete-from-list` com lista
  inexistente: todos `rc=0`). Agora recusam com `NOT FOUND`/`REFUSE` e `rc≠0`. `zipverify` passou a sair com `rc=1`
  quando algum zip não é IDENTICAL, e a aceitar `-Zips a,b` vindo de `pwsh -File`, que entrega a lista como uma string só.
- Editar pelo caminho `\\wsl.localhost\...` reescreve o arquivo com modo 644. Neste clone o `core.fileMode=false`
  faz o git ignorar o `chmod +x`, e o `ls -l` mostrava `rwx` enquanto o índice guardava `100644`. O bit dos
  `.sh`/`.py` foi gravado com `git update-index --chmod=+x` e conferido no índice (`git ls-files -s` → `100755`).

### Evals, rodada 1 (cenário sintético, 3 casos × com/sem skill)
- Resultado: 100% × 100% nas asserções, com +44% de tokens usando a skill. Nenhum caso discriminou: o cenário
  testava prudência genérica, que o modelo já tem sozinho. A rodada 2 vai testar o conhecimento específico da skill.
- O que os cenários quebraram e foi corrigido antes de publicar:
  - `selftest.ps1` passou a terminar com `exit 0` explícito. Sem ele, o código de saída do último comando nativo (o
    dry-run que recusa de propósito) vazava, e um selftest 10/10 saía com `rc≠0`.
  - Em dry-run, `delete-from-list.sh` passou a resumir com `would_delete=` (e `dry_run=1`). Assim a contagem
    não se confunde com o `deleted=` de uma exclusão real.
  - `scan.ps1` ganhou `-DirMin`, com padrão de 200 MB na raiz de um disco e 1 MB numa pasta, e o limiar das pastas
    passou a se adaptar ao alvo. A classe C# virou `WdcScanV2` porque o `Add-Type` não substitui um tipo já
    carregado na sessão, e a V1 tinha outra assinatura.
  - A afirmação sobre o `uv` passou a dizer que não existe flag de dry-run (`catalog.md` e `measurement.md`).
    A recomendação agora é medir antes e depois.
  - `zipverify.ps1 -Zips a,b` chamado por `pwsh -File` (ver a regra 6 acima).
- Achado na verificação pré-commit: `selftest.ps1 -WorkDir` apontando para uma pasta de uma rodada anterior
  deu 10/10 com um erro no meio. O hardlink não foi recriado porque já existia, e o check passou em cima da
  fixture velha. Agora o selftest recusa uma `-WorkDir` que tenha arquivos (`REFUSE`, `rc=2`). Conferido nos
  dois estados: pasta reaproveitada `rc=2`, pasta nova 10/10 `rc=0`.
