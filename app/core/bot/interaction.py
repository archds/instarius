import json

from telebot.async_telebot import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot.types import CallbackQuery, InputMediaPhoto, InputMediaVideo

import settings
from core import model as db

bot = AsyncTeleBot(settings.config.telebot_token, state_storage=StateMemoryStorage())

story_request_factory = CallbackData('user', 'type', prefix='stories')
new_inst_user_factory = CallbackData('username', prefix='users')

try:
    with open(settings.REPLIES_PATH) as fp:
        replies = json.load(fp)
except FileNotFoundError as err:
    logger.warn('Bot response file not found, use default')
    with open(settings.BASE_DIR / 'replies.example.json') as fp:
        replies = json.load(fp)


class StoryRequestFilter(AdvancedCustomFilter):
    key = 'config'

    async def check(self, call: CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


class AuthState(StatesGroup):
    auth_attempt = State()  # statesgroup should contain states


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


def get_temp_size() -> int:
    return round(sum(f.stat().st_size for f in settings.TEMP_DIR.glob('**/*') if f.is_file()) / 1048576, 2)