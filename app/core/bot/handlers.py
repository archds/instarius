import asyncio
from datetime import datetime

from telebot.types import Message

import settings
from core import models as models
from core.bot.interaction import AuthState, bot, get_temp_size, replies, start_time
from core.instagram import send_new_stories


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
        await bot.delete_message(message.chat.id, message.id)
        await bot.send_message(message.chat.id, replies['subscribe'])
        await bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(commands=['check'])
async def check_stories_handler(message: Message):
    if tasks := await send_new_stories():
        await asyncio.gather(*tasks)
    else:
        await bot.send_message(message.chat.id, replies['nostory'])


@bot.message_handler(commands=['log'])
async def log_handler(message: Message):
    with open(settings.LOG_PATH, 'rb') as log:
        await bot.send_document(message.chat.id, log)


@bot.message_handler(commands=['info'])
async def info_handler(message: Message):
    uptime = str(datetime.now() - start_time).split('.')[0]

    answer = (
        'Bot is online 🤖\n'
        f'Uptime: {uptime}\n'
        f'Stories sent: {models.Story.select().count()}\n'
        f'Temp files size: {get_temp_size()} MB\n'
        f'Polling every: {round(settings.config.ig_polling_timeout_sec / 60)} minutes'
    )

    await bot.send_message(message.chat.id, answer)
