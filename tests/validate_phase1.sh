#!/bin/bash
# Phase 1 Validation Script

echo "=== Phase 1: Template System Foundation Validation ==="
echo

# Check directory structure
echo "1. Checking directory structure..."
test -d "parser_engine/engine" && echo "  ✓ parser_engine/engine exists"
test -d "parser_engine/templates" && echo "  ✓ parser_engine/templates exists"
test -d "parser_engine/utils" && echo "  ✓ parser_engine/utils exists"
echo

# Check core files exist
echo "2. Checking core files..."
test -f "parser_engine/templates/schema.yaml" && echo "  ✓ schema.yaml exists"
test -f "parser_engine/utils/validators.py" && echo "  ✓ validators.py exists"
test -f "parser_engine/engine/template_loader.py" && echo "  ✓ template_loader.py exists"
test -f "parser_engine/templates/generic.yaml" && echo "  ✓ generic.yaml exists"
echo

# Check imports work
echo "3. Testing imports..."
python3 -c "from parser_engine.utils.validators import TemplateValidator; print('  ✓ TemplateValidator imports')" 2>/dev/null
python3 -c "from parser_engine.engine.template_loader import TemplateLoader; print('  ✓ TemplateLoader imports')" 2>/dev/null
echo

# Run all tests
echo "4. Running test suite..."
python3 -m pytest tests/test_validator.py tests/test_loader.py tests/test_integration_phase1.py -v --tb=short

echo
echo "=== Phase 1 Validation Complete ==="
