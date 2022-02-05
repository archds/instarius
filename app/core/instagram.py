import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Coroutine

from instagrapi import Client
from instagrapi.types import Story

import settings
from core import models
from core.bot import send_stories

logger = logging.getLogger('Instagrapi')

ig_client = Client()


def get_unseen_stories(stories: list[Story]) -> list[Story]:
    return [
        story for story in stories
        if story.pk not in {db_story.pk for db_story in models.Story.select()}
    ]


def save_stories(stories: list[Story], username: str) -> list[models.Story]:
    user = models.InstUser.get(models.InstUser.username == username)

    story_path = settings.TEMP_DIR / username
    story_path.mkdir(exist_ok=True, parents=True)

    db_models = [
        models.Story(
            pk=story.pk,
            created=story.taken_at,
            user=user,
            s_type=str(story.media_type),
            video_duration=story.video_duration,
            path=ig_client.story_download(int(story.pk), f'{story.pk}', story_path)
        )
        for story in stories
    ]

    models.Story.bulk_create(db_models)

    logger.info(f'Created {len(db_models)} stories in db')

    return db_models


def get_all_stories(username: str) -> list[Story]:
    logger.info(f'User stories request for user - {username}')
    return ig_client.user_stories(int(ig_client.user_id_from_username(username)))


def get_new_stories(username: str) -> list[models.Story]:
    all_stories = get_all_stories(username)
    unseen = get_unseen_stories(all_stories)

    logger.info(f'{len(all_stories)} stories for user {username}; {len(unseen)} new of them')

    return save_stories(unseen, username) if unseen else []


async def send_new_stories() -> list[Coroutine]:
    with ThreadPoolExecutor(len(settings.config.user_list)) as executor:
        results = executor.map(get_new_stories, settings.config.user_list)

    tasks = [
        send_stories(bot_user.chat_id, stories)
        for stories in results if stories
        for bot_user in models.BotUser.select()
    ]

    return tasks


async def inst_app():
    logger.info('Login...')
    ig_client.login(
        username=settings.config.ig_user,
        password=settings.config.ig_pass,
    )

    logger.info('Start inst polling...')

    while True:
        logger.info(f'Check for {settings.config.user_list}')

        if tasks := await send_new_stories():
            await asyncio.gather(*tasks)

        await asyncio.sleep(settings.config.ig_polling_timeout_sec)
