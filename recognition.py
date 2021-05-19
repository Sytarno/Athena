from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk import word_tokenize

import discord
import os
import re

from discord.ext import commands
from discord.utils import get

def validChannel(channel):
    authorizedChannels = read('.authorizedChannels.txt')
    return str(channel.id) in authorizedChannels

def read(path):
    with open(path, 'r') as in_file:
        return in_file.read().split('\n')

import nltk
nltk.download('tagsets')
nltk.help.upenn_tagset()
#nltk.download('stopwords')
#nltk.download('averaged_perceptron_tagger')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

def tokenize(sentence):
    tokens = word_tokenize(sentence)
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

            if name in message.content.lower():
                await message.channel.send(tokenize(message.content))


