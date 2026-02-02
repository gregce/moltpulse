"""Popularity-aware scoring for Moltos."""

import math
from typing import List, Optional

from . import dates, schema

# Score weights by item type
WEIGHTS = {
    "news": {
        "relevance": 0.45,
        "recency": 0.25,
        "engagement": 0.30,
    },
    "financial": {
        "relevance": 0.40,
        "recency": 0.35,
        "materiality": 0.25,
    },
    "social": {
        "relevance": 0.40,
        "recency": 0.30,
        "engagement": 0.30,
    },
    "awards": {
        "relevance": 0.35,
        "recency": 0.25,
        "prestige": 0.40,
    },
    "pe_activity": {
        "relevance": 0.45,
        "recency": 0.25,
        "deal_size": 0.30,
    },
}

# Award prestige tiers (0-100)
AWARD_PRESTIGE = {
    "cannes_lions": {"grand_prix": 100, "gold": 80, "silver": 60, "bronze": 40},
    "effie": {"grand": 90, "gold": 75, "silver": 55, "bronze": 35},
    "clio": {"grand": 85, "gold": 70, "silver": 50, "bronze": 30},
    "one_show": {"best_of": 95, "gold": 75, "silver": 55, "bronze": 35},
    "dnad": {"black_pencil": 100, "yellow_pencil": 80, "graphite_pencil": 60, "wood_pencil": 40},
}

# Default prestige for unknown awards
DEFAULT_AWARD_PRESTIGE = 50

# Penalties
UNKNOWN_ENGAGEMENT_PENALTY = 10
LOW_DATE_CONFIDENCE_PENALTY = 10
MED_DATE_CONFIDENCE_PENALTY = 5


def log1p_safe(x: Optional[int]) -> float:
    """Safe log1p that handles None and negative values."""
    if x is None or x < 0:
        return 0.0
    return math.log1p(x)


def compute_news_engagement_raw(engagement: Optional[schema.Engagement]) -> Optional[float]:
    """Compute raw engagement score for news item."""
    if engagement is None:
        return None

    # Use available metrics
    score = log1p_safe(engagement.score)
    comments = log1p_safe(engagement.num_comments)
    likes = log1p_safe(engagement.likes)

    if score == 0 and comments == 0 and likes == 0:
        return None

    return 0.5 * max(score, likes) + 0.5 * comments


def compute_social_engagement_raw(engagement: Optional[schema.Engagement]) -> Optional[float]:
    """Compute raw engagement score for social item."""
    if engagement is None:
        return None

    likes = log1p_safe(engagement.likes)
    reposts = log1p_safe(engagement.reposts)
    replies = log1p_safe(engagement.replies)
    quotes = log1p_safe(engagement.quotes)

    if likes == 0 and reposts == 0 and replies == 0:
        return None

    return 0.55 * likes + 0.25 * reposts + 0.15 * replies + 0.05 * quotes


def normalize_to_100(values: List[Optional[float]], default: float = 50) -> List[float]:
    """Normalize a list of values to 0-100 scale."""
    valid = [v for v in values if v is not None]
    if not valid:
        return [default if v is None else 50 for v in values]

    min_val = min(valid)
    max_val = max(valid)
    range_val = max_val - min_val

    if range_val == 0:
        return [50 if v is None else 50 for v in values]

    result = []
    for v in values:
        if v is None:
            result.append(None)
        else:
            normalized = ((v - min_val) / range_val) * 100
            result.append(normalized)

    return result


def score_news_items(items: List[schema.NewsItem]) -> List[schema.NewsItem]:
    """Compute scores for news items."""
    if not items:
        return items

    weights = WEIGHTS["news"]

    # Compute raw engagement scores
    eng_raw = [compute_news_engagement_raw(item.engagement) for item in items]
    eng_normalized = normalize_to_100(eng_raw)

    for i, item in enumerate(items):
        rel_score = int(item.relevance * 100)
        rec_score = dates.recency_score(item.date)
        eng_score = int(eng_normalized[i]) if eng_normalized[i] is not None else 35

        item.subs = schema.SubScores(
            relevance=rel_score,
            recency=rec_score,
            engagement=eng_score,
        )

        overall = (
            weights["relevance"] * rel_score
            + weights["recency"] * rec_score
            + weights["engagement"] * eng_score
        )

        if eng_raw[i] is None:
            overall -= UNKNOWN_ENGAGEMENT_PENALTY

        if item.date_confidence == "low":
            overall -= LOW_DATE_CONFIDENCE_PENALTY
        elif item.date_confidence == "med":
            overall -= MED_DATE_CONFIDENCE_PENALTY

        item.score = max(0, min(100, int(overall)))

    return items


def score_financial_items(items: List[schema.FinancialItem]) -> List[schema.FinancialItem]:
    """Compute scores for financial items."""
    if not items:
        return items

    weights = WEIGHTS["financial"]

    # Compute materiality based on change percentage
    materiality_raw = []
    for item in items:
        if item.change_pct is not None:
            # Higher absolute change = more material
            materiality_raw.append(abs(item.change_pct) * 10)
        else:
            materiality_raw.append(None)

    materiality_normalized = normalize_to_100(materiality_raw)

    for i, item in enumerate(items):
        rel_score = int(item.relevance * 100)
        rec_score = dates.recency_score(item.date)
        mat_score = int(materiality_normalized[i]) if materiality_normalized[i] is not None else 50

        item.subs = schema.SubScores(
            relevance=rel_score,
            recency=rec_score,
            materiality=mat_score,
        )

        overall = (
            weights["relevance"] * rel_score
            + weights["recency"] * rec_score
            + weights["materiality"] * mat_score
        )

        item.score = max(0, min(100, int(overall)))

    return items


def score_social_items(items: List[schema.SocialItem]) -> List[schema.SocialItem]:
    """Compute scores for social items."""
    if not items:
        return items

    weights = WEIGHTS["social"]

    eng_raw = [compute_social_engagement_raw(item.engagement) for item in items]
    eng_normalized = normalize_to_100(eng_raw)

    for i, item in enumerate(items):
        rel_score = int(item.relevance * 100)
        rec_score = dates.recency_score(item.date)
        eng_score = int(eng_normalized[i]) if eng_normalized[i] is not None else 35

        item.subs = schema.SubScores(
            relevance=rel_score,
            recency=rec_score,
            engagement=eng_score,
        )

        overall = (
            weights["relevance"] * rel_score
            + weights["recency"] * rec_score
            + weights["engagement"] * eng_score
        )

        if eng_raw[i] is None:
            overall -= UNKNOWN_ENGAGEMENT_PENALTY

        if item.date_confidence == "low":
            overall -= LOW_DATE_CONFIDENCE_PENALTY
        elif item.date_confidence == "med":
            overall -= MED_DATE_CONFIDENCE_PENALTY

        item.score = max(0, min(100, int(overall)))

    return items


def score_award_items(items: List[schema.AwardItem]) -> List[schema.AwardItem]:
    """Compute scores for award items."""
    if not items:
        return items

    weights = WEIGHTS["awards"]

    for item in items:
        rel_score = int(item.relevance * 100)
        rec_score = dates.recency_score(item.date)

        # Get prestige score
        show_prestige = AWARD_PRESTIGE.get(item.award_show.lower(), {})
        prestige_score = show_prestige.get(item.medal.lower(), DEFAULT_AWARD_PRESTIGE)

        item.subs = schema.SubScores(
            relevance=rel_score,
            recency=rec_score,
            engagement=prestige_score,  # Using engagement slot for prestige
        )

        overall = (
            weights["relevance"] * rel_score
            + weights["recency"] * rec_score
            + weights["prestige"] * prestige_score
        )

        item.score = max(0, min(100, int(overall)))

    return items


def score_pe_items(items: List[schema.PEActivityItem]) -> List[schema.PEActivityItem]:
    """Compute scores for PE activity items."""
    if not items:
        return items

    weights = WEIGHTS["pe_activity"]

    # Normalize deal sizes
    deal_sizes = []
    for item in items:
        if item.deal_value is not None:
            deal_sizes.append(log1p_safe(int(item.deal_value / 1_000_000)))  # In millions
        else:
            deal_sizes.append(None)

    deal_normalized = normalize_to_100(deal_sizes)

    for i, item in enumerate(items):
        rel_score = int(item.relevance * 100)
        rec_score = dates.recency_score(item.date)
        deal_score = int(deal_normalized[i]) if deal_normalized[i] is not None else 50

        item.subs = schema.SubScores(
            relevance=rel_score,
            recency=rec_score,
            materiality=deal_score,  # Using materiality slot for deal size
        )

        overall = (
            weights["relevance"] * rel_score
            + weights["recency"] * rec_score
            + weights["deal_size"] * deal_score
        )

        if item.date_confidence == "low":
            overall -= LOW_DATE_CONFIDENCE_PENALTY

        item.score = max(0, min(100, int(overall)))

    return items


def sort_items(items: List[schema.ItemType]) -> List[schema.ItemType]:
    """Sort items by score (descending), then date, then type priority."""

    def sort_key(item):
        score = -item.score
        date = getattr(item, "date", None) or "0000-00-00"
        date_key = -int(date.replace("-", ""))

        # Type priority
        if isinstance(item, schema.FinancialItem):
            type_priority = 0
        elif isinstance(item, schema.NewsItem):
            type_priority = 1
        elif isinstance(item, schema.SocialItem):
            type_priority = 2
        elif isinstance(item, schema.AwardItem):
            type_priority = 3
        elif isinstance(item, schema.PEActivityItem):
            type_priority = 4
        else:
            type_priority = 5

        # Text for stability
        text = getattr(item, "title", "") or getattr(item, "text", "") or getattr(item, "target_name", "")

        return (score, date_key, type_priority, text)

    return sorted(items, key=sort_key)
