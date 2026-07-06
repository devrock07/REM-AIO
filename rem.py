import asyncio
import logging
import os
import traceback
from threading import Thread

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask

from core.axon import axon

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger("axon")

TOKEN = (os.getenv("TOKEN") or "").strip()
COMMAND_LOG_WEBHOOK_URL = os.getenv("COMMAND_LOG_WEBHOOK_URL")
ENABLE_KEEP_ALIVE = os.getenv("ENABLE_KEEP_ALIVE", "true").lower() in {"1", "true", "yes", "on"}

client = axon()
app = Flask(__name__)

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"


@client.event
async def on_ready():
    await client.wait_until_ready()

    log.info("Loaded and online as %s", client.user)
    log.info("Connected to %s guilds and %s cached users", len(client.guilds), len(client.users))

    if client._synced_app_commands:
        return

    try:
        synced = await client.tree.sync()
        client._synced_app_commands = True
        log.info("Synced %s prefix commands and %s slash commands", len(client.commands), len(synced))
    except Exception:
        log.exception("Slash command sync failed")


@client.event
async def on_command_completion(context: commands.Context) -> None:
    if not COMMAND_LOG_WEBHOOK_URL or context.author.id == 767979794411028491:
        return

    full_command_name = context.command.qualified_name
    executed_command = str(full_command_name.split("\n")[0])

    try:
        session = client.session or aiohttp.ClientSession()
        webhook = discord.Webhook.from_url(COMMAND_LOG_WEBHOOK_URL, session=session)
        avatar_url = context.author.display_avatar.url
        embed = discord.Embed(title="Command Executed")
        embed.set_author(name=str(context.author), icon_url=avatar_url)
        embed.add_field(name="Command", value=executed_command, inline=False)
        embed.add_field(name="User", value=f"{context.author} ({context.author.id})", inline=False)

        if context.guild is not None:
            embed.add_field(name="Guild", value=f"{context.guild.name} ({context.guild.id})", inline=False)
            embed.add_field(name="Channel", value=f"{context.channel} ({context.channel.id})", inline=False)

        embed.timestamp = discord.utils.utcnow()
        await webhook.send(embed=embed)

        if client.session is None:
            await session.close()
    except Exception as exc:
        log.warning("Command log webhook failed: %s", exc)
        traceback.print_exc()


@app.route("/")
def home():
    return "Axon X is online"


def run_keep_alive():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), use_reloader=False)


def keep_alive():
    if not ENABLE_KEEP_ALIVE:
        return
    server = Thread(target=run_keep_alive, daemon=True)
    server.start()


async def main():
    if not TOKEN:
        raise RuntimeError("TOKEN is not set. Add it to .env or your process environment.")

    keep_alive()
    async with client:
        await client.load_extension("jishaku")
        await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
