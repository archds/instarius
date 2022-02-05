import asyncio

from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import settings
from core import model as models
from core.bot import bot
from core.bot.interaction import AuthState, replies, send_stories, story_request_factory
from core.instagram import get_new_stories, get_temp_size


@bot.message_handler(commands=['start'])
async def start_handler(message: Message):
    await bot.send_message(message.chat.id, replies[message.text])


@bot.message_handler(commands=['help'])
async def help_handler(message: Message):
    await bot.send_message(message.chat.id, replies[message.text])


@bot.message_handler(commands=['subscribe'])
async def register_handler(message: Message):
    if not models.BotUser.select().where(models.BotUser.chat_id == message.chat.id).exists():
        await bot.set_state(message.from_user.id, AuthState.auth_attempt, message.chat.id)
        await bot.send_message(message.chat.id, replies['password'])
    else:
        await bot.send_message(message.chat.id, replies['subscribed'])


@bot.message_handler(state=AuthState.auth_attempt)
async def check_password_handler(message: Message):
    if message.text != settings.config.primary_password:
        await bot.send_message(message.chat.id, replies['authFailed'])
    else:
        models.BotUser.create(chat_id=message.chat.id)

        tasks = [
            send_stories(
                chat_id=message.chat.id,
                stories=models.Story.select().join(models.InstUser).where(models.InstUser.username == inst_user),
            )
            for inst_user in settings.config.user_list
        ]

        await bot.delete_message(message.chat.id, message.id)
        await bot.send_message(message.chat.id, replies['subscribe'])
        await bot.delete_state(message.from_user.id, message.chat.id)
        await asyncio.gather(*tasks)


@bot.message_handler(commands=['check'])
async def check_stories_handler(message: Message):
    keyboard = [
        InlineKeyboardButton(user, callback_data=story_request_factory.new(user=user, type='new'))
        for user in settings.config.user_list
    ]

    markup = InlineKeyboardMarkup()
    markup.add(*keyboard)

    await bot.send_message(message.chat.id, replies[message.text], reply_markup=markup)


@bot.callback_query_handler(func=None, config=story_request_factory.filter(type='new'))
async def new_stories_callback_handler(call: CallbackQuery):
    call_data = story_request_factory.parse(call.data)

    if stories := get_new_stories(call_data['user']):
        tasks = [
            send_stories(chat_id, stories)
            for chat_id in [bot_user.chat_id for bot_user in models.BotUser.select()]
        ]
        await asyncio.gather(*tasks)
    else:
        await bot.send_message(call.message.chat.id, replies['nostory'])


@bot.message_handler(commands=['log'])
async def log_handler(message: Message):
    with open(settings.LOG_PATH, 'rb') as log:
        await bot.send_document(message.chat.id, log)


@bot.message_handler(commands=['size'])
async def memory_size_handler(message: Message):
    await bot.send_message(message.chat.id, f'Temp files size: {get_temp_size()} MB')
