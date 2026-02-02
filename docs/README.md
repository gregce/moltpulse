# MoltPulse Documentation

Welcome to the MoltPulse documentation hub. MoltPulse is an industry intelligence monitoring system that collects, processes, and delivers insights from multiple data sources.

## Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Installation and first run |
| [Architecture](architecture.md) | System design and data flow |
| [Domains](domains.md) | Creating and configuring domains |
| [Profiles](profiles.md) | User profile customization |
| [Monitoring](monitoring.md) | Run execution and tracing |

## How MoltPulse Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         MOLTPULSE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │ DOMAIN  │───▶│ PROFILE  │───▶│ORCHESTRATOR│───▶│ DELIVERY │  │
│  │ (what)  │    │  (who)   │    │  (how)    │    │ (where)  │  │
│  └─────────┘    └──────────┘    └───────────┘    └──────────┘  │
│       │              │               │                │        │
│       ▼              ▼               ▼                ▼        │
│  ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │Collectors│    │ Focus    │    │ Parallel  │    │ Console  │  │
│  │ Reports │    │ Leaders  │    │ Execution │    │ Email    │  │
│  │ Entities│    │ Keywords │    │ Scoring   │    │ File     │  │
│  └─────────┘    └──────────┘    └───────────┘    └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### Domain
A **domain** defines what CAN be monitored for an industry:
- Entity types (companies, people, publications)
- Available collectors (financial, news, social, etc.)
- Report templates (daily brief, weekly digest)

### Profile
A **profile** defines what a SPECIFIC USER cares about:
- Which entities to focus on
- Thought leaders to track
- Keywords to boost/filter
- Delivery preferences

### Orchestrator
The **orchestrator** runs collectors in parallel, processes results (filter, score, dedupe), and generates reports.

### Delivery
**Delivery** sends the generated report to the user via console, file, or email.

## Common Commands

```bash
# List available domains
moltpulse domain list

# Show domain details
moltpulse domain show advertising

# List profiles in a domain
moltpulse profile list advertising

# Run a report
moltpulse run --domain=advertising --profile=ricki daily

# Dry run (show config without executing)
moltpulse run --domain=advertising --profile=ricki --dry-run daily
```

## API Keys

MoltPulse uses various APIs for data collection. Configure them via:

```bash
moltpulse config set ALPHA_VANTAGE_API_KEY
moltpulse config set NEWSDATA_API_KEY
moltpulse config set XAI_API_KEY
```

Check status with:
```bash
moltpulse config
```
