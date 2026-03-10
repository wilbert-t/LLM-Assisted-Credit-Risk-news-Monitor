# Credit Risk Monitoring System - Claude Code Configuration

## Project Overview
An automated credit risk monitoring system that collects news from multiple sources, analyzes credit-relevant events using NLP/LLM, and generates actionable alerts for financial institutions to monitor obligors (borrowers/counterparties).

**Core Value Proposition**: Banks and hedge funds need early warning systems for credit events (downgrades, defaults, fraud, liquidity issues) across thousands of obligors. Manual monitoring doesn't scale.

## System Architecture

```
News Sources (APIs/Scrapers)
    ↓
Data Ingestion Pipeline (Python + Airflow/Prefect)
    ↓
PostgreSQL (raw articles) + Text Processing (spaCy, transformers)
    ↓
Risk Analysis Layer
    ├─ Sentiment Analysis (FinBERT)
    ├─ NER (company/ticker extraction)
    ├─ Credit-Relevance Classification (rule-based + LLM)
    └─ Event Categorization (downgrade, default, fraud, etc.)
    ↓
Vector Database (Qdrant/pgvector) + Embeddings
    ↓
RAG System (LangChain/LlamaIndex)
    ├─ Retrieve relevant news chunks
    ├─ LLM Summarization (OpenAI/Anthropic)
    └─ Structured Risk Metadata
    ↓
Alert System + FastAPI Backend
    ↓
Dashboard (Streamlit/Dash)
```

## Technology Stack

### Data Collection
- **News APIs**: NewsAPI, GDELT, Alpha Vantage, Alpaca
- **Web Scraping**: requests, BeautifulSoup4, Scrapy, playwright
- **Scheduling**: cron, Apache Airflow, Prefect

### Storage
- **Relational DB**: PostgreSQL with pgvector extension
- **Vector DB**: Qdrant (primary), Weaviate, or pgvector
- **ORM**: SQLAlchemy

### NLP/ML
- **Frameworks**: Hugging Face transformers, spaCy
- **Models**: 
  - FinBERT (sentiment analysis)
  - Named Entity Recognition models
  - OpenAI/Anthropic LLMs for summarization
- **Embeddings**: OpenAI embeddings API or sentence-transformers
- **RAG**: LangChain or LlamaIndex

### Backend/API
- **Framework**: FastAPI
- **Authentication**: Simple token-based or API key
- **Async Processing**: httpx, asyncio

### Frontend
- **Dashboard**: Streamlit (rapid prototyping) or Plotly Dash
- **Visualization**: Plotly, matplotlib

### Deployment
- **Containerization**: Docker, Docker Compose
- **Cloud**: Render, Railway, AWS Lightsail (student-friendly)
- **Monitoring**: Python logging, optional Prometheus + Grafana

## Project Structure

```
credit-risk-monitor/
├── .claude/
│   └── claude.md                 # This file
├── data/
│   ├── raw/                      # Raw API responses
│   ├── processed/                # Cleaned data
│   └── embeddings/               # Vector embeddings cache
├── src/
│   ├── collectors/               # News collection modules
│   │   ├── __init__.py
│   │   ├── news_api.py
│   │   ├── scraper.py
│   │   └── scheduler.py
│   ├── processors/               # Text processing
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   ├── ner_extractor.py
│   │   └── preprocessor.py
│   ├── models/                   # ML/NLP models
│   │   ├── __init__.py
│   │   ├── sentiment.py
│   │   ├── classifier.py
│   │   └── embeddings.py
│   ├── rag/                      # RAG system
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── summarizer.py
│   ├── alerts/                   # Alert generation
│   │   ├── __init__.py
│   │   ├── rules.py
│   │   └── generator.py
│   ├── api/                      # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   └── schemas/
│   ├── db/                       # Database models
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── connection.py
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── dashboard/
│   ├── app.py                    # Streamlit app
│   ├── components/
│   └── pages/
├── notebooks/                    # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_sentiment_analysis.ipynb
│   ├── 03_rag_testing.ipynb
│   └── 04_evaluation.ipynb
├── infra/                        # Infrastructure
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── airflow/                  # Airflow DAGs
│   └── migrations/               # DB migrations
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── architecture.md
│   ├── api_docs.md
│   └── setup.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Development Phases

### Phase 1: Data Collection (Week 1-2)
**Goal**: Build reliable news ingestion pipeline
- Set up PostgreSQL database with initial schema
- Implement NewsAPI/GDELT collectors
- Create article storage with deduplication
- Build simple scraper for supplemental sources
- Test with 10-50 companies (portfolio universe)

**Key Files**: `src/collectors/`, `src/db/models.py`

### Phase 2: Text Processing (Week 3)
**Goal**: Clean and enrich text data
- Text cleaning pipeline (HTML removal, encoding fixes)
- NER for company/ticker extraction
- Entity mapping to obligor list
- Language detection and filtering

**Key Files**: `src/processors/`

### Phase 3: Risk Signal Detection (Week 4)
**Goal**: Classify and score articles
- FinBERT sentiment analysis integration
- Credit-relevance classifier (keywords + LLM)
- Event type classification (downgrade, default, fraud, etc.)
- Aggregation by obligor and time windows

**Key Files**: `src/models/sentiment.py`, `src/models/classifier.py`

### Phase 4: RAG System (Week 5)
**Goal**: Build LLM-powered summarization
- Set up vector database (Qdrant or pgvector)
- Generate and store embeddings
- Implement semantic search retrieval
- Design prompts for credit-focused summaries
- Output structured JSON with risk metadata

**Key Files**: `src/rag/`, `src/models/embeddings.py`

### Phase 5: Alert System (Week 6)
**Goal**: Automated alert generation
- Define alert rules (thresholds, patterns)
- Scheduled job for alert checks
- FastAPI endpoints for alert retrieval
- Optional: Email/Slack notifications

**Key Files**: `src/alerts/`, `src/api/main.py`

### Phase 6: Dashboard (Week 7)
**Goal**: Visual interface for risk monitoring
- Portfolio overview with risk scores
- Obligor drill-down pages
- Time-series sentiment charts
- Alert history and filtering
- LLM summary display

**Key Files**: `dashboard/app.py`, `dashboard/components/`

### Phase 7: Polish & Deploy (Week 8)
**Goal**: Production-ready deployment
- Docker containerization
- Documentation (README, architecture diagram)
- Demo video/screenshots
- Deployment to Render/Railway
- Evaluation metrics documentation

## Database Schema

### Core Tables

```sql
-- Raw articles
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source VARCHAR(100),
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    language VARCHAR(10),
    raw_json JSONB
);

-- Processed articles
CREATE TABLE processed_articles (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    cleaned_text TEXT,
    entities JSONB,  -- [{type: "ORG", text: "XYZ Corp", ticker: "XYZ"}, ...]
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    is_credit_relevant BOOLEAN,
    event_types TEXT[],  -- ['downgrade', 'lawsuit', ...]
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Obligors (companies being monitored)
CREATE TABLE obligors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ticker VARCHAR(20),
    lei VARCHAR(20),  -- Legal Entity Identifier
    sector VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Article-obligor mapping
CREATE TABLE article_obligors (
    article_id INTEGER REFERENCES processed_articles(id),
    obligor_id INTEGER REFERENCES obligors(id),
    mention_count INTEGER DEFAULT 1,
    PRIMARY KEY (article_id, obligor_id)
);

-- Daily aggregates
CREATE TABLE obligor_daily_signals (
    obligor_id INTEGER REFERENCES obligors(id),
    date DATE,
    article_count INTEGER,
    negative_count INTEGER,
    avg_sentiment FLOAT,
    credit_relevant_count INTEGER,
    event_types JSONB,
    PRIMARY KEY (obligor_id, date)
);

-- Alerts
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    obligor_id INTEGER REFERENCES obligors(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    severity VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
    summary TEXT,
    event_types TEXT[],
    supporting_article_ids INTEGER[],
    metadata JSONB,  -- LLM output, scores, etc.
    acknowledged BOOLEAN DEFAULT FALSE
);

-- Vector embeddings (if using pgvector)
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES processed_articles(id),
    chunk_index INTEGER,
    chunk_text TEXT,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/credit_risk

# News APIs
NEWSAPI_KEY=your_key_here
ALPHA_VANTAGE_KEY=your_key_here

# LLM APIs
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_key

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Key Development Principles

### 1. Start Simple, Iterate
- Begin with manual scripts before orchestration
- Use SQLite locally before PostgreSQL
- Test with small data samples (100 articles)
- Add complexity only when needed

### 2. Modularity
- Each component should be independently testable
- Use dependency injection for flexibility
- Create clear interfaces between modules

### 3. Data Quality First
- Log every stage of processing
- Track data lineage
- Monitor distribution shifts (sentiment, volume)
- Build validation checks early

### 4. LLM Best Practices
- Design prompts with few-shot examples
- Request structured output (JSON)
- Set temperature low for classification (0.1-0.3)
- Implement retry logic with exponential backoff
- Cache LLM responses when possible
- Monitor token usage and costs

### 5. RAG Optimization
- Chunk text intelligently (by paragraph, ~500 tokens)
- Use hybrid search (semantic + keyword) when possible
- Rerank retrieved chunks for relevance
- Include metadata in embeddings (date, source, obligor)
- Refresh embeddings periodically

## Testing Strategy

### Unit Tests
- Data cleaning functions
- Entity extraction accuracy
- Classification model outputs
- Alert rule logic

### Integration Tests
- End-to-end pipeline runs
- API endpoint responses
- Database operations
- RAG retrieval quality

### Evaluation Metrics
- **Sentiment**: Compare FinBERT vs human labels on sample
- **NER**: Precision/recall on company extraction
- **Credit-Relevance**: F1 score on classification
- **Alert Quality**: False positive rate, user feedback
- **RAG**: Relevance of retrieved chunks, summary accuracy

## Common Pitfalls & Solutions

### Problem: Entity Matching
**Issue**: News mentions "Apple" - is it Apple Inc. or a different company?
**Solution**: 
- Build fuzzy matching with thresholds
- Use multiple identifiers (ticker, LEI, aliases)
- Validate with external databases (OpenCorporates)
- Manual curation for important obligors

### Problem: LLM Hallucinations
**Issue**: LLM invents non-existent events
**Solution**:
- Always ground with RAG (provide source text)
- Request verbatim quotes in output
- Validate against source articles programmatically
- Lower temperature for factual tasks

### Problem: Alert Fatigue
**Issue**: Too many low-quality alerts
**Solution**:
- Tune thresholds based on backtesting
- Add severity levels
- Implement alert suppression (don't repeat same event)
- Provide drill-down to sources

### Problem: Slow Pipeline
**Issue**: Processing thousands of articles takes too long
**Solution**:
- Batch processing with multiprocessing
- Cache embeddings and model outputs
- Use async I/O for API calls
- Index database properly

## Portfolio Presentation Tips

### README Structure
1. Problem statement (why this matters)
2. Solution overview (high-level architecture)
3. Key features (what it does)
4. Tech stack (tools used)
5. Demo (screenshots, GIF, or video link)
6. Setup instructions (how to run locally)
7. Sample output (example alerts with explanations)
8. Architecture diagram
9. Future improvements

### What Recruiters Want to See
- **Real-world relevance**: Connects to actual finance problems
- **Technical depth**: Not just API calls - shows ML/NLP understanding
- **System design**: Architecture decisions, tradeoffs
- **Data engineering**: Pipelines, storage, processing at scale
- **LLM proficiency**: RAG, prompt engineering, evaluation
- **Polish**: Clean code, documentation, live demo

### GitHub Organization
- Clear directory structure
- Comprehensive .gitignore
- Requirements with versions
- Docker setup for reproducibility
- Jupyter notebooks showing exploratory analysis
- Unit test coverage
- CI/CD (optional but impressive)

## Recommended Tools & Libraries

```python
# requirements.txt
# Core
python==3.11
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Data processing
pandas==2.1.3
numpy==1.26.2
beautifulsoup4==4.12.2
requests==2.31.0
httpx==0.25.2
scrapy==2.11.0
playwright==1.40.0

# NLP/ML
transformers==4.36.0
torch==2.1.1
spacy==3.7.2
sentence-transformers==2.2.2
scikit-learn==1.3.2

# LLM/RAG
openai==1.3.7
anthropic==0.7.7
langchain==0.0.340
langchain-community==0.0.3
llama-index==0.9.15

# Vector DB
qdrant-client==1.7.0
pgvector==0.2.3

# Orchestration
apache-airflow==2.7.3
prefect==2.14.9

# Dashboard
streamlit==1.28.2
plotly==5.18.0
dash==2.14.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Utilities
python-dotenv==1.0.0
pydantic-settings==2.1.0
loguru==0.7.2
```

## Next Steps

1. **Set up development environment**
   - Install Python 3.11+
   - Create virtual environment
   - Install dependencies
   - Configure PostgreSQL locally

2. **Initialize project structure**
   - Create directory tree
   - Set up git repository
   - Initialize database with schema
   - Create .env from template

3. **Start with Phase 1 (Data Collection)**
   - Register for NewsAPI key
   - Write first collector script
   - Test with 5-10 companies
   - Verify data storage

4. **Iterate weekly through phases**
   - Follow the 8-week timeline
   - Commit frequently with clear messages
   - Document learnings in notebooks
   - Test each component before moving on

## Questions to Consider

- **Scale**: How many obligors will you monitor? (Start with 20-50)
- **Update frequency**: Real-time, hourly, or daily? (Daily for MVP)
- **LLM provider**: OpenAI (easy), Anthropic (longer context), or local (cost-effective)?
- **Vector DB**: Cloud (Qdrant Cloud, Pinecone) or self-hosted?
- **Deployment target**: Just demo or actually hosted?

---

**Remember**: This is an ambitious project. Focus on getting a working end-to-end pipeline first, then iterate on quality. A simple but complete system is better than a complex but half-finished one.

For any questions about implementation details, architecture decisions, or debugging, ask Claude Code in this project directory and this configuration will provide context.
