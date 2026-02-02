"""Terminal UI utilities for MoltPulse using Rich library.

Provides progress display for run execution feedback using Rich's
thread-safe Progress class for parallel collector execution.
"""

import time
from typing import Dict, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Console for stderr output
console = Console(stderr=True)

# Check if we're in a real terminal
IS_TTY = console.is_terminal


class RunProgress:
    """Progress display for MoltPulse runs using Rich."""

    def __init__(self, domain: str, profile: str, report_type: str):
        self.domain = domain
        self.profile = profile
        self.report_type = report_type
        self.start_time = time.time()
        self.collector_results: list = []

        # Rich progress instance
        self.progress: Optional[Progress] = None
        self.tasks: Dict[str, int] = {}  # name -> task_id
        self._processing_task: Optional[int] = None

    def show_header(self) -> None:
        """Show run header."""
        console.print(
            f"\n[bold purple]MoltPulse[/] [dim]· {self.domain}/{self.profile} · {self.report_type}[/]\n"
        )

    def start_progress(self) -> None:
        """Start the progress display."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,  # Clear in-progress tasks when done
        )
        self.progress.start()

    def stop_progress(self) -> None:
        """Stop the progress display."""
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.tasks = {}

    def start_collector(self, name: str, collector_type: str) -> None:
        """Add a collector task to progress display."""
        if not self.progress:
            self.start_progress()

        color = self._color_for_type(collector_type)
        task_id = self.progress.add_task(f"[{color}]{name}...[/]", total=None)
        self.tasks[name] = task_id

    def end_collector(
        self,
        name: str,
        item_count: int,
        duration_ms: int,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Update collector task with result."""
        # Format duration
        if duration_ms >= 1000:
            duration_str = f"{duration_ms / 1000:.1f}s"
        else:
            duration_str = f"{duration_ms}ms"

        # Remove the task from progress display
        if self.progress and name in self.tasks:
            task_id = self.tasks[name]
            self.progress.remove_task(task_id)
            del self.tasks[name]

        # Print the completion line directly
        if success:
            console.print(f"[green]✓[/] {name}: {item_count} items ({duration_str})")
        else:
            error_msg = f" - {error}" if error else ""
            console.print(f"[red]✗[/] {name}: failed{error_msg}")

        # Track result
        self.collector_results.append({
            "name": name,
            "items": item_count,
            "duration_ms": duration_ms,
            "success": success,
        })

    def show_processing(self) -> None:
        """Show processing phase."""
        if not self.progress:
            self.start_progress()
        self._processing_task = self.progress.add_task(
            "[purple]Processing items...[/]", total=None
        )

    def end_processing(self) -> None:
        """End processing phase."""
        if self.progress and self._processing_task is not None:
            self.progress.remove_task(self._processing_task)
            self._processing_task = None
        console.print("[green]✓[/] Processing complete")

    def show_complete(self, total_items: int) -> None:
        """Show completion summary."""
        self.stop_progress()
        elapsed = time.time() - self.start_time
        console.print(
            f"\n[bold green]✓ Run complete[/] [dim]({elapsed:.1f}s) - {total_items} items[/]\n"
        )

    def show_error(self, message: str) -> None:
        """Show error message."""
        self.stop_progress()
        console.print(f"[red]✗ Error:[/] {message}")

    def _color_for_type(self, collector_type: str) -> str:
        """Get Rich color for collector type."""
        return {
            "financial": "green",
            "news": "cyan",
            "rss": "purple",
            "social": "yellow",
            "awards": "yellow",
            "pe_activity": "green",
        }.get(collector_type, "cyan")


def print_preflight_status(available: list, unavailable: list) -> None:
    """Print preflight check status using Rich."""
    console.print("\nCollector Status:")

    for item in available:
        name = item.get("name", "Unknown")
        ctype = item.get("type", "")
        console.print(f"  [green]✓[/] {name} ({ctype})")

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

        console.print(f"  [red]✗[/] {name} ({msg})")

    console.print()
