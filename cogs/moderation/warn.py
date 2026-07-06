from utils import emojis

import discord
from discord.ext import commands
from discord import ui
import aiosqlite
import asyncio
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view


class WarnView(ui.View):
    def __init__(self, user, author):
        super().__init__(timeout=60)
        self.user = user
        self.author = author
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @ui.button(style=discord.ButtonStyle.gray, emoji=f"{emojis.DELETE}")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.from_rgb(0, 0, 0)
        self.db_path = "db/warn.db"

        
        asyncio.create_task(self.setup())

    def get_user_avatar(self, user):
        return user.avatar.url if user.avatar else user.default_avatar.url

    async def add_warn(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO warns (guild_id, user_id, warns) VALUES (?, ?, 0)", (guild_id, user_id))
            await db.execute("UPDATE warns SET warns = warns + 1 WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            await db.commit()

    async def get_total_warns(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT warns FROM warns WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return 0

    async def reset_warns(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE warns SET warns = 0 WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            await db.commit()

    async def setup(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    guild_id INTEGER,
                    user_id INTEGER,
                    warns INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
                """)
                await db.commit()
        except Exception as e:
            print(f"Error during database setup: {e}")

    @commands.hybrid_command(
        name="warn",
        help="Warn a user in the server",
        usage="warn <user> [reason]",
        aliases=["warnuser"])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    #@commands.bot_has_permissions(manage_messages=True)
    async def warn(self, ctx, user: discord.Member, *, reason=None):
        if user == ctx.author:
            return await ctx.reply("You cannot warn yourself.")

        if user == ctx.bot.user:
            return await ctx.reply("You cannot warn me.")

        if not ctx.author == ctx.guild.owner:
            if user == ctx.guild.owner:
                return await ctx.reply("I cannot warn the server owner.")

            if ctx.author.top_role <= user.top_role:
                return await ctx.reply("You cannot Warn a member with a higher or equal role.")

        if ctx.guild.me.top_role <= user.top_role:
            return await ctx.reply("I cannot Warn a member with a higher or equal role.")

        if user not in ctx.guild.members:
            return await ctx.reply("The user is not a member of this server.")
        try:
            
            await self.add_warn(ctx.guild.id, user.id)
            total_warns = await self.get_total_warns(ctx.guild.id, user.id)

            
            reason_to_send = reason or "No reason provided"
            try:
                await user.send(f"You have been warned in **{ctx.guild.name}** by **{ctx.author}**. Reason: {reason_to_send}")
                dm_status = "Yes"
            except discord.Forbidden:
                dm_status = "No"
            except discord.HTTPException:
                dm_status = "No"

            
            embed = discord.Embed(description=f"**Target User:** [{user}](https://discord.com/users/{user.id})\n"
                                              f"** User Mention:** {user.mention}\n"
                                              f"**DM Sent:** {dm_status}\n"
                                              f"** Reason:** {reason_to_send}\n"
                                              f"** Total Warns:** {total_warns}",
                                              color=self.color)
            embed.set_author(name=f"Successfully Warned {user.name}", icon_url=self.get_user_avatar(user))
            embed.add_field(name="Moderator:", value=ctx.author.mention, inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=self.get_user_avatar(ctx.author))
            embed.timestamp = discord.utils.utcnow()

            view = WarnView(user=user, author=ctx.author)
            message = await ctx.send(view = embed_to_view(embed, view = view))
            view.message = message
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error during warn command: {e}")

    @commands.hybrid_command(
        name="clearwarns",
        help="Clear all warnings for a user",
        aliases=["clearwarn" , "clearwarnings"],
        usage="clearwarns <user>")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, ctx, user: discord.Member):
        try:
            await self.reset_warns(ctx.guild.id, user.id)
            embed = discord.Embed(description=f"{emojis.TICK} | All warnings have been cleared for **{user}** in this guild.", color=self.color)
            embed.set_author(name=f"Warnings Cleared", icon_url=self.get_user_avatar(user))
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=self.get_user_avatar(ctx.author))
            embed.timestamp = discord.utils.utcnow()

            await ctx.send(view = embed_to_view(embed))
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error during clearwarns command: {e}")


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""