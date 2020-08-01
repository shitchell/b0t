1#!/usr/bin/env python3
# encoding: utf-8

import sys
import time
import atexit
import signal
from types import FrameType
from getpass import getpass
from _io import TextIOWrapper
from .settings import Settings
from syslog import syslog as _syslog
from typing import Optional, List

import discord
from discord.ext import commands

# Setup settings
settings: Settings = Settings(name=__package__)
settings.add_setting("-t", "--token", help="discord bot token")
settings.add_setting("-p", "--prefix", help="command prefix", default=".")
settings.add_setting("-l", "--log", help="log events to file")
settings.add_setting("--timestamp", help="prefix output with a timestamp (log output always has a timestamp regardless of this option)", action="store_true")
settings.add_setting("-c", "--config", help="path to configuration json file", action="load_config")
settings.add_setting("-v", "--verbose", help="increase output verbosity", action="count", default=0)
settings.add_setting("-q", "--quiet", help="no output to stdout", action="store_true")
settings.load()

# Ensure the token has been set
if not settings.get('token'):
	token: str = input('Token: ')
	settings.set('token', token)

# Open the logfile if set
logfile: TextIOWrapper = None
if settings.get("log"):
	try:
		logfile = open(settings.get("log"), 'a')
	except:
		log(f"Error opening logfile: {settings.get('log')}", syslog=True)

# Write to stdout, a log file, and/or syslog
def log(*args, stdout: bool = not settings.get('quiet'), syslog: bool = False, timestamp: bool = True, verbosity: int = 0) -> None:
	if verbosity > settings.get("verbose"):
		return

	if stdout or logfile or syslog:
		_timestamp: str = time.strftime('%Y-%m-%d %H:%M:%S')
		message: str = " ".join([str(x) for x in args])
		if stdout:
			if timestamp:
				print(f"[{_timestamp}] {message}")
			else:
				print(message)
		if logfile and message:
			# Don't write empty lines to logfile
			logfile.write(_timestamp + message)
			logfile.flush()
		if syslog:
			_syslog(_timestamp + message)

class DiscordBot(commands.AutoShardedBot):
	async def on_ready(self):
		log(f"{bot.user} is connected!", timestamp=False)
		log("", timestamp=False)
		log("GUILDS", timestamp=False)
		for guild in bot.guilds:
			log(f"- {guild.name} [{guild.id}] ({guild.member_count} Members)", timestamp=False)
		log("", timestamp=False)

	@commands.command()
	async def hello(ctx):
		await self.send(ctx.message.channel, "world")

	async def send(self, channel, *args):
		message = " ".join([str(x) for x in args])
		try:
			await channel.send(message)
		except Exception as e:
			log(f"Error sending message '{message[:50]}'", str(e))
		else:
			log(f"{channel.guild}#{channel.name} >> {message}")

# Create the bot
log("initializing bot", verbosity=2)
bot: DiscordBot = DiscordBot(command_prefix=settings.get("prefix"), reconnect=True)
log("initialized", verbosity=2)
log(f"command_prefix: '{bot.command_prefix}'", verbosity=3)

# Define the cogs to load
cogs: List[str] = [
	'b0t.cogs.base',
	'b0t.cogs.test'
]

# Load the cogs
log("loading cogs", verbosity=2)
for cog in cogs:
	log("loading cog", cog, verbosity=3)
	bot.load_extension(cog)
log("commands: ", [(str(x.cog_name) if hasattr(x, "cog") else "") + "." + x.name for x in bot.commands], verbosity=2)

# Display the invite link
invite_link: str = f"https://discord.com/api/oauth2/authorize?client_id=738596872222146662&permissions=8&redirect_uri=https%3A%2F%2Fdiscord.com%2F&scope=bot"
log("Invite link:", invite_link, timestamp=False)

log("running bot", verbosity=1)
bot.run(settings.get('token'))

# On closing
def on_exit(signal: int = None, frame: FrameType = None) -> None:
	log("Shutting down...")
	if logfile:
		logfile.close()
atexit.register(on_exit)
signal.signal(signal.SIGINT, on_exit)
signal.signal(signal.SIGTSTP, on_exit)
