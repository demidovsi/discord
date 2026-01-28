import time

import discord
from discord.ext import commands
import asyncio

import common_bot
import common
import config

intents = discord.Intents.default()
intents.message_content = True  # ❗ Обязателен для чтения текста сообщений
intents.guilds = True
intents.messages = True

version = '1.1.1 от 2025-07-09'
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот вошёл как {bot.user}")
    t = time.time()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, lambda: common.write_log_db(
            'START', common_bot.source, 'Старт сканирования сообщений Discord (messages)' +
                                        '\n - version: ' + version +
                                        '\n - host: ' + config.URL +
                                        '\n - schema: ' + config.schema_name,
            law_id='members',
            file_name=common.get_computer_name()))

    guild = discord.utils.get(bot.guilds, name="Urban Heat Official")  # или bot.get_guild(ID)

    count, count_new = 0, 0
    for channel in guild.text_channels:
        if channel.name != 'lore-discussions':
            continue
        print(f"\n📁 Канал: #{channel.name}")
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                count += 1
                # print(f"[{message.created_at}] {message.author}")
                if not await common_bot.exist_message(message.id):
                    # print("⛔ Сообщение уже базе данных")
                # else:
                    await common_bot.insert_message(message)
                    count_new += 1
                    # print("✅ Сообщение успешно сохранено в базу данных")
        except discord.Forbidden:
            print("⛔ Нет доступа к этому каналу")
        except discord.HTTPException as e:
            print(f"⚠️ Ошибка: {e}")
    finish_text = (f"Сканирование сообщений (messages) завершено.\nВсего сообщений на сервере: "
                   f"{count},\n - добавлено: {count_new}.")
    await loop.run_in_executor(None, lambda: common.write_log_db('Sleep', common_bot.source, finish_text,
                                                                 td=time.time() - t, law_id='messages',
                        file_name=common.get_computer_name()))

    await bot.close()

# Токен бота в config.py
bot.run(config.discord_token)
