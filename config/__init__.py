from functools import lru_cache
from enum import Enum

from pydantic import BaseSettings, EmailStr

# BaseSettings descendants should not have public methods
# pylint: disable=too-few-public-methods


class Environment(Enum):
    DEV = 'develop'
    PROD = 'production'


class Settings(BaseSettings):
    environment: Environment = Environment.DEV
    telegram_token: str
    admin_email: EmailStr

    class Config:
        env_file = "config/.env"


@lru_cache
def get_settings():
    return Settings()
