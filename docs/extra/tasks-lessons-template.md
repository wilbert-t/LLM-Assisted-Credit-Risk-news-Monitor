# Tasks & Lessons - Credit Risk Monitor

This file tracks mistakes, learnings, and prevention strategies to avoid repeating errors.

---

## How to Use This File

**After ANY correction or mistake:**
1. Add a new lesson entry below
2. Include date, mistake type, root cause, and prevention rule
3. Review this file at the start of each session
4. Apply relevant lessons to current task

---

## Session Checklist (Review Before Starting Work)

Before starting work each day, review:
- [ ] Relevant lessons from previous mistakes
- [ ] Current blockers from last session
- [ ] Next steps from TODO section

---

## Active Tasks

### Current Sprint (Week X)
- [ ] Task 1: Description
  - Status: In Progress / Blocked / Complete
  - Next step: Specific action
  - Blocker: If any

- [ ] Task 2: Description
  - Status: 
  - Next step:

---

## Lessons Learned

### Template for New Lessons
```markdown
## Lesson: [YYYY-MM-DD] - [Mistake Type]
**What went wrong**: [Specific error or issue]
**Root cause**: [Why it happened - be honest!]
**Prevention rule**: [How to avoid this in future]
**Verification step**: [How to check this won't happen again]
**Related code/files**: [If applicable]
```

---

### Example Lessons (Delete These After Adding Real Ones)

## Lesson: 2024-03-15 - Forgot to Activate Virtual Environment
**What went wrong**: Got "ModuleNotFoundError: No module named 'fastapi'" when running script
**Root cause**: Opened new terminal, forgot to activate venv, ran Python from system
**Prevention rule**: ALWAYS check for (venv) at start of terminal line before running any Python command
**Verification step**: Added alias `crmenv='cd ~/projects/credit-risk-monitor && source venv/bin/activate'` to shell config
**Related files**: All Python scripts

---

## Lesson: 2024-03-15 - Database Not Running
**What went wrong**: Script crashed with "could not connect to server"
**Root cause**: Docker Desktop wasn't started, database container not running
**Prevention rule**: Before ANY database operation, run `docker-compose ps` to verify database is UP
**Verification step**: Added try-catch with helpful error message pointing to check Docker
**Related files**: src/db/connection.py, all scripts that use database

---

## Lesson: 2024-03-16 - Hardcoded API Key in Code
**What went wrong**: Almost committed API key to Git (caught by .gitignore)
**Root cause**: Put API key directly in Python file instead of .env
**Prevention rule**: NEVER hardcode secrets. Always use environment variables from .env file
**Verification step**: Double-check `git diff` before committing, verify no API keys visible
**Related files**: .env (keep this in .gitignore!), src/utils/config.py

---

## Lesson: 2024-03-17 - Tested on Full Dataset, Crashed
**What went wrong**: Ran sentiment analysis on 10,000 articles, ran out of memory
**Root cause**: Didn't test on small sample first, tried to process everything at once
**Prevention rule**: ALWAYS test on small sample (10-50 items) before running on full dataset
**Verification step**: Add `--limit` parameter to all batch processing scripts
**Related files**: src/models/sentiment.py, scripts/process_all.py

---

## Lesson: 2024-03-18 - Wrong Import Path
**What went wrong**: `ImportError: cannot import name 'Article' from 'src.db.models'`
**Root cause**: Forgot that Python imports are from project root, not current file location
**Prevention rule**: Always use absolute imports from project root (e.g., `from src.db.models import Article`)
**Verification step**: Run script from project root to test imports work correctly
**Related files**: All Python files with imports

---

## Common Mistakes Checklist

Before running ANY code, check:
- [ ] Virtual environment activated? (see `(venv)` in terminal)
- [ ] In correct directory? (run `pwd` - should be project root)
- [ ] Database running? (run `docker-compose ps`)
- [ ] .env file has required keys?
- [ ] Testing on small sample first? (not full dataset)
- [ ] Imports use absolute paths from project root?

---

## Prevention Rules Summary

Quick reference of all prevention rules (update as lessons are added):

1. **Environment**:
   - Always activate venv before running Python
   - Check you're in project root directory
   - Verify Docker is running before DB operations

2. **Security**:
   - Never hardcode API keys or passwords
   - Always use .env for secrets
   - Double-check git diff before committing

3. **Development**:
   - Test on small samples before full dataset
   - Use absolute imports from project root
   - Read error messages completely before Googling

4. **Database**:
   - Check connection before running queries
   - Use transactions for data modifications
   - Always have backup before major changes

5. **API Integration**:
   - Check rate limits before bulk operations
   - Add retry logic with exponential backoff
   - Log all API calls for debugging

---

## Blockers & Solutions

### Active Blockers
(None currently - update when blocked)

### Resolved Blockers
- **[Date]**: [What was blocking] → [How it was resolved]

---

## Code Quality Checklist

Before marking any task "complete":
- [ ] Code runs without errors
- [ ] Tested with sample data
- [ ] Added error handling for edge cases
- [ ] Documented with docstrings
- [ ] Follows project conventions
- [ ] Would pass code review
- [ ] Committed with clear message

---

## Weekly Review Template

At end of each week:

### Week X Review (Date Range)

**Completed**:
- Task 1
- Task 2

**Blockers Encountered**:
- Blocker 1 → Solution

**New Lessons**:
- Lesson 1
- Lesson 2

**Next Week Goals**:
- Goal 1
- Goal 2

**Biggest Challenge**:
[What was hardest this week]

**Biggest Win**:
[What went really well]

---

## Notes & Ideas

Random thoughts, ideas for improvements, or things to investigate:

- [Date] Idea: Maybe cache LLM responses to save API costs
- [Date] Note: Found good tutorial on RAG optimization
- [Date] TODO: Research vector database indexing strategies

---

## Emergency Contacts & Resources

**When Really Stuck:**
- Claude Code: `claude "help with [specific issue]"`
- Stack Overflow: [tag] + [error message]
- Official Docs: [links to docs you use frequently]

**Key Documentation**:
- Project docs: `docs/`
- Troubleshooting: `TROUBLESHOOTING_GUIDE.md`
- Commands: `COMMAND_CHEAT_SHEET.md`

---

**Last Updated**: [Date]
**Current Phase**: Week X - [Phase Name]
**Overall Status**: On Track / Behind Schedule / Ahead of Schedule
