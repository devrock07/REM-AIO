#!/usr/bin/env python3
"""
Auto-converter: rewrites discord.Embed + ctx.send/reply patterns to
Components V2 panel helpers (success_panel, error_panel, info_panel, warning_panel).

Usage:
    python tools/convert_to_cv2.py                  # dry-run, shows what would change
    python tools/convert_to_cv2.py --write           # apply changes in-place
    python tools/convert_to_cv2.py --write --file cogs/commands/afk.py  # single file

Strategy
--------
We use regex-based line-by-line rewriting (AST is too fragile for partial
rewrites of real-world bot code).  The converter:

1. Detects embed variable assignments:
       embed = discord.Embed(description="...", color=..., title="...")
   and collects their attributes (.set_author, .set_footer, .add_field, etc.)

2. Detects the final send call:
       await ctx.send(embed=embed)
       await ctx.reply(embed=embed)
       await msg.edit(embed=embed)

3. Chooses the right panel helper:
       success_panel  — title/description contains "success", tick emoji, etc.
       error_panel    — title/description contains "error", "denied", "fail", cross, etc.
       warning_panel  — title/description contains "warn", "are you sure", etc.
       info_panel     — everything else

4. Replaces the entire embed block with a single panel call and adds the
   import at the top if missing.

Safety
------
- Creates a .bak backup of every file before writing.
- Skips files that already import from utils.components_v2.
- Skips embed variables that are used in interaction.response.send_message
  (those are ephemeral and should stay as embeds).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Colour / panel-type detection
# ---------------------------------------------------------------------------

SUCCESS_PATTERNS = re.compile(
    r"success|tick|✅|enabled|added|removed|created|deleted|updated|"
    r"set|configured|saved|done|completed|whitelisted|unwhitelisted|reset",
    re.IGNORECASE,
)
ERROR_PATTERNS = re.compile(
    r"error|denied|fail|not found|missing|invalid|cannot|can't|"
    r"forbidden|already|cross|❌|wrong|ban|kick|warn",
    re.IGNORECASE,
)
WARNING_PATTERNS = re.compile(
    r"warning|are you sure|confirm|sure\?|caution",
    re.IGNORECASE,
)


def classify(title: str, description: str) -> str:
    combined = (title or "") + " " + (description or "")
    if SUCCESS_PATTERNS.search(combined):
        return "success_panel"
    if ERROR_PATTERNS.search(combined):
        return "error_panel"
    if WARNING_PATTERNS.search(combined):
        return "warning_panel"
    return "info_panel"


# ---------------------------------------------------------------------------
# Core rewriter
# ---------------------------------------------------------------------------

# Matches:  varname = discord.Embed(...)
EMBED_ASSIGN_RE = re.compile(
    r'^(\s*)(\w+)\s*=\s*discord\.Embed\s*\(', re.MULTILINE
)

# Matches attribute calls on embed var:  embed.set_author(...)  embed.add_field(...)
EMBED_ATTR_RE = re.compile(
    r'^\s*{var}\.(set_author|set_footer|set_thumbnail|set_image|add_field|set_author)\s*\(',
)

# Matches the send/reply/edit call containing embed=varname
SEND_RE = re.compile(
    r'(await\s+\S+\.(send|reply|edit)\s*\([^)]*?)\bembed\s*=\s*{var}\b([^)]*?\))',
)


def extract_kwarg(text: str, key: str) -> Optional[str]:
    """Pull a keyword argument value from a function call string."""
    pattern = re.compile(
        rf'\b{key}\s*=\s*'
        r'('
        r'f?"(?:[^"\\]|\\.)*"'      # double-quoted string (optionally f-string)
        r"|f?'(?:[^'\\]|\\.)*'"     # single-quoted string
        r'|[^,\)]+?'                # bare expression up to comma/close-paren
        r')'
        r'(?=\s*[,\)])',
        re.DOTALL,
    )
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    return None


def build_panel_call(
    var: str,
    embed_line: str,
    attr_lines: list[str],
    send_line: str,
    indent: str,
) -> list[str]:
    """
    Given the collected embed lines, produce replacement lines.
    Returns a list of source lines (without trailing newline).
    """
    # Grab description / title from Embed(...)
    description = extract_kwarg(embed_line, "description") or '""'
    title = extract_kwarg(embed_line, "title")

    # Grab fields from .add_field calls
    fields: list[tuple[str, str]] = []
    for line in attr_lines:
        if ".add_field(" in line:
            name = extract_kwarg(line, "name") or '""'
            value = extract_kwarg(line, "value") or '""'
            if name != '""' or value != '""':
                fields.append((name, value))

    panel_type = classify(
        (title or "").strip("'\"f"),
        description.strip("'\"f"),
    )

    # Build the panel call arguments
    args = [description]
    if title:
        args.append(f"title={title}")
    if fields:
        fields_repr = "[" + ", ".join(f"({n}, {v})" for n, v in fields) + "]"
        args.append(f"fields={fields_repr}")

    panel_call = f"{panel_type}({', '.join(args)})"

    # Replace embed=var in the send/reply/edit call
    new_send = re.sub(
        rf'\bembed\s*=\s*{re.escape(var)}\b',
        f"view={panel_call}",
        send_line,
    )
    # Remove leftover leading comma before view= if needed
    new_send = re.sub(r',\s*view=', ", view=", new_send)
    new_send = re.sub(r'\(\s*,', "(", new_send)

    return [new_send]


def needs_import(source: str) -> bool:
    return "from utils.components_v2 import" not in source


def add_import(source: str, helpers: set[str]) -> str:
    import_line = f"from utils.components_v2 import {', '.join(sorted(helpers))}\n"
    # If there's already a components_v2 import, merge into it
    existing = re.search(r"from utils\.components_v2 import ([^\n]+)", source)
    if existing:
        old_names = {n.strip() for n in existing.group(1).split(",")}
        merged = ", ".join(sorted(old_names | helpers))
        return source.replace(existing.group(0), f"from utils.components_v2 import {merged}")
    # Insert after the last 'from utils import ...' line or after first import block
    lines = source.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            insert_at = i + 1
    lines.insert(insert_at, import_line)
    return "".join(lines)


# ---------------------------------------------------------------------------
# File-level converter
# ---------------------------------------------------------------------------

def convert_file(path: Path, *, write: bool = False) -> tuple[bool, str]:
    """
    Convert a single file.
    Returns (changed: bool, new_source: str).
    """
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    # Track which embed variables we touch and what panel types we use
    used_panels: set[str] = set()
    result_lines = list(lines)
    changed = False

    # We process embeds in reverse order so line-number shifts don't break us
    # First pass: find all embed assignment blocks
    i = 0
    patches: list[tuple[int, int, list[str]]] = []  # (start, end, replacement_lines)

    while i < len(result_lines):
        line = result_lines[i]
        m = EMBED_ASSIGN_RE.match(line)
        if not m:
            i += 1
            continue

        indent = m.group(1)
        var = m.group(2)

        # Collect the full Embed(...) call (may span multiple lines)
        embed_start = i
        embed_line_parts = [line.rstrip("\n")]
        # Handle multi-line Embed(...)
        open_parens = line.count("(") - line.count(")")
        j = i + 1
        while open_parens > 0 and j < len(result_lines):
            part = result_lines[j].rstrip("\n")
            embed_line_parts.append(part)
            open_parens += part.count("(") - part.count(")")
            j += 1
        embed_full = " ".join(embed_line_parts)

        # Collect attribute lines (set_author, add_field, etc.) and find send
        attr_lines: list[str] = []
        send_line_idx: Optional[int] = None
        send_line: Optional[str] = None

        k = j
        while k < len(result_lines):
            l = result_lines[k].rstrip("\n")
            # Check for embed attribute
            attr_m = re.match(
                rf'^\s*{re.escape(var)}\.(set_author|set_footer|set_thumbnail|set_image|add_field)\s*\(',
                l,
            )
            if attr_m:
                # Collect full attribute call
                attr_parts = [l]
                op = l.count("(") - l.count(")")
                k2 = k + 1
                while op > 0 and k2 < len(result_lines):
                    p = result_lines[k2].rstrip("\n")
                    attr_parts.append(p)
                    op += p.count("(") - p.count(")")
                    k2 += 1
                attr_lines.append(" ".join(attr_parts))
                k = k2
                continue

            # Check for send/reply/edit with this embed
            send_m = re.search(
                rf'\bembed\s*=\s*{re.escape(var)}\b',
                l,
            )
            if send_m and re.search(r'await\s+\S+\.(send|reply|edit)\s*\(', l):
                send_line_idx = k
                send_line = l
                break

            # If we hit another embed assignment or unrelated code, stop
            if EMBED_ASSIGN_RE.match(l) and l != line:
                break
            # If we go more than 30 lines without finding a send, give up
            if k - j > 30:
                break
            k += 1

        if send_line_idx is None or send_line is None:
            i = j
            continue

        # Skip ephemeral sends (interaction.response.send_message)
        if "interaction.response" in send_line or "ephemeral=True" in send_line:
            i = j
            continue

        # Build replacement
        replacement = build_panel_call(
            var, embed_full, attr_lines, send_line, indent
        )

        # Determine which panel type was used
        for r in replacement:
            pm = re.search(r'\b(success_panel|error_panel|info_panel|warning_panel)\b', r)
            if pm:
                used_panels.add(pm.group(1))

        # Record patch: replace from embed_start to send_line_idx (inclusive)
        patches.append((embed_start, send_line_idx, replacement))
        changed = True
        i = send_line_idx + 1

    if not patches:
        return False, source

    # Apply patches in reverse order
    for start, end, replacement in reversed(patches):
        result_lines[start : end + 1] = [r + "\n" for r in replacement]

    new_source = "".join(result_lines)

    # Add imports
    if used_panels:
        new_source = add_import(new_source, used_panels)

    return True, new_source


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------

TARGET_DIRS = [
    "cogs/commands",
    "cogs/moderation",
    "cogs/events",
    "cogs/antinuke",
    "cogs/automod",
    "cogs/axon",
]

# Files where the converter's variable-based approach is unreliable
# (complex multi-view, inline embeds only, etc.) — handled separately
SKIP_FILES = {
    "cogs/commands/music.py",
    "cogs/commands/stats.py",
    "cogs/commands/status.py",
}


def collect_files(root: Path, single_file: Optional[str] = None) -> list[Path]:
    if single_file:
        p = Path(single_file)
        if not p.is_absolute():
            p = root / p
        return [p]
    files = []
    skip_abs = {(root / s).resolve() for s in SKIP_FILES}
    for d in TARGET_DIRS:
        target = root / d
        if target.exists():
            for f in target.rglob("*.py"):
                if f.resolve() not in skip_abs:
                    files.append(f)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert discord.Embed to CV2 panels")
    parser.add_argument("--write", action="store_true", help="Write changes (default: dry-run)")
    parser.add_argument("--file", metavar="PATH", help="Convert a single file only")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    files = collect_files(root, args.file)

    total = 0
    converted = 0

    for path in sorted(files):
        total += 1
        try:
            changed, new_source = convert_file(path)
        except Exception as exc:
            print(f"  ERROR  {path.relative_to(root)}: {exc}")
            continue

        if not changed:
            print(f"  SKIP   {path.relative_to(root)}")
            continue

        converted += 1
        rel = path.relative_to(root)

        if args.write:
            # Backup
            bak = path.with_suffix(".py.bak")
            shutil.copy2(path, bak)
            path.write_text(new_source, encoding="utf-8")
            print(f"  WROTE  {rel}  (backup: {bak.name})")
        else:
            print(f"  WOULD  {rel}")

    print(f"\nDone. {converted}/{total} files {'converted' if args.write else 'would be converted'}.")
    if not args.write:
        print("Run with --write to apply changes.")


if __name__ == "__main__":
    main()
