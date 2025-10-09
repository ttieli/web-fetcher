"""Phase 1 integration tests."""
import pytest
from parser_engine.engine.template_loader import TemplateLoader
from parser_engine.utils.validators import TemplateValidator


def test_full_template_system_flow():
    """Test complete flow: load template, validate, match URL."""
    # 1. Initialize loader
    loader = TemplateLoader()

    # 2. Verify templates loaded
    templates = loader.list_templates()
    assert len(templates) > 0, "Should have loaded templates"

    # 3. Get template for a URL
    template = loader.get_template_for_url("https://example.com/article")

    # 4. Validate returned template
    assert template is not None
    validator = TemplateValidator()
    is_valid, errors = validator.validate_template(template)
    assert is_valid, f"Template should be valid: {errors}"

    # 5. Check template structure
    assert 'selectors' in template
    assert 'title' in template['selectors'] or 'content' in template['selectors']


def test_generic_template_loaded():
    """Test that generic template is loaded and valid."""
    loader = TemplateLoader()

    generic = loader.get_template_by_name('Generic Web Template')

    assert generic is not None, "Generic template should be loaded"
    assert generic.get('name') == 'Generic Web Template'
    assert generic.get('version') == '1.1.0'
    assert '*' in generic.get('domains', [])


def test_validator_integration():
    """Test validator works with loaded templates."""
    loader = TemplateLoader()
    validator = TemplateValidator()

    # All loaded templates should be valid
    for name in loader.list_templates():
        template = loader.get_template_by_name(name)
        is_valid, errors = validator.validate_template(template)
        assert is_valid, f"Template '{name}' should be valid: {errors}"
