import asyncio
import json
import logging

from telebot import logger
from telebot.async_telebot import AsyncTeleBot, CancelUpdate
from telebot.asyncio_filters import AdvancedCustomFilter, StateFilter
from telebot.asyncio_handler_backends import BaseMiddleware, State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
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

bot = AsyncTeleBot(settings.config.telebot_token, state_storage=StateMemoryStorage())
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


class SimpleAuthMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.update_types = ['message']
        self.excluded_commands = ['/start', '/help', '/subscribe']
        # Always specify update types, otherwise middlewares won't work

    async def pre_process(self, message: Message, data):
        subscribed_users = {bot_user.chat_id for bot_user in db.BotUser.select()}
        if await bot.get_state(message.from_user.id, message.chat.id) == AuthState.auth_attempt:
            return

        if message.chat.id not in subscribed_users and message.text not in self.excluded_commands:
            await bot.send_message(message.chat.id, replies['register'])
            return CancelUpdate()

    async def post_process(self, message, data, exception):
        pass


class AuthState(StatesGroup):
    auth_attempt = State()  # statesgroup should contain states


@bot.message_handler(commands=['start'])
async def help_resolver(message: Message):
    await bot.send_message(message.chat.id, replies['/start'])


@bot.message_handler(commands=['help'])
async def help_resolver(message: Message):
    await bot.send_message(message.chat.id, replies['/help'])


@bot.message_handler(commands=['subscribe'])
async def register_resolver(message: Message):
    if not db.BotUser.select().where(db.BotUser.chat_id == message.chat.id).exists():
        await bot.set_state(message.from_user.id, AuthState.auth_attempt, message.chat.id)
        await bot.send_message(message.chat.id, replies['password'])
    else:
        await bot.send_message(message.chat.id, replies['subscribed'])


@bot.message_handler(state=AuthState.auth_attempt)
async def check_password(message: Message):
    if message.text != settings.config.primary_password:
        await bot.send_message(message.chat.id, replies['authFailed'])
    else:
        db.BotUser.create(chat_id=message.chat.id)

        await bot.delete_message(message.chat.id, message.id)
        await bot.send_message(message.chat.id, replies['subscribe'])
        await bot.delete_state(message.from_user.id, message.chat.id)
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
    bot.add_custom_filter(StateFilter(bot))
    bot.setup_middleware(SimpleAuthMiddleware())
    logger.info(f'Start bot polling...')
    await bot.infinity_polling()
