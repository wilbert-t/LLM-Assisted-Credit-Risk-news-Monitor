# Lessons Learned
# Add new lessons at the top. Each entry: date, what went wrong, how to fix.

---

## 2026-04-01 — IVFFlat index returns empty results when lists > row count
**What happened:** Created IVFFlat index with `lists=100` but only 10 rows existed at query time. Retriever returned 0 results even though data was there.
**Fix:** Set `SET LOCAL ivfflat.probes = 10` before any similarity query. Do this at the start of every DB search method that touches the embeddings table. It's session-local and safe to set unconditionally.

---

## 2026-04-01 — pgvector extension must be enabled before create_all()
**What happened:** `Base.metadata.create_all()` fails with a `Vector(384)` column if the `vector` extension isn't installed — SQLAlchemy can't resolve the type.
**Fix:** Always run `conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector")); conn.commit()` before `create_all()`. Do this in both `init_db()` and the test conftest `engine` fixture. Use `pgvector/pgvector:pg15` docker image instead of `postgres:15-alpine`.

---

## 2026-04-01 — Re-running embedding pipeline causes UniqueViolation
**What happened:** Calling `embed_and_store_articles()` twice for the same articles hit the `uq_embeddings_article_chunk` unique constraint and silently rolled back the entire transaction.
**Fix:** Query already-embedded article IDs upfront and filter them out before the embedding loop. Both the pipeline function and CLI script must be idempotent.

---

## 2026-04-01 — ORM model and SQL migration can diverge silently
**What happened:** The IVFFlat index was defined in the SQL migration but not in the ORM model's `__table_args__`. Any deployment using `init_db()` / `create_all()` would create the table without the performance-critical vector index.
**Fix:** Keep `__table_args__` and the migration SQL in sync. For pgvector, add the IVFFlat index to `__table_args__` using `postgresql_using`, `postgresql_with`, and `postgresql_ops` kwargs on `Index()`.

---

## 2026-04-01 — Missing UniqueConstraint on composite FK + sequence columns
**What happened:** `Embedding` model had no uniqueness guarantee on `(article_id, chunk_index)`, meaning re-ingestion would silently produce duplicate chunk rows.
**Fix:** Add `UniqueConstraint("article_id", "chunk_index", name="uq_embeddings_article_chunk")` to `__table_args__` and mirror it in the migration SQL.

---

## 2026-04-01 — datetime.utcnow() produces naive datetime, mismatches timestamptz
**What happened:** `_search_obligor_chunks` used `datetime.datetime.utcnow()` to compute the look-back cutoff. PostgreSQL's `published_at` is `timestamptz` (timezone-aware). Comparing a naive datetime against a timezone-aware column can silently misbehave or raise warnings depending on psycopg2 version.
**Fix:** Use `datetime.datetime.now(datetime.timezone.utc)` everywhere a UTC timestamp is needed. Already noted for collectors — applies equally to any DB filter on timezone-aware columns.

---

## 2026-03-30 — URL uniqueness in test helpers must use a counter, not id()
**What happened:** `_setup_link()` test helper generated URLs using `id(sentiment_score)`. Since `None` is a singleton in Python, `id(None)` is always the same value — two calls with `sentiment_score=None` produced identical URLs, hitting the `uq_articles_url` unique constraint.
**Fix:** Use a module-level counter (`global _url_counter; _url_counter += 1`) for unique URL generation in test helpers. Never use `id()` of a value that might be a singleton (None, True, False, small ints).

---

## 2026-03-30 — JSON column filter: use `::text LIKE` not `!= '{}'`
**What happened:** Filtering a JSON column with `entities != '{}'` raised `operator does not exist: json <> unknown`. PostgreSQL can't compare JSON directly to a string literal.
**Fix:** Cast to text: `entities::text LIKE '%"ORG"%'`. Works for checking key presence in a JSON column without needing `jsonb`.

---

## 2026-03-30 — spaCy + pydantic 2.5.0 + Python 3.12 crashes at import
**What happened:** `import spacy` raised `TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'`. Happened with both spaCy 3.7.4 and 3.8.4.
**Root cause:** spaCy uses `pydantic.v1` (the v1 compat shim bundled in pydantic 2.x) internally. Python 3.12 changed `ForwardRef._evaluate()` to require a `recursive_guard` kwarg, and pydantic 2.5.0's v1 compat didn't account for this.
**Fix:** Upgrade pydantic to `>=2.10.0` — the v1 compat layer was patched to handle the Python 3.12 signature.
```
pydantic==2.10.6
pydantic-settings==2.7.0
```
**Rule:** When adding any NLP library that uses pydantic v1 internally (spaCy, LangChain, etc.) on Python 3.12, ensure pydantic >= 2.10.

---

## 2026-03-29 — datetime.utcnow() deprecated in Python 3.12
**What happened:** Running `collect_news_all.py` printed `DeprecationWarning: datetime.datetime.utcnow() is deprecated`.
**Fix:** Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` everywhere. Import `timezone` from `datetime`. The strftime call stays the same — just the object creation changes:
```python
# Before
from datetime import datetime
datetime.utcnow()

# After
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

---

## 2026-03-29 — Single-ticker queries match too broadly
**What happened:** Citigroup ticker `C` returned 5,192 results — the letter "C" matches almost everything. Same risk with tickers like `T` (AT&T), `F` (Ford).
**Fix:** For single-letter tickers, rely on the quoted company name only, or append sector context to the query. Consider skipping the ticker entirely if `len(ticker) == 1`.

---

## 2026-03-29 — tasks/ directory not persisted in git
**What happened:** The `tasks/` directory was created locally but git doesn't track empty directories.
**Fix:** Always add a `.gitkeep` or real content file to directories that must persist. Moved logs to `.claude/` which is already tracked.

---

## 2026-03-28 — Real API keys committed to .env.template
**What happened:** Real Groq and NewsAPI keys ended up in `.env.template` and got committed. GitHub push protection blocked the push.
**Fix:** `.env.template` must ONLY contain placeholders. Real keys go ONLY in `.env` (gitignored). Used `git filter-branch` to rewrite history, then force-pushed. Rotate any key that touched git history.

---

## 2026-03-28 — SQLAlchemy reserved attribute name
**What happened:** Named a column `metadata` on the `Alert` model — reserved by SQLAlchemy's `declarative_base`.
**Fix:** Renamed to `extra_data`. Avoid: `metadata`, `query`, `registry` as column names.

---

## 2026-03-28 — ModuleNotFoundError running files directly
**What happened:** `python src/db/connection.py` fails — Python doesn't know the project root.
**Fix:** Always use `python -m src.db.connection` from project root.

---

## 2026-03-28 — Docker service name mismatch
**What happened:** `docker-compose exec db psql` fails — service is named `postgres` not `db`.
**Fix:** Check service names with `docker-compose ps`. Use `docker-compose exec postgres psql ...`.
