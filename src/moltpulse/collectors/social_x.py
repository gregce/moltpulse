"""Social media collector using xAI API for X/Twitter search."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from moltpulse.core.collector_base import CollectorResult, SocialCollector
from moltpulse.core.lib import http, schema
from moltpulse.core.profile_loader import ProfileConfig


XAI_BASE_URL = "https://api.x.ai/v1/responses"
XAI_MODEL = "grok-4-1-fast"  # Required for x_search tool


class XAICollector(SocialCollector):
    """Collector for X/Twitter posts via xAI API with x_search tool."""

    @property
    def name(self) -> str:
        return "xAI X Search"

    def is_available(self) -> bool:
        """Check if xAI API key is configured."""
        return bool(self.config.get("XAI_API_KEY"))

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

        # Build search query
        handles_query = " OR ".join([f"from:@{h}" for h in handles[:10]])
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
        """Build the search prompt for xAI."""
        handles_str = ", ".join([f"@{h}" for h in handles])

        return f"""Search X/Twitter for recent posts from these thought leaders: {handles_str}

Focus on posts from {from_date} to {to_date}.

For each relevant post found, extract:
- The post text
- The author's handle
- Post URL
- Date posted
- Engagement metrics (likes, reposts, replies, quotes) if available

Return up to {max_items} posts, prioritizing:
1. Posts about industry trends, insights, or predictions
2. Posts with high engagement
3. Recent posts

Return the results as a JSON array with these fields:
- id: post ID
- text: post content
- url: link to post
- author_handle: @username
- date: YYYY-MM-DD format
- likes: number
- reposts: number
- replies: number
- quotes: number
- relevance: 0.0-1.0 score
- why_relevant: brief explanation
"""

    def _search_x(self, api_key: str, prompt: str) -> List[Dict[str, Any]]:
        """Execute X search via xAI API."""
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

            # Parse response - xAI returns structured data
            output = response.get("output", [])

            # Extract posts from response
            posts = []
            for item in output:
                if item.get("type") == "tool_result":
                    # Parse the tool result
                    content = item.get("content", "")
                    if isinstance(content, str):
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, list):
                                posts.extend(parsed)
                            elif isinstance(parsed, dict) and "posts" in parsed:
                                posts.extend(parsed["posts"])
                        except json.JSONDecodeError:
                            pass
                elif item.get("type") == "text":
                    # Try to extract JSON from text response
                    content = item.get("content", "")
                    try:
                        # Look for JSON array in response
                        start = content.find("[")
                        end = content.rfind("]") + 1
                        if start >= 0 and end > start:
                            parsed = json.loads(content[start:end])
                            posts.extend(parsed)
                    except json.JSONDecodeError:
                        pass

            return posts

        except http.HTTPError as e:
            raise e


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
