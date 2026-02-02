"""Run execution tracing for MoltPulse.

Provides dataclasses for tracking API calls, collector execution,
and overall run metrics. Supports JSON export for OpenClaw integration.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class APICall:
    """Record of a single API call."""

    endpoint: str
    method: str = "GET"
    status: int = 0
    latency_ms: int = 0
    timestamp: str = ""
    cached: bool = False
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "endpoint": self.endpoint,
            "method": self.method,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "cached": self.cached,
        }
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class CollectorTrace:
    """Trace of a collector's execution."""

    name: str
    collector_type: str
    started_at: str = ""
    ended_at: str = ""
    duration_ms: int = 0
    items_collected: int = 0
    items_after_filter: int = 0
    api_calls: List[APICall] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None

    _start_time: float = field(default=0.0, repr=False)

    def start(self) -> None:
        """Mark collection start."""
        self._start_time = time.monotonic()
        self.started_at = datetime.now(timezone.utc).isoformat()

    def complete(
        self,
        items_collected: int = 0,
        items_after_filter: int = 0,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Mark collection complete."""
        self.ended_at = datetime.now(timezone.utc).isoformat()
        self.duration_ms = int((time.monotonic() - self._start_time) * 1000)
        self.items_collected = items_collected
        self.items_after_filter = items_after_filter
        self.success = success
        self.error = error

    def add_api_call(self, call: APICall) -> None:
        """Add an API call record."""
        self.api_calls.append(call)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "type": self.collector_type,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "items_collected": self.items_collected,
            "items_after_filter": self.items_after_filter,
            "api_calls": [c.to_dict() for c in self.api_calls],
            "success": self.success,
        }
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class DeliveryTrace:
    """Trace of report delivery."""

    channel: str
    started_at: str = ""
    ended_at: str = ""
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None

    _start_time: float = field(default=0.0, repr=False)

    def start(self) -> None:
        """Mark delivery start."""
        self._start_time = time.monotonic()
        self.started_at = datetime.now(timezone.utc).isoformat()

    def complete(self, success: bool = True, error: Optional[str] = None) -> None:
        """Mark delivery complete."""
        self.ended_at = datetime.now(timezone.utc).isoformat()
        self.duration_ms = int((time.monotonic() - self._start_time) * 1000)
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "channel": self.channel,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "success": self.success,
        }
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class RunTrace:
    """Complete trace of a MoltPulse run."""

    domain: str
    profile: str
    report_type: str
    depth: str = "default"
    run_id: str = ""
    started_at: str = ""
    ended_at: str = ""
    duration_ms: int = 0
    collectors: List[CollectorTrace] = field(default_factory=list)
    delivery: Optional[DeliveryTrace] = None

    _start_time: float = field(default=0.0, repr=False)

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = str(uuid4())

    def start(self) -> None:
        """Mark run start."""
        self._start_time = time.monotonic()
        self.started_at = datetime.now(timezone.utc).isoformat()

    def complete(self) -> None:
        """Mark run complete."""
        self.ended_at = datetime.now(timezone.utc).isoformat()
        self.duration_ms = int((time.monotonic() - self._start_time) * 1000)

    def add_collector_trace(self, trace: CollectorTrace) -> None:
        """Add a collector trace."""
        self.collectors.append(trace)

    def set_delivery_trace(self, trace: DeliveryTrace) -> None:
        """Set the delivery trace."""
        self.delivery = trace

    @property
    def total_items_collected(self) -> int:
        """Total items collected across all collectors."""
        return sum(c.items_collected for c in self.collectors)

    @property
    def total_items_after_filter(self) -> int:
        """Total items after filtering."""
        return sum(c.items_after_filter for c in self.collectors)

    @property
    def total_api_calls(self) -> int:
        """Total API calls made."""
        return sum(len(c.api_calls) for c in self.collectors)

    @property
    def successful_collectors(self) -> int:
        """Count of successful collectors."""
        return sum(1 for c in self.collectors if c.success)

    @property
    def failed_collectors(self) -> int:
        """Count of failed collectors."""
        return sum(1 for c in self.collectors if not c.success)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "run_id": self.run_id,
            "domain": self.domain,
            "profile": self.profile,
            "report_type": self.report_type,
            "depth": self.depth,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "collectors": [c.to_dict() for c in self.collectors],
        }
        if self.delivery:
            result["delivery"] = self.delivery.to_dict()
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Run: {self.run_id}",
            f"Domain: {self.domain} | Profile: {self.profile} | Report: {self.report_type}",
            "",
            "Collectors:",
        ]

        for i, c in enumerate(self.collectors):
            prefix = "└──" if i == len(self.collectors) - 1 else "├──"
            status = "✓" if c.success else "✗"

            lines.append(f"{prefix} {status} {c.name}")
            lines.append(f"│   ├── Duration: {c.duration_ms}ms")
            lines.append(f"│   ├── Items: {c.items_collected}")

            if c.api_calls:
                lines.append(f"│   └── API Calls: {len(c.api_calls)}")
                for j, call in enumerate(c.api_calls):
                    call_prefix = "│       └──" if j == len(c.api_calls) - 1 else "│       ├──"
                    lines.append(
                        f"{call_prefix} {call.method} {call.endpoint[:50]}... ({call.status}, {call.latency_ms}ms)"
                    )
            else:
                lines.append("│   └── API Calls: 0")

            if c.error:
                lines.append(f"│   └── Error: {c.error}")

        lines.append("")
        lines.append(f"Total Duration: {self.duration_ms}ms")
        lines.append(f"Total Items: {self.total_items_collected}")
        lines.append(f"Total API Calls: {self.total_api_calls}")

        if self.delivery:
            status = "✓" if self.delivery.success else "✗"
            lines.append("")
            lines.append(f"Delivery: {status} {self.delivery.channel} ({self.delivery.duration_ms}ms)")

        return "\n".join(lines)


# Thread-local storage for current collector trace
import threading

_trace_context = threading.local()


def get_current_collector_trace() -> Optional[CollectorTrace]:
    """Get the current collector trace from context."""
    return getattr(_trace_context, "collector_trace", None)


def set_current_collector_trace(trace: Optional[CollectorTrace]) -> None:
    """Set the current collector trace in context."""
    _trace_context.collector_trace = trace


class TracingContext:
    """Context manager for tracking API calls during collection."""

    def __init__(self, trace: CollectorTrace):
        self.trace = trace
        self.previous: Optional[CollectorTrace] = None

    def __enter__(self) -> CollectorTrace:
        self.previous = get_current_collector_trace()
        set_current_collector_trace(self.trace)
        self.trace.start()
        return self.trace

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        set_current_collector_trace(self.previous)
        return None


def record_api_call(
    endpoint: str,
    method: str = "GET",
    status: int = 0,
    latency_ms: int = 0,
    cached: bool = False,
    error: Optional[str] = None,
) -> None:
    """Record an API call in the current collector trace."""
    trace = get_current_collector_trace()
    if trace:
        trace.add_api_call(
            APICall(
                endpoint=endpoint,
                method=method,
                status=status,
                latency_ms=latency_ms,
                cached=cached,
                error=error,
            )
        )
