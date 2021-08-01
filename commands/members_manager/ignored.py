from vkbottle.api import UserApi
from vkbottle.rule import FromMe
from vkbottle.user import Blueprint, Message

from logger import logger_decorator
from objects import Database, IgnoredMembers
from utils import edit_message, get_ids_by_message, get_full_name_by_member_id

user = Blueprint(
    name='ignored_members_blueprint'
)


def add_ignore_member(database: Database, member_id: int, peer_id: int) -> None:
    database.ignored_members.append(
        IgnoredMembers(
            member_id=member_id,
            chat_id=peer_id
        )
    )
    database.save()


def remove_ignore_member(database: Database, member_id: int, peer_id: int) -> None:
    ignored_member = None
    for ign in database.ignored_members:
        if ign.member_id == member_id and ign.chat_id == peer_id:
            ignored_member = ign
    database.ignored_members.remove(ignored_member)
    database.save()


async def show_ignore_members(
        database: Database,
        api: UserApi,
        peer_id: int
) -> str:
    user_ids = [
        ignore_member.member_id
        for ignore_member in database.ignored_members
        if ignore_member.chat_id == peer_id and ignore_member.member_id > 0
    ]
    group_ids = [
        abs(ignore_member.member_id)
        for ignore_member in database.ignored_members
        if ignore_member.chat_id == peer_id and ignore_member.member_id < 0
    ]

    if not user_ids and not group_ids:
        return "Тебе некого игнорить❌"

    index = 1
    message = "Игнорируемые в этом чате:\n"

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
        '<prefix:service_prefix> +игнор [id<user_id:int>|<foo>',
        '<prefix:service_prefix> +игнор [club<group_id:int>|<foo>',
        '<prefix:service_prefix> +игнор https://vk.com/<domain>',
        '<prefix:service_prefix> +игнор',
    ]
)
@logger_decorator
async def add_ignored_member_wrapper(
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
            f'А теперь еще раз в ответ на смс или через @/ссылку'
        )
        return

    member_id = member_ids[0]
    if member_id == await message.api.user_id:
        await edit_message(
            message,
            f'Брат это получается Fire on my own '
        )
        return

    if member_id > 0:
        name = f'Пользователь  [id{member_id}|{await get_full_name_by_member_id(message.api, member_id)}]'
    else:
        name = f'Группа [club{abs(member_id)}|{await get_full_name_by_member_id(message.api, member_id)}]'

    if member_id in [
        igrored_member.member_id
        for igrored_member in db.ignored_members
        if igrored_member.chat_id == message.peer_id
    ]:
        await edit_message(
            message,
            f'⚠ {name} уже в Игноре'
        )
        return
    add_ignore_member(db, member_id, message.peer_id)
    await edit_message(
        message,
        f'✅ {name} Улетел в игнор'
    )


@user.on.message_handler(
    FromMe(),
    text=[
        '<prefix:service_prefix> -игнор [id<user_id:int>|<foo>',
        '<prefix:service_prefix> -игнор [club<group_id:int>|<foo>',
        '<prefix:service_prefix> -игнор https://vk.com/<domain>',
        '<prefix:service_prefix> -игнор',
    ]
)
@logger_decorator
async def remove_ignored_member_wrapper(
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
            f'Покажи кого перестать игнорить...'
        )
        return

    member_id = member_ids[0]

    if member_id > 0:
        name = f'Пользователь  [id{member_id}|{await get_full_name_by_member_id(message.api, member_id)}]'
    else:
        name = f'Группа [club{abs(member_id)}|{await get_full_name_by_member_id(message.api, member_id)}]'

    if member_id not in [
        igrored_member.member_id
        for igrored_member in db.ignored_members
        if igrored_member.chat_id == message.peer_id
    ]:
        await edit_message(
            message,
            f'⚠ {name} и так не в игноре'
        )
        return
    remove_ignore_member(db, member_id, message.peer_id)
    await edit_message(
        message,
        f'✅ {name} теперь не в игноре'
    )


@user.on.message_handler(
    FromMe(),
    text=[
        '<prefix:service_prefix> игнорлист',
        '<prefix:service_prefix> игнор лист',
    ]
)
@logger_decorator
async def show_ignore_members_wrapper(message: Message, **kwargs):
    db = Database.get_current()
    await edit_message(
        message,
        await show_ignore_members(
            db,
            message.api,
            message.peer_id
        )
    )


def get_link(peer_id):
    if peer_id > 2e9:
        return f"vk.com/im?sel=c{peer_id - int(2e9)}"
    return f"vk.com/im?sel={peer_id}"


def get_push_by_id(users, groups, member_id):
    if member_id > 0:
        for user in users:
            if user.id == member_id:
                return f"[id{user.id}|{user.first_name} {user.last_name}]"
    else:
        for group in groups:
            if group.id == abs(member_id):
                return f"[public{group.id}|{group.name}]"


@user.on.message_handler(
    FromMe(),
    text=[
        '<prefix:service_prefix> игнорлист все',
        '<prefix:service_prefix> игнор лист все',
    ]
)
@logger_decorator
async def show_all_ignore_members_wrapper(message: Message, **kwargs):
    db = Database.get_current()

    user_ids = [
        ignore_member.member_id
        for ignore_member in db.ignored_members
        if ignore_member.member_id > 0
    ]
    group_ids = [
        abs(ignore_member.member_id)
        for ignore_member in db.ignored_members
        if ignore_member.member_id < 0
    ]

    if not user_ids and not group_ids:
        return "так-с... А тут пусто🤷🏿‍♂️"
    users = await message.api.users.get(user_ids=user_ids) if user_ids else []
    groups = await message.api.groups.get_by_id(group_ids=group_ids) if group_ids else []

    ignored = {}
    for _ignored in db.ignored_members:
        ignored.setdefault(_ignored.chat_id, [])
        ignored[_ignored.chat_id] += [_ignored]

    text = "🙎🏻‍♂️ Твой игнор по ВСЕМ ЧАТАМ:\n"

    for k in ignored.keys():
        text += f"\n{get_link(k)}\n"
        index = 1
        for member in ignored[k]:
            text += f"{index}. {get_push_by_id(users, groups, member.member_id)}\n"
            index += 1
    await edit_message(
        message, text
    )
