from utils import emojis

import discord
import aiosqlite
from discord.ext import commands
from utils.Tools import blacklist_check, ignore_check
from collections import defaultdict
import time
from utils.cv2_compat import embed_to_view, embeds_to_view

class Media(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.infractions = defaultdict(list)
        

    async def set_db(self):
        async with aiosqlite.connect('db/media.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS media_channels (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS media_bypass (
                    guild_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.set_db()

    @commands.hybrid_group(name="media", help="Setup Media channel, Media channel will not allow users to send messages other than media files.", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def media(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @media.command(name="setup", aliases=["set", "add"], help="Sets up a media-only channel for the server")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, *, channel: discord.TextChannel):
        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT channel_id FROM media_channels WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    embed = discord.Embed(
                        title=f"{emojis.CROSSICON} Error",
                        description="A media channel is already set. Please remove it before setting a new one.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

            await db.execute('INSERT INTO media_channels (guild_id, channel_id) VALUES (?, ?)', (ctx.guild.id, channel.id))
            await db.commit()

        embed = discord.Embed(
            title=f"{emojis.TICK} Success",
            description=f"Successfully set {channel.mention} as the media-only channel.",
            color=0x000000
        )
        embed.set_footer(text="Make sure to grant me \"Manage Messages\" permission for functioning of media channel.")
        await ctx.reply(view = embed_to_view(embed))

    @media.command(name="remove", aliases=["reset", "delete"], help="Removes the current media-only channel")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT channel_id FROM media_channels WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    embed = discord.Embed(
                        title=f"{emojis.CROSSICON} Error",
                        description="There is no media-only channel set for this server.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

            await db.execute('DELETE FROM media_channels WHERE guild_id = ?', (ctx.guild.id,))
            await db.commit()

        embed = discord.Embed(
            title=f"{emojis.TICK} Success",
            description="Successfully removed the media-only channel.",
            color=0x000000
        )
        await ctx.reply(view = embed_to_view(embed))

    @media.command(name="config", aliases=["settings", "show"], help="Shows the configured media-only channel")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT channel_id FROM media_channels WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    embed = discord.Embed(
                        title=f"{emojis.CROSSICON} Error",
                        description="There is no media-only channel set for this server.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

        channel = self.client.get_channel(result[0])
        embed = discord.Embed(
            title="Media Only Channel",
            description=f"The configured media-only channel is {channel.mention}.",
            color=0x000000
        )
        await ctx.reply(view = embed_to_view(embed))

    @media.group(name="bypass", help="Add/Remove user to bypass in Media only channel, Bypassed users can send messages in Media channel.", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def bypass(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @bypass.command(name="add", help="Adds a user to the bypass list")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def bypass_add(self, ctx, user: discord.Member):
        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT COUNT(*) FROM media_bypass WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                count = await cursor.fetchone()
                if count[0] >= 25:
                    embed = discord.Embed(
                        title=f"{emojis.CROSSICON} Error",
                        description="The bypass list can only hold up to 25 users.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

            async with db.execute('SELECT 1 FROM media_bypass WHERE guild_id = ? AND user_id = ?', (ctx.guild.id, user.id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    embed = discord.Embed(
                        title=f"{emojis.CROSSICON} Error",
                        description=f"{user.mention} is already in the bypass list.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

            await db.execute('INSERT INTO media_bypass (guild_id, user_id) VALUES (?, ?)', (ctx.guild.id, user.id))
            await db.commit()

        embed = discord.Embed(
            title=f"{emojis.TICK} Success",
            description=f"{user.mention} has been added to the bypass list.",
            color=0x000000
        )
        await ctx.reply(view = embed_to_view(embed))

    @bypass.command(name="remove", help="Removes a user from the bypass list")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def bypass_remove(self, ctx, user: discord.Member):
        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT 1 FROM media_bypass WHERE guild_id = ? AND user_id = ?', (ctx.guild.id, user.id)) as cursor:
                result = await cursor.fetchone()
                if not result:
                    embed = discord.Embed(
                        title=f"{emojis.CROSSICON} Error",
                        description=f"{user.mention} is not in the bypass list.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

            await db.execute('DELETE FROM media_bypass WHERE guild_id = ? AND user_id = ?', (ctx.guild.id, user.id))
            await db.commit()

        embed = discord.Embed(
            title=f"{emojis.TICK} Success",
            description=f"{user.mention} has been removed from the bypass list.",
            color=0x000000
        )
        await ctx.reply(view = embed_to_view(embed))

    @bypass.command(name="show", aliases=["list", "view"], help="Shows the bypass list")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def bypass_show(self, ctx):
        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT user_id FROM media_bypass WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                result = await cursor.fetchall()
                if not result:
                    embed = discord.Embed(
                        title="Bypass List",
                        description="There are no users in the bypass list.",
                        color=0x000000
                    )
                    await ctx.reply(view = embed_to_view(embed))
                    return

        users = [self.client.get_user(user_id).mention for user_id, in result]
        user_mentions = "\n".join(users)

        embed = discord.Embed(
            title="Bypass List",
            description=user_mentions,
            color=0x000000
        )
        await ctx.reply(view = embed_to_view(embed))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        async with aiosqlite.connect('db/media.db') as db:
            async with db.execute('SELECT channel_id FROM media_channels WHERE guild_id = ?', (message.guild.id,)) as cursor:
                media_channel = await cursor.fetchone()

        if media_channel and message.channel.id == media_channel[0]:
            async with aiosqlite.connect('db/block.db') as block_db:
                async with block_db.execute('SELECT 1 FROM user_blacklist WHERE user_id = ?', (message.author.id,)) as cursor:
                    blacklisted = await cursor.fetchone()

            async with aiosqlite.connect('db/media.db') as db:
                async with db.execute('SELECT 1 FROM media_bypass WHERE guild_id = ? AND user_id = ?', (message.guild.id, message.author.id)) as cursor:
                    bypassed = await cursor.fetchone()

            if blacklisted or bypassed:
                return

            if not message.attachments:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} This channel is configured for Media only. Please send only media files.",
                    delete_after=5
                )
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
                except Exception:
                    pass

                current_time = time.time()
                self.infractions[message.author.id].append(current_time)

                
                self.infractions[message.author.id] = [
                    infraction for infraction in self.infractions[message.author.id]
                    if current_time - infraction <= 5
                ]

                if len(self.infractions[message.author.id]) >= 5:  
                    async with aiosqlite.connect('db/block.db') as block_db:
                        await block_db.execute('INSERT OR IGNORE INTO user_blacklist (user_id) VALUES (?)', (message.author.id,))
                        
                        await block_db.commit()

                    embed = discord.Embed(
                        title="You Have Been Blacklisted",
                        description=(
                            f"{emojis.ICONS_WARNING} You are blacklisted from using my commands due to spamming in the media channel. "
                            "If you believe this is a mistake, please reach out to the support server with proof."
                        ),
                        color=0x000000
                    )
                    await message.channel.send(f"{message.author.mention}", view = embed_to_view(embed))
                    del self.infractions[message.author.id]

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""