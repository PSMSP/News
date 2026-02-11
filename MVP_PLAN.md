# Hedge Fund News Platform - MVP Plan

## Overview

A lightweight web application for monitoring news on a personal watchlist of US public equities. Each stock has two news feeds:

- **Direct News**: Articles that explicitly mention the ticker/company
- **Adjacent News**: Articles about related companies (competitors, suppliers, sector peers) that could impact the watched stock's performance

Target: 1-3 users, 10-15 core tickers, ~75 total companies tracked (including adjacents).

---

## Core Features (MVP)

### 1. Watchlist Management
- User types a stock ticker to add it to their watchlist
- Each watchlist entry stores: ticker, company name, date added
- User can remove tickers from the watchlist
- Watchlist persists across sessions

### 2. Adjacent Company Mapping
- When adding a ticker, the user also curates a list of 2-5 adjacent tickers
- Adjacent mappings are stored per watchlist entry (e.g., KO -> [PEP, MNST, KDP, STZ])
- User can edit adjacent tickers at any time
- Adjacency is directional: adding PEP as adjacent to KO does NOT automatically make KO adjacent to PEP (though the user can set both if desired)

### 3. News Ingestion (Finviz Scraper)
- A background job scrapes Finviz news pages for all tracked tickers (core + adjacents) on a polling interval
- **Polling frequency**: Every 2 minutes
- Scraper pulls: headline, source, timestamp, URL, associated ticker
- Articles are deduplicated by URL before storage
- Scraper runs only between **7:00 AM - 7:00 PM EST** (matching notification window)

### 4. News Classification & Display
- **Direct News tab**: Articles where the scraped ticker matches the watchlist ticker
- **Adjacent News tab**: Articles where the scraped ticker matches one of the watchlist ticker's adjacent companies
- Each article displays: headline, source, timestamp, originating ticker (important for adjacent tab so user knows *why* it appeared), link to full article

### 5. In-App Notifications
- Unread article count badge per ticker on the watchlist (split by Direct / Adjacent)
- A global notification indicator showing total new articles since last visit
- Notifications active between **7:00 AM - 7:00 PM EST** only
- Articles arriving outside this window are still stored but do not trigger notifications until the next active window

### 6. Relevance Feedback
- Each article in the Adjacent News tab has a thumbs-up / thumbs-down button
- Feedback is stored (article_id, ticker, vote, timestamp)
- **MVP scope**: Feedback is collected and stored only. No model retraining or automated filtering in MVP. This data will inform future iterations.

---

## Technical Architecture

### Frontend
- **Framework**: React (Vite for build tooling)
- **Routing**: React Router - single-page app with routes for dashboard, ticker detail, settings
- **State**: React context or lightweight state manager (Zustand)
- **Polling**: Frontend polls the backend API every 30 seconds for new articles during active hours
- **UI Library**: Tailwind CSS for styling, keeping it functional over flashy

### Backend
- **Framework**: Python / FastAPI
- **Why Python**: Strong scraping ecosystem (requests, BeautifulSoup), simple async support, quick to build
- **API style**: REST with JSON responses
- **Background jobs**: APScheduler running within the FastAPI process for the Finviz scraper (avoids needing a separate worker/queue system for MVP)

### Database
- **PostgreSQL** (hosted via Supabase, Railway, or Render's managed Postgres)
- Simple schema, ~5 tables (see below)

### Deployment
- **Backend**: Railway or Render (simple container deploy, includes cron/background task support)
- **Frontend**: Vercel or same platform as backend (served as static build)
- **Low maintenance**: Managed Postgres, auto-deploys from git, no server management

### Authentication (MVP)
- **No passwords**. With only 1-3 users, auth is just a username identifier.
- User selects or types their username on first visit; stored in browser localStorage
- Backend associates all watchlist/read-state/feedback data with the username
- No JWT, no tokens, no sessions — the username is sent as a header or query param with each request
- New users are created automatically on first use (no registration flow needed)

---

## Database Schema (Draft)

```
users
  id          UUID PRIMARY KEY
  username    VARCHAR UNIQUE NOT NULL
  created_at  TIMESTAMP

watchlist
  id          UUID PRIMARY KEY
  user_id     UUID REFERENCES users
  ticker      VARCHAR NOT NULL
  company     VARCHAR NOT NULL
  added_at    TIMESTAMP
  UNIQUE(user_id, ticker)

adjacent_mappings
  id              UUID PRIMARY KEY
  watchlist_id    UUID REFERENCES watchlist
  adjacent_ticker VARCHAR NOT NULL
  adjacent_company VARCHAR NOT NULL
  UNIQUE(watchlist_id, adjacent_ticker)

articles
  id              UUID PRIMARY KEY
  ticker          VARCHAR NOT NULL
  headline        TEXT NOT NULL
  source          VARCHAR
  url             TEXT UNIQUE NOT NULL
  published_at    TIMESTAMP
  scraped_at      TIMESTAMP

article_reads
  id          UUID PRIMARY KEY
  user_id     UUID REFERENCES users
  article_id  UUID REFERENCES articles
  read_at     TIMESTAMP

feedback
  id          UUID PRIMARY KEY
  user_id     UUID REFERENCES users
  article_id  UUID REFERENCES articles
  ticker      VARCHAR NOT NULL (the watchlist ticker this was shown under)
  vote        SMALLINT NOT NULL (1 = thumbs up, -1 = thumbs down)
  created_at  TIMESTAMP
  UNIQUE(user_id, article_id, ticker)
```

---

## News Flow (How an Article Moves Through the System)

```
1. Scraper runs every 2 min
2. For each tracked ticker (core + all adjacents across all users):
     - Fetch Finviz news page for that ticker
     - Parse articles (headline, source, URL, time)
     - Insert new articles into `articles` table (skip duplicates by URL)
3. User opens dashboard or frontend polls API:
     - For each watchlist ticker:
       - Direct News = articles WHERE articles.ticker = watchlist.ticker
       - Adjacent News = articles WHERE articles.ticker IN (adjacent_mappings for this watchlist entry)
     - Articles are sorted by published_at DESC
     - Unread count = articles not in article_reads for this user
4. User clicks article -> marked as read in article_reads
5. User votes on adjacent article -> stored in feedback table
```

---

## Key Screens

### Dashboard (Home)
- List of watchlist tickers as cards/rows
- Each shows: ticker, company name, unread Direct count, unread Adjacent count
- "Add Ticker" input at the top
- Click a ticker to go to its detail view

### Ticker Detail View
- Two tabs: **Direct News** | **Adjacent News**
- Each tab is a reverse-chronological feed of articles
- Adjacent News articles show an "via [TICKER]" label indicating the source company
- Adjacent News articles have thumbs-up/thumbs-down buttons
- Sidebar or section showing the adjacent ticker mapping with ability to add/remove

### Settings
- View/edit notification hours (stretch goal, hardcoded to 7am-7pm EST for MVP)

---

## Open Decisions

These don't need to be resolved before starting, but should be decided during development:

1. **Finviz scraping approach**: Direct HTTP requests + BeautifulSoup, or headless browser (Playwright)? Finviz may require headers/cookies to avoid blocks. Needs testing.
2. **Hosting platform**: Railway vs. Render vs. Fly.io - all are viable. Decision based on free tier limits and Postgres add-on pricing.
3. **Frontend polling vs. WebSockets**: Polling every 30s is simpler for MVP. WebSockets could replace this later for true real-time feel.
4. **Ticker validation**: Should the app validate that a ticker is a real US stock when adding? Could use a simple static list of NYSE/NASDAQ tickers or a free API call. Nice-to-have for MVP.

---

## What is Explicitly NOT in MVP

- Mobile app or responsive mobile layout (desktop-first)
- Email/SMS/Slack notifications (in-app only)
- Automated adjacent company suggestions (user curates manually)
- ML-based relevance scoring (just collect feedback data)
- Historical price data or charts
- Sentiment analysis on articles
- Multi-asset support (crypto, futures, international equities)
- Admin panel for user management

---

## Suggested Build Order

1. **Database setup + schema migration**
2. **Backend: User identification** (auto-create user by username on first request)
3. **Backend: Watchlist CRUD** (add/remove ticker, manage adjacents)
4. **Backend: Finviz scraper** (standalone script first, then scheduled job)
5. **Backend: News API endpoints** (direct news, adjacent news, mark read, submit feedback)
6. **Frontend: Username entry page** (simple username picker, stored in localStorage)
7. **Frontend: Dashboard** (watchlist with unread counts)
8. **Frontend: Ticker detail** (two-tab news view, feedback buttons)
9. **Integration testing + deployment**
10. **Notification badge polish + read/unread state**
