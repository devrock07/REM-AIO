from utils import emojis

import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import re
from typing import *
from utils.Tools import *
from discord.ui import Button, View
from typing import Union, Optional
from typing import Union, Optional
from io import BytesIO
import requests
import aiohttp
import time
from datetime import datetime, timezone, timedelta
from utils.cv2_compat import embed_to_view, embeds_to_view


time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


def convert(argument):
  args = argument.lower()
  matches = re.findall(time_regex, args)
  time = 0
  for key, value in matches:
    try:
      time += time_dict[value] * float(key)
    except KeyError:
      raise commands.BadArgument(
        f"{value} is an invalid time key! h|m|s|d are valid arguments")
    except ValueError:
      raise commands.BadArgument(f"{key} is not a number!")
  return round(time)


class Role(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.color = 0x000000


  @commands.group(name="role",invoke_without_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @top_check()
  @blacklist_check()
  async def role(self, ctx, member: discord.Member, *, role: discord.Role):
    if not ctx.guild.me.guild_permissions.manage_roles:
        return await ctx.send(f"{emojis.ICONS_WARNING} I don't have permission to manage roles!")

    if role >= ctx.guild.me.top_role:
        error = discord.Embed(
            color=self.color,
            description="I can't manage roles for a user with a higher or equal role!"
        )

        error.set_author(name="Error")
        error.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(error))

    if ctx.author != ctx.guild.owner and ctx.author.top_role <= member.top_role:
        error = discord.Embed(
            color=self.color,
            description="You can't manage roles for a user with a higher or equal role than yours!"
        )
        error.set_author(name="Access Denied")
        error.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(error))

    try:
        if role not in member.roles:
            await member.add_roles(role, reason=f"Role added by {ctx.author} (ID: {ctx.author.id})")
            success = discord.Embed(
                color=self.color,
                description=f"Successfully **added** role {role.name} to {member.mention}."
            )
            success.set_author(name="Role Added")
            success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        else:
            await member.remove_roles(role, reason=f"Role removed by {ctx.author} (ID: {ctx.author.id})")
            success = discord.Embed(
                color=self.color,
                description=f"Successfully **removed** role {role.name} from {member.mention}."
            )
            success.set_author(name="Role Removed")
            success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(success))
    except discord.Forbidden:
        error = discord.Embed(
            color=self.color,
            description=f"{emojis.ICONS_WARNING} I don't have permission to manage roles for this user!"
        )
        await ctx.send(view = embed_to_view(error))
    except Exception as e:
        error = discord.Embed(
            color=self.color,
            description=f"{emojis.ICONS_WARNING} An unexpected error occurred: {str(e)}"
        )
        await ctx.send(view = embed_to_view(error))


  @role.command(help="Give role to member for particular time")
  @commands.bot_has_permissions(manage_roles=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 7, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  @commands.bot_has_permissions(manage_roles=True)
  async def temp(self, ctx, role: discord.Role, time, *, user: discord.Member):
    if ctx.author != ctx.guild.owner and role.position >= ctx.author.top_role.position:
        embed = discord.Embed(
              description=f"You can't manage a role that is higher or equal to your top role!",
              color=self.color
          )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed))
          
    else:
      if role.position >= ctx.guild.me.top_role.position:
        embed1 = discord.Embed(
          description=
          f"{role} is higher than my top role, move my role above {role}.",
          color=self.color)
        embed1.set_author(name="Error")
        embed1.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed1))
    seconds = convert(time)
    await user.add_roles(role, reason=None)
    success = discord.Embed(
      description=
      f"Successfully added {role.mention} to {user.mention} .",
      color=self.color)
    success.set_author(name="Success")
    success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(view = embed_to_view(success))
    await asyncio.sleep(seconds)
    await user.remove_roles(role)

  
  @role.command(help="Delete a role in the guild")
  @blacklist_check()
  @ignore_check()
  @top_check()
  @commands.cooldown(1, 7, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  @commands.bot_has_permissions(manage_roles=True)
  async def delete(self, ctx, *, role: discord.Role):
    if ctx.author != ctx.guild.owner and role.position >= ctx.author.top_role.position:
        embed = discord.Embed(
            description=f"You cannot delete a role that is higher or equal to your top role!",
            color=self.color
        )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed))

    if role.position >= ctx.guild.me.top_role.position:
        embed = discord.Embed(
            description=f"I cannot delete {role} because it is higher than my top role. Please move my role above {role}.",
            color=self.color
        )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed))

    if role is None:
        embed = discord.Embed(
            description=f"No role named {role} found in this server.",
            color=self.color
        )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed))

    await role.delete()
    
    embed = discord.Embed(
        description=f"Successfully deleted {role}.",
        color=self.color
    )
    embed.set_author(name="Success")
    embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(view = embed_to_view(embed))
      
  @role.command(help="Create a role in the guild")
  @blacklist_check()
  @ignore_check()
  @top_check()
  @commands.cooldown(1, 7, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  @commands.bot_has_permissions(manage_roles=True)
  async def create(self, ctx, *, name):
    embed = discord.Embed(
        description=f"Successfully created a role named {name}.",
        color=self.color
    )
    embed.set_author(name="Success")
    embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.guild.create_role(name=name, color=discord.Color.default())
    await ctx.send(view = embed_to_view(embed))


  @role.command(help="Renames a role in the server.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  @commands.bot_has_permissions(manage_roles=True)
  async def rename(self, ctx, role: discord.Role, *, newname):
    
    if role.position >= ctx.author.top_role.position:
        embed = discord.Embed(
            description=f"You can't manage the role {role.mention} because it is higher or equal to your top role.",
            color=self.color
        )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed))

    
    if role.position >= ctx.guild.me.top_role.position:
        embed = discord.Embed(
            description=f"I can't manage the role {role.mention} because it is higher than my top role.",
            color=self.color
        )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(view = embed_to_view(embed))

    await role.edit(name=newname)
    embed = discord.Embed(
        description=f"Role {role.name} has been renamed to {newname}.",
        color=self.color
    )
    embed.set_author(name="Success")
    embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(view = embed_to_view(embed))                  

  @role.command(name="humans", help="Gives role to all humans in the guild")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 15, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def role_humans(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Assigning {role.mention} to all humans...")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))
                    for member in interaction.guild.members:
                        if not member.bot and role not in member.roles:
                            try:
                                await member.add_roles(role, reason=f"Role Humans Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK} | Successfully assigned {role.mention} to {count} human(s).")
                else:
                    await interaction.response.edit_message(
                        content=f"{emojis.ICONS_WARNING} I am missing the required permissions. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. No humans will be assigned the role {role.mention}.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        members_without_role = [member for member in ctx.guild.members if not member.bot and role not in member.roles]
        if len(members_without_role) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"{emojis.ICONS_WARNING} | All humans already have the {role.mention} role.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f"Are you sure you want to assign {role.mention} to {len(members_without_role)} members?")
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)

    else:
        denied = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)



  @role.command(name="bots", help="Gives role to all the bots in the guild")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def role_bots(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Adding {role.mention} to all bots...")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))
                    for member in interaction.guild.members:
                        if member.bot and role not in member.roles:
                            try:
                                await member.add_roles(role, reason=f"Role Bots Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK} | Successfully added {role.mention} to {count} bot(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. No bots will be assigned the role {role.mention}.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        bots_without_role = [member for member in ctx.guild.members if member.bot and role not in member.roles]
        if len(bots_without_role) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"{emojis.ICONS_WARNING} | All bots already have the {role.mention} role.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f"**Are you sure you want to give {role.mention} to {len(bots_without_role)} bots?**")
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)

    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)



  @role.command(name="unverified", help="Gives role to all the unverified members in the guild")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def role_unverified(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Adding {role.mention} to all unverified members.")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))
                    for member in interaction.guild.members:
                        if member.avatar is None and role not in member.roles:
                            try:
                                await member.add_roles(role, reason=f"Role Unverified Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK} | Successfully added {role.mention} to {count} unverified member(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. No unverified members will be assigned the role {role.mention}.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        embed = discord.Embed(
            color=self.color,
            description=f'**Are you sure you want to give {role.mention} to all unverified members in this guild?**')
        view = View()
        button.callback = button_callback
        button1.callback = button1_callback
        view.add_item(button)
        view.add_item(button1)
        await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)

    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)


  @role.command(name="all", help="Gives role to all the members in the guild")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 15, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def role_all(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Adding {role.mention} to all members.")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))
                    for member in interaction.guild.members:
                        try:
                            await member.add_roles(role, reason=f"Role All Command Executed By: {ctx.author}")
                            count += 1
                        except Exception as e:
                            print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK} | Successfully added {role.mention} to {count} member(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. No members will be assigned the role {role.mention}.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        members_without_role = [member for member in ctx.guild.members if role not in member.roles]
        if len(members_without_role) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"{emojis.ICONS_WARNING} | {role.mention} is already given to all the members of the server.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f'**Are you sure you want to give {role.mention} to {len(members_without_role)} members?**')
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)
    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)



  @commands.group(name="removerole",invoke_without_command=True,
                 aliases=['rrole'],
                   help="remove a role from all members .")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @blacklist_check()
  @commands.has_permissions(administrator=True)
  async def rrole(self,ctx):
    if ctx.subcommand_passed is None:
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)


  @rrole.command(name="humans", help="Removes a role from all the humans in the server.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  async def rrole_humans(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Removing {role.mention} from all humans.")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))
                    for member in interaction.guild.members:
                        if not member.bot and role in member.roles:
                            try:
                                await member.remove_roles(role, reason=f"Remove Role Humans Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK}| Successfully removed {role.mention} from {count} human(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. {role.mention} will not be removed from any humans.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        humans_with_role = [member for member in ctx.guild.members if not member.bot and role in member.roles]
        if len(humans_with_role) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"| Already no humans have {role.mention}.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f'**Are you sure you want to remove {role.mention} from {len(humans_with_role)} humans in this guild?**')
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)
    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)

        await ctx.send(view = embed_to_view(embed), mention_author=False)
        


  @rrole.command(name="bots", help="Removes a role from all the bots in the server.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  async def rrole_bots(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Removing {role.mention} from all bots...")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))
                    for member in interaction.guild.members:
                        if member.bot and role in member.roles:
                            try:
                                await member.remove_roles(role, reason=f"Remove Role Bots Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK} | Successfully removed {role.mention} from {count} bot(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. {role.mention} will not be removed from any bots.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        bots_with_role = [member for member in ctx.guild.members if member.bot and role in member.roles]
        if len(bots_with_role) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"| Already no bots have {role.mention}.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f'**Are you sure you want to remove {role.mention} from {len(bots_with_role)} bots in this guild?**')
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)
    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)

    



  @rrole.command(name="all", help="Removes a role from all members in the server.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  async def rrole_all(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            removed_count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Removing {role.mention} from all members.")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))

                    for member in interaction.guild.members:
                        if role in member.roles:
                            try:
                                await member.remove_roles(role, reason=f"Remove Role All Command Executed By: {ctx.author}")
                                removed_count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK}| Successfully removed {role.mention} from {removed_count} member(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message("This action is not for you!",
                                                        ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. {role.mention} will not be removed from anyone.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message("This action is not for you!",
                                                        ephemeral=True)

        members_with_role = [member for member in ctx.guild.members if role in member.roles]
        if len(members_with_role) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"| No members currently have {role.mention}.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f'**Are you sure you want to remove {role.mention} from {len(members_with_role)} members in this guild?**')
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)
    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)

    
    

  @rrole.command(name="unverified", help="Removes a role from all the unverified members in the server.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  async def rrole_unverified(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Yes",
                        style=discord.ButtonStyle.green,
                        emoji=f"{emojis.TICK}")
        button1 = Button(label="No",
                         style=discord.ButtonStyle.red,
                         emoji=f"{emojis.CROSSICON}")

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Removing {role.mention} from all unverified members.")
                    await interaction.response.edit_message(view = embed_to_view(embed1, view = None))

                    for member in interaction.guild.members:
                        if member.avatar is None and role in member.roles:
                            try:
                                await member.remove_roles(role, reason=f"Remove Role Unverified Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{emojis.TICK} | Successfully removed {role.mention} from {count} unverified member(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        )
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. {role.mention} will not be removed from any unverified members.")
                await interaction.response.edit_message(view = embed_to_view(embed2, view = None))
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    ephemeral=True)

        unverified_members = [member for member in ctx.guild.members if member.avatar is None and role in member.roles]
        if len(unverified_members) == 0:
            return await ctx.reply(view = embed_to_view(discord.Embed(description=f"| Already no unverified members have {role.mention}.", color=self.color)))
        else:
            embed = discord.Embed(
                color=self.color,
                description=f'**Are you sure you want to remove {role.mention} from {len(unverified_members)} unverified members in this guild?**')
            view = View()
            button.callback = button_callback
            button1.callback = button1_callback
            view.add_item(button)
            view.add_item(button1)
            await ctx.reply(view = embed_to_view(embed, view = view), mention_author=False)
    else:
        denied = discord.Embed(title=f"{emojis.CROSSICON} Access Denied",
            description="Your role should be above my top role.",
            color=0x000000)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(denied), mention_author=False)

  

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""