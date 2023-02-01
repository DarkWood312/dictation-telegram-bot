from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from emoji import emojize

from config import sql, voices


async def options_markup(user_id):
    is_shuffle = await sql.get_data(user_id, 'shuffle')
    separator = await sql.get_data(user_id, 'separator')
    order = await sql.get_data(user_id, 'order_of_words')
    voice = await sql.get_data(user_id, 'voiceru')
    shufflemoji = ':check_mark_button:' if is_shuffle else ':cross_mark:'
    markup = InlineKeyboardMarkup()
    shuffleB = InlineKeyboardButton(emojize(f'Перемешивание {shufflemoji}'), callback_data='shuffle')
    separatorB = InlineKeyboardButton(f"Разделитель: '{separator}'", callback_data='separator')
    orderB = InlineKeyboardButton(f'Ответ{separator}Вопрос' if order else f'Вопрос{separator}Ответ',
                                  callback_data='order')
    voiceB = InlineKeyboardButton(f'Голос для озвучки: {voice.capitalize()}', callback_data='voice')
    markup.row(shuffleB)
    markup.row(separatorB)
    markup.row(orderB)
    markup.row(voiceB)
    return markup


async def menu_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = KeyboardButton(emojize('Начало диктанта:woman_teacher_light_skin_tone:'))
    add_button = KeyboardButton(emojize('Добавить диктант:plus:'))
    get_button = KeyboardButton(emojize('Получить текущий диктант:England:'))
    translate_button = KeyboardButton(emojize('Автоматически перевести диктант:high_voltage:'))  # TODO DICT_TRANSLATION
    synthesize_button = KeyboardButton(emojize('Озвучка:speaker_high_volume:'))
    options_button = KeyboardButton(emojize('Настройки:gear:'))
    markup.row(start_button, add_button).row(get_button).row(synthesize_button).row(options_button)
    return markup


async def stop_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(emojize('Остановить:stop_sign:')))
    return markup


async def voice_choosing_markup(user_id):
    markup = InlineKeyboardMarkup()
    current_voice = await sql.get_data(user_id, 'voiceru')
    rus = voices['ru']
    names = list(rus.keys())
    for name in names:
        sex = 'М' if rus[name]['male'] else 'Ж'
        button = InlineKeyboardButton(emojize(
            f'{name.capitalize()}, {sex}:check_mark_button:') if name == current_voice else f'{name.capitalize()}, {sex}',
                                      callback_data=f'v_{name}')
        markup.row(button)
    return markup