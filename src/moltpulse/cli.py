#!/usr/bin/env python3
"""MoltPulse - Domain-agnostic industry intelligence framework.

Usage:
    # Generate reports
    python moltpulse.py run --domain=advertising --profile=ricki daily
    python moltpulse.py run --domain=advertising --profile=ricki weekly --deliver

    # Manage domains
    python moltpulse.py domain list
    python moltpulse.py domain create healthcare --display-name "Healthcare Intelligence"
    python moltpulse.py domain show advertising

    # Manage profiles
    python moltpulse.py profile list advertising
    python moltpulse.py profile create advertising sarah --thought-leader "Seth Godin:ThisIsSethsBlog:1"
    python moltpulse.py profile show advertising ricki
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from moltpulse.core.domain_loader import load_domain, list_domains
from moltpulse.core.profile_loader import load_profile, list_profiles
from moltpulse.core.orchestrator import Orchestrator
from moltpulse.core.delivery import deliver_report
from moltpulse.core.lib import env
from moltpulse.core.cli.config_commands import add_config_parser, supports_color
from moltpulse.core.cli.cron_commands import add_cron_parser
from moltpulse.core.cli.domain_commands import add_domain_parser
from moltpulse.core.cli.profile_commands import add_profile_parser


# ASCII Art Logo
LOGO = r"""
 __  __       _ _   ____        _
|  \/  | ___ | | |_|  _ \ _   _| |___  ___
| |\/| |/ _ \| | __| |_) | | | | / __|/ _ \
| |  | | (_) | | |_|  __/| |_| | \__ \  __/
|_|  |_|\___/|_|\__|_|    \__,_|_|___/\___|
"""

# ANSI color codes
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_welcome() -> None:
    """Print the welcome screen with logo and usage examples."""
    use_color = supports_color()

    def c(text: str, color: str) -> str:
        return f"{color}{text}{RESET}" if use_color else text

    # Logo in green
    print(c(LOGO, GREEN))

    # Description
    print("MoltPulse is a domain-agnostic industry intelligence framework that")
    print("aggregates news, financial data, social signals, and M&A activity into")
    print("customizable reports for any industry domain.")
    print()

    # Usage section
    print(c("USAGE", YELLOW))
    print()
    print(f"  {c('moltpulse', CYAN)} [command] [--flags]")
    print()

    # Examples section
    print(c("EXAMPLES", YELLOW))
    print()

    # Config examples
    print(c("  # Check configuration status and available collectors", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('config', GREEN)}")
    print()

    print(c("  # Configure API keys interactively", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('config set', GREEN)}")
    print()

    print(c("  # Validate all configured API keys", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('config test', GREEN)}")
    print()

    # Domain examples
    print(c("  # List available domains", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('domain list', GREEN)}")
    print()

    print(c("  # Create a new domain", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('domain create', GREEN)} healthcare {c('--display-name', CYAN)} \"Healthcare Intelligence\"")
    print()

    # Profile examples
    print(c("  # List profiles in a domain", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('profile list', GREEN)} advertising")
    print()

    print(c("  # Show profile details", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('profile show', GREEN)} advertising ricki")
    print()

    # Run examples
    print(c("  # Generate a daily brief", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('run', GREEN)} {c('--domain', CYAN)}=advertising {c('--profile', CYAN)}=ricki {c('daily', GREEN)}")
    print()

    print(c("  # Generate weekly digest and deliver via configured channel", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('run', GREEN)} {c('--domain', CYAN)}=advertising {c('--profile', CYAN)}=ricki {c('weekly', GREEN)} {c('--deliver', CYAN)}")
    print()

    print(c("  # Deep fundraising analysis with JSON output", DIM))
    print(f"  {c('moltpulse', CYAN)} {c('run', GREEN)} {c('--domain', CYAN)}=advertising {c('--deep', CYAN)} {c('fundraising', GREEN)} {c('--output', CYAN)}=json")
    print()

    # Commands section
    print(c("COMMANDS", YELLOW))
    print()
    print(f"  {c('config', GREEN)}   Manage API keys and settings")
    print(f"  {c('cron', GREEN)}     Install scheduled jobs to OpenClaw")
    print(f"  {c('domain', GREEN)}   Manage domain instances (advertising, healthcare, etc.)")
    print(f"  {c('profile', GREEN)}  Manage interest profiles within domains")
    print(f"  {c('run', GREEN)}      Generate intelligence reports")
    print()

    # Help hint
    print(f"Run {c('moltpulse <command> --help', CYAN)} for more information on a command.")
    print()


def add_run_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run command parser."""
    run_parser = subparsers.add_parser(
        "run",
        help="Generate a report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  moltpulse.py run --domain=advertising --profile=ricki daily
  moltpulse.py run --domain=advertising --profile=ricki weekly --deliver
  moltpulse.py run --domain=advertising fundraising --deep --output=json
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
        "--no-deliver",
        action="store_true",
        help="Output to stdout only, skip delivery (for OpenClaw orchestration)",
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
        "--trace",
        action="store_true",
        help="Show detailed execution trace with API calls",
    )

    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    # Collector control flags
    run_parser.add_argument(
        "--collectors",
        help="Comma-separated list of collectors to run (e.g., news,rss,financial)",
    )

    run_parser.add_argument(
        "--exclude-collectors",
        help="Comma-separated list of collectors to skip (e.g., pe_activity,awards)",
    )

    run_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache and fetch fresh data",
    )

    run_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output (for cron/CI)",
    )

    run_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum items per collector (overrides depth defaults)",
    )

    run_parser.add_argument(
        "--retry",
        type=int,
        default=0,
        help="Number of retries for failed API calls (default: 0)",
    )

    run_parser.add_argument(
        "--timeout",
        type=int,
        help="Custom timeout per collector in seconds (overrides depth defaults)",
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
        description="MoltPulse - Industry Intelligence Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  run       Generate a report
  config    Manage API keys and settings
  domain    Manage domain instances
  profile   Manage interest profiles

Examples:
  moltpulse.py config                                  # Show configuration status
  moltpulse.py config set                              # Configure API keys interactively
  moltpulse.py run --domain=advertising --profile=ricki daily
  moltpulse.py domain list
  moltpulse.py profile show advertising ricki
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Add command parsers
    add_run_parser(subparsers)
    add_config_parser(subparsers)
    add_cron_parser(subparsers)
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
    lines.append(report.get("title", "MOLTPULSE REPORT"))
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
    lines.append(f"# {report.get('title', 'MOLTPULSE REPORT')}")
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

    # Get depth
    depth = get_depth(args)

    if args.verbose:
        print(f"Depth: {depth}")

    # Calculate days from date range if specified
    days = 30
    if args.from_date:
        try:
            from datetime import datetime as dt
            from_dt = dt.strptime(args.from_date, "%Y-%m-%d")
            to_dt = dt.strptime(args.to_date, "%Y-%m-%d") if args.to_date else dt.now()
            days = (to_dt - from_dt).days
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD.")
            return 1

    # Parse collector filters
    collectors_list = None
    if args.collectors:
        collectors_list = [c.strip() for c in args.collectors.split(",")]

    exclude_list = []
    if args.exclude_collectors:
        exclude_list = [c.strip() for c in args.exclude_collectors.split(",")]

    # Initialize orchestrator
    orchestrator = Orchestrator(
        domain_name=args.domain,
        profile_name=args.profile,
        depth=depth,
        days=days,
        collectors=collectors_list,
        exclude_collectors=exclude_list,
        no_cache=getattr(args, 'no_cache', False),
        limit=getattr(args, 'limit', None),
        retry=getattr(args, 'retry', 0),
        timeout=getattr(args, 'timeout', None),
    )

    # Dry run - just show configuration and preflight
    if args.dry_run:
        print("\n=== DRY RUN ===")
        print(f"Domain: {args.domain}")
        print(f"Profile: {args.profile}")
        print(f"Report type: {args.report_type}")
        print(f"Date range: {orchestrator.from_date} to {orchestrator.to_date}")
        print(f"Depth: {depth}")

        # Show collector filter options if specified
        if collectors_list:
            print(f"Collectors (include): {', '.join(collectors_list)}")
        if exclude_list:
            print(f"Collectors (exclude): {', '.join(exclude_list)}")
        if getattr(args, 'limit', None):
            print(f"Item limit: {args.limit}")
        if getattr(args, 'no_cache', False):
            print("Cache: DISABLED (--no-cache)")
        if getattr(args, 'retry', 0) > 0:
            print(f"Retries: {args.retry}")
        if getattr(args, 'timeout', None):
            print(f"Timeout: {args.timeout}s")

        # Show preflight status
        orchestrator.print_preflight_report()

        print("Thought leaders to track:")
        for leader in profile.thought_leaders[:5]:
            print(f"  - {leader.get('name')} (@{leader.get('x_handle')})")
        if len(profile.thought_leaders) > 5:
            print(f"  ... and {len(profile.thought_leaders) - 5} more")
        return 0

    # Determine if we should show progress
    # Suppress for: --quiet, JSON output with --no-deliver
    show_progress = not (
        getattr(args, 'quiet', False) or
        (args.output == "json" and args.no_deliver)
    )

    # Run collection and report generation
    try:
        result = orchestrator.run(
            report_type=args.report_type,
            show_progress=show_progress,
        )

        if not result.success:
            for error in result.errors:
                print(f"Warning: {error}", file=sys.stderr)

        if result.report is None:
            print("Error: No report generated")
            return 1

        # Convert report to dict for output
        report_dict = result.report.to_dict()

        # If trace requested and output is JSON, include trace in output
        if args.trace and args.output == "json":
            report_dict["_trace"] = result.trace.to_dict() if result.trace else None

    except Exception as e:
        print(f"Error generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Show trace summary if requested (and not JSON mode)
    if args.trace and args.output != "json" and result.trace:
        print("\n" + result.trace.summary())
        print()

    # Format output
    output = format_output(report_dict, args.output)

    # Delivery (--no-deliver overrides --deliver for OpenClaw orchestration)
    if args.deliver and not args.no_deliver:
        delivery_result = deliver_report(result.report, profile, format=args.output)
        if not delivery_result.success:
            print(f"Warning: Delivery failed ({delivery_result.error}), outputting to console")
            print(output)
        else:
            if args.verbose:
                print(f"Delivered via {delivery_result.channel}: {delivery_result.message}")
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
        # No command specified - show welcome screen
        print_welcome()
        return 0

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
