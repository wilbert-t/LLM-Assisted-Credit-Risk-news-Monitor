# Credit Risk Monitoring System

## Session Start — do this first
1. Read `.claude/session-log.md` → know where we left off
2. Read last 20 lines of `.claude/lessons.md` → avoid repeat mistakes
3. Run `docker-compose ps` → confirm DB + Qdrant are up
4. Confirm venv is active: `source venv/bin/activate`

## Session End — do this before stopping
Update `.claude/session-log.md`:
- What was completed this session
- Current blockers or open questions
- Exact next step to resume (be specific — file, function, line if relevant)
- Any new lesson (also log in `.claude/lessons.md`)
Keep only the last 5 sessions in the log.

---

## Project
Automated pipeline: News → NLP Analysis → RAG Summarization → Alerts → Dashboard
Banks can't manually monitor thousands of obligors. This system ingests news,
scores credit risk, and surfaces alerts automatically.

## Tech Stack
- **Ingestion**: NewsAPI, GDELT, BeautifulSoup4, httpx
- **Storage**: PostgreSQL, Qdrant or pgvector
- **NLP**: spaCy (NER), FinBERT (sentiment), langdetect
- **LLM**: OpenAI GPT-4 or Anthropic Claude
- **Orchestration**: LangChain or LlamaIndex (RAG)
- **Backend**: FastAPI + SQLAlchemy
- **Dashboard**: Streamlit + Plotly
- **Scheduler**: cron or Prefect
- **Deploy**: Docker + Docker Compose

## Build Phases
1. Data collection — NewsAPI, DB setup, `articles` table
2. Text processing — clean HTML, NER, entity mapping
3. Risk signals — FinBERT sentiment, credit-relevance classifier
4. RAG — chunk, embed, Qdrant, retriever + summarizer
5. Alerts — threshold rules, scheduled jobs, FastAPI endpoints
6. Dashboard — Streamlit portfolio view + drill-down
7. Deploy — Docker Compose, hosted demo, README

## Reference
Static details live in `.claude/reference/` — load only when relevant:
- `.claude/reference/schema.md` — full DB schema + env vars
- `.claude/reference/rag.md` — RAG config, LLM prompt pattern, model settings
- `.claude/reference/rules.md` — alert rules, API rate limits, keywords

---

## Workflow Rules

### Planning
- 3+ step task → write plan first: steps, expected outputs, blockers
- Step fails → stop and re-plan, don't randomly try fixes

### Verification (before marking done)
- Run the code, confirm no errors
- Spot-check 5–10 DB rows, confirm data looks correct
- Test one edge case: empty input, bad API key, duplicate data
- Paste evidence of output — "it should work" is not done

### Bug Fixing
- Read full error, find root cause (file + line)
- Fix, verify, log in `.claude/lessons.md`
- Don't ask for info you can find in logs or code

### Elegance
- Get it working first, then ask "is there a simpler way?"
- Refactor if: copy-pasted 3+ times, nested >3 levels, needs comments for basic logic
- Don't refactor: simple fixes, one-off scripts, anything while debugging

### Always
- Activate venv before running anything
- Run `docker-compose ps` before any DB operation
- Test on 10 rows before full dataset runs
- Use `.env` for all secrets, never hardcode