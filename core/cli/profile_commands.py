"""Profile management CLI commands."""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..domain_loader import load_domain, list_domains
from ..profile_loader import (
    ProfileConfig,
    create_profile,
    list_profiles,
    load_profile,
    validate_profile,
)


def add_profile_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add profile management commands to parser."""
    profile_parser = subparsers.add_parser(
        "profile",
        help="Manage interest profiles",
    )

    profile_subparsers = profile_parser.add_subparsers(dest="profile_action")

    # profile create
    create_parser = profile_subparsers.add_parser(
        "create",
        help="Create a new profile",
    )
    create_parser.add_argument(
        "domain",
        help="Domain to create profile in",
    )
    create_parser.add_argument(
        "name",
        help="Profile name",
    )
    create_parser.add_argument(
        "--extends",
        default="default",
        help="Base profile to extend (default: default)",
    )
    create_parser.add_argument(
        "--focus-entities",
        action="append",
        dest="focus_entities",
        metavar="TYPE:SYMBOLS",
        help="Focus on specific entities (e.g., 'holding_companies:WPP,OMC')",
    )
    create_parser.add_argument(
        "--thought-leader",
        action="append",
        dest="thought_leaders",
        metavar="NAME:HANDLE:PRIORITY",
        help="Add thought leader (e.g., 'Scott Galloway:profgalloway:1')",
    )
    create_parser.add_argument(
        "--publications",
        help="Comma-separated list of publication names",
    )
    create_parser.add_argument(
        "--enable-reports",
        help="Comma-separated list of report types to enable",
    )
    create_parser.add_argument(
        "--keywords-boost",
        help="Comma-separated keywords to boost",
    )
    create_parser.add_argument(
        "--delivery-channel",
        choices=["email", "file", "console", "whatsapp", "slack"],
        help="Primary delivery channel",
    )
    create_parser.add_argument(
        "--delivery-email",
        help="Email address for email delivery",
    )
    create_parser.set_defaults(func=cmd_profile_create)

    # profile update
    update_parser = profile_subparsers.add_parser(
        "update",
        help="Update an existing profile",
    )
    update_parser.add_argument(
        "domain",
        help="Domain containing the profile",
    )
    update_parser.add_argument(
        "name",
        help="Profile name to update",
    )
    update_parser.add_argument(
        "--add-thought-leader",
        action="append",
        dest="add_thought_leaders",
        metavar="NAME:HANDLE:PRIORITY",
        help="Add thought leader",
    )
    update_parser.add_argument(
        "--add-publication",
        action="append",
        dest="add_publications",
        help="Add publication to track",
    )
    update_parser.add_argument(
        "--add-keyword-boost",
        action="append",
        dest="add_keywords_boost",
        help="Add keyword to boost",
    )
    update_parser.add_argument(
        "--set-delivery-channel",
        dest="delivery_channel",
        choices=["email", "file", "console", "whatsapp", "slack"],
        help="Set delivery channel",
    )
    update_parser.add_argument(
        "--set-delivery-email",
        dest="delivery_email",
        help="Set email address for delivery",
    )
    update_parser.set_defaults(func=cmd_profile_update)

    # profile list
    list_parser = profile_subparsers.add_parser(
        "list",
        help="List profiles in a domain",
    )
    list_parser.add_argument(
        "domain",
        help="Domain to list profiles from",
    )
    list_parser.set_defaults(func=cmd_profile_list)

    # profile show
    show_parser = profile_subparsers.add_parser(
        "show",
        help="Show profile details",
    )
    show_parser.add_argument(
        "domain",
        help="Domain containing the profile",
    )
    show_parser.add_argument(
        "name",
        help="Profile name to show",
    )
    show_parser.add_argument(
        "--yaml",
        action="store_true",
        help="Output as YAML",
    )
    show_parser.set_defaults(func=cmd_profile_show)

    # profile validate
    validate_parser = profile_subparsers.add_parser(
        "validate",
        help="Validate profile configuration",
    )
    validate_parser.add_argument(
        "domain",
        help="Domain containing the profile",
    )
    validate_parser.add_argument(
        "name",
        help="Profile name to validate",
    )
    validate_parser.set_defaults(func=cmd_profile_validate)


def cmd_profile_create(args: argparse.Namespace) -> int:
    """Create a new profile."""
    # Load domain
    try:
        domain = load_domain(args.domain)
    except FileNotFoundError:
        print(f"Error: Domain '{args.domain}' not found")
        return 1

    # Check if profile already exists
    existing = list_profiles(args.domain)
    if args.name in existing:
        print(f"Error: Profile '{args.name}' already exists in domain '{args.domain}'")
        return 1

    # Build profile data
    profile_data: Dict[str, Any] = {
        "profile_name": args.name,
        "extends": args.extends,
        "focus": {},
        "thought_leaders": [],
        "publications": [],
        "reports": {},
        "keywords": {"boost": [], "filter": []},
        "delivery": {"channel": "file"},
    }

    # Parse focus entities
    if args.focus_entities:
        for fe in args.focus_entities:
            if ":" not in fe:
                print(f"Warning: Invalid focus-entities format: {fe}")
                continue
            type_name, symbols = fe.split(":", 1)
            profile_data["focus"].setdefault(type_name, {})["priority_1"] = [
                s.strip() for s in symbols.split(",") if s.strip()
            ]

    # Parse thought leaders
    if args.thought_leaders:
        for tl in args.thought_leaders:
            parts = tl.split(":")
            if len(parts) < 2:
                print(f"Warning: Invalid thought-leader format: {tl}")
                continue
            leader = {
                "name": parts[0],
                "x_handle": parts[1],
                "priority": int(parts[2]) if len(parts) > 2 else 2,
            }
            profile_data["thought_leaders"].append(leader)

    # Parse publications
    if args.publications:
        profile_data["publications"] = [
            p.strip() for p in args.publications.split(",") if p.strip()
        ]

    # Parse enabled reports
    if args.enable_reports:
        for r in args.enable_reports.split(","):
            r = r.strip()
            if r:
                profile_data["reports"][r] = True

    # Parse boost keywords
    if args.keywords_boost:
        profile_data["keywords"]["boost"] = [
            k.strip() for k in args.keywords_boost.split(",") if k.strip()
        ]

    # Set delivery
    if args.delivery_channel:
        profile_data["delivery"]["channel"] = args.delivery_channel

    if args.delivery_email:
        profile_data["delivery"]["email"] = {
            "to": args.delivery_email,
            "subject_prefix": "[Moltos]",
            "format": "html",
        }

    # Write profile
    profile_path = domain.domain_path / "profiles" / f"{args.name}.yaml"
    profile_path.parent.mkdir(exist_ok=True)

    with open(profile_path, "w") as f:
        yaml.dump(profile_data, f, default_flow_style=False, sort_keys=False)

    print(f"Created profile: {args.name}")
    print(f"  Domain: {args.domain}")
    print(f"  Path: {profile_path}")
    print(f"\nRun with: moltos --domain={args.domain} --profile={args.name} daily")

    return 0


def cmd_profile_update(args: argparse.Namespace) -> int:
    """Update an existing profile."""
    try:
        domain = load_domain(args.domain)
    except FileNotFoundError:
        print(f"Error: Domain '{args.domain}' not found")
        return 1

    profile_path = domain.domain_path / "profiles" / f"{args.name}.yaml"
    if not profile_path.exists():
        print(f"Error: Profile '{args.name}' not found in domain '{args.domain}'")
        return 1

    # Load current profile
    with open(profile_path, "r") as f:
        profile_data = yaml.safe_load(f) or {}

    changed = False

    # Add thought leaders
    if args.add_thought_leaders:
        leaders = profile_data.setdefault("thought_leaders", [])
        for tl in args.add_thought_leaders:
            parts = tl.split(":")
            if len(parts) < 2:
                print(f"Warning: Invalid thought-leader format: {tl}")
                continue
            leader = {
                "name": parts[0],
                "x_handle": parts[1],
                "priority": int(parts[2]) if len(parts) > 2 else 2,
            }
            # Check if already exists
            if not any(l.get("x_handle") == leader["x_handle"] for l in leaders):
                leaders.append(leader)
                print(f"Added thought leader: {parts[0]} (@{parts[1]})")
                changed = True
            else:
                print(f"Thought leader @{parts[1]} already exists")

    # Add publications
    if args.add_publications:
        pubs = profile_data.setdefault("publications", [])
        for pub in args.add_publications:
            if pub not in pubs:
                pubs.append(pub)
                print(f"Added publication: {pub}")
                changed = True
            else:
                print(f"Publication {pub} already exists")

    # Add boost keywords
    if args.add_keywords_boost:
        keywords = profile_data.setdefault("keywords", {}).setdefault("boost", [])
        for kw in args.add_keywords_boost:
            if kw not in keywords:
                keywords.append(kw)
                print(f"Added boost keyword: {kw}")
                changed = True
            else:
                print(f"Keyword {kw} already in boost list")

    # Set delivery channel
    if args.delivery_channel:
        profile_data.setdefault("delivery", {})["channel"] = args.delivery_channel
        print(f"Set delivery channel: {args.delivery_channel}")
        changed = True

    # Set delivery email
    if args.delivery_email:
        profile_data.setdefault("delivery", {}).setdefault("email", {})["to"] = args.delivery_email
        print(f"Set delivery email: {args.delivery_email}")
        changed = True

    if changed:
        with open(profile_path, "w") as f:
            yaml.dump(profile_data, f, default_flow_style=False, sort_keys=False)
        print(f"\nUpdated profile: {args.name}")
    else:
        print("No changes made")

    return 0


def cmd_profile_list(args: argparse.Namespace) -> int:
    """List profiles in a domain."""
    try:
        domain = load_domain(args.domain)
    except FileNotFoundError:
        print(f"Error: Domain '{args.domain}' not found")
        return 1

    profiles = list_profiles(args.domain)

    if not profiles:
        print(f"No profiles found in domain '{args.domain}'")
        print(f"Create one with: moltos profile create {args.domain} <name>")
        return 0

    print(f"Profiles in '{args.domain}':")
    for p in profiles:
        try:
            profile = load_profile(domain, p)
            leader_count = len(profile.thought_leaders)
            pub_count = len(profile.publications)
            delivery = profile.get_delivery_channel()
            print(f"  {p}: {leader_count} thought leaders, {pub_count} publications, delivery: {delivery}")
        except Exception:
            print(f"  {p}: (failed to load)")

    return 0


def cmd_profile_show(args: argparse.Namespace) -> int:
    """Show profile details."""
    try:
        domain = load_domain(args.domain)
    except FileNotFoundError:
        print(f"Error: Domain '{args.domain}' not found")
        return 1

    profile_path = domain.domain_path / "profiles" / f"{args.name}.yaml"
    if not profile_path.exists():
        print(f"Error: Profile '{args.name}' not found in domain '{args.domain}'")
        return 1

    if args.yaml:
        with open(profile_path, "r") as f:
            print(f.read())
        return 0

    try:
        profile = load_profile(domain, args.name)
    except Exception as e:
        print(f"Error loading profile: {e}")
        return 1

    print(f"Profile: {profile.name}")
    print(f"Domain: {domain.name}")
    if profile.extends:
        print(f"Extends: {profile.extends}")
    print()

    print("Focus:")
    for type_name, focus_value in profile.focus.items():
        if isinstance(focus_value, dict):
            # Handle dict-based focus (priority_1, priority_2, primary, secondary, etc.)
            for key, values in focus_value.items():
                if isinstance(values, list) and values:
                    print(f"  {type_name} ({key}): {', '.join(str(v) for v in values[:5])}")
        elif isinstance(focus_value, list):
            # Handle list-based focus (e.g., geographic)
            if focus_value:
                print(f"  {type_name}: {', '.join(str(v) for v in focus_value[:5])}")
    print()

    print("Thought Leaders:")
    for tl in profile.thought_leaders[:10]:
        priority = tl.get("priority", 3)
        print(f"  [{priority}] {tl.get('name')} (@{tl.get('x_handle')})")
    if len(profile.thought_leaders) > 10:
        print(f"  ... and {len(profile.thought_leaders) - 10} more")
    print()

    print("Publications:")
    for pub in profile.publications[:5]:
        print(f"  - {pub}")
    if len(profile.publications) > 5:
        print(f"  ... and {len(profile.publications) - 5} more")
    print()

    print("Reports:")
    for rtype, enabled in profile.reports.items():
        status = "enabled" if enabled else "disabled"
        print(f"  {rtype}: {status}")
    print()

    print("Keywords:")
    boost = profile.get_boost_keywords()
    if boost:
        print(f"  Boost: {', '.join(boost[:5])}")
    filter_kw = profile.get_filter_keywords()
    if filter_kw:
        print(f"  Filter: {', '.join(filter_kw[:5])}")
    print()

    print("Delivery:")
    print(f"  Channel: {profile.get_delivery_channel()}")
    delivery_config = profile.get_delivery_config()
    for key, value in delivery_config.items():
        print(f"  {key}: {value}")

    return 0


def cmd_profile_validate(args: argparse.Namespace) -> int:
    """Validate profile configuration."""
    try:
        domain = load_domain(args.domain)
    except FileNotFoundError:
        print(f"Error: Domain '{args.domain}' not found")
        return 1

    try:
        profile = load_profile(domain, args.name)
    except FileNotFoundError:
        print(f"Error: Profile '{args.name}' not found in domain '{args.domain}'")
        return 1
    except ValueError as e:
        print(f"Error: Invalid YAML in profile config: {e}")
        return 1

    errors = validate_profile(profile)

    if errors:
        print(f"Validation failed for profile '{args.name}':")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Profile '{args.name}' is valid")
    return 0
