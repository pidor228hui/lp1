import argparse
import traceback
import json

import requests
from vkbottle.api import UserApi
from vkbottle.user import User
from logger import logger, Logger, LoggerLevel

import const
from commands import commands_bp
from error_handlers import error_handlers_bp
from objects.json_orm import Database, DatabaseError
from utils import check_ping

if const.ALLOW_SENTRY:
    import sentry_sdk

    sentry_sdk.init(
        const.SENTRY_URL,
        traces_sample_rate=1.0
    )

parser = argparse.ArgumentParser(
    description='LP модуль позволяет работать приемнику сигналов «IDM multi» работать в любых чатах.\n'
                'Так же он добавляет игнор, глоигнор, мут и алиасы.'
)

parser.add_argument(
    '--config_path',
    type=str,
    dest="config_path",
    default="config.json",
    help='Путь до файла с конфингом'
)

parser.add_argument(
    '--use_app_data',
    dest="use_app_data",
    action="store_const",
    const=True,
    help='Использовать папку AppData/IDM (Windows).\n'
         'При использовании этой настройки AppData/IDM и config_path складываются'
)

parser.add_argument(
    '--logger_level',
    dest="logger_level",
    type=str,
    default="INFO",
    help='Уровень логгирования.'
)

parser.add_argument(
    '--vkbottle_logger_level',
    dest="vkbottle_logger_level",
    type=str,
    default="ERROR",
    help='Уровень логгирования VKBottle.'
)

parser.add_argument(
    '--log_to_path',
    dest="log_to_path",
    action="store_const",
    const=True,
    help='Логи в файл'
)


def lp_startup(database):
    async def _lp_startup():
        api = UserApi.get_current()
        text = f'LP работает!🦊\n' \
               f' v{const.__version__}'
        version_rest = requests.get(const.VERSION_REST).json()

        if version_rest['version'] != const.__version__:
            text

        await api.messages.send(
            peer_id=await api.user_id,
            random_id=0,
            message=text
        )
        await check_ping(database.secret_code)

    return _lp_startup


if __name__ == '__main__':
    args = parser.parse_args()

    const.CONFIG_PATH = args.config_path
    const.USE_APP_DATA = args.use_app_data if args.use_app_data else False
    const.LOG_TO_PATH = args.log_to_path if args.log_to_path else False
    const.LOGGER_LEVEL = args.logger_level
    const.VKBOTTLE_LOGGER_LEVEL = args.vkbottle_logger_level

    if isinstance(logger, Logger):
        logger.global_logger_level = LoggerLevel.get_int(const.LOGGER_LEVEL)

    logger.warning(
        f"\n\nЗапуск с параметрами:\n"
        f" -> Уровень логгирования              -> {const.LOGGER_LEVEL}\n"
        f" -> Уровень логгирования VKBottle     -> {const.VKBOTTLE_LOGGER_LEVEL}\n"
        f" -> Логи в файл                       -> {const.LOG_TO_PATH}\n"
        f" -> Путь до файла с конфингом         -> {Database.get_path()}\n"
        f" -> Использовать папку AppData/IDM    -> {const.USE_APP_DATA}\n\n"
    )

    try:
        db = Database.load(is_startup=True)
        Database.set_current(db)
    except DatabaseError as ex:
        exit(-1)
    except json.JSONDecodeError as ex:
        logger.error(
            f'При запуске произошла ошибка базы данных.\n'
            f'Проверте целостность данных.\n'
            f'Строка: {ex.lineno}, столбец: {ex.colno}.'
        )
        exit(-1)

    except Exception as ex:
        logger.error(f'При запуске произошла ошибка [{ex.__class__.__name__}] {ex}\n{traceback.format_exc()}')
        exit(-1)
    else:
        from validators import *

        user = User(
            tokens=db.tokens,
            debug=const.VKBOTTLE_LOGGER_LEVEL,
            log_to_path=const.LOG_TO_PATH
        )
        user.set_blueprints(
            *commands_bp,
            *error_handlers_bp,
        )

        user.run_polling(
            auto_reload=False,
            on_startup=lp_startup(db),
        )
