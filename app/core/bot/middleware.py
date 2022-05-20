from telebot.async_telebot import CancelUpdate
from telebot.asyncio_handler_backends import BaseMiddleware
from telebot.types import Message

from core import models as db
from core.bot.interaction import AuthState, bot, replies


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
