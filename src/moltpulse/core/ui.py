"""Terminal UI utilities for MoltPulse.

Provides progress spinners and display utilities for run execution feedback.
Adapted from the last30days skill pattern.
"""

import sys
import threading
import time
from typing import Optional

# Check if we're in a real terminal (not captured by Claude Code)
IS_TTY = sys.stderr.isatty()

# Global lock for stderr writes to prevent corruption from parallel collectors
_stderr_lock = threading.Lock()


class Colors:
    """ANSI color codes for terminal output."""

    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# Spinner animation frames
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    """Animated spinner for long-running operations."""

    def __init__(self, message: str, color: str = Colors.CYAN):
        self.message = message
        self.color = color
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.frame_idx = 0
        self.shown_static = False

    def _spin(self) -> None:
        """Animation loop running in background thread."""
        while self.running:
            frame = SPINNER_FRAMES[self.frame_idx % len(SPINNER_FRAMES)]
            with _stderr_lock:
                sys.stderr.write(f"\r{self.color}{frame}{Colors.RESET} {self.message}  ")
                sys.stderr.flush()
            self.frame_idx += 1
            time.sleep(0.08)

    def start(self) -> None:
        """Start the spinner animation."""
        self.running = True
        if IS_TTY:
            # Real terminal - animate
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()
        else:
            # Not a TTY (Claude Code, pipes) - just print once
            if not self.shown_static:
                with _stderr_lock:
                    sys.stderr.write(f"⏳ {self.message}\n")
                    sys.stderr.flush()
                self.shown_static = True

    def update(self, message: str) -> None:
        """Update the spinner message."""
        self.message = message
        if not IS_TTY and not self.shown_static:
            with _stderr_lock:
                sys.stderr.write(f"⏳ {message}\n")
                sys.stderr.flush()

    def stop(self, final_message: str = "") -> None:
        """Stop the spinner and show final message."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)  # Increased from 0.2 to allow thread to exit
            self.thread = None  # Clear reference
        with _stderr_lock:
            if IS_TTY:
                # Clear the line in real terminal
                sys.stderr.write("\r" + " " * 80 + "\r")
            if final_message:
                sys.stderr.write(f"✓ {final_message}\n")
            sys.stderr.flush()


class RunProgress:
    """Progress display for MoltPulse runs."""

    def __init__(self, domain: str, profile: str, report_type: str):
        self.domain = domain
        self.profile = profile
        self.report_type = report_type
        self.spinner: Optional[Spinner] = None
        self.start_time = time.time()
        self.collector_results: list = []

    def show_header(self) -> None:
        """Show run header."""
        with _stderr_lock:
            if IS_TTY:
                sys.stderr.write(
                    f"\n{Colors.PURPLE}{Colors.BOLD}MoltPulse{Colors.RESET} "
                    f"{Colors.DIM}· {self.domain}/{self.profile} · {self.report_type}{Colors.RESET}\n\n"
                )
            else:
                sys.stderr.write(f"MoltPulse · {self.domain}/{self.profile} · {self.report_type}\n")
            sys.stderr.flush()

    def start_collector(self, name: str, collector_type: str) -> None:
        """Show spinner for collector starting."""
        # Stop any existing spinner before starting a new one
        # This prevents orphaned spinner threads from accumulating
        if self.spinner:
            self.spinner.stop()

        color = self._color_for_type(collector_type)
        self.spinner = Spinner(f"{name}...", color)
        self.spinner.start()

    def end_collector(
        self,
        name: str,
        item_count: int,
        duration_ms: int,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Stop spinner with result."""
        if self.spinner:
            self.spinner.stop()

        # Format duration
        if duration_ms >= 1000:
            duration_str = f"{duration_ms / 1000:.1f}s"
        else:
            duration_str = f"{duration_ms}ms"

        # Show result
        with _stderr_lock:
            if success:
                if IS_TTY:
                    sys.stderr.write(f"✓ {name}: {item_count} items ({duration_str})\n")
                else:
                    sys.stderr.write(f"✓ {name}: {item_count} items ({duration_str})\n")
            else:
                error_msg = f" - {error}" if error else ""
                if IS_TTY:
                    sys.stderr.write(f"{Colors.RED}✗{Colors.RESET} {name}: failed{error_msg}\n")
                else:
                    sys.stderr.write(f"✗ {name}: failed{error_msg}\n")
            sys.stderr.flush()

        # Track result
        self.collector_results.append({
            "name": name,
            "items": item_count,
            "duration_ms": duration_ms,
            "success": success,
        })

    def show_processing(self) -> None:
        """Show processing phase."""
        # Stop any existing spinner first
        if self.spinner:
            self.spinner.stop()

        self.spinner = Spinner("Processing items...", Colors.PURPLE)
        self.spinner.start()

    def end_processing(self) -> None:
        """End processing phase."""
        if self.spinner:
            self.spinner.stop()

    def show_complete(self, total_items: int) -> None:
        """Show completion summary."""
        elapsed = time.time() - self.start_time
        with _stderr_lock:
            if IS_TTY:
                sys.stderr.write(
                    f"\n{Colors.GREEN}{Colors.BOLD}✓ Run complete{Colors.RESET} "
                    f"{Colors.DIM}({elapsed:.1f}s) - {total_items} items{Colors.RESET}\n\n"
                )
            else:
                sys.stderr.write(f"\n✓ Run complete ({elapsed:.1f}s) - {total_items} items\n")
            sys.stderr.flush()

    def show_error(self, message: str) -> None:
        """Show error message."""
        if self.spinner:
            self.spinner.stop()
        with _stderr_lock:
            if IS_TTY:
                sys.stderr.write(f"{Colors.RED}✗ Error:{Colors.RESET} {message}\n")
            else:
                sys.stderr.write(f"✗ Error: {message}\n")
            sys.stderr.flush()

    def _color_for_type(self, collector_type: str) -> str:
        """Get color for collector type."""
        return {
            "financial": Colors.GREEN,
            "news": Colors.CYAN,
            "rss": Colors.PURPLE,
            "social": Colors.YELLOW,
            "awards": Colors.YELLOW,
            "pe_activity": Colors.GREEN,
        }.get(collector_type, Colors.CYAN)


def print_preflight_status(available: list, unavailable: list) -> None:
    """Print preflight check status."""
    with _stderr_lock:
        sys.stderr.write("\nCollector Status:\n")

        for item in available:
            name = item.get("name", "Unknown")
            ctype = item.get("type", "")
            if IS_TTY:
                sys.stderr.write(f"  {Colors.GREEN}✓{Colors.RESET} {name} ({ctype})\n")
            else:
                sys.stderr.write(f"  ✓ {name} ({ctype})\n")

        for item in unavailable:
            name = item.get("name", "Unknown")
            if "missing_keys" in item:
                if item.get("requires_any"):
                    keys = " or ".join(item["missing_keys"])
                    msg = f"needs one of: {keys}"
                else:
                    keys = ", ".join(item["missing_keys"])
                    msg = f"missing: {keys}"
            else:
                msg = item.get("reason", "unavailable")

            if IS_TTY:
                sys.stderr.write(f"  {Colors.RED}✗{Colors.RESET} {name} ({msg})\n")
            else:
                sys.stderr.write(f"  ✗ {name} ({msg})\n")

        sys.stderr.write("\n")
        sys.stderr.flush()
