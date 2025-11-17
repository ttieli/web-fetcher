"""
URL Matching Logic for Routing System

Provides various matcher implementations for rule conditions.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BaseMatcher:
    """Base class for all matchers."""

    def matches(self, url: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if URL matches this condition.

        Args:
            url: URL to match against
            context: Optional context information (errors, headers, etc.)

        Returns:
            True if matches, False otherwise
        """
        raise NotImplementedError


class DomainMatcher(BaseMatcher):
    """
    Matches URLs by domain name.

    Examples:
        - "example.com" matches "https://example.com/path"
        - "sub.example.com" matches "https://sub.example.com"
    """

    def __init__(self, domain: str):
        """
        Initialize domain matcher.

        Args:
            domain: Domain to match (e.g., "example.com")
        """
        self.domain = domain.lower()

    def matches(self, url: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if URL's domain matches target domain."""
        try:
            parsed = urlparse(url)
            url_domain = parsed.netloc.lower()

            # Exact match
            if url_domain == self.domain:
                return True

            # Subdomain match (e.g., www.example.com matches example.com)
            if url_domain.endswith('.' + self.domain):
                return True

            return False
        except Exception as e:
            logger.warning(f"Domain matching error for {url}: {e}")
            return False


class DomainListMatcher(BaseMatcher):
    """
    Matches URLs against a list of domains.

    Examples:
        - ["example.com", "test.com"] matches both domains
    """

    def __init__(self, domain_list: List[str]):
        """
        Initialize domain list matcher.

        Args:
            domain_list: List of domains to match
        """
        self.matchers = [DomainMatcher(d) for d in domain_list]

    def matches(self, url: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if URL matches any domain in the list."""
        return any(m.matches(url, context) for m in self.matchers)


class PatternMatcher(BaseMatcher):
    """
    Matches URLs by regex pattern.

    Examples:
        - ".*\\.pdf$" matches PDF files
        - ".*/api/.*" matches API endpoints
    """

    def __init__(self, pattern: str):
        """
        Initialize pattern matcher.

        Args:
            pattern: Regex pattern to match against URL
        """
        self.pattern = pattern
        try:
            self.regex = re.compile(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            # Create a matcher that never matches
            self.regex = re.compile(r'(?!.*)')

    def matches(self, url: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if URL matches the regex pattern."""
        try:
            return bool(self.regex.search(url))
        except Exception as e:
            logger.warning(f"Pattern matching error for {url}: {e}")
            return False


class AlwaysMatcher(BaseMatcher):
    """
    Always matches (for default rules).

    Used for catch-all default rules at lowest priority.
    """

    def matches(self, url: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Always returns True."""
        return True


class CompositeMatcher(BaseMatcher):
    """
    Combines multiple matchers with AND logic.

    All conditions must match for the rule to match.
    """

    def __init__(self, matchers: List[BaseMatcher]):
        """
        Initialize composite matcher.

        Args:
            matchers: List of matchers to combine
        """
        self.matchers = matchers

    def matches(self, url: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if URL matches all matchers."""
        return all(m.matches(url, context) for m in self.matchers)


def create_matcher(conditions: Dict[str, Any]) -> BaseMatcher:
    """
    Factory function to create matcher from conditions dict.

    Args:
        conditions: Conditions dictionary from routing rule

    Returns:
        Appropriate matcher instance

    Examples:
        {"domain": "example.com"} -> DomainMatcher
        {"domain_list": ["a.com", "b.com"]} -> DomainListMatcher
        {"url_pattern": ".*\\.pdf$"} -> PatternMatcher
        {"always": true} -> AlwaysMatcher
    """
    matchers = []

    # Domain condition
    if 'domain' in conditions:
        matchers.append(DomainMatcher(conditions['domain']))

    # Domain list condition
    if 'domain_list' in conditions:
        matchers.append(DomainListMatcher(conditions['domain_list']))

    # URL pattern condition
    if 'url_pattern' in conditions:
        matchers.append(PatternMatcher(conditions['url_pattern']))

    # Always condition (for default rules)
    if conditions.get('always', False):
        return AlwaysMatcher()

    # If multiple conditions, combine with AND
    if len(matchers) == 0:
        logger.warning(f"No valid conditions found: {conditions}")
        return AlwaysMatcher()  # Fallback to always match
    elif len(matchers) == 1:
        return matchers[0]
    else:
        return CompositeMatcher(matchers)
