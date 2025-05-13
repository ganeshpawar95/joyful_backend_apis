import os
from pathlib import Path
import warnings
from typing import Annotated, Any, Literal
from dotenv import load_dotenv
import razorpay

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    model_validator,
    Field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

load_dotenv()


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/v1"
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DOMAIN: str = Field(..., env="DOMAIN")
    ENVIRONMENT: Literal["D", "local", "staging", "production"] = Field(
        ..., env="ENVIRONMENT"
    )

    RAZORPAY_KEY_ID: str = Field(..., env="RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET: str = Field(..., env="RAZORPAY_KEY_SECRET")

    @computed_field  # type: ignore[misc]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl], BeforeValidator(parse_cors)] = []

    SQLITE_DB_FILE: str = Field("database.db", env="SQLITE_DB_FILE")
    TABLE_PREFIX: str = "prod_"
    # Directory to Save Banners
    BANNER_DIR: str = "images/banners"
    product_DIR: str = "images/products"
    BASE_IMG_DIR: str = "images/"

    PRODUCT_IMG_DIR: str = "images/products/banners"
    PRODUCT_REVIEW_DIR: str = "images/reviews"

    os.makedirs(BANNER_DIR, exist_ok=True)
    os.makedirs(product_DIR, exist_ok=True)
    os.makedirs(BASE_IMG_DIR, exist_ok=True)
    os.makedirs(PRODUCT_IMG_DIR, exist_ok=True)
    os.makedirs(PRODUCT_REVIEW_DIR, exist_ok=True)

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """SQLite database connection string"""
        db_path = Path(self.SQLITE_DB_FILE).resolve()
        return f"sqlite:///{db_path}"

    def _check_default_secret(self, var_name: str, value: str) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        return self


settings = Settings()  # type: ignore
