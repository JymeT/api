from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str

    # Security settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings() 