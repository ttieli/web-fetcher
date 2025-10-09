# Task 9: 配置驱动的获取器路由系统 / Configuration-Driven Fetcher Routing System

## Priority / 优先级
**MEDIUM**

## Estimated Hours / 预计工时
5 hours

## Description / 描述

### 中文描述
建立一个完全由配置驱动的获取器路由系统，将所有路由逻辑从代码中抽离到配置文件。系统将支持基于域名、URL模式、内容类型等多维度的路由规则，并提供热重载、A/B测试、灰度发布等高级功能。这将使系统更加灵活、可维护，并支持无代码部署的路由策略更新。

### English Description
Establish a fully configuration-driven fetcher routing system that extracts all routing logic from code into configuration files. The system will support multi-dimensional routing rules based on domain, URL patterns, content types, etc., and provide advanced features like hot reload, A/B testing, and canary deployments. This will make the system more flexible, maintainable, and support no-code deployment of routing strategy updates.

## Technical Requirements / 技术要求

### 1. Configuration Schema / 配置架构

```yaml
# config/routing.yaml - Master routing configuration
version: 2.0
last_updated: 2025-10-09

# Global settings
global:
  default_fetcher: "auto"  # auto, urllib, selenium
  fallback_enabled: true
  max_fallback_attempts: 1
  cache_routing_decisions: true
  cache_ttl: 3600

# Routing rules (evaluated in order)
routing_rules:
  # Rule 1: Direct Selenium for known problematic SSL domains
  - id: "ssl_problematic_domains"
    priority: 100  # Higher priority = evaluated first
    enabled: true
    conditions:
      domains:
        - "cebbank.com.cn"
        - "icbc.com.cn"
        - "ccb.com"
        - "boc.cn"
    action:
      fetcher: "selenium"
      reason: "SSL legacy renegotiation issues"
      skip_fallback: true

  # Rule 2: JavaScript-heavy sites
  - id: "js_heavy_sites"
    priority: 90
    enabled: true
    conditions:
      domains:
        - "xiaohongshu.com"
        - "xhslink.com"
        - "douyin.com"
        - "tiktok.com"
      url_patterns:
        - ".*\\/spa\\/.*"  # Single Page Apps
        - ".*\\/#\\/.*"    # Hash routing
    action:
      fetcher: "selenium"
      reason: "JavaScript rendering required"

  # Rule 3: Static content sites
  - id: "static_content"
    priority: 80
    enabled: true
    conditions:
      domains:
        - "github.com"
        - "wikipedia.org"
        - "stackoverflow.com"
      content_types:
        - "documentation"
        - "wiki"
        - "blog"
    action:
      fetcher: "urllib"
      reason: "Static content, no JS needed"
      optimization:
        timeout: 10
        retries: 2

  # Rule 4: Government sites
  - id: "government_sites"
    priority: 70
    enabled: true
    conditions:
      domain_patterns:
        - ".*\\.gov\\.cn"
        - ".*\\.gov"
        - ".*\\.edu\\.cn"
    action:
      fetcher: "urllib"
      fallback_to: "selenium"
      reason: "Government sites may have legacy systems"
      optimization:
        ssl_verify: false
        legacy_ssl: true

  # Rule 5: API endpoints
  - id: "api_endpoints"
    priority: 60
    enabled: true
    conditions:
      url_patterns:
        - ".*/api/.*"
        - ".*/v[0-9]+/.*"
      headers_present:
        - "X-API-Key"
        - "Authorization"
    action:
      fetcher: "urllib"
      reason: "API endpoints don't need browser"
      skip_fallback: true

# A/B testing configuration
ab_testing:
  enabled: false
  experiments:
    - id: "selenium_optimization"
      traffic_percentage: 10
      control:
        fetcher: "urllib"
      variant:
        fetcher: "selenium"
      metrics:
        - "response_time"
        - "success_rate"

# Feature flags
feature_flags:
  smart_routing_v2: true
  error_learning: true
  performance_monitoring: true
  hot_reload: true

# Override rules (highest priority)
overrides:
  # Temporary overrides for debugging
  - url: "https://specific-test-site.com"
    fetcher: "selenium"
    expires: "2025-10-15"
    reason: "Debugging CSS issues"
```

### 2. Configuration Router Implementation / 配置路由器实现

```python
import yaml
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
from urllib.parse import urlparse
import threading
import logging

@dataclass
class RoutingRule:
    """Represents a single routing rule."""
    id: str
    priority: int
    enabled: bool
    conditions: Dict[str, Any]
    action: Dict[str, Any]

    def matches(self, url: str, headers: Optional[Dict] = None) -> bool:
        """Check if URL matches this rule's conditions."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Check domain exact match
        if 'domains' in self.conditions:
            if any(d in domain for d in self.conditions['domains']):
                return True

        # Check domain patterns
        if 'domain_patterns' in self.conditions:
            for pattern in self.conditions['domain_patterns']:
                if re.match(pattern, domain):
                    return True

        # Check URL patterns
        if 'url_patterns' in self.conditions:
            for pattern in self.conditions['url_patterns']:
                if re.search(pattern, url):
                    return True

        # Check headers
        if 'headers_present' in self.conditions and headers:
            required_headers = self.conditions['headers_present']
            if all(h in headers for h in required_headers):
                return True

        return False

class ConfigurationRouter:
    """
    Main configuration-driven router for fetcher selection.
    """

    def __init__(self, config_path: Path = Path("config/routing.yaml")):
        self.config_path = config_path
        self.config = {}
        self.rules: List[RoutingRule] = []
        self.last_reload = 0
        self.reload_lock = threading.Lock()
        self.decision_cache = {}  # URL -> (decision, timestamp)

        self.load_configuration()

        # Start hot reload thread if enabled
        if self.config.get('feature_flags', {}).get('hot_reload'):
            self.start_hot_reload()

    def load_configuration(self):
        """Load and parse configuration file."""
        with self.reload_lock:
            try:
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)

                # Parse routing rules
                self.rules = []
                for rule_config in self.config.get('routing_rules', []):
                    rule = RoutingRule(
                        id=rule_config['id'],
                        priority=rule_config.get('priority', 50),
                        enabled=rule_config.get('enabled', True),
                        conditions=rule_config.get('conditions', {}),
                        action=rule_config.get('action', {})
                    )
                    if rule.enabled:
                        self.rules.append(rule)

                # Sort by priority (higher first)
                self.rules.sort(key=lambda r: r.priority, reverse=True)

                self.last_reload = time.time()
                logging.info(f"Loaded {len(self.rules)} routing rules")

            except Exception as e:
                logging.error(f"Failed to load routing configuration: {e}")
                # Keep existing configuration if reload fails

    def start_hot_reload(self):
        """Start background thread for configuration hot reload."""
        def reload_worker():
            while True:
                time.sleep(60)  # Check every minute
                try:
                    # Check if config file has been modified
                    mtime = self.config_path.stat().st_mtime
                    if mtime > self.last_reload:
                        logging.info("Configuration change detected, reloading...")
                        self.load_configuration()
                        self.decision_cache.clear()  # Clear cache on reload
                except Exception as e:
                    logging.error(f"Hot reload error: {e}")

        thread = threading.Thread(target=reload_worker, daemon=True)
        thread.start()

    def route(self, url: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Determine routing for a given URL.

        Returns:
            Dict containing:
            - fetcher: Selected fetcher (urllib/selenium)
            - reason: Reason for selection
            - rule_id: ID of matching rule
            - fallback: Fallback option if primary fails
            - optimizations: Any optimization parameters
        """
        # Check cache first
        if self.config.get('global', {}).get('cache_routing_decisions'):
            cache_key = url
            if cache_key in self.decision_cache:
                decision, timestamp = self.decision_cache[cache_key]
                cache_ttl = self.config.get('global', {}).get('cache_ttl', 3600)
                if time.time() - timestamp < cache_ttl:
                    logging.debug(f"Using cached routing decision for {url}")
                    return decision

        # Check overrides first (highest priority)
        if 'overrides' in self.config:
            for override in self.config['overrides']:
                if override.get('url') == url:
                    # Check if override has expired
                    if 'expires' in override:
                        from datetime import datetime
                        expires = datetime.fromisoformat(override['expires'])
                        if datetime.now() < expires:
                            decision = {
                                'fetcher': override['fetcher'],
                                'reason': override.get('reason', 'Manual override'),
                                'rule_id': 'override',
                                'skip_fallback': True
                            }
                            self.cache_decision(url, decision)
                            return decision

        # Check A/B testing
        if self.should_ab_test(url):
            decision = self.get_ab_test_decision(url)
            if decision:
                self.cache_decision(url, decision)
                return decision

        # Evaluate routing rules
        for rule in self.rules:
            if rule.matches(url, headers):
                logging.debug(f"URL {url} matched rule: {rule.id}")
                decision = {
                    'fetcher': rule.action.get('fetcher', 'urllib'),
                    'reason': rule.action.get('reason', f'Matched rule {rule.id}'),
                    'rule_id': rule.id,
                    'fallback': rule.action.get('fallback_to'),
                    'skip_fallback': rule.action.get('skip_fallback', False),
                    'optimizations': rule.action.get('optimization', {})
                }
                self.cache_decision(url, decision)
                return decision

        # Default routing
        default_fetcher = self.config.get('global', {}).get('default_fetcher', 'auto')
        decision = {
            'fetcher': default_fetcher,
            'reason': 'Default routing',
            'rule_id': 'default',
            'fallback': 'selenium' if default_fetcher == 'urllib' else None
        }
        self.cache_decision(url, decision)
        return decision

    def cache_decision(self, url: str, decision: Dict):
        """Cache routing decision."""
        if self.config.get('global', {}).get('cache_routing_decisions'):
            self.decision_cache[url] = (decision, time.time())

    def should_ab_test(self, url: str) -> bool:
        """Determine if URL should be part of A/B test."""
        ab_config = self.config.get('ab_testing', {})
        if not ab_config.get('enabled'):
            return False

        # Simple hash-based traffic splitting
        import hashlib
        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
        return url_hash % 100 < 10  # 10% traffic

    def get_ab_test_decision(self, url: str) -> Optional[Dict]:
        """Get A/B test routing decision."""
        experiments = self.config.get('ab_testing', {}).get('experiments', [])
        if not experiments:
            return None

        # Use first active experiment
        experiment = experiments[0]

        # Randomly assign to control or variant
        import random
        is_variant = random.random() < (experiment.get('traffic_percentage', 50) / 100)

        if is_variant:
            return {
                'fetcher': experiment['variant']['fetcher'],
                'reason': f"A/B test variant: {experiment['id']}",
                'rule_id': f"ab_test_{experiment['id']}",
                'experiment_id': experiment['id'],
                'variant': 'variant'
            }
        else:
            return {
                'fetcher': experiment['control']['fetcher'],
                'reason': f"A/B test control: {experiment['id']}",
                'rule_id': f"ab_test_{experiment['id']}",
                'experiment_id': experiment['id'],
                'variant': 'control'
            }

    def get_statistics(self) -> Dict:
        """Get routing statistics."""
        stats = {
            'total_rules': len(self.rules),
            'cache_size': len(self.decision_cache),
            'last_reload': self.last_reload,
            'feature_flags': self.config.get('feature_flags', {}),
            'ab_tests_active': len(self.config.get('ab_testing', {}).get('experiments', [])),
            'rules_by_priority': {}
        }

        for rule in self.rules:
            priority_bucket = f"{(rule.priority // 10) * 10}-{(rule.priority // 10 + 1) * 10}"
            stats['rules_by_priority'][priority_bucket] = \
                stats['rules_by_priority'].get(priority_bucket, 0) + 1

        return stats
```

### 3. Integration with Webfetcher / 与Webfetcher集成

```python
# Modifications to webfetcher.py

# Initialize configuration router
config_router = ConfigurationRouter(Path("config/routing.yaml"))

def fetch_html_with_config_routing(url: str, ua: Optional[str] = None,
                                  timeout: int = 30, headers: Optional[Dict] = None) -> tuple[str, FetchMetrics]:
    """
    Fetch HTML using configuration-driven routing.
    """
    metrics = FetchMetrics(url=url, start_time=time.time())

    # Get routing decision from configuration
    routing_decision = config_router.route(url, headers)
    metrics.routing_rule = routing_decision['rule_id']
    metrics.routing_reason = routing_decision['reason']

    logging.info(f"Routing decision for {url}: {routing_decision['fetcher']} "
                f"(Rule: {routing_decision['rule_id']}, Reason: {routing_decision['reason']})")

    # Apply optimizations if specified
    if 'optimizations' in routing_decision:
        opts = routing_decision['optimizations']
        if 'timeout' in opts:
            timeout = opts['timeout']
        # Apply other optimizations...

    # Execute fetch based on routing decision
    primary_fetcher = routing_decision['fetcher']

    if primary_fetcher == 'selenium':
        return fetch_with_selenium(url, timeout, metrics)
    elif primary_fetcher == 'urllib':
        result = fetch_with_urllib(url, ua, timeout, metrics)

        # Check if we should fallback
        if not result[0] and not routing_decision.get('skip_fallback'):
            if routing_decision.get('fallback'):
                logging.info(f"Falling back to {routing_decision['fallback']}")
                return fetch_with_selenium(url, timeout, metrics)

        return result
    else:  # auto mode
        # Implement smart auto-selection logic
        return fetch_with_auto_selection(url, ua, timeout, metrics, routing_decision)

    return html, metrics
```

## Implementation Approach / 实施方案

### Phase 1: Configuration Schema Design (1 hour) / 配置架构设计
1. Create comprehensive routing.yaml schema
2. Define all routing condition types
3. Establish action specifications
4. Design override and A/B testing structures

### Phase 2: Router Implementation (2 hours) / 路由器实现
1. Create `/src/config_router.py` with ConfigurationRouter
2. Implement rule matching logic
3. Add caching mechanisms
4. Implement hot reload functionality

### Phase 3: Integration (1 hour) / 集成
1. Modify webfetcher.py to use configuration router
2. Update fetch functions to respect routing decisions
3. Add metrics tracking for routing decisions
4. Implement fallback logic

### Phase 4: Testing and Validation (1 hour) / 测试验证
1. Create comprehensive test suite
2. Validate all routing scenarios
3. Test hot reload functionality
4. Verify A/B testing logic

## Dependencies / 依赖关系
- PyYAML for configuration parsing
- Integrates with Task 1 (Direct routing)
- Works with Task 8 (Monitoring)

## Acceptance Criteria / 验收标准
- [ ] All routing logic externalized to configuration
- [ ] Hot reload works without service restart
- [ ] A/B testing framework functional
- [ ] Override rules take precedence
- [ ] Cache improves performance by >30%
- [ ] Configuration validation prevents errors
- [ ] Comprehensive logging of routing decisions

## Files to Modify / 需修改文件

### New Files / 新文件
1. `/config/routing.yaml` - Main routing configuration
2. `/src/config_router.py` - Configuration router implementation
3. `/src/routing_validator.py` - Configuration validation
4. `/tests/test_config_routing.py` - Test suite

### Modified Files / 修改文件
1. `/webfetcher.py` - Use configuration router
2. `/selenium_fetcher.py` - Respect routing optimizations
3. `/error_handler.py` - Report routing decisions in errors

## Testing Plan / 测试计划

### Unit Tests / 单元测试
```python
def test_rule_matching():
    """Test routing rule matching logic."""
    rule = RoutingRule(
        id="test_rule",
        priority=100,
        enabled=True,
        conditions={'domains': ['example.com']},
        action={'fetcher': 'selenium'}
    )

    assert rule.matches("https://example.com/page")
    assert not rule.matches("https://other.com/page")

def test_configuration_loading():
    """Test configuration file loading."""
    router = ConfigurationRouter(Path("test_routing.yaml"))
    assert len(router.rules) > 0
    assert router.config['version'] == '2.0'

def test_routing_decision():
    """Test routing decision making."""
    router = ConfigurationRouter()
    decision = router.route("https://www.cebbank.com.cn/")

    assert decision['fetcher'] == 'selenium'
    assert 'SSL' in decision['reason']
    assert decision['skip_fallback'] == True
```

### Integration Tests / 集成测试
```python
def test_hot_reload():
    """Test configuration hot reload."""
    router = ConfigurationRouter()
    initial_rules = len(router.rules)

    # Modify configuration file
    config = load_yaml("config/routing.yaml")
    config['routing_rules'].append({
        'id': 'test_new_rule',
        'priority': 150,
        'conditions': {'domains': ['newtest.com']},
        'action': {'fetcher': 'selenium'}
    })
    save_yaml("config/routing.yaml", config)

    # Wait for hot reload
    time.sleep(2)

    assert len(router.rules) > initial_rules
    decision = router.route("https://newtest.com/")
    assert decision['fetcher'] == 'selenium'
```

## Risks and Mitigation / 风险与缓解

### Risk 1: Configuration errors / 配置错误
- **Description**: Invalid configuration breaks routing
- **Mitigation**: Schema validation, safe defaults, graceful degradation

### Risk 2: Performance overhead / 性能开销
- **Description**: Rule evaluation slows down routing
- **Mitigation**: Caching, rule optimization, priority-based short-circuit

### Risk 3: Hot reload issues / 热重载问题
- **Description**: Configuration changes cause instability
- **Mitigation**: Atomic reload, validation before apply, rollback capability

## Success Metrics / 成功指标

1. **Flexibility**: 100% of routing logic in configuration
2. **Performance**: <5ms routing decision time
3. **Reliability**: Zero downtime during configuration updates
4. **Adoption**: 50% reduction in code changes for routing updates
5. **Testing**: 30% of traffic through A/B tests

## Future Enhancements / 未来增强

1. **GUI Configuration Editor**: Web interface for rule management
2. **Machine Learning Rules**: Auto-generate rules from patterns
3. **Multi-Environment Support**: Dev/staging/prod configurations
4. **Rule Templates**: Reusable rule components
5. **Audit Trail**: Track all configuration changes

---

**Created**: 2025-10-09
**Author**: Archy (Claude Code)
**Status**: Ready for Implementation
**Priority**: MEDIUM
**Dependencies**: Works with all other tasks