from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from logManager import logger
from constants import BOT_TOKEN, ABOUT_BOT_LONG_INFORMATION, \
    ABOUT_BOT_SHORT_INFORMATION, \
    _CHECK_IN_BUTTON_, \
    THANKS_GAY_MSG
from DbHandler import DbHandler
import json
import datetime
from datetime import datetime, timedelta
import re


# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Эхо функция."""
#     logger.debug("функция echo")
#     await update.message.reply_text(update.message.text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создаем главное меню и отправляем его в ответ."""
    keyboard = [
        [InlineKeyboardButton(_CHECK_IN_BUTTON_, callback_data="check_in_clicked")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_markdown_v2(text=ABOUT_BOT_SHORT_INFORMATION, reply_markup=reply_markup)


async def information(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция с информацией о тг боте"""
    await update.message.reply_markdown_v2(text=ABOUT_BOT_LONG_INFORMATION)


async def inline_button_clicked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Парсим ответ на кнопку."""
    query = update.callback_query

    if query.data == 'check_in_clicked':
        # cred = ydb.iam.MetadataUrlCredentials()
        # YDBHandler = dbHandler()
        user_rating = DbHandler().get_user_rating()

        is_insert = True

        logger.debug(f"rows count: {len(user_rating.rows)}")
        logger.debug(user_rating)

        if len(user_rating.rows) != 0:
            for i in range(len(user_rating.rows)):
                id_user = update.callback_query.from_user.id
                if id_user == user_rating.rows[i]['id_user']:
                    logger.debug("не надо делать insert")
                    is_insert = False

        if is_insert:
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # current_date = datetime.now().strftime('%Y-%m-%d')

            logger.debug("выполняется upsert")

            DbHandler().upsert_user_rating(update.callback_query.from_user.id, current_datetime, 1,
                                           update.callback_query.from_user.first_name,
                                           1, update.callback_query.from_user.username)

            logger.debug("выполнился upsert")

            is_insert = False

        current_user = DbHandler().get_current_user(update.callback_query.from_user.id).rows[0]

        converted_datetime = datetime.utcfromtimestamp(current_user['last_check_datetime'])

        current_check_datetime = datetime.now()

        diff_datetime = current_check_datetime - converted_datetime

        cur_points = current_user['current_points']
        max_points = current_user['maximum_points']

        final_msg = ""

        seconds_limit = 43200

        if diff_datetime.seconds > seconds_limit:
            if diff_datetime.seconds > seconds_limit * 2:
                cur_points = 0

            if max_points > cur_points:
                cur_points += 1
            elif max_points == cur_points:
                max_points += 1
                cur_points = max_points

            logger.debug("выполняется upsert")

            DbHandler().upsert_user_rating(update.callback_query.from_user.id,
                                           current_check_datetime.strftime('%Y-%m-%d %H:%M:%S'), cur_points,
                                           update.callback_query.from_user.first_name,
                                           max_points, update.callback_query.from_user.username)

            logger.debug("выполнился upsert")
            final_msg = f"Спасибо за напоминание\\!\nЖду вас через {seconds_limit} секунд\\!\nКогда подумаете\\, что пора напоминать\\, нажмите на кнопку снизу" + f"\n\nТекущее комбо\\: {cur_points}\\. Максимальное комбо\\: {max_points}"
        else:
            final_msg = f"Вы ещё не преодолели время отката для каминг аута\\.\nЕщё осталось\\: {seconds_limit - diff_datetime.seconds} секунд\\." \
                        f"\nНе стесняйтесь делать каминг аут\\. " \
                        f"\n\nТекущее комбо\\: {cur_points}\\. Максимальное комбо\\: {max_points}"

        user_rating = DbHandler().get_user_rating()
        sorted_users = sorted(user_rating.rows, key=lambda x: x['maximum_points'], reverse=True)

        # Формирование строки с топ-5 пользователями
        max_leaders_list = "Список лидеров по максимально набранным очкам\\:\n"
        for user in sorted_users[:5]:  # Берем топ-5 или меньше
            max_leaders_list += f"{user['fullname'].decode('utf-8')} \\(\\@{user['username'].decode('utf-8')}\\)\\: {user['maximum_points']} очков\n"

        # Добавляем список лидеров в сообщение
        final_msg = final_msg + "\n\n" + max_leaders_list  # Дополните final_msg, если оно уже существует

        sorted_users = sorted(user_rating.rows, key=lambda x: x['current_points'], reverse=True)
        # Формирование строки с топ-5 пользователями
        current_leaders_list = "Список лидеров по текущим набранным очкам\\:\n"
        for user in sorted_users[:5]:  # Берем топ-5 или меньше
            current_leaders_list += f"{user['fullname'].decode('utf-8')} \\(\\@{user['username'].decode('utf-8')}\\)\\: {user['current_points']} очков\n"

        # Добавляем список лидеров в сообщение
        final_msg = final_msg + "\n\n" + current_leaders_list  # Дополните final_msg, если оно уже существует

        keyboard = [
                [InlineKeyboardButton(_CHECK_IN_BUTTON_, callback_data="check_in_clicked")]
            ]

        await query.answer()
        await query.edit_message_text(parse_mode='MarkdownV2', text=final_msg,
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.answer()
        await query.edit_message_text(parse_mode='MarkdownV2', text=query.data)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f'Update {update} caused error {context.error}')


async def clown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Зава клоун')


class TgHandler:
    def __init__(self):
        """Конструктор"""
        logger.debug("Объявление Application")
        self.application = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.debug("Конец объявления Application")
        self.add_user_handlers()

    def add_user_handlers(self):
        """Добавление обработчиков"""
        # Track commands
        # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
        start_handler = CommandHandler(['start', 'menu'], start)
        info_handler = CommandHandler(['info', 'help'], information)

        self.application.add_handler(start_handler)
        self.application.add_handler(MessageHandler(filters.Regex('(?i)кто клоун'), clown_handler))

        # self.application.add_handler(echo_handler)
        self.application.add_handler(info_handler)
        self.application.add_handler(CallbackQueryHandler(inline_button_clicked))

        self.application.add_error_handler(error_handler)

    def local_run(self):
        """Для запуска бота на локальной машине"""
        self.application.run_polling()

    async def cloud_run(self, event):
        """Для запуска бота в облачной функции"""
        try:
            logger.info('Processing update...')
            await self.application.initialize()
            for message in event["messages"]:
                await self.application.process_update(
                    Update.de_json(json.loads(message["details"]["message"]["body"]), self.application.bot)
                )
                logger.info(f'Processed update {message["details"]["message"]["body"]}')
                return 'Success'

        except Exception as exc:
            logger.info(f"Failed to process update with {exc}")
        return 'Failure'
