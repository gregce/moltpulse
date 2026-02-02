"""Weekly digest report generator for advertising domain."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from moltpulse.core.lib import schema
from moltpulse.core.report_base import WeeklyDigestGenerator


class WeeklyDigestReport(WeeklyDigestGenerator):
    """Generate comprehensive weekly digest for advertising industry."""

    def generate(
        self,
        data: Dict[str, List[schema.ItemType]],
        from_date: str,
        to_date: str,
    ) -> schema.Report:
        """Generate the weekly digest report."""
        report = self.create_report(from_date, to_date)
        report.title = f"MOLTOS WEEKLY DIGEST - Week of {from_date}"

        all_sources = []

        # MARKET OVERVIEW section
        financial_items = data.get("financial", [])
        if financial_items:
            market_section = self._create_market_section(financial_items)
            report.sections.append(market_section)
            all_sources.extend(self.collect_sources(financial_items))

        # NEWS ROUNDUP section (more items than daily)
        news_items = data.get("news", []) + data.get("rss", [])
        if news_items:
            news_section = self._create_news_roundup(news_items[:15])
            report.sections.append(news_section)
            all_sources.extend(self.collect_sources(news_items[:15]))

        # AGENCY MOMENTUM section (awards)
        award_items = data.get("awards", [])
        if award_items:
            awards_section = self._create_awards_section(award_items)
            report.sections.append(awards_section)
            all_sources.extend(self.collect_sources(award_items))

        # THOUGHT LEADERSHIP section
        social_items = data.get("social", [])
        if social_items:
            social_section = self._create_thought_leadership_section(social_items[:10])
            report.sections.append(social_section)
            all_sources.extend(self.collect_sources(social_items[:10]))

        # M&A ACTIVITY section
        pe_items = data.get("pe_activity", [])
        if pe_items:
            pe_section = self._create_ma_section(pe_items)
            report.sections.append(pe_section)
            all_sources.extend(self.collect_sources(pe_items))

        # TREND SPOTTING section
        trend_section = self._create_trends_section(news_items, social_items)
        if trend_section.items:
            report.sections.append(trend_section)

        # Dedupe sources
        seen_urls = set()
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                report.all_sources.append(source)

        return report

    def _create_market_section(
        self,
        items: List[schema.FinancialItem],
    ) -> schema.ReportSection:
        """Create market overview section with week-over-week analysis."""
        formatted_items = []

        # Calculate summary stats
        total_change = 0
        gainers = []
        losers = []

        for item in items:
            if item.change_pct is not None:
                total_change += item.change_pct
                if item.change_pct > 0:
                    gainers.append(item)
                elif item.change_pct < 0:
                    losers.append(item)

            formatted_items.append({
                "symbol": item.entity_symbol,
                "name": item.entity_name,
                "price": item.value,
                "change_pct": item.change_pct,
                "source_url": item.source_url,
            })

        avg_change = total_change / len(items) if items else 0

        return schema.ReportSection(
            title="MARKET OVERVIEW",
            items=formatted_items,
            sources=[
                schema.Source(
                    name=items[0].source_name if items else "Financial Data",
                    url=items[0].source_url if items else "",
                )
            ],
        )

    def _create_news_roundup(
        self,
        items: List[schema.NewsItem],
    ) -> schema.ReportSection:
        """Create comprehensive news roundup."""
        # Group by category if available
        by_category: Dict[str, List] = {}
        uncategorized = []

        for item in items:
            if item.categories:
                cat = item.categories[0]
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(item.to_dict())
            else:
                uncategorized.append(item.to_dict())

        formatted_items = []
        for cat, cat_items in by_category.items():
            formatted_items.extend(cat_items)
        formatted_items.extend(uncategorized)

        return schema.ReportSection(
            title="NEWS ROUNDUP",
            items=formatted_items[:15],
        )

    def _create_awards_section(
        self,
        items: List[schema.AwardItem],
    ) -> schema.ReportSection:
        """Create agency momentum / awards section."""
        # Group by holding company
        by_holding: Dict[str, List] = {}

        for item in items:
            holding = item.holding_company or "Independent"
            if holding not in by_holding:
                by_holding[holding] = []
            by_holding[holding].append(item.to_dict())

        formatted_items = []
        for holding, awards in by_holding.items():
            formatted_items.append({
                "holding_company": holding,
                "award_count": len(awards),
                "awards": awards,
            })

        return schema.ReportSection(
            title="AGENCY MOMENTUM",
            items=formatted_items,
        )

    def _create_thought_leadership_section(
        self,
        items: List[schema.SocialItem],
    ) -> schema.ReportSection:
        """Create thought leadership insights section."""
        formatted_items = []

        for item in items:
            formatted_items.append({
                "author": item.author_name,
                "handle": f"@{item.author_handle}",
                "text": item.text,
                "url": item.url,
                "engagement": {
                    "likes": item.engagement.likes if item.engagement else 0,
                    "reposts": item.engagement.reposts if item.engagement else 0,
                },
                "date": item.date,
            })

        return schema.ReportSection(
            title="THOUGHT LEADERSHIP",
            items=formatted_items,
        )

    def _create_ma_section(
        self,
        items: List[schema.PEActivityItem],
    ) -> schema.ReportSection:
        """Create M&A activity section."""
        formatted_items = []

        # Sort by deal value if available
        sorted_items = sorted(
            items,
            key=lambda x: x.deal_value or 0,
            reverse=True,
        )

        for item in sorted_items:
            formatted_items.append({
                "activity_type": item.activity_type,
                "target": item.target_name,
                "acquirer": item.acquirer_name,
                "deal_value": item.deal_value_str,
                "date": item.date,
                "details": item.details[:200] if item.details else "",
                "url": item.source_url,
                "source": item.source_name,
            })

        return schema.ReportSection(
            title="M&A ACTIVITY",
            items=formatted_items,
        )

    def _create_trends_section(
        self,
        news_items: List[schema.NewsItem],
        social_items: List[schema.SocialItem],
    ) -> schema.ReportSection:
        """Create trend spotting section based on content analysis."""
        # Simple keyword frequency analysis
        keywords = {}
        trend_terms = [
            "AI", "artificial intelligence", "automation",
            "first-party data", "privacy", "cookies",
            "retail media", "CTV", "streaming",
            "sustainability", "purpose", "DEI",
            "in-house", "consultancy",
        ]

        content = ""
        for item in news_items:
            content += f" {item.title} {item.snippet}"
        for item in social_items:
            content += f" {item.text}"

        content_lower = content.lower()

        for term in trend_terms:
            count = content_lower.count(term.lower())
            if count > 0:
                keywords[term] = count

        # Sort by frequency
        sorted_trends = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

        formatted_items = [
            {"trend": term, "mentions": count}
            for term, count in sorted_trends[:5]
        ]

        return schema.ReportSection(
            title="TREND SPOTTING",
            items=formatted_items,
        )
