# Antigravity CLI Status Line Reference

Complete setup procedure, composable Python 3 template, JSON `stdin` schema, activation commands, and troubleshooting for **Google Antigravity CLI (`agy`)**.

## Table of Contents

- [Step 1 — Prerequisites & Script Path](#step-1--prerequisites--script-path)
- [Step 2 — Section Selection & JSON Schema](#step-2--section-selection--json-schema)
- [Step 3 — Quota Display Mode (Remaining vs Used)](#step-3--quota-display-mode-remaining-vs-used)
- [Step 4 — Generate Python 3 Script](#step-4--generate-python-3-script)
- [Step 5 — Activate in Antigravity CLI](#step-5--activate-in-antigravity-cli)
- [Step 6 — Preview & Verification](#step-6--preview--verification)
- [Operational Limits & Troubleshooting](#operational-limits--troubleshooting)

---

## Step 1 — Prerequisites & Script Path

Antigravity CLI invokes the configured status line command via shell (`sh -c` on Linux/macOS, `cmd /c` on Windows), pipes session telemetry as JSON into `stdin`, and renders `stdout` (with full ANSI color and multi-line support).

Check Python 3 availability:

```bash
which python3 || which python || echo "ERROR: Python 3 not found"
```

**Recommended script path:** `~/.config/antigravity-cli/statusline.py` (works across Linux, macOS, and Windows without `jq` or Bash/PowerShell drift).

> **Why `~/.config/antigravity-cli/` instead of `~/.gemini/antigravity-cli/`?**
> Agents running inside Antigravity CLI cannot write directly into `~/.gemini/antigravity-cli/` due to the built-in protection boundary. Storing the script in `~/.config/antigravity-cli/statusline.py` lets the agent create and iterate on the script cleanly, while activation happens via the `/statusline` TUI command.

## Step 2 — Section Selection & JSON Schema

Present the available sections and recommend the default set: **1, 2, 3, 4, 5, 6, 7** (model + effort, context bar, git branch, project folder, cost, 5h quota, weekly quota). Conditional sections (`git`, `cost`, `quota`, `vim`, `sandbox`, `subagents`) degrade gracefully and are silently omitted when absent.

| # | Section | Antigravity JSON Field(s) | Emoji | Default Color |
|---|---------|---------------------------|-------|---------------|
| 1 | Model + effort badge | `model.display_name`, `model.id`, `model.effort` | *(none or 🤖)* | Blue / Magenta |
| 2 | Context bar | `context_window.used_percentage`, `.context_window_size` | 📊 | Dynamic (green < 60%, yellow < 85%, red >= 85%) |
| 3 | Git branch | `workspace.current_dir` / `.project_dir` / `cwd` + `git rev-parse` | 🌿 | Magenta |
| 4 | Project folder | `workspace.current_dir` / `.project_dir` / `cwd` (basename) | 📁 | Cyan |
| 5 | Session cost | `cost.total_usd` (fallback: `total_cost_usd`, numeric `estimated`) | 💰 | Yellow |
| 6 | 5h usage quota | `quota.*` / `rate_limits.*` (`5h`/`short`/`session` or `reset_in_seconds <= 21600`) | ⏳ / ⏱️ | Dynamic |
| 7 | Weekly quota | `quota.*` / `rate_limits.*` (`week`/`7d`/`weekly` or `reset_in_seconds > 21600`) | 📅 | Dynamic |
| 8 | Vim mode *(optional)* | `vim.mode` | ⌨️ | Cyan |
| 9 | Sandbox badge *(optional)* | `sandbox.enabled` | 🛡️ | Green |
| 10 | Active subagents *(optional)* | `subagents` (`status == "running"`) | 🤖 | Cyan |

> **Schema gotchas:**
> - `cost.estimated` can be a **boolean** (`true`) alongside `cost.total_usd` — always ignore booleans (`not isinstance(val, bool)`) when reading cost fields so `True` never renders as `$1.00`.
> - `model.display_name` may already end with `(Medium)` / `(High)` while `model.effort` carries `"medium"` — strip the trailing duplicate parenthetical before appending `[effort]`.
> - `quota` exposes buckets by model family (e.g., `gemini-5h`, `gemini-weekly`, `claude-weekly`) with `remaining_fraction` (`0.0–1.0`). Prioritize buckets matching the active `model.id` family.

## Step 3 — Quota Display Mode (Remaining vs Used)

Show this side-by-side comparison so the user can choose their preferred quota perspective (**default: `remaining`**, counting down from `100%` to `0%`, matching Antigravity `/usage`):

- **`remaining` (default — matches Antigravity `/usage`):**
  `⏱️ 5h 82% | 📅 semana 49%` *(how much is left, `100% → 0%`; green `> 40%`, yellow `21–40%`, red `<= 20%`)*
- **`used` (matches Claude Code):**
  `⏳ 5h 18% | 📅 semana 51%` *(how much was consumed, `0% → 100%`; green `< 50%`, yellow `50–79%`, red `>= 80%`)*

## Step 4 — Generate Python 3 Script

Write `~/.config/antigravity-cli/statusline.py`, customizing `QUOTA_MODE` (`"remaining"` or `"used"`), `BAR_WIDTH` (default `20`), `SEPARATOR` (default `" | "`), `PALETTE` (`"tokyo-night"`, `"ansi"`, or `"none"`), and `SECTIONS`:

```python
#!/usr/bin/env python3
"""Custom statusline for Antigravity CLI."""

import json
import os
import re
import subprocess
import sys

# --- Configuration (customized by /statusline wizard) ---
QUOTA_MODE = "remaining"     # "remaining" (default, 100% -> 0% like /usage) or "used" (like Claude Code)
BAR_WIDTH = 20
SEPARATOR = " | "
PALETTE = "tokyo-night"      # "tokyo-night", "ansi", or "none"
USE_EMOJIS = True
SECTIONS = {1, 2, 3, 4, 5, 6, 7}  # 1:model 2:ctx 3:git 4:folder 5:cost 6:5h 7:weekly 8:vim 9:sandbox 10:subagents

PALETTES = {
    "tokyo-night": {
        "RST": "\033[0m", "BOLD": "\033[1m",
        "DIM": "\033[38;2;86;95;137m", "BLUE": "\033[38;2;122;162;247m",
        "CYAN": "\033[38;2;125;207;255m", "MAGENTA": "\033[38;2;187;154;247m",
        "GREEN": "\033[38;2;158;206;106m", "YELLOW": "\033[38;2;224;175;104m",
        "RED": "\033[38;2;247;118;142m", "WHITE": "\033[38;2;192;202;245m",
    },
    "ansi": {
        "RST": "\033[0m", "BOLD": "\033[1m",
        "DIM": "\033[0;90m", "BLUE": "\033[0;34m",
        "CYAN": "\033[0;36m", "MAGENTA": "\033[0;35m",
        "GREEN": "\033[0;32m", "YELLOW": "\033[0;33m",
        "RED": "\033[0;31m", "WHITE": "\033[0;37m",
    },
    "none": {k: "" for k in ("RST", "BOLD", "DIM", "BLUE", "CYAN", "MAGENTA", "GREEN", "YELLOW", "RED", "WHITE")},
}
C = PALETTES.get(PALETTE, PALETTES["tokyo-night"])


def _icon(emoji: str) -> str:
    return f"{emoji} " if USE_EMOJIS else ""


def get_git_branch(directory: str) -> str:
    if not directory or not os.path.isdir(directory):
        return ""
    try:
        res = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1.0, check=False,
        )
        if res.returncode == 0:
            branch = res.stdout.strip()
            if branch == "HEAD":
                sha = subprocess.run(
                    ["git", "-C", directory, "rev-parse", "--short", "HEAD"],
                    capture_output=True, text=True, timeout=1.0, check=False,
                )
                return sha.stdout.strip() if sha.returncode == 0 else "detached"
            return branch
    except Exception:
        pass
    return ""


def format_size_k(tokens: int) -> str:
    if not tokens or tokens <= 0:
        return "0k"
    if tokens == 1048576:
        return "1024k"
    return f"{round(tokens / 1000)}k"


def make_bar(pct: float, width: int = BAR_WIDTH) -> str:
    clamped = max(0.0, min(100.0, pct))
    filled = round((clamped / 100.0) * width)
    fill_ch, empty_ch = ("#", "-") if os.name == "nt" else ("█", "░")
    return fill_ch * filled + empty_ch * (width - filled)


def _quota_remaining_pct(entry: dict) -> float | None:
    if isinstance(entry.get("remaining_fraction"), (int, float)) and not isinstance(entry.get("remaining_fraction"), bool):
        return max(0.0, min(100.0, float(entry["remaining_fraction"]) * 100.0))
    if isinstance(entry.get("remaining_percentage"), (int, float)) and not isinstance(entry.get("remaining_percentage"), bool):
        return max(0.0, min(100.0, float(entry["remaining_percentage"])))
    if isinstance(entry.get("used_percentage"), (int, float)) and not isinstance(entry.get("used_percentage"), bool):
        return max(0.0, min(100.0, 100.0 - float(entry["used_percentage"])))
    return None


def _pick_by_family(entries: list[tuple[str, dict]], family_hints: list[str]) -> dict | None:
    for k_lower, val in entries:
        if any(h in k_lower for h in family_hints):
            return val
    return entries[0][1] if entries else None


def extract_quotas(data: dict, model_id: str) -> tuple[int | None, int | None]:
    """Return (five_hour_pct, weekly_pct) according to QUOTA_MODE."""
    quota = data.get("quota") or data.get("rate_limits")
    if not isinstance(quota, dict) or not quota:
        return None, None

    model_lower = (model_id or "").lower()
    family_hints = []
    if any(k in model_lower for k in ("claude", "opus", "sonnet")):
        family_hints = ["claude", "anthropic"]
    elif "gemini" in model_lower:
        family_hints = ["gemini"]
    elif any(k in model_lower for k in ("gpt", "openai")):
        family_hints = ["gpt", "openai"]

    five_h_entries: list[tuple[str, dict]] = []
    weekly_entries: list[tuple[str, dict]] = []
    other_entries: list[tuple[str, dict]] = []

    for key, val in quota.items():
        if not isinstance(val, dict):
            continue
        k_lower = str(key).lower()
        if any(tok in k_lower for tok in ("5h", "5-h", "5_h", "5hr", "5hour", "short", "session", "five_hour")):
            five_h_entries.append((k_lower, val))
        elif any(tok in k_lower for tok in ("week", "7d", "weekly", "seven_day")):
            weekly_entries.append((k_lower, val))
        else:
            reset_s = val.get("reset_in_seconds")
            if isinstance(reset_s, (int, float)) and not isinstance(reset_s, bool) and reset_s <= 21600:
                five_h_entries.append((k_lower, val))
            elif isinstance(reset_s, (int, float)) and not isinstance(reset_s, bool) and reset_s > 21600:
                weekly_entries.append((k_lower, val))
            else:
                other_entries.append((k_lower, val))

    five_h_entry = _pick_by_family(five_h_entries, family_hints)
    weekly_entry = _pick_by_family(weekly_entries, family_hints)
    if five_h_entry is None and weekly_entry is None and other_entries:
        weekly_entry = _pick_by_family(other_entries, family_hints)

    def _convert(entry: dict | None) -> int | None:
        if not entry:
            return None
        rem = _quota_remaining_pct(entry)
        if rem is None:
            return None
        return round(100.0 - rem) if QUOTA_MODE == "used" else round(rem)

    return _convert(five_h_entry), _convert(weekly_entry)


def _quota_color(pct: int) -> str:
    if QUOTA_MODE == "used":
        return C["GREEN"] if pct < 50 else (C["YELLOW"] if pct < 80 else C["RED"])
    return C["GREEN"] if pct > 40 else (C["YELLOW"] if pct > 20 else C["RED"])


def extract_cost(data: dict) -> float | None:
    cost = data.get("cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        return float(cost)
    if isinstance(cost, dict):
        for key in ("total_usd", "total_cost_usd", "usd", "estimated"):
            val = cost.get(key)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return float(val)
    return None


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return

    parts = []
    sep = f"{C['DIM']}{SEPARATOR}{C['RST']}" if SEPARATOR.strip() else SEPARATOR

    # 1. Model & effort
    model = data.get("model") or {}
    if isinstance(model, str):
        model_id, model_name, effort = model, model, ""
    else:
        model_id = str(model.get("id") or "")
        model_name = str(model.get("display_name") or model_id or "Antigravity")
        effort = str(model.get("effort") or "").strip()

    if 1 in SECTIONS:
        if effort:
            model_name = re.sub(rf"\s*\({re.escape(effort)}\)\s*$", "", model_name, flags=re.IGNORECASE)
            parts.append(f"{C['BOLD']}{C['BLUE']}{model_name}{C['RST']} {C['MAGENTA']}[{effort}]{C['RST']}")
        else:
            parts.append(f"{C['BOLD']}{C['BLUE']}{model_name}{C['RST']}")

    # 2. Context window
    if 2 in SECTIONS:
        ctx = data.get("context_window") or {}
        if isinstance(ctx, dict) and ctx:
            win_size = ctx.get("context_window_size") or 0
            used_pct = ctx.get("used_percentage")
            if used_pct is None and win_size > 0:
                total_tok = (ctx.get("total_input_tokens") or 0) + (ctx.get("total_output_tokens") or 0)
                used_pct = (total_tok / win_size) * 100.0
            if used_pct is not None:
                pct_val = float(used_pct)
                pct_int = round(pct_val)
                ctx_color = C["GREEN"] if pct_val < 60 else (C["YELLOW"] if pct_val < 85 else C["RED"])
                bar = make_bar(pct_val, width=BAR_WIDTH)
                size_str = f" of {format_size_k(int(win_size))}" if win_size else ""
                parts.append(
                    f"{_icon('📊')}{ctx_color}{pct_int}%{C['RST']}{C['WHITE']}{size_str}{C['RST']} "
                    f"{ctx_color}[{bar}]{C['RST']}"
                )

    workspace = data.get("workspace") or {}
    current_dir = (
        (workspace.get("current_dir") if isinstance(workspace, dict) else None)
        or (workspace.get("project_dir") if isinstance(workspace, dict) else None)
        or data.get("cwd")
        or ""
    )

    # 3. Git branch
    if 3 in SECTIONS:
        branch = get_git_branch(current_dir)
        if branch:
            parts.append(f"{_icon('🌿')}{C['MAGENTA']}{branch}{C['RST']}")

    # 4. Project folder
    if 4 in SECTIONS and current_dir:
        folder = os.path.basename(current_dir.rstrip("/\\")) or "/"
        parts.append(f"{_icon('📁')}{C['CYAN']}{folder}{C['RST']}")

    # 5. Session cost
    if 5 in SECTIONS:
        cost_usd = extract_cost(data)
        if cost_usd is not None:
            parts.append(f"{_icon('💰')}{C['YELLOW']}${cost_usd:.2f}{C['RST']}")

    # 6 & 7. 5h and weekly quotas
    if 6 in SECTIONS or 7 in SECTIONS:
        five_h_pct, weekly_pct = extract_quotas(data, model_id)
        if 6 in SECTIONS and five_h_pct is not None:
            q5_icon = "⏳" if QUOTA_MODE == "used" else "⏱️"
            parts.append(f"{_icon(q5_icon)}{C['WHITE']}5h{C['RST']} {_quota_color(five_h_pct)}{five_h_pct}%{C['RST']}")
        if 7 in SECTIONS and weekly_pct is not None:
            parts.append(f"{_icon('📅')}{C['WHITE']}semana{C['RST']} {_quota_color(weekly_pct)}{weekly_pct}%{C['RST']}")

    # 8. Vim mode (optional)
    if 8 in SECTIONS:
        vim = data.get("vim") or {}
        if isinstance(vim, dict) and vim.get("mode"):
            parts.append(f"{_icon('⌨️')}{C['CYAN']}{vim['mode']}{C['RST']}")

    # 9. Sandbox indicator (optional)
    if 9 in SECTIONS:
        sb = data.get("sandbox") or {}
        if isinstance(sb, dict) and sb.get("enabled") is True:
            parts.append(f"{_icon('🛡️')}{C['GREEN']}sandbox{C['RST']}")

    # 10. Running subagents (optional)
    if 10 in SECTIONS:
        subs = data.get("subagents")
        if isinstance(subs, list):
            running = sum(1 for s in subs if isinstance(s, dict) and s.get("status") == "running")
            if running > 0:
                parts.append(f"{_icon('🤖')}{C['CYAN']}{running} sub{C['RST']}")

    if parts:
        sys.stdout.write(sep.join(parts) + "\n")


if __name__ == "__main__":
    main()
```

## Step 5 — Activate in Antigravity CLI

Because `~/.gemini/antigravity-cli/settings.json` is protected from direct agent edits, instruct the user to run the built-in TUI slash command:

```text
/statusline python3 ~/.config/antigravity-cli/statusline.py
```

Other useful `/statusline` commands:
- `/statusline` — toggle visibility on/off
- `/statusline on` / `/statusline off` — explicit enable/disable
- `/statusline reset` (or `delete`) — restore built-in status line

**Manual configuration alternative (`~/.gemini/antigravity-cli/settings.json`):**

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.config/antigravity-cli/statusline.py",
    "enabled": true,
    "padding": 0,
    "stack_with_default": false
  }
}
```

- `padding`: blank lines inserted above the status line (default `0`).
- `stack_with_default`: when `true`, renders the custom status line *below* the built-in one instead of replacing it.

## Step 6 — Preview & Verification

Test the script with a full JSON payload and a minimal JSON payload:

```bash
# Full payload
printf '{"model":{"id":"opus-5.5","display_name":"Opus 5.5","effort":"xhigh"},"context_window":{"context_window_size":1000000,"used_percentage":22.0},"workspace":{"current_dir":"/tmp/my-app"},"cost":{"total_usd":21.46,"estimated":true},"quota":{"claude-5h":{"remaining_fraction":0.82},"claude-weekly":{"remaining_fraction":0.49}}}' | python3 ~/.config/antigravity-cli/statusline.py

# Minimal payload (verifies graceful omission of git, cost, and quotas)
printf '{"model":{"id":"gemini-4","display_name":"Gemini 4 Neon (Medium)","effort":"medium"},"cwd":"/tmp"}' | python3 ~/.config/antigravity-cli/statusline.py
```

## Operational Limits & Troubleshooting

| Constraint / Issue | Behavior / Fix |
|--------------------|----------------|
| Refresh throttle | Invoked at most once every **300 ms** on state change |
| Timeout | Execution halted after **5 seconds** (keep git timeout `<= 1s`) |
| Consecutive failures | Auto-disabled after **30 consecutive non-zero exits** — always exit `0` on empty/malformed `stdin` |
| Permission denied writing `~/.gemini/antigravity-cli/` | Keep the script in `~/.config/antigravity-cli/statusline.py` and activate via `/statusline` |
| Cost shows `$1.00` unexpectedly | `cost.estimated` is a boolean (`true`) in some payloads — filter `not isinstance(val, bool)` |
| Duplicate effort label `Model (Medium) [medium]` | Strip trailing `(<effort>)` from `display_name` before appending `[effort]` |
