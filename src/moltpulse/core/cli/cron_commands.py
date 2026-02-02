"""OpenClaw cron integration commands."""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Find cron templates directory (bundled with package)
def get_cron_templates_dir() -> Optional[Path]:
    """Find the cron templates directory."""
    # Check relative to this file (src/moltpulse/core/cli/cron_commands.py)
    # Templates are at src/moltpulse/cron/
    package_dir = Path(__file__).parent.parent.parent  # src/moltpulse/
    cron_dir = package_dir / "cron"
    if cron_dir.exists():
        return cron_dir

    # Fallback: Check current working directory (development)
    cwd_cron = Path.cwd() / "cron"
    if cwd_cron.exists():
        return cwd_cron

    return None


def load_template(name: str) -> Optional[dict]:
    """Load a cron template by name."""
    cron_dir = get_cron_templates_dir()
    if not cron_dir:
        return None

    # Try with and without .json extension
    template_path = cron_dir / f"{name}.json"
    if not template_path.exists():
        template_path = cron_dir / name
    if not template_path.exists():
        return None

    with open(template_path) as f:
        return json.load(f)


def list_templates() -> List[dict]:
    """List all available cron templates."""
    cron_dir = get_cron_templates_dir()
    if not cron_dir:
        return []

    templates = []
    for path in sorted(cron_dir.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
                data["_filename"] = path.stem
                templates.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    return templates


def check_openclaw_installed() -> bool:
    """Check if OpenClaw CLI is available."""
    try:
        result = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_template(template: dict, dry_run: bool = False) -> tuple[bool, str]:
    """Install a cron template to OpenClaw.

    Returns (success, message).
    """
    schedule = template.get("schedule", {})
    payload = template.get("payload", {})

    # Build the openclaw cron add command
    cmd = ["openclaw", "cron", "add"]

    # Name (use filename or template name)
    name = template.get("_filename") or template.get("name", "moltpulse-job")
    name = f"moltpulse-{name}" if not name.startswith("moltpulse") else name
    cmd.extend(["--name", name])

    # Schedule
    if schedule.get("kind") == "cron":
        cmd.extend(["--cron", schedule.get("expr", "0 7 * * *")])
        if schedule.get("tz"):
            cmd.extend(["--tz", schedule["tz"]])
    elif schedule.get("kind") == "every":
        # Convert ms to human readable
        every_ms = schedule.get("everyMs", 3600000)
        hours = every_ms // 3600000
        cmd.extend(["--every", f"{hours}h"])

    # Session target
    session_target = template.get("sessionTarget", "isolated")
    cmd.extend(["--session", session_target])

    # Message (the command to run)
    message = payload.get("message", "")
    cmd.extend(["--message", message])

    # Delivery settings
    if payload.get("deliver"):
        cmd.append("--deliver")

    if dry_run:
        return True, shlex.join(cmd)

    # Execute
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, f"Installed '{name}'"
        else:
            error = result.stderr or result.stdout or "Unknown error"
            return False, f"Failed to install '{name}': {error.strip()}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout installing '{name}'"
    except Exception as e:
        return False, f"Error installing '{name}': {e}"


# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def supports_color() -> bool:
    """Check if terminal supports color."""
    import os
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(text: str, color: str) -> str:
    """Apply color if supported."""
    if supports_color():
        return f"{color}{text}{RESET}"
    return text


def add_cron_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add cron command and subcommands to parser."""
    cron_parser = subparsers.add_parser(
        "cron",
        help="Manage OpenClaw cron integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  moltpulse cron list                    # List available cron templates
  moltpulse cron show daily-brief        # Show template details
  moltpulse cron install daily-brief     # Install template to OpenClaw
  moltpulse cron install --all           # Install all templates
  moltpulse cron install --all --dry-run # Preview commands without executing
        """,
    )

    cron_subparsers = cron_parser.add_subparsers(dest="cron_action")

    # cron list
    list_parser = cron_subparsers.add_parser(
        "list",
        help="List available cron templates",
    )
    list_parser.set_defaults(func=cmd_cron_list)

    # cron show
    show_parser = cron_subparsers.add_parser(
        "show",
        help="Show cron template details",
    )
    show_parser.add_argument(
        "name",
        help="Template name (e.g., daily-brief)",
    )
    show_parser.set_defaults(func=cmd_cron_show)

    # cron install
    install_parser = cron_subparsers.add_parser(
        "install",
        help="Install cron template(s) to OpenClaw",
    )
    install_parser.add_argument(
        "name",
        nargs="?",
        help="Template name to install (omit for --all)",
    )
    install_parser.add_argument(
        "--all",
        action="store_true",
        help="Install all available templates",
    )
    install_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without executing",
    )
    install_parser.set_defaults(func=cmd_cron_install)

    # Default action shows help
    cron_parser.set_defaults(func=cmd_cron_help)


def cmd_cron_help(args: argparse.Namespace) -> int:
    """Show cron help when no subcommand given."""
    print()
    print(c("MoltPulse OpenClaw Integration", BOLD))
    print("=" * 40)
    print()
    print("Install MoltPulse scheduled jobs into OpenClaw's cron system.")
    print()
    print(c("Commands:", BOLD))
    print(f"  {c('list', GREEN)}      List available cron templates")
    print(f"  {c('show', GREEN)}      Show template details")
    print(f"  {c('install', GREEN)}   Install template(s) to OpenClaw")
    print()
    print(f"Run {c('moltpulse cron <command> --help', CYAN)} for more info.")
    print()
    return 0


def cmd_cron_list(args: argparse.Namespace) -> int:
    """List available cron templates."""
    templates = list_templates()

    if not templates:
        cron_dir = get_cron_templates_dir()
        if cron_dir:
            print(f"No templates found in {cron_dir}")
        else:
            print("Cron templates directory not found")
        return 1

    print()
    print(c("Available Cron Templates", BOLD))
    print("=" * 40)
    print()

    for t in templates:
        name = t.get("_filename", "unknown")
        desc = t.get("description", "No description")
        schedule = t.get("schedule", {})

        expr = schedule.get("expr", "")
        tz = schedule.get("tz", "")
        schedule_str = f"{expr} ({tz})" if tz else expr

        print(f"  {c(name, GREEN)}")
        print(f"    {desc}")
        print(f"    {c('Schedule:', DIM)} {schedule_str}")
        print()

    print(f"Install with: {c('moltpulse cron install <name>', CYAN)}")
    print(f"Or install all: {c('moltpulse cron install --all', CYAN)}")
    print()

    return 0


def cmd_cron_show(args: argparse.Namespace) -> int:
    """Show cron template details."""
    template = load_template(args.name)

    if not template:
        print(f"Template '{args.name}' not found")
        print()
        print("Available templates:")
        for t in list_templates():
            print(f"  - {t.get('_filename')}")
        return 1

    print()
    print(c(f"Template: {args.name}", BOLD))
    print("=" * 40)
    print()

    print(f"{c('Name:', DIM)} {template.get('name', 'N/A')}")
    print(f"{c('Description:', DIM)} {template.get('description', 'N/A')}")
    print()

    schedule = template.get("schedule", {})
    print(c("Schedule:", BOLD))
    print(f"  Kind: {schedule.get('kind', 'N/A')}")
    if schedule.get("expr"):
        print(f"  Expression: {schedule['expr']}")
    if schedule.get("tz"):
        print(f"  Timezone: {schedule['tz']}")
    print()

    payload = template.get("payload", {})
    print(c("Execution:", BOLD))
    print(f"  Session: {template.get('sessionTarget', 'isolated')}")
    print(f"  Message: {payload.get('message', 'N/A')}")
    print(f"  Deliver: {'Yes' if payload.get('deliver') else 'No'}")
    print()

    notes = template.get("notes", [])
    if notes:
        print(c("Notes:", BOLD))
        for note in notes:
            print(f"  - {note}")
        print()

    # Show install command
    template["_filename"] = args.name
    _, cmd = install_template(template, dry_run=True)
    print(c("Install command:", BOLD))
    print(f"  {cmd}")
    print()

    return 0


def cmd_cron_install(args: argparse.Namespace) -> int:
    """Install cron template(s) to OpenClaw."""
    # Check for OpenClaw
    if not args.dry_run and not check_openclaw_installed():
        print(c("Error: OpenClaw CLI not found", RED))
        print()
        print("OpenClaw must be installed to use cron integration.")
        print("MoltPulse can still be run manually without OpenClaw.")
        return 1

    # Determine which templates to install
    if args.all:
        templates = list_templates()
        if not templates:
            print("No templates found to install")
            return 1
    elif args.name:
        template = load_template(args.name)
        if not template:
            print(f"Template '{args.name}' not found")
            return 1
        template["_filename"] = args.name
        templates = [template]
    else:
        print("Please specify a template name or use --all")
        print()
        print("Available templates:")
        for t in list_templates():
            print(f"  - {t.get('_filename')}")
        return 1

    print()
    if args.dry_run:
        print(c("Dry run - commands that would be executed:", BOLD))
    else:
        print(c("Installing cron jobs to OpenClaw...", BOLD))
    print()

    success_count = 0
    fail_count = 0

    for template in templates:
        success, message = install_template(template, dry_run=args.dry_run)

        if args.dry_run:
            print(f"  {message}")
        elif success:
            print(f"  {c('✓', GREEN)} {message}")
            success_count += 1
        else:
            print(f"  {c('✗', RED)} {message}")
            fail_count += 1

    print()

    if not args.dry_run:
        if fail_count == 0:
            print(f"Successfully installed {success_count} cron job(s)")
            print()
            print(f"View with: {c('openclaw cron list', CYAN)}")
        else:
            print(f"Installed {success_count}, failed {fail_count}")
            return 1

    print()
    return 0
