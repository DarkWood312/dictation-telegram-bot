import logging
from aiogram import Bot, Dispatcher, executor, types

from config import token

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.answer('Hi!')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
