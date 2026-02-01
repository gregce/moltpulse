"""Abstract collector base class for MoltPulse."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .lib import schema
from .profile_loader import ProfileConfig


class CollectorResult:
    """Result from a collector run."""

    def __init__(
        self,
        items: List[schema.ItemType],
        sources: List[schema.Source],
        error: Optional[str] = None,
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.items = items
        self.sources = sources
        self.error = error
        self.raw_response = raw_response

    @property
    def success(self) -> bool:
        """Check if collection was successful."""
        return self.error is None

    @property
    def count(self) -> int:
        """Number of items collected."""
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "sources": [s.to_dict() for s in self.sources],
            "error": self.error,
            "count": self.count,
        }


class Collector(ABC):
    """Abstract base class for all data collectors.

    Collectors fetch data from external sources (APIs, RSS, web scraping)
    and return normalized items with source citations.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize collector with configuration.

        Args:
            config: Environment/API configuration from env.get_config()
        """
        self.config = config

    @property
    @abstractmethod
    def collector_type(self) -> str:
        """Return the collector type identifier (e.g., 'financial', 'news')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable collector name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this collector is available (has required API keys, etc.)."""
        pass

    @abstractmethod
    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect data for the given profile and date range.

        Args:
            profile: Profile configuration with focus/filters
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            depth: Collection depth ('quick', 'default', 'deep')

        Returns:
            CollectorResult with items and sources
        """
        pass

    def get_depth_config(self, depth: str) -> Dict[str, Any]:
        """Get configuration for a given depth level."""
        configs = {
            "quick": {
                "max_items": 10,
                "timeout": 30,
            },
            "default": {
                "max_items": 25,
                "timeout": 60,
            },
            "deep": {
                "max_items": 50,
                "timeout": 120,
            },
        }
        return configs.get(depth, configs["default"])


class FinancialCollector(Collector):
    """Base class for financial data collectors."""

    @property
    def collector_type(self) -> str:
        return "financial"

    def get_symbols_to_track(self, profile: ProfileConfig) -> List[str]:
        """Get list of stock symbols to track from profile."""
        symbols = []
        for entity in profile.get_focused_entities("holding_companies"):
            symbol = entity.get("symbol")
            if symbol:
                symbols.append(symbol)
        return symbols


class NewsCollector(Collector):
    """Base class for news collectors."""

    @property
    def collector_type(self) -> str:
        return "news"

    def get_search_keywords(self, profile: ProfileConfig) -> List[str]:
        """Get keywords to search for from profile."""
        keywords = []

        # Add entity names
        for entity_type in profile.domain.entity_types:
            for entity in profile.get_focused_entities(entity_type):
                name = entity.get("name")
                if name:
                    keywords.append(name)

        # Add boost keywords
        keywords.extend(profile.get_boost_keywords())

        return keywords


class SocialCollector(Collector):
    """Base class for social media collectors."""

    @property
    def collector_type(self) -> str:
        return "social"

    def get_handles_to_track(self, profile: ProfileConfig) -> List[str]:
        """Get social media handles to track."""
        return profile.get_thought_leader_handles()


class RSSCollector(Collector):
    """Base class for RSS feed collectors."""

    @property
    def collector_type(self) -> str:
        return "rss"

    def get_feeds(self, profile: ProfileConfig) -> List[Dict[str, str]]:
        """Get RSS feeds to fetch from domain/profile."""
        feeds = []

        # Get domain publications
        domain_pubs = profile.domain.publications

        # Filter by profile preferences
        profile_pubs = set(profile.publications) if profile.publications else None

        for pub in domain_pubs:
            name = pub.get("name", "")
            rss_url = pub.get("rss")

            if not rss_url:
                continue

            if profile_pubs and name not in profile_pubs:
                continue

            feeds.append({"name": name, "url": rss_url})

        return feeds


class AwardsCollector(Collector):
    """Base class for awards/accolades collectors."""

    @property
    def collector_type(self) -> str:
        return "awards"


class PEActivityCollector(Collector):
    """Base class for private equity activity collectors."""

    @property
    def collector_type(self) -> str:
        return "pe_activity"
