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
app_commands_bot = app_commands
tree = app_commands_bot.CommandTree(bot_client)

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

    print('Login!!!')
    bool_VC_connected = False
    Queue_current = 0
    Queue_length_sound = 0

    # Database Initialization
    server_db = db.server_table()
    member_db = db.member_table()

    await tree.sync()

# ボイチャ入室通知
@bot_client.event
async def on_voice_state_update(member, before, after):

    global server_db
    global member_db

    # MMMR自動退出処理
    global bool_VC_connected
    if bool_VC_connected and after.channel is None:
        if member.id != bot_client.user.id:
            if member.guild.voice_client.channel is before.channel:
                num_of_member = 0
                for i_list_in_voice in range(len(member.guild.voice_client.channel.members)):
                    num_of_member += not member.guild.voice_client.channel.members[i_list_in_voice].bot
                    if num_of_member == 0: # 現在残っているbotでないユーザが0のとき
                        await asyncio.sleep(1)
                        await member.guild.voice_client.disconnect()
                        bool_VC_connected = False
    # MMMR自動退出処理おわり

    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
    server_id = member.guild.id
    channel_id_notify_str, status_notify = server_db.get_metrics(server_id,"notify_channel")
    channel_id_dnd_str, status_dnd = server_db.get_metrics(server_id,"dnd_channel")

    if status_notify == 0:
        channel_id_notify = int(channel_id_notify_str)
    else:
        print("notice: notify channel id is not registered.")
        return
    
    if channel_id_dnd_str == None:
        channel_id_dnd = None
    else:
        channel_id_dnd = int(channel_id_dnd_str)

    print(channel_id_notify)
    print(type(channel_id_notify))

    print(channel_id_dnd)
    print(type(channel_id_dnd))

    member_bool_notify, status_member_notify = member_db.get_bool_notify(member.id,server_id)
        
    botRoom = bot_client.get_channel(channel_id_notify)

    # 入室通知（画面共有に反応しないように分岐）
    if after.channel is not None and after.channel is not before.channel:
        if before.channel is None: # 参加
            if channel_id_dnd is not None:
                if after.channel.id == channel_id_dnd:
                    return
            if status_member_notify == 0 and member_bool_notify == 0:
                return
            notify_name, status = member_db.get_metrics(member.id, server_id, "notify_name")
            if status == 0:
                print("vc entry: notify name")
                await botRoom.send( notify_name + " が参加しました!")
            else:
                print("vc entry: default name")
                await botRoom.send( member.name + " が参加しました!")
    if before.channel is not None and after.channel is None: # 退出
        if channel_id_dnd is not None:
            if before.channel.id == channel_id_dnd:
                return
        if len(before.channel.members) == 0: # 誰も居なくなった場合
            if status_member_notify == 0 and member_bool_notify == 0:
                return
            await botRoom.send(before.channel.name + " に誰もいなくなりました")

@tree.command(name="set_notify_ch",description="入室通知先テキストチャンネルを設定します")
@app_commands_bot.describe(channel="入室通知先のチャンネルIDを入力してください")
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
@app_commands_bot.describe(channel="非通知ボイスチャンネルのチャンネルIDを入力してください")
async def set_dnd_ch_command(interaction: discord.Interaction,channel:str):
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

@tree.command(name="set_user_name",description="入室通知での通知名を設定します")
@app_commands_bot.describe(username="入室通知で表示するユーザー名を入力してください")
async def set_user_name_command(interaction: discord.Interaction,username:str):
    global member_db

    member_id = interaction.user.id
    guild_id = interaction.guild_id
    timeout_value = 10
    
    while 1:
        status = member_db.set_metrics(member_id, guild_id, "notify_name", username)
        if status == 0:
            break
        timeout_value += 1
        if timeout_value > 10:
            print("/set_user_name: setting timeout")
            break

    return_text = "通知名を " + username + " に設定しました"
    await interaction.response.send_message(return_text,ephemeral=True)

@tree.command(name="set_notify_user",description="入室通知の有無を設定します（ユーザ単位）")
@app_commands_bot.describe(on_off="on または off と入力してください")
async def set_notify_user_command(interaction: discord.Interaction,on_off:str):
    global member_db

    member_id = interaction.user.id
    guild_id = interaction.guild_id
    timeout_value = 10

    if on_off == "on":
        bool_notify_user = 1
        return_text = "通知をオンに設定しました"
    elif on_off == "off":
        bool_notify_user = 0
        return_text = "通知をオフに設定しました"
    else:
        return_text = "オプションは on または off と入力してください"
        await interaction.response.send_message(return_text,ephemeral=True)
        return
    
    while 1:
        status = member_db.set_bool_notify(member_id, guild_id, bool_notify_user)
        if status == 0:
            break
        timeout_value += 1
        if timeout_value > 10:
            print("/set_notify_user: setting timeout")
            return_text = "エラーが発生しました"
            await interaction.response.send_message(return_text,ephemeral=True)
            return

    await interaction.response.send_message(return_text,ephemeral=True)

bot_client.run(os.environ['DISCORD_KEY'])