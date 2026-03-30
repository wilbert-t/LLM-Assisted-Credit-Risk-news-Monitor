# Session Log
# Keep only last 3 sessions.

---

## Session 4 — 2026-03-30

### Completed
- Fixed Docker port conflict: changed port mapping from 5432 → 5433 in `docker-compose.yml` and `.env`
- Fixed `datetime.utcnow()` deprecation warnings (Python 3.12) in:
  - `src/collectors/news_api.py` — replaced with `datetime.now(timezone.utc)`
  - `scripts/collect_news_all.py` — replaced with `datetime.now(timezone.utc)`
- Re-seeded obligors (50 in DB)
- Re-ran full batch collector: **2,258 articles collected successfully from all 50 obligors**
- ✅ No deprecation warnings, all data verified in DB

### Blockers / Open Questions
- None

### Next Step
- Phase 2: Text processing — `src/processors/cleaner.py`
  - Strip HTML tags from `content` field
  - Normalize whitespace
  - Filter articles under minimum length threshold

---

## Session 3 — 2026-03-29

### Completed
- `src/collectors/news_api.py` — `NewsAPICollector` class with `fetch_news()`, `fetch_all_pages()`, retry/backoff, rate limit handling, 30s timeout
- `src/collectors/storage.py` — `store_articles()` with ON CONFLICT DO NOTHING deduplication, batch inserts, `get_article_count()`
- `scripts/collect_news_all.py` — batch collector looping all 50 obligors, 1s delay between requests, graceful rate limit stop
- **End-to-end test run completed** (9/50 obligors, stopped manually per cowork instructions):
  - 540 articles inserted into DB
  - Duplicates handled correctly (e.g. MSFT: 11 dupes silently skipped)
  - 1s delay between requests confirmed in logs
  - `finally` block printed summary even after Ctrl+C
- Cowork checklist status:
  - ✅ 100+ articles inserted (540)
  - ✅ Deduplication working
  - ✅ Rate limit delays working
  - ✅ API key guard working
  - ⚠️ `datetime.utcnow()` deprecation warning — fix next session

### Blockers / Open Questions
- `datetime.utcnow()` deprecated in Python 3.12 — replace with `datetime.now(UTC)` in `collect_news_all.py` and `news_api.py`
- Only 9/50 obligors collected — run full 50 when ready (costs 50 API requests)

### Next Step
- Fix `datetime.utcnow()` deprecation warning in `scripts/collect_news_all.py` and `src/collectors/news_api.py`
- Then Phase 2: text processing — `src/processors/cleaner.py`
  - Strip HTML tags from `content` field
  - Normalize whitespace
  - Filter articles under minimum length threshold

---

## Session 2 — 2026-03-29

### Completed
- Confirmed all Day 1 work intact: seed_obligors (50 in DB), config, logger, constants
- Moved session-log.md and lessons.md from `tasks/` → `.claude/`, removed `tasks/` dir
- Updated all `tasks/` path references in CLAUDE.md to `.claude/`
- Built `src/collectors/news_api.py` and `src/collectors/storage.py`
- Built `scripts/collect_news_all.py`

### Next Step
- ~~Run collector~~ → completed in Session 3

---

## Session 1 — 2026-03-28

### Completed
- Full project structure, DB models, utilities, seed script
- Git history rewritten to scrub exposed API keys, force-pushed to GitHub

### Next Step
- ~~NewsAPI collector~~ → completed in Sessions 2–3
