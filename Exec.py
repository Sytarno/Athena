'''Name: Exec Cog

Allows execution of commands through chat

Author: Evan Nguyen'''

import discord
from discord.ext import commands

def generateEmbed(ctx: commands.Context, title, description=""):
    embed = discord.Embed(
        colour = ctx.author.colour,
        title = title,
        description = description
    )
    return embed


class Exec(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = "Allows execution of code through chat"
        

    @commands.command(name='run', description='Make sure to highlight code. Context is saved as "ctx"')
    async def _run(self, ctx):
        content = ctx.message.content
        if "```" in content:
            code = content.rsplit("```")[1]
            print(str(code))
            exec(str(code))
        else:
            await ctx.send(ctx, embed=generateEmbed("", "Message did not contain code. Use the triple graves."))
        
