from utils import emojis

import logging

import discord
from discord.ext import commands
import asyncio

log = logging.getLogger(__name__)


class React(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for owner in self.bot.owner_ids:
            if f"<@{owner}>" in message.content:
                try:
                    if owner == 677952614390038559:
                        
                        emojis = [
                            f"{emojis.REM_OWNER}",
                            f"{emojis.EMOJI_7CLUB_BAN}",
                            f"{emojis.LAND_YILDIZ}",
                            f"{emojis.ROSE}",
                            f"{emojis.LAND_YILDIZ}",
                            f"{emojis.EMOJI_37496ALERT}",
                            f"{emojis.SQ_HEADMOD}",
                            f"{emojis.DC_REDCROWNESPORTS}",
                            f"{emojis.GIFD}",
                            f"{emojis.GIFN}",
                            f"{emojis.MAX__A}",
                            f"{emojis.HEERIYE}",
                            f"{emojis.HEART_EM}",
                            f"{emojis.STAR}",
                            f"{emojis.KING}",
                            f"{emojis.HEADMOD}",
                            f"{emojis.SG_RD} ",
                            f"{emojis.REDHEART}",
                            f" {emojis.STAR}"
                        ]
                        for emoji in emojis:
                            await message.add_reaction(emoji)
                    else:
                        
                        await message.add_reaction(f"{emojis.REM_OWNER}")
                except discord.errors.RateLimited as e:
                    await asyncio.sleep(e.retry_after)
                    await message.add_reaction(f"{emojis.REM_OWNER}")
                except Exception:
                    log.exception("Auto react owner mention failed")
