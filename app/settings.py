import logging
from logging.config import dictConfig
from pathlib import Path

from pydantic import BaseSettings, Field

BASE_DIR = Path.cwd()
TEMP_DIR = BASE_DIR / 'temp'

DB_PATH = 'db.sqlite'
REPLIES_PATH = 'replies.json'
LOG_PATH = BASE_DIR / 'app.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s :: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': LOG_PATH,
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}


class Settings(BaseSettings):
    user_list: list[str] = [
        'polyasilver',
        '_alli.on'
    ]

    ig_polling_timeout_sec: int = 1800
    ig_user: str = Field(env='I_USER')
    ig_pass: str = Field(env='I_PASSWORD')

    telebot_token: str = Field(env='BOT_TOKEN')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
dictConfig(LOGGING)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.getLogger('public_request').setLevel(logging.WARNING)
