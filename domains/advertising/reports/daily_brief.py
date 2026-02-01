"""Daily brief report generator for advertising domain."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from core.lib import schema
from core.report_base import DailyBriefGenerator


class DailyBriefReport(DailyBriefGenerator):
    """Generate daily morning brief for advertising industry."""

    def generate(
        self,
        data: Dict[str, List[schema.ItemType]],
        from_date: str,
        to_date: str,
    ) -> schema.Report:
        """Generate the daily brief report."""
        report = self.create_report(from_date, to_date)
        report.title = f"MOLTOS DAILY BRIEF - {to_date}"

        all_sources = []

        # STOCKS section
        financial_items = data.get("financial", [])
        if financial_items:
            stock_section = self._create_stocks_section(financial_items)
            report.sections.append(stock_section)
            all_sources.extend(self.collect_sources(financial_items))

        # TOP NEWS section
        news_items = data.get("news", []) + data.get("rss", [])
        if news_items:
            news_section = self._create_news_section(news_items[:5])
            report.sections.append(news_section)
            all_sources.extend(self.collect_sources(news_items[:5]))

        # THOUGHT LEADERS section
        social_items = data.get("social", [])
        if social_items:
            social_section = self._create_thought_leaders_section(social_items[:3])
            report.sections.append(social_section)
            all_sources.extend(self.collect_sources(social_items[:3]))

        # PE ALERTS section
        pe_items = data.get("pe_activity", [])
        if pe_items:
            pe_section = self._create_pe_section(pe_items[:3])
            report.sections.append(pe_section)
            all_sources.extend(self.collect_sources(pe_items[:3]))

        # Dedupe sources
        seen_urls = set()
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                report.all_sources.append(source)

        return report

    def _create_stocks_section(
        self,
        items: List[schema.FinancialItem],
    ) -> schema.ReportSection:
        """Create stocks summary section."""
        formatted_items = []

        for item in items[:6]:  # Top 6 stocks
            change_str = ""
            if item.change_pct is not None:
                sign = "+" if item.change_pct > 0 else ""
                change_str = f" ({sign}{item.change_pct:.1f}%)"

            formatted_items.append({
                "symbol": item.entity_symbol,
                "name": item.entity_name,
                "price": item.value,
                "change": item.change_pct,
                "change_str": change_str,
                "source_url": item.source_url,
                "source_name": item.source_name,
            })

        return schema.ReportSection(
            title="STOCKS",
            items=formatted_items,
            sources=[
                schema.Source(
                    name=items[0].source_name if items else "Alpha Vantage",
                    url=items[0].source_url if items else "",
                )
            ],
        )

    def _create_news_section(
        self,
        items: List[schema.NewsItem],
    ) -> schema.ReportSection:
        """Create top news section."""
        formatted_items = []

        for item in items:
            formatted_items.append({
                "title": item.title,
                "url": item.url,
                "source_name": item.source_name,
                "date": item.date,
                "snippet": item.snippet[:150] if item.snippet else "",
                "score": item.score,
            })

        return schema.ReportSection(
            title="TOP NEWS",
            items=formatted_items,
        )

    def _create_thought_leaders_section(
        self,
        items: List[schema.SocialItem],
    ) -> schema.ReportSection:
        """Create thought leaders section."""
        formatted_items = []

        for item in items:
            # Truncate text for brief
            text = item.text[:100] + "..." if len(item.text) > 100 else item.text

            engagement_str = ""
            if item.engagement:
                if item.engagement.likes:
                    engagement_str = f"({item.engagement.likes:,} likes)"

            formatted_items.append({
                "author": f"@{item.author_handle}",
                "author_name": item.author_name,
                "text": text,
                "url": item.url,
                "engagement": engagement_str,
                "date": item.date,
            })

        return schema.ReportSection(
            title="THOUGHT LEADERS",
            items=formatted_items,
        )

    def _create_pe_section(
        self,
        items: List[schema.PEActivityItem],
    ) -> schema.ReportSection:
        """Create PE/M&A alerts section."""
        formatted_items = []

        for item in items:
            summary = f"{item.acquirer_name} {item.activity_type} {item.target_name}"
            if item.deal_value_str:
                summary += f" ({item.deal_value_str})"

            formatted_items.append({
                "summary": summary,
                "activity_type": item.activity_type,
                "target": item.target_name,
                "acquirer": item.acquirer_name,
                "deal_value": item.deal_value_str,
                "url": item.source_url,
                "source_name": item.source_name,
            })

        return schema.ReportSection(
            title="PE ALERTS",
            items=formatted_items,
        )
