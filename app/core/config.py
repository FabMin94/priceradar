from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""

    # Auth
    AUTHKIT_URL: str = "http://localhost:8000"

    # App
    APP_NAME: str = "PriceRadar"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive="True",
        extra="ignore",
    )


settings = Settings()
