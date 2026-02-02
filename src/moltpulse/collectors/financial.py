"""Financial data collector using Alpha Vantage API."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib

from moltpulse.core.collector_base import Collector, CollectorResult, FinancialCollector
from moltpulse.core.lib import http, schema
from moltpulse.core.profile_loader import ProfileConfig


ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageCollector(FinancialCollector):
    """Collector for stock market data via Alpha Vantage API."""

    REQUIRED_API_KEYS = ["ALPHA_VANTAGE_API_KEY"]

    @property
    def name(self) -> str:
        return "Alpha Vantage Financial"

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect financial data for tracked symbols."""
        api_key = self.config.get("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return CollectorResult(
                items=[],
                sources=[],
                error="Alpha Vantage API key not configured",
            )

        symbols = self.get_symbols_to_track(profile)
        if not symbols:
            return CollectorResult(
                items=[],
                sources=[],
                error="No symbols to track in profile",
            )

        depth_config = self.get_depth_config(depth)
        max_symbols = min(len(symbols), depth_config.get("max_items", 10))

        items: List[schema.FinancialItem] = []
        sources: List[schema.Source] = []
        errors = []

        for symbol in symbols[:max_symbols]:
            try:
                quote = self._fetch_global_quote(symbol, api_key)
                if quote:
                    item = self._parse_quote(quote, symbol, profile)
                    if item:
                        items.append(item)
                        sources.append(
                            schema.Source(
                                name="Alpha Vantage",
                                url=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}",
                                date_accessed=datetime.now(timezone.utc).date().isoformat(),
                            )
                        )
            except Exception as e:
                errors.append(f"{symbol}: {e}")

        error_msg = "; ".join(errors) if errors else None

        return CollectorResult(
            items=items,
            sources=sources,
            error=error_msg if error_msg and not items else None,
        )

    def _fetch_global_quote(self, symbol: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch global quote for a symbol."""
        url = f"{ALPHA_VANTAGE_BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

        try:
            response = http.get(url, timeout=30)
            return response.get("Global Quote", {})
        except http.HTTPError as e:
            if e.status_code == 429:
                # Rate limited
                return None
            raise

    def _parse_quote(
        self,
        quote: Dict[str, Any],
        symbol: str,
        profile: ProfileConfig,
    ) -> Optional[schema.FinancialItem]:
        """Parse Alpha Vantage quote response to FinancialItem."""
        if not quote:
            return None

        # Alpha Vantage uses numbered keys like "05. price"
        price = quote.get("05. price")
        change = quote.get("09. change")
        change_pct = quote.get("10. change percent")
        latest_day = quote.get("07. latest trading day")

        if not price:
            return None

        # Parse change percent (comes as "1.23%")
        pct_value = None
        if change_pct:
            try:
                pct_value = float(change_pct.rstrip("%"))
            except ValueError:
                pass

        # Get entity name from profile
        entity_name = symbol
        for entity in profile.get_focused_entities("holding_companies"):
            if entity.get("symbol") == symbol:
                entity_name = entity.get("name", symbol)
                break

        return schema.FinancialItem(
            id=hashlib.md5(f"{symbol}:{latest_day}".encode()).hexdigest()[:12],
            entity_symbol=symbol,
            entity_name=entity_name,
            metric_type="stock_price",
            value=float(price),
            change_pct=pct_value,
            date=latest_day,
            date_confidence="high",
            source_url=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}",
            source_name="Alpha Vantage",
            relevance=0.8,  # Financial data is always relevant to tracked entities
        )


class YahooFinanceCollector(FinancialCollector):
    """Fallback collector using Yahoo Finance (no API key needed)."""

    REQUIRED_API_KEYS = []  # No API key needed

    @property
    def name(self) -> str:
        return "Yahoo Finance"

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect financial data from Yahoo Finance."""
        symbols = self.get_symbols_to_track(profile)
        if not symbols:
            return CollectorResult(
                items=[],
                sources=[],
                error="No symbols to track in profile",
            )

        depth_config = self.get_depth_config(depth)
        max_symbols = min(len(symbols), depth_config.get("max_items", 10))

        items: List[schema.FinancialItem] = []
        sources: List[schema.Source] = []

        for symbol in symbols[:max_symbols]:
            try:
                quote = self._fetch_yahoo_quote(symbol)
                if quote:
                    item = self._parse_yahoo_quote(quote, symbol, profile)
                    if item:
                        items.append(item)
                        sources.append(
                            schema.Source(
                                name="Yahoo Finance",
                                url=f"https://finance.yahoo.com/quote/{symbol}",
                                date_accessed=datetime.now(timezone.utc).date().isoformat(),
                            )
                        )
            except Exception:
                continue

        return CollectorResult(items=items, sources=sources)

    def _fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Yahoo Finance API."""
        # Yahoo Finance v8 API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"

        try:
            response = http.get(url, timeout=30)
            chart = response.get("chart", {})
            result = chart.get("result", [])
            if result:
                return result[0]
        except http.HTTPError:
            pass

        return None

    def _parse_yahoo_quote(
        self,
        data: Dict[str, Any],
        symbol: str,
        profile: ProfileConfig,
    ) -> Optional[schema.FinancialItem]:
        """Parse Yahoo Finance response."""
        meta = data.get("meta", {})
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose")

        if not price:
            return None

        change_pct = None
        if prev_close and prev_close > 0:
            change_pct = ((price - prev_close) / prev_close) * 100

        entity_name = symbol
        for entity in profile.get_focused_entities("holding_companies"):
            if entity.get("symbol") == symbol:
                entity_name = entity.get("name", symbol)
                break

        return schema.FinancialItem(
            id=hashlib.md5(f"yahoo:{symbol}:{datetime.now().date()}".encode()).hexdigest()[:12],
            entity_symbol=symbol,
            entity_name=entity_name,
            metric_type="stock_price",
            value=float(price),
            change_pct=change_pct,
            date=datetime.now(timezone.utc).date().isoformat(),
            date_confidence="high",
            source_url=f"https://finance.yahoo.com/quote/{symbol}",
            source_name="Yahoo Finance",
            relevance=0.8,
        )
