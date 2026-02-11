import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Article, WatchlistItem, AdjacentMapping
import logging

logger = logging.getLogger(__name__)

FINVIZ_NEWS_URL = "https://finviz.com/quote.ashx?t={ticker}&ty=c&p=d&b=1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_all_tracked_tickers(db: Session) -> set[str]:
    """Get all unique tickers that need scraping (core watchlist + adjacents)."""
    core_tickers = set(
        row[0] for row in db.execute(select(WatchlistItem.ticker).distinct()).all()
    )
    adjacent_tickers = set(
        row[0] for row in db.execute(select(AdjacentMapping.adjacent_ticker).distinct()).all()
    )
    return core_tickers | adjacent_tickers


def scrape_finviz_news(ticker: str) -> list[dict]:
    """Scrape news articles for a single ticker from Finviz."""
    url = FINVIZ_NEWS_URL.format(ticker=ticker.upper())
    articles = []

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15.0) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        news_table = soup.find("table", {"id": "news-table"})
        if not news_table:
            logger.warning(f"No news table found for {ticker}")
            return articles

        current_date = None
        for row in news_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            date_cell = cells[0].text.strip()
            link_tag = cells[1].find("a")
            if not link_tag:
                continue

            headline = link_tag.text.strip()
            article_url = link_tag.get("href", "")

            # Source is in a span within the second cell
            source_tag = cells[1].find("span")
            source = source_tag.text.strip() if source_tag else None

            # Parse date/time - Finviz shows "Jan-01-25 08:30AM" or just "08:30AM" for same day
            if len(date_cell) > 8:
                # Full date + time
                current_date = date_cell[:9]  # e.g., "Jan-01-25"
                time_str = date_cell[10:].strip()
            else:
                time_str = date_cell

            published_at = None
            if current_date and time_str:
                try:
                    published_at = datetime.strptime(
                        f"{current_date} {time_str}", "%b-%d-%y %I:%M%p"
                    ).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            if article_url:
                articles.append({
                    "ticker": ticker.upper(),
                    "headline": headline,
                    "source": source,
                    "url": article_url,
                    "published_at": published_at,
                })

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping {ticker}: {e}")
    except Exception as e:
        logger.error(f"Error scraping {ticker}: {e}")

    return articles


def store_articles(db: Session, articles: list[dict]) -> int:
    """Store articles in DB, skipping duplicates. Returns count of new articles."""
    new_count = 0
    for article_data in articles:
        existing = db.execute(
            select(Article).where(Article.url == article_data["url"])
        ).scalar_one_or_none()

        if existing is None:
            article = Article(
                ticker=article_data["ticker"],
                headline=article_data["headline"],
                source=article_data["source"],
                url=article_data["url"],
                published_at=article_data["published_at"],
            )
            db.add(article)
            new_count += 1

    db.commit()
    return new_count


def run_scraper(db: Session):
    """Main scraper entrypoint: fetch all tracked tickers and scrape news."""
    tickers = get_all_tracked_tickers(db)
    if not tickers:
        logger.info("No tickers to scrape")
        return

    logger.info(f"Scraping news for {len(tickers)} tickers: {', '.join(sorted(tickers))}")
    total_new = 0
    for ticker in sorted(tickers):
        articles = scrape_finviz_news(ticker)
        if articles:
            new_count = store_articles(db, articles)
            total_new += new_count
            logger.info(f"  {ticker}: {len(articles)} fetched, {new_count} new")

    logger.info(f"Scraper complete: {total_new} new articles stored")
