from aiogram import Bot, Dispatcher, executor, types

from config import get_settings
from i18n import _

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


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    print(message.text)
    await message.answer(message.text)


async def notify_admin(_: Dispatcher):
    if not config.admin_telegram_user_id:
        return

    from schedule.core import get_credentials
    cred = get_credentials('vodovod')
    await bot.send_message(config.admin_telegram_user_id, 'Start request')
    result = await cred['func'](*cred['args'])
    await bot.send_message(config.admin_telegram_user_id, "\n".join(
        [f"{label}: {value}" for label, value in result.items()]))


def start(loop=None):
    executor.start_polling(
        dp,
        skip_updates=True,
        loop=loop,
        on_startup=notify_admin,
        on_shutdown=None,
    )
