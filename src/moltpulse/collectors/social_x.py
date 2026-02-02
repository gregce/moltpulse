"""Social media collector using xAI API for X/Twitter search."""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from moltpulse.core.collector_base import CollectorResult, SocialCollector
from moltpulse.core.lib import http, schema
from moltpulse.core.profile_loader import ProfileConfig

XAI_BASE_URL = "https://api.x.ai/v1/responses"
XAI_MODEL = "grok-4-1-fast"  # Required for x_search tool

# Prompt template that asks for structured JSON response
X_SEARCH_PROMPT = """You have access to real-time X (Twitter) data.

Search for posts from EACH of these thought leaders: {handles}

CRITICAL: Return a BALANCED mix of posts from DIFFERENT handles. Do NOT let any single person dominate the results. Include posts from at least 3-4 different handles if available. Aim for roughly equal representation across all thought leaders listed.

Focus on posts from {from_date} to {to_date}. Find {min_items}-{max_items} high-quality, relevant posts.

IMPORTANT: Return ONLY valid JSON in this exact format, no other text:
{{
  "items": [
    {{
      "text": "Post text content (truncated if long)",
      "url": "https://x.com/user/status/...",
      "author_handle": "username",
      "date": "YYYY-MM-DD or null if unknown",
      "engagement": {{
        "likes": 100,
        "reposts": 25,
        "replies": 15,
        "quotes": 5
      }},
      "why_relevant": "Brief explanation of relevance",
      "relevance": 0.85
    }}
  ]
}}

Rules:
- relevance is 0.0 to 1.0 (1.0 = highly relevant)
- date must be YYYY-MM-DD format or null
- engagement can be null if unknown
- Prefer posts with substantive content about industry trends, insights, or predictions
- MUST include posts from multiple different thought leaders - diversity is required"""


class XAICollector(SocialCollector):
    """Collector for X/Twitter posts via xAI API with x_search tool."""

    REQUIRED_API_KEYS = ["XAI_API_KEY"]

    @property
    def name(self) -> str:
        return "xAI X Search"

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect X posts from thought leaders."""
        api_key = self.config.get("XAI_API_KEY")
        if not api_key:
            return CollectorResult(
                items=[],
                sources=[],
                error="xAI API key not configured",
            )

        handles = self.get_handles_to_track(profile)
        if not handles:
            return CollectorResult(
                items=[],
                sources=[],
                error="No thought leader handles in profile",
            )

        depth_config = self.get_depth_config(depth)
        max_items = depth_config.get("max_items", 25)

        items: List[schema.SocialItem] = []
        sources: List[schema.Source] = []
        errors = []

        # Get thought leader names for display
        leaders_by_handle = {}
        for leader in profile.thought_leaders:
            handle = leader.get("x_handle", "").lower().lstrip("@")
            if handle:
                leaders_by_handle[handle] = leader.get("name", handle)

        # Build search prompt for xAI
        search_prompt = self._build_search_prompt(handles, from_date, to_date, max_items)

        try:
            results = self._search_x(api_key, search_prompt)

            for post in results:
                author_handle = post.get("author_handle", "").lower().lstrip("@")
                author_name = leaders_by_handle.get(author_handle, author_handle)

                item = schema.SocialItem(
                    id=post.get("id", hashlib.md5(post.get("text", "").encode()).hexdigest()[:12]),
                    text=post.get("text", ""),
                    url=post.get("url", ""),
                    platform="x",
                    author_name=author_name,
                    author_handle=author_handle,
                    date=post.get("date"),
                    date_confidence=post.get("date_confidence", "med"),
                    engagement=schema.Engagement(
                        likes=post.get("likes"),
                        reposts=post.get("reposts"),
                        replies=post.get("replies"),
                        quotes=post.get("quotes"),
                    ) if any([post.get("likes"), post.get("reposts")]) else None,
                    relevance=post.get("relevance", 0.7),
                    why_relevant=post.get("why_relevant", ""),
                )
                items.append(item)

                if item.url:
                    sources.append(
                        schema.Source(
                            name=f"X - @{author_handle}",
                            url=item.url,
                            date_accessed=datetime.now(timezone.utc).date().isoformat(),
                        )
                    )

        except http.HTTPError as e:
            errors.append(f"xAI API error: {e}")

        return CollectorResult(
            items=items,
            sources=sources,
            error="; ".join(errors) if errors and not items else None,
        )

    def _build_search_prompt(
        self,
        handles: List[str],
        from_date: str,
        to_date: str,
        max_items: int,
    ) -> str:
        """Build the search prompt for xAI using structured JSON format."""
        handles_str = ", ".join([f"@{h}" for h in handles])
        min_items = max(5, max_items // 2)

        return X_SEARCH_PROMPT.format(
            handles=handles_str,
            from_date=from_date,
            to_date=to_date,
            min_items=min_items,
            max_items=max_items,
        )

    def _search_x(self, api_key: str, prompt: str) -> List[Dict[str, Any]]:
        """Execute X search via xAI API."""
        debug = os.environ.get("MOLTPULSE_DEBUG")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": XAI_MODEL,
            "tools": [{"type": "x_search"}],
            "input": [{"role": "user", "content": prompt}],
        }

        try:
            response = http.post(XAI_BASE_URL, json_data=payload, headers=headers, timeout=120)

            if debug:
                print(f"[DEBUG] xAI response keys: {response.keys()}", file=sys.stderr)

            # Check for API errors
            if "error" in response and response["error"]:
                error = response["error"]
                err_msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                if debug:
                    print(f"[DEBUG] xAI API error: {err_msg}", file=sys.stderr)
                return []

            # Extract output text from the nested response structure
            # xAI returns: output[].type="message", content[].type="output_text", text="..."
            output_text = ""
            if "output" in response:
                output = response["output"]
                if isinstance(output, str):
                    output_text = output
                elif isinstance(output, list):
                    for item in output:
                        if isinstance(item, dict):
                            # Look for type="message" (correct format)
                            if item.get("type") == "message":
                                content = item.get("content", [])
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "output_text":
                                        output_text = c.get("text", "")
                                        break
                            # Fallback: direct text field
                            elif "text" in item:
                                output_text = item["text"]
                        elif isinstance(item, str):
                            output_text = item
                        if output_text:
                            break

            if debug:
                print(f"[DEBUG] xAI output_text length: {len(output_text)}", file=sys.stderr)
                if output_text:
                    print(f"[DEBUG] xAI output_text preview: {output_text[:200]}...", file=sys.stderr)

            if not output_text:
                if debug:
                    print("[DEBUG] xAI no output_text found in response", file=sys.stderr)
                return []

            # Extract JSON with "items" from the response using regex
            json_match = re.search(r'\{[\s\S]*"items"[\s\S]*\}', output_text)
            if not json_match:
                if debug:
                    print("[DEBUG] xAI no JSON with 'items' found in output_text", file=sys.stderr)
                return []

            try:
                data = json.loads(json_match.group())
                items = data.get("items", [])

                if debug:
                    print(f"[DEBUG] xAI parsed {len(items)} items", file=sys.stderr)

                # Clean and validate items
                return self._clean_x_items(items)

            except json.JSONDecodeError as e:
                if debug:
                    print(f"[DEBUG] xAI JSON decode error: {e}", file=sys.stderr)
                return []

        except http.HTTPError as e:
            raise e

    def _clean_x_items(self, items: List[Dict]) -> List[Dict]:
        """Clean and validate X items from API response."""
        clean_items = []

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            url = item.get("url", "")
            if not url:
                continue

            # Parse engagement
            engagement = None
            eng_raw = item.get("engagement")
            if isinstance(eng_raw, dict):
                engagement = {
                    "likes": int(eng_raw.get("likes", 0)) if eng_raw.get("likes") else None,
                    "reposts": int(eng_raw.get("reposts", 0)) if eng_raw.get("reposts") else None,
                    "replies": int(eng_raw.get("replies", 0)) if eng_raw.get("replies") else None,
                    "quotes": int(eng_raw.get("quotes", 0)) if eng_raw.get("quotes") else None,
                }

            clean_item = {
                "id": f"X{i+1}",
                "text": str(item.get("text", "")).strip()[:500],
                "url": url,
                "author_handle": str(item.get("author_handle", "")).strip().lstrip("@"),
                "date": item.get("date"),
                "likes": engagement.get("likes") if engagement else None,
                "reposts": engagement.get("reposts") if engagement else None,
                "replies": engagement.get("replies") if engagement else None,
                "quotes": engagement.get("quotes") if engagement else None,
                "why_relevant": str(item.get("why_relevant", "")).strip(),
                "relevance": min(1.0, max(0.0, float(item.get("relevance", 0.5)))),
            }

            # Validate date format
            if clean_item["date"]:
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(clean_item["date"])):
                    clean_item["date"] = None

            clean_items.append(clean_item)

        return clean_items


class OpenAISocialCollector(SocialCollector):
    """Fallback collector using OpenAI for web search of social content."""

    @property
    def name(self) -> str:
        return "OpenAI Web Search (Social)"

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.config.get("OPENAI_API_KEY"))

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect social content via OpenAI web search."""
        api_key = self.config.get("OPENAI_API_KEY")
        if not api_key:
            return CollectorResult(
                items=[],
                sources=[],
                error="OpenAI API key not configured",
            )

        handles = self.get_handles_to_track(profile)
        if not handles:
            return CollectorResult(items=[], sources=[])

        # This would use OpenAI's web_search tool similar to last30days
        # For now, return empty as fallback
        return CollectorResult(
            items=[],
            sources=[],
            error="OpenAI social search not implemented",
        )
