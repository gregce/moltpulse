"""Tests for schema module."""

import pytest

from core.lib.schema import (
    Source,
    Engagement,
    NewsItem,
    FinancialItem,
    SocialItem,
    AwardItem,
    PEActivityItem,
    ReportSection,
    Report,
)


class TestSource:
    """Tests for Source dataclass."""

    def test_creates_source(self):
        """Should create a source with name and url."""
        source = Source(name="Test Source", url="https://example.com")
        assert source.name == "Test Source"
        assert source.url == "https://example.com"

    def test_to_dict(self):
        """Should convert to dict."""
        source = Source(name="Test", url="https://example.com")
        d = source.to_dict()
        assert d["name"] == "Test"
        assert d["url"] == "https://example.com"


class TestEngagement:
    """Tests for Engagement dataclass."""

    def test_creates_engagement(self):
        """Should create engagement metrics."""
        eng = Engagement(likes=100, reposts=50, replies=25)
        assert eng.likes == 100
        assert eng.reposts == 50
        assert eng.replies == 25

    def test_default_values_are_none(self):
        """Should have None defaults (platform-specific fields)."""
        eng = Engagement()
        assert eng.likes is None
        assert eng.reposts is None

    def test_to_dict_filters_none(self):
        """to_dict should only include non-None values."""
        eng = Engagement(likes=100)
        d = eng.to_dict()
        assert d == {"likes": 100}


class TestNewsItem:
    """Tests for NewsItem dataclass."""

    def test_creates_news_item(self):
        """Should create a news item."""
        item = NewsItem(
            id="test123",
            title="Test Article",
            url="https://example.com/article",
            source_name="Test News",
            snippet="Test snippet",
        )
        assert item.id == "test123"
        assert item.title == "Test Article"

    def test_url_is_citation_source(self):
        """URL serves as the citation source."""
        item = NewsItem(
            id="test",
            title="Test",
            url="https://example.com",
            source_name="Test",
            snippet="Test snippet",
        )
        assert item.url == "https://example.com"

    def test_to_dict(self):
        """Should convert to dict."""
        item = NewsItem(
            id="test",
            title="Test",
            url="https://example.com",
            source_name="Test",
            snippet="Test snippet",
        )
        d = item.to_dict()
        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"


class TestFinancialItem:
    """Tests for FinancialItem dataclass."""

    def test_creates_financial_item(self):
        """Should create a financial item."""
        item = FinancialItem(
            id="WPP",
            entity_symbol="WPP",
            entity_name="WPP plc",
            metric_type="stock_price",
            value=50.25,
            change_pct=2.5,
            source_url="https://finance.example.com/WPP",
            source_name="Finance API",
        )
        assert item.entity_symbol == "WPP"
        assert item.value == 50.25
        assert item.change_pct == 2.5

    def test_to_dict(self):
        """Should convert to dict."""
        item = FinancialItem(
            id="TEST",
            entity_symbol="TEST",
            entity_name="Test Co",
            metric_type="stock_price",
            value=100.0,
            source_url="https://example.com",
            source_name="Finance",
        )
        d = item.to_dict()
        assert d["entity_symbol"] == "TEST"


class TestSocialItem:
    """Tests for SocialItem dataclass."""

    def test_creates_social_item(self):
        """Should create a social item."""
        item = SocialItem(
            id="tweet123",
            author_name="Scott Galloway",
            author_handle="profgalloway",
            text="Test post about advertising",
            url="https://x.com/profgalloway/status/123",
            platform="x",
        )
        assert item.author_handle == "profgalloway"
        assert "advertising" in item.text

    def test_with_engagement(self):
        """Should include engagement metrics."""
        item = SocialItem(
            id="test",
            author_name="Test",
            author_handle="test",
            text="Test",
            url="https://x.com/test",
            platform="x",
            engagement=Engagement(likes=1000, reposts=100),
        )
        assert item.engagement.likes == 1000


class TestReport:
    """Tests for Report dataclass."""

    def test_creates_report(self):
        """Should create a report."""
        report = Report(
            title="Test Report",
            report_type="daily_brief",
            domain="advertising",
            profile="test",
            generated_at="2026-02-01T12:00:00Z",
            date_range_from="2026-01-31",
            date_range_to="2026-02-01",
        )
        assert report.title == "Test Report"
        assert report.report_type == "daily_brief"

    def test_add_section(self):
        """Should add sections."""
        report = Report(
            title="Test",
            report_type="daily",
            domain="test",
            profile="test",
            generated_at="2026-02-01",
            date_range_from="2026-01-31",
            date_range_to="2026-02-01",
        )
        section = ReportSection(title="Test Section", items=[{"test": "data"}])
        report.sections.append(section)
        assert len(report.sections) == 1

    def test_to_dict(self):
        """Should convert to dict including sections."""
        report = Report(
            title="Test",
            report_type="daily",
            domain="test",
            profile="test",
            generated_at="2026-02-01",
            date_range_from="2026-01-31",
            date_range_to="2026-02-01",
        )
        section = ReportSection(title="Section 1", items=[{"key": "value"}])
        report.sections.append(section)

        d = report.to_dict()
        assert d["title"] == "Test"
        assert len(d["sections"]) == 1
        assert d["sections"][0]["title"] == "Section 1"
