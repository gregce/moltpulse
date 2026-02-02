"""Abstract report base class for MoltPulse."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List

from .lib import schema
from .profile_loader import ProfileConfig


class ReportGenerator(ABC):
    """Abstract base class for report generators.

    All reports MUST include source citations for every item.
    """

    def __init__(self, profile: ProfileConfig):
        """Initialize report generator with profile."""
        self.profile = profile
        self.domain = profile.domain

    @property
    @abstractmethod
    def report_type(self) -> str:
        """Return the report type identifier (e.g., 'daily_brief')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable report name."""
        pass

    @abstractmethod
    def generate(
        self,
        data: Dict[str, List[schema.ItemType]],
        from_date: str,
        to_date: str,
    ) -> schema.Report:
        """Generate report from collected data.

        Args:
            data: Dict mapping collector type to list of items
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Complete Report with sections and sources
        """
        pass

    def create_report(self, from_date: str, to_date: str) -> schema.Report:
        """Create an empty report with metadata."""
        return schema.Report(
            title=self.get_title(),
            domain=self.domain.name,
            profile=self.profile.name,
            report_type=self.report_type,
            generated_at=datetime.now(timezone.utc).isoformat(),
            date_range_from=from_date,
            date_range_to=to_date,
        )

    def get_title(self) -> str:
        """Generate report title."""
        return f"{self.domain.display_name} - {self.name}"

    def collect_sources(self, items: List[schema.ItemType]) -> List[schema.Source]:
        """Collect all unique sources from items.

        This ensures every report has a SOURCES section with citations.
        """
        seen_urls = set()
        sources = []

        for item in items:
            # Get URL from item (different attributes for different types)
            url = getattr(item, "url", None) or getattr(item, "source_url", None)
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            # Get source name
            source_name = getattr(item, "source_name", None)
            if not source_name:
                # Try to extract from URL
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(url)
                    source_name = parsed.netloc.replace("www.", "")
                except Exception:
                    source_name = "Unknown"

            sources.append(
                schema.Source(
                    name=source_name,
                    url=url,
                    date_accessed=datetime.now(timezone.utc).date().isoformat(),
                )
            )

        return sources

    def format_item_with_citation(self, item: schema.ItemType) -> str:
        """Format an item with its source citation.

        Returns markdown with inline citation link.
        """
        url = getattr(item, "url", None) or getattr(item, "source_url", None)
        source_name = getattr(item, "source_name", None) or "Source"

        # Get primary text
        if isinstance(item, schema.NewsItem):
            text = item.title
        elif isinstance(item, schema.SocialItem):
            text = item.text[:100] + "..." if len(item.text) > 100 else item.text
        elif isinstance(item, schema.FinancialItem):
            text = f"{item.entity_name}: {item.value}"
            if item.change_pct:
                sign = "+" if item.change_pct > 0 else ""
                text += f" ({sign}{item.change_pct:.1f}%)"
        elif isinstance(item, schema.AwardItem):
            text = f"{item.winner_agency} - {item.campaign_name} ({item.medal})"
        elif isinstance(item, schema.PEActivityItem):
            text = f"{item.acquirer_name} {item.activity_type} {item.target_name}"
            if item.deal_value_str:
                text += f" ({item.deal_value_str})"
        else:
            text = str(item)

        if url:
            return f"{text}\n  [{source_name}]({url})"
        return text


class DailyBriefGenerator(ReportGenerator):
    """Base class for daily brief reports."""

    @property
    def report_type(self) -> str:
        return "daily_brief"

    @property
    def name(self) -> str:
        return "Daily Brief"


class WeeklyDigestGenerator(ReportGenerator):
    """Base class for weekly digest reports."""

    @property
    def report_type(self) -> str:
        return "weekly_digest"

    @property
    def name(self) -> str:
        return "Weekly Digest"


class FundraisingReportGenerator(ReportGenerator):
    """Base class for fundraising outlook reports."""

    @property
    def report_type(self) -> str:
        return "fundraising"

    @property
    def name(self) -> str:
        return "Fundraising Outlook"
