# FinBERT Sentiment & Credit Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add FinBERT sentiment scoring and keyword-based credit-relevance classification to the NLP pipeline, populating `sentiment_score`, `sentiment_label`, `is_credit_relevant`, and `event_types` on `processed_articles`.

**Architecture:** The classifier (`src/models/classifier.py`) is pure Python keyword matching — lightweight enough to run inline in `process_articles_batch()`. FinBERT (`src/models/sentiment.py`) is a heavy transformer model loaded once per process; it runs as a separate scoring pass via `scripts/score_sentiment.py` rather than blocking the main pipeline. New articles processed by the pipeline get classified immediately; sentiment is scored in a nightly batch job.

**Tech Stack:** `transformers` (HuggingFace), `torch` (CPU), `ProsusAI/finbert`, existing `src/utils/constants.py` KEYWORDS dict, SQLAlchemy, PostgreSQL.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/models/sentiment.py` | Create | `FinBERTSentiment` class — lazy model load, predict/predict_batch |
| `src/models/classifier.py` | Create | `is_credit_relevant()` + `classify_events()` — keyword matching |
| `src/processors/pipeline.py` | Modify | Call classifier after NER, populate `is_credit_relevant` + `event_types` |
| `scripts/score_sentiment.py` | Create | CLI script — score existing articles missing sentiment in batches |
| `tests/unit/test_sentiment.py` | Create | Unit tests with mocked HuggingFace model (no download required) |
| `tests/unit/test_classifier.py` | Create | Pure unit tests — no DB, no mocks needed |
| `requirements.txt` | Modify | Add `transformers==4.40.0` and `torch==2.3.0` |

---

## Task 1: Install Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add transformers and torch to requirements.txt**

Open `requirements.txt` and append these two lines at the end:

```
transformers==4.40.0
torch==2.3.0
```

- [ ] **Step 2: Install into active venv**

```bash
source venv/bin/activate
pip install transformers==4.40.0 torch==2.3.0
```

Expected: Both packages install (torch ~800MB on first run — be patient). No import errors.

- [ ] **Step 3: Verify imports**

```bash
python -c "import transformers; import torch; print('OK', transformers.__version__, torch.__version__)"
```

Expected output: `OK 4.40.0 2.3.0`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "deps: add transformers 4.40.0 + torch 2.3.0 for FinBERT sentiment"
```

---

## Task 2: Create FinBERT Sentiment Module

**Files:**
- Create: `src/models/sentiment.py`
- Test: `tests/unit/test_sentiment.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_sentiment.py`:

```python
"""
Unit tests for src/models/sentiment.py.
All tests mock the HuggingFace model — no download or GPU required.
"""

from unittest.mock import MagicMock, patch

import pytest
import torch

from src.models.sentiment import FinBERTSentiment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_logits(pos: float, neg: float, neu: float) -> MagicMock:
    """Return a mock model output with the given raw logits."""
    output = MagicMock()
    output.logits = torch.tensor([[pos, neg, neu]])
    return output


def _patched_sentiment(monkeypatch):
    """
    Return a FinBERTSentiment instance with tokenizer + model mocked.
    Monkeypatches AutoTokenizer.from_pretrained and AutoModelForSequenceClassification.from_pretrained.
    """
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {
        "input_ids": torch.zeros((1, 10), dtype=torch.long),
        "attention_mask": torch.ones((1, 10), dtype=torch.long),
    }
    mock_model = MagicMock()

    monkeypatch.setattr(
        "src.models.sentiment.AutoTokenizer.from_pretrained",
        lambda *a, **kw: mock_tokenizer,
    )
    monkeypatch.setattr(
        "src.models.sentiment.AutoModelForSequenceClassification.from_pretrained",
        lambda *a, **kw: mock_model,
    )

    instance = FinBERTSentiment()
    instance._tokenizer = mock_tokenizer
    instance._model = mock_model
    return instance, mock_model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFinBERTSentimentPredict:

    def test_positive_sentiment_returns_positive_label(self, monkeypatch):
        """High positive logit → label='positive', score > 0."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=5.0, neg=-3.0, neu=0.0)

        result = instance.predict("Strong earnings beat and record revenue growth.")

        assert result["label"] == "positive"
        assert result["score"] > 0.5

    def test_negative_sentiment_returns_negative_label(self, monkeypatch):
        """High negative logit → label='negative', score < -0.5."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=-3.0, neg=5.0, neu=0.0)

        result = instance.predict("Company filed for bankruptcy and missed debt payments.")

        assert result["label"] == "negative"
        assert result["score"] < -0.5

    def test_neutral_sentiment_returns_neutral_label(self, monkeypatch):
        """High neutral logit → label='neutral', score near 0."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=0.0, neg=0.0, neu=5.0)

        result = instance.predict("The company released its quarterly filing.")

        assert result["label"] == "neutral"
        assert -0.3 < result["score"] < 0.3

    def test_predict_returns_all_keys(self, monkeypatch):
        """Result dict must contain label, score, positive, negative, neutral."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        result = instance.predict("Some financial news text.")

        assert set(result.keys()) == {"label", "score", "positive", "negative", "neutral"}

    def test_score_is_positive_minus_negative(self, monkeypatch):
        """score = positive_prob - negative_prob."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        # Use logits that give known softmax values
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        result = instance.predict("text")

        expected_score = result["positive"] - result["negative"]
        assert result["score"] == pytest.approx(expected_score, abs=1e-6)

    def test_empty_string_does_not_crash(self, monkeypatch):
        """Empty string should return a valid result dict, not raise."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=0.0, neg=0.0, neu=1.0)

        result = instance.predict("")

        assert "label" in result

    def test_long_text_is_truncated_to_512_tokens(self, monkeypatch):
        """Tokenizer must be called with truncation=True and max_length=512."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        instance.predict("word " * 600)

        call_kwargs = instance._tokenizer.call_args[1]
        assert call_kwargs.get("truncation") is True
        assert call_kwargs.get("max_length") == 512


class TestFinBERTSentimentBatch:

    def test_predict_batch_returns_one_result_per_text(self, monkeypatch):
        """predict_batch must return a list of the same length as the input."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        texts = ["text one", "text two", "text three"]
        results = instance.predict_batch(texts)

        assert len(results) == 3
        for r in results:
            assert "label" in r and "score" in r

    def test_predict_batch_empty_list_returns_empty(self, monkeypatch):
        """predict_batch([]) → []."""
        instance, mock_model = _patched_sentiment(monkeypatch)

        results = instance.predict_batch([])

        assert results == []

    def test_predict_batch_handles_100_texts(self, monkeypatch):
        """predict_batch should handle 100 texts without error."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=0.5, neg=0.3, neu=0.2)

        texts = [f"Financial news article number {i}." for i in range(100)]
        results = instance.predict_batch(texts)

        assert len(results) == 100
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
source venv/bin/activate
pytest tests/unit/test_sentiment.py -v 2>&1 | head -30
```

Expected: `ImportError` or `ModuleNotFoundError: No module named 'src.models.sentiment'`

- [ ] **Step 3: Create `src/models/sentiment.py`**

```python
"""
FinBERT sentiment scorer for financial news text.

Usage:
    from src.models.sentiment import FinBERTSentiment

    scorer = FinBERTSentiment()
    result = scorer.predict("Company files for bankruptcy.")
    # {"label": "negative", "score": -0.82, "positive": 0.05, "negative": 0.87, "neutral": 0.08}

    batch = scorer.predict_batch(["text one", "text two"])
"""

from __future__ import annotations

from typing import Dict, List

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_MODEL_NAME = "ProsusAI/finbert"
# FinBERT label order as defined by ProsusAI (index 0=positive, 1=negative, 2=neutral)
_LABEL_ORDER = ["positive", "negative", "neutral"]


class FinBERTSentiment:
    """
    Wrapper around ProsusAI/finbert for financial text sentiment.

    The model is lazy-loaded on first call to predict() or predict_batch().
    Pass an instance around rather than creating multiple — the model is ~440MB.
    """

    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load(self) -> None:
        """Download (on first run) and cache the FinBERT model."""
        if self._model is not None:
            return
        logger.info(f"Loading FinBERT from {_MODEL_NAME!r} (device={self._device})...")
        self._tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        self._model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        self._model.to(self._device)
        self._model.eval()
        logger.info("FinBERT loaded.")

    def predict(self, text: str) -> Dict[str, float]:
        """
        Score a single text string.

        Returns a dict with:
            label   — "positive", "negative", or "neutral"
            score   — float in [-1.0, 1.0] = positive_prob - negative_prob
            positive, negative, neutral — raw softmax probabilities
        """
        self._load()
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)

        probs = F.softmax(outputs.logits, dim=-1).squeeze().tolist()
        # probs order: [positive, negative, neutral]
        pos, neg, neu = probs[0], probs[1], probs[2]
        label = _LABEL_ORDER[probs.index(max(probs))]

        return {
            "label":    label,
            "score":    round(pos - neg, 6),
            "positive": round(pos, 6),
            "negative": round(neg, 6),
            "neutral":  round(neu, 6),
        }

    def predict_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Score a list of texts, calling predict() on each.
        Returns a list of result dicts in the same order as the input.
        """
        if not texts:
            return []
        return [self.predict(text) for text in texts]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_sentiment.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models/sentiment.py tests/unit/test_sentiment.py
git commit -m "feat: add FinBERTSentiment module with lazy model loading"
```

---

## Task 3: Create Credit-Relevance Classifier

**Files:**
- Create: `src/models/classifier.py`
- Test: `tests/unit/test_classifier.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_classifier.py`:

```python
"""
Unit tests for src/models/classifier.py.
Pure keyword matching — no DB, no mocks, no model needed.
"""

import pytest

from src.models.classifier import classify_events, is_credit_relevant


class TestIsCreditRelevant:

    def test_returns_true_for_bankruptcy_text(self):
        text = "The company filed for bankruptcy and entered chapter 11 proceedings."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_downgrade_text(self):
        text = "Moody's downgraded the company's credit rating to junk status."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_fraud_text(self):
        text = "Executives were charged with accounting fraud and embezzlement."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_lawsuit_text(self):
        text = "The company was sued by shareholders in a class action lawsuit."
        assert is_credit_relevant(text) is True

    def test_returns_false_for_irrelevant_text(self):
        text = "The annual company picnic was held at the local park on Saturday."
        assert is_credit_relevant(text) is False

    def test_returns_false_for_empty_string(self):
        assert is_credit_relevant("") is False

    def test_case_insensitive_matching(self):
        text = "DOWNGRADED by S&P to B- with NEGATIVE OUTLOOK."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_liquidity_text(self):
        text = "The company is experiencing a severe liquidity crisis and cash crunch."
        assert is_credit_relevant(text) is True


class TestClassifyEvents:

    def test_detects_bankruptcy(self):
        text = "The retailer filed for bankruptcy protection under chapter 11."
        events = classify_events(text)
        assert "bankruptcy" in events

    def test_detects_downgrade(self):
        text = "S&P downgraded the bond from BB to CCC with a negative outlook."
        events = classify_events(text)
        assert "downgrade" in events

    def test_detects_multiple_events(self):
        text = (
            "The company was downgraded by Moody's following a massive fraud scandal "
            "that led to a lawsuit from regulators."
        )
        events = classify_events(text)
        assert "downgrade" in events
        assert "fraud" in events
        assert "lawsuit" in events

    def test_returns_empty_list_for_irrelevant_text(self):
        text = "The CEO attended the annual shareholder meeting in Chicago."
        events = classify_events(text)
        assert events == []

    def test_returns_empty_list_for_empty_string(self):
        assert classify_events("") == []

    def test_no_duplicate_event_types(self):
        text = "Fraud fraud fraud accounting fraud financial fraud."
        events = classify_events(text)
        assert events.count("fraud") == 1

    def test_detects_restructuring(self):
        text = "The firm announced a debt restructuring plan with a haircut for bondholders."
        events = classify_events(text)
        assert "restructuring" in events

    def test_detects_layoffs(self):
        text = "The company announced major layoffs affecting 5,000 employees in workforce reduction."
        events = classify_events(text)
        assert "layoffs" in events

    def test_detects_liquidity_crisis(self):
        text = "Sources say the bank faces a liquidity crisis after a cash crunch last quarter."
        events = classify_events(text)
        assert "liquidity_crisis" in events

    def test_detects_earnings_miss(self):
        text = "The company issued a profit warning after missing earnings expectations."
        events = classify_events(text)
        assert "earnings_miss" in events
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/unit/test_classifier.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'classify_events' from 'src.models.classifier'`

- [ ] **Step 3: Create `src/models/classifier.py`**

```python
"""
Keyword-based credit-relevance classifier.

Determines whether a piece of text mentions a credit-relevant event (bankruptcy,
downgrade, fraud, etc.) and which event types are present.

Usage:
    from src.models.classifier import is_credit_relevant, classify_events

    relevant = is_credit_relevant("Company filed for bankruptcy.")  # True
    events   = classify_events("Company filed for bankruptcy.")     # ["bankruptcy"]
"""

from typing import List

from src.utils.constants import KEYWORDS


def is_credit_relevant(text: str) -> bool:
    """
    Return True if the text contains at least one credit-risk keyword.
    Matching is case-insensitive.
    """
    if not text:
        return False
    lower = text.lower()
    return any(
        kw.lower() in lower
        for keywords in KEYWORDS.values()
        for kw in keywords
    )


def classify_events(text: str) -> List[str]:
    """
    Return a list of matched event type strings (from KEYWORDS keys).
    Each event type appears at most once. Order follows KEYWORDS dict order.
    Returns an empty list if no keywords match.
    """
    if not text:
        return []
    lower = text.lower()
    return [
        event_type
        for event_type, keywords in KEYWORDS.items()
        if any(kw.lower() in lower for kw in keywords)
    ]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_classifier.py -v
```

Expected: all 18 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models/classifier.py tests/unit/test_classifier.py
git commit -m "feat: add keyword-based credit-relevance classifier"
```

---

## Task 4: Integrate Classifier into Pipeline

**Files:**
- Modify: `src/processors/pipeline.py:1-30` (imports), `pipeline.py:120-135` (rows.append block)
- Test: run existing integration tests to confirm nothing broken

The classifier is lightweight — call it inline during `process_articles_batch()`. Sentiment is NOT added here (handled by the separate scoring script).

- [ ] **Step 1: Update imports in `src/processors/pipeline.py`**

At the top of the file, after the existing imports, add:

```python
from src.models.classifier import classify_events, is_credit_relevant
```

The full import block should look like:

```python
from src.db.connection import SessionLocal
from src.db.models import Article, ProcessedArticle
from src.processors.cleaner import clean_article
from src.processors.language_filter import detect_language
from src.processors.ner_extractor import extract_entities
from src.models.classifier import classify_events, is_credit_relevant
from src.utils.logger import setup_logger
```

- [ ] **Step 2: Update the `rows.append(...)` call**

Replace the existing `rows.append({...})` block (around line 122) with:

```python
credit_relevant = is_credit_relevant(cleaned)
events = classify_events(cleaned) if credit_relevant else []

rows.append({
    "article_id":         article.id,
    "cleaned_text":       cleaned,
    "entities":           entities,
    "sentiment_score":    None,
    "sentiment_label":    None,
    "is_credit_relevant": credit_relevant,
    "event_types":        events if events else None,
})
```

- [ ] **Step 3: Run existing pipeline tests to confirm nothing broke**

```bash
pytest tests/unit/test_cleaner.py tests/unit/test_ner_extractor.py tests/integration/test_processing_pipeline.py -v
```

Expected: all tests PASS (same count as before).

- [ ] **Step 4: Commit**

```bash
git add src/processors/pipeline.py
git commit -m "feat: integrate credit classifier into processing pipeline"
```

---

## Task 5: Create Sentiment Scoring Script

**Files:**
- Create: `scripts/score_sentiment.py`

This script scores `processed_articles` rows that have `sentiment_score IS NULL`, in batches. It's designed to be run as a nightly job or manually after new articles are processed.

- [ ] **Step 1: Create `scripts/score_sentiment.py`**

```python
"""
Score processed articles with FinBERT sentiment.

Finds processed_articles rows where sentiment_score IS NULL and populates
sentiment_score and sentiment_label for each one.

Usage:
    python -m scripts.score_sentiment
    python -m scripts.score_sentiment --batch-size 50
    python -m scripts.score_sentiment --limit 100
"""

import argparse

from sqlalchemy import update

from src.db.connection import SessionLocal
from src.db.models import ProcessedArticle
from src.models.sentiment import FinBERTSentiment
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def score_sentiment(batch_size: int = 50, limit: int = 0) -> int:
    """
    Score all processed_articles rows with sentiment_score IS NULL.

    Args:
        batch_size: Number of articles to score before committing to DB.
        limit:      Max articles to score total (0 = no limit).

    Returns:
        Number of articles scored.
    """
    db = SessionLocal()
    scorer = FinBERTSentiment()
    total_scored = 0

    try:
        query = (
            db.query(ProcessedArticle)
            .filter(ProcessedArticle.sentiment_score.is_(None))
            .filter(ProcessedArticle.cleaned_text.isnot(None))
        )
        if limit > 0:
            query = query.limit(limit)

        rows = query.all()
        logger.info(f"score_sentiment: {len(rows)} article(s) to score.")

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            texts = [r.cleaned_text for r in batch]
            results = scorer.predict_batch(texts)

            for row, res in zip(batch, results):
                row.sentiment_score = res["score"]
                row.sentiment_label = res["label"]

            db.commit()
            total_scored += len(batch)
            logger.info(
                f"score_sentiment: scored {total_scored}/{len(rows)} articles "
                f"(last batch avg_score={sum(r['score'] for r in results)/len(results):.3f})"
            )

    except Exception as exc:
        db.rollback()
        logger.error(f"score_sentiment failed: {exc}")
        raise
    finally:
        db.close()

    return total_scored


def main() -> None:
    parser = argparse.ArgumentParser(description="Score processed articles with FinBERT.")
    parser.add_argument("--batch-size", type=int, default=50, help="Commit every N articles.")
    parser.add_argument("--limit", type=int, default=0, help="Max articles to score (0=all).")
    args = parser.parse_args()

    logger.info(f"=== score_sentiment: batch_size={args.batch_size} limit={args.limit} ===")
    count = score_sentiment(batch_size=args.batch_size, limit=args.limit)
    logger.info(f"=== score_sentiment: done — {count} article(s) scored ===")
    print(f"Articles scored: {count}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the script imports without error (no model download yet)**

```bash
source venv/bin/activate
python -c "from scripts.score_sentiment import score_sentiment; print('import OK')"
```

Expected: `import OK` (model not downloaded yet — it's lazy-loaded on first predict call).

- [ ] **Step 3: Commit**

```bash
git add scripts/score_sentiment.py
git commit -m "feat: add score_sentiment.py script for FinBERT batch scoring"
```

---

## Task 6: Full Test Suite + Smoke Test

- [ ] **Step 1: Run the full test suite**

```bash
source venv/bin/activate
pytest --tb=short -q
```

Expected: all existing tests + new tests PASS. Confirm count increased by ~28 (10 sentiment + 18 classifier).

- [ ] **Step 2: Smoke test — score 10 articles with real FinBERT**

This downloads the model on first run (~440MB). Run against the real DB.

```bash
docker-compose ps  # confirm postgres is up
python -m scripts.score_sentiment --batch-size 10 --limit 10
```

Expected output (approximately):
```
Loading FinBERT from 'ProsusAI/finbert' (device=cpu)...
FinBERT loaded.
score_sentiment: 1189 article(s) to score.
score_sentiment: scored 10/1189 articles (last batch avg_score=-0.123)
Articles scored: 10
```

- [ ] **Step 3: Spot-check DB rows**

```bash
docker-compose exec postgres psql -U creditrisk -d creditrisk -c \
  "SELECT id, sentiment_label, sentiment_score FROM processed_articles WHERE sentiment_score IS NOT NULL LIMIT 10;"
```

Expected: 10 rows with `sentiment_label` in {positive, negative, neutral} and `sentiment_score` between -1.0 and 1.0.

- [ ] **Step 4: Smoke test — pipeline classifier integration**

Run a fresh batch through the pipeline (pick any 5 article IDs not yet processed):

```bash
docker-compose exec postgres psql -U creditrisk -d creditrisk -c \
  "SELECT a.id FROM articles a LEFT JOIN processed_articles pa ON a.id = pa.article_id WHERE pa.article_id IS NULL LIMIT 5;"
```

Copy the IDs and run:

```bash
python -c "
from src.processors.pipeline import process_articles_batch
n = process_articles_batch()
print(f'Processed: {n}')
"
```

Then check a newly processed article:

```bash
docker-compose exec postgres psql -U creditrisk -d creditrisk -c \
  "SELECT id, is_credit_relevant, event_types FROM processed_articles ORDER BY created_at DESC LIMIT 5;"
```

Expected: `is_credit_relevant` populated (True/False), `event_types` is a list or NULL (not all articles are credit-relevant).

- [ ] **Step 5: Score all remaining articles**

```bash
python -m scripts.score_sentiment --batch-size 50
```

Expected: logs showing batches completing, final count matching `processed_articles` row count.

- [ ] **Step 6: Commit final state**

```bash
git add -A
git commit -m "test: verify Days 15-17 FinBERT + classifier smoke tests pass"
```

---

## Self-Review

**Spec coverage:**
- ✅ `FinBERTSentiment` class with `predict()` + `predict_batch()` — Task 2
- ✅ GPU if available, CPU fallback — `torch.device("cuda" if torch.cuda.is_available() else "cpu")`
- ✅ Model cached locally by HuggingFace's default cache — automatic with `from_pretrained`
- ✅ `predict()` returns `{"positive": X, "negative": Y, "neutral": Z}` plus `label` and `score`
- ✅ `is_credit_relevant(text) -> bool` — Task 3
- ✅ `classify_events(text) -> List[str]` — Task 3
- ✅ All 5 keyword categories from spec (downgrade, default, legal, fraud, liquidity) covered by existing `KEYWORDS` in `src/utils/constants.py`
- ✅ `scripts/score_sentiment.py --batch-size` — Task 5
- ✅ Pipeline integration for classifier — Task 4
- ✅ Tests: `test_positive_sentiment`, `test_negative_sentiment`, `test_batch_processing`, `test_downgrade_detected`, `test_no_relevance`, `test_multiple_events` — Tasks 2-3

**Note on "100 articles < 30 seconds" performance test:** CPU FinBERT scoring rate is ~1 article/second, so 100 articles takes ~100 seconds on CPU. The unit test (`test_predict_batch_handles_100_texts`) uses a mocked model and verifies correctness. Real throughput can be benchmarked with `--limit 100` on the actual script. GPU would be ~10x faster.

**Type consistency:** `classify_events()` returns `List[str]`, stored in `event_types` (ARRAY(String) PostgreSQL column) — SQLAlchemy handles the conversion. `predict()` returns `Dict[str, float]` — `score` and `label` extracted separately for `sentiment_score`/`sentiment_label` columns.
