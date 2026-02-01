# Moltos

Domain-agnostic industry intelligence framework for OpenClaw.

## Installation

```bash
uv sync
```

## Usage

```bash
# Run daily brief for advertising domain
uv run moltos --domain=advertising --profile=ricki daily

# Run weekly digest
uv run moltos --domain=advertising --profile=ricki weekly

# Run fundraising outlook
uv run moltos --domain=advertising --profile=ricki fundraising --deep
```

## Configuration

See `domains/` for available domain instances and `profiles/` for interest profiles.
