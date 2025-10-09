"""Tests for template loader."""
import pytest
from parser_engine.engine.template_loader import TemplateLoader


def test_loader_initialization():
    """Test that loader initializes and loads templates."""
    loader = TemplateLoader()

    # Should load at least the generic template
    templates = loader.list_templates()
    assert len(templates) > 0, "Should load at least one template"


def test_get_template_for_url():
    """Test URL to template matching."""
    loader = TemplateLoader()

    # Should match a URL to a template
    template = loader.get_template_for_url("https://example.com/page")

    assert template is not None, "Should return a template"
    assert 'name' in template
    assert 'selectors' in template


def test_fallback_to_generic():
    """Test fallback to generic template for unknown domains."""
    loader = TemplateLoader()

    # Unknown domain should get generic template
    template = loader.get_template_for_url("https://unknown-site-12345.com/")

    assert template is not None
    assert template.get('name') == 'Generic Web Template'


def test_wildcard_domain_matching():
    """Test wildcard domain pattern matching."""
    loader = TemplateLoader()

    # If we had a *.github.io template, test it
    # For now, just test that matching logic doesn't crash
    template = loader.get_template_for_url("https://user.github.io/repo")

    assert template is not None
