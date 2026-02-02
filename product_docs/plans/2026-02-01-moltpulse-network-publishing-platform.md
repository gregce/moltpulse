# MoltPulse Network: Crowdsourced Intelligence Publishing Platform

**Date**: 2026-02-01
**Status**: Product Vision & Architecture Plan

## Vision

Transform MoltPulse from a personal CLI tool into a **crowdsourced intelligence publishing platform** where users running MoltPulse via OpenClaw can optionally publish their reports, creating a network of niche, curated industry intelligence.

**Tagline**: "Crowdsourced industry intelligence, powered by open source"

**Core Insight**: MoltPulse already has the hard parts (multi-source collection, scoring, LLM synthesis). The missing piece is a **social layer** for discovery, reputation, and collaboration.

---

## The Flywheel

```
More Domains → More Publishers → Better Coverage → More Consumers
      ↑                                                    │
      └──────────── Domain experts contribute ─────────────┘
```

---

## Strategic Decisions (Confirmed)

1. **Hosting**: **Hosted SaaS** at `hub.moltpulse.io` - central hub for network effects, easier onboarding
2. **OpenClaw Integration**: **Loose coupling** - MoltPulse Network is standalone, works with OpenClaw but doesn't require it
3. **Domain Expansion**: **Community-driven** - build domain creation tools and let community contribute organically

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER'S MACHINE (Unchanged)                       │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
│  │ MoltPulse   │────▶│   Report    │────▶│  Delivery   │            │
│  │    CLI      │     │ Generation  │     │ (existing)  │            │
│  └─────────────┘     └─────────────┘     └──────┬──────┘            │
│                                                  │                   │
│                                          --publish flag (NEW)        │
│                                                  │                   │
└──────────────────────────────────────────────────┼───────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MOLTPULSE NETWORK (New Service)                    │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │  Ingest  │───▶│  Index   │───▶│  Feed    │───▶│   Web    │       │
│  │   API    │    │ (Search) │    │   Gen    │    │   UI     │       │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘       │
│                                                                      │
│  Storage: S3 (reports) + Postgres (metadata) + Meilisearch (search) │
│                                                                      │
│  Hosted at: hub.moltpulse.io (managed SaaS)                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Publishing (Opt-in, Full Control)

**Profile Configuration**:
```yaml
# domains/advertising/profiles/ricki.yaml
publishing:
  enabled: true
  visibility: public          # public | unlisted | private
  delay: 6h                   # Embargo before publishing
  publisher_name: "Ricki's Ad Intel"

  sections:                   # Choose what to share
    stocks: true
    news: true
    thought_leaders: true
    pe_alerts: false          # Keep M&A intel private
    executive_summary: true
    strategic_recommendations: false
```

**CLI Integration**:
```bash
moltpulse run --domain=advertising --profile=ricki daily --publish
moltpulse publish status
moltpulse publish unpublish <report-id>
```

### 2. Discovery

**Browse by**:
- Domain (advertising, healthcare, fintech)
- Entity (WPP, Omnicom, Pfizer)
- Publisher (@ricki, @adguru)
- Thought Leader (@profgalloway)
- Keyword/Topic

**Follow System**: Follow publishers, domains, entities, keywords → personalized feed

**Feed Algorithm**:
```
40% Followed publishers
25% Followed domains/entities
20% Trending in your domains
15% Discovery (new publishers, viral reports)
```

### 3. Quality & Trust

**Publisher Reputation Score (0-100)**:
- 30% Consistency (regular publishing)
- 25% Followers/growth
- 20% Report quality (LLM-assessed)
- 15% Domain tenure
- 10% Profile completeness

**Badges**: Verified, Domain Expert, Consistent Publisher, Top 10%

### 4. Profile Templates Marketplace

Publishers can share their profile configurations:
```bash
moltpulse profile clone advertising/templates/fundraiser --as my-profile
moltpulse profile publish my-profile --name "Tech Sector Fundraiser"
```

### 5. Collaborative Intelligence

- **Cross-publisher validation**: Items surfaced by multiple publishers get boosted
- **Community curation**: Upvotes, saves, comments
- **Collections**: Curated themed collections (e.g., "2026 M&A Tracker")

---

## Data Model Additions

```python
# New in schema.py

@dataclass
class PublishedReport:
    """Sanitized report for public distribution."""
    id: str                     # UUID
    slug: str                   # URL-friendly

    # From Report (preserved)
    title: str
    domain: str
    report_type: str
    generated_at: str
    date_range_from: str
    date_range_to: str
    sections: List[ReportSection]
    all_sources: List[Source]
    executive_summary: Optional[str]

    # Publishing metadata (new)
    publisher_id: str
    publisher_name: str
    published_at: str
    visibility: str
    tags: List[str]
    entities_mentioned: List[str]

    # Engagement (new)
    likes: int = 0
    saves: int = 0
    comments: int = 0
```

---

## Privacy & Sanitization

**Always strip**:
- `delivery` config (email addresses, file paths)
- `llm.prompts` custom prompts (reveal strategy)
- `keywords.filter` (reveals what to hide)
- Profile name → replace with publisher_name

**Preserve for attribution**:
- `all_sources` (original source URLs)
- `domain`, `report_type`
- Section content and insights

---

## API Endpoints (MoltPulse Network Service)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/reports` | POST | API Key | Publish report |
| `/api/v1/reports` | GET | None | List/search |
| `/api/v1/reports/{id}` | GET | None | Get report |
| `/api/v1/reports/{id}` | DELETE | API Key | Unpublish |
| `/api/v1/publishers/{id}` | GET | None | Publisher profile |
| `/api/v1/feed` | GET | Optional | Personalized feed |
| `/feeds/{domain}.xml` | GET | None | RSS feed |

---

## OpenClaw Integration (Loose Coupling)

MoltPulse Network is **standalone** - it works with or without OpenClaw:

**With OpenClaw** (scheduled publishing):
```json
{
  "name": "MoltPulse Daily Brief (Publish)",
  "schedule": { "expr": "0 7 * * 1-5", "tz": "America/Los_Angeles" },
  "payload": {
    "message": "moltpulse run --domain=advertising --profile=ricki --output=json --no-deliver --publish daily",
    "deliver": false
  }
}
```

**Without OpenClaw** (manual or cron):
```bash
# Standard cron, no OpenClaw required
0 7 * * 1-5 moltpulse run --domain=advertising --profile=ricki --publish daily
```

**Key principle**: Separate authentication, separate accounts. OpenClaw is a great scheduler but not required.

---

## Monetization

See [Monetization Design](2026-02-02-monetization-design.md) for the complete model.

**Summary**: "Contribute to consume" model where publishers get free access to all network content and share 50% of subscription revenue, while non-contributing consumers pay $9/month to browse.

---

## Implementation Phases

### Phase 1: CLI Publishing (3-4 weeks)
**Files to modify**:
- `src/moltpulse/core/lib/schema.py` - Add `PublishedReport` dataclass
- `src/moltpulse/core/profile_loader.py` - Parse `publishing` config section
- `src/moltpulse/cli.py` - Add `--publish` flag and `publish` subcommand
- `src/moltpulse/core/delivery.py` - Add `HubDeliverer` class

**New files**:
- `src/moltpulse/core/publish/sanitizer.py` - Strip private data
- `src/moltpulse/core/publish/client.py` - Network API client

**Deliverable**: Users can publish reports with `--publish` flag

### Phase 2: Network Service (4-5 weeks)
**New repo/service**: `moltpulse-hub`
- Ingest API (POST reports)
- Storage (S3 + Postgres)
- Search index (Meilisearch)
- Basic web UI (landing, browse, report view)

**Deliverable**: Central hub accepts and serves published reports

### Phase 3: Discovery & Social (4-5 weeks)
- Follow system (publishers, domains, entities)
- Personalized feed algorithm
- Publisher profiles
- Engagement (likes, saves, comments)
- Reputation scoring

**Deliverable**: Users can discover and follow publishers

### Phase 4: Templates & Ecosystem (3-4 weeks)
- Profile template marketplace
- Clone/fork profiles
- Domain registry and community creation tools
- Integrations (Slack, Discord, RSS)

**Deliverable**: Community-contributed profiles and domains

---

## Community Domain Creation

Since domain expansion is community-driven, Phase 4 becomes critical:

**Domain Creation Toolkit**:
```bash
moltpulse domain create healthcare --interactive
moltpulse domain validate healthcare
moltpulse domain submit healthcare  # Submit to community registry
```

**Domain Quality Gates** (for community submissions):
- Minimum 10 tracked entities
- At least 3 working collectors
- At least 5 publications with valid RSS
- One complete default profile
- 5 beta publishers running for 2 weeks
- Community review and approval

**Domain Registry** (at hub.moltpulse.io):
- Browse available domains
- Domain health metrics
- Maintainer attribution
- Fork/improve existing domains

---

## Naming

**Recommended**: "MoltPulse Network" or "MoltPulse Hub"

**URL**: `network.moltpulse.io` or `hub.moltpulse.io`

**Relationship**: CLI is primary (always works offline). Network is additive (optional publishing layer).

---

## Success Metrics (Year 1)

| Metric | Target |
|--------|--------|
| Active Publishers | 100 |
| Published Reports/week | 500 |
| Unique Domains | 10 |
| Profile Templates | 50 |
| Publisher retention (90 day) | >60% |

---

## Key Principles

1. **CLI remains primary** - Publishing is always optional
2. **Privacy by default** - Explicit opt-in, full control over what's shared
3. **Publisher ownership** - Full control, can unpublish anytime
4. **Open source core** - Network adds value but doesn't lock in
5. **Source attribution** - Original sources always credited

---

## Verification Plan

1. **Phase 1**: Run `moltpulse run --publish` and verify report POSTs to mock endpoint
2. **Phase 2**: Deploy hub service, verify end-to-end publish → browse flow
3. **Phase 3**: Test follow/feed personalization with multiple test publishers
4. **Phase 4**: Test profile clone workflow end-to-end

---

## Related Documents

- [Monetization Design](2026-02-02-monetization-design.md) - Complete monetization model with "contribute to consume" philosophy
- [Competitive Landscape Analysis](../research/2026-02-01-competitive-landscape-analysis.md) - Market positioning and alternatives
