"""Tests for collector base classes."""

import pytest
from typing import Dict, Any, List

from moltpulse.core.collector_base import (
    Collector,
    CollectorResult,
    FinancialCollector,
    NewsCollector,
    SocialCollector,
    RSSCollector,
    AwardsCollector,
    PEActivityCollector,
)
from moltpulse.core.lib import schema
from moltpulse.core.profile_loader import ProfileConfig


class TestCollectorResult:
    """Tests for CollectorResult class."""

    def test_creates_result_with_items(self):
        """Should create result with items and sources."""
        item = schema.NewsItem(
            id="1",
            title="Test News",
            url="https://example.com",
            source_name="Test Source",
            snippet="Test snippet text",
        )
        source = schema.Source(name="Test", url="https://example.com")

        result = CollectorResult(items=[item], sources=[source])

        assert len(result.items) == 1
        assert len(result.sources) == 1
        assert result.items[0].title == "Test News"

    def test_success_when_no_error(self):
        """Should report success when no error."""
        result = CollectorResult(items=[], sources=[])
        assert result.success is True

    def test_not_success_when_error(self):
        """Should report failure when error present."""
        result = CollectorResult(items=[], sources=[], error="API failed")
        assert result.success is False

    def test_count_returns_item_count(self):
        """Should return number of items."""
        items = [
            schema.NewsItem(id="1", title="News 1", url="url1", source_name="src", snippet="s1"),
            schema.NewsItem(id="2", title="News 2", url="url2", source_name="src", snippet="s2"),
            schema.NewsItem(id="3", title="News 3", url="url3", source_name="src", snippet="s3"),
        ]
        result = CollectorResult(items=items, sources=[])
        assert result.count == 3

    def test_count_zero_for_empty(self):
        """Should return 0 for empty items."""
        result = CollectorResult(items=[], sources=[])
        assert result.count == 0

    def test_to_dict(self):
        """Should convert to dictionary."""
        item = schema.NewsItem(
            id="1",
            title="Test",
            url="https://example.com",
            source_name="Source",
            snippet="Test snippet",
        )
        source = schema.Source(name="Source", url="https://example.com")
        result = CollectorResult(
            items=[item],
            sources=[source],
            error=None,
        )

        d = result.to_dict()
        assert len(d["items"]) == 1
        assert len(d["sources"]) == 1
        assert d["error"] is None
        assert d["count"] == 1

    def test_to_dict_with_error(self):
        """Should include error in dict."""
        result = CollectorResult(items=[], sources=[], error="Failed to fetch")
        d = result.to_dict()
        assert d["error"] == "Failed to fetch"

    def test_raw_response_stored(self):
        """Should store raw response for debugging."""
        raw = {"data": [{"id": 1}], "meta": {"count": 1}}
        result = CollectorResult(items=[], sources=[], raw_response=raw)
        assert result.raw_response == raw


# Concrete test collector for testing base class behavior
class MockCollectorForTests(Collector):
    """Test collector implementation."""

    REQUIRED_API_KEYS = ["TEST_API_KEY"]

    @property
    def collector_type(self) -> str:
        return "test"

    @property
    def name(self) -> str:
        return "Test Collector"

    def collect(self, profile, from_date, to_date, depth="default"):
        return CollectorResult(items=[], sources=[])


class MockCollectorAnyKey(Collector):
    """Test collector that needs any one of multiple keys."""

    REQUIRED_API_KEYS = ["KEY_A", "KEY_B", "KEY_C"]
    REQUIRES_ANY_KEY = True

    @property
    def collector_type(self) -> str:
        return "test_any"

    @property
    def name(self) -> str:
        return "Test Any Key Collector"

    def collect(self, profile, from_date, to_date, depth="default"):
        return CollectorResult(items=[], sources=[])


class MockCollectorNoKey(Collector):
    """Test collector that needs no API key."""

    REQUIRED_API_KEYS = []

    @property
    def collector_type(self) -> str:
        return "test_nokey"

    @property
    def name(self) -> str:
        return "No Key Collector"

    def collect(self, profile, from_date, to_date, depth="default"):
        return CollectorResult(items=[], sources=[])


class TestCollectorAPIKeyValidation:
    """Tests for Collector API key validation."""

    def test_is_available_with_required_key(self):
        """Should be available when required key present."""
        config = {"TEST_API_KEY": "sk-12345"}
        collector = MockCollectorForTests(config)
        assert collector.is_available() is True

    def test_not_available_without_required_key(self):
        """Should not be available when required key missing."""
        config = {}
        collector = MockCollectorForTests(config)
        assert collector.is_available() is False

    def test_not_available_with_empty_key(self):
        """Should not be available when key is empty string."""
        config = {"TEST_API_KEY": ""}
        collector = MockCollectorForTests(config)
        assert collector.is_available() is False

    def test_not_available_with_none_key(self):
        """Should not be available when key is None."""
        config = {"TEST_API_KEY": None}
        collector = MockCollectorForTests(config)
        assert collector.is_available() is False

    def test_get_required_keys(self):
        """Should return list of required keys."""
        keys = MockCollectorForTests.get_required_keys()
        assert keys == ["TEST_API_KEY"]

    def test_get_missing_keys_all_missing(self):
        """Should return all missing keys."""
        config = {}
        missing = MockCollectorForTests.get_missing_keys(config)
        assert missing == ["TEST_API_KEY"]

    def test_get_missing_keys_none_missing(self):
        """Should return empty list when all keys present."""
        config = {"TEST_API_KEY": "sk-12345"}
        missing = MockCollectorForTests.get_missing_keys(config)
        assert missing == []

    def test_get_missing_keys_partial(self):
        """Should return only missing keys."""

        class MultiKeyCollector(Collector):
            REQUIRED_API_KEYS = ["KEY_1", "KEY_2", "KEY_3"]

            @property
            def collector_type(self):
                return "test"

            @property
            def name(self):
                return "Multi"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        config = {"KEY_1": "value1", "KEY_3": "value3"}
        missing = MultiKeyCollector.get_missing_keys(config)
        assert missing == ["KEY_2"]


class TestCollectorRequiresAnyKey:
    """Tests for REQUIRES_ANY_KEY behavior."""

    def test_available_with_first_key(self):
        """Should be available with first key."""
        config = {"KEY_A": "value_a"}
        collector = MockCollectorAnyKey(config)
        assert collector.is_available() is True

    def test_available_with_second_key(self):
        """Should be available with second key."""
        config = {"KEY_B": "value_b"}
        collector = MockCollectorAnyKey(config)
        assert collector.is_available() is True

    def test_available_with_third_key(self):
        """Should be available with third key."""
        config = {"KEY_C": "value_c"}
        collector = MockCollectorAnyKey(config)
        assert collector.is_available() is True

    def test_available_with_multiple_keys(self):
        """Should be available with multiple keys."""
        config = {"KEY_A": "value_a", "KEY_C": "value_c"}
        collector = MockCollectorAnyKey(config)
        assert collector.is_available() is True

    def test_not_available_with_no_keys(self):
        """Should not be available with no keys."""
        config = {}
        collector = MockCollectorAnyKey(config)
        assert collector.is_available() is False

    def test_not_available_with_wrong_keys(self):
        """Should not be available with unrelated keys."""
        config = {"OTHER_KEY": "value"}
        collector = MockCollectorAnyKey(config)
        assert collector.is_available() is False


class TestCollectorNoKeyRequired:
    """Tests for collectors that don't need API keys."""

    def test_always_available(self):
        """Should always be available."""
        config = {}
        collector = MockCollectorNoKey(config)
        assert collector.is_available() is True

    def test_get_required_keys_empty(self):
        """Should return empty list."""
        keys = MockCollectorNoKey.get_required_keys()
        assert keys == []

    def test_get_missing_keys_empty(self):
        """Should return empty list."""
        config = {}
        missing = MockCollectorNoKey.get_missing_keys(config)
        assert missing == []


class TestCollectorDepthConfig:
    """Tests for depth configuration."""

    def test_quick_depth(self):
        """Should return quick config."""
        collector = MockCollectorForTests({"TEST_API_KEY": "key"})
        config = collector.get_depth_config("quick")

        assert config["max_items"] == 10
        assert config["timeout"] == 30

    def test_default_depth(self):
        """Should return default config."""
        collector = MockCollectorForTests({"TEST_API_KEY": "key"})
        config = collector.get_depth_config("default")

        assert config["max_items"] == 25
        assert config["timeout"] == 60

    def test_deep_depth(self):
        """Should return deep config."""
        collector = MockCollectorForTests({"TEST_API_KEY": "key"})
        config = collector.get_depth_config("deep")

        assert config["max_items"] == 50
        assert config["timeout"] == 120

    def test_unknown_depth_returns_default(self):
        """Should return default for unknown depth."""
        collector = MockCollectorForTests({"TEST_API_KEY": "key"})
        config = collector.get_depth_config("unknown")

        assert config["max_items"] == 25
        assert config["timeout"] == 60


class TestSpecializedCollectorTypes:
    """Tests for specialized collector base classes."""

    def test_financial_collector_type(self):
        """FinancialCollector should have 'financial' type."""

        class TestFinancial(FinancialCollector):
            @property
            def name(self):
                return "Test Financial"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        collector = TestFinancial({})
        assert collector.collector_type == "financial"

    def test_news_collector_type(self):
        """NewsCollector should have 'news' type."""

        class TestNews(NewsCollector):
            @property
            def name(self):
                return "Test News"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        collector = TestNews({})
        assert collector.collector_type == "news"

    def test_social_collector_type(self):
        """SocialCollector should have 'social' type."""

        class TestSocial(SocialCollector):
            @property
            def name(self):
                return "Test Social"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        collector = TestSocial({})
        assert collector.collector_type == "social"

    def test_rss_collector_type(self):
        """RSSCollector should have 'rss' type."""

        class TestRSS(RSSCollector):
            @property
            def name(self):
                return "Test RSS"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        collector = TestRSS({})
        assert collector.collector_type == "rss"

    def test_awards_collector_type(self):
        """AwardsCollector should have 'awards' type."""

        class TestAwards(AwardsCollector):
            @property
            def name(self):
                return "Test Awards"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        collector = TestAwards({})
        assert collector.collector_type == "awards"

    def test_pe_activity_collector_type(self):
        """PEActivityCollector should have 'pe_activity' type."""

        class TestPE(PEActivityCollector):
            @property
            def name(self):
                return "Test PE"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        collector = TestPE({})
        assert collector.collector_type == "pe_activity"


class TestCollectorOptionalKeys:
    """Tests for optional API keys."""

    def test_optional_keys_declared(self):
        """Should be able to declare optional keys."""

        class CollectorWithOptional(Collector):
            REQUIRED_API_KEYS = ["MAIN_KEY"]
            OPTIONAL_API_KEYS = ["ENHANCE_KEY", "FALLBACK_KEY"]

            @property
            def collector_type(self):
                return "test"

            @property
            def name(self):
                return "Test"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        assert CollectorWithOptional.OPTIONAL_API_KEYS == ["ENHANCE_KEY", "FALLBACK_KEY"]

    def test_optional_keys_dont_affect_availability(self):
        """Optional keys should not affect is_available."""

        class CollectorWithOptional(Collector):
            REQUIRED_API_KEYS = ["MAIN_KEY"]
            OPTIONAL_API_KEYS = ["ENHANCE_KEY"]

            @property
            def collector_type(self):
                return "test"

            @property
            def name(self):
                return "Test"

            def collect(self, profile, from_date, to_date, depth="default"):
                return CollectorResult(items=[], sources=[])

        # Available with just required key (optional missing)
        config = {"MAIN_KEY": "value"}
        collector = CollectorWithOptional(config)
        assert collector.is_available() is True
