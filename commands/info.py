import requests
from vkbottle.rule import FromMe
from vkbottle.user import Blueprint, Message

import const
from const import __version__, __author__
from logger import logger_decorator
from objects import Database
from utils import edit_message

user = Blueprint(
    name='info_blueprint'
)


@user.on.message_handler(FromMe(), text="<prefix:service_prefix> лп")
@logger_decorator
async def info_wrapper(message: Message, **kwargs):
    db = Database.get_current()
    version_rest = requests.get(const.VERSION_REST).json()

    if version_rest['version'] != const.__version__:
        update_text = f"\n\n [https://vk.com/lislp|Запись в группе про обновление 1.1.7]"  \
                      f"\n"
    else:
        update_text = ""

    text = f"""
    🦊 LP by {__author__}\n V{__version__}
    
    📌Префикс команд: {' '.join(db.service_prefixes)}
    
    📚Настройки для чатов: чаты
    🔁Настройки повторялки: повторялка
    🖇️Настройки префиксов: префиксы
    
    🛡️Алиасы: {len(db.aliases)}
    
    Updates:{update_text}
      
    """.replace('    ', '')
    await edit_message(
        message,
        text
    )


@user.on.message_handler(FromMe(), text="<prefix:service_prefix> чаты")
@logger_decorator
async def info_wrapper(message: Message, **kwargs):
    db = Database.get_current()
    version_rest = requests.get(const.VERSION_REST).json()

    if version_rest['version'] != const.__version__:
        update_text = f"\n\n Обновление у вас\n на глазах📡"  \
                      f"\n"
    else:
        update_text = ""

    text = f"""   
    ⚙️Команды для чатов:
    
    🔕Удаление уведомлений:{"&#9989;" if db.delete_all_notify else "&#10060;"}
    🔔Вкл/Выкл уведомлений:{"&#9989;" if db.disable_notifications else "&#10060;"}
    🚶Автовыход с бесед:{"&#9989;" if db.auto_exit_from_chat else "&#10060;"}
    🏃Автовыход\n и удаление:{"&#9989;" if db.auto_exit_from_chat_delete_chat else "&#10060;"}
    📃Добавлять\n пригласившего в ЧС:{"&#9989;" if db.auto_exit_from_chat_add_to_black_list else "&#10060;"}
    🤗 Ответка в ебало:{"&#9989;" if db.bio_reply else "&#10060;"}
    
    """.replace('    ', '')
    await edit_message(
        message,
        text
    )
    

@user.on.message_handler(FromMe(), text="<prefix:service_prefix> повторялка")
@logger_decorator
async def info_wrapper(message: Message, **kwargs):
    db = Database.get_current()
    version_rest = requests.get(const.VERSION_REST).json()

    if version_rest['version'] != const.__version__:
        update_text = f"\n\n Обновление у вас\n на глазах📡"  \
                      f"\n"
    else:
        update_text = ""

    text = f"""   
    🔄Настройки повторялки:
    
    🗨️ Повторялка: {"on&#9989;" if db.repeater_active else "off&#10060;"}
    💫 Префикс повторялки: {db.repeater_word}

    """.replace('    ', '')
    await edit_message(
        message,
        text
    )


@user.on.message_handler(FromMe(), text="<prefix:service_prefix> префиксы")
@logger_decorator
async def info_wrapper(message: Message, **kwargs):
    db = Database.get_current()
    version_rest = requests.get(const.VERSION_REST).json()

    if version_rest['version'] != const.__version__:
        update_text = f"\n\n Обновление у вас\n на глазах📡"  \
                      f"\n"
    else:
        update_text = ""

    text = f"""    
    🖇️Префиксы:
    
    ⚜️Удалялка: {db.dd_prefix}
    
    🔱Префиксы ЛП: {' '.join(db.service_prefixes)}
    
    ⚕️Мои префиксы: {' '.join(db.self_prefixes) if db.self_prefixes else ''}
    
    🔺Префиксы ИДМ: {' '.join(db.duty_prefixes) if db.duty_prefixes else ''}
    
    """.replace('    ', '')
    await edit_message(
        message,
        text
    )
