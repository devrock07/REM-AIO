import discord
from discord.ext import commands
import aiohttp
import os

PEXELS_API_KEY = "js24mfV1bCCvgV6KfnEFvo5UnCHnATFarFnAdDrpDbczl7f0yXpjDF8x"

class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_pexels_image(self, query):
        headers = {
            "Authorization": PEXELS_API_KEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.pexels.com/v1/search?query={query}&per_page=50", headers=headers) as resp:
                data = await resp.json()
                if data["photos"]:
                    image = random.choice(data["photos"])
                    return image["src"]["original"]
                return None

    async def fetch_waifu_image(self, category="waifu"):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.waifu.pics/sfw/{category}") as resp:
                data = await resp.json()
                return data["url"]

    @commands.command(name="boy")
    async def boy_image(self, ctx):
        url = await self.fetch_pexels_image("handsome boy")
        if url:
            await ctx.send(embed=discord.Embed(title="👦 Boy Pic").set_image(url=url))
        else:
            await ctx.send("No boy image found.")

    @commands.command(name="girl")
    async def girl_image(self, ctx):
        url = await self.fetch_pexels_image("beautiful girl")
        if url:
            await ctx.send(embed=discord.Embed(title="👧 Girl Pic").set_image(url=url))
        else:
            await ctx.send("No girl image found.")

    @commands.command(name="couple")
    async def couple_image(self, ctx):
        url = await self.fetch_pexels_image("romantic couple")
        if url:
            await ctx.send(embed=discord.Embed(title="💑 Couple Pic").set_image(url=url))
        else:
            await ctx.send("No couple image found.")

    @commands.command(name="anime")
    async def anime_image(self, ctx):
        url = await self.fetch_waifu_image("waifu")
        await ctx.send(embed=discord.Embed(title="🧚 Anime Waifu").set_image(url=url))

async def setup(bot):
    await bot.add_cog(ImageCommands(bot))
