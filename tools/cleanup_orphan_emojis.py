"""Remove application emojis not referenced in utils/emojis.py."""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "utils" / "emojis.py"


def registry_names() -> set[str]:
    text = REGISTRY.read_text(encoding="utf-8")
    return {name.lower() for name in re.findall(r"CustomEmoji\('([^']+)'", text)}


async def main() -> None:
    load_dotenv(ROOT / ".env")
    token = os.environ.get("TOKEN", "").strip()
    if not token:
        raise SystemExit("TOKEN missing")

    wanted = registry_names()
    client = discord.Client(intents=discord.Intents.none())

    @client.event
    async def on_ready() -> None:
        try:
            removed = 0
            for emoji in await client.fetch_application_emojis():
                if emoji.name.lower() not in wanted:
                    await emoji.delete()
                    removed += 1
                    print(f"Deleted orphan: {emoji.name} ({emoji.id})")
            print(f"Removed {removed} orphan application emoji(s)")
        finally:
            await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())