import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, SmallInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")
    article_reads = relationship("ArticleRead", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    company = Column(String, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="watchlist")
    adjacent_mappings = relationship("AdjacentMapping", back_populates="watchlist_item", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),)


class AdjacentMapping(Base):
    __tablename__ = "adjacent_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey("watchlist.id"), nullable=False)
    adjacent_ticker = Column(String, nullable=False)
    adjacent_company = Column(String, nullable=False)

    watchlist_item = relationship("WatchlistItem", back_populates="adjacent_mappings")

    __table_args__ = (UniqueConstraint("watchlist_id", "adjacent_ticker", name="uq_watchlist_adjacent"),)


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String, nullable=False, index=True)
    headline = Column(Text, nullable=False)
    source = Column(String)
    url = Column(Text, unique=True, nullable=False)
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reads = relationship("ArticleRead", back_populates="article", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="article", cascade="all, delete-orphan")


class ArticleRead(Base):
    __tablename__ = "article_reads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    read_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="article_reads")
    article = relationship("Article", back_populates="reads")

    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_user_article_read"),)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    ticker = Column(String, nullable=False)
    vote = Column(SmallInteger, nullable=False)  # 1 = thumbs up, -1 = thumbs down
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="feedback")
    article = relationship("Article", back_populates="feedback")

    __table_args__ = (UniqueConstraint("user_id", "article_id", "ticker", name="uq_user_article_ticker_feedback"),)
