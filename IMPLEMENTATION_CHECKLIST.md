# 编码修复实施检查清单

## 给 @agent-cody-fullstack-engineer 的实施指导

### 📋 前置准备
- [ ] 阅读 `ENCODING_FIX_PHASE1_SPEC.md` 理解需求
- [ ] 备份当前 `webfetcher.py` 文件
- [ ] 确认测试脚本 `test_encoding_fix.py` 可运行

### 🔧 核心实施步骤

#### 步骤1：添加编码检测辅助函数
在 `webfetcher.py` 中添加以下函数（建议放在 `fetch_html_base` 函数前）：

```python
# 位置：约第700行前添加

def detect_encoding_from_headers(headers: dict) -> Optional[str]:
    """从HTTP响应头提取charset"""
    # TODO: 实现
    pass

def detect_encoding_from_html(html_bytes: bytes, limit: int = 8192) -> Optional[str]:
    """从HTML meta标签检测编码"""
    # TODO: 实现
    pass

def smart_decode(data: bytes, response=None) -> str:
    """智能解码HTML内容，支持GB2312/GBK/UTF-8"""
    # TODO: 实现
    pass
```

#### 步骤2：修改 fetch_html_base 函数
位置：`webfetcher.py` 第723行

**原代码**：
```python
return data.decode("utf-8", errors="ignore")
```

**修改为**：
```python
# 智能编码检测和解码
return smart_decode(data, response=r)
```

注意：需要在 `with urllib.request.urlopen` 块中保留响应对象 `r` 的引用。

#### 步骤3：实现编码检测逻辑

##### 3.1 HTTP头检测
```python
def detect_encoding_from_headers(response) -> Optional[str]:
    """
    实现要求：
    1. 从 response.headers.get('Content-Type') 提取
    2. 查找 charset= 参数
    3. 规范化编码名称（gb2312->gb2312, GBK->gbk等）
    """
```

##### 3.2 HTML Meta检测
```python
def detect_encoding_from_html(html_bytes: bytes, limit: int = 8192) -> Optional[str]:
    """
    实现要求：
    1. 扫描前8KB内容
    2. 支持两种格式：
       - <meta charset="gb2312">
       - <meta http-equiv="Content-Type" content="text/html; charset=gb2312">
    3. 使用正则表达式，注意大小写不敏感
    """
```

##### 3.3 智能解码
```python
def smart_decode(data: bytes, response=None) -> str:
    """
    实现顺序：
    1. 尝试从HTTP头获取编码
    2. 尝试从HTML meta获取编码  
    3. 如果都失败，尝试编码链：
       - gb2312
       - gbk
       - gb18030
       - utf-8
    4. 最终降级到 utf-8 with errors='ignore'
    """
```

### ✅ 测试验证

#### 步骤4：运行测试脚本
```bash
python test_encoding_fix.py
```

**必须通过的测试**：
1. ✅ 人民网GB2312页面 - 标题显示"十八届中央政治局"
2. ✅ 新浪UTF-8页面 - 正常显示"新浪"
3. ✅ 12371.cn页面 - 正常显示"中国共产党"
4. ✅ Example.com - 向后兼容

### 📊 性能验证

- [ ] 编码检测时间 < 10ms
- [ ] 整体性能下降 < 5%
- [ ] 无内存泄漏

### 🐛 调试提示

1. **添加日志**：
```python
logging.debug(f"Detected encoding: {encoding} for URL: {url}")
```

2. **测试单个URL**：
```python
# 测试人民网
url = "http://cpc.people.com.cn/n/2012/1119/c352110-19621695.html"
html = webfetcher.fetch_html(url)
print(html[:500])  # 检查是否有乱码
```

3. **常见问题**：
- GB2312解码失败 → 尝试GBK（GB2312的超集）
- 编码名称大小写 → 统一转换为小写
- 编码别名 → gb2312 = gb-2312 = GB2312

### 📝 代码质量要求

- [ ] 每个函数都有docstring
- [ ] 关键逻辑有注释说明
- [ ] 错误处理使用try-except
- [ ] 使用logging记录关键信息
- [ ] 变量命名清晰

### 🚀 提交前检查

- [ ] 所有测试通过
- [ ] 代码格式规范（PEP 8）
- [ ] 无硬编码值
- [ ] 无调试代码遗留
- [ ] 更新相关文档

### 📦 交付物

1. 修改后的 `webfetcher.py`
2. 测试报告 `encoding_test_report.md`
3. 实施总结（包含遇到的问题和解决方案）

### ⚠️ 注意事项

1. **不要**修改其他功能模块
2. **不要**引入新的依赖包
3. **保持**向后兼容性
4. **确保**可以快速回滚

### 🔄 回滚方案

如果出现问题，恢复备份的 `webfetcher.py` 即可。

---

## 时间预估

- 编码检测函数实现：30分钟
- fetch_html_base修改：20分钟
- 测试验证：30分钟
- 调试优化：30分钟
- 文档更新：10分钟

**总计**：约2小时

## 支持资源

- 技术规范：`ENCODING_FIX_PHASE1_SPEC.md`
- 测试脚本：`test_encoding_fix.py`
- 问题反馈：向架构师报告任何阻塞

---

**批准**：Archy-Principle-Architect
**执行**：@agent-cody-fullstack-engineer
**截止时间**：紧急（建议立即开始）