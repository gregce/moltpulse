"""Tests for run execution tracing module."""

import json
import threading
import time

from moltpulse.core.trace import (
    APICall,
    CollectorTrace,
    DeliveryTrace,
    RunTrace,
    TracingContext,
    get_current_collector_trace,
    record_api_call,
    set_current_collector_trace,
)


class TestAPICall:
    """Tests for APICall dataclass."""

    def test_creates_api_call(self):
        """Should create APICall with required fields."""
        call = APICall(endpoint="https://api.example.com/data", method="GET")
        assert call.endpoint == "https://api.example.com/data"
        assert call.method == "GET"

    def test_default_values(self):
        """Should have sensible defaults."""
        call = APICall(endpoint="https://api.example.com")
        assert call.method == "GET"
        assert call.status == 0
        assert call.latency_ms == 0
        assert call.cached is False
        assert call.error is None

    def test_auto_timestamp(self):
        """Should auto-generate timestamp if not provided."""
        call = APICall(endpoint="https://api.example.com")
        assert call.timestamp != ""
        assert "T" in call.timestamp  # ISO format

    def test_to_dict(self):
        """Should convert to dictionary."""
        call = APICall(
            endpoint="https://api.example.com",
            method="POST",
            status=200,
            latency_ms=150,
            cached=True,
        )
        d = call.to_dict()
        assert d["endpoint"] == "https://api.example.com"
        assert d["method"] == "POST"
        assert d["status"] == 200
        assert d["latency_ms"] == 150
        assert d["cached"] is True
        assert "error" not in d  # None values excluded

    def test_to_dict_includes_error(self):
        """Should include error in dict when present."""
        call = APICall(endpoint="https://api.example.com", error="Connection timeout")
        d = call.to_dict()
        assert d["error"] == "Connection timeout"


class TestCollectorTrace:
    """Tests for CollectorTrace dataclass."""

    def test_creates_collector_trace(self):
        """Should create CollectorTrace with required fields."""
        trace = CollectorTrace(name="Test Collector", collector_type="news")
        assert trace.name == "Test Collector"
        assert trace.collector_type == "news"

    def test_default_values(self):
        """Should have sensible defaults."""
        trace = CollectorTrace(name="Test", collector_type="news")
        assert trace.started_at == ""
        assert trace.ended_at == ""
        assert trace.duration_ms == 0
        assert trace.items_collected == 0
        assert trace.api_calls == []
        assert trace.success is True
        assert trace.error is None

    def test_start_sets_timestamp(self):
        """Should set start timestamp."""
        trace = CollectorTrace(name="Test", collector_type="news")
        trace.start()
        assert trace.started_at != ""
        assert "T" in trace.started_at

    def test_complete_sets_fields(self):
        """Should set completion fields."""
        trace = CollectorTrace(name="Test", collector_type="news")
        trace.start()
        time.sleep(0.01)  # Small delay for timing
        trace.complete(items_collected=10, items_after_filter=8, success=True)

        assert trace.ended_at != ""
        assert trace.duration_ms > 0
        assert trace.items_collected == 10
        assert trace.items_after_filter == 8
        assert trace.success is True

    def test_complete_with_error(self):
        """Should record error on completion."""
        trace = CollectorTrace(name="Test", collector_type="news")
        trace.start()
        trace.complete(success=False, error="API rate limited")

        assert trace.success is False
        assert trace.error == "API rate limited"

    def test_add_api_call(self):
        """Should add API call to trace."""
        trace = CollectorTrace(name="Test", collector_type="news")
        call = APICall(endpoint="https://api.example.com", status=200)
        trace.add_api_call(call)

        assert len(trace.api_calls) == 1
        assert trace.api_calls[0].endpoint == "https://api.example.com"

    def test_to_dict(self):
        """Should convert to dictionary."""
        trace = CollectorTrace(name="Test Collector", collector_type="financial")
        trace.start()
        trace.add_api_call(APICall(endpoint="https://api.example.com", status=200))
        trace.complete(items_collected=5)

        d = trace.to_dict()
        assert d["name"] == "Test Collector"
        assert d["type"] == "financial"
        assert d["items_collected"] == 5
        assert len(d["api_calls"]) == 1
        assert "error" not in d

    def test_to_dict_includes_error(self):
        """Should include error in dict when present."""
        trace = CollectorTrace(name="Test", collector_type="news")
        trace.start()
        trace.complete(success=False, error="Failed")
        d = trace.to_dict()
        assert d["error"] == "Failed"


class TestDeliveryTrace:
    """Tests for DeliveryTrace dataclass."""

    def test_creates_delivery_trace(self):
        """Should create DeliveryTrace with channel."""
        trace = DeliveryTrace(channel="email")
        assert trace.channel == "email"

    def test_start_and_complete(self):
        """Should track timing."""
        trace = DeliveryTrace(channel="file")
        trace.start()
        time.sleep(0.01)
        trace.complete(success=True)

        assert trace.started_at != ""
        assert trace.ended_at != ""
        assert trace.duration_ms > 0
        assert trace.success is True

    def test_complete_with_error(self):
        """Should record error."""
        trace = DeliveryTrace(channel="email")
        trace.start()
        trace.complete(success=False, error="SMTP connection failed")

        assert trace.success is False
        assert trace.error == "SMTP connection failed"

    def test_to_dict(self):
        """Should convert to dictionary."""
        trace = DeliveryTrace(channel="console")
        trace.start()
        trace.complete(success=True)
        d = trace.to_dict()

        assert d["channel"] == "console"
        assert d["success"] is True
        assert "error" not in d


class TestRunTrace:
    """Tests for RunTrace dataclass."""

    def test_creates_run_trace(self):
        """Should create RunTrace with required fields."""
        trace = RunTrace(
            domain="advertising",
            profile="ricki",
            report_type="daily_brief",
        )
        assert trace.domain == "advertising"
        assert trace.profile == "ricki"
        assert trace.report_type == "daily_brief"

    def test_auto_generates_run_id(self):
        """Should auto-generate run_id if not provided."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        assert trace.run_id != ""
        assert len(trace.run_id) == 36  # UUID format

    def test_default_values(self):
        """Should have sensible defaults."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        assert trace.depth == "default"
        assert trace.collectors == []
        assert trace.delivery is None

    def test_start_and_complete(self):
        """Should track run timing."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        trace.start()
        time.sleep(0.01)
        trace.complete()

        assert trace.started_at != ""
        assert trace.ended_at != ""
        assert trace.duration_ms > 0

    def test_add_collector_trace(self):
        """Should add collector traces."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        collector = CollectorTrace(name="News", collector_type="news")
        collector.start()
        collector.complete(items_collected=10)
        trace.add_collector_trace(collector)

        assert len(trace.collectors) == 1
        assert trace.collectors[0].name == "News"

    def test_set_delivery_trace(self):
        """Should set delivery trace."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        delivery = DeliveryTrace(channel="email")
        delivery.start()
        delivery.complete(success=True)
        trace.set_delivery_trace(delivery)

        assert trace.delivery is not None
        assert trace.delivery.channel == "email"

    def test_total_items_collected(self):
        """Should sum items across collectors."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")

        c1 = CollectorTrace(name="C1", collector_type="news")
        c1.start()
        c1.complete(items_collected=10)
        trace.add_collector_trace(c1)

        c2 = CollectorTrace(name="C2", collector_type="financial")
        c2.start()
        c2.complete(items_collected=5)
        trace.add_collector_trace(c2)

        assert trace.total_items_collected == 15

    def test_total_api_calls(self):
        """Should sum API calls across collectors."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")

        c1 = CollectorTrace(name="C1", collector_type="news")
        c1.add_api_call(APICall(endpoint="url1"))
        c1.add_api_call(APICall(endpoint="url2"))
        trace.add_collector_trace(c1)

        c2 = CollectorTrace(name="C2", collector_type="financial")
        c2.add_api_call(APICall(endpoint="url3"))
        trace.add_collector_trace(c2)

        assert trace.total_api_calls == 3

    def test_successful_and_failed_collectors(self):
        """Should count successful and failed collectors."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")

        c1 = CollectorTrace(name="C1", collector_type="news")
        c1.start()
        c1.complete(success=True)
        trace.add_collector_trace(c1)

        c2 = CollectorTrace(name="C2", collector_type="financial")
        c2.start()
        c2.complete(success=False, error="Failed")
        trace.add_collector_trace(c2)

        c3 = CollectorTrace(name="C3", collector_type="rss")
        c3.start()
        c3.complete(success=True)
        trace.add_collector_trace(c3)

        assert trace.successful_collectors == 2
        assert trace.failed_collectors == 1

    def test_to_dict(self):
        """Should convert to dictionary."""
        trace = RunTrace(
            domain="advertising",
            profile="ricki",
            report_type="daily_brief",
            depth="deep",
        )
        trace.start()

        c = CollectorTrace(name="Test", collector_type="news")
        c.start()
        c.complete(items_collected=5)
        trace.add_collector_trace(c)

        trace.complete()

        d = trace.to_dict()
        assert d["domain"] == "advertising"
        assert d["profile"] == "ricki"
        assert d["report_type"] == "daily_brief"
        assert d["depth"] == "deep"
        assert len(d["collectors"]) == 1
        assert "delivery" not in d  # None excluded

    def test_to_dict_with_delivery(self):
        """Should include delivery in dict when present."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        trace.start()

        delivery = DeliveryTrace(channel="file")
        delivery.start()
        delivery.complete(success=True)
        trace.set_delivery_trace(delivery)

        trace.complete()

        d = trace.to_dict()
        assert "delivery" in d
        assert d["delivery"]["channel"] == "file"

    def test_to_json(self):
        """Should convert to JSON string."""
        trace = RunTrace(domain="test", profile="test", report_type="daily")
        trace.start()
        trace.complete()

        json_str = trace.to_json()
        parsed = json.loads(json_str)

        assert parsed["domain"] == "test"
        assert "run_id" in parsed

    def test_summary(self):
        """Should generate human-readable summary."""
        trace = RunTrace(
            domain="advertising",
            profile="ricki",
            report_type="daily_brief",
        )
        trace.start()

        c = CollectorTrace(name="News Collector", collector_type="news")
        c.start()
        c.add_api_call(APICall(endpoint="https://api.example.com", status=200, latency_ms=100))
        c.complete(items_collected=10)
        trace.add_collector_trace(c)

        trace.complete()

        summary = trace.summary()
        assert "advertising" in summary
        assert "ricki" in summary
        assert "News Collector" in summary
        assert "10" in summary  # items


class TestTracingContext:
    """Tests for TracingContext context manager."""

    def test_sets_current_trace(self):
        """Should set current trace in context."""
        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace):
            current = get_current_collector_trace()
            assert current is trace

    def test_restores_previous_trace(self):
        """Should restore previous trace after exit."""
        previous = CollectorTrace(name="Previous", collector_type="news")
        set_current_collector_trace(previous)

        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace):
            assert get_current_collector_trace() is trace

        assert get_current_collector_trace() is previous

    def test_clears_trace_when_no_previous(self):
        """Should clear trace when no previous exists."""
        set_current_collector_trace(None)

        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace):
            assert get_current_collector_trace() is trace

        assert get_current_collector_trace() is None

    def test_starts_trace(self):
        """Should call start() on trace."""
        trace = CollectorTrace(name="Test", collector_type="news")
        assert trace.started_at == ""

        with TracingContext(trace):
            pass

        assert trace.started_at != ""

    def test_returns_trace(self):
        """Should return trace from context manager."""
        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace) as t:
            assert t is trace


class TestRecordAPICall:
    """Tests for record_api_call function."""

    def test_records_call_in_active_trace(self):
        """Should record API call when trace is active."""
        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace):
            record_api_call(
                endpoint="https://api.example.com",
                method="GET",
                status=200,
                latency_ms=150,
            )

        assert len(trace.api_calls) == 1
        assert trace.api_calls[0].endpoint == "https://api.example.com"
        assert trace.api_calls[0].status == 200

    def test_does_nothing_without_active_trace(self):
        """Should not raise when no trace is active."""
        set_current_collector_trace(None)

        # Should not raise
        record_api_call(endpoint="https://api.example.com", status=200)

    def test_records_error(self):
        """Should record error in API call."""
        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace):
            record_api_call(
                endpoint="https://api.example.com",
                status=500,
                error="Internal Server Error",
            )

        assert trace.api_calls[0].error == "Internal Server Error"

    def test_records_cached_flag(self):
        """Should record cached flag."""
        trace = CollectorTrace(name="Test", collector_type="news")

        with TracingContext(trace):
            record_api_call(
                endpoint="https://api.example.com",
                status=200,
                cached=True,
            )

        assert trace.api_calls[0].cached is True


class TestThreadSafety:
    """Tests for thread-local storage behavior."""

    def test_traces_are_thread_local(self):
        """Should maintain separate traces per thread."""
        results = {}

        def thread_func(thread_id: int):
            trace = CollectorTrace(name=f"Thread-{thread_id}", collector_type="news")
            with TracingContext(trace):
                time.sleep(0.01)  # Small delay to allow interleaving
                current = get_current_collector_trace()
                results[thread_id] = current.name

        threads = [
            threading.Thread(target=thread_func, args=(i,))
            for i in range(3)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each thread should have seen its own trace
        assert results[0] == "Thread-0"
        assert results[1] == "Thread-1"
        assert results[2] == "Thread-2"
