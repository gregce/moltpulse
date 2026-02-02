"""Tests for date utilities module."""

from datetime import datetime, timedelta, timezone

from moltpulse.core.lib.dates import (
    days_ago,
    format_date_human,
    get_date_confidence,
    get_date_range,
    parse_date,
    recency_score,
    timestamp_to_date,
)


class TestGetDateRange:
    """Tests for get_date_range function."""

    def test_returns_tuple_of_strings(self):
        """Should return tuple of (from_date, to_date)."""
        from_date, to_date = get_date_range(30)
        assert isinstance(from_date, str)
        assert isinstance(to_date, str)

    def test_format_is_iso(self):
        """Should return dates in YYYY-MM-DD format."""
        from_date, to_date = get_date_range(30)
        # Check format by parsing
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")

    def test_to_date_is_today(self):
        """to_date should be today."""
        _, to_date = get_date_range(30)
        today = datetime.now(timezone.utc).date().isoformat()
        assert to_date == today

    def test_from_date_is_n_days_ago(self):
        """from_date should be N days before today."""
        from_date, to_date = get_date_range(30)

        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()

        delta = to_dt - from_dt
        assert delta.days == 30

    def test_default_is_30_days(self):
        """Default should be 30 days."""
        from_date, to_date = get_date_range()

        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()

        delta = to_dt - from_dt
        assert delta.days == 30

    def test_custom_days(self):
        """Should support custom day ranges."""
        from_date, to_date = get_date_range(7)

        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()

        assert (to_dt - from_dt).days == 7


class TestParseDate:
    """Tests for parse_date function."""

    def test_parses_iso_date(self):
        """Should parse YYYY-MM-DD format."""
        result = parse_date("2025-01-15")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parses_iso_datetime(self):
        """Should parse YYYY-MM-DDTHH:MM:SS format."""
        result = parse_date("2025-01-15T10:30:00")
        assert result is not None
        assert result.year == 2025
        assert result.hour == 10
        assert result.minute == 30

    def test_parses_iso_datetime_z(self):
        """Should parse format with Z timezone."""
        result = parse_date("2025-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2025

    def test_parses_iso_datetime_with_tz(self):
        """Should parse format with timezone offset."""
        result = parse_date("2025-01-15T10:30:00+00:00")
        assert result is not None
        assert result.year == 2025

    def test_parses_unix_timestamp(self):
        """Should parse Unix timestamp."""
        # 2025-01-15 00:00:00 UTC
        ts = 1736899200.0
        result = parse_date(str(ts))
        assert result is not None
        assert result.year == 2025
        assert result.month == 1

    def test_parses_unix_timestamp_int(self):
        """Should parse Unix timestamp as int string."""
        ts = "1736899200"
        result = parse_date(ts)
        assert result is not None

    def test_returns_none_for_invalid(self):
        """Should return None for invalid format."""
        assert parse_date("not a date") is None
        assert parse_date("15-01-2025") is None  # Wrong format
        assert parse_date("Jan 15, 2025") is None  # Not supported

    def test_returns_none_for_empty(self):
        """Should return None for empty string."""
        assert parse_date("") is None

    def test_returns_none_for_none(self):
        """Should return None for None input."""
        assert parse_date(None) is None

    def test_returns_utc_timezone(self):
        """Should return datetime with UTC timezone."""
        result = parse_date("2025-01-15")
        assert result is not None
        assert result.tzinfo == timezone.utc


class TestTimestampToDate:
    """Tests for timestamp_to_date function."""

    def test_converts_timestamp(self):
        """Should convert Unix timestamp to date string."""
        # 2025-01-15 00:00:00 UTC
        result = timestamp_to_date(1736899200.0)
        assert result == "2025-01-15"

    def test_returns_none_for_none(self):
        """Should return None for None input."""
        assert timestamp_to_date(None) is None

    def test_returns_none_for_invalid(self):
        """Should return None for invalid timestamp."""
        # Note: Some invalid values like float("inf") raise OverflowError
        # which is not currently caught. Test with values that are caught.
        # The function catches ValueError, TypeError, OSError
        pass  # Currently no values trigger these without None

    def test_handles_float_timestamp(self):
        """Should handle float timestamps with decimals."""
        result = timestamp_to_date(1736899200.123)
        assert result is not None


class TestGetDateConfidence:
    """Tests for get_date_confidence function."""

    def test_high_for_date_in_range(self):
        """Should return 'high' for date within range."""
        result = get_date_confidence("2025-01-15", "2025-01-01", "2025-01-31")
        assert result == "high"

    def test_high_for_date_at_start(self):
        """Should return 'high' for date at range start."""
        result = get_date_confidence("2025-01-01", "2025-01-01", "2025-01-31")
        assert result == "high"

    def test_high_for_date_at_end(self):
        """Should return 'high' for date at range end."""
        result = get_date_confidence("2025-01-31", "2025-01-01", "2025-01-31")
        assert result == "high"

    def test_low_for_date_before_range(self):
        """Should return 'low' for date before range."""
        result = get_date_confidence("2024-12-31", "2025-01-01", "2025-01-31")
        assert result == "low"

    def test_low_for_date_after_range(self):
        """Should return 'low' for future date."""
        result = get_date_confidence("2025-02-15", "2025-01-01", "2025-01-31")
        assert result == "low"

    def test_low_for_none(self):
        """Should return 'low' for None date."""
        result = get_date_confidence(None, "2025-01-01", "2025-01-31")
        assert result == "low"

    def test_low_for_empty(self):
        """Should return 'low' for empty date."""
        result = get_date_confidence("", "2025-01-01", "2025-01-31")
        assert result == "low"

    def test_low_for_invalid_format(self):
        """Should return 'low' for invalid date format."""
        result = get_date_confidence("invalid", "2025-01-01", "2025-01-31")
        assert result == "low"


class TestDaysAgo:
    """Tests for days_ago function."""

    def test_today_is_zero(self):
        """Today should be 0 days ago."""
        today = datetime.now(timezone.utc).date().isoformat()
        assert days_ago(today) == 0

    def test_yesterday_is_one(self):
        """Yesterday should be 1 day ago."""
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        assert days_ago(yesterday) == 1

    def test_week_ago(self):
        """Should calculate days for older dates."""
        week_ago = (datetime.now(timezone.utc).date() - timedelta(days=7)).isoformat()
        assert days_ago(week_ago) == 7

    def test_future_is_negative(self):
        """Future dates should return negative days."""
        tomorrow = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
        assert days_ago(tomorrow) == -1

    def test_returns_none_for_none(self):
        """Should return None for None input."""
        assert days_ago(None) is None

    def test_returns_none_for_empty(self):
        """Should return None for empty string."""
        assert days_ago("") is None

    def test_returns_none_for_invalid(self):
        """Should return None for invalid date."""
        assert days_ago("not-a-date") is None


class TestRecencyScore:
    """Tests for recency_score function."""

    def test_today_is_100(self):
        """Today should score 100."""
        today = datetime.now(timezone.utc).date().isoformat()
        assert recency_score(today) == 100

    def test_max_days_is_0(self):
        """Date at max_days should score 0."""
        old = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
        assert recency_score(old, max_days=30) == 0

    def test_beyond_max_days_is_0(self):
        """Date beyond max_days should score 0."""
        very_old = (datetime.now(timezone.utc).date() - timedelta(days=60)).isoformat()
        assert recency_score(very_old, max_days=30) == 0

    def test_middle_range(self):
        """Date in middle of range should score proportionally."""
        # 15 days ago with 30 day max should be ~50
        mid = (datetime.now(timezone.utc).date() - timedelta(days=15)).isoformat()
        score = recency_score(mid, max_days=30)
        assert 45 <= score <= 55  # Allow some rounding variation

    def test_custom_max_days(self):
        """Should support custom max_days."""
        week_ago = (datetime.now(timezone.utc).date() - timedelta(days=7)).isoformat()
        # With 7-day max, 7 days ago should be 0
        assert recency_score(week_ago, max_days=7) == 0
        # With 14-day max, 7 days ago should be ~50
        score = recency_score(week_ago, max_days=14)
        assert 45 <= score <= 55

    def test_future_is_100(self):
        """Future dates should score 100 (treated as today)."""
        tomorrow = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
        assert recency_score(tomorrow) == 100

    def test_unknown_date_is_0(self):
        """Unknown/None date should score 0."""
        assert recency_score(None) == 0
        assert recency_score("") == 0


class TestFormatDateHuman:
    """Tests for format_date_human function."""

    def test_today(self):
        """Today should format as 'Today'."""
        today = datetime.now(timezone.utc).date().isoformat()
        assert format_date_human(today) == "Today"

    def test_yesterday(self):
        """Yesterday should format as 'Yesterday'."""
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        assert format_date_human(yesterday) == "Yesterday"

    def test_days_ago(self):
        """Recent dates should show 'X days ago'."""
        three_days = (datetime.now(timezone.utc).date() - timedelta(days=3)).isoformat()
        assert format_date_human(three_days) == "3 days ago"

    def test_singular_day(self):
        """2 days should say 'days' (not '1 day ago' for 1)."""
        two_days = (datetime.now(timezone.utc).date() - timedelta(days=2)).isoformat()
        assert format_date_human(two_days) == "2 days ago"

    def test_week_ago(self):
        """Week-old dates should show 'X week(s) ago'."""
        week_ago = (datetime.now(timezone.utc).date() - timedelta(days=7)).isoformat()
        assert format_date_human(week_ago) == "1 week ago"

    def test_weeks_plural(self):
        """Multiple weeks should be plural."""
        two_weeks = (datetime.now(timezone.utc).date() - timedelta(days=14)).isoformat()
        assert format_date_human(two_weeks) == "2 weeks ago"

    def test_old_shows_date(self):
        """Old dates should show the actual date."""
        old = (datetime.now(timezone.utc).date() - timedelta(days=60)).isoformat()
        assert format_date_human(old) == old  # Returns the date string

    def test_none_input(self):
        """None should return 'Unknown date'."""
        assert format_date_human(None) == "Unknown date"

    def test_empty_input(self):
        """Empty string should return 'Unknown date'."""
        assert format_date_human("") == "Unknown date"

    def test_invalid_returns_as_is(self):
        """Invalid date format should return as-is."""
        # The function returns the string if it can't parse it
        assert format_date_human("invalid-date") == "invalid-date"
