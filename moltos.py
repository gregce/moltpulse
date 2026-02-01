#!/usr/bin/env python3
"""Moltos - Domain-agnostic industry intelligence framework.

Usage:
    # Generate reports
    python moltos.py run --domain=advertising --profile=ricki daily
    python moltos.py run --domain=advertising --profile=ricki weekly --deliver

    # Manage domains
    python moltos.py domain list
    python moltos.py domain create healthcare --display-name "Healthcare Intelligence"
    python moltos.py domain show advertising

    # Manage profiles
    python moltos.py profile list advertising
    python moltos.py profile create advertising sarah --thought-leader "Seth Godin:ThisIsSethsBlog:1"
    python moltos.py profile show advertising ricki
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from core.domain_loader import load_domain, list_domains
from core.profile_loader import load_profile, list_profiles
from core.orchestrator import Orchestrator
from core.delivery import deliver_report
from core.lib import env
from core.cli.domain_commands import add_domain_parser
from core.cli.profile_commands import add_profile_parser


def add_run_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run command parser."""
    run_parser = subparsers.add_parser(
        "run",
        help="Generate a report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  moltos.py run --domain=advertising --profile=ricki daily
  moltos.py run --domain=advertising --profile=ricki weekly --deliver
  moltos.py run --domain=advertising fundraising --deep --output=json
        """,
    )

    # Required arguments
    run_parser.add_argument(
        "--domain",
        required=True,
        help="Domain instance to use (e.g., advertising, healthcare)",
    )

    # Optional arguments
    run_parser.add_argument(
        "--profile",
        default="default",
        help="Interest profile to load (default: default)",
    )

    run_parser.add_argument(
        "--quick",
        action="store_true",
        help="Use quick/shallow data collection",
    )

    run_parser.add_argument(
        "--deep",
        action="store_true",
        help="Use deep/thorough data collection",
    )

    run_parser.add_argument(
        "--deliver",
        action="store_true",
        help="Deliver report via profile's delivery settings",
    )

    run_parser.add_argument(
        "--output",
        choices=["compact", "json", "markdown", "full"],
        default="compact",
        help="Output format (default: compact)",
    )

    run_parser.add_argument(
        "--output-path",
        type=Path,
        help="Write output to file path",
    )

    run_parser.add_argument(
        "--from-date",
        help="Start date (YYYY-MM-DD). Defaults based on report type.",
    )

    run_parser.add_argument(
        "--to-date",
        help="End date (YYYY-MM-DD). Defaults to today.",
    )

    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be collected without running",
    )

    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    # Report type subcommands
    report_subparsers = run_parser.add_subparsers(dest="report_type", help="Report type to generate")

    # Daily brief
    daily_parser = report_subparsers.add_parser("daily", help="Generate daily brief")
    daily_parser.add_argument(
        "--sections",
        nargs="+",
        help="Specific sections to include",
    )

    # Weekly digest
    weekly_parser = report_subparsers.add_parser("weekly", help="Generate weekly digest")
    weekly_parser.add_argument(
        "--sections",
        nargs="+",
        help="Specific sections to include",
    )

    # Fundraising outlook
    fundraising_parser = report_subparsers.add_parser("fundraising", help="Generate fundraising outlook")
    fundraising_parser.add_argument(
        "--horizon",
        choices=["6m", "1y", "3y", "all"],
        default="all",
        help="Forecast horizon to include",
    )

    run_parser.set_defaults(func=cmd_run)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Moltos - Industry Intelligence Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  run       Generate a report
  domain    Manage domain instances
  profile   Manage interest profiles

Examples:
  moltos.py run --domain=advertising --profile=ricki daily
  moltos.py domain list
  moltos.py profile show advertising ricki
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Add command parsers
    add_run_parser(subparsers)
    add_domain_parser(subparsers)
    add_profile_parser(subparsers)

    return parser.parse_args()


def get_depth(args: argparse.Namespace) -> str:
    """Determine collection depth from arguments."""
    if args.quick:
        return "quick"
    elif args.deep:
        return "deep"
    return "default"


def get_date_range(args: argparse.Namespace) -> tuple[str, str]:
    """Get date range based on report type and arguments."""
    today = datetime.now().date()
    to_date = args.to_date or today.isoformat()

    if args.from_date:
        from_date = args.from_date
    else:
        # Default ranges based on report type
        if args.report_type == "daily":
            from_date = (today - timedelta(days=1)).isoformat()
        elif args.report_type == "weekly":
            from_date = (today - timedelta(days=7)).isoformat()
        elif args.report_type == "fundraising":
            from_date = (today - timedelta(days=30)).isoformat()
        else:
            from_date = (today - timedelta(days=1)).isoformat()

    return from_date, to_date


def format_output(report: dict, format_type: str) -> str:
    """Format report based on output type."""
    if format_type == "json":
        return json.dumps(report, indent=2, default=str)

    elif format_type == "markdown":
        return format_markdown(report)

    elif format_type == "full":
        return format_full(report)

    else:  # compact
        return format_compact(report)


def format_compact(report: dict) -> str:
    """Format report in compact style for terminal."""
    lines = []

    # Title
    lines.append(f"\n{'=' * 60}")
    lines.append(report.get("title", "MOLTOS REPORT"))
    lines.append(f"Generated: {report.get('generated_at', 'Unknown')}")
    lines.append(f"{'=' * 60}\n")

    # Sections
    for section in report.get("sections", []):
        lines.append(f"\n{section.get('title', 'SECTION')}")
        lines.append("-" * 40)

        items = section.get("items", [])
        for item in items[:10]:  # Limit items in compact view
            if isinstance(item, dict):
                # Format based on item type
                if "symbol" in item:
                    # Financial item
                    change = item.get("change_pct") or item.get("change", 0)
                    sign = "+" if change > 0 else ""
                    lines.append(f"  {item.get('symbol')}: {item.get('price', 'N/A')} ({sign}{change:.1f}%)")

                elif "title" in item and "url" in item:
                    # News item
                    lines.append(f"  - {item.get('title', '')[:60]}...")
                    lines.append(f"    [{item.get('source_name', 'Source')}]({item.get('url', '')})")

                elif "author" in item or "author_handle" in item:
                    # Social item
                    handle = item.get("author") or f"@{item.get('author_handle', '')}"
                    text = item.get("text", "")[:80]
                    lines.append(f"  {handle}: {text}...")

                elif "summary" in item:
                    # PE/M&A item
                    lines.append(f"  - {item.get('summary', '')}")

                elif "status" in item:
                    # Health indicator
                    lines.append(f"  Status: {item.get('status')} - {item.get('description', '')}")

                elif "trend" in item:
                    # Trend item
                    lines.append(f"  - {item.get('trend')}: {item.get('pitch_angle', item.get('mentions', ''))}")

                elif "timeframe" in item:
                    # Outlook item
                    lines.append(f"  {item.get('timeframe')} ({item.get('confidence', 'N/A')} confidence)")
                    lines.append(f"  {item.get('summary', '')[:100]}...")

                else:
                    # Generic item
                    lines.append(f"  - {str(item)[:100]}")
            else:
                lines.append(f"  - {str(item)[:100]}")

    # Sources
    sources = report.get("all_sources", [])
    if sources:
        lines.append(f"\n{'=' * 60}")
        lines.append("SOURCES:")
        for i, source in enumerate(sources[:10], 1):
            name = source.get("name", "Source") if isinstance(source, dict) else getattr(source, "name", "Source")
            url = source.get("url", "") if isinstance(source, dict) else getattr(source, "url", "")
            lines.append(f"  {i}. [{name}]({url})")
        if len(sources) > 10:
            lines.append(f"  ... and {len(sources) - 10} more sources")

    lines.append("")
    return "\n".join(lines)


def format_markdown(report: dict) -> str:
    """Format report as markdown."""
    lines = []

    # Title
    lines.append(f"# {report.get('title', 'MOLTOS REPORT')}")
    lines.append(f"*Generated: {report.get('generated_at', 'Unknown')}*")
    lines.append("")

    # Sections
    for section in report.get("sections", []):
        lines.append(f"## {section.get('title', 'Section')}")
        lines.append("")

        items = section.get("items", [])
        for item in items:
            if isinstance(item, dict):
                if "symbol" in item:
                    change = item.get("change_pct") or item.get("change", 0)
                    sign = "+" if change > 0 else ""
                    lines.append(f"- **{item.get('symbol')}** ({item.get('name', '')}): {item.get('price', 'N/A')} ({sign}{change:.1f}%)")

                elif "title" in item and "url" in item:
                    lines.append(f"- [{item.get('title', '')}]({item.get('url', '')})")
                    if item.get("snippet"):
                        lines.append(f"  > {item.get('snippet')[:150]}...")

                elif "author" in item or "author_handle" in item:
                    handle = item.get("author") or f"@{item.get('author_handle', '')}"
                    lines.append(f"- **{handle}**: {item.get('text', '')}")
                    if item.get("url"):
                        lines.append(f"  [View]({item.get('url')})")

                elif "summary" in item and "url" in item:
                    lines.append(f"- {item.get('summary', '')}")
                    lines.append(f"  [Source]({item.get('url', '')})")

                elif "timeframe" in item:
                    lines.append(f"### {item.get('timeframe')} Outlook")
                    lines.append(f"*Confidence: {item.get('confidence', 'N/A')}*")
                    lines.append("")
                    lines.append(item.get("summary", ""))
                    if item.get("action_items"):
                        lines.append("")
                        lines.append("**Action Items:**")
                        for action in item.get("action_items", []):
                            lines.append(f"- {action}")

                else:
                    lines.append(f"- {json.dumps(item, default=str)}")
            else:
                lines.append(f"- {item}")

        lines.append("")

    # Sources
    sources = report.get("all_sources", [])
    if sources:
        lines.append("## Sources")
        lines.append("")
        for i, source in enumerate(sources, 1):
            name = source.get("name", "Source") if isinstance(source, dict) else getattr(source, "name", "Source")
            url = source.get("url", "") if isinstance(source, dict) else getattr(source, "url", "")
            lines.append(f"{i}. [{name}]({url})")

    return "\n".join(lines)


def format_full(report: dict) -> str:
    """Format report with full details."""
    return json.dumps(report, indent=2, default=str)


def cmd_run(args: argparse.Namespace) -> int:
    """Run report generation command."""
    if not args.report_type:
        print("Error: Please specify a report type (daily, weekly, fundraising)")
        return 1

    # Load API keys
    config = env.get_config()

    if args.verbose:
        print(f"Domain: {args.domain}")
        print(f"Profile: {args.profile}")
        print(f"Report: {args.report_type}")

    # Load domain configuration
    try:
        domain = load_domain(args.domain)
    except FileNotFoundError as e:
        print(f"Error: Domain '{args.domain}' not found")
        print(f"Available domains: {', '.join(list_domains())}")
        return 1

    # Load profile
    try:
        profile = load_profile(domain, args.profile)
    except FileNotFoundError as e:
        print(f"Error: Profile '{args.profile}' not found in domain '{args.domain}'")
        print(f"Available profiles: {', '.join(list_profiles(args.domain))}")
        return 1

    # Get date range
    from_date, to_date = get_date_range(args)
    depth = get_depth(args)

    if args.verbose:
        print(f"Date range: {from_date} to {to_date}")
        print(f"Depth: {depth}")

    # Dry run - just show configuration
    if args.dry_run:
        print("\n=== DRY RUN ===")
        print(f"Domain: {args.domain}")
        print(f"Profile: {args.profile}")
        print(f"Report type: {args.report_type}")
        print(f"Date range: {from_date} to {to_date}")
        print(f"Depth: {depth}")
        print(f"\nCollectors to run:")
        for collector in domain.collectors:
            print(f"  - {collector.get('type')}: {collector.get('module')}")
        print(f"\nThought leaders to track:")
        for leader in profile.thought_leaders[:5]:
            print(f"  - {leader.get('name')} (@{leader.get('x_handle')})")
        return 0

    # Initialize orchestrator
    orchestrator = Orchestrator(domain, profile, config)

    # Run collection and report generation
    try:
        if args.verbose:
            print("\nCollecting data...")

        report = orchestrator.run(
            report_type=args.report_type,
            from_date=from_date,
            to_date=to_date,
            depth=depth,
        )

        # Convert report to dict for output
        report_dict = report.to_dict()

    except Exception as e:
        print(f"Error generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Format output
    output = format_output(report_dict, args.output)

    # Delivery
    if args.deliver:
        result = deliver_report(report, profile, format=args.output)
        if not result.success:
            print(f"Warning: Delivery failed ({result.error}), outputting to console")
            print(output)
        else:
            if args.verbose:
                print(f"Delivered via {result.channel}: {result.message}")
    elif args.output_path:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(output)
        print(f"Report written to: {args.output_path}")
    else:
        print(output)

    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if not args.command:
        print("Error: Please specify a command (run, domain, profile)")
        print("Use --help for usage information")
        return 1

    # Execute command
    if hasattr(args, "func"):
        return args.func(args)
    else:
        # Handle missing subcommand
        if args.command == "domain" and not args.domain_action:
            print("Error: Please specify a domain action (create, update, list, show, validate)")
            return 1
        elif args.command == "profile" and not args.profile_action:
            print("Error: Please specify a profile action (create, update, list, show, validate)")
            return 1
        elif args.command == "run" and not args.report_type:
            print("Error: Please specify a report type (daily, weekly, fundraising)")
            return 1
        return 1


if __name__ == "__main__":
    sys.exit(main())
