"""Awards and accolades collector for advertising domain."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.collector_base import AwardsCollector as AwardsCollectorBase, CollectorResult
from core.lib import http, schema
from core.profile_loader import ProfileConfig
from collectors.web_scraper import WebScraperCollector


# Known award shows with their scraping configurations
AWARD_SHOWS = {
    "cannes_lions": {
        "name": "Cannes Lions",
        "url": "https://www.canneslions.com",
        "medals": ["Grand Prix", "Gold", "Silver", "Bronze"],
    },
    "effie": {
        "name": "Effie Awards",
        "url": "https://www.effie.org",
        "medals": ["Grand Effie", "Gold", "Silver", "Bronze"],
    },
    "clio": {
        "name": "Clio Awards",
        "url": "https://clios.com",
        "medals": ["Grand Clio", "Gold", "Silver", "Bronze"],
    },
}


class AwardsCollector(AwardsCollectorBase):
    """Collector for advertising industry awards."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._scraper = WebScraperCollector(config)

    @property
    def name(self) -> str:
        return "Advertising Awards"

    def is_available(self) -> bool:
        """Awards collector is available if scraping is enabled."""
        return self._scraper.is_available()

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect recent award wins."""
        items: List[schema.AwardItem] = []
        sources: List[schema.Source] = []
        errors = []

        # Get year from date range
        try:
            year = int(to_date[:4])
        except (ValueError, IndexError):
            year = datetime.now().year

        # Get agencies to focus on from profile
        focus_agencies = self._get_focus_agencies(profile)

        # Collect from each award show
        # Note: In production, this would scrape actual award databases
        # For now, we search news for award announcements
        depth_config = self.get_depth_config(depth)

        for show_id, show_config in AWARD_SHOWS.items():
            try:
                show_items = self._collect_show_awards(
                    show_config,
                    year,
                    focus_agencies,
                    from_date,
                    to_date,
                )
                items.extend(show_items[:depth_config.get("max_items", 10)])

                if show_items:
                    sources.append(
                        schema.Source(
                            name=show_config["name"],
                            url=show_config["url"],
                            date_accessed=datetime.now(timezone.utc).date().isoformat(),
                        )
                    )
            except Exception as e:
                errors.append(f"{show_config['name']}: {e}")

        return CollectorResult(
            items=items,
            sources=sources,
            error="; ".join(errors) if errors and not items else None,
        )

    def _get_focus_agencies(self, profile: ProfileConfig) -> List[str]:
        """Get list of agencies to focus on from profile."""
        agencies = []

        # Add holding company names
        for entity in profile.get_focused_entities("holding_companies"):
            agencies.append(entity.get("name", ""))

        # Add independent agencies if defined
        for entity in profile.get_focused_entities("independent_agencies"):
            agencies.append(entity.get("name", ""))

        return [a for a in agencies if a]

    def _collect_show_awards(
        self,
        show_config: Dict[str, Any],
        year: int,
        focus_agencies: List[str],
        from_date: str,
        to_date: str,
    ) -> List[schema.AwardItem]:
        """Collect awards from a specific show.

        In production, this would scrape the award show's winner database.
        For now, returns placeholder data structure.
        """
        items = []
        show_name = show_config["name"]
        show_url = show_config["url"]

        # This is where we would implement actual scraping
        # For now, search for award news via RSS/news collectors would fill this
        # The structure is ready for when scraping is implemented

        return items

    def _parse_scraped_award(
        self,
        raw: Dict[str, Any],
        show_id: str,
        show_config: Dict[str, Any],
    ) -> Optional[schema.AwardItem]:
        """Parse scraped data into AwardItem."""
        agency = raw.get("agency", "")
        campaign = raw.get("campaign", "")
        medal = raw.get("medal", "")
        category = raw.get("category", "")
        client = raw.get("client", "")
        year = raw.get("year", datetime.now().year)

        if not agency:
            return None

        # Determine holding company
        holding_company = self._identify_holding_company(agency)

        return schema.AwardItem(
            id=hashlib.md5(f"{show_id}:{agency}:{campaign}:{medal}".encode()).hexdigest()[:12],
            award_show=show_id,
            category=category,
            winner_agency=agency,
            holding_company=holding_company,
            campaign_name=campaign,
            client=client,
            year=year,
            medal=medal.lower(),
            source_url=show_config["url"],
            date=f"{year}-01-01",  # Approximate
            relevance=0.8,
        )

    def _identify_holding_company(self, agency: str) -> Optional[str]:
        """Identify which holding company owns an agency."""
        # Known agency-to-holding-company mappings
        mappings = {
            # WPP agencies
            "ogilvy": "WPP",
            "wunderman": "WPP",
            "grey": "WPP",
            "vmly&r": "WPP",
            "hogarth": "WPP",
            # Omnicom agencies
            "bbdo": "Omnicom",
            "ddb": "Omnicom",
            "tbwa": "Omnicom",
            "omg": "Omnicom",
            # Publicis agencies
            "leo burnett": "Publicis",
            "saatchi": "Publicis",
            "publicis": "Publicis",
            "starcom": "Publicis",
            # IPG agencies
            "mccann": "IPG",
            "fcb": "IPG",
            "mullen": "IPG",
            "weber": "IPG",
            # Dentsu agencies
            "dentsu": "Dentsu",
            "carat": "Dentsu",
            "isobar": "Dentsu",
            # Havas agencies
            "havas": "Havas",
            "arnold": "Havas",
        }

        agency_lower = agency.lower()
        for key, holding in mappings.items():
            if key in agency_lower:
                return holding

        return None
