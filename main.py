import logging
from random import shuffle

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ParseMode
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.markdown import hcode

from config import token, owner_id, separator, sql

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


class AddDict(StatesGroup):
    adding_dict = State()


class LetsDictate(StatesGroup):
    Dictate = State()


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        await state.finish()


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
    sql.add_user(message.from_user.id)
    await message.answer('Hi!')


@dp.message_handler(commands=['cancel'], state='*')
async def cancel(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Действие отменено', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['add'])
async def add(message: Message):
    await AddDict.adding_dict.set()
    await message.answer('dict...')


@dp.message_handler(state=AddDict.adding_dict)
async def state_AddDict_adding_dict(message: Message, state: FSMContext):
    text = message.text.split('\n')
    dict_ = {}
    for line in text:
        k, v = line.split(separator, 1)
        dict_[k] = v
    # sql.upd_dict(message.from_user.id, str(dict_))
    sql.upd_dict(message.from_user.id, message.text.replace(separator, ' *** '))
    await message.answer(str(dict_))
    await message.answer('Добавлено')
    await state.finish()


@dp.message_handler(commands=['begin', 'run', 'dictate'])
async def dictate(message: Message, state: FSMContext):
    dict_ = sql.get_data(message.from_user.id, 'dict')
    dict_ = dict_.split('\n')
    to_dictate = {}
    for line in dict_:
        k, v = line.split(' *** ', 1)
        to_dictate[k] = v

    if sql.get_data(message.from_user.id, 'shuffle'):
        list_ = list(to_dictate.items())
        shuffle(list_)
        to_dictate = dict(list_)

    await state.update_data(to_dictate=to_dictate, count=0, correct=0, incorrect=0)
    await message.answer('1. ' + list(to_dictate.keys())[0])
    await LetsDictate.Dictate.set()


@dp.message_handler(state=LetsDictate.Dictate)
async def state_LetsDictate_Dictate(message: types.Message, state: FSMContext):
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
        await message.answer(f'total - {count}\ncorrect - {correct}\nincorrect - {incorrect}')
        await message.answer('the end')
        await state.finish()
    else:
        await message.answer(f'{count + 1}. {list(to_dictate.keys())[count]}')
        await LetsDictate.Dictate.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
