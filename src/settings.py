import json
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotionColumns(BaseModel):
    assignee_id: str
    issue_id: str
    sentry_url_id: str


class NotionTasksDatabaseConfig(BaseModel):
    database_id: str
    columns: NotionColumns


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Notion API settings
    notion_token: str = Field(default="", validation_alias="NOTION_TOKEN")
    notion_config: NotionTasksDatabaseConfig = Field(
        validation_alias="NOTION_CONFIG"
    )

    @field_validator("notion_config", mode="before")
    @classmethod
    def parse_notion_config(cls, value: str) -> Dict[str, Any]:
        """Parse the notion_config JSON string into a dictionary."""
        if not value:
            raise ValueError("NOTION_CONFIG is required")
        try:
            config_dict = json.loads(value)
            return config_dict  # Will be validated as NotionTasksDatabaseConfig by Pydantic
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in NOTION_CONFIG: {e}") from e

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
