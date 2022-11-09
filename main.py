import logging
import yaml

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
        with open('messages.yaml', 'r', encoding="utf-8") as info:
            messages = yaml.load(info, Loader=yaml.FullLoader)
            if not db.user_exist(message.from_user.id):
                db.add_user(message.from_user.id)
            button_for_mailings_tracks = types.InlineKeyboardMarkup(row_width=1)
            button = types.InlineKeyboardButton(messages['Hello']['button'], messages['Hello']['url'])
            button_for_mailings_tracks.add(button)
            keyboard_menu = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=messages['B_playlists'])],
                    [KeyboardButton(text=messages['B_news'])]
                ], resize_keyboard=True
            )
            await message.answer(f'{messages["Hello"]["hi"]}, {message.from_user.full_name}', reply_markup=keyboard_menu)
            await message.answer(
                f'{messages["Hello"]["text"]}',
                reply_markup=button_for_mailings_tracks
            )


# after pushing button 'Плэйлісты'
@dp.message_handler(text=['Плэйлісты'])
async def start(message: types.Message):
    with open('playlists.yaml', 'r', encoding="utf-8") as name_of_playlists:
        dict_names_of_buttons = yaml.load(name_of_playlists, Loader=yaml.FullLoader)
        buttons = []
        markup = types.InlineKeyboardMarkup(row_width=1)
        for name_of_button, info in dict_names_of_buttons.items():
            if 'url' in info:
                buttons.append(types.InlineKeyboardButton(name_of_button, info['url']))
        markup.add(*buttons)
        photo = open(f'inflames+group_3.jpg', 'rb')
        await message.answer_photo(
            photo=photo,
            caption='Глянь, якія плэйлісты мы табе сабралі',
            reply_markup=markup
        )


# after pushing button 'Навіны'
@dp.message_handler(text=['Навіны'])
async def news(message: types.Message):
    with open('messages.yaml', 'r', encoding="utf-8") as messages:
        dict_of_messages = yaml.load(messages, Loader=yaml.FullLoader)
        markup = types.InlineKeyboardMarkup(row_width=1)
        print(dict_of_messages["News"]["button"])
        button = types.InlineKeyboardButton(
            dict_of_messages["News"]["button"],
            dict_of_messages["News"]["url"]
        )
        markup = markup.add(button)
        await message.answer(dict_of_messages["News"]["news"], reply_markup=markup)




#######################################################################################
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
