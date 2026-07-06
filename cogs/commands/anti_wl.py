from utils import emojis

import asyncio
import discord
from discord.ext import commands
import aiosqlite
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view


class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.initialize_db())

    
    #@commands.Cog.listener()
    async def initialize_db(self):
        self.db = await aiosqlite.connect('db/anti.db')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS whitelisted_users (
                guild_id INTEGER,
                user_id INTEGER,
                ban BOOLEAN DEFAULT FALSE,
                kick BOOLEAN DEFAULT FALSE,
                prune BOOLEAN DEFAULT FALSE,
                botadd BOOLEAN DEFAULT FALSE,
                serverup BOOLEAN DEFAULT FALSE,
                memup BOOLEAN DEFAULT FALSE,
                chcr BOOLEAN DEFAULT FALSE,
                chdl BOOLEAN DEFAULT FALSE,
                chup BOOLEAN DEFAULT FALSE,
                rlcr BOOLEAN DEFAULT FALSE,
                rlup BOOLEAN DEFAULT FALSE,
                rldl BOOLEAN DEFAULT FALSE,
                meneve BOOLEAN DEFAULT FALSE,
                mngweb BOOLEAN DEFAULT FALSE,
                mngstemo BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        await self.db.commit()

    @commands.hybrid_command(name='whitelist', aliases=['wl'], help="Whitelists a user from antinuke for a specific action.")

    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)

    async def whitelist(self, ctx, member: discord.Member = None):
        if ctx.guild.member_count < 2:
            embed = discord.Embed(
                color=0x000000,
                description=f"{emojis.CROSSICON} | Your Server Doesn't Meet My 30 Member Criteria"
            )
            return await ctx.send(view = embed_to_view(embed))

        prefix=ctx.prefix

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
            embed = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
                color=0x000000,
                description="Only Server Owner or Extra Owner can Run this Command!"
            )
            return await ctx.send(view = embed_to_view(embed))

        if not antinuke or not antinuke[0]:
            embed = discord.Embed(
                color=0x000000,
                description=(
                    f"**{ctx.guild.name} Security Settings {emojis.MOD}\n"
                    "Ohh No! looks like your server doesn't enabled Antinuke\n\n"
                    f"Current Status : {emojis.DISABLED1}\n\n"
                    f"To enable use `{prefix}antinuke enable` **"
                )
            )
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            return await ctx.send(view = embed_to_view(embed))

        if not member:
            embed = discord.Embed(
                color=0x000000,
                title="__**Whitelist Commands**__",
                description="**Adding a user to the whitelist means that no actions will be taken against them if they trigger the Anti-Nuke Module.**"
            )
            embed.add_field(name="__**Usage**__", value=f"{emojis.ICONARROWRIGHT} `{prefix}whitelist @user/id`\n{emojis.ICONARROWRIGHT} `{prefix}wl @user`")
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            return await ctx.send(view = embed_to_view(embed))

        async with self.db.execute(
            "SELECT * FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id)
        ) as cursor:
            data = await cursor.fetchone()

        if data:
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                color=0x000000,
                description=f"<@{member.id}> is already a whitelisted member, **Unwhitelist** the user and try again."
            )
            return await ctx.send(view = embed_to_view(embed))

        await self.db.execute(
            "INSERT INTO whitelisted_users (guild_id, user_id) VALUES (?, ?)",
            (ctx.guild.id, member.id)
        )
        await self.db.commit()

        options = [
            discord.SelectOption(label="Ban", description="Whitelist a member with ban permission", value="ban"),
            discord.SelectOption(label="Kick", description="Whitelist a member with kick permission", value="kick"),
            discord.SelectOption(label="Prune", description="Whitelist a member with prune permission", value="prune"),
            discord.SelectOption(label="Bot Add", description="Whitelist a member with bot add permission", value="botadd"),
            discord.SelectOption(label="Server Update", description="Whitelist a member with server update permission", value="serverup"),
            discord.SelectOption(label="Member Update", description="Whitelist a member with member update permission", value="memup"),
            discord.SelectOption(label="Channel Create", description="Whitelist a member with channel create permission", value="chcr"),
            discord.SelectOption(label="Channel Delete", description="Whitelist a member with channel delete permission", value="chdl"),
            discord.SelectOption(label="Channel Update", description="Whitelist a member with channel update permission", value="chup"),
            discord.SelectOption(label="Role Create", description="Whitelist a member with role create permission", value="rlcr"),
            discord.SelectOption(label="Role Update", description="Whitelist a member with role update permission", value="rlup"),
            discord.SelectOption(label="Role Delete", description="Whitelist a member with role delete permission", value="rldl"),
            discord.SelectOption(label="Mention Everyone", description="Whitelist a member with mention everyone permission", value="meneve"),
            discord.SelectOption(label="Manage Webhook", description="Whitelist a member with manage webhook permission", value="mngweb")
        ]

        select = discord.ui.Select(placeholder="Choose Your Options", min_values=1, max_values=len(options), options=options, custom_id="wl")
        button = discord.ui.Button(label="Add This User To All Categories", style=discord.ButtonStyle.primary, custom_id="catWl")

        view = discord.ui.View()
        view.add_item(select)
        view.add_item(button)

        embed = discord.Embed(
            title=ctx.guild.name,
            color=0x000000,
            description=(
                f"{emojis.CROSSICON}{emojis.TICK} : **Ban**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Kick**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Prune**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Bot Add**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Server Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Member Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Channel Create**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Channel Delete**\n"
                f"{emojis.CROSSICON}{emojis.TICK}: **Channel Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Role Create**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Role Delete**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Role Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Mention** @everyone\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Webhook Management**"
                
            )
        )
        embed.add_field(name="**Executor**", value=f"<@!{ctx.author.id}>", inline=True)
        embed.add_field(name="**Target**", value=f"<@!{member.id}>", inline=True)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text=f"Developed by REM ALL IN ONE BOT")

        msg = await ctx.send(view = embed_to_view(embed, view = view))

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
            if interaction.data["custom_id"] == "catWl":
                
                await self.db.execute(
                    "UPDATE whitelisted_users SET ban = ?, kick = ?, prune = ?, botadd = ?, serverup = ?, memup = ?, chcr = ?, chdl = ?, chup = ?, rlcr = ?, rldl = ?, rlup = ?, meneve = ?, mngweb = ?, mngstemo = ? WHERE guild_id = ? AND user_id = ?",
                    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, ctx.guild.id, member.id)
                )
                await self.db.commit()

                
                embed = discord.Embed(
                    title=ctx.guild.name,
                    color=0x000000,
                    description=(
                         f"{emojis.CROSSICON}{emojis.TICK} : **Ban**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Kick**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Prune**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Bot Add**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Server Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Member Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Channel Create**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Channel Delete**\n"
                f"{emojis.CROSSICON}{emojis.TICK}: **Channel Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Role Create**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Role Delete**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Role Update**\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Mention** @everyone\n"
                f"{emojis.CROSSICON}{emojis.TICK} : **Webhook Management**"
                    )
                )
                embed.add_field(name="**Executor**", value=f"<@!{ctx.author.id}>", inline=True)
                embed.add_field(name="**Target**", value=f"<@!{member.id}>", inline=True)
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embed.set_footer(text=f"Developed by REM ALL IN ONE BOT")

                await interaction.response.edit_message(view = embed_to_view(embed, view = None))
            else:
                
                fields = {
                    'ban': 'Ban',
                    'kick': 'Kick',
                    'prune': 'Prune',
                    'botadd': 'Bot Add',
                    'serverup': 'Server Update',
                    'memup': 'Member Update',
                    'chcr': 'Channel Create',
                    'chdl': 'Channel Delete',
                    'chup': 'Channel Update',
                    'rlcr': 'Role Create',
                    'rldl': 'Role Delete',
                    'rlup': 'Role Update',
                    'meneve': 'Mention Everyone',
                    'mngweb': 'Manage Webhooks'
                }

                
                embed_description = "\n".join(f"{emojis.CROSSICON}{emojis.TICK} : **{name}**" for key, name in fields.items())

                
                for value in interaction.data["values"]:
                    await self.db.execute(
                        f"UPDATE whitelisted_users SET {value} = ? WHERE guild_id = ? AND user_id = ?",
                        (True, ctx.guild.id, member.id)
                    )
                    embed_description = embed_description.replace(f"{emojis.CROSSICON}{emojis.TICK} : **{fields[value]}**", f"{emojis.CROSSICON}{emojis.TICK} : **{fields[value]}**")

                await self.db.commit()

                
                embed = discord.Embed(
                    title=ctx.guild.name,
                    color=0x000000,
                    description=embed_description
                )
                embed.add_field(name="**Executor**", value=f"<@!{ctx.author.id}>", inline=True)
                embed.add_field(name="**Target**", value=f"<@!{member.id}>", inline=True)
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embed.set_footer(text=f"Developed by REM ALL IN ONE BOT")

                await interaction.response.edit_message(view = embed_to_view(embed, view = None))
        except TimeoutError:
            await msg.edit(view=None)


    @commands.hybrid_command(name='whitelisted', aliases=['wlist'], help="Shows the list of whitelisted users.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def whitelisted(self, ctx):
        if ctx.guild.member_count < 2:
            embed = discord.Embed(
                color=0x000000,
                description=f"{emojis.CROSSICON} | Your Server Doesn't Meet My 30 Member Criteria"
            )
            return await ctx.send(view = embed_to_view(embed))

        pre=ctx.prefix

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
            embed = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
                color=0x000000,
                description="Only Server Owner or Extra Owner can Run this Command!"
            )
            return await ctx.send(view = embed_to_view(embed))

        if not antinuke or not antinuke[0]:
            embed = discord.Embed(
                color=0x000000,
                description=(
                    f"**{ctx.guild.name} security settings {emojis.MOD}\n"
                    "Ohh NO! looks like your server doesn't enabled security\n\n"
                    f"Current Status : {emojis.DISABLED1}\n\n"
                    f"To enable use `{pre}antinuke enable` **"
                )
            )
            return await ctx.send(view = embed_to_view(embed))


        async with self.db.execute(
            "SELECT user_id FROM whitelisted_users WHERE guild_id = ?",
            (ctx.guild.id,)
        ) as cursor:
            data = await cursor.fetchall()

        if not data:
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                color=0x000000,
                description="No whitelisted users found."
            )
            return await ctx.send(view = embed_to_view(embed))

        whitelisted_users = [self.bot.get_user(user_id[0]) for user_id in data]
        whitelisted_users_str = ", ".join(f"<@!{user.id}>" for user in whitelisted_users if user)

        embed = discord.Embed(
            color=0x000000,
            title=f"__Whitelisted Users for {ctx.guild.name}__",
            description=whitelisted_users_str
        )
        await ctx.send(view = embed_to_view(embed))


    @commands.hybrid_command(name="whitelistreset", aliases=['wlreset'], help="Resets the whitelisted users.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def whitelistreset(self, ctx):
        if ctx.guild.member_count < 2:
            embed = discord.Embed(
                color=0x000000,
                description=f"{emojis.CROSSICON} | Your Server Doesn't Meet My 30 Member Criteria"
            )
            return await ctx.send(view = embed_to_view(embed))

        pre=ctx.prefix

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
            embed = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
                color=0x000000,
                description="Only Server Owner or Extra Owner can Run this Command!"
            )
            return await ctx.send(view = embed_to_view(embed))

        if not antinuke or not antinuke[0]:
            embed = discord.Embed(
                color=0x000000,
                description=(
                    f"**{ctx.guild.name} Security Settings {emojis.MOD}\n"
                    "Ohh NO! looks like your server doesn't enabled security\n\n"
                    f"Current Status : {emojis.DISABLED1}\n\n"
                    f"To enable use `{pre}antinuke enable` **"
                )
            )
            return await ctx.send(view = embed_to_view(embed))

        async with self.db.execute(
            "SELECT user_id FROM whitelisted_users WHERE guild_id = ?",
            (ctx.guild.id,)
        ) as cursor:
            data = await cursor.fetchall()


        if not data:
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error",
                color=0x000000,
                description="No whitelisted users found."
            )
            return await ctx.send(view = embed_to_view(embed))

        await self.db.execute("DELETE FROM whitelisted_users WHERE guild_id = ?", (ctx.guild.id,))
        await self.db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success",
            color=0x000000,
            description=f"Removed all whitelisted members from {ctx.guild.name}"
        )
        await ctx.send(view = embed_to_view(embed))

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""