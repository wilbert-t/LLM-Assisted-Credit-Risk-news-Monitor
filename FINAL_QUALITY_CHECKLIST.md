# Final Quality Checklist ✅

Use this checklist before marking ANY task as "COMPLETE". This ensures professional-quality work.

---

## 🎯 How to Use This Checklist

**Before saying "I'm done":**
1. Go through EVERY section relevant to your task
2. Check off each item (or mark N/A if not applicable)
3. Provide evidence for each check
4. If ANY item fails → Task is NOT complete yet

**Remember**: "It looks like it works" ≠ "It's actually complete"

---

## ⚡ Quick 5-Question Test (Start Here!)

**Answer honestly. If ANY answer is "NO" → Not done yet.**

1. **Does it run without errors?** YES / NO
2. **Does it produce correct results?** YES / NO  
3. **Did you test edge cases?** YES / NO
4. **Can someone else understand it?** YES / NO
5. **Would you show this in a job interview?** YES / NO

**All YES?** → Proceed with full checklist below  
**Any NO?** → Fix that first, then come back

---

## Level 1: Code Execution ⚙️

### Basic Functionality
- [ ] Code runs without errors
- [ ] No warnings or deprecation notices
- [ ] Completes in reasonable time (<1 min for dev tasks)
- [ ] Doesn't hang or loop infinitely

**Evidence Required:**
```bash
Command: python src/models/sentiment.py
Output: [paste full output here]
Time: 8.3 seconds
Errors: None
```

### Environment
- [ ] Virtual environment activated (`(venv)` visible)
- [ ] All packages installed (`pip list` shows them)
- [ ] Database running (`docker-compose ps` shows "Up")
- [ ] .env file loaded correctly

---

## Level 2: Correctness 🎯

### Output Verification  
- [ ] Produces expected output
- [ ] Output format is correct (JSON, data types, etc.)
- [ ] All required fields populated (no unexpected None/null)

**Evidence Required:**
```python
Expected: {'positive': 0.85, 'negative': 0.05, 'neutral': 0.10}
Actual: {'positive': 0.87, 'negative': 0.04, 'neutral': 0.09}
✓ Matches expected format and ranges
```

### Database Integrity (if applicable)
- [ ] Data saved correctly
- [ ] No duplicates created
- [ ] Data types match schema
- [ ] Timestamps are accurate

**Evidence Required:**
```sql
SELECT COUNT(*) FROM articles;  -- Expected: 47
SELECT * FROM articles LIMIT 3;  -- Verify structure
```

### Edge Cases
- [ ] Empty input handled: `test_function("")`
- [ ] Invalid input raises error: `test_function(None)`
- [ ] Large input doesn't crash: `test_function([1000 items])`
- [ ] Special characters work: `test_function("O'Brien")`

---

## Level 3: Error Handling 🛡️

### Try-Catch Coverage
- [ ] Risky operations wrapped in try-except
- [ ] Error messages are helpful
- [ ] Errors include enough context for debugging
- [ ] Doesn't crash on expected errors

**Good Error Message Example:**
```
❌ Bad: "Error occurred"
✅ Good: "Database connection failed. Is Docker running? 
         Run: docker-compose up -d"
```

### Graceful Degradation
- [ ] API rate limits handled (retry logic)
- [ ] Network failures handled (exponential backoff)
- [ ] Partial failures don't lose progress

---

## Level 4: Performance ⚡

### Speed Benchmarks
- [ ] Batch processing: >10 items/second
- [ ] API endpoints: <2 seconds response
- [ ] Database queries: <1 second
- [ ] Works with 10x current data

**Evidence Required:**
```
Processed 100 articles in 8.5 seconds
= 11.7 articles/second ✓ (exceeds 10/sec target)
```

### Resource Usage  
- [ ] Memory: <500MB for dev tasks
- [ ] CPU: <80% sustained
- [ ] Connections closed properly
- [ ] No resource leaks

---

## Level 5: Code Quality 📝

### Documentation
- [ ] Function has complete docstring
- [ ] Docstring includes: Args, Returns, Raises, Example
- [ ] Complex logic has inline comments
- [ ] Example usage provided

**Required Docstring Format:**
```python
def collect_news(company_name: str, days: int = 7) -> List[Article]:
    """
    Collect recent news articles for a company.
    
    Args:
        company_name: Company to search (e.g., "Apple Inc.")
        days: Days to look back (default: 7)
    
    Returns:
        List of Article objects with title, content, URL
    
    Raises:
        ValueError: If company_name is empty
        APIError: If NewsAPI returns 401/403
    
    Example:
        >>> articles = collect_news("Tesla", days=14)
        >>> print(len(articles))
        23
    """
```

### Code Style
- [ ] Follows PEP 8 / project conventions
- [ ] Descriptive variable names (`article_count` not `x`)
- [ ] Functions <50 lines (ideally <30)
- [ ] No code duplication (DRY)
- [ ] Type hints on parameters and return

---

## Level 6: Testing 🧪

### Manual Testing
- [ ] Tested with realistic data
- [ ] Tested "happy path" (everything works)
- [ ] Tested "sad path" (things go wrong)
- [ ] Tested edge cases

**Test Cases Evidence:**
```
Happy Path: collect_news("Apple Inc.") → 47 articles ✓
Sad Path: collect_news("") → ValueError ✓
Edge Case: collect_news("O'Reilly") → 12 articles ✓
Large Input: 100 companies → completes in 180 sec ✓
```

### Integration Testing
- [ ] Works with actual database
- [ ] Works with actual API
- [ ] Works with rest of system
- [ ] Full pipeline test passes

---

## Level 7: Database (if applicable) 🗄️

### Schema
- [ ] Proper data types (TEXT, INTEGER, TIMESTAMP, etc.)
- [ ] Primary keys defined
- [ ] Foreign keys defined
- [ ] Indexes on queried columns

**Verification:**
```sql
\d articles  -- Check structure
\di          -- Check indexes exist
```

### Queries
- [ ] Efficient (use `EXPLAIN ANALYZE`)
- [ ] No N+1 query problems
- [ ] Proper JOINs used
- [ ] Transactions for multi-step ops

---

## Level 8: Security 🔒

### Secrets Management
- [ ] No API keys hardcoded (`grep -r "sk-" src/`)
- [ ] All secrets in .env
- [ ] .env in .gitignore
- [ ] .env.example provided

### Input Validation
- [ ] User input validated
- [ ] SQL injection prevented (parameterized queries)
- [ ] No eval()/exec() with user input
- [ ] File uploads validated (if applicable)

---

## Level 9: Integration 🔗

### Project Fit
- [ ] Follows project structure
- [ ] Uses project utilities
- [ ] Follows naming conventions
- [ ] Doesn't break existing tests

### Dependencies
- [ ] Added to requirements.txt
- [ ] Versions pinned (`package==1.2.3`)
- [ ] No conflicts
- [ ] No unused imports

### Git
- [ ] Committed with clear message
- [ ] Message describes WHAT and WHY
- [ ] No sensitive files committed
- [ ] Branch up to date

**Good Commit Message:**
```
Add sentiment analysis with FinBERT

- Implements SentimentAnalyzer class using ProsusAI/finbert
- Adds batch processing for efficiency (50 articles/batch)
- Includes error handling for API failures
- Adds unit tests with 85% coverage

Resolves: #23
```

---

## Level 10: Documentation 📚

### Project Documentation
- [ ] README updated (if new feature)
- [ ] API docs updated (if backend change)
- [ ] Setup steps documented (if new dependencies)
- [ ] Known limitations noted

### User Documentation
- [ ] How to use is documented
- [ ] Example output shown
- [ ] Screenshots/GIFs (if UI)
- [ ] Demo-able in <2 minutes

---

## Level 11: Self-Improvement 📖

### Lessons Learned
- [ ] Updated tasks/lessons.md (if made mistakes)
- [ ] Prevention rules created
- [ ] Added to personal checklist

**If you made mistakes, document them:**
```markdown
## Lesson: 2024-03-20 - Forgot Rate Limiting

What went wrong: Hit API limit, script crashed
Root cause: Didn't check NewsAPI limits (100/day)
Prevention: Always check API docs BEFORE bulk operations
Verification: Added rate limiter with delays
```

### Quality Review
- [ ] Asked: "Would a staff engineer approve this?"
- [ ] Considered: "Is there a more elegant way?"
- [ ] Identified areas for improvement

---

## 📋 Task Completion Report Template

**Fill this out before marking complete:**

```markdown
# Task Completion Report

**Task**: [Description]
**Date**: 2024-03-20
**Status**: ✅ COMPLETE

## Verification Evidence

### 1. Execution
Command: python src/collectors/news_api.py
Output: Fetched 47 articles for Apple Inc.
Time: 12.3 seconds
Errors: None

### 2. Database  
Query: SELECT COUNT(*) FROM articles;
Result: 47 rows (matches expected)

Sample: 
- "Apple announces new iPhone" (valid)
- "AAPL stock rises 3%" (valid)
- All fields populated ✓

### 3. Edge Cases
- Empty input → ValueError ✓
- Invalid API key → Helpful error ✓
- Network timeout → Retry logic works ✓

### 4. Performance
- 47 articles in 12.3 sec = 3.8 articles/sec
- Memory: 145MB (under 500MB limit)
- CPU: 45% average

### 5. Code Quality
- Added docstrings to all functions
- Type hints on all parameters
- No code duplication
- Follows PEP 8

## Files Changed
```
src/collectors/news_api.py (new, 120 lines)
tests/test_news_collector.py (new, 60 lines)  
requirements.txt (added: requests, beautifulsoup4)
README.md (added: News Collection section)
```

## Lessons Learned
None - followed checklist, no mistakes

## Next Steps
- Add more news sources (GDELT, Alpha Vantage)
- Implement scheduled collection (cron job)
```

---

## 🚨 Red Flags (Stop If You See These!)

- [ ] "I think it works" → Need EVIDENCE
- [ ] "I tested it once" → Need systematic testing
- [ ] "I'll add docs later" → Do it NOW
- [ ] "No one will use that case" → They WILL
- [ ] "Good enough for now" → Define "good enough"
- [ ] "I'll remember this" → You WON'T

---

## ✅ Green Lights (Signs of Quality)

- [x] Clear, helpful error messages
- [x] Comprehensive docstrings  
- [x] Edge cases handled
- [x] Tests pass consistently
- [x] Someone else could maintain this
- [x] Proud to demo this
- [x] Committed with clear message
- [x] Updated lessons.md

---

## 📊 Skill Development Tracker

Track how long the checklist takes:

**Week 1**: 30 minutes (learning)  
**Week 4**: 10 minutes (habit forming)  
**Week 8**: 5 minutes (automatic)

**Goal**: Eventually you won't need this checklist - quality becomes automatic! 🎯

---

## 🎓 Professional Standards Summary

**Ask these before saying "done":**

1. **Would this pass code review?** (Quality)
2. **Would this work in production?** (Reliability)
3. **Can someone else maintain it?** (Readability)
4. **Would I put this in my portfolio?** (Pride)

**All YES = ✅ COMPLETE**  
**Any NO = Keep working**

---

**Remember**: This checklist trains you to build professionally. Use it every time until it becomes second nature. Then you'll just naturally ship quality work! 🚀
