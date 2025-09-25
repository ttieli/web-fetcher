# Phase 1 Quick Reference Card

## 🎯 Mission
Extract 9 parser functions from webfetcher.py → parsers.py  
**NO LOGIC CHANGES** - Pure copy & paste operation

## 📍 Function Locations in webfetcher.py

### Core Parsers (Lines)
```
111:    add_metrics_to_markdown()      [~20 lines]
605:    docusaurus_to_markdown()       [~182 lines]
787:    mkdocs_to_markdown()            [~137 lines]
1924:   wechat_to_markdown()            [~791 lines] ⚠️ LARGE
2715:   xhs_to_markdown()               [~172 lines]
2887:   dianping_to_markdown()          [~155 lines]
3042:   ebchina_news_list_to_markdown() [~63 lines]
3105:   raw_to_markdown()               [~722 lines] ⚠️ LARGE
3827:   generic_to_markdown()           [~308 lines]
```

### Helper Functions (Lines)
```
1752:   extract_meta()                  [~5 lines]
1757:   extract_json_ld_content()       [~53 lines]
1810:   extract_from_modern_selectors() [~48 lines]
1858:   extract_text_from_html_fragment()[~66 lines]
3480:   extract_list_content()          [~347 lines]
```

## 🛠 Quick Commands

### Check webfetcher.py for function
```bash
# Find exact line of function
grep -n "^def docusaurus_to_markdown" webfetcher.py

# Show function with context
sed -n '605,787p' webfetcher.py | head -20
```

### Extract function to clipboard (macOS)
```bash
# Example: Extract docusaurus_to_markdown
sed -n '605,787p' webfetcher.py | pbcopy
```

### Validate parsers.py
```bash
# Quick syntax check
python -m py_compile parsers.py && echo "✅ Syntax OK"

# Check all functions exist
python -c "import parsers; print(dir(parsers))" | grep _to_markdown
```

### Test import
```bash
python -c "
import parsers
print(f'✅ {len([x for x in dir(parsers) if \"_to_markdown\" in x])} parser functions found')
"
```

## ⚠️ Large Functions Warning

These functions are particularly large, be careful:

1. **wechat_to_markdown** (~791 lines)
   - Has multiple internal helper functions
   - Complex article extraction logic
   - Start at line 1924, end around line 2715

2. **raw_to_markdown** (~722 lines)  
   - Multiple site detection patterns
   - Many regex patterns
   - Start at line 3105, end around line 3827

3. **generic_to_markdown** (~308 lines)
   - Main fallback parser
   - Complex content extraction
   - Start at line 3827

## 📋 Copy Checklist (for each function)

```python
# 1. Find function start
def function_name(parameters):
    """Docstring...
    
# 2. Find function end (check indentation)
    return result  # Last line at function indent level

# 3. Copy EVERYTHING between, including:
- Docstrings
- Comments  
- Nested functions
- Try/except blocks
- All return statements
```

## 🔍 Dependency Quick Check

After copying a function, search for these patterns to identify dependencies:

```bash
# Check what the function imports/uses
grep -E "(extract_|clean_|process_|get_|BeautifulSoup)" <function_content>
```

Common dependencies:
- `get_beautifulsoup_parser()` → Note for Phase 2
- `extract_*` functions → Copy to parsers.py
- `FetchMetrics` → Note for Phase 2
- `ListItem` → Copy class definition

## 🚫 Phase 1 Rules

### DON'T
- ❌ Change any code logic
- ❌ Fix any bugs you notice
- ❌ Optimize or refactor
- ❌ Update webfetcher.py imports
- ❌ Remove functions from webfetcher.py yet

### DO
- ✅ Copy exactly as-is
- ✅ Preserve all formatting
- ✅ Include all comments
- ✅ Maintain function order
- ✅ Test syntax after each major function

## 📊 Progress Tracker

```
[ ] parsers.py created with header
[ ] Imports added
[ ] add_metrics_to_markdown
[ ] docusaurus_to_markdown  
[ ] mkdocs_to_markdown
[ ] wechat_to_markdown ⚠️
[ ] xhs_to_markdown
[ ] dianping_to_markdown
[ ] ebchina_news_list_to_markdown
[ ] raw_to_markdown ⚠️
[ ] generic_to_markdown
[ ] Helper functions
[ ] Syntax validates
[ ] Import test passes
[ ] Validation script passes
```

## 🎯 Success = 
All functions copied + parsers.py imports successfully + validation passes

---
Phase 1 Target: 2 hours | Phase 2: Update imports & cleanup