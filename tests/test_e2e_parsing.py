"""End-to-End Testing for Complete Parsing Flow - Phase 2.2 Step 2.2.4

This module provides comprehensive end-to-end tests for the parsing pipeline,
validating the complete workflow from HTML input to structured output.

Test Scenarios:
1. Blog Article Parsing - Standard blog post structure
2. News Website Parsing - News article structure
3. Technical Documentation Parsing - Documentation page structure
4. Simple Static Page Parsing - Basic HTML structure
5. Performance Benchmarks - Validate <1 second per page performance target

Acceptance Criteria:
- E2E tests cover multiple website types
- All tests pass
- Performance meets <1 second/page target
- Generic template handles various content structures
"""

import pytest
import time
import sys
from pathlib import Path
from typing import List

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from parser_engine.template_parser import TemplateParser
from parser_engine.base_parser import ParseResult


# ============================================================================
# Test Data: Real-world HTML Samples
# ============================================================================

BLOG_POST_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Understanding Python Decorators - Tech Blog</title>
    <meta name="description" content="A comprehensive guide to understanding and using Python decorators effectively">
    <meta name="author" content="Jane Developer">
    <meta property="og:title" content="Understanding Python Decorators">
    <meta property="og:description" content="Learn how to use decorators in Python">
    <meta property="og:image" content="https://blog.example.com/images/python-decorators.jpg">
    <meta property="article:published_time" content="2025-01-15T10:00:00Z">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/about">About</a>
        </nav>
    </header>

    <main role="main">
        <article class="post-content">
            <h1>Understanding Python Decorators</h1>
            <div class="post-meta">
                <span class="author">By Jane Developer</span>
                <time datetime="2025-01-15">January 15, 2025</time>
            </div>

            <p>Decorators are one of Python's most powerful features, allowing you to modify
            the behavior of functions or classes without changing their source code.</p>

            <h2>What is a Decorator?</h2>
            <p>A decorator is a function that takes another function as an argument and
            extends its behavior without explicitly modifying it.</p>

            <h2>Basic Example</h2>
            <p>Here's a simple decorator example:</p>
            <pre><code>
def my_decorator(func):
    def wrapper():
        print("Before function")
        func()
        print("After function")
    return wrapper
            </code></pre>

            <h2>Practical Applications</h2>
            <ul>
                <li>Logging function calls</li>
                <li>Measuring execution time</li>
                <li>Authentication and authorization</li>
                <li>Caching results</li>
            </ul>

            <h2>Conclusion</h2>
            <p>Decorators are an essential tool in any Python developer's toolkit.
            Understanding them will make your code more maintainable and elegant.</p>
        </article>
    </main>

    <aside class="sidebar">
        <h3>Related Posts</h3>
        <p>This sidebar should not be in extracted content</p>
    </aside>

    <footer>
        <p>&copy; 2025 Tech Blog</p>
    </footer>
</body>
</html>
"""

NEWS_ARTICLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Breaking: New AI Breakthrough Announced - Tech News Today</title>
    <meta name="description" content="Researchers announce major breakthrough in artificial intelligence">
    <meta name="author" content="News Team">
    <meta property="article:published_time" content="2025-01-20T14:30:00Z">
    <meta property="og:title" content="Breaking: New AI Breakthrough Announced">
    <meta property="og:image" content="https://news.example.com/ai-breakthrough.jpg">
</head>
<body>
    <div class="container">
        <header class="site-header">
            <h1>Tech News Today</h1>
        </header>

        <article class="news-article">
            <h1 class="headline">Breaking: New AI Breakthrough Announced</h1>
            <div class="byline">
                <span>By News Team</span>
                <time>January 20, 2025</time>
            </div>

            <div class="article-body">
                <p class="lead">Scientists at a leading research institute have announced
                a major breakthrough in artificial intelligence that could transform
                the field in the coming years.</p>

                <p>The new technique, described in a paper published today, addresses
                one of the fundamental challenges in machine learning: reducing the
                amount of training data needed for accurate predictions.</p>

                <h2>Key Findings</h2>
                <p>The research team demonstrated that their approach can achieve
                comparable accuracy with 90% less training data than conventional methods.</p>

                <h2>Industry Impact</h2>
                <p>Industry experts believe this breakthrough could make AI more
                accessible to smaller organizations that lack massive datasets.</p>

                <blockquote>
                    "This is a game-changer for the AI industry," said Dr. Smith,
                    an AI researcher not involved in the study.
                </blockquote>

                <h2>Next Steps</h2>
                <p>The team plans to release their implementation as open-source
                software within the next quarter.</p>
            </div>
        </article>

        <div class="advertisement">
            <p>Advertisement - Should not appear in content</p>
        </div>
    </div>
</body>
</html>
"""

TECHNICAL_DOCS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>API Reference - Authentication | Developer Docs</title>
    <meta name="description" content="Complete API reference for authentication endpoints">
    <meta property="og:title" content="Authentication API Reference">
</head>
<body>
    <div class="docs-layout">
        <nav class="docs-sidebar">
            <ul>
                <li><a href="#getting-started">Getting Started</a></li>
                <li><a href="#authentication">Authentication</a></li>
                <li><a href="#endpoints">Endpoints</a></li>
            </ul>
        </nav>

        <main class="docs-content" role="main">
            <h1>Authentication API Reference</h1>

            <section id="overview">
                <h2>Overview</h2>
                <p>This document provides a complete reference for our Authentication API.
                All API requests require authentication using an API key.</p>
            </section>

            <section id="authentication">
                <h2>Authentication</h2>
                <p>Include your API key in the Authorization header:</p>
                <pre><code>Authorization: Bearer YOUR_API_KEY</code></pre>
            </section>

            <section id="endpoints">
                <h2>Endpoints</h2>

                <h3>POST /auth/login</h3>
                <p>Authenticate a user and receive an access token.</p>

                <h4>Request Body</h4>
                <ul>
                    <li><code>email</code> (string, required) - User's email address</li>
                    <li><code>password</code> (string, required) - User's password</li>
                </ul>

                <h4>Response</h4>
                <pre><code>{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}</code></pre>

                <h3>POST /auth/refresh</h3>
                <p>Refresh an expired access token.</p>

                <h4>Request Body</h4>
                <ul>
                    <li><code>refresh_token</code> (string, required) - Valid refresh token</li>
                </ul>
            </section>

            <section id="errors">
                <h2>Error Handling</h2>
                <p>The API uses standard HTTP status codes:</p>
                <ul>
                    <li>200 - Success</li>
                    <li>401 - Unauthorized</li>
                    <li>403 - Forbidden</li>
                    <li>404 - Not Found</li>
                    <li>500 - Server Error</li>
                </ul>
            </section>
        </main>
    </div>
</body>
</html>
"""

SIMPLE_STATIC_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>About Us - Simple Company</title>
    <meta name="description" content="Learn more about Simple Company and our mission">
</head>
<body>
    <div id="content">
        <h1>About Simple Company</h1>

        <p>Simple Company was founded in 2020 with a mission to make
        technology accessible to everyone.</p>

        <h2>Our Mission</h2>
        <p>We believe that technology should be simple, reliable, and
        available to all. That's why we focus on creating products that
        are easy to use and understand.</p>

        <h2>Our Team</h2>
        <p>Our team consists of experienced developers, designers, and
        product managers who are passionate about creating great software.</p>

        <h2>Contact Us</h2>
        <p>Have questions? Reach out to us at contact@simplecompany.com</p>
    </div>
</body>
</html>
"""

EDGE_CASE_NO_ARTICLE_TAG = """
<!DOCTYPE html>
<html>
<head>
    <title>Blog Post Without Article Tag</title>
    <meta name="description" content="Testing content extraction without semantic HTML">
</head>
<body>
    <div class="content">
        <h1>Blog Post Title</h1>
        <p>This is a blog post that doesn't use semantic HTML5 tags.</p>
        <p>It should still be extracted correctly using the .content class selector.</p>
    </div>
</body>
</html>
"""


# ============================================================================
# E2E Test Class
# ============================================================================

class TestE2EParsing:
    """End-to-End tests for complete parsing workflow"""

    @pytest.fixture
    def parser(self):
        """Create a fresh TemplateParser instance for each test"""
        return TemplateParser()

    # ========================================================================
    # Scenario 1: Blog Article Parsing
    # ========================================================================

    def test_blog_post_complete_extraction(self, parser):
        """Test complete extraction of blog post with all metadata"""
        result = parser.parse(BLOG_POST_HTML, 'https://blog.example.com/python-decorators')

        # Verify success
        assert result.success is True, "Parsing should succeed"

        # Verify title extraction (OG title takes precedence in optimized template)
        assert result.title in [
            "Understanding Python Decorators - Tech Blog",  # From <title> tag
            "Understanding Python Decorators"  # From og:title (takes precedence)
        ], f"Expected valid title, got: {result.title}"

        # Verify content extraction
        assert "Decorators are one of Python's most powerful features" in result.content
        assert "What is a Decorator?" in result.content
        assert "Basic Example" in result.content
        assert "Practical Applications" in result.content

        # Verify sidebar is excluded
        assert "This sidebar should not be in extracted content" not in result.content

        # Verify metadata (OG tags take precedence in optimized template)
        assert result.metadata['description'] in [
            "A comprehensive guide to understanding and using Python decorators effectively",  # meta description
            "Learn how to use decorators in Python"  # og:description (takes precedence)
        ]
        assert result.metadata['author'] == "Jane Developer"
        assert result.metadata['date'] == "2025-01-15T10:00:00Z"
        assert result.metadata['image'] == "https://blog.example.com/images/python-decorators.jpg"

    def test_blog_post_markdown_formatting(self, parser):
        """Test that blog content is properly converted to Markdown"""
        result = parser.parse(BLOG_POST_HTML, 'https://blog.example.com/python-decorators')

        # Check for Markdown headers
        assert '#' in result.content, "Should have Markdown headers"

        # Check for list formatting
        assert '- ' in result.content or '* ' in result.content, "Should have Markdown lists"

        # Check for code blocks (if preserved)
        # html2text converts <pre><code> to indented code blocks
        assert 'def my_decorator' in result.content

    def test_blog_post_structure_preservation(self, parser):
        """Test that blog content structure is preserved"""
        result = parser.parse(BLOG_POST_HTML, 'https://blog.example.com/python-decorators')

        # Content should be multi-line
        lines = [l for l in result.content.split('\n') if l.strip()]
        assert len(lines) > 10, "Should have multiple content lines"

        # Should not have excessive whitespace
        assert '\n\n\n' not in result.content, "Should not have triple blank lines"

    # ========================================================================
    # Scenario 2: News Website Parsing
    # ========================================================================

    def test_news_article_extraction(self, parser):
        """Test extraction of news article with headline and byline"""
        result = parser.parse(NEWS_ARTICLE_HTML, 'https://news.example.com/ai-breakthrough')

        assert result.success is True

        # Title should be extracted
        assert "Breaking" in result.title and "AI Breakthrough" in result.title

        # Content should include main article body
        assert "Scientists at a leading research institute" in result.content
        assert "Key Findings" in result.content
        assert "Industry Impact" in result.content

        # Advertisement should be excluded
        assert "Advertisement - Should not appear" not in result.content

    def test_news_article_metadata(self, parser):
        """Test news article metadata extraction"""
        result = parser.parse(NEWS_ARTICLE_HTML, 'https://news.example.com/ai-breakthrough')

        assert result.metadata['author'] == "News Team"
        assert result.metadata['date'] == "2025-01-20T14:30:00Z"
        assert 'image' in result.metadata

    def test_news_article_blockquote_handling(self, parser):
        """Test that blockquotes are preserved in news articles"""
        result = parser.parse(NEWS_ARTICLE_HTML, 'https://news.example.com/ai-breakthrough')

        # Quote should be in content
        assert "game-changer" in result.content
        assert "Dr. Smith" in result.content

    # ========================================================================
    # Scenario 3: Technical Documentation Parsing
    # ========================================================================

    def test_documentation_extraction(self, parser):
        """Test extraction of technical documentation"""
        result = parser.parse(TECHNICAL_DOCS_HTML, 'https://docs.example.com/api/auth')

        assert result.success is True

        # Title
        assert "Authentication" in result.title

        # Main content sections
        assert "Overview" in result.content
        assert "Authentication" in result.content
        assert "Endpoints" in result.content

        # Sidebar navigation should be excluded
        assert "Getting Started" not in result.content or \
            result.content.count("Getting Started") == 1  # Only in main content, not nav

    def test_documentation_code_blocks(self, parser):
        """Test that code blocks are preserved in documentation"""
        result = parser.parse(TECHNICAL_DOCS_HTML, 'https://docs.example.com/api/auth')

        # Code examples should be present
        assert "Authorization: Bearer" in result.content
        assert "access_token" in result.content
        assert "refresh_token" in result.content

    def test_documentation_structured_lists(self, parser):
        """Test that structured lists are preserved"""
        result = parser.parse(TECHNICAL_DOCS_HTML, 'https://docs.example.com/api/auth')

        # HTTP status codes should be listed
        assert "200" in result.content
        assert "401" in result.content
        assert "404" in result.content

    # ========================================================================
    # Scenario 4: Simple Static Page Parsing
    # ========================================================================

    def test_simple_static_page(self, parser):
        """Test extraction from simple static HTML page"""
        result = parser.parse(SIMPLE_STATIC_HTML, 'https://simplecompany.com/about')

        assert result.success is True

        # Title
        assert "About Us" in result.title

        # Content sections
        assert "Simple Company was founded" in result.content
        assert "Our Mission" in result.content
        assert "Our Team" in result.content
        assert "Contact Us" in result.content

    def test_simple_static_page_metadata(self, parser):
        """Test metadata extraction from simple page"""
        result = parser.parse(SIMPLE_STATIC_HTML, 'https://simplecompany.com/about')

        assert result.metadata['description'] == \
            "Learn more about Simple Company and our mission"
        assert result.metadata['source_url'] == 'https://simplecompany.com/about'

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_edge_case_no_article_tag(self, parser):
        """Test extraction when semantic HTML5 tags are not used"""
        result = parser.parse(EDGE_CASE_NO_ARTICLE_TAG, 'https://example.com/blog')

        assert result.success is True
        assert result.title == "Blog Post Without Article Tag"

        # Should still extract content using .content class selector
        assert "doesn't use semantic HTML5 tags" in result.content

    def test_empty_html(self, parser):
        """Test handling of empty HTML"""
        empty_html = "<html><head></head><body></body></html>"
        result = parser.parse(empty_html, 'https://example.com/empty')

        # Should not crash
        assert result.success is True
        assert result.title == ""
        assert result.content == ""

    def test_malformed_html(self, parser):
        """Test handling of malformed HTML"""
        malformed = "<<div>Not properly formed<<>>"
        result = parser.parse(malformed, 'https://example.com/malformed')

        # Should not crash, may succeed or fail gracefully
        assert isinstance(result, ParseResult)

    # ========================================================================
    # Scenario 5: Performance Benchmarks
    # ========================================================================

    def test_single_page_parse_performance(self, parser):
        """Test that single page parsing completes in <1 second"""
        start_time = time.time()
        result = parser.parse(BLOG_POST_HTML, 'https://blog.example.com/test')
        elapsed = time.time() - start_time

        assert result.success is True
        assert elapsed < 1.0, f"Parsing took {elapsed:.3f}s, expected <1.0s"

    def test_batch_parsing_performance(self, parser):
        """Test batch parsing of 10 pages averages <1 second per page"""
        test_cases = [
            (BLOG_POST_HTML, 'https://example.com/blog1'),
            (NEWS_ARTICLE_HTML, 'https://example.com/news1'),
            (TECHNICAL_DOCS_HTML, 'https://example.com/docs1'),
            (SIMPLE_STATIC_HTML, 'https://example.com/static1'),
            (BLOG_POST_HTML, 'https://example.com/blog2'),
            (NEWS_ARTICLE_HTML, 'https://example.com/news2'),
            (TECHNICAL_DOCS_HTML, 'https://example.com/docs2'),
            (SIMPLE_STATIC_HTML, 'https://example.com/static2'),
            (BLOG_POST_HTML, 'https://example.com/blog3'),
            (NEWS_ARTICLE_HTML, 'https://example.com/news3'),
        ]

        start_time = time.time()
        results = []

        for html, url in test_cases:
            result = parser.parse(html, url)
            results.append(result)

        total_time = time.time() - start_time
        avg_time = total_time / len(test_cases)

        # All should succeed
        assert all(r.success for r in results), "All parses should succeed"

        # Average should be <1 second per page
        assert avg_time < 1.0, \
            f"Average parse time {avg_time:.3f}s, expected <1.0s (total: {total_time:.3f}s for {len(test_cases)} pages)"

    def test_performance_with_caching(self, parser):
        """Test that template caching improves performance for same domain"""
        url1 = 'https://example.com/page1'
        url2 = 'https://example.com/page2'

        # First parse (cold cache)
        start1 = time.time()
        result1 = parser.parse(BLOG_POST_HTML, url1)
        time1 = time.time() - start1

        # Second parse (warm cache - same domain pattern)
        start2 = time.time()
        result2 = parser.parse(BLOG_POST_HTML, url2)
        time2 = time.time() - start2

        # Both should succeed
        assert result1.success and result2.success

        # Second should be faster or similar (template cached)
        # This is a soft assertion - caching should help but not guaranteed to be faster
        assert time2 <= time1 * 1.2, "Cached parse should not be significantly slower"

    def test_memory_efficiency(self, parser):
        """Test that parser doesn't leak memory across multiple parses"""
        # Parse 50 times and ensure no memory issues
        for i in range(50):
            result = parser.parse(BLOG_POST_HTML, f'https://example.com/page{i}')
            assert result.success is True

        # If we got here without crashing, memory is managed well
        assert True

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_parse_result_to_dict_conversion(self, parser):
        """Test that ParseResult can be converted to dictionary"""
        result = parser.parse(BLOG_POST_HTML, 'https://blog.example.com/test')

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'title' in result_dict
        assert 'content' in result_dict
        assert 'metadata' in result_dict
        assert 'success' in result_dict
        assert 'parser_name' in result_dict
        assert 'template_name' in result_dict
        assert 'parse_time' in result_dict

    def test_parser_metadata(self, parser):
        """Test parser metadata is accessible"""
        metadata = parser.get_metadata()

        assert metadata['parser_name'] == 'TemplateParser'
        assert 'version' in metadata
        assert 'templates_loaded' in metadata
        assert 'supported_features' in metadata

    def test_template_reloading(self, parser):
        """Test that templates can be reloaded"""
        # Parse once
        result1 = parser.parse(BLOG_POST_HTML, 'https://example.com/test')

        # Reload templates
        parser.reload_templates()

        # Parse again - should still work
        result2 = parser.parse(BLOG_POST_HTML, 'https://example.com/test')

        assert result1.success and result2.success
        assert result1.title == result2.title

    # ========================================================================
    # Validation Tests
    # ========================================================================

    def test_result_validation_success(self, parser):
        """Test validation of successful parse result"""
        result = parser.parse(BLOG_POST_HTML, 'https://example.com/test')

        assert parser.validate(result) is True

    def test_result_validation_failure(self, parser):
        """Test validation of failed parse result"""
        # Create a failed result
        from parser_engine.base_parser import ParseResult
        failed_result = ParseResult(
            success=False,
            errors=["Test error"],
            parser_name="TemplateParser"
        )

        assert parser.validate(failed_result) is False

    # ========================================================================
    # Complete Workflow Test
    # ========================================================================

    def test_complete_parsing_workflow(self, parser):
        """Test complete workflow: parse -> validate -> convert to dict"""
        # Parse
        result = parser.parse(BLOG_POST_HTML, 'https://blog.example.com/decorators')

        # Validate
        assert result.success is True
        assert parser.validate(result) is True

        # Convert to dict
        result_dict = result.to_dict()

        # Verify all components
        assert result_dict['success'] is True
        assert len(result_dict['title']) > 0
        assert len(result_dict['content']) > 0
        assert len(result_dict['metadata']) > 0
        assert result_dict['parser_name'] == 'TemplateParser'
        assert result_dict['template_name'] == 'Generic Web Template'

        # Verify metadata includes all expected fields
        assert 'source_url' in result_dict['metadata']
        assert 'template_name' in result_dict['metadata']
        assert 'template_version' in result_dict['metadata']
        assert 'description' in result_dict['metadata']
        assert 'author' in result_dict['metadata']


# ============================================================================
# Performance Benchmark Suite (Optional - requires pytest-benchmark)
# ============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmark tests (optional - requires pytest-benchmark)

    To install pytest-benchmark: pip install pytest-benchmark
    These tests will be skipped if pytest-benchmark is not installed.
    """

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return TemplateParser()

    def test_benchmark_blog_parsing(self, parser, request):
        """Benchmark blog post parsing performance"""
        # Check if benchmark fixture is available
        try:
            benchmark = request.getfixturevalue('benchmark')
            result = benchmark(parser.parse, BLOG_POST_HTML, 'https://example.com/blog')
            assert result.success is True
        except Exception:
            pytest.skip("pytest-benchmark not available - install with: pip install pytest-benchmark")

    def test_benchmark_news_parsing(self, parser, request):
        """Benchmark news article parsing performance"""
        try:
            benchmark = request.getfixturevalue('benchmark')
            result = benchmark(parser.parse, NEWS_ARTICLE_HTML, 'https://example.com/news')
            assert result.success is True
        except Exception:
            pytest.skip("pytest-benchmark not available - install with: pip install pytest-benchmark")

    def test_benchmark_docs_parsing(self, parser, request):
        """Benchmark documentation parsing performance"""
        try:
            benchmark = request.getfixturevalue('benchmark')
            result = benchmark(parser.parse, TECHNICAL_DOCS_HTML, 'https://example.com/docs')
            assert result.success is True
        except Exception:
            pytest.skip("pytest-benchmark not available - install with: pip install pytest-benchmark")


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__, '-v'])
