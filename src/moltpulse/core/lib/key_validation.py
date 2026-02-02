"""API key validation and testing for MoltPulse."""

import json
import urllib.error
import urllib.request
from typing import Tuple

from .http import fetch_text


def test_alpha_vantage_key(key: str) -> Tuple[bool, str]:
    """Test Alpha Vantage API key with a minimal API call.

    Returns (success, message) tuple.
    """
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={key}"
        response = fetch_text(url, timeout=10)

        if not response:
            return False, "No response from API"

        data = json.loads(response)

        # Check for error messages
        if "Error Message" in data:
            return False, "Invalid API key"

        if "Note" in data:
            # Rate limit message
            return True, "Valid (rate limit reached)"

        if "Global Quote" in data:
            return True, "Valid"

        # Check for "Information" which indicates API key is valid but maybe wrong endpoint
        if "Information" in data:
            return True, "Valid"

        return False, "Unexpected response format"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid API key"
        return False, f"HTTP error: {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except json.JSONDecodeError:
        return False, "Invalid response format"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_newsdata_key(key: str) -> Tuple[bool, str]:
    """Test NewsData.io API key with a minimal API call.

    Returns (success, message) tuple.
    """
    try:
        url = f"https://newsdata.io/api/1/news?apikey={key}&q=test&size=1"
        response = fetch_text(url, timeout=10)

        if not response:
            return False, "No response from API"

        data = json.loads(response)

        if data.get("status") == "success":
            return True, "Valid"

        if data.get("status") == "error":
            error_msg = data.get("results", {}).get("message", "Unknown error")
            if "Invalid API key" in error_msg or "unauthorized" in error_msg.lower():
                return False, "Invalid API key"
            return False, error_msg

        return False, "Unexpected response format"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid API key"
        if e.code == 403:
            return False, "API key forbidden"
        return False, f"HTTP error: {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except json.JSONDecodeError:
        return False, "Invalid response format"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_newsapi_key(key: str) -> Tuple[bool, str]:
    """Test NewsAPI.org API key with a minimal API call.

    Returns (success, message) tuple.
    """
    try:
        url = f"https://newsapi.org/v2/top-headlines?apiKey={key}&country=us&pageSize=1"
        response = fetch_text(url, timeout=10)

        if not response:
            return False, "No response from API"

        data = json.loads(response)

        if data.get("status") == "ok":
            return True, "Valid"

        if data.get("status") == "error":
            code = data.get("code", "")
            if code == "apiKeyInvalid":
                return False, "Invalid API key"
            if code == "rateLimited":
                return True, "Valid (rate limited)"
            return False, data.get("message", "Unknown error")

        return False, "Unexpected response format"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid API key"
        if e.code == 429:
            return True, "Valid (rate limited)"
        return False, f"HTTP error: {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except json.JSONDecodeError:
        return False, "Invalid response format"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_xai_key(key: str) -> Tuple[bool, str]:
    """Test xAI API key.

    Note: xAI may not have a simple validation endpoint,
    so we do a basic format check and attempt a minimal call.

    Returns (success, message) tuple.
    """
    # Basic format validation
    if not key or len(key) < 10:
        return False, "Key too short"

    # xAI API validation would require knowing their endpoint structure
    # For now, accept keys that pass format validation
    # TODO: Implement actual API validation when xAI docs are available
    if key.startswith("xai-") or key.startswith("sk-"):
        return True, "Format valid (not verified with API)"

    return True, "Format valid (not verified with API)"


def test_openai_key(key: str) -> Tuple[bool, str]:
    """Test OpenAI API key with a minimal API call.

    Returns (success, message) tuple.
    """
    try:
        url = "https://api.openai.com/v1/models"
        headers = {
            "Authorization": f"Bearer {key}",
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if "data" in data:
                return True, "Valid"
            return True, "Valid"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid API key"
        if e.code == 429:
            return True, "Valid (rate limited)"
        return False, f"HTTP error: {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_intellizence_key(key: str) -> Tuple[bool, str]:
    """Test Intellizence API key.

    Note: Intellizence validation depends on their specific API.
    For now, do a basic format check.

    Returns (success, message) tuple.
    """
    if not key or len(key) < 10:
        return False, "Key too short"

    # TODO: Implement actual API validation when endpoint is known
    return True, "Format valid (not verified with API)"


# Mapping of key names to their test functions
KEY_TESTERS = {
    "ALPHA_VANTAGE_API_KEY": test_alpha_vantage_key,
    "NEWSDATA_API_KEY": test_newsdata_key,
    "NEWSAPI_API_KEY": test_newsapi_key,
    "XAI_API_KEY": test_xai_key,
    "OPENAI_API_KEY": test_openai_key,
    "INTELLIZENCE_API_KEY": test_intellizence_key,
}


def test_key(key_name: str, value: str) -> Tuple[bool, str]:
    """Test an API key by name.

    Returns (success, message) tuple.
    """
    if key_name not in KEY_TESTERS:
        return True, "No validation available"

    tester = KEY_TESTERS[key_name]
    return tester(value)


def test_all_keys(config: dict) -> dict:
    """Test all configured API keys.

    Returns dict mapping key name to (success, message) tuple.
    """
    results = {}

    for key_name in KEY_TESTERS:
        value = config.get(key_name)
        if value:
            results[key_name] = test_key(key_name, value)
        else:
            results[key_name] = (None, "Not configured")

    return results
