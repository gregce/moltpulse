"""Tests for LLM enhancement module."""

import os
from unittest.mock import MagicMock, patch

from moltpulse.core.lib.schema import Report, ReportSection
from moltpulse.core.llm_enhance import (
    PromptBuilder,
    _build_summary_prompt,
    detect_llm_context,
    enhance_report,
)


class TestDetectLLMContext:
    """Tests for detect_llm_context function."""

    def test_explicit_mode_override(self):
        """Should return explicit mode when not 'auto'."""
        assert detect_llm_context("openclaw") == "openclaw"
        assert detect_llm_context("claude_cli") == "claude_cli"
        assert detect_llm_context("anthropic") == "anthropic"
        assert detect_llm_context("disabled") == "disabled"

    def test_auto_with_openclaw_env(self):
        """Should detect OpenClaw when OPENCLAW_GATEWAY_URL is set."""
        with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
            result = detect_llm_context("auto")
            assert result == "openclaw"

    def test_auto_disabled_when_nothing_available(self):
        """Should return disabled when no LLM backend available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("shutil.which", return_value=None):
                result = detect_llm_context("auto")
                assert result == "disabled"


class TestBuildSummaryPrompt:
    """Tests for _build_summary_prompt function."""

    def test_includes_report_metadata(self):
        """Should include report metadata in prompt."""
        report = Report(
            title="Test Report",
            domain="advertising",
            profile="ricki",
            report_type="daily_brief",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        prompt = _build_summary_prompt(report)

        assert "advertising" in prompt
        assert "ricki" in prompt
        assert "daily_brief" in prompt

    def test_includes_section_items(self):
        """Should include section items in prompt."""
        report = Report(
            title="Test Report",
            domain="advertising",
            profile="default",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
            sections=[
                ReportSection(
                    title="News",
                    items=[
                        {"title": "Big announcement from Apple"},
                        {"title": "Google launches new product"},
                    ],
                )
            ],
        )
        prompt = _build_summary_prompt(report)

        assert "News" in prompt
        assert "Apple" in prompt
        assert "Google" in prompt


class TestEnhanceReport:
    """Tests for enhance_report function."""

    def test_skips_when_skip_llm_true(self):
        """Should skip enhancement when skip_llm is True."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        result = enhance_report(report, skip_llm=True)

        assert result.llm_enhanced is False
        assert result.executive_summary is None

    def test_skips_when_disabled_mode(self):
        """Should skip enhancement when mode is disabled."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        result = enhance_report(report, mode="disabled")

        assert result.llm_enhanced is False
        assert result.executive_summary is None

    def test_records_error_on_failure(self):
        """Should record error when LLM call fails."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )

        # Mock a failing OpenClaw call
        with patch("moltpulse.core.llm_enhance._call_llm") as mock_call:
            mock_call.side_effect = RuntimeError("Connection failed")
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                result = enhance_report(report, mode="openclaw")

        assert result.llm_enhanced is False
        assert any("failed" in e.lower() for e in result.errors)

    def test_sets_llm_fields_on_success(self):
        """Should set LLM fields when enhancement succeeds."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )

        with patch("moltpulse.core.llm_enhance._call_openclaw") as mock_call:
            mock_call.return_value = "This is the executive summary."
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                result = enhance_report(report, mode="openclaw")

        assert result.llm_enhanced is True
        assert result.executive_summary == "This is the executive summary."
        assert result.llm_provider == "openclaw"


class TestReportSchemaLLMFields:
    """Tests for LLM-related fields in Report schema."""

    def test_report_has_llm_fields(self):
        """Report should have LLM enhancement fields."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )

        # Default values
        assert report.executive_summary is None
        assert report.strategic_recommendations == []
        assert report.llm_enhanced is False
        assert report.llm_provider is None

    def test_report_to_dict_includes_llm_fields(self):
        """Report.to_dict() should include LLM fields when set."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
            executive_summary="Summary here",
            strategic_recommendations=["Rec 1", "Rec 2"],
            llm_enhanced=True,
            llm_provider="openclaw",
        )
        d = report.to_dict()

        assert d["executive_summary"] == "Summary here"
        assert d["strategic_recommendations"] == ["Rec 1", "Rec 2"]
        assert d["llm_enhanced"] is True
        assert d["llm_provider"] == "openclaw"

    def test_report_to_dict_excludes_empty_llm_fields(self):
        """Report.to_dict() should exclude empty LLM fields."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        d = report.to_dict()

        assert "executive_summary" not in d
        assert "strategic_recommendations" not in d
        assert "llm_provider" not in d
        assert d["llm_enhanced"] is False  # Always included


class TestReportSectionInsight:
    """Tests for ReportSection insight field."""

    def test_section_has_insight_field(self):
        """ReportSection should have insight field."""
        section = ReportSection(title="Test", items=[])
        assert section.insight is None

    def test_section_to_dict_includes_insight(self):
        """ReportSection.to_dict() should include insight when set."""
        section = ReportSection(
            title="Test",
            items=[],
            insight="This is an insight.",
        )
        d = section.to_dict()

        assert d["insight"] == "This is an insight."

    def test_section_to_dict_excludes_empty_insight(self):
        """ReportSection.to_dict() should exclude insight when not set."""
        section = ReportSection(title="Test", items=[])
        d = section.to_dict()

        assert "insight" not in d


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    def test_default_system_context(self):
        """Should use default system context without profile."""
        report = Report(
            title="Test",
            domain="advertising",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        builder = PromptBuilder()
        system = builder.get_system_context(report)

        assert "advertising" in system
        assert "actionable" in system

    def test_custom_system_context_from_profile(self):
        """Should use custom system context from profile."""
        mock_profile = MagicMock()
        mock_profile.get_prompt.return_value = "Custom system context for testing."

        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        builder = PromptBuilder(mock_profile)
        system = builder.get_system_context(report)

        assert system == "Custom system context for testing."
        mock_profile.get_prompt.assert_called_with("system_context")

    def test_default_executive_summary_prompt(self):
        """Should use default executive summary prompt without profile."""
        builder = PromptBuilder()
        prompt = builder.get_executive_summary_prompt()

        assert "executive summary" in prompt.lower()
        assert "2-3 sentence" in prompt

    def test_custom_executive_summary_from_profile(self):
        """Should use custom executive summary from profile."""
        mock_profile = MagicMock()
        mock_profile.get_prompt.return_value = "Custom summary prompt."

        builder = PromptBuilder(mock_profile)
        prompt = builder.get_executive_summary_prompt()

        assert prompt == "Custom summary prompt."

    def test_section_insight_prompt_from_profile(self):
        """Should get section insight prompt from profile."""
        mock_profile = MagicMock()
        mock_profile.get_prompt.return_value = "Financial analysis prompt."

        builder = PromptBuilder(mock_profile)
        prompt = builder.get_section_insight_prompt("financial")

        assert prompt == "Financial analysis prompt."
        mock_profile.get_prompt.assert_called_with("financial")

    def test_section_insight_prompt_none_without_profile(self):
        """Should return None for section insight without profile."""
        builder = PromptBuilder()
        prompt = builder.get_section_insight_prompt("financial")

        assert prompt is None

    def test_build_summary_prompt_includes_sections(self):
        """build_summary_prompt should include report sections."""
        report = Report(
            title="Test Report",
            domain="advertising",
            profile="ricki",
            report_type="daily_brief",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
            sections=[
                ReportSection(
                    title="Financial",
                    items=[{"title": "Stock moved up"}],
                )
            ],
        )
        builder = PromptBuilder()
        prompt = builder.build_summary_prompt(report)

        assert "Financial" in prompt
        assert "Stock moved up" in prompt
        assert "advertising" in prompt


class TestEnhanceReportWithProfile:
    """Tests for enhance_report with profile integration."""

    def test_respects_profile_llm_disabled(self):
        """Should skip enhancement when profile has LLM disabled."""
        mock_profile = MagicMock()
        mock_profile.is_llm_enabled.return_value = False

        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        result = enhance_report(report, profile=mock_profile)

        assert result.llm_enhanced is False
        assert result.executive_summary is None

    def test_uses_profile_mode_override(self):
        """Should use profile mode when set."""
        mock_profile = MagicMock()
        mock_profile.is_llm_enabled.return_value = True
        mock_profile.get_llm_mode.return_value = "disabled"

        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )
        result = enhance_report(report, mode="auto", profile=mock_profile)

        # Profile mode "disabled" should take effect
        assert result.llm_enhanced is False

    def test_uses_profile_prompts(self):
        """Should use profile custom prompts for LLM calls."""
        mock_profile = MagicMock()
        mock_profile.is_llm_enabled.return_value = True
        mock_profile.get_llm_mode.return_value = "auto"
        mock_profile.get_prompt.return_value = "Custom prompt from profile"

        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )

        with patch("moltpulse.core.llm_enhance._call_openclaw") as mock_call:
            mock_call.return_value = "LLM response"
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                enhance_report(report, mode="openclaw", profile=mock_profile)

        # Verify profile prompts were used
        mock_profile.get_prompt.assert_called()


class TestSectionInsightsAndRecommendations:
    """Tests for section insights and strategic recommendations."""

    def test_generates_section_insights(self):
        """Should generate insights for each section."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
            sections=[
                ReportSection(title="News", items=[{"title": "Test news"}]),
                ReportSection(title="Financial", items=[{"symbol": "AAPL", "value": 150}]),
            ],
        )

        with patch("moltpulse.core.llm_enhance._call_llm") as mock_call:
            mock_call.return_value = "Generated insight"
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                enhance_report(report, mode="openclaw")

        # Each section should have an insight
        for section in report.sections:
            assert section.insight == "Generated insight"

    def test_generates_strategic_recommendations(self):
        """Should generate strategic recommendations."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
            sections=[ReportSection(title="News", items=[{"title": "Test"}])],
        )

        with patch("moltpulse.core.llm_enhance._call_llm") as mock_call:
            # Return different responses for different calls
            mock_call.side_effect = [
                "Executive summary",
                "Section insight",
                "1. Target executives during the transition period for outreach\n2. Approach new market entrants to build relationships\n3. Time your outreach to coincide with major campaigns",
            ]
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                enhance_report(report, mode="openclaw")

        assert len(report.strategic_recommendations) >= 1

    def test_skips_insights_when_disabled(self):
        """Should not generate insights when disabled."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
            sections=[ReportSection(title="News", items=[{"title": "Test"}])],
        )

        with patch("moltpulse.core.llm_enhance._call_llm") as mock_call:
            mock_call.return_value = "Response"
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                enhance_report(report, mode="openclaw", generate_insights=False)

        # Section should not have insight
        assert report.sections[0].insight is None

    def test_skips_recommendations_when_disabled(self):
        """Should not generate recommendations when disabled."""
        report = Report(
            title="Test",
            domain="test",
            profile="test",
            report_type="daily",
            generated_at="2025-01-31T12:00:00Z",
            date_range_from="2025-01-30",
            date_range_to="2025-01-31",
        )

        with patch("moltpulse.core.llm_enhance._call_llm") as mock_call:
            mock_call.return_value = "Response"
            with patch.dict(os.environ, {"OPENCLAW_GATEWAY_URL": "http://localhost:8080"}):
                enhance_report(report, mode="openclaw", generate_recommendations=False)

        assert report.strategic_recommendations == []


class TestParseRecommendations:
    """Tests for _parse_recommendations function."""

    def test_parses_numbered_list(self):
        """Should parse numbered recommendations."""
        from moltpulse.core.llm_enhance import _parse_recommendations

        text = """1. First recommendation here
2. Second recommendation here
3. Third recommendation here"""

        result = _parse_recommendations(text)
        assert len(result) == 3
        assert "First recommendation" in result[0]

    def test_parses_bullet_list(self):
        """Should parse bullet point recommendations."""
        from moltpulse.core.llm_enhance import _parse_recommendations

        text = """- First recommendation here
- Second recommendation here
- Third recommendation here"""

        result = _parse_recommendations(text)
        assert len(result) == 3

    def test_limits_to_five(self):
        """Should limit to 5 recommendations."""
        from moltpulse.core.llm_enhance import _parse_recommendations

        text = "\n".join([f"{i}. Recommendation {i}" for i in range(1, 10)])
        result = _parse_recommendations(text)
        assert len(result) <= 5

    def test_filters_short_items(self):
        """Should filter out very short items."""
        from moltpulse.core.llm_enhance import _parse_recommendations

        text = """1. Short
2. This is a proper recommendation with enough content
3. Too short"""

        result = _parse_recommendations(text)
        assert len(result) == 1
        assert "proper recommendation" in result[0]

    def test_filters_markdown_headers_and_separators(self):
        """Should filter out markdown headers and horizontal rules."""
        from moltpulse.core.llm_enhance import _parse_recommendations

        text = """--

## Recommendations

1. **Target executives during the transition period.** This is an important recommendation.
2. Approach new market entrants to build strong relationships early.
3. Time your outreach to coincide with their major campaign launches."""

        result = _parse_recommendations(text)
        # Should get 3 recommendations, not include "--" or "## Recommendations"
        assert len(result) == 3
        assert not any("--" in r for r in result)
        assert not any("##" in r for r in result)
        assert "Target executives" in result[0] or "transition" in result[0]
