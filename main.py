import logging
from random import shuffle
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import Message, ParseMode, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.markdown import hcode, hbold
from emoji import emojize, demojize
from config import token, sql
from keyboards import options_markup, menu_markup
from defs import cancel_state

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


class IsAdminFilter(filters.BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: Message):
        admins = await sql.get_admins()
        user = message.from_user.id
        return user in admins


class Contain(filters.BoundFilter):
    key = 'contain'

    def __init__(self, contain: list):
        self.contain = contain

    async def check(self, message: Message):
        boolean = False
        for i in self.contain:
            if i in demojize(message.text):
                boolean = True
        if boolean: return True


dp.filters_factory.bind(IsAdminFilter)
dp.filters_factory.bind(Contain)


class Dictation(StatesGroup):
    adding_dict = State()
    dictate = State()


class Options(StatesGroup):
    option = State()
    separator = State()


@dp.message_handler(commands=['gs', 'ds'], state='*', is_admin=True)
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


@dp.message_handler(commands=['start', 'info'], state='*')
async def start_message(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    await message.answer(
        '''/start | /info - *Получить это информационное сообщение*
/cancel - *Отмена действия*
/add - *Добавить новый словарь(диктант)*
/run | /begin | /dictate - *Запустить словарь(диктант)*
/get - *Получить текущий словарь(диктант)*
/options | /settings - *Настройки* _(Перемешивание слов, разделитель и тд...)_
''', parse_mode=ParseMode.MARKDOWN, reply_markup=await menu_markup())


@dp.message_handler(commands=['cancel'], state='*')
async def cancel(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Действие отменено', reply_markup=await menu_markup())


@dp.message_handler(commands=['get'], state='*')
async def get(message: Message, state: FSMContext):
    await cancel_state(state)
    separator = await sql.get_data(message.from_user.id, 'separator')
    raw_dict = await sql.get_data(message.from_user.id, 'dict')
    if raw_dict is None:
        await message.answer('Словарь пустой!\nДобавьте словарь командой /add')
    else:
        await message.answer(raw_dict.replace(' *** ', separator))


@dp.message_handler(commands=['add'], state='*')
async def add(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    separator = await sql.get_data(message.from_user.id, 'separator')
    order_of_words = bool(await sql.get_data(message.from_user.id, 'order_of_words'))
    await Dictation.adding_dict.set()
    example_dict = {'cat': 'кот', 'dog': 'собака', 'parrot': 'попугай', 'fox': 'лиса', 'wolf': 'волк'}
    example_list = example_dict.items()
    lines = []
    for line in example_list:
        if order_of_words:
            lines.append(f'{line[0]}{separator}{line[1]}')
        else:
            lines.append(f'{line[1]}{separator}{line[0]}')
    await message.answer('<b>Пример:</b>\n<code>' + '\n'.join(lines) + '</code>', parse_mode=ParseMode.HTML)


@dp.message_handler(commands=['begin', 'run', 'dictate'], state='*')
async def dictate(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    dict_ = await sql.get_data(message.from_user.id, 'dict')
    if dict_ is None:
        await message.answer('Словарь пустой!\nДобавьте словарь командой /add')
    else:
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
        list_of_dict = list(to_dictate.keys())
        await state.update_data(to_dictate=to_dictate, count=0, correct=0, incorrect=0)
        await message.answer(f'1 / {len(list_of_dict)}) {list_of_dict[0]}')
        await Dictation.dictate.set()


@dp.message_handler(commands=['options', 'settings'], state='*')
async def options(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer(f"{hbold('Настройки:')}\n", parse_mode=ParseMode.HTML,
                         reply_markup=await options_markup(message.from_user.id))


@dp.message_handler(state=Dictation.dictate)
async def state_Dictation_Dictate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    count = data['count']
    correct = data['correct']
    incorrect = data['incorrect']
    to_dictate = data['to_dictate']
    list_of_dict = list(to_dictate.keys())
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
        await message.answer(f'{count + 1} / {len(list_of_dict)}) {list_of_dict[count]}')
        await Dictation.dictate.set()


@dp.message_handler(contain=['Начало диктанта', 'Добавить диктант', 'Получить текущий диктант', 'Настройки'])
async def menu_messages(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    msg = demojize(message.text)
    if 'Начало диктанта' in msg:
        await dictate(message, state)
    elif 'Добавить диктант' in msg:
        await add(message, state)
    elif 'Получить текущий диктант' in msg:
        await get(message, state)
    elif 'Настройки' in msg:
        await options(message, state)


@dp.message_handler(state=Options.separator)
async def state_Options_separator(message: Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['msg_id']
    await sql.upd_data(message.from_user.id, 'separator', f' {message.text} ')
    await message.answer(f"Новый разделитель: ' {hcode(message.text)} '", parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=msg_id,
                                        reply_markup=await options_markup(message.from_user.id))
    await cancel_state(state)


@dp.message_handler(state=Dictation.adding_dict)
async def state_AddDict_adding_dict(message: Message, state: FSMContext):
    try:
        text = message.text.split('\n')
        separator = await sql.get_data(message.from_user.id, 'separator')
        dict_ = {}
        for line in text:
            k, v = line.split(separator, 1)
            dict_[k] = v
        await sql.upd_dict(message.from_user.id, message.text.replace(separator, ' *** '))
        await message.answer('Добавлено. (Для просмотра - /get, Для запуска - /run)')
    except ValueError:
        await message.answer('Ошибка! Смотреть пример словаря!')
        await message.answer('Действие отменено.')
    finally:
        await state.finish()


@dp.callback_query_handler()
async def callback_handler(call: CallbackQuery, state: FSMContext):
    if call.data in ['shuffle', 'separator', 'order']:
        if call.data == 'shuffle':
            await sql.upd_data(call.from_user.id, 'shuffle',
                               False if await sql.get_data(call.from_user.id, 'shuffle') else True)
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
