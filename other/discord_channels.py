import discord
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Бот вошёл как {client.user}')

    for guild in client.guilds:
        print(f'\n=== Сервер: {guild.name} ({guild.id}) ===\n')
        for channel in guild.channels:
            print(f"Тип: {type(channel).__name__}")
            print(f"  Название: {channel.name}")
            print(f"  ID: {channel.id}")
            print(f"  Категория: {channel.category}")
            print(f"  NSFW: {getattr(channel, 'is_nsfw', lambda: 'n/a')()}")
            print(f"  Позиция: {channel.position}")
            print(f"  Создан: {channel.created_at}")
            print("-" * 40)

    await client.close()

import config
client.run(config.discord_token)


"""
📦Структура канала (discord.TextChannel)
channel.id                  # int: уникальный ID канала
channel.name                # str: имя канала (без #)
channel.mention             # str: <#id> для упоминания канала
channel.guild               # discord.Guild: сервер, к которому принадлежит канал
channel.category            # discord.CategoryChannel | None: категория
channel.position            # int: позиция в списке каналов
channel.topic               # str | None: тема канала (если задана)
channel.nsfw                # bool: помечен ли как NSFW
channel.slowmode_delay      # int: задержка между сообщениями в секундах
channel.created_at          # datetime: дата создания
channel.last_message_id     # int | None: ID последнего сообщения
channel.type                # discord.ChannelType: тип канала (text, voice, news и т.д.)
channel.overwrites          # dict: права доступа (PermissionOverwrite)
channel.permissions_for(member)  # метод: возвращает итоговые права участника

🔊 Для голосового канала (discord.VoiceChannel) добавляются:
python
Копировать код
channel.bitrate             # int: битрейт
channel.user_limit          # int: лимит участников
channel.voice_states        # list: список пользователей в канале

📁 Для категории (discord.CategoryChannel):
python
Копировать код
channel.channels            # list: вложенные каналы

🧵 Для тредов (discord.Thread):
python
Копировать код
thread.id
thread.name
thread.parent               # канал, к которому относится тред
thread.owner_id
thread.archived             # bool
thread.locked               # bool
thread.auto_archive_duration
thread.message_count
thread.member_count

"""