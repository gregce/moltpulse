"""Domain management CLI commands."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from ..domain_loader import (
    DomainConfig,
    create_domain_skeleton,
    find_domains_dir,
    list_domains,
    load_domain,
    validate_domain,
)


def add_domain_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add domain management commands to parser."""
    domain_parser = subparsers.add_parser(
        "domain",
        help="Manage domain instances",
    )

    domain_subparsers = domain_parser.add_subparsers(dest="domain_action")

    # domain create
    create_parser = domain_subparsers.add_parser(
        "create",
        help="Create a new domain instance",
    )
    create_parser.add_argument(
        "name",
        help="Domain name (e.g., healthcare, fintech)",
    )
    create_parser.add_argument(
        "--display-name",
        help="Display name for the domain",
    )
    create_parser.add_argument(
        "--entity-type",
        action="append",
        dest="entity_types",
        metavar="NAME:SYMBOLS",
        help="Add entity type with symbols (e.g., 'pharma:PFE,JNJ,MRK')",
    )
    create_parser.add_argument(
        "--collector",
        action="append",
        dest="collectors",
        metavar="TYPE:MODULE",
        help="Add collector (e.g., 'financial:collectors.financial')",
    )
    create_parser.add_argument(
        "--publication",
        action="append",
        dest="publications",
        metavar="NAME:RSS_URL",
        help="Add publication with RSS feed",
    )
    create_parser.add_argument(
        "--report",
        action="append",
        dest="reports",
        metavar="TYPE:MODULE",
        help="Add report type (e.g., 'daily_brief:domains.myindustry.reports.daily_brief')",
    )
    create_parser.set_defaults(func=cmd_domain_create)

    # domain update
    update_parser = domain_subparsers.add_parser(
        "update",
        help="Update an existing domain",
    )
    update_parser.add_argument(
        "name",
        help="Domain name to update",
    )
    update_parser.add_argument(
        "--add-entity",
        action="append",
        dest="add_entities",
        metavar="TYPE:SYMBOL:NAME",
        help="Add entity (e.g., 'holding_companies:NEWCO:New Company Inc')",
    )
    update_parser.add_argument(
        "--add-collector",
        action="append",
        dest="add_collectors",
        metavar="TYPE:MODULE",
        help="Add collector",
    )
    update_parser.add_argument(
        "--add-publication",
        action="append",
        dest="add_publications",
        metavar="NAME:RSS_URL",
        help="Add publication",
    )
    update_parser.add_argument(
        "--add-report",
        action="append",
        dest="add_reports",
        metavar="TYPE:MODULE",
        help="Add report type",
    )
    update_parser.set_defaults(func=cmd_domain_update)

    # domain list
    list_parser = domain_subparsers.add_parser(
        "list",
        help="List available domains",
    )
    list_parser.set_defaults(func=cmd_domain_list)

    # domain show
    show_parser = domain_subparsers.add_parser(
        "show",
        help="Show domain details",
    )
    show_parser.add_argument(
        "name",
        help="Domain name to show",
    )
    show_parser.add_argument(
        "--yaml",
        action="store_true",
        help="Output as YAML",
    )
    show_parser.set_defaults(func=cmd_domain_show)

    # domain validate
    validate_parser = domain_subparsers.add_parser(
        "validate",
        help="Validate domain configuration",
    )
    validate_parser.add_argument(
        "name",
        help="Domain name to validate",
    )
    validate_parser.set_defaults(func=cmd_domain_validate)


def cmd_domain_create(args: argparse.Namespace) -> int:
    """Create a new domain."""
    # Check if domain already exists
    existing = list_domains()
    if args.name in existing:
        print(f"Error: Domain '{args.name}' already exists")
        return 1

    # Create skeleton
    domain_path = create_domain_skeleton(args.name, args.display_name)
    config_file = domain_path / "domain.yaml"

    # Load and update with provided options
    with open(config_file, "r") as f:
        config = yaml.safe_load(f) or {}

    # Add entity types
    if args.entity_types:
        for et in args.entity_types:
            if ":" not in et:
                print(f"Warning: Invalid entity-type format: {et} (expected NAME:SYMBOLS)")
                continue
            type_name, symbols = et.split(":", 1)
            entities = []
            for symbol in symbols.split(","):
                symbol = symbol.strip()
                if symbol:
                    entities.append({"symbol": symbol, "name": ""})
            config.setdefault("entity_types", {})[type_name] = entities

    # Add collectors
    if args.collectors:
        for c in args.collectors:
            if ":" not in c:
                print(f"Warning: Invalid collector format: {c} (expected TYPE:MODULE)")
                continue
            ctype, module = c.split(":", 1)
            config.setdefault("collectors", []).append({
                "type": ctype,
                "module": module,
            })

    # Add publications
    if args.publications:
        for p in args.publications:
            if ":" not in p:
                print(f"Warning: Invalid publication format: {p} (expected NAME:RSS_URL)")
                continue
            name, rss = p.split(":", 1)
            config.setdefault("publications", []).append({
                "name": name,
                "rss": rss,
            })

    # Add reports
    if args.reports:
        for r in args.reports:
            if ":" not in r:
                print(f"Warning: Invalid report format: {r} (expected TYPE:MODULE)")
                continue
            rtype, module = r.split(":", 1)
            config.setdefault("reports", []).append({
                "type": rtype,
                "module": module,
            })

    # Write updated config
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"Created domain: {args.name}")
    print(f"  Path: {domain_path}")
    print(f"  Config: {config_file}")
    print(f"\nNext steps:")
    print(f"  1. Edit {config_file} to customize the domain")
    print(f"  2. Create collectors in {domain_path}/collectors/")
    print(f"  3. Create reports in {domain_path}/reports/")
    print(f"  4. Create profiles with: moltpulse profile create {args.name} <profile_name>")

    return 0


def cmd_domain_update(args: argparse.Namespace) -> int:
    """Update an existing domain."""
    try:
        domain = load_domain(args.name)
    except FileNotFoundError:
        print(f"Error: Domain '{args.name}' not found")
        return 1

    config_file = domain.domain_path / "domain.yaml"

    # Load current config
    with open(config_file, "r") as f:
        config = yaml.safe_load(f) or {}

    changed = False

    # Add entities
    if args.add_entities:
        for e in args.add_entities:
            parts = e.split(":")
            if len(parts) < 2:
                print(f"Warning: Invalid entity format: {e} (expected TYPE:SYMBOL:NAME)")
                continue
            type_name = parts[0]
            symbol = parts[1]
            name = parts[2] if len(parts) > 2 else ""

            entities = config.setdefault("entity_types", {}).setdefault(type_name, [])
            # Check if already exists
            if not any(ent.get("symbol") == symbol for ent in entities):
                entities.append({"symbol": symbol, "name": name})
                print(f"Added entity: {symbol} to {type_name}")
                changed = True
            else:
                print(f"Entity {symbol} already exists in {type_name}")

    # Add collectors
    if args.add_collectors:
        for c in args.add_collectors:
            if ":" not in c:
                print(f"Warning: Invalid collector format: {c}")
                continue
            ctype, module = c.split(":", 1)
            collectors = config.setdefault("collectors", [])
            if not any(col.get("type") == ctype for col in collectors):
                collectors.append({"type": ctype, "module": module})
                print(f"Added collector: {ctype}")
                changed = True
            else:
                print(f"Collector {ctype} already exists")

    # Add publications
    if args.add_publications:
        for p in args.add_publications:
            if ":" not in p:
                print(f"Warning: Invalid publication format: {p}")
                continue
            name, rss = p.split(":", 1)
            pubs = config.setdefault("publications", [])
            if not any(pub.get("name") == name for pub in pubs):
                pubs.append({"name": name, "rss": rss})
                print(f"Added publication: {name}")
                changed = True
            else:
                print(f"Publication {name} already exists")

    # Add reports
    if args.add_reports:
        for r in args.add_reports:
            if ":" not in r:
                print(f"Warning: Invalid report format: {r}")
                continue
            rtype, module = r.split(":", 1)
            reports = config.setdefault("reports", [])
            if not any(rep.get("type") == rtype for rep in reports):
                reports.append({"type": rtype, "module": module})
                print(f"Added report: {rtype}")
                changed = True
            else:
                print(f"Report {rtype} already exists")

    if changed:
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"\nUpdated domain: {args.name}")
    else:
        print("No changes made")

    return 0


def cmd_domain_list(args: argparse.Namespace) -> int:
    """List available domains."""
    domains = list_domains()

    if not domains:
        print("No domains found")
        print("Create one with: moltpulse domain create <name>")
        return 0

    print("Available domains:")
    for d in domains:
        try:
            config = load_domain(d)
            display = config.display_name or d
            entity_count = sum(len(v) for v in config.entity_types.values())
            collector_count = len(config.collectors)
            print(f"  {d}: {display} ({entity_count} entities, {collector_count} collectors)")
        except Exception:
            print(f"  {d}: (failed to load)")

    return 0


def cmd_domain_show(args: argparse.Namespace) -> int:
    """Show domain details."""
    try:
        domain = load_domain(args.name)
    except FileNotFoundError:
        print(f"Error: Domain '{args.name}' not found")
        return 1

    if args.yaml:
        with open(domain.domain_path / "domain.yaml", "r") as f:
            print(f.read())
        return 0

    print(f"Domain: {domain.name}")
    print(f"Display Name: {domain.display_name}")
    print(f"Path: {domain.domain_path}")
    print()

    print("Entity Types:")
    for type_name, entities in domain.entity_types.items():
        symbols = [e.get("symbol", "") for e in entities[:5]]
        suffix = f" (+{len(entities) - 5} more)" if len(entities) > 5 else ""
        print(f"  {type_name}: {', '.join(symbols)}{suffix}")
    print()

    print("Collectors:")
    for c in domain.collectors:
        print(f"  - {c.get('type')}: {c.get('module')}")
    print()

    print("Publications:")
    for p in domain.publications[:5]:
        print(f"  - {p.get('name')}")
    if len(domain.publications) > 5:
        print(f"  ... and {len(domain.publications) - 5} more")
    print()

    print("Reports:")
    for r in domain.reports:
        print(f"  - {r.get('type')}: {r.get('module')}")

    return 0


def cmd_domain_validate(args: argparse.Namespace) -> int:
    """Validate domain configuration."""
    try:
        domain = load_domain(args.name)
    except FileNotFoundError:
        print(f"Error: Domain '{args.name}' not found")
        return 1
    except ValueError as e:
        print(f"Error: Invalid YAML in domain config: {e}")
        return 1

    errors = validate_domain(domain)

    if errors:
        print(f"Validation failed for domain '{args.name}':")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Domain '{args.name}' is valid")
    return 0
