# Frequently Asked Questions

Honest answers for OpenClaw builders considering a domain.

---

## About MoltPulse

### What exactly is MoltPulse?

A CLI tool that collects industry data from multiple sources and generates formatted intelligence reports.

**Sources**: Stock APIs (Alpha Vantage), news APIs (NewsData.io, NewsAPI), RSS feeds, X/Twitter, web scraping

**Output**: Daily briefs, weekly digests, custom reports with scored and deduplicated content

Think of it as: "What if you could automate a research analyst's daily reading?"

### How is this different from Google Alerts?

| Feature | MoltPulse | Google Alerts |
|---------|-----------|---------------|
| Sources | Stock + news + RSS + social + scraping | Web pages only |
| Scoring | Relevance + recency + engagement | None |
| Deduplication | Yes | No |
| Custom entities | Track specific companies/people | Keywords only |
| Report format | Structured, customizable | Email list |
| LLM summaries | Optional AI enhancement | No |
| Self-hosted | Yes | No |

### Why would I use this instead of just reading Twitter/news?

Time. MoltPulse automates the collection and filtering you'd otherwise do manually.

A daily brief that takes 30+ minutes to compile by hand is generated in 2 minutes.

### Is this actually free?

The framework is MIT licensed. You pay only for API keys:

| API | Cost |
|-----|------|
| Alpha Vantage | Free tier available (25 calls/day) |
| NewsData.io | Free tier available (200 calls/day) |
| xAI (Twitter) | Pay-per-use (~$0.01-0.05 per report) |
| OpenAI/Claude (LLM) | Pay-per-use (~$0.02-0.10 per report) |

**Total cost**: $0-20/month depending on usage. Most users stay in free tiers.

### What industries/domains exist?

Currently: **advertising** (fully built)

Planned: healthcare, fintech, legal, real estate, energy, retail, media, SaaS

This is why we're recruiting domain experts.

---

## About the Network

### What is MoltPulse Network?

A publishing platform (planned, not yet launched) where:

1. Publishers run MoltPulse and share their reports
2. Consumers browse and subscribe ($9/month)
3. Revenue is split 50% platform / 50% publishers

### How does the revenue share work?

1. Consumers pay $9/month to browse all reports
2. 50% goes to platform (infrastructure, development)
3. 50% goes to publisher pool
4. Pool is distributed by weighted formula:
   - 35% Engagement (likes, saves, comments on your reports)
   - 25% Consistency (regular publishing schedule)
   - 20% Quality (LLM-assessed report quality)
   - 15% Volume (number of reports published)
   - 5% Tenure (time as active publisher)

### What are realistic earnings?

**At Year 1 scale (500 subscribers, ~50 publishers)**:
- Total monthly revenue: $4,500
- Publisher pool: $2,250
- Top 10% (5 publishers): ~$180/month each
- Middle 40% (20 publishers): ~$45/month each
- Bottom 50% (25 publishers): ~$12/month each

**At scale (10,000 subscribers, ~200 publishers)**:
- Total monthly revenue: $90,000
- Publisher pool: $45,000
- Top 10%: ~$3,600/month each

**These are projections, not guarantees.** They assume successful launch and subscriber growth.

### Why would anyone pay $9/month when MoltPulse is free?

Running MoltPulse yourself requires:
- Setting up Python environment
- Configuring API keys
- Creating/maintaining profiles
- Running reports on schedule
- Keeping configs updated

The Network is for people who want intelligence without operations. Same reason people pay for newsletters instead of reading primary sources.

### What if my domain overlaps with someone else's?

Good. Multiple perspectives are valuable.

The advertising domain might have 10 publishers with different focuses:
- Creative agencies
- Media buying
- Ad tech
- Brand marketing
- Performance marketing

Competition improves quality. Readers follow publishers whose perspective they value.

### What stops someone from copying my domain config?

Nothing. Configs are YAML files - they're not defensible IP.

Your value comes from:
- **Consistent, quality publishing**: Readers follow reliable publishers
- **Audience you build**: Followers, engagement, reputation
- **Perspective**: Your unique curation and insights
- **Tenure bonus**: Payout formula rewards long-term publishers

### What if the Network never launches?

You still have a free, self-hosted industry intelligence tool for your own use.

The Network is potential upside. The tool is guaranteed value.

### What if it launches but doesn't get subscribers?

Same answer. Your reports are still valuable to you. The Network is bonus, not the core value.

---

## About Contributing

### How hard is it really to create a domain?

**With Claude/LLM assistance**:
- 2-4 hours for basic domain (mostly YAML)
- 4-8 hours for enhanced domain with custom collectors

**The hard part is industry knowledge, not code.**

You need to know: Which companies matter? Which publications are credible? Who are the thought leaders? What signals indicate important news?

If you already have this knowledge, Claude handles the technical work.

### Do I need to know Python?

**For basic domain**: No. You describe your industry to Claude, it generates YAML.

**For custom collectors**: Helpful but not required. Claude writes the Python, you review it.

### What skills do I actually need?

**Essential**:
- Deep industry knowledge (the actual requirement)
- Access to Claude or similar LLM

**Helpful**:
- Ability to read Python (to review Claude's output)
- Understanding of APIs in your industry

**If you're in the OpenClaw community**: You already have the technical skills. The question is whether you have domain expertise worth monetizing.

### What if I start and don't finish?

Nothing bad happens. Your fork is yours. We won't publicly shame abandoned PRs.

If you get stuck, open an issue. We'll help or find someone to take over.

### Can I build a domain for internal company use only?

Yes. MIT license means use it however you want. You don't have to publish to the Network.

Many users will run MoltPulse purely for internal intelligence.

### What industries are most needed?

**High value (underserved by free tools)**:
- Healthcare / Biotech / Pharma
- Financial services / Fintech
- Legal / Law firms
- Real estate / PropTech
- Energy / Climate / Cleantech

**Interesting niches**:
- Nonprofit fundraising
- Academic research
- Government contracting
- Supply chain / Logistics

**Already crowded (harder to differentiate)**:
- General tech news
- Crypto

### How do I know if my domain idea is good?

Ask yourself:
1. Would I use this daily/weekly? (If not, who would?)
2. Are there 5+ trade publications with RSS feeds?
3. Are there 10+ public companies I'd track?
4. Do people currently pay for similar intelligence?
5. Can I identify 5+ thought leaders on X/Twitter?

If yes to most: probably good. Open an issue to discuss.

---

## Skepticism / Concerns

### This sounds too good to be true

Fair. Here's the honest version:

**What's real**:
- MoltPulse is working software (try it)
- The tool genuinely replaces $10K+/year enterprise subscriptions
- MIT license means it's actually free

**What's uncertain**:
- Network revenue depends on subscriber growth
- Your payout depends on competition and performance
- Early projections are projections

**The trade-off**:
- You invest an afternoon to a weekend
- Guaranteed: useful intelligence tool for yourself
- Potential: revenue share as network grows

### Why are you recruiting contributors instead of building domains yourself?

Three reasons:

1. **We don't have deep expertise in every industry**. A healthcare domain built by someone who reads STAT News daily will be better than one we build from research.

2. **Community-built content creates network effects**. Publishers have incentive to promote their domains.

3. **Speed**. With the OpenClaw community, we can launch 10 domains in parallel instead of one at a time.

### What's the catch?

Time investment with variable payoff.

You might build a healthcare domain and:
- Be the only healthcare publisher (big share)
- Be one of 50 healthcare publishers (small share)
- Find healthcare doesn't get subscribers

**Mitigations**:
- Early publishers get tenure bonus
- First-mover in a vertical owns it
- You get a useful tool regardless
- Time investment is small (afternoon to weekend)

### Why should I trust this will happen?

You've seen what this community ships. Moltbook went from idea to viral in a week. The OpenClaw ecosystem moves fast.

Verify for yourself:
1. **Is the current tool useful?** Try it.
2. **Is the architecture sound?** Read the docs.
3. **Is the time investment acceptable?** An afternoon to a weekend.
4. **Is the downside acceptable?** You get a useful tool either way.

### What happens to my domain if the project dies?

You keep it. MIT license means your fork is yours forever.

The code doesn't depend on any central service. You can run MoltPulse indefinitely on your own infrastructure.

### Who's behind this?

[Add founder/team background here]

---

## Technical Questions

### What APIs do I need?

**Required for basic functionality**:
- Alpha Vantage (free tier: 25 calls/day)
- NewsData.io (free tier: 200 calls/day)

**Optional**:
- xAI API (for Twitter/X data) - pay per use
- OpenAI or Anthropic API (for LLM enhancement) - pay per use

### Can I run this without any API keys?

Yes, but limited. RSS collector works without keys. You'd get trade publication content but no stock data, news search, or social.

### How often should I run reports?

Depends on your use case:
- **Daily brief**: Every morning (weekdays)
- **Weekly digest**: Once per week
- **Real-time monitoring**: Not supported (this is batch processing)

### Can I customize the scoring algorithm?

Yes. Weights are configurable per profile. Default is:
- 45% Relevance (keyword matching)
- 25% Recency (newer = higher)
- 30% Engagement (likes, shares, comments)

### Does it work on Windows?

Yes, but less tested. Linux/macOS recommended.

### Can I deploy this to a server?

Yes. Common setups:
- Cron job on Linux server
- GitHub Actions scheduled workflow
- Docker container
- OpenClaw (scheduling service)

---

## Getting Started

### What's the fastest way to try MoltPulse?

```bash
# Install
pip install moltpulse

# See available commands
moltpulse --help

# Run advertising domain (built-in)
# Requires API keys set as environment variables
moltpulse run --domain=advertising --profile=default daily
```

### Where do I go for help?

1. [Documentation](https://github.com/gregce/moltpulse/tree/main/docs)
2. [GitHub Issues](https://github.com/gregce/moltpulse/issues)
3. [Contributor Guide](./contributor-guide.md)

### How do I propose a new domain?

Open a GitHub issue with:
- Industry name
- 5-10 companies you'd track
- 5-10 publications with RSS feeds
- 3-5 thought leaders on X
- Your background in this industry

We'll provide feedback before you invest time building.
