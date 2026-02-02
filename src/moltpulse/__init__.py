"""MoltPulse - Domain-agnostic industry intelligence framework."""

try:
    from moltpulse._version import __version__
except ImportError:
    # Fallback for editable installs or running from source without build
    __version__ = "0.0.0.dev0+unknown"
