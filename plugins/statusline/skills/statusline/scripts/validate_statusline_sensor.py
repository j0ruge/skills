#!/usr/bin/env python3
"""Deterministic regression sensor for the statusline skill templates.

Validates:
1. Claude Code reference (references/claude-code.md):
   - Presence of all 12 sections and critical invariants (LC_NUMERIC=C,
     InvariantCulture, ConvertFromUtf32, -ExecutionPolicy Bypass, effortLevel,
     five_hour, seven_day, review_state, ASCII Windows bar).
   - Live execution of the assembled Bash script against full JSON and minimal
     JSON (confirming locale-safe cost formatting and graceful omission).
2. Antigravity CLI reference (references/antigravity-cli.md):
   - Live execution of the extracted Python template in both QUOTA_MODE="used"
     and QUOTA_MODE="remaining", plus edge cases: minimal JSON omission,
     boolean cost.estimated, duplicate effort suffix, empty/malformed stdin.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SKILL_DIR = Path(__file__).resolve().parent.parent
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def extract_fenced_blocks(md_text: str, lang: str) -> list[str]:
    pat = re.compile(rf"```{re.escape(lang)}\r?\n(.*?)```", re.DOTALL)
    return [m.group(1) for m in pat.finditer(md_text)]


def check_claude_code(ref_path: Path) -> list[str]:
    errors: list[str] = []
    if not ref_path.exists():
        return [f"missing Claude Code reference: {ref_path}"]
    text = ref_path.read_text(encoding="utf-8")

    # 1. Verify all 12 sections exist
    for i in range(1, 13):
        if f"**Section {i} —" not in text:
            errors.append(f"claude-code: missing Section {i} block")

    # 2. Verify critical non-regression invariants from v1.5.2
    invariants = [
        ("LC_NUMERIC=C", "locale-safe Bash cost formatting"),
        ("InvariantCulture", "locale-safe PowerShell cost formatting"),
        ("ConvertFromUtf32", "PowerShell 5.1 safe emoji encoding"),
        ("-ExecutionPolicy Bypass", "Windows PowerShell invocation flag"),
        ("effortLevel", "Claude Code effortLevel badge"),
        ("rate_limits.five_hour", "5h usage window field"),
        ("rate_limits.seven_day", "weekly usage window field"),
        ("review_state", "PR review state field"),
        ('BAR_FILLED="#"', "Windows ASCII progress bar fallback"),
    ]
    for token, desc in invariants:
        if token not in text:
            errors.append(f"claude-code: missing invariant '{token}' ({desc})")

    # 3. Assemble and execute the Bash template (header + sections 1-5,10,11,12 + footer)
    bash_blocks = extract_fenced_blocks(text, "bash")
    header = next((b for b in bash_blocks if "# Claude Code Status Line Script" in b), None)
    footer = next((b for b in bash_blocks if 'separator="{SEPARATOR}"' in b), None)
    section_markers = [
        'parts+=("🤖',
        'parts+=("📊',
        'parts+=("🌿',
        'parts+=("📁',
        'parts+=("💰',
        'parts+=("⏳ 5h',
        'parts+=("📅 semana',
        'parts+=("${PR_ICON}',
    ]
    selected_sections = []
    for marker in section_markers:
        blk = next((b for b in bash_blocks if marker in b), None)
        if blk is None:
            errors.append(f"claude-code: could not locate Bash block for {marker!r}")
        else:
            selected_sections.append(blk)

    if not header or not footer or len(selected_sections) != len(section_markers):
        return errors

    script = "\n".join([header, *selected_sections, footer])
    script = (
        script.replace("{BAR_WIDTH}", "20")
        .replace("{SEPARATOR}", " | ")
        .replace("{GENERATION_DATE}", "2026-11-22")
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "claude-status.sh"
        script_path.write_text(script, encoding="utf-8")
        os.chmod(script_path, 0o755)

        # Case A: full JSON
        full_json = (
            '{"model":{"display_name":"Opus 4.6"},'
            '"context_window":{"used_percentage":42,"context_window_size":1000000},'
            f'"workspace":{{"current_dir":"{tmpdir}","project_dir":"{tmpdir}"}},'
            '"cost":{"total_cost_usd":0.05},'
            '"rate_limits":{"five_hour":{"used_percentage":23},"seven_day":{"used_percentage":81}},'
            '"pr":{"number":128,"review_state":"approved"}}'
        )
        res_full = subprocess.run(
            ["bash", str(script_path)],
            input=full_json, text=True, capture_output=True, timeout=5, check=False,
        )
        if res_full.returncode != 0:
            errors.append(f"claude-code full JSON failed rc={res_full.returncode}: {res_full.stderr.strip()}")
        else:
            out = strip_ansi(res_full.stdout).strip()
            for expected in ("Opus 4.6", "42% of 1000k", "$0.05", "5h 23%", "semana 81%", "#128"):
                if expected not in out:
                    errors.append(f"claude-code full JSON missing {expected!r} in output: {out!r}")

        # Case B: minimal JSON (graceful omission of rate_limits and pr)
        min_json = (
            '{"model":{"display_name":"Sonnet 4.6"},'
            '"context_window":{"used_percentage":10,"context_window_size":200000},'
            f'"workspace":{{"current_dir":"{tmpdir}"}},'
            '"cost":{"total_cost_usd":0.01}}'
        )
        res_min = subprocess.run(
            ["bash", str(script_path)],
            input=min_json, text=True, capture_output=True, timeout=5, check=False,
        )
        if res_min.returncode != 0:
            errors.append(f"claude-code minimal JSON failed rc={res_min.returncode}: {res_min.stderr.strip()}")
        else:
            out_min = strip_ansi(res_min.stdout).strip()
            for forbidden in ("5h ", "semana ", "#"):
                if forbidden in out_min:
                    errors.append(f"claude-code minimal JSON should omit {forbidden!r}, got: {out_min!r}")

    return errors


def check_antigravity_cli(ref_path: Path) -> list[str]:
    errors: list[str] = []
    if not ref_path.exists():
        return [f"missing Antigravity CLI reference: {ref_path}"]
    text = ref_path.read_text(encoding="utf-8")

    py_blocks = extract_fenced_blocks(text, "python")
    template = next((b for b in py_blocks if "Custom statusline for Antigravity CLI" in b), None)
    if not template:
        return ["antigravity-cli: missing Python template block"]

    with tempfile.TemporaryDirectory() as tmpdir:
        proj_dir = Path(tmpdir) / "my-app"
        proj_dir.mkdir()
        script_rem = Path(tmpdir) / "statusline_rem.py"
        script_used = Path(tmpdir) / "statusline_used.py"
        script_rem.write_text(template, encoding="utf-8")
        script_used.write_text(
            template.replace('QUOTA_MODE = "remaining"', 'QUOTA_MODE = "used"', 1),
            encoding="utf-8",
        )

        full_json = (
            '{"model":{"id":"opus-5.5","display_name":"Opus 5.5","effort":"xhigh"},'
            '"context_window":{"context_window_size":1000000,"used_percentage":22.0},'
            f'"workspace":{{"current_dir":"{proj_dir}"}},'
            '"cost":{"total_usd":21.46,"estimated":true},'
            '"quota":{"claude-5h":{"remaining_fraction":0.82},"claude-weekly":{"remaining_fraction":0.49},'
            '"gemini-5h":{"remaining_fraction":0.10},"gemini-weekly":{"remaining_fraction":0.10}}}'
        )

        # Case 1: used mode (default)
        res_used = subprocess.run(
            [sys.executable, str(script_used)],
            input=full_json, text=True, capture_output=True, timeout=5, check=False,
        )
        if res_used.returncode != 0:
            errors.append(f"antigravity used mode failed rc={res_used.returncode}: {res_used.stderr.strip()}")
        else:
            out = strip_ansi(res_used.stdout).strip()
            for expected in ("Opus 5.5 [xhigh]", "22% of 1000k", "my-app", "$21.46", "5h 18%", "semana 51%"):
                if expected not in out:
                    errors.append(f"antigravity used mode missing {expected!r} in output: {out!r}")

        # Case 2: remaining mode
        res_rem = subprocess.run(
            [sys.executable, str(script_rem)],
            input=full_json, text=True, capture_output=True, timeout=5, check=False,
        )
        if res_rem.returncode != 0:
            errors.append(f"antigravity remaining mode failed rc={res_rem.returncode}: {res_rem.stderr.strip()}")
        else:
            out_r = strip_ansi(res_rem.stdout).strip()
            for expected in ("5h 82%", "semana 49%"):
                if expected not in out_r:
                    errors.append(f"antigravity remaining mode missing {expected!r} in output: {out_r!r}")

        # Case 3: boolean cost.estimated + duplicate effort suffix + minimal omission
        edge_json = (
            '{"model":{"id":"gemini-4","display_name":"Gemini 4 Neon (Medium)","effort":"medium"},'
            f'"cwd":"{proj_dir}",'
            '"cost":{"estimated":true}}'
        )
        res_edge = subprocess.run(
            [sys.executable, str(script_used)],
            input=edge_json, text=True, capture_output=True, timeout=5, check=False,
        )
        if res_edge.returncode != 0:
            errors.append(f"antigravity edge JSON failed rc={res_edge.returncode}: {res_edge.stderr.strip()}")
        else:
            out_e = strip_ansi(res_edge.stdout).strip()
            if "Gemini 4 Neon [medium]" not in out_e:
                errors.append(f"antigravity failed to deduplicate effort suffix: {out_e!r}")
            if "$1.00" in out_e or "💰" in out_e:
                errors.append(f"antigravity treated boolean cost.estimated as money: {out_e!r}")
            if "5h " in out_e or "semana " in out_e:
                errors.append(f"antigravity should omit absent quotas: {out_e!r}")

        # Case 4: empty & malformed stdin must exit 0 cleanly (avoid 30-failure auto-disable)
        for label, bad_in in (("empty", ""), ("malformed", "{not-json")):
            res_bad = subprocess.run(
                [sys.executable, str(script_used)],
                input=bad_in, text=True, capture_output=True, timeout=5, check=False,
            )
            if res_bad.returncode != 0 or res_bad.stdout.strip():
                errors.append(
                    f"antigravity {label} stdin must exit 0 silently; got rc={res_bad.returncode}, out={res_bad.stdout!r}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--claude-ref",
        type=Path,
        default=DEFAULT_SKILL_DIR / "references" / "claude-code.md",
        help="Path to Claude Code reference markdown",
    )
    parser.add_argument(
        "--antigravity-ref",
        type=Path,
        default=DEFAULT_SKILL_DIR / "references" / "antigravity-cli.md",
        help="Path to Antigravity CLI reference markdown",
    )
    args = parser.parse_args()

    errors = []
    errors.extend(check_claude_code(args.claude_ref))
    errors.extend(check_antigravity_cli(args.antigravity_ref))

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print("OK: Claude Code (12 sections + Bash execution) and Antigravity CLI (used/remaining/edge cases) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
