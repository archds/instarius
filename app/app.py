import asyncio

from core.bot import bot_app
from core.instagram import inst_app
from core.models import init_db


async def app():
    init_db()

    await asyncio.gather(
        bot_app(),
        inst_app(),
    )


if __name__ == '__main__':
    asyncio.run(app())
