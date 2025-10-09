# Task 001: 性能监控与指标仪表板 / Performance Monitoring and Metrics Dashboard

## 任务状态 / Task Status
**⏳ PENDING** - 待开始 / Ready to Start

## 优先级 / Priority
**HIGH** (Next Sprint Priority / 下一阶段优先任务)

## 预计工时 / Estimated Hours
6 hours (实时监控系统 / Real-time Monitoring System)

## Description / 描述

### 中文描述
建立全面的性能监控系统，实时跟踪获取器性能、错误率、响应时间等关键指标。系统将提供可视化仪表板，帮助识别性能瓶颈、预测问题并优化系统配置。这将使团队能够主动管理系统健康状况，而非被动响应问题。

### English Description
Establish a comprehensive performance monitoring system that tracks fetcher performance, error rates, response times, and other key metrics in real-time. The system will provide a visual dashboard to help identify performance bottlenecks, predict issues, and optimize system configuration. This will enable the team to proactively manage system health rather than reactively responding to problems.

## Technical Requirements / 技术要求

### 1. Metrics Collection Framework / 指标收集框架

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
import sqlite3
from pathlib import Path

@dataclass
class FetchMetrics:
    """Enhanced metrics for comprehensive monitoring."""
    # Basic info
    url: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Performance metrics
    total_time: float = 0
    urllib_time: Optional[float] = None
    selenium_time: Optional[float] = None
    parser_time: Optional[float] = None

    # Method tracking
    primary_method: str = "urllib"  # urllib, selenium, cache
    fallback_used: bool = False
    fallback_reason: Optional[str] = None

    # Error tracking
    error_count: int = 0
    error_types: List[str] = field(default_factory=list)
    ssl_error: bool = False

    # Retry tracking
    retry_count: int = 0
    retry_delays: List[float] = field(default_factory=list)

    # Content metrics
    html_size_bytes: int = 0
    markdown_size_bytes: int = 0
    image_count: int = 0
    link_count: int = 0

    # Domain info
    domain: str = ""
    is_problematic_domain: bool = False

    # Success tracking
    success: bool = False
    partial_success: bool = False

class MetricsCollector:
    """Centralized metrics collection and storage."""

    def __init__(self, db_path: Path = Path("metrics.db")):
        self.db_path = db_path
        self.current_metrics: Dict[str, FetchMetrics] = {}
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for metrics storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                domain TEXT,
                total_time REAL,
                primary_method TEXT,
                fallback_used BOOLEAN,
                error_count INTEGER,
                retry_count INTEGER,
                success BOOLEAN,
                html_size INTEGER,
                markdown_size INTEGER,
                metadata JSON
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON fetch_metrics(timestamp);
            CREATE INDEX IF NOT EXISTS idx_domain ON fetch_metrics(domain);
            CREATE INDEX IF NOT EXISTS idx_success ON fetch_metrics(success);
        """)

        conn.commit()
        conn.close()

    def record_fetch(self, metrics: FetchMetrics):
        """Record fetch metrics to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        metadata = {
            "error_types": metrics.error_types,
            "fallback_reason": metrics.fallback_reason,
            "urllib_time": metrics.urllib_time,
            "selenium_time": metrics.selenium_time,
            "parser_time": metrics.parser_time,
            "ssl_error": metrics.ssl_error,
            "image_count": metrics.image_count,
            "link_count": metrics.link_count
        }

        cursor.execute("""
            INSERT INTO fetch_metrics (
                url, domain, total_time, primary_method,
                fallback_used, error_count, retry_count,
                success, html_size, markdown_size, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.url,
            metrics.domain,
            metrics.total_time,
            metrics.primary_method,
            metrics.fallback_used,
            metrics.error_count,
            metrics.retry_count,
            metrics.success,
            metrics.html_size_bytes,
            metrics.markdown_size_bytes,
            json.dumps(metadata)
        ))

        conn.commit()
        conn.close()
```

### 2. Real-time Analytics Engine / 实时分析引擎

```python
class PerformanceAnalyzer:
    """Analyze performance metrics and identify patterns."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def get_domain_stats(self, domain: str, hours: int = 24) -> Dict:
        """Get performance statistics for a specific domain."""
        conn = sqlite3.connect(self.collector.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                AVG(total_time) as avg_response_time,
                MAX(total_time) as max_response_time,
                MIN(total_time) as min_response_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                SUM(CASE WHEN fallback_used = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as fallback_rate,
                AVG(retry_count) as avg_retries,
                AVG(html_size) as avg_html_size
            FROM fetch_metrics
            WHERE domain = ?
                AND timestamp > datetime('now', '-' || ? || ' hours')
        """, (domain, hours))

        result = cursor.fetchone()
        conn.close()

        return {
            "domain": domain,
            "total_requests": result[0],
            "avg_response_time": round(result[1], 2) if result[1] else 0,
            "max_response_time": round(result[2], 2) if result[2] else 0,
            "min_response_time": round(result[3], 2) if result[3] else 0,
            "success_rate": round(result[4], 1) if result[4] else 0,
            "fallback_rate": round(result[5], 1) if result[5] else 0,
            "avg_retries": round(result[6], 2) if result[6] else 0,
            "avg_html_size": int(result[7]) if result[7] else 0
        }

    def identify_problematic_domains(self, threshold_success_rate: float = 50) -> List[Dict]:
        """Identify domains with poor performance."""
        conn = sqlite3.connect(self.collector.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                domain,
                COUNT(*) as request_count,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                AVG(total_time) as avg_time,
                GROUP_CONCAT(DISTINCT json_extract(metadata, '$.fallback_reason')) as reasons
            FROM fetch_metrics
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY domain
            HAVING success_rate < ?
                OR avg_time > 10
            ORDER BY success_rate ASC, request_count DESC
        """, (threshold_success_rate,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "domain": row[0],
                "request_count": row[1],
                "success_rate": round(row[2], 1),
                "avg_time": round(row[3], 2),
                "failure_reasons": row[4].split(',') if row[4] else []
            })

        conn.close()
        return results

    def get_method_comparison(self) -> Dict:
        """Compare performance across different fetch methods."""
        conn = sqlite3.connect(self.collector.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                primary_method,
                COUNT(*) as count,
                AVG(total_time) as avg_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM fetch_metrics
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY primary_method
        """)

        methods = {}
        for row in cursor.fetchall():
            methods[row[0]] = {
                "count": row[1],
                "avg_time": round(row[2], 2),
                "success_rate": round(row[3], 1)
            }

        conn.close()
        return methods
```

### 3. Dashboard Interface / 仪表板界面

```python
class MetricsDashboard:
    """Generate dashboard reports and visualizations."""

    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer

    def generate_text_report(self) -> str:
        """Generate a text-based performance report."""
        report = []
        report.append("=" * 60)
        report.append("Web Fetcher Performance Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)

        # Method comparison
        report.append("\n📊 Fetch Method Performance (Last 24 hours)")
        report.append("-" * 40)
        methods = self.analyzer.get_method_comparison()
        for method, stats in methods.items():
            report.append(f"{method.upper()}:")
            report.append(f"  Requests: {stats['count']}")
            report.append(f"  Avg Time: {stats['avg_time']}s")
            report.append(f"  Success Rate: {stats['success_rate']}%")

        # Problematic domains
        report.append("\n⚠️  Problematic Domains")
        report.append("-" * 40)
        problems = self.analyzer.identify_problematic_domains()
        for domain_info in problems[:10]:  # Top 10
            report.append(f"{domain_info['domain']}:")
            report.append(f"  Success Rate: {domain_info['success_rate']}%")
            report.append(f"  Avg Response: {domain_info['avg_time']}s")
            if domain_info['failure_reasons']:
                report.append(f"  Issues: {', '.join(domain_info['failure_reasons'])}")

        return "\n".join(report)

    def generate_json_metrics(self) -> Dict:
        """Generate JSON metrics for external monitoring systems."""
        return {
            "timestamp": datetime.now().isoformat(),
            "methods": self.analyzer.get_method_comparison(),
            "problematic_domains": self.analyzer.identify_problematic_domains(),
            "alerts": self.generate_alerts()
        }

    def generate_alerts(self) -> List[Dict]:
        """Generate alerts based on performance thresholds."""
        alerts = []

        # Check for high failure domains
        problems = self.analyzer.identify_problematic_domains(threshold_success_rate=30)
        for domain in problems:
            if domain['request_count'] > 10:
                alerts.append({
                    "severity": "high",
                    "type": "domain_failure",
                    "message": f"Domain {domain['domain']} has {domain['success_rate']}% success rate",
                    "data": domain
                })

        # Check method performance
        methods = self.analyzer.get_method_comparison()
        for method, stats in methods.items():
            if stats['avg_time'] > 15:
                alerts.append({
                    "severity": "medium",
                    "type": "slow_method",
                    "message": f"{method} method averaging {stats['avg_time']}s response time",
                    "data": stats
                })

        return alerts
```

### 4. Live Monitoring CLI / 实时监控CLI

```python
class LiveMonitor:
    """Live monitoring interface for real-time metrics."""

    def __init__(self, dashboard: MetricsDashboard):
        self.dashboard = dashboard
        self.running = False

    def start(self):
        """Start live monitoring display."""
        import curses
        import time

        def draw_screen(stdscr):
            curses.curs_set(0)  # Hide cursor
            stdscr.nodelay(1)   # Non-blocking input

            while self.running:
                stdscr.clear()
                height, width = stdscr.getmaxyx()

                # Header
                header = "🔍 Web Fetcher Live Monitor"
                stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD)

                # Get current metrics
                metrics = self.dashboard.generate_json_metrics()

                # Display method stats
                y = 2
                stdscr.addstr(y, 0, "Method Performance:", curses.A_BOLD)
                y += 1
                for method, stats in metrics['methods'].items():
                    line = f"  {method}: {stats['count']} reqs, {stats['avg_time']}s avg, {stats['success_rate']}% success"
                    stdscr.addstr(y, 0, line)
                    y += 1

                # Display alerts
                y += 1
                stdscr.addstr(y, 0, "Active Alerts:", curses.A_BOLD)
                y += 1
                for alert in metrics['alerts'][:5]:  # Show top 5 alerts
                    color = curses.A_NORMAL
                    if alert['severity'] == 'high':
                        color = curses.A_BOLD
                    stdscr.addstr(y, 0, f"  [{alert['severity'].upper()}] {alert['message']}", color)
                    y += 1

                # Refresh
                stdscr.addstr(height - 1, 0, "Press 'q' to quit, 'r' to refresh report")
                stdscr.refresh()

                # Check for input
                key = stdscr.getch()
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # Generate full report
                    report = self.dashboard.generate_text_report()
                    # Save to file
                    with open("performance_report.txt", "w") as f:
                        f.write(report)

                time.sleep(1)  # Update every second

        self.running = True
        curses.wrapper(draw_screen)
```

## Implementation Approach / 实施方案

### Phase 1: Metrics Infrastructure (2 hours) / 指标基础设施
1. Create `/src/metrics_collector.py` with MetricsCollector class
2. Set up SQLite database for metrics storage
3. Integrate metrics collection into webfetcher.py
4. Add metrics hooks to selenium_fetcher.py

### Phase 2: Analytics Engine (2 hours) / 分析引擎
1. Create `/src/performance_analyzer.py` with PerformanceAnalyzer
2. Implement domain performance analysis
3. Add method comparison analytics
4. Create alert generation logic

### Phase 3: Dashboard Creation (1 hour) / 仪表板创建
1. Create `/src/metrics_dashboard.py` with MetricsDashboard
2. Implement text report generation
3. Add JSON metrics export
4. Create alert formatting

### Phase 4: Live Monitoring (1 hour) / 实时监控
1. Create `/src/live_monitor.py` with LiveMonitor
2. Implement curses-based UI
3. Add real-time updates
4. Create keyboard shortcuts

## Dependencies / 依赖关系
- SQLite for metrics storage
- Optional: curses for live monitoring
- Integrates with all fetch methods

## Acceptance Criteria / 验收标准
- [ ] Metrics collected for every fetch operation
- [ ] Dashboard shows real-time performance data
- [ ] Problematic domains automatically identified
- [ ] Alerts generated for performance issues
- [ ] Historical data retained for trend analysis
- [ ] Export capability for external monitoring tools
- [ ] Live monitoring interface functional

## Files to Modify / 需修改文件

### New Files / 新文件
1. `/src/metrics_collector.py` - Metrics collection and storage
2. `/src/performance_analyzer.py` - Analytics engine
3. `/src/metrics_dashboard.py` - Dashboard generation
4. `/src/live_monitor.py` - Live monitoring interface
5. `/config/monitoring.yaml` - Monitoring configuration

### Modified Files / 修改文件
1. `/webfetcher.py` - Add metrics collection hooks
2. `/selenium_fetcher.py` - Report performance metrics
3. `/error_handler.py` - Include error metrics

## Testing Plan / 测试计划

### Unit Tests / 单元测试
```python
def test_metrics_collection():
    """Test metrics are properly collected and stored."""
    collector = MetricsCollector(db_path=":memory:")

    metrics = FetchMetrics(
        url="https://example.com",
        total_time=2.5,
        success=True,
        domain="example.com"
    )

    collector.record_fetch(metrics)

    # Verify storage
    conn = sqlite3.connect(collector.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fetch_metrics")
    assert cursor.fetchone()[0] == 1

def test_performance_analysis():
    """Test performance analyzer identifies issues."""
    collector = MetricsCollector(db_path=":memory:")
    analyzer = PerformanceAnalyzer(collector)

    # Add test data
    for i in range(10):
        metrics = FetchMetrics(
            url=f"https://slow-site.com/page{i}",
            domain="slow-site.com",
            total_time=15.0,  # Slow response
            success=i % 3 != 0,  # 66% success rate
        )
        collector.record_fetch(metrics)

    # Check problematic domain detection
    problems = analyzer.identify_problematic_domains()
    assert len(problems) > 0
    assert problems[0]['domain'] == 'slow-site.com'
```

## Configuration Example / 配置示例

```yaml
# config/monitoring.yaml
monitoring:
  # Database settings
  database:
    path: "metrics.db"
    retention_days: 30
    vacuum_interval: 7  # days

  # Collection settings
  collection:
    enabled: true
    sample_rate: 1.0  # Collect 100% of requests
    detailed_errors: true
    include_content_metrics: true

  # Analysis thresholds
  thresholds:
    slow_response: 10  # seconds
    low_success_rate: 50  # percent
    high_retry_count: 3
    high_error_rate: 0.1  # 10%

  # Dashboard settings
  dashboard:
    refresh_interval: 60  # seconds
    max_alerts: 20
    export_format: "json"  # json, csv, prometheus

  # Alerting
  alerts:
    enabled: true
    channels:
      - type: "log"
        level: "warning"
      - type: "file"
        path: "alerts.log"
      # Future: email, slack, webhook
```

## Risks and Mitigation / 风险与缓解

### Risk 1: Performance overhead / 性能开销
- **Description**: Metrics collection slows down fetching
- **Mitigation**: Async recording, sampling option, lightweight storage

### Risk 2: Storage growth / 存储增长
- **Description**: Metrics database grows too large
- **Mitigation**: Auto-rotation, configurable retention, vacuum schedule

### Risk 3: Alert fatigue / 警报疲劳
- **Description**: Too many alerts reduce effectiveness
- **Mitigation**: Smart thresholds, alert deduplication, severity levels

## Success Metrics / 成功指标

1. **Visibility**: 100% of fetch operations tracked
2. **Performance**: <1% overhead from monitoring
3. **Insights**: Identify 90% of performance issues proactively
4. **Actionability**: Generate <10 false positive alerts per day
5. **Adoption**: Dashboard used daily by team

## Future Enhancements / 未来增强

1. **Web UI**: Browser-based dashboard with charts
2. **Predictive Analytics**: ML-based performance prediction
3. **External Integration**: Prometheus, Grafana, DataDog
4. **Custom Metrics**: User-defined metrics and KPIs
5. **A/B Testing**: Compare configuration changes

---

**Created**: 2025-10-09
**Author**: Archy (Claude Code)
**Status**: Ready for Implementation
**Priority**: MEDIUM
**Dependencies**: None (can run independently)