from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


# --- Users ---
class UserOut(BaseModel):
    id: UUID
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Watchlist ---
class AdjacentMappingCreate(BaseModel):
    adjacent_ticker: str
    adjacent_company: str


class AdjacentMappingOut(BaseModel):
    id: UUID
    adjacent_ticker: str
    adjacent_company: str

    model_config = {"from_attributes": True}


class WatchlistItemCreate(BaseModel):
    ticker: str
    company: str
    adjacents: list[AdjacentMappingCreate] = []


class WatchlistItemOut(BaseModel):
    id: UUID
    ticker: str
    company: str
    added_at: datetime
    adjacent_mappings: list[AdjacentMappingOut] = []

    model_config = {"from_attributes": True}


# --- Articles ---
class ArticleOut(BaseModel):
    id: UUID
    ticker: str
    headline: str
    source: str | None
    url: str
    published_at: datetime | None
    scraped_at: datetime | None
    is_read: bool = False

    model_config = {"from_attributes": True}


# --- Feedback ---
class FeedbackCreate(BaseModel):
    vote: int  # 1 or -1


class FeedbackOut(BaseModel):
    id: UUID
    article_id: UUID
    ticker: str
    vote: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Notification counts ---
class TickerNewsCount(BaseModel):
    ticker: str
    company: str
    watchlist_id: UUID
    direct_unread: int
    adjacent_unread: int
