"""Real-world example demonstrating TemplateParser functionality.

This test shows the complete workflow of parsing a real-world HTML page
using the TemplateParser with the generic template.
"""

from parser_engine.template_parser import TemplateParser


def test_parse_real_world_html():
    """Test parsing a realistic blog post HTML"""

    # Realistic blog post HTML
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Understanding Python Decorators - Tech Blog</title>
        <meta name="description" content="A comprehensive guide to Python decorators and how to use them effectively">
        <meta name="author" content="Jane Developer">
        <meta property="article:published_time" content="2025-01-15T10:30:00Z">
        <meta property="og:title" content="Understanding Python Decorators">
        <meta property="og:description" content="Deep dive into Python decorators">
        <meta property="og:image" content="https://example.com/images/decorators.jpg">
    </head>
    <body>
        <header>
            <nav>Site Navigation</nav>
        </header>

        <main role="main">
            <article class="blog-post">
                <h1>Understanding Python Decorators</h1>

                <p class="intro">
                    Decorators are one of Python's most powerful features,
                    allowing you to modify or enhance functions and classes.
                </p>

                <h2>What are Decorators?</h2>
                <p>
                    A decorator is a function that takes another function as
                    input and extends its behavior without modifying it.
                </p>

                <h3>Basic Example</h3>
                <pre><code>
                def my_decorator(func):
                    def wrapper():
                        print("Before")
                        func()
                        print("After")
                    return wrapper
                </code></pre>

                <h2>Common Use Cases</h2>
                <ul>
                    <li>Logging function calls</li>
                    <li>Measuring execution time</li>
                    <li>Access control and authentication</li>
                    <li>Caching results</li>
                </ul>

                <p>
                    For more information, check out the
                    <a href="https://docs.python.org/decorators">official documentation</a>.
                </p>
            </article>
        </main>

        <aside class="sidebar">
            <h3>Related Posts</h3>
            <p>This sidebar content should not appear in extraction</p>
        </aside>

        <footer>
            <p>Copyright 2025</p>
        </footer>
    </body>
    </html>
    """

    # Create parser and parse
    parser = TemplateParser()
    result = parser.parse(html, 'https://techblog.example.com/python-decorators')

    # Verify success
    assert result.success is True
    print(f"\n✓ Parse successful: {result.success}")

    # Verify title extraction
    assert result.title == "Understanding Python Decorators"
    print(f"✓ Title: {result.title}")

    # Verify content extraction (should be in Markdown)
    assert result.content is not None
    assert len(result.content) > 100
    assert "Decorators" in result.content
    assert "What are Decorators?" in result.content
    assert "Common Use Cases" in result.content
    # Sidebar should NOT be included
    assert "sidebar content" not in result.content.lower()
    print(f"✓ Content length: {len(result.content)} characters")
    print(f"✓ Content is Markdown: {('#' in result.content or '*' in result.content)}")

    # Verify metadata extraction
    assert result.metadata is not None
    assert result.metadata['description'] == "Deep dive into Python decorators"
    assert result.metadata['author'] == "Jane Developer"
    assert result.metadata['date'] == "2025-01-15T10:30:00Z"
    assert result.metadata['image'] == "https://example.com/images/decorators.jpg"
    print(f"✓ Description: {result.metadata['description'][:50]}...")
    print(f"✓ Author: {result.metadata['author']}")
    print(f"✓ Date: {result.metadata['date']}")
    print(f"✓ Image: {result.metadata['image']}")

    # Verify template info
    assert result.template_name == "Generic Web Template"
    assert result.metadata['template_name'] == "Generic Web Template"
    assert result.metadata['template_version'] == "1.1.0"
    print(f"✓ Template: {result.template_name} v{result.metadata['template_version']}")

    # Print sample of Markdown content
    print("\n--- Sample Markdown Content ---")
    content_lines = result.content.split('\n')[:15]
    for line in content_lines:
        print(line)
    print("...")

    print("\n✅ All assertions passed! TemplateParser successfully extracted structured content.")


if __name__ == '__main__':
    test_parse_real_world_html()
