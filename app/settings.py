import logging
from logging.config import dictConfig
from pathlib import Path

from pydantic import BaseSettings, Field
from telebot import console_output_handler as telebot_handler
from telebot.async_telebot import logger as telebot_logger

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / 'data'
TEMP_DIR = DATA_DIR / 'temp'
STATIC_DIR = BASE_DIR / 'static'

DB_PATH = DATA_DIR / 'db.sqlite'
LOG_PATH = DATA_DIR / 'app.log'
REPLIES_PATH = STATIC_DIR / 'replies.json'
COMMANDS_PATH = STATIC_DIR / 'commands.json'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s'
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
    primary_password: str = Field(env='PASSWORD')

    user_list: list[str] = Field(env='USERS')

    ig_polling_timeout_sec: int = 900
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

telebot_logger.removeHandler(telebot_handler)
telebot_logger.setLevel(logging.INFO)

logging.getLogger('public_request').setLevel(logging.WARNING)
