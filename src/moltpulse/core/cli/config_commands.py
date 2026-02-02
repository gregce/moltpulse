"""Configuration management CLI commands."""

import argparse
import getpass
import sys
from typing import Optional

from ..lib import env
from ..lib.key_validation import test_key, test_all_keys


# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"


def supports_color() -> bool:
    """Check if the terminal supports color."""
    import os
    # Check for NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False
    # Check if stdout is a tty
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def colorize(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if supports_color():
        return f"{color}{text}{RESET}"
    return text


def add_config_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add config command and subcommands to parser."""
    config_parser = subparsers.add_parser(
        "config",
        help="Manage MoltPulse configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  moltpulse config                           # Show configuration status
  moltpulse config set                       # Interactive key setup
  moltpulse config set ALPHA_VANTAGE_API_KEY # Set specific key interactively
  moltpulse config set XAI_API_KEY sk-xxx    # Set key directly
  moltpulse config unset NEWSDATA_API_KEY    # Remove a key
  moltpulse config test                      # Validate all configured keys
        """,
    )

    config_subparsers = config_parser.add_subparsers(dest="config_action")

    # config set
    set_parser = config_subparsers.add_parser(
        "set",
        help="Set a configuration value",
    )
    set_parser.add_argument(
        "key",
        nargs="?",
        help="Configuration key to set (interactive if omitted)",
    )
    set_parser.add_argument(
        "value",
        nargs="?",
        help="Value to set (prompts if omitted)",
    )
    set_parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip API key validation",
    )
    set_parser.set_defaults(func=cmd_config_set)

    # config unset
    unset_parser = config_subparsers.add_parser(
        "unset",
        help="Remove a configuration value",
    )
    unset_parser.add_argument(
        "key",
        help="Configuration key to remove",
    )
    unset_parser.set_defaults(func=cmd_config_unset)

    # config test
    test_parser = config_subparsers.add_parser(
        "test",
        help="Validate all configured API keys",
    )
    test_parser.add_argument(
        "key",
        nargs="?",
        help="Specific key to test (tests all if omitted)",
    )
    test_parser.set_defaults(func=cmd_config_test)

    # config (no subcommand) shows status
    config_parser.set_defaults(func=cmd_config_status)


def cmd_config_status(args: argparse.Namespace) -> int:
    """Display configuration status."""
    config = env.get_config()

    print()
    print(colorize("MoltPulse Configuration", BOLD))
    print("=" * 40)
    print(f"Config file: {env.CONFIG_FILE}")
    if env.config_exists():
        print(colorize("  (file exists)", GREEN))
    else:
        print(colorize("  (file not found - using defaults)", YELLOW))
    print()

    # API Keys section
    print(colorize("API Keys:", BOLD))
    api_keys = env.get_api_key_status(config)
    for key_info in api_keys:
        if key_info["configured"]:
            check = colorize("✓", GREEN)
        else:
            check = colorize("✗", RED)

        key_name = key_info["key"]
        masked = key_info["value_masked"]
        desc = key_info["description"]

        # Pad for alignment
        print(f"  {check} {key_name:28} {masked:16} ({desc})")

    print()

    # Collectors section
    print(colorize("Available Collectors:", BOLD))
    collectors = env.get_collector_status(config)
    for collector in collectors:
        if collector["available"]:
            check = colorize("✓", GREEN)
            status = ""
        else:
            check = colorize("✗", RED)
            status = colorize(f" ({collector.get('missing', 'unavailable')})", RED)

        name = collector["name"]
        desc = collector["description"]
        print(f"  {check} {name:14} {desc}{status}")

    print()

    # Settings section
    print(colorize("Settings:", BOLD))
    settings = env.get_settings_status(config)
    for setting in settings:
        key = setting["key"]
        value = setting["value"]
        is_default = value == setting["default"]
        default_note = " (default)" if is_default else ""
        print(f"  {key:32} {value}{default_note}")

    print()
    print(f"Run '{colorize('moltpulse config set', BLUE)}' to configure API keys.")
    print()

    return 0


def cmd_config_set(args: argparse.Namespace) -> int:
    """Set a configuration value."""
    config = env.get_config()

    # If no key specified, show interactive menu
    if not args.key:
        return _interactive_key_select(config, args)

    # Validate key name
    key = args.key.upper()
    if key not in env.API_KEY_REGISTRY and key not in env.SETTINGS_REGISTRY:
        print(f"Error: Unknown configuration key '{args.key}'")
        print()
        print("Available API keys:")
        for k in env.API_KEY_REGISTRY:
            print(f"  {k}")
        print()
        print("Available settings:")
        for k in env.SETTINGS_REGISTRY:
            print(f"  {k}")
        return 1

    # If no value specified, prompt for it
    if args.value:
        value = args.value
    else:
        value = _prompt_for_value(key)
        if value is None:
            print("Cancelled.")
            return 1

    # Test API key if applicable
    if key in env.API_KEY_REGISTRY and not args.no_test:
        print("Testing key... ", end="", flush=True)
        success, message = test_key(key, value)
        if success:
            print(colorize(f"✓ {message}", GREEN))
        elif success is False:
            print(colorize(f"✗ {message}", RED))
            response = input("Save anyway? [y/N]: ").strip().lower()
            if response != "y":
                print("Cancelled.")
                return 1

    # Save the value
    env.set_config_value(key, value)
    print(f"Saved {key} to {env.CONFIG_FILE}")

    return 0


def _interactive_key_select(config: dict, args: argparse.Namespace) -> int:
    """Show interactive menu to select a key to configure."""
    print()
    print(colorize("Which API key would you like to configure?", BOLD))
    print()

    # Build list of options
    options = []
    for key, info in env.API_KEY_REGISTRY.items():
        configured = bool(config.get(key))
        status = colorize("✓", GREEN) if configured else colorize("✗", RED)
        options.append((key, info["description"], status, configured))

    # Show options
    for i, (key, desc, status, _) in enumerate(options, 1):
        print(f"  {i}. {status} {key}")
        print(f"      {desc}")

    print()
    print("  0. Cancel")
    print()

    # Get selection
    try:
        selection = input("Enter number: ").strip()
        if not selection or selection == "0":
            print("Cancelled.")
            return 0

        idx = int(selection) - 1
        if idx < 0 or idx >= len(options):
            print("Invalid selection.")
            return 1

        key = options[idx][0]

    except (ValueError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1

    # Get value for selected key
    print()
    value = _prompt_for_value(key)
    if value is None:
        print("Cancelled.")
        return 1

    # Test the key
    if not args.no_test:
        print("Testing key... ", end="", flush=True)
        success, message = test_key(key, value)
        if success:
            print(colorize(f"✓ {message}", GREEN))
        elif success is False:
            print(colorize(f"✗ {message}", RED))
            response = input("Save anyway? [y/N]: ").strip().lower()
            if response != "y":
                print("Cancelled.")
                return 1

    # Save
    env.set_config_value(key, value)
    print(f"Saved {key} to {env.CONFIG_FILE}")

    return 0


def _prompt_for_value(key: str) -> Optional[str]:
    """Prompt user for a configuration value."""
    info = env.API_KEY_REGISTRY.get(key) or env.SETTINGS_REGISTRY.get(key, {})
    desc = info.get("description", key)
    provider = info.get("provider", "")
    signup_url = info.get("signup_url", "")

    print(f"Setting: {colorize(key, BOLD)}")
    if provider:
        print(f"Provider: {provider}")
    if signup_url:
        print(f"Get key: {signup_url}")
    print()

    try:
        # Use getpass for API keys to hide input
        if key in env.API_KEY_REGISTRY:
            value = getpass.getpass(f"Enter {desc}: ")
        else:
            default = info.get("default", "")
            prompt = f"Enter {desc}"
            if default:
                prompt += f" [{default}]"
            prompt += ": "
            value = input(prompt).strip()
            if not value and default:
                value = default

        return value.strip() if value else None

    except (KeyboardInterrupt, EOFError):
        return None


def cmd_config_unset(args: argparse.Namespace) -> int:
    """Remove a configuration value."""
    key = args.key.upper()

    if env.unset_config_value(key):
        print(f"Removed {key} from {env.CONFIG_FILE}")
        return 0
    else:
        print(f"Key '{key}' not found in configuration file")
        return 1


def cmd_config_test(args: argparse.Namespace) -> int:
    """Validate configured API keys."""
    config = env.get_config()

    print()
    print(colorize("Testing configured API keys...", BOLD))
    print()

    if args.key:
        # Test specific key
        key = args.key.upper()
        value = config.get(key)

        if not value:
            print(f"  {key}: {colorize('not configured', YELLOW)}")
            return 1

        print(f"  {key}: ", end="", flush=True)
        success, message = test_key(key, value)

        if success:
            print(colorize(f"✓ {message}", GREEN))
            return 0
        elif success is False:
            print(colorize(f"✗ {message}", RED))
            return 1
        else:
            print(colorize(message, YELLOW))
            return 0

    # Test all keys
    results = test_all_keys(config)
    all_passed = True

    for key, (success, message) in results.items():
        if success is None:
            # Not configured
            print(f"  {key:28} {colorize('not configured', YELLOW)}")
        elif success:
            print(f"  {key:28} {colorize(f'✓ {message}', GREEN)}")
        else:
            print(f"  {key:28} {colorize(f'✗ {message}', RED)}")
            all_passed = False

    print()
    return 0 if all_passed else 1
