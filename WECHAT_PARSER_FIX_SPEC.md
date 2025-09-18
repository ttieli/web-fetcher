# WeChat Parser JavaScript Extraction Fix Specification

## Architecture Analysis

### Current Problem
The `WxParser` class in the `wechat_to_markdown()` function lacks script/style tag filtering, causing 29,500+ lines of JavaScript to be included in the markdown output.

### Root Cause
The `WxParser` class is missing:
1. `in_script` flag to track when inside `<script>` tags
2. `in_style` flag to track when inside `<style>` tags  
3. Logic in `handle_starttag()` to set these flags
4. Logic in `handle_endtag()` to clear these flags
5. Logic in `handle_data()` to skip content when these flags are set

### Pattern Found in Other Parsers
Both `DocParser` (docusaurus_to_markdown) and `EBChinaParser` (ebchina_to_markdown) correctly implement script/style filtering:

```python
# In __init__:
self.in_script = False
self.in_style = False  # EBChinaParser only has in_script

# In handle_starttag:
elif tag == 'script':
    self.in_script = True
elif tag == 'style':
    self.in_style = True

# In handle_endtag:
elif tag == 'script':
    self.in_script = False
elif tag == 'style':
    self.in_style = False

# In handle_data:
if self.capture and not self.in_script:  # Skip content when in_script is True
    # Process data...
```

## Implementation Specification

### Code Changes Required

#### Location: `webfetcher.py` - `wechat_to_markdown()` function - `WxParser` class

#### 1. Modify `__init__` method (add after line with `self.images: list[str] = []`):
```python
def __init__(self):
    super().__init__()
    self.capture = False
    self.depth = 0
    self.parts: list[str] = []
    self.link = None
    self.images: list[str] = []
    self.in_script = False  # ADD THIS LINE
    self.in_style = False   # ADD THIS LINE
```

#### 2. Modify `handle_starttag` method (add before the final `elif tag == 'a':` block):
```python
elif tag == 'script':
    self.in_script = True
elif tag == 'style':
    self.in_style = True
```

#### 3. Modify `handle_endtag` method (add after the existing `if tag == 'a' and self.link:` block):
```python
def handle_endtag(self, tag):
    if self.capture:
        if tag == 'a' and self.link:
            self.parts.append(f" ({self.link})")
            self.link = None
        elif tag == 'script':  # ADD THIS BLOCK
            self.in_script = False
        elif tag == 'style':   # ADD THIS BLOCK
            self.in_style = False
        self.depth -= 1
        if self.depth == 0:
            self.capture = False
```

#### 4. Modify `handle_data` method:
```python
def handle_data(self, data):
    if self.capture and not self.in_script and not self.in_style:  # MODIFY THIS LINE
        t = data.strip('\n')
        if t.strip(): self.parts.append(ihtml.unescape(t))
```

## Implementation Steps

### Step 1: Backup Current Code
```bash
cp webfetcher.py webfetcher.py.backup
```

### Step 2: Apply Changes
1. Open `webfetcher.py` 
2. Search for `class WxParser(HTMLParser):`
3. Apply the 4 modifications specified above in exact order

### Step 3: Verification
Run test command on a WeChat article:
```bash
python3 wf.py https://mp.weixin.qq.com/s/example_article
```

### Step 4: Validation Criteria
- Output file size should be significantly smaller (expect ~5-10KB instead of ~700KB)
- Markdown content should contain article text without JavaScript code
- Check for absence of patterns like `var`, `function`, `window.`, `document.`

## Test Plan

### Pre-Fix Test (Baseline)
```bash
# Test with current broken version
python3 wf.py https://mp.weixin.qq.com/s/example > test_before.md
ls -lh test_before.md  # Should show ~700KB
grep -c "function" test_before.md  # Should show high count
```

### Post-Fix Test
```bash
# Test after applying fix
python3 wf.py https://mp.weixin.qq.com/s/example > test_after.md
ls -lh test_after.md  # Should show ~5-10KB
grep -c "function" test_after.md  # Should show 0 or very low count
```

### Content Preservation Test
Verify essential content is preserved:
```bash
# Check for article title
grep "^# " test_after.md

# Check for metadata
grep "^- 标题:" test_after.md
grep "^- 作者:" test_after.md

# Check for body content (should have paragraphs)
grep -c "^[A-Za-z中文]" test_after.md  # Should show multiple lines
```

### Edge Cases to Verify
1. **Inline scripts**: `<p>Text <script>alert()</script> more text</p>` → Should output: "Text  more text"
2. **Style blocks**: `<style>.class{}</style>` → Should be completely removed
3. **Nested content**: Script/style tags within captured content area should be filtered
4. **Multiple scripts**: Multiple script blocks should all be filtered

## Risk Mitigation

### Potential Risks
1. **Content Loss**: Legitimate content accidentally filtered
   - **Mitigation**: Only filter when `in_script` or `in_style` is True
   - **Validation**: Compare article text before/after to ensure no narrative content lost

2. **Parser State Corruption**: Unbalanced tags causing state issues
   - **Mitigation**: Script/style flags are independent of depth tracking
   - **Validation**: Test with malformed HTML to ensure graceful handling

3. **Performance Impact**: Additional flag checks
   - **Mitigation**: Minimal - just 2 boolean checks
   - **Validation**: Time parsing of large articles before/after

### Backward Compatibility
- No API changes - function signature remains identical
- Output format unchanged except for filtered content
- Existing code calling `wechat_to_markdown()` needs no modifications

### Rollback Plan
If issues discovered:
```bash
cp webfetcher.py.backup webfetcher.py
```

## Success Criteria

1. ✅ JavaScript code blocks completely removed from output
2. ✅ CSS style blocks completely removed from output  
3. ✅ Article title, metadata, and body text preserved
4. ✅ Output file size reduced by >90% for JavaScript-heavy pages
5. ✅ No errors or exceptions during parsing
6. ✅ Images and links still properly extracted

## Implementation Priority

**CRITICAL** - This fix should be implemented immediately as:
- Current output is unusable (700KB of JavaScript)
- Simple fix with proven pattern from other parsers
- Low risk with high impact
- No architectural changes required