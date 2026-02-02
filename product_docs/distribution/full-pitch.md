# MoltPulse: Open-Source Industry Intelligence

The complete pitch for OpenClaw builders.

---

## What It Is

MoltPulse is a CLI tool that monitors industries and generates automated intelligence reports. It aggregates:

- **Stock/financial data** (Alpha Vantage, Yahoo Finance)
- **News** (NewsData.io, NewsAPI)
- **RSS feeds** (trade publications)
- **Social media** (X/Twitter via xAI)
- **Web scraping** (awards, M&A activity)

One command generates a daily brief, weekly digest, or specialized report:

```bash
moltpulse run --domain=advertising --profile=default daily
```

The output is a structured report with scored, deduplicated content and optional LLM-enhanced summaries.

---

## Why It Matters

Enterprise intelligence tools cost $10K-$50K+/year:

| Tool | Annual Cost | Focus |
|------|-------------|-------|
| AlphaSense | $10,000+ | AI market intelligence |
| Meltwater | $12,000-50,000 | News/social monitoring |
| CB Insights | $50,000+ | Private company data |
| Contify | Custom | Competitive intelligence |

**There's no open-source alternative that combines all these capabilities.**

Developers who need industry intelligence today either:
1. Pay enterprise prices
2. Cobble together 5-10 separate tools (yfinance, feedparser, tweepy, etc.)
3. Do it manually (30+ minutes/day)

MoltPulse is the batteries-included solution: free, self-hosted, extensible.

---

## What We're Building Next: MoltPulse Network

A publishing platform where domain experts share reports:

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR MACHINE                                 │
│  MoltPulse CLI → Report Generation → --publish flag             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MOLTPULSE NETWORK                              │
│  Ingest API → Search Index → Feed Generation → Web UI           │
│                                                                  │
│  Hosted at: hub.moltpulse.ai                                    │
└─────────────────────────────────────────────────────────────────┘
```

**How it works**:
1. **Publishers** run MoltPulse and optionally publish reports
2. **Consumers** browse the network and subscribe ($9/month)
3. **Revenue split**: 50% platform / 50% publisher pool

---

## Why Publish?

| Benefit | Details |
|---------|---------|
| **Free access** | Publishers get all network content free (normally $9/mo) |
| **Revenue share** | 50% of subscription revenue distributed to publishers |
| **First-mover advantage** | Early publishers build audience before competition |
| **Tenure bonus** | Payout formula rewards long-term publishers |
| **Ownership** | Your domain, your profile, your audience |

### Revenue Projections

| Scale | Monthly Subscribers | Publisher Pool | Top 10% Earns |
|-------|---------------------|----------------|---------------|
| Year 1 (Q4) | 500 | $2,250/mo | ~$180/mo |
| Year 2 | 1,000 | $4,500/mo | ~$360/mo |
| At scale | 10,000 | $45,000/mo | ~$3,600/mo |

**These are projections, not promises.** Early, consistent publishers will earn more due to the payout formula:

- 35% Engagement (likes, saves, comments)
- 25% Consistency (regular publishing)
- 20% Quality (LLM-assessed report quality)
- 15% Volume (number of reports)
- 5% Tenure (time as active publisher)

---

## What We Need: Domain Experts

MoltPulse currently has one domain: **advertising**. We need experts to build:

- Healthcare / Biotech / Pharma
- Fintech / Banking / Insurance
- Real Estate / PropTech
- Energy / Climate / Cleantech
- Retail / E-commerce / CPG
- Media / Entertainment
- Legal / Law Firms
- SaaS / Developer Tools
- Your industry

---

## What Domain Creation Involves

### With Claude/LLM Assistance (An Afternoon)

Uses existing collectors (financial, news, RSS, social). Mostly YAML config.

1. **domain.yaml** (~100-150 lines): Define entities, publications, thought leaders
2. **profiles/default.yaml** (~50-80 lines): Default focus and delivery settings
3. **Test and iterate** with existing collectors

Claude can generate most of this from a conversation about your industry. You provide the domain knowledge, Claude handles the YAML.

### Enhanced Domain (Add a Day)

Add industry-specific data sources if needed.

4. **Custom collectors** (100-300 lines Python): FDA filings, SEC reports, industry APIs
5. **Custom report templates** (150-250 lines): Industry-specific formatting

With LLM assistance, custom collectors are straightforward - you describe the API, Claude writes the integration.

### Example: Healthcare Domain Structure

```
domains/healthcare/
├── domain.yaml                    # Entities, publications, collectors
├── profiles/
│   └── default.yaml               # Default monitoring config
├── collectors/
│   └── regulatory.py              # FDA/regulatory data (optional)
└── reports/
    └── daily_brief.py             # Healthcare-specific report format
```

### Sample domain.yaml

```yaml
domain: healthcare
display_name: "Healthcare Industry Intelligence"

entity_types:
  pharma_companies:
    - {symbol: PFE, name: "Pfizer"}
    - {symbol: JNJ, name: "Johnson & Johnson"}
    - {symbol: MRK, name: "Merck"}
    - {symbol: ABBV, name: "AbbVie"}

  focus_areas:
    - oncology
    - immunology
    - digital_health

collectors:
  - {type: financial, module: collectors.financial}
  - {type: news, module: collectors.news}
  - {type: rss, module: collectors.rss}
  - {type: social, module: collectors.social_x}

publications:
  - name: "STAT News"
    rss: "https://www.statnews.com/feed/"
    priority: 1
  - name: "FiercePharma"
    rss: "https://www.fiercepharma.com/rss/xml"
    priority: 1

thought_leaders:
  - {name: "Eric Topol", x_handle: "EricTopol"}
  - {name: "Vinay Prasad", x_handle: "VPrasadMDMPH"}

reports:
  - {type: daily_brief, module: reports.daily_brief}
```

---

## Skills Required

**Essential**:
- Domain knowledge (the hard part - you know your industry)
- Access to Claude or similar LLM (handles the technical work)

**Helpful** (for enhanced domains):
- Python familiarity (Claude writes it, you review it)
- Understanding of APIs in your industry

**The reality**: If you're in the OpenClaw community, you already have the technical skills. The question is whether you have deep enough industry knowledge to make a useful domain.

---

## The Trade-off

**You invest**: An afternoon (basic domain) to a weekend (enhanced domain)

**Guaranteed benefit**: A free, self-hosted industry intelligence tool for your own use

**Potential upside**: Revenue share if the network succeeds, first-mover advantage in your vertical

**Why now**: Early publishers get tenure bonus in the payout formula. First-movers own their verticals.

---

## Next Steps

1. **Explore**: Install and try MoltPulse
   ```bash
   pip install moltpulse
   moltpulse --help
   ```

2. **Read**: Review the domain documentation
   - [domains.md](https://github.com/gregce/moltpulse/blob/main/docs/domains.md)
   - [profiles.md](https://github.com/gregce/moltpulse/blob/main/docs/profiles.md)

3. **Discuss**: Open an issue with your domain idea
   - What industry?
   - What entities would you track?
   - What publications/feeds exist?
   - We'll provide feedback before you invest significant time

4. **Build**: Fork, create your domain, submit a PR

---

## Questions?

See [FAQ](./faq.md) for common questions and honest answers.
