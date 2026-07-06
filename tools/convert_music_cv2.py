#!/usr/bin/env python3
"""
Targeted CV2 converter for cogs/commands/music.py.

Handles the inline pattern:
    await ctx.send(embed=discord.Embed(description="...", color=...))
    await ctx.send(embed=discord.Embed(description=f"...", color=...))

Also fixes the broken double-view= lines produced by the generic converter.

Usage:
    python tools/convert_music_cv2.py           # dry-run
    python tools/convert_music_cv2.py --write   # apply
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern: await <expr>.send(embed=discord.Embed(description=<desc>, color=<c>))
# Captures the whole inline Embed inside the send call.
# We only handle single-line cases.
# ---------------------------------------------------------------------------

INLINE_EMBED_RE = re.compile(
    r'(await\s+\S+?\.(send|reply)\s*\()'        # await ctx.send(
    r'(?P<pre>[^)]*?)'                            # anything before embed=
    r'\bembed\s*=\s*discord\.Embed\s*\('          # embed=discord.Embed(
    r'(?P<args>[^)]+)'                            # args inside Embed(...)
    r'\)'                                         # closing ) of Embed
    r'(?P<post>[^)]*?\))',                        # rest of send() call
)

# Fix broken double view= from the generic converter
DOUBLE_VIEW_RE = re.compile(r',?\s*view=\S+\(.*?\)\s*\)\s*,\s*view=')


def extract_kwarg(text: str, key: str) -> str | None:
    pattern = re.compile(
        rf'\b{key}\s*=\s*'
        r'('
        r'f?"(?:[^"\\]|\\.)*"'
        r"|f?'(?:[^'\\]|\\.)*'"
        r'|[^,\)]+?'
        r')'
        r'(?=\s*[,\)]|$)',
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else None


SUCCESS = re.compile(r'success|tick|✅|enabled|added|removed|created|deleted|updated|set|configured|saved|done|completed|whitelisted|reset', re.I)
ERROR   = re.compile(r'error|denied|fail|not found|missing|invalid|cannot|can\'t|forbidden|already|wrong|warning|⚠️|❌', re.I)


def panel_type(description: str) -> str:
    if SUCCESS.search(description):
        return "success_panel"
    if ERROR.search(description):
        return "error_panel"
    return "info_panel"


def convert_inline(line: str) -> str | None:
    """Convert a single inline embed line. Returns new line or None if no change."""
    m = INLINE_EMBED_RE.search(line)
    if not m:
        return None

    embed_args = m.group("args")
    description = extract_kwarg(embed_args, "description") or '""'
    title = extract_kwarg(embed_args, "title")

    ptype = panel_type((title or "") + " " + description.strip("'\"f"))

    args = [description]
    if title:
        args.append(f"title={title}")

    panel_call = f"{ptype}({', '.join(args)})"

    # Build replacement: replace embed=discord.Embed(...) with view=panel_call
    pre  = m.group("pre").rstrip(", ")
    post = m.group("post")

    # Reconstruct the send call
    call_prefix = m.group(1)  # "await ctx.send("
    if pre:
        new_inner = f"{pre}, view={panel_call}{post}"
    else:
        new_inner = f"view={panel_call}{post}"

    new_call = call_prefix + new_inner
    new_line = line[: m.start()] + new_call + line[m.end():]
    return new_line


def convert_file(path: Path) -> tuple[bool, str]:
    source = path.read_text(encoding="utf-8")
    lines  = source.splitlines(keepends=True)
    changed = False
    result  = []
    used_panels: set[str] = set()

    for line in lines:
        # Skip ephemeral or interaction.response lines
        if "ephemeral=True" in line or "interaction.response" in line:
            result.append(line)
            continue

        new_line = convert_inline(line)
        if new_line and new_line != line:
            changed = True
            line = new_line
            m = re.search(r'\b(success_panel|error_panel|info_panel|warning_panel)\b', line)
            if m:
                used_panels.add(m.group(1))

        result.append(line)

    if not changed:
        return False, source

    new_source = "".join(result)

    # Add/merge import
    if used_panels:
        existing = re.search(r"from utils\.components_v2 import ([^\n]+)", new_source)
        if existing:
            old_names = {n.strip() for n in existing.group(1).split(",")}
            merged = ", ".join(sorted(old_names | used_panels))
            new_source = new_source.replace(existing.group(0), f"from utils.components_v2 import {merged}")
        else:
            import_line = f"from utils.components_v2 import {', '.join(sorted(used_panels))}\n"
            lines2 = new_source.splitlines(keepends=True)
            insert_at = 0
            for i, l in enumerate(lines2):
                if l.startswith(("import ", "from ")):
                    insert_at = i + 1
            lines2.insert(insert_at, import_line)
            new_source = "".join(lines2)

    return True, new_source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    path = root / "cogs/commands/music.py"

    changed, new_source = convert_file(path)
    if not changed:
        print("No changes needed.")
        return

    # Count how many embeds remain (shouldn't be many)
    remaining = len(re.findall(r'embed=discord\.Embed', new_source))
    converted = len(re.findall(r'\b(success_panel|error_panel|info_panel)\b', new_source))
    print(f"Converted: ~{converted} calls | Remaining inline embeds: {remaining}")

    if args.write:
        bak = path.with_suffix(".py.bak2")
        shutil.copy2(path, bak)
        path.write_text(new_source, encoding="utf-8")
        print(f"Written. Backup: {bak.name}")
    else:
        # Show a diff preview
        orig_lines = path.read_text(encoding="utf-8").splitlines()
        new_lines  = new_source.splitlines()
        changes = [(i+1, o, n) for i,(o,n) in enumerate(zip(orig_lines, new_lines)) if o != n]
        for lineno, old, new in changes[:20]:
            print(f"\n  Line {lineno}:")
            print(f"  - {old.strip()}")
            print(f"  + {new.strip()}")
        if len(changes) > 20:
            print(f"\n  ... and {len(changes)-20} more changes")
        print("\nRun with --write to apply.")


if __name__ == "__main__":
    main()
