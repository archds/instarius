import logging

from telebot import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import StateFilter
from telebot.asyncio_storage import StateMemoryStorage

import settings
from core.bot.interaction import StoryRequestFilter, send_stories
from core.bot.middleware import SimpleAuthMiddleware

__all__ = [
    'bot',
    'send_stories',
]

bot = AsyncTeleBot(settings.config.telebot_token, state_storage=StateMemoryStorage())
logger.setLevel(logging.INFO)


async def bot_app():
    logger.info('Setting up bot...')

    bot.add_custom_filter(StoryRequestFilter())
    bot.add_custom_filter(StateFilter(bot))

    bot.setup_middleware(SimpleAuthMiddleware())

    logger.info(f'Start bot polling...')

    await bot.infinity_polling()
