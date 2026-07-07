from __future__ import annotations

import asyncio
import logging
import typing
from typing import List

import aiohttp
import discord
from discord.ext import commands

from utils import console, getConfig, updateConfig
from utils.components_v2 import error_panel, warning_panel
from utils.config import OWNER_IDS
from utils.database import close_shared_databases, connect, get_anti_db
from utils.security import AccessDecision, get_security_gate
from utils.discord_compat import install_neutral_embed_policy
from utils.migrations import run_startup_migrations

from .Context import Context

install_neutral_embed_policy()

log = logging.getLogger(__name__)

extensions: List[str] = [
    "cogs"
]


class Rem(commands.AutoShardedBot):

    def __init__(self, *arg, **kwargs):
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        self.session: aiohttp.ClientSession | None = None
        self._synced_app_commands = False
        self._shutting_down = False
        self.security = get_security_gate()
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            intents=intents,
            status=discord.Status.online,
            strip_after_prefix=True,
            owner_ids=OWNER_IDS,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, replied_user=False, roles=False
            ),
            shard_count=2,
        )

    async def setup_hook(self):
        await run_startup_migrations()
        await get_anti_db()
        self.session = aiohttp.ClientSession()
        self.add_check(self._global_security_check)
        self.tree.interaction_check = self._interaction_security_check
        await self.load_extensions()

    async def _deny_access(self, ctx: Context, decision: AccessDecision) -> None:
        if self._shutting_down or self.is_closed():
            return

        reason = decision.reason
        if reason.startswith("rate_limit:"):
            if not self.security.should_notify_rate_limit(ctx.author.id):
                return
            retry = reason.split(":", 1)[1]
            view = warning_panel(
                f"Slow down — try again in **{retry}s**.",
                title="Rate Limited",
            )
        elif reason == "guild_blacklisted":
            view = error_panel(
                "This server is restricted from using REM.",
                title="Access Denied",
            )
        elif reason == "user_blacklisted":
            view = error_panel(
                "You are restricted from using REM.",
                title="Access Denied",
            )
        elif reason == "channel_ignored":
            view = warning_panel(
                "This channel is ignored.",
                title="Ignored",
            )
        elif reason == "user_ignored":
            view = warning_panel(
                "You are ignored in this server.",
                title="Ignored",
            )
        elif reason == "command_ignored":
            view = warning_panel(
                "This command is ignored in this server.",
                title="Ignored",
            )
        else:
            view = error_panel("You cannot use this command here.", title="Access Denied")

        try:
            delete_after = None if reason.startswith("rate_limit:") else 8
            await ctx.reply(view=view, delete_after=delete_after, mention_author=False)
        except (discord.HTTPException, asyncio.CancelledError):
            pass
        except Exception:
            log.debug("Failed to send access denial", exc_info=True)

    async def _global_security_check(self, ctx: Context) -> bool:
        if ctx.command is None:
            return True

        decision = await self.security.run_command_gate(ctx)
        if decision.allowed:
            return True

        await self._deny_access(ctx, decision)
        return False

    async def _interaction_security_check(self, interaction: discord.Interaction) -> bool:
        if self._shutting_down or self.is_closed():
            return False

        decision = await self.security.run_interaction_gate(interaction)
        if decision.allowed:
            return True

        reason = decision.reason
        if reason.startswith("rate_limit:"):
            if not self.security.should_notify_rate_limit(interaction.user.id):
                return False
            retry = reason.split(":", 1)[1]
            message = f"Slow down — try again in **{retry}s**."
        elif reason == "user_blacklisted":
            message = "You are restricted from using REM."
        elif reason == "guild_blacklisted":
            message = "This server is restricted from using REM."
        else:
            message = "You cannot use this command."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return False

    async def load_extensions(self):
        timer = console.LoadTimer("EXT")
        console.section("Loading extensions")
        for extension in extensions:
            try:
                await self.load_extension(extension)
                console.success(f"Loaded {extension}")
                log.info("Loaded extension: %s", extension)
            except Exception as e:
                console.error(f"Failed to load {extension}: {e}")
                log.exception("Failed to load extension %s", extension)
                raise
        timer.finish(f"Loaded {len(extensions)} extension(s)")

    async def _close_cog_resources(self) -> None:
        for cog in self.cogs.values():
            session = getattr(cog, "aiohttp", None)
            if session is not None and hasattr(session, "closed") and not session.closed:
                try:
                    await session.close()
                except Exception:
                    log.exception("Failed to close aiohttp session for %s", type(cog).__name__)

    async def close(self) -> None:
        if self.is_closed():
            return

        self._shutting_down = True
        await asyncio.sleep(0.75)

        await self._close_cog_resources()

        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except Exception:
                log.exception("Failed to close aiohttp session")
            finally:
                self.session = None

        try:
            await close_shared_databases()
        except Exception:
            log.exception("Failed to close shared database connection")

        try:
            await super().close()
        except AttributeError as exc:
            if "_AutoShardedClient__queue" not in str(exc):
                raise
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error during Discord client shutdown")

    async def on_connect(self):
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(type=discord.ActivityType.playing, name=">help | >invite"),
        )

    async def send_raw(
        self, channel_id: int, content: str, **kwargs
    ) -> typing.Optional[discord.Message]:
        return await self.http.send_message(channel_id, content, **kwargs)

    async def invoke_help_command(self, ctx: Context) -> None:
        return await ctx.send_help(ctx.command)

    async def fetch_message_by_channel(
        self, channel: discord.TextChannel, messageID: int
    ) -> typing.Optional[discord.Message]:
        async for msg in channel.history(
            limit=1,
            before=discord.Object(messageID + 1),
            after=discord.Object(messageID - 1),
        ):
            return msg

    async def get_prefix(self, message: discord.Message):
        no_prefix = await self.security.has_no_prefix(message.author.id)

        if message.guild:
            prefix = await self.security.get_prefix(message.guild.id)
            if no_prefix:
                return commands.when_mentioned_or(prefix, "")(self, message)
            return commands.when_mentioned_or(prefix)(self, message)

        if no_prefix:
            return commands.when_mentioned_or(">", "")(self, message)
        return commands.when_mentioned_or("")(self, message)

    async def on_message_edit(self, before, after):
        ctx: Context = await self.get_context(after, cls=Context)
        if before.content != after.content:
            if after.guild is None or after.author.bot:
                return
            if ctx.command is None:
                return
            if isinstance(ctx.channel, discord.Thread) and ctx.channel.type == discord.ChannelType.public_thread:
                return
            await self.invoke(ctx)


def setup_bot():
    intents = discord.Intents.all()
    bot = Rem(intents=intents)
    return bot