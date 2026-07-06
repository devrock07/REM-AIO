from utils import emojis

import asyncio
import discord
from discord.ext import commands
import aiosqlite
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view

class NotifCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/notify.db"
        self.loop_task = asyncio.create_task(self.setup_db())

    async def setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS notifications (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                type TEXT NOT NULL UNIQUE,
                                role_id INTEGER NOT NULL,
                                channel_id INTEGER NOT NULL)''')
            await db.commit()

    @commands.group(invoke_without_command=True)
    async def setnotif(self, ctx):
        embed = discord.Embed(title="Notification Commands", color=0x000000)
        embed.add_field(name="Subcommands", value="twitch, youtube, list, reset")
        await ctx.send(view = embed_to_view(embed))

    @setnotif.command()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def twitch(self, ctx, role: discord.Role, channel: discord.TextChannel):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT * FROM notifications WHERE type = ?', ('twitch',)) as existing:
                row = await existing.fetchone()
                if row:
                    await ctx.reply(view = embed_to_view(discord.Embed(title=f"{emojis.ICONS_WARNING}Access Denied", description="Twitch notification already set. Remove it first.", color=0x000000)))
                    return

            await db.execute('INSERT INTO notifications (type, role_id, channel_id) VALUES (?, ?, ?)', ('twitch', role.id, channel.id))
            await db.commit()
            await ctx.reply(view = embed_to_view(discord.Embed(title=f"{emojis.TICK} Success", description=f"Twitch notifications set for {role.mention} in {channel.mention}.", color=0x000000)))

    @setnotif.command()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def youtube(self, ctx, role: discord.Role, channel: discord.TextChannel):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT * FROM notifications WHERE type = ?', ('youtube',)) as existing:
                row = await existing.fetchone()
                if row:
                    await ctx.reply(view = embed_to_view(discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="YouTube notification already set. Remove it first.", color=0x000000)))
                    return

            await db.execute('INSERT INTO notifications (type, role_id, channel_id) VALUES (?, ?, ?)', ('youtube', role.id, channel.id))
            await db.commit()
            await ctx.reply(view = embed_to_view(discord.Embed(title=f"{emojis.TICK} Success", description=f"YouTube notifications set for {role.mention} in {channel.mention}.", color=0x000000)))

    @setnotif.command()
    async def list(self, ctx):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT * FROM notifications') as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    await ctx.reply(view = embed_to_view(discord.Embed(description="No Twitch and YouTube notification channels set.", color=0xFF0000)))
                    return

            embed = discord.Embed(title="Current Notification Settings", color=0x000000)
            for row in rows:
                notif_type = row[1].capitalize() 
                role = ctx.guild.get_role(row[2])
                channel = ctx.guild.get_channel(row[3])
                if role and channel:
                    embed.add_field(name=f"{notif_type} Notifications", value=f"Role: {role.mention} | Channel: {channel.mention}", inline=False)
                else:
                    embed.add_field(name=f"{notif_type} Notifications", value="Role or Channel not found", inline=False)

            await ctx.reply(view = embed_to_view(embed))

    @setnotif.command()
    async def reset(self, ctx):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM notifications WHERE type IN (?, ?)', ('twitch', 'youtube'))
            await db.commit()
            await ctx.send(view = embed_to_view(discord.Embed(title=f"{emojis.TICK} Success", description="Twitch and YouTube notifications have been reset.", color=0x00FF00)))


    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        
        streaming = next((activity for activity in after.activities if isinstance(activity, discord.Streaming)), None)

        if streaming:
            stream_type = "twitch" if "twitch" in streaming.url.lower() else "youtube" if "youtube" in streaming.url.lower() else None
            if stream_type:
                async with aiosqlite.connect(self.db_path) as db:
                    async with db.execute('SELECT role_id, channel_id FROM notifications WHERE type = ?', (stream_type,)) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            role_id, channel_id = row
                            role = after.guild.get_role(role_id)
                            channel = after.guild.get_channel(channel_id)

                            if role and channel:
                                embed = discord.Embed(
                                    title=f"{after.display_name} is now live!",
                                    description=f"{after.mention} is now streaming on {stream_type.capitalize()}.",
                                    color=0x000000
                                )
                                embed.add_field(name="Stream Title", value=streaming.name, inline=False)
                                embed.add_field(name="Watch here", value=streaming.url, inline=False)
                                await channel.send(content=role.mention, view = embed_to_view(embed))

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""