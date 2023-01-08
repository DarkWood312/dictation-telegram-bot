import logging
from random import shuffle
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ParseMode, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.markdown import hcode, hbold
from emoji import emojize
from config import token, owner_id, sql

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


class Dictation(StatesGroup):
    adding_dict = State()
    dictate = State()


class Options(StatesGroup):
    option = State()
    separator = State()


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        await state.finish()


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


@dp.message_handler(commands=['gs', 'ds'], state='*', user_id=owner_id)
async def OptionState(message: Message, state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        if message.text.lower() == '/gs':
            await message.answer(hcode(state_), parse_mode=ParseMode.HTML)
        elif message.text.lower() == '/ds':
            await state.finish()
            await message.answer(f'{hcode(state_)} удален', parse_mode=ParseMode.HTML)
    else:
        await message.answer('no state')


@dp.message_handler(commands=['start'], state='*')
async def start_message(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id)
    await message.answer('Hi!')


@dp.message_handler(commands=['cancel'], state='*')
async def cancel(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Действие отменено', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['get'])
async def get(message: Message):
    separator = await sql.get_data(message.from_user.id, 'separator')
    raw_dict = await sql.get_data(message.from_user.id, 'dict')
    await message.answer(raw_dict.replace(' *** ', separator))


@dp.message_handler(commands=['add'])
async def add(message: Message):
    separator = await sql.get_data(message.from_user.id, 'separator')
    await Dictation.adding_dict.set()
    await message.answer(
        f'*Пример:*\n`cat{separator}кот\ndog{separator}собака\nparrot{separator}попугай\nfox{separator}лиса\nwolf{separator}волк`',
        parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state=Dictation.adding_dict)
async def state_AddDict_adding_dict(message: Message, state: FSMContext):
    text = message.text.split('\n')
    separator = await sql.get_data(message.from_user.id, 'separator')
    dict_ = {}
    for line in text:
        k, v = line.split(separator, 1)
        dict_[k] = v
    await sql.upd_dict(message.from_user.id, message.text.replace(separator, ' *** '))
    await message.answer(str(dict_))
    await message.answer('Добавлено')
    await state.finish()


@dp.message_handler(commands=['begin', 'run', 'dictate'], state='*')
async def dictate(message: Message, state: FSMContext):
    await cancel_state(state)
    dict_ = await sql.get_data(message.from_user.id, 'dict')
    dict_ = dict_.split('\n')
    order = await sql.get_data(message.from_user.id, 'order_of_words')
    to_dictate = {}
    for line in dict_:
        k, v = line.split(' *** ', 1)
        if order:
            to_dictate[v] = k
        else:
            to_dictate[k] = v

    if await sql.get_data(message.from_user.id, 'shuffle'):
        list_ = list(to_dictate.items())
        shuffle(list_)
        to_dictate = dict(list_)

    await state.update_data(to_dictate=to_dictate, count=0, correct=0, incorrect=0)
    await message.answer('1. ' + list(to_dictate.keys())[0])
    await Dictation.dictate.set()


@dp.message_handler(state=Dictation.dictate)
async def state_Dictation_Dictate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    count = data['count']
    correct = data['correct']
    incorrect = data['incorrect']
    to_dictate = data['to_dictate']
    items = list(to_dictate.items())
    request_answer = message.text.lower().strip()
    answer = items[count][1].strip()

    if request_answer == answer:
        await message.answer('Правильно!')
        correct += 1
    else:
        await message.answer(f'Неправильно --> {items[count][1].strip()}')
        incorrect += 1
    count += 1

    await state.update_data(count=count, correct=correct, incorrect=incorrect)
    if len(items) == count:
        await message.answer(
            f'*Статистика:*\n_Всего_ - `{count}`\n_Правильных_ - `{correct}`\n_Неправильных_ - `{incorrect}`\n_Процент_ - `{round(correct / count * 100, 2)}%`',
            parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    else:
        await message.answer(f'{count + 1}. {list(to_dictate.keys())[count]}')
        await Dictation.dictate.set()


@dp.message_handler(commands=['options'], state='*')
async def options(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer(f"{hbold('Настройки:')}\n", parse_mode=ParseMode.HTML,
                         reply_markup=await options_markup(message.from_user.id))


@dp.message_handler(state=Options.separator)
async def state_Options_separator(message: Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['msg_id']
    await sql.upd_data(message.from_user.id, 'separator', f' {message.text} ')
    await message.answer(f"Новый разделитель: ' {hcode(message.text)} '", parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=msg_id,
                                        reply_markup=await options_markup(message.from_user.id))
    await cancel_state(state)


@dp.callback_query_handler()
async def callback_handler(call: CallbackQuery, state: FSMContext):
    if call.data in ['shuffle', 'separator', 'order']:
        if call.data == 'shuffle':
            await sql.upd_data(call.from_user.id, 'shuffle', False if await sql.get_data(call.from_user.id, 'shuffle') else True)
            await call.message.edit_reply_markup(await options_markup(call.from_user.id))
        elif call.data == 'separator':
            await call.message.answer('Введите новый разделитель')
            await state.update_data(msg_id=call.message.message_id)
            await Options.separator.set()
        elif call.data == 'order':
            await sql.upd_data(call.from_user.id, 'order_of_words',
                         False if await sql.get_data(call.from_user.id, 'order_of_words') else True)
            await call.message.edit_reply_markup(await options_markup(call.from_user.id))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
