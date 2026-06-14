"""Application configuration module.

Defines the schema and validation rules for application environment variables
using Pydantic's BaseSettings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr


class Settings(BaseSettings):
    """App settings container validated via Pydantic.

    Reads variables from the environment or a `.env` file, parsing and
    coercing them into respective typed Python fields.

    Attributes:
        DB_URL (str): Connection URL string for the PostgreSQL database.
        JWT_SECRET (str): Cryptographic secret key used to sign JWT signatures.
        JWT_ALGORITHM (str): Encryption algorithm used for JWT operations.
        JWT_REFRESH_TOKEN_EXPIRE_MINUTES (int): Lifespan duration of refresh tokens in minutes.
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES (int): Lifespan duration of access tokens in minutes.
        MAIL_USERNAME (EmailStr): Username used for SMTP server authentication.
        MAIL_PASSWORD (str): Password used for SMTP server authentication.
        MAIL_FROM (EmailStr): Default sender email address used for outbound messages.
        MAIL_PORT (int): Connection port of the SMTP server.
        MAIL_SERVER (str): Hostname or IP of the SMTP server.
        MAIL_FROM_NAME (str): Visible sender name on outbound emails. Defaults to "Contacts API Service".
        MAIL_STARTTLS (bool): Enable or disable STARTTLS for SMTP. Defaults to False.
        MAIL_SSL_TLS (bool): Enable or disable SSL/TLS secure connection. Defaults to True.
        USE_CREDENTIALS (bool): Dictates whether to use credentials during SMTP connection. Defaults to True.
        VALIDATE_CERTS (bool): Dictates whether to validate SSL certificates. Defaults to True.
        CLOUDINARY_NAME (str): Target Cloudinary cloud namespace.
        CLOUDINARY_API_KEY (int): Public API key for Cloudinary integrations.
        CLOUDINARY_API_SECRET (str): Private API secret key for Cloudinary integrations.
        REDIS_HOST (str): Hostname of the Redis server. Defaults to "localhost".
        REDIS_PORT (int): Connection port of the Redis server. Defaults to 6379.
        REDIS_PASSWORD (str, optional): Password for the Redis server. Defaults to None.
        REDIS_CACHE_TTL (int): Time-to-live (in seconds) for cached users. Defaults to 900.
        JWT_RESET_TOKEN_EXPIRE_MINUTES (int): Lifespan of password reset tokens in minutes. Defaults to 60.
    """

    DB_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Contacts API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_CACHE_TTL: int = 900

    JWT_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
