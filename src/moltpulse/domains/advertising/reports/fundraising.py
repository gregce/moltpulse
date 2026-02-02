"""Fundraising outlook report for nonprofit sector targeting advertising industry."""

from datetime import datetime
from typing import Dict, List

from moltpulse.core.lib import schema
from moltpulse.core.report_base import FundraisingReportGenerator


class FundraisingReport(FundraisingReportGenerator):
    """Generate fundraising outlook for nonprofits in advertising sector.

    This report helps nonprofit fundraisers understand:
    - Industry health (are agencies in a position to give?)
    - Optimal timing for outreach
    - Key trends to leverage in pitches
    - 6-month, 1-year, and 3-year projections
    """

    def generate(
        self,
        data: Dict[str, List[schema.ItemType]],
        from_date: str,
        to_date: str,
    ) -> schema.Report:
        """Generate the fundraising outlook report."""
        report = self.create_report(from_date, to_date)
        report.title = f"FUNDRAISING OUTLOOK - {datetime.now().strftime('%B %Y')}"

        all_sources = []

        # INDUSTRY HEALTH section
        financial_items = data.get("financial", [])
        health_section = self._create_health_section(financial_items)
        report.sections.append(health_section)
        all_sources.extend(self.collect_sources(financial_items))

        # M&A INDICATOR section
        pe_items = data.get("pe_activity", [])
        ma_section = self._create_ma_indicator_section(pe_items)
        report.sections.append(ma_section)
        all_sources.extend(self.collect_sources(pe_items))

        # TIMING RECOMMENDATIONS section
        timing_section = self._create_timing_section(financial_items, pe_items)
        report.sections.append(timing_section)

        # KEY TRENDS section
        news_items = data.get("news", []) + data.get("rss", [])
        social_items = data.get("social", [])
        trends_section = self._create_trends_section(news_items, social_items)
        report.sections.append(trends_section)
        all_sources.extend(self.collect_sources(news_items[:5]))

        # 6-MONTH OUTLOOK section
        outlook_6m = self._create_6month_outlook(financial_items, pe_items, news_items)
        report.sections.append(outlook_6m)

        # 1-YEAR OUTLOOK section
        outlook_1y = self._create_1year_outlook(financial_items, pe_items, news_items)
        report.sections.append(outlook_1y)

        # 3-YEAR OUTLOOK section
        outlook_3y = self._create_3year_outlook(financial_items, pe_items, news_items)
        report.sections.append(outlook_3y)

        # Dedupe sources
        seen_urls = set()
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                report.all_sources.append(source)

        return report

    def _create_health_section(
        self,
        items: List[schema.FinancialItem],
    ) -> schema.ReportSection:
        """Create industry health assessment."""
        # Calculate overall health score
        positive = 0
        negative = 0
        neutral = 0

        for item in items:
            if item.change_pct is not None:
                if item.change_pct > 2:
                    positive += 1
                elif item.change_pct < -2:
                    negative += 1
                else:
                    neutral += 1

        # Determine health status
        if positive > negative:
            status = "POSITIVE"
            description = "Holding companies showing growth - favorable for fundraising"
        elif negative > positive:
            status = "CAUTIOUS"
            description = "Market volatility - be strategic with timing"
        else:
            status = "NEUTRAL"
            description = "Stable market - standard fundraising approach"

        # Calculate average change
        changes = [i.change_pct for i in items if i.change_pct is not None]
        avg_change = sum(changes) / len(changes) if changes else 0

        formatted_items = [{
            "status": status,
            "description": description,
            "avg_change_pct": round(avg_change, 2),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "holding_companies": [
                {
                    "name": i.entity_name,
                    "change": i.change_pct,
                    "source_url": i.source_url,
                }
                for i in items[:6]
            ],
        }]

        return schema.ReportSection(
            title="INDUSTRY HEALTH",
            items=formatted_items,
        )

    def _create_ma_indicator_section(
        self,
        items: List[schema.PEActivityItem],
    ) -> schema.ReportSection:
        """Create M&A activity indicator section."""
        deal_count = len(items)

        # M&A activity level
        if deal_count > 10:
            level = "HIGH"
            implication = "Active M&A suggests industry consolidation - target acquiring companies"
        elif deal_count > 5:
            level = "MODERATE"
            implication = "Normal deal flow - standard approach recommended"
        else:
            level = "LOW"
            implication = "Quiet period - agencies may be focused internally"

        formatted_items = [{
            "activity_level": level,
            "deal_count": deal_count,
            "implication": implication,
            "notable_deals": [
                {
                    "summary": f"{i.acquirer_name} {i.activity_type} {i.target_name}",
                    "value": i.deal_value_str,
                    "url": i.source_url,
                }
                for i in items[:5]
            ],
        }]

        return schema.ReportSection(
            title="M&A INDICATOR",
            items=formatted_items,
        )

    def _create_timing_section(
        self,
        financial_items: List[schema.FinancialItem],
        pe_items: List[schema.PEActivityItem],
    ) -> schema.ReportSection:
        """Create timing recommendations section."""
        now = datetime.now()
        month = now.month

        # General timing guidance based on agency calendar
        timing_notes = []

        if month in [1, 2]:
            timing_notes.append({
                "period": "Q1 (Now)",
                "recommendation": "GOOD",
                "reason": "Post-holiday, new budget cycles starting",
            })
        elif month in [3, 4]:
            timing_notes.append({
                "period": "Q1-Q2 Transition",
                "recommendation": "EXCELLENT",
                "reason": "Budget finalization period - decisions being made",
            })
        elif month in [5, 6]:
            timing_notes.append({
                "period": "Pre-Cannes",
                "recommendation": "MODERATE",
                "reason": "Industry focused on awards season",
            })
        elif month in [7, 8]:
            timing_notes.append({
                "period": "Summer",
                "recommendation": "SLOW",
                "reason": "Vacation season - decision-makers often unavailable",
            })
        elif month in [9, 10]:
            timing_notes.append({
                "period": "Fall Planning",
                "recommendation": "EXCELLENT",
                "reason": "Next year budgeting - ideal for multi-year commitments",
            })
        else:
            timing_notes.append({
                "period": "Holiday Season",
                "recommendation": "MODERATE",
                "reason": "Year-end giving possible, but attention divided",
            })

        # Best months
        timing_notes.append({
            "best_months": ["March", "April", "September", "October"],
            "avoid_months": ["July", "August", "December"],
        })

        return schema.ReportSection(
            title="TIMING RECOMMENDATIONS",
            items=timing_notes,
        )

    def _create_trends_section(
        self,
        news_items: List[schema.NewsItem],
        social_items: List[schema.SocialItem],
    ) -> schema.ReportSection:
        """Create key trends to leverage in fundraising pitches."""
        # Identify trends relevant to nonprofit positioning
        leverage_trends = [
            {
                "trend": "AI & Automation",
                "pitch_angle": "Support workforce transition and upskilling initiatives",
            },
            {
                "trend": "Sustainability & Purpose",
                "pitch_angle": "Partner on purpose-driven campaigns and CSR initiatives",
            },
            {
                "trend": "DEI Commitments",
                "pitch_angle": "Diversity programs and inclusive hiring pipelines",
            },
            {
                "trend": "Mental Health Awareness",
                "pitch_angle": "Industry wellness and burnout prevention programs",
            },
        ]

        return schema.ReportSection(
            title="TRENDS TO LEVERAGE",
            items=leverage_trends,
        )

    def _create_6month_outlook(
        self,
        financial_items: List[schema.FinancialItem],
        pe_items: List[schema.PEActivityItem],
        news_items: List[schema.NewsItem],
    ) -> schema.ReportSection:
        """Create 6-month outlook."""
        outlook = {
            "timeframe": "6 MONTHS",
            "confidence": "HIGH",
            "summary": self._generate_short_term_summary(financial_items, pe_items),
            "action_items": [
                "Identify and approach agencies with recent wins",
                "Target companies post-acquisition for goodwill initiatives",
                "Leverage industry events for relationship building",
            ],
        }

        return schema.ReportSection(
            title="6-MONTH OUTLOOK",
            items=[outlook],
        )

    def _create_1year_outlook(
        self,
        financial_items: List[schema.FinancialItem],
        pe_items: List[schema.PEActivityItem],
        news_items: List[schema.NewsItem],
    ) -> schema.ReportSection:
        """Create 1-year outlook."""
        outlook = {
            "timeframe": "1 YEAR",
            "confidence": "MODERATE",
            "summary": self._generate_medium_term_summary(financial_items, pe_items),
            "action_items": [
                "Build relationships with CSR and purpose teams",
                "Position for annual giving cycles",
                "Develop multi-year partnership proposals",
            ],
        }

        return schema.ReportSection(
            title="1-YEAR OUTLOOK",
            items=[outlook],
        )

    def _create_3year_outlook(
        self,
        financial_items: List[schema.FinancialItem],
        pe_items: List[schema.PEActivityItem],
        news_items: List[schema.NewsItem],
    ) -> schema.ReportSection:
        """Create 3-year outlook."""
        outlook = {
            "timeframe": "3 YEARS",
            "confidence": "SPECULATIVE",
            "summary": "Industry likely to continue consolidation; focus on building relationships with acquiring entities and emerging independent agencies",
            "considerations": [
                "AI transformation will reshape agency workforce",
                "Holding company structures may evolve",
                "Purpose-driven positioning increasingly important",
                "Privacy changes affecting business models",
            ],
            "action_items": [
                "Build institutional relationships, not just individual contacts",
                "Position as strategic partner for industry transformation",
                "Develop thought leadership on industry trends",
            ],
        }

        return schema.ReportSection(
            title="3-YEAR OUTLOOK",
            items=[outlook],
        )

    def _generate_short_term_summary(
        self,
        financial_items: List[schema.FinancialItem],
        pe_items: List[schema.PEActivityItem],
    ) -> str:
        """Generate short-term outlook summary."""
        changes = [i.change_pct for i in financial_items if i.change_pct is not None]
        avg_change = sum(changes) / len(changes) if changes else 0
        deal_count = len(pe_items)

        if avg_change > 0 and deal_count > 5:
            return "Strong market conditions with active M&A - excellent fundraising environment"
        elif avg_change > 0:
            return "Positive market sentiment - favorable for new relationships"
        elif deal_count > 5:
            return "Active consolidation - target acquiring companies for CSR partnerships"
        else:
            return "Stable conditions - focus on deepening existing relationships"

    def _generate_medium_term_summary(
        self,
        financial_items: List[schema.FinancialItem],
        pe_items: List[schema.PEActivityItem],
    ) -> str:
        """Generate medium-term outlook summary."""
        return "Industry continues digital transformation; position partnerships around workforce development, sustainability, and community impact"
