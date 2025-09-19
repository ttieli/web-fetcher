# 爬虫优化验证测试规格

## 测试目标
验证全站爬取优化的正确性、性能提升和向后兼容性

## 测试用例设计

### 1. 基础功能回归测试

#### 1.1 兼容性测试
```python
def test_backward_compatibility():
    """验证API向后兼容性"""
    # 测试原有参数调用
    result = crawl_site(
        start_url="https://example.com",
        max_depth=2,
        max_pages=10
    )
    assert isinstance(result, list)
    assert all(isinstance(item, tuple) for item in result)
    assert all(len(item) == 2 for item in result)
```

#### 1.2 默认行为测试
```python
def test_default_behavior():
    """验证默认模式行为不变"""
    # 对比优化前后的爬取结果
    old_result = crawl_site_old(url)
    new_result = crawl_site(url, enable_optimizations=False)
    assert compare_results(old_result, new_result)
```

### 2. 性能优化测试

#### 2.1 链接预过滤测试
```python
def test_link_prefiltering():
    """测试链接预过滤效果"""
    # 测量过滤前后的队列大小
    # 验证无效链接不进入队列
    # 检查过滤准确性
    metrics = {
        'total_links': 0,
        'filtered_links': 0,
        'valid_links': 0
    }
    return metrics
```

#### 2.2 内存使用测试
```python
def test_memory_optimization():
    """测试内存优化效果"""
    import tracemalloc
    
    # 测试大规模爬取的内存使用
    tracemalloc.start()
    result = crawl_site(url, max_pages=100)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert peak < MAX_MEMORY_MB * 1024 * 1024
```

#### 2.3 性能基准测试
```python
def benchmark_performance():
    """性能基准对比测试"""
    import time
    
    test_sites = [
        "https://example.com",
        "https://hdqw.bjhd.gov.cn/qwyw/tzgg/"
    ]
    
    for site in test_sites:
        # 测试原版
        start = time.time()
        old_result = crawl_site(site, enable_optimizations=False)
        old_time = time.time() - start
        
        # 测试优化版
        start = time.time()
        new_result = crawl_site(site, enable_optimizations=True)
        new_time = time.time() - start
        
        improvement = (old_time - new_time) / old_time * 100
        print(f"Site: {site}")
        print(f"Improvement: {improvement:.1f}%")
        assert improvement >= 15  # 至少15%提升
```

### 3. 政府网站专项测试

#### 3.1 网站类型检测测试
```python
def test_government_site_detection():
    """测试政府网站检测准确性"""
    test_cases = [
        ("https://www.gov.cn", True),
        ("https://hdqw.bjhd.gov.cn", True),
        ("https://example.com", False),
        ("https://github.com", False)
    ]
    
    for url, expected in test_cases:
        html = fetch_page(url)
        result = detect_government_site(url, html)
        assert result == expected
```

#### 3.2 栏目识别测试
```python
def test_category_extraction():
    """测试栏目识别功能"""
    url = "https://hdqw.bjhd.gov.cn"
    html = fetch_page(url)
    categories = extract_site_categories(url, html)
    
    # 验证基本栏目
    assert len(categories) > 0
    assert any("通知公告" in cat.name for cat in categories)
    assert all(cat.url.startswith("http") for cat in categories)
```

#### 3.3 栏目优先策略测试
```python
def test_category_first_strategy():
    """测试栏目优先爬取策略"""
    url = "https://hdqw.bjhd.gov.cn/qwyw/tzgg/"
    
    # 使用栏目优先策略
    results = list(crawl_site_by_categories(url))
    
    # 验证按栏目组织
    assert len(results) > 0
    for category_result in results:
        assert hasattr(category_result, 'category_name')
        assert hasattr(category_result, 'pages')
        assert len(category_result.pages) > 0
```

### 4. 错误处理和降级测试

#### 4.1 策略降级测试
```python
def test_strategy_fallback():
    """测试策略自动降级"""
    # 模拟栏目识别失败
    url = "https://special-case-site.com"
    
    result = crawl_site(
        url,
        crawl_strategy='category_first'
    )
    
    # 验证降级到默认策略
    assert result is not None
    assert len(result) > 0
```

#### 4.2 异常恢复测试
```python
def test_partial_failure_recovery():
    """测试部分失败恢复"""
    # 模拟部分页面失败
    result = crawl_site(
        "https://example.com",
        max_pages=10
    )
    
    # 验证继续爬取其他页面
    assert len(result) > 0
```

## 测试执行计划

### 阶段1验收标准
- [ ] 所有回归测试通过
- [ ] 性能提升15-25%
- [ ] 内存使用降低30%以上
- [ ] 无新增BUG

### 阶段2验收标准
- [ ] 政府网站检测准确率>90%
- [ ] 栏目识别成功率>85%
- [ ] 栏目优先策略正常工作
- [ ] 自动降级机制有效

## 测试数据收集

### 性能指标
- 爬取速度（页面/秒）
- 内存峰值使用
- CPU使用率
- 网络请求效率

### 质量指标
- 爬取完整性
- 去重准确性
- 链接过滤准确性
- 错误恢复率

## 测试报告模板
```markdown
# 爬虫优化测试报告

## 测试概况
- 测试日期：
- 测试版本：
- 测试环境：

## 功能测试结果
| 测试项 | 状态 | 说明 |
|-------|------|------|
| API兼容性 | ✅/❌ | |
| 默认行为 | ✅/❌ | |
| 栏目识别 | ✅/❌ | |

## 性能测试结果
| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 爬取速度 | | | |
| 内存使用 | | | |
| CPU使用 | | | |

## 问题和建议
```