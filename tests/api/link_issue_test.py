from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from sentry.types import GetPageDataResponse


class TestLinkNotionIssue:
    # API endpoint URL
    API_ENDPOINT: str = "/link"

    # Common test data
    PAGE_ID: str = "59833787-2cf9-4fdf-8782-e53db20768a5"
    ISSUE_ID: str = "ENG-123"
    PAGE_URL: str = "https://www.notion.so/Tuscan-kale-598337872cf94fdf8782e53db20768a5"

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def request_data(self):
        return {
            "fields": {
                "page_id": self.PAGE_ID,
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
    @patch("main.NotionClient.add_sentry_link_to_page")
    @patch("main.NotionClient.get_page_data")
    def test_link_notion_issue(
        self,
        mock_get_page_data: MagicMock,
        mock_add_link: MagicMock,
        mock_verify: MagicMock,
        client,
        request_data,
        expected_response,
    ) -> None:
        """Test linking a Sentry issue to a Notion page successfully."""
        # Setup mocks
        self._setup_auth_mock(mock_verify)

        # Mock the get_page_data method to return a proper response
        mock_get_page_data.return_value = GetPageDataResponse(
            url=self.PAGE_URL,
            identifier=self.ISSUE_ID,
        )

        # Make the request
        response = self._make_request(client, request_data)

        # Verify response
        self._verify_successful_response(response, expected_response)

        # Verify the mocks were called correctly
        mock_verify.assert_called_once()
        mock_add_link.assert_called_once()
        mock_get_page_data.assert_called_once()

        # Verify add_sentry_link_to_page was called with correct params
        add_link_args = mock_add_link.call_args
        assert str(add_link_args[0][0]) == self.PAGE_ID  # page_id
        assert add_link_args[0][1] == request_data["webUrl"]  # url

        # Verify get_page_data was called with correct page_id
        get_page_args = mock_get_page_data.call_args
        assert str(get_page_args[0][0]) == self.PAGE_ID
