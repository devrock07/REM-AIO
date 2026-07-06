from utils import emojis

import discord
from discord.ext import commands
import aiosqlite
import asyncio
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view

class Invcrole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'db/invc.db'
        asyncio.create_task(self.create_table())

    async def create_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS vcroles (
                    guild_id INTEGER PRIMARY KEY,
                    role_id INTEGER NOT NULL
                )
            ''')
            await db.commit()

    @commands.group(name='vcrole', help="Vcrole Setup commands", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def vcrole(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @vcrole.command(name='add', help="Adds a role to the vcrole list")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, role: discord.Role):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT role_id FROM vcroles WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied",
                                          description=f"VC role is already set in this guild with the role {ctx.guild.get_role(row[0]).mention}.\nPlease **remove** it to add another one.", color=0x000000)
                    await ctx.reply(view = embed_to_view(embed))
                    return
            await db.execute('INSERT INTO vcroles (guild_id, role_id) VALUES (?, ?)', (ctx.guild.id, role.id))
            await db.commit()
            embed = discord.Embed(title=f"{emojis.TICK} Success",
                                  description=f"VC role {role.mention} added for this guild.", color=0x000000)
            await ctx.reply(view = embed_to_view(embed))

    @vcrole.command(name='remove', aliases=["reset"], help="Removes the role from vcrole list")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, role: discord.Role):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT role_id FROM vcroles WHERE guild_id = ? AND role_id = ?', (ctx.guild.id, role.id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                                          description="Given role is not set in VC role.", color=0x000000)
                    await ctx.send(view = embed_to_view(embed))
                    return
            await db.execute('DELETE FROM vcroles WHERE guild_id = ? AND role_id = ?', (ctx.guild.id, role.id))
            await db.commit()
            embed = discord.Embed(title=f"{emojis.TICK} Success",
                                  description=f"VC role {role.mention} removed for this guild.", color=0x000000)
            await ctx.send(view = embed_to_view(embed))

    @vcrole.command(name='config', aliases=['view', 'show'], help="Shows the Current vcrole in this Guild")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT role_id FROM vcroles WHERE guild_id = ?', (ctx.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                                          description="VC role is not set in this guild.", color=0x000000)
                    await ctx.send(view = embed_to_view(embed))
                    return
                role = ctx.guild.get_role(row[0])
                embed = discord.Embed(title="VC Role Configuration",
                                      description=f"Current VC role in this guild is {role.mention}.", color=0x000000)
                embed.set_footer(text="Make sure to place My role above Vc role")
                await ctx.send(view = embed_to_view(embed))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT role_id FROM vcroles WHERE guild_id = ?', (member.guild.id,)) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return
                    role = member.guild.get_role(row[0])

                    if after.channel and role not in member.roles:
                        await self.add_role_with_retry(member, role, reason="Member Joined VC | REM ALL IN ONE BOT Invcrole")
                    elif not after.channel and role in member.roles:
                        await self.remove_role_with_retry(member, role, reason="Member Left VC | REM ALL IN ONE BOT Invcrole")
        except discord.Forbidden:
            print(f"Bot lacks permissions to maange role in a guild during Invc Event .")
        except Exception as e:
            print(f"Error in on_voice_state_update: {e}")

    async def add_role_with_retry(self, member, role, reason, retries=5):
        attempt = 0
        while attempt < retries:
            try:
                await member.add_roles(role, reason=reason)
                break
            except discord.errors.RateLimited as e:
                retry_after = e.retry_after if hasattr(e, 'retry_after') else 1
                await asyncio.sleep(retry_after)
            except discord.HTTPException as e:
                print(f"Error adding role: {e}")
                break
            attempt += 1

    async def remove_role_with_retry(self, member, role, reason, retries=5):
        attempt = 0
        while attempt < retries:
            try:
                await member.remove_roles(role, reason=reason)
                break
            except discord.errors.RateLimited as e:
                retry_after = e.retry_after if hasattr(e, 'retry_after') else 1
                await asyncio.sleep(retry_after)
            except discord.HTTPException as e:
                print(f"Error removing role: {e}")
                break
            attempt += 1


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""