from utils import emojis

import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
import aiosqlite
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view

class Extraowner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.initialize_db())

    async def initialize_db(self):
        self.db = await aiosqlite.connect('db/anti.db')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS extraowners (
                guild_id INTEGER PRIMARY KEY,
                owner_id INTEGER
            )
        ''')
        await self.db.commit()

    @commands.hybrid_command(name='extraowner', aliases=["owner"], help="Adds Extraowner to the server")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def extraowner(self, ctx, option: str = None, user: discord.Member = None):
        guild_id = ctx.guild.id

        if ctx.guild.member_count < 2:
            embed = discord.Embed(
                description="❌ | Your Server Doesn't Meet My 30 Member Criteria",
                color=0x000000
            )
            await ctx.send(view = embed_to_view(embed))
            return

        REM_BYPASS_IDS = ['767979794411028491', '767979794411028491']
        if ctx.author.id != ctx.guild.owner_id and str(ctx.author.id) not in REM_BYPASS_IDS:
            embed = discord.Embed(title="Access Denied",
                                  description="Only Server Owner Can Run This Command",
                                  color=0x000000
            )
            await ctx.send(view = embed_to_view(embed))
            return

        if option is None:
            pre = ctx.prefix
            embed = discord.Embed(
                title="__**Extra Owner**__",
                description="Extraowners can adjust server antinuke settings & manage whitelist events, so careful consideration is essential before assigning it to someone.",
                color=0x000000
            )
            embed.add_field(name="__**Extraowner Set**__", value=f"To Set Extra Owner, Use - **{pre}extraowner set @user**")
            embed.add_field(name="__**Extraowner Reset**__", value=f"To Reset Extra Owner, Use - **{pre}extraowner reset**")
            embed.add_field(name="__**Extraowner View**__", value=f"To View Extra Owner, Use - **{pre}extraowner view**")
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            await ctx.reply(view = embed_to_view(embed))
            return

        
        if option.lower() == 'set':
            if user is None or user.bot:
                embed = discord.Embed(title="Error",
                    description="Please Provide a Valid User Mention or ID to Set as Extra Owner!",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed))
                return

            
            view = ConfirmView(ctx)
            embed = discord.Embed(
                title="Confirm Action",
                description=f"**Are you sure you want to set {user.mention} as the Extra Owner?**",
                color=0x000000
            )
            message = await ctx.reply(view = embed_to_view(embed, view = view))
            await view.wait()

            if view.value is None:
                await message.edit(content=" Confirmation timed out.", )
            elif view.value:
                await self.db.execute('INSERT OR REPLACE INTO extraowners (guild_id, owner_id) VALUES (?, ?)', (guild_id, user.id))
                await self.db.commit()
                embed = discord.Embed(title=f"{emojis.TICK} Success",
                    description=f"Added {user.mention} As Extraowner",
                    color=0x000000
                )
                await message.edit(view = embed_to_view(embed, view = None))
            else:
                await message.edit(content=f"{emojis.CROSSICON} Action cancelled.", )

        
        elif option.lower() == 'reset':
            async with self.db.execute('SELECT owner_id FROM extraowners WHERE guild_id = ?', (guild_id,)) as cursor:
                row = await cursor.fetchone()

            if not row:
                embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                    description="No extra owner has been designated for this guild.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed))
            else:
                
                view = ConfirmView(ctx)
                embed = discord.Embed(
                    title="Confirm Action",
                    description="**Are you sure you want to reset the Extra Owner?**",
                    color=0x000000
                )
                message = await ctx.reply(view = embed_to_view(embed, view = view))
                await view.wait()

                if view.value is None:
                    await message.edit(content=" Confirmation timed out.", )
                elif view.value:
                    await self.db.execute('DELETE FROM extraowners WHERE guild_id = ?', (guild_id,))
                    await self.db.commit()
                    embed = discord.Embed(title=f"{emojis.OLYMPUS_TICK} Success",
                        description="Disabled Extraowner Configuration!",
                        color=0x000000
                    )
                    await message.edit(view = embed_to_view(embed, view = None))
                else:
                    await message.edit(content=f"{emojis.CROSSICON} Action canceled.", )

        elif option.lower() == 'view':
            async with self.db.execute('SELECT owner_id FROM extraowners WHERE guild_id = ?', (guild_id,)) as cursor:
                row = await cursor.fetchone()

            if not row:
                embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                    description="No extra owner is currently assigned.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed))
            else:
                embed = discord.Embed(
                    description=f"Current Extraowner is <@{row[0]}>",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed))

class ConfirmView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You cannot interact with this confirmation.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.value = False
        self.stop()

