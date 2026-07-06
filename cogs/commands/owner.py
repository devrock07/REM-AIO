from __future__ import annotations
from utils import emojis

from discord.ext import commands
from discord import *
from PIL import Image, ImageDraw, ImageFont
import discord
import json
import datetime
import asyncio
import aiosqlite
from typing import Optional
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator
from utils.Tools import *
from utils.config import OWNER_IDS
from core import Cog, axon, Context
import sqlite3
import os
import requests
from io import BytesIO
from utils.config import OWNER_IDS
from discord.errors import Forbidden
from discord import Embed
from discord.ui import Button, View
from utils.cv2_compat import embed_to_view, embeds_to_view




BADGE_URLS = {
    "owner": "https://cdn.discordapp.com/emojis/1228227536207740989.png",
    "staff": "https://cdn.discordapp.com/emojis/1228227884481515613.png",
    "partner": "https://cdn.discordapp.com/emojis/1228228301089144976.png",
    "sponsor": "https://cdn.discordapp.com/emojis/1228246375180013678.png",
    "friend": "https://cdn.discordapp.com/emojis/1228229690376982549.png",
    "early": "https://cdn.discordapp.com/emojis/1228241490246111302.png",
    "vip": "https://cdn.discordapp.com/emojis/1228230884583276584.png",
    "bug": "https://cdn.discordapp.com/emojis/1228231513456382015.png"
}

BADGE_NAMES = {
    "owner": "Owner",
    "staff": "Staff",
    "partner": "Partner",
    "sponsor": "Sponsor",
    "friend": "Owner's Friend",
    "early": "Early Supporter",
    "vip": "VIP",
    "bug": "Bug Hunter"
}


db_folder = 'db'
db_file = 'badges.db'
db_path = os.path.join(db_folder, db_file)
FONT_PATH = os.path.join('utils', 'arial.ttf')


conn = sqlite3.connect(db_path)
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS badges (
    user_id INTEGER PRIMARY KEY,
    owner INTEGER DEFAULT 0,
    staff INTEGER DEFAULT 0,
    partner INTEGER DEFAULT 0,
    sponsor INTEGER DEFAULT 0,
    friend INTEGER DEFAULT 0,
    early INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0,
    bug INTEGER DEFAULT 0
)''')
conn.commit()

def add_badge(user_id, badge):
    c.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result is None:
        c.execute(f"INSERT INTO badges (user_id, {badge}) VALUES (?, 1)", (user_id,))
    elif result[0] == 0:
        c.execute(f"UPDATE badges SET {badge} = 1 WHERE user_id = ?", (user_id,))
    else:
        return False
    conn.commit()
    return True

def remove_badge(user_id, badge):
    c.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result and result[0] == 1:
        c.execute(f"UPDATE badges SET {badge} = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    return False


def convert_time_to_seconds(time_str):
    time_units = {
        "h": "hours",
        "d": "days",
        "m": "months"
    }
    num = int(time_str[:-1])
    unit = time_units.get(time_str[-1])
    return datetime.timedelta(**{unit: num})


async def do_removal(ctx, limit, predicate, *, before=None, after=None):
  if limit > 2000:
      return await ctx.error(f"Too many messages to search given ({limit}/2000)")

  if before is None:
      before = ctx.message
  else:
      before = discord.Object(id=before)

  if after is not None:
      after = discord.Object(id=after)

  try:
      deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
  except discord.Forbidden as e:
      return await ctx.error("I do not have permissions to delete messages.")
  except discord.HTTPException as e:
      return await ctx.error(f"Error: {e} (try a smaller search?)")

  spammers = Counter(m.author.display_name for m in deleted)
  deleted = len(deleted)
  messages = [f'{emojis.TICK} | {deleted} message{" was" if deleted == 1 else "s were"} removed.']
  if deleted:
      messages.append("")
      spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
      messages.extend(f"**{name}**: {count}" for name, count in spammers)

  to_send = "\n".join(messages)

  if len(to_send) > 2000:
      await ctx.send(f"{emojis.TICK} | Successfully removed {deleted} messages.", delete_after=3)
  else:
      await ctx.send(to_send, delete_after=3)

def load_owner_ids():
    return OWNER_IDS



async def is_staff(user, staff_ids):
    return user.id in staff_ids


async def is_owner_or_staff(ctx):
    return await is_staff(ctx.author, ctx.cog.staff) or ctx.author.id in OWNER_IDS


class Owner(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.staff = set()
        self.np_cache = []
        self.db_path = 'db/np.db'
        self.stop_tour = False
        self.bot_owner_ids = [767979794411028491,]
        asyncio.create_task(self.setup_database())
        asyncio.create_task(self.load_staff())
        

    async def setup_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS staff (
                    id INTEGER PRIMARY KEY
                )
            ''')
            await db.commit()

    

    async def load_staff(self):
        try:
            await self.client.wait_until_ready()
        except RuntimeError:
            pass
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT id FROM staff') as cursor:
                self.staff = {row[0] for row in await cursor.fetchall()}

    @commands.command(name="staff_add", aliases=["staffadd", "addstaff"], help="Adds a user to the staff list.")
    @commands.is_owner()
    async def staff_add(self, ctx, user: discord.User):
        if user.id in self.staff:
            sonu = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description=f"{user} is already in the staff list.", color=0x000000)
            await ctx.reply(view = embed_to_view(sonu), mention_author=False)
        else:
            self.staff.add(user.id)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('INSERT OR IGNORE INTO staff (id) VALUES (?)', (user.id,))
                await db.commit()
            sonu2 = discord.Embed(title=f"{emojis.TICK} Success", description=f"Added {user} to the staff list.", color=0x000000)
            await ctx.reply(view = embed_to_view(sonu2), mention_author=False)

    @commands.command(name="staff_remove", aliases=["staffremove", "removestaff"], help="Removes a user from the staff list.")
    @commands.is_owner()
    async def staff_remove(self, ctx, user: discord.User):
        if user.id not in self.staff:
            sonu = discord.Embed(title=f"{emojis.ICONS_WARNING} Access Denied", description=f"{user} is not in the staff list.", color=0x000000)
            await ctx.reply(view = embed_to_view(sonu), mention_author=False)
        else:
            self.staff.remove(user.id)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM staff WHERE id = ?', (user.id,))
                await db.commit()
                sonu2 = discord.Embed(title=f"{emojis.TICK} Success", description=f"Removed {user} from the staff list.", color=0x000000)
            await ctx.reply(view = embed_to_view(sonu2), mention_author=False)

    @commands.command(name="staff_list", aliases=["stafflist", "liststaff", "staffs"], help="Lists all staff members.")
    @commands.is_owner()
    async def staff_list(self, ctx):
        if not self.staff:
            await ctx.send("The staff list is currently empty.")
        else:
            member_list = []
            for staff_id in self.staff:
                member = await self.client.fetch_user(staff_id)
                member_list.append(f"{member.name}#{member.discriminator} (ID: {staff_id})")
            staff_display = "\n".join(member_list)
            sonu = discord.Embed(title=f"{emojis.TICK} REM ALL IN ONE BOT Staff", description=f"\n{staff_display}", color=0x000000)
            await ctx.send(view = embed_to_view(sonu))

    @commands.command(name="slist")
    @commands.check(is_owner_or_staff)
    async def _slist(self, ctx):
        servers = sorted(self.client.guilds, key=lambda g: g.member_count, reverse=True)
        entries = [
            f"`#{i}` | [{g.name}](https://discord.com/guilds/{g.id}) - {g.member_count}"
            for i, g in enumerate(servers, start=1)
        ]
        paginator = Paginator(source=DescriptionEmbedPaginator(
            entries=entries,
            description="",
            title=f"Guild List of REM ALL IN ONE BOT [{len(self.client.guilds)}]",
            color=0x000000,
            per_page=10),
            ctx=ctx)
        await paginator.paginate()


    @commands.command(name="mutuals", aliases=["mutual"])
    @commands.is_owner()
    async def mutuals(self, ctx, user: discord.User):
        guilds = [guild for guild in self.client.guilds if user in guild.members]
        entries = [
            f"`#{no}` | [{guild.name}](https://discord.com/channels/{guild.id}) - {guild.member_count}"
            for no, guild in enumerate(guilds, start=1)
        ]
        paginator = Paginator(source=DescriptionEmbedPaginator(
            entries=entries,
            description="",
            title=f"Mutual Guilds of {user.name} [{len(guilds)}]",
            color=0x000000,
            per_page=10),
            ctx=ctx)
        await paginator.paginate()

    @commands.command(name="getinvite", aliases=["gi", "guildinvite"])
    @commands.is_owner()
    async def getinvite(self, ctx: Context, guild= discord.Guild):
        
        if not guild:
            await ctx.send("Invalid server.")
            return

        perms_ha = guild.me.guild_permissions.view_audit_log
        invite_krskta = guild.me.guild_permissions.create_instant_invite

        try:
            invites = await guild.invites()
            if invites:
                entries = [f"{invite.url} - {invite.uses} uses" for invite in invites]
                paginator = Paginator(source=DescriptionEmbedPaginator(
                    entries=entries,
                    title=f"Active Invites for {guild.name}",
                    description="",
                    per_page=10,
                    color=0xff0000),
                    ctx=ctx)
                await paginator.paginate()
            elif invite_krskta:
                channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite), None)
                if channel:
                    invite = await channel.create_invite(max_age=86400, max_uses=1, reason="No active invites found, creating a new one.")
                    await ctx.send(f"Created new invite: {invite.url}")
                else:
                    await ctx.send("No channel found.")
            else:
                await ctx.send("Can't create invites.")
        except discord.Forbidden:
            await ctx.send("Forbidden.")


    @commands.command(name="Q.reload", help="Restarts the client.")
    @commands.is_owner()
    async def _restart(self, ctx: Context):
        await ctx.reply("Restarting REM ALL IN ONE BOT...")
        restart_program()

    @commands.command(name="sync", help="Syncs all database.")
    @commands.is_owner()
    async def _sync(self, ctx):
        await ctx.reply("Syncing...", mention_author=False)
        with open('events.json', 'r') as f:
            data = json.load(f)
        for guild in self.client.guilds:
            if str(guild.id) not in data['guild']:
                data['guilds'][str(guild.id)] = 'on'
                with open('events.json', 'w') as f:
                    json.dump(data, f, indent=4)
            else:
                pass
        with open('config.json', 'r') as f:
            data = json.load(f)
        for op in data["guilds"]:
            g = self.client.get_guild(int(op))
            if not g:
                data["guilds"].pop(str(op))
                with open('config.json', 'w') as f:
                    json.dump(data, f, indent=4)


    @commands.command(name="owners")
    @commands.is_owner()
    async def own_list(self, ctx):
        nplist = OWNER_IDS
        npl = ([await self.client.fetch_user(nplu) for nplu in nplist])
        npl = sorted(npl, key=lambda nop: nop.created_at)
        entries = [
            f"`#{no}` | [{mem}](https://discord.com/users/{mem.id}) (ID: {mem.id})"
            for no, mem in enumerate(npl, start=1)
        ]
        paginator = Paginator(source=DescriptionEmbedPaginator(
            entries=entries,
            title=f"REM ALL IN ONE BOT Owners [{len(nplist)}]",
            description="",
            per_page=10,
            color=0x000000),
                              ctx=ctx)
        await paginator.paginate()





    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, message: str):
        """ DM the user of your choice """
        try:
            await user.send(message)
            await ctx.send(f"{emojis.TICK} | Successfully Sent a DM to **{user}**")
        except discord.Forbidden:
            await ctx.send("This user might be having DMs blocked or it's a bot account...")           



    @commands.group()
    @commands.is_owner()
    async def change(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))


    @change.command(name="nickname")
    @commands.is_owner()
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"{emojis.TICK} | Successfully changed nickname to **{name}**")
            else:
                await ctx.send(f"{emojis.TICK} | Successfully removed nickname")
        except Exception as err:
            await ctx.send(err) 


    @commands.command(name="ownerban", aliases=["forceban", "dna"])
    @commands.is_owner()
    async def _ownerban(self, ctx: Context, user_id: int, *, reason: str = "No reason provided"):
        
        member = ctx.guild.get_member(user_id)
        if member:
            try:
                await member.ban(reason=reason)
                embed = discord.Embed(
                    title="Successfully Banned",
                    description=f"{emojis.TICK} | **{member.name}** has been successfully banned from {ctx.guild.name} by the Bot Owner.",
                    color=0x000000)
                await ctx.reply(view = embed_to_view(embed), mention_author=False, delete_after=3)
                await ctx.message.delete()
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Error!",
                    description=f"{emojis.ICONS_WARNING} I do not have permission to ban **{member.name}** in this guild.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed), mention_author=False, delete_after=5)
                await ctx.message.delete()
            except discord.HTTPException:
                embed = discord.Embed(
                    title="Error!",
                    description=f"{emojis.ICONS_WARNING} An error occurred while banning **{member.name}**.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed), mention_author=False, delete_after=5)
                await ctx.message.delete()
        else:
            await ctx.reply("User not found in this guild.", mention_author=False, delete_after=3)
            await ctx.message.delete()

    @commands.command(name="ownerunban", aliases=["forceunban"])
    @commands.is_owner()
    async def _ownerunban(self, ctx: Context, user_id: int, *, reason: str = "No reason provided"):
        user = self.client.get_user(user_id)
        if user:
            try:
                await ctx.guild.unban(user, reason=reason)
                embed = discord.Embed(
                    title="Successfully Unbanned",
                    description=f"{emojis.TICK} | **{user.name}** has been successfully unbanned from {ctx.guild.name} by the Bot Owner.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed), mention_author=False)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Error!",
                    description=f"{emojis.ICONS_WARNING} I do not have permission to unban **{user.name}** in this guild.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed), mention_author=False)
            except discord.HTTPException:
                embed = discord.Embed(
                    title="Error!",
                    description=f"{emojis.ICONS_WARNING} An error occurred while unbanning **{user.name}**.",
                    color=0x000000
                )
                await ctx.reply(view = embed_to_view(embed), mention_author=False)
        else:
            await ctx.reply("User not found.", mention_author=False)



    @commands.command(name="globalunban")
    @commands.is_owner()
    async def globalunban(self, ctx: Context, user: discord.User):
        success_guilds = []
        error_guilds = []

        for guild in self.client.guilds:
            bans = await guild.bans()
            if any(ban_entry.user.id == user.id for ban_entry in bans):
                try:
                    await guild.unban(user, reason="Global Unban")
                    success_guilds.append(guild.name)
                except discord.HTTPException:
                    error_guilds.append(guild.name)
                except discord.Forbidden:
                    error_guilds.append(guild.name)

        user_mention = f"{user.mention} (**{user.name}**)"

        success_message = f"Successfully unbanned {user_mention} from the following guild(s):\n{',     '.join(success_guilds)}" if success_guilds else "No guilds where the user was successfully unbanned."
        error_message = f"Failed to unban {user_mention} from the following guild(s):\n{',    '.join(error_guilds)}" if error_guilds else "No errors during unbanning."

        await ctx.reply(f"{success_message}\n{error_message}", mention_author=False)

    @commands.command(name="guildban")
    @commands.is_owner()
    async def guildban(self, ctx: Context, guild_id: int, user_id: int, *, reason: str = "No reason provided"):
        guild = self.client.get_guild(guild_id)
        if not guild:
            await ctx.reply("Bot is not present in the specified guild.", mention_author=False)
            return

        member = guild.get_member(user_id)
        if member:
            try:
                await guild.ban(member, reason=reason)
                await ctx.reply(f"Successfully banned **{member.name}** from {guild.name}.", mention_author=False)
            except discord.Forbidden:
                await ctx.reply(f"Missing permissions to ban **{member.name}** in {guild.name}.", mention_author=False)
            except discord.HTTPException as e:
                await ctx.reply(f"An error occurred while banning **{member.name}** in {guild.name}: {str(e)}", mention_author=False)
        else:
            await ctx.reply(f"User not found in the specified guild {guild.name}.", mention_author=False)

    @commands.command(name="guildunban")
    @commands.is_owner()
    async def guildunban(self, ctx: Context, guild_id: int, user_id: int, *, reason: str = "No reason provided"):
        guild = self.client.get_guild(guild_id)
        if not guild:
            await ctx.reply("Bot is not present in the specified guild.", mention_author=False)
            return
        #member = guild.get_member(user_id)

        try:
            user = await self.client.fetch_user(user_id)
        except discord.NotFound:
            await ctx.reply(f"User with ID {user_id} not found.", mention_author=False)
            return

        user = discord.Object(id=user_id)
        try:
            await guild.unban(user, reason=reason)
            await ctx.reply(f"Successfully unbanned user ID {user_id} from {guild.name}.", mention_author=False)
        except discord.Forbidden:
            await ctx.reply(f"Missing permissions to unban user ID {user_id} in {guild.name}.", mention_author=False)
        except discord.HTTPException as e:
            await ctx.reply(f"An error occurred while unbanning user ID {user_id} in {guild.name}: {str(e)}", mention_author=False)


    @commands.command(name="leaveguild", aliases=["leavesv"])
    @commands.is_owner()
    async def leave_guild(self, ctx, guild_id: int):
        guild = self.client.get_guild(guild_id)
        if guild is None:
            await ctx.send(f"Guild with ID {guild_id} not found.")
            return

        await guild.leave()
        await ctx.send(f"Left the guild: {guild.name} ({guild.id})")

    @commands.command(name="guildinfo")
    @commands.check(is_owner_or_staff)
    async def guild_info(self, ctx, guild_id: int):
        guild = self.client.get_guild(guild_id)
        if guild is None:
            await ctx.send(f"Guild with ID {guild_id} not found.")
            return

        embed = discord.Embed(
            title=guild.name,
            description=f"Information for guild ID {guild.id}",
            color=0x00000
        )
        embed.add_field(name="Owner", value=str(guild.owner), inline=True)
        embed.add_field(name="Member Count", value=str(guild.member_count), inline=True)
        embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        if guild.icon is not None:
                embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"Created at: {guild.created_at}")

        await ctx.send(view = embed_to_view(embed))

    @commands.command()
    @commands.is_owner()
    async def servertour(self, ctx, time_in_seconds: int, member: discord.Member):
        guild = ctx.guild

        if time_in_seconds > 3600:
            await ctx.send("Time cannot be greater than 3600 seconds (1 hour).")
            return

        if not member.voice:
            await ctx.send(f"{member.display_name} is not in a voice channel.")
            return

        voice_channels = [ch for ch in guild.voice_channels if ch.permissions_for(guild.me).move_members]

        if len(voice_channels) < 2:
            await ctx.send("Not enough voice channels to move the user.")
            return

        self.stop_tour = False

        class StopButton(discord.ui.View):
            def __init__(self, outer_self):
                super().__init__(timeout=time_in_seconds)
                self.outer_self = outer_self

            @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
            async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id not in self.outer_self.bot_owner_ids:
                    await interaction.response.send_message("Only the bot owner can stop this process.", ephemeral=True)
                    return
                self.outer_self.stop_tour = True
                await interaction.response.send_message("Server tour has been stopped.", ephemeral=True)
                self.stop()

        view = StopButton(self)
        message = await ctx.send(f"Started moving {member.display_name} for {time_in_seconds} seconds. Click the button to stop.", view=view)

        end_time = asyncio.get_event_loop().time() + time_in_seconds

        while asyncio.get_event_loop().time() < end_time and not self.stop_tour:
            for ch in voice_channels:
                if self.stop_tour:
                    await ctx.send("Tour stopped.")
                    return
                if not member.voice:
                    await ctx.send(f"{member.display_name} left the voice channel.")
                    return
                try:
                    await member.move_to(ch)
                    await asyncio.sleep(5)
                except Forbidden:
                    await ctx.send(f"Missing permissions to move {member.display_name}.")
                    return
                except Exception as e:
                    await ctx.send(f"Error: {str(e)}")
                    return

        if not self.stop_tour:
            await message.edit(content=f"Finished moving {member.display_name} after {time_in_seconds} seconds.", view=None)




    


    @commands.group()
    @commands.check(is_owner_or_staff)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bdg(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(description='Invalid `bdg` command passed. Use `add` or `remove`.', color=0x000000)
            await ctx.send(view = embed_to_view(embed))

    @bdg.command()
    @commands.check(is_owner_or_staff)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def add(self, ctx, member: discord.Member, badge: str):
        badge = badge.lower()
        user_id = member.id
        if badge in BADGE_URLS or badge == 'bug' or badge == 'all':
            if badge == 'all':
                for b in BADGE_URLS.keys():
                    add_badge(user_id, b)
                add_badge(user_id, 'bug')
                embed = discord.Embed(description=f"All badges added to {member.mention}.", color=0x000000)
                await ctx.send(view = embed_to_view(embed))
            else:
                success = add_badge(user_id, badge)
                if success:
                    embed = discord.Embed(description=f"Badge `{badge}` added to {member.mention}.", color=0x000000)
                else:
                    embed = discord.Embed(description=f"{member.mention} already has the badge `{badge}`.", color=0x000000)
                await ctx.send(view = embed_to_view(embed))
        else:
            embed = discord.Embed(description=f"Invalid badge: `{badge}`", color=0x000000)
            await ctx.send(view = embed_to_view(embed))

    @bdg.command()
    @commands.check(is_owner_or_staff)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def remove(self, ctx, member: discord.Member, badge: str):
        badge = badge.lower()
        user_id = member.id
        if badge in BADGE_URLS or badge == 'bug' or badge == 'all':
            if badge == 'all':
                for b in BADGE_URLS.keys():
                    remove_badge(user_id, b)
                remove_badge(user_id, 'bug')
                embed = discord.Embed(description=f"All badges removed from {member.mention}.", color=0x000000)
                await ctx.send(view = embed_to_view(embed))
            else:
                success = remove_badge(user_id, badge)
                if success:
                    embed = discord.Embed(description=f"Badge `{badge}` removed from {member.mention}.", color=0x000000)
                else:
                    embed = discord.Embed(description=f"{member.mention} does not have the badge `{badge}`.", color=0x000000)
                await ctx.send(view = embed_to_view(embed))
        else:
            embed = discord.Embed(description=f"Invalid badge: `{badge}`", color=0x000000)
            await ctx.send(view = embed_to_view(embed))


    @commands.command(name="forcepurgebots",
        aliases=["fpb"],
        help="Clear recently bot messages in channel (Bot owner only)")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_messages=True)
    async def _purgebot(self, ctx, prefix=None, search=100):
        
        await ctx.message.delete()
        
        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))
        
        await do_removal(ctx, search, predicate)


    @commands.command(name="forcepurgeuser",
        aliases=["fpu"],
        help="Clear recent messages of a user in channel (Bot owner only)")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.is_owner()
    @commands.bot_has_permissions(manage_messages=True)
    async def purguser(self, ctx, member: discord.Member, search=100):
        
        await ctx.message.delete()
        
        await do_removal(ctx, search, lambda e: e.author == member)




class Badges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'db/np.db'

        
    @commands.hybrid_command(aliases=['profile', 'pr'])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def badges(self, ctx, member: discord.Member = None):

        processing_message = await ctx.send(f"{emojis.LOADING} Loading your profile...")

        member = member or ctx.author
        user_id = member.id

        
        c.execute("SELECT * FROM badges WHERE user_id = ?", (user_id,))
        badges = c.fetchone()

        if badges:
            badges = dict(zip([column[0] for column in c.description], badges))
        else:
            badges = {k: 0 for k in BADGE_URLS.keys()}

        
        badge_size = 120
        padding = 80
        num_columns = 4
        image_width = 960
        image_height = 540



        def calculate_text_dimensions(badge_name, font, padding=1):
            text_bbox = draw.textbbox((0, 0), badge_name, font=font)
            text_width = (text_bbox[2] - text_bbox[0]) + 2 * padding
            text_height = (text_bbox[3] - text_bbox[1]) + 2 * padding
            return text_width, text_height

        
        def draw_badges(badges, draw, img):

            
            upper_y = (image_height // 4) - (badge_size // 2)
            lower_y = (3 * image_height // 4) - (badge_size // 2)
            
            x_positions = [padding + i * ((image_width - 2 * padding) // (num_columns - 1)) for i in range(num_columns)]

            badge_positions = []
            for badge in BADGE_URLS.keys():
                if badges[badge]:
                    badge_positions.append(badge)

            for i, badge in enumerate(badge_positions):
                y = upper_y if i < num_columns else lower_y
                x = x_positions[i % num_columns]
                response = requests.get(BADGE_URLS[badge])
                badge_img = Image.open(BytesIO(response.content)).resize((badge_size, badge_size))
                img.paste(badge_img, (x - badge_size // 2, y), badge_img)
                text_width, text_height = calculate_text_dimensions(BADGE_NAMES[badge], font)
                draw.text((x - text_width // 2, y + badge_size + 5), BADGE_NAMES[badge], fill=(255, 0, 0), font=font)  

        
        has_badges = any(value == 1 for value in badges.values())

        if has_badges:
            
            img = Image.new('RGBA', (image_width, image_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(FONT_PATH, 25)  

            
            draw_badges(badges, draw, img)

            with BytesIO() as image_binary:
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='badge.png')

            embed = discord.Embed(title=f"{member.display_name}'s Profile", color=0x000000)

            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            embed.add_field(name="__**Account Created At**__", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
            embed.add_field(name="__**Joined This Guild At**__", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)



            # User Badges
            user_flags = member.public_flags
            user_badges = []

            badge_mapping = {
              "staff": " Discord Employee",
              "partner": " Partnered Server Owner",
              "discord_certified_moderator": "Moderator Programs Alumni",
              "hypesquad_balance": "House Balance Member",
              "hypesquad_bravery": "House Bravery Member",
              "hypesquad_brilliance": " House Brilliance Member",
              "hypesquad": " HypeSquad Events Member",
              "early_supporter": " Early Supporter",
              "bug_hunter": " Bug Hunter Level 1",
              "bug_hunter_level_2": " Bug Hunter Level 2",
              "verified_bot": "Verified Bot",
              "verified_bot_developer": "Verified Bot Developer",
              "active_developer": "Active Developer",
              "early_verified_bot_developer": " Early Verified Bot Developer",
              "system": " System User",
              "team_user": "👷 User is a [Team](https://discord.com/developers/docs/topics/teams)",
              "spammer": " Marked as Spammer",
              "bot_http_interactions": " Bot uses only [HTTP interactions](https://discord.com/developers/docs/interactions/receiving-and-responding#receiving-an-interaction) and is shown in the online member list."
            }

            for flag, value in badge_mapping.items():
              if getattr(user_flags, flag):
                user_badges.append(value)

            
            user = await self.bot.fetch_user(member.id)
            wtf = bool(user.avatar and user.avatar.is_animated())
            omg = bool(user.banner)
            if not member.bot:
                if omg or wtf:
                    user_badges.append(" Nitro Subscriber")
                for guild in self.bot.guilds:
                    if member in guild.members:
                        if guild.premium_subscription_count > 0 and member in guild.premium_subscribers:
                            user_badges.append("Server Booster Badge")
                            
            if user_badges:
              embed.add_field(name="__**User Badges**__", value="\n".join(user_badges), inline=False)
            else:
              embed.add_field(name="__**User Badges**__", value="None", inline=False)

            # Bot Badges
            embed.add_field(name="__**Bot Badges**__", value="Below", inline=False)
            embed.set_image(url="attachment://badge.png")
            embed.set_footer(text=f"Requested by {ctx.author} | Nitro badge if banner/animated avatar; Booster badge if boosting a mutual guild with bot.", icon_url=ctx.author.avatar.url
                               if ctx.author.avatar else ctx.author.default_avatar.url)

            await ctx.send(view = embed_to_view(embed), file=file)
            await processing_message.delete()
        else:
            embed = discord.Embed(title=f"{member.display_name}'s Profile", color=0x000000)

            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            embed.add_field(name="__**Account Created At**__", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
            embed.add_field(name="__**Joined This Guild At**__", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=True)




            # User Badges
            user_flags = member.public_flags
            user_badges = []

            badge_mapping = {
              "staff": "< Discord Employee",
              "partner": " Partnered Server Owner",
              "discord_certified_moderator": " Moderator Programs Alumni",
              "hypesquad_balance": "<House Balance Member",
              "hypesquad_bravery": "House Bravery Member",
              "hypesquad_brilliance": " House Brilliance Member",
              "hypesquad": "HypeSquad Events Member",
              "early_supporter": "> Early Supporter",
              "bug_hunter": "Bug Hunter Level 1",
              "bug_hunter_level_2": " Bug Hunter Level 2",
              "verified_bot": "Verified Bot",
              "verified_bot_developer": "Verified Bot Developer",
              "active_developer": "Active Developer",
              "early_verified_bot_developer": " Early Verified Bot Developer",
              "system": "System User",
              "team_user": "👷 User is a [Team](https://discord.com/developers/docs/topics/teams)",
              "spammer": "Marked as Spammer",
              "bot_http_interactions": "Bot uses only [HTTP interactions](https://discord.com/developers/docs/interactions/receiving-and-responding#receiving-an-interaction) and is shown in the online member list."
            }

            for flag, value in badge_mapping.items():
              if getattr(user_flags, flag):
                user_badges.append(value)

            user = await self.bot.fetch_user(member.id)
            wtf = bool(user.avatar and user.avatar.is_animated())
            omg = bool(user.banner)
            if not member.bot:
                if omg or wtf:
                    user_badges.append(" Nitro Subscriber")
                for guild in self.bot.guilds:
                    if member in guild.members:
                        if guild.premium_subscription_count > 0 and member in guild.premium_subscribers:
                            user_badges.append(" Server Booster Badge")

            if user_badges:
              embed.add_field(name="__**User Badges**__", value="\n".join(user_badges), inline=False)
            else:
              embed.add_field(name="__**User Badges**__", value="None", inline=False)

            # Bot Badges
            embed.add_field(name="__**Bot Badges**__", value="No bot badges", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author} | Nitro badge if banner/animated avatar; Booster badge if boosting a mutual guild with bot.", icon_url=ctx.author.avatar.url
                               if ctx.author.avatar else ctx.author.default_avatar.url)

            await ctx.send(view = embed_to_view(embed))
            await processing_message.delete()

