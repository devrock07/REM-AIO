from __future__ import annotations
from discord.ext import commands
import discord
import aiohttp
import typing
from typing import List
import aiosqlite
from utils.config import OWNER_IDS
from utils import getConfig, updateConfig
from utils.discord_compat import install_neutral_embed_policy
from utils.migrations import run_startup_migrations
from .Context import Context
from colorama import Fore, Style, init
import logging

install_neutral_embed_policy()

init(autoreset=True)
log = logging.getLogger(__name__)

extensions: List[str] = [
    "cogs"
]

class axon(commands.AutoShardedBot):

    def __init__(self, *arg, **kwargs):
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        self.session: aiohttp.ClientSession | None = None
        self._synced_app_commands = False
        super().__init__(command_prefix=self.get_prefix,
                         case_insensitive=True,
                         intents=intents,
                         status=discord.Status.online,
                         strip_after_prefix=True,
                         owner_ids=OWNER_IDS,
                         allowed_mentions=discord.AllowedMentions(
                             everyone=False, replied_user=False, roles=False),
                         shard_count=2)

    async def setup_hook(self):
        await run_startup_migrations()
        self.session = aiohttp.ClientSession()
        await self.load_extensions() 

    async def load_extensions(self):
        for extension in extensions:
            try:
                await self.load_extension(extension) 
                log.info("Loaded extension: %s", extension)
                print(Fore.BLUE + Style.BRIGHT + f"Loaded extension: {extension}")
            except Exception as e:
                log.exception("Failed to load extension %s", extension)
                print(f"{Fore.RED}{Style.BRIGHT}Failed to load extension {extension}. {e}")
                raise
        print(Fore.GREEN + Style.BRIGHT + "*" * 20)

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
        try:
            await super().close()
        except AttributeError as exc:
            if "_AutoShardedClient__queue" not in str(exc):
                raise

    
    async def on_connect(self):
        await self.change_presence(status=discord.Status.dnd,
                                   activity=discord.Activity(
                                       type=discord.ActivityType.playing,
                                       name='>help | >invite'))

    async def send_raw(self, channel_id: int, content: str,
                       **kwargs) -> typing.Optional[discord.Message]:
        return await self.http.send_message(channel_id, content, **kwargs)

    async def invoke_help_command(self, ctx: Context) -> None:
        """Invoke the help command or default help command if help extensions is not loaded."""
        return await ctx.send_help(ctx.command)

    async def fetch_message_by_channel(
            self, channel: discord.TextChannel,
            messageID: int) -> typing.Optional[discord.Message]:
        async for msg in channel.history(
                limit=1,
                before=discord.Object(messageID + 1),
                after=discord.Object(messageID - 1),
        ):
            return msg

    async def get_prefix(self, message: discord.Message):
        if message.guild:
            guild_id = message.guild.id
            async with aiosqlite.connect('db/np.db') as db:
                async with db.execute("SELECT id FROM np WHERE id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        data = await getConfig(guild_id)
                        prefix = data["prefix"]
                        # Np user
                        return commands.when_mentioned_or(prefix, '')(self, message)
                    else:
                        # non np
                        data = await getConfig(guild_id)
                        prefix = data["prefix"]
                        return commands.when_mentioned_or(prefix)(self, message)
        else:
            async with aiosqlite.connect('db/np.db') as db:
                async with db.execute("SELECT id FROM np WHERE id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        #NO user (Dms)
                        return commands.when_mentioned_or('>', '')(self, message)
                    else:
                        #Non Np user (DMs)
                        return commands.when_mentioned_or('')(self, message)


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
        else:
            return




def setup_bot():
    intents = discord.Intents.all()
    bot = axon(intents=intents)
    return bot
