from peewee import BigIntegerField, CharField, DateTimeField, FloatField, ForeignKeyField, Model, SqliteDatabase

import settings

db = SqliteDatabase(settings.DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class BotUser(BaseModel):
    chat_id = BigIntegerField()


class InstUser(BaseModel):
    username = CharField()


class Story(BaseModel):
    story_types = [
        ('1', 'Image'),
        ('2', 'Video'),
    ]

    pk = BigIntegerField(unique=True)
    created = DateTimeField()
    user = ForeignKeyField(InstUser)
    s_type = CharField(max_length=3, choices=story_types)
    path = CharField(null=True, unique=True)

    video_duration = FloatField()


def init_db(flush=False):
    db.connect()
    db.create_tables([Story, InstUser, BotUser])

    if flush:
        Story.delete().execute()
        InstUser.delete().execute()
        BotUser.delete().execute()

    for user in settings.config.user_list:
        InstUser.get_or_create(username=user)
