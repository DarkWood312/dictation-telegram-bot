from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from emoji import emojize

from config import sql


async def options_markup(user_id):
    is_shuffle = await sql.get_data(user_id, 'shuffle')
    separator = await sql.get_data(user_id, 'separator')
    order = await sql.get_data(user_id, 'order_of_words')
    shufflemoji = ':check_mark_button:' if is_shuffle else ':cross_mark:'
    markup = InlineKeyboardMarkup()
    shuffleB = InlineKeyboardButton(emojize(f'Перемешивание {shufflemoji}'), callback_data='shuffle')
    separatorB = InlineKeyboardButton(f"Разделитель: '{separator}'", callback_data='separator')
    orderB = InlineKeyboardButton(f'Ответ{separator}Вопрос' if order else f'Вопрос{separator}Ответ',
                                  callback_data='order')
    markup.row(shuffleB)
    markup.row(separatorB)
    markup.row(orderB)
    return markup


async def menu_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = KeyboardButton(emojize('Начало диктанта:woman_teacher_light_skin_tone:'))
    add_button = KeyboardButton(emojize('Добавить диктант:plus:'))
    get_button = KeyboardButton(emojize('Получить текущий диктант:England:'))
    translate_button = KeyboardButton(emojize('Автоматически перевести диктант:high_voltage:'))     # TODO DICT_TRANSLATION
    options_button = KeyboardButton(emojize('Настройки:gear:'))
    markup.row(start_button, add_button).row(get_button).row(options_button)
    return markup
