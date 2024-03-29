'''Name: Athena 2.0
Author: Evan Nguyen'''

import discord
import os
import pickle
from discord.ext import commands
from discord.utils import get

from PIL import Image
from PIL import ImageFilter
import numpy
import math
import random

import asyncio
import wavelink
'''from wavelink.eqs import Equalizer'''

import re

dPATH = "data/"

intents = discord.Intents.all()

bot = commands.Bot(command_prefix = '>?', intents=intents)
PARSE = open(dPATH + '.env.txt').read().split('\n')
TOKEN = PARSE[0]
AUTHOR = int(PARSE[1])
SELFID = int(PARSE[2])

botCommands = {}

with open(dPATH + '.authorizedChannels.txt', 'r') as in_file:
        authorizedChannels = in_file.read().split('\n')

def validChannel(channel):
    authorizedChannels = read(dPATH + '.authorizedChannels.txt')
    return str(channel.id) in authorizedChannels

def embedChannel(channel):
    activeEmbedChannels = read(dPATH + '.embedChannels.txt')
    return str(channel.id) in activeEmbedChannels


def read(path):
    with open(path, 'r') as in_file:
        return in_file.read().split('\n')

def write(path, data):
    with open(path, 'w') as out_file:
        out_file.write('\n'.join(data))

authorizedChannels = read(dPATH + '.authorizedChannels.txt')
activeEmbedChannels = read(dPATH + '.embedChannels.txt')

voicepkl = open(dPATH + '.voiceLock.pkl', "rb")
try:
    voiceLocks = pickle.load(voicepkl)
except:
    print("Unable to load voiceLock pickle.")
    voiceLocks = {}

from MusicWave import *

@bot.event
async def on_ready():
    await bot.add_cog(AthenaCore(bot))
    await bot.add_cog(VoiceCMD(bot))
    #await bot.add_cog(MudaeHelper(bot))

    #from MusicNew import *
    #bot.add_cog(Music(bot))

    await bot.add_cog(Music(bot))

    #from recognition import *
    #bot.add_cog(NLP(bot))

    #from Exec import *
    #bot.add_cog(Exec(bot))
    print(f'{bot.user} is now Online.')

#EXTRA----------------------------------------------------------------
def generateEmbed(ctx, title, description=""):
    embed = discord.Embed(
        colour = ctx.author.colour,
        title = title,
        description = description
    )
    return embed

def get_prefix(bot, msg):
    try:
        with open(dPATH + '.prefix.pkl', "rb") as ppkl:
            prefixes = pickle.load(ppkl)

        return prefixes[str(msg.guild.id)]
    except:
        return ">?"

#COMMANDS-------------------------------------------------------------
class AthenaCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = 'Main functionality for Athena.'

    @commands.command(name="prefix", description="Changes the prefix for the server. Accepts up to 3 sequential characters.")
    async def _prefixChange(self, ctx, *, message: str):
        if message:
            message = message.replace(" ", "") #trim spaces
            if(len(message) > 3):
                message = message[:3]

            async def button_callback(interact):
                ci = interact.data['custom_id']
                b1.disabled=True
                b2.disabled=True
                if(ci == "0"):
                    try:
                        with open(dPATH + '.prefix.pkl', "rb") as ppkl:
                            prefixes = pickle.load(ppkl)
                    except:
                        print("Unable to load custom prefix file. Creating new one.")
                        prefixes = {}

                    prefixes[str(ctx.guild.id)] = message #Default prefix = >?

                    ppkl = open(dPATH + '.prefix.pkl', "wb")
                    pickle.dump(prefixes, ppkl)
                    
                    await interact.response.edit_message(embed=genEmbed('', f'The prefix for this server is now **{message}**.'), view=view)
                else:
                    await interact.response.edit_message(embed=genEmbed('', f'The prefix for this server was not changed.'), view=view)

            b1 = Button(label="Yes", style=discord.ButtonStyle.green, custom_id="0")
            b2 = Button(label="Decline", custom_id="1")
            b1.callback = button_callback
            b2.callback = button_callback

            view=View()
            view.add_item(b1)
            view.add_item(b2)

            await ctx.send(embed=genEmbed('', f'Would you like to change the server prefix to **{message}**?'), view=view)

            #resp = await self.bot.wait_for("button_click")
            #if resp.channel == ctx.channel:
            #    await resp.respond(
            #        type=InteractionType.ChannelMessageWithSource
            #    )
        else:
            await ctx.send(embed=genEmbed('', f'{ctx.author.mention}, you did not specify a prefix.'))       
    
    @commands.command(name="status")
    async def _statusCheck(self, ctx):
        user = await self.bot.fetch_user(AUTHOR)
        out = f'This bot is made by {user.name}.\n\n'
        for cog in self.bot.cogs:
            try:
                out += f'**{cog}** - {self.bot.cogs[cog].desc}\n' if self.bot.cogs[cog].desc else f'**{cog}**\n'
            except:
                pass
        await ctx.send(embed=generateEmbed(ctx, f'Athena is currently online with **{len(self.bot.cogs)}** cogs.\n', out))

    @commands.command(name="vcLock")
    async def _vcLock(self, ctx):
        if ctx.author.voice.channel:
            if ctx.guild.id not in voiceLocks.keys(): 
                voiceLocks[ctx.guild.id] = [ctx.author.voice.channel.id, []]
                voicepkl = open(dPATH + '.voiceLock.pkl', "wb")
                pickle.dump(voiceLocks, voicepkl)

                await ctx.send(embed=generateEmbed(ctx, '', f'Attached a listener to **{ctx.author.voice.channel.name}**, {ctx.author.mention}'))
            else:
                del voiceLocks[ctx.guild.id]
                await ctx.send(embed=generateEmbed(ctx, '', f'Successfully removed the listener on **{ctx.author.voice.channel.name}**.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, you are not connected to a voice channel.'))

    @commands.command(name="delLock")
    async def _delLock(self, ctx):
        def check(author):
            def inner_check(message):
                return message.author == author
            return inner_check

        if ctx.guild.id in voiceLocks.keys():
            await ctx.send(embed=generateEmbed(ctx, f'Are you sure you want to remove the listener?',
            'Any extra channels that were created will not be automatically destroyed. Respond with (y/Y) to confirm.'))
            msg = await bot.wait_for('message', check=check(ctx.author), timeout=30)
            print(msg.content)
            if(msg.content == 'y' or msg.content == 'Y'):
                del voiceLocks[ctx.guild.id]
                await ctx.send(embed=generateEmbed(ctx, '', f'Successfully removed the listener from all channels. Cleanup as necessary.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, there are no listeners.'))

    @commands.command(name="addChannel")
    async def _addChannel(self, b):
        if(b.author.id == AUTHOR):
            authorizedChannels = read(dPATH + '.authorizedChannels.txt')
            
            if str(b.channel.id) not in authorizedChannels:
                authorizedChannels.append(str(b.channel.id))
                write(dPATH + '.authorizedChannels.txt', authorizedChannels)

                await b.send(embed=generateEmbed(b, '', f'Added this channel to {bot.user}'))
            else:
                await b.send(embed=generateEmbed(b, '', f'This channel has already been added, {b.author.mention}.'))
        else:
            await b.send(embed=generateEmbed(b, '', f'You are not authorized to do that, {b.author.mention}.'))

    @commands.command(name="removeChannel")
    async def _removeChannel(self, b):
        if(b.author.id == AUTHOR):
            authorizedChannels = read(dPATH + '.authorizedChannels.txt')
            
            if validChannel(b.channel):
                authorizedChannels.remove(str(b.channel.id))
                write(dPATH + '.authorizedChannels.txt', authorizedChannels)

                await b.send(embed=generateEmbed(b, '', f'Removed this channel from {bot.user}'))
            else:
                await b.send(embed=generateEmbed(b, '', f'This channel has been removed already, {b.author.mention}.'))
        else:
            await b.send(embed=generateEmbed(b, '', f'You are not authorized to do that, {b.author.mention}.'))

    @commands.command(name="ping")
    async def _ping(self, b):
        await b.send('pong!')

    @commands.command(name="embedMode")
    async def _toggleEmbed(self, b):
        activeEmbedChannels = read(dPATH + '.embedChannels.txt')
        if str(b.channel.id) not in activeEmbedChannels:
            activeEmbedChannels.append(str(b.channel.id))

            await b.send(f'Embed conversion is now **on** for this channel.')
        else:
            activeEmbedChannels.remove(str(b.channel.id))

            await b.send(f'Embed conversion is now **off** for this channel.')

        write(dPATH + '.embedChannels.txt', activeEmbedChannels)

    @commands.command(name="downscale")
    async def _distort(self, i, arg=8):
        if(len(i.message.attachments) > 0):
            for x in range(0, len(i.message.attachments)):
                attach = i.message.attachments[x]
                path = f"{x}{attach.url[attach.url.rindex('.'):]}"
                await attach.save(f'temp/{path}')

                im = Image.open(f'temp/{path}')
                
                imC = im.resize((math.ceil(im.size[0]/arg), math.ceil(im.size[1]/arg)))
                imC = imC.filter(ImageFilter.EDGE_ENHANCE)
                imC = imC.filter(ImageFilter.SHARPEN)
        
                imC = imC.resize((im.size[0], im.size[1]))
                
                imC.save(f'temp/ex{path}')

                await i.send(file=discord.File(f'temp/ex{path}'))
                os.remove(f'temp/ex{path}')
                os.remove(f'temp/{path}')
        else:
            await i.send(f'This message has no attachments, {i.author}.')
            
    @commands.command(name="purge")
    async def _purge(self, i, num=1):
        if i.author.permissions_in(i.channel).administrator:
            messages = await i.channel.history(limit=num+1).flatten()
            d = len(messages)
            for x in messages:
                await x.delete()
                
            await i.send(f'{i.author} purged {num} {"messages" if d>1 else "message"}.')
        else:
            await i.send(f'You do not have administrator privileges.')

    @commands.command(name="scan")
    async def servers(self, ctx):
        activeservers = bot.guilds
        out = ""
        c = 0
        for guild in activeservers:
            c += 1
            out += f'{guild.name}\n'

        await ctx.send(embed=discord.Embed(description = f'**I am currently in {c} servers.**```css\n{out}\n```',
                                                   colour = 1973790))

#---Mudae Test---------------------------------------------------------
class VoiceCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = 'Author-only message ventriloquism.'

    def cog_check(self, ctx: commands.Context):
        return ctx.author.id == AUTHOR
        #return True

    

    @commands.command(name="pGrant")
    async def _giveRole(self, ctx, msg=1):
        print(ctx.guild.roles)
        
        user= ctx.message.author
        role = (discord.utils.get(user.guild.roles, id=msg))
        if(role) and msg != 1:
            try:   
                await ctx.author.add_roles(role)
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, you have been successfully granted **{role}**.'))
            except:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, I do not have the permissions to grant **{role}**.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, I could not find the specified role.'))

    @commands.command(name="pRemove")
    async def _removeRole(self, ctx, msg=1):
        #print(ctx.guild.roles)
        
        user= ctx.message.author
        role = (discord.utils.get(user.guild.roles, id=msg))
        if(role) and msg != 1:
            try:   
                await ctx.author.remove_roles(role)
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, **{role}** was removed from you.'))
            except:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, I do not have the permissions to remove **{role}**.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, I could not find the specified role.'))
    
    @commands.command(name="pColor")
    async def _changeColor(self, ctx, *msg):
        user = ctx.message.author
        s = ' '.join(msg)
        role = discord.utils.get(user.guild.roles, name=s)
        #print(s)
        def check(author):
            def inner_check(message):
                return message.author == author
            return inner_check

        if(role):
            height = role.position
            if(role.position < user.top_role.position):
                await ctx.send(embed=generateEmbed(ctx, '', f'**{role}** is currently below your top role.\nWould you like me to attempt to move it? (y/n)'))
                msg = await bot.wait_for('message', check=check(ctx.author), timeout=30)
                if(msg.content == 'y' or msg.content == 'Y'):
                    try:
                        await role.edit(position = user.top_role.position + 2)
                        await ctx.send(embed=generateEmbed(ctx, '', f'Successfully elevated **{role}**'))
                    except:
                        await ctx.send(embed=generateEmbed(ctx, '', f'Failed to elevate that role.'))
        
            if(role):
                await ctx.send(embed=generateEmbed(ctx, '', f'Would you like to modify the role **{role}**? (y/n)'))
                msg = await bot.wait_for('message', check=check(ctx.author), timeout=30)
                if(msg.content == 'y' or msg.content == 'Y'):
                    await ctx.send(embed=generateEmbed(ctx, '', f'Please state the r, g, b value you would like to change it to.'))
                    color = await bot.wait_for('message', check=check(ctx.author), timeout=30)
                    colorT = tuple(map(int, color.content.split(', '))) 
                    #print(colorT)
                    if(colorT):
                        await role.edit(colour = discord.Colour.from_rgb(colorT[0], colorT[1], colorT[2]))
                        await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} changed the color of **{role}** to **({colorT[0]}, {colorT[1]}, {colorT[2]})**'))
                    
                if(msg == 'n' or msg == 'N'):
                    await ctx.send(embed=generateEmbed(ctx, '', f'Canceled.'))
            else:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, I could not find the specified role.'))
        else:
            if(msg == ''):
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, you must specify a role'))

    @commands.command(name="pCopy")
    async def _copy(self, ctx, *msg):
        args = list(msg)
        try:
            count = int(args[0])
            args.pop(0)

            m = ' '.join(map(str, args))

            for x in range(0, count):
                await ctx.send(f'{m}')
                await asyncio.sleep(0.75)
        except:
            await ctx.send(embed=generateEmbed(ctx, '', 'Invalid arguments. Count expected as first argument'))

    @commands.command(name="pID")
    async def _getId(self, ctx, arg=1):
        try:
            msgs = await ctx.channel.history(limit=arg+1).flatten()
            out = ""
            
            msgs.pop(0)
            for msg in msgs:
                out += f'**{msg.author}** : {msg.author.id}\n'
                
            await ctx.send(embed=generateEmbed(ctx, '', out))
        except:
            await ctx.send(embed=generateEmbed(ctx, f'{ctx.author}, there was no message before that.'))

    @commands.command(name="pReact")
    async def _react(self, ctx, arg=1, mode=1):
        msgs = await ctx.channel.history(limit=20).flatten()
        z = 0
        while msgs[z].author == ctx.author:
            z += 1

        if z == 19:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena could not find the last person to react to.'))
        else:
            msg = msgs[z]
            
            g = list(ctx.guild.emojis)
            emo = self.bot.emojis

            e = []
            for i in emo:
                if i not in g:
                    e.append(i)
                    
            arg = max(min(arg, len(g)+len(e)), 1)
            
            random.shuffle(g)
            random.shuffle(e)
            b = e + g
            #random.shuffle(b)
            
            f = []
            while len(f) < arg:
                if mode == 1:
                    if len(g) > 0:
                        p = g.pop(0)
                    else:
                        p = e.pop(0)
                else:
                    p = b.pop(0)

                if (p not in f) and (p.available):
                    f.append(p)
            try:
                for emoji in f:
                    await msg.add_reaction(emoji)
            except:
                pass
        
class MudaeHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = 'Mudae-related commands. Only contains one function atm.'

    @commands.command(name="mmk")
    async def _scan(self, ctx, arg=1):
        messages = await ctx.channel.history(limit=30).flatten()

        names = {}
        value = []

        try:
            page = 0
            for msg in messages:
                if msg.embeds and page < arg:
                    page += 1
                    embed = msg.embeds[0]
                    
                    s = embed.description.split("\n")
                    
                    for line in s:
                        if line == '\u200b' or line == '':
                            s.remove(line)

                    for line in s:
                        if "<:kakera:469835869059153940>" in line:
                            s.remove(line)

                    
                    for x in range(0, len(s)):
                        s[x] = s[x].replace("*", "")
                        s[x] = s[x].replace(" ka", "")

                    for char in s:
                        ind = len(char)-1
                        while(char[ind].isdigit()):
                            ind -= 1
                        
                        v = char[ind:]
                        n = char[:ind]
                        
                        
                        value.append(int(v))
                        if str(int(v)) not in names.keys():
                            names[str(int(v))] = [n]
                        else:
                            names[str(int(v))].append(n)

            if page > 0 and len(value) > 0:
                out = "\n**Copy and send this message after $sm:** \n\n"
                value.sort(reverse = True)
            
                valueF = []
                for x in range(0, len(value)):
                    if value[x] not in valueF:
                        valueF.append(value[x])

                for key in valueF:
                    nameOut = names[str(key)]
                    for ex in nameOut:
                        out += f'${ex}'
            
                await ctx.send(embed=generateEmbed(ctx, f"{ctx.author} sorted a harem of {len(value)} characters.", out))
            else:
                await ctx.send(embed=generateEmbed(ctx, f'{ctx.author}, sorting failed.', 'Make sure that !mmk was ran however many times necessary for all your pages.'))
        except:
            await ctx.send(embed=generateEmbed(ctx, f'{ctx.author}, sorting failed.', 'Make sure that !mmk was ran however many times necessary for all your pages.'))

#--MAIN READER---------------------------------------------------------
@bot.event
async def on_message(msg):
    if(msg.author != bot.user and msg.mentions):
        if len(msg.mentions) == 1 and msg.mentions[0] == bot.user:
            await msg.channel.send(embed=genEmbed('', f'The current prefix for this server is **{get_prefix(bot, message)}**\n'))

    if validChannel(msg.channel) or "channel" in msg.content.lower():
        await bot.process_commands(msg)
        
        if msg.author.id != SELFID and not msg.author.bot:      
            if embedChannel(msg.channel):
                if len(msg.content) > 250:
                    embed = discord.Embed(
                        colour = msg.author.colour,
                        description = msg.content
                    )
                else:
                    embed = discord.Embed(
                        colour = msg.author.colour,
                        title = msg.content
                    )
                    
                avatar = f'https://cdn.discordapp.com/avatars/{msg.author.id}/{msg.author.avatar}.png'
                embed.set_author(name=msg.author.display_name, icon_url=avatar)

                await msg.delete()
                await msg.channel.send(embed=embed)

#--VOICE STATE READER--------------------------------------------------

async def moveRoutine(member, guild, origChannel):
    try:
        if(member.nick):
            nameStr = f"{member.nick}" + "'s room"
        else:
            nameStr = member.name + "'s room"

        made = await origChannel.clone(name=nameStr)
        voiceLocks[guild.id][1].append(made.id)
        voicepkl = open(dPATH + '.voiceLock.pkl', "wb")
        pickle.dump(voiceLocks, voicepkl)

        await member.move_to(made)
    except:
        pass

userQueue = []

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        agid = after.channel.guild.id
        if(agid in voiceLocks.keys()):
            if(after.channel.id in voiceLocks[agid]):
                userQueue.append(member)
                await moveRoutine(member, after.channel.guild, after.channel)
                
    except:
        pass

    try:
        bgid = before.channel.guild.id
        if(bgid in voiceLocks.keys()):
            if(before.channel.id in voiceLocks[before.channel.guild.id][1]):
                if not before.channel.members:
                    voiceLocks[before.channel.guild.id][1].remove(before.channel.id)
                    voicepkl = open(dPATH + '.voiceLock.pkl', "wb")
                    pickle.dump(voiceLocks, voicepkl)
                    await before.channel.delete()
    except:
        pass

bot.run(TOKEN)
