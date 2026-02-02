"""LLM enhancement for MoltPulse reports.

Provides executive summaries, section insights, and strategic recommendations
using available LLM backends with fallback chain:
1. OpenClaw gateway (if OPENCLAW_GATEWAY_URL set or `openclaw gateway probe` succeeds)
2. Claude Code CLI (`claude --print`)
3. Anthropic SDK (if ANTHROPIC_API_KEY set)
4. Disabled (no LLM enhancement)

Narrative Mode (Pyramid Principle):
Uses a two-pass theme-first approach for coherent prose output with inline citations.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple

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


# =============================================================================
# Narrative Mode (Pyramid Principle) Enhancement
# =============================================================================

# Default prompts for narrative mode
THEME_IDENTIFICATION_PROMPT = """You are analyzing {domain} industry intelligence for {profile_purpose}.

Review the following data items and identify exactly 3 themes that would be most relevant
for {profile_purpose}. Each theme should:
- Combine evidence from multiple sources/types
- Have a clear "so what" implication
- Be actionable for the reader

DATA:
{formatted_items}

Respond with JSON only (no markdown code fences):
{{
  "themes": [
    {{
      "title": "Theme title (5-7 words)",
      "summary": "One sentence explaining the theme",
      "relevant_citations": [1, 3, 5],
      "implication": "One sentence on what this means for {profile_purpose}"
    }}
  ]
}}
"""

NARRATIVE_GENERATION_PROMPT = """You are writing an executive intelligence brief for {profile_purpose}.

Use the Barbara Minto Pyramid Principle:
1. Lead with the key takeaway (answer first)
2. Support with 3 themes (the "why")
3. Each theme backed by evidence with inline citations [1][2]
4. End with specific action items

THEMES IDENTIFIED:
{themes_json}

FULL DATA WITH CITATIONS:
{formatted_items}

Write a cohesive brief in this exact structure:

# {domain} Intelligence Brief
*{date}*

## Key Takeaway
[2-3 sentences: the bottom line for {profile_purpose}]

## {theme_1_title}
[Prose paragraph weaving evidence with [N] citations]

**{profile_angle} angle:** [1-2 sentences]

## {theme_2_title}
[Prose paragraph with citations]

**{profile_angle} angle:** [1-2 sentences]

## {theme_3_title}
[Prose paragraph with citations]

**{profile_angle} angle:** [1-2 sentences]

## Recommended Actions
1. [Specific, timed action]
2. [Specific, timed action]
3. [Specific, timed action]

Rules:
- Write in prose, not bullet lists (except for Recommended Actions)
- Use [N] citations inline where you reference specific evidence
- Keep each theme section to 2-3 sentences
- Make actions specific and timed
- Do not include a Sources section - that will be appended automatically
"""


def _get_item_title(item: Dict[str, Any], section_type: str) -> str:
    """Get display title for citation based on item type."""
    section_lower = section_type.lower()

    if "stock" in section_lower or section_type == "STOCKS":
        # Financial: "WPP +2.3% ($45.20)"
        symbol = item.get("entity_symbol") or item.get("symbol", "")
        change = item.get("change_pct") or item.get("change") or 0
        price = item.get("value") or item.get("price", 0)
        sign = "+" if change > 0 else ""
        if isinstance(price, (int, float)) and price > 0:
            return f"{symbol} {sign}{change:.1f}% (${price:.2f})"
        return f"{symbol} data"

    elif "author_handle" in item or "author" in item:
        # Social: "@garyvee post"
        handle = item.get("author_handle") or item.get("author", "")
        return f"@{handle} post"

    elif "activity_type" in item:
        # PE Activity: "Acquisition: Target by Acquirer"
        activity = item.get("activity_type", "deal")
        target = item.get("target_name", "")
        acquirer = item.get("acquirer_name", "")
        return f"{activity.title()}: {target} by {acquirer}"[:60]

    else:
        # News/RSS: use title
        title = item.get("title") or item.get("summary") or item.get("text", "")
        return title[:60]


def _item_to_context(item: Dict[str, Any], section_type: str) -> Dict[str, Any]:
    """Convert an item to a context dict for LLM consumption."""
    context: Dict[str, Any] = {}
    section_lower = section_type.lower()

    if "stock" in section_lower or section_type == "STOCKS":
        context["type"] = "financial"
        context["symbol"] = item.get("entity_symbol") or item.get("symbol", "")
        context["name"] = item.get("entity_name") or item.get("name", "")
        context["price"] = item.get("value") or item.get("price")
        context["change_pct"] = item.get("change_pct") or item.get("change")

    elif "author_handle" in item or "author" in item:
        context["type"] = "social"
        context["author"] = item.get("author_name") or item.get("author", "")
        context["handle"] = item.get("author_handle") or item.get("author", "")
        context["text"] = item.get("text", "")[:300]
        context["why_relevant"] = item.get("why_relevant", "")

    elif "activity_type" in item:
        context["type"] = "pe_activity"
        context["activity"] = item.get("activity_type", "")
        context["target"] = item.get("target_name", "")
        context["acquirer"] = item.get("acquirer_name", "")
        context["details"] = item.get("details", "")
        context["deal_value"] = item.get("deal_value_str") or item.get("deal_value", "")

    else:
        # News/RSS
        context["type"] = "news"
        context["title"] = item.get("title", "")
        context["snippet"] = item.get("snippet", "")[:200]
        context["source"] = item.get("source_name", "")

    return context


def _build_citation_context(
    report: Report, items_per_section: int = 10
) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, str]]]:
    """Assign citation IDs to all items and build context.

    Args:
        report: The report containing sections with items
        items_per_section: Maximum items to include per section

    Returns:
        Tuple of (all_items_with_ids, citation_map)
    """
    all_items: List[Dict[str, Any]] = []
    citation_map: Dict[int, Dict[str, str]] = {}
    citation_id = 1

    for section in report.sections:
        items = section.items[:items_per_section]

        for item in items:
            if isinstance(item, dict):
                item_dict = item
            else:
                # Convert dataclass to dict if needed
                item_dict = item.to_dict() if hasattr(item, "to_dict") else {}

            if not item_dict:
                continue

            # Build context for this item
            context = _item_to_context(item_dict, section.title)
            context["citation_id"] = citation_id
            context["section"] = section.title
            all_items.append(context)

            # Build citation reference
            url = (
                item_dict.get("url")
                or item_dict.get("source_url")
                or f"#cite-{citation_id}"
            )
            citation_map[citation_id] = {
                "url": url,
                "title": _get_item_title(item_dict, section.title),
                "source": item_dict.get("source_name", "Source"),
            }
            citation_id += 1

    return all_items, citation_map


def _format_items_for_prompt(items: List[Dict[str, Any]]) -> str:
    """Format items for LLM prompt."""
    lines = []
    for item in items:
        cid = item.get("citation_id", "?")
        item_type = item.get("type", "item")
        section = item.get("section", "")

        if item_type == "financial":
            symbol = item.get("symbol", "")
            change = item.get("change_pct") or 0
            price = item.get("price") or 0
            sign = "+" if change > 0 else ""
            if isinstance(price, (int, float)) and price > 0:
                lines.append(
                    f"[{cid}] FINANCIAL ({section}): {symbol} {sign}{change:.1f}% "
                    f"(${price:.2f})"
                )
            else:
                lines.append(f"[{cid}] FINANCIAL ({section}): {symbol}")

        elif item_type == "social":
            handle = item.get("handle", "")
            text = item.get("text", "")[:150]
            why = item.get("why_relevant", "")
            lines.append(f'[{cid}] SOCIAL ({section}): @{handle}: "{text}"')
            if why:
                lines.append(f"     → Why relevant: {why}")

        elif item_type == "pe_activity":
            activity = item.get("activity", "")
            target = item.get("target", "")
            acquirer = item.get("acquirer", "")
            details = item.get("details", "")[:100]
            lines.append(
                f"[{cid}] PE ACTIVITY ({section}): {activity} - {target} by {acquirer}"
            )
            if details:
                lines.append(f"     {details}")

        else:  # news
            title = item.get("title", "")
            source = item.get("source", "")
            snippet = item.get("snippet", "")[:100]
            lines.append(f"[{cid}] NEWS ({section}): {title}")
            lines.append(f"     Source: {source}")
            if snippet:
                lines.append(f"     {snippet}")

        lines.append("")  # Empty line between items

    return "\n".join(lines)


def _identify_themes(
    all_items: List[Dict[str, Any]],
    profile: Optional[ProfileConfig],
    llm_mode: LLMMode,
    domain: str,
) -> List[Dict[str, Any]]:
    """Pass 1: Identify themes from all data.

    Args:
        all_items: All items with citation IDs
        profile: Profile configuration
        llm_mode: LLM backend to use
        domain: Domain name

    Returns:
        List of identified themes
    """
    # Get profile-specific settings
    profile_purpose = "industry intelligence analysis"
    custom_theme_prompt = None

    if profile:
        prompts = profile.get_all_prompts()
        profile_purpose = prompts.get("profile_purpose", profile_purpose)
        custom_theme_prompt = prompts.get("theme_identification")

    # Build prompt
    formatted_items = _format_items_for_prompt(all_items)

    if custom_theme_prompt:
        # Allow profile to customize the prompt
        prompt = f"{custom_theme_prompt}\n\nDATA:\n{formatted_items}"
    else:
        prompt = THEME_IDENTIFICATION_PROMPT.format(
            domain=domain,
            profile_purpose=profile_purpose,
            formatted_items=formatted_items,
        )

    system = f"You are an expert {domain} industry analyst. Respond with valid JSON only."

    try:
        response = _call_llm(prompt, system, llm_mode)

        # Parse JSON response
        # Handle potential markdown code fence wrapping
        json_text = response.strip()
        if json_text.startswith("```"):
            # Extract JSON from code fence
            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)

        data = json.loads(json_text)
        themes = data.get("themes", [])

        # Validate themes
        valid_themes = []
        for theme in themes[:3]:  # Limit to 3 themes
            if isinstance(theme, dict) and "title" in theme:
                valid_themes.append({
                    "title": theme.get("title", "Theme"),
                    "summary": theme.get("summary", ""),
                    "relevant_citations": theme.get("relevant_citations", []),
                    "implication": theme.get("implication", ""),
                })

        return valid_themes

    except (json.JSONDecodeError, Exception):
        # Return default themes on failure
        return [
            {
                "title": "Industry Performance",
                "summary": "Key financial and operational developments",
                "relevant_citations": [],
                "implication": "Monitor for strategic implications",
            },
            {
                "title": "Market Dynamics",
                "summary": "Competitive and market landscape shifts",
                "relevant_citations": [],
                "implication": "Assess impact on strategy",
            },
            {
                "title": "Leadership & People",
                "summary": "Executive moves and organizational changes",
                "relevant_citations": [],
                "implication": "Identify relationship opportunities",
            },
        ]


def _generate_narrative(
    themes: List[Dict[str, Any]],
    all_items: List[Dict[str, Any]],
    citation_map: Dict[int, Dict[str, str]],
    profile: Optional[ProfileConfig],
    llm_mode: LLMMode,
    domain: str,
) -> str:
    """Pass 2: Generate narrative brief from themes.

    Args:
        themes: Identified themes from pass 1
        all_items: All items with citation IDs
        citation_map: Citation ID to reference mapping
        profile: Profile configuration
        llm_mode: LLM backend to use
        domain: Domain name

    Returns:
        Generated narrative brief markdown
    """
    # Get profile-specific settings
    profile_purpose = "industry intelligence analysis"
    profile_angle = "Strategic"
    custom_narrative_prompt = None

    if profile:
        prompts = profile.get_all_prompts()
        profile_purpose = prompts.get("profile_purpose", profile_purpose)
        profile_angle = prompts.get("profile_angle", "Strategic")
        custom_narrative_prompt = prompts.get("narrative_style")

    # Format themes
    themes_json = json.dumps(themes, indent=2)

    # Format items
    formatted_items = _format_items_for_prompt(all_items)

    # Get theme titles for prompt
    theme_titles = [t.get("title", f"Theme {i+1}") for i, t in enumerate(themes)]
    while len(theme_titles) < 3:
        theme_titles.append(f"Theme {len(theme_titles) + 1}")

    # Build prompt
    today = datetime.now().strftime("%B %d, %Y")

    if custom_narrative_prompt:
        # Profile can override narrative style
        prompt = f"""{custom_narrative_prompt}

THEMES:
{themes_json}

DATA WITH CITATIONS:
{formatted_items}

Write the brief for {profile_purpose}. Use [N] inline citations.
Date: {today}
Domain: {domain}
"""
    else:
        prompt = NARRATIVE_GENERATION_PROMPT.format(
            domain=domain.title(),
            profile_purpose=profile_purpose,
            profile_angle=profile_angle,
            themes_json=themes_json,
            formatted_items=formatted_items,
            date=today,
            theme_1_title=theme_titles[0],
            theme_2_title=theme_titles[1],
            theme_3_title=theme_titles[2],
        )

    system = (
        f"You are an expert {domain} industry analyst writing for {profile_purpose}. "
        "Write clear, actionable prose. Use inline [N] citations."
    )

    try:
        narrative = _call_llm(prompt, system, llm_mode)
        return narrative.strip()
    except Exception:
        # Return minimal narrative on failure
        return f"""# {domain.title()} Intelligence Brief
*{today}*

## Key Takeaway

Unable to generate narrative summary. Please review the data sections below.

## Data Summary

This report contains {len(all_items)} items across multiple categories.

## Recommended Actions

1. Review individual section data for insights
2. Check LLM configuration if narrative generation continues to fail
"""


def enhance_report_narrative(
    report: Report,
    mode: str = "auto",
    profile: Optional[ProfileConfig] = None,
) -> None:
    """Generate narrative brief using theme-first approach.

    This is the Pyramid Principle implementation:
    1. Collect all items from all sections into unified context
    2. Pass 1: LLM identifies 3 themes from all data
    3. Pass 2: LLM generates narrative organized by themes
    4. Store results in report

    Args:
        report: The report to enhance (mutated in place)
        mode: LLM mode override
        profile: Optional profile with custom prompts
    """
    # Check if narrative mode is enabled
    if profile:
        prompts = profile.get_all_prompts()
        if not prompts.get("narrative_mode", False):
            # Fall back to legacy enhancement
            return

    llm_mode = detect_llm_context(mode)
    if llm_mode == "disabled":
        return

    # 1. Collect all items with citation IDs
    all_items, citation_map = _build_citation_context(report)

    if not all_items:
        return

    # 2. Pass 1: Identify themes
    themes = _identify_themes(all_items, profile, llm_mode, report.domain)

    # 3. Pass 2: Generate narrative per theme
    narrative = _generate_narrative(
        themes, all_items, citation_map, profile, llm_mode, report.domain
    )

    # 4. Store results
    report.narrative_brief = narrative
    report.themes = themes
    report.citation_map = citation_map
    report.llm_enhanced = True
    report.llm_provider = llm_mode
