from utils import emojis

import json, sys, os
import discord
from discord.ext import commands
from utils.config import BYPASS_IDS
from utils.database import connect
from utils.security import get_security_gate

async def setup_db():
  async with connect('prefix.db') as db:
    await db.execute('''
      CREATE TABLE IF NOT EXISTS prefixes (
        guild_id INTEGER PRIMARY KEY,
        prefix TEXT NOT NULL
      )
    ''')
    await db.commit()


async def is_topcheck_enabled(guild_id: int):
    return await get_security_gate().is_topcheck_enabled(guild_id)
            


def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"guilds": {}}

def write_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def get_or_create_guild_config(file_path, guild_id, default_config):
    data = read_json(file_path)
    if "guilds" not in data:
        data["guilds"] = {}  

    guild_id_str = str(guild_id)
    if guild_id_str not in data["guilds"]:
        data["guilds"][guild_id_str] = default_config
        write_json(file_path, data)
    return data["guilds"][guild_id_str]

def update_guild_config(file_path, guild_id, new_data):
    data = read_json(file_path)
    if "guilds" not in data:
        data["guilds"] = {}  

    data["guilds"][str(guild_id)] = new_data
    write_json(file_path, data)

def getIgnore(guild_id):
    default_config = {
        "channel": [],
        "role": None,
        "user": [],
        "bypassrole": None,
        "bypassuser": [],
        "commands": []
    }
    return get_or_create_guild_config("ignore.json", guild_id, default_config)

def updateignore(guild_id, data):
    update_guild_config("ignore.json", guild_id, data)





async def getConfig(guildID):
  prefix = await get_security_gate().get_prefix(guildID)
  return {"prefix": prefix}

async def updateConfig(guildID, data):
  async with connect('prefix.db') as db:
    await db.execute(
      "INSERT OR REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)",
      (guildID, data["prefix"])
    )
    await db.commit()
  await get_security_gate().invalidate_prefix(guildID)



def restart_program():
  python = sys.executable
  os.execl(python, python, *sys.argv)


def blacklist_check():

  async def predicate(ctx):
    if ctx.guild is None:
      return True

    decision = await get_security_gate().check_blacklist(ctx.author.id, ctx.guild.id)
    return decision.allowed

  return commands.check(predicate)
    

async def get_ignore_data(guild_id: int) -> dict:
    return await get_security_gate().get_ignore_data(guild_id)

def ignore_check():
    async def predicate(ctx):
        if ctx.guild is None:
            return True

        decision = await get_security_gate().check_ignore(ctx)
        return decision.allowed

    return commands.check(predicate)


def is_security_manager(member: discord.Member) -> bool:
    if member.guild is None:
        return False
    return (
        member.id == member.guild.owner_id
        or member.guild_permissions.administrator
        or member.id in BYPASS_IDS
    )


def can_manage_member(actor: discord.Member, target: discord.Member) -> bool:
    if actor.guild is None or target.guild is None or actor.guild.id != target.guild.id:
        return False
    if actor.id == actor.guild.owner_id:
        return True
    if target.id == actor.guild.owner_id:
        return False
    return actor.top_role > target.top_role


def can_manage_role(actor: discord.Member, role: discord.Role) -> bool:
    if actor.guild is None or role.guild.id != actor.guild.id:
        return False
    if actor.id == actor.guild.owner_id:
        return True
    return actor.top_role > role


async def deny(ctx, message: str):
    try:
        return await ctx.reply(message, mention_author=False)
    except Exception:
        return await ctx.send(message)


def security_manager_check():
    async def predicate(ctx):
        return bool(ctx.guild and is_security_manager(ctx.author))

    return commands.check(predicate)


def is_moderation_staff(member: discord.Member) -> bool:
    if member.guild is None:
        return False

    perms = member.guild_permissions
    return (
        is_security_manager(member)
        or perms.manage_messages
        or perms.manage_roles
        or perms.manage_channels
        or perms.kick_members
        or perms.ban_members
        or perms.moderate_members
        or perms.manage_nicknames
        or getattr(perms, "manage_emojis_and_stickers", False)
        or getattr(perms, "manage_emojis", False)
        or perms.view_audit_log
    )


def moderation_staff_check():
    async def predicate(ctx):
        return bool(ctx.guild and is_moderation_staff(ctx.author))

    return commands.check(predicate)


def bot_has_permissions(**permissions: bool):
    """Ensure the bot has required guild permissions before running a command."""

    async def predicate(ctx):
        if ctx.guild is None or ctx.guild.me is None:
            return True

        missing = [
            perm.replace("_", " ").title()
            for perm, required in permissions.items()
            if required and not getattr(ctx.guild.me.guild_permissions, perm, False)
        ]
        if not missing:
            return True

        from utils.components_v2 import warning_panel

        label = ", ".join(missing)
        await ctx.reply(
            view=warning_panel(
                f"I need **{label}** permission(s) to run `{ctx.command.qualified_name}`.",
                title="Missing Bot Permissions",
            ),
            mention_author=False,
        )
        return False

    return commands.check(predicate)

def top_check():
    async def predicate(ctx):
        if not ctx.guild:
            return True

        if getattr(ctx, "invoked_with", None) in ["help", "h"]:
            return True

        topcheck_enabled = await is_topcheck_enabled(ctx.guild.id)

        if not topcheck_enabled:
            return True

        if ctx.author != ctx.guild.owner and ctx.author.top_role.position <= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title=f"{emojis.DENIED} Access Denied", 
                description="Your top role must be at a **higher** position than my top role.",
                color=0x000000
            )
            embed.set_footer(
                text=f"“{ctx.command.qualified_name}” command executed by {ctx.author}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            await ctx.send(embed=embed)
            return False

        return True

    return commands.check(predicate)
