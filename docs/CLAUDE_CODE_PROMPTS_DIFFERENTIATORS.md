# 🎯 Claude Code Prompts for Differentiation Features

When you reach each week, copy-paste these prompts into Claude Code (or ask Claude directly).

---

## WEEK 5, DAY 29-30: Baseline Comparisons

**Prompt to use in Claude Code:**

```
You are helping me build a credit risk monitoring system. I'm at Week 5, Day 29-30.

I need to implement BASELINE COMPARISONS to show my system is better than obvious alternatives.

Follow my STARTUP_PLAN exactly (you have access to it in .claude/claude.md).

Tasks:
1. Create src/models/baselines.py with these functions:
   - sentiment_baseline(articles: List[Dict]) -> float
   - frequency_baseline(obligor_id: int, days: int) -> float  
   - merton_distance_to_default(obligor_id: int) -> float
   - compare_baselines(obligor_id: int, days: int = 7) -> Dict

2. Each baseline should return a risk score (0-1)

3. compare_baselines() should return:
   {
       'my_score': 0.73,
       'sentiment_baseline': 0.52,
       'frequency_baseline': 0.61,
       'merton_baseline': 0.68,
       'improvement_vs_sentiment': '40%',
       'improvement_vs_frequency': '20%',
       'improvement_vs_merton': '7%'
   }

4. Write comprehensive tests in tests/unit/test_baselines.py

5. Add integration test showing compare_baselines() on 10 real obligors

Success criteria:
- All baselines calculate without errors
- compare_baselines() shows your system beats all 3
- Tests pass with >80% coverage
- Can run: python scripts/compare_baselines.py
```

---

## WEEK 6, DAY 36-37: Explainability Layer

**Prompt to use in Claude Code:**

```
You are helping me build a credit risk monitoring system. I'm at Week 6, Day 36-37.

I need to implement EXPLAINABILITY LAYER so every alert explains WHY it triggered.

Follow my STARTUP_PLAN exactly.

Tasks:
1. Create src/models/explainer.py with these functions:
   - explain_alert(alert_id: int) -> Dict
   - explain_risk_score(obligor_id: int, date: datetime) -> Dict
   - get_evidence(alert_id: int) -> Dict

2. explain_alert() should return:
   {
       'primary_driver': 'Negative sentiment spike (4 articles, avg -0.6)',
       'supporting_signals': [
           'Covenant violation language detected',
           'Debt maturity in 6 months',
           'Sector declining 15% this week'
       ],
       'confidence': 0.78,
       'similar_past_cases': [
           {'company': 'ABC Corp', 'year': 2022, 'outcome': 'defaulted'}
       ]
   }

3. explain_risk_score() should return:
   {
       'sentiment_contribution': 0.4,
       'event_contribution': 0.2,
       'volume_contribution': 0.15,
       'trend_contribution': 0.25,
       'total_score': 0.72
   }

4. get_evidence() should return:
   {
       'evidence': [
           {
               'quote': 'Apple misses bond payment deadline',
               'source': 'Reuters',
               'date': '2024-01-15',
               'sentiment': -0.8
           },
           ...
       ]
   }

5. Update src/api/main.py GET /api/alerts/{id} endpoint to include:
   - explanation: Dict
   - evidence: List[Dict]
   - confidence: float

6. Update AlertResponse Pydantic model with new fields

7. Write tests in tests/unit/test_explainer.py

Success criteria:
- All explanations generate without errors
- Evidence quotes are from actual articles
- API returns properly structured JSON
- Tests pass
- GET /api/alerts/{id} returns all new fields
```

---

## WEEK 7, DAY 43-44: Real-Time Monitoring Dashboard

**Prompt to use in Claude Code:**

```
You are helping me build a credit risk monitoring system. I'm at Week 7, Day 43-44.

I need to build a REAL-TIME MONITORING DASHBOARD to show this is production-ready.

Follow my STARTUP_PLAN exactly.

Create: dashboard/pages/realtime_monitor.py

Features to implement:
1. Risk Heatmap
   - Grid: Companies (rows) × Risk levels (columns: Low, Medium, High, Critical)
   - Color intensity = risk score (darker = higher risk)
   - Interactive: click cell to drill-down
   - Update: refresh every 5 minutes

2. Live Alert Stream
   - Show newest alerts first (live feed)
   - Color by severity: 🟢 low, 🟡 medium, 🔴 high, 🔴🔴 critical
   - Show: timestamp, company name, alert title, risk score
   - Button: "View Details" (links to drill-down)
   - Update: check every 30 seconds

3. KPI Metric Cards
   - Total alerts this week
   - Critical alerts count
   - Companies at risk (>50 score)
   - Average portfolio risk score
   - Update: every hour

4. Risk Timeline (7-day trend)
   - X-axis: Days (last 7 days)
   - Y-axis: Number of alerts
   - Color by severity
   - Show if alerts trending up/down

5. Sector Heatmap
   - Sectors (rows) × Risk level (columns)
   - Which sectors most at risk?

Implementation:
- Use Plotly for interactive charts
- Cache data with @st.cache_data (5 min TTL)
- Show "Last updated: X seconds ago"
- Add manual refresh button
- Handle missing data gracefully

Tests:
- Test heatmap renders (plotly chart returns valid JSON)
- Test alert stream updates
- Test KPI calculations
- Test data freshness (cache expiry)

Success criteria:
- Dashboard loads in <5 seconds
- Charts interactive (hover, click work)
- Real-time updates working
- No crashes with missing data
- Professional appearance
- Can run: streamlit run dashboard/app.py --pages.showSidebarNavigation=true
```

---

## WEEK 8, DAY 50-51: Backtesting Module

**Prompt to use in Claude Code:**

```
You are helping me build a credit risk monitoring system. I'm at Week 8, Day 50-51.

I need to implement BACKTESTING to PROVE my system actually works.

This is the #1 most important feature for resume impact.

Follow my STARTUP_PLAN exactly.

Tasks:
1. Create src/models/backtester.py with:

   Class BacktestEngine:
       def run_backtest(self, start_date: datetime, end_date: datetime) -> List[Dict]
           """Replay alerts from start_date to end_date"""
           # For each day in range:
           #   - Get alerts that were generated that day
           #   - Check if actual credit event happened within 30 days
           #   - Calculate: was_correct, days_to_event
           # Return list of backtest results

       def calculate_metrics(self, results: List[Dict]) -> Dict
           """Calculate precision, recall, ROC-AUC, etc."""
           # Precision: correct alerts / total alerts
           # Recall: caught events / actual events
           # F1: harmonic mean
           # ROC-AUC: ranking quality
           # Avg time to event: average days before event occurred
           Return:
           {
               'precision': 0.73,
               'recall': 0.62,
               'f1_score': 0.67,
               'roc_auc': 0.81,
               'avg_time_to_event': 7.3,
               'best_case': 'Caught Apple default 14 days early',
               'worst_case': 'Missed 3 downgrades in 2020'
           }

2. Create src/models/ground_truth.py with:

   Class GroundTruthCollector:
       def fetch_defaults(self, date_from, date_to) -> List[Tuple]
           """Get actual bankruptcies from 2020-2024"""
           # Return: [(company_id, date, source), ...]
           
       def fetch_downgrades(self, date_from, date_to) -> List[Tuple]
           """Get credit rating downgrades"""
           # Return: [(company_id, date, old_rating, new_rating), ...]
           
       def fetch_stock_crashes(self, date_from, date_to, threshold=0.20) -> List[Tuple]
           """Get stock crashes >20%"""
           # Use Yahoo Finance API
           # Return: [(company_id, date, drop_pct), ...]

3. Create data/ground_truth_events.csv
   - Manually curated list of known defaults/downgrades
   - Columns: company_id, date, event_type, source
   - At least 20 events from 2020-2024
   - Examples:
     * Lehman Brothers collapse (2008 - before range, skip)
     * Any real defaults from 2020-2024

4. Update database schema:
   - Add BacktestResult table:
     * alert_date
     * company_id
     * actual_event
     * days_to_event
     * was_correct

5. Write integration test: tests/integration/test_backtesting.py
   - test_backtest_runs_without_error
   - test_metrics_calculation
   - test_ground_truth_fetch
   - test_precision_recall

6. Create scripts/run_backtest.py
   - Run full backtest for 2020-2024
   - Print metrics table
   - Show sample results
   
7. Update README.md with backtest results section:
   - Table: Precision, Recall, F1, ROC-AUC
   - Comparison to baselines
   - Key finding: "Caught 78% of defaults 7 days early"

Success criteria:
- Backtest runs without errors
- Metrics calculated correctly
- Results show 60%+ precision
- Can show improvement over baselines
- README shows impressive metrics
- Can run: python scripts/run_backtest.py

THIS IS YOUR BIGGEST RESUME DIFFERENTIATOR.
Make sure metrics are accurate and impressive.
```

---

## 📋 How to Use These Prompts

### When You're Ready

**Week 5, Day 29:**
1. Open this file and copy the "Baseline Comparisons" prompt
2. Go to Claude Code (or ask Claude in chat)
3. Paste the prompt exactly
4. Claude implements it
5. Test and verify it works
6. Commit to git: `git commit -m "Feature: baseline comparisons (Week 5)"`

**Repeat for each week:**
- Week 6, Day 36: Copy "Explainability" prompt
- Week 7, Day 43: Copy "Real-Time Dashboard" prompt
- Week 8, Day 50: Copy "Backtesting" prompt (MOST IMPORTANT)

---

## ⚡ Pro Tips

1. **Copy the exact prompt** - Claude Code works best with detailed instructions
2. **Test immediately** - After Claude finishes, run the code right away
3. **If something's wrong** - Read the error, fix it, then ask Claude to update
4. **Git commit after each** - Makes it easy to track progress
5. **Don't skip backtesting** - Week 8 backtest is worth 50% of your portfolio value

---

## 🎯 Expected Outcomes

| Feature | Prompt Location | Expected Output | Resume Impact |
|---------|-----------------|-----------------|---------------|
| Baselines | Week 5 | 3 baseline comparisons | ⭐⭐⭐⭐ |
| Explainability | Week 6 | Detailed alert explanations | ⭐⭐⭐⭐ |
| Real-time Dashboard | Week 7 | Live monitoring UI | ⭐⭐⭐⭐⭐ |
| Backtesting | Week 8 | Precision/Recall metrics | ⭐⭐⭐⭐⭐ |

---

**Save this file. You'll reference it 4 times during the 8-week build. 📌**
