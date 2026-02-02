# Contributing to MoltPulse

Thank you for your interest in contributing to MoltPulse! This guide will help you understand the codebase architecture and how to add new functionality.

## Development Setup

```bash
# Clone and install
git clone https://github.com/your-org/moltpulse.git
cd moltpulse

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"

# Run tests
uv run pytest tests/

# Check configuration
uv run moltpulse config
```

## Project Structure

```
moltpulse/
├── src/moltpulse/
│   ├── cli.py                      # Main CLI entry point
│   ├── core/
│   │   ├── orchestrator.py         # Coordinates collectors and reports
│   │   ├── collector_base.py       # Base classes for collectors
│   │   ├── domain_loader.py        # Loads domain.yaml configurations
│   │   ├── profile_loader.py       # Loads user profile configurations
│   │   ├── delivery.py             # Report delivery (email, file, console)
│   │   ├── trace.py                # Execution tracing for monitoring
│   │   ├── ui.py                   # Progress spinners and display
│   │   ├── cli/                    # CLI command implementations
│   │   │   ├── config_commands.py
│   │   │   ├── cron_commands.py
│   │   │   ├── domain_commands.py
│   │   │   └── profile_commands.py
│   │   └── lib/                    # Shared utilities
│   │       ├── schema.py           # Data models (NewsItem, FinancialItem, etc.)
│   │       ├── http.py             # HTTP client with caching
│   │       ├── env.py              # Configuration and API key management
│   │       ├── dates.py            # Date parsing and formatting
│   │       ├── dedupe.py           # Deduplication utilities
│   │       ├── score.py            # Item scoring algorithms
│   │       └── normalize.py        # Text normalization
│   ├── collectors/                 # Shared collectors (cross-domain)
│   │   ├── financial.py            # Alpha Vantage collector
│   │   ├── news.py                 # NewsData.io collector
│   │   ├── rss.py                  # RSS feed collector
│   │   ├── social_x.py             # xAI X/Twitter collector
│   │   └── web_scraper.py          # Playwright-based scraper
│   ├── domains/                    # Domain-specific implementations
│   │   └── advertising/
│   │       ├── domain.yaml         # Domain configuration
│   │       ├── collectors/         # Domain-specific collectors
│   │       │   ├── awards.py
│   │       │   └── pe_activity.py
│   │       ├── reports/            # Report generators
│   │       │   ├── daily_brief.py
│   │       │   ├── weekly_digest.py
│   │       │   └── fundraising.py
│   │       └── profiles/           # User profiles
│   │           ├── default.yaml
│   │           └── ricki.yaml
│   └── cron/                       # OpenClaw cron templates
│       ├── daily-brief.json
│       ├── weekly-digest.json
│       └── fundraising-outlook.json
├── tests/                          # Test suite
├── docs/                           # Documentation
└── README.md
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CLI (cli.py)                                                        │
│       │                                                              │
│       ▼                                                              │
│  Orchestrator (orchestrator.py)                                      │
│       │                                                              │
│       ├───────────────────────────────────────────────────┐          │
│       │                                                   │          │
│       ▼                                                   ▼          │
│  Domain Config (domain_loader.py)              Profile (profile_loader.py)
│  - Available collectors                        - Focus entities     │
│  - Entity types                                - Thought leaders    │
│  - Publications                                - Keywords           │
│  - Report types                                - Delivery settings  │
│       │                                                   │          │
│       └───────────────────────────────────────────────────┘          │
│                              │                                       │
│                              ▼                                       │
│                    Collectors (parallel execution)                   │
│                    - Financial → Alpha Vantage                       │
│                    - News → NewsData.io                              │
│                    - RSS → Feed URLs                                 │
│                    - Social → xAI API                                │
│                    - Awards → Web scraping                           │
│                    - PE Activity → Intellizence/News                 │
│                              │                                       │
│                              ▼                                       │
│                    Processing Pipeline                               │
│                    - Deduplicate (dedupe.py)                         │
│                    - Score (score.py)                                │
│                    - Filter & Sort                                   │
│                              │                                       │
│                              ▼                                       │
│                    Report Generator                                  │
│                    - Daily Brief                                     │
│                    - Weekly Digest                                   │
│                    - Fundraising Outlook                             │
│                              │                                       │
│                              ▼                                       │
│                    Delivery (delivery.py)                            │
│                    - Console                                         │
│                    - Email                                           │
│                    - File                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Common Contribution Types

### 1. Adding a New Collector

Collectors fetch data from external sources. To add a new collector:

**Step 1: Create the collector class**

```python
# src/moltpulse/collectors/my_source.py

from moltpulse.core.collector_base import Collector, CollectorResult, NewsCollector
from moltpulse.core.lib import schema
from moltpulse.core.profile_loader import ProfileConfig


class MySourceCollector(NewsCollector):  # or FinancialCollector, SocialCollector, etc.
    """Collector for MySource API."""

    # Declare required API keys
    REQUIRED_API_KEYS = ["MY_SOURCE_API_KEY"]

    # Optional: Use REQUIRES_ANY_KEY = True if any one of multiple keys works
    # REQUIRED_API_KEYS = ["KEY_A", "KEY_B"]
    # REQUIRES_ANY_KEY = True

    @property
    def name(self) -> str:
        return "MySource"

    def collect(
        self,
        profile: ProfileConfig,
        from_date: str,
        to_date: str,
        depth: str = "default",
    ) -> CollectorResult:
        """Collect data from MySource."""
        api_key = self.config.get("MY_SOURCE_API_KEY")
        if not api_key:
            return CollectorResult(
                items=[], sources=[], error="MySource API key not configured"
            )

        depth_config = self.get_depth_config(depth)
        max_items = depth_config.get("max_items", 25)

        # Fetch data from API
        items = []
        sources = []

        try:
            # Your API fetching logic here
            response = self._fetch_data(api_key, profile, from_date, to_date)

            for item_data in response.get("results", [])[:max_items]:
                items.append(schema.NewsItem(
                    id=item_data["id"],
                    title=item_data["title"],
                    url=item_data["url"],
                    source_name="MySource",
                    snippet=item_data.get("description", ""),
                    published_date=item_data.get("date"),
                ))

            sources.append(schema.Source(
                name="MySource",
                url="https://mysource.com",
            ))

        except Exception as e:
            return CollectorResult(items=[], sources=[], error=str(e))

        return CollectorResult(items=items, sources=sources)

    def _fetch_data(self, api_key: str, profile: ProfileConfig, from_date: str, to_date: str) -> dict:
        """Fetch data from the MySource API."""
        # Implementation here
        pass
```

**Step 2: Register in env.py (for `moltpulse config` display)**

```python
# src/moltpulse/core/lib/env.py

API_KEY_REGISTRY = {
    # ... existing keys ...
    "MY_SOURCE_API_KEY": {
        "description": "MySource data",
        "provider": "MySource",
        "signup_url": "https://mysource.com/api",
        "enables": ["my_source"],
        "required": False,
    },
}

COLLECTOR_INFO = {
    # ... existing collectors ...
    "my_source": {
        "name": "MySource",
        "description": "Data from MySource API",
        "requires": ["MY_SOURCE_API_KEY"],
    },
}
```

**Step 3: Add to domain configuration**

```yaml
# domains/advertising/domain.yaml

collectors:
  - {type: my_source, module: collectors.my_source}  # if shared
  # OR
  - {type: my_source, module: domains.advertising.collectors.my_source}  # if domain-specific
```

**Step 4: Write tests**

```python
# tests/test_my_source_collector.py

import pytest
from moltpulse.collectors.my_source import MySourceCollector

class TestMySourceCollector:
    def test_is_available_with_key(self):
        config = {"MY_SOURCE_API_KEY": "test-key"}
        collector = MySourceCollector(config)
        assert collector.is_available() is True

    def test_not_available_without_key(self):
        collector = MySourceCollector({})
        assert collector.is_available() is False
```

### 2. Adding a New Domain

Domains represent industries (advertising, healthcare, fintech). To add a new domain:

**Step 1: Create the directory structure**

```bash
mkdir -p src/moltpulse/domains/healthcare/{collectors,reports,profiles}
```

**Step 2: Create domain.yaml**

```yaml
# src/moltpulse/domains/healthcare/domain.yaml

domain: healthcare
display_name: "Healthcare Industry Intelligence"

entity_types:
  pharma_companies:
    - {symbol: JNJ, name: "Johnson & Johnson"}
    - {symbol: PFE, name: "Pfizer"}
    - {symbol: MRK, name: "Merck"}
    # ... more companies

  hospital_systems:
    - {name: "HCA Healthcare", type: hospital}
    - {name: "CommonSpirit", type: hospital}
    # ... more systems

collectors:
  - {type: financial, module: collectors.financial}
  - {type: news, module: collectors.news}
  - {type: rss, module: collectors.rss}
  # Add domain-specific collectors as needed

publications:
  - name: "STAT News"
    rss: "https://www.statnews.com/feed/"
    priority: 1
  - name: "FiercePharma"
    rss: "https://www.fiercepharma.com/rss/xml"
    priority: 1
  # ... more publications

reports:
  - {type: daily_brief, module: domains.healthcare.reports.daily_brief}
  - {type: weekly_digest, module: domains.healthcare.reports.weekly_digest}

thought_leaders:
  - {name: "Eric Topol", x_handle: "EricTopol"}
  - {name: "Vinay Prasad", x_handle: "VPrasadMDMPH"}
```

**Step 3: Create default profile**

```yaml
# src/moltpulse/domains/healthcare/profiles/default.yaml

name: "Default Healthcare Profile"

focus:
  entity_types:
    - pharma_companies
    - hospital_systems

delivery:
  channel: console

reports:
  daily_brief:
    enabled: true
  weekly_digest:
    enabled: true
```

**Step 4: Implement reports**

```python
# src/moltpulse/domains/healthcare/reports/daily_brief.py

from moltpulse.core.lib import schema

def generate(orchestrator_result, profile) -> schema.Report:
    """Generate healthcare daily brief."""
    report = schema.Report(
        title="Healthcare Daily Brief",
        report_type="daily_brief",
    )

    # Add sections based on collected data
    # ...

    return report
```

### 3. Adding a New Report Type

Reports transform collected data into formatted output. To add a new report type:

**Step 1: Create the report module**

```python
# src/moltpulse/domains/advertising/reports/competitive_analysis.py

from datetime import datetime
from moltpulse.core.lib import schema

def generate(orchestrator_result, profile) -> schema.Report:
    """Generate competitive analysis report."""
    report = schema.Report(
        title="Competitive Analysis Report",
        report_type="competitive_analysis",
        generated_at=datetime.now().isoformat(),
    )

    # Financial comparison section
    financial_items = [
        item for item in orchestrator_result.all_items
        if isinstance(item, schema.FinancialItem)
    ]

    if financial_items:
        report.add_section(schema.Section(
            title="Stock Performance Comparison",
            items=[item.to_dict() for item in financial_items],
        ))

    # Add more sections...

    return report
```

**Step 2: Register in domain.yaml**

```yaml
reports:
  - {type: competitive_analysis, module: domains.advertising.reports.competitive_analysis}
```

**Step 3: Add CLI support**

```python
# In cli.py add_run_parser function

competitive_parser = report_subparsers.add_parser(
    "competitive",
    help="Generate competitive analysis"
)
competitive_parser.add_argument(
    "--competitors",
    nargs="+",
    help="Specific competitors to analyze",
)
```

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints for function signatures
- Keep functions focused and under 50 lines when practical
- Write docstrings for public functions and classes

### Collector Guidelines

- Always implement `is_available()` check via `REQUIRED_API_KEYS`
- Return `CollectorResult` with proper `error` message on failure
- Respect `depth_config` for rate limiting (`max_items`, `timeout`)
- Use the `http` module for requests (handles caching and tracing)
- Create unique IDs for items (use hashlib for consistency)

### Testing Guidelines

- Write tests for new collectors, focusing on:
  - API key availability checks
  - Error handling
  - Item parsing logic
- Use mocks for external API calls
- Tests should not require real API keys to run

```python
# Example test with mocking
from unittest.mock import patch, MagicMock

class TestMyCollector:
    @patch('moltpulse.collectors.my_source.http.get')
    def test_collects_items(self, mock_get):
        mock_get.return_value = {"results": [{"id": "1", "title": "Test"}]}

        collector = MySourceCollector({"MY_SOURCE_API_KEY": "test"})
        result = collector.collect(mock_profile, "2025-01-01", "2025-01-31")

        assert result.success
        assert len(result.items) == 1
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_collector_base.py

# Run with coverage
uv run pytest tests/ --cov=moltpulse
```

## Submitting Changes

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make your changes** following the guidelines above
4. **Write/update tests** for your changes
5. **Run the test suite** to ensure everything passes
6. **Commit** with clear messages describing what and why
7. **Push** to your fork
8. **Open a Pull Request** with:
   - Description of what the change does
   - Why it's needed
   - Any breaking changes or migration notes
   - Test plan (how to verify the changes work)

## Questions?

- Open an issue for bugs or feature requests
- Check existing documentation in `docs/`
- Review existing collectors as examples
