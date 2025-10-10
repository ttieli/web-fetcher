# 🔬 Manual Chrome Hybrid Testing Guide
# 手动Chrome混合测试指南

## Quick Start / 快速开始

### Step 1: Check Environment / 检查环境
```bash
python check_manual_test_env.py
```

### Step 2: Start Chrome with Debug Port / 启动调试端口的Chrome
```bash
# Kill any existing debug Chrome first
pkill -f "remote-debugging-port"

# Start fresh Chrome with debug port
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-manual-test \
  --no-first-run \
  --disable-extensions
```

### Step 3: Manually Navigate / 手动导航
1. In the Chrome window that opens, navigate to:
   https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html
2. Wait for the page to fully load
3. **IMPORTANT**: Note what you see (content or blank page)

### Step 4: Run Tests / 运行测试
```bash
# Test with Selenium
python test_manual_chrome_selenium.py

# Test with pychrome CDP
python test_manual_chrome_pychrome.py
```

### Step 5: Document Results / 记录结果
Fill in the report template: `TASKS/test-manual-chrome-hybrid-approach.md`

---

## Detailed Testing Protocol / 详细测试协议

### 📋 Pre-Test Checklist / 测试前检查清单

#### Environment Setup / 环境设置
- [ ] macOS system
- [ ] Google Chrome installed
- [ ] Python 3.x installed
- [ ] Terminal/command line access

#### Dependencies / 依赖项
```bash
# Install if missing
pip install selenium pychrome requests
```

#### Port Availability / 端口可用性
```bash
# Check if port 9222 is free
lsof -i :9222

# If occupied, kill the process
kill -9 [PID]
```

---

## 🔴 CRITICAL: Manual Observation / 关键：人工观察

### What to Look For / 观察要点

When you manually open the page, document:

1. **Page Loading**
   - [ ] Loads immediately
   - [ ] Takes time to load
   - [ ] Never finishes loading

2. **Content Visibility**
   - [ ] Full article content visible
   - [ ] Only header/footer visible
   - [ ] Completely blank/white
   - [ ] Error message displayed

3. **Specific Elements**
   - [ ] "中国光大银行" text visible
   - [ ] Announcement title visible
   - [ ] Date/time stamps visible
   - [ ] Document content visible

4. **Browser Indicators**
   - Tab title shows: ______________
   - URL bar shows: ________________
   - SSL padlock: [ ] Green | [ ] Warning | [ ] Error

### Screenshot Requirements / 截图要求

Take manual screenshots of:
1. Full page view
2. Browser DevTools Console tab (F12)
3. Browser DevTools Network tab
4. Any error messages

Save as: `test_artifacts/manual_[description]_[timestamp].png`

---

## 🔧 Troubleshooting Guide / 故障排除指南

### Common Issues and Solutions / 常见问题和解决方案

#### Issue 1: Chrome won't start with debug port
```bash
# Solution: Kill all Chrome processes first
pkill -f Chrome
sleep 2
# Then try starting again
```

#### Issue 2: "Address already in use" error
```bash
# Find what's using port 9222
lsof -i :9222
# Kill that process
kill -9 [PID]
```

#### Issue 3: Selenium can't connect to Chrome
```bash
# Verify Chrome is running with debug port
curl http://127.0.0.1:9222/json/version
# Should return JSON with browser info
```

#### Issue 4: pychrome ImportError
```bash
# Install pychrome
pip install pychrome
# Or upgrade
pip install --upgrade pychrome
```

#### Issue 5: Page shows blank in manual Chrome
**This is important data!** It means even manual access is blocked.
Document this carefully as it indicates the hybrid approach won't work.

---

## 📊 Test Scenarios / 测试场景

### Scenario A: SUCCESS ✅
**Observed**: Human sees content, script extracts content
**Conclusion**: Hybrid approach works
**Next Steps**: Implement production solution

### Scenario B: PARTIAL ⚠️
**Observed**: Human sees content, script extracts partial/different content
**Conclusion**: Needs debugging
**Next Steps**: Investigate extraction method

### Scenario C: BLOCKED 🚫
**Observed**: Human sees blank/error page
**Conclusion**: Site blocks even manual access
**Next Steps**: Need completely different approach

### Scenario D: TECHNICAL FAIL ❌
**Observed**: Human sees content, script fails to connect
**Conclusion**: Technical/configuration issue
**Next Steps**: Fix technical problems

---

## 📝 Data Collection Template / 数据收集模板

Copy this template for each test run:

```markdown
## Test Run #___
Date/Time: _________
Tester: _________

### Manual Observation
- Page loads: YES / NO
- Content visible: YES / NO / PARTIAL
- What I see: _________

### Selenium Test
- Connection: SUCCESS / FAIL
- HTML extracted: _____ bytes
- Content matches manual: YES / NO

### pychrome Test
- Connection: SUCCESS / FAIL
- HTML extracted: _____ bytes
- Content matches manual: YES / NO

### Conclusion
This approach: WORKS / DOESN'T WORK
Because: _________
```

---

## 🎯 Success Criteria / 成功标准

The test is **SUCCESSFUL** if ALL of these are true:
1. ✅ Human can manually view the actual page content
2. ✅ Script successfully connects to manual Chrome
3. ✅ Script extracts >10KB of meaningful HTML
4. ✅ Extracted content matches what human sees

The test **FAILS** if ANY of these are true:
1. ❌ Human cannot see content (blank/error page)
2. ❌ Script cannot connect to Chrome
3. ❌ Script extracts <1KB or empty HTML
4. ❌ Extracted content doesn't match human view

---

## 📁 File Organization / 文件组织

```
Web_Fetcher/
├── test_manual_chrome_selenium.py    # Selenium test script
├── test_manual_chrome_pychrome.py    # CDP test script
├── check_manual_test_env.py          # Environment checker
├── test_artifacts/                   # All test outputs
│   ├── manual_*.png                  # Your manual screenshots
│   ├── selenium_*.html               # Selenium extracted HTML
│   ├── selenium_*.png                # Selenium screenshots
│   ├── pychrome_*.html               # CDP extracted HTML
│   ├── pychrome_*.png                # CDP screenshots
│   └── *_results.json                # Test results data
└── TASKS/
    ├── test-manual-chrome-hybrid-approach.md  # Main report
    └── MANUAL_CHROME_TEST_GUIDE.md           # This guide
```

---

## 🚀 Next Steps Based on Results / 基于结果的下一步

### If Successful ✅
1. Design production implementation
2. Create user-friendly wrapper
3. Add batch processing support
4. Implement caching system

### If Partially Successful ⚠️
1. Debug extraction differences
2. Try alternative CDP commands
3. Test with different wait times
4. Investigate JavaScript execution

### If Failed ❌
1. Document why it failed
2. Consider alternative approaches:
   - Browser automation frameworks
   - Proxy-based solutions
   - API reverse engineering
   - Manual data entry

---

## 📞 Getting Help / 获取帮助

If you encounter issues:
1. Check the troubleshooting guide above
2. Review Chrome DevTools documentation
3. Check Selenium/pychrome documentation
4. Document the exact error with screenshots

---

## ⏱️ Estimated Time / 预计时间

- Environment setup: 15 minutes
- Manual Chrome test: 15 minutes
- Selenium test: 15 minutes
- pychrome test: 15 minutes
- Documentation: 30 minutes
- **Total**: ~90 minutes

---

## 🎭 Important Reminders / 重要提醒

1. **BE OBJECTIVE**: Report what you actually see, not what you expect
2. **DOCUMENT EVERYTHING**: Every detail could be important
3. **TAKE SCREENSHOTS**: Visual evidence is crucial
4. **TEST MULTIPLE TIMES**: Results may vary between runs
5. **COMPARE CAREFULLY**: Small differences matter

---

Good luck with your testing! 祝测试顺利！