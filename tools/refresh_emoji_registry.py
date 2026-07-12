"""Refresh utils/emojis.py IDs and animated flags from Discord application emojis."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.upload_rem_emojis import persist_application_emoji_ids  # noqa: E402


async def main() -> None:
    load_dotenv(ROOT / ".env")
    token = os.environ.get("TOKEN", "").strip()
    if not token:
        raise SystemExit("TOKEN missing")

    client = discord.Client(intents=discord.Intents.none())

    @client.event
    async def on_ready() -> None:
        try:
            emojis = list(await client.fetch_application_emojis())
            updates = persist_application_emoji_ids(emojis)
            print(f"Refreshed registry from {len(emojis)} application emojis ({updates} line updates)")
        finally:
            await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())