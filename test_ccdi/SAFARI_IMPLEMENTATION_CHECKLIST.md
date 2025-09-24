# Safari Integration Implementation Checklist
**For:** Cody Fullstack Engineer  
**Date:** 2025-09-23  
**Priority:** Production Implementation  
**Time Estimate:** 6 days

## Pre-Implementation Checklist

### Environment Setup
- [ ] Verify macOS environment available
- [ ] Check Safari browser installed and accessible
- [ ] Confirm AppleScript permissions for Terminal/Python
- [ ] Verify Python 3.7+ installed
- [ ] Check BeautifulSoup4 installed (`pip show beautifulsoup4`)
- [ ] Confirm existing Web_Fetcher installation working
- [ ] Test basic `wf` command functionality

### Code Review
- [ ] Read SAFARI_INTEGRATION_PLAN.md thoroughly
- [ ] Review existing ccdi_production_extractor.py 
- [ ] Understand current webfetcher.py fetch flow
- [ ] Review safari_fallback_wrapper.py for patterns
- [ ] Check test results in test reports

## Phase 1: Foundation Setup (Day 1)

### Task 1.1: Create Directory Structure
```bash
cd /Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher
```
- [ ] Create `safari_extractor.py` in root
- [ ] Create `safari_config.py` in root  
- [ ] Create `extractors/` directory
- [ ] Create `extractors/__init__.py`
- [ ] Create `extractors/base_extractor.py`
- [ ] Create `extractors/ccdi_extractor.py`
- [ ] Create `extractors/qcc_extractor.py`
- [ ] Create `extractors/generic_extractor.py`

### Task 1.2: Implement Base Extractor Class
File: `extractors/base_extractor.py`
- [ ] Define abstract base class
- [ ] Add required methods: `extract()`, `validate()`, `convert_to_markdown()`
- [ ] Implement logging setup
- [ ] Add error handling base methods
- [ ] Include Safari automation helpers
- [ ] Add content validation methods

### Task 1.3: Set Up Configuration System
File: `safari_config.py`
- [ ] Define environment variable readers
- [ ] Create SAFARI_SITES dictionary
- [ ] Add CAPTCHA_INDICATORS list
- [ ] Set up timeout configurations
- [ ] Add site-specific settings
- [ ] Include debug/logging levels

### Task 1.4: Implement Logging Infrastructure
- [ ] Set up centralized logger
- [ ] Add log rotation configuration
- [ ] Create debug mode settings
- [ ] Implement performance timing logs
- [ ] Add extraction metrics logging

## Phase 2: Core Integration (Day 2)

### Task 2.1: Create Safari Extractor Module
File: `safari_extractor.py`
- [ ] Import required dependencies
- [ ] Create SafariExtractor class
- [ ] Implement `should_use_safari()` method
  - [ ] Check URL patterns
  - [ ] Detect CAPTCHA indicators
  - [ ] Evaluate content quality
  - [ ] Check error conditions
- [ ] Implement `fetch_with_safari()` method
  - [ ] Route to site-specific extractor
  - [ ] Handle extraction errors
  - [ ] Convert results to webfetcher format
- [ ] Add cleanup methods
- [ ] Implement timeout handling

### Task 2.2: Modify fetch_html_with_retry Function
File: `webfetcher.py` (around line 1650)
- [ ] Locate fetch_html_with_retry function
- [ ] Add Safari extractor import (conditional)
- [ ] Insert Safari fallback check after standard fetch
- [ ] Update metrics tracking for Safari method
- [ ] Ensure backward compatibility
- [ ] Test modification doesn't break existing flow

### Task 2.3: Add Safari Detection Helper
File: `webfetcher.py` (new helper function)
- [ ] Create `is_safari_extracted()` helper
- [ ] Add content marker for Safari-extracted HTML
- [ ] Implement validation helper
- [ ] Add to parser selection logic

### Task 2.4: Implement Result Conversion
- [ ] Create HTML to webfetcher format converter
- [ ] Preserve metadata from Safari extraction
- [ ] Ensure date extraction compatibility
- [ ] Maintain encoding handling

## Phase 3: Site-Specific Extractors (Day 3-4)

### Task 3.1: Implement CCDI Extractor
File: `extractors/ccdi_extractor.py`
- [ ] Import CCDIProductionExtractor from test_ccdi
- [ ] Create CCDIExtractor class extending BaseExtractor
- [ ] Implement extract() method
  - [ ] Initialize Safari automation
  - [ ] Navigate to URL
  - [ ] Wait for page load
  - [ ] Extract HTML content
  - [ ] Parse content structure
- [ ] Implement validate() method
  - [ ] Check for article content
  - [ ] Validate Chinese text presence
  - [ ] Ensure no CAPTCHA remains
- [ ] Implement convert_to_markdown()
  - [ ] Extract title, date, content
  - [ ] Format as clean markdown
  - [ ] Add metadata

### Task 3.2: Implement QCC Extractor
File: `extractors/qcc_extractor.py`
- [ ] Port QCC extraction logic from test files
- [ ] Create QCCExtractor class
- [ ] Implement company data extraction
- [ ] Handle dynamic content loading
- [ ] Add QCC-specific validation
- [ ] Format business data properly

### Task 3.3: Implement Generic Extractor
File: `extractors/generic_extractor.py`
- [ ] Create fallback extractor for any site
- [ ] Implement basic content extraction
- [ ] Add readability algorithm
- [ ] Include basic content cleaning
- [ ] Provide minimal formatting

### Task 3.4: Create Extractor Factory
File: `extractors/__init__.py`
- [ ] Implement get_extractor_for_site()
- [ ] Add site pattern matching
- [ ] Handle extractor initialization
- [ ] Include fallback to generic
- [ ] Add error handling

## Phase 4: Testing & Validation (Day 5)

### Task 4.1: Create Unit Tests
File: `test_safari_unit.py`
- [ ] Test Safari availability detection
- [ ] Test CAPTCHA indicator detection
- [ ] Test site pattern matching
- [ ] Test extractor factory
- [ ] Test error conditions
- [ ] Test timeout handling

### Task 4.2: Create Integration Tests
File: `test_safari_integration.py`
- [ ] Test CCDI extraction end-to-end
- [ ] Test QCC extraction end-to-end
- [ ] Test fallback triggering
- [ ] Test metrics collection
- [ ] Test concurrent extractions
- [ ] Test error recovery

### Task 4.3: Perform Manual Testing
- [ ] Test with real CCDI article URL
- [ ] Test with QCC company page
- [ ] Test with site that doesn't need Safari
- [ ] Test with Safari unavailable
- [ ] Test with network issues
- [ ] Test with malformed URLs

### Task 4.4: Performance Testing
- [ ] Measure extraction time for CCDI
- [ ] Measure extraction time for QCC  
- [ ] Compare with standard fetch
- [ ] Test memory usage
- [ ] Check for resource leaks
- [ ] Validate cleanup procedures

## Phase 5: Production Preparation (Day 6)

### Task 5.1: Error Handling Enhancement
- [ ] Add comprehensive try-catch blocks
- [ ] Implement graceful degradation
- [ ] Add retry logic for transient failures
- [ ] Include timeout recovery
- [ ] Log all error conditions
- [ ] Create error reporting

### Task 5.2: Performance Monitoring
- [ ] Add timing metrics
- [ ] Implement success rate tracking
- [ ] Create performance logs
- [ ] Add resource usage monitoring
- [ ] Include extraction statistics
- [ ] Set up alerting thresholds

### Task 5.3: Documentation
- [ ] Create README for Safari extraction
- [ ] Document configuration options
- [ ] Write troubleshooting guide
- [ ] Add usage examples
- [ ] Document API changes
- [ ] Create operations runbook

### Task 5.4: Deployment Preparation
- [ ] Create deployment script
- [ ] Set up environment variables
- [ ] Prepare rollback procedure
- [ ] Document deployment steps
- [ ] Create health check script
- [ ] Set up monitoring dashboard

## Post-Implementation Checklist

### Validation
- [ ] All tests passing
- [ ] No regression in existing functionality
- [ ] Safari extraction working for CCDI
- [ ] Safari extraction working for QCC
- [ ] Fallback working correctly
- [ ] Metrics being collected

### Code Quality
- [ ] Code follows existing patterns
- [ ] Proper error handling throughout
- [ ] Logging at appropriate levels
- [ ] Comments for complex logic
- [ ] No hardcoded values
- [ ] Configuration externalized

### Documentation
- [ ] All new files have headers
- [ ] Functions have docstrings
- [ ] Complex logic commented
- [ ] README updated
- [ ] Change log updated
- [ ] API documentation complete

### Deployment Readiness
- [ ] Feature flag tested
- [ ] Rollback tested
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Performance acceptable
- [ ] Security reviewed

## Critical Files to Modify

### Core Modifications (Handle with Care!)
1. **webfetcher.py**
   - Location: Line ~1650 (fetch_html_with_retry function)
   - Change: Add Safari fallback check
   - Impact: Core fetch flow
   - Rollback: Remove Safari check block

2. **webfetcher.py** 
   - Location: Line ~5000 (parser selection)
   - Change: Add Safari content detection
   - Impact: Parser routing
   - Rollback: Remove Safari parser check

### New Files to Create (Safe to Add)
1. **safari_extractor.py** - Main Safari module
2. **safari_config.py** - Configuration
3. **extractors/** - Site-specific extractors

## Testing Commands

### Basic Functionality Tests
```bash
# Test CCDI extraction
python safari_extractor.py --test-ccdi

# Test QCC extraction  
python safari_extractor.py --test-qcc

# Test with wf command
WF_ENABLE_SAFARI=1 wf "https://www.ccdi.gov.cn/yaowen/..."

# Test without Safari
WF_ENABLE_SAFARI=0 wf "https://www.ccdi.gov.cn/yaowen/..."
```

### Integration Tests
```bash
# Run full test suite
python -m pytest test_safari_integration.py -v

# Run specific test
python -m pytest test_safari_integration.py::test_ccdi_extraction -v

# Run with coverage
python -m pytest --cov=safari_extractor test_safari_integration.py
```

## Common Issues & Solutions

### Issue 1: Safari Permission Denied
**Solution:** Grant Terminal/Python AppleScript permissions in System Preferences

### Issue 2: Safari Not Found
**Solution:** Ensure Safari is installed and can be launched manually

### Issue 3: Extraction Timeout
**Solution:** Increase WF_SAFARI_TIMEOUT environment variable

### Issue 4: Content Validation Fails
**Solution:** Update site-specific validation rules in extractor

### Issue 5: Safari Window Management
**Solution:** Implement proper cleanup in extractor cleanup() method

## Support Resources

### Reference Documentation
- Original CCDI extractor: `test_ccdi/ccdi_production_extractor.py`
- Safari wrapper example: `test_ccdi/safari_fallback_wrapper.py`
- Integration tests: `test_ccdi/test_safari_integration.py`

### Key Contacts
- Architecture: Archy-Principle-Architect
- Testing: Review test reports in test_ccdi/
- Production: Follow Web_Fetcher operational guidelines

## Sign-Off Checklist

### Pre-Production Review
- [ ] Code review completed
- [ ] Tests reviewed and passing
- [ ] Documentation reviewed
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Rollback plan validated

### Production Release
- [ ] Deployed to production
- [ ] Feature flag configured
- [ ] Monitoring active
- [ ] Initial extraction successful
- [ ] No regression detected
- [ ] Handoff completed

---

## Notes for Implementation

1. **Start Simple:** Begin with CCDI only, add QCC after validation
2. **Test Frequently:** Run tests after each major change
3. **Keep Backwards Compatibility:** Ensure existing functionality unchanged
4. **Use Feature Flags:** Always implement behind WF_ENABLE_SAFARI flag
5. **Document Changes:** Update documentation as you implement
6. **Ask Questions:** Clarify requirements before implementing complex logic

**Remember:** This is a production system. Test thoroughly, implement carefully, and always have a rollback plan.

---
*Checklist prepared for Cody Fullstack Engineer*  
*Refer to SAFARI_INTEGRATION_PLAN.md for detailed architecture*