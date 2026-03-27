# Task Completion Checklist

**Rule**: Never say "done" without passing this checklist. "It looks like it works" ≠ done.

---

## ⚡ Quick Gate (answer honestly — any NO = not done yet)
- [ ] Does it run without errors?
- [ ] Does it produce correct results?
- [ ] Did you test at least one edge case?
- [ ] Can someone else understand it?
- [ ] Would you show this in a job interview?

---

## ✅ Full Checklist

### 1. 🔧 Execution
- [ ] Runs without errors or warnings
- [ ] Completes in reasonable time (<1 min for dev tasks)
- [ ] venv activated, Docker running, `.env` loaded

### 2. 🎯 Correctness
- [ ] Output matches expected format and values
- [ ] DB rows look correct — spot-check 5–10 rows
- [ ] No unexpected `None`/null values in required fields
- [ ] Deduplication works (re-run adds 0 new rows)

### 3. 🧪 Edge Cases
- [ ] Empty input → raises clear error
- [ ] Invalid/None input → handled gracefully
- [ ] Duplicate data → no crash, no double inserts
- [ ] API failure → retries or fails with helpful message

### 4. 🛡️ Error Handling
- [ ] Risky operations wrapped in try-except
- [ ] Error messages tell you what to do, not just what failed
- [ ] API rate limits handled (retry + backoff)
- [ ] No secrets hardcoded (`grep -r "sk-" src/` returns nothing)

### 5. ⚡ Performance
- [ ] Batch processing: >10 items/sec
- [ ] API endpoints: <2 sec response
- [ ] DB queries: <1 sec
- [ ] Memory: <500MB for dev tasks

### 6. 📝 Code Quality
- [ ] All functions have docstrings (Args, Returns, Raises, Example)
- [ ] Type hints on parameters and return values
- [ ] No copy-pasted blocks (DRY)
- [ ] Functions <50 lines, no nesting >3 levels deep
- [ ] New packages added to `requirements.txt`

### 7. 🗄️ Database (if applicable)
- [ ] Schema uses correct types, PKs, FKs, and indexes
- [ ] Queries use `EXPLAIN ANALYZE` — no seq scans on large tables
- [ ] Multi-step writes use transactions

### 8. 📚 Documentation & Git
- [ ] README updated if new feature or dependency added
- [ ] Committed with a clear message: what + why
- [ ] No sensitive files committed (`.env` in `.gitignore`)

### 9. 📖 Self-Improvement
- [ ] If you made a mistake → logged in `tasks/lessons.md` (what went wrong, root cause, prevention rule)
- [ ] Asked: "Is there a simpler way?" before marking done

---

## 📋 Completion Report (fill out before closing the task)

```
Task: [description]
Date: YYYY-MM-DD

Execution:   command ran, output was [X], time [X]s, no errors
DB check:    [X] rows, sample looks correct
Edge cases:  empty input ✓ | invalid input ✓ | duplicate ✓
Performance: [X] items/sec | [X]MB memory
Files changed: [list]
Lessons learned: [none / what you logged]
```

---

## 🚨 Red Flags — stop if you catch yourself thinking:
- *"I think it works"* → need evidence
- *"I'll add docs later"* → do it now
- *"No one will hit that case"* → they will
- *"Good enough for now"* → define good enough first