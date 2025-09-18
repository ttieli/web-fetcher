# WeChat Parser Fix - Implementation Guide for Engineer

## Quick Fix Summary
Add script/style filtering to the `WxParser` class in `webfetcher.py` to prevent 29,500+ lines of JavaScript from appearing in markdown output.

## Exact Code Changes Required

### File: `webfetcher.py`
### Function: `wechat_to_markdown()` 
### Class: `WxParser`

### Change 1: Add flags to __init__ method
**Location:** Inside `class WxParser(HTMLParser):` → `def __init__(self):`

**Current Code:**
```python
def __init__(self):
    super().__init__()
    self.capture = False
    self.depth = 0
    self.parts: list[str] = []
    self.link = None
    self.images: list[str] = []
```

**Change To:**
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

### Change 2: Handle script/style start tags
**Location:** Inside `def handle_starttag(self, tag, attrs):` method

**Current Code (end of method):**
```python
                elif tag == 'a':
                    self.link = a.get('href')
```

**Change To:**
```python
                elif tag == 'script':  # ADD THIS BLOCK
                    self.in_script = True
                elif tag == 'style':   # ADD THIS BLOCK  
                    self.in_style = True
                elif tag == 'a':
                    self.link = a.get('href')
```

### Change 3: Handle script/style end tags
**Location:** Inside `def handle_endtag(self, tag):` method

**Current Code:**
```python
def handle_endtag(self, tag):
    if self.capture:
        if tag == 'a' and self.link:
            self.parts.append(f" ({self.link})")
            self.link = None
        self.depth -= 1
        if self.depth == 0:
            self.capture = False
```

**Change To:**
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

### Change 4: Filter data when in script/style
**Location:** Inside `def handle_data(self, data):` method

**Current Code:**
```python
def handle_data(self, data):
    if self.capture:
        t = data.strip('\n')
        if t.strip(): self.parts.append(ihtml.unescape(t))
```

**Change To:**
```python
def handle_data(self, data):
    if self.capture and not self.in_script and not self.in_style:  # MODIFY THIS LINE
        t = data.strip('\n')
        if t.strip(): self.parts.append(ihtml.unescape(t))
```

## Step-by-Step Implementation

### Step 1: Backup
```bash
cp webfetcher.py webfetcher.py.backup_before_wechat_fix
```

### Step 2: Open File
```bash
# Use your preferred editor
vim webfetcher.py
# or
code webfetcher.py
```

### Step 3: Find the WxParser Class
Search for: `class WxParser(HTMLParser):`
This should be around line 1000-1200 (inside the `wechat_to_markdown` function)

### Step 4: Apply the 4 Changes
Apply each change exactly as specified above. The changes are:
1. Add 2 lines to `__init__`
2. Add 4 lines to `handle_starttag` (2 elif blocks)
3. Add 4 lines to `handle_endtag` (2 elif blocks)
4. Modify 1 line in `handle_data` (add condition)

### Step 5: Save and Test
```bash
# Save the file
# Test with a WeChat article
python3 wf.py https://mp.weixin.qq.com/s/kYiJjQk-bPobDRHJw1hMRA
```

## Verification Commands

### Quick Verification
```bash
# Check file size (should be <20KB instead of 700KB)
ls -lh "2025-09-18-*.md" | tail -1

# Check for JavaScript contamination (should return 0)
grep -c "function\|var\|window\." "$(ls -t 2025-09-18-*.md | head -1)"

# View the cleaned output
head -n 50 "$(ls -t 2025-09-18-*.md | head -1)"
```

### Full Test
```bash
# Test with problematic article
TEST_URL="https://mp.weixin.qq.com/s/kYiJjQk-bPobDRHJw1hMRA"
python3 wf.py "$TEST_URL"

# Get the latest output file
OUTPUT_FILE=$(ls -t 2025-09-18-*.md | head -1)

# Run checks
echo "=== File Size Check ==="
ls -lh "$OUTPUT_FILE"

echo -e "\n=== JavaScript Check ==="
echo "JavaScript keywords found: $(grep -c 'function\|var\|window\.' "$OUTPUT_FILE" || echo 0)"

echo -e "\n=== Content Preview ==="
head -n 30 "$OUTPUT_FILE"

echo -e "\n=== Summary ==="
echo "Total lines: $(wc -l < "$OUTPUT_FILE")"
echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
```

## What Success Looks Like

### Before Fix
- File size: ~700KB
- Lines: ~29,500
- Contains massive JavaScript blocks
- Article content buried in code

### After Fix  
- File size: ~5-10KB
- Lines: ~50-200
- Clean markdown with only article content
- No JavaScript or CSS pollution

## Troubleshooting

### If Parser Breaks
```bash
# Restore backup
cp webfetcher.py.backup_before_wechat_fix webfetcher.py
```

### If Content Missing
Check that you only modified the condition in `handle_data`, not the logic:
- ✅ Correct: `if self.capture and not self.in_script and not self.in_style:`
- ❌ Wrong: `if not self.in_script and not self.in_style:` (missing self.capture)

### If Scripts Still Appear
Verify all 4 changes were applied:
1. Check `__init__` has both flags initialized
2. Check `handle_starttag` sets both flags to True
3. Check `handle_endtag` sets both flags to False
4. Check `handle_data` has the combined condition

## Code Review Checklist

Before committing:
- [ ] All 4 changes applied exactly as specified
- [ ] No typos in variable names (`in_script`, `in_style`)
- [ ] Indentation matches surrounding code
- [ ] Test passes with real WeChat article
- [ ] Output file size reduced by >90%
- [ ] Article content still readable
- [ ] No Python syntax errors

## Final Test Command

```bash
# One-liner to test everything
python3 wf.py https://mp.weixin.qq.com/s/kYiJjQk-bPobDRHJw1hMRA && \
  OUTPUT=$(ls -t 2025-09-18-*.md | head -1) && \
  echo "Size: $(ls -lh "$OUTPUT" | awk '{print $5}')" && \
  echo "JS contamination: $(grep -c 'function\|var' "$OUTPUT" || echo 0)" && \
  echo "Success: File is clean!" || echo "Failed: Check implementation"
```

## Expected Git Diff

Your git diff should show approximately:
- 2 lines added in `__init__`
- 4 lines added in `handle_starttag`  
- 4 lines added in `handle_endtag`
- 1 line modified in `handle_data`
- Total: ~11 line changes

This is a surgical fix that solves the critical issue with minimal code changes.