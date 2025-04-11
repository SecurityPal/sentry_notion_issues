from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from notion.types import CreateNotionIssueResponse


class TestCreateNotionIssue:
    # API endpoint URL
    API_ENDPOINT: str = "/create"

    # Common test data
    USER_ID: str = "ee5f0f84-409a-440f-983a-a5315961c6e4"
    ISSUE_ID: str = "ENG-123"
    PAGE_URL: str = "https://www.notion.so/Tuscan-kale-598337872cf94fdf8782e53db20768a5"

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def request_data(self):
        return {
            "fields": {
                "owner_id": self.USER_ID,
                "title": "Test Issue",
                "description": "This is a test issue description",
            },
            "installationId": "test-installation-id",
            "issueId": 123,
            "webUrl": "https://sentry.io/issues/123",
            "project": {"slug": "test-project", "id": 123},
            "actor": {"name": "Test User", "id": 123},
        }

    @pytest.fixture
    def expected_response(self):
        return {
            "webUrl": self.PAGE_URL,
            "project": "",
            "identifier": self.ISSUE_ID,
        }

    def _setup_auth_mock(self, mock_verify: MagicMock, authorized: bool = True) -> None:
        """Helper method to set up the authentication mock."""
        mock_verify.return_value = authorized

    def _get_api_url(self) -> str:
        """Helper method to get the API URL."""
        return self.API_ENDPOINT

    def _make_request(self, client, request_data):
        """Helper method to make a request to the API."""
        url = self._get_api_url()
        return client.post(
            url, json=request_data, headers={"sentry-hook-signature": "valid-signature"}
        )

    def _verify_successful_response(self, response, expected_response) -> None:
        """Helper method to verify a successful response."""
        assert response.status_code == 200
        data = response.json()
        assert data == expected_response

    @patch("sentry.utils.is_correct_sentry_signature", return_value=True)
    @patch("main.NotionClient.create_issue")
    def test_create_notion_issue(
        self,
        mock_create_issue: MagicMock,
        mock_verify: MagicMock,
        client,
        request_data,
        expected_response,
    ) -> None:
        """Test creating a Notion issue successfully."""
        # Mock the create_issue method to return a proper response
        mock_create_issue.return_value = CreateNotionIssueResponse(
            url=self.PAGE_URL,
            issue_id=self.ISSUE_ID,
        )

        # Make the request
        response = self._make_request(client, request_data)

        # Verify response
        self._verify_successful_response(response, expected_response)

        # Verify the mocks were called correctly
        mock_verify.assert_called()
        mock_create_issue.assert_called_once()

        # Verify the create_issue was called with correct parameters
        mock_create_issue.assert_called_with(
            title=request_data["fields"]["title"],
            sentry_issue_url=request_data["webUrl"],
            description=request_data["fields"]["description"],
            owner_id=request_data["fields"]["owner_id"],
        )
