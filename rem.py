from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import asyncio
import logging
import os
import signal
import sys
import traceback
from threading import Thread

import aiohttp
import discord
from discord.ext import commands
from flask import Flask

from core.rem import Rem
from utils.config import COMMAND_LOG_IGNORE_IDS, COMMAND_LOG_WEBHOOK_URL, ENABLE_KEEP_ALIVE, LOG_LEVEL, NAME, PORT, PREFIX, TOKEN
from utils import console
from utils.startup import StartupError, validate_startup_config

console.setup_console_logging(LOG_LEVEL)
log = logging.getLogger("rem")

client = Rem()
app = Flask(__name__)

_shutdown_lock = asyncio.Lock()
_shutdown_done = False
_loop: asyncio.AbstractEventLoop | None = None
_bot_task: asyncio.Task | None = None
_shutdown_task: asyncio.Task | None = None
_interrupt_count = 0
_interrupt_at = 0.0

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"


@client.event
async def on_shard_connect(shard_id: int):
    console.shard_connected(shard_id)


@client.event
async def on_ready():
    await client.wait_until_ready()

    prefix_count = len(client.commands)
    slash_count = 0

    if not client._synced_app_commands:
        try:
            synced = await client.tree.sync()
            client._synced_app_commands = True
            slash_count = len(synced)
        except Exception:
            log.exception("Slash command sync failed")

    console.ready(
        str(client.user),
        guilds=len(client.guilds),
        users=len(client.users),
        prefix_commands=prefix_count,
        slash_commands=slash_count,
    )
    log.info(
        "Online as %s (%s guilds, %s users, prefix=%r)",
        client.user,
        len(client.guilds),
        len(client.users),
        PREFIX,
    )


@client.event
async def on_command_completion(context: commands.Context) -> None:
    if not COMMAND_LOG_WEBHOOK_URL or context.author.id in COMMAND_LOG_IGNORE_IDS:
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
    return "REM ALL IN ONE BOT is online"


@app.route("/health")
def health():
    from flask import jsonify
    return jsonify(status="ok", bot_ready=client.is_ready())


def run_keep_alive():
    import logging as _logging
    _logging.getLogger("werkzeug").setLevel(_logging.ERROR)
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


def keep_alive():
    if not ENABLE_KEEP_ALIVE:
        return
    server = Thread(target=run_keep_alive, daemon=True, name="rem-keepalive")
    server.start()


async def graceful_shutdown(*, reason: str = "signal") -> None:
    global _shutdown_done

    async with _shutdown_lock:
        if _shutdown_done:
            return
        _shutdown_done = True

    console.goodbye()
    log.info("Shutting down (%s)...", reason)

    client._shutting_down = True

    if _bot_task is not None and not _bot_task.done():
        _bot_task.cancel()
        try:
            await asyncio.wait_for(_bot_task, timeout=8.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        except Exception:
            log.exception("Error while stopping bot task")

    try:
        if not client.is_closed():
            await asyncio.wait_for(client.close(), timeout=10.0)
    except asyncio.TimeoutError:
        log.warning("Discord client close timed out")
    except Exception:
        log.exception("Error while closing Discord client")

    await asyncio.sleep(0.25)


def _schedule_shutdown(reason: str = "Ctrl+C") -> None:
    global _shutdown_task

    if _loop is None or not _loop.is_running():
        return

    def _start_shutdown() -> None:
        global _shutdown_task
        if _shutdown_task is None or _shutdown_task.done():
            _shutdown_task = asyncio.create_task(
                graceful_shutdown(reason=reason),
                name="rem-shutdown",
            )

    _loop.call_soon_threadsafe(_start_shutdown)


async def _wait_for_shutdown() -> None:
    if _shutdown_task is not None:
        await _shutdown_task
    elif not _shutdown_done:
        await graceful_shutdown(reason="cleanup")


def _register_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def _handler() -> None:
        _schedule_shutdown("signal")

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handler)
            return
        except (NotImplementedError, RuntimeError, AttributeError):
            continue

    def _win_handler(signum, frame) -> None:
        global _interrupt_count, _interrupt_at
        import time

        now = time.monotonic()
        if now - _interrupt_at > 2.0:
            _interrupt_count = 0
        _interrupt_at = now
        _interrupt_count += 1

        if _interrupt_count >= 2:
            console.warn("Force stopping REM...")
            os._exit(0)

        console.warn("Interrupted — shutting down... (Ctrl+C again to force)")
        _schedule_shutdown("Ctrl+C")

    signal.signal(signal.SIGINT, _win_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _win_handler)


async def _run_bot() -> None:
    await client.load_extension("jishaku")
    await client.start(TOKEN)


async def main():
    global _loop, _bot_task
    _loop = asyncio.get_running_loop()

    console.print_banner(NAME)
    console.section("Boot sequence")

    try:
        warnings = validate_startup_config()
        for warning in warnings:
            console.warn(warning)
        console.info("Environment validated")
    except StartupError as exc:
        console.error(str(exc))
        raise SystemExit(1) from exc

    if ENABLE_KEEP_ALIVE:
        keep_alive()
        console.info(f"Keep-alive server listening on port {PORT}")
    else:
        console.info("Keep-alive server disabled")

    _register_signal_handlers(_loop)

    _bot_task = asyncio.create_task(_run_bot(), name="rem-bot")

    try:
        await _bot_task
    except asyncio.CancelledError:
        pass
    finally:
        await _wait_for_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        console.info("REM stopped cleanly.")
        sys.exit(0)