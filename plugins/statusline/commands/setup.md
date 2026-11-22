---
description: "Interactive wizard to configure Claude Code and Antigravity CLI status lines — model (+ effort), context bar, git branch/PR, cost, and 5h/weekly quotas. Cross-platform (Bash, PowerShell, Python). Triggers — statusline, status bar, footer, rate limit, usage window, antigravity statusline."
metadata:
  version: "1.6.1"
---

## Status Line Setup (`/statusline:setup`)

This command launches the interactive multi-harness status line wizard defined in `../skills/statusline/SKILL.md`.

### Execution

1. Read `../skills/statusline/SKILL.md` for Step 0 (harness selection: **Claude Code**, **Antigravity CLI**, or **both**) and shared visual preferences.
2. Based on the selected harness, load only the needed reference:
   - **Claude Code:** `../skills/statusline/references/claude-code.md`
   - **Antigravity CLI:** `../skills/statusline/references/antigravity-cli.md`
3. Follow the reference steps end-to-end (prerequisites, section selection, backup, script generation, activation, and preview with both full and minimal test JSON).
