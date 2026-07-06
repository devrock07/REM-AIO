from utils import emojis
from utils.components_v2 import success_panel, error_panel, info_panel

import asyncio
import discord
from discord.ext import commands
import aiosqlite
from utils.Tools import *


class Unwhitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.initialize_db())

    async def initialize_db(self):
        self.db = await aiosqlite.connect('db/anti.db')

    @commands.hybrid_command(name='unwhitelist', aliases=['unwl'], help="Unwhitelist a user from antinuke")
    @commands.has_permissions(administrator=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def unwhitelist(self, ctx, member: discord.Member = None):
        if ctx.guild.member_count < 2:
            return await ctx.send(view=error_panel(f"{emojis.CROSSICON} | Your Server Doesn't Meet My 30 Member Criteria"))

        async with self.db.execute(
            "SELECT owner_id FROM extraowners WHERE guild_id = ? AND owner_id = ?",
            (ctx.guild.id, ctx.author.id)
        ) as cursor:
            check = await cursor.fetchone()

        async with self.db.execute(
            "SELECT status FROM antinuke WHERE guild_id = ?",
            (ctx.guild.id,)
        ) as cursor:
            antinuke = await cursor.fetchone()

        is_owner = ctx.author.id == ctx.guild.owner_id
        if not is_owner and not check:
            return await ctx.send(view=error_panel(
                "Only Server Owner or Extra Owner can Run this Command!",
                title=f"{emojis.CROSSICON} Access Denied"
            ))

        if not antinuke or not antinuke[0]:
            return await ctx.send(view=info_panel(
                f"**{ctx.guild.name} Security Settings {emojis.MOD}\n"
                "Ohh NO! looks like your server doesn't enabled security\n\n"
                f"Current Status : {emojis.DISABLED1}\n\n"
                "To enable use `antinuke enable` **"
            ))

        if not member:
            return await ctx.send(view=info_panel(
                f"**Removes user from whitelisted users which means that the antinuke module will now take actions on them if they trigger it.**",
                title="__**Unwhitelist Commands**__",
                fields=[("__**Usage**__", f"{emojis.RED_DOT} `unwhitelist @user/id`\n{emojis.RED_DOT} `unwl @user`")]
            ))

        async with self.db.execute(
            "SELECT * FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id)
        ) as cursor:
            data = await cursor.fetchone()

        if not data:
            return await ctx.send(view=error_panel(
                f"<@{member.id}> is not a whitelisted member.",
                title=f"{emojis.CROSSICON} Error"
            ))

        await self.db.execute(
            "DELETE FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id)
        )
        await self.db.commit()

        await ctx.send(view=success_panel(
            f"User <@!{member.id}> has been removed from the whitelist.",
            title=f"{emojis.TICK} Success"
        ))


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""
