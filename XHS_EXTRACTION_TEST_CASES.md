# XiaoHongShu Image Extraction Test Cases

## Test Case 1: Standard XHS Image Object
**Scenario**: Process typical XHS image data with urlDefault and infoList

**Input**:
```json
{
  "urlDefault": "http://sns-webpic-qc.xhscdn.com/202509181737/e637ee2f851df4e784176ae213892452/notes_pre_post/1040g3k031mg8ljhrli005nm1rt008v1fri75epo!nd_dft_wgth_jpg_3",
  "urlPre": "http://sns-webpic-qc.xhscdn.com/202509181737/ae4c5f70978bbf9d8aeb6411fce00802/notes_pre_post/1040g3k031mg8ljhrli005nm1rt008v1fri75epo!nd_prv_wgth_jpg_3",
  "url": "",
  "infoList": [
    {"imageScene": "WB_PRV", "url": "http://sns-webpic-qc.xhscdn.com/.../prv.jpg"},
    {"imageScene": "WB_DFT", "url": "http://sns-webpic-qc.xhscdn.com/.../dft.jpg"}
  ],
  "width": 2560,
  "height": 1920
}
```

**Expected Result**:
- Extract 1 image using `urlDefault`
- `XHSImageData` created with correct metadata
- Width: 2560, Height: 1920

## Test Case 2: Complete 8-Image Array
**Scenario**: Process actual imageList from test URL

**Input**: Full `imageList` array from `window.__INITIAL_STATE__`

**Expected Result**:
- Extract all 8 images
- First image marked as `is_cover=True`
- All URLs pass validation
- Preserve image order

## Test Case 3: Legacy Format Compatibility  
**Scenario**: Handle old-style image objects with url field

**Input**:
```json
{
  "url": "http://sns-webpic-qc.xhscdn.com/image.jpg",
  "pic": "http://sns-webpic-qc.xhscdn.com/pic.jpg", 
  "width": 1920,
  "height": 1080
}
```

**Expected Result**:
- Extract using `url` field
- Maintain backward compatibility

## Test Case 4: Preview-Only Image
**Scenario**: Image with only urlPre available

**Input**:
```json
{
  "urlPre": "http://sns-webpic-qc.xhscdn.com/.../preview.jpg",
  "urlDefault": "",
  "url": "",
  "infoList": []
}
```

**Expected Result**:
- Extract using `urlPre` as fallback
- Create valid `XHSImageData` object

## Test Case 5: InfoList-Only Image
**Scenario**: URL only available in infoList

**Input**:
```json
{
  "urlDefault": "",
  "urlPre": "",
  "url": "",
  "infoList": [
    {"imageScene": "WB_DFT", "url": "http://sns-webpic-qc.xhscdn.com/.../info.jpg"}
  ]
}
```

**Expected Result**:
- Extract from infoList WB_DFT scene
- Successful extraction

## Test Case 6: Malformed Object
**Scenario**: Handle missing or invalid fields gracefully

**Input**:
```json
{
  "width": "invalid",
  "height": null,
  "infoList": "not_an_array"
}
```

**Expected Result**:
- Skip malformed object
- No exceptions thrown
- Continue processing next images

## Test Case 7: String URL in Array
**Scenario**: Direct URL string in imageList array

**Input**:
```json
[
  "http://sns-webpic-qc.xhscdn.com/direct.jpg",
  {"urlDefault": "http://sns-webpic-qc.xhscdn.com/object.jpg"}
]
```

**Expected Result**:
- Extract both URLs
- Handle mixed array types

## Test Case 8: Empty or Invalid URLs
**Scenario**: Filter out invalid URLs

**Input**:
```json
{
  "urlDefault": "http://invalid-domain.com/image.jpg",
  "urlPre": "http://sns-webpic-qc.xhscdn.com/valid.jpg",
  "infoList": [
    {"imageScene": "WB_DFT", "url": ""}
  ]
}
```

**Expected Result**:
- Skip invalid domain URL
- Extract valid urlPre URL
- Apply domain validation correctly

## Validation Script Template

```python
def test_xhs_extraction():
    """Test XHS image extraction against all test cases"""
    
    # Test Case 1: Standard object
    standard_obj = {...}  # Test case 1 data
    extractor = XHSImageExtractor("<html>", "test-url")
    extractor._process_image_list([standard_obj])
    assert len(extractor.images) == 1
    assert extractor.images[0].width == 2560
    
    # Test Case 2: Full 8-image array
    with open('snapshot_xhslink.com_20250918_173707.html') as f:
        html = f.read()
    extractor = XHSImageExtractor(html, "http://xhslink.com/o/9aAFGUwOWq0")
    images = extractor.extract_all()
    assert len(images) == 8  # PRIMARY SUCCESS METRIC
    
    # Additional test cases...
    
if __name__ == "__main__":
    test_xhs_extraction()
    print("All tests passed!")
```

## Performance Benchmarks

### Timing Expectations
- Single image processing: < 1ms
- 8-image array processing: < 10ms  
- Full HTML parsing: < 100ms
- Memory usage: < 1MB additional

### Regression Testing URLs
1. `http://xhslink.com/o/9aAFGUwOWq0` - Should extract 8 images
2. Previous working XHS URLs - Should maintain same behavior
3. Non-XHS URLs - Should not interfere

## Acceptance Criteria

✅ **Primary Goal**: Extract all 8 images from test URL
✅ **Backward Compatibility**: Existing functionality unaffected  
✅ **Error Resilience**: Graceful handling of malformed data
✅ **Performance**: No significant slowdown
✅ **Code Quality**: Maintainable and well-documented

## Manual Testing Protocol

1. **Baseline Test**: Run original problematic URL
   - Expected: 1 image extracted (current behavior)

2. **Apply Fix**: Update `_process_image_list()` method  

3. **Verification Test**: Run same URL again
   - Expected: 8 images extracted (fixed behavior)

4. **Regression Test**: Test other XHS URLs
   - Expected: Same or improved results

5. **Edge Case Testing**: Run malformed data tests
   - Expected: Graceful error handling

This comprehensive test suite ensures the fix addresses the core issue while maintaining system reliability and performance.