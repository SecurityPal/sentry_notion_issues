from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from main import app
from notion.types import NotionRetrievePageResponse


class TestSearchNotionIssues:
    # API endpoint URL
    API_ENDPOINT: str = "/search"

    # Common test data
    ISSUE_ID_1: str = "59833787-2cf9-4fdf-8782-e53db20768a5"
    ISSUE_ID_2: str = "ee5f0f84-409a-440f-983a-a5315961c6e4"
    ISSUE_TITLE_1: str = "Security Vulnerability in Auth Service"
    ISSUE_TITLE_2: str = "Performance Issue in API Gateway"
    ISSUE_URL_1: str = (
        "https://www.notion.so/Security-Vulnerability-598337872cf94fdf8782e53db20768a5"
    )
    ISSUE_URL_2: str = (
        "https://www.notion.so/Performance-Issue-ee5f0f84409a440f983aa5315961c6e4"
    )

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_issues(self):
        # Setup mock Notion page responses
        return [
            NotionRetrievePageResponse(
                id=UUID(self.ISSUE_ID_1),
                url=self.ISSUE_URL_1,
                properties={
                    "Name": {
                        "id": "title",
                        "type": "title",
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": self.ISSUE_TITLE_1, "link": None},
                                "plain_text": self.ISSUE_TITLE_1,
                            }
                        ],
                    }
                },
            ),
            NotionRetrievePageResponse(
                id=UUID(self.ISSUE_ID_2),
                url=self.ISSUE_URL_2,
                properties={
                    "Name": {
                        "id": "title",
                        "type": "title",
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": self.ISSUE_TITLE_2, "link": None},
                                "plain_text": self.ISSUE_TITLE_2,
                            }
                        ],
                    }
                },
            ),
        ]

    @pytest.fixture
    def expected_response(self):
        # Expected response format for the API
        return [
            {
                "label": self.ISSUE_TITLE_1,
                "value": self.ISSUE_ID_1,
                "default": False,
            },
            {
                "label": self.ISSUE_TITLE_2,
                "value": self.ISSUE_ID_2,
                "default": False,
            },
        ]

    def _setup_auth_mock(self, mock_verify: MagicMock, authorized: bool = True) -> None:
        """Helper method to set up the authentication mock."""
        mock_verify.return_value = authorized

    def _get_api_url(self, query: Optional[str] = None) -> str:
        """Helper method to get the API URL with optional query parameter."""
        url = self.API_ENDPOINT
        if query is not None:
            return f"{url}?query={query}"
        return url

    def _make_request(self, client, query: Optional[str] = None):
        """Helper method to make a request to the API."""
        url = self._get_api_url(query)
        return client.get(
            url, headers={"sentry-hook-signature": "valid-signature"}
        )

    def _verify_successful_response(
        self, response, expected_data: List[Dict[str, Any]]
    ) -> None:
        """Helper method to verify a successful response."""
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(expected_data)
        assert data == expected_data

    @patch("sentry.utils.is_correct_sentry_signature", return_value=True)
    @patch("main.NotionClient.search_issues")
    def test_search_notion_issues_no_query(
        self, mock_search_issues: MagicMock, mock_verify: MagicMock, client, mock_issues, expected_response
    ) -> None:
        """Test searching Notion issues without a query parameter."""
        # Setup mocks
        self._setup_auth_mock(mock_verify)
        mock_search_issues.return_value = mock_issues

        # Make the request
        response = self._make_request(client)

        # Verify response
        self._verify_successful_response(response, expected_response)

        # Verify the mocks were called correctly
        mock_search_issues.assert_called_once_with(None)
        mock_verify.assert_called_once()

    @patch("sentry.utils.is_correct_sentry_signature", return_value=True)
    @patch("main.NotionClient.search_issues")
    def test_search_notion_issues_with_query(
        self, mock_search_issues: MagicMock, mock_verify: MagicMock, client, mock_issues, expected_response
    ) -> None:
        """Test searching Notion issues with a query parameter."""
        # Setup mocks
        self._setup_auth_mock(mock_verify)
        # Return only the first issue for the filtered search
        mock_search_issues.return_value = [mock_issues[0]]

        # Make the request with a query
        query = "Security"
        response = self._make_request(client, query)

        # Verify response
        expected_filtered_response = [expected_response[0]]
        self._verify_successful_response(response, expected_filtered_response)

        # Verify the mocks were called correctly
        mock_search_issues.assert_called_once_with(query)
        mock_verify.assert_called_once()

    @patch("sentry.utils.is_correct_sentry_signature", return_value=True)
    @patch("main.NotionClient.search_issues")
    def test_search_notion_issues_empty_results(
        self, mock_search_issues: MagicMock, mock_verify: MagicMock, client, mock_issues
    ) -> None:
        """Test searching Notion issues with no matching results."""
        # Setup mocks
        self._setup_auth_mock(mock_verify)
        mock_search_issues.return_value = []

        # Make the request with a query that won't match anything
        query = "NonExistentIssue"
        response = self._make_request(client, query)

        # Verify response is an empty list
        self._verify_successful_response(response, [])

        # Verify the mocks were called correctly
        mock_search_issues.assert_called_once_with(query)
        mock_verify.assert_called_once()
