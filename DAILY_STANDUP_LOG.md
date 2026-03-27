# ⏰ Daily Standup Log - Credit Risk Monitor

**Format**: Complete this EVERY DAY at same time (e.g., 9 AM)  
**Duration**: 15 minutes  
**Who**: You + Claude Code (reviewing)

---

## 📋 STANDUP TEMPLATE (Copy this for each day)

```
## Week X, Day Y: [DATE YYYY-MM-DD]

### ✅ COMPLETED YESTERDAY
- [Task name]: [What works now that didn't yesterday?]
- [Task name]: [Brief result/evidence]

Example:
- NewsAPI collector: ✅ Pulling 100+ articles, deduplication working
- Unit tests: ✅ 12/15 tests passing (3 failures need fixing)

### 🚧 IN PROGRESS TODAY
- [Task]: [Specific goal for today, done by EOD]
- [Task]: [Specific goal]

Example:
- NER extraction: Extract company names from 50 test articles (goal: 80% accuracy)
- Database migration: Add processed_articles table + run migration

### 🚨 BLOCKERS (if any)
- [Issue]: [What's preventing progress]
- [Impact]: [How does it slow us down]
- [Workaround]: [What we'll do to unblock]

Example:
- NewsAPI key invalid: Not pulling articles
  → Workaround: Using test data from fixtures until key is fixed

### 📊 METRICS (measurable)
- Articles in database: X
- Tests passing: X/Y (coverage: X%)
- Code commits: X
- Lines of code: X
- Bugs fixed: X

### 🎯 NEXT 24H
- [Specific, achievable goal]
- [Next step after that]

Example:
- Complete NER extraction by EOD
- Tomorrow: Start sentiment analysis module

### ⚠️ RED FLAGS (if any)
- Running behind schedule? By how much?
- Quality concerns? What needs to be redone?
- Scope creep? What are we adding that wasn't planned?

### 📝 NOTES
- Anything else to remember?
- Ideas for optimization?
- Questions for next sync?
```

---

## 📅 WEEK 1 STANDUPS

### Week 1, Day 1: [28 march 2026]

✅ COMPLETED:
- Project structure: ✅ All directories created
- venv + dependencies: ✅ Installed
- Docker PostgreSQL: ✅ Running
- Database models: ✅ 6 models defined
- Database connection: ✅ Tested and working
- Utilities: ✅ config, logger, constants
- Obligor seeding script: ✅ Ready (will run tomorrow)
- Git: ✅ Initial commit done

🚧 IN PROGRESS:
- Alembic migration: Created, will apply tomorrow

🚨 BLOCKERS:
- None

📊 METRICS:
- Files created: 15+
- Lines of code: 1200+
- Commits: 1
- Tests written: 0 (starting tomorrow)

🎯 NEXT 24H:
- Apply Alembic migration
- Seed 50 obligors
- Create NewsAPI collector module
```

And update `session-log.md`:

---

### Week 1, Day 2: [DATE]

✅ COMPLETED:
- SQLAlchemy models: ✅ All models defined (Article, Obligor, ProcessedArticle, etc.)
- Alembic: ✅ First migration created and applied successfully
- Database: ✅ Tables created in PostgreSQL

🚧 IN PROGRESS TODAY:
- Obligor seed script: Create list of 50 companies + insert into DB
- Utils modules: config.py, logger.py, constants.py

🚨 BLOCKERS:
- None

📊 METRICS:
- Articles in DB: 0
- Obligors in DB: (pending, will be 50 by EOD)
- Tests passing: 0/0
- Commits: 2

🎯 NEXT 24H:
- Seed 50 obligors by EOD
- Tomorrow: Start NewsAPI collector

---

### Week 1, Day 3: [DATE]

✅ COMPLETED:
- Obligor seeding: ✅ 50 companies inserted into database
- Utility modules: ✅ config.py, logger.py, constants.py all working
- Config loading: ✅ .env template created, settings singleton working

🚧 IN PROGRESS TODAY:
- NewsAPI collector: Implement fetch_news() function
- Storage module: Implement store_articles() with deduplication

🚨 BLOCKERS:
- API key not tested yet (waiting to start actual collection)

📊 METRICS:
- Articles in DB: 0
- Obligors in DB: 50 ✅
- Tests passing: 0/0
- Commits: 3

🎯 NEXT 24H:
- Test NewsAPI collector with 1 company by EOD
- Tomorrow: Run full collection for all 50 companies

---

### Week 1, Day 4: [DATE]

✅ COMPLETED:
- NewsAPI collector: ✅ Fetching articles successfully
- Storage module: ✅ Articles inserting with deduplication
- Test collection: ✅ Pulled ~50 articles for Apple, zero duplicates on re-run

🚧 IN PROGRESS TODAY:
- Run full collection: Collect for all 50 obligors
- Create collection script with progress tracking

🚨 BLOCKERS:
- NewsAPI rate limit at 100/day (might hit limit on 50 companies)
  → Workaround: Spread requests over time, add delays

📊 METRICS:
- Articles in DB: 100+ ✅
- Obligors in DB: 50
- Tests passing: 0/0 (still no tests)
- Commits: 4

🎯 NEXT 24H:
- Finish collecting all 50 obligors by EOD
- Tomorrow: Start test suite

---

### Week 1, Day 5: [DATE]

✅ COMPLETED:
- Full collection: ✅ 50 obligors processed, ~500 articles collected
- Collection script: ✅ Progress tracking + logging working
- Rate limiting: ✅ Delays between requests prevent hitting API limit

🚧 IN PROGRESS TODAY:
- Test fixtures: Create conftest.py with test_db, test_obligor, etc.
- Unit tests: Write tests for storage module (test_store_single, test_dedup, etc.)

🚨 BLOCKERS:
- None

📊 METRICS:
- Articles in DB: 500 ✅
- Obligors in DB: 50
- Tests passing: 0/0 (will start writing today)
- Commits: 5

🎯 NEXT 24H:
- Write 10+ unit tests by EOD
- Tomorrow: Run pytest, verify coverage >70%

---

### Week 1, Day 6: [DATE]

✅ COMPLETED:
- Test fixtures: ✅ conftest.py with all fixtures defined
- Unit tests: ✅ 12 tests written for storage + models
- Test data: ✅ Factories created (article_factory, obligor_factory)

🚧 IN PROGRESS TODAY:
- Run pytest: Execute all tests, fix failures
- Calculate coverage: Target >70%

🚨 BLOCKERS:
- 3 tests failing (fixture issues, will debug)
  → Plan: Use pytest -v to see errors, fix one by one

📊 METRICS:
- Articles in DB: 500
- Tests passing: 12/12 (after fixes)
- Coverage: 72% (target achieved!)
- Commits: 6

🎯 NEXT 24H:
- Fix remaining test failures by EOD
- Tomorrow: GitHub Actions + README

---

### Week 1, Day 7: [DATE]

✅ COMPLETED:
- All tests passing: ✅ 15/15 green
- GitHub Actions: ✅ Workflow created, tests run on every push
- README: ✅ Project overview + quick start guide
- Week 1 complete: ✅ Foundation solid

🚧 IN PROGRESS TODAY:
- Final polish: Update README with metrics
- Week 1 summary in this log

🚨 BLOCKERS:
- None, Week 1 complete!

📊 METRICS:
- Articles in DB: 500+ ✅
- Obligors in DB: 50 ✅
- Tests passing: 15/15 ✅
- Coverage: 72% ✅
- Commits: 7
- Code lines: 2000+

🎯 WEEK 2 STARTS:
- NER extraction
- Text cleaning
- Entity mapping

---

## 🎯 KEY REMINDERS

**Before standup:**
- [ ] Run tests: `pytest tests/unit -v`
- [ ] Check coverage: `pytest --cov=src`
- [ ] Count articles: `psql -U postgres -d credit_risk -c "SELECT COUNT(*) FROM articles;"`
- [ ] Review yesterday's blockers

**During standup:**
- [ ] Be honest about progress (did we actually do it?)
- [ ] Note any surprises (good or bad)
- [ ] Quantify (use numbers, not "it's working")
- [ ] Identify one blocker if any

**After standup:**
- [ ] Commit any progress: `git add . && git commit -m "Update: [what changed]"`
- [ ] Update this log
- [ ] Plan tomorrow's work

---

## 📊 WEEKLY SUMMARY TEMPLATE

```markdown
## WEEK X SUMMARY (Days 1-7)

### ✅ COMPLETED
- Feature 1
- Feature 2
- Feature 3

### 🔢 METRICS
- Articles: X
- Tests: X/Y passing
- Coverage: X%
- Commits: X
- Time spent: X hours

### 🚨 BLOCKERS ENCOUNTERED
- Blocker 1 → Resolved by [solution]
- Blocker 2 → Resolved by [solution]

### 📚 LESSONS LEARNED
- Lesson 1: [What went wrong + how to prevent]
- Lesson 2: [What went well + repeat it]

### 🎯 WEEK X+1 GOALS
- [Goal 1]
- [Goal 2]
```

---

**Start with Week 1, Day 1 tomorrow! 🚀**
