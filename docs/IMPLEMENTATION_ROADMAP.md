# Credit Risk Monitor - Implementation Roadmap

## Week-by-Week Task Breakdown

### Week 1-2: Foundation & Data Collection

#### Week 1: Environment Setup
**Goal**: Get development environment ready

**Day 1-2: Local Setup**
- [ ] Install Python 3.11+ and create virtual environment
- [ ] Install PostgreSQL locally (or use Docker)
- [ ] Set up VSCode/PyCharm with Python extensions
- [ ] Install Claude Code CLI
- [ ] Create GitHub repository

**Day 3-4: Project Structure**
- [ ] Initialize project directory structure
- [ ] Create `requirements.txt` with initial dependencies
- [ ] Set up `.env` file management with python-dotenv
- [ ] Initialize git and create .gitignore
- [ ] Write initial README.md

**Day 5-7: Database Setup**
- [ ] Design initial database schema (articles, obligors tables)
- [ ] Create SQLAlchemy models
- [ ] Set up Alembic for migrations
- [ ] Write first migration (create tables)
- [ ] Test database connection and basic CRUD operations
- [ ] Create seed data with 20-50 obligor companies

#### Week 2: Data Collection
**Goal**: Reliable news ingestion

**Day 1-2: News API Integration**
- [ ] Sign up for NewsAPI (free tier)
- [ ] Write `src/collectors/news_api.py` module
- [ ] Implement fetching articles by company name/ticker
- [ ] Add rate limiting and error handling
- [ ] Store raw responses in database

**Day 3-4: Data Storage**
- [ ] Create `Article` database model
- [ ] Implement deduplication logic (by URL)
- [ ] Add batch insert functionality
- [ ] Write unit tests for storage operations
- [ ] Test with 100-200 sample articles

**Day 5-6: Basic Scraper (Optional)**
- [ ] Choose one target website (e.g., Reuters, Bloomberg free content)
- [ ] Write BeautifulSoup scraper
- [ ] Handle pagination
- [ ] Add polite delays and user-agent
- [ ] Test and compare with API data

**Day 7: Pipeline Orchestration**
- [ ] Create simple Python script to run collection
- [ ] Set up logging with loguru
- [ ] Add command-line arguments (date range, companies)
- [ ] Document how to run manually
- [ ] Test full collection for your portfolio

**Deliverable**: 1000+ articles stored in database for 20-50 companies

---

### Week 3: Text Processing & NER

#### Day 1-2: Text Cleaning
**Goal**: Clean and normalize article text

- [ ] Create `src/processors/cleaner.py`
- [ ] Implement HTML removal
- [ ] Fix encoding issues (UTF-8 normalization)
- [ ] Remove boilerplate (disclaimers, ads)
- [ ] Handle special characters and formatting
- [ ] Write unit tests with edge cases

**Code Starter**:
```python
import re
from bs4 import BeautifulSoup

def clean_article_text(html_content: str) -> str:
    """Remove HTML and normalize text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    # Remove multiple whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    
    return text.strip()
```

#### Day 3-4: Named Entity Recognition
**Goal**: Extract companies and tickers

- [ ] Install spaCy and download model (`python -m spacy download en_core_web_lg`)
- [ ] Create `src/processors/ner_extractor.py`
- [ ] Extract ORG entities from text
- [ ] Create custom dictionary for tickers
- [ ] Implement fuzzy matching to obligor list
- [ ] Handle ambiguous names (Apple Inc. vs Apple Computers)

**Code Starter**:
```python
import spacy
from typing import List, Dict

nlp = spacy.load("en_core_web_lg")

def extract_companies(text: str) -> List[Dict]:
    """Extract organization entities."""
    doc = nlp(text)
    companies = []
    
    for ent in doc.ents:
        if ent.label_ == "ORG":
            companies.append({
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char
            })
    
    return companies
```

#### Day 5-6: Entity Mapping
**Goal**: Link extracted entities to obligor database

- [ ] Create `src/processors/entity_mapper.py`
- [ ] Implement string similarity matching (fuzzy)
- [ ] Build lookup table with aliases (e.g., "AAPL" → Apple Inc.)
- [ ] Add validation rules
- [ ] Create `article_obligors` mapping table
- [ ] Test accuracy on sample articles

**Evaluation**:
- Manually label 100 articles with correct companies
- Measure precision/recall of your entity extraction
- Target: >80% precision, >70% recall

#### Day 7: Language Detection & Pipeline Integration
**Goal**: Filter non-English content and integrate processing

- [ ] Add language detection with `langdetect`
- [ ] Create `ProcessedArticle` model
- [ ] Write `src/processors/pipeline.py` to orchestrate all steps
- [ ] Add error handling and logging
- [ ] Process all collected articles
- [ ] Save results to `processed_articles` table

**Deliverable**: Processed articles with clean text, extracted entities, and obligor mappings

---

### Week 4: Sentiment Analysis & Risk Classification

#### Day 1-2: Sentiment Analysis
**Goal**: Score article sentiment with FinBERT

- [ ] Install transformers and pytorch
- [ ] Download FinBERT model from Hugging Face
- [ ] Create `src/models/sentiment.py`
- [ ] Write sentiment scoring function
- [ ] Batch process for efficiency
- [ ] Store scores in database

**Code Starter**:
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class FinBERTSentiment:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    
    def predict(self, text: str) -> dict:
        """Return sentiment scores."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        return {
            "positive": probs[0][0].item(),
            "negative": probs[0][1].item(),
            "neutral": probs[0][2].item()
        }
```

#### Day 3-4: Credit-Relevance Classification
**Goal**: Identify credit-relevant articles

**Approach 1: Rule-based**
- [ ] Define keyword lists for credit events
- [ ] Keywords: downgrade, default, bankruptcy, restructuring, covenant breach, liquidity
- [ ] Create `src/models/classifier.py`
- [ ] Implement keyword matching with scoring
- [ ] Test on labeled samples

**Approach 2: LLM-enhanced (time permitting)**
- [ ] Set up OpenAI API client
- [ ] Create prompt for classification
- [ ] Implement zero-shot classification
- [ ] Add caching to reduce costs
- [ ] Compare with keyword approach

**Deliverable**: Every article has:
- Sentiment score (positive/negative/neutral)
- Credit-relevance flag (boolean)
- Confidence score

#### Day 5-6: Event Type Classification
**Goal**: Categorize event types

- [ ] Define event taxonomy:
  - Downgrade
  - Default/Bankruptcy
  - Lawsuit/Legal
  - Fraud/Governance
  - M&A/Restructuring
  - Liquidity Issues
  - Earnings Miss
  - Management Change
- [ ] Create multi-label classification logic
- [ ] Use keywords + LLM for accuracy
- [ ] Store as array in database

#### Day 7: Aggregation & Testing
**Goal**: Create time-series signals

- [ ] Create `obligor_daily_signals` table
- [ ] Write aggregation queries (pandas groupby)
- [ ] Calculate rolling windows (7-day, 30-day)
- [ ] Visualize sentiment trends in Jupyter notebook
- [ ] Validate aggregates look reasonable

**SQL Query Example**:
```sql
SELECT 
    o.name,
    DATE(a.published_at) as date,
    COUNT(*) as article_count,
    AVG(pa.sentiment_score) as avg_sentiment,
    SUM(CASE WHEN pa.is_credit_relevant THEN 1 ELSE 0 END) as relevant_count
FROM articles a
JOIN processed_articles pa ON a.id = pa.article_id
JOIN article_obligors ao ON pa.id = ao.article_id
JOIN obligors o ON ao.obligor_id = o.id
WHERE a.published_at >= NOW() - INTERVAL '30 days'
GROUP BY o.name, DATE(a.published_at)
ORDER BY date DESC, avg_sentiment ASC;
```

**Deliverable**: Daily risk signals for each obligor

---

### Week 5: RAG System Implementation

#### Day 1-2: Vector Database Setup
**Goal**: Store article embeddings

**Option A: Qdrant (Recommended)**
- [ ] Install Qdrant with Docker: `docker run -p 6333:6333 qdrant/qdrant`
- [ ] Install `qdrant-client`
- [ ] Create collection for article chunks
- [ ] Define schema with metadata (date, obligor, sentiment)

**Option B: pgvector**
- [ ] Install pgvector extension in PostgreSQL
- [ ] Create embeddings table with vector column
- [ ] Create HNSW index for similarity search

#### Day 3-4: Embedding Generation
**Goal**: Convert text to vectors

- [ ] Sign up for OpenAI API (or use sentence-transformers locally)
- [ ] Create `src/models/embeddings.py`
- [ ] Implement chunking strategy (500-token paragraphs)
- [ ] Generate embeddings in batches
- [ ] Store in vector database with metadata
- [ ] Add indexing for performance

**Code Starter**:
```python
from openai import OpenAI
from typing import List

client = OpenAI()

def get_embeddings(texts: List[str], model="text-embedding-3-small") -> List[List[float]]:
    """Generate embeddings for text list."""
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]

def chunk_article(text: str, chunk_size: int = 500) -> List[str]:
    """Split article into overlapping chunks."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - 50):  # 50-word overlap
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk.split()) > 100:  # minimum chunk size
            chunks.append(chunk)
    
    return chunks
```

#### Day 5-6: RAG Retrieval System
**Goal**: Semantic search for relevant articles

- [ ] Create `src/rag/retriever.py`
- [ ] Implement similarity search function
- [ ] Add filters (date range, obligor, sentiment)
- [ ] Test retrieval quality with sample queries
- [ ] Implement re-ranking if needed
- [ ] Add hybrid search (semantic + keyword) if time permits

**Code Starter**:
```python
from qdrant_client import QdrantClient

class ArticleRetriever:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "article_chunks"
    
    def search(
        self, 
        query_embedding: List[float],
        obligor_id: int,
        limit: int = 10,
        date_from: Optional[datetime] = None
    ) -> List[dict]:
        """Search for relevant article chunks."""
        filters = {
            "must": [
                {"key": "obligor_id", "match": {"value": obligor_id}}
            ]
        }
        
        if date_from:
            filters["must"].append({
                "key": "published_at",
                "range": {"gte": date_from.isoformat()}
            })
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=filters,
            limit=limit
        )
        
        return results
```

#### Day 7: LLM Summarization
**Goal**: Generate credit-focused summaries

- [ ] Create `src/rag/summarizer.py`
- [ ] Design prompt template for risk summaries
- [ ] Implement few-shot examples in prompt
- [ ] Request structured JSON output
- [ ] Add error handling and retries
- [ ] Test with 5-10 companies
- [ ] Validate summaries are factual (no hallucinations)

**Prompt Template**:
```python
SYSTEM_PROMPT = """You are a credit risk analyst. Analyze news articles about a company and provide a concise risk assessment.

Focus on:
- Credit-relevant events (defaults, downgrades, liquidity issues, lawsuits, fraud)
- Potential impact on creditworthiness
- Specific facts and dates

Always:
- Be factual and cite specific details from articles
- Distinguish between confirmed events and speculation
- Note if information is incomplete

Output format (JSON):
{
  "company": "Company Name",
  "summary": "2-3 sentence overview",
  "key_events": [
    {"type": "downgrade", "description": "...", "date": "YYYY-MM-DD", "severity": "high"}
  ],
  "risk_assessment": {
    "overall_risk": "low|medium|high|critical",
    "key_concerns": ["concern 1", "concern 2"],
    "positive_factors": ["factor 1"]
  }
}
"""

USER_PROMPT = """Analyze the following recent news articles about {company_name}:

{articles}

Provide a credit risk assessment in JSON format."""
```

**Deliverable**: RAG system that can answer "Summarize risk signals for Company X in the last 7 days"

---

### Week 6: Alert System & API Backend

#### Day 1-2: Alert Rule Engine
**Goal**: Define when to generate alerts

- [ ] Create `src/alerts/rules.py`
- [ ] Define alert severity levels (low, medium, high, critical)
- [ ] Implement threshold-based rules:
  - Sentiment drop > 20% in 7 days
  - 3+ credit-relevant articles in 24 hours
  - High-severity event detected by LLM
  - Specific keywords (default, bankruptcy)
- [ ] Add rule combination logic
- [ ] Test rules on historical data

**Code Starter**:
```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class AlertRule:
    name: str
    severity: str
    condition: callable

class AlertEngine:
    def __init__(self):
        self.rules = [
            AlertRule(
                name="sentiment_drop",
                severity="medium",
                condition=lambda signals: self._check_sentiment_drop(signals)
            ),
            AlertRule(
                name="high_negative_volume",
                severity="high",
                condition=lambda signals: signals['negative_count'] >= 3
            )
        ]
    
    def _check_sentiment_drop(self, signals: dict) -> bool:
        """Check if sentiment dropped significantly."""
        current = signals['current_sentiment']
        previous = signals['previous_sentiment']
        return (previous - current) > 0.2 and current < -0.3
    
    def evaluate(self, obligor_id: int, date: datetime) -> List[dict]:
        """Evaluate all rules and return triggered alerts."""
        signals = self.get_signals(obligor_id, date)
        alerts = []
        
        for rule in self.rules:
            if rule.condition(signals):
                alerts.append({
                    "rule": rule.name,
                    "severity": rule.severity,
                    "timestamp": datetime.now()
                })
        
        return alerts
```

#### Day 3-4: Alert Generation
**Goal**: Automated alert creation

- [ ] Create `src/alerts/generator.py`
- [ ] Implement scheduled alert check function
- [ ] Retrieve relevant context from RAG
- [ ] Generate alert with LLM summary
- [ ] Store in alerts table
- [ ] Add deduplication (don't repeat same alert)
- [ ] Write tests for alert logic

#### Day 5-6: FastAPI Backend
**Goal**: REST API for frontend

- [ ] Create `src/api/main.py`
- [ ] Set up FastAPI application
- [ ] Define Pydantic schemas for requests/responses
- [ ] Implement endpoints:
  - `GET /api/obligors` - List all companies
  - `GET /api/obligors/{id}` - Company details
  - `GET /api/obligors/{id}/signals` - Time-series signals
  - `GET /api/obligors/{id}/summary` - RAG summary
  - `GET /api/alerts` - List alerts (with filters)
  - `GET /api/alerts/{id}` - Alert details
  - `POST /api/alerts/{id}/acknowledge` - Mark as read
- [ ] Add authentication (simple API key)
- [ ] Test with curl/Postman

**Code Starter**:
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

app = FastAPI(title="Credit Risk Monitor API")

class ObligorResponse(BaseModel):
    id: int
    name: str
    ticker: str
    current_risk_score: float
    latest_alert: Optional[str]

class AlertResponse(BaseModel):
    id: int
    obligor_id: int
    severity: str
    summary: str
    timestamp: datetime
    event_types: List[str]

@app.get("/api/obligors", response_model=List[ObligorResponse])
async def list_obligors():
    """Get list of monitored obligors."""
    # Query database
    pass

@app.get("/api/obligors/{obligor_id}/summary")
async def get_summary(
    obligor_id: int,
    days: int = 7
):
    """Get RAG-generated risk summary."""
    # Retrieve articles from last N days
    # Generate summary with RAG
    pass

@app.get("/api/alerts", response_model=List[AlertResponse])
async def list_alerts(
    severity: Optional[str] = None,
    date_from: Optional[date] = None,
    acknowledged: bool = False
):
    """List alerts with optional filters."""
    # Query alerts table
    pass
```

#### Day 7: Scheduled Alert Job
**Goal**: Automation

- [ ] Create `src/alerts/scheduler.py`
- [ ] Implement cron-like scheduler with APScheduler
- [ ] Run alert checks every 6 hours
- [ ] Add error notification (email on failure)
- [ ] Log all alert generations
- [ ] Test scheduling locally

**Deliverable**: API endpoints + automated alert generation

---

### Week 7: Dashboard Development

#### Day 1-2: Streamlit Setup & Layout
**Goal**: Basic dashboard structure

- [ ] Create `dashboard/app.py`
- [ ] Set up Streamlit configuration
- [ ] Design page layout:
  - Sidebar: filters (date range, sector, severity)
  - Main: portfolio overview table
  - Secondary: charts and drill-downs
- [ ] Connect to PostgreSQL database
- [ ] Test data fetching

#### Day 3-4: Portfolio Overview
**Goal**: Main dashboard view

- [ ] Create portfolio table with columns:
  - Obligor name
  - Current risk score
  - 7-day sentiment trend (sparkline)
  - Alert count (by severity)
  - Latest event
- [ ] Add sortable columns
- [ ] Color-code by risk level
- [ ] Implement row click → drill-down

**Code Starter**:
```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Credit Risk Monitor", layout="wide")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    date_range = st.date_input("Date Range", [])
    severity = st.multiselect("Alert Severity", ["low", "medium", "high", "critical"])
    sector = st.multiselect("Sector", get_sectors())

# Main dashboard
st.title("Portfolio Risk Monitor")

# Fetch data
df_obligors = get_portfolio_data(date_range, severity, sector)

# Display table
st.dataframe(
    df_obligors,
    column_config={
        "risk_score": st.column_config.ProgressColumn(
            "Risk Score",
            min_value=0,
            max_value=100
        ),
        "sentiment_trend": st.column_config.LineChartColumn(
            "7-Day Trend"
        )
    },
    hide_index=True,
    use_container_width=True
)
```

#### Day 5-6: Drill-Down Pages
**Goal**: Company-specific analysis

- [ ] Create obligor detail page
- [ ] Show:
  - Company info header
  - Risk timeline chart (sentiment over time)
  - Alert history table
  - Recent articles list
  - LLM-generated summary card
- [ ] Add interactive Plotly charts
- [ ] Include links to source articles

#### Day 7: Polish & Testing
**Goal**: Production-ready dashboard

- [ ] Add loading spinners
- [ ] Implement caching (`@st.cache_data`)
- [ ] Error handling for missing data
- [ ] Responsive design testing
- [ ] Add export functionality (CSV download)
- [ ] Write usage documentation

**Deliverable**: Interactive dashboard accessible at localhost:8501

---

### Week 8: Documentation, Deployment & Polish

#### Day 1-2: Documentation
**Goal**: Comprehensive project docs

- [ ] Write detailed README.md:
  - Problem statement
  - Solution overview
  - Tech stack
  - Setup instructions
  - Usage examples
  - Screenshots/GIFs
- [ ] Create architecture diagram (draw.io, Excalidraw)
- [ ] Document API endpoints (OpenAPI/Swagger)
- [ ] Write CONTRIBUTING.md
- [ ] Add code comments and docstrings

#### Day 3-4: Containerization
**Goal**: Docker setup

- [ ] Create Dockerfile for API
- [ ] Create Dockerfile for dashboard
- [ ] Write docker-compose.yml with services:
  - PostgreSQL
  - Qdrant
  - API
  - Dashboard
  - Worker (for alert jobs)
- [ ] Test full stack with Docker
- [ ] Document Docker setup

#### Day 5-6: Deployment
**Goal**: Live demo

**Option 1: Render (Recommended)**
- [ ] Create Render account
- [ ] Deploy PostgreSQL database
- [ ] Deploy API as Web Service
- [ ] Deploy dashboard as Web Service
- [ ] Set environment variables
- [ ] Test live deployment

**Option 2: Railway**
- Similar steps to Render
- Connect GitHub repo for auto-deploy

#### Day 7: Demo & Evaluation
**Goal**: Portfolio presentation

- [ ] Record demo video (5-10 minutes):
  - Problem explanation
  - System walkthrough
  - Live demo of dashboard
  - Code highlights
  - Results and impact
- [ ] Create evaluation notebook:
  - Sentiment analysis accuracy
  - NER precision/recall
  - Alert quality metrics
  - Sample alerts with explanations
- [ ] Final README polish
- [ ] Prepare for presentations/interviews

**Deliverable**: Complete, deployed, documented portfolio project

---

## Success Metrics

### Technical Metrics
- [ ] 1000+ articles collected
- [ ] >80% precision on company extraction
- [ ] Sentiment scores correlate with known events
- [ ] <2 second API response time
- [ ] Dashboard loads in <5 seconds

### Portfolio Impact
- [ ] Clear README with problem/solution
- [ ] Live demo available
- [ ] Clean, commented code
- [ ] Test coverage >60%
- [ ] Professional architecture diagram
- [ ] Example alerts show real insights

## Common Issues & Solutions

### Issue: NewsAPI rate limits
**Solution**: Implement exponential backoff, cache responses, or use multiple API keys

### Issue: Entity extraction too noisy
**Solution**: Add manual curation for top 50 obligors, use LEI/ticker databases

### Issue: LLM costs too high
**Solution**: Cache results, use smaller models for classification, batch requests

### Issue: Slow embeddings generation
**Solution**: Use sentence-transformers locally, batch processing, or smaller embedding models

### Issue: Dashboard crashes with large data
**Solution**: Implement pagination, data sampling, caching, and lazy loading

---

## Optional Enhancements (If Time Permits)

### Advanced Features
- [ ] Knowledge graph visualization of company relationships
- [ ] Sector-level risk aggregation
- [ ] Email/Slack notifications for critical alerts
- [ ] Historical backtesting of alert accuracy
- [ ] Multi-language support (translate non-English)
- [ ] Real-time streaming with Kafka
- [ ] A/B testing of different LLM prompts

### ML Improvements
- [ ] Fine-tune FinBERT on your labeled data
- [ ] Train custom NER model for financial entities
- [ ] Build risk scoring model (predict defaults)
- [ ] Implement active learning for classification
- [ ] Add explainability (SHAP values for predictions)

Remember: **Done is better than perfect**. Aim for a working MVP first, then iterate based on feedback and learning.
