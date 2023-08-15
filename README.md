# Athena
Discord bot made and maintained by me, sytarno / Evan Nguyen

# Changelog / WIP
8/14/23 - I have lost my cloud instance, so I'll have to forcibly downgrade to a 1 gb free instance.
Wavelink and pycord have changed significantly in the last 2 years, so the music player is currently broken. Will be attempting to replace it soon.

# Instructions

This bot will not run on its own. .env.txt is a missing file that contains the token and other private info I will not divulge.

In order to start this bot, add a new .env.txt (the extension is mandatory) with the following information line-separated:
- bot token
- author id
- bots own id (find on developer portal)

# Log

bot.py is the main core that is required to run. 
however, in order for youtube pull/push requests, lavalink.jar in the folder lavalink needs to run concurrently.

musicNew.py is the currently used cog for youtube through lavalink.
musicPl.py is deprecated and only serves as a backup; uses ffmpeg.


