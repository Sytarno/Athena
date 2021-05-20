from nltk.stem import LancasterStemmer, PorterStemmer, WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk import word_tokenize

import discord
import os
import re

from itertools import product
from discord.ext import commands
from discord.utils import get

def validChannel(channel):
    authorizedChannels = read('.authorizedChannels.txt')
    return str(channel.id) in authorizedChannels

def read(path):
    with open(path, 'r') as in_file:
        return in_file.read().split('\n')

import nltk

#nltk.download('stopwords')
#nltk.download('averaged_perceptron_tagger')

class Node:
    def __init__(self):
        aa = 1

#--------------------------------------------------------------build graph
        

#------------------------------------------------------------------


stop_words = set(stopwords.words('english'))
ps = PorterStemmer()

def tokenize(sentence):
    stem = ps.stem(sentence)
    tokens = word_tokenize(stem)
    clean_tokens = [w for w in tokens if not w in stop_words]
    tagged = nltk.pos_tag(clean_tokens)

    return tagged

class NLP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desc = 'NLP test, designed for basic commands. Responds to its nickname.'

    @commands.Cog.listener()
    async def on_message(self, message):
        if validChannel(message.channel) and message.guild and not message.author.bot:
            name = message.guild.get_member(353029839860662274).display_name.lower()

            if re.search(r'\b' + name + r'\b', message.content):
                ctx = await self.bot.get_context(message)
                tk = tokenize(message.content)

                await message.channel.send(tk)

    async def response_hello(self, ctx, message=""):
        await ctx.send("hello!")

