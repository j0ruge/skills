# Onde o hook mora: settings, plugin ou frontmatter

Fontes (lidas em 2026-09-30, Claude Code 2.1.283): https://code.claude.com/docs/en/hooks#hook-locations,
`#reference-scripts-by-path`, `#hooks-in-skills-and-agents`, `#disable-or-remove-hooks`,
`#workspace-trust`; https://code.claude.com/docs/en/plugins/components#hooks;
`/en/plugins/manifest-reference#environment-variables`; `/en/plugins/cli-reference#reload-plugins`;
`/en/settings-reference#hooks-and-automation`.

## Locais

| Local | Escopo | Recarga | Rótulo no `/hooks` |
|---|---|---|---|
| `~/.claude/settings.json` | você, todos os projetos | file watcher, sozinho | User Settings |
| `.claude/settings.json` | projeto, versionado | file watcher | Project Settings |
| `.claude/settings.local.json` | projeto, só você | file watcher | Local Settings |
| plugin `hooks/hooks.json` | quem habilita o plugin | `/reload-plugins` ou sessão nova | Plugin Hooks |
| frontmatter de skill | a partir do momento em que a skill roda, até o fim da sessão | — | — |
| frontmatter de subagente | só enquanto o subagente roda (`Stop` vira `SubagentStop`) | — | — |
| settings gerenciado | organização | — | — |

O `/hooks` é um navegador **só de leitura**. Para mudar, edite o JSON.

## Plugin

```
meu-plugin/
  .claude-plugin/plugin.json   # sem chave "hooks" (ou "hooks": "./hooks/hooks.json")
  hooks/hooks.json             # {"description": "...", "hooks": {Evento: [grupos]}}
  scripts/<hook>.py
```

- **`plugin.json`:** `"hooks": "./hooks"` (diretório) quebra o `claude plugin install` com
  `hooks: Invalid input`. O mesmo vale para `"agents": "./agents"`. O `hooks/hooks.json` é
  descoberto sozinho. O manifesto aceita um path de arquivo, um objeto inline ou um array, e
  isso **se soma** ao `hooks/hooks.json`. Confira com
  `claude plugin validate <dir-do-plugin>`.
- **Quando os hooks de plugin rodam:** desde que o plugin está **habilitado**, e não só quando
  uma skill dele roda. Para restringir, use o matcher ou filtre no script.
- **Variáveis de ambiente** (exportadas para o processo do hook, **não** para o Bash do Claude):

  | Variável | Aponta para | Guardar estado? |
  |---|---|---|
  | `${CLAUDE_PLUGIN_ROOT}` | diretório da versão instalada; **muda a cada update** | não |
  | `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/<id>/`. Sobrevive a updates, é criado na 1ª referência e apagado no uninstall (a menos que `--keep-data`) | sim |
  | `${CLAUDE_PROJECT_DIR}` | raiz do projeto onde a sessão começou | — |
  | `CLAUDE_PLUGIN_OPTION_<KEY>` | valores de `userConfig` do plugin | — |

  `${user_config.*}` só é substituído na **forma exec**. Na forma shell, a referência dá erro.
  Use a variável `CLAUDE_PLUGIN_OPTION_<KEY>`.
- **Dev local:** `claude --plugin-dir <dir>` carrega o plugin sem instalar. Um marketplace local
  (diretório) carrega no lugar, e edições entram com `/reload-plugins`, que imprime
  `Reloaded: N plugins · … · N hooks`.
- **Erros de carga:** aparecem como `Failed to load hooks from <path>` na aba Errors do
  `/plugin`.

## Frontmatter de skill

```yaml
---
name: minha-skill
description: …
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/<check>.sh"
          once: true
---
```

O hook registra quando a skill é invocada, por você ou pelo Claude, e fica ativo pelo resto da
sessão, inclusive nos turnos seguintes. `once: true` remove o hook depois da 1ª execução com
sucesso. É o único lugar em que `once` vale. O campo `hooks` no frontmatter é do Claude Code e
fica fora do spec agentskills.io, que só lista `name`, `description`, `license`,
`compatibility`, `metadata` e `allowed-tools`. Validadores estritos reclamam dele.

## Trust e desligamento

- **Sessão interativa:** nenhum hook de arquivo de settings roda antes do trust dialog da
  pasta. Isso vale também para o `~/.claude/settings.json`.
- **`-p` e SDK:** a pasta conta como confiável, e os hooks commitados num `.claude/settings.json`
  **rodam**. Contra um repositório de terceiros, use `--bare` ou
  `--settings '{"disableAllHooks": true}'`.
- **Hooks em frontmatter:** os de skill de projeto seguem a regra dos settings. Os de subagente
  de projeto exigem trust aceito, e o `-p` não conta como aceite.
- **`disableAllHooks: true`:** desliga todos os hooks e também o status line. Um `false` no
  projeto vence um `true` do usuário. Fora do gerenciado, não desliga os hooks gerenciados. Não
  há como desligar um hook só, mantendo-o na config.
- **`allowManagedHooksOnly`** (gerenciado): só rodam hooks gerenciados, do SDK e de plugins
  force-enabled.
