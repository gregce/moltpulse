# Domain Contributor Guide

How to build a MoltPulse domain. Written for OpenClaw builders who move fast.

**Context**: You've seen what this community ships - Moltbook went from idea to viral in a week. A domain is simpler than that.

---

## Prerequisites

- Python 3.11+ environment
- Claude or similar LLM (handles the YAML/Python generation)
- Deep knowledge of your industry (this is the actual requirement)

---

## Time Estimates (With LLM Assistance)

| Task | Time | Required? |
|------|------|-----------|
| Brain dump to Claude (entities, publications, thought leaders) | 30-60 min | Yes |
| Generate + refine domain.yaml | 30-60 min | Yes |
| Generate + refine default profile | 15-30 min | Yes |
| Test with existing collectors | 30-60 min | Yes |
| **Basic domain** | **2-4 hours** | **Yes** |
| Custom collector (per source) | 1-2 hours | No |
| Custom report template | 30-60 min | No |
| **Enhanced domain** | **4-8 hours** | **No** |

**Note**: These estimates assume you're using Claude/LLM assistance. If you're writing everything manually, multiply by 2-3x.

---

## Step 1: Brain Dump to Claude (30-60 min)

Start a conversation with Claude about your industry. You're extracting your domain knowledge into structured form.

### Entities to Track

**Public companies with stock symbols**: These get financial data (price, volume, change %)
```yaml
pharma_companies:
  - {symbol: PFE, name: "Pfizer"}
  - {symbol: JNJ, name: "Johnson & Johnson"}
```

**Private companies/organizations**: These get news matching only (no symbol needed)
```yaml
hospital_systems:
  - {name: "Mayo Clinic"}
  - {name: "Cleveland Clinic"}
```

**Categories/sectors**: For filtering and organization
```yaml
focus_areas:
  - oncology
  - immunology
  - digital_health
```

### Publications with RSS Feeds

Find 8-15 industry publications. For each, verify:
- RSS feed is actively updated (check dates)
- Feed is accessible without authentication
- Content is substantive (not just headlines)

**How to find RSS feeds**:
- Check `/feed/`, `/rss.xml`, `/rss/`, `/feed.xml` on publication sites
- Use a feed reader to verify the feed works
- Google "[publication name] RSS feed"

Example research output:
```yaml
publications:
  - name: "STAT News"
    url: "https://www.statnews.com"
    rss: "https://www.statnews.com/feed/"
    priority: 1  # Primary trade publication

  - name: "FiercePharma"
    url: "https://www.fiercepharma.com"
    rss: "https://www.fiercepharma.com/rss/xml"
    priority: 1

  - name: "Healthcare Dive"
    url: "https://www.healthcaredive.com"
    rss: "https://www.healthcaredive.com/feeds/news/"
    priority: 2  # Secondary source
```

### Thought Leaders on X/Twitter

Identify 5-15 people actively posting about your industry:
```yaml
thought_leaders:
  - {name: "Eric Topol", x_handle: "EricTopol", focus: "digital health, AI"}
  - {name: "Vinay Prasad", x_handle: "VPrasadMDMPH", focus: "oncology, policy"}
```

---

## Step 2: Create Directory Structure

```bash
# From repo root
mkdir -p src/moltpulse/domains/healthcare/{collectors,reports,profiles}
touch src/moltpulse/domains/healthcare/__init__.py
touch src/moltpulse/domains/healthcare/collectors/__init__.py
touch src/moltpulse/domains/healthcare/reports/__init__.py
touch src/moltpulse/domains/healthcare/profiles/__init__.py
```

---

## Step 3: Generate domain.yaml with Claude (30-60 min)

Prompt Claude with your research and ask it to generate the YAML. Review and refine.

Create `src/moltpulse/domains/healthcare/domain.yaml`:

```yaml
# Domain configuration for healthcare industry intelligence

domain: healthcare
display_name: "Healthcare Industry Intelligence"
description: "Monitor pharma, biotech, hospitals, and healthcare policy"

# Entity types define what you're tracking
entity_types:
  # Companies with stock symbols get financial data
  pharma_companies:
    - {symbol: PFE, name: "Pfizer"}
    - {symbol: JNJ, name: "Johnson & Johnson"}
    - {symbol: MRK, name: "Merck"}
    - {symbol: ABBV, name: "AbbVie"}
    - {symbol: BMY, name: "Bristol-Myers Squibb"}
    - {symbol: LLY, name: "Eli Lilly"}
    - {symbol: GILD, name: "Gilead Sciences"}
    - {symbol: AMGN, name: "Amgen"}
    - {symbol: REGN, name: "Regeneron"}
    - {symbol: VRTX, name: "Vertex Pharmaceuticals"}

  biotech_companies:
    - {symbol: MRNA, name: "Moderna"}
    - {symbol: BNTX, name: "BioNTech"}
    - {symbol: NVAX, name: "Novavax"}

  # Companies without symbols get news matching only
  hospital_systems:
    - {name: "Mayo Clinic"}
    - {name: "Cleveland Clinic"}
    - {name: "Johns Hopkins"}
    - {name: "Kaiser Permanente"}

  # Categories for filtering
  focus_areas:
    - oncology
    - immunology
    - gene_therapy
    - digital_health
    - telehealth
    - medical_devices

# Collectors to use (these are built-in, no custom code needed)
collectors:
  - {type: financial, module: collectors.financial}
  - {type: news, module: collectors.news}
  - {type: rss, module: collectors.rss}
  - {type: social, module: collectors.social_x}

# Publications with RSS feeds
publications:
  # Primary trade publications (priority 1)
  - name: "STAT News"
    rss: "https://www.statnews.com/feed/"
    priority: 1

  - name: "FiercePharma"
    rss: "https://www.fiercepharma.com/rss/xml"
    priority: 1

  - name: "FierceBiotech"
    rss: "https://www.fiercebiotech.com/rss/xml"
    priority: 1

  # Secondary sources (priority 2)
  - name: "BioPharma Dive"
    rss: "https://www.biopharmadive.com/feeds/news/"
    priority: 2

  - name: "Healthcare Dive"
    rss: "https://www.healthcaredive.com/feeds/news/"
    priority: 2

  - name: "MedCity News"
    rss: "https://medcitynews.com/feed/"
    priority: 2

  # General business (priority 3)
  - name: "Reuters Health"
    rss: "https://www.reuters.com/arc/outboundfeeds/v3/all/?outputType=xml&_website=reuters"
    priority: 3
    keywords: ["health", "pharma", "drug", "FDA"]

# Thought leaders on X/Twitter
thought_leaders:
  - {name: "Eric Topol", x_handle: "EricTopol"}
  - {name: "Vinay Prasad", x_handle: "VPrasadMDMPH"}
  - {name: "Bob Wachter", x_handle: "Bob_Wachter"}
  - {name: "Ashish Jha", x_handle: "ashaboradwaj"}

# Report types available
reports:
  - {type: daily_brief, module: reports.daily_brief}
  - {type: weekly_digest, module: reports.weekly_digest}
```

---

## Step 4: Generate Default Profile (15-30 min)

Same process - Claude generates, you refine.

Create `src/moltpulse/domains/healthcare/profiles/default.yaml`:

```yaml
# Default profile for healthcare domain

profile_name: "default"
description: "Balanced healthcare industry monitoring"

# Which entity types to focus on
focus:
  entity_types:
    - pharma_companies
    - biotech_companies

  focus_areas:
    primary:
      - oncology
      - immunology
    secondary:
      - digital_health
      - gene_therapy

# Thought leaders to track
thought_leaders:
  - name: "Eric Topol"
    x_handle: "EricTopol"
    priority: 1
  - name: "Vinay Prasad"
    x_handle: "VPrasadMDMPH"
    priority: 1

# Publications to monitor
publications:
  - "STAT News"
  - "FiercePharma"
  - "FierceBiotech"
  - "BioPharma Dive"

# Keywords for relevance boosting
keywords:
  boost:
    - "FDA approval"
    - "clinical trial"
    - "Phase 3"
    - "breakthrough therapy"
    - "acquisition"
    - "merger"

  filter:  # Items with these keywords get lower scores
    - "sponsored"
    - "advertisement"

# Report preferences
reports:
  daily_brief: true
  weekly_digest: true

# Delivery settings
delivery:
  channel: console  # console | email | file

# LLM enhancement (optional)
llm:
  enhance: true
  provider: auto  # auto-detects available LLM
```

---

## Step 5: Test Your Domain (30-60 min)

```bash
# Validate configuration syntax
moltpulse domain validate healthcare

# Dry run (no API calls, checks config loading)
moltpulse run --domain=healthcare --profile=default --dry-run daily

# Test individual collectors
moltpulse run --domain=healthcare --profile=default --collectors=rss daily
moltpulse run --domain=healthcare --profile=default --collectors=news daily

# Full run (requires API keys)
moltpulse run --domain=healthcare --profile=default daily
```

### Common Issues

**RSS feed errors**: Feed URL changed or requires auth. Test in browser/feed reader first.

**No results from news collector**: Check that your entity names appear in news. Try broader keywords.

**API rate limits**: Free tiers have limits. Space out testing.

---

## Step 6 (Optional): Custom Collectors (1-2 hours each)

If your industry has unique data sources, Claude can write custom collectors for you.

### When You Need a Custom Collector

- Industry-specific APIs (FDA openFDA, SEC EDGAR, etc.)
- Databases that require authentication
- Websites that need scraping
- Data formats that need special parsing

### How to Build One with Claude

1. Find an example collector: `src/moltpulse/domains/advertising/collectors/`
2. Describe your data source to Claude (API docs, website structure, etc.)
3. Ask Claude to generate a collector following the existing pattern
4. Review, test, iterate

### Collector Structure (for reference)

```python
# src/moltpulse/domains/healthcare/collectors/regulatory.py

from moltpulse.core.collector_base import Collector, CollectorResult
from moltpulse.core.lib.schema import NewsItem, Source

class RegulatoryCollector(Collector):
    """Collects FDA regulatory actions."""

    REQUIRED_API_KEYS = []  # Or ["OPENFDA_API_KEY"] if needed

    @property
    def name(self) -> str:
        return "FDA Regulatory Actions"

    @property
    def collector_type(self) -> str:
        return "regulatory"

    def collect(self, profile, from_date, to_date, depth="default") -> CollectorResult:
        items = []
        sources = []

        # Your data fetching logic here
        # ...

        # Return structured result
        return CollectorResult(
            items=items,
            sources=sources,
            collector_name=self.name
        )
```

Claude will handle the implementation details. You just need to describe what data you want and where it comes from.

---

## Step 7: Submit Your Domain

### Before Submitting

- [ ] All config files pass validation
- [ ] At least one successful full run
- [ ] Default profile generates useful output
- [ ] RSS feeds are all working
- [ ] Stock symbols are correct

### PR Checklist

1. Fork the repository
2. Create your domain under `src/moltpulse/domains/`
3. Add basic tests (config validation at minimum)
4. Open a PR with:
   - **What industry**: Brief description
   - **Why you**: Your background/expertise
   - **Entity coverage**: Number of companies, publications, thought leaders
   - **Test results**: Sample output from a run

### Review Process

1. Maintainers review config for completeness
2. Test run on CI
3. Feedback and iteration
4. Merge

---

## Getting Help

### Before You Start

Open a GitHub issue with the `domain-proposal` label:
- What industry?
- Initial entity list (5-10 companies)
- Initial publication list (5-10 RSS feeds)
- Any unique data sources you'd want to add?

We'll provide feedback before you invest significant time.

### During Development

- Check existing domains for patterns
- Open draft PR early for feedback
- Ask in issues if stuck

---

## FAQ

**Q: What if I can't find enough RSS feeds?**
A: 5 good feeds is enough to start. News and social collectors supplement RSS.

**Q: Do I need to build custom collectors?**
A: No. Start with built-in collectors. Add custom ones later if needed.

**Q: What if my industry overlaps with someone else's?**
A: That's fine. Multiple healthcare domains with different focuses (pharma vs. hospitals vs. digital health) are valuable.

**Q: How long until my domain is merged?**
A: Typically 1-2 weeks for review and iteration.

**Q: Can I update my domain after it's merged?**
A: Yes. Submit PRs for updates. Active maintainers get commit access.
