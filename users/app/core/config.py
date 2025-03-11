import secrets
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Distributed TicTacToe"
    SECRET: str = secrets.token_urlsafe(32)

    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production", "test"] = "local"

    @computed_field  # type: ignore[misc]
    @property
    def SERVER_HOST(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return "http://localhost:8000"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_MASTER_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    POSTGRES_REPL_SERVER: str = "localhost"
    POSTGRES_REPL_PORT: int = 5433
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_REPLICA_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_REPL_SERVER,
            port=self.POSTGRES_REPL_PORT,
            path=self.POSTGRES_DB,
        )
    
    GITHUB_OAUTH_CLIENT_ID: str = ""
    GITHUB_OAUTH_CLIENT_SECRET: str = ""
    ON_SUCCESS_REDIRECT_URL: str = "https://magpie-liberal-heavily.ngrok-free.app/authenticated-route"


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
        env_file=".env.local", env_ignore_empty=True, extra="ignore"
    )

settings = Settings()  # type: ignore