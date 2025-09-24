# Safari会话复用架构分析报告

## 执行摘要

本报告分析了利用macOS Safari已验证会话来支持wf工具下载中央纪委网站内容的技术可行性。经过深入分析，我们确定了三种主要技术路径，并推荐采用**Cookie提取与复用方案**作为最佳实施路径。

## 问题背景

### 当前状态
- ✅ Safari浏览器已成功通过ccdi.gov.cn的验证码验证
- ✅ Safari中存在有效的会话和Cookie
- ❌ wf工具(webfetcher)无法直接访问受保护的内容
- ❌ Playwright自动化会触发新的验证流程

### 核心挑战
1. Safari的安全架构限制了Cookie的直接访问
2. Playwright不支持连接现有Safari实例
3. 需要在不修改核心代码的前提下实现解决方案

## 技术方案分析

### 方案一：Safari Cookie提取与复用 ✅ (推荐)

#### 架构设计

```
Safari Browser
    │
    ├── Cookie Storage (~/Library/Cookies/Cookies.binarycookies)
    │   └── [加密存储，需要特殊工具读取]
    │
    ├── Developer Tools Export
    │   └── [手动导出Cookie为HAR/JSON]
    │
    └── AppleScript/JavaScript Bridge
        └── [程序化访问Safari数据]
            │
            ▼
    Cookie Extraction Layer
            │
            ├── Manual Export Tool
            ├── AppleScript Automation
            └── Browser Extension
                    │
                    ▼
            Cookie Format Converter
                    │
                    ▼
            WebFetcher Integration
```

#### 实现方式

##### 方法1：手动Cookie导出（最简单）
```bash
# 1. 在Safari中访问目标网站并通过验证
# 2. 打开开发者工具 (Preferences > Advanced > Show Develop menu)
# 3. Network标签 > 右键请求 > Copy as cURL
# 4. 提取Cookie值
```

##### 方法2：AppleScript自动提取
```applescript
-- extract_safari_cookies.scpt
tell application "Safari"
    set currentURL to URL of current tab of window 1
    set cookieData to do JavaScript "
        var cookies = document.cookie.split(';');
        var result = {};
        cookies.forEach(function(cookie) {
            var parts = cookie.trim().split('=');
            result[parts[0]] = parts[1];
        });
        JSON.stringify(result);
    " in current tab of window 1
    return cookieData
end tell
```

##### 方法3：Safari扩展开发
```javascript
// Safari Extension - background.js
browser.cookies.getAll({domain: ".ccdi.gov.cn"}, function(cookies) {
    // 导出cookies到文件或发送到本地服务
    const cookieData = cookies.map(c => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path
    }));
    saveToFile(cookieData);
});
```

#### WebFetcher集成适配器

```python
# cookie_adapter.py - 无需修改核心代码的适配器
import json
import subprocess
import tempfile
from pathlib import Path

class SafariCookieAdapter:
    """Safari Cookie复用适配器"""
    
    def __init__(self, cookie_source='manual'):
        self.cookie_source = cookie_source
        self.cookies = {}
        
    def extract_cookies(self):
        """提取Safari Cookies"""
        if self.cookie_source == 'manual':
            # 从文件读取手动导出的Cookie
            return self._load_manual_cookies()
        elif self.cookie_source == 'applescript':
            # 使用AppleScript提取
            return self._extract_via_applescript()
        elif self.cookie_source == 'extension':
            # 从扩展导出文件读取
            return self._load_extension_export()
    
    def _load_manual_cookies(self):
        """加载手动导出的Cookie文件"""
        cookie_file = Path.home() / '.wf_cookies' / 'ccdi_cookies.json'
        if cookie_file.exists():
            with open(cookie_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _extract_via_applescript(self):
        """通过AppleScript提取Cookie"""
        script = '''
        tell application "Safari"
            do JavaScript "document.cookie" in current tab of window 1
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        return self._parse_cookie_string(result.stdout)
    
    def create_curl_command(self, url, cookies):
        """创建带Cookie的curl命令"""
        cookie_header = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        return [
            'curl',
            '-H', f'Cookie: {cookie_header}',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            url
        ]
    
    def fetch_with_cookies(self, url):
        """使用Safari Cookie获取内容"""
        cookies = self.extract_cookies()
        cmd = self.create_curl_command(url, cookies)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        return None

# 使用示例 - 包装webfetcher
def wrapped_webfetcher(url):
    """包装的webfetcher，自动使用Safari Cookie"""
    if 'ccdi.gov.cn' in url:
        adapter = SafariCookieAdapter('manual')
        html_content = adapter.fetch_with_cookies(url)
        if html_content:
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_path = f.name
            
            # 调用原始webfetcher处理本地文件
            import subprocess
            result = subprocess.run(
                ['python', 'webfetcher.py', f'file://{temp_path}', '-o', 'output.md'],
                capture_output=True
            )
            return result.returncode == 0
    
    # 非CCDI网站，使用原始webfetcher
    subprocess.run(['python', 'webfetcher.py', url])
```

### 方案二：Playwright连接现有浏览器 ❌ (不可行)

#### 技术限制
```
Playwright架构限制:
├── 不支持连接现有Safari实例
├── Safari缺少Chrome的--remote-debugging-port功能
├── WebKit驱动模式始终创建新实例
└── 无法继承现有会话状态
```

#### 为何不可行
1. **Safari不支持远程调试协议**：不像Chrome可以通过CDP连接
2. **Playwright设计限制**：始终启动新的浏览器实例
3. **安全模型不兼容**：Safari的安全架构阻止外部进程接管

### 方案三：浏览器自动化桥接 ⚠️ (复杂)

#### 架构设计
```
Safari (已验证)
    │
    ├── AppleScript Control
    │   ├── 导航控制
    │   ├── 内容提取
    │   └── 页面交互
    │
    └── JavaScript Injection
        ├── DOM操作
        ├── 数据提取
        └── 事件触发
            │
            ▼
    Bridge Service (Python)
            │
            ├── Command Queue
            ├── Result Parser
            └── Error Handler
                    │
                    ▼
            WebFetcher
```

#### 实现示例
```python
# safari_bridge.py
import subprocess
import json
import time

class SafariBridge:
    """Safari自动化桥接器"""
    
    def __init__(self):
        self.ensure_safari_ready()
    
    def navigate_to(self, url):
        """控制Safari导航"""
        script = f'''
        tell application "Safari"
            set URL of current tab of window 1 to "{url}"
            delay 2
        end tell
        '''
        self._run_applescript(script)
    
    def extract_content(self):
        """提取页面内容"""
        script = '''
        tell application "Safari"
            set pageContent to do JavaScript "document.documentElement.outerHTML" in current tab of window 1
            return pageContent
        end tell
        '''
        return self._run_applescript(script)
    
    def save_page(self, output_path):
        """保存完整页面"""
        content = self.extract_content()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_path
    
    def _run_applescript(self, script):
        """执行AppleScript"""
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

# 集成示例
def fetch_via_safari_bridge(url):
    """通过Safari桥接获取内容"""
    bridge = SafariBridge()
    bridge.navigate_to(url)
    time.sleep(3)  # 等待页面加载
    
    temp_file = '/tmp/safari_content.html'
    bridge.save_page(temp_file)
    
    # 使用webfetcher处理
    subprocess.run([
        'python', 'webfetcher.py',
        f'file://{temp_file}',
        '-o', 'output.md'
    ])
```

## 实施难度与可行性评估

### 方案对比矩阵

| 评估维度 | Cookie提取复用 | Playwright连接 | 浏览器桥接 |
|---------|---------------|----------------|------------|
| **技术可行性** | ✅ 高 | ❌ 不可行 | ⚠️ 中 |
| **实施难度** | 🟢 低 | 🔴 极高 | 🟡 中 |
| **开发时间** | 1-2天 | N/A | 3-5天 |
| **维护成本** | 低 | N/A | 中 |
| **稳定性** | 高 | N/A | 中 |
| **用户体验** | 良好 | N/A | 一般 |
| **自动化程度** | 半自动 | N/A | 自动 |
| **安全性** | 高 | N/A | 中 |

### 技术风险评估

#### Cookie方案风险
- **Cookie过期**：需要定期更新（缓解：自动提醒机制）
- **格式兼容**：不同导出方式格式不同（缓解：统一转换器）
- **安全存储**：Cookie包含敏感信息（缓解：加密存储）

#### 桥接方案风险
- **性能开销**：AppleScript执行较慢（缓解：批量处理）
- **稳定性**：依赖GUI状态（缓解：错误重试机制）
- **兼容性**：macOS版本差异（缓解：版本检测）

## 推荐实施方案

### 第一阶段：快速原型（1-2天）

#### 1. Cookie手动导出工具
```bash
#!/bin/bash
# extract_cookies.sh - Cookie提取脚本

echo "请在Safari中访问目标网站并通过验证"
echo "然后按以下步骤操作："
echo "1. 打开开发者工具"
echo "2. Network标签"
echo "3. 刷新页面"
echo "4. 右键点击主请求"
echo "5. Copy as cURL"
echo "6. 将内容粘贴到cookie_export.txt"

read -p "完成后按Enter继续..."

# 解析cookie_export.txt提取Cookie
grep -o "Cookie: [^']*" cookie_export.txt | sed 's/Cookie: //' > cookies.txt

echo "Cookie已提取到cookies.txt"
```

#### 2. WebFetcher包装器
```python
# wf_with_cookies.py - 带Cookie支持的包装器
import sys
import subprocess
from pathlib import Path

def load_cookies():
    """加载提取的Cookie"""
    cookie_file = Path('cookies.txt')
    if cookie_file.exists():
        return cookie_file.read_text().strip()
    return None

def fetch_with_cookies(url):
    """使用Cookie获取内容"""
    cookies = load_cookies()
    if not cookies:
        print("错误：未找到Cookie文件")
        return False
    
    # 使用curl获取内容
    cmd = [
        'curl', '-s',
        '-H', f'Cookie: {cookies}',
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        '-o', 'temp_content.html',
        url
    ]
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        # 使用webfetcher处理
        subprocess.run([
            'python', 'webfetcher.py',
            'file://temp_content.html',
            '-o', 'output.md'
        ])
        return True
    return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wf_with_cookies.py <url>")
        sys.exit(1)
    
    fetch_with_cookies(sys.argv[1])
```

### 第二阶段：自动化增强（3-5天）

#### 功能增强清单
- [ ] AppleScript自动Cookie提取
- [ ] Cookie有效性检测
- [ ] 批量URL处理
- [ ] 错误重试机制
- [ ] 进度显示
- [ ] 日志记录

### 第三阶段：用户体验优化（1周）

#### Safari扩展开发
- [ ] 一键导出Cookie
- [ ] 自动更新机制
- [ ] 可视化管理界面
- [ ] 与wf工具深度集成

## 操作指南

### 快速开始步骤

#### 步骤1：准备Safari
```bash
# 启用开发者菜单
defaults write com.apple.Safari IncludeDevelopMenu -bool true
defaults write com.apple.Safari ShowDevelopMenu -bool true
```

#### 步骤2：获取验证会话
1. 打开Safari
2. 访问 https://www.ccdi.gov.cn
3. 完成验证码验证
4. 确认可以正常浏览内容

#### 步骤3：导出Cookie
```bash
# 方法A：使用开发者工具
# 1. Command+Option+I 打开开发者工具
# 2. Network标签
# 3. 刷新页面
# 4. 找到主文档请求
# 5. 右键 > Copy as cURL
# 6. 保存到cookie_curl.txt

# 方法B：使用AppleScript
osascript -e 'tell application "Safari" to do JavaScript "document.cookie" in current tab of window 1' > cookies.txt
```

#### 步骤4：使用Cookie获取内容
```bash
# 提取Cookie
grep -o "Cookie: [^']*" cookie_curl.txt | sed 's/Cookie: //' > cookie_header.txt

# 下载内容
curl -H "@cookie_header.txt" \
     -H "User-Agent: Mozilla/5.0 (Macintosh)" \
     -o content.html \
     "https://www.ccdi.gov.cn/yaowenn/202509/t20250904_445401.html"

# 转换为Markdown
python webfetcher.py file://$(pwd)/content.html -o output.md
```

## 监控与维护

### Cookie有效性监控
```python
# monitor_cookies.py
import requests
import json
from datetime import datetime

def check_cookie_validity(cookies):
    """检查Cookie是否仍然有效"""
    test_url = "https://www.ccdi.gov.cn/api/test"
    
    response = requests.get(
        test_url,
        headers={'Cookie': cookies},
        allow_redirects=False
    )
    
    # 如果被重定向到验证页面，Cookie已失效
    if response.status_code == 302:
        return False
    
    return response.status_code == 200

def log_cookie_status(status):
    """记录Cookie状态"""
    with open('cookie_log.json', 'a') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'valid': status
        }, f)
        f.write('\n')
```

### 自动化维护脚本
```bash
#!/bin/bash
# maintain_session.sh - 会话维护脚本

while true; do
    # 检查Cookie有效性
    python monitor_cookies.py
    
    if [ $? -ne 0 ]; then
        echo "Cookie已失效，请重新验证"
        osascript -e 'display notification "Cookie已失效" with title "WebFetcher"'
        
        # 打开Safari到验证页面
        open "https://www.ccdi.gov.cn"
        
        # 等待用户完成验证
        read -p "完成验证后按Enter继续..."
        
        # 重新提取Cookie
        ./extract_cookies.sh
    fi
    
    # 每30分钟检查一次
    sleep 1800
done
```

## 总结与建议

### 核心结论
1. **Safari Cookie提取复用**是最可行的方案
2. **Playwright无法连接**现有Safari实例
3. **AppleScript桥接**可作为备选方案

### 实施建议
1. **立即实施**：Cookie手动导出方案（1天完成）
2. **逐步优化**：添加自动化提取功能（1周内）
3. **长期规划**：开发Safari扩展（2周内）

### 关键成功因素
- ✅ 保持Cookie新鲜度
- ✅ 优雅处理失效情况
- ✅ 提供清晰的用户指引
- ✅ 建立监控机制
- ✅ 文档化操作流程

### 下一步行动
1. 🚀 实现Cookie手动导出原型
2. 🧪 测试不同类型页面
3. 📊 收集使用反馈
4. 🔄 迭代优化方案
5. 📝 编写用户手册

---

**文档版本**: 1.0.0
**更新日期**: 2025-09-23
**架构师**: Archy-Principle-Architect
**状态**: 待实施验证