import discord
from discord.ext import commands
from deep_translator import GoogleTranslator

class TranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="hinglish",
        help="Translate informal Hinglish to proper English.",
        usage="!hinglish chlo udhr chat active krlo idhr nai"
    )
    async def hinglish(self, ctx: commands.Context, *, text: str = None):
        if not text:
            return await ctx.reply(
                "⚠️ Please provide some Hinglish text to translate.",
                ephemeral=True if ctx.interaction else False
            )

        msg = await ctx.reply(
            "🔄 Translating Hinglish...",
            ephemeral=True if ctx.interaction else False
        )

        try:
            # Translation using deep-translator (Google)
            translated = GoogleTranslator(source="auto", target="en").translate(text)

            embed = discord.Embed(
                title="🗣 Hinglish → English",
                color=0x00b0f4
            )
            embed.add_field(name="Original", value=text, inline=False)
            embed.add_field(name="Translated", value=translated, inline=False)
            embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )

            await msg.edit(content=None, embed=embed)

        except Exception as e:
            await msg.edit(content=f"❌ Translation failed: `{str(e)}`")

async def setup(bot):
    await bot.add_cog(TranslateCog(bot))
