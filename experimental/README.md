# Skills experimentais

Estas skills já servem a quem as escreveu, mas **ainda não temos maturidade para recomendar o uso**.
Elas ficam versionadas aqui para não se perderem fora do git.

## Diferença em relação a `plugins/`

- **Ninguém as instala pela loja.** Elas não entram no `.claude-plugin/marketplace.json`, no catálogo
  Codex (`.agents/plugins/marketplace.json`), no `install.py` nem na tabela de plugins do README.
- **Não têm versão nem `plugin.json`.** Cada uma registra suas mudanças no próprio `CHANGELOG.md`, com
  data e motivo.
- **O `validate-versions.py` não as confere,** porque o check 7 lê só `plugins/*/skills/*`. O sensor
  delas é o auditor da `skill-quality-audit`, rodado à mão a partir da raiz:

  ```bash
  python3 plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py \
    experimental/<skill> --claims --desc-budget 0
  ```

- **O `check-private-names.py` varre esta pasta** como varre o resto da loja.

## Skills

| Skill | Escopo | Onde foi conferida |
|---|---|---|
| `rust` | Toolchain, Cargo, lockfile e escolha da evidência | Uma aplicação desktop: Rust 1.97.0, Ubuntu 24.04 x86_64 |
| `gpui` | API GPUI por versão, ambiente gráfico Linux e QA na janela nativa | A mesma aplicação: GPUI 0.2.2, gpui-component 0.5.1, X11 |

O arquivo `agents/openai.yaml` de cada uma é a interface do Codex.

## Instalar por symlink

```bash
ln -s "$PWD/experimental/rust" ~/.codex/skills/rust   # a partir da raiz deste clone
```

O link aponta para a árvore de trabalho deste clone. Se você fizer checkout de um branch sem
`experimental/`, a skill some do harness até a árvore voltar para `main`. Para editar a loja em outro
branch, use um worktree, como o `/retrofit-skill` já faz, e deixe este checkout em `main`.

## Promover para `plugins/`

Uma skill sai daqui quando o uso real em mais de um projeto justificar a recomendação. Antes disso:

1. Zere os ERRO do auditor.
2. Reescreva a `description` no padrão da loja (`CLAUDE.md`, *Skill description guidelines*).
3. Siga *Adding a New Plugin* no `CLAUDE.md`.
4. Registre a promoção no `CHANGELOG.md` da skill.
