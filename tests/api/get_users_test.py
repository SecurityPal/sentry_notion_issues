from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from notion.types import NotionUserResponse


class TestGetNotionUsers:
    # API endpoint URL
    API_ENDPOINT: str = "/users"

    # Common test data
    USER_ID_1: str = "d40e767c-d7af-4b18-a86d-55c61f1e39a4"
    USER_ID_2: str = "9a3b5ae0-c6e6-482d-b0e1-ed315ee6dc57"
    USER_NAME_1: str = "Avocado Lovelace"
    USER_NAME_2: str = "Doug Engelbot"

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_users(self):
        return [
            NotionUserResponse(
                id=self.USER_ID_1,
                name=self.USER_NAME_1,
            ),
            NotionUserResponse(
                id=self.USER_ID_2,
                name=self.USER_NAME_2,
            ),
        ]

    @pytest.fixture
    def expected_response(self):
        return [
            {
                "label": self.USER_NAME_1,
                "value": self.USER_ID_1,
                "default": False,
            },
            {
                "label": self.USER_NAME_2,
                "value": self.USER_ID_2,
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
    @patch("main.NotionClient.get_users")
    def test_get_notion_users_no_query(
        self, mock_get_users: MagicMock, mock_verify: MagicMock, client, mock_users, expected_response
    ) -> None:
        # Setup mocks
        self._setup_auth_mock(mock_verify)
        mock_get_users.return_value = mock_users

        # Make the request
        response = self._make_request(client)

        # Verify response
        self._verify_successful_response(response, expected_response)

        # Verify the mock was called correctly
        mock_get_users.assert_called_once_with(None)
        mock_verify.assert_called_once()

    @patch("sentry.utils.is_correct_sentry_signature", return_value=True)
    @patch("main.NotionClient.get_users")
    def test_get_notion_users_with_query(
        self, mock_get_users: MagicMock, mock_verify: MagicMock, client, mock_users, expected_response
    ) -> None:
        # Setup mocks
        self._setup_auth_mock(mock_verify)
        # For this test, we'll return only the first user when the query is "avocado"
        mock_get_users.return_value = [mock_users[0]]

        # Make the request with a query that should match only "Avocado"
        response = self._make_request(client, "avocado")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # Only one user should match the query
        expected_filtered_response = [expected_response[0]]
        assert len(data) == 1
        assert data == expected_filtered_response

        # Verify the mock was called correctly
        mock_get_users.assert_called_once_with("avocado")
        mock_verify.assert_called_once()
