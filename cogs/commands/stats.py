from __future__ import annotations

import datetime
import os
import platform
import time

import aiosqlite
import discord
import psutil
import wavelink
<<<<<<< HEAD
from discord import Embed
from discord.ext import commands

from utils import emojis
from utils.Tools import blacklist_check, ignore_check
from utils.cv2_compat import embed_to_view

=======
from utils.cv2_compat import embed_to_view, embeds_to_view
>>>>>>> 597e821a07560f19f64c5b9f02daf0e0fc653532

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.total_songs_played = 0
        self._code_stats: tuple[int, int, int] | None = None
        bot.loop.create_task(self.setup_database())

    async def setup_database(self):
        os.makedirs("db", exist_ok=True)
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER)")
            await db.commit()
            async with db.execute("SELECT value FROM stats WHERE key = 'total_songs_played'") as cursor:
                row = await cursor.fetchone()
            self.total_songs_played = row[0] if row else 0
            if row is None:
                await db.execute("INSERT INTO stats (key, value) VALUES ('total_songs_played', 0)")
                await db.commit()

    async def update_total_songs_played(self):
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute(
                "INSERT OR REPLACE INTO stats (key, value) VALUES ('total_songs_played', ?)",
                (self.total_songs_played,),
            )
            await db.commit()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        self.total_songs_played += 1
        await self.update_total_songs_played()

    def count_code_stats(self, file_path: str) -> tuple[int, int]:
        total_lines = 0
        total_words = 0
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    stripped = line.strip()
                    if stripped:
                        total_lines += 1
                        total_words += len(stripped.split())
        except (UnicodeDecodeError, OSError):
            pass
        return total_lines, total_words

    def gather_file_stats(self, directory: str) -> tuple[int, int, int]:
        total_files = 0
        total_lines = 0
        total_words = 0
        skipped_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".venv",
            "venv",
            "env",
            "data",
            "db",
            "node_modules",
        }

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in skipped_dirs]
            if any(part in skipped_dirs for part in os.path.normpath(root).split(os.sep)):
                continue
            for file in files:
                if not file.endswith(".py") or ".bak" in file:
                    continue
                file_path = os.path.join(root, file)
                total_files += 1
                file_lines, file_words = self.count_code_stats(file_path)
                total_lines += file_lines
                total_words += file_words

        return total_files, total_lines, total_words

    @commands.hybrid_command(
        name="stats",
        aliases=["botinfo", "botstats", "bi", "statistics"],
        help="Shows the bot's information.",
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 7, commands.BucketType.user)
<<<<<<< HEAD
    async def stats(self, ctx: commands.Context):
        processing_message = await ctx.send(f"{emojis.LOADING} Loading REM ALL IN ONE BOT information...")

=======
    async def stats(self, ctx):
        processing_message = await ctx.send(f"{emojis.LOADING} Loading REM ALL IN ONE BOT information...")
>>>>>>> 597e821a07560f19f64c5b9f02daf0e0fc653532
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds if g.member_count is not None)
        bot_count = sum(sum(1 for m in g.members if m.bot) for g in self.bot.guilds)
        human_count = max(user_count - bot_count, 0)
        total_users = human_count + bot_count

        all_channels = list(self.bot.get_all_channels())
        text_channel_count = sum(isinstance(c, discord.TextChannel) for c in all_channels)
        voice_channel_count = sum(isinstance(c, discord.VoiceChannel) for c in all_channels)
        category_channel_count = sum(isinstance(c, discord.CategoryChannel) for c in all_channels)
        channel_count = len(all_channels)

        slash_commands = len(self.bot.tree.get_commands())
        commands_count = len(set(self.bot.walk_commands()))

        uptime_seconds = int(time.time() - self.start_time)
        uptime_timedelta = datetime.timedelta(seconds=uptime_seconds)
        uptime = str(uptime_timedelta)

        if self._code_stats is None:
            self._code_stats = self.gather_file_stats(".")
        total_files, total_lines, total_words = self._code_stats
        cpu_info = psutil.cpu_freq()
        memory_info = psutil.virtual_memory()
        channels_connected = sum(1 for vc in self.bot.voice_clients if vc)
        playing_tracks = sum(1 for vc in self.bot.voice_clients if getattr(vc, "playing", False))

<<<<<<< HEAD
        shard_id = ctx.guild.shard_id if ctx.guild else 0
        shard = self.bot.get_shard(shard_id)
        websocket_latency = round(self.bot.latency * 1000, 2)
        shard_latency = round((shard.latency if shard else self.bot.latency) * 1000, 2)
=======
        embed = Embed(title="REM ALL IN ONE BOT Statistics: General", color=0x000000)
        embed.add_field(name=" Channels", value=f"Total: **{channel_count}**\nText: **{text_channel_count}**   |   Voice: **{voice_channel_count}**   |   Category: **{category_channel_count}**", inline=False)
        embed.add_field(name=f"{emojis.ICON_PING} Uptime", value=f"{uptime}", inline=False)
        embed.add_field(name=f"{emojis.USER} User Count", value=f"Humans: **{human_count}**   |   Bots: **{bot_count}**", inline=False)
        embed.add_field(name=f"{emojis.FILE} Commands", value=f"Total: **{commands_count}**   |   Slash: **{slash_commands}**", inline=False)
        embed.add_field(name=f"{emojis.ICONS_CHANNEL} Libraries Used", value=f"Discord Library: **[discord.py](https://discordpy.readthedocs.io/en/stable/)**", inline=False)
        embed.add_field(name=f"{emojis.ICONS_DISCORDBOTDEV} Codebase Stats", value=f"Total Python Files: **{total_files}**\nTotal Lines: **{total_lines}**\nTotal Words: **{total_words}**", inline=False)
        embed.add_field(name=f"{emojis.ICONS_MUSIC} Music Stats", value=f"Currently Connected: **{channels_connected}**\nCurrently Playing: **{playing_tracks}**\nTotal Songs Played: **{self.total_songs_played}**", inline=False)
        embed.set_footer(text="Powered by REM ALL IN ONE BOT", icon_url=self.bot.user.display_avatar.url)
>>>>>>> 597e821a07560f19f64c5b9f02daf0e0fc653532

        db_latency = "N/A"
        try:
            async with aiosqlite.connect("db/afk.db") as db:
                start = time.perf_counter()
                await db.execute("SELECT 1")
                db_latency = f"{round((time.perf_counter() - start) * 1000, 2)} ms"
        except Exception:
            pass

<<<<<<< HEAD
        embed = Embed(title="REM ALL IN ONE BOT Statistics", color=0x000000)
        embed.add_field(
            name="Channels",
            value=(
                f"Total: **{channel_count}**\n"
                f"Text: **{text_channel_count}** | Voice: **{voice_channel_count}** | "
                f"Categories: **{category_channel_count}**"
            ),
            inline=False,
        )
        embed.add_field(name=f"{emojis.ICON_PING} Uptime", value=uptime, inline=False)
        embed.add_field(name=f"{emojis.USER} Users", value=f"Humans: **{human_count}** | Bots: **{bot_count}** | Total: **{total_users}**", inline=False)
        embed.add_field(name=f"{emojis.FILE} Commands", value=f"Prefix: **{commands_count}** | Slash: **{slash_commands}**", inline=False)
        embed.add_field(name=f"{emojis.ICONS_DISCORDBOTDEV} Codebase", value=f"Python Files: **{total_files}**\nLines: **{total_lines}**\nWords: **{total_words}**", inline=False)
        embed.add_field(name=f"{emojis.ICONS_MUSIC} Music", value=f"Connected: **{channels_connected}**\nPlaying: **{playing_tracks}**\nSongs Played: **{self.total_songs_played}**", inline=False)
        embed.add_field(
            name="System",
            value=(
                f"discord.py: **{discord.__version__}**\n"
                f"Python: **{platform.python_version()}**\n"
                f"Platform: **{platform.system()} {platform.machine()}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="Memory / CPU",
            value=(
                f"Memory Used: **{memory_info.used / (1024 ** 2):,.2f} MB**\n"
                f"Memory Available: **{memory_info.available / (1024 ** 2):,.2f} MB**\n"
                f"CPU Usage: **{psutil.cpu_percent()}%**\n"
                f"CPU Speed: **{(cpu_info.current if cpu_info else 0):.2f} MHz**"
            ),
            inline=False,
        )
        embed.add_field(name="Latency", value=f"Shard: **{shard_latency} ms**\nWebsocket: **{websocket_latency} ms**\nDatabase: **{db_latency}**", inline=False)
        embed.set_footer(text="Powered by REM ALL IN ONE BOT", icon_url=self.bot.user.display_avatar.url)

        await ctx.reply(view=embed_to_view(embed), mention_author=False)
=======
        general_button = Button(label="General", style=ButtonStyle.gray)
        async def general_button_callback(interaction):
            if interaction.user == ctx.author:
                await interaction.response.edit_message(view = embed_to_view(embed, view = view))
        general_button.callback = general_button_callback
        view.add_item(general_button)

        system_button = Button(label="System", style=ButtonStyle.gray)
        async def system_button_callback(interaction):
            if interaction.user == ctx.author:
                system_embed = Embed(title="REM ALL IN ONE BOT Statistics: System", color=0x000000)
                system_embed.add_field(name=f"{emojis.COMMANDS} System Info", value=f"• Discord.py: **{discord.__version__}**\n• Python: **{platform.python_version()}**\n• Architecture: **{platform.machine()}**\n• Platform: **{platform.system()}**", inline=False)
                system_embed.add_field(name=f"{emojis.QUESTIONS} Memory Info", value=f"• Total Memory: **{memory_info.total / (1024 ** 2):,.2f} MB**\n• Memory Left: **{memory_info.available / (1024 ** 2):,.2f} MB**\n• Heap Total: **{memory_info.used / (1024 ** 2):,.2f} MB**", inline=False)
                system_embed.add_field(name=f"{emojis.ICONSETTING} CPU Info", value=f"• CPU: **{psutil.cpu_freq().max}' GHz**\n• CPU Usage: **{psutil.cpu_percent()}%**\n• CPU Cores: **{psutil.cpu_count(logical=False)}**\n• CPU Speed: **{cpu_info.current:.2f} MHz**", inline=False)
                system_embed.set_footer(text="Powered by REM ALL IN ONE BOT", icon_url=self.bot.user.display_avatar.url)
                await interaction.response.edit_message(view = embed_to_view(system_embed, view = view))
        system_button.callback = system_button_callback
        view.add_item(system_button)

        ping_button = Button(label="Ping", style=ButtonStyle.green)
        async def ping_button_callback(interaction):
            if interaction.user == ctx.author:
                s_id = ctx.guild.shard_id
                sh = self.bot.get_shard(s_id)
                db_latency = None
                try:
                    async with aiosqlite.connect("db/afk.db") as db:
                        start_time = time.perf_counter()
                        await db.execute("SELECT 1")
                        end_time = time.perf_counter()
                        db_latency = (end_time - start_time) * 1000
                        db_latency = round(db_latency, 2)
                except Exception:
                    db_latency = "N/A"
                wsping = round(self.bot.latency * 1000, 2)
                ping_embed = Embed(title="Bot Statistic: Ping", color=0x000000)
                ping_embed.add_field(name="🏓 Bot Latency", value=f"{round(sh.latency * 800)} ms", inline=False)
                ping_embed.add_field(name="🏓 Database Latency", value=f"{db_latency} ms", inline=False)
                ping_embed.add_field(name="🏓 Websocket Latency", value=f"{wsping} ms", inline=False)
                ping_embed.set_footer(text="Powered by REM ALL IN ONE BOT", icon_url=self.bot.user.display_avatar.url)
                await interaction.response.edit_message(view = embed_to_view(ping_embed, view = view))
        ping_button.callback = ping_button_callback
        view.add_item(ping_button)

        delete_button = Button(label="🗑️", style=ButtonStyle.red)
        async def delete_button_callback(interaction):
            if interaction.user == ctx.author:
                await interaction.message.delete()
        delete_button.callback = delete_button_callback
        view.add_item(delete_button)

        server_count_button = Button(label=f"Servers: {guild_count}    |    Users: {blahh}", style=ButtonStyle.success, disabled=True)
        view.add_item(server_count_button)

        await ctx.reply(view = embed_to_view(embed, view = view))
>>>>>>> 597e821a07560f19f64c5b9f02daf0e0fc653532
        await processing_message.delete()
