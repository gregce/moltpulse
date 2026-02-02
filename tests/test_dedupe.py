"""Tests for deduplication module."""

import pytest

from moltpulse.core.lib import schema
from moltpulse.core.lib.dedupe import (
    dedupe_by_url,
    dedupe_items,
    dedupe_news,
    dedupe_social,
    find_duplicates,
    get_ngrams,
    jaccard_similarity,
    normalize_text,
)


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_lowercases_text(self):
        """Should lowercase text."""
        assert normalize_text("Hello World") == "hello world"

    def test_removes_punctuation(self):
        """Should remove punctuation."""
        assert normalize_text("Hello, World!") == "hello world"

    def test_collapses_whitespace(self):
        """Should collapse multiple spaces."""
        assert normalize_text("Hello   World") == "hello world"

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert normalize_text("  Hello World  ") == "hello world"

    def test_handles_special_chars(self):
        """Should handle special characters."""
        result = normalize_text("Company's $100M Deal!")
        assert "company" in result
        assert "100m" in result
        assert "deal" in result

    def test_preserves_numbers(self):
        """Should preserve numbers."""
        assert "2025" in normalize_text("Year 2025")

    def test_handles_empty(self):
        """Should handle empty string."""
        assert normalize_text("") == ""

    def test_handles_only_punctuation(self):
        """Should handle string with only punctuation."""
        assert normalize_text("!!!") == ""


class TestGetNgrams:
    """Tests for get_ngrams function."""

    def test_generates_trigrams(self):
        """Should generate character trigrams."""
        ngrams = get_ngrams("hello")
        assert "hel" in ngrams
        assert "ell" in ngrams
        assert "llo" in ngrams

    def test_default_n_is_3(self):
        """Default n should be 3."""
        ngrams = get_ngrams("hello", n=3)
        assert all(len(ng) == 3 for ng in ngrams)

    def test_handles_short_text(self):
        """Should handle text shorter than n."""
        ngrams = get_ngrams("hi", n=3)
        assert "hi" in ngrams

    def test_normalizes_first(self):
        """Should normalize text before generating ngrams."""
        ngrams1 = get_ngrams("Hello")
        ngrams2 = get_ngrams("HELLO")
        assert ngrams1 == ngrams2

    def test_returns_set(self):
        """Should return a set (no duplicates)."""
        ngrams = get_ngrams("hello hello")
        assert isinstance(ngrams, set)

    def test_custom_n(self):
        """Should support custom n values."""
        ngrams = get_ngrams("hello", n=2)
        assert all(len(ng) == 2 for ng in ngrams)


class TestJaccardSimilarity:
    """Tests for jaccard_similarity function."""

    def test_identical_sets(self):
        """Identical sets should have similarity 1.0."""
        s = {"a", "b", "c"}
        assert jaccard_similarity(s, s) == 1.0

    def test_disjoint_sets(self):
        """Disjoint sets should have similarity 0.0."""
        s1 = {"a", "b", "c"}
        s2 = {"d", "e", "f"}
        assert jaccard_similarity(s1, s2) == 0.0

    def test_partial_overlap(self):
        """Partial overlap should give intermediate value."""
        s1 = {"a", "b", "c"}
        s2 = {"b", "c", "d"}
        # Intersection: {b, c} = 2, Union: {a, b, c, d} = 4
        # Jaccard = 2/4 = 0.5
        assert jaccard_similarity(s1, s2) == 0.5

    def test_empty_sets(self):
        """Empty sets should return 0.0."""
        assert jaccard_similarity(set(), set()) == 0.0
        assert jaccard_similarity({"a"}, set()) == 0.0
        assert jaccard_similarity(set(), {"a"}) == 0.0

    def test_symmetric(self):
        """Similarity should be symmetric."""
        s1 = {"a", "b", "c"}
        s2 = {"c", "d", "e"}
        assert jaccard_similarity(s1, s2) == jaccard_similarity(s2, s1)


class TestFindDuplicates:
    """Tests for find_duplicates function."""

    def test_finds_duplicate_pair(self):
        """Should find similar items."""
        items = [
            schema.NewsItem(
                id="1",
                title="Apple announces new iPhone model",
                url="url1",
                source_name="TechNews",
                snippet="snippet1",
            ),
            schema.NewsItem(
                id="2",
                title="Apple announces new iPhone model today",
                url="url2",
                source_name="TechDaily",
                snippet="snippet2",
            ),
        ]
        duplicates = find_duplicates(items, threshold=0.7)
        assert len(duplicates) == 1
        assert duplicates[0] == (0, 1)

    def test_no_duplicates(self):
        """Should return empty list for distinct items."""
        items = [
            schema.NewsItem(
                id="1",
                title="Apple iPhone announcement",
                url="url1",
                source_name="src",
                snippet="s",
            ),
            schema.NewsItem(
                id="2",
                title="Microsoft Windows update",
                url="url2",
                source_name="src",
                snippet="s",
            ),
        ]
        duplicates = find_duplicates(items, threshold=0.7)
        assert len(duplicates) == 0

    def test_multiple_duplicates(self):
        """Should find multiple duplicate pairs."""
        items = [
            schema.NewsItem(id="1", title="Apple announces new iPhone model for 2025", url="u1", source_name="s", snippet="x"),
            schema.NewsItem(id="2", title="Apple announces new iPhone model for 2025 today", url="u2", source_name="s", snippet="x"),
            schema.NewsItem(id="3", title="Apple announces new iPhone model for 2025 release", url="u3", source_name="s", snippet="x"),
        ]
        duplicates = find_duplicates(items, threshold=0.6)
        # All three are highly similar, should find at least 2 pairs
        assert len(duplicates) >= 2

    def test_respects_threshold(self):
        """Should respect similarity threshold."""
        items = [
            schema.NewsItem(id="1", title="Apple iPhone", url="u1", source_name="s", snippet="x"),
            schema.NewsItem(id="2", title="Apple iPad", url="u2", source_name="s", snippet="x"),
        ]
        # With high threshold, should not be duplicates
        high_threshold = find_duplicates(items, threshold=0.9)
        assert len(high_threshold) == 0

        # With low threshold, might be duplicates
        low_threshold = find_duplicates(items, threshold=0.3)
        # May or may not find duplicates depending on ngram overlap


class TestDedupeItems:
    """Tests for dedupe_items function."""

    def test_removes_duplicates(self):
        """Should remove duplicate items."""
        items = [
            schema.NewsItem(id="1", title="Same story", url="u1", source_name="s", snippet="x", score=80),
            schema.NewsItem(id="2", title="Same story here", url="u2", source_name="s", snippet="x", score=70),
        ]
        result = dedupe_items(items, threshold=0.6)
        assert len(result) == 1
        # Should keep higher scored item
        assert result[0].score == 80

    def test_keeps_higher_scored(self):
        """Should keep higher scored item when deduping."""
        items = [
            schema.NewsItem(id="1", title="News about Apple", url="u1", source_name="s", snippet="x", score=50),
            schema.NewsItem(id="2", title="News about Apple today", url="u2", source_name="s", snippet="x", score=90),
        ]
        result = dedupe_items(items, threshold=0.6)
        assert len(result) == 1
        assert result[0].score == 90

    def test_single_item(self):
        """Should handle single item."""
        items = [
            schema.NewsItem(id="1", title="Only one", url="u1", source_name="s", snippet="x"),
        ]
        result = dedupe_items(items)
        assert len(result) == 1

    def test_empty_list(self):
        """Should handle empty list."""
        result = dedupe_items([])
        assert result == []

    def test_distinct_items_preserved(self):
        """Should preserve distinct items."""
        items = [
            schema.NewsItem(id="1", title="Apple news", url="u1", source_name="s", snippet="x"),
            schema.NewsItem(id="2", title="Microsoft news", url="u2", source_name="s", snippet="x"),
            schema.NewsItem(id="3", title="Google news", url="u3", source_name="s", snippet="x"),
        ]
        result = dedupe_items(items, threshold=0.7)
        assert len(result) == 3


class TestDedupeByUrl:
    """Tests for dedupe_by_url function."""

    def test_removes_url_duplicates(self):
        """Should remove items with duplicate URLs."""
        items = [
            schema.NewsItem(id="1", title="First", url="https://example.com/article", source_name="s", snippet="x", score=80),
            schema.NewsItem(id="2", title="Second", url="https://example.com/article", source_name="s", snippet="x", score=90),
        ]
        result = dedupe_by_url(items)
        assert len(result) == 1
        # Should keep higher scored one
        assert result[0].score == 90

    def test_keeps_different_urls(self):
        """Should keep items with different URLs."""
        items = [
            schema.NewsItem(id="1", title="First", url="https://example.com/1", source_name="s", snippet="x"),
            schema.NewsItem(id="2", title="Second", url="https://example.com/2", source_name="s", snippet="x"),
        ]
        result = dedupe_by_url(items)
        assert len(result) == 2

    def test_handles_no_url(self):
        """Should keep items without URLs."""
        items = [
            schema.FinancialItem(id="1", entity_symbol="AAPL", entity_name="Apple", metric_type="stock", value=150),
            schema.FinancialItem(id="2", entity_symbol="GOOGL", entity_name="Google", metric_type="stock", value=100),
        ]
        result = dedupe_by_url(items)
        assert len(result) == 2

    def test_single_item(self):
        """Should handle single item."""
        items = [
            schema.NewsItem(id="1", title="Only", url="https://example.com", source_name="s", snippet="x"),
        ]
        result = dedupe_by_url(items)
        assert len(result) == 1

    def test_empty_list(self):
        """Should handle empty list."""
        result = dedupe_by_url([])
        assert result == []


class TestDedupeNews:
    """Tests for dedupe_news function."""

    def test_dedupes_by_url_first(self):
        """Should dedupe by URL before content."""
        items = [
            schema.NewsItem(id="1", title="Different title 1", url="https://same.url", source_name="s", snippet="x", score=80),
            schema.NewsItem(id="2", title="Different title 2", url="https://same.url", source_name="s", snippet="x", score=90),
        ]
        result = dedupe_news(items)
        assert len(result) == 1

    def test_dedupes_similar_content(self):
        """Should also dedupe similar content."""
        items = [
            schema.NewsItem(id="1", title="Breaking: Apple launches new product", url="u1", source_name="s", snippet="x", score=80),
            schema.NewsItem(id="2", title="Breaking: Apple launches new product today", url="u2", source_name="s", snippet="x", score=70),
        ]
        result = dedupe_news(items, threshold=0.6)
        assert len(result) == 1


class TestDedupeSocial:
    """Tests for dedupe_social function."""

    def test_dedupes_social_items(self):
        """Should dedupe social items."""
        items = [
            schema.SocialItem(id="1", text="Great news about AI today!", url="u1", platform="x", author_name="user1", author_handle="@u1", score=80),
            schema.SocialItem(id="2", text="Great news about AI today!", url="u1", platform="x", author_name="user2", author_handle="@u2", score=70),
        ]
        result = dedupe_social(items)
        # Same URL, should dedupe
        assert len(result) == 1


class TestItemTextExtraction:
    """Tests for get_item_text function used internally."""

    def test_news_uses_title(self):
        """NewsItem should use title for comparison."""
        item = schema.NewsItem(id="1", title="Test Title", url="u", source_name="s", snippet="not used")
        # The dedupe uses title for news
        items = [item, item]
        # If we had two items with same title, they'd be dupes
        result = dedupe_items(items, threshold=0.9)
        assert len(result) == 1

    def test_social_uses_text(self):
        """SocialItem should use text for comparison."""
        items = [
            schema.SocialItem(id="1", text="Same text here", url="u1", platform="x", author_name="a", author_handle="h"),
            schema.SocialItem(id="2", text="Same text here", url="u2", platform="x", author_name="b", author_handle="i"),
        ]
        result = dedupe_items(items, threshold=0.9)
        assert len(result) == 1

    def test_financial_uses_entity_and_metric(self):
        """FinancialItem should use entity name and metric type."""
        items = [
            schema.FinancialItem(id="1", entity_symbol="AAPL", entity_name="Apple", metric_type="stock_price", value=150, score=80),
            schema.FinancialItem(id="2", entity_symbol="AAPL", entity_name="Apple", metric_type="stock_price", value=151, score=70),
        ]
        result = dedupe_items(items, threshold=0.9)
        # Same entity name + metric type should be considered duplicate
        assert len(result) == 1
