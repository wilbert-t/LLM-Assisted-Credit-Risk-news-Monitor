# Quick Start Guide - Credit Risk Monitor

## Overview

This guide will help you set up your development environment and start building the credit risk monitoring system in ~30 minutes.

## Prerequisites

- Python 3.11+ installed
- PostgreSQL 14+ (or Docker)
- Git installed
- OpenAI API key (optional, for Week 5+)
- Claude Code CLI installed

## Step 1: Initial Setup (10 minutes)

### 1.1 Create Project Directory

```bash
# Create main project directory
mkdir credit-risk-monitor
cd credit-risk-monitor

# Initialize git
git init

# Create .claude directory
mkdir -p .claude

# Copy the claude.md file into .claude/
# (This file provides context to Claude Code)
```

### 1.2 Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 1.3 Install Core Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
# Core
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
python-dotenv==1.0.0

# Data processing
pandas==2.1.3
requests==2.31.0
beautifulsoup4==4.12.2

# NLP (Week 3+)
# spacy==3.7.2
# transformers==4.36.0

# Dashboard (Week 7+)
# streamlit==1.28.2
# plotly==5.18.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
EOF

# Install
pip install -r requirements.txt
```

## Step 2: Database Setup (10 minutes)

### Option A: PostgreSQL with Docker (Recommended)

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: credit_risk
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

# Start PostgreSQL
docker-compose up -d

# Verify it's running
docker-compose ps
```

### Option B: Local PostgreSQL Installation

```bash
# On macOS
brew install postgresql@15
brew services start postgresql@15

# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
createdb credit_risk
```

### 2.2 Test Database Connection

```python
# test_db.py
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/credit_risk"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        print("Database connected:", result.fetchone())
except Exception as e:
    print(f"Connection failed: {e}")
```

Run: `python test_db.py`

## Step 3: Project Structure (5 minutes)

```bash
# Create directory structure
mkdir -p src/{collectors,processors,models,rag,alerts,api,db,utils}
mkdir -p dashboard/{components,pages}
mkdir -p notebooks
mkdir -p tests/{unit,integration}
mkdir -p infra/{docker,migrations}
mkdir -p data/{raw,processed,embeddings}
mkdir -p docs

# Create __init__.py files
touch src/__init__.py
touch src/{collectors,processors,models,rag,alerts,api,db,utils}/__init__.py

# Create basic files
touch src/utils/config.py
touch src/utils/logger.py
touch src/db/models.py
touch src/db/connection.py
```

## Step 4: Configuration (5 minutes)

### 4.1 Create .env File

```bash
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/credit_risk

# APIs (add keys when ready)
NEWSAPI_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF
```

### 4.2 Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Data
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Jupyter
.ipynb_checkpoints/
*.ipynb

# OS
.DS_Store
Thumbs.db
EOF

# Create .gitkeep files
touch data/raw/.gitkeep data/processed/.gitkeep
```

### 4.3 Set Up Logging

```python
# src/utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "credit-risk-monitor") -> logging.Logger:
    """Set up application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(console_handler)
    
    return logger

# Usage
# from src.utils.logger import setup_logger
# logger = setup_logger()
# logger.info("Starting application...")
```

### 4.4 Set Up Configuration

```python
# src/utils/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str
    
    # APIs
    newsapi_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Application
    log_level: str = "INFO"
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton
settings = Settings()

# Usage
# from src.utils.config import settings
# db_url = settings.database_url
```

## Step 5: Database Models (Week 1)

```python
# src/db/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Article(Base):
    """Raw article from news sources."""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    source = Column(String(100))
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, server_default=func.now())
    language = Column(String(10))
    raw_json = Column(JSON)

class Obligor(Base):
    """Company being monitored."""
    __tablename__ = "obligors"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    ticker = Column(String(20))
    lei = Column(String(20))  # Legal Entity Identifier
    sector = Column(String(100))
    country = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

class ProcessedArticle(Base):
    """Processed and analyzed articles."""
    __tablename__ = "processed_articles"
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, nullable=False)  # FK to articles
    cleaned_text = Column(Text)
    entities = Column(JSON)  # Extracted companies/tickers
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    is_credit_relevant = Column(Boolean)
    event_types = Column(ARRAY(String))
    processed_at = Column(DateTime, server_default=func.now())
```

```python
# src/db/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.config import settings
from src.db.models import Base

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Run once to create tables
if __name__ == "__main__":
    init_db()
    print("Database initialized!")
```

Run: `python src/db/connection.py`

## Step 6: First News Collector (Week 1-2)

### 6.1 Sign Up for NewsAPI

1. Go to https://newsapi.org/
2. Sign up for free account
3. Get API key
4. Add to .env: `NEWSAPI_KEY=your_actual_key`

### 6.2 Create Simple Collector

```python
# src/collectors/news_api.py
import requests
from typing import List, Dict
from datetime import datetime, timedelta
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger()

class NewsAPICollector:
    """Collect news from NewsAPI."""
    
    def __init__(self):
        self.api_key = settings.newsapi_key
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_news(
        self, 
        query: str, 
        from_date: datetime = None,
        page_size: int = 100
    ) -> List[Dict]:
        """Fetch news articles for a query."""
        
        if from_date is None:
            from_date = datetime.now() - timedelta(days=7)
        
        params = {
            "q": query,
            "from": from_date.strftime("%Y-%m-%d"),
            "pageSize": page_size,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "ok":
                logger.info(f"Fetched {len(data['articles'])} articles for '{query}'")
                return data["articles"]
            else:
                logger.error(f"API error: {data.get('message')}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return []

# Test script
if __name__ == "__main__":
    collector = NewsAPICollector()
    
    # Test with one company
    articles = collector.fetch_news("Apple Inc.")
    
    print(f"Found {len(articles)} articles")
    if articles:
        print("\nFirst article:")
        print(f"Title: {articles[0]['title']}")
        print(f"Source: {articles[0]['source']['name']}")
        print(f"Published: {articles[0]['publishedAt']}")
```

Run: `python src/collectors/news_api.py`

### 6.3 Store Articles in Database

```python
# src/collectors/storage.py
from sqlalchemy.dialects.postgresql import insert
from src.db.models import Article
from src.db.connection import SessionLocal
from src.utils.logger import setup_logger

logger = setup_logger()

def store_articles(articles: List[Dict]) -> int:
    """Store articles in database with deduplication."""
    db = SessionLocal()
    stored_count = 0
    
    try:
        for article in articles:
            # Skip if no URL
            if not article.get("url"):
                continue
            
            # Prepare data
            article_data = {
                "title": article.get("title", ""),
                "content": article.get("content") or article.get("description", ""),
                "url": article["url"],
                "source": article.get("source", {}).get("name"),
                "published_at": article.get("publishedAt"),
                "raw_json": article
            }
            
            # Insert or ignore if URL exists
            stmt = insert(Article).values(**article_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
            
            result = db.execute(stmt)
            db.commit()
            
            if result.rowcount > 0:
                stored_count += 1
        
        logger.info(f"Stored {stored_count} new articles")
        return stored_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Storage failed: {e}")
        return 0
    finally:
        db.close()
```

## Step 7: Seed Data & Initial Test (Final Setup)

### 7.1 Create Obligor List

```python
# scripts/seed_obligors.py
from src.db.models import Obligor
from src.db.connection import SessionLocal

# Sample companies (expand this list)
COMPANIES = [
    {"name": "Apple Inc.", "ticker": "AAPL", "sector": "Technology"},
    {"name": "Microsoft Corporation", "ticker": "MSFT", "sector": "Technology"},
    {"name": "JPMorgan Chase", "ticker": "JPM", "sector": "Banking"},
    {"name": "Goldman Sachs", "ticker": "GS", "sector": "Banking"},
    {"name": "Tesla Inc.", "ticker": "TSLA", "sector": "Automotive"},
    {"name": "Amazon.com Inc.", "ticker": "AMZN", "sector": "E-commerce"},
    {"name": "Netflix Inc.", "ticker": "NFLX", "sector": "Media"},
    {"name": "Boeing Company", "ticker": "BA", "sector": "Aerospace"},
    {"name": "Exxon Mobil", "ticker": "XOM", "sector": "Energy"},
    {"name": "Pfizer Inc.", "ticker": "PFE", "sector": "Pharmaceuticals"},
]

def seed_obligors():
    """Add obligors to database."""
    db = SessionLocal()
    
    for company in COMPANIES:
        obligor = Obligor(**company)
        db.add(obligor)
    
    db.commit()
    db.close()
    print(f"Seeded {len(COMPANIES)} obligors")

if __name__ == "__main__":
    seed_obligors()
```

Run: `python scripts/seed_obligors.py`

### 7.2 Collect Initial Data

```python
# scripts/collect_initial_data.py
from src.collectors.news_api import NewsAPICollector
from src.collectors.storage import store_articles
from src.db.models import Obligor
from src.db.connection import SessionLocal

def collect_for_all_obligors():
    """Collect news for all obligors."""
    collector = NewsAPICollector()
    db = SessionLocal()
    
    obligors = db.query(Obligor).all()
    total_articles = 0
    
    for obligor in obligors:
        print(f"\nCollecting for {obligor.name}...")
        
        # Search by name
        articles = collector.fetch_news(obligor.name)
        count = store_articles(articles)
        total_articles += count
        
        print(f"Stored {count} articles")
    
    db.close()
    print(f"\n✓ Total: {total_articles} articles collected")

if __name__ == "__main__":
    collect_for_all_obligors()
```

Run: `python scripts/collect_initial_data.py`

### 7.3 Verify Data

```python
# scripts/verify_data.py
from src.db.connection import SessionLocal
from src.db.models import Article, Obligor

db = SessionLocal()

# Count articles
article_count = db.query(Article).count()
print(f"Articles in database: {article_count}")

# Count obligors
obligor_count = db.query(Obligor).count()
print(f"Obligors in database: {obligor_count}")

# Show sample
if article_count > 0:
    sample = db.query(Article).first()
    print(f"\nSample article:")
    print(f"Title: {sample.title}")
    print(f"URL: {sample.url}")
    print(f"Published: {sample.published_at}")

db.close()
```

Run: `python scripts/verify_data.py`

## Next Steps

You're now ready to start Week 1 development! 

### Week 1 Tasks:
1. ✅ Environment set up
2. ✅ Database initialized
3. ✅ Basic news collector working
4. ✅ Initial data collected

### Week 2: Focus on
- Refining collection logic
- Adding more data sources
- Building scheduling system
- Improving data quality

### Getting Help from Claude Code

Now that `.claude/claude.md` is set up, you can ask Claude Code questions like:

```bash
# In your project directory
claude-code "How do I implement deduplication for articles?"
claude-code "Show me how to add sentiment analysis with FinBERT"
claude-code "Help me debug this database connection issue"
claude-code "Create a unit test for the NewsAPI collector"
```

Claude will have full context about your project architecture, tech stack, and current phase.

## Troubleshooting

### Issue: Database connection fails
**Solution**: Check if PostgreSQL is running: `docker-compose ps` or `pg_isready`

### Issue: NewsAPI returns 401
**Solution**: Verify API key in .env file is correct

### Issue: Import errors
**Solution**: Make sure virtual environment is activated and all dependencies installed

### Issue: No articles collected
**Solution**: Check if NewsAPI has free tier limits, try with fewer obligors first

## Resources

- Project documentation: `docs/`
- Implementation roadmap: `IMPLEMENTATION_ROADMAP.md`
- Full architecture: `.claude/claude.md`
- Weekly tasks: See roadmap for detailed breakdown

---

**Congratulations! Your project is set up and ready for development.** 🚀

Follow the IMPLEMENTATION_ROADMAP.md for week-by-week tasks.
