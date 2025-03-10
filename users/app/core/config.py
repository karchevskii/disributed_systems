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
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    # 60 minutes * 24 hours * 7 days = 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60 * 24 * 7
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET: str = ""

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
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    MONGODB_SERVER: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: str = ""
    MONGODB_PASSWORD: str
    MONGODB_DB: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def MONGODB_URI(self) -> str:
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_SERVER}:{self.MONGODB_PORT}/{self.MONGODB_DB}"

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    DEVICE_TYPES: list[str] = ["ios", "android", "web"]

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 2
    DELETE_UNVERIFIED_USERS_OLDER_THAN_HOURS: int = 24
    DELETE_EXPIRED_REFRESH_TOKENS_EVERY_MINUTES: int = 120
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60 * 24 * 7


    @computed_field  # type: ignore[misc]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)


    AZURE_ENDPOINT: str = ""
    AZURE_KEY: str = ""
    ACCEPTED_FILE_FORMATS: list[str] = [b"image/jpeg", b"image/png", b"image/jpg"]

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