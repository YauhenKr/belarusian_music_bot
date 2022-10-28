import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton,\
    CallbackQuery, KeyboardButton
from asyncio import sleep
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import DataBase


logging.basicConfig(level=logging.INFO)

bot = Bot(token='5788713050:AAHyOG4XqvtjT0qg3yGSQPBTjGiPQf5XZrc')
dp = Dispatcher(bot, storage=MemoryStorage())
db = DataBase('database.db')

admins_id = [
    655796453
]


# start and open the meny with buttons
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        if not db.user_exist(message.from_user.id):
            db.add_user(message.from_user.id)
        keyboard_menu = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='playlists')]], resize_keyboard=True
        )
        await message.answer(f'Вітаю {message.from_user.full_name}', reply_markup=keyboard_menu)


# after pushing button 'playlists'
@dp.message_handler(text=['playlists'])
async def start(message: types.Message):
    in_keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='name_of_playlist',
                    url='https://open.spotify.com/track/07J5gvVBcXUPcsa9KVYwHu?si=68da09977e8c40c3'
                )
            ]
        ]
    )
    await message.answer('Глянь, якія плэйлісты мы табе сабралі', reply_markup=in_keyboard)


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand('start', 'Уключыць бота'),
        types.BotCommand('help', 'Дапамога'),
    ])


@dp.message_handler(text='/help')
async def command_help(message: types.Message):
    await message.answer(f'Вітаю {message.from_user.full_name}! \n'
                         f'Табе патрэбна дапамога?')


async def on_startup_notify(dp: Dispatcher):
    for admin in admins_id:
        try:
            text = 'Бот уключаны'
            await dp.bot.send_message(chat_id=admin, text=text)
        except Exception as err:
            logging.exception(err)


# admin side/ mailing
class BotMailing(StatesGroup):
    text = State()
    photo = State()
    state = State()


@dp.message_handler(text='/mailing', chat_id=admins_id)
async def start_mailing(message: types.Message):
    await message.answer(f'Увядзіце тэкст рассылкі')
    await BotMailing.text.set()


@dp.message_handler(state=BotMailing.text, chat_id=admins_id)
async def mailing_text(message: types.Message, state: FSMContext):
    answer = message.text
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Дадаць фатаздымак', callback_data='add_photo'),
                InlineKeyboardButton(text='Апулікаваць', callback_data='next'),
                InlineKeyboardButton(text='Скасаваць', callback_data='quit')
            ]
        ]
    )
    await state.update_data(text=answer)
    await message.answer(text=answer, reply_markup=markup)
    await BotMailing.state.set()


@dp.callback_query_handler(text='next', state=BotMailing.state, chat_id=admins_id)
async def start(call: CallbackQuery, state: FSMContext):
    users = db.get_users()
    data = await state.get_data()
    text = data.get('text')
    await state.finish()
    for user in users:
        try:
            await dp.bot.send_message(chat_id=user[0], text=text)
            await sleep(0.3)
        except Exception:
            pass
    await call.message.answer('Рассылка зроблена')


@dp.callback_query_handler(text='add_photo', state=BotMailing.state, chat_id=admins_id)
async def add_photo(call: CallbackQuery):
    await call.message.answer('Дашліце фота')
    await BotMailing.photo.set()


@dp.message_handler(state=BotMailing.photo, content_types=types.ContentType.PHOTO, chat_id=admins_id)
async def mailing_text(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo=photo_file_id)
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Апублікаваць', callback_data='next'),
                InlineKeyboardButton(text='Скасаваць', callback_data='quit')
            ]
        ]
    )
    await message.answer_photo(photo=photo, caption=text, reply_markup=markup)


@dp.callback_query_handler(text='next', state=BotMailing.photo, chat_id=admins_id)
async def start(call: types.CallbackQuery, state: FSMContext):
    users = db.get_users()
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    await state.finish()
    for user in users:
        try:
            await dp.bot.send_photo(chat_id=user[0], photo=photo, caption=text)
            await sleep(0.3)
        except Exception:
            pass
    await call.message.answer('Рассылка зроблена')


@dp.message_handler(state=BotMailing.photo, chat_id=admins_id)
async def no_photo(message: types.Message):
    markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[InlineKeyboardButton(text='Скасаваць', callback_data='quit')]]
    )
    await message.answer('Дашлі мне фатаздымак', reply_markup=markup)


@dp.callback_query_handler(
    text='quit',
    state=[BotMailing.photo, BotMailing.text, BotMailing.state],
    chat_id=admins_id
)
async def quit(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer('Рассылка скасавана')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
