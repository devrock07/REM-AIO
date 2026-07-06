import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import random
import time
from utils.ai_utils import poly_image_gen, generate_image_prodia
from prodia.constants import Model
from utils.Tools import *

blacklisted_words = [
    "naked", "nude", "nudes", "teen", "gay", "lesbian", "porn", "xnxx",
    "bitch", "loli", "hentai", "explicit", "pornography", "adult", "XXX",
    "sex", "erotic", "dick", "vagina", "pussy", "gay", "lick", "creampie", "nsfw",
    "hardcore", "ass", "anal", "anus", "boobs", "tits", "cum", "cunnilingus", "squirt", "penis", "lick", "masturbate", "masturbation ", "orgasm", "orgy", "fap", "fapping", "fuck", "fucking", "handjob", "cowgirl", "doggystyle", "blowjob", "boobjob", "boobies", "horny", "nudity"
]

blocked=["minor", "minors", "kid", "kids", "child", "children", "baby", "babies", "toddler", "childporn", "todd", "underage"]

class CooldownManager:
    def __init__(self, rate: int, per: float):
        self.rate = rate
        self.per = per
        self.cooldowns = {}

    def check_cooldown(self, user_id: int):
        now = time.time()
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = [now]
            return None

        self.cooldowns[user_id] = [timestamp for timestamp in self.cooldowns[user_id] if now - timestamp < self.per]
        if len(self.cooldowns[user_id]) >= self.rate:
            retry_after = self.per - (now - self.cooldowns[user_id][0])
            return retry_after
        self.cooldowns[user_id].append(now)
        return None

cooldown_manager = CooldownManager(rate=1, per=60.0)

async def cooldown_check(interaction: discord.Interaction):
    retry_after = cooldown_manager.check_cooldown(interaction.user.id)
    if retry_after:
        await interaction.response.send_message(f"You are on cooldown. Try again in {retry_after:.2f} seconds.", ephemeral=True)
        return False
    return True





class AiStuffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @app_commands.command(name="imagine", description="Generate an image using AI")

    #@app_commands.check(blacklist_check())
    #@app_commands.check(ignore_check())
    #@app_commands.check(cooldown_check)
    @discord.app_commands.choices(
        model=[
            discord.app_commands.Choice(name='✨ Elldreth vivid mix (Landscapes, Stylized characters, nsfw)', value='ELLDRETHVIVIDMIX'),
            discord.app_commands.Choice(name='💪 Deliberate v2 (Anything you want, nsfw)', value='DELIBERATE'),
            discord.app_commands.Choice(name='🔮 Dreamshaper (HOLYSHIT this so good)', value='DREAMSHAPER_6'),
            discord.app_commands.Choice(name='🎼 Lyriel', value='LYRIEL_V16'),
            discord.app_commands.Choice(name='💥 Anything diffusion (Good for anime)', value='ANYTHING_V4'),
            discord.app_commands.Choice(name='🌅 Openjourney (Midjourney alternative)', value='OPENJOURNEY'),
            discord.app_commands.Choice(name='🏞️ Realistic (Lifelike pictures)', value='REALISTICVS_V20'),
            discord.app_commands.Choice(name='👨‍🎨 Portrait (For headshots I guess)', value='PORTRAIT'),
            discord.app_commands.Choice(name='🌟 Rev animated (Illustration, Anime)', value='REV_ANIMATED'),
            discord.app_commands.Choice(name='🤖 Analog', value='ANALOG'),
            discord.app_commands.Choice(name='🌌 AbyssOrangeMix', value='ABYSSORANGEMIX'),
            discord.app_commands.Choice(name='🌌 Dreamlike v1', value='DREAMLIKE_V1'),
            discord.app_commands.Choice(name='🌌 Dreamlike v2', value='DREAMLIKE_V2'),
            discord.app_commands.Choice(name='🌌 Dreamshaper 5', value='DREAMSHAPER_5'),
            discord.app_commands.Choice(name='🌌 MechaMix', value='MECHAMIX'),
            discord.app_commands.Choice(name='🌌 MeinaMix', value='MEINAMIX'),
            discord.app_commands.Choice(name='🌌 Stable Diffusion v14', value='SD_V14'),
            discord.app_commands.Choice(name='🌌 Stable Diffusion v15', value='SD_V15'),
            discord.app_commands.Choice(name="🌌 Shonin's Beautiful People", value='SBP'),
            discord.app_commands.Choice(name="🌌 TheAlly's Mix II", value='THEALLYSMIX'),
            discord.app_commands.Choice(name='🌌 Timeless', value='TIMELESS')
        ],
        sampler=[
            discord.app_commands.Choice(name='📏 Euler (Recommended)', value='Euler'),
            discord.app_commands.Choice(name='📏 Euler a', value='Euler a'),
            discord.app_commands.Choice(name='📐 Heun', value='Heun'),
            discord.app_commands.Choice(name='💥 DPM++ 2M Karras', value='DPM++ 2M Karras'),
            discord.app_commands.Choice(name='💥 DPM++ SDE Karras', value='DPM++ SDE Karras'),
            discord.app_commands.Choice(name='🔍 DDIM', value='DDIM')
        ]
    )
    @discord.app_commands.describe(
        prompt="Write an amazing prompt for an image",
        model="Model to generate image",
        sampler="Sampler for denoising",
        negative="Prompt that specifies what you do not want the model to generate",
    )
    async def imagine(self, interaction: discord.Interaction, prompt: str, model: discord.app_commands.Choice[str], sampler: discord.app_commands.Choice[str], negative: str = None, seed: int = None):
        retry_after = cooldown_manager.check_cooldown(interaction.user.id)
        if retry_after:
            await interaction.response.send_message(f"You are on cooldown. Try again in {retry_after:.2f} seconds.", ephemeral=True)
            return

        await interaction.response.defer()

        is_nsfw = any(word in prompt.lower() for word in blacklisted_words)

        is_child = any(word in prompt.lower() for word in blocked)

        if is_child:
            await interaction.followup.send("Child porn is not allowed as it violates Discord ToS. Please try again with a different peompt.")
            return

        if is_nsfw and not interaction.channel.nsfw:
            await interaction.followup.send("You can create NSFW images in NSFW channels only. Please try in an appropriate channel.", ephemeral=True)
            return

        model_uid = Model[model.value].value[0]

        try:
            imagefileobj = await generate_image_prodia(prompt, model_uid, sampler.value, seed, negative)
        except aiohttp.ClientPayloadError:
            await interaction.followup.send("An error occurred while generating the image. Please try again later.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)
            return

        if is_nsfw:
            img_file = discord.File(imagefileobj, filename="image.png", spoiler=True, description=prompt)
            prompt = f"||{prompt}||"
        else:
            img_file = discord.File(imagefileobj, filename="image.png", description=prompt)

        embed = discord.Embed(color=0xFF0000) if is_nsfw else discord.Embed(color=discord.Color.random())
        embed.title = f"Generated Image by {interaction.user.display_name}"
        embed.add_field(name='Prompt', value=f'- {prompt}', inline=False)
        embed.add_field(name='Image Details', value=f"- **Model:** {model.value}\n- **Sampler:** {sampler.value}\n- **Seed:**{seed}", inline=True)
        embed.set_footer(text=f"© Olympus Development", icon_url=self.bot.user.avatar.url)
        #embed.set_thumbnail(url=img_file)
        if negative:
            embed.add_field(name='Negative Prompt', value=f'- {negative}', inline=False)
        if is_nsfw:
            embed.add_field(name='NSFW', value=f'- {str(is_nsfw)}', inline=True)
            


        await interaction.followup.send(embed=embed, file=img_file, ephemeral=True)


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out Community or DM me.
"""