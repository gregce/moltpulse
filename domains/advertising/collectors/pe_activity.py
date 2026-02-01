"""Private equity and M&A activity collector for advertising domain."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from core.collector_base import PEActivityCollector as PEActivityCollectorBase, CollectorResult
from core.lib import http, schema
from core.profile_loader import ProfileConfig


# Key PE firms active in advertising/marketing
PE_FIRMS = [
    "Bain Capital",
    "Blackstone",
    "Vista Equity",
    "KKR",
    "Carlyle",
    "Providence Equity",
    "Golden Gate Capital",
    "Platinum Equity",
    "Advent International",
    "TPG Capital",
    "Thoma Bravo",
    "Silver Lake",
]

# Keywords for M&A search
MA_KEYWORDS = [
    "acquisition",
    "merger",
    "acquired",
    "buys",
    "acquires",
    "investment",
    "stake",
    "deal",
    "private equity",
    "PE investment",
]


class PEActivityCollector(PEActivityCollectorBase):
    """Collector for PE investments and M&A in advertising industry."""

    @property
    def name(self) -> str:
        return "PE & M&A Activity"

    def is_available(self) -> bool:
        """Available if news APIs are configured or Intellizence API."""
        return bool(
            self.config.get("INTELLIZENCE_API_KEY")
            or self.config.get("NEWSDATA_API_KEY")
            or self.config.get("NEWSAPI_API_KEY")
        )

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect PE and M&A activity in the advertising industry."""
        items: List[schema.PEActivityItem] = []
        sources: List[schema.Source] = []
        errors = []

        depth_config = self.get_depth_config(depth)
        max_items = depth_config.get("max_items", 20)

        # Try Intellizence API first (if available)
        if self.config.get("INTELLIZENCE_API_KEY"):
            try:
                intel_items, intel_sources = self._collect_from_intellizence(
                    from_date, to_date, max_items
                )
                items.extend(intel_items)
                sources.extend(intel_sources)
            except Exception as e:
                errors.append(f"Intellizence: {e}")

        # Supplement with news search
        if len(items) < max_items:
            try:
                news_items, news_sources = self._collect_from_news(
                    profile, from_date, to_date, max_items - len(items)
                )
                items.extend(news_items)
                sources.extend(news_sources)
            except Exception as e:
                errors.append(f"News search: {e}")

        return CollectorResult(
            items=items,
            sources=sources,
            error="; ".join(errors) if errors and not items else None,
        )

    def _collect_from_intellizence(
        self,
        from_date: str,
        to_date: str,
        max_items: int,
    ) -> tuple[List[schema.PEActivityItem], List[schema.Source]]:
        """Collect from Intellizence M&A API."""
        api_key = self.config.get("INTELLIZENCE_API_KEY")
        if not api_key:
            return [], []

        # Intellizence API endpoint (placeholder - actual API would be used)
        # url = f"https://api.intellizence.com/v1/deals?industry=advertising&from={from_date}&to={to_date}"

        # For now, return empty - would implement actual API call
        return [], []

    def _collect_from_news(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        max_items: int,
    ) -> tuple[List[schema.PEActivityItem], List[schema.Source]]:
        """Collect PE/M&A activity from news search."""
        items = []
        sources = []

        # Build search query
        agency_terms = []
        for entity in profile.get_focused_entities("holding_companies"):
            agency_terms.append(entity.get("name", ""))

        # Combine with M&A keywords
        search_terms = agency_terms[:5] + ["advertising agency", "marketing agency"]
        ma_query = f"({' OR '.join(MA_KEYWORDS)}) AND ({' OR '.join(search_terms)})"

        # Use news API if available
        if self.config.get("NEWSDATA_API_KEY"):
            try:
                news_results = self._search_newsdata(ma_query, from_date, max_items)
                for article in news_results:
                    item = self._parse_news_to_pe_activity(article)
                    if item:
                        items.append(item)
                        sources.append(
                            schema.Source(
                                name=article.get("source_id", "News"),
                                url=article.get("link", ""),
                            )
                        )
            except Exception:
                pass

        return items, sources

    def _search_newsdata(
        self,
        query: str,
        from_date: str,
        max_items: int,
    ) -> List[Dict[str, Any]]:
        """Search NewsData.io for M&A articles."""
        api_key = self.config.get("NEWSDATA_API_KEY")
        if not api_key:
            return []

        encoded_query = quote_plus(query)
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={encoded_query}&language=en"

        try:
            response = http.get(url, timeout=60)
            return response.get("results", [])[:max_items]
        except http.HTTPError:
            return []

    def _parse_news_to_pe_activity(
        self,
        article: Dict[str, Any],
    ) -> Optional[schema.PEActivityItem]:
        """Parse news article to PE activity item if relevant."""
        title = article.get("title", "")
        description = article.get("description", "")
        content = f"{title} {description}".lower()

        # Check if it's actually about M&A
        is_ma = any(kw.lower() in content for kw in MA_KEYWORDS)
        if not is_ma:
            return None

        # Try to extract activity type
        activity_type = "unknown"
        if any(w in content for w in ["acquir", "acquisition", "buys", "bought"]):
            activity_type = "acquisition"
        elif "merger" in content:
            activity_type = "merger"
        elif any(w in content for w in ["invest", "stake", "funding"]):
            activity_type = "investment"

        # Try to extract deal value (very basic)
        deal_value = None
        deal_value_str = ""
        import re

        value_match = re.search(r"\$(\d+(?:\.\d+)?)\s*(billion|million|B|M)", content, re.IGNORECASE)
        if value_match:
            num = float(value_match.group(1))
            unit = value_match.group(2).lower()
            if unit in ("billion", "b"):
                deal_value = num * 1_000_000_000
                deal_value_str = f"${num}B"
            elif unit in ("million", "m"):
                deal_value = num * 1_000_000
                deal_value_str = f"${num}M"

        # Parse date
        pub_date = article.get("pubDate") or article.get("pubDateTZ")
        date_str = None
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace(" ", "T").replace("Z", "+00:00"))
                date_str = dt.date().isoformat()
            except ValueError:
                pass

        return schema.PEActivityItem(
            id=hashlib.md5(article.get("link", title).encode()).hexdigest()[:12],
            activity_type=activity_type,
            target_name=self._extract_company_name(title, "target"),
            acquirer_name=self._extract_company_name(title, "acquirer"),
            deal_value=deal_value,
            deal_value_str=deal_value_str,
            date=date_str,
            date_confidence="high" if date_str else "low",
            source_url=article.get("link", ""),
            source_name=article.get("source_id", "News"),
            details=description[:500] if description else "",
            relevance=0.7,
        )

    def _extract_company_name(self, title: str, role: str) -> str:
        """Extract company name from title based on role.

        This is a simplified extraction - production would use NER.
        """
        # Very basic extraction - would use NLP in production
        words = title.split()

        if role == "acquirer":
            # Usually before "acquires", "buys", etc.
            for i, word in enumerate(words):
                if word.lower() in ["acquires", "buys", "to", "acquire"]:
                    return " ".join(words[:i]) if i > 0 else ""
        else:
            # Usually after "acquires", "buys", etc.
            for i, word in enumerate(words):
                if word.lower() in ["acquires", "buys"]:
                    return " ".join(words[i + 1 :]) if i < len(words) - 1 else ""

        return ""
