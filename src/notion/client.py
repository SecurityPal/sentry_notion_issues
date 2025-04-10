import json
import logging
from typing import Any, List, Optional
from uuid import UUID

from notion_client import Client
from redis import Redis

from notion.types import (
    CreateNotionIssueResponse,
    GetPageDataResponse,
    NotionCreatePageResponse,
    NotionFilterDatabaseResponse,
    NotionListUsersResponse,
    NotionRetrieveDatabaseResponse,
    NotionRetrievePageResponse,
    NotionUniqueIdPageProperty,
    NotionUserResponse,
)
from notion.utils import initialize_empty_properties
from settings import settings

logger = logging.getLogger(__name__)


class NotionClient:
    """Client for interacting with the Notion API.

    This class provides methods for creating issues, retrieving users,
    and other Notion-related operations with caching support.
    """

    # Cache keys
    USER_CACHE_KEY: str = "notion:users:all"
    DATABASE_CACHE_KEY: str = "notion:database"

    # Notion API client
    notion = Client(auth=settings.notion_token)

    # Redis client for caching
    _redis = Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    ###############################
    # Public API methods
    ###############################

    @classmethod
    def create_issue(
        cls,
        *,
        title: str,
        sentry_issue_url: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> CreateNotionIssueResponse:
        database = cls._retrieve_database()
        property_schema = database.properties

        # Initialize properties with empty values
        properties_object = initialize_empty_properties(property_schema)

        # Set the title property with the issue title
        properties_object["title"] = {
            "title": [{"type": "text", "text": {"content": title}}]
        }
        properties_object[settings.notion_config.columns.sentry_url_id] = {
            "url": sentry_issue_url
        }

        # Set the assignee property if owner_id is provided
        if owner_id:
            properties_object[settings.notion_config.columns.assignee_id] = {
                "people": [{"id": owner_id}]
            }

        # Create the page in Notion
        try:
            raw_response = cls.notion.pages.create(
                parent={
                    "type": "database_id",
                    "database_id": settings.notion_config.database_id,
                },
                properties=properties_object,
                children=[
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": description},
                                }
                            ]
                        },
                    }
                ]
                if description
                else [],
            )
        except Exception as e:
            logger.error(f"Failed to create Notion issue: {e}")
            raise

        response = NotionCreatePageResponse.model_validate(raw_response)
        page_data = cls.get_page_data(response.id)

        return CreateNotionIssueResponse(
            url=page_data.url,
            issue_id=page_data.identifier,
        )

    @classmethod
    def get_users(
        cls, query: Optional[str] = None, limit: int = 10
    ) -> List[NotionUserResponse]:
        # Get all users from cache or API
        all_users = cls._get_and_cache_users()

        # If no query, return limited number of users
        if not query:
            return all_users[:limit]

        # Filter users by query (case-insensitive) and limit results
        query = query.lower()
        filtered_users = [user for user in all_users if query in user.name.lower()]
        return filtered_users[:limit]

    @classmethod
    def search_issues(
        cls, query: Optional[str] = None, limit: int = 10
    ) -> list[NotionRetrievePageResponse]:
        params: dict[str, Any] = {"page_size": limit}
        if query:
            params["filter"] = {
                "property": "title",
                "title": {"contains": query},
            }

        try:
            raw_response = cls.notion.databases.query(
                database_id=settings.notion_config.database_id,
                **params,
            )
        except Exception as e:
            logger.error(f"Failed to search Notion issues: {e}")
            raise

        response = NotionFilterDatabaseResponse.model_validate(raw_response)
        return [
            NotionRetrievePageResponse.model_validate(page) for page in response.results
        ]

    @classmethod
    def get_page_data(cls, page_id: UUID) -> GetPageDataResponse:
        try:
            raw_response = cls.notion.pages.retrieve(page_id=str(page_id))
        except Exception as e:
            logger.error(f"Failed to get Notion page data: {e}")
            raise

        retrieve_response = NotionRetrievePageResponse.model_validate(raw_response)

        page_response = GetPageDataResponse(identifier="", url=retrieve_response.url)
        for property in retrieve_response.properties.values():
            if property["type"] == "unique_id":
                unique_property = NotionUniqueIdPageProperty.model_validate(property)
                page_response.identifier = f"{unique_property.unique_id.prefix}-{unique_property.unique_id.number}"
                return page_response

        logger.error("Failed to get page data")
        raise ValueError("Failed to get page data")

    @classmethod
    def add_sentry_link_to_page(cls, page_id: UUID, url: str) -> None:
        try:
            cls.notion.pages.update(
                page_id=str(page_id),
                properties={settings.notion_config.columns.sentry_url_id: {"url": url}},
            )
        except Exception as e:
            logger.error(f"Failed to add Sentry link to Notion page: {e}")
            raise

    ###############################
    # Private helper methods
    ###############################

    @classmethod
    def _retrieve_database(cls) -> NotionRetrieveDatabaseResponse:
        # Try to get from cache first
        cached_data = cls._redis.get(cls.DATABASE_CACHE_KEY)
        if cached_data:
            try:
                data = json.loads(cached_data.decode("utf-8"))
                return NotionRetrieveDatabaseResponse.model_validate(data)
            except Exception:
                # If deserialization fails, continue to fetch from API
                pass

        # If not in cache, fetch from API
        database_id = settings.notion_config.database_id
        response = cls.notion.databases.retrieve(database_id=database_id)

        # Create the response object
        database = NotionRetrieveDatabaseResponse.model_validate(response)

        # Cache the results
        if hasattr(database, "model_dump"):
            serialized = json.dumps(database.model_dump(mode="json"))
            cls._redis.setex(cls.DATABASE_CACHE_KEY, settings.cache_timeout, serialized)

        return database

    @classmethod
    def _get_and_cache_users(cls) -> List[NotionUserResponse]:
        # Try to get from cache first
        cached_data = cls._redis.get(cls.USER_CACHE_KEY)
        if cached_data:
            try:
                data = json.loads(cached_data.decode("utf-8"))
                return [NotionUserResponse.model_validate(item) for item in data]
            except Exception:
                # If deserialization fails, continue to fetch from API
                pass

        # If not in cache, fetch from API
        all_users: List[NotionUserResponse] = []
        start_cursor: Optional[str] = None
        has_more: bool = True

        # Use cursor pagination to fetch all users
        while has_more:
            params: dict[str, Any] = {}
            if start_cursor:
                params["start_cursor"] = start_cursor

            response = NotionListUsersResponse.model_validate(
                cls.notion.users.list(**params)
            )

            # Add the current page of results
            users = [
                NotionUserResponse.model_validate(user) for user in response.results
            ]
            all_users.extend(users)

            # Check if there are more pages
            if response.next_cursor:
                start_cursor = response.next_cursor
            else:
                has_more = False

        # Cache the results
        serialized = json.dumps([user.model_dump(mode="json") for user in all_users])
        cls._redis.setex(cls.USER_CACHE_KEY, settings.cache_timeout, serialized)

        return all_users
