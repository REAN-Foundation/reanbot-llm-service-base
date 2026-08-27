from dotenv import find_dotenv, load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

load_dotenv(find_dotenv('.env'))

class Settings(BaseSettings):

    # App
    ENVIRONMENT: str = "development"
    BASE_URL: str = "http://localhost:8080"
    OPENAI_API_KEY: str

    # For database ---> Future implementations

    model_config = SettingsConfigDict(case_sensitive=True)


@lru_cache()
def get_settings():
    return Settings().model_dump_json()
