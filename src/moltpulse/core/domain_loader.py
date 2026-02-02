"""Domain configuration loader for MoltPulse."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class DomainConfig:
    """Loaded domain configuration."""

    def __init__(self, data: Dict[str, Any], domain_path: Path):
        self.domain_path = domain_path
        self.name = data.get("domain", "")
        self.display_name = data.get("display_name", self.name)

        # Entity types
        self.entity_types: Dict[str, List[Dict[str, Any]]] = data.get("entity_types", {})

        # Collectors
        self.collectors: List[Dict[str, str]] = data.get("collectors", [])

        # Publications
        self.publications: List[Dict[str, str]] = data.get("publications", [])

        # Reports
        self.reports: List[Dict[str, str]] = data.get("reports", [])

        # Raw data
        self._raw = data

    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get entities of a specific type."""
        return self.entity_types.get(entity_type, [])

    def get_all_entities(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all entity types and their entities."""
        return self.entity_types

    def get_collector_modules(self) -> List[str]:
        """Get list of collector module paths."""
        return [c.get("module", "") for c in self.collectors if c.get("module")]

    def get_publication_list(self) -> List[str]:
        """Get list of publication names."""
        return [p.get("name", "") for p in self.publications if p.get("name")]

    def get_report_types(self) -> List[str]:
        """Get list of available report types."""
        return [r.get("type", "") for r in self.reports if r.get("type")]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._raw


def find_domains_dir() -> Path:
    """Find the domains directory."""
    # Check relative to this file
    core_dir = Path(__file__).parent
    domains_dir = core_dir.parent / "domains"
    if domains_dir.exists():
        return domains_dir

    # Check current working directory
    cwd_domains = Path.cwd() / "domains"
    if cwd_domains.exists():
        return cwd_domains

    raise FileNotFoundError("Could not find domains directory")


def list_domains() -> List[str]:
    """List available domains."""
    domains_dir = find_domains_dir()
    domains = []
    for d in domains_dir.iterdir():
        if d.is_dir() and (d / "domain.yaml").exists():
            domains.append(d.name)
    return sorted(domains)


def load_domain(domain_name: str) -> DomainConfig:
    """Load a domain configuration.

    Args:
        domain_name: Name of the domain (e.g., "advertising")

    Returns:
        DomainConfig object

    Raises:
        FileNotFoundError: If domain doesn't exist
        ValueError: If domain.yaml is invalid
    """
    domains_dir = find_domains_dir()
    domain_path = domains_dir / domain_name
    config_file = domain_path / "domain.yaml"

    if not config_file.exists():
        raise FileNotFoundError(f"Domain not found: {domain_name} (no domain.yaml at {config_file})")

    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid domain.yaml for {domain_name}: {e}")

    return DomainConfig(data, domain_path)


def validate_domain(config: DomainConfig) -> List[str]:
    """Validate a domain configuration.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    if not config.name:
        errors.append("Domain name is required")

    if not config.entity_types:
        errors.append("At least one entity type is required")

    if not config.collectors:
        errors.append("At least one collector is required")

    # Validate collector module paths
    for c in config.collectors:
        module = c.get("module", "")
        if not module:
            errors.append(f"Collector missing module: {c}")

    return errors


def get_domain_collector_types(config: DomainConfig) -> List[str]:
    """Get list of collector types defined in domain."""
    return [c.get("type", "") for c in config.collectors if c.get("type")]


def create_domain_skeleton(domain_name: str, display_name: Optional[str] = None) -> Path:
    """Create a new domain skeleton.

    Args:
        domain_name: Name for the domain
        display_name: Optional display name

    Returns:
        Path to created domain directory
    """
    domains_dir = find_domains_dir()
    domain_path = domains_dir / domain_name

    # Create directories
    domain_path.mkdir(exist_ok=True)
    (domain_path / "collectors").mkdir(exist_ok=True)
    (domain_path / "reports").mkdir(exist_ok=True)
    (domain_path / "profiles").mkdir(exist_ok=True)

    # Create minimal domain.yaml
    config = {
        "domain": domain_name,
        "display_name": display_name or domain_name.replace("_", " ").title(),
        "entity_types": {},
        "collectors": [],
        "publications": [],
        "reports": [],
    }

    config_file = domain_path / "domain.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Create default profile
    default_profile = {
        "profile_name": "default",
        "focus": {},
        "thought_leaders": [],
        "publications": [],
        "reports": {},
        "delivery": {
            "channel": "file",
            "file": {"path": "~/moltpulse-reports"},
        },
    }

    default_profile_file = domain_path / "profiles" / "default.yaml"
    with open(default_profile_file, "w") as f:
        yaml.dump(default_profile, f, default_flow_style=False, sort_keys=False)

    # Create __init__.py files
    (domain_path / "collectors" / "__init__.py").touch()
    (domain_path / "reports" / "__init__.py").touch()

    return domain_path
