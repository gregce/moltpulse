# MoltPulse

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> Domain-agnostic industry intelligence framework

MoltPulse monitors industries, tracks market trends, and generates intelligence reports. Configure domains (advertising, healthcare, fintech), define user profiles, and schedule automated reports. Works standalone or integrates with [OpenClaw](https://github.com/anthropics/claude-code) for orchestrated execution.

## Features

- **Multi-Domain** - Monitor any industry with YAML configuration
- **User Profiles** - Different users get personalized focus areas within the same domain
- **Report Types** - Daily briefs, weekly digests, and specialized reports (fundraising outlook)
- **Parallel Collection** - Fast data gathering from multiple sources simultaneously
- **Flexible Delivery** - Console, file, or email output
- **OpenClaw Integration** - Scheduled execution via cron jobs with `--no-deliver` for orchestrated delivery
- **Standalone Operation** - Works without OpenClaw installed

## Quick Start

### Install

```bash
# From source
uv tool install /path/to/moltpulse

# Or with pip (when published)
pip install moltpulse
```

### Configure API Keys

```bash
moltpulse config set ALPHA_VANTAGE_API_KEY your_key
moltpulse config set NEWSDATA_API_KEY your_key

# Verify configuration
moltpulse config list
```

### Generate a Report

```bash
# Generate daily brief for advertising domain
moltpulse run --domain=advertising --profile=ricki daily

# Preview what would be collected (dry run)
moltpulse run --domain=advertising --profile=ricki --dry-run daily

# Deep collection for comprehensive reports
moltpulse run --domain=advertising --profile=ricki --deep weekly
```

## Commands

<!-- COMMANDS:START -->
| Command | Description |
|---------|-------------|
| `run` | Generate a report |
| `config` | Manage MoltPulse configuration |
| `cron` | Manage OpenClaw cron integration |
| `domain` | Manage domain instances |
| `profile` | Manage interest profiles |
<!-- COMMANDS:END -->

### Report Generation

```bash
moltpulse run --domain=DOMAIN --profile=PROFILE REPORT_TYPE [options]
```

**Report Types:**
- `daily` - Compact morning brief with stock performance, top news, thought leader highlights
- `weekly` - Comprehensive weekly analysis with trends and M&A activity
- `fundraising` - Nonprofit-focused outlook with timing recommendations

**Options:**
- `--quick` - Fast, shallow collection
- `--deep` - Thorough, comprehensive collection
- `--deliver` - Send via profile's delivery settings
- `--no-deliver` - Output to stdout only (for OpenClaw orchestration)
- `--output FORMAT` - Output format: `compact`, `json`, `markdown`, `full`
- `--dry-run` - Show configuration without running collectors

### Configuration Management

```bash
# List all configuration
moltpulse config list

# Set an API key
moltpulse config set ALPHA_VANTAGE_API_KEY your_key

# Get a specific value
moltpulse config get ALPHA_VANTAGE_API_KEY

# Test API key validity
moltpulse config test ALPHA_VANTAGE_API_KEY

# Open config directory
moltpulse config path
```

### Domain Management

```bash
# List available domains
moltpulse domain list

# Show domain details
moltpulse domain show advertising

# Create a new domain
moltpulse domain create healthcare --display-name "Healthcare Intelligence"

# Add entities to a domain
moltpulse domain update healthcare --add-entity "hospital_systems:HCA:HCA Healthcare"
```

### Profile Management

```bash
# List profiles in a domain
moltpulse profile list advertising

# Show profile details
moltpulse profile show advertising ricki

# Create a new profile
moltpulse profile create advertising sarah \
  --thought-leader "Seth Godin:ThisIsSethsBlog:1" \
  --publications "Ad Age,AdWeek" \
  --delivery-channel email \
  --delivery-email "sarah@example.com"
```

## OpenClaw Integration

MoltPulse integrates with [OpenClaw](https://github.com/anthropics/claude-code) for scheduled execution and orchestrated delivery.

### Install Cron Jobs

```bash
# List available cron templates
moltpulse cron list

# Show template details
moltpulse cron show daily-brief

# Install all cron jobs to OpenClaw
moltpulse cron install --all

# Install a specific job
moltpulse cron install daily-brief

# Preview without installing
moltpulse cron install --all --dry-run
```

### Bundled Cron Templates

| Template | Schedule | Description |
|----------|----------|-------------|
| `daily-brief` | Weekdays 7am PT | Morning industry intelligence brief |
| `weekly-digest` | Mondays 8am PT | Comprehensive weekly analysis |
| `fundraising-outlook` | 1st of month 9am PT | Monthly fundraising outlook |

### Orchestrated Execution

When OpenClaw runs MoltPulse, use `--no-deliver` so OpenClaw handles delivery:

```bash
# OpenClaw runs this command and delivers the output
moltpulse run --domain=advertising --profile=ricki --output=markdown --no-deliver daily
```

MoltPulse outputs to stdout; OpenClaw delivers to Slack, email, or other channels.

## Configuration

### Domain Configuration (domain.yaml)

```yaml
domain: advertising
display_name: "Advertising Industry Intelligence"

entity_types:
  holding_companies:
    - {symbol: WPP, name: "WPP plc"}
    - {symbol: OMC, name: "Omnicom Group"}
    - {symbol: IPG, name: "Interpublic Group"}

collectors:
  - {type: financial, module: collectors.financial}
  - {type: news, module: collectors.news}
  - {type: rss, module: collectors.rss}
  - {type: social_x, module: collectors.social_x}

publications:
  - {name: "Ad Age", rss: "https://adage.com/rss"}
  - {name: "AdWeek", rss: "https://adweek.com/feed"}

reports:
  - {type: daily_brief, module: domains.advertising.reports.daily_brief}
  - {type: weekly_digest, module: domains.advertising.reports.weekly_digest}
```

### Profile Configuration (profiles/user.yaml)

```yaml
profile_name: "ricki"
extends: default

focus:
  holding_companies:
    priority_1: [WPP, OMC]
    priority_2: [IPG, PUBGY]

thought_leaders:
  - {name: "Scott Galloway", x_handle: "profgalloway", priority: 1}
  - {name: "Bob Hoffman", x_handle: "adcontrarian", priority: 2}

publications: [Ad Age, AdWeek]

reports:
  daily_brief: true
  weekly_digest: true
  fundraising_outlook: true

delivery:
  channel: email
  email:
    to: "user@example.com"
    subject_prefix: "[MoltPulse]"
```

## API Keys

Configure API keys for data collection:

| Key | Provider | Purpose | Required |
|-----|----------|---------|----------|
| `ALPHA_VANTAGE_API_KEY` | [Alpha Vantage](https://www.alphavantage.co/) | Stock data | Yes |
| `NEWSDATA_API_KEY` | [NewsData.io](https://newsdata.io/) | News aggregation | Yes |
| `XAI_API_KEY` | xAI | X/Twitter search | Optional |
| `NEWSAPI_API_KEY` | [NewsAPI](https://newsapi.org/) | Fallback news source | Optional |
| `INTELLIZENCE_API_KEY` | Intellizence | M&A data | Optional |

Keys are stored in `~/.config/moltpulse/.env` or can be set via environment variables.

## Architecture

### Two-Layer Design

1. **Domain Layer** - Defines what CAN be monitored for an industry
   - Entity types (companies, organizations)
   - Available collectors (data sources)
   - Publications and RSS feeds
   - Report types

2. **Profile Layer** - Customizes WHAT a specific user cares about
   - Prioritized entities
   - Thought leaders to track
   - Publication preferences
   - Delivery configuration

### Directory Structure

```
moltpulse/
├── src/moltpulse/
│   ├── cli.py                # CLI entry point
│   ├── core/                 # Framework engine
│   │   ├── orchestrator.py   # Parallel execution
│   │   ├── domain_loader.py  # Domain configuration
│   │   ├── profile_loader.py # Profile configuration
│   │   ├── collector_base.py # Abstract collectors
│   │   ├── report_base.py    # Abstract reports
│   │   ├── delivery.py       # Delivery mechanisms
│   │   └── cli/              # CLI subcommands
│   ├── collectors/           # Reusable collectors
│   │   ├── financial.py      # Stock data
│   │   ├── news.py           # News aggregation
│   │   ├── rss.py            # RSS feeds
│   │   └── social_x.py       # X/Twitter
│   ├── domains/              # Domain instances
│   │   └── advertising/      # Example domain
│   └── cron/                 # OpenClaw cron templates
├── SKILL.md                  # OpenClaw skill definition
└── pyproject.toml
```

## Development

### Adding a New Domain

```bash
# Create domain skeleton
moltpulse domain create fintech --display-name "Fintech Intelligence"

# Edit the domain configuration
# domains/fintech/domain.yaml
```

### Adding Domain-Specific Collectors

```python
# domains/fintech/collectors/regulatory.py
from moltpulse.core.collector_base import Collector

class RegulatoryCollector(Collector):
    def collect(self, profile, from_date, to_date, depth):
        # Collect regulatory filings, SEC data, etc.
        pass
```

### Running Tests

```bash
uv run python -m pytest tests/
```

## License

MIT
