"""Profile configuration loader for MoltPulse."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .domain_loader import DomainConfig, find_domains_dir


class ProfileConfig:
    """Loaded profile configuration merged with domain."""

    def __init__(self, data: Dict[str, Any], domain: DomainConfig):
        self.domain = domain
        self._raw = data

        # Profile metadata
        self.name = data.get("profile_name", "default")
        self.extends = data.get("extends")

        # Focus filters
        self.focus: Dict[str, Any] = data.get("focus", {})

        # Thought leaders to track
        self.thought_leaders: List[Dict[str, Any]] = data.get("thought_leaders", [])

        # Publication preferences (subset of domain)
        self.publications: List[str] = data.get("publications", [])

        # Report preferences
        self.reports: Dict[str, bool] = data.get("reports", {})

        # Keywords for boosting/filtering
        self.keywords: Dict[str, List[str]] = data.get("keywords", {})

        # Delivery configuration
        self.delivery: Dict[str, Any] = data.get("delivery", {})

    def get_focused_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get entities filtered by profile focus.

        Returns entities from domain, filtered/prioritized by profile focus.
        """
        domain_entities = self.domain.get_entities(entity_type)
        focus_config = self.focus.get(entity_type, {})

        if not focus_config:
            return domain_entities

        # Get priority lists
        priority_1 = set(focus_config.get("priority_1", []))
        priority_2 = set(focus_config.get("priority_2", []))
        exclude = set(focus_config.get("exclude", []))

        result = []
        for entity in domain_entities:
            symbol = entity.get("symbol", "")
            name = entity.get("name", "")

            if symbol in exclude or name in exclude:
                continue

            # Set priority
            if symbol in priority_1 or name in priority_1:
                entity["_priority"] = 1
            elif symbol in priority_2 or name in priority_2:
                entity["_priority"] = 2
            else:
                entity["_priority"] = 3

            result.append(entity)

        # Sort by priority
        result.sort(key=lambda x: x.get("_priority", 3))
        return result

    def get_enabled_reports(self) -> List[str]:
        """Get list of report types enabled for this profile."""
        enabled = []
        for report_type, is_enabled in self.reports.items():
            if is_enabled:
                enabled.append(report_type)

        # If none specified, use all domain reports
        if not enabled:
            enabled = self.domain.get_report_types()

        return enabled

    def get_delivery_channel(self) -> str:
        """Get primary delivery channel."""
        return self.delivery.get("channel", "file")

    def get_delivery_config(self) -> Dict[str, Any]:
        """Get delivery configuration for the primary channel."""
        channel = self.get_delivery_channel()
        return self.delivery.get(channel, {})

    def get_fallback_delivery(self) -> Optional[Dict[str, Any]]:
        """Get fallback delivery configuration."""
        return self.delivery.get("fallback")

    def get_boost_keywords(self) -> List[str]:
        """Get keywords that should boost relevance."""
        return self.keywords.get("boost", [])

    def get_filter_keywords(self) -> List[str]:
        """Get keywords that should filter out items."""
        return self.keywords.get("filter", [])

    def get_thought_leader_handles(self) -> List[str]:
        """Get X/Twitter handles for thought leaders."""
        handles = []
        for leader in self.thought_leaders:
            handle = leader.get("x_handle")
            if handle:
                handles.append(handle)
        return handles

    def get_thought_leaders_by_priority(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get thought leaders grouped by priority."""
        by_priority: Dict[int, List[Dict[str, Any]]] = {}
        for leader in self.thought_leaders:
            priority = leader.get("priority", 3)
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(leader)
        return by_priority

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._raw


def list_profiles(domain_name: str) -> List[str]:
    """List available profiles for a domain."""
    domains_dir = find_domains_dir()
    profiles_dir = domains_dir / domain_name / "profiles"

    if not profiles_dir.exists():
        return []

    profiles = []
    for f in profiles_dir.glob("*.yaml"):
        profiles.append(f.stem)
    return sorted(profiles)


def load_profile(domain: DomainConfig, profile_name: str) -> ProfileConfig:
    """Load a profile configuration.

    Args:
        domain: The domain configuration
        profile_name: Name of the profile (e.g., "ricki")

    Returns:
        ProfileConfig object

    Raises:
        FileNotFoundError: If profile doesn't exist
        ValueError: If profile.yaml is invalid
    """
    profile_file = domain.domain_path / "profiles" / f"{profile_name}.yaml"

    if not profile_file.exists():
        raise FileNotFoundError(f"Profile not found: {profile_name} in {domain.name}")

    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid profile.yaml for {profile_name}: {e}")

    # Handle extends
    if data.get("extends"):
        base_profile_name = data["extends"]
        base_data = _load_profile_raw(domain.domain_path, base_profile_name)
        # Merge base with current (current overrides)
        data = _deep_merge(base_data, data)

    return ProfileConfig(data, domain)


def _load_profile_raw(domain_path: Path, profile_name: str) -> Dict[str, Any]:
    """Load raw profile data without processing."""
    profile_file = domain_path / "profiles" / f"{profile_name}.yaml"

    if not profile_file.exists():
        return {}

    with open(profile_file, "r") as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence."""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def validate_profile(config: ProfileConfig) -> List[str]:
    """Validate a profile configuration.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    if not config.name:
        errors.append("Profile name is required")

    # Validate delivery configuration
    channel = config.get_delivery_channel()
    if channel == "email":
        email_config = config.delivery.get("email", {})
        if not email_config.get("to"):
            errors.append("Email delivery requires 'to' address")
    elif channel == "whatsapp":
        whatsapp_config = config.delivery.get("whatsapp", {})
        if not whatsapp_config.get("to"):
            errors.append("WhatsApp delivery requires 'to' phone number")

    return errors


def create_profile(
    domain: DomainConfig,
    profile_name: str,
    focus_entities: Optional[Dict[str, List[str]]] = None,
    thought_leaders: Optional[List[Dict[str, Any]]] = None,
    publications: Optional[List[str]] = None,
    reports: Optional[Dict[str, bool]] = None,
    delivery: Optional[Dict[str, Any]] = None,
) -> Path:
    """Create a new profile.

    Args:
        domain: Domain configuration
        profile_name: Name for the profile
        focus_entities: Entity focus configuration
        thought_leaders: List of thought leader configs
        publications: List of publication names
        reports: Report enable/disable flags
        delivery: Delivery configuration

    Returns:
        Path to created profile file
    """
    profiles_dir = domain.domain_path / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    profile_data = {
        "profile_name": profile_name,
        "extends": "default",
        "focus": focus_entities or {},
        "thought_leaders": thought_leaders or [],
        "publications": publications or [],
        "reports": reports or {},
        "delivery": delivery or {"channel": "file"},
    }

    profile_file = profiles_dir / f"{profile_name}.yaml"
    with open(profile_file, "w") as f:
        yaml.dump(profile_data, f, default_flow_style=False, sort_keys=False)

    return profile_file
