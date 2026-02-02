# Profiles

A **profile** defines what a SPECIFIC USER cares about within a domain. It personalizes the monitoring experience by filtering entities, tracking thought leaders, and configuring delivery.

## Profile Concept

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

## Working with Profiles

### List Profiles

```bash
moltpulse profile list advertising
```

### Show Profile Details

```bash
moltpulse profile show advertising ricki
```

### Show Profile as YAML

```bash
moltpulse profile show advertising ricki --yaml
```

### Validate Profile

```bash
moltpulse profile validate advertising ricki
```

## Creating a Profile

### Quick Create via CLI

```bash
moltpulse profile create advertising myname \
  --extends default \
  --focus-entities "holding_companies:WPP,OMC,PUBGY" \
  --thought-leader "Scott Galloway:profgalloway:1" \
  --thought-leader "Seth Godin:ThisIsSethsBlog:1" \
  --publications "Ad Age,AdWeek,Campaign" \
  --enable-reports "daily_brief,weekly_digest" \
  --keywords-boost "AI,automation,sustainability" \
  --delivery-channel email \
  --delivery-email "me@example.com"
```

### Full YAML Configuration

For complex configurations, edit the YAML file directly:

```yaml
# domains/advertising/profiles/myname.yaml
profile_name: myname
extends: default

# Entity focus - prioritize specific companies
focus:
  holding_companies:
    priority_1: [WPP, OMC]      # Most important
    priority_2: [PUBGY, IPG]    # Secondary
    exclude: [DNTUY]            # Ignore these

  agency_types:
    primary: [creative, media, technology]
    secondary: [ad_tech]

  geographic: [United States, United Kingdom]

# Thought leaders to track on X/Twitter
thought_leaders:
  - name: "Scott Galloway"
    x_handle: "profgalloway"
    priority: 1

  - name: "Seth Godin"
    x_handle: "ThisIsSethsBlog"
    priority: 1

  - name: "Gary Vaynerchuk"
    x_handle: "garyvee"
    priority: 2

# Publications to include (subset of domain publications)
publications:
  - Ad Age
  - AdWeek
  - Campaign
  - The Drum
  - Marketing Week

# Which reports to enable
reports:
  daily_brief: true
  weekly_digest: true
  fundraising: false

# Keywords for relevance boosting/filtering
keywords:
  boost:
    - AI
    - automation
    - sustainability
    - purpose-driven
    - DEI

  filter:
    - spam
    - clickbait

# Delivery configuration
delivery:
  channel: email
  email:
    to: "me@example.com"
    subject_prefix: "[MoltPulse]"
    format: html

  fallback:
    channel: file
    path: "~/.moltpulse/reports/"
```

## Profile Inheritance

Profiles can extend other profiles:

```yaml
profile_name: tech_focus
extends: ricki    # Inherits all of ricki's config

# Only override what's different
focus:
  agency_types:
    primary: [technology, ad_tech]

keywords:
  boost:
    - AI
    - machine learning
    - programmatic
```

The merge is deep - nested dictionaries are merged, lists are replaced.

## Updating Profiles

### Add Thought Leader

```bash
moltpulse profile update advertising myname \
  --add-thought-leader "New Leader:handle:2"
```

### Add Publication

```bash
moltpulse profile update advertising myname \
  --add-publication "Marketing Week"
```

### Add Boost Keyword

```bash
moltpulse profile update advertising myname \
  --add-keyword-boost "metaverse"
```

### Change Delivery

```bash
moltpulse profile update advertising myname \
  --set-delivery-channel email \
  --set-delivery-email "newemail@example.com"
```

## Delivery Channels

### Console (Default)

```yaml
delivery:
  channel: console
```

Output goes to stdout. Best for testing and CLI usage.

### File

```yaml
delivery:
  channel: file
  file:
    path: "~/moltpulse-reports"
    format: json  # or html, markdown
```

Reports saved to disk with timestamped filenames.

### Email

```yaml
delivery:
  channel: email
  email:
    to: "user@example.com"
    subject_prefix: "[MoltPulse]"
    format: html  # or text
```

Requires SMTP configuration via environment variables:
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

### Fallback Delivery

Configure a backup channel in case primary fails:

```yaml
delivery:
  channel: email
  email:
    to: "user@example.com"

  fallback:
    channel: file
    path: "~/.moltpulse/reports/"
```

## Priority System

Thought leaders and entities can have priorities (1 = highest):

```yaml
thought_leaders:
  - {name: "Scott Galloway", x_handle: "profgalloway", priority: 1}
  - {name: "Gary Vee", x_handle: "garyvee", priority: 2}
  - {name: "Industry Blogger", x_handle: "blogger", priority: 3}
```

Priority affects:
- Order in reports
- Weight in relevance scoring
- Collection depth allocation

## Common Patterns

### Minimal Profile

```yaml
profile_name: quick
extends: default
delivery:
  channel: console
```

### Email-Focused Profile

```yaml
profile_name: email_digest
extends: default

publications:
  - Ad Age
  - AdWeek

delivery:
  channel: email
  email:
    to: "team@company.com"
    subject_prefix: "[Daily Ad Intel]"
    format: html
```

### Research Profile

```yaml
profile_name: deep_research
extends: default

# Track more leaders
thought_leaders:
  - {name: "Academic 1", x_handle: "prof1", priority: 1}
  - {name: "Academic 2", x_handle: "prof2", priority: 1}
  # ... many more

# All publications
publications:
  - Ad Age
  - AdWeek
  - Campaign
  - The Drum
  - Marketing Week
  - Forbes
  - HBR

# Many boost keywords
keywords:
  boost:
    - research
    - study
    - analysis
    - trends
    - forecast
```
