---
name: statusline
description: "Interactive wizard to configure Claude Code and Antigravity CLI status lines — model (+ effort), context bar, git branch/PR, cost, and 5h/weekly quotas. Cross-platform (Bash, PowerShell, Python). Triggers — statusline, status bar, footer, rate limit, usage window, antigravity statusline."
metadata:
  version: "1.6.1"
---

# Status Line Setup

Interactive wizard to configure a composable status line for **Claude Code** and/or **Antigravity CLI (`agy`)**.

## Step 0 — Detect & Select Target Harness

Check which harness directories exist on the machine:

```bash
ls -d ~/.claude ~/.gemini/antigravity-cli 2>/dev/null
```

Ask the user which target to configure (if only one exists, propose it as the default):
1. **Claude Code** — generates `~/.claude/claude-status.sh` (Bash + Python) or `~/.claude/claude-status.ps1` (PowerShell) and updates `~/.claude/settings.json`.
2. **Antigravity CLI** — generates `~/.config/antigravity-cli/statusline.py` (Python 3, cross-platform) and activates it via `/statusline`.
3. **Both** — runs both flows sequentially, sharing visual preferences.

## Progressive Disclosure — Read Only the Target Reference

Load **only** the reference matching the user's selection before generating scripts:

- Read `references/claude-code.md` when configuring **Claude Code** (OS detection, 12 composable sections, Bash + PowerShell templates, `effortLevel`, `rate_limits.five_hour`/`seven_day`, `pr`, locale-safe cost formatting, Windows troubleshooting).
- Read `references/antigravity-cli.md` when configuring **Antigravity CLI** (Python 3 template, JSON `stdin` schema, `model.effort` deduplication, 5h/weekly quota buckets by model family, Tokyo Night / ANSI palettes, `/statusline` activation, execution limits).

If configuring **both**, read both references and apply the same visual choices to each.

## Gotchas

- **Locale-safe cost formatting (Claude Code):** on comma-decimal locales (`pt-BR`, `de-DE`), `printf "%.2f"` fails unless prefixed with `LC_NUMERIC=C` (Bash) or `CultureInfo.InvariantCulture` (PowerShell).
- **Boolean `cost.estimated` (Antigravity CLI):** some payloads send `"estimated": true` alongside `total_usd`; always reject booleans (`not isinstance(val, bool)`) so `True` never renders as `$1.00`.
- **Protected config directory (Antigravity CLI):** agents cannot write into `~/.gemini/antigravity-cli/` directly; save the script at `~/.config/antigravity-cli/statusline.py` and activate via `/statusline`.
- **Failure budget (Antigravity CLI):** Antigravity auto-disables status line scripts after 30 consecutive non-zero exits — always exit `0` silently on empty or malformed `stdin`.
- **Field naming (Claude Code):** weekly limit is `rate_limits.seven_day` (not `weekly`), and `~/.claude/settings.json` requires `"type": "command"` (not `"enabled": true`).

## Shared Visual Preferences

Ask the user once (if they accept defaults, proceed immediately):

1. **Emojis:** keep default emojis or disable them (plain text).
2. **Color scheme:**
   - **Claude Code:** default ANSI colors or no colors.
   - **Antigravity CLI:** **Tokyo Night (24-bit truecolor)**, standard ANSI, or no colors.
3. **Context bar width:** progress bar characters (default: `20`).
4. **Section separator:** separator string (default: ` | `).
5. **Quota display mode (Antigravity CLI only):** show the comparison below and let the user pick (**default: `remaining`**, `100% → 0%`, matching `/usage`):
   - **`remaining` (default):** `⏱️ 5h 82% | 📅 semana 49%` — percentage left, counting down from `100%` (green `> 40%`, yellow `21–40%`, red `<= 20%`).
   - **`used`:** `⏳ 5h 18% | 📅 semana 51%` — percentage consumed, matching Claude Code (green `< 50%`, yellow `50–79%`, red `>= 80%`).

## Verification & Regression Sensor

Always verify the generated script with a full sample JSON **and** a minimal JSON (confirming graceful omission of conditional sections and `rc=0` on empty/malformed `stdin`).

When maintaining this skill's templates, run the bundled regression sensor to verify both Claude Code (12 sections + Bash execution) and Antigravity CLI (used/remaining modes + edge cases):

```bash
python3 scripts/validate_statusline_sensor.py
```
