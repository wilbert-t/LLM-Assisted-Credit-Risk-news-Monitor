# Credit Risk Monitoring System

> An automated pipeline that ingests financial news, scores credit risk with NLP, and surfaces alerts for portfolio managers — so they stop reading thousands of articles manually.

[![CI](https://github.com/wilbert-t/LLM-Assisted-Credit-Risk-news-Monitor/actions/workflows/test.yml/badge.svg)](https://github.com/wilbert-t/LLM-Assisted-Credit-Risk-news-Monitor/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/wilbert-t/LLM-Assisted-Credit-Risk-news-Monitor/branch/main/graph/badge.svg)](https://codecov.io/gh/wilbert-t/LLM-Assisted-Credit-Risk-news-Monitor)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

---

## Problem Statement

Banks monitor thousands of borrowers (obligors) for credit risk. Manual news monitoring does not scale:

- Credit officers spend hours a day reading news reports
- Critical events (defaults, downgrades, fraud) are often spotted too late
- Analysis is inconsistent across analysts
- Regulatory pressure demands documented, auditable decisions

## Solution

An automated pipeline that:

1. **Collects** news from NewsAPI across 50+ obligors
2. **Processes** articles — strips HTML, detects language, extracts entities (spaCy NER)
3. **Scores** sentiment using FinBERT (finance-specific model)
4. **Retrieves** relevant context via RAG (Qdrant vector search)
5. **Generates** LLM-powered summaries (Groq / Anthropic)
6. **Alerts** portfolio managers when risk thresholds are breached
7. **Visualises** trends in a Streamlit dashboard

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Ingestion | NewsAPI, GDELT, BeautifulSoup4 |
| Storage | PostgreSQL 15, Qdrant |
| NLP | spaCy, FinBERT, langdetect |
| LLM | Groq (llama-3.3-70b), Anthropic Claude |
| RAG | LangChain / LlamaIndex |
| Backend | FastAPI, SQLAlchemy |
| Dashboard | Streamlit, Plotly |
| Scheduler | cron / Prefect |
| Deploy | Docker, Docker Compose |

---

## Quick Start

**Prerequisites:** Python 3.12, Docker, a free [NewsAPI key](https://newsapi.org/)

```bash
# 1. Clone and enter the repo
git clone https://github.com/wilbert-t/LLM-Assisted-Credit-Risk-news-Monitor.git
cd LLM-Assisted-Credit-Risk-news-Monitor

# 2. Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.template .env
# Edit .env — add your NEWSAPI_KEY at minimum

# 5. Start the database
docker-compose up -d
```

Then initialise and collect data:

```bash
python -m src.db.connection          # create tables
python -m scripts.seed_obligors      # seed 50 obligors
python -m scripts.collect_news_all   # collect articles (uses ~50 API requests)
```

---

## Project Structure

```
.
├── src/
│   ├── collectors/       # News ingestion (NewsAPI, storage)
│   ├── processors/       # Text cleaning, NER, sentiment (Phase 2+)
│   ├── rag/              # Embeddings, vector search, summariser (Phase 4+)
│   ├── alerts/           # Alert rules and scheduler (Phase 5+)
│   ├── api/              # FastAPI endpoints (Phase 5+)
│   ├── db/               # SQLAlchemy models and connection
│   └── utils/            # Config, logger, constants
├── dashboard/            # Streamlit app (Phase 6+)
├── scripts/              # One-off CLI scripts
├── tests/
│   ├── unit/             # Unit tests (pytest)
│   └── integration/      # Integration tests (Phase 5+)
├── .github/workflows/    # CI/CD (GitHub Actions)
├── docker-compose.yml    # PostgreSQL service
└── requirements.txt
```

---

## Development Workflow

```bash
# Activate environment
source venv/bin/activate

# Confirm services are running
docker-compose ps

# Run tests
pytest tests/unit -v

# Run tests with coverage
pytest tests/unit --cov=src --cov-report=term-missing

# Collect fresh news data
python -m scripts.collect_news_all
```

---

## Week-by-Week Progress

**Week 1 — Foundation & Data Collection**
- [x] Project structure, DB models, utility modules
- [x] PostgreSQL via Docker Compose
- [x] 50 obligors seeded
- [x] NewsAPI collector — 2,258 articles from 50 obligors
- [x] Unit test suite — 24 tests, all passing
- [x] CI/CD pipeline (GitHub Actions)

**Week 2 — Text Processing**
- [ ] HTML cleaning, whitespace normalisation
- [ ] Language detection
- [ ] spaCy NER — extract company/person entities

**Week 3 — Risk Signals**
- [ ] FinBERT sentiment scoring
- [ ] Credit-relevance classifier
- [ ] Obligor–article linking

**Week 4 — RAG**
- [ ] Chunk + embed articles (sentence-transformers)
- [ ] Qdrant vector store
- [ ] LLM summarisation with retrieved context

**Week 5 — Alerts**
- [ ] Alert rules (threshold-based)
- [ ] Scheduled batch job
- [ ] FastAPI endpoints

**Week 6 — Dashboard**
- [ ] Streamlit portfolio overview
- [ ] Obligor drill-down page
- [ ] Sentiment trend charts

**Week 7–8 — Deploy**
- [ ] Docker Compose full stack
- [ ] Cloud hosting (Render / Railway)
- [ ] Demo-ready README

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Acknowledgements

- [FinBERT](https://huggingface.co/ProsusAI/finbert) — finance-specific sentiment model
- [NewsAPI](https://newsapi.org/) — news data
- [Qdrant](https://qdrant.tech/) — vector database
