# Phase 1 Parser Migration Specification
**Architect**: Archy-Principle-Architect  
**Date**: 2025-09-25  
**Duration**: 2 hours maximum  
**Risk Level**: Low (Pure code movement, no logic changes)

## Executive Summary
Phase 1 focuses exclusively on extracting parser functions from `webfetcher.py` into a new `parsers.py` file. This is a pure refactoring operation with zero functional changes.

## 1. Scope Definition

### In Scope (Phase 1)
- Create new `parsers.py` file
- Move 9 parser functions and their direct dependencies
- Ensure syntactic correctness of both files
- No functional changes to any code

### Out of Scope (Reserved for Phase 2)
- Modifying webfetcher.py imports
- Updating function calls
- Any logic changes
- Testing integration

## 2. Functions to Migrate

### Primary Parser Functions (MUST migrate)
```python
# Line numbers from webfetcher.py
1. add_metrics_to_markdown      (line 111)
2. docusaurus_to_markdown       (line 605)
3. mkdocs_to_markdown           (line 787)
4. wechat_to_markdown          (line 1924)
5. xhs_to_markdown             (line 2715)
6. dianping_to_markdown        (line 2887)
7. ebchina_news_list_to_markdown (line 3042)
8. raw_to_markdown             (line 3105)
9. generic_to_markdown          (line 3827)
```

### Helper Functions (MUST migrate if used by parsers)
```python
# Analyze dependencies and migrate as needed:
- extract_meta                 (line 1752)
- extract_json_ld_content      (line 1757)
- extract_from_modern_selectors (line 1810)
- extract_text_from_html_fragment (line 1858)
- extract_list_content          (line 3480)
```

### Shared Dependencies (DO NOT migrate)
```python
# These stay in webfetcher.py as they're used by other components:
- get_beautifulsoup_parser     (line 254)
- extract_with_htmlparser      (line 489)
- get_effective_host           (line 1675)
```

## 3. Migration Process

### Step 1: Create parsers.py Structure
```python
#!/usr/bin/env python3
"""
Web content parsers for different site types.
Extracted from webfetcher.py for better modularity.
"""

# Import statements (copy ONLY what's needed)
import re
import json
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
# ... other necessary imports

# Helper functions (if needed by parsers)
def extract_meta(html: str, name_or_prop: str) -> str:
    # Copy exact implementation
    pass

# Parser functions
def docusaurus_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    # Copy exact implementation
    pass

# ... rest of parser functions
```

### Step 2: Migration Checklist
For each function being migrated:

1. **Copy Complete Function**
   - [ ] Copy function signature exactly
   - [ ] Copy entire function body
   - [ ] Include all docstrings
   - [ ] Preserve all comments

2. **Handle Dependencies**
   - [ ] Identify all functions called within
   - [ ] Check if they're parser-specific helpers
   - [ ] Migrate helper functions if needed
   - [ ] Note shared dependencies for Phase 2

3. **Import Analysis**
   - [ ] List all imports used by the function
   - [ ] Add necessary imports to parsers.py
   - [ ] Don't import unnecessary modules

### Step 3: Preserve Function Order
Maintain logical grouping:
```
1. Helper functions (extract_*, process_*)
2. Site-specific parsers (docusaurus, mkdocs, wechat, etc.)
3. Generic parsers (raw, generic)
4. Utility functions (add_metrics)
```

## 4. Quality Assurance

### Validation Points
1. **Syntax Validation**
   ```bash
   python -m py_compile parsers.py
   ```

2. **Import Test**
   ```python
   import parsers
   # Should succeed without errors
   ```

3. **Function Availability**
   ```python
   import parsers
   assert hasattr(parsers, 'docusaurus_to_markdown')
   assert hasattr(parsers, 'generic_to_markdown')
   # ... check all migrated functions
   ```

4. **Run Validation Script**
   ```bash
   python tests/phase1_parser_migration_test.py
   ```

## 5. Common Pitfalls to Avoid

### ❌ DO NOT
- Change any function logic
- Rename any functions
- Modify function signatures
- Update webfetcher.py imports yet
- Try to optimize or refactor code
- Add new features or fixes

### ✅ DO
- Copy functions exactly as they are
- Maintain all whitespace and formatting
- Preserve all comments and docstrings
- Include necessary helper functions
- Verify syntax after migration

## 6. Dependencies Matrix

| Parser Function | Helper Dependencies | External Dependencies |
|----------------|--------------------|-----------------------|
| docusaurus_to_markdown | extract_meta, BeautifulSoup* | re, json |
| mkdocs_to_markdown | extract_meta, BeautifulSoup* | re, json |
| wechat_to_markdown | extract_json_ld_content | re, json, datetime |
| xhs_to_markdown | extract_json_ld_content | re, json |
| generic_to_markdown | extract_from_modern_selectors, extract_text_from_html_fragment | re, BeautifulSoup* |

*Note: BeautifulSoup usage via get_beautifulsoup_parser() - handle in Phase 2

## 7. Success Criteria

### Phase 1 is complete when:
- [ ] parsers.py exists with all 9 parser functions
- [ ] All necessary helper functions are included
- [ ] parsers.py has valid Python syntax
- [ ] parsers.py can be imported successfully
- [ ] Validation script passes all checks
- [ ] No runtime changes to webfetcher.py yet

## 8. Phase 1 Deliverables

1. **parsers.py** - New file containing all parser functions
2. **Migration log** - Document which functions were moved
3. **Validation report** - Output from phase1_parser_migration_test.py

## 9. Time Estimates

| Task | Duration |
|------|----------|
| Analyze dependencies | 15 min |
| Create parsers.py structure | 10 min |
| Migrate parser functions | 45 min |
| Migrate helper functions | 30 min |
| Validate migration | 20 min |
| **Total** | **2 hours** |

## 10. Next Steps (Phase 2 Preview)

After Phase 1 completion:
1. Update webfetcher.py to import from parsers
2. Remove migrated functions from webfetcher.py
3. Test end-to-end functionality
4. Update documentation

---

**Architecture Decision Record (ADR)**

**Decision**: Implement two-phase parser extraction
**Status**: Approved
**Context**: webfetcher.py has grown to 65k+ tokens
**Decision**: Split migration into two phases for risk mitigation
**Consequences**: 
- Positive: Lower risk, easier rollback, clear validation points
- Negative: Temporary code duplication between phases
**Alternatives Considered**: Single-phase migration (rejected due to higher risk)