# Run Execution Monitoring

MoltPulse provides visibility into run execution through progress spinners and execution traces.

## Progress Display

When running a report, MoltPulse shows real-time progress with thread-safe output:

```bash
$ moltpulse run --domain=advertising --profile=ricki daily

⠹ Alpha Vantage Financial...
✓ Alpha Vantage Financial: 5 items (6.2s)
⠸ RSS Feed...
✓ RSS Feed: 12 items (0.3s)
⠼ NewsData...
✓ NewsData: 15 items (0.8s)
⠴ X Social...
✓ X Social: 6 items (2.0s)

✓ Run complete (6.5s) - 38 items collected
```

Note: Financial collector takes longer due to Alpha Vantage rate limiting (1.2s between requests).

In non-TTY environments (like OpenClaw or Claude Code), static progress is shown:

```
⏳ Alpha Vantage Financial...
✓ Alpha Vantage Financial: 5 items (6.2s)
⏳ RSS Feed...
✓ RSS Feed: 12 items (0.3s)
```

Progress output is thread-safe - parallel collectors won't corrupt the display.

## Run Tracing

For detailed execution information, use the `--trace` flag:

```bash
moltpulse run --domain=advertising --profile=ricki --trace daily
```

This outputs a trace summary:

```
Run: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Domain: advertising | Profile: ricki | Report: daily_brief

Collectors:
├── RSS Feed
│   ├── Duration: 312ms
│   ├── Items: 12
│   └── API Calls: 0 (RSS feeds)
├── Alpha Vantage Financial
│   ├── Duration: 1,142ms
│   ├── Items: 8
│   └── API Calls: 2
│       ├── GET https://api.alphavantage.co/... (200, 234ms)
│       └── GET https://api.alphavantage.co/... (200, 189ms)
├── NewsData
│   ├── Duration: 823ms
│   ├── Items: 15
│   └── API Calls: 1
│       └── GET https://newsdata.io/api/... (200, 756ms)
└── X Social
    ├── Duration: 2,034ms
    ├── Items: 6
    └── API Calls: 1
        └── POST https://api.x.ai/... (200, 1,892ms)

Processing:
├── Total collected: 41 items
├── After filter: 38 items
├── After dedupe: 35 items
└── Final score range: 0.42 - 0.89

Delivery:
├── Channel: console
└── Status: success

Total Duration: 4,234ms
```

## JSON Trace Output

For programmatic access (OpenClaw integration), output trace as JSON:

```bash
moltpulse run --domain=advertising --profile=ricki \
  --trace --output=json --no-deliver daily
```

```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "domain": "advertising",
  "profile": "ricki",
  "report_type": "daily_brief",
  "depth": "default",
  "started_at": "2024-01-15T09:00:00Z",
  "ended_at": "2024-01-15T09:00:04Z",
  "duration_ms": 4234,
  "collectors": [
    {
      "name": "RSS Feed",
      "type": "rss",
      "started_at": "2024-01-15T09:00:00Z",
      "ended_at": "2024-01-15T09:00:00Z",
      "duration_ms": 312,
      "items_collected": 12,
      "items_after_filter": 11,
      "api_calls": [],
      "success": true,
      "error": null
    },
    {
      "name": "Alpha Vantage Financial",
      "type": "financial",
      "duration_ms": 1142,
      "items_collected": 8,
      "api_calls": [
        {
          "endpoint": "https://api.alphavantage.co/query",
          "method": "GET",
          "status": 200,
          "latency_ms": 234,
          "cached": false
        }
      ],
      "success": true
    }
  ],
  "delivery": {
    "channel": "console",
    "success": true,
    "duration_ms": 12
  }
}
```

## Preflight Check

Before running collectors, check availability:

```bash
moltpulse run --domain=advertising --profile=ricki --dry-run daily
```

Output includes collector status:

```
Collector Status:
  ✓ RSS Feed (rss)
  ✓ Alpha Vantage Financial (financial)
  ✗ NewsData (missing: NEWSDATA_API_KEY)
  ✗ X Social (missing: XAI_API_KEY)
  ✓ Advertising Awards (awards)
  ✗ PE & M&A Activity (needs one of: INTELLIZENCE_API_KEY or NEWSDATA_API_KEY)
```

## OpenClaw Integration

When running under OpenClaw orchestration:

```bash
# OpenClaw calls MoltPulse with:
moltpulse run --domain=advertising --profile=ricki \
  --trace --output=json --no-deliver daily
```

This returns:
- Report data as JSON
- Execution trace for monitoring
- No direct delivery (OpenClaw handles it)

OpenClaw can aggregate traces across scheduled runs to:
- Track API usage over time
- Identify slow collectors
- Monitor success/failure rates
- Optimize scheduling

## Error Handling

Collector errors are captured in the trace:

```json
{
  "name": "NewsData",
  "type": "news",
  "success": false,
  "error": "API rate limit exceeded",
  "api_calls": [
    {
      "endpoint": "https://newsdata.io/api/...",
      "status": 429,
      "error": "Rate limited"
    }
  ]
}
```

The run continues with available collectors - one failure doesn't stop others.

## Debug Mode

Enable verbose output to troubleshoot issues:

```bash
MOLTPULSE_DEBUG=true moltpulse run --domain=advertising daily
```

Debug output includes:
- API request/response details
- Rate limiting events and delays
- Collector selection decisions (priority, availability)
- LLM backend detection
- Entity matching details

## Rate Limiting

MoltPulse handles API rate limits automatically:

| API | Limit | Handling |
|-----|-------|----------|
| Alpha Vantage (free) | 1 req/sec, 25/day | 1.2s delay between requests |
| NewsData.io | 200 req/day | Batched queries |

Rate-limited requests appear in traces:

```json
{
  "name": "Alpha Vantage Financial",
  "api_calls": [
    {"endpoint": "...", "status": 200, "latency_ms": 234},
    {"endpoint": "...", "status": 429, "error": "Rate limited"}
  ]
}
```

Use `--quick` to reduce API calls:

```bash
# Quick mode: 3 stock symbols max vs 5 in default
moltpulse run --domain=advertising --quick daily
```

## Performance Tips

1. **Use `--quick` for testing**: Faster execution, fewer API calls
2. **Check preflight first**: `--dry-run` shows what will work
3. **Monitor API calls**: `--trace` reveals bottlenecks
4. **Configure fallbacks**: Email delivery can fall back to file
5. **Watch rate limits**: Alpha Vantage free tier is very limited (25/day)

## Trace Schema Reference

### RunTrace

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique run identifier (UUID) |
| `domain` | string | Domain name |
| `profile` | string | Profile name |
| `report_type` | string | Report type (daily_brief, etc.) |
| `depth` | string | Collection depth (quick, default, deep) |
| `started_at` | string | ISO8601 start timestamp |
| `ended_at` | string | ISO8601 end timestamp |
| `duration_ms` | int | Total duration in milliseconds |
| `collectors` | array | List of CollectorTrace objects |
| `delivery` | object | DeliveryTrace object |

### CollectorTrace

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Collector display name |
| `type` | string | Collector type (financial, news, etc.) |
| `started_at` | string | ISO8601 start timestamp |
| `ended_at` | string | ISO8601 end timestamp |
| `duration_ms` | int | Duration in milliseconds |
| `items_collected` | int | Raw items collected |
| `items_after_filter` | int | Items after date/relevance filter |
| `api_calls` | array | List of APICall objects |
| `success` | bool | Whether collection succeeded |
| `error` | string | Error message if failed |

### APICall

| Field | Type | Description |
|-------|------|-------------|
| `endpoint` | string | API endpoint URL |
| `method` | string | HTTP method (GET, POST) |
| `status` | int | HTTP status code |
| `latency_ms` | int | Request latency in milliseconds |
| `cached` | bool | Whether served from cache |
| `error` | string | Error message if failed |
