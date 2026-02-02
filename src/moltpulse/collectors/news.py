"""News collector using NewsData.io API."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from moltpulse.core.collector_base import CollectorResult, NewsCollector
from moltpulse.core.lib import http, schema
from moltpulse.core.profile_loader import ProfileConfig

NEWSDATA_BASE_URL = "https://newsdata.io/api/1/news"


class NewsDataCollector(NewsCollector):
    """Collector for news articles via NewsData.io API (primary)."""

    REQUIRED_API_KEYS = ["NEWSDATA_API_KEY"]
    COLLECTOR_PRIORITY = 10  # Primary news collector

    @property
    def name(self) -> str:
        return "NewsData.io"

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect news articles matching profile keywords."""
        api_key = self.config.get("NEWSDATA_API_KEY")
        if not api_key:
            return CollectorResult(
                items=[],
                sources=[],
                error="NewsData.io API key not configured",
            )

        keywords = self.get_search_keywords(profile)
        if not keywords:
            return CollectorResult(
                items=[],
                sources=[],
                error="No keywords to search in profile",
            )

        depth_config = self.get_depth_config(depth)
        max_results = depth_config.get("max_items", 25)

        # Build search query from top keywords
        query = " OR ".join(keywords[:5])  # Limit query complexity

        items: List[schema.NewsItem] = []
        sources: List[schema.Source] = []

        try:
            results = self._search_news(api_key, query, from_date, max_results)

            for article in results:
                item = self._parse_article(article, from_date, to_date, keywords)
                if item:
                    items.append(item)

                    # Add source
                    source_name = article.get("source_id") or article.get("source_name", "Unknown")
                    sources.append(
                        schema.Source(
                            name=source_name,
                            url=article.get("link", ""),
                            date_accessed=datetime.now(timezone.utc).date().isoformat(),
                        )
                    )

        except http.HTTPError as e:
            return CollectorResult(
                items=[],
                sources=[],
                error=f"NewsData.io API error: {e}",
            )

        return CollectorResult(items=items, sources=sources)

    def _search_news(
        self,
        api_key: str,
        query: str,
        from_date: str,
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """Search news articles."""
        encoded_query = quote_plus(query)
        url = f"{NEWSDATA_BASE_URL}?apikey={api_key}&q={encoded_query}&language=en"

        # Add date filter if supported
        # NewsData uses from_date format: 2024-01-15

        response = http.get(url, timeout=60)

        results = response.get("results", [])
        return results[:max_results]

    def _parse_article(
        self,
        article: Dict[str, Any],
        from_date: str,
        to_date: str,
        keywords: List[str],
    ) -> Optional[schema.NewsItem]:
        """Parse NewsData article to NewsItem."""
        title = article.get("title", "")
        url = article.get("link", "")

        if not title or not url:
            return None

        # Parse date
        pub_date = article.get("pubDate") or article.get("pubDateTZ")
        date_str = None
        if pub_date:
            try:
                # NewsData format: 2024-01-15 12:30:00
                dt = datetime.fromisoformat(pub_date.replace(" ", "T").replace("Z", "+00:00"))
                date_str = dt.date().isoformat()
            except ValueError:
                pass

        # Calculate relevance based on keyword matches
        content = f"{title} {article.get('description', '')}".lower()
        matches = sum(1 for kw in keywords if kw.lower() in content)
        relevance = min(0.5 + (matches * 0.1), 1.0)

        # Get categories
        categories = article.get("category", [])
        if isinstance(categories, str):
            categories = [categories]

        return schema.NewsItem(
            id=hashlib.md5(url.encode()).hexdigest()[:12],
            title=title,
            url=url,
            source_name=article.get("source_id") or article.get("source_name", "Unknown"),
            snippet=article.get("description", "")[:300],
            date=date_str,
            date_confidence="high" if date_str else "low",
            categories=categories,
            entities_mentioned=[],  # Could extract with NER
            relevance=relevance,
            why_relevant=f"Matched {matches} keywords" if matches else "",
        )


class NewsAPICollector(NewsCollector):
    """Fallback collector using NewsAPI.org."""

    REQUIRED_API_KEYS = ["NEWSAPI_API_KEY"]

    @property
    def name(self) -> str:
        return "NewsAPI.org"

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect news from NewsAPI."""
        api_key = self.config.get("NEWSAPI_API_KEY")
        if not api_key:
            return CollectorResult(
                items=[],
                sources=[],
                error="NewsAPI key not configured",
            )

        keywords = self.get_search_keywords(profile)
        if not keywords:
            return CollectorResult(items=[], sources=[])

        depth_config = self.get_depth_config(depth)
        query = " OR ".join(keywords[:5])

        try:
            url = f"https://newsapi.org/v2/everything?q={quote_plus(query)}&from={from_date}&sortBy=relevancy&apiKey={api_key}&language=en&pageSize={depth_config['max_items']}"

            response = http.get(url, timeout=60)
            articles = response.get("articles", [])

            items = []
            sources = []

            for article in articles:
                item = schema.NewsItem(
                    id=hashlib.md5(article.get("url", "").encode()).hexdigest()[:12],
                    title=article.get("title", ""),
                    url=article.get("url", ""),
                    source_name=article.get("source", {}).get("name", "Unknown"),
                    snippet=article.get("description", "")[:300],
                    date=article.get("publishedAt", "")[:10] if article.get("publishedAt") else None,
                    date_confidence="high",
                    relevance=0.7,
                )
                items.append(item)

                sources.append(
                    schema.Source(
                        name=article.get("source", {}).get("name", "Unknown"),
                        url=article.get("url", ""),
                    )
                )

            return CollectorResult(items=items, sources=sources)

        except http.HTTPError as e:
            return CollectorResult(items=[], sources=[], error=str(e))
