from utils import emojis

from discord.ext import commands
from core import Rem, Cog
import discord
import logging
from discord.ui import View, Button
from utils.config import GUILD_JOIN_LOG_CHANNEL_ID, GUILD_LEAVE_LOG_CHANNEL_ID, PREFIX, serverLink
from utils.cv2_compat import embed_to_view, embeds_to_view

log = logging.getLogger(__name__)


class Guild(Cog):
    def __init__(self, client: Rem):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        try:
            rope = [inv for inv in await guild.invites() if inv.max_age == 0 and inv.max_uses == 0]

            if GUILD_JOIN_LOG_CHANNEL_ID:
                me = self.client.get_channel(GUILD_JOIN_LOG_CHANNEL_ID)
                if me is None:
                    log.error("Guild join log channel %s not found.", GUILD_JOIN_LOG_CHANNEL_ID)
                else:
                    channels = len(set(self.client.get_all_channels()))
                    embed = discord.Embed(title=f"{guild.name}'s Information", color=0x000000)
                    embed.set_author(name="Guild Joined")
                    embed.set_footer(text=f"Added in {guild.name}")
                    embed.add_field(
                        name="**__About__**",
                        value=(
                            f"**Name : ** {guild.name}\n**ID :** {guild.id}\n"
                            f"**Owner {emojis.OWNER} :** {guild.owner} (<@{guild.owner_id}>)\n"
                            f"**Created At : **{guild.created_at.month}/{guild.created_at.day}/{guild.created_at.year}\n"
                            f"**Members :** {len(guild.members)}"
                        ),
                        inline=False,
                    )
                    embed.add_field(name="**__Description__**", value=f"{guild.description}", inline=False)
                    embed.add_field(
                        name="**__Members__**",
                        value=(
                            f"{emojis.RIVERSE_FUN} Members : {len(guild.members)}\n"
                            f" {emojis.USER} Humans : {len(list(filter(lambda m: not m.bot, guild.members)))}\n"
                            f"{emojis.ICONS_BOT} Bots : {len(list(filter(lambda m: m.bot, guild.members)))}"
                        ),
                        inline=False,
                    )
                    embed.add_field(
                        name="**__Channels__**",
                        value=(
                            f"Categories : {len(guild.categories)}\n"
                            f"Text Channels : {len(guild.text_channels)}\n"
                            f"Voice Channels : {len(guild.voice_channels)}\n"
                            f"Threads : {len(guild.threads)}"
                        ),
                        inline=False,
                    )
                    embed.add_field(
                        name="__Bot Stats:__",
                        value=f"Servers: `{len(self.client.guilds)}`\nUsers: `{len(self.client.users)}`\nChannels: `{channels}`",
                        inline=False,
                    )
                    if guild.icon is not None:
                        embed.set_thumbnail(url=guild.icon.url)
                    embed.timestamp = discord.utils.utcnow()
                    await me.send(
                        f"{rope[0]}" if rope else "No Pre-Made Invite Found",
                        view=embed_to_view(embed),
                    )

            if not guild.chunked:
                await guild.chunk()

            embed = discord.Embed(
                description=(
                    f"{emojis.ICONARROWRIGHT} Prefix For This Server is `{PREFIX}`\n"
                    f"{emojis.ICONARROWRIGHT} Get Started with `{PREFIX}help`\n"
                    f"{emojis.ICONARROWRIGHT} For detailed guides, FAQ & information, visit our **[Support Server]({serverLink})**"
                ),
                color=0xFF0000,
            )
            embed.set_author(name="Thanks for adding me!", icon_url=guild.me.display_avatar.url)
            embed.set_footer(text="Powered by REM ALL IN ONE BOT")
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            support = Button(label="Support", style=discord.ButtonStyle.link, url=serverLink)
            view = View()
            view.add_item(support)

            channel = discord.utils.get(guild.text_channels, name="general")
            if not channel:
                channels = [
                    ch for ch in guild.text_channels
                    if ch.permissions_for(guild.me).send_messages
                ]
                channel = channels[0] if channels else None

            if channel is None:
                log.warning("No sendable channel found in guild: %s", guild.name)
                return

            await channel.send(view=embed_to_view(embed, view=view))

        except Exception:
            log.exception("Error in on_guild_join for guild %s", guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if not GUILD_LEAVE_LOG_CHANNEL_ID:
            return
        try:
            idk = self.client.get_channel(GUILD_LEAVE_LOG_CHANNEL_ID)
            if idk is None:
                log.error("Guild leave log channel %s not found.", GUILD_LEAVE_LOG_CHANNEL_ID)
                return

            channels = len(set(self.client.get_all_channels()))
            embed = discord.Embed(title=f"{guild.name}'s Information", color=0x000000)
            embed.set_author(name="Guild Removed")
            embed.set_footer(text=f"{guild.name}")
            embed.add_field(
                name="**__About__**",
                value=(
                    f"**Name : ** {guild.name}\n**ID :** {guild.id}\n"
                    f"**Owner {emojis.AXON_OWNER} :** {guild.owner} (<@{guild.owner_id}>)\n"
                    f"**Created At : **{guild.created_at.month}/{guild.created_at.day}/{guild.created_at.year}\n"
                    f"**Members :** {len(guild.members)}"
                ),
                inline=False,
            )
            embed.add_field(name="**__Description__**", value=f"{guild.description}", inline=False)
            embed.add_field(
                name="**__Members__**",
                value=(
                    f"Members : {len(guild.members)}\n"
                    f"Humans : {len(list(filter(lambda m: not m.bot, guild.members)))}\n"
                    f"Bots : {len(list(filter(lambda m: m.bot, guild.members)))}"
                ),
                inline=False,
            )
            embed.add_field(
                name="**__Channels__**",
                value=(
                    f"Categories : {len(guild.categories)}\n"
                    f"Text Channels : {len(guild.text_channels)}\n"
                    f"Voice Channels : {len(guild.voice_channels)}\n"
                    f"Threads : {len(guild.threads)}"
                ),
                inline=False,
            )
            embed.add_field(
                name="__Bot Stats:__",
                value=f"Servers: `{len(self.client.guilds)}`\nUsers: `{len(self.client.users)}`\nChannels: `{channels}`",
                inline=False,
            )
            if guild.icon is not None:
                embed.set_thumbnail(url=guild.icon.url)
            embed.timestamp = discord.utils.utcnow()
            await idk.send(view=embed_to_view(embed))
        except Exception:
            log.exception("Error in on_guild_remove for guild %s", guild.id)