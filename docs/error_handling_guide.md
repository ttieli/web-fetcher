# 错误处理指南 / Error Handling Guide

本指南详细介绍Web_Fetcher项目的统一错误处理框架。

## 1. 快速开始 / Quick Start

### 基本使用

error_handler模块已自动集成到webfetcher中，无需手动配置：

```python
# 自动错误处理示例
from webfetcher import fetch_html

try:
    html, metrics = fetch_html("https://example.com")
except Exception as e:
    # 错误已自动分类并生成FAILED_报告
    print(f"Fetch failed: {e}")
```

### 常见错误场景

1. **网络连接错误** - Connection refused, SSL errors
2. **浏览器初始化失败** - Chrome not found, ChromeDriver issues
3. **页面加载超时** - Slow network, heavy page
4. **权限错误** - Access denied
5. **依赖缺失** - Missing libraries
6. **操作超时** - General timeout
7. **未知错误** - Other exceptions

## 2. 错误分类体系 / Error Classification System

### 7大错误类别详解

#### 2.1 NETWORK_CONNECTION（网络连接）
- **识别特征**：connection refused, SSL, certificate, network
- **常见原因**：
  - 网络不可达
  - SSL证书问题
  - 防火墙阻止
- **解决方案**：
  - 检查网络连接
  - 验证SSL证书
  - 配置代理设置

#### 2.2 BROWSER_INIT（浏览器初始化）
- **识别特征**：Chrome, WebDriver, browser, launch
- **常见原因**：
  - Chrome未安装
  - ChromeDriver版本不匹配
  - 浏览器权限问题
- **解决方案**：
  - 安装/更新Chrome
  - 匹配ChromeDriver版本
  - 检查权限设置

#### 2.3 PAGE_LOAD（页面加载）
- **识别特征**：load, navigate, page, DOM
- **常见原因**：
  - 页面资源过大
  - JavaScript执行错误
  - 网络速度慢
- **解决方案**：
  - 增加超时时间
  - 使用快速网络
  - 禁用不必要的资源

#### 2.4 TIMEOUT（操作超时）
- **识别特征**：timeout, timed out, deadline
- **常见原因**：
  - 网络延迟高
  - 服务器响应慢
  - 超时设置过短
- **解决方案**：
  - 增加超时配置
  - 优化网络环境
  - 使用重试机制

#### 2.5 PERMISSION（权限错误）
- **识别特征**：permission, denied, access, unauthorized
- **常见原因**：
  - 文件系统权限
  - API访问限制
  - 系统安全策略
- **解决方案**：
  - 检查文件权限
  - 验证API密钥
  - 调整安全策略

#### 2.6 DEPENDENCY（依赖缺失）
- **识别特征**：import, module, not found, missing
- **常见原因**：
  - 未安装依赖库
  - Python版本不兼容
  - 环境配置错误
- **解决方案**：
  - pip install 缺失的包
  - 检查Python版本
  - 验证虚拟环境

#### 2.7 UNKNOWN（未知错误）
- **识别特征**：无法匹配其他类别
- **处理方式**：
  - 提供通用故障排除建议
  - 记录详细错误信息
  - 建议联系支持

### 分类决策树

```
异常发生
    |
    ├─ 检查异常类型（ConnectionError, TimeoutError等）
    |       └─ 匹配 → 返回对应类别
    |
    ├─ 检查错误消息模式（52个预定义模式）
    |       └─ 匹配 → 返回对应类别
    |
    └─ 无法匹配 → UNKNOWN
```

## 3. 集成指南 / Integration Guide

### 3.1 WebFetcher集成（已完成）

错误处理已自动集成到`generate_failure_markdown()`：

```python
# webfetcher.py中的集成
from error_handler import ErrorClassifier, ErrorReporter

def generate_failure_markdown(url, metrics, exception=None):
    if ERROR_HANDLER_AVAILABLE:
        # 使用增强的错误处理
        reporter = ErrorReporter()
        return reporter.generate_markdown_report(url, metrics_dict, exception)
    else:
        # 回退到原始实现
        return original_implementation()
```

### 3.2 自定义扩展

如需在其他模块中使用错误处理：

```python
from error_handler import ErrorClassifier, ErrorReporter, ErrorCategory

# 初始化
classifier = ErrorClassifier()
reporter = ErrorReporter()

# 分类错误
try:
    risky_operation()
except Exception as e:
    category = classifier.classify(e)
    print(f"Error category: {category.name}")

    # 生成报告
    metrics = {
        'primary_method': 'custom',
        'final_status': 'failed',
        'error_message': str(e)
    }
    report = reporter.generate_markdown_report(
        url="https://example.com",
        metrics=metrics,
        exception=e
    )

    # 保存报告
    with open("error_report.md", "w") as f:
        f.write(report)
```

## 4. API参考 / API Reference

### ErrorClassifier

```python
class ErrorClassifier:
    def classify(self, exception: Exception) -> ErrorCategory:
        """将异常分类到错误类别"""

    def get_error_chain(self, exception: Exception) -> List[Exception]:
        """提取完整的错误链"""

    def extract_root_cause(self, exception: Exception) -> str:
        """从异常中提取根因"""
```

### ErrorReporter

```python
class ErrorReporter:
    def __init__(self, classifier: Optional[ErrorClassifier] = None):
        """初始化错误报告器"""

    def generate_markdown_report(
        self,
        url: str,
        metrics: Dict[str, Any],
        exception: Optional[Exception] = None
    ) -> str:
        """生成Markdown格式的错误报告"""

    def get_troubleshooting_guide(
        self,
        category: ErrorCategory
    ) -> Dict[str, Any]:
        """获取特定错误类别的故障排除指南"""
```

### ErrorCategory枚举

```python
class ErrorCategory(Enum):
    NETWORK_CONNECTION = "network_connection"
    BROWSER_INIT = "browser_initialization"
    PAGE_LOAD = "page_loading"
    PERMISSION = "permission_denied"
    DEPENDENCY = "missing_dependency"
    TIMEOUT = "operation_timeout"
    UNKNOWN = "unknown_error"
```

## 5. 最佳实践 / Best Practices

### 5.1 错误处理模式

**推荐：**
```python
# 让错误自然传播，由error_handler自动处理
try:
    result = fetch_html(url)
except Exception as e:
    # 错误已自动分类并生成报告
    logging.error(f"Fetch failed: {e}")
    raise  # 继续传播
```

**不推荐：**
```python
# 不要吞掉异常
try:
    result = fetch_html(url)
except:
    pass  # ❌ 错误信息丢失
```

### 5.2 性能优化建议

1. **复用ErrorClassifier实例** - 避免重复初始化
2. **批量错误处理** - 使用并发处理提高吞吐量
3. **缓存分类结果** - 相同错误类型可缓存

### 5.3 日志记录规范

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

# 错误自动记录到日志
try:
    result = operation()
except Exception as e:
    logging.error(f"Operation failed: {e}")
    # error_handler会自动记录详细信息
```

## 6. 性能指标 / Performance Metrics

### 基准测试结果

| 指标 | 性能 |
|------|------|
| 错误分类速度 | 0.0036ms/次 |
| 报告生成速度 | 0.014ms/次 |
| 内存使用 | 0.23MB/1000错误 |
| 并发处理能力 | 69,293错误/秒 |

### 性能建议

- 单次错误处理：< 1ms
- 批量处理（1000错误）：< 5秒
- 内存占用：< 10MB

## 7. 常见问题 / FAQ

**Q: 错误处理会影响性能吗？**
A: 影响极小，单次处理< 0.02ms，可以忽略。

**Q: 如何禁用增强的错误处理？**
A: 错误处理框架具有自动降级功能，如果模块不可用会自动回退到原始实现。

**Q: 可以自定义错误分类规则吗？**
A: 可以，通过扩展ErrorClassifier._init_error_patterns()方法添加自定义模式。

**Q: 错误报告保存在哪里？**
A: FAILED_前缀的Markdown文件保存在output目录中。

## 8. 参考资源 / References

- [故障排除手册](troubleshooting_manual.md)
- [API文档](../README.md#错误处理)
- [测试用例](../tests/test_error_handler.py)

---

最后更新：2025-09-30
版本：1.0.0