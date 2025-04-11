from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SentryProject(BaseModel):
    slug: str
    id: int


class SentryActor(BaseModel):
    name: str
    id: int


class CreateNotionIssueFields(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: Optional[str] = None


class SentryIntegrationRequestParams(BaseModel):
    installationId: str
    issueId: int
    webUrl: str
    project: SentryProject
    actor: SentryActor


class CreateNotionIssueParams(SentryIntegrationRequestParams):
    fields: CreateNotionIssueFields


class SentryIssueResponse(BaseModel):
    webUrl: str
    project: str
    identifier: str


class SentryAsyncFieldResponse(BaseModel):
    label: str
    value: str
    default: bool = False


class GetNotionUsersParams(BaseModel):
    query: Optional[str] = None


class SearchNotionIssuesParams(BaseModel):
    query: Optional[str] = None


class LinkNotionIssueFields(BaseModel):
    page_id: UUID


class LinkNotionIssueParams(SentryIntegrationRequestParams):
    fields: LinkNotionIssueFields


class GetPageDataResponse(BaseModel):
    identifier: str
    url: str
