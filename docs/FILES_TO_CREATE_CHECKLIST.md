# 📁 Files to Create for Differentiation Features

When you reach each week, use this checklist to know exactly which files Claude Code will create.

---

## WEEK 5: Baseline Comparisons

### Files Claude Will Create:

```
src/models/baselines.py
├── sentiment_baseline() function
├── frequency_baseline() function
├── merton_distance_to_default() function
└── compare_baselines() function

tests/unit/test_baselines.py
├── test_sentiment_baseline()
├── test_frequency_baseline()
├── test_merton_model()
└── test_compare_baselines()

scripts/compare_baselines.py (optional)
└── Script to test on all 50 obligors
```

### Files You Need to Update:

```
src/models/__init__.py
└── Add: from .baselines import sentiment_baseline, compare_baselines
```

### Expected Result:

```bash
$ python scripts/compare_baselines.py

Results:
┌─────────────┬────────┬─────────┬──────────┐
│ Metric      │ My Sys │ Baseln  │ Improve  │
├─────────────┼────────┼─────────┼──────────┤
│ Sentiment   │ 0.73   │ 0.52    │ +40%     │
│ Frequency   │ 0.73   │ 0.61    │ +20%     │
│ Merton      │ 0.73   │ 0.68    │ +7%      │
└─────────────┴────────┴─────────┴──────────┘
```

---

## WEEK 6: Explainability Layer

### Files Claude Will Create:

```
src/models/explainer.py
├── explain_alert(alert_id: int) -> Dict
├── explain_risk_score(obligor_id: int, date: datetime) -> Dict
└── get_evidence(alert_id: int) -> Dict

tests/unit/test_explainer.py
├── test_alert_explanation_structure()
├── test_evidence_retrieval()
├── test_confidence_scoring()
└── test_explanation_accuracy()
```

### Files You Need to Update:

```
src/api/main.py
└── Update GET /api/alerts/{id} endpoint to:
    - Add explanation field
    - Add evidence field
    - Add confidence field

src/api/schemas.py (or similar)
└── Update AlertResponse Pydantic model:
    class AlertResponse(BaseModel):
        id: int
        company: str
        risk_score: float
        explanation: Dict  # NEW
        evidence: List[Dict]  # NEW
        confidence: float  # NEW
```

### Expected Result:

```bash
$ curl http://localhost:8000/api/alerts/123

{
  "id": 123,
  "company": "Apple Inc",
  "risk_score": 8.2,
  "explanation": {
    "primary_driver": "Negative sentiment spike (4 articles, avg -0.6)",
    "supporting_signals": [
      "Covenant violation language detected",
      "Debt maturity in 6 months",
      "Sector declining 15% this week"
    ],
    "confidence": 0.78,
    "similar_past_cases": [
      {"company": "XYZ Corp", "year": 2022, "outcome": "defaulted"}
    ]
  },
  "evidence": [
    {
      "quote": "Apple misses bond payment deadline",
      "source": "Reuters",
      "date": "2024-01-15"
    }
  ]
}
```

---

## WEEK 7: Real-Time Monitoring Dashboard

### Files Claude Will Create:

```
dashboard/pages/realtime_monitor.py
├── Risk heatmap (Plotly)
├── Live alert stream (Streamlit)
├── KPI metric cards (Streamlit columns)
├── Risk timeline chart (Plotly)
└── Sector heatmap (Plotly)

dashboard/components/realtime_charts.py (helper functions)
├── build_risk_heatmap()
├── build_alert_stream()
├── build_kpi_cards()
├── build_risk_timeline()
└── build_sector_heatmap()

tests/dashboard/test_realtime_monitor.py
├── test_heatmap_rendering()
├── test_alert_stream_updates()
├── test_kpi_calculations()
└── test_data_freshness()
```

### Files You Need to Update:

```
dashboard/app.py (main app router)
└── Add new page to navigation:
    pages = {
        "Portfolio": "pages.portfolio",
        "Real-Time Monitor": "pages.realtime_monitor",  # NEW
        "Alerts": "pages.alerts",
        ...
    }

dashboard/config.py (or similar)
└── Add caching TTL settings:
    CACHE_TTL_MINUTES = 5
    ALERT_REFRESH_SECONDS = 30
```

### Expected Result:

Browser view at `http://localhost:8501`:
```
┌─────────────────────────────────────────────────┐
│  📊 Real-Time Credit Risk Monitor              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ⚠️  KPI Cards:                                 │
│  [Critical Alerts: 3] [At Risk: 12] [Avg: 45]  │
│                                                  │
│  🔴 Risk Heatmap:                              │
│  ┌─────────┬─────┬──────┬──────┬──────────┐    │
│  │ Company │ Low │ Med  │ High │ Critical │    │
│  ├─────────┼─────┼──────┼──────┼──────────┤    │
│  │ Apple   │     │  ██  │      │          │    │
│  │ JPM     │     │      │  ███ │          │    │
│  │ Tesla   │     │      │  ███ │   ██     │    │
│  └─────────┴─────┴──────┴──────┴──────────┘    │
│                                                  │
│  🚨 Live Alert Stream (Last 5):                │
│  🔴 Critical - Tesla default risk (35m ago)    │
│  🟠 High - JPM covenant violation (1h ago)     │
│  🟡 Medium - Apple downgrade risk (2h ago)     │
│                                                  │
│  📈 7-Day Risk Trend:                          │
│  [Line chart showing alert count over time]    │
└─────────────────────────────────────────────────┘
```

---

## WEEK 8: Backtesting Module

### Files Claude Will Create:

```
src/models/backtester.py
├── BacktestEngine class
│   ├── run_backtest(start_date, end_date) -> List[Dict]
│   └── calculate_metrics(results) -> Dict
└── Helper functions

src/models/ground_truth.py
├── GroundTruthCollector class
│   ├── fetch_defaults(date_from, date_to)
│   ├── fetch_downgrades(date_from, date_to)
│   └── fetch_stock_crashes(date_from, date_to)
└── Helper functions

data/ground_truth_events.csv
├── Manually curated defaults/downgrades
├── Columns: company_id, date, event_type, source
└── Rows: 20+ credit events from 2020-2024

tests/integration/test_backtesting.py
├── test_backtest_runs_without_error()
├── test_metrics_calculation()
├── test_ground_truth_fetch()
├── test_precision_recall()
└── test_time_to_event_calculation()

scripts/run_backtest.py
├── Run full backtest
├── Print metrics table
├── Show sample results
└── Export results to CSV
```

### Files You Need to Create:

```
data/ground_truth_events.csv
Example content:
─────────────────────────────────────────────
company_id,date,event_type,source
1,2020-03-15,stock_crash,yahoo_finance
2,2021-06-22,downgrade,s_and_p
3,2022-09-01,default,sec_filing
...
─────────────────────────────────────────────
```

### Files You Need to Update:

```
README.md
└── Add new section: "Validation Results"
    - Metrics table: Precision, Recall, F1, ROC-AUC
    - Comparison to baselines
    - Key finding statement
    - Example: "My system caught 78% of defaults 7 days early"

src/db/models.py
└── Add BacktestResult table:
    class BacktestResult(Base):
        __tablename__ = "backtest_results"
        
        id = Column(Integer, primary_key=True)
        alert_date = Column(DateTime)
        company_id = Column(Integer, FK)
        actual_event = Column(String)  # 'default', 'downgrade', 'none'
        days_to_event = Column(Integer)
        was_correct = Column(Boolean)
```

### Expected Result:

```bash
$ python scripts/run_backtest.py

Running backtest: 2020-01-01 to 2024-12-31
Processing 500 alerts...
Comparing to 35 actual credit events...

═══════════════════════════════════════════════════════════
                    BACKTEST RESULTS
═══════════════════════════════════════════════════════════

Performance Metrics:
┌──────────────────┬─────────┐
│ Metric           │ Value   │
├──────────────────┼─────────┤
│ Precision        │ 73%     │
│ Recall           │ 62%     │
│ F1 Score         │ 0.67    │
│ ROC-AUC          │ 0.81    │
│ Avg time before  │ 7.3 days│
└──────────────────┴─────────┘

Comparison to Baselines:
┌──────────────────┬──────────┬──────────┐
│ Baseline         │ My Score │ Better   │
├──────────────────┼──────────┼──────────┤
│ Sentiment avg    │ 73%      │ +45%     │
│ Frequency count  │ 73%      │ +20%     │
│ Merton model     │ 73%      │ +7%      │
└──────────────────┴──────────┴──────────┘

Sample Results:
✅ Apple downgrade - Caught 9 days early
✅ JPM default - Caught 5 days early
❌ Tesla covenant - Missed (false negative)

═══════════════════════════════════════════════════════════
Backtest complete. Results saved to: data/backtest_results.csv
```

---

## 📋 Full File Structure After All Features

```
credit-risk-monitor/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sentiment.py (existing)
│   │   ├── baselines.py ✨ NEW (Week 5)
│   │   ├── explainer.py ✨ NEW (Week 6)
│   │   ├── backtester.py ✨ NEW (Week 8)
│   │   └── ground_truth.py ✨ NEW (Week 8)
│   ├── api/
│   │   ├── main.py (updated Week 6)
│   │   └── schemas.py (updated Week 6)
│   └── ... (other existing files)
│
├── dashboard/
│   ├── pages/
│   │   ├── realtime_monitor.py ✨ NEW (Week 7)
│   │   └── ... (other pages)
│   ├── components/
│   │   ├── realtime_charts.py ✨ NEW (Week 7)
│   │   └── ... (other components)
│   └── app.py (updated Week 7)
│
├── tests/
│   ├── unit/
│   │   ├── test_baselines.py ✨ NEW (Week 5)
│   │   ├── test_explainer.py ✨ NEW (Week 6)
│   │   └── ... (other tests)
│   ├── integration/
│   │   ├── test_backtesting.py ✨ NEW (Week 8)
│   │   └── ... (other tests)
│   └── dashboard/
│       └── test_realtime_monitor.py ✨ NEW (Week 7)
│
├── scripts/
│   ├── compare_baselines.py ✨ NEW (Week 5)
│   └── run_backtest.py ✨ NEW (Week 8)
│
├── data/
│   ├── ground_truth_events.csv ✨ NEW (Week 8)
│   ├── backtest_results.csv ✨ GENERATED (Week 8)
│   └── ... (other data)
│
├── README.md (updated Week 8)
└── STARTUP_PLAN_WEEK1-8.md (your plan)
```

---

## ✅ Quick Checklist: Files to Create

- [ ] Week 5: `src/models/baselines.py`
- [ ] Week 5: `tests/unit/test_baselines.py`
- [ ] Week 5: `scripts/compare_baselines.py`
- [ ] Week 6: `src/models/explainer.py`
- [ ] Week 6: `tests/unit/test_explainer.py`
- [ ] Week 6: Update `src/api/main.py`
- [ ] Week 7: `dashboard/pages/realtime_monitor.py`
- [ ] Week 7: `dashboard/components/realtime_charts.py`
- [ ] Week 7: `tests/dashboard/test_realtime_monitor.py`
- [ ] Week 8: `src/models/backtester.py`
- [ ] Week 8: `src/models/ground_truth.py`
- [ ] Week 8: `data/ground_truth_events.csv`
- [ ] Week 8: `tests/integration/test_backtesting.py`
- [ ] Week 8: `scripts/run_backtest.py`
- [ ] Week 8: Update `README.md`

---

**Total new files: ~14 files across 4 weeks**
**Total lines of code: ~2000-3000 lines**
**Resume impact: ⭐⭐⭐⭐⭐ (Portfolio project that gets interviews)**
