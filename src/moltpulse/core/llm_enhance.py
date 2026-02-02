"""LLM enhancement for MoltPulse reports.

Provides executive summaries, section insights, and strategic recommendations
using available LLM backends with fallback chain:
1. OpenClaw gateway (if OPENCLAW_GATEWAY_URL set or `openclaw gateway probe` succeeds)
2. Claude Code CLI (`claude --print`)
3. Anthropic SDK (if ANTHROPIC_API_KEY set)
4. Disabled (no LLM enhancement)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING, Literal, Optional

from moltpulse.core.lib.schema import Report

if TYPE_CHECKING:
    from moltpulse.core.profile_loader import ProfileConfig

LLMMode = Literal["openclaw", "claude_cli", "anthropic", "disabled"]


def detect_llm_context(profile_mode: str = "auto") -> LLMMode:
    """Detect available LLM backend.

    Args:
        profile_mode: Override from profile config. "auto" means detect.

    Returns:
        The detected or specified LLM mode.
    """
    # Profile override takes precedence
    if profile_mode and profile_mode != "auto":
        if profile_mode in ("openclaw", "claude_cli", "anthropic", "disabled"):
            return profile_mode  # type: ignore

    # Check OpenClaw gateway
    if os.environ.get("OPENCLAW_GATEWAY_URL"):
        return "openclaw"

    # Try openclaw gateway probe
    if shutil.which("openclaw"):
        try:
            result = subprocess.run(
                ["openclaw", "gateway", "probe"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "openclaw"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check Claude Code CLI
    if shutil.which("claude"):
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "claude_cli"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check Anthropic SDK
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401

            return "anthropic"
        except ImportError:
            pass

    return "disabled"


def _call_openclaw(prompt: str, system: Optional[str] = None) -> str:
    """Call OpenClaw gateway via subprocess."""
    cmd = ["openclaw", "message", "send", prompt, "--json"]
    if system:
        cmd.extend(["--system", system])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"OpenClaw error: {result.stderr}")

    try:
        response = json.loads(result.stdout)
        return response.get("content", result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()


def _call_claude_cli(prompt: str, system: Optional[str] = None) -> str:
    """Call Claude Code CLI via subprocess.

    Uses file-based prompting for large content (>10KB).
    """
    directive = system or "Analyze and respond concisely"

    # For large content, use temp file approach
    if len(prompt) > 10000:
        return _call_claude_cli_via_file(prompt, directive)

    # Inline approach for smaller content
    # Escape shell special characters
    escaped = prompt.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("$", "\\$").replace("`", "\\`")

    cmd = f'echo "{escaped}" | claude --print "{directive}"'
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr}")

    return _parse_claude_response(result.stdout)


def _call_claude_cli_via_file(prompt: str, directive: str) -> str:
    """Use temp files for large content."""
    prompt_file = None
    response_file = None

    try:
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write(prompt)
            prompt_file = f.name

        response_file = tempfile.mktemp(suffix=".txt")

        cmd = (
            f'cat "{prompt_file}" | claude --dangerously-skip-permissions '
            f'--print "{directive}" > "{response_file}" 2>&1'
        )
        subprocess.run(cmd, shell=True, timeout=180)

        with open(response_file) as f:
            return _parse_claude_response(f.read())

    finally:
        if prompt_file and os.path.exists(prompt_file):
            os.unlink(prompt_file)
        if response_file and os.path.exists(response_file):
            os.unlink(response_file)


def _parse_claude_response(stdout: str) -> str:
    """Parse Claude CLI response, extracting from markdown blocks if present."""
    import re

    # Try JSON extraction from markdown blocks
    json_match = re.search(r"```json\s*(.*?)\s*```", stdout, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict) and "content" in data:
                return data["content"]
            return json_match.group(1)
        except json.JSONDecodeError:
            pass

    return stdout.strip()


def _call_anthropic(prompt: str, system: Optional[str] = None) -> str:
    """Call Anthropic API directly using SDK."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed")

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system or "You are a helpful assistant.",
        messages=messages,
    )

    return response.content[0].text


class PromptBuilder:
    """Builds prompts for LLM enhancement, using profile customizations when available."""

    # Default prompts
    DEFAULT_SYSTEM = (
        "You are analyzing {domain} industry intelligence. "
        "Focus on actionable insights. Be concise."
    )

    DEFAULT_EXECUTIVE_SUMMARY = """Provide a 2-3 sentence executive summary highlighting the single most important
development and its key implications. Be specific and actionable."""

    DEFAULT_RECOMMENDATIONS = """Provide 3-5 specific, actionable recommendations based on this intelligence.
Consider timing and prioritization. Be concise."""

    def __init__(self, profile: Optional[ProfileConfig] = None):
        """Initialize PromptBuilder.

        Args:
            profile: Optional profile with custom prompts.
        """
        self.profile = profile

    def get_system_context(self, report: Report) -> str:
        """Get system context prompt."""
        if self.profile:
            custom = self.profile.get_prompt("system_context")
            if custom:
                return custom

        return self.DEFAULT_SYSTEM.format(domain=report.domain)

    def get_executive_summary_prompt(self) -> str:
        """Get executive summary prompt."""
        if self.profile:
            custom = self.profile.get_prompt("executive_summary")
            if custom:
                return custom

        return self.DEFAULT_EXECUTIVE_SUMMARY

    def get_recommendations_prompt(self) -> str:
        """Get recommendations prompt."""
        if self.profile:
            custom = self.profile.get_prompt("recommendations")
            if custom:
                return custom

        return self.DEFAULT_RECOMMENDATIONS

    def get_section_insight_prompt(self, section_key: str) -> Optional[str]:
        """Get prompt for a specific section insight.

        Args:
            section_key: The section key (e.g., "financial", "news", "pe_activity")

        Returns:
            Custom prompt if defined, None otherwise.
        """
        if self.profile:
            return self.profile.get_prompt(section_key)
        return None

    def build_summary_prompt(self, report: Report) -> str:
        """Build full prompt for executive summary generation."""
        sections_text = self._format_sections(report)
        summary_instruction = self.get_executive_summary_prompt()

        return f"""Analyze this {report.report_type} report for the {report.domain} domain.

Report: {report.title}
Profile: {report.profile}
Date Range: {report.date_range_from} to {report.date_range_to}

Sections:
{chr(10).join(sections_text)}

{summary_instruction}"""

    def _format_sections(self, report: Report) -> list[str]:
        """Format report sections for prompt inclusion."""
        sections_text = []
        for section in report.sections:
            items_summary = []
            for item in section.items[:5]:  # Top 5 items per section
                if isinstance(item, dict):
                    title = item.get("title") or item.get("text", "")[:100]
                    items_summary.append(f"  - {title}")
                else:
                    items_summary.append(f"  - {str(item)[:100]}")
            sections_text.append(f"{section.title}:\n" + "\n".join(items_summary))
        return sections_text

    def build_section_insight_prompt(self, section_title: str, items: list) -> str:
        """Build prompt for a section insight.

        Args:
            section_title: The title of the section
            items: The items in the section

        Returns:
            The full prompt for generating the section insight.
        """
        # Format items for the prompt
        items_text = []
        for item in items[:10]:  # Top 10 items
            if isinstance(item, dict):
                if "title" in item:
                    items_text.append(f"- {item['title']}")
                    if item.get("snippet"):
                        items_text.append(f"  {item['snippet'][:150]}")
                elif "text" in item:
                    items_text.append(f"- {item['text'][:200]}")
                elif "symbol" in item:
                    change = item.get("change_pct", 0)
                    items_text.append(
                        f"- {item.get('name', item['symbol'])}: "
                        f"{item.get('value', 'N/A')} ({change:+.1f}%)"
                    )
                else:
                    items_text.append(f"- {str(item)[:100]}")
            else:
                items_text.append(f"- {str(item)[:100]}")

        # Get custom section prompt if available
        section_key = section_title.lower().replace(" ", "_")
        custom_prompt = self.get_section_insight_prompt(section_key)

        if custom_prompt:
            instruction = custom_prompt
        else:
            instruction = (
                f"Provide a 1-2 sentence insight about this {section_title} data. "
                "Focus on the most significant pattern or implication."
            )

        return f"""{section_title} Data:
{chr(10).join(items_text)}

{instruction}"""

    def build_recommendations_prompt(self, report: Report) -> str:
        """Build prompt for strategic recommendations.

        Args:
            report: The report to analyze

        Returns:
            The full prompt for generating recommendations.
        """
        sections_text = self._format_sections(report)
        recommendations_instruction = self.get_recommendations_prompt()

        return f"""Based on this {report.report_type} report for the {report.domain} domain:

Report: {report.title}
Profile: {report.profile}

Sections:
{chr(10).join(sections_text)}

{recommendations_instruction}

Return recommendations as a numbered list (1. First recommendation, 2. Second, etc.)."""


def _build_summary_prompt(report: Report) -> str:
    """Build prompt for executive summary generation.

    Deprecated: Use PromptBuilder.build_summary_prompt() instead.
    """
    builder = PromptBuilder()
    return builder.build_summary_prompt(report)


def _call_llm(
    prompt: str,
    system: Optional[str],
    llm_mode: LLMMode,
) -> str:
    """Call the appropriate LLM backend.

    Args:
        prompt: The prompt to send
        system: Optional system context
        llm_mode: The LLM backend to use

    Returns:
        The LLM response text

    Raises:
        RuntimeError: If the LLM call fails
    """
    if llm_mode == "openclaw":
        return _call_openclaw(prompt, system)
    elif llm_mode == "claude_cli":
        return _call_claude_cli(prompt, system)
    elif llm_mode == "anthropic":
        return _call_anthropic(prompt, system)
    else:
        raise RuntimeError(f"Unknown LLM mode: {llm_mode}")


def _parse_recommendations(text: str) -> list[str]:
    """Parse numbered recommendations from LLM response.

    Args:
        text: The LLM response text

    Returns:
        List of recommendation strings
    """
    import re

    recommendations = []

    # Pre-clean the text: remove markdown headers and horizontal rules
    clean_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Skip markdown headers
        if stripped.startswith("#"):
            continue
        # Skip horizontal rules (---, ***, ___)
        if re.match(r"^[-*_]{2,}\s*$", stripped):
            continue
        # Skip empty lines
        if not stripped:
            continue
        clean_lines.append(line)

    clean_text = "\n".join(clean_lines)

    # Match numbered items like "1. ...", "1) ...", "- ..." but not standalone dashes
    pattern = r"(?:^|\n)\s*(?:\d+[\.\)]\s+)(.+?)(?=\n\s*\d+[\.\)]|$)"
    matches = re.findall(pattern, clean_text, re.DOTALL)

    for match in matches:
        rec = match.strip()
        # Filter: must be >20 chars, not just markdown formatting
        if rec and len(rec) > 20 and not rec.startswith("#"):
            # Clean up any bold markers at the start
            rec = re.sub(r"^\*\*(.+?)\*\*", r"\1", rec)
            recommendations.append(rec)

    # If regex didn't work, try line-by-line parsing
    if not recommendations:
        for line in clean_lines:
            line = line.strip()
            # Skip if it looks like a header or separator
            if line.startswith("#") or re.match(r"^[-*_]{2,}$", line):
                continue
            # Remove leading numbers/bullets
            clean = re.sub(r"^\d+[\.\)]\s+", "", line)
            clean = re.sub(r"^[\-\*]\s+", "", clean)
            # Filter: must be >20 chars
            if clean and len(clean) > 20:
                recommendations.append(clean)

    return recommendations[:5]  # Limit to 5


def enhance_report(
    report: Report,
    mode: str = "auto",
    skip_llm: bool = False,
    profile: Optional[ProfileConfig] = None,
    generate_insights: bool = True,
    generate_recommendations: bool = True,
) -> Report:
    """Enhance a report with LLM-generated content.

    Args:
        report: The report to enhance.
        mode: LLM mode override ("auto", "openclaw", "claude_cli", "anthropic", "disabled").
        skip_llm: If True, skip LLM enhancement entirely.
        profile: Optional profile with custom prompts.
        generate_insights: Whether to generate per-section insights.
        generate_recommendations: Whether to generate strategic recommendations.

    Returns:
        The enhanced report (mutated in place).
    """
    if skip_llm:
        return report

    # Check profile-level LLM settings
    if profile:
        if not profile.is_llm_enabled():
            return report
        # Profile mode overrides CLI mode if not disabled
        profile_mode = profile.get_llm_mode()
        if profile_mode != "auto":
            mode = profile_mode

    llm_mode = detect_llm_context(mode)
    if llm_mode == "disabled":
        return report

    # Build prompts using profile customizations
    builder = PromptBuilder(profile)
    system = builder.get_system_context(report)

    # 1. Generate executive summary
    try:
        summary_prompt = builder.build_summary_prompt(report)
        summary = _call_llm(summary_prompt, system, llm_mode)
        report.executive_summary = summary
        report.llm_enhanced = True
        report.llm_provider = llm_mode
    except Exception as e:
        report.errors.append(f"Executive summary generation failed: {e}")

    # 2. Generate per-section insights
    if generate_insights:
        for section in report.sections:
            if not section.items:
                continue
            try:
                insight_prompt = builder.build_section_insight_prompt(
                    section.title, section.items
                )
                insight = _call_llm(insight_prompt, system, llm_mode)
                section.insight = insight
            except Exception as e:
                report.errors.append(
                    f"Section insight generation failed for {section.title}: {e}"
                )

    # 3. Generate strategic recommendations
    if generate_recommendations:
        try:
            rec_prompt = builder.build_recommendations_prompt(report)
            rec_text = _call_llm(rec_prompt, system, llm_mode)
            report.strategic_recommendations = _parse_recommendations(rec_text)
        except Exception as e:
            report.errors.append(f"Recommendations generation failed: {e}")

    return report
