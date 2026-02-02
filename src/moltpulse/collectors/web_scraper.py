"""Playwright-based web scraper for MoltPulse."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from moltpulse.core.collector_base import Collector, CollectorResult
from moltpulse.core.lib import schema
from moltpulse.core.profile_loader import ProfileConfig


class WebScraperCollector(Collector):
    """Base class for Playwright-based web scraping.

    This collector provides infrastructure for scraping websites that
    don't have APIs. Domain-specific collectors (like awards scrapers)
    inherit from this.
    """

    @property
    def collector_type(self) -> str:
        return "web_scraper"

    @property
    def name(self) -> str:
        return "Web Scraper"

    def is_available(self) -> bool:
        """Check if scraping is enabled."""
        enabled = self.config.get("MOLTPULSE_ENABLE_SCRAPING", "true")
        return enabled.lower() in ("1", "true", "yes")

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Base implementation - subclasses override this."""
        return CollectorResult(
            items=[],
            sources=[],
            error="WebScraperCollector.collect() must be overridden",
        )

    def scrape_url(self, url: str, selectors: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Scrape a URL using Playwright.

        Args:
            url: URL to scrape
            selectors: Dict mapping field names to CSS selectors

        Returns:
            Dict of extracted data, or None on failure
        """
        try:
            # Try to import playwright
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None

        result = {}

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000)

                for field, selector in selectors.items():
                    try:
                        elements = page.query_selector_all(selector)
                        if elements:
                            if len(elements) == 1:
                                result[field] = elements[0].inner_text()
                            else:
                                result[field] = [e.inner_text() for e in elements]
                    except Exception:
                        result[field] = None

                browser.close()

            return result

        except Exception:
            return None

    def scrape_with_pagination(
        self,
        base_url: str,
        item_selector: str,
        field_selectors: Dict[str, str],
        next_selector: Optional[str] = None,
        max_pages: int = 5,
    ) -> List[Dict[str, Any]]:
        """Scrape multiple pages with pagination.

        Args:
            base_url: Starting URL
            item_selector: Selector for item containers
            field_selectors: Selectors for fields within each item
            next_selector: Selector for next page link
            max_pages: Maximum pages to scrape

        Returns:
            List of extracted items
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return []

        all_items = []
        current_url = base_url

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                for page_num in range(max_pages):
                    page.goto(current_url, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=10000)

                    # Extract items from current page
                    containers = page.query_selector_all(item_selector)

                    for container in containers:
                        item = {}
                        for field, selector in field_selectors.items():
                            try:
                                elem = container.query_selector(selector)
                                if elem:
                                    item[field] = elem.inner_text()

                                    # Also try to get href for links
                                    if "url" in field.lower() or "link" in field.lower():
                                        href = elem.get_attribute("href")
                                        if href:
                                            item[field] = href
                            except Exception:
                                pass

                        if item:
                            all_items.append(item)

                    # Check for next page
                    if next_selector:
                        next_link = page.query_selector(next_selector)
                        if next_link:
                            next_href = next_link.get_attribute("href")
                            if next_href:
                                # Handle relative URLs
                                if next_href.startswith("/"):
                                    parsed = urlparse(current_url)
                                    current_url = f"{parsed.scheme}://{parsed.netloc}{next_href}"
                                else:
                                    current_url = next_href
                            else:
                                break
                        else:
                            break
                    else:
                        break

                browser.close()

        except Exception:
            pass

        return all_items

    def parse_items_to_news(
        self,
        raw_items: List[Dict[str, Any]],
        source_name: str,
        from_date: str,
        to_date: str,
    ) -> List[schema.NewsItem]:
        """Convert scraped items to NewsItem schema."""
        items = []

        for raw in raw_items:
            title = raw.get("title", "")
            url = raw.get("url", "") or raw.get("link", "")

            if not title:
                continue

            # Parse date if present
            date_str = raw.get("date")
            if date_str:
                # Try common date formats
                date_str = self._parse_date(date_str)

            items.append(
                schema.NewsItem(
                    id=hashlib.md5((url or title).encode()).hexdigest()[:12],
                    title=title,
                    url=url,
                    source_name=source_name,
                    snippet=raw.get("description", "")[:300] or raw.get("summary", "")[:300],
                    date=date_str,
                    date_confidence="med" if date_str else "low",
                    relevance=0.6,
                )
            )

        return items

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Try to parse date string to YYYY-MM-DD."""
        import re

        if not date_str:
            return None

        # Clean up
        date_str = date_str.strip()

        # Already in ISO format
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str[:10]

        # Common formats
        formats = [
            "%B %d, %Y",  # January 15, 2024
            "%b %d, %Y",  # Jan 15, 2024
            "%d %B %Y",  # 15 January 2024
            "%d %b %Y",  # 15 Jan 2024
            "%m/%d/%Y",  # 01/15/2024
            "%d/%m/%Y",  # 15/01/2024
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue

        return None
