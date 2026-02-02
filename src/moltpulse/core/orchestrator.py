"""Orchestrator for parallel collector execution and report generation."""

import importlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .collector_base import Collector, CollectorResult
from .domain_loader import DomainConfig, load_domain
from .lib import cache, dates, dedupe, env, normalize, schema, score
from .profile_loader import ProfileConfig, load_profile
from .report_base import ReportGenerator
from .trace import CollectorTrace, RunTrace, TracingContext
from .ui import RunProgress


class OrchestratorResult:
    """Result from orchestrator run."""

    def __init__(
        self,
        report: Optional[schema.Report] = None,
        collector_results: Optional[Dict[str, CollectorResult]] = None,
        errors: Optional[List[str]] = None,
        trace: Optional[RunTrace] = None,
    ):
        self.report = report
        self.collector_results = collector_results or {}
        self.errors = errors or []
        self.trace = trace

    @property
    def success(self) -> bool:
        return self.report is not None and len(self.errors) == 0


class Orchestrator:
    """Coordinates data collection, processing, and report generation."""

    def __init__(
        self,
        domain_name: str,
        profile_name: str = "default",
        depth: str = "default",
        days: int = 30,
    ):
        """Initialize orchestrator.

        Args:
            domain_name: Name of the domain to use
            profile_name: Name of the profile to use
            depth: Collection depth ('quick', 'default', 'deep')
            days: Number of days to look back
        """
        self.domain_name = domain_name
        self.profile_name = profile_name
        self.depth = depth
        self.days = days

        # Load configurations
        self.config = env.get_config()
        self.domain = load_domain(domain_name)
        self.profile = load_profile(self.domain, profile_name)

        # Date range
        self.from_date, self.to_date = dates.get_date_range(days)

        # Loaded collectors and report generators
        self._collectors: List[Collector] = []
        self._report_generators: Dict[str, ReportGenerator] = {}

    def discover_collectors(self) -> List[Collector]:
        """Discover and instantiate available collectors for the domain."""
        collectors = []

        for collector_def in self.domain.collectors:
            module_path = collector_def.get("module", "")
            collector_type = collector_def.get("type", "")

            if not module_path:
                continue

            try:
                collector = self._load_collector(module_path, collector_type)
                if collector and collector.is_available():
                    collectors.append(collector)
            except Exception as e:
                if env.is_debug():
                    print(f"[DEBUG] Failed to load collector {module_path}: {e}", file=sys.stderr)

        self._collectors = collectors
        return collectors

    def preflight_check(self) -> Dict[str, Any]:
        """Check which collectors are available and report missing keys.

        Returns:
            Dict with:
                - available: list of ready collector info
                - unavailable: list of collectors with missing keys
                - warnings: human-readable warning messages
        """
        results: Dict[str, Any] = {
            "available": [],
            "unavailable": [],
            "warnings": [],
        }

        for collector_def in self.domain.collectors:
            module_path = collector_def.get("module", "")
            collector_type = collector_def.get("type", "")

            if not module_path:
                continue

            try:
                collector = self._load_collector(module_path, collector_type)
                if collector is None:
                    results["unavailable"].append({
                        "name": module_path,
                        "type": collector_type,
                        "reason": "Failed to load",
                    })
                    continue

                # Check API key requirements
                missing_keys = collector.get_missing_keys(self.config)

                if missing_keys and not collector.REQUIRES_ANY_KEY:
                    # All keys required, some missing
                    results["unavailable"].append({
                        "name": collector.name,
                        "type": collector_type,
                        "missing_keys": missing_keys,
                    })
                    results["warnings"].append(
                        f"⚠ {collector.name} unavailable: missing {', '.join(missing_keys)}"
                    )
                elif collector.REQUIRES_ANY_KEY and not collector.is_available():
                    # Needs any one key, none present
                    results["unavailable"].append({
                        "name": collector.name,
                        "type": collector_type,
                        "missing_keys": collector.REQUIRED_API_KEYS,
                        "requires_any": True,
                    })
                    results["warnings"].append(
                        f"⚠ {collector.name} unavailable: needs one of {', '.join(collector.REQUIRED_API_KEYS)}"
                    )
                elif collector.is_available():
                    results["available"].append({
                        "name": collector.name,
                        "type": collector_type,
                    })
            except Exception as e:
                results["unavailable"].append({
                    "name": module_path,
                    "type": collector_type,
                    "reason": str(e),
                })

        return results

    def print_preflight_report(self) -> None:
        """Print human-readable preflight status."""
        check = self.preflight_check()

        print("\nCollector Status:")
        for item in check["available"]:
            print(f"  ✓ {item['name']} ({item['type']})")

        for item in check["unavailable"]:
            if "missing_keys" in item:
                if item.get("requires_any"):
                    keys = " or ".join(item["missing_keys"])
                    print(f"  ✗ {item['name']} (needs one of: {keys})")
                else:
                    keys = ", ".join(item["missing_keys"])
                    print(f"  ✗ {item['name']} (missing: {keys})")
            else:
                print(f"  ✗ {item.get('name', 'Unknown')} ({item.get('reason', 'failed to load')})")

        print()

    def _load_collector(self, module_path: str, collector_type: str) -> Optional[Collector]:
        """Load a collector from module path."""
        try:
            # Add project root to path if needed
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            module = importlib.import_module(module_path)

            # Look for collector class
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, Collector)
                    and obj is not Collector
                    and hasattr(obj, "collector_type")
                ):
                    # Check if this is the right type
                    instance = obj(self.config)
                    if instance.collector_type == collector_type or not collector_type:
                        return instance

            return None
        except Exception as e:
            if env.is_debug():
                print(f"[DEBUG] Collector load error: {e}", file=sys.stderr)
            return None

    def run_collectors(self, max_workers: int = 5) -> Dict[str, CollectorResult]:
        """Run all available collectors in parallel.

        Args:
            max_workers: Maximum number of parallel collectors

        Returns:
            Dict mapping collector type to result
        """
        if not self._collectors:
            self.discover_collectors()

        results: Dict[str, CollectorResult] = {}

        def run_collector(collector: Collector) -> Tuple[str, CollectorResult]:
            try:
                result = collector.collect(
                    self.profile,
                    self.from_date,
                    self.to_date,
                    self.depth,
                )
                return collector.collector_type, result
            except Exception as e:
                return collector.collector_type, CollectorResult(
                    items=[],
                    sources=[],
                    error=f"Collector error: {e}",
                )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_collector, c): c for c in self._collectors
            }

            for future in as_completed(futures):
                collector_type, result = future.result()
                results[collector_type] = result

        return results

    def process_items(
        self, collector_results: Dict[str, CollectorResult]
    ) -> Dict[str, List[schema.ItemType]]:
        """Process collected items: filter, score, sort, dedupe.

        Args:
            collector_results: Results from collectors

        Returns:
            Dict mapping collector type to processed items
        """
        processed: Dict[str, List[schema.ItemType]] = {}

        for collector_type, result in collector_results.items():
            if not result.success or not result.items:
                processed[collector_type] = []
                continue

            items = result.items

            # Filter by date range
            items = normalize.filter_by_date_range(
                items, self.from_date, self.to_date
            )

            # Score items based on type
            if collector_type == "news":
                items = score.score_news_items(items)
            elif collector_type == "financial":
                items = score.score_financial_items(items)
            elif collector_type == "social":
                items = score.score_social_items(items)
            elif collector_type == "awards":
                items = score.score_award_items(items)
            elif collector_type == "pe_activity":
                items = score.score_pe_items(items)

            # Sort by score
            items = score.sort_items(items)

            # Dedupe
            items = dedupe.dedupe_items(items)

            processed[collector_type] = items

        return processed

    def generate_report(
        self,
        report_type: str,
        processed_items: Dict[str, List[schema.ItemType]],
    ) -> schema.Report:
        """Generate a report from processed items.

        Args:
            report_type: Type of report to generate
            processed_items: Processed items by collector type

        Returns:
            Generated report
        """
        # Try to load report generator
        generator = self._load_report_generator(report_type)

        if generator:
            return generator.generate(processed_items, self.from_date, self.to_date)

        # Fallback: create basic report
        return self._create_basic_report(report_type, processed_items)

    def _load_report_generator(self, report_type: str) -> Optional[ReportGenerator]:
        """Load a report generator for the given type."""
        # Check cache
        if report_type in self._report_generators:
            return self._report_generators[report_type]

        # Find in domain reports
        for report_def in self.domain.reports:
            if report_def.get("type") == report_type:
                module_path = report_def.get("module", "")
                if module_path:
                    try:
                        project_root = Path(__file__).parent.parent
                        if str(project_root) not in sys.path:
                            sys.path.insert(0, str(project_root))

                        module = importlib.import_module(module_path)

                        for name in dir(module):
                            obj = getattr(module, name)
                            if (
                                isinstance(obj, type)
                                and issubclass(obj, ReportGenerator)
                                and obj is not ReportGenerator
                            ):
                                instance = obj(self.profile)
                                if instance.report_type == report_type:
                                    self._report_generators[report_type] = instance
                                    return instance
                    except Exception as e:
                        if env.is_debug():
                            print(f"[DEBUG] Report generator load error: {e}", file=sys.stderr)

        return None

    def _create_basic_report(
        self,
        report_type: str,
        processed_items: Dict[str, List[schema.ItemType]],
    ) -> schema.Report:
        """Create a basic report when no custom generator is available."""
        report = schema.Report(
            title=f"{self.domain.display_name} - {report_type.replace('_', ' ').title()}",
            domain=self.domain.name,
            profile=self.profile.name,
            report_type=report_type,
            generated_at=datetime.now(timezone.utc).isoformat(),
            date_range_from=self.from_date,
            date_range_to=self.to_date,
        )

        # Create sections for each collector type
        all_sources = []
        for collector_type, items in processed_items.items():
            if not items:
                continue

            section = schema.ReportSection(
                title=collector_type.replace("_", " ").title(),
                items=[i.to_dict() for i in items],
            )

            # Collect sources
            for item in items:
                url = getattr(item, "url", None) or getattr(item, "source_url", None)
                source_name = getattr(item, "source_name", None) or "Source"
                if url:
                    all_sources.append(
                        schema.Source(name=source_name, url=url)
                    )

            report.sections.append(section)

        # Dedupe sources
        seen_urls = set()
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                report.all_sources.append(source)

        return report

    def run(
        self,
        report_type: str = "daily_brief",
        show_progress: bool = True,
    ) -> OrchestratorResult:
        """Run full orchestration pipeline.

        Args:
            report_type: Type of report to generate
            show_progress: Whether to show progress spinners

        Returns:
            OrchestratorResult with report and metadata
        """
        errors = []

        # Initialize trace
        trace = RunTrace(
            domain=self.domain_name,
            profile=self.profile_name,
            report_type=report_type,
            depth=self.depth,
        )
        trace.start()

        # Initialize progress display
        progress = None
        if show_progress:
            progress = RunProgress(self.domain_name, self.profile_name, report_type)
            progress.show_header()

        # Discover collectors
        collectors = self.discover_collectors()
        if not collectors:
            errors.append("No collectors available")

        # Run collectors with tracing
        collector_results = self._run_collectors_with_trace(
            trace, progress, max_workers=5
        )

        # Check for collector errors
        for ctype, result in collector_results.items():
            if result.error:
                errors.append(f"{ctype}: {result.error}")

        # Process items
        if progress:
            progress.show_processing()

        processed_items = self.process_items(collector_results)

        if progress:
            progress.end_processing()

        # Generate report
        try:
            report = self.generate_report(report_type, processed_items)
            report.errors = errors
        except Exception as e:
            errors.append(f"Report generation failed: {e}")
            report = None

        # Complete trace
        trace.complete()

        # Show completion
        if progress:
            total_items = sum(len(items) for items in processed_items.values())
            progress.show_complete(total_items)

        return OrchestratorResult(
            report=report,
            collector_results=collector_results,
            errors=errors,
            trace=trace,
        )

    def _run_collectors_with_trace(
        self,
        trace: RunTrace,
        progress: Optional[RunProgress],
        max_workers: int = 5,
    ) -> Dict[str, CollectorResult]:
        """Run collectors with tracing and progress display.

        Args:
            trace: RunTrace to populate
            progress: Optional progress display
            max_workers: Maximum parallel workers

        Returns:
            Dict mapping collector type to result
        """
        if not self._collectors:
            self.discover_collectors()

        results: Dict[str, CollectorResult] = {}

        def run_collector(collector: Collector) -> Tuple[str, CollectorResult, CollectorTrace]:
            # Create collector trace
            collector_trace = CollectorTrace(
                name=collector.name,
                collector_type=collector.collector_type,
            )

            try:
                # Run collection within tracing context
                with TracingContext(collector_trace):
                    result = collector.collect(
                        self.profile,
                        self.from_date,
                        self.to_date,
                        self.depth,
                    )
                    collector_trace.complete(
                        items_collected=len(result.items),
                        success=result.success,
                        error=result.error,
                    )
            except Exception as e:
                collector_trace.complete(success=False, error=str(e))
                result = CollectorResult(
                    items=[],
                    sources=[],
                    error=f"Collector error: {e}",
                )

            return collector.collector_type, result, collector_trace

        # Run collectors in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all collectors
            future_to_collector = {}
            for collector in self._collectors:
                if progress:
                    progress.start_collector(collector.name, collector.collector_type)
                future = executor.submit(run_collector, collector)
                future_to_collector[future] = collector

            # Process results as they complete
            for future in as_completed(future_to_collector):
                collector = future_to_collector[future]
                collector_type, result, collector_trace = future.result()

                # Add to results
                results[collector_type] = result
                trace.add_collector_trace(collector_trace)

                # Update progress
                if progress:
                    progress.end_collector(
                        collector.name,
                        len(result.items),
                        collector_trace.duration_ms,
                        success=result.success,
                        error=result.error,
                    )

        return results


def run_moltpulse(
    domain: str,
    profile: str = "default",
    report_type: str = "daily_brief",
    depth: str = "default",
    days: int = 30,
    show_progress: bool = True,
) -> OrchestratorResult:
    """Convenience function to run MoltPulse.

    Args:
        domain: Domain name
        profile: Profile name
        report_type: Type of report
        depth: Collection depth
        days: Days to look back
        show_progress: Whether to show progress spinners

    Returns:
        OrchestratorResult
    """
    orchestrator = Orchestrator(
        domain_name=domain,
        profile_name=profile,
        depth=depth,
        days=days,
    )
    return orchestrator.run(report_type, show_progress=show_progress)
