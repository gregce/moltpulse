# MoltPulse Network: Monetization Design

**Date**: 2026-02-02
**Status**: Design Document
**Replaces**: Monetization section in `2026-02-01-moltpulse-network-publishing-platform.md`

---

## Core Philosophy

> **"Contribute to consume freely. Pay to browse passively."**

MoltPulse Network rewards contributors with free access while generating revenue from passive consumers. Revenue is split 50/50 between platform sustainability and publisher rewards.

---

## The Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCESS & REVENUE MODEL                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PUBLISHERS (via OpenClaw)              CONSUMERS (browsers)               │
│   ─────────────────────────              ───────────────────                │
│                                                                             │
│   ┌─────────────────────┐                ┌─────────────────────┐            │
│   │ • Run MoltPulse CLI │                │ • Browse hub.moltpulse.io       │
│   │ • Publish reports   │                │ • Search/discover    │            │
│   │ • Contribute intel  │                │ • Read reports       │            │
│   └──────────┬──────────┘                └──────────┬──────────┘            │
│              │                                      │                       │
│              ▼                                      ▼                       │
│   ┌─────────────────────┐                ┌─────────────────────┐            │
│   │   FREE ACCESS       │                │   PAID SUBSCRIPTION │            │
│   │   to all content    │                │   $9/month          │            │
│   │   + revenue share   │                │                     │            │
│   └─────────────────────┘                └──────────┬──────────┘            │
│                                                     │                       │
│                                                     ▼                       │
│                                          ┌─────────────────────┐            │
│                                          │   REVENUE SPLIT     │            │
│                                          │   ───────────────   │            │
│                                          │   50% → Platform    │            │
│                                          │   50% → Publishers  │            │
│                                          └─────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Access Tiers

### Tier 1: Publisher (Free)

**Who qualifies:**
- Runs MoltPulse CLI via OpenClaw agent
- Publishes at least 1 report per week (active publisher status)
- Reports meet minimum quality threshold

**What they get:**
- Full access to all published content on the network
- API access for programmatic consumption
- Publisher dashboard with analytics
- Share of subscription revenue pool

**Verification:**
- OpenClaw agent authentication (agent token, not browser session)
- Publishing activity tracked and verified
- 30-day grace period if publishing lapses

### Tier 2: Consumer (Paid)

**Who this is:**
- Individuals who want to consume intelligence without contributing
- Teams who want to browse without running their own agents
- Anyone who prefers to pay rather than operate

**Pricing:**
| Plan | Price | Access |
|------|-------|--------|
| Individual | $9/month | Full access, 1 user |
| Team (5 seats) | $29/month | Full access, 5 users |
| Enterprise | Custom | Unlimited seats, API, SLA |

**What they get:**
- Full access to all published content
- Search, browse, follow publishers
- Email digests and notifications
- API access (with rate limits)

### Tier 3: Free Preview

**What's free for everyone:**
- Browse domain listings
- View publisher profiles
- Read report titles and executive summaries (first 100 words)
- View 3 full reports per month (freemium gate)

---

## Revenue Split: 50/50

### Platform Share (50%)

Covers:
- Infrastructure (AWS, CDN, databases)
- Development and maintenance
- Support and operations
- Marketing and growth
- Reserve for sustainability

### Publisher Pool (50%)

Distributed among active publishers using a weighted formula.

---

## Publisher Payout Formula

### Weighting Factors

Each publisher's share is calculated based on multiple factors:

```
Publisher Score = (
    0.35 × Engagement Score +
    0.25 × Consistency Score +
    0.20 × Quality Score +
    0.15 × Volume Score +
    0.05 × Tenure Bonus
)
```

#### 1. Engagement Score (35%)
- Views, likes, saves, comments on their reports
- Follower count and growth
- Click-through rates

```python
engagement_score = (
    0.40 × normalized_views +
    0.25 × normalized_likes +
    0.20 × normalized_saves +
    0.15 × normalized_followers
)
```

#### 2. Consistency Score (25%)
- Regular publishing schedule
- Meeting declared frequency (daily, weekly)
- No gaps or lapses

```python
consistency_score = (
    reports_published / reports_expected
) * streak_multiplier

# streak_multiplier: 1.0 base, +0.1 per month of unbroken publishing, max 1.5
```

#### 3. Quality Score (20%)
- LLM-assessed report quality
- Source diversity and citation quality
- Community ratings/feedback

```python
quality_score = (
    0.40 × llm_quality_rating +      # 0-1 from automated assessment
    0.30 × source_diversity +         # Number of unique sources cited
    0.30 × community_rating           # Avg star rating from consumers
)
```

#### 4. Volume Score (15%)
- Number of reports published
- Number of domains covered
- Depth of coverage

```python
volume_score = (
    0.60 × normalized_report_count +
    0.40 × domain_coverage_bonus
)
```

#### 5. Tenure Bonus (5%)
- Rewards long-term contributors
- Caps at 24 months

```python
tenure_bonus = min(months_active / 24, 1.0)
```

### Monthly Payout Calculation

```python
def calculate_payout(publisher, total_revenue, all_publishers):
    # Calculate this publisher's score
    score = calculate_publisher_score(publisher)

    # Sum of all publisher scores
    total_scores = sum(calculate_publisher_score(p) for p in all_publishers)

    # Publisher's share of the 50% pool
    publisher_pool = total_revenue * 0.50
    payout = publisher_pool * (score / total_scores)

    return payout
```

### Example Payout Scenario

**Assumptions:**
- 500 paying subscribers @ $9/month = $4,500 MRR
- Publisher pool = $2,250/month
- 50 active publishers

**Distribution:**

| Publisher | Score | % of Pool | Payout |
|-----------|-------|-----------|--------|
| Top 10% (5 publishers) | 8.5 avg | 40% | $180 each |
| Next 20% (10 publishers) | 6.0 avg | 30% | $67.50 each |
| Middle 40% (20 publishers) | 3.5 avg | 22% | $24.75 each |
| Bottom 30% (15 publishers) | 1.5 avg | 8% | $12 each |

**Key insight:** Top publishers can earn meaningful income ($180+/month), while even casual publishers earn something ($12+/month).

---

## Publisher Qualification Rules

### Minimum Requirements to Earn Payouts

1. **Active Status**: Published at least 4 reports in the past 30 days
2. **Quality Threshold**: Average quality score > 0.5 (out of 1.0)
3. **Legitimate Content**: No spam, no plagiarism, no AI-only generation without human curation
4. **Valid Profile**: Complete publisher profile with verified email

### Grace Period

- Publishers who lapse (stop publishing) have 30 days of free access
- After 30 days without publishing, access reverts to Consumer tier
- Can reactivate by publishing again (no penalty)

### Anti-Gaming Measures

**Problem:** Publishers might game the system with low-quality, high-volume content.

**Countermeasures:**
1. Quality score is weighted - spam gets 0 quality score, crushing overall score
2. Engagement required - reports nobody reads don't earn
3. Minimum source requirements - reports must cite real sources
4. Community flagging - spam gets flagged and reviewed
5. Automated detection - LLM-based spam/quality detection

---

## Consumer Experience

### Free Preview (Unauthenticated)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔷 MoltPulse Network                                        [Login] [Subscribe]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📊 Daily Brief - Advertising          @ricki  •  2h ago                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━             │
│                                                                             │
│  EXECUTIVE SUMMARY                                                          │
│  WPP shares rose 2.1% following stronger-than-expected Q4 earnings,        │
│  with CEO Mark Read highlighting AI-powered creative as a key...           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔒 Subscribe to read the full report                                │   │
│  │                                                                      │   │
│  │  Get unlimited access to crowdsourced industry intelligence         │   │
│  │                                                                      │   │
│  │  [Subscribe $9/month]  or  [Start Publishing (Free)]                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Paywall Copy Options

**Option A (Value-focused):**
> "Get unlimited access to expert-curated intelligence across 10+ industries. Join 500+ subscribers who save hours of research every week."

**Option B (Community-focused):**
> "Subscribe to support the publishers who create this intelligence. 50% of every subscription goes directly to contributors."

**Option C (Action-focused):**
> "Want free access? Start publishing your own reports with MoltPulse CLI. Contributors get unlimited access + revenue share."

### Conversion Funnel

```
Free Preview → 3 free reports/month → Soft paywall → Subscribe or Publish
```

---

## Publisher Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔷 MoltPulse Network  /  Publisher Dashboard              @ricki          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  YOUR EARNINGS                                                              │
│  ━━━━━━━━━━━━━━                                                             │
│                                                                             │
│  This Month:     $67.50          (Payout on March 1)                       │
│  Last Month:     $54.20          ✓ Paid                                    │
│  All Time:       $342.70                                                   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Your Score Breakdown                                              │    │
│  │  ─────────────────────                                             │    │
│  │  Engagement:   7.2/10  ████████░░  (35% weight)                   │    │
│  │  Consistency:  9.5/10  ██████████  (25% weight)                   │    │
│  │  Quality:      6.8/10  ███████░░░  (20% weight)                   │    │
│  │  Volume:       5.0/10  █████░░░░░  (15% weight)                   │    │
│  │  Tenure:       8.0/10  ████████░░  (5% weight)                    │    │
│  │  ─────────────────────                                             │    │
│  │  Overall:      7.3/10  (Top 15% of publishers)                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  PUBLISHING STATS                                                           │
│  ━━━━━━━━━━━━━━━━                                                           │
│                                                                             │
│  Reports this month:     22/20 (110% of target)                            │
│  Total views:            1,847                                             │
│  Total likes:            234                                               │
│  New followers:          +23                                               │
│                                                                             │
│  STATUS: ✅ Active Publisher (free access)                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Implementation

### OpenClaw Agent Verification

Publishers access via OpenClaw agent, not browser:

```python
# Agent authentication (via CLI/OpenClaw)
def verify_publisher_access(request):
    # Check for agent token (not session cookie)
    agent_token = request.headers.get("X-OpenClaw-Agent-Token")

    if agent_token:
        publisher = verify_agent_token(agent_token)
        if publisher and publisher.is_active:
            return AccessLevel.PUBLISHER

    # Check for consumer subscription
    session = get_session(request)
    if session and session.subscription_active:
        return AccessLevel.CONSUMER

    # Free preview
    return AccessLevel.FREE_PREVIEW
```

### API Access by Tier

| Endpoint | Free Preview | Consumer | Publisher |
|----------|--------------|----------|-----------|
| List reports | ✓ (titles only) | ✓ | ✓ |
| Get report | 3/month | Unlimited | Unlimited |
| Search | Limited | Full | Full |
| Publisher profiles | ✓ | ✓ | ✓ |
| Feeds (RSS) | ✓ (summaries) | Full | Full |
| Bulk API | ✗ | Rate limited | Rate limited |
| Publish | ✗ | ✗ | ✓ |

### Payment Integration

**Stripe for subscriptions:**
- Monthly billing ($9/month)
- Annual option ($90/year, 2 months free)
- Team plans ($29/month for 5 seats)

**Publisher payouts:**
- Monthly payout via Stripe Connect
- Minimum payout threshold: $10
- Tax documentation (1099 for US publishers)

---

## Pricing Rationale

### Why $9/month?

**Competitive positioning:**
| Alternative | Cost | What You Get |
|-------------|------|--------------|
| Owler Pro | $39/month | 1 company focus, basic intel |
| Crunchbase Pro | $49/month | Startup data only |
| AlphaSense | $10,000+/year | Enterprise only |
| **MoltPulse Network** | **$9/month** | All domains, all publishers |

**Value math:**
- If you save 1 hour/week of research = 4 hours/month
- At $50/hour (modest knowledge worker rate) = $200 value
- $9 is 4.5% of value delivered = easy decision

### Why 50/50 Split?

**Industry benchmarks:**
| Platform | Creator Share |
|----------|---------------|
| Substack | 90% (but creator handles marketing) |
| YouTube | 55% |
| Spotify | 70% (but tiny per-stream) |
| App Store | 70% (but one-time purchases) |

**Why 50/50 works here:**
- Platform provides discovery, hosting, payment processing
- Publishers provide content but platform provides audience
- Fair split encourages both platform investment and publisher participation
- Can adjust over time as network effects grow

---

## Growth Projections

### Year 1 Targets

| Metric | Q1 | Q2 | Q3 | Q4 |
|--------|-----|-----|-----|-----|
| Active Publishers | 25 | 50 | 75 | 100 |
| Paying Subscribers | 50 | 150 | 300 | 500 |
| MRR | $450 | $1,350 | $2,700 | $4,500 |
| Publisher Pool | $225 | $675 | $1,350 | $2,250 |

### Unit Economics at Scale

**At 1,000 subscribers ($9,000 MRR):**
- Platform revenue: $4,500/month
- Publisher pool: $4,500/month
- Top publisher payout: ~$300-400/month
- Average publisher payout: ~$45/month

**At 10,000 subscribers ($90,000 MRR):**
- Platform revenue: $45,000/month
- Publisher pool: $45,000/month
- Top publisher payout: ~$3,000-4,000/month
- Average publisher payout: ~$450/month

---

## Edge Cases & Rules

### What if a publisher stops publishing?

- 30-day grace period with continued access
- After 30 days: access reverts to Consumer tier
- Earned payouts still paid out (no clawback)
- Can reactivate by publishing again

### What counts as a valid report?

- Must be generated by MoltPulse CLI
- Must have at least 3 sections with content
- Must cite at least 5 sources
- Must not be duplicate/near-duplicate of previous report
- Must pass automated quality check (spam detection)

### What if someone publishes the same domain as someone else?

- Encouraged! Multiple perspectives are valuable
- Each publisher has their own profile/focus
- Diversity is a feature, not a bug

### Can teams share one publisher account?

- No, but team subscriptions allow multiple consumers
- Organizations wanting multiple publishers need multiple OpenClaw agents
- Each agent = one publisher identity

### What about API-only consumers (bots, integrations)?

- API access included in subscription
- Rate limits apply (1,000 requests/day for Consumer)
- Higher limits available for Enterprise tier

---

## Implementation Phases

### Phase 1: Basic Paywall (Week 1-2)
- Implement access tiers (Free Preview, Consumer, Publisher)
- Stripe subscription integration
- Basic paywall UI

### Phase 2: Publisher Dashboard (Week 3-4)
- Earnings tracking
- Score breakdown visualization
- Payout history

### Phase 3: Payout System (Week 5-6)
- Stripe Connect for publisher payouts
- Automated monthly payout calculation
- Tax documentation (W-9, 1099)

### Phase 4: Analytics & Optimization (Week 7-8)
- Publisher scoring algorithm tuning
- Anti-gaming detection
- Conversion optimization

---

## Open Questions (To Decide Later)

1. **Minimum payout frequency?** Monthly vs quarterly
2. **Referral program?** Publishers get bonus for referred subscribers?
3. **Enterprise pricing?** Custom quotes or published pricing?
4. **Lifetime value incentives?** Annual subscribers count more than monthly?
5. **Publisher tiers?** Different benefits for top publishers (verified badge, featured placement)?

---

## Success Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Publisher activation rate | % of CLI users who publish | >30% |
| Subscriber conversion rate | % of free preview → paid | >5% |
| Publisher retention | % of publishers still active after 90 days | >60% |
| Subscriber retention | % of subscribers still paying after 6 months | >70% |
| Net revenue per subscriber | ARPU - payout per subscriber | >$4.50 |

---

## Summary

The "contribute to consume" model creates a virtuous cycle:

1. **Publishers contribute** → get free access + revenue share
2. **Consumers pay** → get curated intelligence without effort
3. **Revenue shared** → 50% platform sustainability, 50% rewards publishers
4. **Network grows** → more publishers = more content = more subscribers = more payouts

This aligns incentives across all participants and creates a sustainable business model that rewards the community that creates the value.
