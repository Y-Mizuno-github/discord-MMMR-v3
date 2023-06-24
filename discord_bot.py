import os
import traceback
import asyncio
import html
import re
import random

import sqlite3

from discord.ext import commands
from discord.channel import VoiceChannel
from discord.player import FFmpegPCMAudio

from collections import deque
import dropbox
import requests

token = getenv('DISCORD_BOT_TOKEN')
guild_ID_1_str = getenv('GUILD_ID')
guild_ID_1 = int(guild_ID_1_str)
APP_KEY = getenv('DROPBOX_APP_KEY')
APP_SECRET = getenv('DROPBOX_APP_SECRET')
REFRESH_TOKEN = getenv('DROPBOX_REFRESH_TOKEN')

TEXT_CHANNEL_ENV = getenv('TEXT_CHANNEL')
TEXT_CHANNEL_ve = int(TEXT_CHANNEL_ENV)
DND_CHANNEL = 889433349951733770
Text_Channel = 0
Audio_queue = None
length_queue = 10
guild_ID = [guild_ID_1]
URL_pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"

bot_client = commands.Bot(command_prefix = '/')
inter_client = InteractionClient(bot_client, test_guilds=[guild_ID_1])

db_exist = 0

# 起動時
@bot_client.event
async def on_ready():
    global Voice_State
    global Queue_num
    global Queue_num_sound

    global db_exist

    print('Login!!!')
    Voice_State = 0
    Queue_num = 0
    Queue_num_sound = 0

    dbname = 'discord.db'
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()

    curs.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="discord-server-ids"')
    if curs.fetchone() == (0,): # not exist
        db_exist = 0
    else: # exist
        db_exist = 1