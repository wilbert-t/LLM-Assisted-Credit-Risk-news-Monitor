# Contributing

## Development Setup

```bash
git clone https://github.com/wilbert-t/LLM-Assisted-Credit-Risk-news-Monitor.git
cd LLM-Assisted-Credit-Risk-news-Monitor
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env   # add your NEWSAPI_KEY
docker-compose up -d
python -m src.db.connection
```

## Running Tests

```bash
# Unit tests
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=src --cov-report=term-missing

# Single file
pytest tests/unit/test_storage.py -v
```

Tests use a separate `credit_risk_test` database. Create it once:

```bash
docker exec <postgres-container> psql -U postgres -c "CREATE DATABASE credit_risk_test;"
```

## Code Style

This project uses **ruff** for linting. Run before committing:

```bash
ruff check src/ tests/
```

Follow PEP 8. Key rules enforced by ruff:
- Max line length: 100 characters
- No unused imports
- No bare `except:` clauses

## Commit Message Format

```
<Type>: <short summary> (<scope>)

Types: Feature | Fix | Test | Docs | Refactor | Chore
```

Examples:
```
Feature: NewsAPI collector with retry and rate limit handling
Fix: datetime.utcnow() deprecation in Python 3.12
Test: unit tests for storage module (12 tests)
Docs: README quick start and week-by-week progress
```

## Before Pushing

- [ ] `pytest tests/unit` — all tests pass
- [ ] `ruff check src/ tests/` — no lint errors
- [ ] No secrets or API keys in code (use `.env`)
- [ ] New behaviour is tested
- [ ] Session log updated if it was a full work session
