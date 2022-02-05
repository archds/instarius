import logging

from telebot import logger
from telebot.asyncio_filters import StateFilter

from core.bot.interaction import StoryRequestFilter, bot, send_stories
from core.bot.middleware import SimpleAuthMiddleware

__all__ = [
    'send_stories',
    'bot_app'
]

logger.setLevel(logging.INFO)


async def bot_app():
    logger.info('Setting up bot...')

    import core.bot.handlers

    bot.add_custom_filter(StoryRequestFilter())
    bot.add_custom_filter(StateFilter(bot))

    bot.setup_middleware(SimpleAuthMiddleware())

    logger.info(f'Start bot polling...')

    await bot.infinity_polling()
