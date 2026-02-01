"""CLI commands for Moltos configuration."""

from .domain_commands import add_domain_parser
from .profile_commands import add_profile_parser

__all__ = ["add_domain_parser", "add_profile_parser"]
