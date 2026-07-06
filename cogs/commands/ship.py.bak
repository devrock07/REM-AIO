import os
import io
import random
import discord
import datetime
import requests
from discord.ext import commands
from discord.ext.commands import errors
from PIL import Image, ImageFont, ImageDraw
from utils.Tools import *

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.special_users = [767979794411028491,]

    @commands.hybrid_command(pass_context=True, help="Ship two users together.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ship(self, ctx, user1: discord.Member = None, user2: discord.Member = None):
        

        if user1 is None:  
            user1 = ctx.author
            guild = ctx.guild
            members = guild.members
            user2 = random.choice(members)
        elif user2 is None:  
            user2 = user1
            user1 = ctx.author

        author_id = float(user1.id)
        user_id = float(user2.id)

        if user1.id in self.special_users and user2.id in self.special_users:
            rate = 100
        else:
            now = datetime.datetime.now()
            day_seed = (now.day + now.month + now.year) / 3
            seed = (author_id + user_id) / day_seed
            random.seed(seed)
            rate = random.randint(1, 99)

        user_avatar = await get_avatar(user2)
        author_avatar = await get_avatar(user1)

        if user_avatar and author_avatar:
            self.make_image(author_avatar, user_avatar, user1.name, user2.name, rate)
            await self.img_ship(ctx, user1.mention, user2.mention, rate)
        else:
            await self.text_ship(ctx, user1.mention, user2.mention, rate)

    async def img_ship(self, ctx, author, user, rate):
        msg = "**Love rate between {0} & {1} is:**\n`{3}` {2}%"
        progress_bar = self.create_progress_bar(rate)
        try:
            b = discord.Embed(color=discord.Color(0xeb1818), description=msg.format(author, user, rate, progress_bar))
            f = discord.File("./data/ship/tmp_ship.png")
            b.set_image(url="attachment://tmp_ship.png")
            await ctx.send(file=f, embed=b)
        except errors.BadArgument:
            await ctx.send("Oops, something went wrong! Try again later!")

    def make_image(self, author_avatar, user_avatar, author, user, rate):
        red = (191, 15, 0, 255)
        white = (255, 255, 255, 255)
        blank = (255, 255, 255, 0)
        tmpl = Image.open("./data/ship/Template.png", "r").convert('RGBA')
        fill = Image.open("./data/ship/Tmpl_fill.png", "r").convert('RGBA')
        blank = Image.new('RGBA', tmpl.size, blank)
        fnt = ImageFont.truetype("./data/ship/font.ttf", 34)
        draw = ImageDraw.Draw(blank)
        author_avatar = author_avatar.resize((150, 150), Image.Resampling.LANCZOS)
        user_avatar = user_avatar.resize((150, 150), Image.Resampling.LANCZOS)
        tmpl.paste(author_avatar, (20, 50))
        tmpl.paste(user_avatar, (20, 312))
        offset = (100 - rate) * 2
        fill = fill.crop((0, offset, fill.width, fill.height))
        blank.paste(fill, (tmpl.width - fill.width - 1, 154 + offset))
        draw.text((20, 10), str(author), font=fnt, fill=red)
        draw.text((20, 460), str(user), font=fnt, fill=red)
        fnt = ImageFont.truetype("./data/ship/font.ttf", 80)
        draw.text((330, 192), str(rate) + "%", font=fnt, fill=white)
        tmpl = Image.alpha_composite(tmpl, blank)
        tmpl.save("./data/ship/tmp_ship.png", "PNG")

    async def text_ship(self, ctx, author, user, rate):
        msg = "**Love rate between {0} & {1} is:**\n`{3}` {2}%"
        progress_bar = self.create_progress_bar(rate)
        try:
            b = discord.Embed(color=discord.Color(0xeb1818), description=msg.format(author, user, rate, progress_bar))
            await ctx.send(embed=b)
        except errors.BadArgument:
            await ctx.send("Oops, something went wrong! Try again later!")

    def create_progress_bar(self, rate):
        filled_length = int(20 * rate // 100)
        bar = '█' * filled_length + ' ' * (20 - filled_length)
        return bar


async def get_avatar(user):
    try:
        user_url = user.display_avatar.replace(format="png").url
        response = requests.get(user_url + "?size=256")
        avatar = Image.open(io.BytesIO(response.content)).convert('RGBA')
        tmp = Image.new('RGBA', avatar.size, (255, 255, 255, 255))
        tmp = Image.alpha_composite(tmp, avatar)
        return tmp
    except Exception as e:
        print(f"Error fetching avatar: {e}")
        return None


def setup(bot):
    bot.add_cog(Ship(bot))




"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out support or DM me.
"""
