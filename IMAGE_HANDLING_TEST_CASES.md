# Image Handling Test Cases

## Test Suite Overview

This document provides comprehensive test scenarios for validating the image handling architecture changes. Each test case includes setup, execution steps, and validation criteria.

## 1. Behavior Validation Tests

### Test 1.1: Default Behavior - Link Preservation

```bash
# Setup
TEST_URL="https://example.com/article-with-images"
OUTPUT_DIR="./test-output-default"

# Execute
wf "$TEST_URL" "$OUTPUT_DIR"

# Validate
# 1. Check markdown file exists
test -f "$OUTPUT_DIR"/*.md || echo "FAIL: No markdown file created"

# 2. Verify image links are preserved
grep -E '!\[.*\]\(https?://.*\)' "$OUTPUT_DIR"/*.md || echo "FAIL: No image links found"

# 3. Verify no assets directory created
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Assets directory should not exist"

# 4. Check metadata includes image URLs
grep '"images":' "$OUTPUT_DIR"/*.json 2>/dev/null || echo "WARN: No JSON metadata"

# Expected output in markdown:
# ![](https://example.com/image1.jpg)
# ![](https://cdn.example.com/photos/image2.png)

# Cleanup
rm -rf "$OUTPUT_DIR"
```

### Test 1.2: Explicit Download Flag

```bash
# Setup
TEST_URL="https://example.com/article-with-images"
OUTPUT_DIR="./test-output-download"

# Execute
wf "$TEST_URL" "$OUTPUT_DIR" --download-assets

# Validate
# 1. Check assets directory exists
test -d "$OUTPUT_DIR/assets" || echo "FAIL: Assets directory not created"

# 2. Verify images downloaded
IMAGE_COUNT=$(find "$OUTPUT_DIR/assets" -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.webp" \) | wc -l)
[ "$IMAGE_COUNT" -gt 0 ] || echo "FAIL: No images downloaded"

# 3. Verify markdown has rewritten links
grep -E '!\[.*\]\(assets/.*\)' "$OUTPUT_DIR"/*.md || echo "FAIL: Links not rewritten"

# Expected output in markdown:
# ![](assets/2025-09-18-120000 - Article Title/01.jpg)
# ![](assets/2025-09-18-120000 - Article Title/02.png)

# Cleanup
rm -rf "$OUTPUT_DIR"
```

### Test 1.3: Skip Images Flag

```bash
# Setup
TEST_URL="https://example.com/article-with-images"
OUTPUT_DIR="./test-output-skip"

# Execute (Phase 2 feature)
wf "$TEST_URL" "$OUTPUT_DIR" --skip-images

# Validate
# 1. Verify no image references in markdown
! grep -E '!\[.*\]\(' "$OUTPUT_DIR"/*.md || echo "FAIL: Image references found"

# 2. Verify no assets directory
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Assets directory should not exist"

# 3. Verify content is otherwise intact
grep -q "article content" "$OUTPUT_DIR"/*.md || echo "FAIL: Content missing"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

## 2. Mode-Specific Tests

### Test 2.1: Full Mode Behavior

```bash
# Setup
TEST_URL="https://example.com/article-with-images"
OUTPUT_DIR="./test-output-full"

# Execute
wf full "$TEST_URL" "$OUTPUT_DIR"

# Validate
# Full mode should download assets by default (backward compatibility)
test -d "$OUTPUT_DIR/assets" || echo "FAIL: Full mode should download assets"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

### Test 2.2: Raw Mode Behavior

```bash
# Setup
TEST_URL="https://example.com/article-with-images"
OUTPUT_DIR="./test-output-raw"

# Execute
wf raw "$TEST_URL" "$OUTPUT_DIR"

# Validate
# Raw mode should preserve links without downloading
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Raw mode should not download"
grep -E '!\[.*\]\(https?://.*\)' "$OUTPUT_DIR"/*.md || echo "FAIL: Links not preserved"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

### Test 2.3: Fast Mode Behavior

```bash
# Setup
TEST_URL="https://example.com/article-with-images"
OUTPUT_DIR="./test-output-fast"

# Execute
wf fast "$TEST_URL" "$OUTPUT_DIR"

# Validate
# Fast mode should preserve links without downloading
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Fast mode should not download"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

## 3. Domain-Specific Tests

### Test 3.1: WeChat Articles (No Auto-Download)

```bash
# Setup
WEIXIN_URL="https://mp.weixin.qq.com/s/example"
OUTPUT_DIR="./test-output-weixin"

# Execute
wf "$WEIXIN_URL" "$OUTPUT_DIR"

# Validate
# Should NOT auto-download anymore (behavior change)
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Should not auto-download for WeChat"

# Verify links preserved
grep -E '!\[.*\]\(https?://.*\)' "$OUTPUT_DIR"/*.md || echo "FAIL: Links not preserved"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

### Test 3.2: XiaoHongShu Posts (No Auto-Download)

```bash
# Setup
XHS_URL="https://www.xiaohongshu.com/explore/example"
OUTPUT_DIR="./test-output-xhs"

# Execute
wf "$XHS_URL" "$OUTPUT_DIR"

# Validate
# Should NOT auto-download anymore (behavior change)
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Should not auto-download for XHS"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

## 4. Migration Tests

### Test 4.1: Legacy Script Compatibility

```bash
# Simulate existing script that expects downloads
#!/bin/bash

# Old script expecting auto-downloads
URLS=("https://mp.weixin.qq.com/s/article1" 
      "https://www.xiaohongshu.com/post1")

for url in "${URLS[@]}"; do
    # Old way (would download automatically)
    # wf "$url" ./output/
    
    # New way (explicit download flag needed)
    wf "$url" ./output/ --download-assets
done

# Validate downloads occurred
test -d ./output/assets || echo "FAIL: Migration requires --download-assets flag"
```

### Test 4.2: Environment Variable Override

```bash
# Setup legacy mode via environment variable
export WF_LEGACY_IMAGE_MODE=1
TEST_URL="https://mp.weixin.qq.com/s/example"
OUTPUT_DIR="./test-output-legacy"

# Execute
wf "$TEST_URL" "$OUTPUT_DIR"

# Validate
# With legacy mode, should auto-download for specific domains
test -d "$OUTPUT_DIR/assets" || echo "WARN: Legacy mode might not be implemented"

# Cleanup
unset WF_LEGACY_IMAGE_MODE
rm -rf "$OUTPUT_DIR"
```

## 5. Edge Cases Tests

### Test 5.1: Mixed Content Types

```bash
# Test page with various media types
TEST_URL="https://example.com/mixed-media"
OUTPUT_DIR="./test-output-mixed"

# Execute with explicit image handling
wf "$TEST_URL" "$OUTPUT_DIR" --download-assets

# Validate
# Should only download image types, not videos/audio
find "$OUTPUT_DIR/assets" -type f \( -name "*.mp4" -o -name "*.mp3" \) | \
    grep -q . && echo "FAIL: Non-image media downloaded"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

### Test 5.2: Invalid Image URLs

```bash
# Create test HTML with broken image links
cat > test.html << 'EOF'
<html>
<body>
<img src="https://broken.example.com/404.jpg">
<img src="not-a-url">
<img src="">
</body>
</html>
EOF

# Execute
wf --html test.html ./test-output-broken --download-assets

# Validate
# Should handle failures gracefully
test -f ./test-output-broken/*.md || echo "FAIL: Should create output despite broken images"

# Check that broken URLs are preserved, not rewritten
grep "broken.example.com" ./test-output-broken/*.md || echo "FAIL: Failed URLs should remain"

# Cleanup
rm -f test.html
rm -rf ./test-output-broken
```

### Test 5.3: Large Image Handling

```bash
# Test with size limits (Phase 3 feature)
TEST_URL="https://example.com/huge-images"
OUTPUT_DIR="./test-output-size-limit"

# Execute with size limit
wf "$TEST_URL" "$OUTPUT_DIR" --download-assets --image-size-limit 5

# Validate
# No single image should exceed 5MB
for img in "$OUTPUT_DIR"/assets/*/*; do
    [ -f "$img" ] || continue
    SIZE=$(stat -f%z "$img" 2>/dev/null || stat -c%s "$img" 2>/dev/null)
    [ "$SIZE" -le 5242880 ] || echo "FAIL: Image exceeds size limit: $img"
done

# Cleanup
rm -rf "$OUTPUT_DIR"
```

## 6. Performance Tests

### Test 6.1: Bandwidth Usage Comparison

```bash
# Measure bandwidth with and without downloads
TEST_URL="https://example.com/image-heavy-article"

# Baseline: with downloads
time wf "$TEST_URL" ./test-with-download --download-assets
DL_SIZE=$(du -sh ./test-with-download | cut -f1)

# New default: links only
time wf "$TEST_URL" ./test-links-only
LINK_SIZE=$(du -sh ./test-links-only | cut -f1)

echo "Storage used with downloads: $DL_SIZE"
echo "Storage used with links only: $LINK_SIZE"

# Cleanup
rm -rf ./test-with-download ./test-links-only
```

### Test 6.2: Execution Time Comparison

```bash
# Compare execution times
TEST_URL="https://example.com/multi-image-article"

# Time with downloads
START=$(date +%s)
wf "$TEST_URL" ./test-timed-download --download-assets
END=$(date +%s)
DOWNLOAD_TIME=$((END - START))

# Time without downloads
START=$(date +%s)
wf "$TEST_URL" ./test-timed-links
END=$(date +%s)
LINK_TIME=$((END - START))

echo "Time with downloads: ${DOWNLOAD_TIME}s"
echo "Time with links only: ${LINK_TIME}s"
echo "Speed improvement: $(( (DOWNLOAD_TIME - LINK_TIME) * 100 / DOWNLOAD_TIME ))%"

# Cleanup
rm -rf ./test-timed-download ./test-timed-links
```

## 7. Integration Tests

### Test 7.1: Batch Processing

```bash
# Create URL list with mixed content
cat > urls.txt << EOF
https://example.com/article1
https://mp.weixin.qq.com/s/article2
https://www.xiaohongshu.com/post3
EOF

# Execute batch with new default
wf batch urls.txt ./test-batch-output

# Validate
# No assets should be downloaded by default
test ! -d ./test-batch-output/assets || echo "FAIL: Batch should not download by default"

# All markdown files should exist
[ $(ls ./test-batch-output/*.md 2>/dev/null | wc -l) -eq 3 ] || echo "FAIL: Missing output files"

# Cleanup
rm -f urls.txt
rm -rf ./test-batch-output
```

### Test 7.2: Site Crawl Mode

```bash
# Test site crawl with image handling
TEST_SITE="https://docs.example.com"
OUTPUT_DIR="./test-site-crawl"

# Execute
wf site "$TEST_SITE" "$OUTPUT_DIR" --max-pages 5

# Validate
# Site mode should preserve links by default
test ! -d "$OUTPUT_DIR/assets" || echo "FAIL: Site mode should not download by default"

# Multiple pages should be captured
[ $(ls "$OUTPUT_DIR"/*.md 2>/dev/null | wc -l) -gt 1 ] || echo "FAIL: Site crawl incomplete"

# Cleanup
rm -rf "$OUTPUT_DIR"
```

## 8. Validation Scripts

### Comprehensive Test Runner

```bash
#!/bin/bash
# test-image-handling.sh

set -e

echo "Starting Image Handling Test Suite"
echo "==================================="

TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    echo -n "Running $test_name... "
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo "PASS"
        ((TESTS_PASSED++))
    else
        echo "FAIL"
        ((TESTS_FAILED++))
    fi
}

# Run all tests
run_test "Default Link Preservation" "test_default_preserves_links"
run_test "Explicit Download" "test_explicit_download"
run_test "Full Mode Compatibility" "test_full_mode"
run_test "WeChat No Auto-Download" "test_weixin_no_auto"
run_test "Performance Improvement" "test_performance"

echo ""
echo "Test Results:"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"

exit $TESTS_FAILED
```

## 9. Acceptance Criteria Summary

### Phase 1 Acceptance

- [ ] Default behavior preserves links without downloading
- [ ] `--download-assets` flag explicitly triggers downloads
- [ ] Full mode maintains backward compatibility
- [ ] All parsers correctly populate image metadata
- [ ] No automatic downloads for specific domains
- [ ] Documentation updated with behavior changes
- [ ] Migration guide available for users

### Phase 2 Acceptance

- [ ] `--skip-images` flag removes image references
- [ ] `--images` flag supports multiple modes
- [ ] Configuration file support for defaults
- [ ] Smart download rules configurable

### Phase 3 Acceptance

- [ ] Size limits enforced for downloads
- [ ] Format filtering works correctly
- [ ] Thumbnail generation option available
- [ ] Performance metrics meet targets

## Test Execution Guidelines

1. **Manual Testing**: Run each test case individually during development
2. **Automated Testing**: Use test runner script for regression testing
3. **Performance Testing**: Execute on various network conditions
4. **Compatibility Testing**: Test with existing scripts and workflows
5. **User Acceptance**: Gather feedback from early adopters

## Monitoring and Validation

After deployment, monitor:

1. **Error Rates**: Check for increased failures
2. **Performance Metrics**: Validate bandwidth savings
3. **User Feedback**: Track support requests
4. **Adoption Rates**: Monitor flag usage patterns