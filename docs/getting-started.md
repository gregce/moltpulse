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
moltpulse --version  # Shows git-based version (e.g., 0.1.1.dev0+10.g2214efdf3)
```

> **Note**: MoltPulse uses git-based versioning. When installed from source, the version includes the commit count and hash (e.g., `0.1.1.dev0+10.g2214efdf3`). Tagged releases show clean versions like `0.1.1`.

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
# Financial data (Alpha Vantage - free tier available)
moltpulse config set ALPHA_VANTAGE_API_KEY

# News data (NewsData.io - primary news collector)
moltpulse config set NEWSDATA_API_KEY

# Optional: X/Twitter data
moltpulse config set XAI_API_KEY

# Optional: LLM enhancement (if not using Claude Code CLI)
moltpulse config set ANTHROPIC_API_KEY
```

Check status:
```bash
moltpulse config
```

> **Rate Limits**: Alpha Vantage free tier allows 1 request/second and 25/day. MoltPulse automatically handles rate limiting with delays between requests. The `--quick` flag reduces symbols checked (3 max) to minimize API usage.

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
# Quick scan (faster, fewer items, lower API usage)
moltpulse run --domain=advertising --profile=ricki --quick daily

# Deep scan (thorough, more items)
moltpulse run --domain=advertising --profile=ricki --deep daily
```

Depth affects collector behavior:

| Depth | Financial Symbols | News Items | Timeout |
|-------|-------------------|------------|---------|
| quick | 3 max | 5 max | 30s |
| default | 5 max | 10 max | 60s |
| deep | 10 max | 20 max | 120s |

## LLM Enhancement

MoltPulse can enhance reports with AI-generated insights using Claude:

```bash
# Auto-detect LLM backend (OpenClaw → Claude CLI → Anthropic SDK)
moltpulse run --domain=advertising --profile=ricki daily

# Force specific LLM mode
moltpulse run --domain=advertising --profile=ricki --llm-mode=claude_cli daily

# Disable LLM enhancement
moltpulse run --domain=advertising --profile=ricki --no-llm daily
```

LLM modes (in detection priority order):
- `openclaw` - OpenClaw gateway (if running)
- `claude_cli` - Claude Code CLI (`claude --print`)
- `anthropic` - Direct Anthropic SDK (requires `ANTHROPIC_API_KEY`)
- `disabled` - No LLM enhancement

When enabled, reports include:
- Executive summary
- Per-section insights
- Strategic recommendations (customizable via profile)

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

## Combining Flags

All CLI flags can be combined in a single command:

```bash
# Full example: quick scan, JSON output, trace enabled, no LLM
moltpulse run --domain=advertising --profile=ricki \
  --quick --output=json --trace --no-llm daily

# Test configuration without running
moltpulse run --domain=advertising --profile=ricki \
  --quick --dry-run daily

# Deep scan with markdown output saved to file
moltpulse run --domain=advertising --profile=ricki \
  --deep --output=markdown --output-path=report.md daily
```

Flag reference:

| Flag | Description |
|------|-------------|
| `--domain=NAME` | Domain to use (required) |
| `--profile=NAME` | Profile to use (default: default) |
| `--quick` | Faster scan, fewer items |
| `--deep` | Thorough scan, more items |
| `--output=FORMAT` | Output format: compact, json, markdown |
| `--output-path=FILE` | Save output to file |
| `--trace` | Show execution trace |
| `--dry-run` | Show config without executing |
| `--deliver` | Use profile's delivery settings |
| `--no-deliver` | Suppress delivery |
| `--llm-mode=MODE` | Force LLM mode |
| `--no-llm` | Disable LLM enhancement |

## Debugging

Enable debug output to troubleshoot issues:

```bash
MOLTPULSE_DEBUG=true moltpulse run --domain=advertising daily
```

This shows:
- API request/response details
- Rate limiting events
- Collector selection decisions
- LLM backend detection

## Next Steps

- [Create a custom profile](profiles.md)
- [Add a new domain](domains.md)
- [Understand the architecture](architecture.md)
- [Monitor run execution](monitoring.md)
