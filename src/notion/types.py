from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class NotionProperty(BaseModel):
    id: str
    type: str


class NotionUserResponse(BaseModel):
    id: UUID
    name: str


class NotionUniqueIdPagePropertyValue(BaseModel):
    number: int
    prefix: str


class NotionUniqueIdPageProperty(NotionProperty):
    id: str
    type: Literal["unique_id"]
    unique_id: NotionUniqueIdPagePropertyValue


class NotionCreatePageResponse(BaseModel):
    id: UUID
    url: str


class NotionRetrieveDatabaseResponse(BaseModel):
    properties: Dict[str, NotionProperty]


class NotionRetrievePageResponse(BaseModel):
    id: UUID
    url: str
    properties: Dict[str, dict[str, Any]]


class NotionListUsersResponse(BaseModel):
    results: List[NotionUserResponse]
    next_cursor: Optional[str]


class NotionListUsersParams(BaseModel):
    start_cursor: str


class CreateNotionIssueParams(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: Optional[str] = None


class CreateNotionIssueResponse(BaseModel):
    url: str
    issue_id: str


class GetPageDataResponse(BaseModel):
    identifier: str
    url: str


class NotionFilterDatabaseResponse(BaseModel):
    results: List[NotionRetrievePageResponse]
