# Workflow Best Practices Guide

This guide explains how to use the workflow orchestration patterns integrated into your project's `.claude/claude.md` file.

---

## 🎯 Why These Patterns Matter

These workflow patterns help you:
- ✅ Break down complex tasks into manageable steps
- ✅ Learn from mistakes and avoid repeating them
- ✅ Write better code through self-review
- ✅ Work more efficiently with Claude Code
- ✅ Build professional development habits

**Think of this as:** Your personal software engineering training system.

---

## Pattern 1: Plan Mode Default 📋

### When to Use Plan Mode

**Use Plan Mode for ANY task that:**
- Has 3 or more steps
- Involves architectural decisions
- Requires debugging complex issues
- Implements a new feature
- Refactors existing code

**Don't Use Plan Mode for:**
- Fixing typos
- Changing configuration values
- Simple one-line fixes
- Documentation updates

### How to Use Plan Mode

#### Step 1: Break Down the Task
```
Task: "Implement sentiment analysis"

Plan:
1. Research FinBERT model (15 min)
2. Create sentiment.py file (10 min)
3. Write sentiment analyzer class (30 min)
4. Add batch processing (20 min)
5. Write tests (20 min)
6. Test on real data (15 min)
7. Document usage (10 min)

Total estimate: 2 hours
```

#### Step 2: Identify Potential Issues
```
Potential Blockers:
- FinBERT might need GPU (check if CPU is sufficient)
- Need to handle out-of-memory errors for large batches
- Should cache model to avoid reloading every time
```

#### Step 3: Define Success Criteria
```
Success Criteria:
- Can classify sentiment on test article
- Batch processing 100 articles < 1 minute
- Returns scores in correct format for database
- 80%+ accuracy on manual spot check
```

#### Step 4: Execute with Checkpoints
```
✅ Step 1: Found FinBERT model - ProsusAI/finbert
✅ Step 2: Created src/models/sentiment.py
⏳ Step 3: Writing SentimentAnalyzer class
   - Issue found: Need to handle long articles (>512 tokens)
   - STOP: Need to re-plan text chunking strategy
```

### Example: Real Task with Plan Mode

**Task**: "Add news collection for 50 companies"

**BAD Approach (No Plan):**
```
Just run collector.py with all 50 companies → crashes after 30
→ Why? Rate limit hit
→ Now what? Not sure, try again?
→ Wasted 20 minutes
```

**GOOD Approach (With Plan):**
```
Plan:
1. Check NewsAPI rate limits (100 requests/day)
2. Calculate: 50 companies × 2 requests each = 100 requests (at limit!)
3. Implement rate limiting with sleep()
4. Add progress tracking
5. Test with 5 companies first
6. If works, run all 50
7. Monitor for errors
8. Verify data in database

Success: All 50 companies have articles, no rate limit errors

Execution:
✅ 1. Rate limit: 100 requests/day ✓
✅ 2. Added sleep(1) between requests
✅ 3. Added progress bar
✅ 4. Tested with 5 companies - works!
✅ 5. Running all 50... 
   [After 25 companies] - Hit rate limit!
❌ STOP - Plan didn't account for date range
   Re-plan: Split into 2 days OR reduce lookback from 7 to 3 days
✅ New plan: Reduce to 3 days, continue
✅ All 50 complete, verified in database
```

---

## Pattern 2: Subagent Strategy 🤖

### What Are Subagents?

Think of subagents as **specialized assistants** you can delegate specific tasks to, keeping your main conversation focused.

### When to Use Subagents

**Good Uses:**
- Research: "Find best practices for X"
- Exploration: "Investigate why this error occurs"
- Comparison: "Compare library A vs library B"
- Documentation: "Generate API docs from code"
- Parallel work: "Write tests while I write code"

**Bad Uses:**
- Chaining: "Do task 1, then task 2, then task 3" (too complex)
- Main logic: "Build the entire feature" (keep in main context)

### How to Use Subagents

#### Format Your Subagent Request

```
Claude, I need help with [task]. Please use a subagent to:

Task: [Specific, focused task]
Context: [What the subagent needs to know]
Expected Output: [What you want back]
Success Criteria: [How you'll know it's done]

Example:

Claude, I need help choosing a vector database. Please use a subagent to:

Task: Compare Qdrant vs pgvector for storing article embeddings
Context: 
- Project will have ~10,000 articles initially
- Will grow to ~100,000 articles
- Need semantic search functionality
- Budget: Free tier or <$20/month
- Hosted vs self-hosted: Either is fine

Expected Output: Comparison table with pros/cons of each option
Success Criteria: Clear recommendation with reasoning
```

#### Bring Findings Back to Main Context

```
[After subagent completes research]

Main Context:
Based on subagent research:
- Qdrant: Better for learning, easier setup, good docs
- pgvector: Better for production, integrates with existing DB

Decision: Start with Qdrant for MVP, migrate to pgvector if needed
Next step: Install Qdrant with Docker
```

### Example Workflow

```
Task: Implement RAG system

Main Context:
- I need to build RAG for article summarization
- Let me delegate research

Subagent 1: Research optimal chunk sizes for RAG in finance domain
→ Returns: 500-800 tokens recommended for financial documents

Subagent 2: Find example code for embedding generation with OpenAI
→ Returns: Code sample with error handling

Main Context:
- Use 500 tokens per chunk (from research)
- Implement embedding generation (adapt example code)
- Build retrieval function
- Test end-to-end

Result: Completed RAG system with researched best practices
```

---

## Pattern 3: Self-Improvement Loop 📚

### The Learning System

Every mistake is a learning opportunity. The key is to **capture lessons** so you don't repeat them.

### How to Use tasks/lessons.md

#### Step 1: When Something Goes Wrong

```
[You get an error]

Error: ModuleNotFoundError: No module named 'transformers'

[Fix it, then document]
```

#### Step 2: Record the Lesson

Open `tasks/lessons.md` and add:

```markdown
## Lesson: 2024-03-15 - Forgot to Install Dependencies

**What went wrong**: 
Got ModuleNotFoundError when trying to import transformers

**Root cause**: 
Added transformers to code but forgot to install it with pip

**Prevention rule**: 
After adding ANY new import, immediately run:
pip install <package> && pip freeze > requirements.txt

**Verification step**: 
Created checklist: Before testing code, check requirements.txt
has all imported packages

**Related code**: 
src/models/sentiment.py (uses transformers)
```

#### Step 3: Review Before Starting Work

Every work session, open `tasks/lessons.md` and read:
- Recent lessons (last week)
- Lessons relevant to today's task

#### Step 4: Apply Lessons

```
Today's task: Implement NER (Named Entity Recognition)

Check lessons:
- Lesson about missing imports → Install spacy FIRST
- Lesson about testing on full dataset → Start with 10 articles
- Lesson about Docker not running → Check database is up

Action: 
✅ pip install spacy
✅ Download spacy model: python -m spacy download en_core_web_lg
✅ Test on 10 articles before processing all
✅ Verify database connection first
```

### Example Lessons to Track

**Common Student Mistakes:**
- Forgetting to activate virtual environment
- Not checking if database is running
- Testing on full dataset instead of sample
- Hardcoding secrets instead of using .env
- Not reading error messages completely
- Skipping tests because "it should work"

### Weekly Review

Every Sunday (or end of week):

```markdown
## Week 2 Review (March 15-21)

**Completed**:
- ✅ Implemented news collection
- ✅ Added text cleaning
- ✅ Set up database

**Mistakes Made This Week**:
1. Hit API rate limit (didn't check limits first)
2. Database connection failed (Docker not running)
3. Import error (forgot to install package)

**Lessons Learned**:
- Always check API limits before bulk operations
- Add database health check to scripts
- Install dependencies immediately after adding imports

**Improvement**:
Last week: 5 mistakes → This week: 3 mistakes (-40% 🎉)

**Next Week Goals**:
- Zero database connection errors (add auto-check)
- Zero import errors (create setup validation script)
```

---

## Pattern 4: Verification Before "Done" ✅

### The Staff Engineer Standard

Before marking ANY task complete, ask:

**"Would a senior engineer approve this?"**

If unsure, it's not done yet.

### Verification Checklist

#### Level 1: It Runs
```
- [ ] Code executes without errors
- [ ] No warnings or deprecation notices
- [ ] Completes in reasonable time
```

#### Level 2: It Works Correctly
```
- [ ] Produces expected output
- [ ] Handles edge cases (empty input, wrong type, etc.)
- [ ] Data in database looks correct
- [ ] Logs show correct behavior
```

#### Level 3: It's Production-Ready
```
- [ ] Has error handling (try-catch)
- [ ] Has helpful error messages
- [ ] Has documentation/comments
- [ ] Follows project conventions
- [ ] Would be easy for someone else to understand
```

### Verification Examples

#### Example 1: News Collector

**Task**: "Implement news collector"

**Insufficient Verification:**
```
"I wrote the code, it should work"
Status: NOT DONE
```

**Proper Verification:**
```
✅ Verification Checklist:

Code Execution:
- Ran: python src/collectors/news_api.py
- No errors
- Completed in 15 seconds

Correctness:
- Output: "Fetched 47 articles for Apple Inc."
- Database: SELECT COUNT(*) FROM articles → 47 rows
- Spot check: First 3 articles have title, content, URL
- All fields populated correctly

Edge Cases:
- Empty company name → Raises ValueError ✓
- Invalid API key → Returns helpful error message ✓
- Rate limit hit → Waits and retries ✓

Production Ready:
- Has docstring explaining usage
- Error messages tell user what went wrong
- Follows project naming conventions
- Logging shows progress

Status: COMPLETE ✅
```

#### Example 2: Sentiment Analysis

**Task**: "Add sentiment analysis with FinBERT"

**Proper Verification:**
```
✅ Manual Testing:
test_article = "Company reports record profits and strong growth"
result = analyzer.predict(test_article)

Expected: Positive sentiment
Actual: {'positive': 0.89, 'negative': 0.05, 'neutral': 0.06}
✓ Correct!

✅ Batch Testing:
Processed 100 articles in 45 seconds
All results have scores between 0-1
No errors in logs

✅ Accuracy Check:
Manually labeled 20 articles
Agreement: 17/20 = 85% ✓ (target was >75%)

✅ Integration:
Results save to database correctly
Dashboard displays sentiment scores

Status: COMPLETE ✅
```

### Before & After Comparison

Always show **proof of improvement**:

```
Task: Optimize database queries

Before:
- Query time: 5.2 seconds
- Memory usage: 800MB
- CPU usage: 85%

After:
- Query time: 0.8 seconds (6.5x faster!)
- Memory usage: 200MB (4x less)
- CPU usage: 15% (5.6x less)

Verification:
- Ran EXPLAIN ANALYZE on query
- Added index on published_at column
- Tested with 10,000 articles
- All results identical to before (correctness maintained)
```

---

## Pattern 5: Demand Elegance (Balanced) 💎

### The "Pause and Refactor" Moment

After getting code working, pause and ask:

**"Is there a better way to do this?"**

### When to Refactor

#### Refactor If Code Is:
- Hard to understand (needs comments to explain)
- Repetitive (copy-pasted blocks)
- Fragile (breaks easily with small changes)
- Long (>100 lines in one function)
- Nested deeply (>3 levels of indentation)

#### Don't Refactor If:
- It's a simple fix (<10 lines)
- It's prototype/experimental code
- It's a one-time script
- You're time-pressured (but mark TODO)

### The Two-Pass Approach

**First Pass**: Get it working (quick & dirty)
**Second Pass**: Make it elegant (if worthwhile)

### Refactoring Examples

#### Example 1: Text Cleaning

**First Pass (Working but Messy):**
```python
def clean_text(text):
    text = text.replace("<p>", "")
    text = text.replace("</p>", "")
    text = text.replace("<div>", "")
    text = text.replace("</div>", "")
    text = text.replace("<br>", "")
    text = text.replace("<br/>", "")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&quot;", '"')
    # ... 15 more lines of replaces
    return text
```

**Second Pass (Elegant):**
```python
from bs4 import BeautifulSoup
import html

def clean_text(html_text):
    """Remove HTML tags and decode entities."""
    # Remove HTML tags
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Normalize whitespace
    return ' '.join(text.split())
```

**Why Better?**
- Uses existing library (BeautifulSoup) instead of manual replaces
- Handles ALL HTML tags, not just the ones we listed
- Shorter and easier to understand
- More maintainable

#### Example 2: Database Queries

**First Pass:**
```python
def get_articles_for_company(company_name):
    db = SessionLocal()
    all_articles = db.query(Article).all()
    company_articles = []
    for article in all_articles:
        if company_name.lower() in article.title.lower():
            company_articles.append(article)
    db.close()
    return company_articles
```

**Second Pass:**
```python
def get_articles_for_company(company_name: str) -> List[Article]:
    """
    Fetch articles mentioning a specific company.
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        List of Article objects matching the company
    """
    db = SessionLocal()
    try:
        return db.query(Article).filter(
            Article.title.ilike(f'%{company_name}%')
        ).all()
    finally:
        db.close()
```

**Why Better?**
- Uses database filtering (faster for large datasets)
- Has type hints
- Has documentation
- Uses try/finally for proper resource cleanup
- Case-insensitive search with ilike

### Balance for Student Projects

**Priority Order:**
1. **Working** (most important) - Does it run?
2. **Readable** (very important) - Can you understand it next week?
3. **Elegant** (nice to have) - Is it the "best" way?

**Golden Rule**: 
Don't let pursuit of elegance prevent completion. 
Better to have working code that's a bit messy than perfect code that's incomplete.

---

## Pattern 6: Autonomous Bug Fixing 🔧

### How Claude Should Help with Bugs

When you report a bug, Claude should **diagnose and fix** without hand-holding.

### Bug Report Template

**Instead of:**
```
"It's not working"
```

**Provide:**
```
Bug Report:
- What I tried: [Command or action]
- What happened: [Error message or unexpected behavior]
- What I expected: [Correct behavior]
- Context: [Relevant files, recent changes]

Example:
- Tried: python src/db/connection.py
- Happened: sqlalchemy.exc.OperationalError: could not connect
- Expected: "✅ Database tables created"
- Context: Just started Docker, .env file looks correct
```

### Claude's Response Should Include:

1. **Root Cause Analysis**
2. **Specific Fix**
3. **Verification**
4. **Prevention**

### Example: Autonomous Fix

**Your Report:**
```
"Getting ImportError when running sentiment analysis"
```

**Claude's Response Should Be:**
```
I see the issue. Let me fix this:

ROOT CAUSE:
Line 3 in src/models/sentiment.py imports transformers:
`from transformers import AutoTokenizer`

But transformers isn't installed in your virtual environment.

DIAGNOSIS STEPS:
1. Checked requirements.txt → transformers not listed ✗
2. Checked venv packages → pip list shows no transformers ✗
3. Confirmed venv is active → (venv) visible ✓

FIX:
pip install transformers torch

VERIFICATION:
```python
python -c "from transformers import AutoTokenizer; print('✅ Import works')"
```

PREVENTION:
I've added transformers to requirements.txt so this is documented.
For future: Always add dependencies to requirements.txt immediately.

Try running your script now. It should work.
```

### Types of Bugs Claude Can Fix Autonomously

**Environment Issues:**
- Virtual environment not activated
- Packages not installed
- Wrong Python version

**Code Issues:**
- Import errors
- Typos in variable names
- Wrong function signatures
- Missing error handling

**Configuration Issues:**
- .env file missing or wrong format
- Database connection string incorrect
- API keys not set

**Logic Issues:**
- Off-by-one errors
- Wrong conditions in if statements
- Incorrect data types

---

## Putting It All Together: A Complete Workflow

### Morning Routine (Start of Work Session)

```
1. Open terminal
   cd ~/projects/credit-risk-monitor
   source venv/bin/activate

2. Check environment
   docker-compose ps  # Database running?
   git status        # Any uncommitted changes?

3. Review tasks/lessons.md
   - Read recent lessons
   - Check current blockers
   - Review today's plan

4. Set today's goal
   "Today I will: [specific, achievable goal]"
```

### Working on a Task

```
1. Enter Plan Mode (for 3+ step tasks)
   - Break down into steps
   - Identify blockers
   - Define success criteria

2. Execute step-by-step
   - Verify each step before moving on
   - If something breaks: STOP and re-plan
   - Use subagents for research/exploration

3. Test thoroughly
   - Start with small sample (10 items)
   - Check edge cases
   - Verify data looks correct

4. Demand elegance
   - Ask: "Is there a better way?"
   - Refactor if worthwhile
   - Don't over-engineer

5. Verify before "Done"
   - Run final tests
   - Check logs
   - Prove it works
   - Would a senior engineer approve?

6. Document
   - Add comments to tricky parts
   - Update README if needed
   - Commit with clear message
```

### End of Day Routine

```
1. Review what was done
   - What worked well?
   - What was challenging?
   - Any new lessons?

2. Update tasks/lessons.md
   - Add any new lessons
   - Note blockers for tomorrow
   - Plan next steps

3. Clean up
   - Commit all changes
   - Push to GitHub
   - docker-compose down (if desired)

4. Prepare for tomorrow
   - What's the priority task?
   - Any blockers to resolve first?
   - Need to research anything?
```

---

## Quick Reference Card

**BEFORE starting ANY task:**
- [ ] Virtual environment activated?
- [ ] Database running?
- [ ] Read relevant lessons?
- [ ] Have a plan (for 3+ steps)?

**DURING the task:**
- [ ] Testing on small sample first?
- [ ] Verifying each step?
- [ ] Stopping and re-planning if stuck?
- [ ] Using elegant solutions?

**AFTER completing task:**
- [ ] Proved it works?
- [ ] Added documentation?
- [ ] Updated lessons if mistake?
- [ ] Committed with clear message?

---

**Remember**: These patterns are tools to help you learn and build professionally. Don't stress about following them perfectly – focus on gradual improvement!

The goal is to build good habits that will serve you throughout your career. 🚀
