import os

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotionColumns(BaseModel):
    assignee: str = "Assignee"
    id: str = "ID"
    sentry_url: str = "Sentry link"


class NotionTasksDatabaseConfig(BaseModel):
    database_id: str
    column_names: NotionColumns


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Determine which env file to use based on TEST_MODE environment variable
    model_config = SettingsConfigDict(
        env_file=".env.test" if os.getenv("TEST_MODE") == "1" else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Notion API settings
    notion_token: str = Field(default="", validation_alias="NOTION_TOKEN")
    notion_config: NotionTasksDatabaseConfig = Field(validation_alias="NOTION_CONFIG")

    # Sentry API settings
    sentry_notion_integration_client_secret: str = Field(
        default="", validation_alias="SENTRY_NOTION_INTEGRATION_CLIENT_SECRET"
    )

    # Cache settings
    cache_timeout: int = Field(
        default=21600, validation_alias="CACHE_TIMEOUT"
    )  # 6 hours default
    redis_host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")


# Create a global settings instance
settings = Settings()
