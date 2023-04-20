'''Name: Activities cog

Allows execution of commands through chat

Author: Evan Nguyen'''

import discord
from discord.ext import commands

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = "Initiates Discord activites. Temporary solution until they release it fully."

        