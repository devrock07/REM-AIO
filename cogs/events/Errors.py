import discord
import json
import aiosqlite
import logging
from discord.ext import commands
from utils.config import serverLink
from core import axon, Cog, Context
from utils.Tools import get_ignore_data
from utils.cv2_compat import embed_to_view, embeds_to_view

log = logging.getLogger(__name__)

class Errors(Cog):
  def __init__(self, client: axon):
    self.client = client

  @commands.Cog.listener()
  async def on_command_error(self, ctx: Context, error):
    if ctx.command is None:
      return
    

    if isinstance(error, commands.CommandNotFound):
      return

    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)
      return

    if isinstance(error, commands.CheckFailure):
      if ctx.guild is None:
        return

      data = await get_ignore_data(ctx.guild.id)
      ch = data["channel"]
      iuser = data["user"]
      cmd = data["command"]
      buser = data["bypassuser"]

      if str(ctx.author.id) in buser:
        return

      if str(ctx.channel.id) in ch:
        await ctx.reply(f"{ctx.author.mention} This **channel** is on the **ignored** list. Please try my commands in another channel.",
                        delete_after=8)
        return

      if str(ctx.author.id) in iuser:
        await ctx.reply(f"{ctx.author.mention} You are set as an **ignored user** for this guild. Please try my commands or modules in a different guild.", delete_after=8)
        return

      if ctx.command.name in cmd or any(alias in cmd for alias in ctx.command.aliases):
        await ctx.reply(f"{ctx.author.mention} This **command is ignored** in this guild. Please use other commands or try this command in a different guild", delete_after=8)
        return

    if isinstance(error, commands.NoPrivateMessage):
      embed = discord.Embed(color=0x000000, description="You can't use my commands in DMs.")
      embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
      embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
      await ctx.reply(view = embed_to_view(embed), delete_after=20)
      return

    if isinstance(error, commands.TooManyArguments):
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)
      return

    if isinstance(error, commands.CommandOnCooldown):
      embed = discord.Embed(color=0x000000, description=f"{ctx.author.mention} Whoa, slow down there! You can run the command again in **{error.retry_after:.2f}** seconds.")
      embed.set_author(name="Cooldown", icon_url=self.client.user.avatar.url)
      
      embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
      await ctx.reply(view = embed_to_view(embed), delete_after=10)
      return

    if isinstance(error, commands.MaxConcurrencyReached):
      embed = discord.Embed(color=0x000000, description=f"{ctx.author.mention} This command is already in progress. Please let it finish and try again afterward.")
      embed.set_author(name="Command in Progress.", icon_url=self.client.user.avatar.url)
      
      embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
      await ctx.reply(view = embed_to_view(embed), delete_after=10)
      ctx.command.reset_cooldown(ctx)
      return

    if isinstance(error, commands.MissingPermissions):
      missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_permissions]
      fmt = "{}, and {}".format(", ".join(missing[:-1]), missing[-1]) if len(missing) > 2 else " and ".join(missing)
      embed = discord.Embed(color=0x000000, description=f"You lack the **{fmt}** Permission to run the **{ctx.command.name}** command!")
      embed.set_author(name="Missing Permissions", icon_url=self.client.user.avatar.url)
      
      embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
      await ctx.reply(view = embed_to_view(embed), delete_after=7)
      ctx.command.reset_cooldown(ctx)
      return

    if isinstance(error, commands.BadArgument):
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)
      return

    if isinstance(error, commands.BotMissingPermissions):
      missing = ", ".join(error.missing_permissions)
      await ctx.reply(f' I need **{missing}** Permission to run the **{ctx.command.qualified_name}** command!', delete_after=7)
      return

    if isinstance(error, discord.HTTPException):
      return

    if isinstance(error, commands.CommandInvokeError):
      log.exception("Command %s failed", ctx.command.qualified_name if ctx.command else "unknown", exc_info=error.original)
      return

