# WeChat Parser Fix - Test Specification

## Test Architecture

### Test Objective
Validate that the WeChat parser correctly filters JavaScript and CSS while preserving article content.

### Test Strategy
1. **Unit Testing**: Test individual parser components
2. **Integration Testing**: Test full parsing flow
3. **Regression Testing**: Ensure no functionality broken
4. **Performance Testing**: Verify parsing speed maintained

## Test Cases

### TC-001: Basic Script Filtering
**Input HTML Fragment:**
```html
<div id="js_content">
  <p>Article paragraph 1</p>
  <script>
    var config = { key: "value" };
    function init() { console.log("test"); }
  </script>
  <p>Article paragraph 2</p>
</div>
```

**Expected Output:**
```markdown
Article paragraph 1

Article paragraph 2
```

**Validation:**
- No "var config" in output
- No "function init" in output
- Both paragraphs preserved

### TC-002: Style Block Filtering
**Input HTML Fragment:**
```html
<div id="js_content">
  <style>
    .article { font-size: 16px; }
    #content { margin: 20px; }
  </style>
  <h1>Article Title</h1>
  <p>Content here</p>
</div>
```

**Expected Output:**
```markdown
# Article Title

Content here
```

**Validation:**
- No CSS rules in output
- Heading and paragraph preserved

### TC-003: Mixed Script/Style/Content
**Input HTML Fragment:**
```html
<div id="js_content">
  <h2>Introduction</h2>
  <script>window.data = {}</script>
  <p>First paragraph</p>
  <style>.highlight { color: red; }</style>
  <p>Second paragraph</p>
  <script type="text/javascript">
    // Long JavaScript code
    function process() {
      return "should not appear";
    }
  </script>
  <p>Third paragraph</p>
</div>
```

**Expected Output:**
```markdown
## Introduction

First paragraph

Second paragraph

Third paragraph
```

### TC-004: Inline Script Handling
**Input HTML Fragment:**
```html
<div id="js_content">
  <p>Text before <script>alert('test')</script> text after</p>
</div>
```

**Expected Output:**
```markdown
Text before  text after
```

### TC-005: Nested Script Tags
**Input HTML Fragment:**
```html
<div id="js_content">
  <div>
    <p>Outer content</p>
    <script>
      document.write('<script>nested</script>');
    </script>
    <p>After script</p>
  </div>
</div>
```

**Expected Output:**
```markdown
Outer content

After script
```

### TC-006: Script with Attributes
**Input HTML Fragment:**
```html
<div id="js_content">
  <script type="application/json">
    {"data": "should be filtered"}
  </script>
  <script src="external.js"></script>
  <script async defer>
    console.log("async script");
  </script>
  <p>Actual content</p>
</div>
```

**Expected Output:**
```markdown
Actual content
```

### TC-007: Real WeChat Article Structure
**Input HTML Fragment:**
```html
<div id="js_content">
  <section>
    <h2>文章标题</h2>
    <script>
      var __INLINE_SCRIPT__ = function() {
        // 29,000+ lines of JavaScript here
        window.__second_open__ = true;
      };
    </script>
    <p>正文第一段内容...</p>
    <img data-src="https://example.com/image.jpg" />
    <p>正文第二段内容...</p>
  </section>
</div>
```

**Expected Output:**
```markdown
## 文章标题

正文第一段内容...

![](https://example.com/image.jpg)

正文第二段内容...
```

## Test Execution Script

### Create Test Runner
```python
#!/usr/bin/env python3
# test_wechat_parser.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webfetcher import wechat_to_markdown

test_cases = {
    "TC-001": {
        "html": '''<html><body>
            <div id="js_content">
              <p>Article paragraph 1</p>
              <script>
                var config = { key: "value" };
                function init() { console.log("test"); }
              </script>
              <p>Article paragraph 2</p>
            </div>
        </body></html>''',
        "should_contain": ["Article paragraph 1", "Article paragraph 2"],
        "should_not_contain": ["var config", "function init", "console.log"]
    },
    # Add more test cases...
}

def run_tests():
    passed = 0
    failed = 0
    
    for test_id, test_data in test_cases.items():
        print(f"Running {test_id}...")
        
        date_only, markdown, metadata = wechat_to_markdown(
            test_data["html"], 
            "https://mp.weixin.qq.com/test"
        )
        
        test_passed = True
        
        # Check should_contain
        for expected in test_data.get("should_contain", []):
            if expected not in markdown:
                print(f"  ❌ Missing expected content: {expected}")
                test_passed = False
        
        # Check should_not_contain
        for unexpected in test_data.get("should_not_contain", []):
            if unexpected in markdown:
                print(f"  ❌ Found unexpected content: {unexpected}")
                test_passed = False
        
        if test_passed:
            print(f"  ✅ {test_id} passed")
            passed += 1
        else:
            failed += 1
            print(f"  ❌ {test_id} failed")
            print(f"  Output: {markdown[:200]}...")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
```

## Performance Test

### Before Fix
```bash
time python3 wf.py https://mp.weixin.qq.com/s/[article_id] > before.md
# Expected: ~2-3 seconds, 700KB output
```

### After Fix  
```bash
time python3 wf.py https://mp.weixin.qq.com/s/[article_id] > after.md
# Expected: <1 second, <10KB output
```

## Validation Checklist

### Functional Validation
- [ ] All script tags filtered
- [ ] All style tags filtered
- [ ] Article title preserved
- [ ] Article metadata preserved
- [ ] Article body text preserved
- [ ] Images still extracted with correct URLs
- [ ] Links still extracted properly
- [ ] Chinese text handled correctly

### Non-Functional Validation
- [ ] No parsing errors or exceptions
- [ ] Performance not degraded
- [ ] Memory usage reasonable
- [ ] Output format unchanged (except filtered content)

### Edge Case Validation
- [ ] Empty script/style tags handled
- [ ] Malformed tags handled gracefully
- [ ] Unclosed tags don't break parser
- [ ] Very long scripts filtered efficiently

## Automated Test Command

```bash
# Run all tests
python3 test_wechat_parser.py

# Test with real article
python3 wf.py https://mp.weixin.qq.com/s/kYiJjQk-bPobDRHJw1hMRA > test_output.md

# Verify output
echo "File size check:"
ls -lh test_output.md

echo "JavaScript contamination check:"
grep -c "function\|var\|window\.\|document\." test_output.md || echo "0"

echo "Content preservation check:" 
head -n 50 test_output.md
```

## Success Metrics

1. **File Size Reduction**: >90% reduction for JavaScript-heavy articles
2. **Content Preservation**: 100% of article text preserved
3. **JavaScript Removal**: 0 occurrences of JS keywords in output
4. **CSS Removal**: 0 occurrences of CSS rules in output
5. **Performance**: <1 second parsing time for typical articles
6. **Error Rate**: 0% parsing errors on valid WeChat HTML