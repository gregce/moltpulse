"""Normalization of raw data to canonical schema."""

from typing import Any, Dict, List, TypeVar

from . import dates, schema

T = TypeVar("T")


def filter_by_date_range(
    items: List[T],
    from_date: str,
    to_date: str,
    date_field: str = "date",
    require_date: bool = False,
) -> List[T]:
    """Hard filter: Remove items outside the date range.

    This is the safety net - ensures all items are within the valid date range.

    Args:
        items: List of items to filter
        from_date: Start date (YYYY-MM-DD) - exclude items before this
        to_date: End date (YYYY-MM-DD) - exclude items after this
        date_field: Name of the date attribute on items
        require_date: If True, also remove items with no date

    Returns:
        Filtered list with only items in range
    """
    result = []
    for item in items:
        item_date = getattr(item, date_field, None)

        if item_date is None:
            if not require_date:
                result.append(item)
            continue

        # Hard filter: if date is before from_date, exclude
        if item_date < from_date:
            continue

        # Hard filter: if date is after to_date, exclude (likely parsing error)
        if item_date > to_date:
            continue

        result.append(item)

    return result


def normalize_news_item(
    raw: Dict[str, Any],
    from_date: str,
    to_date: str,
) -> schema.NewsItem:
    """Normalize a raw news item dict to NewsItem schema."""
    date_str = raw.get("date") or raw.get("publishedAt") or raw.get("pubDate")
    if date_str:
        parsed = dates.parse_date(date_str)
        if parsed:
            date_str = parsed.date().isoformat()

    date_confidence = dates.get_date_confidence(date_str, from_date, to_date)

    engagement = None
    eng_raw = raw.get("engagement")
    if isinstance(eng_raw, dict):
        engagement = schema.Engagement(
            score=eng_raw.get("score"),
            num_comments=eng_raw.get("num_comments") or eng_raw.get("comments"),
            likes=eng_raw.get("likes"),
        )

    return schema.NewsItem(
        id=raw.get("id", ""),
        title=raw.get("title", ""),
        url=raw.get("url") or raw.get("link", ""),
        source_name=raw.get("source_name") or raw.get("source", {}).get("name", ""),
        snippet=raw.get("snippet") or raw.get("description", ""),
        date=date_str,
        date_confidence=date_confidence,
        categories=raw.get("categories", []),
        entities_mentioned=raw.get("entities_mentioned", []),
        relevance=raw.get("relevance", 0.5),
        why_relevant=raw.get("why_relevant", ""),
        engagement=engagement,
    )


def normalize_financial_item(
    raw: Dict[str, Any],
    from_date: str,
    to_date: str,
) -> schema.FinancialItem:
    """Normalize a raw financial item dict to FinancialItem schema."""
    date_str = raw.get("date")
    date_confidence = dates.get_date_confidence(date_str, from_date, to_date) if date_str else "high"

    return schema.FinancialItem(
        id=raw.get("id", ""),
        entity_symbol=raw.get("symbol") or raw.get("entity_symbol", ""),
        entity_name=raw.get("name") or raw.get("entity_name", ""),
        metric_type=raw.get("metric_type", "stock_price"),
        value=float(raw.get("value", 0)),
        change_pct=raw.get("change_pct") or raw.get("changePercent"),
        date=date_str,
        date_confidence=date_confidence,
        source_url=raw.get("source_url", ""),
        source_name=raw.get("source_name", ""),
        relevance=raw.get("relevance", 0.5),
    )


def normalize_social_item(
    raw: Dict[str, Any],
    from_date: str,
    to_date: str,
) -> schema.SocialItem:
    """Normalize a raw social item dict to SocialItem schema."""
    date_str = raw.get("date") or raw.get("created_at")
    if date_str:
        parsed = dates.parse_date(date_str)
        if parsed:
            date_str = parsed.date().isoformat()

    date_confidence = dates.get_date_confidence(date_str, from_date, to_date)

    engagement = None
    eng_raw = raw.get("engagement")
    if isinstance(eng_raw, dict):
        engagement = schema.Engagement(
            likes=eng_raw.get("likes") or eng_raw.get("favorite_count"),
            reposts=eng_raw.get("reposts") or eng_raw.get("retweet_count"),
            replies=eng_raw.get("replies") or eng_raw.get("reply_count"),
            quotes=eng_raw.get("quotes") or eng_raw.get("quote_count"),
        )

    return schema.SocialItem(
        id=raw.get("id", ""),
        text=raw.get("text") or raw.get("content", ""),
        url=raw.get("url", ""),
        platform=raw.get("platform", "unknown"),
        author_name=raw.get("author_name") or raw.get("author", {}).get("name", ""),
        author_handle=raw.get("author_handle") or raw.get("author", {}).get("handle", ""),
        date=date_str,
        date_confidence=date_confidence,
        engagement=engagement,
        relevance=raw.get("relevance", 0.5),
        why_relevant=raw.get("why_relevant", ""),
    )


def normalize_award_item(
    raw: Dict[str, Any],
    from_date: str,
    to_date: str,
) -> schema.AwardItem:
    """Normalize a raw award item dict to AwardItem schema."""
    date_str = raw.get("date")
    if not date_str and raw.get("year"):
        date_str = f"{raw['year']}-01-01"

    return schema.AwardItem(
        id=raw.get("id", ""),
        award_show=raw.get("award_show", ""),
        category=raw.get("category", ""),
        winner_agency=raw.get("winner_agency") or raw.get("agency", ""),
        holding_company=raw.get("holding_company"),
        campaign_name=raw.get("campaign_name") or raw.get("campaign", ""),
        client=raw.get("client", ""),
        year=raw.get("year", 0),
        medal=raw.get("medal") or raw.get("award_type", ""),
        source_url=raw.get("source_url", ""),
        date=date_str,
        relevance=raw.get("relevance", 0.5),
    )


def normalize_pe_item(
    raw: Dict[str, Any],
    from_date: str,
    to_date: str,
) -> schema.PEActivityItem:
    """Normalize a raw PE activity item dict to PEActivityItem schema."""
    date_str = raw.get("date") or raw.get("announced_date")
    if date_str:
        parsed = dates.parse_date(date_str)
        if parsed:
            date_str = parsed.date().isoformat()

    date_confidence = dates.get_date_confidence(date_str, from_date, to_date)

    # Parse deal value
    deal_value = raw.get("deal_value")
    deal_value_str = raw.get("deal_value_str", "")
    if deal_value_str and not deal_value:
        # Try to parse from string like "$200M" or "$1.5B"
        try:
            val_str = deal_value_str.replace("$", "").replace(",", "").strip()
            if val_str.endswith("B"):
                deal_value = float(val_str[:-1]) * 1_000_000_000
            elif val_str.endswith("M"):
                deal_value = float(val_str[:-1]) * 1_000_000
            elif val_str.endswith("K"):
                deal_value = float(val_str[:-1]) * 1_000
            else:
                deal_value = float(val_str)
        except (ValueError, AttributeError):
            pass

    return schema.PEActivityItem(
        id=raw.get("id", ""),
        activity_type=raw.get("activity_type") or raw.get("type", ""),
        target_name=raw.get("target_name") or raw.get("target", ""),
        acquirer_name=raw.get("acquirer_name") or raw.get("acquirer", ""),
        deal_value=deal_value,
        deal_value_str=deal_value_str,
        date=date_str,
        date_confidence=date_confidence,
        source_url=raw.get("source_url", ""),
        source_name=raw.get("source_name", ""),
        details=raw.get("details") or raw.get("description", ""),
        relevance=raw.get("relevance", 0.5),
    )


def items_to_dicts(items: List) -> List[Dict[str, Any]]:
    """Convert schema items to dicts for JSON serialization."""
    return [item.to_dict() for item in items]
