"""MoltPulse core framework - domain-agnostic intelligence engine."""

__version__ = "0.1.0"

from . import lib
from .collector_base import (
    AwardsCollector,
    Collector,
    CollectorResult,
    FinancialCollector,
    NewsCollector,
    PEActivityCollector,
    RSSCollector,
    SocialCollector,
)
from .delivery import DeliveryResult, deliver_report
from .domain_loader import DomainConfig, create_domain_skeleton, list_domains, load_domain
from .orchestrator import Orchestrator, OrchestratorResult, run_moltpulse
from .profile_loader import ProfileConfig, create_profile, list_profiles, load_profile
from .report_base import DailyBriefGenerator, ReportGenerator, WeeklyDigestGenerator

__all__ = [
    # Version
    "__version__",
    # Core classes
    "Orchestrator",
    "OrchestratorResult",
    "run_moltpulse",
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
