"""Tests for template validator."""
import pytest
from parsers.utils.validators import TemplateValidator


def test_valid_template():
    """Test that a valid template passes validation."""
    template = {
        'name': 'Test Template',
        'version': '1.0',
        'domains': ['example.com'],
        'selectors': {
            'title': 'h1',
            'content': 'article'
        }
    }

    validator = TemplateValidator()
    is_valid, errors = validator.validate_template(template)

    assert is_valid, f"Template should be valid but got errors: {errors}"
    assert len(errors) == 0


def test_missing_required_field():
    """Test that missing required fields are detected."""
    template = {
        'name': 'Test Template',
        'version': '1.0'
        # Missing 'domains' and 'selectors'
    }

    validator = TemplateValidator()
    is_valid, errors = validator.validate_template(template)

    assert not is_valid, "Template with missing required fields should be invalid"
    assert len(errors) > 0
    assert any('domains' in err for err in errors)
    assert any('selectors' in err for err in errors)


def test_invalid_field_type():
    """Test that invalid field types are detected."""
    template = {
        'name': 'Test Template',
        'version': '1.0',
        'domains': 'should-be-array',  # Wrong type
        'selectors': {
            'title': 'h1'
        }
    }

    validator = TemplateValidator()
    is_valid, errors = validator.validate_template(template)

    assert not is_valid, "Template with wrong type should be invalid"
    assert any('array' in err.lower() for err in errors)


def test_selectors_must_have_title_or_content():
    """Test that selectors must contain title or content."""
    template = {
        'name': 'Test Template',
        'version': '1.0',
        'domains': ['example.com'],
        'selectors': {
            'metadata': {'author': 'meta[name=author]'}
            # Missing both title and content
        }
    }

    validator = TemplateValidator()
    is_valid, errors = validator.validate_template(template)

    assert not is_valid, "Template without title/content selectors should be invalid"
    assert any('title' in err or 'content' in err for err in errors)
