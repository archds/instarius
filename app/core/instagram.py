import logging

from instagrapi import Client
from instagrapi.types import Story

import core.model as db
import settings

logger = logging.getLogger(__name__)

logger.info('Instagrapi login...')
ig_client = Client()
ig_client.login(
    username=settings.config.ig_user,
    password=settings.config.ig_pass,
)


def get_temp_size() -> int:
    return round(sum(f.stat().st_size for f in settings.TEMP_DIR.glob('**/*') if f.is_file()) / 1048576, 2)


def get_unseen_stories(stories: list[Story]) -> list[Story]:
    return [
        story for story in stories
        if story.pk not in {db_story.pk for db_story in db.Story.select()}
    ]


def save_stories(stories: list[Story], username: str) -> list[db.Story]:
    user = db.InstUser.get(db.InstUser.username == username)

    story_path = settings.TEMP_DIR / username
    story_path.mkdir(exist_ok=True, parents=True)

    db_models = [
        db.Story(
            pk=story.pk,
            created=story.taken_at,
            user=user,
            s_type=str(story.media_type),
            video_duration=story.video_duration,
            path=ig_client.story_download(int(story.pk), f'{story.pk}', story_path)
        )
        for story in stories
    ]

    db.Story.bulk_create(db_models)

    logger.info(f'Created {len(db_models)} stories in db')

    return db_models


def get_all_stories(username: str) -> list[Story]:
    logger.info(f'User stories request for user - {username}')
    return ig_client.user_stories(int(ig_client.user_id_from_username(username)))


def get_new_stories(username: str) -> list[db.Story]:
    all_stories = get_all_stories(username)
    unseen = get_unseen_stories(all_stories)

    logger.info(f'{len(all_stories)} stories for user {username}; {len(unseen)} new of them')

    return save_stories(unseen, username)
