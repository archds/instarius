import json

from telebot import logger
from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot.types import CallbackQuery, InputMediaPhoto, InputMediaVideo

import settings
from core import model as db
from core.bot import bot
from core.instagram import get_temp_size

story_request_factory = CallbackData('user', 'type', prefix='stories')
new_inst_user_factory = CallbackData('username', prefix='users')

try:
    with open(settings.REPLIES_PATH) as fp:
        replies = json.load(fp)
except FileNotFoundError as err:
    logger.error('Bot response file not found')
    raise err


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
