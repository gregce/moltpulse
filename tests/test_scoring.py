"""Tests for scoring module."""

from datetime import datetime, timedelta

from moltpulse.core.lib.schema import Engagement, FinancialItem, NewsItem, SocialItem
from moltpulse.core.lib.score import (
    score_financial_items,
    score_news_items,
    score_social_items,
    sort_items,
)


class TestScoreNewsItems:
    """Tests for news item scoring."""

    def test_scores_items(self):
        """Should score multiple news items."""
        items = [
            NewsItem(
                id="test1",
                title="AI transformation in advertising industry",
                url="https://example.com/article1",
                source_name="Test News",
                snippet="Test snippet about AI",
            ),
            NewsItem(
                id="test2",
                title="Another article",
                url="https://example.com/article2",
                source_name="Test News",
                snippet="Another test snippet",
            ),
        ]
        scored = score_news_items(items)
        assert len(scored) == 2
        assert all(item.score is not None for item in scored)

    def test_recent_items_score_higher(self):
        """Recent items should score higher than old items."""
        today = datetime.now().date().isoformat()
        old_date = (datetime.now() - timedelta(days=30)).date().isoformat()

        items = [
            NewsItem(
                id="recent",
                title="Test article",
                url="https://example.com/recent",
                source_name="News",
                snippet="Recent test",
                date=today,
                relevance=0.5,
            ),
            NewsItem(
                id="old",
                title="Test article",
                url="https://example.com/old",
                source_name="News",
                snippet="Old test",
                date=old_date,
                relevance=0.5,
            ),
        ]

        scored = score_news_items(items)
        recent_item = next(i for i in scored if i.id == "recent")
        old_item = next(i for i in scored if i.id == "old")
        assert recent_item.score > old_item.score

    def test_returns_empty_for_empty_list(self):
        """Should handle empty list."""
        result = score_news_items([])
        assert result == []


class TestScoreFinancialItems:
    """Tests for financial item scoring."""

    def test_large_changes_score_higher(self):
        """Large price changes should score higher."""
        items = [
            FinancialItem(
                id="high",
                entity_symbol="TEST",
                entity_name="Test Co",
                metric_type="stock_price",
                value=100.0,
                change_pct=10.0,
                source_url="https://example.com",
                source_name="Finance",
                relevance=0.5,
            ),
            FinancialItem(
                id="low",
                entity_symbol="TEST",
                entity_name="Test Co",
                metric_type="stock_price",
                value=100.0,
                change_pct=0.5,
                source_url="https://example.com",
                source_name="Finance",
                relevance=0.5,
            ),
        ]

        scored = score_financial_items(items)
        high_item = next(i for i in scored if i.id == "high")
        low_item = next(i for i in scored if i.id == "low")
        assert high_item.score > low_item.score

    def test_handles_none_change_pct(self):
        """Should handle items without change percentage."""
        items = [
            FinancialItem(
                id="no_change",
                entity_symbol="TEST",
                entity_name="Test Co",
                metric_type="stock_price",
                value=100.0,
                change_pct=None,
                source_url="https://example.com",
                source_name="Finance",
            ),
        ]
        scored = score_financial_items(items)
        assert scored[0].score is not None


class TestScoreSocialItems:
    """Tests for social item scoring."""

    def test_high_engagement_scores_higher(self):
        """High engagement items should score higher."""
        items = [
            SocialItem(
                id="high",
                author_name="Test User",
                author_handle="testuser",
                text="Test post",
                url="https://x.com/test/high",
                platform="x",
                engagement=Engagement(likes=10000, reposts=1000),
                relevance=0.5,
            ),
            SocialItem(
                id="low",
                author_name="Test User",
                author_handle="testuser",
                text="Test post",
                url="https://x.com/test/low",
                platform="x",
                engagement=Engagement(likes=10, reposts=1),
                relevance=0.5,
            ),
        ]

        scored = score_social_items(items)
        high_item = next(i for i in scored if i.id == "high")
        low_item = next(i for i in scored if i.id == "low")
        assert high_item.score > low_item.score

    def test_handles_no_engagement(self):
        """Should handle items without engagement data."""
        items = [
            SocialItem(
                id="test",
                author_name="Test",
                author_handle="test",
                text="Test",
                url="https://x.com/test",
                platform="x",
                engagement=None,
            ),
        ]
        scored = score_social_items(items)
        assert scored[0].score is not None


class TestSortItems:
    """Tests for sorting items."""

    def test_sorts_by_score_descending(self):
        """Should sort by score descending."""
        items = [
            NewsItem(
                id="low",
                title="Low",
                url="https://example.com/low",
                source_name="News",
                snippet="Low priority",
            ),
            NewsItem(
                id="high",
                title="High",
                url="https://example.com/high",
                source_name="News",
                snippet="High priority",
            ),
        ]
        items[0].score = 30
        items[1].score = 70

        sorted_items = sort_items(items)
        assert sorted_items[0].id == "high"
        assert sorted_items[1].id == "low"

    def test_handles_mixed_types(self):
        """Should sort mixed item types."""
        news = NewsItem(
            id="news",
            title="News",
            url="https://example.com/news",
            source_name="News",
            snippet="News item",
        )
        news.score = 50

        financial = FinancialItem(
            id="fin",
            entity_symbol="TEST",
            entity_name="Test",
            metric_type="stock_price",
            value=100.0,
            source_url="https://example.com/fin",
            source_name="Finance",
        )
        financial.score = 60

        sorted_items = sort_items([news, financial])
        assert sorted_items[0].id == "fin"  # Higher score
