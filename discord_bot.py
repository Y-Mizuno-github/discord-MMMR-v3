import os
import traceback
import asyncio
import html
import re
import random

import discord
from discord.ext import commands
from discord.channel import VoiceChannel
from discord.player import FFmpegPCMAudio
from discord import app_commands

from collections import deque
#import dropbox
#import requests

from dotenv import load_dotenv

import server_member_db as db

intents = discord.Intents.default()
intents.message_content = True

bot_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot_client)

Audio_queue = None
length_queue = 10

URL_pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"

load_dotenv()

# 起動時
@bot_client.event
async def on_ready():
    global bool_VC_connected # ボイスチャンネルに接続しているかどうか（bool）
    global Queue_current
    global Queue_length_sound

    global server_db
    global member_db

    await tree.sync()

    print('Login!!!')
    bool_VC_connected = False
    Queue_current = 0
    Queue_length_sound = 0

    # Database Initialization
    server_db = db.server_table()
    member_db = db.member_table()

    all_dnd_channel = dict()

# ボイチャ入室通知
@bot_client.event
async def on_voice_state_update(member, before, after):
    global bool_VC_connected

    global server_db
    global member_db

    global all_dnd_channel
    
    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
    server_id = member.guild.id
    channel_id_notify_str, status_notify = server_db.get_metrics(server_id,"notify_channel")
    channel_id_dnd_str, status_dnd = server_db.get_metrics(server_id,"dnd_channel")

    channel_id_notify = int(channel_id_notify_str)
    channel_id_dnd = int(channel_id_dnd_str)

    print(channel_id_notify)
    print(type(channel_id_notify))

    print(channel_id_dnd)
    print(type(channel_id_dnd))

    member_bool_dnd, status_member_dnd = member_db.get_bool_DND(member.id,server_id)

    if status_notify != 0 or status_dnd != 0:
        print("Error: server_id is not registered.")
        
    botRoom = bot_client.get_channel(channel_id_notify)

    # 入室通知（画面共有に反応しないように分岐）
    if after.channel is not None and after.channel is not before.channel:
        if before.channel is None: # 参加
            if after.channel.id == channel_id_dnd:
                return
            if status_member_dnd == 0 and member_bool_dnd == 1:
                all_dnd_channel[after.channel.id] = True
                return
            notify_name, status = server_db.get_metrics(member.id,"notify_name")
            if status == 0:
                await botRoom.send( notify_name + " が参加しました!")
            else:
                await botRoom.send( member.name + " が参加しました!")
    if before.channel is not None and after.channel is None: # 退出
        if before.channel.id == channel_id_dnd:
            return
        if len(before.channel.members) == 0: # 誰も居なくなった場合
            if status_member_dnd == 0 and member_bool_dnd == 1:
                return
            await botRoom.send(before.channel.name + " に誰もいなくなりました")

    if bool_VC_connected and after.channel is None: #  MMMR自動退出処理
        if member.id != bot_client.user.id:
            if member.guild.voice_client.channel is before.channel:
                num_of_member = 0
                for i_list_in_voice in range(len(member.guild.voice_client.channel.members)):
                    num_of_member += not member.guild.voice_client.channel.members[i_list_in_voice].bot
                    if num_of_member == 0: # 現在残っているbotでないユーザが0のとき
                        await asyncio.sleep(1)
                        await member.guild.voice_client.disconnect()
                        bool_VC_connected = False


@tree.command(name="set_notify_ch",description="入室通知先テキストチャンネルを設定します")
async def set_notify_ch_command(interaction: discord.Interaction,channel:str):
    global server_db

    guild_id = interaction.guild_id

    timeout_value = 10

    while 1:
        status = server_db.set_metrics(guild_id, "notify_channel", channel)
        if status == 0:
            break
        timeout_value += 1
        if timeout_value > 10:
            print("/set_notify_ch: setting timeout")
            break

    return_text = "入室通知先テキストチャンネルが設定されました"
    await interaction.response.send_message(return_text,ephemeral=True)

@tree.command(name="set_dnd_ch",description="非通知ボイスチャンネルを設定します")
async def set_dnd_ch_command(interaction: discord.Interaction,channel:str):#デフォルト値を指定
    global server_db

    guild_id = interaction.guild_id
    timeout_value = 10
    
    while 1:
        status = server_db.set_metrics(guild_id, "dnd_channel", channel)
        if status == 0:
            break
        timeout_value += 1
        if timeout_value > 10:
            print("/set_DND_ch: setting timeout")
            break

    return_text = "非通知ボイスチャンネルが設定されました"
    await interaction.response.send_message(return_text,ephemeral=True)

bot_client.run(os.environ['DISCORD_KEY'])