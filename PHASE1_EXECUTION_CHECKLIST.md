# Phase 1 Execution Checklist for Engineer

## Pre-Migration Setup (5 minutes)
- [ ] Ensure git is clean: `git status`
- [ ] Create feature branch: `git checkout -b refactor/extract-parsers-phase1`
- [ ] Review this checklist completely before starting

## Step 1: Create parsers.py File (10 minutes)

### 1.1 Create file with proper header
```python
#!/usr/bin/env python3
"""
Web content parsers for different site types.
Extracted from webfetcher.py for better modularity.

Phase 1: Pure extraction - no logic changes
"""

__version__ = "1.0.0"
__author__ = "WebFetcher Team"
```

### 1.2 Add necessary imports
Look for these patterns in the parser functions and add only what's needed:
- [ ] Standard library imports (re, json, html, etc.)
- [ ] Type hints (typing module)
- [ ] Dataclasses if used
- [ ] DO NOT import BeautifulSoup yet (handle in Phase 2)

## Step 2: Migrate Functions in Order (90 minutes)

### Group A: Helper Functions (30 min)
Navigate to each line number and copy the ENTIRE function:

- [ ] `extract_meta` (line ~1752)
  - Copy from `def extract_meta` to the end of function
  - This is a small helper, ~5 lines

- [ ] `extract_json_ld_content` (line ~1757)
  - Copy entire function including try/except blocks
  - Check for json import dependency

- [ ] `extract_from_modern_selectors` (line ~1810)
  - Large function, copy carefully
  - Note BeautifulSoup dependency for Phase 2

- [ ] `extract_text_from_html_fragment` (line ~1858)
  - Copy entire function
  - Check HTMLParser dependency

- [ ] `extract_list_content` (line ~3480)
  - Large function with ListItem dataclass
  - Copy ListItem class definition if present

### Group B: Site-Specific Parsers (45 min)
Copy each parser function COMPLETELY:

- [ ] `add_metrics_to_markdown` (line ~111)
  - Small utility function
  - Check FetchMetrics dataclass dependency

- [ ] `docusaurus_to_markdown` (line ~605)
  - ~180 lines, copy entire function
  - Note dependencies on extract_meta

- [ ] `mkdocs_to_markdown` (line ~787)
  - ~140 lines, copy entire function
  - Similar structure to docusaurus

- [ ] `wechat_to_markdown` (line ~1924)
  - ~790 lines, VERY LARGE function
  - Copy carefully, includes multiple internal helpers

- [ ] `xhs_to_markdown` (line ~2715)
  - ~170 lines
  - Includes JSON-LD extraction

- [ ] `dianping_to_markdown` (line ~2887)
  - ~155 lines
  - Site-specific parsing logic

- [ ] `ebchina_news_list_to_markdown` (line ~3042)
  - ~60 lines
  - List extraction logic

- [ ] `raw_to_markdown` (line ~3105)
  - ~720 lines, LARGE function
  - Multiple detection patterns

### Group C: Generic Parser (15 min)

- [ ] `generic_to_markdown` (line ~3827)
  - ~300 lines
  - Main fallback parser
  - Note filter_level parameter

## Step 3: Handle Dependencies (15 minutes)

### 3.1 Check for missing imports
Run this to check syntax:
```bash
python -c "import parsers"
```

### 3.2 Add missing type definitions
If you see NameError for types like:
- [ ] ListItem → Copy the dataclass definition
- [ ] FetchMetrics → Note for Phase 2 (stays in webfetcher)

### 3.3 Handle BeautifulSoup references
For now, add a comment at the top of parsers.py:
```python
# TODO Phase 2: Handle BeautifulSoup import and get_beautifulsoup_parser dependency
```

## Step 4: Validation (10 minutes)

### 4.1 Syntax Check
```bash
python -m py_compile parsers.py
```
- [ ] No syntax errors

### 4.2 Import Check
```python
python -c "import parsers; print('Import successful')"
```
- [ ] Import succeeds

### 4.3 Function Availability
```python
python -c "
import parsers
funcs = ['docusaurus_to_markdown', 'mkdocs_to_markdown', 'wechat_to_markdown', 
         'xhs_to_markdown', 'dianping_to_markdown', 'ebchina_news_list_to_markdown',
         'raw_to_markdown', 'generic_to_markdown', 'add_metrics_to_markdown']
for f in funcs:
    assert hasattr(parsers, f), f'{f} not found'
print('All functions present!')
"
```
- [ ] All functions found

### 4.4 Run Validation Script
```bash
python tests/phase1_parser_migration_test.py
```
- [ ] Validation passes

## Step 5: Documentation (5 minutes)

### 5.1 Create migration log
Create a simple text file noting what was moved:
```bash
echo "Phase 1 Migration Complete: $(date)" > migration_phase1.log
echo "Moved 9 parser functions and 5 helper functions" >> migration_phase1.log
echo "Files affected: parsers.py (created)" >> migration_phase1.log
```

### 5.2 Commit Phase 1
```bash
git add parsers.py
git add tests/phase1_parser_migration_test.py
git add PHASE1_*.md
git add migration_phase1.log
git commit -m "refactor(phase1): extract parser functions to parsers.py

- Created parsers.py with 9 parser functions
- Included necessary helper functions
- No logic changes, pure code movement
- Phase 2 will update imports and remove from webfetcher.py"
```

## Troubleshooting Guide

### Issue: Import errors when checking parsers.py
**Solution**: You're missing imports. Check the function for:
- re.compile → need `import re`
- json.loads → need `import json`
- datetime → need `import datetime`

### Issue: NameError for BeautifulSoup
**Solution**: This is expected in Phase 1. Add a TODO comment and handle in Phase 2.

### Issue: Function seems incomplete
**Solution**: Check if the function has nested functions or long content. Use line numbers as guide and scroll carefully.

### Issue: IndentationError
**Solution**: The function wasn't copied completely or indentation was changed. Re-copy preserving exact spacing.

## Phase 1 Complete! ✅

Once all boxes are checked:
1. Run validation script one more time
2. Commit your changes
3. Ready for Phase 2: Updating imports and cleaning webfetcher.py

**Time Tracking:**
- Start time: ________
- End time: ________
- Total duration: ________ (target: <2 hours)