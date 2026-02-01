"""Environment and API key management for Moltos."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".config" / "moltos"
CONFIG_FILE = CONFIG_DIR / ".env"


def load_env_file(path: Path) -> Dict[str, str]:
    """Load environment variables from a file."""
    env = {}
    if not path.exists():
        return env

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value and value[0] in ('"', "'") and value[-1] == value[0]:
                    value = value[1:-1]
                if key and value:
                    env[key] = value
    return env


def get_config() -> Dict[str, Any]:
    """Load configuration from ~/.config/moltos/.env and environment.

    Environment variables override file values.
    """
    # Load from config file first
    file_env = load_env_file(CONFIG_FILE)

    # Define all supported API keys and config options
    keys = [
        # API Keys
        "ALPHA_VANTAGE_API_KEY",
        "NEWSDATA_API_KEY",
        "NEWSAPI_API_KEY",
        "XAI_API_KEY",
        "OPENAI_API_KEY",
        "INTELLIZENCE_API_KEY",
        # Feature flags
        "MOLTOS_ENABLE_SCRAPING",
        "MOLTOS_CACHE_TTL_HOURS",
        "MOLTOS_DEBUG",
    ]

    config = {}
    for key in keys:
        config[key] = os.environ.get(key) or file_env.get(key)

    # Set defaults for feature flags
    if config.get("MOLTOS_CACHE_TTL_HOURS") is None:
        config["MOLTOS_CACHE_TTL_HOURS"] = "24"
    if config.get("MOLTOS_ENABLE_SCRAPING") is None:
        config["MOLTOS_ENABLE_SCRAPING"] = "true"
    if config.get("MOLTOS_DEBUG") is None:
        config["MOLTOS_DEBUG"] = "false"

    return config


def config_exists() -> bool:
    """Check if configuration file exists."""
    return CONFIG_FILE.exists()


def ensure_config_dir() -> Path:
    """Ensure config directory exists and return path."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def get_available_collectors(config: Dict[str, Any]) -> Dict[str, bool]:
    """Determine which collectors are available based on API keys.

    Returns dict mapping collector name to availability.
    """
    return {
        "financial": bool(config.get("ALPHA_VANTAGE_API_KEY")),
        "news": bool(config.get("NEWSDATA_API_KEY") or config.get("NEWSAPI_API_KEY")),
        "rss": True,  # No API key needed
        "social_x": bool(config.get("XAI_API_KEY")),
        "social_openai": bool(config.get("OPENAI_API_KEY")),
        "pe_activity": bool(config.get("INTELLIZENCE_API_KEY")),
        "web_scraper": config.get("MOLTOS_ENABLE_SCRAPING", "").lower() in ("1", "true", "yes"),
    }


def get_missing_keys(config: Dict[str, Any]) -> list[str]:
    """Return list of missing API keys that would enable more collectors."""
    missing = []
    key_names = {
        "ALPHA_VANTAGE_API_KEY": "Alpha Vantage (financial data)",
        "NEWSDATA_API_KEY": "NewsData.io (news aggregation)",
        "XAI_API_KEY": "xAI (X/Twitter search)",
        "OPENAI_API_KEY": "OpenAI (enhanced analysis)",
    }

    for key, description in key_names.items():
        if not config.get(key):
            missing.append(f"{key} - {description}")

    return missing


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    config = get_config()
    return config.get("MOLTOS_DEBUG", "").lower() in ("1", "true", "yes")
