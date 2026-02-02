"""Tests for domain loader module."""

import pytest
from pathlib import Path

from moltpulse.core.domain_loader import (
    DomainConfig,
    list_domains,
    load_domain,
    validate_domain,
)


class TestListDomains:
    """Tests for list_domains function."""

    def test_lists_advertising_domain(self):
        """Should list the advertising domain."""
        domains = list_domains()
        assert "advertising" in domains

    def test_returns_list(self):
        """Should return a list."""
        domains = list_domains()
        assert isinstance(domains, list)


class TestLoadDomain:
    """Tests for load_domain function."""

    def test_loads_advertising_domain(self):
        """Should load the advertising domain successfully."""
        domain = load_domain("advertising")
        assert domain.name == "advertising"

    def test_raises_for_nonexistent_domain(self):
        """Should raise FileNotFoundError for nonexistent domain."""
        with pytest.raises(FileNotFoundError):
            load_domain("nonexistent_domain_xyz")

    def test_domain_has_required_attributes(self):
        """Should have all required attributes."""
        domain = load_domain("advertising")
        assert hasattr(domain, "name")
        assert hasattr(domain, "display_name")
        assert hasattr(domain, "entity_types")
        assert hasattr(domain, "collectors")
        assert hasattr(domain, "publications")
        assert hasattr(domain, "reports")


class TestDomainConfig:
    """Tests for DomainConfig class."""

    @pytest.fixture
    def advertising_domain(self):
        """Load the advertising domain for testing."""
        return load_domain("advertising")

    def test_get_entities(self, advertising_domain):
        """Should return entities for a type."""
        entities = advertising_domain.get_entities("holding_companies")
        assert len(entities) > 0
        assert all("symbol" in e for e in entities)

    def test_get_entities_empty_for_unknown_type(self, advertising_domain):
        """Should return empty list for unknown type."""
        entities = advertising_domain.get_entities("unknown_type")
        assert entities == []

    def test_get_collector_modules(self, advertising_domain):
        """Should return collector module paths."""
        modules = advertising_domain.get_collector_modules()
        assert len(modules) > 0
        assert "collectors.financial" in modules

    def test_get_report_types(self, advertising_domain):
        """Should return report types."""
        types = advertising_domain.get_report_types()
        assert "daily_brief" in types
        assert "weekly_digest" in types
        assert "fundraising" in types


class TestValidateDomain:
    """Tests for validate_domain function."""

    def test_advertising_domain_is_valid(self):
        """Advertising domain should pass validation."""
        domain = load_domain("advertising")
        errors = validate_domain(domain)
        assert errors == []

    def test_empty_domain_has_errors(self):
        """Empty domain config should have validation errors."""
        empty_config = DomainConfig({}, Path("/tmp"))
        errors = validate_domain(empty_config)
        assert len(errors) > 0
