'''Name: MusicPl Module
Deprecated and unused music playing module. Uses ffmpeg and ytdl.

Author: Evan Nguyen'''

import discord
from discord.ext import commands

import numpy
import math
import random
import youtube_dl
import asyncio

#YT-DL----------------------------------------------------------------
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp\music\%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '192.168.0.34',
    'cachedir': False
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

ffmpeg_options = {
    'options': '-vn'
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')




    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def name_from_url(cls, url):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        return data.get('title', data.get('id', 'video'))

class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx
        self.loop = self.bot.loop

        self.voice = None
        self.source = None
        self.queue = Queue(self.bot, self.ctx)




    def after_seq(self, error):
        coro = self.play_next_song()
        fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            fut.result()
        except:
            pass
    
    async def play_next_song(self):
        if(len(self.queue) > 0):
            self.source = await YTDLSource.from_url(self.queue.getNext())
            self.voice.play(self.source, after = self.after_seq)

            emb = discord.Embed(
                colour = 000000,
                title = f'Currently playing:',
                description = f'{self.source.title}'
            )

            #await self.ctx.send(embed=generateEmbed(self.ctx, f'Currently playing:', f'{self.source.title}'))
            await self.ctx.send(embed = emb)
        else:
            await self.stop()

    async def skip(self):
        self.voice.stop()

    async def stop(self):
        self.queue = Queue(self.bot, self.ctx)

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

class Queue:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx
        self.loop = False

        self.queue = []
        self.titles = {}
        
    def __len__(self):
        return len(self.queue)

    def shuffle(self):
        random.shuffle(self.queue)

    def addTitle(self, title, link):
        self.titles[link] = title
        
    def addUrl(self, source):
        self.queue.append(source)

    def getNext(self):
        try:
            try:
                del self.titles[self.queue[0]]
            except:
                pass

            if self.loop:
                return self.queue[0]
            else:
                return self.queue.pop(0)
        except:
            return ""

    def removeAt(self, index):
        try:
            try:
                link = self.queue[index]
                self.queue.pop(index)
            except:
                pass

            return self.titles.pop(link)
        except:
            return ""

    def getTitles(self):
        x = []
        for link in self.queue:
            x.append(self.titles[link])
        return x

#-------------------------------------------------------------------------------------------------------------------------------------------
    
class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = "Basic cross-server music player."
        
        self.voice_states = {}

    def get_voice_state(self, ctx):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)


    
    @commands.command(name="join", aliases=["summon"])
    async def _join(self, ctx):
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(ctx.author.voice.channel)
            return

        ctx.voice_state.voice = await ctx.author.voice.channel.connect()

    @commands.command(name="play", aliases=["p"])
    async def _play(self, ctx, *, link=""):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        if link != "":
            ctx.voice_state.queue.addUrl(link)

            if ctx.voice_state.voice.is_playing():
                title = await YTDLSource.name_from_url(link)
                ctx.voice_state.queue.addTitle(title, link)
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} Added to the queue: {title}'))

            if not ctx.voice_state.voice.is_playing():
                await ctx.voice_state.play_next_song()

    @commands.command(name="remove")
    async def _remove(self, ctx, index=1):
        if ctx.voice_state.voice:
            trueInd = index-1
            if trueInd >= 0 and trueInd < len(ctx.voice_state.queue):
                de = ctx.voice_state.queue.removeAt(trueInd)
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} has removed: {de}'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.')) 

    @commands.command(name="queue", aliases=["q"])
    async def _queueCheck(self, ctx):
        if ctx.voice_state.voice:
            ar = ctx.voice_state.queue.getTitles()
            if len(ar) > 0:
                out = ""
                for x in range(0, len(ar)):
                    out += f'**{x+1}**. {ar[x]}\n' 
                await ctx.send(embed=generateEmbed(ctx, 'Queue', out))
            else:
                await ctx.send(embed=generateEmbed(ctx, 'Queue', 'very empty . . .'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))

    @commands.command(name="skip")
    async def _skip(self, ctx):
        if ctx.voice_state.voice:
            await ctx.voice_state.skip()
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx):
        if ctx.voice_state.voice:
            if len(ctx.voice_state.queue) > 0:
                ctx.voice_state.queue.shuffle()
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} has shuffled the playlist.'))
            else:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, there is nothing to shuffle.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.')) 

    @commands.command(name="stop", aliases=["disconnect", "dc"])
    async def _stop(self, ctx):
        if ctx.voice_state.voice:

            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]
            
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} has disconnected Athena.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))

    @commands.command(name="volume", aliases=["vol"])
    async def _vol(self, ctx, val=50):
        if ctx.voice_state.voice:
            if ctx.voice_state.voice.channel == ctx.author.voice.channel:
                ctx.voice_state.source.volume = val/100

                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} has set the volume of the player to **{val}%**'))
            else:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, you are not in a channel with Athena.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))

    @commands.command(name="pause")
    async def _pause(self, ctx):
        if ctx.voice_state.voice:
            if ctx.voice_state.voice.is_paused():
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is already paused.'))
            else:
                ctx.voice_state.voice.pause()
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} has paused Athena.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))

    @commands.command(name="resume")
    async def _resume(self, ctx):
        if ctx.voice_state.voice:
            if ctx.voice_state.voice.is_paused():
                ctx.voice_state.voice.resume()
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author} has resumed Athena.'))
            else:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is already playing.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))

    @commands.command(name="loop")
    async def _loop(self, ctx, arg=''):
        if ctx.voice_state.voice:
            ctx.voice_state.queue.loop = not ctx.voice_state.queue.loop
            if(ctx.voice_state.queue.loop):
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, queue is now looped.'))
            else:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, queue is no longer looped.'))
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author}, Athena is not connected to a channel.'))  
