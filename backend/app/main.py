import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import SCRAPE_INTERVAL_MINUTES, NOTIFICATION_START_HOUR, NOTIFICATION_END_HOUR
from app.database import SessionLocal, engine
from app.models import Base
from app.routes import users, watchlist, news
from app.scraper import run_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_scrape():
    """Run scraper if within active hours (EST)."""
    now_est = datetime.now(ZoneInfo("America/New_York"))
    if NOTIFICATION_START_HOUR <= now_est.hour < NOTIFICATION_END_HOUR:
        logger.info(f"Running scheduled scrape at {now_est.strftime('%H:%M EST')}")
        db = SessionLocal()
        try:
            run_scraper(db)
        finally:
            db.close()
    else:
        logger.debug(f"Outside active hours ({now_est.strftime('%H:%M EST')}), skipping scrape")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for development; use Alembic in production)
    Base.metadata.create_all(bind=engine)

    # Start the scraper scheduler
    scheduler.add_job(
        scheduled_scrape,
        "interval",
        minutes=SCRAPE_INTERVAL_MINUTES,
        id="finviz_scraper",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scraper scheduled every {SCRAPE_INTERVAL_MINUTES} minutes")

    yield

    # Shutdown
    scheduler.shutdown()


app = FastAPI(title="Hedge Fund News Platform", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(watchlist.router)
app.include_router(news.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
