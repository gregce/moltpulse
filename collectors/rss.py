"""RSS feed collector for Moltos."""

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

from core.collector_base import CollectorResult, RSSCollector as RSSCollectorBase
from core.lib import http, schema
from core.profile_loader import ProfileConfig


class RSSCollector(RSSCollectorBase):
    """Collector for RSS/Atom feeds from publications."""

    @property
    def name(self) -> str:
        return "RSS Feed"

    def is_available(self) -> bool:
        """RSS collector is always available (no API key needed)."""
        return True

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect articles from RSS feeds."""
        feeds = self.get_feeds(profile)
        if not feeds:
            return CollectorResult(
                items=[],
                sources=[],
                error="No RSS feeds configured",
            )

        depth_config = self.get_depth_config(depth)
        max_items_per_feed = depth_config.get("max_items", 25) // max(len(feeds), 1)

        items: List[schema.NewsItem] = []
        sources: List[schema.Source] = []
        errors = []

        for feed in feeds:
            feed_name = feed.get("name", "Unknown")
            feed_url = feed.get("url", "")

            if not feed_url:
                continue

            try:
                feed_items = self._fetch_feed(feed_url, feed_name, from_date, to_date)
                items.extend(feed_items[:max_items_per_feed])

                if feed_items:
                    sources.append(
                        schema.Source(
                            name=feed_name,
                            url=feed_url,
                            date_accessed=datetime.now(timezone.utc).date().isoformat(),
                        )
                    )
            except Exception as e:
                errors.append(f"{feed_name}: {e}")

        return CollectorResult(
            items=items,
            sources=sources,
            error="; ".join(errors) if errors and not items else None,
        )

    def _fetch_feed(
        self,
        url: str,
        source_name: str,
        from_date: str,
        to_date: str,
    ) -> List[schema.NewsItem]:
        """Fetch and parse an RSS feed."""
        try:
            content = http.fetch_text(url, timeout=30)
        except http.HTTPError:
            return []

        # Parse XML
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return []

        items = []

        # Detect feed type and parse accordingly
        if root.tag == "rss":
            items = self._parse_rss(root, source_name, from_date, to_date)
        elif root.tag.endswith("feed"):  # Atom
            items = self._parse_atom(root, source_name, from_date, to_date)
        elif root.tag == "rdf:RDF" or "rdf" in root.tag.lower():
            items = self._parse_rdf(root, source_name, from_date, to_date)

        return items

    def _parse_rss(
        self,
        root: ET.Element,
        source_name: str,
        from_date: str,
        to_date: str,
    ) -> List[schema.NewsItem]:
        """Parse RSS 2.0 feed."""
        items = []
        channel = root.find("channel")
        if channel is None:
            return items

        for item in channel.findall("item"):
            title = self._get_text(item, "title")
            link = self._get_text(item, "link")
            description = self._get_text(item, "description")
            pub_date = self._get_text(item, "pubDate")

            if not title or not link:
                continue

            date_str = self._parse_rss_date(pub_date)

            # Filter by date range
            if date_str:
                if date_str < from_date or date_str > to_date:
                    continue

            items.append(
                schema.NewsItem(
                    id=hashlib.md5(link.encode()).hexdigest()[:12],
                    title=self._clean_html(title),
                    url=link,
                    source_name=source_name,
                    snippet=self._clean_html(description)[:300] if description else "",
                    date=date_str,
                    date_confidence="high" if date_str else "low",
                    relevance=0.6,  # RSS items get base relevance
                )
            )

        return items

    def _parse_atom(
        self,
        root: ET.Element,
        source_name: str,
        from_date: str,
        to_date: str,
    ) -> List[schema.NewsItem]:
        """Parse Atom feed."""
        items = []

        # Handle namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns) or root.findall("entry"):
            title = self._get_text(entry, "atom:title", ns) or self._get_text(entry, "title")

            # Get link (may be in href attribute)
            link_elem = entry.find("atom:link", ns) or entry.find("link")
            link = ""
            if link_elem is not None:
                link = link_elem.get("href", "") or link_elem.text or ""

            summary = self._get_text(entry, "atom:summary", ns) or self._get_text(entry, "summary")
            updated = self._get_text(entry, "atom:updated", ns) or self._get_text(entry, "updated")
            published = self._get_text(entry, "atom:published", ns) or self._get_text(entry, "published")

            if not title or not link:
                continue

            date_str = self._parse_iso_date(published or updated)

            if date_str:
                if date_str < from_date or date_str > to_date:
                    continue

            items.append(
                schema.NewsItem(
                    id=hashlib.md5(link.encode()).hexdigest()[:12],
                    title=self._clean_html(title),
                    url=link,
                    source_name=source_name,
                    snippet=self._clean_html(summary)[:300] if summary else "",
                    date=date_str,
                    date_confidence="high" if date_str else "low",
                    relevance=0.6,
                )
            )

        return items

    def _parse_rdf(
        self,
        root: ET.Element,
        source_name: str,
        from_date: str,
        to_date: str,
    ) -> List[schema.NewsItem]:
        """Parse RDF/RSS 1.0 feed."""
        items = []

        # RDF uses namespaces
        ns = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rss": "http://purl.org/rss/1.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        for item in root.findall("rss:item", ns) or root.findall("item"):
            title = self._get_text(item, "rss:title", ns) or self._get_text(item, "title")
            link = self._get_text(item, "rss:link", ns) or self._get_text(item, "link")
            description = self._get_text(item, "rss:description", ns) or self._get_text(item, "description")
            dc_date = self._get_text(item, "dc:date", ns)

            if not title or not link:
                continue

            date_str = self._parse_iso_date(dc_date)

            items.append(
                schema.NewsItem(
                    id=hashlib.md5(link.encode()).hexdigest()[:12],
                    title=self._clean_html(title),
                    url=link,
                    source_name=source_name,
                    snippet=self._clean_html(description)[:300] if description else "",
                    date=date_str,
                    date_confidence="high" if date_str else "low",
                    relevance=0.6,
                )
            )

        return items

    def _get_text(self, elem: ET.Element, tag: str, ns: Optional[Dict[str, str]] = None) -> str:
        """Get text content from element."""
        if ns:
            child = elem.find(tag, ns)
        else:
            child = elem.find(tag)

        if child is not None and child.text:
            return child.text.strip()
        return ""

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse RSS pubDate format to YYYY-MM-DD."""
        if not date_str:
            return None

        try:
            dt = parsedate_to_datetime(date_str)
            return dt.date().isoformat()
        except (ValueError, TypeError):
            pass

        return None

    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse ISO date format to YYYY-MM-DD."""
        if not date_str:
            return None

        try:
            # Handle various ISO formats
            date_str = date_str.replace("Z", "+00:00")
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str)
                return dt.date().isoformat()
            else:
                return date_str[:10]  # Already YYYY-MM-DD
        except ValueError:
            pass

        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Simple HTML tag removal
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&\w+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
