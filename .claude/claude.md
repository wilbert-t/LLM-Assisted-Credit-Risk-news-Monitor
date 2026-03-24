# Credit Risk Monitoring System - Claude Code Configuration

## Project Overview
Automated credit risk monitoring system using NLP/LLM to analyze financial news and generate alerts for portfolio managers.

**Problem**: Banks monitor thousands of obligors. Manual news scanning doesn't scale.  
**Solution**: Automated pipeline: News Collection → NLP Analysis → RAG Summarization → Alerts → Dashboard

## Quick Architecture
```
News APIs/Scrapers → PostgreSQL + Text Processing → Risk Analysis (FinBERT, NER, Classification)
→ Vector DB + RAG → Alerts → FastAPI + Streamlit Dashboard
```

## Tech Stack (Condensed)
**Data**: NewsAPI, GDELT, BeautifulSoup, Airflow/Prefect  
**Storage**: PostgreSQL, Qdrant/pgvector  
**NLP/ML**: FinBERT, spaCy, transformers, OpenAI/Anthropic LLMs, LangChain  
**Backend**: FastAPI, SQLAlchemy  
**Frontend**: Streamlit, Plotly  
**Deploy**: Docker, Render/Railway

## Project Structure
```
credit-risk-monitor/
├── .claude/claude.md          # This file
├── src/
│   ├── collectors/            # News collection
│   ├── processors/            # Text cleaning, NER
│   ├── models/                # Sentiment, classification, embeddings
│   ├── rag/                   # Vector store, retrieval, summarization
│   ├── alerts/                # Alert generation
│   ├── api/                   # FastAPI backend
│   └── db/                    # Database models
├── dashboard/                 # Streamlit app
├── data/                      # Raw/processed data
├── notebooks/                 # Jupyter exploration
├── tests/                     # Unit & integration tests
├── scripts/                   # Seed data, collectors
└── tasks/lessons.md          # Self-improvement tracking
```

## Database Schema (Key Tables)
```sql
articles: id, title, content, url, source, published_at, fetched_at
obligors: id, name, ticker, lei, sector, country
processed_articles: id, article_id, cleaned_text, entities, sentiment_score, is_credit_relevant
alerts: id, obligor_id, timestamp, severity, summary, event_types, metadata
embeddings: id, article_id, chunk_text, embedding (vector)
```

## Development Phases (8 Weeks)
**Week 1-2**: Data collection (NewsAPI, database setup)  
**Week 3**: Text processing (cleaning, NER, entity mapping)  
**Week 4**: Sentiment analysis (FinBERT) + credit-relevance classification  
**Week 5**: RAG system (embeddings, vector DB, LLM summarization)  
**Week 6**: Alert system (rules, thresholds, FastAPI)  
**Week 7**: Dashboard (Streamlit, visualizations)  
**Week 8**: Deploy & document (Docker, README, demo)

## Environment Variables
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/credit_risk
NEWSAPI_KEY=your_key
OPENAI_API_KEY=your_key
QDRANT_URL=http://localhost:6333
```

---

# 🚀 CRITICAL WORKFLOW PATTERNS (MUST FOLLOW)

These patterns are REQUIRED for professional development. Follow them strictly.

---

## 1. Plan Mode Default ⚡ (REQUIRED)

### When to Enter Plan Mode
Enter plan mode for **ANY task with 3+ steps** or architectural decisions.

**Examples that REQUIRE plan mode:**
- "Implement sentiment analysis pipeline"
- "Debug alert system not generating alerts"
- "Refactor database queries for performance"
- "Add new data source to collectors"

**Examples that DON'T need plan mode:**
- Fix typo in code
- Update README
- Change config value

### Plan Mode Protocol

```
STEP 1: Break down into specific, measurable steps
STEP 2: Identify blockers/edge cases upfront  
STEP 3: Define success criteria for EACH step
STEP 4: Execute step-by-step WITH verification
STEP 5: If ANYTHING fails → STOP, re-assess, create NEW plan
```

### Example: Implementing FinBERT Sentiment Analysis

**GOOD Plan:**
```
Plan: Implement FinBERT Sentiment Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Steps:
1. Research FinBERT model on Hugging Face
   → Find model ID: ProsusAI/finbert
   → Verify: Check model card, confirm it's for financial text
   
2. Create src/models/sentiment.py
   → Implement SentimentAnalyzer class
   → Add __init__ to load model once
   
3. Write predict() method
   → Input: article text (string)
   → Output: {positive: float, negative: float, neutral: float}
   → Handle: Articles >512 tokens (truncate or chunk)
   
4. Add batch processing for efficiency
   → Process 50 articles at once
   → Add progress tracking
   
5. Create unit test
   → Test positive article: "Company reports record profits"
   → Test negative article: "Company faces bankruptcy"
   → Verify scores make sense
   
6. Test on 10 real articles from database
   → Manually verify sentiment looks correct
   → Check processing time (<10 seconds for 10 articles)
   
7. Integrate with database
   → Update processed_articles table
   → Verify schema matches

Blockers:
- Model download might take 15 min first time → Run ahead of time
- May need GPU for speed → Test on CPU first, optimize if slow
- Memory issues with large batches → Start with batch_size=10

Success Criteria:
✓ Can classify sentiment on test articles
✓ Batch processing 100 articles < 1 minute  
✓ >75% agreement with manual labels on 20-article test set
✓ Results save to database correctly
```

**BAD Plan (Too Vague):**
```
Plan: Add sentiment analysis
1. Install transformers
2. Write code
3. Test it
4. Done
```

### If Something Goes Wrong

**IMMEDIATELY STOP AND RE-PLAN:**
```
Original Plan: Fetch news for 100 companies
Step 3: Running collector...
ERROR: Rate limit exceeded after 50 companies

❌ DON'T: Keep trying different things randomly
✅ DO: STOP. Re-plan:
  - Research: NewsAPI limit is 100 requests/day
  - New plan: Split into 2 batches OR reduce lookback from 7 to 3 days
  - Verify: Test new approach with 5 companies first
```

---

## 2. Self-Improvement Loop 📚 (REQUIRED)

**Purpose**: Never repeat the same mistake twice.

### After ANY Correction from User

**IMMEDIATELY update `tasks/lessons.md`:**

```markdown
## Lesson: [YYYY-MM-DD] - [Short Title]

**What went wrong**: 
[Specific error or issue - be brutally honest]

**Root cause**: 
[WHY it happened - dig deep, not just surface]

**Prevention rule**: 
[Concrete rule to follow in future - make it actionable]

**Verification step**: 
[How to verify this won't happen again]

**Related files**: 
[Which files/code this applies to]
```

### Real Example

```markdown
## Lesson: 2024-03-15 - Database Connection Failed

**What went wrong**: 
Script crashed with "sqlalchemy.exc.OperationalError: could not connect to server"

**Root cause**: 
I forgot to start Docker Desktop. Database container wasn't running.
This happened because I opened a new terminal and jumped straight to coding.

**Prevention rule**: 
BEFORE running ANY script that uses database:
1. Run: docker-compose ps
2. If not "Up" → Run: docker-compose up -d
3. Wait 5 seconds for database to initialize
4. THEN run script

**Verification step**: 
Added try-catch to src/db/connection.py with helpful error:
"Database connection failed. Did you start Docker? Run: docker-compose up -d"

**Related files**: 
All scripts using database: src/db/*, scripts/*
```

### Review Lessons at Session Start

**Every work session:**
```bash
# 1. Navigate to project
cd ~/projects/credit-risk-monitor

# 2. Read lessons
cat tasks/lessons.md | tail -50  # Last 50 lines

# 3. Apply relevant lessons to today's task
"Today: Implement NER"
Check lessons: Any about imports? Testing? Database?
```

### Ruthlessly Iterate

**Track your improvement:**
```
Week 1: 8 mistakes (baseline)
Week 2: 5 mistakes (-37% ✓)
Week 3: 3 mistakes (-62% ✓✓)
Week 4: 1 mistake (-87% 🎉)

Goal: <2 mistakes per week by Week 4
```

### Common Mistakes to Document

**Environment:**
- Forgot to activate venv
- Docker not running
- Wrong directory

**Code:**
- Missing imports (forgot pip install)
- Hardcoded secrets (should use .env)
- Didn't test on small sample first

**Process:**
- Skipped verification
- Marked task "done" without testing
- Didn't read error message fully

---

## 3. Verification Before "Done" ✅ (REQUIRED)

**Never mark a task complete without PROVING it works.**

### The Staff Engineer Standard

Before saying "done", ask:

**"Would a staff engineer at Google/Meta approve this in code review?"**

If uncertain → NOT DONE YET.

### Verification Checklist (ALL REQUIRED)

```
LEVEL 1: IT RUNS
□ Code executes without errors
□ No warnings in console
□ Completes in reasonable time (<1 min for dev tasks)

LEVEL 2: IT WORKS CORRECTLY  
□ Produces expected output
□ Handles edge cases (empty input, wrong type, None)
□ Data in database looks correct (spot check 5-10 rows)
□ Logs show expected behavior

LEVEL 3: IT'S PRODUCTION-READY
□ Has error handling (try-except with helpful messages)
□ Has documentation (docstrings)
□ Follows project conventions (naming, structure)
□ Would be easy for someone else to understand
□ Has tests (or manual test procedure documented)
```

### Evidence Required

**For every completed task, provide:**

1. **Command you ran**
2. **Output received**  
3. **Database verification** (if applicable)
4. **Edge case tests**
5. **Performance check**

### Example: Proper Verification

**Task**: Implement news collector

**INSUFFICIENT:**
```
❌ "I wrote the collector. It should work."
Status: NOT DONE
```

**PROPER:**
```
✅ VERIFICATION EVIDENCE:

1. Code Execution:
   Command: python src/collectors/news_api.py
   Output: "Fetched 47 articles for Apple Inc."
   Time: 12 seconds
   Errors: None

2. Database Verification:
   Query: SELECT COUNT(*) FROM articles;
   Result: 47 rows
   
   Query: SELECT title, url FROM articles LIMIT 3;
   Sample:
   - "Apple announces new iPhone" | https://...
   - "Apple Q3 earnings beat..." | https://...
   - "AAPL stock rises 3%" | https://...
   
   ✓ All have title, content, url populated
   ✓ published_at timestamps look correct

3. Edge Cases Tested:
   ✓ Empty company name → ValueError with message "Company name required"
   ✓ Invalid API key → Returns clear error "Check NEWSAPI_KEY in .env"
   ✓ Network timeout → Retries 3 times, then fails gracefully
   ✓ Duplicate articles → Deduplication works (re-run added 0 new rows)

4. Performance:
   ✓ 50 articles in 15 seconds = ~3 articles/second
   ✓ Memory usage: 150MB (acceptable)

5. Code Quality:
   ✓ Has docstring explaining usage
   ✓ Error messages are helpful
   ✓ Follows project naming (snake_case)
   ✓ Imports organized alphabetically

Status: COMPLETE ✅
```

### Before/After Comparison

**Always show measurable improvement:**

```
Task: Optimize database query

BEFORE:
- Query time: 5.2 seconds
- Returned: 1,247 rows
- Memory: 800MB

AFTER:
- Query time: 0.8 seconds (6.5x faster ✓)
- Returned: 1,247 rows (same results ✓)  
- Memory: 200MB (4x improvement ✓)

Changes Made:
- Added index on published_at column
- Used SELECT only needed columns (not SELECT *)
- Added LIMIT clause for pagination

Verification:
- Ran EXPLAIN ANALYZE → Confirms index is used
- Spot-checked 20 rows → Results identical to before
- Load tested with 10,000 articles → Consistent performance
```

### Test Coverage

**Minimum tests required:**

```python
def test_sentiment_analyzer():
    """Test sentiment analysis works correctly."""
    analyzer = FinBERTSentiment()
    
    # Test positive sentiment
    result = analyzer.predict("Company reports record profits")
    assert result['positive'] > 0.7, "Should detect positive sentiment"
    
    # Test negative sentiment  
    result = analyzer.predict("Company faces bankruptcy filing")
    assert result['negative'] > 0.7, "Should detect negative sentiment"
    
    # Test edge case: empty string
    with pytest.raises(ValueError):
        analyzer.predict("")
    
    print("✅ All sentiment tests passed")
```

---

## 4. Demand Elegance (Balanced) 💎 (REQUIRED)

**For non-trivial changes, pause and ask: "Is there a more elegant way?"**

### When to Refactor

**Refactor if code is:**
- Hard to understand (needs comments to explain basic logic)
- Repetitive (same pattern copy-pasted 3+ times)
- Fragile (small changes break it)
- Nested deeply (>3 levels of indentation)
- >100 lines in one function

**Don't refactor if:**
- It's a simple fix (<10 lines changed)
- It's prototype/exploratory code
- It's a one-time script
- You're debugging urgent issue

### The Two-Pass Approach

**First Pass**: Get it working (quick & dirty is OK)  
**Second Pass**: Make it elegant (if non-trivial)

### Example: Text Cleaning

**First Pass (Works but Messy):**
```python
def clean_text(text):
    text = text.replace("<p>", "")
    text = text.replace("</p>", "")
    text = text.replace("<div>", "")
    text = text.replace("</div>", "")
    text = text.replace("<br>", "")
    text = text.replace("<span>", "")
    text = text.replace("</span>", "")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&quot;", '"')
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    # ... 10 more lines
    return text.strip()
```

**Pause: "Is there a better way?"**

**Second Pass (Elegant):**
```python
from bs4 import BeautifulSoup
import html

def clean_text(html_text):
    """Remove HTML tags and decode entities.
    
    Args:
        html_text: Raw HTML string
        
    Returns:
        Clean text with HTML removed and whitespace normalized
    """
    # Remove all HTML tags
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()
    
    # Decode HTML entities (&nbsp; → space, etc.)
    text = html.unescape(text)
    
    # Normalize whitespace
    return ' '.join(text.split())
```

**Why better?**
- Uses existing library (handles ALL tags, not just ones we listed)
- 7 lines vs 20+ lines
- More maintainable
- Handles edge cases we didn't think of

### Balance Rule

**For this student project, prioritize:**

1. **Working** (must have) - Does it run?
2. **Readable** (must have) - Can you understand it next week?  
3. **Elegant** (nice to have) - Is it the "best" way?

**Don't over-engineer simple things:**
```python
# Simple task: Get current timestamp
# ❌ Don't do this:
import pytz
from datetime import datetime
now = datetime.now(pytz.timezone('UTC')).isoformat()

# ✓ Do this:
from datetime import datetime
now = datetime.utcnow()
```

### "Knowing Everything I Know Now"

**If a fix feels hacky, ask:**

_"Knowing everything I know now about this problem, what's the elegant solution?"_

Then implement that instead.

---

## 5. Autonomous Bug Fixing 🔧 (REQUIRED)

**When given a bug report, just fix it. No hand-holding needed.**

### How to Handle Bug Reports

**User reports bug → You should:**

1. **Diagnose immediately** (read error, check logs, find root cause)
2. **Point at the issue** (file, line number, why it's happening)
3. **Provide fix** (exact commands or code changes)
4. **Verify it works** (test the fix)
5. **Prevent recurrence** (add to tasks/lessons.md)

### Example: Autonomous Fix

**User Reports:**
```
"Getting ImportError when running sentiment analysis"
```

**BAD Response:**
```
❌ "Did you install transformers?"
❌ "What does the error say?"
❌ "Check if your venv is activated"
```

**GOOD Response:**
```
✅ I see the issue. Let me fix this:

ROOT CAUSE:
Line 3 in src/models/sentiment.py imports transformers:
  from transformers import AutoTokenizer

But transformers is not installed in your virtual environment.

DIAGNOSIS:
1. ✓ Checked requirements.txt → transformers NOT listed
2. ✗ Checked venv packages → pip list shows no transformers  
3. ✓ Confirmed venv is active → (venv) visible in prompt

FIX:
Run these commands:
  pip install transformers torch
  pip freeze > requirements.txt

VERIFICATION:
Test the import:
  python -c "from transformers import AutoTokenizer; print('✅ Works')"

PREVENTION:
Added to tasks/lessons.md:
- Prevention rule: After adding ANY new import, immediately run pip install
- Updated requirements.txt with all dependencies

Try running your script now. It should work.

If you get another error, paste it and I'll fix it.
```

### Zero Context Switching

**User should be able to:**
1. Report bug: "X is broken"
2. Go make coffee ☕
3. Come back
4. See it's fixed with explanation

**You should NOT ask:**
- "What error did you get?"
- "What version are you using?"
- "Did you try restarting?"

**Instead, proactively:**
- Check logs yourself
- Identify the issue
- Fix it
- Verify it works

### Types of Bugs to Fix Autonomously

**Environment Issues:**
```
Error: "No module named X"
→ Check if installed
→ Check venv active
→ Install if missing
→ Update requirements.txt
```

**Database Issues:**
```
Error: "Could not connect"
→ Check Docker running
→ Check DATABASE_URL correct
→ Provide fix commands
→ Add healthcheck to code
```

**Logic Errors:**
```
Error: "List index out of range"
→ Find the line
→ Identify why (empty list? wrong index?)
→ Fix with bounds check
→ Add test for edge case
```

### Failing Tests/CI

**User:** "pytest is failing"

**You should:**
```
1. Run: pytest -v
2. Read failure message
3. Identify issue (wrong import, missing fixture, wrong assertion)
4. Fix the code
5. Verify: pytest passes
6. Commit fix with message: "Fix: [what was wrong]"

Don't wait for user to investigate - just fix it.
```

---

## Implementation Guidelines

### Task Execution Flow

```
User Request
    ↓
[3+ steps?] ──YES──→ Enter PLAN MODE
    │                    ↓
    NO              Create detailed plan
    ↓                    ↓
Simple task         Execute step-by-step
    ↓                    ↓
Execute             Verify each step
    ↓                    ↓
Verify          [Something wrong?] ──YES──→ STOP & Re-plan
    ↓                    │
Update lessons          NO
    ↓                    ↓
   DONE             All steps done
                         ↓
                    Final verification
                         ↓
                    Update lessons
                         ↓
                        DONE
```

### Code Quality Standards

**Every code change must have:**

1. **Purpose**: Why is this needed? (link to requirement)
2. **Implementation**: What does it do? (docstring)
3. **Testing**: How do we know it works? (tests or manual verification)
4. **Documentation**: How do others use it? (examples)

**Minimum documentation:**
```python
def collect_news(company_name: str, days: int = 7) -> List[Article]:
    """
    Collect recent news articles for a company.
    
    Args:
        company_name: Company name to search for (e.g., "Apple Inc.")
        days: Number of days to look back (default: 7)
    
    Returns:
        List of Article objects with title, content, URL, published_at
    
    Raises:
        APIError: If NewsAPI returns non-200 response
        ValueError: If company_name is empty or None
    
    Example:
        articles = collect_news("Apple Inc.", days=14)
        print(f"Found {len(articles)} articles")
    """
    if not company_name:
        raise ValueError("Company name cannot be empty")
    # Implementation...
```

### Progress Tracking Format

```markdown
## [Date] Task: [Task Name]

**Status**: In Progress / Complete / Blocked

**What Was Done**:
- ✅ Step 1: Created database models  
- ✅ Step 2: Wrote connection logic
- ⏳ Step 3: Testing with sample data (in progress)
- ❌ Step 4: Blocked on API key

**Verification**:
[Evidence that it works - paste commands + output]

**Next Steps**:
1. Get NewsAPI key from .env
2. Test collector with 5 companies
3. Verify data in database

**Blockers**:
- Need to fix DATABASE_URL format in .env

**Lessons Learned**:
- Always check .env file exists before running
- Use .env.example as template
```

---

## Quick Reference

### Before Starting ANY Task
- [ ] Is this 3+ steps? → Enter plan mode
- [ ] Virtual environment activated?
- [ ] Database running? (docker-compose ps)
- [ ] Read relevant lessons from tasks/lessons.md?

### During Task
- [ ] Testing on small sample first? (10 items, not 10,000)
- [ ] Verifying each step works before moving on?
- [ ] Stopping and re-planning if stuck?

### After Completing Task  
- [ ] Proved it works? (ran commands, have output)
- [ ] Handles edge cases?
- [ ] Added documentation?
- [ ] Updated tasks/lessons.md if learned something?
- [ ] Committed with clear message?

### If You Made a Mistake
1. Fix it
2. Document in tasks/lessons.md (root cause + prevention)
3. Create verification step to prevent recurrence

---

## Project-Specific Notes

### LLM Best Practices
- Keep temperature low for classification (0.1-0.3)
- Request structured output (JSON) with schema
- Add few-shot examples in prompts
- Implement retry logic with exponential backoff
- Cache responses when possible
- Monitor token usage and costs

### RAG Optimization  
- Chunk text at 500-800 tokens for finance domain
- Use hybrid search (semantic + keyword) when possible
- Include metadata in embeddings (date, source, obligor)
- Rerank retrieved chunks before sending to LLM
- Refresh embeddings periodically

### Common Pitfalls to Avoid
- Testing on full dataset without trying small sample first
- Not checking API rate limits before bulk operations
- Forgetting to activate venv before running scripts
- Hardcoding secrets instead of using .env
- Marking task "done" without verification
- Not reading error messages completely

---

**Remember**: Focus on getting a working end-to-end pipeline first, then iterate on quality. A simple but complete system is better than a complex but half-finished one.

For questions about implementation, architecture, or debugging, ask Claude Code - this configuration provides full context.