# Web_Fetcher Image Handling - Development Handoff Plan

## Executive Summary

This document provides a comprehensive, actionable plan for the cody-fullstack-engineer to implement image handling improvements in the Web_Fetcher tool. The primary goal is to change the default behavior from automatically downloading images to preserving image URLs only, while adding an explicit flag for downloads.

## Phase 1 Implementation (Critical - Priority 1)

### Objective
Change default behavior to preserve image links without downloading, add explicit control via `--download-assets` flag.

### Specific Code Changes Required

#### 1. File: `webfetcher.py` - Main Argument Parser

**Location**: Lines 2072-2101 (main function, argument parser setup)

**Task 1.1**: Add deprecation warning and environment variable check
```python
# After line 2101 (after args = ap.parse_args()), ADD:
# Check for legacy mode environment variable
if os.environ.get('WF_LEGACY_IMAGE_MODE'):
    logging.warning("DEPRECATION: WF_LEGACY_IMAGE_MODE is set. Auto-download behavior will be removed in future versions.")
    # Set a flag for legacy behavior
    args.legacy_image_mode = True
else:
    args.legacy_image_mode = False
```

**Task 1.2**: Update help text for `--download-assets` flag
```python
# Line 2084, MODIFY the help text:
# FROM: help='Download images to assets/<file>/ and rewrite links'
# TO: help='Download images to assets/<file>/ and rewrite links (default: preserve URLs only)'
```

#### 2. File: `webfetcher.py` - Remove Automatic Domain Downloads

**Location**: Lines 2179 and 2323 (two identical lines)

**Task 2.1**: Modify image download decision logic

```python
# Line 2179, REPLACE:
# FROM: do_download_assets = args.download_assets or ('mp.weixin.qq.com' in host) or ('xiaohongshu.com' in host)
# TO: 
if hasattr(args, 'legacy_image_mode') and args.legacy_image_mode:
    # Legacy behavior for backward compatibility
    do_download_assets = args.download_assets or ('mp.weixin.qq.com' in host) or ('xiaohongshu.com' in host)
else:
    # New default: only download if explicitly requested
    do_download_assets = args.download_assets

# Line 2323, APPLY THE SAME CHANGE
```

#### 3. File: `wf.py` - Command Wrapper Updates

**Location**: Lines 174-190 (full mode handler)

**Task 3.1**: Ensure full mode maintains download behavior
```python
# In the full mode command construction (around line 188)
# Verify that '--download-assets' is included in the command
# This maintains backward compatibility for full mode
```

### Implementation Order

1. **Start with webfetcher.py changes**:
   - Add environment variable check (Task 1.1)
   - Update help text (Task 1.2)
   - Modify download logic (Task 2.1)

2. **Verify wf.py full mode**:
   - Ensure full mode includes `--download-assets` flag

3. **Test each change incrementally**

## Testing Protocol

### Test Case 1: Default Behavior (No Downloads)
```bash
# Test that default behavior preserves links
python webfetcher.py https://mp.weixin.qq.com/s/example ./test-default/

# Validation:
ls ./test-default/assets/ 2>/dev/null && echo "FAIL: Assets downloaded" || echo "PASS: No downloads"
grep -E '!\[.*\]\(https?://' ./test-default/*.md && echo "PASS: URLs preserved" || echo "FAIL: No URLs"
```

### Test Case 2: Explicit Download Flag
```bash
# Test that --download-assets works
python webfetcher.py https://mp.weixin.qq.com/s/example ./test-download/ --download-assets

# Validation:
ls ./test-download/assets/ && echo "PASS: Assets downloaded" || echo "FAIL: No downloads"
grep -E '!\[.*\]\(assets/' ./test-download/*.md && echo "PASS: Links rewritten" || echo "FAIL: Links not rewritten"
```

### Test Case 3: Legacy Mode Compatibility
```bash
# Test environment variable override
export WF_LEGACY_IMAGE_MODE=1
python webfetcher.py https://mp.weixin.qq.com/s/example ./test-legacy/

# Validation:
ls ./test-legacy/assets/ && echo "PASS: Legacy auto-download works" || echo "FAIL: Legacy mode broken"
unset WF_LEGACY_IMAGE_MODE
```

### Test Case 4: Full Mode Compatibility
```bash
# Test that full mode still downloads
python wf.py full https://example.com/article ./test-full/

# Validation:
ls ./test-full/assets/ && echo "PASS: Full mode downloads" || echo "FAIL: Full mode broken"
```

### Test Case 5: Multiple Domain Types
```bash
# Test various domains without downloads
for url in "https://mp.weixin.qq.com/s/test" "https://www.xiaohongshu.com/test" "https://example.com/test"; do
    python webfetcher.py "$url" ./test-domains/
    if [ -d "./test-domains/assets" ]; then
        echo "FAIL: $url auto-downloaded (should not)"
    else
        echo "PASS: $url preserved links only"
    fi
    rm -rf ./test-domains/
done
```

## Success Criteria

### Functional Requirements
- [ ] Default behavior preserves image URLs without downloading
- [ ] `--download-assets` flag explicitly triggers downloads
- [ ] Full mode (`wf full`) maintains download behavior
- [ ] WeChat articles no longer auto-download by default
- [ ] XiaoHongShu posts no longer auto-download by default
- [ ] Legacy mode environment variable works as fallback

### Performance Benchmarks
- [ ] Default mode executes 30-50% faster (no downloads)
- [ ] Bandwidth usage reduced by 70-90% in default mode
- [ ] No performance regression when using `--download-assets`

### Code Quality
- [ ] All existing tests pass
- [ ] New behavior properly logged
- [ ] No runtime errors or exceptions
- [ ] Clean handling of edge cases

## Files to Modify - Summary

1. **webfetcher.py** (Primary):
   - Line 2084: Update help text
   - After line 2101: Add environment check
   - Lines 2179, 2323: Modify download logic

2. **wf.py** (Verification only):
   - Verify line ~188: Full mode includes `--download-assets`

## Implementation Notes

### Important Considerations

1. **Preserve Existing Functions**: Do not modify the `rewrite_and_download_assets` function itself - it should continue to work when called.

2. **Backward Compatibility**: The environment variable `WF_LEGACY_IMAGE_MODE` provides an escape hatch for users who need the old behavior.

3. **Logging**: Add appropriate logging when decisions are made about image handling to aid debugging.

4. **Error Handling**: Ensure graceful handling if image URLs are malformed or downloads fail.

### Common Pitfalls to Avoid

1. **Don't break raw mode**: Raw mode should continue to preserve everything as-is
2. **Don't affect HTML saving**: The `--save-html` functionality should remain unchanged
3. **Don't modify parser logic**: Parsers should continue to collect image URLs in metadata
4. **Maintain JSON output**: The `--json` flag should still include image URLs in output

## Validation Checklist for Architect Review

After implementation, I will verify:

### Code Review
- [ ] Environment variable check implemented correctly
- [ ] Download logic modified at both locations (lines 2179, 2323)
- [ ] Help text updated to reflect new behavior
- [ ] No unintended side effects in other modes

### Functional Testing
- [ ] Test Case 1: Default preserves links ✓
- [ ] Test Case 2: Explicit download works ✓
- [ ] Test Case 3: Legacy mode functions ✓
- [ ] Test Case 4: Full mode unchanged ✓
- [ ] Test Case 5: All domains respect new default ✓

### Performance Testing
- [ ] Measure execution time improvement
- [ ] Verify bandwidth usage reduction
- [ ] Check memory usage remains stable

### Documentation
- [ ] Help text accurately describes behavior
- [ ] Comments explain the change rationale
- [ ] Legacy mode documented for users

## Phase 2 Enhancement (Optional - If Time Permits)

### Additional Control Flags
Only implement if Phase 1 is complete and tested:

1. **Add `--skip-images` flag**: Remove all image references from output
2. **Add `--images <mode>` flag**: Support modes (links/download/skip/smart)
3. **Add configuration file support**: Allow defaults in config file

These are lower priority and should only be attempted after Phase 1 is fully validated.

## Handoff Communication

### For the Engineer

1. **Start with Phase 1 only** - This is the critical change needed
2. **Test after each modification** - Use the provided test cases
3. **Preserve all existing functionality** - Only change the default behavior
4. **Use the environment variable** for testing legacy compatibility
5. **Document any challenges** encountered during implementation

### Expected Timeline

- Phase 1 implementation: 2-3 hours
- Testing and validation: 1-2 hours
- Total estimated time: 3-5 hours

### Definition of Done

Phase 1 is complete when:
1. All test cases pass
2. No existing functionality is broken
3. Default behavior changed as specified
4. Legacy escape hatch works
5. Code is ready for architect review

## Support Resources

### Key Functions Reference
- `rewrite_and_download_assets()`: Lines 2007-2069 - DO NOT MODIFY
- `main()`: Lines 2072-2357 - PRIMARY WORK AREA
- Parser functions: Various locations - NO CHANGES NEEDED

### Testing Commands Quick Reference
```bash
# Quick test suite
./run_image_tests.sh  # Create this script with all test cases

# Manual verification
python webfetcher.py <url> ./test/ [--download-assets]
ls ./test/assets/ 2>/dev/null  # Check for downloads
grep -c '!\[.*\](http' ./test/*.md  # Count preserved URLs
grep -c '!\[.*\](assets/' ./test/*.md  # Count rewritten links
```

## Questions to Address Before Starting

1. Confirm Python version compatibility requirements
2. Verify test environment has network access
3. Ensure ability to set/unset environment variables
4. Confirm write permissions to test directories

---

**Document Version**: 1.0
**Created**: 2025-09-18
**Architecture Owner**: Archy-Principle-Architect
**Implementation Owner**: cody-fullstack-engineer
**Status**: Ready for Handoff