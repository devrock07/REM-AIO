import discord
from discord.ext import commands

class QR(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="qr",
        aliases=["qrcode"],
        help="Sends a QR code image.",
        with_app_command=True
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def qr(self, ctx):
        embed = discord.Embed(
            title="Payment Platform",
            description="Here's you can pay UPI With Below QR",
            color=discord.Color.blurple()
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1334099972739829843/1377897856286851152/share_image4613677226378289500.png?ex=683aa2e1&is=68395161&hm=fa960adfa3b38961d4fad9861156100111b54d256259cdf436924db1ac0fee48&")
        await ctx.reply(embed=embed)

    @qr.error
    async def qr_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You must be an **administrator** to use this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ You're on cooldown. Try again in `{round(error.retry_after, 1)}s`.")
        else:
            await ctx.reply(f"⚠️ An error occurred: `{str(error)}`")

# Required for bot.load_extension()
async def setup(bot):
    await bot.add_cog(QR(bot))
