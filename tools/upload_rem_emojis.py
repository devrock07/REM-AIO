"""Generate REM emoji pack and upload/replace application emojis on Discord."""

from __future__ import annotations

import argparse
import ast
import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.rem_emoji_pack import EMOJI_NAMES, generate_pack  # noqa: E402

log = logging.getLogger("rem.emoji.upload")
REGISTRY_PATH = ROOT / "utils" / "emojis.py"
ASSET_DIR = ROOT / "assets" / "emojis"
UPLOAD_DELAY = 1.2


async def _replace_application_emoji(
    client: discord.Client,
    existing: discord.Emoji,
    *,
    name: str,
    image: bytes,
) -> discord.Emoji:
    if client.application_id is None:
        raise discord.MissingApplicationID

    # Delete + recreate guarantees static PNGs replace legacy animated GIF slots.
    if existing.animated:
        await existing.delete()
        return await client.create_application_emoji(name=name, image=image)

    payload = {
        "name": name,
        "image": discord.utils._bytes_to_base64_data(image),
    }
    try:
        data = await client.http.edit_application_emoji(client.application_id, existing.id, payload=payload)
        updated = discord.Emoji(guild=discord.Object(0), state=client._connection, data=data)
        if updated.animated:
            await updated.delete()
            return await client.create_application_emoji(name=name, image=image)
        return updated
    except discord.HTTPException:
        await existing.delete()
        return await client.create_application_emoji(name=name, image=image)


def persist_application_emoji_ids(application_emojis: list[discord.Emoji]) -> int:
    if not REGISTRY_PATH.exists():
        return 0

    by_name = {emoji.name.lower(): emoji for emoji in application_emojis if emoji.name and emoji.id}
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
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

        if not node.body or not isinstance(node.body[0], ast.Assign):
            continue
        assignment = node.body[0]
        if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
            continue
        if not isinstance(assignment.value, ast.Call):
            continue
        if not isinstance(assignment.value.func, ast.Name) or assignment.value.func.id != "CustomEmoji":
            continue
        if not assignment.value.args or not isinstance(assignment.value.args[0], ast.Constant):
            continue

        emoji_name = str(assignment.value.args[0].value)
        application_emoji = by_name.get(emoji_name.lower())
        if application_emoji is None:
            continue

        next_line = (
            f"{assignment.targets[0].id} = CustomEmoji("
            f"{application_emoji.name!r}, "
            f"{int(application_emoji.id)}, "
            f"{bool(application_emoji.animated)!r})"
            f"{line_ending}"
        )
        if next_line != line:
            lines[index] = next_line
            updates += 1

    if updates:
        REGISTRY_PATH.write_text("".join(lines), encoding="utf-8")
    return updates


async def run_upload(token: str, *, replace: bool) -> None:
    intents = discord.Intents.none()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            generated = generate_pack(ASSET_DIR)
            log.info("Generated %s emoji PNG assets", len(generated))

            existing = list(await client.fetch_application_emojis())
            by_name = {emoji.name.lower(): emoji for emoji in existing}
            log.info("Found %s existing application emojis", len(existing))

            created = 0
            replaced = 0
            skipped = 0
            failed: list[str] = []

            for name in EMOJI_NAMES:
                asset_path = ASSET_DIR / f"{name}.png"
                image = asset_path.read_bytes()
                current = by_name.get(name.lower())

                try:
                    if current and replace:
                        updated = await _replace_application_emoji(client, current, name=name, image=image)
                        by_name[updated.name.lower()] = updated
                        replaced += 1
                        log.info("Replaced: %s (%s)", updated.name, updated.id)
                    elif current:
                        skipped += 1
                    else:
                        created_emoji = await client.create_application_emoji(name=name, image=image)
                        by_name[created_emoji.name.lower()] = created_emoji
                        created += 1
                        log.info("Created: %s (%s)", created_emoji.name, created_emoji.id)
                    await asyncio.sleep(UPLOAD_DELAY)
                except discord.HTTPException as exc:
                    failed.append(f"{name}: HTTP {exc.status}")
                    log.warning("Failed %s: HTTP %s", name, exc.status)
                except Exception as exc:  # noqa: BLE001
                    failed.append(f"{name}: {exc}")
                    log.warning("Failed %s: %s", name, exc)

            refreshed = list(await client.fetch_application_emojis())
            file_updates = persist_application_emoji_ids(refreshed)

            from utils import emojis  # noqa: WPS433

            runtime_updates = emojis.apply_application_emojis(refreshed)
            log.info(
                "Upload complete — created=%s replaced=%s skipped=%s failed=%s | emojis.py updates=%s runtime=%s",
                created,
                replaced,
                skipped,
                len(failed),
                file_updates,
                runtime_updates,
            )
            if failed:
                log.error("Failures (%s): %s", len(failed), "; ".join(failed[:15]))
        finally:
            await client.close()

    await client.start(token)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload REM application emoji pack")
    parser.add_argument("--generate-only", action="store_true", help="Only write PNG files")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing application emojis with the same name (default: create only)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.generate_only:
        files = generate_pack(ASSET_DIR)
        print(f"Generated {len(files)} files in {ASSET_DIR}")
        return

    load_dotenv(ROOT / ".env")
    token = os.environ.get("TOKEN", "").strip()
    if not token:
        raise SystemExit("TOKEN missing in .env — cannot upload application emojis.")

    asyncio.run(run_upload(token, replace=args.replace))


if __name__ == "__main__":
    main()