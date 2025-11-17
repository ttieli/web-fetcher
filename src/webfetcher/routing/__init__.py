"""
Routing Module for Web Fetcher

Provides configuration-driven routing for fetcher selection.
"""

from .config_loader import ConfigLoader, ConfigurationError
from .engine import RoutingEngine, RoutingDecision
from .matchers import (
    BaseMatcher,
    DomainMatcher,
    DomainListMatcher,
    PatternMatcher,
    AlwaysMatcher,
    CompositeMatcher,
    create_matcher
)

__version__ = "1.0.0"
__all__ = [
    "ConfigLoader",
    "ConfigurationError",
    "RoutingEngine",
    "RoutingDecision",
    "BaseMatcher",
    "DomainMatcher",
    "DomainListMatcher",
    "PatternMatcher",
    "AlwaysMatcher",
    "CompositeMatcher",
    "create_matcher"
]
