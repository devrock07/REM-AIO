from utils import emojis

import discord
from discord.ext import commands
from discord import ui, ButtonStyle, SelectOption
import requests
import asyncio
from utils.Tools import *
from utils.cv2_compat import embed_to_view, embeds_to_view

class MapView(ui.View):
    def __init__(self, bot, location, ctx):
        super().__init__(timeout=None)
        self.bot = bot
        self.location = location
        self.ctx = ctx
        self.zoom_level = 14
        self.map_style = 'map'
        self.map_size = '1200,900'
        self.coordinates = self.get_coordinates(location)
        self.latitude, self.longitude = None, None
        if self.coordinates != (None, None):
            self.latitude, self.longitude = float(self.coordinates[0]), float(self.coordinates[1])
        self.update_map()

        self.add_item(MapStyleSelect(self))
        self.add_item(MapSizeSelect(self))

    def get_coordinates(self, location):
        
        try:
            headers = {'User-Agent': 'REM ALL IN ONE BOT'}
            response = requests.get(f'https://nominatim.openstreetmap.org/search?q={location}&format=json', headers=headers)
            response.raise_for_status()
            data = response.json()[0]
            return data['lat'], data['lon']
        except (requests.RequestException, IndexError) as e:
            print(f"Failed to get coordinates: {e}")
            return None, None

    def update_map(self):
        if self.latitude is None or self.longitude is None:
            return
        self.map_url = f'https://www.mapquestapi.com/staticmap/v5/map?key=E2SaL3qiTpXQ43nxZFBp0wzEnBI6pqbG&center={self.latitude},{self.longitude}&zoom={self.zoom_level}&size={self.map_size}&type={self.map_style}'

    async def update_embed(self, interaction: discord.Interaction):
        if self.latitude is None or self.longitude is None:
            await interaction.response.send_message("Failed to retrieve map data. Please try again.", ephemeral=True)
            return
        embed = discord.Embed(title=f" Map of {self.location}", color=0x000000)
        embed.add_field(name="🌐  Open in Webpage", value=f"➜  **[Click Here](https://www.openstreetmap.org/?mlat={self.latitude}&mlon={self.longitude}&zoom={self.zoom_level})**")
        embed.add_field(name="🔍  Current Zoom Level", value=f"➜  {str(self.zoom_level)}")
        embed.add_field(name="🗺️  Map Style", value=f"➜  {self.map_style}")
        embed.add_field(name="📏  Map Size", value=f"➜  {self.map_size}")
        embed.add_field(name="📍 Current Coordinates", value=f"➜  {self.latitude}, {self.longitude}")
        embed.set_image(url=self.map_url)
        embed.set_footer(text="Made by REM ALL IN ONE BOT")
        try:
            await interaction.message.edit(view = embed_to_view(embed, view = self))
        except Exception as e:
            await interaction.response.send_message(f"Error updating message: {e}", ephemeral=True)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                view = embed_to_view(discord.Embed(description="Sorry only the requested author can control this", color=0x000000)), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="", emoji="arrow_left", style=ButtonStyle.secondary)
    async def move_left(self, interaction: discord.Interaction, button: ui.Button):
        if self.longitude is not None:
            self.longitude -= 0.01
            self.update_map()
            await self.update_embed(interaction)
            await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Moved left.")), ephemeral=True)
    
    @discord.ui.button(label="",  emoji=":arrow_up:", style=ButtonStyle.secondary)
    async def move_up(self, interaction: discord.Interaction, button: ui.Button):
        if self.latitude is not None:
            self.latitude += 0.01
            self.update_map()
            await self.update_embed(interaction)
            await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Moved up.")), ephemeral=True)

    @discord.ui.button(label="", emoji=f"{emojis.DELETE}", style=ButtonStyle.danger)
    async def delete_embed(self, interaction: discord.Interaction, button: ui.Button):
        try:
            await interaction.message.delete()
        except Exception as e:
            await interaction.response.send_message(f"Error deleting message: {e}", ephemeral=True)


    @discord.ui.button(label="", emoji=":arrow_down:", style=ButtonStyle.secondary)
    async def move_down(self, interaction: discord.Interaction, button: ui.Button):
        if self.latitude is not None:
            self.latitude -= 0.01
            self.update_map()
            await self.update_embed(interaction)
            await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Moved down.")), ephemeral=True)

    @discord.ui.button(label="", emoji=":arrow_right:", style=ButtonStyle.secondary)
    async def move_right(self, interaction: discord.Interaction, button: ui.Button):
        if self.longitude is not None:
            self.longitude += 0.01
            self.update_map()
            await self.update_embed(interaction)
            await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Moved right.")), ephemeral=True)
    
    @discord.ui.button(label="Zoom In", style=ButtonStyle.primary)
    async def zoom_in(self, interaction: discord.Interaction, button: ui.Button):
        print("Zooming in")
        self.zoom_level = min(self.zoom_level + 1, 18)
        self.update_map()
        await self.update_embed(interaction)
        await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Zoomed in.")), ephemeral=True)

    @discord.ui.button(label="Zoom Out", style=ButtonStyle.primary)
    async def zoom_out(self, interaction: discord.Interaction, button: ui.Button):
        print("Zooming out")
        self.zoom_level = max(self.zoom_level - 1, 0)
        self.update_map()
        await self.update_embed(interaction)
        await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Zoomed Out.")), ephemeral=True)


    @discord.ui.button(label="Enter Coordinates", style=ButtonStyle.primary)
    async def enter_coordinates(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Please enter the coordinates (latitude, longitude):", ephemeral=True)

        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel

        try:
            coords_msg = await self.bot.wait_for('message', check=check, timeout=60)
            coords = coords_msg.content.split(',')
            if len(coords) == 2:
                self.latitude, self.longitude = float(coords[0].strip()), float(coords[1].strip())
                self.update_map()
                await self.update_embed(interaction)
                await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Coordinates updated.")), ephemeral=True)
            else:
                await interaction.response.send_message("Invalid coordinates format. Please enter in the format 'latitude, longitude'.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Please try again.", ephemeral=True)

    @discord.ui.button(label="Enter Address", style=ButtonStyle.success)
    async def enter_address(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Please enter the address:", ephemeral=True)


        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel

        try:
            address_msg = await self.bot.wait_for('message', check=check, timeout=60)
            address = address_msg.content
            self.coordinates = self.get_coordinates(address)
            if self.coordinates == (None, None):
                await interaction.response.send_message("Failed to retrieve coordinates for the address. Please try again.", ephemeral=True)
            else:
                self.latitude, self.longitude = float(self.coordinates[0]), float(self.coordinates[1])
                self.update_map()
                await self.update_embed(interaction)
                await interaction.response.send_message(view = embed_to_view(discord.Embed(description="Address updated.")), ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Please try again.", ephemeral=True)


class MapStyleSelect(ui.Select):
    def __init__(self, map_view):
        super().__init__(placeholder='Select Map Style')
        self.map_view = map_view  
        options = [
            SelectOption(label='Map', value='map'),
            SelectOption(label='Satellite', value='sat'),
            SelectOption(label='Hybrid', value='hyb'),
            SelectOption(label='Light', value='light'),
            SelectOption(label='Dark', value='dark'),
        ]
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        print(f"Changing map style to {self.values[0]}")
        self.map_view.map_style = self.values[0]
        self.map_view.update_map()
        await self.map_view.update_embed(interaction)
        await interaction.response.send_message("Map style updated successfully.", ephemeral=True)

class MapSizeSelect(ui.Select):
    def __init__(self, map_view):
        super().__init__(placeholder='Select Map Size')
        self.map_view = map_view  
        options = [
            SelectOption(label='400x300', value='400,300'),
            SelectOption(label='800x600', value='800,600'),
            SelectOption(label='1200x900', value='1200,900')
        ]
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        print(f"Changing map size to {self.values[0]}")
        self.map_view.map_size = self.values[0]
        self.map_view.update_map()
        await self.map_view.update_embed(interaction)
        await interaction.response.send_message("Map size updated successfully.", ephemeral=True)


class Map(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="map", help="Shows a map of a location", usage="<location>", description="Shows a map of a location")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def map(self, ctx, *, location: str):
        view = MapView(self.bot, location, ctx)
        if view.coordinates == (None, None):
            await ctx.send("Failed to retrieve coordinates for the location. Please try again.")
            return
        embed = discord.Embed(title=f" Map of {location}", color=0x000000)
        embed.add_field(name="🌐  Open in Webpage", value=f"➜  **[Click Here](https://www.openstreetmap.org/?mlat={view.coordinates[0]}&mlon={view.coordinates[1]}&zoom={view.zoom_level})**")
        embed.add_field(name="🔍  Current Zoom Level", value=f"➜  {str(view.zoom_level)}")
        embed.add_field(name="🗺️  Map Style", value=f"➜  {view.map_style}")
        embed.add_field(name="📏  Map Size", value=f"➜  {view.map_size}")
        embed.add_field(name="📍 Current Coordinates", value=f"➜  {view.coordinates[0]}, {view.coordinates[1]}")
        embed.set_image(url=view.map_url)
        embed.set_footer(text=f"Requested By {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(view = embed_to_view(embed, view = view))




    """
    @Author: Sonu Jana
        + Discord: me.sonu
        + Community: https://discord.gg/codexdev (REM ALL IN ONE BOT)
        + for any queries reach out Community or DM me.
    """
