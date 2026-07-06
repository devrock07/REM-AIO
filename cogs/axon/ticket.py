from utils import emojis

import discord

from discord.ext import commands

class _ticket(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    """Ticket"""

    def help_custom(self):

              emoji = f'{emojis.TICKET}'

              label = "Ticket"

              description = "Show you Commands of Ticket"

              return emoji, label, description

    @commands.group()

    async def __Ticket__(self, ctx: commands.Context):

        """`/ticket-panel`"""