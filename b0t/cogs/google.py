import discord
from discord.ext import commands

class Google(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

def setupt(bot: commands.Bot):
	bot.add_cog(Google(bot))