# ADR-001: Backward Compatibility for fetch_html_with_metrics

## Status
APPROVED - Immediate implementation required

## Context
During the plugin system migration, the `fetch_html_with_metrics` function was removed without providing a backward compatibility alias. This breaks existing code that depends on this API.

## Decision
Add a function alias mapping `fetch_html_with_metrics` to `fetch_html_with_plugins` to maintain backward compatibility.

## Rationale
1. **Zero Breaking Changes**: Existing code continues to work without modification
2. **Minimal Risk**: Simple alias addition with no logic changes
3. **Clear Migration Path**: Users can migrate at their own pace
4. **Consistent Interface**: All functions return (html, metrics) tuple

## Implementation
```python
# In webfetcher.py, after line 1462
fetch_html_with_metrics = fetch_html_with_plugins
```

## Consequences
### Positive
- No breaking changes for existing users
- Smooth migration path to plugin system
- Maintains API stability

### Negative
- Multiple names for same functionality (temporary)
- Need to maintain aliases until major version bump

## Testing Strategy
1. Use https://www.example.com as standard test URL
2. Verify all function aliases work correctly
3. Confirm return format consistency
4. Test with both legacy and new code patterns

## Migration Timeline
- Phase 1 (Now): Add alias for immediate compatibility
- Phase 2 (Future): Deprecation warnings in next minor version
- Phase 3 (Future): Remove in next major version (2.0)

## Approval
- Architecture: Approved
- Implementation: Pending
- Testing: Required before merge