"""HTTP utilities for MoltPulse (stdlib only)."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0
USER_AGENT = "moltpulse/0.1 (Industry Intelligence Framework)"

DEBUG = os.environ.get("MOLTPULSE_DEBUG", "").lower() in ("1", "true", "yes")


def _record_trace(
    method: str,
    url: str,
    status: int,
    start_time: float,
    cached: bool = False,
    error: Optional[str] = None,
) -> None:
    """Record API call in active trace context if available."""
    try:
        from moltpulse.core.trace import record_api_call

        latency_ms = int((time.monotonic() - start_time) * 1000)
        record_api_call(
            endpoint=url,
            method=method,
            status=status,
            latency_ms=latency_ms,
            cached=cached,
            error=error,
        )
    except ImportError:
        # Trace module not available, skip
        pass


def log(msg: str):
    """Log debug message to stderr."""
    if DEBUG:
        sys.stderr.write(f"[DEBUG] {msg}\n")
        sys.stderr.flush()


class HTTPError(Exception):
    """HTTP request error with status code."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, body: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = MAX_RETRIES,
) -> Dict[str, Any]:
    """Make an HTTP request and return JSON response.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        headers: Optional headers dict
        json_data: Optional JSON body (for POST)
        timeout: Request timeout in seconds
        retries: Number of retries on failure

    Returns:
        Parsed JSON response

    Raises:
        HTTPError: On request failure
    """
    headers = headers or {}
    headers.setdefault("User-Agent", USER_AGENT)

    data = None
    if json_data is not None:
        data = json.dumps(json_data).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    log(f"{method} {url}")
    if json_data:
        log(f"Payload keys: {list(json_data.keys())}")

    # Track timing for tracing
    start_time = time.monotonic()
    status_code = 0
    error_msg = None

    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                status_code = response.status
                log(f"Response: {response.status} ({len(body)} bytes)")

                # Record API call in trace context if active
                _record_trace(method, url, status_code, start_time, cached=False, error=None)

                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = None
            try:
                body = e.read().decode("utf-8")
            except:
                pass
            log(f"HTTP Error {e.code}: {e.reason}")
            if body:
                log(f"Error body: {body[:500]}")
            last_error = HTTPError(f"HTTP {e.code}: {e.reason}", e.code, body)

            # Record trace for HTTP errors
            _record_trace(method, url, e.code, start_time, cached=False, error=str(e.reason))

            # Don't retry client errors (4xx) except rate limits
            if 400 <= e.code < 500 and e.code != 429:
                raise last_error

            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except urllib.error.URLError as e:
            log(f"URL Error: {e.reason}")
            last_error = HTTPError(f"URL Error: {e.reason}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except json.JSONDecodeError as e:
            log(f"JSON decode error: {e}")
            last_error = HTTPError(f"Invalid JSON response: {e}")
            raise last_error
        except (OSError, TimeoutError, ConnectionResetError) as e:
            # Handle socket-level errors
            log(f"Connection error: {type(e).__name__}: {e}")
            last_error = HTTPError(f"Connection error: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    if last_error:
        raise last_error
    raise HTTPError("Request failed with no error details")


def get(url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
    """Make a GET request."""
    return request("GET", url, headers=headers, **kwargs)


def post(
    url: str,
    json_data: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Make a POST request with JSON body."""
    return request("POST", url, headers=headers, json_data=json_data, **kwargs)


def fetch_text(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch URL and return raw text (for RSS, HTML, etc.)."""
    headers = headers or {}
    headers.setdefault("User-Agent", USER_AGENT)

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise HTTPError(f"HTTP {e.code}: {e.reason}", e.code)
    except urllib.error.URLError as e:
        raise HTTPError(f"URL Error: {e.reason}")
