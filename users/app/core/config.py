import secrets
from typing import Literal

from pydantic import (
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    PROJECT_NAME: str = "Distributed TicTacToe"
    SECRET: str = secrets.token_urlsafe(32)

    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production", "test"] = "local"


    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    GITHUB_OAUTH_CLIENT_ID: str 
    GITHUB_OAUTH_CLIENT_SECRET: str 
    CALLBACK_URL: str = "http://localhost:8000/auth/github/callback"
    ON_SUCCESS_REDIRECT_URL: str = "http://localhost:8000/authenticated-route"

    FRONTEND_URL: str
    CORS_URL: str
    COOKIE_DOMAIN: str
    
    # Logging
    LOG_FILE_PATH: str = "logs/app.log"
    DISABLE_EXISTING_LOGGERS: bool = False
    DEFAULT_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
    CONSOLE_LOG_LEVEL: str = "INFO"
    FILE_LOG_LEVEL: str = "INFO"
    ROOT_LOG_LEVEL: str = "INFO"
    ROOT_PROPAGATE: bool = False
    MODULE_LOG_LEVEL: str = "INFO"
    MODULE_PROPAGATE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

settings = Settings()  # type: ignore