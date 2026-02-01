---
name: moltos
description: Generate industry intelligence reports from configured domains and profiles
argument-hint: "[run|domain|profile] [options]"
context: fork
allowed-tools: Bash, Read, Write
---

# Moltos - Industry Intelligence Framework

Generate daily, weekly, and specialized reports for monitored industries.

## Quick Start

```bash
# Generate daily brief for advertising industry with Ricki's profile
uv run python moltos.py run --domain=advertising --profile=ricki daily

# Generate weekly digest
uv run python moltos.py run --domain=advertising --profile=ricki weekly

# Generate fundraising outlook
uv run python moltos.py run --domain=advertising --profile=ricki fundraising
```

## Commands

### Report Generation

```bash
# Daily brief - compact morning summary
moltos run --domain=DOMAIN --profile=PROFILE daily [--quick|--deep] [--deliver]

# Weekly digest - comprehensive weekly analysis
moltos run --domain=DOMAIN --profile=PROFILE weekly [--quick|--deep] [--deliver]

# Fundraising outlook - nonprofit targeting report
moltos run --domain=DOMAIN --profile=PROFILE fundraising [--deep] [--deliver]
```

Options:
- `--quick` - Fast, shallow collection
- `--deep` - Thorough, comprehensive collection
- `--deliver` - Send via profile's delivery settings
- `--output` - Format: compact, json, markdown, full
- `--dry-run` - Show configuration without running

### Domain Management

```bash
# List available domains
moltos domain list

# Show domain details
moltos domain show advertising

# Create new domain
moltos domain create healthcare --display-name "Healthcare Intelligence"

# Add entities to domain
moltos domain update healthcare --add-entity "hospital_systems:HCA:HCA Healthcare"
```

### Profile Management

```bash
# List profiles in a domain
moltos profile list advertising

# Show profile details
moltos profile show advertising ricki

# Create new profile
moltos profile create advertising sarah \
  --thought-leader "Seth Godin:ThisIsSethsBlog:1" \
  --publications "Ad Age,AdWeek" \
  --delivery-channel email \
  --delivery-email "sarah@example.com"

# Update profile
moltos profile update advertising sarah \
  --add-thought-leader "Gary Vee:garyvee:2" \
  --add-keyword-boost "AI"
```

## Available Domains

Run `moltos domain list` to see configured domains.

Current domains:
- **advertising** - Advertising industry monitoring (holding companies, agencies, M&A)

## Report Types

### Daily Brief
Compact morning summary including:
- Stock performance of tracked entities
- Top 5 news items
- Thought leader highlights
- PE/M&A alerts

### Weekly Digest
Comprehensive weekly analysis:
- Market overview with trends
- News roundup (15 items)
- Agency momentum (awards)
- Thought leadership insights
- M&A activity summary
- Trend spotting

### Fundraising Outlook
Nonprofit-focused analysis:
- Industry health assessment
- M&A activity indicators
- Timing recommendations
- Key trends to leverage in pitches
- 6-month, 1-year, and 3-year outlooks

## Delivery Channels

Reports can be delivered via:
- `console` - Print to terminal (default)
- `file` - Save to local file
- `email` - Send via SMTP

Configure delivery in profile YAML or via CLI:
```bash
moltos profile update advertising ricki \
  --set-delivery-channel email \
  --set-delivery-email "user@example.com"
```

## API Keys

Configure in `~/.config/moltos/.env`:
```
ALPHA_VANTAGE_API_KEY=xxx    # Stock data
NEWSDATA_API_KEY=xxx          # News aggregation
XAI_API_KEY=xxx               # X/Twitter search
```

## Examples

### Morning Brief Workflow
```bash
# Check what will be collected
moltos run --domain=advertising --profile=ricki --dry-run daily

# Generate and deliver the report
moltos run --domain=advertising --profile=ricki --deliver daily
```

### Create Custom Profile
```bash
# Create profile for a different user
moltos profile create advertising bob \
  --focus-entities "holding_companies:WPP,OMC" \
  --thought-leader "Scott Galloway:profgalloway:1" \
  --publications "Ad Age,Forbes" \
  --keywords-boost "programmatic,CTV" \
  --delivery-channel email \
  --delivery-email "bob@example.com"

# Generate report with new profile
moltos run --domain=advertising --profile=bob daily
```

### Setup New Industry Domain
```bash
# Create domain skeleton
moltos domain create fintech --display-name "Fintech Intelligence"

# Add entities
moltos domain update fintech \
  --add-entity "banks:JPM:JPMorgan Chase" \
  --add-entity "banks:BAC:Bank of America" \
  --add-collector "financial:collectors.financial" \
  --add-collector "news:collectors.news"

# Create profile
moltos profile create fintech analyst1 \
  --thought-leader "Cathie Wood:CathieDWood:1" \
  --publications "Bloomberg,WSJ"
```
