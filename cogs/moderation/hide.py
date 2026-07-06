from utils import emojis

import discord
from discord.ext import commands
from discord import ui
from utils.cv2_compat import embed_to_view, embeds_to_view

class HideUnhideView(ui.View):
    def __init__(self, channel, author, ctx):
        super().__init__(timeout=120)
        self.channel = channel
        self.author = author
        self.ctx = ctx 
        self.message = None  

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            if item.label != "Delete":
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @ui.button(label="Unhide", style=discord.ButtonStyle.success)
    async def unhide(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.channel.set_permissions(interaction.guild.default_role, read_messages=True)
        await interaction.response.send_message(f"{self.channel.mention} has been unhidden.", ephemeral=True)

        embed = discord.Embed(
            description=f"{emojis.ICONS_CHANNEL} **Channel**: {self.channel.mention}\n{emojis.TICK} **Status**: Unhidden\n {emojis.COMMANDS}**Reason:** Unhide request by {self.author}",
            color=0x000000
        )
        embed.add_field(name=f"{emojis.U_ADMIN} **Moderator:**", value=self.ctx.author.mention, inline=False)
        embed.set_author(name=f"Successfully Unhidden {self.channel.name}")
        await self.message.edit(view = embed_to_view(embed, view = self))

        for item in self.children:
            if item.label != "Delete":
                item.disabled = True
        await self.message.edit(view=self)

    @ui.button(style=discord.ButtonStyle.gray, emoji=f"{emojis.DELETE}")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


class Hide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.from_rgb(0, 0, 0)

    @commands.hybrid_command(
        name="hide",
        help="Hides a channel from the default role (@everyone).",
        usage="hide <channel>",
        aliases=["hidechannel"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def hide_command(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel 
        if not channel.permissions_for(ctx.guild.default_role).read_messages:
            embed = discord.Embed(
                description=f"**{emojis.ICONS_CHANNEL} Channel**: {channel.mention}\n{emojis.TICK} **Status**: Already Hidden",
                color=self.color
            )
            embed.set_author(name=f"{channel.name} is Already Hidden")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            view = HideUnhideView(channel=channel, author=ctx.author, ctx=ctx) 
            message = await ctx.send(view = embed_to_view(embed, view = view))
            view.message = message
            return

        await channel.set_permissions(ctx.guild.default_role, read_messages=False)

        embed = discord.Embed(
            description=f"{emojis.ICONS_CHANNEL} **Channel**: {channel.mention}\n{emojis.TICK} **Status**: Hidden\n{emojis.COMMANDS} **Reason:** Hide request by {ctx.author}",
            color=self.color
        )
        embed.add_field(name=f"{emojis.U_ADMIN} **Moderator:**", value=ctx.author.mention, inline=False)
        embed.set_author(name=f"Successfully Hidden {channel.name}")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        view = HideUnhideView(channel=channel, author=ctx.author, ctx=ctx) 
        message = await ctx.send(view = embed_to_view(embed, view = view))
        view.message = message


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out Community or DM me.
"""