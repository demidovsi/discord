"""
Общие модули для бота (custom_bot).
"""
import json
import datetime

import asyncio

import common
import config
from common import send_rest, write_log_db

source = "discord"

async def insert_member(member, token=None):
    """
    Добавляет участника в БД, если он отсутствует.

    :param member: Объект участника, полученный из Discord API.
    :type member: Discord.member
    :param token: Токен для доступа к БД. Если не указан, будет получен через common.login_admin().
    :type token: Str, optional
    :return: True, если участник успешно добавлен в БД, False, если участник уже существует,
             None в случае ошибки.
    :rtype: Bool | None
    """
    loop = asyncio.get_running_loop()
    # Если токен не передан, выполняется авторизация администратора для получения токена.
    if token is None:
        _, _, token, _ = await loop.run_in_executor(
            None, lambda: common.login_admin())

    values = {
        "member_id": str(member.id),
        "sh_name": member.name,
        "display_name": member.display_name,
        "bot": member.bot,
    }

    try:
        join_at = member.joined_at.isoformat() if member.joined_at else None
        values["join_at"] = join_at
    except:
        pass

    params = {
        "schema_name": config.schema_name,
        "object_code": "discord_members",
        "values": values
    }

    # Проверка наличия участника в БД по его ID.
    ans, is_ok, _ = await loop.run_in_executor(
        None, lambda: send_rest("v2/select/{schema}/nsi_discord_members?where=member_id='{member_id}'".format(
            schema=config.schema_name, member_id=member.id)))
    if not is_ok:
        # Логирование ошибки при получении данных участника из БД.
        await loop.run_in_executor(
        None, lambda: write_log_db('ERROR', source,
            '❌ Ошибка при получении участника {} из БД: {}'.format(member.id, ans),
            file_name=common.get_computer_name(), token=token
        ))
        return None

    # Преобразование ответа в JSON.
    ans = json.loads(ans)

    # Если участник отсутствует в БД, выполняется его добавление.
    if len(ans) == 0:
        # Запись участника в БД.
        ans, is_ok, _ = await loop.run_in_executor(
        None, lambda: send_rest("v2/entity", 'PUT', params=params, token_user=token))
        if not is_ok:
            # Логирование ошибки при записи данных участника в БД.
            await loop.run_in_executor(
        None, lambda: write_log_db(
                'ERROR', source,
                '❌ Ошибка при записи участника {} в БД: {}'.format(member.id, ans),
                file_name=common.get_computer_name(), token=token
            ))
            return None
        else:
            await loop.run_in_executor(
                None, lambda: write_log_db(
                    'info', source,
                    '😇 Новый участник {} {}'.format(member.id, member.display_name),
                    file_name=common.get_computer_name(), token=token
                ))
        ans = json.loads(ans)
        if "join_at" in values:
            await write_value_join_member(member, 1, int(ans[0]['id']),  token, False)
        return True  # Участник успешно добавлен в БД.
    else:
        # Участник уже существует в БД.
        return False

async def write_value_join_member(member, value, id=None, token=None, in_log=False):
    """
    Записывает информацию в БД о присоединении или покидании участника сервера.

    :param member: Объект участника, полученный из Discord API.
    :param id: id участника в БД
    :param value: 1 - для присоединения участника, -1 для покидания.
    :param token: Токен для доступа к БД.
    :param in_log: Признак записи в лог факта присоединении или покидании участника сервера.
    """
    loop = asyncio.get_running_loop()
    if token is None:
        _, _, token, _ = await loop.run_in_executor(
            None, lambda: common.login_admin())
    if id is None:
        ans, is_ok, _ = await loop.run_in_executor(
            None, lambda: send_rest("v2/select/{schema}/nsi_discord_members?where=member_id='{member_id}'".format(
                schema=config.schema_name, member_id=member.id)))
        if not is_ok:
            return False
        ans = json.loads(ans)
        if len(ans) == 0:
            return False
        id = ans[0]['id']  # Получаем ID участника из БД.

    params = {"schema_name": config.schema_name, "object_code": "discord_members",
              "values": {
                  "remove": value == -1,
                  "id": id,  # ID участника в БД.
              }}
    if value == -1:
        params["values"]["remove_at"] = datetime.datetime.utcnow().isoformat()
    # Обновление информации о присоединении участника в БД.
    ans, is_ok, _ = await loop.run_in_executor(None, lambda: send_rest('v2/entity', 'PUT', token_user=token, params=params))
    if not is_ok:
        await loop.run_in_executor(None, lambda: write_log_db(
            'ERROR', source, f'❌ Ошибка при обновлении участника {member.id} {member.display_name} в БД: {ans}',
            file_name=common.get_computer_name(), token=token))
        return False

    if in_log:
        await loop.run_in_executor(None, lambda: write_log_db(
            'INFO', source,
            f'📌 Участник {member.id} {member.display_name} присоединился к серверу' if value == 1 else f'Участник {member.id} {member.display_name} покинул сервер',
            file_name=common.get_computer_name(), token=token))

    # формируем запись в discord_his_count_members
    if value == 1:
        date = member.joined_at.isoformat().split('T')[0]
    else:
        date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    # hour = int(member.joined_at.isoformat().split('T')[1][:2]) if member.joined_at else 0
    # ans, is_ok, _ = await loop.run_in_executor(None, lambda: send_rest(
    #     "v2/select/{schema}/nsi_discord_his_count_members?where=date='{date}'".format(schema=config.schema_name, date=date)))
    # if not is_ok:
    #     await loop.run_in_executor(None, lambda: write_log_db(
    #         'ERROR', source, f'❌ Ошибка при формировании истории кол-ва участников {member.id} в БД: {ans}',
    #         file_name=common.get_computer_name(), token=token))
    #     return False

    params = {
        "schema_name": config.schema_name,
        "object_code": "discord_his_count_members",
        "values": {
            "date": date,
            "count_join": 1 if value == 1 else 0,
            "count_remove": 1 if value == -1 else 0,
        }
    }
    # ans = json.loads(ans)
    # if len(ans) > 0:
        # Если запись есть, то обновляем её
        # for data in ans:
        #     params["values"]['count'] += data['count']
        #     params["values"]['count_join'] += data['count_join']
        #     params["values"]['count_remove'] += data['count_remove']
        #     params['values']['id'] = data['id']  # ID записи для обновления
    ans, is_ok, _ = await loop.run_in_executor(None, lambda: send_rest("v2/entity", 'PUT', params=params, token_user=token))
    if not is_ok:
        await loop.run_in_executor(None, lambda: write_log_db(
            'ERROR', source, f'❌ Ошибка при создании истории кол-ва участников {member.id} в БД: {ans}',
            file_name=common.get_computer_name(), token=token))
        return False
    return True


async def insert_status_member(member, token=None):
    loop = asyncio.get_running_loop()

    if token is None:
        _, _, token, _ = await loop.run_in_executor(None, lambda: common.login_admin())

    at_date_time = datetime.datetime.utcnow().isoformat()
    values = {
        "member_id": str(member.id),
        "sh_name": member.display_name,
        "status": member.status.value,  # 'online', 'offline', 'idle', 'dnd'
        "at_date_time": at_date_time,
    }
    params = {
        "schema_name": config.schema_name,
        "object_code": "discord_his_status_members",
        "values": values
    }

    ans, is_ok, _ = await loop.run_in_executor(
        None, lambda: send_rest("v3/entity", 'PUT', params=params, token_user=token))
    if not is_ok:
        # Логирование ошибки при записи данных участника в БД.
        await loop.run_in_executor(
        None, lambda: write_log_db(
            'ERROR', source,
            '❌ Ошибка при записи статуса участника {} в БД: {}'.format(member.id, ans),
            file_name=common.get_computer_name(), token=token
        ))
        return None
    # else:
    #     await loop.run_in_executor(
    #     None, lambda: write_log_db(
    #         'info', source,
    #         '✅ Участник {member} сменил статус на [{status}]'.format(member=member.display_name, status=member.status.value),
    #         file_name=common.get_computer_name(), token=token
    #     ))
    return True


async def get_author_id(author_id):
    """
    Получает ID автора из БД по его коду.

    :param author_id: Код автора.
    :return: ID автора, если он существует, иначе None.
    """
    query = f"v2/select/{config.schema_name}/nsi_discord_members?where=member_id='{author_id}'"
    ans, is_ok, _ = common.send_rest(query, params={"columns": "id"})

    if is_ok:
        ans = json.loads(ans)
        if ans:
            return ans[0]['id']
    return None


async def get_channel_id(channel_id):
    """
    Получает ID канала из БД по его коду.

    :param channel_id: Код канала.
    :return: ID канала, если он существует, иначе None.
    """
    query = f"v2/select/{config.schema_name}/nsi_discord_channels?where=code='{channel_id}'"
    ans, is_ok, _ = common.send_rest(query, params={"columns": "id"})

    if is_ok:
        ans = json.loads(ans)
        if ans:
            return ans[0]['id']
    return None


async def exist_message(message_id):
    loop = asyncio.get_running_loop()
    ans, is_ok, _ = await loop.run_in_executor(
            None, lambda: common.send_rest("v2/select/{schema}/nsi_discord_messages?where=message_id='{message_id}'".format(
            schema=config.schema_name, message_id=message_id)))
    if not is_ok:
        await loop.run_in_executor(
            None, lambda: write_log_db(
                'Error', 'discord', f'❌ {ans}', file_name=common.get_computer_name(), law_id='messages'))
        return True  # лучше пропустим
    ans = json.loads(ans)
    if len(ans) > 0:
        return True # Сообщение найдено в БД
    return False  # Сообщение не найдено в БД


async def insert_message(msg, token=None):
    loop = asyncio.get_running_loop()
    if token is None:
        _, _, token, _ = await loop.run_in_executor(None, lambda: common.login_admin())
    try:
        author_id = await get_author_id(msg.author.id)
        if author_id is None:
            await insert_member(msg.author, token=token)
            author_id = await get_author_id(msg.author.id)

        channel_id = await get_channel_id(msg.channel.id)
        if channel_id is None:
            await insert_channel(msg.channel, token=token)
            channel_id = await get_channel_id(msg.channel.id)

        values = {
            "channel": channel_id,
            "message_id": str(msg.id),
            "created_at": msg.created_at.isoformat(),
            "edited_at": msg.edited_at.isoformat() if msg.edited_at else "",
            "is_reply": bool(msg.reference),
        }
        datas = ''
        if msg.content.strip():
            values["content"] = '%s'
            datas = msg.content.strip()

        if author_id is not None:
            values["author"] = author_id
        if channel_id is not None:
            values["channel"] = channel_id

        if msg.attachments:
            attachment_urls = ", ".join(a.url for a in msg.attachments)
            values["attachments"] = '%s'
            values["has_attachments"] = True
            datas = f"{datas}~~~{attachment_urls}" if datas else attachment_urls

        if msg.reactions:
            values["reactions"] = json.dumps([
                {"emoji": r.emoji.name if hasattr(r.emoji, 'name') else r.emoji, "count": r.count}
                for r in msg.reactions
            ])

        if msg.mentions:
            mention_names = ", ".join(u.name for u in msg.mentions)
            if mention_names:
                values["mentions"] = '%s'
                datas = f"{datas}~~~{mention_names}" if datas else mention_names

        params = {
            'schema_name': common.config.schema_name,
            'object_code': 'discord_messages',
            "values": values,
            'datas': datas
        }

        ans, is_ok, _ = await loop.run_in_executor(
            None, lambda: common.send_rest('v2/entity', 'PUT', params=params, token_user=token))
        if not is_ok:
            await loop.run_in_executor(
                None, lambda: write_log_db(
                    'Error', 'discord', f'❌ {ans}', file_name=common.get_computer_name(), token=token, law_id='messages'
                ))
            return 0
        else:
            await loop.run_in_executor(
                None, lambda: write_log_db(
                    'info', 'discord', f'Добавлено новое сообщение ' + str(msg.id),
                    file_name=common.get_computer_name(), token=token, law_id='messages'))
            return 1
    except Exception as er:
        await loop.run_in_executor(
            None, lambda: write_log_db(
                '❌Exception', 'discord', f'{er}', file_name=common.get_computer_name(), token=token, law_id='messages'
            )
        )
    return 0


async def insert_channel(channel, token=None):
    loop = asyncio.get_running_loop()
    if token is None:
        _, _, token, _ = await loop.run_in_executor(None, lambda: common.login_admin())
    values = {
        "code": str(channel.id),
        "sh_name": '%s',
        "guild_name": channel.guild.name,
        "position": channel.position if hasattr(channel, 'position') else 0,
        "category": channel.category.name if hasattr(channel, 'category') and channel.category and channel.category != 'None' else None,
        "created_at": str(channel.created_at),
        "nsfw": channel.is_nsfw() if hasattr(channel, 'is_nsfw') else False,
        "slowmode_delay": channel.slowmode_delay if hasattr(channel, 'slowmode_delay') else 0,
        "member_count": len(channel.members) or channel.member_count if hasattr(channel, 'member_count') else 0,
        "permission_overwrites": json.dumps({
            str(target): perms._values
            for target, perms in channel.overwrites.items()
        } if hasattr(channel, 'overwrites') else {})
    }
    datas = channel.name
    if hasattr(channel, 'topic') and channel.topic:
        values['topic'] = '%s'
        datas += '~~~' + channel.topic
    params = {'schema_name': common.config.schema_name, 'object_code': 'discord_channels',
              "values": values, 'datas': datas}
    ans, is_ok, _ = await loop.run_in_executor(
            None, lambda: common.send_rest('v2/entity', 'PUT', params=params, token_user=token))
    if not is_ok:
        await loop.run_in_executor(
            None, lambda:
            write_log_db('❌Error', 'discord', f'❌ {ans}', file_name=common.get_computer_name(), token=token))
    else:
        ans = json.loads(ans)
        if len(ans) > 0:
            if 'id' not in values:
                st = f'Канал [{channel.name}] успешно добавлен в базу данных'
                await loop.run_in_executor(
                    None, lambda:
                    write_log_db('➕ Новый канал', 'discord', st, file_name=common.get_computer_name(), token=token))
                return True
    return False


async def delete_channel(channel, token=None):
    loop = asyncio.get_running_loop()
    if token is None:
        _, _, token, _ = await loop.run_in_executor(None, lambda: common.login_admin())
    removed_at = datetime.datetime.utcnow().isoformat()
    query = "update {schema}.nsi_discord_channels set remove=true, removed_at={removed_at} where code='{channel_id}'".format(
        schema=config.schema_name, channel_id=channel.id, removed_at=removed_at
    )
    ans, is_ok, _ = await loop.run_in_executor(
            None, lambda: common.send_rest('v2/execute', 'PUT', params={"script": query}, token_user=token))
    if not is_ok:
        await loop.run_in_executor(
            None, lambda:
            write_log_db('❌Error', 'discord', f'❌ {ans}', file_name=common.get_computer_name(), token=token))
