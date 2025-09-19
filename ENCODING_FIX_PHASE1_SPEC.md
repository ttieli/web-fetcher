# 编码处理紧急修复规范（第一阶段）

## 架构决策记录 ADR-002

### 状态：待实施
### 日期：2025-09-19
### 决策者：Archy-Principle-Architect

## 1. 背景与问题

人民网等使用GB2312编码的网站出现乱码问题。当前 `webfetcher.py` 硬编码使用UTF-8解码，导致：
- GB2312/GBK编码内容显示为乱码
- 无法正确处理中文政府网站
- 影响用户体验和系统可用性

## 2. 决策：智能编码检测方案

### 2.1 核心策略
实施**三层编码检测机制**：
1. HTTP响应头charset检测
2. HTML meta标签编码检测
3. 中文编码降级链尝试

### 2.2 技术架构

```python
# 伪代码架构（仅供参考，不要直接复制）
def detect_and_decode(data: bytes, response_headers: Optional[dict] = None) -> tuple[str, str]:
    """
    智能检测并解码HTML内容
    
    Returns:
        tuple[str, str]: (decoded_html, detected_encoding)
    """
    # 第一层：HTTP响应头
    encoding = extract_charset_from_headers(response_headers)
    
    # 第二层：HTML meta标签
    if not encoding:
        encoding = detect_encoding_from_html(data[:8192])
    
    # 第三层：中文编码降级链
    if not encoding:
        for enc in ['gb2312', 'gbk', 'gb18030', 'utf-8']:
            if try_decode(data, enc):
                encoding = enc
                break
    
    # 解码
    return safe_decode(data, encoding)
```

## 3. 实施细节

### 3.1 修改位置
文件：`webfetcher.py`
函数：`fetch_html_base` (约723行)

### 3.2 必需的辅助函数

#### 3.2.1 编码检测函数
```python
def detect_encoding_from_headers(headers: dict) -> Optional[str]:
    """从HTTP响应头提取charset"""
    # 实现要求：
    # 1. 检查Content-Type header
    # 2. 提取charset参数
    # 3. 规范化编码名称
    pass

def detect_encoding_from_html(html_bytes: bytes) -> Optional[str]:
    """从HTML meta标签检测编码"""
    # 实现要求：
    # 1. 使用正则表达式查找meta charset
    # 2. 支持HTML5和HTML4两种格式
    # 3. 限制扫描前8KB
    pass

def safe_decode(data: bytes, encoding: str = 'utf-8') -> str:
    """安全解码，带降级处理"""
    # 实现要求：
    # 1. 尝试指定编码
    # 2. 失败时尝试备用编码
    # 3. 最终使用utf-8 ignore模式
    pass
```

### 3.3 编码优先级

1. **显式声明优先**：
   - HTTP Content-Type charset
   - HTML meta charset

2. **智能推测降级**：
   - GB2312 (最严格)
   - GBK (GB2312超集)
   - GB18030 (最完整)
   - UTF-8 (默认)

### 3.4 性能约束

- 编码检测总时间 < 10ms
- HTML扫描限制在前8KB
- 避免重复解码相同内容
- 使用编译的正则表达式

## 4. 测试验收标准

### 4.1 功能测试用例

```python
# 测试用例结构
TEST_CASES = [
    {
        "url": "http://cpc.people.com.cn/n/2012/1119/c352110-19621695.html",
        "expected_encoding": "gb2312",
        "expected_title": "十八届中央政治局会议",
        "must_not_contain": ["ä¸­", "æ–‡", "乱码"]
    },
    {
        "url": "https://www.sina.com.cn",
        "expected_encoding": "utf-8",
        "expected_title_contains": "新浪"
    },
    {
        "url": "https://www.12371.cn/2023/11/28/STUD1701138144744927.shtml",
        "expected_encoding": "utf-8",
        "expected_content_contains": "中国共产党"
    }
]
```

### 4.2 性能测试要求

```python
# 性能基准测试
def performance_benchmark():
    """
    要求：
    1. 编码检测时间 < 10ms (95分位)
    2. 总体性能下降 < 5%
    3. 内存占用增加 < 1MB
    """
    pass
```

### 4.3 回归测试

确保现有功能不受影响：
- Markdown转换正常
- 链接提取准确
- 图片处理无误
- 文件保存格式正确

## 5. 实施步骤

### Phase 1: 核心实现（当前）
1. 实现编码检测函数
2. 修改 `fetch_html_base` 解码逻辑
3. 添加日志记录
4. 基础测试验证

### Phase 2: 优化（后续）
1. 添加编码缓存
2. 优化正则表达式
3. 完善错误处理
4. 性能调优

## 6. 风险与缓解

### 风险1：误判编码
- **缓解**：保留原有UTF-8降级机制

### 风险2：性能下降
- **缓解**：限制扫描范围，使用缓存

### 风险3：兼容性问题
- **缓解**：充分测试，保留回滚能力

## 7. 监控指标

实施后需要监控：
- 编码检测成功率
- 平均响应时间
- 错误日志频率
- 用户反馈

## 8. 代码审查清单

- [ ] 编码检测逻辑正确
- [ ] 错误处理完善
- [ ] 日志记录充分
- [ ] 性能符合要求
- [ ] 测试覆盖完整
- [ ] 代码注释清晰
- [ ] 向后兼容性保证

## 9. 部署验证

部署后立即验证：
1. 人民网页面正确显示
2. UTF-8网站功能正常
3. 性能监控无异常
4. 错误日志无增长

---

**批准签署**：Archy-Principle-Architect
**实施负责**：@agent-cody-fullstack-engineer
**预计工时**：2-3小时
**风险等级**：中等（可回滚）