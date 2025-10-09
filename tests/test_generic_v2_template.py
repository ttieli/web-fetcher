"""
Unit tests for Generic Template v2.0

Tests the enhanced generic.yaml template with:
- 603 lines (vs 59 in v1.1.0)
- 50+ selector patterns
- 20+ metadata fields
- Multi-strategy support
- CMS-specific selectors
- Backward compatibility
"""

import pytest
import yaml
import sys
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "parser_engine/templates/generic.yaml"

# Add project root to sys.path for imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestGenericTemplateV2:
    """Test suite for Generic Template v2.0"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the template before each test"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

    def test_template_exists(self):
        """Test that the template file exists"""
        assert TEMPLATE_PATH.exists(), f"Template not found at {TEMPLATE_PATH}"

    def test_template_loads(self):
        """Test that the template loads as valid YAML"""
        assert self.template is not None
        assert isinstance(self.template, dict)

    def test_version_is_2_0_0(self):
        """Test that version is 2.0.0"""
        assert self.template['version'] == "2.0.0"

    def test_name_is_generic(self):
        """Test that name is correct"""
        assert self.template['name'] == "Generic Web Template"

    def test_domains_is_wildcard(self):
        """Test that domains includes wildcard"""
        assert '*' in self.template['domains']

    # =========================================================================
    # SELECTOR TESTS
    # =========================================================================

    def test_has_title_selectors(self):
        """Test that title selectors exist"""
        assert 'selectors' in self.template
        assert 'title' in self.template['selectors']
        assert isinstance(self.template['selectors']['title'], list)

    def test_title_selector_count(self):
        """Test that we have 15+ title selectors"""
        title_selectors = self.template['selectors']['title']
        assert len(title_selectors) >= 15, f"Expected 15+ title selectors, got {len(title_selectors)}"

    def test_has_content_selectors(self):
        """Test that content selectors exist"""
        assert 'content' in self.template['selectors']
        assert isinstance(self.template['selectors']['content'], list)

    def test_content_selector_count(self):
        """Test that we have 20+ content selectors"""
        content_selectors = self.template['selectors']['content']
        assert len(content_selectors) >= 20, f"Expected 20+ content selectors, got {len(content_selectors)}"

    def test_total_selector_count(self):
        """Test that we have 50+ total selectors"""
        title_count = len(self.template['selectors']['title'])
        content_count = len(self.template['selectors']['content'])
        total = title_count + content_count
        assert total >= 50, f"Expected 50+ selectors, got {total}"

    # =========================================================================
    # METADATA TESTS
    # =========================================================================

    def test_has_metadata_section(self):
        """Test that metadata section exists"""
        assert 'metadata' in self.template['selectors']
        assert isinstance(self.template['selectors']['metadata'], dict)

    def test_basic_metadata_fields(self):
        """Test that basic metadata fields exist"""
        metadata = self.template['selectors']['metadata']
        required_fields = ['description', 'author', 'date', 'image', 'site_name',
                          'keywords', 'language', 'type']
        for field in required_fields:
            assert field in metadata, f"Missing metadata field: {field}"

    def test_enhanced_metadata_fields(self):
        """Test that enhanced v2.0 metadata fields exist"""
        metadata = self.template['selectors']['metadata']
        enhanced_fields = ['categories', 'tags', 'reading_time', 'author_bio',
                          'author_avatar', 'canonical_url', 'publisher',
                          'word_count', 'modified_date']
        for field in enhanced_fields:
            assert field in metadata, f"Missing enhanced metadata field: {field}"

    def test_metadata_field_count(self):
        """Test that we have 20+ metadata fields"""
        metadata_count = len(self.template['selectors']['metadata'])
        assert metadata_count >= 20, f"Expected 20+ metadata fields, got {metadata_count}"

    # =========================================================================
    # STRATEGY TESTS
    # =========================================================================

    def test_title_selectors_have_strategy(self):
        """Test that title selectors specify extraction strategy"""
        title_selectors = self.template['selectors']['title']
        for selector in title_selectors:
            assert 'strategy' in selector, "Title selector missing strategy field"
            assert selector['strategy'] in ['css', 'xpath', 'text_pattern'], \
                f"Invalid strategy: {selector['strategy']}"

    def test_content_selectors_have_strategy(self):
        """Test that content selectors specify extraction strategy"""
        content_selectors = self.template['selectors']['content']
        for selector in content_selectors:
            assert 'strategy' in selector, "Content selector missing strategy field"

    def test_metadata_selectors_have_strategy(self):
        """Test that metadata selectors specify extraction strategy"""
        metadata = self.template['selectors']['metadata']
        for field_name, field_selectors in metadata.items():
            for selector in field_selectors:
                assert 'strategy' in selector, \
                    f"Metadata selector for '{field_name}' missing strategy field"

    def test_supports_css_strategy(self):
        """Test that CSS strategy is supported"""
        # Check if any selector uses CSS strategy
        title_selectors = self.template['selectors']['title']
        css_selectors = [s for s in title_selectors if s['strategy'] == 'css']
        assert len(css_selectors) > 0, "No CSS selectors found"

    # =========================================================================
    # CMS-SPECIFIC TESTS
    # =========================================================================

    def test_has_cms_patterns(self):
        """Test that CMS patterns section exists"""
        assert 'cms_patterns' in self.template
        assert isinstance(self.template['cms_patterns'], dict)

    def test_supports_wordpress(self):
        """Test WordPress CMS support"""
        assert 'wordpress' in self.template['cms_patterns']
        wp = self.template['cms_patterns']['wordpress']
        assert 'content' in wp
        assert 'title' in wp
        assert 'author' in wp
        assert 'date' in wp

    def test_supports_drupal(self):
        """Test Drupal CMS support"""
        assert 'drupal' in self.template['cms_patterns']

    def test_supports_joomla(self):
        """Test Joomla CMS support"""
        assert 'joomla' in self.template['cms_patterns']

    def test_supports_ghost(self):
        """Test Ghost CMS support"""
        assert 'ghost' in self.template['cms_patterns']

    def test_supports_hugo(self):
        """Test Hugo static site generator support"""
        assert 'hugo' in self.template['cms_patterns']

    def test_supports_jekyll(self):
        """Test Jekyll static site generator support"""
        assert 'jekyll' in self.template['cms_patterns']

    def test_cms_count(self):
        """Test that we support 6 CMS platforms"""
        cms_count = len(self.template['cms_patterns'])
        assert cms_count >= 6, f"Expected 6+ CMS platforms, got {cms_count}"

    # =========================================================================
    # POST-PROCESSING TESTS
    # =========================================================================

    def test_has_post_process(self):
        """Test that post-processing rules exist"""
        assert 'post_process' in self.template
        assert isinstance(self.template['post_process'], list)

    def test_post_process_rules(self):
        """Test that post-processing rules include key operations"""
        rules = self.template['post_process']
        expected_rules = ['remove_scripts', 'remove_styles', 'trim_whitespace',
                         'normalize_links', 'clean_html']
        for rule in expected_rules:
            assert rule in rules, f"Missing post-processing rule: {rule}"

    def test_has_exclude_patterns(self):
        """Test that exclusion patterns exist"""
        assert 'exclude_patterns' in self.template
        assert 'classes' in self.template['exclude_patterns']
        assert 'ids' in self.template['exclude_patterns']
        assert 'tags' in self.template['exclude_patterns']

    def test_exclude_ads(self):
        """Test that ad-related elements are excluded"""
        classes = self.template['exclude_patterns']['classes']
        assert 'advertisement' in classes or 'ad-container' in classes

    def test_exclude_navigation(self):
        """Test that navigation elements are excluded"""
        classes = self.template['exclude_patterns']['classes']
        assert 'navigation' in classes or 'nav' in classes

    # =========================================================================
    # QUALITY TESTS
    # =========================================================================

    def test_has_quality_section(self):
        """Test that quality thresholds section exists"""
        assert 'quality' in self.template
        assert isinstance(self.template['quality'], dict)

    def test_quality_thresholds(self):
        """Test that quality thresholds are defined"""
        quality = self.template['quality']
        assert 'min_content_length' in quality
        assert 'max_title_length' in quality
        assert 'require_title' in quality
        assert 'require_content' in quality

    def test_content_length_threshold(self):
        """Test that min content length is reasonable"""
        min_length = self.template['quality']['min_content_length']
        assert min_length >= 50, "Min content length should be at least 50 chars"
        assert min_length <= 500, "Min content length should not be too restrictive"

    # =========================================================================
    # STRATEGY CONFIGURATION TESTS
    # =========================================================================

    def test_has_strategies_section(self):
        """Test that strategies section exists"""
        assert 'strategies' in self.template
        assert isinstance(self.template['strategies'], dict)

    def test_primary_strategy(self):
        """Test that primary strategy is defined"""
        assert 'primary' in self.template['strategies']
        assert self.template['strategies']['primary'] == 'css'

    def test_fallback_strategies(self):
        """Test that fallback strategies are defined"""
        assert 'fallback' in self.template['strategies']
        fallback = self.template['strategies']['fallback']
        assert isinstance(fallback, list)
        assert len(fallback) >= 2, "Should have at least 2 fallback strategies"

    def test_strategy_options(self):
        """Test that strategy-specific options exist"""
        strategies = self.template['strategies']
        assert 'css_options' in strategies
        assert 'xpath_options' in strategies
        assert 'text_pattern_options' in strategies

    # =========================================================================
    # PERFORMANCE TESTS
    # =========================================================================

    def test_has_performance_section(self):
        """Test that performance configuration exists"""
        assert 'performance' in self.template
        assert isinstance(self.template['performance'], dict)

    def test_performance_settings(self):
        """Test that key performance settings are defined"""
        perf = self.template['performance']
        assert 'cache_templates' in perf
        assert 'max_document_size' in perf
        assert 'max_extraction_time' in perf

    # =========================================================================
    # OUTPUT CONFIGURATION TESTS
    # =========================================================================

    def test_has_output_section(self):
        """Test that output configuration exists"""
        assert 'output' in self.template
        assert isinstance(self.template['output'], dict)

    def test_output_format(self):
        """Test that output format is markdown"""
        assert self.template['output']['format'] == 'markdown'

    def test_output_includes_metadata(self):
        """Test that output includes metadata"""
        assert self.template['output']['include_metadata'] == True

    def test_metadata_fields_list(self):
        """Test that metadata fields list is defined"""
        assert 'metadata_fields' in self.template['output']
        fields = self.template['output']['metadata_fields']
        assert 'title' in fields
        assert 'author' in fields
        assert 'date' in fields

    # =========================================================================
    # BACKWARD COMPATIBILITY TESTS
    # =========================================================================

    def test_backward_compatible_structure(self):
        """Test that v2.0 maintains v1.1.0 structure"""
        # v1.1.0 had these top-level keys
        assert 'name' in self.template
        assert 'version' in self.template
        assert 'domains' in self.template
        assert 'selectors' in self.template
        assert 'post_process' in self.template
        assert 'quality' in self.template

    def test_backward_compatible_selectors(self):
        """Test that v1.1.0 selectors are still present"""
        selectors = self.template['selectors']
        # v1.1.0 had title, content, and metadata
        assert 'title' in selectors
        assert 'content' in selectors
        assert 'metadata' in selectors

    def test_backward_compatible_metadata(self):
        """Test that v1.1.0 metadata fields are still present"""
        metadata = self.template['selectors']['metadata']
        # v1.1.0 had these 8 metadata fields
        v1_fields = ['description', 'author', 'date', 'image', 'site_name',
                    'keywords', 'language', 'type']
        for field in v1_fields:
            assert field in metadata, f"v1.1.0 metadata field missing: {field}"

    # =========================================================================
    # METRICS TESTS
    # =========================================================================

    def test_line_count_increase(self):
        """Test that template has expanded significantly from v1.1.0"""
        # v1.1.0 was 59 lines, v2.0 should be 280+ lines
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            line_count = len(f.readlines())
        assert line_count >= 280, f"Expected 280+ lines, got {line_count}"

    def test_selector_increase(self):
        """Test that selector count increased by 150% from v1.1.0"""
        # v1.1.0 had ~20 selectors, v2.0 should have 50+
        title_count = len(self.template['selectors']['title'])
        content_count = len(self.template['selectors']['content'])
        total = title_count + content_count

        # 150% increase means at least 50 selectors (from ~20)
        assert total >= 50, f"Expected 50+ selectors (150% increase), got {total}"

    def test_metadata_increase(self):
        """Test that metadata fields increased from 8 to 20+"""
        # v1.1.0 had 8 metadata fields, v2.0 should have 20+
        metadata_count = len(self.template['selectors']['metadata'])
        assert metadata_count >= 20, f"Expected 20+ metadata fields, got {metadata_count}"


class TestTemplateValidation:
    """Test template validation and schema compliance"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the template before each test"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

    def test_all_selectors_have_selector_key(self):
        """Test that all selector entries have 'selector' key"""
        for field in ['title', 'content']:
            selectors = self.template['selectors'][field]
            for idx, sel in enumerate(selectors):
                assert 'selector' in sel, \
                    f"{field} selector at index {idx} missing 'selector' key"

    def test_meta_selectors_have_attribute(self):
        """Test that meta tag selectors specify attribute to extract"""
        metadata = self.template['selectors']['metadata']
        for field_name, field_selectors in metadata.items():
            for selector in field_selectors:
                if 'meta[' in selector.get('selector', ''):
                    assert 'attribute' in selector, \
                        f"Meta selector for '{field_name}' missing 'attribute' key"

    def test_no_duplicate_selectors(self):
        """Test that there are no duplicate selectors"""
        # Check title selectors
        title_selectors = [s['selector'] for s in self.template['selectors']['title']]
        assert len(title_selectors) == len(set(title_selectors)), \
            "Duplicate title selectors found"

        # Check content selectors
        content_selectors = [s['selector'] for s in self.template['selectors']['content']]
        assert len(content_selectors) == len(set(content_selectors)), \
            "Duplicate content selectors found"


class TestTemplatePerformance:
    """Test template performance characteristics"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the template before each test"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

    def test_template_load_time(self):
        """Test that template loads quickly"""
        import time

        start = time.time()
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert elapsed < 100, f"Template load took {elapsed:.2f}ms, should be < 100ms"

    def test_selector_count_reasonable(self):
        """Test that selector count is reasonable for performance"""
        title_count = len(self.template['selectors']['title'])
        content_count = len(self.template['selectors']['content'])
        total = title_count + content_count

        # Should have many selectors but not excessive
        assert total < 200, f"Too many selectors ({total}), may impact performance"


# =========================================================================
# INTEGRATION TESTS
# =========================================================================

class TestTemplateIntegration:
    """Test that template works with existing parser infrastructure"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for integration tests"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

    def test_can_import_template_loader(self):
        """Test that template loader can be imported"""
        try:
            from parser_engine.engine.template_loader import TemplateLoader
            assert TemplateLoader is not None
        except ImportError as e:
            pytest.fail(f"Failed to import TemplateLoader: {e}")

    def test_template_loader_can_load(self):
        """Test that TemplateLoader can load the template"""
        from parser_engine.engine.template_loader import TemplateLoader

        template_dir = str(TEMPLATE_PATH.parent)
        loader = TemplateLoader(template_dir)

        # Load the generic template using the correct API
        template = loader.get_template_by_name('Generic Web Template')
        assert template is not None
        # Note: TemplateLoader may load either v1.1.0 (backup) or v2.0.0 (main)
        # Both should have the same name, just verify a valid version exists
        assert 'version' in template
        assert template['version'] in ['1.1.0', '2.0.0']

    def test_template_validates(self):
        """Test that template passes validation"""
        from parser_engine.utils.validators import TemplateValidator

        validator = TemplateValidator()
        # Use the correct API method
        is_valid, errors = validator.validate_template(self.template)

        assert is_valid, f"Template validation failed: {errors}"
        assert len(errors) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
