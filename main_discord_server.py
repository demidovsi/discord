import time

import discord
from discord.ext import commands

import common_bot
import common
import config


version = '1.2.3 от 2025-08-11'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True  # <--- ОБЯЗАТЕЛЬНО!
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(time.ctime(), f'Запущен как {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await common_bot.insert_message(message)
    print(time.ctime(), '--->   Новое сообщение от {}: {}'.format(message.author.name, message.content[:100]))
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    """
    Обрабатывает событие присоединения участника к серверу.

    :param member: Участник, который присоединился.
    """
    await common_bot.write_value_join_member(member, 1, in_log=True)
    print(time.ctime(), f"{member} присоединился к серверу {member.guild.name}")


@bot.event
async def on_member_remove(member):
    """
    Обрабатывает событие удаления участника с сервера.

    :param member: Участник, который покинул сервер.
    :type member: Discord.member
    """
    # Записывает информацию о покидании участником сервера в базу данных.
    await common_bot.write_value_join_member(member, -1, in_log=True)
    print(time.ctime(), f"{member} покинул сервер {member.guild.name}")


@bot.event
async def on_presence_update(before, after):
    if before.status != after.status:
        if after.status.value in ['offline', 'online']:
            await  common_bot.insert_status_member(after)
        # print(time.ctime(), f"{after.name} сменил статус с {before.status} на {after.status}")


@bot.event
async def on_guild_channel_create(channel):
    await common_bot.insert_channel(channel)
    print(time.ctime(), f"🆕 Канал создан: {channel.name}")


@bot.event
async def on_guild_channel_delete(channel):
    print(time.ctime(), f"🗑️ Канал удалён: {channel.name}")


@bot.event
async def on_guild_channel_update(before, after):
    if before.name != after.name:
        print(time.ctime(), f"✏️ Переименование канала: {before.name} → {after.name}")


# _, is_ok, token, _ = common.login_admin()
common.write_log_db(
    '✈StartUp', common_bot.source, 'Старт бота работы с Discord \n' +
                             ' - version: ' + version +
                             '\n - host: ' + config.URL +
                             '\n - schema: ' + config.schema_name,
    file_name=common.get_computer_name())
bot.run(config.discord_token)
