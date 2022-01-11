from nltk.stem import LancasterStemmer, PorterStemmer, WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk import word_tokenize

import discord
import os
import re

from itertools import product
from discord.ext import commands
from discord.utils import get

dPATH = "data/"

def validChannel(channel):
    authorizedChannels = read(dPATH + '.authorizedChannels.txt')
    return str(channel.id) in authorizedChannels

def read(path):
    with open(path, 'r') as in_file:
        return in_file.read().split('\n')

import nltk

#nltk.download('stopwords')
#nltk.download('averaged_perceptron_tagger')

class Node:
    def __init__(self, name=None, param=None):
        self.name = name
        self.command = param


#--------------------------------------------------------------build graph
tree = {}
allowed = []

#defined to add a single path from root to end
def addPath(tree_dict, connections, command_str):
    h = hash(tuple(connections))
    for word in connections:
        if word not in allowed:
            allowed.append(word)
    tree[h] = command_str

'''def generateList(string):
    lst = string.split("-")
    o = []
    for v in lst:
        o.append(Node(v))

    return o'''

def generateList(string):
    return string.split("-")

addPath(tree, generateList("athena-hello"), "response_hello(ctx)")
addPath(tree, generateList("hi-athena"), "response_hello(ctx)")
addPath(tree, generateList("hello-athena"), "response_hello(ctx)")

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
        self.tree = tree
        self.allowed = allowed

    async def get_command(self, tokens):
        uniques = []
        valid = []
        
        for word, identifier in tokens:
            if identifier == "NN" and word not in self.allowed:
                uniques.append(word)
            if word in self.allowed:
                valid.append(word)

        '''if out[0] == '-':
            out = out[1:]
        if out[-1] == '-':
            out = out[:-1]'''

        h = hash(tuple(valid))
        cmd = None
        try:
            cmd = self.tree[h]
        except:
            pass
        
        return cmd

#---------------------------------------------------

        
    async def response_hello(self, ctx, message=""):
        await ctx.send("hello!")

#---------------------------------------------------


    @commands.Cog.listener()
    async def on_message(self, message):
        if validChannel(message.channel) and message.guild and not message.author.bot:
            name = message.guild.get_member(353029839860662274).display_name.lower()

            if re.search(r'\b' + name + r'\b', message.content):
                ctx = await self.bot.get_context(message)
                tk = tokenize(message.content)

                c = await self.get_command(tk)

                f = "self." + c
                await eval(f)
