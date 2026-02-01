# MoltPulse

Domain-agnostic industry intelligence framework for OpenClaw.

## Overview

MoltPulse is a flexible framework for monitoring industries, tracking market trends, and generating intelligence reports. It supports:

- **Multiple Domains**: Configure monitoring for any industry (advertising, healthcare, fintech, etc.)
- **Interest Profiles**: Different users can have different focus areas within the same domain
- **Multiple Report Types**: Daily briefs, weekly digests, specialized reports
- **Flexible Delivery**: Email, file, or console output
- **OpenClaw Integration**: Scheduled execution via cron jobs

## Installation

```bash
# Clone the repository
cd moltpulse

# Install dependencies with UV
uv sync

# Configure API keys
mkdir -p ~/.config/moltpulse
cat > ~/.config/moltpulse/.env << EOF
ALPHA_VANTAGE_API_KEY=your_key_here
NEWSDATA_API_KEY=your_key_here
XAI_API_KEY=your_key_here
EOF
```

## Quick Start

```bash
# Generate daily brief for advertising domain
uv run python moltpulse.py run --domain=advertising --profile=ricki daily

# See available domains
uv run python moltpulse.py domain list

# See available profiles
uv run python moltpulse.py profile list advertising

# Dry run to see what would be collected
uv run python moltpulse.py run --domain=advertising --profile=ricki --dry-run daily
```

## Architecture

### Two-Layer Design

1. **Domain Layer**: Defines what CAN be monitored for an industry
   - Entity types (companies, organizations)
   - Available collectors (data sources)
   - Publications and RSS feeds
   - Report types

2. **Profile Layer**: Customizes WHAT a specific user cares about
   - Prioritized entities
   - Thought leaders to track
   - Publication preferences
   - Delivery configuration

### Directory Structure

```
moltpulse/
├── moltpulse.py             # CLI entry point
├── SKILL.md                 # OpenClaw skill definition
├── core/                    # Framework engine
│   ├── orchestrator.py      # Parallel execution
│   ├── domain_loader.py     # Domain configuration
│   ├── profile_loader.py    # Profile configuration
│   ├── collector_base.py    # Abstract collectors
│   ├── report_base.py       # Abstract reports
│   ├── delivery.py          # Delivery mechanisms
│   ├── cli/                 # CLI commands
│   └── lib/                 # Utilities
├── collectors/              # Reusable collectors
│   ├── financial.py         # Stock data
│   ├── news.py              # News aggregation
│   ├── rss.py               # RSS feeds
│   └── social_x.py          # X/Twitter
├── domains/                 # Domain instances
│   └── advertising/         # Advertising domain
│       ├── domain.yaml      # Domain definition
│       ├── collectors/      # Domain-specific collectors
│       ├── reports/         # Domain-specific reports
│       └── profiles/        # User profiles
└── cron/                    # OpenClaw cron templates
```

## Commands

### Report Generation

```bash
moltpulse run --domain=DOMAIN --profile=PROFILE REPORT_TYPE [options]
```

Report types:
- `daily` - Compact morning brief
- `weekly` - Comprehensive weekly digest
- `fundraising` - Nonprofit-focused outlook

Options:
- `--quick` - Fast, shallow collection
- `--deep` - Thorough collection
- `--deliver` - Use profile's delivery settings
- `--output FORMAT` - compact, json, markdown, full
- `--dry-run` - Show config without running

### Domain Management

```bash
# List domains
moltpulse domain list

# Create domain
moltpulse domain create DOMAIN --display-name "Display Name"

# Show domain
moltpulse domain show DOMAIN [--yaml]

# Update domain
moltpulse domain update DOMAIN --add-entity TYPE:SYMBOL:NAME
```

### Profile Management

```bash
# List profiles
moltpulse profile list DOMAIN

# Create profile
moltpulse profile create DOMAIN NAME [options]

# Show profile
moltpulse profile show DOMAIN NAME [--yaml]

# Update profile
moltpulse profile update DOMAIN NAME [options]
```

## Configuration

### Domain Configuration (domain.yaml)

```yaml
domain: advertising
display_name: "Advertising Industry Intelligence"

entity_types:
  holding_companies:
    - {symbol: WPP, name: "WPP plc"}
    - {symbol: OMC, name: "Omnicom Group"}

collectors:
  - {type: financial, module: collectors.financial}
  - {type: news, module: collectors.news}

publications:
  - {name: "Ad Age", rss: "https://adage.com/rss"}

reports:
  - {type: daily_brief, module: domains.advertising.reports.daily_brief}
```

### Profile Configuration (profiles/user.yaml)

```yaml
profile_name: "user"
extends: default

focus:
  holding_companies:
    priority_1: [WPP, OMC]

thought_leaders:
  - {name: "Scott Galloway", x_handle: "profgalloway", priority: 1}

publications: [Ad Age, AdWeek]

reports:
  daily_brief: true
  weekly_digest: true

delivery:
  channel: email
  email:
    to: "user@example.com"
    subject_prefix: "[MoltPulse]"
```

## OpenClaw Integration

### Skill Usage

```bash
# In OpenClaw
/moltpulse run --domain=advertising --profile=ricki daily
```

### Cron Scheduling

Copy templates from `cron/` to `~/.openclaw/cron.json`:

```bash
# Add daily brief cron job
openclaw cron add --config cron/daily-brief.json
```

Or manually:

```bash
openclaw cron add \
  --name "MoltPulse Daily Brief" \
  --cron "0 7 * * 1-5" \
  --tz "America/Los_Angeles" \
  --session isolated \
  --message "Run /moltpulse run --domain=advertising --profile=ricki --deliver daily"
```

## API Keys

Required for full functionality:

| Key | Provider | Purpose |
|-----|----------|---------|
| `ALPHA_VANTAGE_API_KEY` | [Alpha Vantage](https://www.alphavantage.co/) | Stock data |
| `NEWSDATA_API_KEY` | [NewsData.io](https://newsdata.io/) | News aggregation |
| `XAI_API_KEY` | xAI | X/Twitter search |

Optional:
- `NEWSAPI_API_KEY` - Fallback news source
- `OPENAI_API_KEY` - Enhanced analysis
- `INTELLIZENCE_API_KEY` - M&A data

## Development

### Adding a New Domain

1. Create domain skeleton:
   ```bash
   moltpulse domain create myindustry --display-name "My Industry"
   ```

2. Edit `domains/myindustry/domain.yaml`

3. Add domain-specific collectors (if needed):
   ```python
   # domains/myindustry/collectors/custom.py
   from core.collector_base import Collector

   class CustomCollector(Collector):
       def collect(self, profile, from_date, to_date, depth):
           # Implementation
           pass
   ```

4. Add reports:
   ```python
   # domains/myindustry/reports/daily_brief.py
   from core.report_base import DailyBriefGenerator

   class DailyBriefReport(DailyBriefGenerator):
       def generate(self, data, from_date, to_date):
           # Implementation
           pass
   ```

5. Create profiles:
   ```bash
   moltpulse profile create myindustry user1 --thought-leader "Expert:handle:1"
   ```

### Running Tests

```bash
uv run pytest tests/
```

## License

MIT
