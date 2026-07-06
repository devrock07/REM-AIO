from utils import emojis
from utils.components_v2 import success_panel, error_panel, info_panel

import asyncio
import discord
from discord.ext import commands
import aiosqlite
import re
from utils.Tools import *

class AutoReaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'db/autoreact.db'
        asyncio.create_task(self.setup_database())

    async def setup_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS autoreact (
                    guild_id INTEGER,
                    trigger TEXT,
                    emojis TEXT
                )
            """)
            await db.commit()

    async def get_triggers(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT trigger, emojis FROM autoreact WHERE guild_id = ?", (guild_id,))
            return await cursor.fetchall()

    async def trigger_exists(self, guild_id, trigger):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT 1 FROM autoreact WHERE guild_id = ? AND trigger = ?", (guild_id, trigger))
            return await cursor.fetchone()

    @commands.group(name="react", aliases=["autoreact"], help="Lists all subcommands of autoreact group.", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def react(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @react.command(name="add", aliases=["set", "create"], help="Adds a trigger and its emojis to the autoreact.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, trigger: str, *, emojis_arg: str):
        if len(trigger.split()) > 1:
            return await ctx.reply(view=error_panel(
                "Triggers can only be one word.",
                title=f"{emojis.CROSSICON} Invalid Trigger"
            ))

        emoji_list = re.findall(r"<a?:\w+:\d+>|[\u263a-\U0001f645]", emojis_arg)
        if len(emoji_list) > 10:
            return await ctx.reply(view=error_panel(
                "You can only set up to **10** emojis per trigger.",
                title=f"{emojis.CROSSICON} Too Many Emojis"
            ))

        triggers = await self.get_triggers(ctx.guild.id)
        if len(triggers) >= 10:
            return await ctx.reply(view=error_panel(
                "You can only set up to 10 triggers for auto-reactions in this guild.",
                title=f"{emojis.ICONS_WARNING} Trigger Limit Reached"
            ))

        if await self.trigger_exists(ctx.guild.id, trigger):
            return await ctx.reply(view=error_panel(
                f"The trigger '{trigger}' already exists. Remove it before adding it again.",
                title=f"{emojis.ICONS_WARNING} Trigger Exists"
            ))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO autoreact (guild_id, trigger, emojis) VALUES (?, ?, ?)", 
                             (ctx.guild.id, trigger, " ".join(emoji_list)))
            await db.commit()

        await ctx.reply(view=success_panel(
            f"Successfully added trigger '{trigger}' with emojis {', '.join(emoji_list)}.",
            title=f"{emojis.TICK} Trigger Added"
        ))

    @react.command(name="remove", aliases=["clear", "delete"], help="Removes a trigger and its emojis from the autoreact.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, trigger: str):
        if not await self.trigger_exists(ctx.guild.id, trigger):
            return await ctx.reply(view=error_panel(
                f"The trigger '{trigger}' does not exist.",
                title=f"{emojis.CROSSICON} Trigger Not Found"
            ))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM autoreact WHERE guild_id = ? AND trigger = ?", (ctx.guild.id, trigger))
            await db.commit()

        await ctx.reply(view=success_panel(
            f"Successfully removed trigger '{trigger}'.",
            title=f"{emojis.TICK} Trigger Removed"
        ))

    @react.command(name="list", aliases=["show", "config"], help="Lists all the triggers and their emojis in the autoreact module.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def list(self, ctx):
        triggers = await self.get_triggers(ctx.guild.id)
        if not triggers:
            return await ctx.reply(view=info_panel(
                "There are no auto-reaction triggers set in this guild.",
                title="No Triggers Set"
            ))

        trigger_list = "\n".join([f"{t[0]}: {t[1]}" for t in triggers])
        await ctx.reply(view=info_panel(
            trigger_list,
            title="Auto-Reaction Triggers"
        ))

    @react.command(name="reset", help="Resets all the triggers and their emojis in the autoreact module.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx):
        triggers = await self.get_triggers(ctx.guild.id)
        if not triggers:
            return await ctx.reply(view=error_panel(
                "There are no auto-reaction triggers set to reset.",
                title=f"{emojis.CROSSICON} No Triggers Set"
            ))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM autoreact WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()

        await ctx.reply(view=success_panel(
            "Successfully removed all auto-reaction triggers.",
            title=f"{emojis.TICK} All Triggers Reset"
        ))

async def setup(bot):
    await bot.add_cog(AutoReaction(bot))

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out support or DM me.
"""
