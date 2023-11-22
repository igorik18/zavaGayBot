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

async def general(event, context):
    # добавляем обработчики
    add_user_handlers() # функция вынесена в main, потому что она будет изменяться каждый раз, когда будет добавляться обработчик
    # запускаем функцию, которая сообщит приложению о наличие новых сообщений
    return await handle_update(event)


async def handle_update(event):
    try:
        logger.info('Processing update...')
        await application.initialize()
        for message in event["messages"]:
            await application.process_update(
                Update.de_json(json.loads(message["details"]["message"]["body"]), application.bot)
            )
            logger.info(f'Processed update {message["details"]["message"]["body"]}')
            return 'Success'

    except Exception as exc:
        logger.info(f"Failed to process update with {exc}")
    return 'Failure'