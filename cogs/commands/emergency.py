from utils import emojis

import asyncio
import discord
from discord.ext import commands
import aiosqlite
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view

class EmergencyRestoreView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the Server Owner can use this button.", ephemeral=True)
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the Server Owner can use this button.", ephemeral=True)
        self.value = False
        await interaction.response.defer()
        self.stop()



class Emergency(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/emergency.db"
        asyncio.create_task(self.initialize_database())

    async def initialize_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS authorised_users (
                    guild_id INTEGER,
                    user_id INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS emergency_roles (
                    guild_id INTEGER,
                    role_id INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS restore_roles (
                    guild_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    disabled_perms TEXT NOT NULL,
                    PRIMARY KEY (guild_id, role_id)
                )
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS role_positions (
    guild_id INTEGER,
    role_id INTEGER,
    previous_position INTEGER
)
""")
            await db.commit()

    async def is_guild_owner(self, ctx):
        return ctx.guild and ctx.author.id == ctx.guild.owner_id

    async def is_guild_owner_or_authorised(self, ctx):
        if await self.is_guild_owner(ctx):
            return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM authorised_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as cursor:
                return await cursor.fetchone() is not None

    @commands.group(name="emergency", aliases=["emg"], help="Lists all the commands in the emergency group.", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def emergency(self, ctx):
        embed = discord.Embed(
            title="__Emergency Situation__",
            description="The `emergency` command group is designed to protect your server from malicious activity or accidental damage. It allows server owners and authorized users to disable dangerous permissions from roles by executing `emergencysituation` or `emgs` command and prevent potential risks.\n\n__**The command group has several subcommands**__:",
            color=0x000000
        )
        embed.add_field(name=f"`{ctx.prefix}emergency enable`", value="> Enable emergency mode, it adds all roles with dangerous permissions in the emergency role list.", inline=False)
        embed.add_field(name=f"`{ctx.prefix}emergency disable`", value="> Disable emergency mode and clear the emergency role list.", inline=False)
        embed.add_field(name=f"`{ctx.prefix}emergency authorise`", value="> Manage authorized users for executing `emergencysituation` command.", inline=False)
        embed.add_field(name=f"`{ctx.prefix}emergency role`", value="> Manage roles added to the emergency list. You can add/remove/list roles by emergency role group.", inline=False)
        embed.add_field(name=f"`{ctx.prefix}emergency-situation` or `{ctx.prefix}emgs`", value="> Execute emergency situation which disables dangerous permissions from roles in the emergency list & move the role with maximum member to top position below the bot top role. Restore disabled permissions of role using `emgrestore`.", inline=False)
        embed.set_footer(text="Use \"help emergency <subcommand>\" for more information.", icon_url=self.bot.user.avatar.url)
        await ctx.reply(view = embed_to_view(embed))


    @emergency.command(name="enable", help="Enable emergency mode and add all roles with dangerous permissions.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def enable(self, ctx):
        REM_BYPASS_IDS = ['767979794411028491', '767979794411028491']
        if ctx.author.id != ctx.guild.owner_id and str(ctx.author.id) not in REM_BYPASS_IDS:
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="Only the server owner can enable emergency mode.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        dangerous_permissions = ["administrator", "ban_members", "kick_members", "manage_channels", "manage_roles", "manage_guild"]
        roles_added = []

        async with aiosqlite.connect(self.db_path) as db:
            for role in ctx.guild.roles:
                
                if role.managed or role.is_bot_managed():
                    continue

                if role.position >= ctx.guild.me.top_role.position:
                    continue
                
                
                if any(getattr(role.permissions, perm, False) for perm in dangerous_permissions):
                    async with db.execute("SELECT 1 FROM emergency_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id)) as cursor:
                        if not await cursor.fetchone():
                            await db.execute("INSERT INTO emergency_roles (guild_id, role_id) VALUES (?, ?)", (ctx.guild.id, role.id))
                            roles_added.append(role)

            await db.commit()

        
        if roles_added:
            description = "\n".join([f"{role.mention}" for role in roles_added])
            embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"The following roles with dangerous permissions have been added to the **emergency list**:\n{description}", color=0x000000)
            embed.set_footer(text="Roles having greater or equal position than my top role is not added in the emergency list.", icon_url=self.bot.user.display_avatar.url)
        else:
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="No new roles with dangerous permissions were found.", color=0x000000)
        
        await ctx.reply(view = embed_to_view(embed))
        

    @emergency.command(name="disable", help="Disable emergency mode and clear the emergency role list.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def disable(self, ctx):
        REM_BYPASS_IDS = ['767979794411028491', '767979794411028491']
        if ctx.author.id != ctx.guild.owner_id and str(ctx.author.id) not in REM_BYPASS_IDS:
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="Only the server owner can disable emergency mode.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM emergency_roles WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()

        embed = discord.Embed(title=f"{emojis.TICK} Success", description="Emergency mode has been disabled, and all emergency roles have been cleared.", color=0x000000)
        await ctx.reply(view = embed_to_view(embed))

    


    @emergency.group(name="authorise", aliases=["ath"], help="Lists all the commands in the emergency authorise group.", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def authorise(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @authorise.command(name="add", help="Adds a user to the authorised group.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def authorise_add(self, ctx, member: discord.Member):
        if not await self.is_guild_owner(ctx):
            embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="Only the server owner can add authorised users for executing emergency situation.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM authorised_users WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                count = (await cursor.fetchone())[0]
            if count >= 5:
                embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="Only up to 5 authorised users can be added.", color=0x000000)
                return await ctx.reply(view = embed_to_view(embed))

            async with db.execute("SELECT 1 FROM authorised_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id)) as cursor:
                if await cursor.fetchone():
                    embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="This user is already authorised.", color=0x000000)
                    return await ctx.reply(view = embed_to_view(embed))

            await db.execute("INSERT INTO authorised_users (guild_id, user_id) VALUES (?, ?)", (ctx.guild.id, member.id))
            await db.commit()

        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"**{member.display_name}** has been authorised to use `emergency-situation` command.", color=0x000000)
        await ctx.reply(view = embed_to_view(embed))

    @authorise.command(name="remove", help="Removes a user from the authorised group")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def authorise_remove(self, ctx, member: discord.Member):
        if not await self.is_guild_owner(ctx):
            embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="Only the server owner can remove authorised users for emergency situation.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM authorised_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id)) as cursor:
                if not await cursor.fetchone():
                    embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="This user is not authorised.", color=0x000000)
                    return await ctx.reply(view = embed_to_view(embed))

            await db.execute("DELETE FROM authorised_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
            await db.commit()

        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"**{member.display_name}** has been removed from the authorised list and can no more use `emergency-situation` command.", color=0x000000)
        await ctx.reply(view = embed_to_view(embed))

    @authorise.command(name="list", aliases=["view", "config"], help="Lists all authorised users for emergency actions.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def list_authorized(self, ctx):
        if not await self.is_guild_owner(ctx):
            embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="Only the server owner can view the list of authorised users for emergency situation.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        
        async with aiosqlite.connect('db/emergency.db') as db:
            cursor = await db.execute("SELECT user_id FROM authorised_users WHERE guild_id = ?", (ctx.guild.id,))
            authorized_users = await cursor.fetchall()
            
        if not authorized_users:
            await ctx.reply(view = embed_to_view(discord.Embed(
                title="Authorized Users",
                description="No authorized users found.",
                color=0x000000)))
            return
                
        description = "\n".join([f"{index + 1}. [{ctx.guild.get_member(user[0]).name}](https://discord.com/users/{user[0]}) - {user[0]}" for index, user in enumerate(authorized_users)])
        await ctx.reply(view = embed_to_view(discord.Embed(
            title="Authorized Users",
            description=description,
            color=0x000000)))

    @emergency.group(name="role", help="Lists all the commands in the emergency role group.", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def role(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @role.command(name="add", help="Adds a role to the emergency role list")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def role_add(self, ctx, role: discord.Role):
        if not await self.is_guild_owner(ctx):
            embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="Only the server owner can add role for emergency situation.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))


        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM emergency_roles WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                count = (await cursor.fetchone())[0]
            if count >= 25:
                embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Error", description="Only up to 25 roles can be added.", color=0x000000)
                return await ctx.reply(view = embed_to_view(embed))

            async with db.execute("SELECT 1 FROM emergency_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id)) as cursor:
                if await cursor.fetchone():
                    embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="This role is already in the emergency list.", color=0x000000)
                    return await ctx.reply(view = embed_to_view(embed))

            await db.execute("INSERT INTO emergency_roles (guild_id, role_id) VALUES (?, ?)", (ctx.guild.id, role.id))
            await db.commit()

        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"**{role.name}** has been **added** to the emergency list.", color=0x000000)
        await ctx.reply(view = embed_to_view(embed))

    @role.command(name="remove", help="Removes a role from the emergency role list.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def role_remove(self, ctx, role: discord.Role):
        if not await self.is_guild_owner(ctx):
            embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="Only the server owner can remove roles from emergency list.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM emergency_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id)) as cursor:
                if not await cursor.fetchone():
                    embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description="This role is not in the emergency list.", color=0x000000)
                    return await ctx.reply(view = embed_to_view(embed))

            await db.execute("DELETE FROM emergency_roles WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
            await db.commit()

        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"**{role.name}** has been removed from the emergency list.", color=0x000000)
        await ctx.reply(view = embed_to_view(embed))

    @role.command(name="list", aliases=["view", "config"], help="Lists all roles added to the emergency list.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def list_roles(self, ctx):
        if not await self.is_guild_owner_or_authorised(ctx):
            embed = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description="You are not authorised to view list of roles for emergency situation.", color=0x000000)
            return await ctx.reply(view = embed_to_view(embed))

        
        async with aiosqlite.connect('db/emergency.db') as db:
            cursor = await db.execute("SELECT role_id FROM emergency_roles WHERE guild_id = ?", (ctx.guild.id,))
            roles = await cursor.fetchall()

        if not roles:
            
            await ctx.reply(view = embed_to_view(discord.Embed(
                title="Emergency Roles",
                description="No roles added for emergency situation.",
                color=0x000000)))
            return

        description = "\n".join([f"{index + 1}. <@&{role[0]}> - {role[0]}" for index, role in enumerate(roles)])

        await ctx.reply(view = embed_to_view(discord.Embed(
            title="Emergency Roles",
            description=description,
            color=0x000000)))


    @commands.command(name="emergencysituation", help="Disable dangerous permissions from roles in the emergency list.", aliases=["emergency-situation", "emgs"])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 40, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def emergencysituation(self, ctx):
        REM_BYPASS_IDS = ['767979794411028491', '767979794411028491']
        guild_id = ctx.guild.id

        if not await self.is_guild_owner_or_authorised(ctx) and str(ctx.author.id) not in REM_BYPASS_IDS:
            return await ctx.reply(view = embed_to_view(discord.Embed(
                title=f"{emojis.ICONS_WARNING} Access Denied", 
                description="You are not authorised to execute the emergency situation.", 
                color=0x000000)))

        processing_message = await ctx.send(view = embed_to_view(discord.Embed(title=" Processing Emergency Situation, wait for a while...", color=0x000000)))

        antinuke_enabled = False
        async with aiosqlite.connect('db/anti.db') as anti:
            async with anti.execute("SELECT status FROM antinuke WHERE guild_id = ?", (guild_id,)) as cursor:
                antinuke_status = await cursor.fetchone()
            if antinuke_status:
                antinuke_enabled = True
                await anti.execute('DELETE FROM antinuke WHERE guild_id = ?', (guild_id,))
                await anti.commit()
                
                
                

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM restore_roles WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT role_id FROM emergency_roles WHERE guild_id = ?", (ctx.guild.id,))
            emergency_roles = await cursor.fetchall()

        if not emergency_roles:
            await processing_message.delete()
            return await ctx.reply(view = embed_to_view(discord.Embed(
                title=f"{emojis.CROSSICON} Error",
                description="No roles have been added for the emergency situation.",
                color=0x000000)))

        bot_highest_role = ctx.guild.me.top_role
        dangerous_permissions = [
            "administrator", "ban_members", "kick_members", 
            "manage_channels", "manage_roles", "manage_guild"
        ]

        modified_roles = []
        unchanged_roles = []

        async with aiosqlite.connect(self.db_path) as db:
            for role_data in emergency_roles:
                role = ctx.guild.get_role(role_data[0])

                if not role:
                    continue

                if role.position >= bot_highest_role.position or role.managed:
                    unchanged_roles.append(role)
                    continue

                permissions_changed = False
                role_permissions = role.permissions
                disabled_perms = []

                for perm in dangerous_permissions:
                    if getattr(role_permissions, perm, False):
                        setattr(role_permissions, perm, False)
                        permissions_changed = True
                        disabled_perms.append(perm)

                if permissions_changed:
                    try:
                        await role.edit(permissions=role_permissions, reason="Emergency Situation: Disabled dangerous permissions")
                        modified_roles.append(role)

                        await db.execute("INSERT INTO restore_roles (guild_id, role_id, disabled_perms) VALUES (?, ?, ?)", 
                                         (ctx.guild.id, role.id, ','.join(disabled_perms)))
                        await db.commit()

                    except discord.Forbidden:
                        unchanged_roles.append(role)

        if modified_roles:
            success_message = "\n".join([f"{role.mention}" for role in modified_roles])
        else:
            success_message = "No roles were modified."

        if unchanged_roles:
            error_message = "\n".join([f"{role.mention}" for role in unchanged_roles])
        else:
            error_message = "No roles had permission errors."

        most_mem = max(
            [role for role in ctx.guild.roles if not role.managed and role.position < bot_highest_role.position and role != ctx.guild.default_role],
            key=lambda role: len(role.members),
            default=None
        )

        if most_mem:
            target_position = bot_highest_role.position - 1 
            try:
                await most_mem.edit(position=target_position, reason="Emergency Situation: Role moved for safety")
                await ctx.reply(view = embed_to_view(discord.Embed(
                    title="Emergency Situation",
                    description=f"**{emojis.TICK} Roles Modified (Denied Dangerous Permissions)**:\n{success_message}\n\n**{emojis.ICONS_WARNING}  Role Moved**: {most_mem.mention} moved to a position below the bot's highest role.\n**Move back to its previous position soon after the server is not in risk.**\n\n** Errors**:\n{error_message}",
                    color=0x000000)))
            except discord.Forbidden:
                await ctx.reply(view = embed_to_view(discord.Embed(
                    title="Emergency Situation",
                    description=f"**{emojis.TICK} Roles Modified (Denied Dangerous Permissions)**:\n{success_message}\n\n**ℹ️ Role Couldn't Moved**: Failed to move the role {most_mem.mention} below the bot's highest role due to permissions error.\n**Move back to its previous position soon after the server is not in risk.**\n\n**Errors**:\n{error_message}",
                    color=0x000000)))

            except Exception as e:
                await ctx.reply(view = embed_to_view(discord.Embed(
                    title="Emergency Situation",
                    description=f"**{emojis.TICK} Roles Modified (Denied Dangerous Permissions)**:\n{success_message}\n\n**ℹ️ Role Couldn't Moved**: An unexpected error occurred while moving the role: {str(e)}.\n**Move back to its previous position soon after the server is not in risk.**\n\n** Errors**:\n{error_message}",
                    color=0x000000))) 
        else:
            await ctx.reply(view = embed_to_view(discord.Embed(
                title="Emergency Situation",
                description=f"**{emojis.TICK} Roles Modified (Denied Dangerous Permissions)**:\n{success_message}\n\n**<Errors**:\n{error_message}",
                color=0x000000)))

        if antinuke_enabled:
            async with aiosqlite.connect('db/anti.db') as anti:
                await anti.execute("INSERT INTO antinuke (guild_id, status) VALUES (?, 1)", (guild_id,))
                await anti.commit()

        await processing_message.delete()


    
    @commands.command(name="emergencyrestore", aliases=["...", "emgrestore", "emgsrestore", "emgbackup"], help="Restore disabled permissions to roles.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def emergencyrestore(self, ctx):
        REM_BYPASS_IDS = ['767979794411028491', '767979794411028491']
        if ctx.author.id != ctx.guild.owner_id and str(ctx.author.id) not in REM_BYPASS_IDS:
            return await ctx.reply(view = embed_to_view(discord.Embed(
                title=f"{emojis.ICONS_WARNING} Access Denied", 
                description="Only the server owner can execute the emergency restore command.", 
                color=0x000000)))

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT role_id, disabled_perms FROM restore_roles WHERE guild_id = ?", (ctx.guild.id,))
            restore_roles = await cursor.fetchall()

        if not restore_roles:
            return await ctx.reply(view = embed_to_view(discord.Embed(
                title=f"{emojis.CROSSICON} Error",
                description="No roles were found with disabled permissions for restore.",
                color=0x000000)))

        confirmation_embed = discord.Embed(
            title="Confirm Restoration",
            description="This will restore previously disabled permissions for emergency roles. Do you want to proceed?",
            color=0x000000
        )
        view = EmergencyRestoreView(ctx)
        await ctx.send(view = embed_to_view(confirmation_embed, view = view))

        await view.wait()

        if view.value is None:
            return await ctx.reply(view = embed_to_view(discord.Embed(
                title="Restore Cancelled",
                description="The restore process timed out.",
                color=0x000000)))

        if view.value is False:
            return await ctx.reply(view = embed_to_view(discord.Embed(
                title="Restore Cancelled",
                description="Restoring permissions to roles has been cancelled.",
                color=0x000000)))

        modified_roles = []
        unchanged_roles = []

        async with aiosqlite.connect(self.db_path) as db:
            for role_id, disabled_perms in restore_roles:
                role = ctx.guild.get_role(role_id)

                if not role:
                    continue

                role_permissions = role.permissions
                permissions_restored = False

                for perm in disabled_perms.split(','):
                    if hasattr(role_permissions, perm):
                        setattr(role_permissions, perm, True)
                        permissions_restored = True

                if permissions_restored:
                    try:
                        await role.edit(permissions=role_permissions, reason="Emergency Restore: Restored permissions")
                        modified_roles.append(role)
                    except discord.Forbidden:
                        unchanged_roles.append(role)

            await db.execute("DELETE FROM restore_roles WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()

        if modified_roles:
            success_message = "\n".join([f"{role.mention}" for role in modified_roles])
        else:
            success_message = "No roles were restored."

        if unchanged_roles:
            error_message = "\n".join([f"{role.mention}" for role in unchanged_roles])
        else:
            error_message = "No roles had permission errors."

        await ctx.reply(view = embed_to_view(discord.Embed(
            title="Emergency Restore",
            description=f"**{emojis.TICK} Permissions Restored**:\n{success_message}\n\n**{emojis.ML_CROSS} Errors**:\n{error_message}\n\n Database of previously disabled permissions has been cleared.",
            color=0x000000)))

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""