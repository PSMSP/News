import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/newsplatform")
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "2"))
NOTIFICATION_START_HOUR = int(os.getenv("NOTIFICATION_START_HOUR", "7"))
NOTIFICATION_END_HOUR = int(os.getenv("NOTIFICATION_END_HOUR", "19"))
