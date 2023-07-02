import os
import asyncio
import re

import discord
from discord.ext import commands
from discord.channel import VoiceChannel
from discord.player import FFmpegPCMAudio
from discord import app_commands

from collections import deque
#import dropbox

from dotenv import load_dotenv

import server_member_db as db
from voicevox import text_to_speech

intents = discord.Intents.default()
intents.message_content = True

bot_client = discord.Client(intents=intents)
app_commands_bot = app_commands
tree = app_commands_bot.CommandTree(bot_client)

AudioQ = None
TextQ = None
lengthQ = 10

load_dotenv()
url_voicevox = os.environ['URL_VOICEVOX']
print(type(url_voicevox))

URL_pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"

MMMR_guild_status = dict()

# 起動時
@bot_client.event
async def on_ready():
    global dict_bool_VC_connected # ボイスチャンネルに接続しているかどうか（bool）
    global Queue_current
    global Queue_length_sound
    global MMMR_guild_textchannel_id
    global server_db
    global member_db

    print('Login!!!')
    MMMR_guild_textchannel_id = dict()
    dict_bool_VC_connected = dict()
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
    server_id = member.guild.id

    # MMMR自動退出処理
    global dict_bool_VC_connected
    if server_id in dict_bool_VC_connected:
        if dict_bool_VC_connected[server_id] and after.channel is None:
            if member.id != bot_client.user.id:
                if member.guild.voice_client.channel is before.channel:
                    num_of_member = 0
                    for i_list_in_voice in range(len(member.guild.voice_client.channel.members)):
                        num_of_member += not member.guild.voice_client.channel.members[i_list_in_voice].bot
                        if num_of_member == 0: # 現在残っているbotでないユーザが0のとき
                            await asyncio.sleep(1)
                            await member.guild.voice_client.disconnect()
                            dict_bool_VC_connected[server_id] = False
    # MMMR自動退出処理おわり

    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
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
                await botRoom.send( notify_name + " が参加しました！")
            else:
                print("vc entry: default name")
                await botRoom.send( member.name + " が参加しました！")
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

@tree.command(name="connect",description="MMMRをボイスチャンネルに入室させます")
async def connect_command(interaction: discord.Interaction):

    global MMMR_guild_textchannel_id
    global dict_bool_VC_connected
    global author_voicechannel
    global VoiceClient_MMMR
    global AudioQ
    global TextQ
    global itr_AudioQ
    global itr_TextQ

    guild_id = interaction.user.guild.id

    if guild_id in dict_bool_VC_connected:
        if dict_bool_VC_connected[guild_id] == True:
            return_text = "このコマンドはMMMRが入室していない時のみ利用できます"
            await interaction.response.send_message(return_text)
            return

    author_voicechannel = interaction.user.voice.channel
    if author_voicechannel.id is None:
        return_text = "入室先ボイスチャンネルが特定できませんでした"
        await interaction.response.send_message(return_text,ephemeral=True)
        return
    
    VoiceClient_MMMR = await VoiceChannel.connect(author_voicechannel)
    dict_bool_VC_connected[guild_id] = True
    AudioQ = deque([], lengthQ)
    itr_AudioQ = 0
    TextQ = deque([], lengthQ)
    itr_TextQ = 0
    MMMR_guild_textchannel_id[guild_id] = interaction.channel_id
    return_text = "MMMR が参加しました！\n音声 VOICEVOX:ずんだもん"
    await interaction.response.send_message(return_text)


@tree.command(name="disconnect",description="ボイスチャンネルからMMMRを退出させます")
async def disconnect_command(interaction: discord.Interaction):
    global author_voicechannel
    global VoiceClient_MMMR
    global MMMR_guild_textchannel_id
    global dict_bool_VC_connected
    global TextQ
    global itr_TextQ
    global AudioQ
    global itr_AudioQ

    guild_id = interaction.user.guild.id

    if guild_id not in dict_bool_VC_connected:
        return_text = "このコマンドはMMMRが入室している時のみ利用できます"
        await interaction.response.send_message(return_text)
        return
    else:
        if dict_bool_VC_connected[guild_id] == False:
            return_text = "このコマンドはMMMRが入室している時のみ利用できます"
            await interaction.response.send_message(return_text)
            return

    VoiceClient_MMMR.stop()
    print("TTS is stopped!")
    await VoiceClient_MMMR.disconnect()
    dict_bool_VC_connected[guild_id] = False
    del MMMR_guild_textchannel_id[guild_id]

    itr_TextQ = 0
    itr_AudioQ = 0
    TextQ.clear()
    AudioQ.clear()

    return_text = "MMMR が退出しました！"
    await interaction.response.send_message(return_text)

@tree.command(name="stop",description="MMMRの読み上げを停止します")
async def stop_command(interaction: discord.Interaction):
    global VoiceClient_MMMR
    print("MMMR stop()")
    for i in range(len(AudioQ) + 1):
        VoiceClient_MMMR.stop()
        await asyncio.sleep(0.05)
    return_text = "MMMR を黙らせました！"
    await interaction.response.send_message(return_text)

# TTS関係
@bot_client.event
async def on_message(message):
    global VoiceClient_MMMR
    global MMMR_guild_textchannel_id
    global dict_bool_VC_connected
    global itr_TextQ
    global TextQ

    if message.guild == None:
        return
    
    guild_id = message.guild.id
    speaker_id = 3
    if guild_id in dict_bool_VC_connected and guild_id in MMMR_guild_textchannel_id:
        if message.channel.id == MMMR_guild_textchannel_id[guild_id] and message.author != bot_client.user and dict_bool_VC_connected[guild_id] == 1:
            if re.search(URL_pattern, message.content):
                message.content = re.sub(URL_pattern, 'URL', message.content)
            speechdata = text_to_speech(message.content, url_voicevox, speaker_id)
            itr_TextQ = add_queue_tts(speechdata, itr_TextQ, TextQ)
            if not VoiceClient_MMMR.is_playing():
                print("play_sound()")
                play_sound(TextQ)
        else:
            return

def add_queue_tts(raw_data, itr_TextQ, TextQ):
    filename = str(itr_TextQ) + ".wav"

    with open(filename, "wb") as out:
        out.write(raw_data)
        print("Audio content written to file " + filename)

    TextQ.append(filename)
    itr_TextQ = itr_TextQ + 1
    if itr_TextQ > 9:
        itr_TextQ = 0
    return itr_TextQ

def play_sound(TextQ):
    print(len(TextQ))
    if len(TextQ) == 0:
        return
    else:
        popfile = TextQ.popleft()
        print("playing " + popfile)
        source = FFmpegPCMAudio("./"+popfile)
        VoiceClient_MMMR.play(source, after=lambda e:play_sound(TextQ))

def add_queue_sound(sound_file, itr_AudioQ, AudioQ):
    AudioQ.append(sound_file)
    itr_AudioQ = itr_AudioQ + 1
    if itr_AudioQ > 9:
        itr_AudioQ = 0
    return itr_AudioQ
   
bot_client.run(os.environ['DISCORD_KEY'])