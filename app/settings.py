import logging
from logging.config import dictConfig
from pathlib import Path

from pydantic import BaseSettings, Field

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / 'data'
TEMP_DIR = DATA_DIR / 'temp'

REPLIES_PATH = 'replies.json'
DB_PATH = DATA_DIR / 'db.sqlite'
LOG_PATH = DATA_DIR / 'app.log'

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
        'polya_silver',
        '_alli.on'
    ]

    ig_polling_timeout_sec: int = 1800
    ig_user: str = Field(env='I_USER')
    ig_pass: str = Field(env='I_PASSWORD')

    telebot_token: str = Field(env='BOT_TOKEN')

    temp_limit_mb: int = 256  # 256 MB

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
dictConfig(LOGGING)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.getLogger('public_request').setLevel(logging.WARNING)
