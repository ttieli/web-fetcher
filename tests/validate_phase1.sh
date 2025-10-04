#!/bin/bash
# Phase 1 Validation Script

echo "=== Phase 1: Template System Foundation Validation ==="
echo

# Check directory structure
echo "1. Checking directory structure..."
test -d "parsers/engine" && echo "  ✓ parsers/engine exists"
test -d "parsers/templates" && echo "  ✓ parsers/templates exists"
test -d "parsers/utils" && echo "  ✓ parsers/utils exists"
echo

# Check core files exist
echo "2. Checking core files..."
test -f "parsers/templates/schema.yaml" && echo "  ✓ schema.yaml exists"
test -f "parsers/utils/validators.py" && echo "  ✓ validators.py exists"
test -f "parsers/engine/template_loader.py" && echo "  ✓ template_loader.py exists"
test -f "parsers/templates/generic.yaml" && echo "  ✓ generic.yaml exists"
echo

# Check imports work
echo "3. Testing imports..."
python3 -c "from parsers.utils.validators import TemplateValidator; print('  ✓ TemplateValidator imports')" 2>/dev/null
python3 -c "from parsers.engine.template_loader import TemplateLoader; print('  ✓ TemplateLoader imports')" 2>/dev/null
echo

# Run all tests
echo "4. Running test suite..."
python3 -m pytest tests/test_validator.py tests/test_loader.py tests/test_integration_phase1.py -v --tb=short

echo
echo "=== Phase 1 Validation Complete ==="
