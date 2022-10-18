import logging
import io

import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.input_file import InputFile

from config import get_settings
from i18n import _
from schedule.core import call_by_name

logger = logging.getLogger(__name__)
config = get_settings()

# Initialize bot and dispatcher
bot = Bot(token=config.telegram_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply(_("Hi!\nI'm EchoBot!\n"))


@dp.message_handler(commands=['get'])
async def get_data(message: types.Message):
    await message.answer('Start request')
    logger.info("Start sending data")
    msg, files = await get_message(message['chat']['id'])
    await message.answer(msg)
    for file in files:
        for filename, data in file.items():
            file = InputFile(io.BytesIO(data), filename=filename)
            await message.answer_document(file)
    logger.info("Data sent")


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    logger.debug(message.text)
    logger.debug(message)
    await message.answer(message.text)


async def notify_admin(_: Dispatcher):
    if not config.admin_telegram_user_id:
        return
    logger.info("Start sending notify")
    await bot.send_message(config.admin_telegram_user_id, "Bot set up...")
    await bot.send_message(config.admin_telegram_user_id, "Configuring...")
    if config.SEND_ON_START:
        await bot.send_message(
            config.admin_telegram_user_id, "Request bills...")
        msg, files = await get_message(config.admin_telegram_user_id)
        await bot.send_message(config.admin_telegram_user_id, msg)
        await bot.send_file()
    await bot.send_message(config.admin_telegram_user_id, "Bot started")
    logger.info("Notify sent")


async def get_message(user_id):
    try:
        responses = await asyncio.gather(
            call_by_name('vodovod'),
            call_by_name('electricity'),
            call_by_name('komunalno'),
        )
        messages = []
        files = []
        for res in responses:
            messages.append(res['msg'])
            if res.get('files'):
                files.extend(res.get('files'))
        msg = '\n\n---\n\n'.join(messages)
    except Exception as exc:  # pylint: disable=broad-except
        msg = "Sorry something went wrong"
        if user_id == config.admin_telegram_user_id:
            msg = f"{msg}\n{repr(exc)}"
    return msg, files


def start(loop=None):
    executor.start_polling(
        dp,
        skip_updates=True,
        loop=loop,
        on_startup=notify_admin,
        on_shutdown=None,
    )
