# -*- coding: utf-8 -*-
import discord
import asyncio
from discord.ext import commands
from pathlib import Path
from discord.sinks import MP3Sink
import pydub  # pip install pydub==0.25.1
import time
import youtube_dl

# 123
import os

# speech-to-text (python stt)
import speech_recognition as sr

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

# yt search via api
from googleapiclient.discovery import build
import random

bot = commands.Bot(command_prefix='!', intents=intents)

#discord Token

with open('discordToken.txt', 'r') as file:
    BOT_TOKEN = file.read().replace('\n', '')

#ключ api google YouTube V3 / api key google YouTube V3
with open('YouTubeV3Token.txt', 'r') as file:
    dvKey = file.read().replace('\n', '')

MIN_FILE_SIZE = 10 * 1024


async def finished_callback(sink: MP3Sink, channel: discord.TextChannel, filename: str = "test.wav"):
    mention_strs = []
    audio_segs: list[pydub.AudioSegment] = []
    files: list[discord.File] = []

    longest = pydub.AudioSegment.empty()

    for user_id, audio in sink.audio_data.items():
        mention_strs.append(f"<@{user_id}>")

        seg = pydub.AudioSegment.from_file(audio.file, format="mp3")

        # самый длинный аудиосегмент (the longest audio segment)
        if len(seg) > len(longest):
            audio_segs.append(longest)
            longest = seg
        else:
            audio_segs.append(seg)

        audio.file.seek(0)
        files.append(discord.File(audio.file, filename=f"{user_id}.mp3"))

    for seg in audio_segs:
        longest = longest.overlay(seg)

    with open(filename, "wb") as f:
        longest.export(f, format="wav")


async def check_voice_channels():
    while not bot.is_closed():
        for guild in bot.guilds:
            for voice_channel in guild.voice_channels:
                if voice_channel.members:
                    if not voice_channel.guild.voice_client:
                        await voice_channel.connect()
                        print(f"Подключен to {voice_channel.name}")

#кринж / cringe))))

        path_q = Path("test.mp3")
        path_w = Path("test.wav")
        path_e = Path("backwash.wav")
        path_p = Path("play.wav")


# проигрывание музыки по ссылке / music via link (not included), can be set to command from text chat      


        if path_q.is_file():
            for voice_client in bot.voice_clients:
                if voice_client.is_connected() and not voice_client.is_playing():
                    
                    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
                    
                    def get_audio_url(url):
                        with youtube_dl.YoutubeDL({}) as ydl:
                            info = ydl.extract_info(url, download=False)
                            return info['formats'][0]['url']
                    
                    if not voice_client.is_connected():
                        await voice_client.connect()
                    
                    audio_url = get_audio_url(url)
                    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_url))
                    source = discord.PCMVolumeTransformer(source, volume=0.02)

                    def after_playing(error):
                        if path_q.is_file():
                            path_q.unlink()

                    voice_client.play(source, after=after_playing)


# какую музыку включить? what music to play?    


        elif path_p.is_file():
            print ("Слушаю название музыки...")
            for voice_client in bot.voice_clients:
                if voice_client.is_connected() and not voice_client.is_playing():
                    print("Какую музыку включить?")
                    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio('song.mp3'))
                    source = discord.PCMVolumeTransformer(source, volume=0.1)

                    def after_playing(error):
                        if path_p.is_file():
                            os.rename(path_p, "startplaying.wav")
            voice_client.play(source, after=after_playing)
            time.sleep(0.5)
            vc = bot.voice_clients[0] if bot.voice_clients else None
            if vc:
                print("Запись запроса музыки (5sec)")
                filename = "song.wav"
                vc.start_recording(
                    MP3Sink(),
                    finished_callback,
                    voice_channel.name,
                    filename,
                    
                )
                time.sleep(5)
                print("stop recording (song.wav)")
                vc.stop_recording()   

        SONG_FILE_PATH = Path("song.wav")

        if SONG_FILE_PATH.is_file():
            if os.path.getsize(SONG_FILE_PATH) <= MIN_FILE_SIZE:
                os.remove(SONG_FILE_PATH)
                os.remove(Path("startplaying.wav"))
                pass
            else:
                print("преобразование запроса музыки") # music request conversion
                r = sr.Recognizer()
                try:
                    with sr.AudioFile(SONG_FILE_PATH.resolve().as_posix()) as source:
                        audio = r.record(source)
                    
                    text = r.recognize_google(audio, language="ru-RU") # change to your language
                    print(text)

                    # time.sleep(0.5)

                    query = text
                    os.remove(SONG_FILE_PATH)
                    os.remove(Path("startplaying.wav"))
                    
                    # поиск через googleapi (search via google api) - need key

                    def search_video(query):
                        youtube = build('youtube', 'v3', developerKey=dvKey)
                        request = youtube.search().list(
                            q=query,
                            part='id',
                            maxResults=3,  # количество результатов (number of results per request)
                            type='video',
                            # videoDuration='short'  # длительность музыки (duration of found music)
                        )
                        response = request.execute()
                        video_ids = [item['id']['videoId'] for item in response['items']]
                        random.shuffle(video_ids)  # перемешать
                        return [f'https://www.youtube.com/watch?v={video_id}' for video_id in video_ids]

                    video_urls = search_video(query)

                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'extractor_retries': 'auto',
                    }

                    random_video_url = random.choice(video_urls)  # случайный URL из списка

                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(random_video_url, download=False)
                        url = info['formats'][0]['url']

                        options = {
                            'options': '-vn',
                            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        }

                        source = discord.FFmpegPCMAudio(url, **options)
                        source = discord.PCMVolumeTransformer(source, volume=0.06) #you can change volume (default 1.0)
                        vc = voice_client
                        vc.play(source)
                        


                except (TypeError, sr.UnknownValueError, sr.RequestError) as e:
                    if isinstance(e, TypeError):
                        print("Ошибка чтения аудиофайла")
                    elif isinstance(e, sr.UnknownValueError):
                        print("Ошибка распознавания речи")
                    elif isinstance(e, sr.RequestError):
                        print("Ошибка соединения с сервисом распознавания речи")
                    text = ""
                    os.remove(SONG_FILE_PATH)
                    os.remove(Path("startplaying.wav"))
                            

                await asyncio.sleep(0.5)

            
# вызвать комманду (call command)


        elif path_e.is_file():
            print ("Слушаю запрос...")
            for voice_client in bot.voice_clients:
                if voice_client.is_connected() and voice_client.is_playing():
                    voice_client.stop()
                print("Говори, я слушаю")
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio('answer.mp3'))
                source = discord.PCMVolumeTransformer(source, volume=0.1)

                def after_playing(error):
                    if path_e.is_file():
                        path_e.unlink()
            
            voice_client.play(source, after=after_playing)
            time.sleep(1)
            vc = bot.voice_clients[0] if bot.voice_clients else None
            if vc:
                print("Запись запроса (4sec)")
                filename = "answer.wav"
                vc.start_recording(
                    MP3Sink(),
                    finished_callback,
                    voice_channel.name,
                    filename,
                )
                time.sleep(4)
                print("stop recording (save answer.wav)")
                vc.stop_recording()


# стандартный запрос(call out)


        else:
            vc = bot.voice_clients[0] if bot.voice_clients else None
            if vc:
                if path_w.is_file() or path_p.is_file() or Path("startplaying.wav").is_file() or Path("song.wav").is_file() or Path("answer.wav").is_file():
                    pass
                else:
                    print("\n + (Жду запроса)")
                    print("Начало записи (5 секунд)")
                    try:
                        vc.start_recording(
                            MP3Sink(),
                            finished_callback,
                            voice_channel.name,
                        )
                        await asyncio.sleep(3)
                        print("Завершение записи (test.wav)+\n")
                        vc.stop_recording()
                    except discord.sinks.errors.RecordingException as e:
                        print(f"Ошибка при завершении записи: {str(e)} +\n")
                        pass
            
        await asyncio.sleep(0.5)

AUDIO_FILE_PATH = Path("test.wav")
ANSWER_FILE_PATH = Path("answer.wav")

async def transcribe_audio():
    text = ""

    while True:
        if AUDIO_FILE_PATH.is_file() and os.path.getsize(AUDIO_FILE_PATH) >= MIN_FILE_SIZE:
            print("преобразование запроса")
            print(os.path.getsize(AUDIO_FILE_PATH))
            r = sr.Recognizer()
            try:
                with sr.AudioFile(AUDIO_FILE_PATH.resolve().as_posix()) as source:
                    audio = r.record(source)
                # гугл stt
                text = r.recognize_google(audio, language="ru-RU")
                print(text)
                
                # keywords in a voice request \/

                if "Test" in text or "test" in text or "тест" in text or "Тест" in text:
                    print("Найден +\n")
                    
                    os.rename(AUDIO_FILE_PATH, "backwash.wav")
                else:
                    print("не найден +\n")
                    os.remove(AUDIO_FILE_PATH)

            except (TypeError, sr.UnknownValueError, sr.RequestError) as e:
                if isinstance(e, TypeError):
                    print("Ошибка чтения аудиофайла")
                elif isinstance(e, sr.UnknownValueError):
                    print("Ошибка распознавания речи")
                elif isinstance(e, sr.RequestError):
                    print("Ошибка соединения с сервисом распознавания речи")
                text = ""
                os.remove(AUDIO_FILE_PATH)

        elif ANSWER_FILE_PATH.is_file() and os.path.getsize(ANSWER_FILE_PATH) >= MIN_FILE_SIZE:
            print("преобразование вопроса...")
            r = sr.Recognizer()
            try:
                with sr.AudioFile(ANSWER_FILE_PATH.resolve().as_posix()) as source:
                    audio = r.record(source)  # запись файла
                # гугл stt
                text = r.recognize_google(audio, language="ru-RU")
                print(text)

                # keywords in a voice request (Turn on the music) \/

                if "Включи музыку" in text or "музыку" in text or "Музыку" in text or "включи" in text or "включи музыку" in text:
                    print("Включить музыку? +\n")
                    os.rename(ANSWER_FILE_PATH, "play.wav")
                else:
                    print("не найден +\n")
                    os.remove(ANSWER_FILE_PATH)

            except (TypeError, sr.UnknownValueError, sr.RequestError) as e:
                if isinstance(e, TypeError):
                    print("Ошибка чтения аудиофайла")
                elif isinstance(e, sr.UnknownValueError):
                    print("Ошибка распознавания речи")
                elif isinstance(e, sr.RequestError):
                    print("Ошибка соединения с сервисом распознавания речи")
                text = ""
                os.remove(ANSWER_FILE_PATH)

        else:
            if AUDIO_FILE_PATH.is_file():
                if os.path.getsize(AUDIO_FILE_PATH) < MIN_FILE_SIZE:
                    os.remove(AUDIO_FILE_PATH)
            if ANSWER_FILE_PATH.is_file():
                if os.path.getsize(ANSWER_FILE_PATH) < MIN_FILE_SIZE:
                    os.remove(ANSWER_FILE_PATH)



        await asyncio.sleep(0.5)


# запуск (start bot)


async def start_bot():
    await bot.login(BOT_TOKEN)
    await bot.connect()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    bot.loop.create_task(check_voice_channels())
    bot.loop.create_task(transcribe_audio())

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return

    current_voice_channel = member.guild.voice_client

    if not after.channel:
        if current_voice_channel:
            await current_voice_channel.disconnect()
            print(f"\n + Disconnected from {before.channel.name}")
    else:
        if not current_voice_channel or current_voice_channel.channel != after.channel:
            if current_voice_channel:
                await current_voice_channel.disconnect()
                print(f"Disconnected from {before.channel.name} + \n")

            voice_channel = after.channel
            new_voice_client = await voice_channel.connect()
            print(f"Connected to {after.channel.name}")

@bot.command()
async def leave(ctx: discord.ApplicationContext):
    vc: discord.VoiceClient = ctx.voice_client

    if not vc:
        return await ctx.respond("не в канале")

    await vc.disconnect()

    await ctx.respond("Выхожу!")

def main():
    bot.loop.run_until_complete(start_bot())

if __name__ == "__main__":
    main()
