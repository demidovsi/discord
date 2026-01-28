"""
Скрипт для получения списка участников сервера Discord и их сохранения в базу данных.
"""
from itertools import count
import time
import datetime
import json

import discord
import asyncio

import common
import common_bot
import config

version = '1.2.1 от 2025-07-09'
intents = discord.Intents.default()
intents.members = True  # 🔴 ОБЯЗАТЕЛЬНО для получения списка участников
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Бот вошёл как {bot.user}")
    while True:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, lambda: common.write_log_db(
            'START', common_bot.source, 'Старт опроса участников сервера Discord (members)' +
                                        '\n - version: ' + version +
                                        '\n - host: ' + config.URL +
                                        '\n - schema: ' + config.schema_name,
            law_id='members',
            file_name=common.get_computer_name()))
        # Чтение списка members.
        members = list()  # Список идентификатор существующих участников сервера.
        ans, is_ok, _ = await loop.run_in_executor(
            None, lambda: common.send_rest("v2/select/{schema}/nsi_discord_members?where=remove <> true".format(
                schema=config.schema_name), params={"columns": "member_id"}))
        if not is_ok:
            # Логирование ошибки при получении данных участника из БД.
            await loop.run_in_executor(
            None, lambda: common.write_log_db('ERROR', common_bot.source,
                '❌ Ошибка при получении участников из БД: {}'.format(ans),
                file_name=common.get_computer_name(), law_id='members', token=token
            ))
        else:
            # Преобразование ответа в JSON.
            ans = json.loads(ans)
            for data in ans:
                members.append(data['member_id'])


        t = time.time()
        _, is_ok, token, _ = common.login_admin()
        count, count_error, count_insert, count_remove = 0, 0, 0, 0
        for guild in bot.guilds:
            async for member in guild.fetch_members():
                result = await common_bot.insert_member(member, token=token)
                if result is None:
                    count_error += 1
                elif result:
                    count_insert += 1
                if result != True and str(member.id) in members:  # либо ошибка, либо существует - удаляем из members
                    members.remove(str(member.id))
                count += 1  # Считаем количество обработанных участников

        # Записывает информацию о покидании участником сервера в базу данных.
        date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for member_id in members:
            query = "update {schema}.nsi_discord_members set remove=true where member_id='{member_id}'".format(
                schema=config.schema_name, member_id=member_id)
            ans, is_ok, _ = await loop.run_in_executor(
                None, lambda: common.send_rest('v2/execute', 'PUT', params={"script": query}, token_user=token))
            if not is_ok:
                await loop.run_in_executor(None, lambda: common.write_log_db(
                    'ERROR', common_bot.source, f'❌ Ошибка при обновлении участника {member_id} в БД: {ans}',
                    file_name=common.get_computer_name(), token=token, law_id='members'))
            else:
                count_remove += 1
                await loop.run_in_executor(None, lambda: common.write_log_db(
                    'info', common_bot.source, f'Участник {member_id} помечен как удалённый в БД.',
                    file_name=common.get_computer_name(), token=token, law_id='members'))
            # пометим уход участника из БД в истории
            params = {
                "schema_name": config.schema_name,
                "object_code": "discord_his_count_members",
                "values": {
                    "date": date,
                    "count": -1,
                    "count_remove": 1,
                }
            }
            ans, is_ok, _ = await loop.run_in_executor(None, lambda: common.send_rest("v2/entity", 'PUT', params=params, token_user=token))
            if not is_ok:
                await loop.run_in_executor(None, lambda: common.write_log_db(
                    'ERROR', common_bot.source, f'❌ Ошибка при создании истории кол-ва участников {member.id} в БД: {ans}',
                    file_name=common.get_computer_name(), token=token, law_id='members'))

        finish_text = (f"Сканирование участников (members) завершено.\nВсего участников на сервере: "
                       f"{count},\n - добавлено: {count_insert},\n - ошибки: {count_error},\n - удалено: {count_remove}."
                       f"\nОжидание 1 час, чтобы не перегружать API Discord")
        await loop.run_in_executor(None, lambda: common.write_log_db('Sleep', common_bot.source, finish_text, td=time.time() - t, law_id='members',
                            file_name=common.get_computer_name()))
        # await bot.close()
        await asyncio.sleep(3600)  # 24 часа в секундах, чтобы не перегружать API Discord


# 🔑 Токен бота в config.py
bot.run(config.discord_token)

# Полная структура участника (member) в Discord API:
# {
#   "id": int,                      # Уникальный Discord ID пользователя
#   "name": str,                    # Имя пользователя (без дискриминатора)
#   "display_name": str,           # Отображаемое имя (с учётом ника на сервере)
#   "discriminator": str,          # 4-значный тег, например '1234' (устарело с введением новых юзернеймов)
#   "global_name": Optional[str],  # Новый глобальный никнейм, если есть
#   "bot": bool,                   # True, если это бот
#   "system": bool,                # True, если это системный аккаунт
#
#   "joined_at": datetime,         # Дата вступления на сервер
#   "premium_since": Optional[datetime],  # Если бустит — дата начала буста
#   "pending": bool,               # Ожидает ли прохождения экранинга (правил сервера)
#
#   "status": str,                 # 'online', 'offline', 'idle', 'dnd'
#   "activity": Optional[Activity],# Текущая активность (игра, стрим и т.п.)
#   "activities": List[Activity],  # Все активности (например, игра + Spotify)
#
#   "roles": List[Role],           # Роли участника (включая @everyone)
#   "top_role": Role,              # Наивысшая роль
#   "guild_permissions": Permissions,  # Разрешения на сервере
#
#   "voice": VoiceState,           # Информация о голосовом канале (если подключен)
#   "dm_channel": DMChannel,       # Личный канал с ботом (если открыт)
#
#   "avatar": Asset,               # Аватар пользователя
#   "guild_avatar": Asset,         # Аватар на сервере, если задан отдельно
#
#   "mention": str,                # Строка, по которой можно упомянуть @User
#   "is_timed_out": bool,          # Заблокирован ли пользователь во временном муте
# }

# Возможные статусы пользователя в Discord:
# online	Пользователь активен — сейчас в сети и что-то делает
# idle	Пользователь ничего не делал какое-то время (AFK)
# dnd	"Do Not Disturb" — не беспокоить, отключены уведомления
# offline	Не в сети (или скрыл своё присутствие)
# invisible	То же самое, что offline, но пользователь в сети скрыт
