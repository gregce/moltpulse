"""Environment and API key management for MoltPulse."""

import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONFIG_DIR = Path.home() / ".config" / "moltpulse"
CONFIG_FILE = CONFIG_DIR / ".env"


# API Key Registry - metadata for all supported API keys
API_KEY_REGISTRY = {
    "ALPHA_VANTAGE_API_KEY": {
        "description": "Financial data (stock prices)",
        "provider": "Alpha Vantage",
        "signup_url": "https://www.alphavantage.co/support/#api-key",
        "enables": ["financial"],
        "required": False,
    },
    "NEWSDATA_API_KEY": {
        "description": "News aggregation",
        "provider": "NewsData.io",
        "signup_url": "https://newsdata.io/register",
        "enables": ["news"],
        "required": False,
    },
    "NEWSAPI_API_KEY": {
        "description": "News aggregation (fallback)",
        "provider": "NewsAPI",
        "signup_url": "https://newsapi.org/register",
        "enables": ["news"],
        "required": False,
    },
    "XAI_API_KEY": {
        "description": "X/Twitter search",
        "provider": "xAI",
        "signup_url": "https://x.ai/",
        "enables": ["social_x"],
        "required": False,
    },
    "OPENAI_API_KEY": {
        "description": "Enhanced analysis",
        "provider": "OpenAI",
        "signup_url": "https://platform.openai.com/api-keys",
        "enables": ["social_openai"],
        "required": False,
    },
    "INTELLIZENCE_API_KEY": {
        "description": "M&A and PE data",
        "provider": "Intellizence",
        "signup_url": "https://www.intellizence.com/",
        "enables": ["pe_activity"],
        "required": False,
    },
}

# Settings Registry - metadata for feature flags and settings
SETTINGS_REGISTRY = {
    "MOLTPULSE_CACHE_TTL_HOURS": {
        "description": "Cache time-to-live in hours",
        "default": "24",
        "type": "integer",
    },
    "MOLTPULSE_ENABLE_SCRAPING": {
        "description": "Enable web scraping",
        "default": "true",
        "type": "boolean",
    },
    "MOLTPULSE_DEBUG": {
        "description": "Enable debug output",
        "default": "false",
        "type": "boolean",
    },
}

# Collector information for status display
COLLECTOR_INFO = {
    "financial": {
        "name": "Financial",
        "description": "Alpha Vantage stock data",
        "requires": ["ALPHA_VANTAGE_API_KEY"],
    },
    "news": {
        "name": "News",
        "description": "News aggregation",
        "requires": ["NEWSDATA_API_KEY", "NEWSAPI_API_KEY"],  # Either one works
        "requires_any": True,
    },
    "rss": {
        "name": "RSS",
        "description": "RSS feeds (no key required)",
        "requires": [],
    },
    "social_x": {
        "name": "Social/X",
        "description": "X/Twitter search",
        "requires": ["XAI_API_KEY"],
    },
    "social_openai": {
        "name": "Social/OpenAI",
        "description": "OpenAI-powered analysis",
        "requires": ["OPENAI_API_KEY"],
    },
    "pe_activity": {
        "name": "PE/M&A",
        "description": "M&A tracking",
        "requires": ["INTELLIZENCE_API_KEY"],
    },
    "web_scraper": {
        "name": "Web Scraper",
        "description": "Playwright-based scraping",
        "requires": [],
        "requires_setting": "MOLTPULSE_ENABLE_SCRAPING",
    },
}


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
    """Load configuration from ~/.config/moltpulse/.env and environment.

    Environment variables override file values.
    """
    # Load from config file first
    file_env = load_env_file(CONFIG_FILE)

    # Collect all supported keys
    keys = list(API_KEY_REGISTRY.keys()) + list(SETTINGS_REGISTRY.keys())

    config = {}
    for key in keys:
        config[key] = os.environ.get(key) or file_env.get(key)

    # Set defaults for settings
    for key, info in SETTINGS_REGISTRY.items():
        if config.get(key) is None:
            config[key] = info["default"]

    return config


def config_exists() -> bool:
    """Check if configuration file exists."""
    return CONFIG_FILE.exists()


def ensure_config_dir() -> Path:
    """Ensure config directory exists and return path."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def set_config_value(key: str, value: str) -> None:
    """Write or update a key in the config file.

    Creates the config file if it doesn't exist.
    Sets file permissions to 0600 for security.
    """
    ensure_config_dir()

    # Load existing config
    existing = load_env_file(CONFIG_FILE)
    existing[key] = value

    # Write back all values
    _write_env_file(existing)


def unset_config_value(key: str) -> bool:
    """Remove a key from the config file.

    Returns True if key was found and removed, False otherwise.
    """
    if not CONFIG_FILE.exists():
        return False

    existing = load_env_file(CONFIG_FILE)
    if key not in existing:
        return False

    del existing[key]
    _write_env_file(existing)
    return True


def _write_env_file(values: Dict[str, str]) -> None:
    """Write values to the .env file with secure permissions."""
    ensure_config_dir()

    lines = ["# MoltPulse Configuration", "# Generated by moltpulse config", ""]

    # Group API keys
    api_keys = {k: v for k, v in values.items() if k in API_KEY_REGISTRY}
    settings = {k: v for k, v in values.items() if k in SETTINGS_REGISTRY}
    other = {k: v for k, v in values.items() if k not in API_KEY_REGISTRY and k not in SETTINGS_REGISTRY}

    if api_keys:
        lines.append("# API Keys")
        for key, value in sorted(api_keys.items()):
            lines.append(f"{key}={value}")
        lines.append("")

    if settings:
        lines.append("# Settings")
        for key, value in sorted(settings.items()):
            lines.append(f"{key}={value}")
        lines.append("")

    if other:
        lines.append("# Other")
        for key, value in sorted(other.items()):
            lines.append(f"{key}={value}")
        lines.append("")

    # Write file
    CONFIG_FILE.write_text("\n".join(lines))

    # Set secure permissions (owner read/write only)
    CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def mask_key(value: Optional[str], visible_chars: int = 4) -> str:
    """Mask API key for display, showing only first and last few characters.

    Examples:
        "sk-abc123xyz789" -> "sk-a...789"
        "short" -> "s...t"
        None -> "not set"
    """
    if not value:
        return "not set"

    if len(value) <= visible_chars * 2 + 3:
        # Too short to mask meaningfully
        return value[:2] + "..." + value[-2:] if len(value) > 4 else "***"

    return value[:visible_chars] + "..." + value[-visible_chars:]


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
        "web_scraper": str(config.get("MOLTPULSE_ENABLE_SCRAPING", "")).lower() in ("1", "true", "yes"),
    }


def get_collector_status(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get detailed status of all collectors.

    Returns list of dicts with collector info and availability.
    """
    available = get_available_collectors(config)
    result = []

    for collector_id, info in COLLECTOR_INFO.items():
        status = {
            "id": collector_id,
            "name": info["name"],
            "description": info["description"],
            "available": available.get(collector_id, False),
            "requires": info.get("requires", []),
        }

        # Determine what's missing
        if not status["available"] and info.get("requires"):
            missing = [k for k in info["requires"] if not config.get(k)]
            if info.get("requires_any"):
                status["missing"] = f"needs one of: {', '.join(missing)}"
            elif missing:
                status["missing"] = f"needs {missing[0]}"

        result.append(status)

    return result


def get_missing_keys(config: Dict[str, Any]) -> List[str]:
    """Return list of missing API keys that would enable more collectors."""
    missing = []
    for key, info in API_KEY_REGISTRY.items():
        if not config.get(key):
            missing.append(f"{key} - {info['description']}")
    return missing


def get_api_key_status(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get status of all API keys with metadata.

    Returns list of dicts with key info, value (masked), and status.
    """
    result = []
    for key, info in API_KEY_REGISTRY.items():
        value = config.get(key)
        result.append({
            "key": key,
            "description": info["description"],
            "provider": info["provider"],
            "signup_url": info["signup_url"],
            "configured": bool(value),
            "value_masked": mask_key(value),
            "enables": info["enables"],
        })
    return result


def get_settings_status(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get status of all settings.

    Returns list of dicts with setting info and current value.
    """
    result = []
    for key, info in SETTINGS_REGISTRY.items():
        value = config.get(key, info["default"])
        result.append({
            "key": key,
            "description": info["description"],
            "value": value,
            "default": info["default"],
            "type": info["type"],
        })
    return result


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    config = get_config()
    return str(config.get("MOLTPULSE_DEBUG", "")).lower() in ("1", "true", "yes")
