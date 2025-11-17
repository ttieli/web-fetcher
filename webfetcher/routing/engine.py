"""
Routing Engine for Web Fetcher

Evaluates routing rules and selects appropriate fetcher for each URL.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from functools import lru_cache

from .config_loader import ConfigLoader
from .matchers import create_matcher

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """
    Represents a routing decision for a URL.

    Attributes:
        fetcher: Selected fetcher (urllib, selenium, manual_chrome)
        rule_name: Name of the matching rule
        priority: Priority of the matching rule
        reason: Explanation for this routing choice
        cached: Whether this decision came from cache
    """
    fetcher: str
    rule_name: str
    priority: int
    reason: str = ""
    cached: bool = False


class RoutingEngine:
    """
    Main routing engine that evaluates rules and selects fetcher.

    Features:
        - Priority-based rule evaluation
        - LRU caching for performance
        - Thread-safe hot reload
        - Comprehensive logging

    Usage:
        engine = RoutingEngine()
        decision = engine.evaluate("https://example.com")
        print(f"Use {decision.fetcher} because: {decision.reason}")
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize routing engine.

        Args:
            config_path: Path to routing.yaml (optional, uses default if not provided)
        """
        self.config_loader = ConfigLoader(config_path)
        self._lock = threading.RLock()
        self._compiled_rules: List[Tuple[dict, Any]] = []
        self._stats = {
            'total_evaluations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_reload': time.time()
        }

        # Load and compile rules
        self._compile_rules()

    def _compile_rules(self) -> None:
        """
        Load configuration and compile matchers for each rule.

        This is called during initialization and on reload.
        Compiles regex patterns once for efficiency.
        """
        with self._lock:
            try:
                rules = self.config_loader.get_rules()
                self._compiled_rules = []

                for rule in rules:
                    # Only include enabled rules
                    if not rule.get('enabled', True):
                        continue

                    # Create matcher for this rule's conditions
                    conditions = rule.get('conditions', {})
                    matcher = create_matcher(conditions)

                    # Store rule with its compiled matcher
                    self._compiled_rules.append((rule, matcher))

                logger.info(f"Compiled {len(self._compiled_rules)} routing rules")

            except Exception as e:
                logger.error(f"Failed to compile rules: {e}")
                self._compiled_rules = []

    def evaluate(self, url: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Evaluate routing rules for a given URL.

        Args:
            url: URL to route
            context: Optional context (error info, headers, etc.)

        Returns:
            RoutingDecision with selected fetcher and metadata

        Example:
            >>> engine = RoutingEngine()
            >>> decision = engine.evaluate("https://www.cebbank.com.cn/site/test")
            >>> print(decision.fetcher)  # "manual_chrome"
            >>> print(decision.rule_name)  # "CEB Bank Anti-Bot Protection"
        """
        with self._lock:
            self._stats['total_evaluations'] += 1

            # Check cache first
            cached_decision = self._check_cache(url, context)
            if cached_decision:
                self._stats['cache_hits'] += 1
                return cached_decision

            self._stats['cache_misses'] += 1

            # Evaluate rules in priority order (already sorted by ConfigLoader)
            for rule, matcher in self._compiled_rules:
                try:
                    if matcher.matches(url, context):
                        # Rule matched! Create decision
                        action = rule['action']
                        decision = RoutingDecision(
                            fetcher=action['fetcher'],
                            rule_name=rule['name'],
                            priority=rule['priority'],
                            reason=action.get('reason', 'No reason provided'),
                            cached=False
                        )

                        # Log decision
                        logger.info(
                            f"Routing decision for {url}: {decision.fetcher} "
                            f"(rule: {decision.rule_name}, priority: {decision.priority})"
                        )

                        # Cache decision
                        self._cache_decision(url, context, decision)

                        return decision

                except Exception as e:
                    logger.warning(f"Error evaluating rule '{rule['name']}': {e}")
                    continue

            # No rule matched - use default fetcher
            default_fetcher = self.config_loader.get_global_settings().get('default_fetcher', 'urllib')
            decision = RoutingDecision(
                fetcher=default_fetcher,
                rule_name="default",
                priority=0,
                reason="No matching rule, using default fetcher",
                cached=False
            )

            logger.info(f"No matching rule for {url}, using default: {default_fetcher}")
            return decision

    def _check_cache(self, url: str, context: Optional[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """
        Check if routing decision is cached.

        Args:
            url: URL to check
            context: Optional context

        Returns:
            Cached decision if found, None otherwise
        """
        # Simple implementation - can be enhanced with LRU cache
        # For now, we don't cache to ensure fresh decisions
        # TODO: Implement LRU cache with TTL
        return None

    def _cache_decision(self, url: str, context: Optional[Dict[str, Any]], decision: RoutingDecision) -> None:
        """
        Cache a routing decision.

        Args:
            url: URL that was routed
            context: Context used for decision
            decision: Routing decision to cache
        """
        # Simple implementation - can be enhanced with LRU cache
        # For now, no caching implemented
        # TODO: Implement LRU cache with TTL
        pass

    def reload(self) -> None:
        """
        Reload configuration and recompile rules.

        This is thread-safe and atomic - ongoing evaluations
        continue with old rules until reload completes.
        """
        logger.info("Reloading routing configuration...")
        try:
            # Force reload configuration
            self.config_loader.reload()

            # Recompile rules
            self._compile_rules()

            # Update stats
            with self._lock:
                self._stats['last_reload'] = time.time()

            logger.info("Configuration reloaded successfully")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get routing engine statistics.

        Returns:
            Dictionary with stats including evaluations, cache performance, etc.
        """
        with self._lock:
            return {
                **self._stats,
                'active_rules': len(self._compiled_rules),
                'cache_hit_rate': (
                    self._stats['cache_hits'] / max(self._stats['total_evaluations'], 1)
                ) * 100
            }
