"""
Project-wide constants for credit risk event types, severity levels, and NLP keywords.
Import directly:

    from src.utils.constants import EVENT_TYPES, SEVERITY_LEVELS, KEYWORDS
"""

# ---------------------------------------------------------------------------
# Event types
# A ProcessedArticle can be tagged with one or more of these.
# ---------------------------------------------------------------------------

EVENT_TYPES: list[str] = [
    "default",
    "bankruptcy",
    "downgrade",
    "restructuring",
    "rating_watch",
    "covenant_breach",
    "liquidity_crisis",
    "fraud",
    "regulatory_action",
    "merger_acquisition",
    "management_change",
    "earnings_miss",
    "debt_issuance",
    "layoffs",
    "lawsuit",
]

# ---------------------------------------------------------------------------
# Severity levels (ordered low → critical)
# ---------------------------------------------------------------------------

SEVERITY_LEVELS: list[str] = ["low", "medium", "high", "critical"]

# Map event types to a default severity for initial alert triage.
EVENT_SEVERITY_MAP: dict[str, str] = {
    "default":           "critical",
    "bankruptcy":        "critical",
    "fraud":             "critical",
    "liquidity_crisis":  "high",
    "covenant_breach":   "high",
    "downgrade":         "high",
    "rating_watch":      "medium",
    "restructuring":     "medium",
    "regulatory_action": "medium",
    "lawsuit":           "medium",
    "earnings_miss":     "low",
    "merger_acquisition":"low",
    "management_change": "low",
    "debt_issuance":     "low",
    "layoffs":           "low",
}

# ---------------------------------------------------------------------------
# Keywords
# Used by the credit-relevance classifier and event-type tagger.
# Each key is an EVENT_TYPE; values are trigger phrases (case-insensitive).
# ---------------------------------------------------------------------------

KEYWORDS: dict[str, list[str]] = {
    "default": [
        "default", "failed to pay", "missed payment", "payment default",
        "debt default", "sovereign default", "cross-default",
    ],
    "bankruptcy": [
        "bankruptcy", "chapter 11", "chapter 7", "insolvency", "insolvent",
        "receivership", "administration", "liquidation", "wound up",
    ],
    "downgrade": [
        "downgrade", "downgraded", "rating cut", "credit rating lowered",
        "outlook negative", "placed on negative watch",
    ],
    "restructuring": [
        "debt restructuring", "restructure", "debt swap", "haircut",
        "bond exchange", "liability management", "distressed exchange",
    ],
    "rating_watch": [
        "credit watch", "rating watch", "review for downgrade",
        "negative outlook", "ratings under review",
    ],
    "covenant_breach": [
        "covenant breach", "covenant violation", "breached covenant",
        "waiver request", "technical default",
    ],
    "liquidity_crisis": [
        "liquidity crisis", "cash crunch", "funding pressure", "cash flow problem",
        "burning through cash", "liquidity concern", "short of cash",
    ],
    "fraud": [
        "fraud", "accounting fraud", "financial fraud", "misrepresentation",
        "embezzlement", "falsified", "fictitious", "ponzi",
    ],
    "regulatory_action": [
        "regulatory action", "fined", "penalty", "enforcement action",
        "cease and desist", "regulatory probe", "under investigation",
        "SEC charges", "DOJ investigation",
    ],
    "merger_acquisition": [
        "merger", "acquisition", "takeover", "buyout", "acquired by",
        "merging with", "deal agreed", "LBO", "leveraged buyout",
    ],
    "management_change": [
        "CEO resigned", "CFO departure", "management change", "stepping down",
        "board shake-up", "executive departure", "leadership change",
    ],
    "earnings_miss": [
        "missed earnings", "earnings miss", "below expectations", "profit warning",
        "revenue shortfall", "guidance cut", "lowered forecast",
    ],
    "debt_issuance": [
        "bond issuance", "new debt", "credit facility", "raised debt",
        "term loan", "high-yield bond", "junk bond issued",
    ],
    "layoffs": [
        "layoffs", "job cuts", "redundancies", "workforce reduction",
        "downsizing", "headcount reduction", "retrenchment",
    ],
    "lawsuit": [
        "lawsuit", "sued", "legal action", "class action", "litigation",
        "filed suit", "court ruling", "damages awarded",
    ],
}

# ---------------------------------------------------------------------------
# News sources considered high-signal for credit risk
# ---------------------------------------------------------------------------

HIGH_SIGNAL_SOURCES: list[str] = [
    "Bloomberg",
    "Reuters",
    "Financial Times",
    "Wall Street Journal",
    "Moody's",
    "S&P Global",
    "Fitch Ratings",
    "The Economist",
    "CNBC",
    "MarketWatch",
]

# ============================================================================
# LLM Configuration — Groq
# ============================================================================

GROQ_PRIMARY_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"
GROQ_TIMEOUT_SECONDS = 30
GROQ_RETRY_SLEEP_BASE = 20  # seconds, multiplied by attempt number

# Cache TTL by obligor tier (minutes)
SUMMARY_CACHE_TTL_HIGH_RISK = 230  # 4 hours - 10 min buffer
SUMMARY_CACHE_TTL_NORMAL = 350     # 6 hours - 10 min buffer

# ============================================================================
# Alert Rule Names
# ============================================================================

ALERT_RULE_CREDIT_EVENT = "Rule1_CreditEvent"
ALERT_RULE_COVENANT_LIQUIDITY = "Rule2_CovenantLiquidity"
ALERT_RULE_DOWNGRADE_WATCH = "Rule3_DowngradeWatch"
ALERT_RULE_SENTIMENT_SPIKE = "Rule4_SentimentSpike"
ALERT_RULE_MULTIPLE_EVENTS = "Rule5_MultipleEvents"

# Rule thresholds
SENTIMENT_SPIKE_THRESHOLD = -0.5
SENTIMENT_SPIKE_MIN_ARTICLES = 3
MULTIPLE_EVENTS_THRESHOLD = 2
MULTIPLE_EVENTS_WINDOW_HOURS = 48

# Alert Scheduler
INTER_CALL_SLEEP_SECONDS = 15
HIGH_RISK_CYCLE_HOURS = 4
NORMAL_CYCLE_HOURS = 6

# Priority tier thresholds
HIGH_RISK_MIN_ALERTS_7D = 2
HIGH_RISK_MAX_SENTIMENT = -0.4

# Deduplication
ALERT_DEDUP_WINDOW_HOURS = 24
