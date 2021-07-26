from vkbottle.api import UserApi
from vkbottle.framework.framework.rule import FromMe
from vkbottle.user import Blueprint, Message

from logger import logger_decorator
from objects import Database
from objects.trusted_user import TrustedUser
from utils import get_ids_by_message, edit_message, get_full_name_by_member_id

user = Blueprint(
    name='trusted_blueprint'
)


@user.on.message_handler(
    FromMe(),
    text=[
        '<prefix:service_prefix> +дов [id<user_id:int>|<foo>',
        '<prefix:service_prefix> +дов [club<group_id:int>|<foo>',
        '<prefix:service_prefix> +дов https://vk.com/<domain>',
        '<prefix:service_prefix> +дов',
    ]
)
@logger_decorator
async def add_trusted_member_wrapper(
        message: Message,
        domain: str = None,
        user_id: int = None,
        group_id: int = None,
        **kwargs
):
    db = Database.get_current()
    member_id = user_id if user_id else None
    if not user_id and group_id:
        member_id = -group_id

    member_ids = await get_ids_by_message(message, member_id, domain)
    if not member_ids:
        await edit_message(
            message,
            f'⚠ Вась а кого добавить то?'
        )
        return

    member_id = member_ids[0]
    if member_id == await message.api.user_id:
        await edit_message(
            message,
            f'⚠ Так-то ты создатель...'
        )
        return

    if member_id > 0:
        name = f'Пользователь [id{member_id}|{await get_full_name_by_member_id(message.api, member_id)}]'
    else:
        name = f'Группа [club{abs(member_id)}|{await get_full_name_by_member_id(message.api, member_id)}]'

    if member_id in [
        muted_member.member_id
        for muted_member in db.muted_members
        if muted_member.chat_id == message.peer_id
    ]:
        await edit_message(
            message,
            f'⚠ {name} я ему уже верю'
        )
        return
    db.trusted.append(TrustedUser(user_id=member_id))
    db.save()
    await edit_message(
        message,
        f'✅ челик - {name} втёрся в доверие😎 '
    )


@user.on.message_handler(
    FromMe(),
    text=[
        '<prefix:service_prefix> -дов [id<user_id:int>|<foo>',
        '<prefix:service_prefix> -дов [club<group_id:int>|<foo>',
        '<prefix:service_prefix> -дов https://vk.com/<domain>',
        '<prefix:service_prefix> -дов',
    ]
)
@logger_decorator
async def remove_trusted_member_wrapper(
        message: Message,
        domain: str = None,
        user_id: int = None,
        group_id: int = None,
        **kwargs
):
    db = Database.get_current()
    member_id = user_id if user_id else None
    if not user_id and group_id:
        member_id = -group_id

    member_ids = await get_ids_by_message(message, member_id, domain)
    if not member_ids:
        await edit_message(
            message,
            f'⚠ кого удалить то?'
        )
        return

    member_id = member_ids[0]

    if member_id > 0:
        name = f'Пользователь  [id{member_id}|{await get_full_name_by_member_id(message.api, member_id)}]'
    else:
        name = f'Группа [club{abs(member_id)}|{await get_full_name_by_member_id(message.api, member_id)}]'

    if member_id not in [
        trusted_member.user_id
        for trusted_member in db.trusted
    ]:
        await edit_message(
            message,
            f'⚠ я {name} и так не знаю...'
        )
        return
    trusted = None
    for ign in db.trusted:
        if ign.user_id == member_id:
            trusted = ign
    db.trusted.remove(trusted)
    db.save()
    await edit_message(
        message,
        f'✅ {name} послан с доверенных...'
    )


async def show_trusted_members(
        database: Database,
        api: UserApi
) -> str:
    user_ids = [
        trusted.user_id
        for trusted in database.trusted
        if trusted.user_id > 0
    ]
    group_ids = [
        abs(trusted.user_id)
        for trusted in database.trusted
        if trusted.user_id < 0
    ]

    if not user_ids and not group_ids:
        return "📃 Ты и так никому не веришь"

    index = 1
    message = "📃 ты веришь им\n"

    if user_ids:
        for vk_user in await api.users.get(user_ids=user_ids):
            message += f"{index}. [id{vk_user.id}|{vk_user.first_name} {vk_user.last_name}]\n"
            index += 1

    if group_ids:
        for vk_group in await api.groups.get_by_id(group_ids=group_ids):
            message += f'{index}. [club{vk_group.id}|{vk_group.name}]'
            index += 1
    return message


@user.on.message_handler(
    FromMe(),
    text=[
        '<prefix:service_prefix> довы',
    ]
)
@logger_decorator
async def show_trusted_members_wrapper(message: Message, **kwargs):
    db = Database.get_current()
    await edit_message(
        message,
        await show_trusted_members(
            db,
            message.api
        )
    )
