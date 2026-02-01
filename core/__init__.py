"""Moltos core framework - domain-agnostic intelligence engine."""

__version__ = "0.1.0"

from . import lib
from .collector_base import (
    Collector,
    CollectorResult,
    FinancialCollector,
    NewsCollector,
    SocialCollector,
    RSSCollector,
    AwardsCollector,
    PEActivityCollector,
)
from .delivery import deliver_report, DeliveryResult
from .domain_loader import DomainConfig, load_domain, list_domains, create_domain_skeleton
from .orchestrator import Orchestrator, OrchestratorResult, run_moltos
from .profile_loader import ProfileConfig, load_profile, list_profiles, create_profile
from .report_base import ReportGenerator, DailyBriefGenerator, WeeklyDigestGenerator

__all__ = [
    # Version
    "__version__",
    # Core classes
    "Orchestrator",
    "OrchestratorResult",
    "run_moltos",
    # Domain/Profile
    "DomainConfig",
    "ProfileConfig",
    "load_domain",
    "load_profile",
    "list_domains",
    "list_profiles",
    "create_domain_skeleton",
    "create_profile",
    # Collectors
    "Collector",
    "CollectorResult",
    "FinancialCollector",
    "NewsCollector",
    "SocialCollector",
    "RSSCollector",
    "AwardsCollector",
    "PEActivityCollector",
    # Reports
    "ReportGenerator",
    "DailyBriefGenerator",
    "WeeklyDigestGenerator",
    # Delivery
    "deliver_report",
    "DeliveryResult",
    # Lib
    "lib",
]
