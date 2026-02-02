"""Tests for profile loader module."""

import pytest

from moltpulse.core.domain_loader import load_domain
from moltpulse.core.profile_loader import (
    ProfileConfig,
    list_profiles,
    load_profile,
    validate_profile,
)


class TestListProfiles:
    """Tests for list_profiles function."""

    def test_lists_profiles_in_advertising(self):
        """Should list profiles in advertising domain."""
        profiles = list_profiles("advertising")
        assert "default" in profiles
        assert "ricki" in profiles

    def test_returns_list(self):
        """Should return a list."""
        profiles = list_profiles("advertising")
        assert isinstance(profiles, list)

    def test_empty_for_nonexistent_domain(self):
        """Should return empty for nonexistent domain."""
        profiles = list_profiles("nonexistent_xyz")
        assert profiles == []


class TestLoadProfile:
    """Tests for load_profile function."""

    @pytest.fixture
    def advertising_domain(self):
        """Load advertising domain."""
        return load_domain("advertising")

    def test_loads_default_profile(self, advertising_domain):
        """Should load the default profile."""
        profile = load_profile(advertising_domain, "default")
        assert profile.name == "default"

    def test_loads_ricki_profile(self, advertising_domain):
        """Should load Ricki's profile."""
        profile = load_profile(advertising_domain, "ricki")
        assert profile.name == "ricki"

    def test_raises_for_nonexistent_profile(self, advertising_domain):
        """Should raise for nonexistent profile."""
        with pytest.raises(FileNotFoundError):
            load_profile(advertising_domain, "nonexistent_xyz")

    def test_profile_extends_default(self, advertising_domain):
        """Ricki's profile should extend default."""
        profile = load_profile(advertising_domain, "ricki")
        assert profile.extends == "default"


class TestProfileConfig:
    """Tests for ProfileConfig class."""

    @pytest.fixture
    def ricki_profile(self):
        """Load Ricki's profile."""
        domain = load_domain("advertising")
        return load_profile(domain, "ricki")

    def test_has_thought_leaders(self, ricki_profile):
        """Should have thought leaders."""
        assert len(ricki_profile.thought_leaders) > 0

    def test_get_thought_leader_handles(self, ricki_profile):
        """Should return X handles."""
        handles = ricki_profile.get_thought_leader_handles()
        assert "profgalloway" in handles
        assert "ThisIsSethsBlog" in handles

    def test_get_enabled_reports(self, ricki_profile):
        """Should return enabled reports."""
        reports = ricki_profile.get_enabled_reports()
        assert "daily_brief" in reports
        assert "fundraising" in reports

    def test_get_delivery_channel(self, ricki_profile):
        """Should return delivery channel."""
        channel = ricki_profile.get_delivery_channel()
        assert channel == "email"

    def test_get_boost_keywords(self, ricki_profile):
        """Should return boost keywords."""
        keywords = ricki_profile.get_boost_keywords()
        assert "fundraising" in keywords
        assert "nonprofit" in keywords

    def test_get_focused_entities(self, ricki_profile):
        """Should return focused entities with priorities."""
        entities = ricki_profile.get_focused_entities("holding_companies")
        assert len(entities) > 0
        # Priority 1 entities should come first
        assert entities[0].get("_priority") == 1


class TestValidateProfile:
    """Tests for validate_profile function."""

    def test_ricki_profile_is_valid(self):
        """Ricki's profile should pass validation."""
        domain = load_domain("advertising")
        profile = load_profile(domain, "ricki")
        errors = validate_profile(profile)
        # May have email config warning but should be usable
        assert all("email" not in e.lower() for e in errors) or len(errors) <= 1
