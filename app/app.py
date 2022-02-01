import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import core.model as db
import settings
from core.bot import bot_app, send_stories
from core.instagram import get_new_stories
from core.model import init_db

logger = logging.getLogger('app')


async def inst_app():
    logger.info('Start inst polling...')
    while True:
        logger.info(f'Check for {settings.config.user_list}')

        with ThreadPoolExecutor(len(settings.config.user_list)) as executor:
            results = executor.map(get_new_stories, settings.config.user_list)

        await asyncio.gather(
            *(
                send_stories(bot_user.chat_id, stories)
                for stories in results if stories
                for bot_user in db.BotUser.select()
            )
        )

        await asyncio.sleep(settings.config.BOT_POLLING_TIMEOUT_SEC)


async def app():
    init_db()

    await asyncio.gather(
        bot_app(),
        inst_app(),
    )


if __name__ == '__main__':
    asyncio.run(app())
