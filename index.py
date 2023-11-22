#  Copyright (c) ChernV (@otter18), 2021.

#from main import application, add_user_handlers

from TgHandler import TgHandler
from logManager import logger

import json
import asyncio

from telegram import Update

def handler(event: dict, context: str):
    # запускаем ассинхронную функцию, которая займётся обработкой полученного сообщения
    # result = asyncio.get_event_loop().run_until_complete(general(event, context))
    result = asyncio.get_event_loop().run_until_complete(TgHandler().cloud_run(event))
    return {
        'statusCode': 200,
        'body': result
    }
