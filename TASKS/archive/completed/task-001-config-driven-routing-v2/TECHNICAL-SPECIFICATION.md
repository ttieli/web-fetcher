# Technical Specification: Config-Driven Routing System
# 技术规范：配置驱动路由系统

## System Architecture Overview / 系统架构概述

### Component Diagram / 组件图

```
┌──────────────────────────────────────────────────────┐
│                    Web Fetcher                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────┐        ┌─────────────────┐         │
│  │ webfetcher │───────▶│ routing.engine  │         │
│  └────────────┘        └────────┬────────┘         │
│                                 │                    │
│                                 ▼                    │
│                      ┌──────────────────┐           │
│                      │ config_loader    │           │
│                      └────────┬─────────┘           │
│                                │                     │
│                                ▼                     │
│                      ┌──────────────────┐           │
│                      │ routing.yaml     │           │
│                      └──────────────────┘           │
└──────────────────────────────────────────────────────┘
```

### Data Flow / 数据流

1. **Request Input / 请求输入**: URL enters webfetcher / URL进入webfetcher
2. **Route Query / 路由查询**: webfetcher calls routing engine / webfetcher调用路由引擎
3. **Rule Evaluation / 规则评估**: Engine evaluates rules in priority order / 引擎按优先级评估规则
4. **Cache Check / 缓存检查**: LRU cache consulted for performance / 查询LRU缓存以提高性能
5. **Decision Output / 决策输出**: Fetcher type returned (urllib/selenium/manual_chrome) / 返回抓取器类型

## Configuration File Format / 配置文件格式

### routing.yaml Structure / routing.yaml结构

```yaml
# Config-Driven Routing Configuration
# 配置驱动路由配置
version: "1.0"

# Global settings / 全局设置
global:
  default_fetcher: "urllib"  # Default when no rules match / 无规则匹配时的默认值
  cache_ttl: 3600  # Cache time-to-live in seconds / 缓存生存时间（秒）
  enable_logging: true  # Enable detailed logging / 启用详细日志

# Routing rules (evaluated in priority order)
# 路由规则（按优先级顺序评估）
rules:
  - name: "rule_name"  # Unique identifier / 唯一标识符
    priority: 100  # Higher number = higher priority / 数字越大优先级越高
    conditions:  # All conditions must match / 所有条件必须匹配
      domain_pattern: "regex"  # Domain regex pattern / 域名正则模式
      url_pattern: "regex"  # URL regex pattern / URL正则模式
      content_type: "text/html"  # Expected content type / 预期内容类型
    action:
      fetcher: "selenium"  # Target fetcher / 目标抓取器
      reason: "Explanation"  # Human-readable reason / 可读的原因说明
      timeout: 30  # Optional override / 可选覆盖
      retry_count: 3  # Optional override / 可选覆盖
```

### JSON Schema Validation / JSON架构验证

The system uses `/config/routing_schema.json` for strict validation:
系统使用`/config/routing_schema.json`进行严格验证：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "rules"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "global": {
      "type": "object",
      "properties": {
        "default_fetcher": {
          "type": "string",
          "enum": ["urllib", "selenium", "manual_chrome"]
        },
        "cache_ttl": {
          "type": "integer",
          "minimum": 0
        },
        "enable_logging": {
          "type": "boolean"
        }
      }
    },
    "rules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "priority", "action"],
        "properties": {
          "name": {"type": "string"},
          "priority": {"type": "integer"},
          "conditions": {"type": "object"},
          "action": {"type": "object"}
        }
      }
    }
  }
}
```

## API Documentation / API文档

### Python API

#### RoutingEngine Class / RoutingEngine类

```python
from routing.engine import RoutingEngine

# Initialize engine / 初始化引擎
engine = RoutingEngine(config_path="/path/to/routing.yaml")

# Get routing decision / 获取路由决策
result = engine.get_route(url="https://example.com")
# Returns: {"fetcher": "urllib", "reason": "Default route", "rule": "default"}

# Reload configuration / 重载配置
engine.reload_config()

# Get statistics / 获取统计
stats = engine.get_stats()
# Returns: {"cache_hits": 100, "cache_misses": 20, "total_requests": 120}

# Clear cache / 清除缓存
engine.clear_cache()
```

#### ConfigLoader Class / ConfigLoader类

```python
from routing.config_loader import ConfigLoader

# Load and validate config / 加载并验证配置
loader = ConfigLoader()
config = loader.load_config("/path/to/routing.yaml")

# Validate configuration / 验证配置
is_valid = loader.validate_config(config)

# Get validation errors / 获取验证错误
errors = loader.get_validation_errors()
```

#### Matcher Utilities / 匹配器工具

```python
from routing.matchers import DomainMatcher, URLMatcher

# Domain matching / 域名匹配
domain_matcher = DomainMatcher(pattern=".*\\.bank\\..*")
is_match = domain_matcher.match("www.bank.com")  # True

# URL matching / URL匹配
url_matcher = URLMatcher(pattern=".*/api/.*")
is_match = url_matcher.match("https://example.com/api/data")  # True
```

## CLI Command Reference / CLI命令参考

### routing_ctl.py Usage / routing_ctl.py使用

```bash
# Basic usage / 基本用法
python scripts/routing_ctl.py [command] [options]
```

#### Commands / 命令

##### lint - Validate Configuration / 验证配置

```bash
python scripts/routing_ctl.py lint [--config PATH]

# Example / 示例
python scripts/routing_ctl.py lint --config config/routing.yaml

# Output / 输出
✓ Configuration valid
✓ Schema validation passed
✓ 5 rules loaded successfully
```

##### dry-run - Test Routing Decision / 测试路由决策

```bash
python scripts/routing_ctl.py dry-run URL [--config PATH] [--verbose]

# Example / 示例
python scripts/routing_ctl.py dry-run https://www.example.com --verbose

# Output / 输出
URL: https://www.example.com
Matched Rule: static_sites (priority: 50)
Decision: urllib
Reason: Static content site
Cache Status: MISS
Evaluation Time: 2.3ms
```

##### reload - Hot Reload Configuration / 热重载配置

```bash
python scripts/routing_ctl.py reload [--config PATH]

# Example / 示例
python scripts/routing_ctl.py reload

# Output / 输出
✓ Configuration reloaded successfully
✓ 5 rules active
✓ Cache cleared
```

##### stats - View Statistics / 查看统计

```bash
python scripts/routing_ctl.py stats [--format json|table]

# Example / 示例
python scripts/routing_ctl.py stats --format table

# Output / 输出
┌─────────────────┬────────┐
│ Metric          │ Value  │
├─────────────────┼────────┤
│ Total Requests  │ 1,234  │
│ Cache Hits      │ 1,100  │
│ Cache Misses    │ 134    │
│ Hit Rate        │ 89.1%  │
│ Avg Decision    │ 3.2ms  │
└─────────────────┴────────┘
```

##### test - Run Test Suite / 运行测试套件

```bash
python scripts/routing_ctl.py test [--url-file PATH]

# Example / 示例
python scripts/routing_ctl.py test --url-file tests/test_urls.txt

# Output / 输出
Testing 10 URLs...
✓ https://www.bank.com → selenium (expected)
✓ https://static.example.com → urllib (expected)
✓ https://spa.app.com → selenium (expected)
...
Results: 10/10 passed
```

## Integration Guide / 集成指南

### Step 1: Install Dependencies / 安装依赖

```bash
# No additional dependencies required / 无需额外依赖
# Uses Python standard library + existing project dependencies
# 使用Python标准库 + 现有项目依赖
```

### Step 2: Configure routing.yaml / 配置routing.yaml

```yaml
# config/routing.yaml
version: "1.0"

global:
  default_fetcher: "urllib"
  cache_ttl: 3600

rules:
  # Add your rules here / 在此添加规则
  - name: "javascript_heavy"
    priority: 90
    conditions:
      domain_pattern: ".*spa.*|.*app.*"
    action:
      fetcher: "selenium"
      reason: "JavaScript-heavy application"
```

### Step 3: Integrate with Code / 与代码集成

```python
# In your webfetcher.py or main application
from routing.engine import RoutingEngine

# Initialize once / 初始化一次
routing_engine = RoutingEngine("config/routing.yaml")

def fetch_url(url):
    # Get routing decision / 获取路由决策
    route = routing_engine.get_route(url)

    # Use appropriate fetcher / 使用适当的抓取器
    if route["fetcher"] == "selenium":
        return fetch_with_selenium(url)
    elif route["fetcher"] == "manual_chrome":
        return fetch_with_manual_chrome(url)
    else:
        return fetch_with_urllib(url)
```

### Step 4: Monitor and Optimize / 监控和优化

```bash
# Check statistics regularly / 定期检查统计
python scripts/routing_ctl.py stats

# Test new rules before deployment / 部署前测试新规则
python scripts/routing_ctl.py dry-run https://new-site.com

# Validate after changes / 更改后验证
python scripts/routing_ctl.py lint
```

## Troubleshooting Guide / 故障排除指南

### Common Issues and Solutions / 常见问题和解决方案

#### 1. Configuration Not Loading / 配置未加载

**Symptom / 症状**: `ConfigurationError: Failed to load routing.yaml`

**Solution / 解决方案**:
```bash
# Check file exists / 检查文件存在
ls -la config/routing.yaml

# Validate syntax / 验证语法
python scripts/routing_ctl.py lint

# Check permissions / 检查权限
chmod 644 config/routing.yaml
```

#### 2. Rules Not Matching / 规则不匹配

**Symptom / 症状**: Always using default fetcher / 始终使用默认抓取器

**Solution / 解决方案**:
```bash
# Test specific URL / 测试特定URL
python scripts/routing_ctl.py dry-run URL --verbose

# Check rule patterns / 检查规则模式
# Ensure regex patterns are correct / 确保正则表达式正确
```

#### 3. Performance Issues / 性能问题

**Symptom / 症状**: Slow routing decisions / 路由决策缓慢

**Solution / 解决方案**:
```python
# Increase cache TTL / 增加缓存TTL
global:
  cache_ttl: 7200  # 2 hours

# Optimize regex patterns / 优化正则模式
# Use simpler patterns when possible / 尽可能使用简单模式
```

#### 4. Cache Not Working / 缓存不工作

**Symptom / 症状**: High cache miss rate / 高缓存未命中率

**Solution / 解决方案**:
```bash
# Check cache statistics / 检查缓存统计
python scripts/routing_ctl.py stats

# Clear and rebuild cache / 清除并重建缓存
python scripts/routing_ctl.py reload
```

### Debug Mode / 调试模式

Enable detailed logging for troubleshooting:
启用详细日志进行故障排除：

```yaml
# In routing.yaml
global:
  enable_logging: true
  log_level: "DEBUG"  # INFO, WARNING, ERROR
```

```python
# In Python code
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization / 性能优化

### Caching Strategy / 缓存策略

The system uses an LRU (Least Recently Used) cache:
系统使用LRU（最近最少使用）缓存：

- **Default size / 默认大小**: 1000 entries / 1000条目
- **TTL / 生存时间**: Configurable (default 3600s) / 可配置（默认3600秒）
- **Hit rate target / 命中率目标**: >85%

### Rule Optimization Tips / 规则优化技巧

1. **Order by frequency / 按频率排序**: Most common patterns first / 最常见的模式优先
2. **Use specific patterns / 使用特定模式**: Avoid overly broad regex / 避免过于宽泛的正则
3. **Minimize conditions / 最小化条件**: Fewer conditions = faster evaluation / 条件越少=评估越快
4. **Cache-friendly URLs / 缓存友好的URL**: Normalize URLs before routing / 路由前规范化URL

### Benchmarks / 基准测试

```
Operation               | Time      | Notes
------------------------|-----------|------------------
Cold start              | 15ms      | First request
Cached decision         | <1ms      | From cache
Rule evaluation (avg)   | 3.2ms     | 5 rules
Config reload           | 8ms       | With validation
Cache clear             | <1ms      | Instant
```

## Security Considerations / 安全考虑

### Input Validation / 输入验证

- All URLs are validated before processing / 所有URL在处理前验证
- Regex patterns are compiled with timeout / 正则模式编译带超时
- Configuration files are schema-validated / 配置文件经过架构验证

### Access Control / 访问控制

- Configuration files should be read-only in production / 生产环境中配置文件应为只读
- CLI tools require appropriate permissions / CLI工具需要适当权限
- Logging excludes sensitive data / 日志排除敏感数据

## Migration Guide / 迁移指南

### From Hard-coded Rules / 从硬编码规则迁移

Before / 之前:
```python
if "bank" in url:
    use_selenium = True
elif "static" in url:
    use_selenium = False
```

After / 之后:
```yaml
rules:
  - name: "banks"
    conditions:
      domain_pattern: ".*bank.*"
    action:
      fetcher: "selenium"
```

### Gradual Migration Strategy / 渐进迁移策略

1. **Phase 1**: Add routing system alongside existing code / 在现有代码旁添加路由系统
2. **Phase 2**: Route subset of traffic through new system / 通过新系统路由部分流量
3. **Phase 3**: Monitor and optimize rules / 监控和优化规则
4. **Phase 4**: Complete migration and remove old code / 完成迁移并删除旧代码

## Appendix / 附录

### Example Configurations / 示例配置

#### Banking Sites / 银行网站
```yaml
- name: "banking_sites"
  priority: 100
  conditions:
    domain_pattern: ".*\\.(bank|banking|finance)\\.*"
  action:
    fetcher: "selenium"
    reason: "Financial sites require JavaScript"
    timeout: 45
```

#### Static Content / 静态内容
```yaml
- name: "static_content"
  priority: 30
  conditions:
    url_pattern: ".*\\.(pdf|jpg|png|css|js)$"
  action:
    fetcher: "urllib"
    reason: "Static files don't need browser"
```

#### SPA Applications / 单页应用
```yaml
- name: "spa_apps"
  priority: 80
  conditions:
    domain_pattern: ".*(react|vue|angular).*"
  action:
    fetcher: "selenium"
    reason: "SPA requires JavaScript execution"
```

### Glossary / 术语表

- **Fetcher / 抓取器**: Component that retrieves web content / 检索网页内容的组件
- **Routing / 路由**: Process of selecting appropriate fetcher / 选择适当抓取器的过程
- **Rule / 规则**: Configuration that maps conditions to actions / 将条件映射到操作的配置
- **Priority / 优先级**: Order in which rules are evaluated / 规则评估的顺序
- **Cache / 缓存**: Storage for recent routing decisions / 最近路由决策的存储

---

*Technical Specification Version 1.0*
*技术规范版本 1.0*

*Last Updated / 最后更新: 2025-10-10*