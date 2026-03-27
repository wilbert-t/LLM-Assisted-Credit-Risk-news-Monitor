# 📚 Credit Risk Monitor - Master Guide & Index

**Welcome!** This is your reference guide for the 8-week project. Bookmark this file.

---

## 🗂️ YOUR PROJECT FILES (In Order of Importance)

| File | Purpose | When to Read |
|------|---------|--------------|
| **START_TODAY.md** | Your first day checklist | 🔴 **RIGHT NOW** |
| **STARTUP_PLAN_WEEK1-8.md** | Complete 8-week breakdown (56 days of tasks) | Every Sunday before week starts |
| **CLAUDE_CODE_WORKFLOW.md** | How to use Claude Code + Cowork together | Daily, reference as needed |
| **DAILY_STANDUP_LOG.md** | Your daily check-in template | Daily, 9 AM |
| **claude.md** | Project philosophy + rules | Once at start, then reference |
| **QUICK_START.md** | Setup guide (detailed) | Week 1 |
| **IMPLEMENTATION_ROADMAP.md** | Detailed task breakdown | Reference by week |
| **WORKFLOW_BEST_PRACTICES.md** | How to work effectively | Read once, apply daily |

---

## ⚡ QUICK COMMAND REFERENCE

### Before Any Work Session
```bash
# 1. Navigate to project
cd ~/projects/credit-risk-monitor

# 2. Activate venv
source venv/bin/activate

# 3. Verify Docker is running
docker-compose ps

# 4. Check git status
git status
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# Only unit tests
pytest tests/unit -v

# With coverage
pytest tests/ --cov=src

# Quick check (quiet)
pytest tests/ -q
```

### Running Scripts
```bash
# Database connection test
python src/db/connection.py

# Seed obligors
python scripts/seed_obligors.py

# Collect news
python scripts/collect_news_all.py

# Process articles
python scripts/process_articles.py
```

### Git Workflow
```bash
# Check what changed
git status
git diff src/

# Stage and commit
git add .
git commit -m "Feature: [description]"

# Push to GitHub
git push origin main

# View history
git log --oneline -10
```

### Docker
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Check status
docker-compose ps

# View logs
docker-compose logs postgres
```

---

## 📅 WEEK-BY-WEEK OVERVIEW

### Week 1: Foundation (Environment + Collection)
- Days 1-7: Bootstrap project, collect 500+ articles, write tests
- **Deliverable**: NewsAPI collector working + 50 obligors seeded
- **Time**: 15-20 hours
- **Key file**: `STARTUP_PLAN_WEEK1-8.md` → "WEEK 1" section

### Week 2: Processing (Cleaning + NER)
- Days 8-14: Clean text, extract company names, map to obligors
- **Deliverable**: 500+ processed articles with entities
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 2" section

### Week 3: Enrichment (Sentiment + Classification)
- Days 15-21: Score sentiment, classify credit relevance, detect events
- **Deliverable**: All articles scored + classified
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 3" section

### Week 4: RAG (Embeddings + Vector Search)
- Days 22-28: Generate embeddings, set up vector DB, build retriever
- **Deliverable**: Working RAG system for article retrieval
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 4" section

### Week 5: Alerts (Summaries + Rules)
- Days 29-35: LLM summaries, alert rules, scheduled jobs
- **Deliverable**: Alerts generating automatically every 6 hours
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 5" section

### Week 6: API (FastAPI Backend)
- Days 36-42: Create 10+ API endpoints, authentication, deployment config
- **Deliverable**: Working REST API with full documentation
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 6" section

### Week 7: Dashboard (Streamlit UI)
- Days 43-49: Interactive portfolio view, charts, drill-downs, filters
- **Deliverable**: Beautiful, functional dashboard
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 7" section

### Week 8: Finalization (Docs + Deploy)
- Days 50-56: Documentation, Docker setup, live deployment, demo
- **Deliverable**: Fully deployed, production-ready project
- **Time**: 15-20 hours
- **Key file**: Same, "WEEK 8" section

**Total**: ~120 hours (10-15 hours/week ≈ 2-3 hours/day)

---

## 🎯 YOUR DAILY ROUTINE

### 9:00 AM - Start of Day (15 min)
```
1. Read DAILY_STANDUP_LOG.md (yesterday's entry)
2. Check docker-compose ps (database running?)
3. Read STARTUP_PLAN_WEEK1-8.md (what's today's task?)
4. Update LOG with "🚧 IN PROGRESS" for today
```

### 9:15 AM - 12:30 PM - Work Session 1 (3+ hours)
```
1. Claude Code: Write code for today's task (~90 min)
2. Cowork: Run tests/scripts to verify (~30 min)
3. Iterate: Fix any issues (~30 min)
4. Commit: git add . && git commit -m "..." (~5 min)
```

### 12:30 PM - Lunch (30 min)

### 1:00 PM - 4:30 PM - Work Session 2 (3+ hours)
```
Same pattern as Session 1, or start next task
```

### 5:00 PM - End of Day (15 min)
```
1. Run pytest tests/ -q (everything passing?)
2. Update DAILY_STANDUP_LOG.md with "✅ COMPLETED"
3. Update session-log.md (next step, blockers)
4. git push origin main (backup to GitHub)
5. docker-compose down (optional, save resources)
```

---

## 🤖 HOW CLAUDE CODE + COWORK WORK

### Claude Code (You interact with)
- **What it does**: Writes code, creates files, edits existing code
- **How to use**: 
  ```bash
  claude-code "Create [module] that does [X] with [requirements]"
  ```
- **What to expect**: Code appears in your IDE, ready to review

### Cowork (Runs in background)
- **What it does**: Runs scripts, tests, docker commands, file management
- **How to use**: 
  ```
  Cowork Action:
  1. Run: python scripts/collect_news.py
  2. Check: psql -c "SELECT COUNT(*) FROM articles;"
  3. Report: [results]
  ```
- **What to expect**: Output in console, confirmation that task completed

### Feedback Loop
```
Claude Code writes
        ↓
You review code
        ↓
Cowork tests it
        ↓
See if passing
        ↓
Claude Code fixes if needed
        ↓
Commit when done
```

---

## 📊 SUCCESS METRICS

Track these numbers every week:

| Metric | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 | Week 6 | Week 7 | Week 8 |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| Articles | 500+ | 500+ | 500+ | 500+ | 500+ | 500+ | 500+ | 1000+ |
| Tests | 15+ | 20+ | 25+ | 30+ | 35+ | 40+ | 40+ | 40+ |
| Coverage | 70%+ | 70%+ | 72%+ | 75%+ | 75%+ | 80%+ | 80%+ | 80%+ |
| Commits | 5+ | 7+ | 7+ | 7+ | 7+ | 7+ | 5+ | 5+ |
| Features | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 2 |

---

## 🚨 COMMON BLOCKERS & SOLUTIONS

### "psycopg2 won't install"
```bash
# This is a C extension, sometimes finicky
pip install psycopg2-binary  # Use binary version instead
# Or: brew install libpq (Mac), apt-get install libpq-dev (Linux)
```

### "Database connection fails"
```bash
# Check Docker is running
docker-compose ps

# If not:
docker-compose up -d

# If still fails, reset everything:
docker-compose down
docker-compose up -d
```

### "Tests failing on my machine but Cowork says they pass"
```bash
# Different Python versions? Check:
python --version  # Should be 3.11+

# Different database state? Reset:
docker-compose down -v  # Remove volumes
docker-compose up -d
```

### "Out of memory generating embeddings"
```bash
# Reduce batch size in .env:
BATCH_SIZE=25  # Instead of 50

# Or process fewer articles at once:
python scripts/generate_embeddings.py --limit 100
```

### "API rate limits hit"
```bash
# Add delays in collector:
time.sleep(2)  # Wait 2 seconds between requests

# Or use backup API:
# GDELT is free and unlimited (but lower quality)
```

---

## 📚 REFERENCE DOCS

### Official Docs
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Streamlit](https://docs.streamlit.io/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Alembic](https://alembic.sqlalchemy.org/)

### Libraries
- [spaCy](https://spacy.io/) - NER
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/) - FinBERT
- [Anthropic](https://docs.anthropic.com/) - Claude API
- [Sentence Transformers](https://www.sbert.net/) - Embeddings

### APIs
- [NewsAPI](https://newsapi.org/) - News collection
- [GDELT](https://www.gdeltproject.org/) - News monitoring (free)

---

## 🎓 LEARNING PATH

If you're new to these concepts:

**Week 1-2**: Focus on database fundamentals
- [ ] Watch: "Databases for beginners" (YouTube, 30 min)
- [ ] Read: SQLAlchemy ORM basics
- [ ] Practice: Write simple queries

**Week 3**: Focus on NLP basics
- [ ] Watch: "NLP pipeline overview" (20 min)
- [ ] Read: spaCy NER tutorial
- [ ] Practice: Extract entities from sample text

**Week 4**: Focus on embeddings/RAG
- [ ] Watch: "Vector embeddings explained" (15 min)
- [ ] Read: Semantic search basics
- [ ] Practice: Embed and retrieve text

**Week 5**: Focus on LLMs
- [ ] Read: Claude prompting guide
- [ ] Watch: "RAG systems" (20 min)
- [ ] Practice: Write prompts, iterate

**Week 6-7**: Focus on APIs + UIs
- [ ] Read: FastAPI tutorial (30 min)
- [ ] Read: Streamlit tutorial (30 min)
- [ ] Build: Simple CRUD app

**Week 8**: Polish and deployment
- [ ] Read: Docker basics
- [ ] Practice: Deploy locally, then cloud

---

## 💡 PRO TIPS

### Code Quality
- **Comment complex logic**: Future you will thank present you
- **Use type hints**: Makes debugging 100x easier
- **Write tests early**: Not after, during development
- **Keep functions small**: <50 lines is good, <30 is better

### Git Habits
- **Commit frequently**: Every working feature, not at end of day
- **Write clear messages**: "Add sentiment analysis" not "update stuff"
- **Push to GitHub**: Backup + easy to review

### Performance
- **Profile before optimizing**: Use `time.time()` to measure
- **Batch process**: 50 items at a time, not 1 at a time
- **Cache results**: Don't re-compute same thing twice

### Debugging
- **Read the error**: 90% of time, the error message tells you what's wrong
- **Check assumptions**: "Database is running?" "API key is correct?"
- **Isolate the problem**: Test one thing at a time, not everything

---

## 🎯 FINAL CHECKLIST (At End of Week 8)

- [ ] 1000+ articles collected
- [ ] 50 companies monitored
- [ ] 100+ alerts generated
- [ ] API with 10+ endpoints
- [ ] Dashboard with 3+ pages
- [ ] Tests passing (>70% coverage)
- [ ] README complete + professional
- [ ] Deployed (or ready to deploy)
- [ ] Demo video created
- [ ] All code on GitHub
- [ ] Committed 40+ times
- [ ] Zero hardcoded secrets
- [ ] Zero warnings/errors in logs

---

## 🚀 YOU'VE GOT THIS!

**Next step**: Open `START_TODAY.md` and begin. Good luck! 💪

---

**Questions?**
- Check the relevant week in `STARTUP_PLAN_WEEK1-8.md`
- Search in `CLAUDE_CODE_WORKFLOW.md` for command help
- Review `WORKFLOW_BEST_PRACTICES.md` for methodology

**Stuck?** Update `DAILY_STANDUP_LOG.md` with the blocker, then ask Claude Code for help with specifics.

---

**Let's build something amazing in 8 weeks!** 🎉
