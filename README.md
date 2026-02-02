# MoltPulse

![MoltPulse](header.jpeg)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> Domain-agnostic industry intelligence framework

MoltPulse monitors industries, tracks market trends, and generates intelligence reports. Configure **domains** (advertising, healthcare, fintech), define **user profiles**, and schedule automated reports.

```
┌─────────────────────────────────────────────────────────────────┐
│                         MOLTPULSE                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │ DOMAIN  │───▶│ PROFILE  │───▶│ORCHESTRATOR│───▶│ DELIVERY │  │
│  │ (what)  │    │  (who)   │    │  (how)    │    │ (where)  │  │
│  └─────────┘    └──────────┘    └───────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Install

```bash
# From source
uv tool install /path/to/moltpulse

# Or with pip
pip install moltpulse
```

### Configure

```bash
# Interactive setup
moltpulse config set

# Or set keys directly
moltpulse config set ALPHA_VANTAGE_API_KEY your_key
moltpulse config set NEWSDATA_API_KEY your_key

# Check status
moltpulse config
```

### Run

```bash
# Generate a daily brief
moltpulse run --domain=advertising --profile=ricki daily

# Preview without running collectors
moltpulse run --domain=advertising --profile=ricki --dry-run daily

# Deep collection for comprehensive reports
moltpulse run --domain=advertising --profile=ricki --deep weekly
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and first run |
| [Architecture](docs/architecture.md) | System design, data flow, and scoring |
| [Domains](docs/domains.md) | Creating and configuring domains |
| [Profiles](docs/profiles.md) | User profile customization and delivery |
| [Monitoring](docs/monitoring.md) | Run execution tracing and debugging |

## Commands

| Command | Description |
|---------|-------------|
| `run` | Generate a report |
| `config` | Manage API keys and settings |
| `domain` | List, show, create domains |
| `profile` | List, show, create profiles |
| `cron` | Manage OpenClaw cron integration |

## Report Types

| Type | Command | Description |
|------|---------|-------------|
| Daily Brief | `moltpulse run ... daily` | Morning intelligence with stock performance, top news, thought leader highlights |
| Weekly Digest | `moltpulse run ... weekly` | Comprehensive weekly analysis with trends and M&A activity |
| Fundraising | `moltpulse run ... fundraising` | Nonprofit-focused outlook with timing recommendations |

## API Keys

| Key | Provider | Enables |
|-----|----------|---------|
| `ALPHA_VANTAGE_API_KEY` | [Alpha Vantage](https://www.alphavantage.co/) | Financial data |
| `NEWSDATA_API_KEY` | [NewsData.io](https://newsdata.io/) | News aggregation |
| `XAI_API_KEY` | [xAI](https://x.ai/) | X/Twitter search |
| `NEWSAPI_API_KEY` | [NewsAPI](https://newsapi.org/) | Fallback news |
| `INTELLIZENCE_API_KEY` | Intellizence | M&A data |

Keys are stored in `~/.config/moltpulse/.env` or can be set via environment variables.

## OpenClaw Integration

MoltPulse integrates with [OpenClaw](https://github.com/anthropics/openclaw) for scheduled execution:

```bash
# Install cron jobs
moltpulse cron install --all

# For orchestrated delivery, use --no-deliver
moltpulse run --domain=advertising --profile=ricki --no-deliver daily
```

See [cron templates](src/moltpulse/cron/) for available schedules.

## Development

```bash
# Run tests
uv run python -m pytest tests/

# Check collector status
moltpulse config
```

See [Architecture](docs/architecture.md) for adding domains and collectors.

## License

MIT
