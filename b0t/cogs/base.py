import discord
from discord.ext import commands

class Base(commands.Cog):
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@commands.command(name="say")
	async def saysomethin(self, ctx, *, text: str):
		await ctx.send(discord.utils.escape_mentions(text))
		try:
			await ctx.message.delete()
		except Exception:
			pass

def setup(bot: commands.Bot):
	bot.add_cog(Base(bot))
