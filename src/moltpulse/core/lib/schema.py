"""Data schemas for Moltos.

All items include source citations as a requirement.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Source:
    """A cited source with URL."""

    name: str  # e.g., "Ad Age", "Alpha Vantage"
    url: str
    date_accessed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "date_accessed": self.date_accessed,
        }


@dataclass
class Engagement:
    """Engagement metrics (platform-specific fields)."""

    # Generic
    score: Optional[int] = None

    # Reddit-style
    num_comments: Optional[int] = None
    upvote_ratio: Optional[float] = None

    # X/Twitter-style
    likes: Optional[int] = None
    reposts: Optional[int] = None
    replies: Optional[int] = None
    quotes: Optional[int] = None

    # Financial
    volume: Optional[int] = None
    market_cap: Optional[float] = None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        d = {}
        for key in [
            "score",
            "num_comments",
            "upvote_ratio",
            "likes",
            "reposts",
            "replies",
            "quotes",
            "volume",
            "market_cap",
        ]:
            val = getattr(self, key, None)
            if val is not None:
                d[key] = val
        return d if d else None


@dataclass
class SubScores:
    """Component scores for ranking."""

    relevance: int = 0
    recency: int = 0
    engagement: int = 0
    materiality: int = 0  # For financial items

    def to_dict(self) -> Dict[str, int]:
        return {
            "relevance": self.relevance,
            "recency": self.recency,
            "engagement": self.engagement,
            "materiality": self.materiality,
        }


@dataclass
class Entity:
    """A tracked entity (company, person, etc.)."""

    id: str
    name: str
    entity_type: str  # e.g., "holding_company", "thought_leader"
    symbol: Optional[str] = None  # Stock ticker if applicable
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "symbol": self.symbol,
            "metadata": self.metadata,
        }


@dataclass
class NewsItem:
    """A news article or publication item."""

    id: str
    title: str
    url: str  # Source citation - required
    source_name: str  # e.g., "Ad Age", "Forbes"
    snippet: str
    date: Optional[str] = None
    date_confidence: str = "low"
    categories: List[str] = field(default_factory=list)
    entities_mentioned: List[str] = field(default_factory=list)
    relevance: float = 0.5
    why_relevant: str = ""
    engagement: Optional[Engagement] = None
    subs: SubScores = field(default_factory=SubScores)
    score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source_name": self.source_name,
            "snippet": self.snippet,
            "date": self.date,
            "date_confidence": self.date_confidence,
            "categories": self.categories,
            "entities_mentioned": self.entities_mentioned,
            "relevance": self.relevance,
            "why_relevant": self.why_relevant,
            "engagement": self.engagement.to_dict() if self.engagement else None,
            "subs": self.subs.to_dict(),
            "score": self.score,
        }


@dataclass
class FinancialItem:
    """A financial data point (stock price, revenue, etc.)."""

    id: str
    entity_symbol: str
    entity_name: str
    metric_type: str  # "stock_price", "market_cap", "revenue", "change_pct"
    value: float
    change_pct: Optional[float] = None
    date: Optional[str] = None
    date_confidence: str = "high"
    source_url: str = ""  # Required citation
    source_name: str = ""
    relevance: float = 0.5
    subs: SubScores = field(default_factory=SubScores)
    score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_symbol": self.entity_symbol,
            "entity_name": self.entity_name,
            "metric_type": self.metric_type,
            "value": self.value,
            "change_pct": self.change_pct,
            "date": self.date,
            "date_confidence": self.date_confidence,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "relevance": self.relevance,
            "subs": self.subs.to_dict(),
            "score": self.score,
        }


@dataclass
class SocialItem:
    """A social media post (X, LinkedIn, etc.)."""

    id: str
    text: str
    url: str  # Required citation
    platform: str  # "x", "linkedin"
    author_name: str
    author_handle: str
    date: Optional[str] = None
    date_confidence: str = "low"
    engagement: Optional[Engagement] = None
    relevance: float = 0.5
    why_relevant: str = ""
    subs: SubScores = field(default_factory=SubScores)
    score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "url": self.url,
            "platform": self.platform,
            "author_name": self.author_name,
            "author_handle": self.author_handle,
            "date": self.date,
            "date_confidence": self.date_confidence,
            "engagement": self.engagement.to_dict() if self.engagement else None,
            "relevance": self.relevance,
            "why_relevant": self.why_relevant,
            "subs": self.subs.to_dict(),
            "score": self.score,
        }


@dataclass
class AwardItem:
    """An award or accolade."""

    id: str
    award_show: str  # "cannes_lions", "effie", etc.
    category: str
    winner_agency: str
    holding_company: Optional[str] = None
    campaign_name: str = ""
    client: str = ""
    year: int = 0
    medal: str = ""  # "gold", "silver", "bronze", "grand_prix"
    source_url: str = ""  # Required citation
    date: Optional[str] = None
    relevance: float = 0.5
    subs: SubScores = field(default_factory=SubScores)
    score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "award_show": self.award_show,
            "category": self.category,
            "winner_agency": self.winner_agency,
            "holding_company": self.holding_company,
            "campaign_name": self.campaign_name,
            "client": self.client,
            "year": self.year,
            "medal": self.medal,
            "source_url": self.source_url,
            "date": self.date,
            "relevance": self.relevance,
            "subs": self.subs.to_dict(),
            "score": self.score,
        }


@dataclass
class PEActivityItem:
    """A private equity activity (acquisition, investment, etc.)."""

    id: str
    activity_type: str  # "acquisition", "investment", "merger"
    target_name: str
    acquirer_name: str
    deal_value: Optional[float] = None
    deal_value_str: str = ""  # Human readable, e.g., "$200M"
    date: Optional[str] = None
    date_confidence: str = "low"
    source_url: str = ""  # Required citation
    source_name: str = ""
    details: str = ""
    relevance: float = 0.5
    subs: SubScores = field(default_factory=SubScores)
    score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "target_name": self.target_name,
            "acquirer_name": self.acquirer_name,
            "deal_value": self.deal_value,
            "deal_value_str": self.deal_value_str,
            "date": self.date,
            "date_confidence": self.date_confidence,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "details": self.details,
            "relevance": self.relevance,
            "subs": self.subs.to_dict(),
            "score": self.score,
        }


@dataclass
class ReportSection:
    """A section of a report with items and sources."""

    title: str
    items: List[Any]  # List of item dicts
    sources: List[Source] = field(default_factory=list)
    insight: Optional[str] = None  # LLM-generated insight for this section

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "title": self.title,
            "items": self.items,
            "sources": [s.to_dict() for s in self.sources],
        }
        if self.insight:
            d["insight"] = self.insight
        return d


@dataclass
class Report:
    """A complete Moltos report."""

    title: str
    domain: str
    profile: str
    report_type: str  # "daily_brief", "weekly_digest", "fundraising"
    generated_at: str
    date_range_from: str
    date_range_to: str
    sections: List[ReportSection] = field(default_factory=list)
    all_sources: List[Source] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    from_cache: bool = False
    cache_age_hours: Optional[float] = None
    # LLM enhancement fields
    executive_summary: Optional[str] = None
    strategic_recommendations: List[str] = field(default_factory=list)
    llm_enhanced: bool = False
    llm_provider: Optional[str] = None  # "openclaw" | "claude_cli" | "anthropic"

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "title": self.title,
            "domain": self.domain,
            "profile": self.profile,
            "report_type": self.report_type,
            "generated_at": self.generated_at,
            "date_range": {
                "from": self.date_range_from,
                "to": self.date_range_to,
            },
            "sections": [s.to_dict() for s in self.sections],
            "all_sources": [s.to_dict() for s in self.all_sources],
            "errors": self.errors,
            "from_cache": self.from_cache,
            "cache_age_hours": self.cache_age_hours,
            "llm_enhanced": self.llm_enhanced,
        }
        if self.executive_summary:
            d["executive_summary"] = self.executive_summary
        if self.strategic_recommendations:
            d["strategic_recommendations"] = self.strategic_recommendations
        if self.llm_provider:
            d["llm_provider"] = self.llm_provider
        return d


def create_report(
    title: str,
    domain: str,
    profile: str,
    report_type: str,
    from_date: str,
    to_date: str,
) -> Report:
    """Create a new report with metadata."""
    return Report(
        title=title,
        domain=domain,
        profile=profile,
        report_type=report_type,
        generated_at=datetime.now(timezone.utc).isoformat(),
        date_range_from=from_date,
        date_range_to=to_date,
    )


# Type alias for any item type
ItemType = NewsItem | FinancialItem | SocialItem | AwardItem | PEActivityItem
