"""Caching utilities for Moltos."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path.home() / ".cache" / "moltos"
DEFAULT_TTL_HOURS = 24


def ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_key(*args: str) -> str:
    """Generate a cache key from arguments."""
    key_data = "|".join(str(a) for a in args)
    return hashlib.sha256(key_data.encode()).hexdigest()[:16]


def get_cache_path(cache_key: str, namespace: str = "default") -> Path:
    """Get path to cache file."""
    ns_dir = CACHE_DIR / namespace
    ns_dir.mkdir(parents=True, exist_ok=True)
    return ns_dir / f"{cache_key}.json"


def is_cache_valid(cache_path: Path, ttl_hours: int = DEFAULT_TTL_HOURS) -> bool:
    """Check if cache file exists and is within TTL."""
    if not cache_path.exists():
        return False

    try:
        stat = cache_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - mtime).total_seconds() / 3600
        return age_hours < ttl_hours
    except OSError:
        return False


def get_cache_age_hours(cache_path: Path) -> Optional[float]:
    """Get age of cache file in hours."""
    if not cache_path.exists():
        return None
    try:
        stat = cache_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - mtime).total_seconds() / 3600
    except OSError:
        return None


def load_cache(
    cache_key: str,
    namespace: str = "default",
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> Optional[dict]:
    """Load data from cache if valid."""
    cache_path = get_cache_path(cache_key, namespace)

    if not is_cache_valid(cache_path, ttl_hours):
        return None

    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_cache_with_age(
    cache_key: str,
    namespace: str = "default",
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> tuple:
    """Load data from cache with age info.

    Returns:
        Tuple of (data, age_hours) or (None, None) if invalid
    """
    cache_path = get_cache_path(cache_key, namespace)

    if not is_cache_valid(cache_path, ttl_hours):
        return None, None

    age = get_cache_age_hours(cache_path)

    try:
        with open(cache_path, "r") as f:
            return json.load(f), age
    except (json.JSONDecodeError, OSError):
        return None, None


def save_cache(cache_key: str, data: dict, namespace: str = "default"):
    """Save data to cache."""
    ensure_cache_dir()
    cache_path = get_cache_path(cache_key, namespace)

    try:
        with open(cache_path, "w") as f:
            json.dump(data, f)
    except OSError:
        pass  # Silently fail on cache write errors


def clear_cache(namespace: Optional[str] = None):
    """Clear cache files.

    Args:
        namespace: If provided, only clear that namespace. Otherwise clear all.
    """
    if namespace:
        ns_dir = CACHE_DIR / namespace
        if ns_dir.exists():
            for f in ns_dir.glob("*.json"):
                try:
                    f.unlink()
                except OSError:
                    pass
    else:
        if CACHE_DIR.exists():
            for ns_dir in CACHE_DIR.iterdir():
                if ns_dir.is_dir():
                    for f in ns_dir.glob("*.json"):
                        try:
                            f.unlink()
                        except OSError:
                            pass


def get_ttl_from_config() -> int:
    """Get TTL from config or use default."""
    try:
        ttl = os.environ.get("MOLTOS_CACHE_TTL_HOURS")
        if ttl:
            return int(ttl)
    except (ValueError, TypeError):
        pass
    return DEFAULT_TTL_HOURS
