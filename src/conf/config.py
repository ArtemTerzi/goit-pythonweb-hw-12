"""Application configuration module.

Defines the schema and validation rules for application environment variables
using Pydantic's BaseSettings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, field_validator


class Settings(BaseSettings):
    """App settings container validated via Pydantic.

    Reads variables from the environment or a `.env` file, parsing and
    coercing them into respective typed Python fields.

    Attributes:
        POSTGRES_USER (str): PostgreSQL user. Shared with docker-compose. Defaults to "postgres".
        POSTGRES_PASSWORD (str): PostgreSQL password. Shared with docker-compose. Defaults to "postgres".
        POSTGRES_DB (str): PostgreSQL database name. Shared with docker-compose. Defaults to "contacts".
        POSTGRES_HOST (str): Database host. Defaults to "localhost" (overridden to "db" in docker-compose).
        POSTGRES_PORT (int): Database port. Defaults to 5434 (overridden to 5432 in docker-compose).
        DB_URL (str): Connection URL string for the PostgreSQL database.
        JWT_SECRET (str): Cryptographic secret key used to sign JWT signatures.
        JWT_ALGORITHM (str): Encryption algorithm used for JWT operations.
        JWT_REFRESH_TOKEN_EXPIRE_MINUTES (int): Lifespan duration of refresh tokens in minutes.
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES (int): Lifespan duration of access tokens in minutes.
        MAIL_USERNAME (EmailStr): SMTP auth username. Defaults to a placeholder so the app boots without mail configured.
        MAIL_PASSWORD (str): Password used for SMTP server authentication. Defaults to "".
        MAIL_FROM (EmailStr): Default sender email address used for outbound messages. Defaults to a placeholder.
        MAIL_PORT (int): Connection port of the SMTP server. Defaults to 465.
        MAIL_SERVER (str): Hostname or IP of the SMTP server. Defaults to "smtp.example.com".
        MAIL_FROM_NAME (str): Visible sender name on outbound emails. Defaults to "Contacts API Service".
        MAIL_STARTTLS (bool): Enable or disable STARTTLS for SMTP. Defaults to False.
        MAIL_SSL_TLS (bool): Enable or disable SSL/TLS secure connection. Defaults to True.
        USE_CREDENTIALS (bool): Dictates whether to use credentials during SMTP connection. Defaults to True.
        VALIDATE_CERTS (bool): Dictates whether to validate SSL certificates. Defaults to True.
        CLOUDINARY_NAME (str): Target Cloudinary cloud namespace. Defaults to "" (avatar upload disabled until set).
        CLOUDINARY_API_KEY (int): Public API key for Cloudinary integrations. Defaults to 0.
        CLOUDINARY_API_SECRET (str): Private API secret key for Cloudinary integrations. Defaults to "".
        REDIS_HOST (str): Hostname of the Redis server. Defaults to "localhost".
        REDIS_PORT (int): Connection port of the Redis server. Defaults to 6379.
        REDIS_PASSWORD (str, optional): Password for the Redis server. Defaults to None.
        REDIS_CACHE_TTL (int): Time-to-live (in seconds) for cached users. Defaults to 900.
        JWT_RESET_TOKEN_EXPIRE_MINUTES (int): Lifespan of password reset tokens in minutes. Defaults to 60.
    """

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "contacts"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5434

    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    MAIL_USERNAME: EmailStr = "example@example.com"
    MAIL_PASSWORD: str = ""
    MAIL_FROM: EmailStr = "example@example.com"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Contacts API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLOUDINARY_NAME: str = ""
    CLOUDINARY_API_KEY: int = 0
    CLOUDINARY_API_SECRET: str = ""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_CACHE_TTL: int = 900

    JWT_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    @field_validator("DB_URL")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        """Ensures the database URL uses the async (asyncpg) driver.

        Managed Postgres providers such as Render and Heroku hand out
        connection strings with the ``postgres://`` or ``postgresql://`` scheme,
        but ``create_async_engine`` requires the asyncpg driver. This validator
        rewrites those schemes to ``postgresql+asyncpg://`` while leaving an
        already-correct URL untouched.

        Args:
            v (str): The raw database URL from the environment.

        Returns:
            str: A URL guaranteed to use the ``postgresql+asyncpg`` driver.
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
