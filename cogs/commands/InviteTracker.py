import asyncio
import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timezone
from utils.cv2_compat import embed_to_view, embeds_to_view

DB_FILE = "db/invite_tracker.db"

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.init_db())
        self.guild_invites = {}

    async def init_db(self):
        await self.bot.wait_until_ready()
        with sqlite3.connect(DB_FILE) as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS invites (
                guild_id TEXT,
                inviter_id TEXT,
                invite_code TEXT,
                uses INTEGER DEFAULT 0,
                PRIMARY KEY(guild_id, invite_code)
            );

            CREATE TABLE IF NOT EXISTS invite_stats (
                guild_id TEXT,
                user_id TEXT PRIMARY KEY,
                invites INTEGER DEFAULT 0,
                fake INTEGER DEFAULT 0,
                leaves INTEGER DEFAULT 0,
                rejoins INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS invite_settings (
                guild_id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0
            );
            """)
            conn.commit()

        for guild in self.bot.guilds:
            try:
                self.guild_invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                self.guild_invites[guild.id] = []

    async def is_enabled(self, guild_id):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("SELECT enabled FROM invite_settings WHERE guild_id = ?", (str(guild_id),))
            row = cursor.fetchone()
            return bool(row[0]) if row else False

    async def set_enabled(self, guild_id, enabled: bool):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT INTO invite_settings (guild_id, enabled) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET enabled=excluded.enabled
            """, (str(guild_id), int(enabled)))
            conn.commit()

    @commands.command(name="Invite enable")
    @commands.has_permissions(administrator=True)
    async def inviteenable(self, ctx):
        await self.set_enabled(ctx.guild.id, True)
        await ctx.reply("✅ Invite tracking **enabled** for this server.")

    @commands.command(name="Invite disable")
    @commands.has_permissions(administrator=True)
    async def invitedisable(self, ctx):
        await self.set_enabled(ctx.guild.id, False)
        await ctx.reply("✅ Invite tracking **disabled** for this server.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            self.guild_invites[guild.id] = await guild.invites()
        except discord.Forbidden:
            self.guild_invites[guild.id] = []

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        invites = self.guild_invites.get(invite.guild.id, [])
        invites.append(invite)
        self.guild_invites[invite.guild.id] = invites

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        invites = self.guild_invites.get(invite.guild.id, [])
        self.guild_invites[invite.guild.id] = [i for i in invites if i.code != invite.code]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not await self.is_enabled(member.guild.id):
            return

        guild = member.guild
        before_invites = self.guild_invites.get(guild.id, [])
        try:
            after_invites = await guild.invites()
        except discord.Forbidden:
            return

        self.guild_invites[guild.id] = after_invites
        used_invite = None

        for before in before_invites:
            after = discord.utils.get(after_invites, code=before.code)
            if after and after.uses > before.uses:
                used_invite = after
                break

        if not used_invite:
            return

        inviter = used_invite.inviter
        now = datetime.now(timezone.utc)
        acc_age = now - member.created_at

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO invites (guild_id, inviter_id, invite_code, uses)
                VALUES (?, ?, ?, 0)
            """, (str(guild.id), str(inviter.id), used_invite.code))
            conn.execute("""
                UPDATE invites SET uses = uses + 1 WHERE guild_id = ? AND invite_code = ?
            """, (str(guild.id), used_invite.code))
            conn.execute("""
                INSERT OR IGNORE INTO invite_stats (guild_id, user_id)
                VALUES (?, ?)
            """, (str(guild.id), str(inviter.id)))

            if acc_age.total_seconds() < 86400:
                conn.execute("""
                    UPDATE invite_stats SET fake = fake + 1 WHERE guild_id = ? AND user_id = ?
                """, (str(guild.id), str(inviter.id)))
            else:
                conn.execute("""
                    UPDATE invite_stats SET invites = invites + 1 WHERE guild_id = ? AND user_id = ?
                """, (str(guild.id), str(inviter.id)))
            conn.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not await self.is_enabled(member.guild.id):
            return
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                UPDATE invite_stats SET leaves = leaves + 1 WHERE guild_id = ? AND user_id = ?
            """, (str(member.guild.id), str(member.id)))
            conn.commit()

    async def get_stats(self, guild_id, user_id):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("""
                SELECT invites, fake, leaves, rejoins FROM invite_stats WHERE guild_id = ? AND user_id = ?
            """, (str(guild_id), str(user_id)))
            return cursor.fetchone() or (0, 0, 0, 0)

    @commands.command(name="invites")
    async def invites(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        if not await self.is_enabled(ctx.guild.id):
            return await ctx.reply("❌ Invite tracking is disabled.")

        invites, fake, leaves, rejoins = await self.get_stats(ctx.guild.id, member.id)
        embed = discord.Embed(title=f"📨 Invite Stats: {member}", color=discord.Color.blurple())
        embed.add_field(name="Total Invites", value=invites, inline=True)
        embed.add_field(name="Fake", value=fake, inline=True)
        embed.add_field(name="Leaves", value=leaves, inline=True)
        embed.add_field(name="Rejoins", value=rejoins, inline=True)
        await ctx.reply(view = embed_to_view(embed))

    @commands.command(name="inviteleaderboard")
    async def inviteleaderboard(self, ctx):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("""
                SELECT user_id, invites FROM invite_stats WHERE guild_id = ? ORDER BY invites DESC LIMIT 10
            """, (str(ctx.guild.id),))
            rows = cursor.fetchall()

        embed = discord.Embed(title="🏆 Invite Leaderboard", color=discord.Color.gold())
        for i, (user_id, count) in enumerate(rows, start=1):
            user = ctx.guild.get_member(int(user_id))
            name = user.name if user else f"<@{user_id}>"
            embed.add_field(name=f"#{i} {name}", value=f"{count} invites", inline=False)

        await ctx.reply(view = embed_to_view(embed))

    @commands.command(name="resetinvites")
    @commands.has_permissions(administrator=True)
    async def resetinvites(self, ctx, member: discord.Member):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM invite_stats WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(member.id)))
            conn.commit()
        await ctx.reply(f"✅ Reset invites for {member.mention}")

    @commands.command(name="addinvites")
    @commands.has_permissions(administrator=True)
    async def addinvites(self, ctx, member: discord.Member, amount: int):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO invite_stats (guild_id, user_id, invites)
                VALUES (?, ?, 0)
            """, (str(ctx.guild.id), str(member.id)))
            conn.execute("""
                UPDATE invite_stats SET invites = invites + ? WHERE guild_id = ? AND user_id = ?
            """, (amount, str(ctx.guild.id), str(member.id)))
            conn.commit()
        await ctx.reply(f"✅ Added {amount} invites to {member.mention}")

    @commands.command(name="removeinvites")
    @commands.has_permissions(administrator=True)
    async def removeinvites(self, ctx, member: discord.Member, amount: int):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO invite_stats (guild_id, user_id, invites)
                VALUES (?, ?, 0)
            """, (str(ctx.guild.id), str(member.id)))
            conn.execute("""
                UPDATE invite_stats SET invites = MAX(invites - ?, 0) WHERE guild_id = ? AND user_id = ?
            """, (amount, str(ctx.guild.id), str(member.id)))
            conn.commit()
        await ctx.reply(f"✅ Removed {amount} invites from {member.mention}")

    @commands.command(name="resetserverinvites")
    @commands.has_permissions(administrator=True)
    async def resetserverinvites(self, ctx):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM invite_stats WHERE guild_id = ?", (str(ctx.guild.id),))
            conn.execute("DELETE FROM invites WHERE guild_id = ?", (str(ctx.guild.id),))
            conn.commit()
        await ctx.reply("✅ Reset all invite stats for this server.")

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
