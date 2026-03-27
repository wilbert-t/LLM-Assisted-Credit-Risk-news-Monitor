# 🤖 Claude Code + Cowork Workflow Guide

## Overview

You have two tools working together:

| Tool | Role | Best For |
|------|------|----------|
| **Claude Code** | Terminal-based coding | Writing code, running scripts, git commands |
| **Cowork** | UI automation | Running tests, docker commands, file management |

**Both are always running.** They work in parallel—Claude Code writes the code, Cowork runs it and reports back.

---

## ⚡ DAILY WORKFLOW

### Morning (9 AM)
1. **Review standup log** from yesterday (5 min)
2. **Read session-log.md** to know where we left off (5 min)
3. **Check project status** (5 min):
   ```bash
   # In terminal
   docker-compose ps        # Database running?
   git log --oneline -5    # Recent commits
   pytest tests/ -q        # Tests passing?
   ```

### Work Session (2-4 hours)
1. **Claude Code**: Writes code based on daily task
2. **Cowork**: Runs tests/docker/scripts to verify
3. **Both**: Iterate until feature complete

### End of Day (5 PM)
1. **Verify work**: All tests passing
2. **Commit**: `git add . && git commit -m "..."`
3. **Update logs**: 
   - DAILY_STANDUP_LOG.md (today's entry)
   - session-log.md (what was done, blockers, next step)

---

## 🎯 CLAUDE CODE COMMANDS

These are commands you'll use to invoke Claude Code. Run these in your terminal (you have Claude Code active in your IDE).

### Week 1, Day 1: Bootstrap

```bash
# Command 1: Initialize project structure
claude-code "Set up complete project directory structure for Credit Risk Monitor:
- Create src/ subdirectories (collectors, processors, models, rag, alerts, api, db, utils)
- Create tests/ (unit/, integration/), infra/, dashboard/, docs/, scripts/
- Create all __init__.py files
- Initialize git repo
Show me the tree structure when done."

# Command 2: Create requirements.txt with base dependencies
claude-code "Create requirements.txt with these base packages:
fastapi, uvicorn, sqlalchemy, psycopg2-binary, alembic, python-dotenv, pydantic, pandas, requests, beautifulsoup4
Keep it minimal for now (no ML/NLP yet).
Show me the file content."

# Command 3: Write .env template
claude-code "Create .env.template file with:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/credit_risk
NEWSAPI_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
LOG_LEVEL=INFO
ENVIRONMENT=development
Show the file."
```

### Week 1, Day 2: Database Models

```bash
# Command 4: Create SQLAlchemy models
claude-code "Write src/db/models.py with SQLAlchemy ORM models for:
1. Article (id, title, content, url, source, published_at, fetched_at, language)
2. Obligor (id, name, ticker, lei, sector, country)
3. ProcessedArticle (id, article_id FK, cleaned_text, entities JSON, sentiment_score, is_credit_relevant)
4. ArticleObliger (article_id FK, obligor_id FK) - many-to-many join table
5. Alert (id, obligor_id FK, triggered_at, severity, summary, event_types JSON, article_ids JSON)
6. ObligorDailySignals (id, obligor_id FK, date, neg_article_count, avg_sentiment, credit_relevant_count)

Include proper primary keys, foreign keys, indexes, and timestamps (created_at, updated_at).
Use proper SQLAlchemy syntax and docstrings."

# Command 5: Create database connection module
claude-code "Write src/db/connection.py with:
1. Import and create SQLAlchemy engine from DATABASE_URL env var
2. Create SessionLocal = sessionmaker(bind=engine)
3. Function: get_db() - yields DB session (for FastAPI dependency injection)
4. Function: init_db() - creates all tables
5. Function: test_connection() - connects and prints database version
6. __main__ block - calls test_connection()

Make it production-ready with error handling."

# Command 6: Set up Alembic migrations
claude-code "Initialize Alembic for database migrations:
1. Run: alembic init infra/migrations
2. Configure alembic.ini to point to src/db/models.py
3. Create first migration with: alembic revision --autogenerate -m 'Initial: articles, obligors, processed_articles tables'
4. Show me the migration file so I can review it
Don't apply it yet (Cowork will do that)."
```

### Week 1, Day 3: Utilities & Seeding

```bash
# Command 7: Create utility modules
claude-code "Write three utility modules:

1. src/utils/config.py
   - Use pydantic BaseSettings
   - Load from .env with python-dotenv
   - Fields: DATABASE_URL, NEWSAPI_KEY, ANTHROPIC_API_KEY, LOG_LEVEL, ENVIRONMENT
   - Create singleton: settings = Settings()

2. src/utils/logger.py
   - Use loguru
   - Setup console + file logging
   - Return logger instance

3. src/utils/constants.py
   - EVENT_TYPES = ['downgrade', 'default', 'bankruptcy', 'lawsuit', 'fraud', 'liquidity']
   - SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']
   - KEYWORDS dict mapping event types to keywords

All with docstrings and type hints."

# Command 8: Create obligor seed script
claude-code "Write scripts/seed_obligors.py that:
1. Define 50 companies (FAANG, major banks, tech, pharma, energy, aerospace, media, consumer)
2. Import models and SessionLocal
3. Function: seed_obligors() that:
   - Creates Obligor record for each company
   - Avoids duplicates (check if ticker exists first)
   - Commits to database
4. __main__ block - calls seed_obligors() and prints 'Seeded 50 obligors'

Include companies like: Apple, Microsoft, Google, Amazon, Meta, JPMorgan, Goldman Sachs, Tesla, NVIDIA, Pfizer, Exxon, Boeing, etc.
Each with: name, ticker, sector, country (USA)"

# Command 9: Initial git commit
claude-code "Stage all files and commit with message:
git add .
git commit -m 'Initial: project structure, database models, utilities, obligor seeding'
Show me the git log (last 5 commits)."
```

### Week 1, Day 4: NewsAPI Collector

```bash
# Command 10: Create NewsAPI collector
claude-code "Write src/collectors/news_api.py with:

Class NewsAPICollector:
- __init__(api_key): Store API key + base_url = 'https://newsapi.org/v2/everything'

Methods:
- fetch_news(query, from_date=None, page_size=100) -> List[Dict]
  * Default from_date: 7 days ago
  * Parameters: q, from, pageSize, language=en, sortBy=publishedAt, apiKey
  * Make GET request with timeout=30
  * Handle rate limits (return [] if error)
  * Return articles list

- With error handling:
  * Catch RequestException
  * Log to logger
  * Return empty list on failure

Test function at bottom:
- Fetch news for 'Apple Inc.'
- Print count + first article title
- Can be run as: python src/collectors/news_api.py"

# Command 11: Create storage module
claude-code "Write src/collectors/storage.py with:

Function: store_articles(articles: List[Dict]) -> int
- For each article:
  * Create Article dict with: title, content, url, source, published_at, raw_json
  * Use SQLAlchemy insert().on_conflict_do_nothing(index_elements=['url'])
  * This prevents duplicate URLs

Function: get_article_count() -> int
- Query count of articles in database

Error handling:
- Try/except around db.execute()
- Rollback on error
- Log failures
- Return count of new articles inserted

Both functions should use SessionLocal from connection.py"

# Command 12: Create main collection script
claude-code "Write scripts/collect_news_all.py that:
1. Load all obligors from database
2. For each obligor:
   - Fetch news by obligor.name (use NewsAPICollector)
   - Store articles (use store_articles)
   - Sleep 1 second (rate limiting)
   - Print progress: 'Collected X articles for [Company] (Y/50)'
3. After all: Print total count

Error handling:
- If NEWSAPI_KEY missing, print helpful error
- If API fails, log and continue to next obligor

Can be run as: python scripts/collect_news_all.py"
```

### Week 1, Day 5: Testing Framework

```bash
# Command 13: Create test fixtures
claude-code "Write tests/conftest.py with pytest fixtures:

Fixtures:
1. test_db() - Create in-memory SQLite for tests
   - Create engine with sqlite:///:memory:
   - Create all tables (Base.metadata.create_all)
   - Yield session
   - Cleanup after

2. test_obligor(test_db) - Insert sample Obligor
   - name='TestCorp', ticker='TEST', sector='Tech'
   - Return obligor object

3. test_article(test_db) - Insert sample Article
   - title='Test', content='Test content', url='https://test.com/1'
   - published_at=datetime.now()
   - Return article object

4. client - FastAPI TestClient
   - Will be used later for API tests

All fixtures should clean up after themselves (no pollution between tests)"

# Command 14: Write unit tests for storage
claude-code "Write tests/unit/test_storage.py with pytest tests:

Tests:
1. test_store_single_article(test_db)
   - Create article dict
   - Call store_articles([article])
   - Assert count returned == 1
   - Query DB, verify article exists

2. test_store_duplicate(test_db)
   - Insert same article twice
   - Assert second insert returns 0 (deduplication worked)

3. test_store_batch(test_db)
   - Create 50 article dicts
   - Call store_articles(articles)
   - Assert count == 50
   - Query DB, verify all 50 exist

4. test_store_missing_url(test_db)
   - Article without 'url' field
   - Should be skipped (no crash)

5. test_store_invalid_data(test_db)
   - Article with invalid data types
   - Should handle gracefully (log error)"

# Command 15: Write model tests
claude-code "Write tests/unit/test_models.py with:

Tests:
1. test_article_creation(test_db)
   - Create Article instance
   - Verify all fields set correctly

2. test_obligor_relationships(test_db)
   - Create Obligor + multiple Articles
   - Verify foreign keys working

3. test_timestamps(test_db)
   - Create record
   - Verify created_at populated automatically

4. test_article_uniqueness(test_db)
   - Try to insert 2 articles with same URL
   - Second should fail or be skipped"
```

### Week 1, Day 6: GitHub Actions & Docs

```bash
# Command 16: Create GitHub Actions workflow
claude-code "Write .github/workflows/test.yml that:
1. Trigger: on push to any branch
2. Runs on: ubuntu-latest, Python 3.11
3. Steps:
   - Checkout code
   - Set up Python 3.11
   - Install dependencies: pip install -r requirements.txt
   - Run tests: pytest tests/unit -v --cov=src
   - Upload coverage

Make it only run if changes to src/ or tests/"

# Command 17: Write initial README
claude-code "Write README.md with sections:
1. Title: Credit Risk Monitoring System
2. Problem: Banks monitor thousands of companies, need automated solution
3. Solution: AI pipeline (News → NLP → RAG → Alerts)
4. Quick Start: 5 steps to get running
5. Project Structure: tree view
6. Tech Stack: table format
7. Development: how to run tests
8. Week-by-week: checklist with ✅/⏳
9. Links: to GitHub Actions, docs, etc.

Include code badges for coverage (once we have them)"

# Command 18: Commit Week 1 progress
claude-code "Commit all Week 1 work:
git add .
git commit -m 'Feature: NewsAPI collector, storage module, test suite, docs'
git log --oneline -10
Show me the commit history."
```

---

## 🎬 COWORK COMMANDS

These are tasks Cowork will handle—file management, Docker, tests, automation.

### Setup (One-time)

```
Cowork Action:
1. CD to: /path/to/credit-risk-monitor
2. Copy .env.template → .env
3. Edit .env: add your API keys
4. Run: python -m venv venv
5. Activate: source venv/bin/activate
6. Install: pip install -r requirements.txt
7. Verify: python -c "import fastapi; print('✅ Dependencies OK')"
```

### Daily Checks

```
Cowork Action (run at start of day):
1. Docker up: docker-compose ps → should show postgres UP
2. Tests: pytest tests/unit -q → should show X passed
3. Articles: psql -U postgres -d credit_risk -c "SELECT COUNT(*) FROM articles;"
4. Status report → send to console
```

### Data Seeding (Day 2)

```
Cowork Action:
1. Activate venv
2. python src/db/connection.py → "✅ Database connected"
3. alembic upgrade head → "✅ Migration applied"
4. python scripts/seed_obligors.py → "✅ Seeded 50 obligors"
5. psql -c "SELECT name, ticker FROM obligors LIMIT 5;"
6. Report: X obligors in database
```

### Collection (Day 4)

```
Cowork Action:
1. Activate venv
2. Add NEWSAPI_KEY to .env (verify not empty)
3. python scripts/collect_news_all.py (limit to 10 obligors first)
4. Wait for completion
5. Check: psql -c "SELECT COUNT(*) FROM articles;" → report count
6. If successful: run for all 50 obligors
```

### Testing (Day 5)

```
Cowork Action:
1. Activate venv
2. pytest tests/unit -v → run verbose
3. pytest tests/unit --cov=src → check coverage
4. Report: X/Y tests passing, Z% coverage
5. If any failures: save output, share with Claude Code
```

### CI/CD Verification (Day 6)

```
Cowork Action:
1. Push to GitHub: git push origin main
2. Check GitHub Actions: should run automatically
3. Wait for tests to complete
4. Report: ✅ All tests passing OR ❌ Test failures
5. If failures: pull logs and share with Claude Code
```

---

## 📊 DAILY ROUTINE (Script This)

### Morning (9 AM)
```bash
#!/bin/bash
# morning_check.sh

echo "=== CREDIT RISK MONITOR - Morning Check ==="
echo ""

# Check Docker
echo "🐳 Docker Status:"
docker-compose ps

echo ""
echo "📊 Database Status:"
psql -U postgres -d credit_risk -c "SELECT COUNT(*) as article_count FROM articles;"

echo ""
echo "✅ Tests:"
cd /path/to/project
source venv/bin/activate
pytest tests/ -q --tb=no

echo ""
echo "📝 Recent commits:"
git log --oneline -5

echo ""
echo "=== Ready to work! ==="
```

### End of Day (5 PM)
```bash
#!/bin/bash
# eod_checkin.sh

echo "=== END OF DAY CHECK-IN ==="

# Run final tests
source venv/bin/activate
pytest tests/ -q

# Commit
git add .
git commit -m "Update: [describe changes]"

# Push
git push origin main

echo ""
echo "✅ Day complete. See you tomorrow!"
```

---

## 🔄 FEEDBACK LOOP

**Each task should follow this cycle:**

1. **Claude Code writes** the code (30 min)
   ```bash
   claude-code "Create [module] that does [X]"
   ```

2. **Cowork runs** tests/scripts to verify (10 min)
   ```
   Cowork: Run pytest, report results
   ```

3. **Review** output together (5 min)
   - Tests passing? ✅
   - Code quality good? ✅
   - Ready for next task? ✅

4. **Iterate** if needed (5-15 min)
   - If tests fail: Claude Code fixes
   - If performance bad: Cowork profiles
   - If logic wrong: Claude Code refactors

5. **Commit** and move on (2 min)
   ```bash
   git commit -m "Feature: [what was added]"
   ```

---

## ✅ QUALITY GATES

Before marking a task **DONE**, verify:

- [ ] Code runs without errors
- [ ] Tests passing (100% of new tests)
- [ ] Coverage maintained (>70% for core modules)
- [ ] Git committed with clear message
- [ ] Daily log updated with standup
- [ ] Next task identified

---

## 🚨 WHEN STUCK

**If something breaks:**

1. **Read the error** carefully (don't skip!)
2. **Claude Code**: Ask "What's wrong with this error: [ERROR_TEXT]"
3. **Cowork**: Provide error logs + context
4. **Iterate** until fixed

**Example:**

```
You: pytest is failing with "ModuleNotFoundError: No module named 'fastapi'"
Claude Code: "You need to install fastapi. The requirements.txt needs updating."
Cowork: pip install fastapi, pip freeze > requirements.txt
Claude Code: "Now let's verify by running the test again"
Cowork: pytest tests/unit -q → ✅ PASSED
```

---

## 📅 WEEK-BY-WEEK COMMAND PATTERN

**Week 1**: Foundation (Database, collection, tests)
**Week 2**: Processing (Cleaning, NER, entity mapping)
**Week 3**: Enrichment (Sentiment, classification, risk scoring)
**Week 4**: RAG (Embeddings, vector DB, retriever)
**Week 5**: Summarization (LLM summaries, alerts)
**Week 6**: API (FastAPI endpoints, deployment)
**Week 7**: Dashboard (Streamlit UI, charts)
**Week 8**: Finalization (Docs, deploy, demo)

Each week follows the same pattern:
1. Claude Code writes the core module
2. Cowork tests it
3. Commit when passing
4. Move to next module

---

**You're ready! Start Week 1, Day 1 tomorrow. Good luck! 🚀**
