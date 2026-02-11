from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.database import get_db
from app.models import User, WatchlistItem, AdjacentMapping, Article, ArticleRead, Feedback
from app.schemas import ArticleOut, FeedbackCreate, FeedbackOut, TickerNewsCount
from app.routes.users import get_current_user

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/counts", response_model=list[TickerNewsCount])
def get_unread_counts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get unread article counts for each ticker in the user's watchlist."""
    watchlist_items = db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id)
    ).scalars().all()

    read_article_ids = set(
        row[0] for row in db.execute(
            select(ArticleRead.article_id).where(ArticleRead.user_id == user.id)
        ).all()
    )

    counts = []
    for item in watchlist_items:
        # Direct: unread articles for this ticker
        direct_articles = db.execute(
            select(Article.id).where(Article.ticker == item.ticker)
        ).all()
        direct_unread = sum(1 for (aid,) in direct_articles if aid not in read_article_ids)

        # Adjacent: unread articles for adjacent tickers
        adjacent_tickers = [m.adjacent_ticker for m in item.adjacent_mappings]
        adjacent_unread = 0
        if adjacent_tickers:
            adj_articles = db.execute(
                select(Article.id).where(Article.ticker.in_(adjacent_tickers))
            ).all()
            adjacent_unread = sum(1 for (aid,) in adj_articles if aid not in read_article_ids)

        counts.append(TickerNewsCount(
            ticker=item.ticker,
            company=item.company,
            watchlist_id=item.id,
            direct_unread=direct_unread,
            adjacent_unread=adjacent_unread,
        ))

    return counts


@router.get("/{watchlist_id}/direct", response_model=list[ArticleOut])
def get_direct_news(
    watchlist_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get direct news articles for a watchlist ticker."""
    item = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == watchlist_id,
            WatchlistItem.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    read_article_ids = set(
        row[0] for row in db.execute(
            select(ArticleRead.article_id).where(ArticleRead.user_id == user.id)
        ).all()
    )

    articles = db.execute(
        select(Article)
        .where(Article.ticker == item.ticker)
        .order_by(Article.published_at.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return [
        ArticleOut(
            id=a.id,
            ticker=a.ticker,
            headline=a.headline,
            source=a.source,
            url=a.url,
            published_at=a.published_at,
            scraped_at=a.scraped_at,
            is_read=a.id in read_article_ids,
        )
        for a in articles
    ]


@router.get("/{watchlist_id}/adjacent", response_model=list[ArticleOut])
def get_adjacent_news(
    watchlist_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get adjacent news articles for a watchlist ticker."""
    item = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == watchlist_id,
            WatchlistItem.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    adjacent_tickers = [m.adjacent_ticker for m in item.adjacent_mappings]
    if not adjacent_tickers:
        return []

    read_article_ids = set(
        row[0] for row in db.execute(
            select(ArticleRead.article_id).where(ArticleRead.user_id == user.id)
        ).all()
    )

    articles = db.execute(
        select(Article)
        .where(Article.ticker.in_(adjacent_tickers))
        .order_by(Article.published_at.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return [
        ArticleOut(
            id=a.id,
            ticker=a.ticker,
            headline=a.headline,
            source=a.source,
            url=a.url,
            published_at=a.published_at,
            scraped_at=a.scraped_at,
            is_read=a.id in read_article_ids,
        )
        for a in articles
    ]


@router.post("/{article_id}/read", status_code=201)
def mark_article_read(
    article_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark an article as read."""
    article = db.execute(select(Article).where(Article.id == article_id)).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    existing = db.execute(
        select(ArticleRead).where(
            ArticleRead.user_id == user.id,
            ArticleRead.article_id == article_id,
        )
    ).scalar_one_or_none()
    if existing:
        return {"status": "already_read"}

    read = ArticleRead(user_id=user.id, article_id=article_id)
    db.add(read)
    db.commit()
    return {"status": "marked_read"}


@router.post("/{article_id}/feedback/{ticker}", response_model=FeedbackOut, status_code=201)
def submit_feedback(
    article_id: UUID,
    ticker: str,
    body: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit thumbs up/down feedback on an adjacent news article."""
    if body.vote not in (1, -1):
        raise HTTPException(status_code=400, detail="Vote must be 1 or -1")

    article = db.execute(select(Article).where(Article.id == article_id)).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    existing = db.execute(
        select(Feedback).where(
            Feedback.user_id == user.id,
            Feedback.article_id == article_id,
            Feedback.ticker == ticker.upper(),
        )
    ).scalar_one_or_none()

    if existing:
        existing.vote = body.vote
        db.commit()
        db.refresh(existing)
        return existing

    fb = Feedback(
        user_id=user.id,
        article_id=article_id,
        ticker=ticker.upper(),
        vote=body.vote,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb
