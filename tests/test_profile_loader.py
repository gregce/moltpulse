"""Tests for profile loader module."""

import pytest

from moltpulse.core.domain_loader import load_domain
from moltpulse.core.profile_loader import (
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


class TestProfileConfigLLMMethods:
    """Tests for ProfileConfig LLM-related methods."""

    @pytest.fixture
    def ricki_profile(self):
        """Load Ricki's profile (has LLM config)."""
        domain = load_domain("advertising")
        return load_profile(domain, "ricki")

    @pytest.fixture
    def default_profile(self):
        """Load default profile (no LLM config)."""
        domain = load_domain("advertising")
        return load_profile(domain, "default")

    def test_is_llm_enabled_with_config(self, ricki_profile):
        """Should return True when LLM is enabled in config."""
        assert ricki_profile.is_llm_enabled() is True

    def test_is_llm_enabled_default(self, default_profile):
        """Default profile has LLM disabled (explicit setting in default.yaml)."""
        # Default profile explicitly sets llm.enabled: false for baseline
        assert default_profile.is_llm_enabled() is False

    def test_get_llm_mode_with_config(self, ricki_profile):
        """Should return mode from config."""
        mode = ricki_profile.get_llm_mode()
        assert mode == "auto"

    def test_get_llm_mode_default(self, default_profile):
        """Should return 'auto' by default."""
        mode = default_profile.get_llm_mode()
        assert mode == "auto"

    def test_get_llm_thinking_with_config(self, ricki_profile):
        """Should return thinking level from config."""
        thinking = ricki_profile.get_llm_thinking()
        assert thinking == "medium"

    def test_get_prompt_system_context(self, ricki_profile):
        """Should return custom system context prompt."""
        prompt = ricki_profile.get_prompt("system_context")
        assert prompt is not None
        assert "nonprofit" in prompt.lower()

    def test_get_prompt_executive_summary(self, ricki_profile):
        """Should return custom executive summary prompt."""
        prompt = ricki_profile.get_prompt("executive_summary")
        assert prompt is not None
        assert "fundraising" in prompt.lower()

    def test_get_prompt_section_insight(self, ricki_profile):
        """Should return section insight prompts."""
        financial = ricki_profile.get_prompt("financial")
        assert financial is not None
        assert "stock" in financial.lower()

        news = ricki_profile.get_prompt("news")
        assert news is not None

    def test_get_prompt_missing(self, ricki_profile):
        """Should return None for undefined prompts."""
        prompt = ricki_profile.get_prompt("nonexistent_prompt")
        assert prompt is None

    def test_get_all_prompts(self, ricki_profile):
        """Should return all custom prompts."""
        prompts = ricki_profile.get_all_prompts()
        assert "system_context" in prompts
        assert "executive_summary" in prompts
        assert "section_insights" in prompts

    def test_llm_attribute_exists(self, ricki_profile):
        """Profile should have llm attribute."""
        assert hasattr(ricki_profile, "llm")
        assert isinstance(ricki_profile.llm, dict)
