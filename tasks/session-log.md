# Session Log

## Session 1 — 2026-03-28

### Completed
- Created full project directory structure (`src/`, `tests/`, `infra/`, `dashboard/`, `scripts/`, `notebooks/`, `tasks/`)
- `requirements.txt` — 14 pinned Week 1 base dependencies
- `.env.template` — all env vars with placeholder values (GROQ, NewsAPI, DB, app settings)
- `.gitignore` — excludes `.env`, `venv/`, `__pycache__/`, `.DS_Store`, logs
- `docker-compose.yml` — removed obsolete `version:` attribute; Postgres service confirmed running
- `src/db/models.py` — 6 SQLAlchemy models: Article, Obligor, ProcessedArticle, ArticleObligor, Alert, ObligorDailySignals
- `src/db/connection.py` — engine, SessionLocal, get_db(), get_db_context(), init_db(), test_connection(); tables created in DB
- `src/utils/config.py` — pydantic-settings singleton (`settings`) loading from `.env`
- `src/utils/logger.py` — loguru logger factory with colored console + optional file sink
- `src/utils/constants.py` — 15 EVENT_TYPES, SEVERITY_LEVELS, KEYWORDS dict, EVENT_SEVERITY_MAP, HIGH_SIGNAL_SOURCES
- `scripts/seed_obligors.py` — 50 obligors seeded across FAANG, banks, tech, pharma, energy, automotive, industrial
- All imports verified working; DB connected (PostgreSQL 15.17); all 6 tables live
- Committed to git: `4f27068` — 34 files, 2379 insertions

### Blockers / Open Questions
- Real API keys (NewsAPI, Groq) need to be added to `.env` — placeholders only right now
- `.env` keys were accidentally exposed in chat — rotate both before use

### Next Step
- Phase 1 data collection: build `src/collectors/newsapi.py`
  - Use `settings.NEWSAPI_KEY` from config
  - Fetch articles by company name/ticker, store into `articles` table
  - Deduplicate by URL (unique constraint already in place)
  - Test with 10 rows before full run (per workflow rules)
