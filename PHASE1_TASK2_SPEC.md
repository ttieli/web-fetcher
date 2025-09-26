# Phase 1 Task 2: Technical Specification
## Connect Parameters to Fetch Logic Implementation

### Overview
Task 2 connects the parameter framework from Task 1 to the actual fetch method selection logic, implementing the user preference system that controls how WebFetcher chooses between urllib and Selenium methods.

### Architectural Context
- **Prerequisite**: Task 1 completed and validated ✅
- **Dependencies**: Global variables `_user_method_choice` and `_user_no_fallback`
- **Integration Points**: Main function's render decision logic (line ~5035) and fallback logic (line ~5047)
- **Risk Level**: MEDIUM - Modifies core fetch logic but with fallback safety

### Implementation Requirements

#### 1. Method Selection Logic Integration

**Location**: Main function, around line 5035 where `should_render` is determined
**Current State**: Decision based on `args.render` and domain heuristics
**Target State**: Respect user preferences while maintaining intelligent fallback

**Current Code** (line ~5035):
```python
should_render = (args.render == 'always') or (args.render == 'auto' and ('xiaohongshu.com' in host or 'xhslink.com' in original_host or 'dianping.com' in host))
```

**Updated Logic**:
```python
# Check user method preference first
if _user_method_choice == 'selenium':
    should_render = True
    logging.info("Using Selenium/Playwright per user preference (overriding heuristics)")
elif _user_method_choice == 'urllib':
    should_render = False
    logging.info("Using urllib/static fetch per user preference (overriding heuristics)")
else:
    # Auto mode - use existing heuristics
    should_render = (args.render == 'always') or (args.render == 'auto' and ('xiaohongshu.com' in host or 'xhslink.com' in original_host or 'dianping.com' in host))
```

#### 2. Fallback Control Implementation

**Location**: Main function, around line 5047 where fallback occurs
**Current Behavior**: Automatically falls back to static fetch when rendering fails
**Target Behavior**: Respect `_user_no_fallback` preference

**Current Code** (lines ~5046-5048):
```python
else:
    logging.info("Rendering failed, falling back to static fetch")
    rendered = False
```

**Updated Logic**:
```python
else:
    if _user_no_fallback:
        logging.error("Rendering failed. Fallback disabled by user preference (--no-fallback)")
        # Set error metrics and exit
        fetch_metrics = FetchMetrics(
            primary_method="playwright",
            final_status="failed",
            error_message="Rendering failed, fallback disabled by user"
        )
        print(f"Error: Failed to fetch {url} with Selenium/Playwright (fallback disabled)", file=sys.stderr)
        sys.exit(1)
    else:
        logging.info("Rendering failed, falling back to static fetch")
        rendered = False
```

**Key Points**:
- Preserve error messages and logging
- Include clear indication when fallback is disabled
- Maintain metrics tracking for both scenarios
- Exit with proper error code when fallback disabled and primary method fails

#### 3. Logging Enhancement

**Requirements**:
- Log when user preference overrides heuristic decision
- Log when fallback is prevented by user preference
- Include method source in fetch metrics

**Log Messages**:
```python
# When user forces method
"Using {method} method per user preference (overriding heuristic suggestion)"

# When fallback is prevented
"Fetch failed with {method}. Fallback disabled by user preference."

# In metrics
metrics.method_source = 'user_preference' | 'heuristic' | 'fallback'
```

### Test Scenarios

#### Test Case 1: User Forces urllib
```bash
webfetcher -u https://js-heavy-site.com
```
**Expected**: Uses urllib even if site normally requires Selenium
**Validation**: Check logs for "per user preference"

#### Test Case 2: User Forces Selenium
```bash
webfetcher -s https://simple-static-site.com
```
**Expected**: Uses Selenium even for simple static content
**Validation**: Verify Selenium initialization in logs

#### Test Case 3: No Fallback - Success Case
```bash
webfetcher --method urllib --no-fallback https://static-site.com
```
**Expected**: Successful fetch with urllib, no fallback attempted
**Validation**: Single method attempt in metrics

#### Test Case 4: No Fallback - Failure Case
```bash
webfetcher -u --no-fallback https://js-only-site.com
```
**Expected**: Fails without attempting Selenium fallback
**Validation**: Error message indicates fallback was disabled

#### Test Case 5: Auto Mode (Default)
```bash
webfetcher https://any-site.com
```
**Expected**: Existing behavior unchanged
**Validation**: Heuristic selection and fallback work as before

### Implementation Checklist

- [ ] Locate main function's render decision logic (line ~5035)
- [ ] Add user preference check before heuristic logic
- [ ] Map user choices to `should_render` boolean correctly
- [ ] Locate fallback logic in main function (line ~5047)  
- [ ] Add `_user_no_fallback` check to prevent fallback when disabled
- [ ] Enhance logging with preference indicators
- [ ] Update metrics to track method source
- [ ] Create test script `test_phase1_task2.py`
- [ ] Test all 5 scenarios
- [ ] Verify backward compatibility

### Success Criteria

1. **Functional Requirements**:
   - User can force urllib method with -u/--urllib
   - User can force Selenium with -s/--selenium  
   - User can disable fallback with --no-fallback
   - Auto mode remains default behavior

2. **Quality Requirements**:
   - No breaking changes to existing functionality
   - Clear logging of user preference effects
   - Proper error handling when fallback disabled
   - Metrics accurately reflect method selection

3. **Test Requirements**:
   - All 5 test scenarios pass
   - No regression in existing functionality
   - Performance unchanged in auto mode
   - Clear error messages for user

### Risk Mitigation

**Risk 1**: Breaking existing auto-selection logic
**Mitigation**: Only add override at top of function, preserve all existing logic

**Risk 2**: Confusing error messages when fallback disabled
**Mitigation**: Add explicit message explaining fallback was disabled by user

**Risk 3**: Performance regression from additional checks
**Mitigation**: Simple variable checks have negligible performance impact

### Code Organization

**Files to Modify**:
- `webfetcher.py`: Main implementation in 2 functions

**Files to Create**:
- `test_phase1_task2.py`: Test script for Task 2

**No Breaking Changes**:
- All modifications are additive
- Existing code paths preserved
- Default behavior unchanged

### Implementation Notes

1. **DO NOT** refactor existing logic, only add user preference checks
2. **PRESERVE** all existing error handling and recovery mechanisms
3. **MAINTAIN** existing log format and levels for compatibility
4. **ENSURE** metrics remain backward compatible
5. **TEST** with real websites to verify behavior

### Estimated Effort
- Implementation: 30-45 minutes
- Testing: 20-30 minutes
- Total: ~1 hour

### Deliverables

1. Modified `webfetcher.py` with:
   - Updated `determine_fetch_strategy()` function
   - Updated `intelligent_fetch()` function
   - Enhanced logging

2. New `test_phase1_task2.py` with:
   - 5 test scenarios
   - Clear pass/fail reporting
   - Integration with real fetch operations

3. Validation evidence:
   - Test results showing all scenarios pass
   - Log samples demonstrating preference effects
   - Metrics showing correct method tracking

---

**Specification Author**: Archy-Principle-Architect
**Date**: 2025-09-26
**Status**: READY FOR IMPLEMENTATION