# Domains

A **domain** defines what CAN be monitored for an industry. It contains entity definitions, collectors, publications, and report templates.

## Domain Structure

```
domains/{domain_name}/
├── domain.yaml           # Main configuration
├── collectors/           # Domain-specific collectors
│   ├── __init__.py
│   └── custom_collector.py
├── reports/              # Domain-specific reports
│   ├── __init__.py
│   └── daily_brief.py
└── profiles/             # User profiles
    ├── default.yaml
    └── {username}.yaml
```

## Working with Domains

### List Domains

```bash
moltpulse domain list
```

### Show Domain Details

```bash
moltpulse domain show advertising
```

Output:
```
Domain: advertising
Display Name: Advertising Industry Intelligence

Entity Types:
  holding_companies: 10 entities
  agency_categories: 8 types
  independent_agencies: 5 entities

Collectors:
  - financial (collectors.financial)
  - news (collectors.news)
  - rss (collectors.rss)
  - social (collectors.social_x)
  - awards (domains.advertising.collectors.awards)
  - pe_activity (domains.advertising.collectors.pe_activity)

Reports:
  - daily_brief
  - weekly_digest
  - fundraising
```

### Validate Domain

```bash
moltpulse domain validate advertising
```

## Creating a New Domain

### Step 1: Create Domain Skeleton

```bash
moltpulse domain create healthcare --display-name "Healthcare Intelligence"
```

This creates:
```
domains/healthcare/
├── domain.yaml
├── collectors/
│   └── __init__.py
├── reports/
│   └── __init__.py
└── profiles/
    └── default.yaml
```

### Step 2: Edit domain.yaml

```yaml
domain: healthcare
display_name: "Healthcare Intelligence"

# Define entity types for this industry
entity_types:
  pharma_companies:
    - {name: "Pfizer", symbol: "PFE"}
    - {name: "Johnson & Johnson", symbol: "JNJ"}
    - {name: "Merck", symbol: "MRK"}

  hospital_systems:
    - {name: "HCA Healthcare", symbol: "HCA"}
    - {name: "Universal Health Services", symbol: "UHS"}

  focus_areas:
    - oncology
    - immunology
    - gene_therapy
    - digital_health

# Define collectors (use generic or create domain-specific)
collectors:
  - {type: financial, module: collectors.financial}
  - {type: news, module: collectors.news}
  - {type: rss, module: collectors.rss}
  - {type: regulatory, module: domains.healthcare.collectors.regulatory}

# Industry publications
publications:
  - name: "STAT News"
    url: "https://www.statnews.com"
    rss: "https://www.statnews.com/feed/"

  - name: "Fierce Healthcare"
    url: "https://www.fiercehealthcare.com"
    rss: "https://www.fiercehealthcare.com/rss/xml"

# Report templates
reports:
  - {type: daily_brief, module: domains.healthcare.reports.daily_brief}
  - {type: regulatory_update, module: domains.healthcare.reports.regulatory}
```

### Step 3: Implement Domain-Specific Collectors (Optional)

```python
# domains/healthcare/collectors/regulatory.py
from moltpulse.core.collector_base import Collector, CollectorResult
from moltpulse.core.lib import schema

class RegulatoryCollector(Collector):
    """Collector for FDA and regulatory updates."""

    REQUIRED_API_KEYS = []  # Uses public FDA API

    @property
    def collector_type(self) -> str:
        return "regulatory"

    @property
    def name(self) -> str:
        return "FDA Regulatory"

    def collect(self, profile, from_date, to_date, depth="default"):
        items = []
        sources = []

        # Implement collection logic here
        # Fetch from FDA API, parse results, create NewsItem objects

        return CollectorResult(items=items, sources=sources)
```

### Step 4: Implement Domain-Specific Reports (Optional)

```python
# domains/healthcare/reports/daily_brief.py
from moltpulse.core.report_base import DailyBriefGenerator
from moltpulse.core.lib import schema

class HealthcareDailyBrief(DailyBriefGenerator):
    """Healthcare-specific daily briefing."""

    @property
    def report_type(self) -> str:
        return "daily_brief"

    def generate(self, processed_items, from_date, to_date):
        report = schema.Report(
            title="Healthcare Daily Brief",
            domain="healthcare",
            profile=self.profile.name,
            report_type="daily_brief",
        )

        # Build report sections
        # Add regulatory updates section
        # Add market moves section
        # Add news highlights section

        return report
```

### Step 5: Create Default Profile

```yaml
# domains/healthcare/profiles/default.yaml
profile_name: default

focus:
  pharma_companies:
    priority_1: []
    exclude: []
  focus_areas:
    primary: [oncology, immunology]

thought_leaders: []

publications:
  - STAT News
  - Fierce Healthcare

reports:
  daily_brief: true
  regulatory_update: true

delivery:
  channel: console
```

### Step 6: Validate

```bash
moltpulse domain validate healthcare
moltpulse run --domain=healthcare --profile=default --dry-run daily
```

## Updating Domains

### Add Entity

```bash
moltpulse domain update healthcare --add-entity "pharma:ABBV:AbbVie"
```

### Add Collector

```bash
moltpulse domain update healthcare \
  --add-collector "clinical_trials:domains.healthcare.collectors.clinical_trials"
```

### Add Publication

```bash
moltpulse domain update healthcare \
  --add-publication "BioPharma Dive:https://www.biopharmadive.com/feeds/news/"
```

## Generic vs Domain-Specific Collectors

**Generic collectors** work across domains:
- `collectors.financial` - Stock/financial data via Alpha Vantage
- `collectors.news` - News via NewsData.io or NewsAPI
- `collectors.rss` - RSS feed parsing
- `collectors.social_x` - X/Twitter via xAI

**Domain-specific collectors** handle industry-specific data:
- `domains.advertising.collectors.awards` - Ad industry awards
- `domains.advertising.collectors.pe_activity` - M&A tracking
- `domains.healthcare.collectors.regulatory` - FDA updates

Use generic collectors when possible; create domain-specific ones for specialized data sources.
