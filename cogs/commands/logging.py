import discord
from discord.ext import commands
import sqlite3
from datetime import datetime

DB_FILE = "logging.db"

LOG_CHANNELS = {
    "channel-logs": "channel",
    "mod-logs": "mod",
    "messgae-logs": "message",
    "role-logs": "role",
    "guild-logs": "guild",
    "invite-logs": "invite",
    "webhook-logs": "webhook",
    "emoji-logs": "emoji"
}

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = DB_FILE
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log_channels (
                    guild_id INTEGER,
                    log_type TEXT,
                    channel_id INTEGER
                )
            """)

    def set_log_channel(self, guild_id, log_type, channel_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "REPLACE INTO log_channels (guild_id, log_type, channel_id) VALUES (?, ?, ?)",
                (guild_id, log_type, channel_id)
            )

    def get_log_channel(self, guild_id, log_type):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT channel_id FROM log_channels WHERE guild_id = ? AND log_type = ?",
                (guild_id, log_type)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    async def send_log(self, guild, log_type, embed):
        embed.timestamp = datetime.utcnow()
        channel_id = self.get_log_channel(guild.id, log_type)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    @commands.command(name="loggingsetup")
    @commands.has_permissions(administrator=True)
    async def setlogsetup(self, ctx):
        """Creates Axon-logging category and log channels with private permissions"""
        guild = ctx.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        category = discord.utils.get(guild.categories, name="Axon-logging")
        if not category:
            category = await guild.create_category("Axon-logging", overwrites=overwrites)

        for name, log_type in LOG_CHANNELS.items():
            channel = discord.utils.get(guild.text_channels, name=name)
            if not channel:
                channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites)
            self.set_log_channel(guild.id, log_type, channel.id)

        await ctx.send("✅ Logging channels created privately under 'Axon-logging'.")

    @commands.command(name="removelogs")
    @commands.has_permissions(administrator=True)
    async def removelogs(self, ctx):
        """Removes Axon-logging channels and logging DB config"""
        guild = ctx.guild

        # Remove DB entries
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM log_channels WHERE guild_id = ?", (guild.id,))
            conn.commit()

        # Delete channels and category
        category = discord.utils.get(guild.categories, name="Axon-logging")
        if category:
            for channel in category.channels:
                await channel.delete()
            await category.delete()

        await ctx.send("🗑️ Logging channels and category 'Axon-logging' have been removed.")

    # === Events ===

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild and not message.author.bot:
            embed = discord.Embed(title="🗑️ Message Deleted", color=discord.Color.red())
            embed.add_field(name="User", value=message.author.mention)
            embed.add_field(name="Channel", value=message.channel.mention)
            embed.add_field(name="Content", value=message.content or "None", inline=False)
            await self.send_log(message.guild, "message", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild and not before.author.bot and before.content != after.content:
            embed = discord.Embed(title="✏️ Message Edited", color=discord.Color.orange())
            embed.add_field(name="User", value=before.author.mention)
            embed.add_field(name="Channel", value=before.channel.mention)
            embed.add_field(name="Before", value=before.content or "None", inline=False)
            embed.add_field(name="After", value=after.content or "None", inline=False)
            await self.send_log(before.guild, "message", embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=str(user))
        await self.send_log(guild, "mod", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(title="⚖️ Member Unbanned", color=discord.Color.green())
        embed.add_field(name="User", value=str(user))
        await self.send_log(guild, "mod", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="📁 Channel Created", color=discord.Color.green())
        embed.add_field(name="Channel", value=channel.name)
        await self.send_log(channel.guild, "channel", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="🗑️ Channel Deleted", color=discord.Color.red())
        embed.add_field(name="Channel", value=channel.name)
        await self.send_log(channel.guild, "channel", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title="➕ Role Created", color=discord.Color.green())
        embed.add_field(name="Role", value=role.name)
        await self.send_log(role.guild, "role", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title="➖ Role Deleted", color=discord.Color.red())
        embed.add_field(name="Role", value=role.name)
        await self.send_log(role.guild, "role", embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = discord.Embed(title="📨 Invite Created", color=discord.Color.green())
        embed.add_field(name="Code", value=invite.code)
        embed.add_field(name="Channel", value=invite.channel.mention)
        if invite.inviter:
            embed.add_field(name="Created By", value=invite.inviter.mention)
        await self.send_log(invite.guild, "invite", embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = discord.Embed(title="❌ Invite Deleted", color=discord.Color.red())
        embed.add_field(name="Code", value=invite.code)
        embed.add_field(name="Channel", value=invite.channel.mention)
        await self.send_log(invite.guild, "invite", embed)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        embed = discord.Embed(title="🔄 Webhook Updated", color=discord.Color.blurple())
        embed.add_field(name="Channel", value=channel.mention)
        await self.send_log(channel.guild, "webhook", embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]

        for emoji in added:
            embed = discord.Embed(title="✨ Emoji Created", color=discord.Color.green())
            embed.add_field(name="Name", value=emoji.name)
            embed.set_thumbnail(url=emoji.url)
            await self.send_log(guild, "emoji", embed)

        for emoji in removed:
            embed = discord.Embed(title="❌ Emoji Deleted", color=discord.Color.red())
            embed.add_field(name="Name", value=emoji.name)
            await self.send_log(guild, "emoji", embed)

# Setup
async def setup(bot):
    await bot.add_cog(Logging(bot))
