# Quick Plugin Migration Guide (Personal Tool)
# 快速插件迁移指南（个人工具）

## TODAY: Make it Work (2 Hours Max)
## 今天：让它工作（最多2小时）

### Step 1: Create Minimal Plugin Base (5 minutes)
### 步骤1：创建最小插件基础（5分钟）

```bash
# In your Web_Fetcher directory:
cd /Users/tieli/Library/Mobile\ Documents/com~apple~CloudDocs/Project/Web_Fetcher/

# Create simple base (if not exists)
cat > plugins/simple_base.py << 'EOF'
"""Ultra-simple plugin base - that's all!"""

class SimplePlugin:
    def __init__(self, name):
        self.name = name
        self.enabled = True
    
    def fetch(self, url, timeout=30):
        """Return (success, content, error)"""
        raise NotImplementedError
EOF
```

### Step 2: Create Curl Plugin (10 minutes)
### 步骤2：创建Curl插件（10分钟）

```bash
# Create curl plugin from existing code
cat > plugins/simple_curl.py << 'EOF'
"""Simple curl plugin for SSL issues"""
import subprocess
import logging
from plugins.simple_base import SimplePlugin

class CurlPlugin(SimplePlugin):
    def __init__(self):
        super().__init__('curl')
        
    def fetch(self, url, timeout=30):
        """Just use curl, bypass SSL issues"""
        try:
            cmd = [
                'curl', '-L',
                '--insecure',  # Fix SSL issues
                '--max-time', str(timeout),
                '--compressed',
                '--silent',
                url
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout + 5
            )
            
            if result.returncode == 0:
                logging.info(f"Curl fetch successful for {url}")
                return True, result.stdout, None
            else:
                return False, None, result.stderr
                
        except Exception as e:
            return False, None, str(e)
EOF
```

### Step 3: Integrate with webfetcher.py (15 minutes)
### 步骤3：与webfetcher.py集成（15分钟）

Find the SSL error handling in webfetcher.py (around line 1443) and add:

```python
# At the top of webfetcher.py, after imports:
try:
    from plugins.simple_curl import CurlPlugin
    CURL_PLUGIN = CurlPlugin()
except ImportError:
    CURL_PLUGIN = None
    logging.info("Curl plugin not available")

# In fetch_html_original function, where SSL error is caught:
# Around line 1443-1454, modify the SSL error handler:
if "SSL" in str(e) or "CERTIFICATE" in str(e).upper():
    logging.info(f"SSL error detected for {url}")
    
    # Try simple curl plugin
    if CURL_PLUGIN and CURL_PLUGIN.enabled:
        success, content, error = CURL_PLUGIN.fetch(url, timeout)
        if success:
            logging.info(f"Curl plugin succeeded for {url}")
            return content
        else:
            logging.warning(f"Curl plugin failed: {error}")
    
    # Continue with existing fallback...
    # (keep existing code)
```

### Step 4: Test It (5 minutes)
### 步骤4：测试（5分钟）

```bash
# Test with a known SSL-problematic URL
python -c "
from plugins.simple_curl import CurlPlugin
plugin = CurlPlugin()
success, content, error = plugin.fetch('https://raw.githubusercontent.com/test/test/main/README.md')
print(f'Success: {success}')
print(f'Content length: {len(content) if content else 0}')
"

# Or test the whole flow
python webfetcher.py 'https://raw.githubusercontent.com/test/test/main/README.md'
```

## That's It for Today!
## 今天就这些！

You now have:
- ✅ Working curl plugin for SSL issues
- ✅ Simple integration with main code
- ✅ No complex abstractions
- ✅ No enterprise features

## Tomorrow (Optional): Add Playwright
## 明天（可选）：添加Playwright

```python
# plugins/simple_playwright.py
from plugins.simple_base import SimplePlugin

class PlaywrightPlugin(SimplePlugin):
    def __init__(self):
        super().__init__('playwright')
        
    def fetch(self, url, timeout=30):
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=timeout * 1000)
                content = page.content()
                browser.close()
                return True, content, None
        except Exception as e:
            return False, None, str(e)
```

## Later (If Needed): Simple Plugin Selection
## 以后（如果需要）：简单插件选择

```python
# In webfetcher.py, create simple plugin list:
PLUGINS = []

try:
    from plugins.simple_curl import CurlPlugin
    PLUGINS.append(CurlPlugin())
except: pass

try:
    from plugins.simple_playwright import PlaywrightPlugin
    PLUGINS.append(PlaywrightPlugin())
except: pass

# Simple domain-based selection
def get_plugin_for_url(url):
    if 'xiaohongshu.com' in url:
        # Try playwright first for JS sites
        for p in PLUGINS:
            if p.name == 'playwright':
                return p
    
    if 'githubusercontent.com' in url:
        # Use curl for SSL issues
        for p in PLUGINS:
            if p.name == 'curl':
                return p
    
    return None  # Use default urllib
```

## What NOT to Do
## 不要做什么

❌ Don't create complex plugin registries  
❌ Don't add YAML configuration  
❌ Don't implement sandboxing  
❌ Don't add monitoring/metrics  
❌ Don't build for other users  
❌ Don't over-abstract  

## Troubleshooting
## 故障排除

| Problem | Quick Fix |
|---------|-----------|
| ImportError | Check plugins/ directory exists |
| Curl not found | Install curl: `brew install curl` |
| SSL still fails | Make sure `--insecure` is in curl command |
| Plugin not called | Check if CURL_PLUGIN is not None |
| Timeout | Increase timeout value |

## Success Check
## 成功检查

Run the validation script:
```bash
python tests/validate_simple_plugins.py
```

If it shows curl plugin working, you're done! 🎉

## Remember
## 记住

- This is YOUR tool - make it work for YOU
- Fix problems when they actually happen
- 2 hours today > 2 weeks of planning
- Working code > perfect architecture

---

**Time Required**: 30-45 minutes actual work
**所需时间**: 30-45分钟实际工作

**Complexity Level**: Copy & Paste
**复杂度等级**: 复制粘贴