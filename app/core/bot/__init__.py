import json
import logging

from telebot import logger
from telebot.asyncio_filters import StateFilter
from telebot.types import BotCommand

import settings
from core.bot.interaction import StoryRequestFilter, bot, send_stories
from core.bot.middleware import SimpleAuthMiddleware

__all__ = [
    'send_stories',
    'bot_app'
]

logger.setLevel(logging.INFO)

try:
    with open(settings.COMMANDS_PATH) as fp:
        commands = json.load(fp)
except FileNotFoundError as err:
    logger.warn('Bot response file not found, use default')
    with open(settings.BASE_DIR / 'commands.example.json') as fp:
        commands = json.load(fp)


async def bot_app():
    logger.info('Setting up bot...')

    import core.bot.handlers

    bot.add_custom_filter(StoryRequestFilter())
    bot.add_custom_filter(StateFilter(bot))

    bot.setup_middleware(SimpleAuthMiddleware())

    await bot.set_my_commands(
        [
            BotCommand(command, description)
            for command, description in commands.items()
        ]
    )

    logger.info(f'Start bot polling...')

    await bot.infinity_polling()
