import json
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from notion.client import NotionClient
from notion.types import NotionRetrieveDatabaseResponse
from sentry.types import (
    CreateNotionIssueFields,
    CreateNotionIssueParams,
    SentryActor,
    SentryProject,
)
from settings import settings


class TestNotionClient:
    """Test suite for the NotionClient class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        # Test data for users
        self.user_id_1: str = "59833787-2cf9-4fdf-8782-e53db20768a5"
        self.user_id_2: str = "ee5f0f84-409a-440f-983a-a5315961c6e4"
        self.user_name_1: str = "John Doe"
        self.user_name_2: str = "Jane Smith"

        # Test data for issues - using valid UUID format
        self.issue_id_1: str = "12345678-1234-5678-1234-567812345678"
        self.issue_id_2: str = "87654321-4321-8765-4321-876543210987"
        self.issue_title_1: str = "Security Vulnerability in Auth Service"
        self.issue_title_2: str = "Performance Issue in API Gateway"
        self.issue_url_1: str = (
            "https://www.notion.so/Security-Vulnerability-123456781234567812345678"
        )
        self.issue_url_2: str = (
            "https://www.notion.so/Performance-Issue-876543214321876543218765"
        )

        # Mock users response
        self.mock_users_response = {
            "object": "list",
            "results": [
                {
                    "object": "user",
                    "id": self.user_id_1,
                    "type": "person",
                    "person": {"email": "john@example.org"},
                    "name": self.user_name_1,
                    "avatar_url": "https://secure.notion-static.com/e6a352a8-8381-44d0-a1dc-9ed80e62b53d.jpg",
                },
                {
                    "object": "user",
                    "id": self.user_id_2,
                    "type": "bot",
                    "bot": {},
                    "name": self.user_name_2,
                    "avatar_url": "https://secure.notion-static.com/6720d746-3402-4171-8ebb-28d15144923c.jpg",
                },
            ],
            "next_cursor": None,
            "has_more": False,
        }

        # Mock database response
        self.mock_database_response = {
            "object": "database",
            "id": settings.notion_config.database_id,
            "properties": {
                "Name": {
                    "id": "title",
                    "name": "Name",
                    "type": "title",
                },
                "Assignee": {
                    "id": "Oz%40b",
                    "name": "Assignee",
                    "type": "people",
                },
                "Issue ID": {
                    "id": "%3CFZ%7C",
                    "name": "Issue ID",
                    "type": "rich_text",
                },
                "Sentry URL": {
                    "id": "nLlM",
                    "name": "Sentry URL",
                    "type": "url",
                },
            },
        }

        # Mock issues response
        self.mock_issues_response = {
            "object": "list",
            "results": [
                {
                    "object": "page",
                    "id": self.issue_id_1,
                    "url": self.issue_url_1,
                    "properties": {
                        "Name": {
                            "id": "title",
                            "type": "title",
                            "title": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": self.issue_title_1,
                                        "link": None,
                                    },
                                    "plain_text": self.issue_title_1,
                                }
                            ],
                        }
                    },
                },
                {
                    "object": "page",
                    "id": self.issue_id_2,
                    "url": self.issue_url_2,
                    "properties": {
                        "Name": {
                            "id": "title",
                            "type": "title",
                            "title": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": self.issue_title_2,
                                        "link": None,
                                    },
                                    "plain_text": self.issue_title_2,
                                }
                            ],
                        }
                    },
                },
            ],
        }

        # Mock create page response
        self.mock_create_page_response = {
            "id": self.issue_id_1,
            "url": self.issue_url_1,
            "properties": {
                "ID": {
                    "id": "ID",
                    "type": "unique_id",
                    "unique_id": {
                        "number": 123,
                        "prefix": "ID",
                    },
                },
            },
        }

    @patch("notion.client.NotionClient._redis")
    @patch("notion.client.NotionClient.notion")
    def test_get_users_no_cache(
        self, mock_notion: MagicMock, mock_get_redis: MagicMock
    ) -> None:
        """Test getting users without cache."""
        # Setup mocks
        mock_get_redis.get.return_value = None  # No cache

        # Mock the Notion API response - return a dict that can be properly validated
        mock_notion.users.list.return_value = self.mock_users_response

        # Call the method
        users = NotionClient.get_users()

        # Verify the results
        assert len(users) == 2
        assert str(users[0].id) == self.user_id_1
        assert users[0].name == self.user_name_1
        assert str(users[1].id) == self.user_id_2
        assert users[1].name == self.user_name_2

        # Verify the mocks were called correctly
        mock_get_redis.get.assert_called_once_with("notion:users:all")
        mock_notion.users.list.assert_called_once_with()
        mock_get_redis.setex.assert_called_once()

        # Verify the cache was set with the correct timeout
        args = mock_get_redis.setex.call_args[0]
        assert args[0] == "notion:users:all"
        assert args[1] == settings.cache_timeout
        # The third argument is the JSON string, which we can't easily compare directly

    @patch("notion.client.NotionClient._redis")
    @patch("notion.client.NotionClient.notion")
    def test_get_users_with_cache(
        self, mock_notion: MagicMock, mock_get_redis: MagicMock
    ) -> None:
        """Test getting users with cache."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Create cached data that matches what would have been stored
        cached_data = json.dumps(
            [
                {"id": self.user_id_1, "name": self.user_name_1, "object": "user"},
                {"id": self.user_id_2, "name": self.user_name_2, "object": "user"},
            ]
        ).encode("utf-8")
        mock_get_redis.get.return_value = cached_data

        # Call the method
        users = NotionClient.get_users()

        # Verify the results
        assert len(users) == 2
        assert str(users[0].id) == self.user_id_1
        assert users[0].name == self.user_name_1
        assert str(users[1].id) == self.user_id_2
        assert users[1].name == self.user_name_2

        # Verify the mocks were called correctly
        mock_get_redis.get.assert_called_once_with("notion:users:all")

        # Verify the Notion API was NOT called (cache was used)
        mock_notion.users.list.assert_not_called()

        # Verify setex was not called again (no need to set cache again)
        mock_get_redis.setex.assert_not_called()

    @patch("notion.client.NotionClient._redis")
    @patch("notion.client.NotionClient.notion")
    def test_get_users_with_query(
        self, mock_notion: MagicMock, mock_get_redis: MagicMock
    ) -> None:
        """Test getting users with a search query."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Create cached data that matches what would have been stored
        cached_data = json.dumps(
            [
                {"id": self.user_id_1, "name": self.user_name_1, "object": "user"},
                {"id": self.user_id_2, "name": self.user_name_2, "object": "user"},
            ]
        ).encode("utf-8")
        mock_get_redis.get.return_value = cached_data

        # Call the method with a query
        query = "John"
        users = NotionClient.get_users(query=query)

        # Verify the results - should only return the first user
        assert len(users) == 1
        assert str(users[0].id) == self.user_id_1
        assert users[0].name == self.user_name_1

        # Verify the mocks were called correctly
        mock_get_redis.get.assert_called_once_with("notion:users:all")

        # Verify the Notion API was NOT called (cache was used)
        mock_notion.users.list.assert_not_called()

    @patch("notion.client.NotionClient.notion")
    def test_search_issues_no_query(self, mock_notion: MagicMock) -> None:
        """Test searching issues without a query."""
        # Setup mocks
        mock_notion.databases.query.return_value = self.mock_issues_response

        # Call the method
        issues = NotionClient.search_issues()

        # Verify the results
        assert len(issues) == 2
        assert str(issues[0].id) == self.issue_id_1
        assert issues[0].url == self.issue_url_1
        assert str(issues[1].id) == self.issue_id_2
        assert issues[1].url == self.issue_url_2

        database_id = settings.notion_config.database_id

        # Verify the mocks were called correctly
        mock_notion.databases.query.assert_called_once_with(
            database_id=database_id, page_size=10
        )

    @patch("notion.client.NotionClient.notion")
    def test_search_issues_with_query(self, mock_notion: MagicMock) -> None:
        """Test searching issues with a query."""
        # Setup mocks
        mock_notion.databases.query.return_value = {
            "object": "list",
            "results": [self.mock_issues_response["results"][0]],
        }

        # Call the method with a query
        query = "Security"
        issues = NotionClient.search_issues(query=query)

        # Verify the results
        assert len(issues) == 1
        assert str(issues[0].id) == self.issue_id_1
        assert issues[0].url == self.issue_url_1

        database_id = settings.notion_config.database_id

        # Verify the mocks were called correctly
        mock_notion.databases.query.assert_called_once_with(
            database_id=database_id,
            page_size=10,
            filter={
                "property": "title",
                "title": {"contains": query},
            },
        )

    @patch("notion.client.NotionClient.notion")
    @patch("notion.client.NotionClient._retrieve_database")
    def test_create_issue(
        self,
        mock_retrieve_database: MagicMock,
        mock_notion: MagicMock,
    ) -> None:
        """Test creating an issue."""
        # Setup mocks
        mock_database = NotionRetrieveDatabaseResponse.model_validate(
            self.mock_database_response
        )
        mock_retrieve_database.return_value = mock_database
        mock_notion.pages.create.return_value = self.mock_create_page_response
        mock_notion.pages.retrieve.return_value = self.mock_create_page_response

        # Create issue params
        params = CreateNotionIssueParams(
            fields=CreateNotionIssueFields(
                title=self.issue_title_1,
                description="This is a test issue description",
                owner_id=self.user_id_1,
            ),
            webUrl="https://sentry.io/organizations/example/issues/123456/",
            installationId="12345678123456781234567812345678",
            issueId=123,
            project=SentryProject(
                id=123,
                slug="example",
            ),
            actor=SentryActor(id=123, name="John Doe"),
        )

        # Call the method
        response = NotionClient.create_issue(
            title=params.fields.title,
            sentry_issue_url=params.webUrl,
            description=params.fields.description,
            owner_id=params.fields.owner_id,
        )

        # Verify the results
        assert response.issue_id == "ID-123"
        assert response.url == self.issue_url_1

        # Verify the mocks were called correctly
        mock_retrieve_database.assert_called_once()
        mock_notion.pages.create.assert_called_once()

        # Verify the correct properties were passed to the create method
        create_args = mock_notion.pages.create.call_args[1]
        assert (
            create_args["parent"]["database_id"] == settings.notion_config.database_id
        )

        columns = settings.notion_config.column_names

        # In the actual implementation, we don't set the ID property directly
        # The ID is auto-generated by Notion, so we don't need to check it

        assert create_args["properties"][columns.sentry_url]["url"] == params.webUrl
        assert (
            create_args["properties"][columns.assignee]["people"][0]["id"]
            == params.fields.owner_id
        )

    @patch("notion.client.NotionClient.notion")
    def test_get_page_data(self, mock_notion: MagicMock) -> None:
        """Test getting page data."""
        # Setup mocks
        page_id = UUID(self.issue_id_1)
        mock_notion.pages.retrieve.return_value = self.mock_create_page_response

        # Call the method
        response = NotionClient.get_page_data(page_id)

        # Verify the results
        assert response.identifier == "ID-123"
        assert response.url == self.issue_url_1

        # Verify the mocks were called correctly
        mock_notion.pages.retrieve.assert_called_once_with(page_id=str(page_id))

    @patch("notion.client.NotionClient.notion")
    def test_add_sentry_link_to_page(self, mock_notion: MagicMock) -> None:
        """Test adding a Sentry link to a page."""
        # Setup mocks
        page_id = UUID(self.issue_id_1)
        sentry_url = "https://sentry.io/organizations/example/issues/123456/"

        # Call the method
        NotionClient.add_sentry_link_to_page(page_id, sentry_url)

        columns = settings.notion_config.column_names

        # Verify the mocks were called correctly
        mock_notion.pages.update.assert_called_once_with(
            page_id=str(page_id),
            properties={columns.sentry_url: {"url": sentry_url}},
        )

    @patch("notion.client.NotionClient._redis")
    @patch("notion.client.NotionClient.notion")
    def test_retrieve_database_no_cache(
        self, mock_notion: MagicMock, mock_get_redis: MagicMock
    ) -> None:
        """Test retrieving database without cache."""
        # Setup mocks
        mock_get_redis.get.return_value = None  # No cache

        # Mock the Notion API response - return a dict that can be properly validated
        mock_notion.databases.retrieve.return_value = self.mock_database_response

        # Call the method
        database = NotionClient._retrieve_database()

        # Verify the results
        assert len(database.properties) == 4

        # Verify the mocks were called correctly
        mock_get_redis.get.assert_called_once_with("notion:database")
        mock_notion.databases.retrieve.assert_called_once_with(
            database_id=settings.notion_config.database_id
        )
        mock_get_redis.setex.assert_called_once()

        # Verify the cache was set with the correct timeout
        args = mock_get_redis.setex.call_args[0]
        assert args[0] == "notion:database"
        assert args[1] == settings.cache_timeout

    @patch("notion.client.NotionClient._redis")
    @patch("notion.client.NotionClient.notion")
    def test_retrieve_database_with_cache(
        self, mock_notion: MagicMock, mock_get_redis: MagicMock
    ) -> None:
        """Test retrieving database with cache."""
        # Setup mocks
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # First create a NotionRetrieveDatabaseResponse object from the mock data
        database_obj = NotionRetrieveDatabaseResponse.model_validate(
            self.mock_database_response
        )

        # Then serialize it as it would be in the actual implementation
        cached_data = json.dumps(database_obj.model_dump(mode="json")).encode("utf-8")
        mock_get_redis.get.return_value = cached_data

        # Call the method
        database = NotionClient._retrieve_database()

        # Verify the results
        assert len(database.properties) == 4

        # Verify the mocks were called correctly
        mock_get_redis.get.assert_called_once_with("notion:database")
        # Verify the Notion API was NOT called (cache was used)
        mock_notion.databases.retrieve.assert_not_called()

        # Verify setex was not called again (no need to set cache again)
        mock_get_redis.setex.assert_not_called()
