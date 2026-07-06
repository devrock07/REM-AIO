from utils import emojis

import os
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
from utils.Tools import *
import re
from utils.cv2_compat import embed_to_view, embeds_to_view

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = bot

    @commands.hybrid_command(name="embed")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 7, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def _embed(self, ctx):
        msgx = "Example embed. You can customize everything.\n*Respond within 30 seconds to avoid time out.*"
        embed = discord.Embed(title="Edit your Embed!", 
                              description="- Select Options what to edit from the below select menu.\n\nMust edit embed title & description to remove these instructions.", 
                              color=0x000000)
        interaction_user = ctx.author

        def chk(m):
            return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id and not m.author.bot

        async def select_callback(interaction):
            if interaction.user.id != interaction_user.id:
                await interaction.response.send_message("Uh oh! That message doesn't belong to you.\nYou must run this command to interact with it.", ephemeral=True)
                return

            await interaction.response.defer()

            value = select.values[0]

            if value == "Title":
                await ctx.send("Please enter the **Title of the embed**:")
                try:
                    tit = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    embed.title = tit.content
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Description":
                await ctx.send("Please enter the **Description of the embed**:")
                try:
                    desc = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    embed.description = desc.content
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Color":
                await ctx.send("Please enter the color of the embed as a hexadecimal value (e.g., #FF0000 for red):")
                try:
                    col = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    color = discord.Colour(int(col.content.strip("#"), 16))  # hex se int
                    embed.color = color
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except ValueError:
                    await ctx.send("Invalid color format. Please retry with a valid hexadecimal color value.")
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Thumbnail":
                await ctx.send("Please enter the **URL of the thumbnail:**")
                try:
                    thumb = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    if not thumb.content.startswith("http"):
                        raise ValueError("Invalid URL format")
                    embed.set_thumbnail(url=thumb.content)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except ValueError as e:
                    await ctx.send(str(e))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Image":
                await ctx.send("Please enter the **URL of the image:**")
                try:
                    img = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    if not img.content.startswith("http"):
                        raise ValueError("Invalid URL format")
                    embed.set_image(url=img.content)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except ValueError as e:
                    await ctx.send(str(e))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Footer Text":
                await ctx.send("Please enter the **text of the footer:**")
                try:
                    foot = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    embed.set_footer(text=foot.content)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Footer Icon":
                await ctx.send("Please enter the **URL of the footer icon:**")
                try:
                    foot_icon = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    if not foot_icon.content.startswith("http"):
                        raise ValueError("Invalid URL format")
                    embed.set_footer(text=embed.footer.text or "Footer", icon_url=foot_icon.content)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except ValueError as e:
                    await ctx.send(str(e))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Author Text":
                await ctx.send("Please enter the **author text:**")
                try:
                    auth_text = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    embed.set_author(name=auth_text.content)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Author Icon":
                await ctx.send("Please enter the **URL of the author icon:**")
                try:
                    auth_icon = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    if not auth_icon.content.startswith("http"):
                        raise ValueError("Invalid URL format")
                    embed.set_author(name=embed.author.name or "Author", icon_url=auth_icon.content)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except ValueError as e:
                    await ctx.send(str(e))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")
            elif value == "Add Field":
                await ctx.send("**Enter Field title:**")
                try:
                    name = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    await ctx.send("**Enter Field value:**")
                    value = await ctx.bot.wait_for("message", timeout=30, check=chk)
                    embed.add_field(name=name.content, value=value.content, inline=False)
                    await msg.edit(content=msgx, view = embed_to_view(embed))
                except asyncio.TimeoutError:
                    await ctx.send("Timed Out")

        select = Select(
            placeholder="Choose an option to edit the Embed",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Title", description="Edit the title of the embed"),
                discord.SelectOption(label="Description", description="Edit the description of the embed"),
                discord.SelectOption(label="Add Field", description="Add a field to the embed"),
                discord.SelectOption(label="Color", description="Edit the color of the embed"),
                discord.SelectOption(label="Thumbnail", description="Edit the thumbnail of the embed"),
                discord.SelectOption(label="Image", description="Edit the image of the embed"),
                discord.SelectOption(label="Footer Text", description="Edit the footer text of the embed"),
                discord.SelectOption(label="Footer Icon", description="Edit the footer icon of the embed"),
                discord.SelectOption(label="Author Text", description="Edit the author text of the embed"),
                discord.SelectOption(label="Author Icon", description="Edit the author icon of the embed"),
                
            ]
        )
        select.callback = select_callback

        async def send_callback(interaction):
            if interaction.user.id != interaction_user.id:
                await interaction.response.send_message("Uh oh! That message doesn't belong to you.\nYou must run this command to interact with it.", ephemeral=True)
                return
            await interaction.response.defer()
            await ctx.send("Please mention the **channel** where you want to send this embed:")
            try:
                tit = await ctx.bot.wait_for("message", timeout=30, check=chk)
                chnl = tit.channel_mentions[0]
                await chnl.send(view = embed_to_view(embed))
                await ctx.send(view = embed_to_view(discord.Embed(title=f"{emojis.TICK} Success",
                                                   description="Sent the embed message to the mentioned channel",
                                                   color=0x000000)))
            except asyncio.TimeoutError:
                await ctx.send("Timed Out")

        async def delete_callback(interaction):
            if interaction.user.id != interaction_user.id:
                await interaction.response.send_message("Uh oh! That message doesn't belong to you.\nYou must run this command to interact with it.", ephemeral=True)
                return
            await interaction.response.defer()
            await msg.delete()

        button_send = Button(label="Send Embed",  emoji=f"{emojis.TICK}", style=discord.ButtonStyle.success)
        button_send.callback = send_callback

        button_delete = Button(label="Cancel Setup",  emoji=f"{emojis.CROSSICON}", style=discord.ButtonStyle.danger)
        button_delete.callback = delete_callback

        view = View(timeout=180)
        view.add_item(select)
        view.add_item(button_send)
        view.add_item(button_delete)

        msg = await ctx.send(view = embed_to_view(embed, view = view), content=msgx, )
        ctx.message = msg



"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
    + for any queries reach out support or DM me.
"""