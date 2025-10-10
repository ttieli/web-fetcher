"""
Unit tests for Routing Engine

Tests rule evaluation, matching logic, and edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from routing.engine import RoutingEngine, RoutingDecision
from routing.matchers import (
    DomainMatcher,
    DomainListMatcher,
    PatternMatcher,
    AlwaysMatcher,
    CompositeMatcher,
    create_matcher
)


class TestMatchers:
    """Test URL matching logic."""

    def test_domain_matcher_exact(self):
        """Test exact domain matching."""
        matcher = DomainMatcher("example.com")
        assert matcher.matches("https://example.com/path")
        assert matcher.matches("http://example.com")
        assert not matcher.matches("https://other.com")

    def test_domain_matcher_subdomain(self):
        """Test subdomain matching."""
        matcher = DomainMatcher("example.com")
        assert matcher.matches("https://www.example.com/path")
        assert matcher.matches("https://sub.example.com")
        assert not matcher.matches("https://examplexcom.com")

    def test_domain_list_matcher(self):
        """Test domain list matching."""
        matcher = DomainListMatcher(["example.com", "test.com"])
        assert matcher.matches("https://example.com/path")
        assert matcher.matches("https://test.com/path")
        assert not matcher.matches("https://other.com")

    def test_pattern_matcher(self):
        """Test regex pattern matching."""
        matcher = PatternMatcher(r".*/api/.*")
        assert matcher.matches("https://example.com/api/users")
        assert matcher.matches("https://test.com/api/v1/data")
        assert not matcher.matches("https://example.com/web/page")

    def test_always_matcher(self):
        """Test always matcher."""
        matcher = AlwaysMatcher()
        assert matcher.matches("https://example.com")
        assert matcher.matches("https://anything.com")
        assert matcher.matches("invalid-url")

    def test_composite_matcher(self):
        """Test composite matcher with AND logic."""
        matcher = CompositeMatcher([
            DomainMatcher("example.com"),
            PatternMatcher(r".*/api/.*")
        ])
        assert matcher.matches("https://example.com/api/users")
        assert not matcher.matches("https://example.com/web/page")
        assert not matcher.matches("https://other.com/api/users")

    def test_create_matcher_domain(self):
        """Test matcher factory for domain condition."""
        matcher = create_matcher({"domain": "example.com"})
        assert isinstance(matcher, DomainMatcher)
        assert matcher.matches("https://example.com/path")

    def test_create_matcher_domain_list(self):
        """Test matcher factory for domain_list condition."""
        matcher = create_matcher({"domain_list": ["a.com", "b.com"]})
        assert isinstance(matcher, DomainListMatcher)
        assert matcher.matches("https://a.com/path")

    def test_create_matcher_pattern(self):
        """Test matcher factory for url_pattern condition."""
        matcher = create_matcher({"url_pattern": r".*/test/.*"})
        assert isinstance(matcher, PatternMatcher)
        assert matcher.matches("https://example.com/test/page")

    def test_create_matcher_always(self):
        """Test matcher factory for always condition."""
        matcher = create_matcher({"always": True})
        assert isinstance(matcher, AlwaysMatcher)
        assert matcher.matches("https://anything.com")

    def test_create_matcher_composite(self):
        """Test matcher factory for multiple conditions."""
        matcher = create_matcher({
            "domain": "example.com",
            "url_pattern": r".*/api/.*"
        })
        assert isinstance(matcher, CompositeMatcher)
        assert matcher.matches("https://example.com/api/users")
        assert not matcher.matches("https://example.com/web/page")


class TestRoutingEngine:
    """Test routing engine logic."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = RoutingEngine()
        assert engine is not None
        assert len(engine._compiled_rules) > 0

    def test_cebbank_routing(self):
        """Test routing for CEB Bank URL."""
        engine = RoutingEngine()
        decision = engine.evaluate("https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html")

        assert decision.fetcher == "manual_chrome"
        assert decision.rule_name == "CEB Bank Anti-Bot Protection"
        assert decision.priority == 100

    def test_xiaohongshu_routing(self):
        """Test routing for Xiaohongshu URL."""
        engine = RoutingEngine()
        decision = engine.evaluate("https://www.xiaohongshu.com/explore/123456")

        assert decision.fetcher == "selenium"
        assert decision.rule_name == "JavaScript-Heavy Sites"
        assert decision.priority == 50

    def test_weixin_routing(self):
        """Test routing for WeChat URL."""
        engine = RoutingEngine()
        decision = engine.evaluate("https://mp.weixin.qq.com/s/abc123")

        assert decision.fetcher == "selenium"
        assert decision.rule_name == "WeChat Articles"
        assert decision.priority == 50

    def test_default_routing(self):
        """Test default routing for unknown URL."""
        engine = RoutingEngine()
        decision = engine.evaluate("https://www.python.org")

        assert decision.fetcher == "urllib"
        assert decision.rule_name == "Default - Static Sites"
        assert decision.priority == 1

    def test_engine_reload(self):
        """Test engine reload functionality."""
        engine = RoutingEngine()
        initial_rules = len(engine._compiled_rules)

        engine.reload()

        assert len(engine._compiled_rules) == initial_rules

    def test_engine_stats(self):
        """Test engine statistics tracking."""
        engine = RoutingEngine()

        # Make some evaluations
        engine.evaluate("https://example.com")
        engine.evaluate("https://test.com")

        stats = engine.get_stats()
        assert stats['total_evaluations'] >= 2
        assert stats['active_rules'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
