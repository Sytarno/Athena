'''Name: MusicNew Module
Player module used by the main bot. Uses lavalink that can be found here:
https://github.com/Frederikam/Lavalink/releases/

Author: Evan Nguyen'''

'''
ytsearch: [search YouTube]
ytmsearch: [search YouTube Music]
scsearch: [Search SoundCloud]

URL only:
[Bandcamp]
[Getyarn]
[Nico]
[Twitch]
[Vimeo]

Other:
[Http]
[Stream]
[Local]
'''

import discord
from discord.ext import commands

import numpy
import math
import random
import wavelink
import json

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import validators

import time
import asyncio
import re
import socket

from urllib.parse import urlparse, parse_qs

def get_id(url):
    u_pars = urlparse(url)
    quer_v = parse_qs(u_pars.query).get('v')
    if quer_v:
        return quer_v[0]
    pth = u_pars.path.split('/')
    if pth:
        return pth[-1]





global GLOBAL_RATE
#GLOBAL_RATE = 30 / (60 ** 2) #PLAYS PER HOUR
GLOBAL_RATE = 1200 / (60 ** 2) #PLAYS PER HOUR

#------------
def generateEmbed(ctx: commands.Context, title, description=""):
    embed = discord.Embed(
        colour = ctx.author.colour,
        title = title,
        description = description
    )
    return embed

dPATH = "data/"

fm = open(dPATH + '.avgs.txt', 'r')
throttle_dict = json.load(fm)
fm.close()

#EXTRA VARS
BAR_ORIGINAL = "▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅"

#------------
class NewPlayer(wavelink.player.Player):
    def __init__(self, bot, guild_id, node):
        super().__init__(bot, guild_id, node)

        self.queue = []
        self.repeat = []
        
        self.text_channel = None
        self.now_playing_message = None
        self.current = None
        self.paused = False

        self.mode = 'ytsearch'
        self.filter = 'flat'
        self.validModes = {'default': 'ytsearch', 'youtube' : 'ytsearch', 'soundcloud': 'scsearch', 'url': ''}
        self.filters = {'flat': wavelink.eqs.Equalizer.flat(), 'metal': wavelink.eqs.Equalizer.metal(), 'boost': wavelink.eqs.Equalizer.boost(), 'piano': wavelink.eqs.Equalizer.piano()}
        
        self.avgUse = throttle_dict.get(str(guild_id))
        #if not self.avgUse:
        self.avgUse = [1, 0, time.time()]
            
        self.disconnect_task = None
        self.skips = 0
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="051b9bd0a22f4740bea03b9363ef883a",
                                                           client_secret="c2cf3efd91e04bdb8b1b3194fcba8b9e"))

    async def send(self, content=None, *, embed=None, now_playing=False, delete_np=False, delete_after=None):
        channel = self.text_channel
        if channel is None or not channel.permissions_for(channel.guild.me).send_messages:
            return

        try:
            msg = await channel.send(content=content, embed=embed, delete_after=delete_after)
        except (discord.Forbidden, discord.NotFound):
            pass

        if delete_np and self.now_playing_message:
            try:
                await self.now_playing_message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

        if now_playing:
            self.now_playing_message = msg

    def updateAvg(self, uses):
        difference = time.time() - self.avgUse[2]
        self.avgUse[2] += difference
        self.avgUse[0] += difference
        self.avgUse[1] += uses

        throttle_dict[self.guild_id] = self.avgUse
            
        fm = open('.avgs.txt', 'w')
        json.dump(throttle_dict, fm)
        fm.close()

    def getAvg(self):
        return self.avgUse[1]/self.avgUse[0]
    
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}
        self.desc = "Revamped music player using lavalink + wavelink."

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        
        #ip = socket.gethostbyname(socket.gethostname())
        ip = "10.0.0.156"
                
        await self.bot.wavelink.initiate_node(host=f'{ip}',
                                              port=2333,
                                              rest_uri=f'http://{ip}:2333',
                                              password='youshallnotpass',
                                              identifier='Athena',
                                              region='us_west')

        print(f'Connected successfully to: {ip}') 
        for node in self.bot.wavelink.nodes.values():
            node.set_hook(self.on_node_event)

    async def playerConnectedCheck(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        
        if player.is_connected:
            return True
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, Athena is not connected to a voice channel.'))
            return False

    async def userConnectedCheck(self, ctx):
        if ctx.author.voice:
            return True
        else:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, you are not in a voice channel.'))
            return False

    async def acquire_tracks(self, player):
        tracks = None
        
        query = player.queue.pop(0)
        #regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        #url = re.findall(regex, query)  

        if(validators.url(query)):
            tracks = await self.bot.wavelink.get_tracks(f'{query}')
        else:
            tracks = await self.bot.wavelink.get_tracks(f'{player.mode}:{query}')
        '''
        if player.mode == 'scsearch':
            tracks = await self.bot.wavelink.SoundCloudTrack.search(query)
        if player.mode == 'ytsearch':
            tracks = await self.bot.wavelink.YouTubeTrack.search(query)
        if player.mode == '':
            tracks = await self.bot.wavelink.SearchableTrack.search(query)
        '''
        player.updateAvg(1)

        if(type(tracks) == wavelink.player.TrackPlaylist):
            return tracks.tracks[0], query
        else:
            return tracks[0], query

    @commands.command(name='connect', aliases=["join", "summon"])
    async def _connect(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send(embed=generateEmbed(ctx, '', 'No channel to join. Please either specify a valid channel or join one.'))

        if channel:
            player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
            #await ctx.send(embed=generateEmbed(ctx, '', f'Connecting to **{channel.name}**'))

            player.text_channel = ctx.channel
            await player.connect(channel.id)

    @commands.command(name='stop', aliases=["dc", "leave"])
    async def _disconnect(self, ctx, *, channel: discord.VoiceChannel=None):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if player.queue:
            player.queue = []
            
        await player.disconnect()

    @commands.command(name='play', aliases = ["p"])
    async def _play(self, ctx, *, query: str):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)

        if not player.is_connected:
            await ctx.invoke(self._connect)

        if player.is_playing:        
            await ctx.send(embed=generateEmbed(ctx, '', f"Enqueued the query '*{query}*'. [{ctx.author.mention}]"))

        #Check if it is a spotify link
        spot = re.findall(r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*track[/:]*[A-Za-z0-9?=]+", query)
        if(spot):
            try:
                t = player.sp.track(query)
                player.queue.append(f"{t['artists'][0]['name']} {t['name']}")
                
            except:
                pass
        else:
            player.queue.append(query)

        if not player.is_playing:
            await self.coroutinePlay(player)

    @commands.command(name='mode', aliases = ["m"], description="Available modes:\n" +
                                                                "default (youtube)\n" +
                                                                "youtube\n" +
                                                                "soundcloud\n" +
                                                                "url: This supports:\n" +
                                                                "[Bandcamp]\n" +
                                                                "[Getyarn]\n" +
                                                                "[Nico]\n" +
                                                                "[Twitch]\n" +
                                                                "[Vimeo]\n")
    async def _mode(self, ctx, arg='ytsearch'):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            if arg in player.validModes.keys():
                player.mode = player.validModes[arg]
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention} changed the mode to **{player.validModes[arg]}**.'))
            else:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, that is not a valid search parameter. Use "help mode" to see available modes.'))
            
          
    @commands.command(name='queue', aliases = ["q"])
    async def _queue(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)

        if await self.playerConnectedCheck(ctx):
            ar = player.queue
            if len(ar) > 0:
                out = ""
                for x in range(0, len(ar)):
                    out += f'{x+1}. {ar[x]}\n' 
                await ctx.send(embed=discord.Embed(description = f'**Queue**```css\n{out}\n```',
                                                   colour = 1973790))
            else:
                await ctx.send(embed=discord.Embed(description = f'**Queue**```css\nvery empty . . .\n```',
                                                   colour = 1973790))

    @commands.command(name='remove', aliases = ["r"])
    async def _remove(self, ctx, arg=0):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx) and arg > 0:
            await ctx.send(embed=generateEmbed(ctx, '', f'{player.queue.pop(arg-1)} at index **{arg}** was removed from the queue. [{ctx.author.mention}]')) 

    @commands.command(name='clear', aliases = ["c"])
    async def _clear(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            player.queue = []
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention} cleared the queue')) 

    @commands.command(name='skip', aliases = ["s"])
    async def _skip(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            player.updateAvg(0)

            if(player.getAvg() > GLOBAL_RATE):
                if player.skips == 0:
                    await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, the current rate of the player exceeds the global rate.'
                                                   + ' Skipping will forcefully pause the player. Are you sure you want to skip? Use this command again to proceed.'))
                    player.skips += 1
                else:
                    await player.stop()
            else:
                await player.stop()

    @commands.command(name='pause')
    async def _pause(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            await player.set_pause(not player.paused)
            await ctx.send(embed=generateEmbed(ctx, '', f"{ctx.author.mention} has {'paused' if player.paused else 'unpaused'} Athena."))

    @commands.command(name='filter', aliases = ["f"], description = "boost: This equalizer emphasizes Punchy Bass and Crisp Mid-High tones. Not suitable for tracks with Deep/Low Bass.\n" +
                                                                    "metal: Experimental Metal/Rock Equalizer. Expect clipping on Bassy songs.\n" + 
                                                                    "piano: Piano Equalizer. Suitable for Piano tracks, or tacks with an emphasis on Female Vocals. Could also be used as a Bass Cutoff.\n" +
                                                                    "flat: Default. Resets the equalizer to none.")
    async def _filter(self, ctx, arg = None):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if arg == None:
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, you must specify a filter.'))
        else:
            try:
                if arg == 'boost' or arg == 'metal' or arg == 'piano' or arg == 'flat':
                    player.filter = arg
                    
                    await player.set_eq(player.filters[player.filter])
                    msg = await ctx.send(embed=generateEmbed(ctx, '', f'Changing filter to **{arg}**...'))
                    await asyncio.sleep(5.5)

                    await msg.edit(embed=generateEmbed(ctx, '', f'{ctx.author.mention} changed the filter to **{arg}**'))
                else:
                    await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, invalid filter. Use "help filter" to see the available ones.'))
            except:
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, invalid filter. Use "help filter" to see the available ones.'))

    @commands.command(name='volume', aliases = ["v"])
    async def _volume(self, ctx, arg=100):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            await player.set_volume(arg)

            c = int(((player.volume/1000) ** 0.5) * 28)
            highlight = BAR_ORIGINAL[:c]
            nonhighlight = BAR_ORIGINAL[c:]
            
            await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention} set the volume to **{arg}%**\n' +
                                               f'[{highlight}](https://www.youtube.com/watch?v=dQw4w9WgXcQ){nonhighlight}'))

    @commands.command(name='seek', description="Seeks via seconds.")
    async def _seek(self, ctx, arg=0):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            def timeGet(secs):
                return f'{int(secs/60)}m {int(secs%60)}s'

            if(arg > (player.current.length / 1000)):
                await ctx.send(embed=generateEmbed(ctx, '', f'{ctx.author.mention}, that is beyond the length of the track.'))
            else:
                await player.seek(arg*1000)
                await ctx.send(embed=generateEmbed(ctx, '', f'Seeked to **{timeGet(arg)}** {ctx.author.mention}'))
        
    @commands.command(name='reqs')
    async def _requestCheck(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        player.updateAvg(0)
        
        e = generateEmbed(ctx, '', f'The current guild player is at a rate of **{round(player.getAvg(), 5)}**.')
        e.add_field(name = '**Rate**', value = f'The current global rate is **{round(GLOBAL_RATE, 5)}**, or *{round(GLOBAL_RATE*60, 5)}* requests per minute. Exceeding this will force the player to sleep.')
        await ctx.send(embed=e)

    @commands.command(name='now playing', aliases = ["np"])
    async def _currentCheck(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        if await self.userConnectedCheck(ctx) and await self.playerConnectedCheck(ctx):
            if(player.current):
                c = int(((player.volume/1000) ** 0.5) * 28)
                highlight = BAR_ORIGINAL[:c]
                nonhighlight = BAR_ORIGINAL[c:]

                #uri = player.current.uri.replace("https://www.youtube.com/watch?v=", "")
                uri = get_id(player.current.uri)
            
                e = discord.Embed(title = 'Currently playing:',
                                                    thumbnail = f'https://img.youtube.com/vi/{uri}/maxresdefault.jpg',
                                                    description = f'```css\n{player.current.title}\n```\n\n',
                                                    colour = 1973790)

                FULL = "───────────────────────────────────────"
                #secIn = time.time() - player.playTime
                secIn = player.position / 1000
                secLen = player.current.length / 1000
                cur = int(len(FULL) * secIn / secLen)
                
                def timeGet(secs):
                    return f'{int(secs/60)}m {int(secs%60)}s'
                
                e.add_field(name = f'{timeGet(secIn)} | {timeGet(secLen)}', value = f'{FULL[:cur] + "[●](https://www.youtube.com/watch?v=dQw4w9WgXcQ)" + FULL[1+cur:]}')
                e.add_field(name = f'**Volume**', value = f'[{highlight}](https://www.youtube.com/watch?v=dQw4w9WgXcQ){nonhighlight}', inline=False)
                e.add_field(name = '**Filter**', value = f'wavelink.eqs.Equalizer.{player.filter}()\n', inline=False)
                e.set_thumbnail(url=f'https://img.youtube.com/vi/{uri}/maxresdefault.jpg')

                await ctx.send(embed=e)  
            else:
                await ctx.send(embed=discord.Embed(description = f'**Currently playing:**```css\nnothing . . .\n```',
                                                   colour = 1973790))


    @commands.command(name='view_eq', aliases = ["view-eq"])
    async def _display_Eq(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        di = player.filters[player.filter].raw

        BAR = "───"
        BAR = " ─ "
        SPACE = "   "
        SCALAR = 4

        MAX = 0
        MIN = 0
        for i in range(0, len(di)):
            if di[i][1] > MAX:
                MAX = di[i][1]
            if di[i][1] < MIN:
                MIN = di[i][1]
        
        out = ""
        for y in range(SCALAR, -SCALAR-1, -1):
            out += "z " if y == 0 else "  "
                
            for x in range(0, len(di)):
                if(y == math.ceil(di[x][1]*SCALAR)):
                    out += f'{BAR}'
                else:
                    out += f'{SPACE}'

            out += " z\n" if y == 0 else "  \n"

        e = discord.Embed(description = f'**Equalizer:**\n'
                            + f'\t{player.filter} | Max: {MAX}, Min: {MIN}\n'
                            + f'```css\n{out}\n```',
                            colour = 1973790)
        await ctx.send(embed=e)
    
    @commands.command(name='build_eq', aliases = ["build-eq"], description = 'Provide up to 15 numbers representing 15 frequency bands. The value should be between -1 and 1.')
    async def _build_Eq(self, ctx, a=0.0, b=0.0, c=0.0, d=0.0, e=0.0, f=0.0, g=0.0, h=0.0, i=0.0, j=0.0, k=0.0, l=0.0, m=0.0, n=0.0, o=0.0):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=NewPlayer)
        player.filter = 'custom'

        c = [(1, a), (2, b), (3, c), (4, d), (5, e), (6, f), (7, g), (8, h), (9, i), (10, j), (11, k), (12, l), (13, m), (14, n), (15, o)]
        
        player.filters['custom'] = wavelink.eqs.Equalizer(levels=c)

        await player.set_eq(player.filters[player.filter])
        msg = await ctx.send(embed=generateEmbed(ctx, '', f'Changing filter to **custom**...'))
        await asyncio.sleep(5.5)

        await msg.edit(embed=generateEmbed(ctx, '', f'{ctx.author.mention} installed a custom filter. View it using view_eq.'))
        
    
    async def send_song_info(self, player: NewPlayer, track: wavelink.GenericTrack):
        await player.send(embed=discord.Embed(description = '**Currently playing:**\n' + f'```css\n{track.title}\n```',
                                                  colour = 1973790))
    
    async def await_disconnect(self, player: NewPlayer):
        try:
            await asyncio.sleep(120)
            await player.disconnect()
        except asyncio.CancelledError:
            raise
        finally:
            pass
    
    async def coroutinePlay(self, player):
        player.updateAvg(0)

        if player.getAvg() >= GLOBAL_RATE:
            secs = ((player.getAvg() * 60) / (GLOBAL_RATE * 60)) * 60
            if(secs >= 60):
                out = f'{int(secs/60)}m {int(secs%60)}s'
            else:
                out = f'{int(secs)}s'
            await player.send(embed=discord.Embed(description = f'Global rate exceeded. Sleeping for {out}.',
                                                  colour = 1973790))
            await asyncio.sleep(secs)

        tracks = None

        while tracks == None:
            tracks, query = await self.acquire_tracks(player)

            if not tracks:
                return await player.send(embed=discord.Embed(description = f"Could not find any songs with the query '*{query}*'. Skipping.",
                                                  colour = 1973790))
                pass
        
        player.current = tracks
        await player.play(player.current)
    
    async def on_node_event(self, event):
        if isinstance(event, wavelink.events.TrackEnd):
            player = event.player
            track = player.current

            if len(player.queue) > 0:
                await self.coroutinePlay(player)
            else:
                player.disconnect_task = asyncio.create_task(self.await_disconnect(player))
                await player.disconnect_task

        if isinstance(event, wavelink.events.TrackStart):
            player = event.player
            track = player.current

            if(player.disconnect_task):
                player.disconnect_task.cancel()

            print(f'Playing a song in {player.guild_id}: {track.title}')

            await self.send_song_info(player, track)

        if isinstance(event, wavelink.events.TrackException):
            player = event.player
            track = player.current
            error = event.error
            
            await player.send(embed=discord.Embed(description = f'Error while attempting to play ```css\n{track} : {error}\n```',
                                                  colour = 1973790))
            
            
        
