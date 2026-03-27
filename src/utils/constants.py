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
