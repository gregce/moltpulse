# Architecture

MoltPulse follows a modular, domain-driven architecture that separates concerns and enables extensibility.

## System Overview

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

## Data Flow

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│  COLLECT   │────▶│  PROCESS   │────▶│  GENERATE  │────▶│  DELIVER   │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
      │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼
 ┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐
 │Financial│       │ Filter  │       │  Daily  │       │ Console │
 │  News   │       │ Score   │       │ Weekly  │       │  Email  │
 │  RSS    │       │ Sort    │       │Fundraise│       │  File   │
 │ Social  │       │ Dedupe  │       │         │       │         │
 │ Awards  │       │         │       │         │       │         │
 │   PE    │       │         │       │         │       │         │
 └─────────┘       └─────────┘       └─────────┘       └─────────┘
```

### 1. Collect Phase
Collectors run in parallel using `ThreadPoolExecutor`. Each collector:
- Checks if required API keys are available
- Fetches data from external APIs or RSS feeds
- Returns normalized items in a common schema

### 2. Process Phase
Processing applies to all collected items:
- **Filter**: Remove items outside date range
- **Score**: Calculate relevance using weighted formula (45% relevance, 25% recency, 30% engagement)
- **Sort**: Order by score descending
- **Dedupe**: Remove duplicate items by URL/content hash

### 3. Generate Phase
Report generators create structured output:
- Domain-specific formatting
- Section organization
- Source citation collection

### 4. Deliver Phase
Delivery sends the report via configured channel:
- **Console**: Print to stdout
- **File**: Save to disk (JSON, HTML, Markdown)
- **Email**: Send via SMTP

## Directory Structure

```
src/moltpulse/
├── cli.py                    # Main CLI entry point
├── core/
│   ├── orchestrator.py       # Parallel execution coordinator
│   ├── collector_base.py     # Abstract collector interface
│   ├── report_base.py        # Abstract report generator
│   ├── delivery.py           # Delivery channel implementations
│   ├── domain_loader.py      # Domain configuration loading
│   ├── profile_loader.py     # Profile configuration loading
│   ├── ui.py                 # Progress spinners and display
│   ├── trace.py              # Run execution tracing
│   └── lib/
│       ├── schema.py         # Data models
│       ├── score.py          # Scoring algorithms
│       ├── http.py           # HTTP client with retry
│       └── normalize.py      # Date/data normalization
├── collectors/               # Generic collectors
│   ├── financial.py          # Stock/financial data
│   ├── news.py               # News API collectors
│   ├── rss.py                # RSS feed collector
│   └── social_x.py           # X/Twitter collector
└── domains/
    └── advertising/          # Domain-specific implementation
        ├── domain.yaml       # Domain configuration
        ├── collectors/       # Domain-specific collectors
        │   ├── awards.py
        │   └── pe_activity.py
        ├── reports/          # Domain-specific reports
        │   ├── daily_brief.py
        │   └── weekly_digest.py
        └── profiles/         # User profiles
            ├── default.yaml
            └── ricki.yaml
```

## Domain vs Profile

```
DOMAIN (advertising)              PROFILE (ricki)
═══════════════════              ═══════════════
What CAN be monitored    +       What USER cares about
                         │
┌─────────────────┐      │       ┌─────────────────┐
│ 10 Holding Cos  │──────┼──────▶│ Focus: WPP, OMC │
│ 8 Agency Types  │      │       │ Type: creative  │
│ 12 Publications │      │       │ Pubs: Ad Age    │
│ 6 Collectors    │      │       │ Leaders: 5      │
│ 3 Report Types  │      │       │ Keywords: boost │
└─────────────────┘      │       └─────────────────┘
                         │
        AVAILABLE        │         PERSONALIZED
```

## Collector Architecture

Collectors self-declare their API key requirements:

```python
class AlphaVantageCollector(FinancialCollector):
    REQUIRED_API_KEYS = ["ALPHA_VANTAGE_API_KEY"]

class RSSCollector(Collector):
    REQUIRED_API_KEYS = []  # No API key needed

class PEActivityCollector(Collector):
    REQUIRED_API_KEYS = ["INTELLIZENCE_API_KEY", "NEWSDATA_API_KEY"]
    REQUIRES_ANY_KEY = True  # Only one needed
```

The orchestrator runs a preflight check to identify available collectors before execution.

## Scoring Algorithm

Items are scored using a weighted formula:

```
Score = (Relevance × 0.45) + (Recency × 0.25) + (Engagement × 0.30)
```

- **Relevance**: How well the item matches profile keywords and focus entities
- **Recency**: How recent the item is (exponential decay over 30 days)
- **Engagement**: Platform-specific metrics (likes, comments, shares)

## Extension Points

1. **New Collectors**: Implement `Collector` base class
2. **New Domains**: Create domain directory with `domain.yaml`
3. **New Reports**: Implement `ReportGenerator` base class
4. **New Delivery Channels**: Implement `Deliverer` base class
