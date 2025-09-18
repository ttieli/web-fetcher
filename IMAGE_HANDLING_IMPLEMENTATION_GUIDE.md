# Image Handling Implementation Guide

## Implementation Overview

This guide provides the structural blueprint for implementing the image handling architecture without providing actual code. Teams should use this as a reference for implementation while maintaining code ownership and quality standards.

## 1. Code Structure Changes

### 1.1 New Module Structure

```
webfetcher/
├── core/
│   ├── image_handler.py      # New: Image handling logic
│   ├── asset_manager.py      # New: Asset download management
│   └── config.py             # New: Configuration management
├── parsers/
│   ├── base_parser.py        # Modified: Add image handling interface
│   ├── generic_parser.py     # Modified: Implement new interface
│   ├── weixin_parser.py      # Modified: Remove auto-download
│   └── xhs_parser.py         # Modified: Remove auto-download
└── webfetcher.py             # Modified: Integrate new components
```

### 1.2 Configuration Schema

```yaml
# config.schema.yaml
image_handling:
  default_mode: "links"       # links|download|skip|smart
  auto_download_domains: []   # Empty by default (was: [mp.weixin.qq.com, xiaohongshu.com])
  size_limit_mb: null         # No limit by default
  allowed_formats:            # All formats by default
    - jpg
    - jpeg
    - png
    - gif
    - webp
    - svg
  smart_rules:
    min_width: 100           # Skip tiny images
    min_height: 100
    max_size_mb: 10
    skip_patterns:           # URL patterns to skip
      - "avatar"
      - "favicon"
      - "icon"
```

## 2. Implementation Checklist

### Phase 1: Core Changes (Week 1)

#### Day 1-2: Argument Parsing
- [ ] Add `--skip-images` argument to ArgumentParser
- [ ] Add deprecation warning for domain-specific auto-downloads
- [ ] Update help text to reflect new defaults
- [ ] Add environment variable check for `WF_LEGACY_IMAGE_MODE`

#### Day 3-4: Parser Updates
- [ ] Create abstract method `should_download_images()` in base parser
- [ ] Update generic parser to check flags instead of domain
- [ ] Update WeChat parser to respect flags
- [ ] Update XiaoHongShu parser to respect flags
- [ ] Update Dianping parser to respect flags
- [ ] Ensure raw parser preserves all content

#### Day 5: Integration
- [ ] Modify main flow to use new image handling logic
- [ ] Update `rewrite_and_download_assets()` function calls
- [ ] Add logging for image handling decisions
- [ ] Test all parsers with new behavior

### Phase 2: Enhanced Control (Week 2)

#### Day 1-2: Mode Implementation
- [ ] Define ImageHandlingMode enum
- [ ] Implement mode selection logic
- [ ] Add `--images` argument with mode choices
- [ ] Map legacy flags to modes

#### Day 3-4: Asset Manager
- [ ] Create AssetManager class
- [ ] Implement process_images() method
- [ ] Add mode-specific processing logic
- [ ] Integrate with existing download function

#### Day 5: Testing
- [ ] Unit tests for each mode
- [ ] Integration tests for mode transitions
- [ ] Performance benchmarks
- [ ] Documentation updates

### Phase 3: Smart Features (Future)

- [ ] Implement image analysis (size, dimensions)
- [ ] Add smart filtering rules
- [ ] Implement progressive download
- [ ] Add caching layer
- [ ] Implement thumbnail generation

## 3. Code Modification Points

### 3.1 Main Entry Point (webfetcher.py)

**Location**: Around line 4500-4600 (main function)

**Changes Required**:
1. Update argument parser with new flags
2. Add mode selection logic
3. Remove hardcoded domain checks
4. Add legacy mode support

**Key Functions to Modify**:
- `main()` - Add new argument handling
- `process_url()` - Update image download logic
- `save_content()` - Integrate new image handling

### 3.2 Asset Download Function

**Location**: `rewrite_and_download_assets()` function

**Changes Required**:
1. Add mode parameter
2. Implement skip mode (return markdown unchanged)
3. Add size checking for smart mode
4. Add format filtering

**Interface Change**:
```python
# From:
def rewrite_and_download_assets(md, md_base, outdir, ua, assets_root)

# To:
def rewrite_and_download_assets(md, md_base, outdir, ua, assets_root, mode, config)
```

### 3.3 Parser Modifications

**Common Changes for All Parsers**:

1. **Remove Domain Checks**:
   - Location: Lines with `'mp.weixin.qq.com' in host`
   - Action: Remove or make conditional on flags

2. **Add Mode Support**:
   - Location: Parser class definitions
   - Action: Add image_mode parameter

3. **Update Metadata**:
   - Location: Metadata dictionary creation
   - Action: Ensure 'images' key always present

### 3.4 Command Wrapper (wf.py)

**Location**: Mode-specific command handlers

**Changes Required**:

1. **Full Mode** (line ~188):
   - Keep `--download-assets` flag
   - Document behavior in help

2. **Fast Mode** (line ~174):
   - Remove any download flags
   - Ensure links preserved

3. **Raw Mode** (line ~206):
   - No changes needed
   - Already preserves everything

## 4. Testing Implementation

### 4.1 Unit Test Structure

```
tests/
├── test_image_handler.py
│   ├── test_mode_selection()
│   ├── test_legacy_compatibility()
│   └── test_environment_override()
├── test_asset_manager.py
│   ├── test_download_with_mode()
│   ├── test_skip_mode()
│   └── test_smart_filtering()
└── test_parsers_image_handling.py
    ├── test_generic_parser_modes()
    ├── test_weixin_no_auto_download()
    └── test_xhs_no_auto_download()
```

### 4.2 Integration Test Scenarios

1. **End-to-End Mode Tests**:
   - Default behavior (links only)
   - Explicit download flag
   - Skip images flag
   - Full mode compatibility

2. **Migration Tests**:
   - Legacy script compatibility
   - Environment variable override
   - Domain-specific behavior change

3. **Performance Tests**:
   - Bandwidth usage comparison
   - Execution time measurement
   - Resource consumption analysis

## 5. Documentation Updates

### 5.1 README.md Updates

**Sections to Modify**:

1. **Quick Start**:
   - Update examples with new default behavior
   - Add image handling examples

2. **Command Reference**:
   - Document new flags
   - Update mode descriptions

3. **Migration Guide** (New Section):
   - Explain behavior changes
   - Provide update instructions
   - Show before/after examples

### 5.2 Help Text Updates

**Location**: Argument parser help strings

**Updates Required**:
1. Main help text explaining default behavior
2. Flag descriptions with clear explanations
3. Mode-specific help in wf.py

### 5.3 Inline Documentation

**Key Areas**:
1. Function docstrings for modified functions
2. Class docstrings for new components
3. Comments explaining behavior changes
4. TODO markers for future phases

## 6. Rollback Plan

### 6.1 Quick Rollback

**Environment Variable**:
```bash
export WF_LEGACY_IMAGE_MODE=1
```

**Code Location**: Early in main() function
```python
if os.environ.get('WF_LEGACY_IMAGE_MODE'):
    # Apply legacy behavior
    pass
```

### 6.2 Feature Flag

**Implementation**:
1. Add `--legacy-image-handling` flag
2. Check flag before mode selection
3. Log deprecation warning

### 6.3 Version Pinning

**For Users**:
1. Document last version with old behavior
2. Provide installation instructions for old version
3. Maintain branch with legacy behavior

## 7. Deployment Strategy

### 7.1 Pre-Deployment

1. **Code Review Checklist**:
   - [ ] All parsers updated
   - [ ] Tests passing
   - [ ] Documentation complete
   - [ ] Migration guide ready

2. **Testing Checklist**:
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Performance benchmarks acceptable
   - [ ] Manual testing complete

### 7.2 Deployment Steps

1. **Stage 1: Documentation** (Day -3):
   - Publish migration guide
   - Update online documentation
   - Send announcement to users

2. **Stage 2: Release** (Day 0):
   - Tag release with clear version number
   - Include detailed changelog
   - Monitor error rates

3. **Stage 3: Support** (Day 1-7):
   - Monitor user feedback
   - Quick response to issues
   - Collect improvement suggestions

### 7.3 Success Metrics

**Week 1**:
- Error rate < 0.1%
- Performance improvement > 30%
- User complaints < 5

**Month 1**:
- Adoption of new flags > 20%
- Bandwidth savings > 50%
- Positive feedback > negative

## 8. Risk Mitigation

### 8.1 Identified Risks

1. **Breaking Changes**:
   - Risk: Existing scripts fail
   - Mitigation: Legacy mode, clear migration guide

2. **Performance Regression**:
   - Risk: New logic slower
   - Mitigation: Benchmarking, optimization

3. **User Confusion**:
   - Risk: Unexpected behavior
   - Mitigation: Clear documentation, warnings

### 8.2 Contingency Plans

1. **High Error Rate**:
   - Immediate: Enable legacy mode by default
   - Short-term: Hotfix release
   - Long-term: Redesign approach

2. **User Revolt**:
   - Immediate: Communication and support
   - Short-term: Optional update
   - Long-term: Feature flags for gradual rollout

## 9. Quality Gates

### 9.1 Code Quality

- [ ] No reduction in test coverage
- [ ] All linting passes
- [ ] Security scan clean
- [ ] Performance benchmarks pass

### 9.2 Functional Quality

- [ ] All test cases pass
- [ ] Manual testing complete
- [ ] User acceptance testing done
- [ ] Migration tested on real data

### 9.3 Documentation Quality

- [ ] All changes documented
- [ ] Examples updated
- [ ] Migration guide reviewed
- [ ] Help text accurate

## 10. Future Enhancements

### Planned for Phase 2

1. **Configuration File Support**:
   - User-specific defaults
   - Per-domain rules
   - Smart filtering rules

2. **Enhanced Modes**:
   - Thumbnail mode
   - Selective download
   - Format conversion

### Planned for Phase 3

1. **Smart Features**:
   - Content-aware filtering
   - Duplicate detection
   - Compression options

2. **Performance Optimizations**:
   - Parallel downloads
   - Caching layer
   - Progressive loading

## Conclusion

This implementation guide provides the blueprint for updating the Web_Fetcher image handling behavior. The phased approach ensures minimal disruption while delivering immediate value through reduced bandwidth usage and improved performance. Teams should follow this guide while maintaining code quality standards and testing rigor.