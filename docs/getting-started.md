# Getting Started

This guide will help you set up MoltPulse and run your first report.

## Installation

```bash
# Clone and install
git clone https://github.com/gregce/moltpulse.git
cd moltpulse
uv pip install -e .

# Verify installation
moltpulse --help
```

## Quick Start

### 1. Check Available Domains

```bash
moltpulse domain list
```

Output:
```
Available domains:
  advertising    Advertising Industry Intelligence
```

### 2. Configure API Keys

MoltPulse uses external APIs for data collection. Configure the ones you have:

```bash
# Required for financial data
moltpulse config set ALPHA_VANTAGE_API_KEY

# Required for news
moltpulse config set NEWSDATA_API_KEY

# Optional: X/Twitter data
moltpulse config set XAI_API_KEY
```

Check status:
```bash
moltpulse config
```

### 3. View Available Profiles

```bash
moltpulse profile list advertising
```

Output:
```
Profiles in 'advertising':
  default: 0 thought leaders, 0 publications, delivery: file
  ricki: 5 thought leaders, 8 publications, delivery: email
```

### 4. Run a Report

```bash
# Test run (shows config without executing)
moltpulse run --domain=advertising --profile=ricki --dry-run daily

# Actual run
moltpulse run --domain=advertising --profile=ricki daily
```

### 5. Create Your Own Profile

```bash
moltpulse profile create advertising myname \
  --extends default \
  --thought-leader "Scott Galloway:profgalloway:1" \
  --publications "Ad Age,AdWeek" \
  --keywords-boost "AI,automation" \
  --delivery-channel console
```

## Output Formats

```bash
# Compact summary (default)
moltpulse run --domain=advertising --profile=ricki daily

# JSON output
moltpulse run --domain=advertising --profile=ricki --output=json daily

# Markdown output
moltpulse run --domain=advertising --profile=ricki --output=markdown daily

# Save to file
moltpulse run --domain=advertising --profile=ricki --output=json \
  --output-path=report.json daily
```

## Depth Options

```bash
# Quick scan (faster, fewer items)
moltpulse run --domain=advertising --profile=ricki --quick daily

# Deep scan (thorough, more items)
moltpulse run --domain=advertising --profile=ricki --deep daily
```

## Delivery Options

```bash
# Output to console only (default)
moltpulse run --domain=advertising --profile=ricki daily

# Use profile's delivery settings (email, file, etc.)
moltpulse run --domain=advertising --profile=ricki --deliver daily

# Suppress delivery (for orchestration)
moltpulse run --domain=advertising --profile=ricki --no-deliver daily
```

## Report Types

The advertising domain supports:

| Report | Description |
|--------|-------------|
| `daily` | Morning briefing with top news and market moves |
| `weekly` | Comprehensive weekly analysis |
| `fundraising` | Nonprofit-focused outlook |

```bash
moltpulse run --domain=advertising --profile=ricki daily
moltpulse run --domain=advertising --profile=ricki weekly
moltpulse run --domain=advertising --profile=ricki fundraising
```

## Next Steps

- [Create a custom profile](profiles.md)
- [Add a new domain](domains.md)
- [Understand the architecture](architecture.md)
- [Monitor run execution](monitoring.md)
