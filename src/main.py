from typing import List, Optional

from fastapi import FastAPI

from notion.client import NotionClient
from sentry.types import (
    CreateNotionIssueParams,
    GetNotionUsersParams,
    LinkNotionIssueParams,
    SearchNotionIssuesParams,
    SentryAsyncFieldResponse,
    SentryIssueResponse,
)
from sentry.utils import require_sentry_signature

app = FastAPI(title="Sentry Notion Integration")


@app.post("/create", response_model=SentryIssueResponse)
@require_sentry_signature
def create_notion_issue(params: CreateNotionIssueParams):
    notion_response = NotionClient.create_issue(
        title=params.fields.title,
        sentry_issue_url=params.webUrl,
        description=params.fields.description,
        owner_id=params.fields.owner_id,
    )
    return SentryIssueResponse(
        webUrl=notion_response.url,
        project="",  # Intentionally blank as identifier is sufficient
        identifier=notion_response.issue_id,
    )


@app.get("/search", response_model=List[SentryAsyncFieldResponse])
@require_sentry_signature
def search_notion_issues(query: Optional[str] = None):
    params = SearchNotionIssuesParams(query=query)
    issues = NotionClient.search_issues(params.query)

    responses: List[SentryAsyncFieldResponse] = []
    for issue in issues:
        for prop in issue.properties.values():
            if prop["type"] == "title":
                title_plain_text = (
                    prop["title"][0]["plain_text"] if prop["title"] else ""
                )
                responses.append(
                    SentryAsyncFieldResponse(
                        label=title_plain_text, value=str(issue.id)
                    )
                )

    return responses


@app.post("/link", response_model=SentryIssueResponse)
@require_sentry_signature
def link_notion_issue(params: LinkNotionIssueParams):
    NotionClient.add_sentry_link_to_page(params.fields.page_id, params.webUrl)

    page_data = NotionClient.get_page_data(params.fields.page_id)

    return SentryIssueResponse(
        webUrl=page_data.url,
        project="",  # Intentionally blank as identifier is sufficient
        identifier=page_data.identifier,
    )


@app.get("/users", response_model=List[SentryAsyncFieldResponse])
@require_sentry_signature
def get_notion_users(query: Optional[str] = None):
    params = GetNotionUsersParams(query=query)
    users = NotionClient.get_users(params.query)
    return [
        SentryAsyncFieldResponse(label=user.name, value=str(user.id)) for user in users
    ]
