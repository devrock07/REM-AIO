"""Rename emoji registry entries to rem_ names and refresh local assets."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.rem_emoji_names import OLD_TO_REM  # noqa: E402

REGISTRY = ROOT / "utils" / "emojis.py"
ASSET_DIR = ROOT / "assets" / "emojis"


def rename_registry() -> int:
    lines = REGISTRY.read_text(encoding="utf-8").splitlines(keepends=True)
    updates = 0

    for index, line in enumerate(lines):
        if "CustomEmoji(" not in line or not line.lstrip()[:1].isupper():
            continue

        line_ending = "\n" if line.endswith("\n") else ""
        source = line[:-1] if line_ending else line
        try:
            node = ast.parse(source)
        except SyntaxError:
            continue

        assignment = node.body[0]
        if not isinstance(assignment, ast.Assign):
            continue
        call = assignment.value
        if not isinstance(call, ast.Call) or not call.args:
            continue
        if not isinstance(call.args[0], ast.Constant):
            continue

        old_name = str(call.args[0].value)
        new_name = OLD_TO_REM.get(old_name)
        if not new_name or new_name == old_name:
            continue

        emoji_id = int(call.args[1].value) if len(call.args) > 1 else 0
        animated = bool(call.args[2].value) if len(call.args) > 2 else False
        target = assignment.targets[0].id
        next_line = f"{target} = CustomEmoji({new_name!r}, {emoji_id}, {animated!r}){line_ending}"
        if next_line != line:
            lines[index] = next_line
            updates += 1

    # Rewrite manual dict keys that mirror legacy names
    text = "".join(lines)
    for old, new in OLD_TO_REM.items():
        text = re.sub(rf"'{re.escape(old)}':", f"'{new}':", text)

    REGISTRY.write_text(text, encoding="utf-8")
    return updates


def purge_legacy_assets() -> int:
    removed = 0
    if not ASSET_DIR.exists():
        return removed
    for path in ASSET_DIR.glob("*.png"):
        if not path.stem.startswith("rem_"):
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def main() -> None:
    removed = purge_legacy_assets()
    updates = rename_registry()
    print(f"Renamed {updates} registry lines; removed {removed} legacy asset files")


if __name__ == "__main__":
    main()