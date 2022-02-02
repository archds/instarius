import asyncio
import json
import logging

from telebot import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message
)

import core.model as db
import settings
from core.instagram import get_new_stories, get_temp_size

bot = AsyncTeleBot(settings.config.telebot_token)
logger.setLevel(logging.INFO)

try:
    with open(settings.REPLIES_PATH) as fp:
        replies = json.load(fp)
except FileNotFoundError as err:
    logger.error('Bot response file not found')
    raise err

story_request_factory = CallbackData('user', 'type', prefix='stories')
new_inst_user_factory = CallbackData('username', prefix='users')


class StoryRequestFilter(AdvancedCustomFilter):
    key = 'config'

    async def check(self, call: CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


async def send_stories(chat_id: int, stories: list[db.Story]):
    story_files = {
        story.pk: open(story.path, 'rb')
        for story in stories
    }

    if not stories:
        return

    await bot.send_media_group(
        chat_id,
        [
            InputMediaPhoto(
                media=story_files[story.pk],
                caption=story.user.username
            ) if story.s_type == '1' else InputMediaVideo(
                story_files[story.pk],
                caption=story.user.username
            )
            for story in stories
        ]
    )

    for file in story_files.values():
        file.close()

    await check_temp_size(chat_id)


async def check_temp_size(chat_id: int):
    temp_size = get_temp_size()
    if temp_size >= settings.config.temp_limit_mb:
        await bot.send_message(chat_id, f'DEBUG: Temp size limit exceeded, {temp_size} MB used')


@bot.message_handler(func=lambda m: True)
async def any_resolver(message: Message):
    await bot.reply_to(message, replies['/start'])


@bot.message_handler(commands=['start', 'help'])
async def help_resolver(message: Message):
    await bot.send_message(message.chat.id, replies['/help'])


@bot.message_handler(commands=['subscribe'])
async def register_resolver(message: Message):
    db.BotUser.get_or_create(chat_id=message.chat.id)
    await bot.send_message(message.chat.id, replies[message.text])

    await asyncio.gather(
        *[
            send_stories(
                chat_id=message.chat.id,
                stories=db.Story.select().join(db.InstUser).where(db.InstUser.username == inst_user),
            )
            for inst_user in settings.config.user_list
        ]
    )


@bot.message_handler(commands=['check'])
async def check_resolver(message: Message):
    markup = InlineKeyboardMarkup()
    markup.add(
        *[
            InlineKeyboardButton(user, callback_data=story_request_factory.new(user=user, type='new'))
            for user in settings.config.user_list
        ]
    )

    await bot.send_message(message.chat.id, replies[message.text], reply_markup=markup)


@bot.callback_query_handler(func=None, config=story_request_factory.filter(type='new'))
async def new_stories_callback_resolver(call: CallbackQuery):
    call_data = story_request_factory.parse(call.data)
    if stories := get_new_stories(call_data['user']):
        await send_stories(call.message.id, stories)
    else:
        await bot.send_message(call.message.chat.id, replies['nostory'])


@bot.message_handler(commands=['all'])
async def all_resolver(message: Message):
    markup = InlineKeyboardMarkup()
    markup.add(
        *[
            InlineKeyboardButton(
                user,
                callback_data=story_request_factory.new(user=user, type='all')
            )
            for user in settings.config.user_list
        ]
    )

    await bot.send_message(message.chat.id, replies[message.text], reply_markup=markup)


@bot.callback_query_handler(func=None, config=story_request_factory.filter(type='all'))
async def all_stories_callback_resolver(call: CallbackQuery):
    call_data = story_request_factory.parse(call.data)

    if stories := db.Story.select().join(db.InstUser).where(db.InstUser.username == call_data['user']):
        await send_stories(
            chat_id=call.message.chat.id,
            stories=stories,
        )
    else:
        await bot.send_message(call.message.chat.id, replies['nostory'])


@bot.message_handler(commands=['log'])
async def log_resolver(message: Message):
    with open(settings.LOG_PATH, 'rb') as log:
        await bot.send_document(message.chat.id, log)


@bot.message_handler(commands=['size'])
async def size_resolver(message: Message):
    await bot.send_message(message.chat.id, f'Temp files size: {get_temp_size()} MB')


async def bot_app():
    bot.add_custom_filter(StoryRequestFilter())
    logger.info(f'Start bot polling...')
    await bot.polling()
