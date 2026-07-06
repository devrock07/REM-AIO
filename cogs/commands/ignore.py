from __future__ import annotations
from utils import emojis

import asyncio
import discord
from discord.ext import commands
from core import *
from utils.Tools import *
from typing import Optional
import aiosqlite
from utils.cv2_compat import embed_to_view, embeds_to_view

class Ignore(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.db_path = "db/ignore.db"
    self.color = 0x000000
    asyncio.create_task(self.initialize_db())

  async def initialize_db(self):
    async with aiosqlite.connect(self.db_path) as db:
      await db.execute("CREATE TABLE IF NOT EXISTS ignored_commands (guild_id INTEGER, command_name TEXT)")
      await db.execute("CREATE TABLE IF NOT EXISTS ignored_channels (guild_id INTEGER, channel_id INTEGER)")
      await db.execute("CREATE TABLE IF NOT EXISTS ignored_users (guild_id INTEGER, user_id INTEGER)")
      await db.execute("CREATE TABLE IF NOT EXISTS bypassed_users (guild_id INTEGER, user_id INTEGER)")
      await db.commit()

  @commands.group(name="ignore", help="Manage ignored commands, channels, users, and bypassed users.", invoke_without_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def _ignore(self, ctx):
    if ctx.subcommand_passed is None:
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)

  @_ignore.group(name="command", help="Manage ignored commands in this guild.", invoke_without_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def _command(self, ctx):
      if ctx.subcommand_passed is None:
          await ctx.send_help(ctx.command)
          ctx.command.reset_cooldown(ctx)

  @_command.command(name="add", help="Adds a command to the ignore list.")
  @commands.has_permissions(administrator=True)
  @blacklist_check()
  async def command_add(self, ctx: commands.Context, command_name: str):
      command_name_normalized = command_name.strip().lower()
      command = self.bot.get_command(command_name_normalized)
      if not command:
          embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"`{command_name}` is not a valid command.", color=self.color)
          await ctx.reply(view = embed_to_view(embed), mention_author=False)
          return
      async with aiosqlite.connect(self.db_path) as db:
          cursor = await db.execute("SELECT COUNT(*) FROM ignored_commands WHERE guild_id = ?", (ctx.guild.id,))
          count = await cursor.fetchone()
          if count[0] >= 25:
              embed = discord.Embed(description="You can only add up to 25 commands to the ignore list.", color=self.color)
              await ctx.reply(view = embed_to_view(embed))
              return
          cursor = await db.execute("SELECT command_name FROM ignored_commands WHERE guild_id = ? AND command_name = ?", (ctx.guild.id, command_name_normalized))
          result = await cursor.fetchone()
          if result:
              embed = discord.Embed(description=f"`{command_name}` is already in the ignore commands list.", color=self.color)
              await ctx.reply(view = embed_to_view(embed), mention_author=False)
          else:
              await db.execute("INSERT INTO ignored_commands (guild_id, command_name) VALUES (?, ?)", (ctx.guild.id, command_name_normalized))
              await db.commit()
              embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully added `{command_name}` to the ignore commands list.", color=self.color)
              await ctx.reply(view = embed_to_view(embed))

  @_command.command(name="remove", help="Removes a command from the ignore list.")
  @commands.has_permissions(administrator=True)
  @blacklist_check()
  async def command_remove(self, ctx: commands.Context, command_name: str):
      command_name_normalized = command_name.strip().lower()
      async with aiosqlite.connect(self.db_path) as db:
          cursor = await db.execute("SELECT command_name FROM ignored_commands WHERE guild_id = ? AND command_name = ?", (ctx.guild.id, command_name_normalized))
          result = await cursor.fetchone()
          if not result:
              embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"`{command_name}` is not in the ignore commands list.", color=self.color)
              await ctx.reply(view = embed_to_view(embed))
          else:
              await db.execute("DELETE FROM ignored_commands WHERE guild_id = ? AND command_name = ?", (ctx.guild.id, command_name_normalized))
              await db.commit()
              embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully removed `{command_name}` from the ignore commands list.", color=self.color)
              await ctx.reply(view = embed_to_view(embed))

  @_command.command(name="show", help="Displays the list of ignored commands.")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(administrator=True)
  async def command_show(self, ctx: commands.Context):
      async with aiosqlite.connect(self.db_path) as db:
          cursor = await db.execute("SELECT command_name FROM ignored_commands WHERE guild_id = ?", (ctx.guild.id,))
          commands = await cursor.fetchall()
          if not commands:
              embed = discord.Embed(description="No commands are currently ignored in this server.", color=self.color)
              await ctx.reply(view = embed_to_view(embed), mention_author=False)
          else:
              entries = [f"`{command[0]}`" for command in commands]
              description = "\n".join(entries)
              embed = discord.Embed(title="Ignored Commands", description=description, color=self.color)
              await ctx.reply(view = embed_to_view(embed), mention_author=False)

  @_ignore.group(name="channel", help="Manage ignored channels in this guild.", invoke_without_command=True)
  @blacklist_check()
  #@ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def _channel(self, ctx):
    if ctx.subcommand_passed is None:
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)

  @_channel.command(name="add", help="Adds a channel to the ignore list.")
  @blacklist_check()
  #@ignore_check()
  @commands.has_permissions(administrator=True)
  async def channel_add(self, ctx: commands.Context, channel: discord.TextChannel):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT COUNT(*) FROM ignored_channels WHERE guild_id = ?", (ctx.guild.id,))
      count = await cursor.fetchone()

      if count[0] >= 30:
        embed = discord.Embed(title=f"{emojis.OLYMPUS_NOTIFY} Access Denied", description="You can only add up to 30 channels to the ignore list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))
        return

      cursor = await db.execute("SELECT channel_id FROM ignored_channels WHERE guild_id = ? AND channel_id = ?", (ctx.guild.id, channel.id))
      result = await cursor.fetchone()

      if result:
        embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"{channel.mention} is already in the ignore channels list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
      else:
        await db.execute("INSERT INTO ignored_channels (guild_id, channel_id) VALUES (?, ?)", (ctx.guild.id, channel.id))
        await db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully added {channel.mention} to the ignore channels list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))

  @_channel.command(name="remove", help="Removes a channel from the ignore list.")
  @blacklist_check()
  #@ignore_check()
  @commands.has_permissions(administrator=True)
  async def channel_remove(self, ctx: commands.Context, channel: discord.TextChannel):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT channel_id FROM ignored_channels WHERE guild_id = ? AND channel_id = ?", (ctx.guild.id, channel.id))
      result = await cursor.fetchone()

      if not result:
        embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"{channel.mention} is not in the ignore channels list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))
      else:
        await db.execute("DELETE FROM ignored_channels WHERE guild_id = ? AND channel_id = ?", (ctx.guild.id, channel.id))
        await db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully removed {channel.mention} from the ignore channels list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))

  @_channel.command(name="show", help="Displays the list of ignored channels.")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(administrator=True)
  async def channel_show(self, ctx: commands.Context):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT channel_id FROM ignored_channels WHERE guild_id = ?", (ctx.guild.id,))
      channels = await cursor.fetchall()

      if not channels:
        embed = discord.Embed(description="No channels are currently ignored in this server.", color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
      else:
        channel_mentions = [ctx.guild.get_channel(channel_id).mention if ctx.guild.get_channel(channel_id) else f"Channel ID {channel_id}" for channel_id, in channels]
        description = "\n".join(channel_mentions)
        embed = discord.Embed(title="Ignored Channels", description=description, color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)

  @_ignore.group(name="user", help="Manage ignored users in this guild.", invoke_without_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def _user(self, ctx):
    if ctx.subcommand_passed is None:
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)

  @_user.command(name="add", help="Adds a user to the ignore list.")
  @commands.has_permissions(administrator=True)
  @blacklist_check()

  async def user_add(self, ctx: commands.Context, user: discord.User):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT COUNT(*) FROM ignored_users WHERE guild_id = ?", (ctx.guild.id,))
      count = await cursor.fetchone()

      if count[0] >= 30:
        embed = discord.Embed(title=f"{emojis.OLYMPUS_NOTIFY} Access Denied", description="You can only add up to 30 users to the ignore list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))
        return

      cursor = await db.execute("SELECT user_id FROM ignored_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
      result = await cursor.fetchone()

      if result:
        embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"{user.mention} is already in the ignore users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
      else:
        await db.execute("INSERT INTO ignored_users (guild_id, user_id) VALUES (?, ?)", (ctx.guild.id, user.id))
        await db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully added {user.mention} to the ignore users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))

  @_user.command(name="remove", help="Removes a user from the ignore list.")
  @blacklist_check()

  @commands.has_permissions(administrator=True)
  async def user_remove(self, ctx: commands.Context, user: discord.User):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT user_id FROM ignored_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
      result = await cursor.fetchone()

      if not result:
        embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"{user.mention} is not in the ignore users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))
      else:
        await db.execute("DELETE FROM ignored_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
        await db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully removed {user.mention} from the ignore users list.", color=self.color)
        await ctx.send(view = embed_to_view(embed))

  @_user.command(name="show", help="Displays the list of ignored users.")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(administrator=True)
  async def user_show(self, ctx: commands.Context):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT user_id FROM ignored_users WHERE guild_id = ?", (ctx.guild.id,))
      users = await cursor.fetchall()

      if not users:
        embed = discord.Embed(description="No users are currently ignored in this server.", color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
      else:
        user_mentions = [ctx.guild.get_member(user_id).mention if ctx.guild.get_member(user_id) else f"User ID {user_id}" for user_id, in users]
        description = "\n".join(user_mentions)
        embed = discord.Embed(title="Ignored Users", description=description, color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)

  @_ignore.group(name="bypass", help="Manage bypassed users in this guild.", invoke_without_command=True)
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def _bypass(self, ctx):
    if ctx.subcommand_passed is None:
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)

  @_bypass.command(name="add", help="Adds a user to the bypass list.")
  @blacklist_check()
  @ignore_check()
  
  @commands.has_permissions(administrator=True)
  async def bypass_add(self, ctx: commands.Context, user: discord.User):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT COUNT(*) FROM bypassed_users WHERE guild_id = ?", (ctx.guild.id,))
      count = await cursor.fetchone()

      if count[0] >= 30:
        embed = discord.Embed(description="You can only add up to 30 users to the bypass list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))
        return

      cursor = await db.execute("SELECT user_id FROM bypassed_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
      result = await cursor.fetchone()

      if result:
        embed = discord.Embed(title=f"{emojis.CROSSICON} Error", description=f"{user.mention} is already in the bypass users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
      else:
        await db.execute("INSERT INTO bypassed_users (guild_id, user_id) VALUES (?, ?)", (ctx.guild.id, user.id))
        await db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully added {user.mention} to the bypass users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))

  @_bypass.command(name="remove", help="Removes a user from the bypass list.")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(administrator=True)
  async def bypass_remove(self, ctx: commands.Context, user: discord.User):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT user_id FROM bypassed_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
      result = await cursor.fetchone()

      if not result:
        embed = discord.Embed(description=f"{user.mention} is not in the bypass users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))
      else:
        await db.execute("DELETE FROM bypassed_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
        await db.commit()
        embed = discord.Embed(title=f"{emojis.TICK} Success", description=f"Successfully removed {user.mention} from the bypass users list.", color=self.color)
        await ctx.reply(view = embed_to_view(embed))

  @_bypass.command(name="show", aliases=["list"], help="Displays the list of bypassed users.")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(administrator=True)
  async def bypass_show(self, ctx: commands.Context):
    async with aiosqlite.connect(self.db_path) as db:
      cursor = await db.execute("SELECT user_id FROM bypassed_users WHERE guild_id = ?", (ctx.guild.id,))
      users = await cursor.fetchall()

      if not users:
        embed = discord.Embed(description="No users are currently bypassed in this server.", color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
      else:
        user_mentions = [ctx.guild.get_member(user_id).mention if ctx.guild.get_member(user_id) else f"User ID {user_id}" for user_id, in users]
        description = "\n".join(user_mentions)
        embed = discord.Embed(title="Bypassed Users", description=description, color=self.color)
        await ctx.reply(view = embed_to_view(embed), mention_author=False)
