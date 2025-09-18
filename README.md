# Web_Fetcher

A powerful and intelligent web content extraction tool with multi-mode crawling capabilities and smart URL parsing.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Web_Fetcher.git
cd Web_Fetcher

# Install dependencies
pip install -r requirements.txt

# Make the script executable (optional)
chmod +x wf.py
```

## Quick Start

```bash
# Basic usage - extract content from a URL
wf https://example.com

# Extract URL from mixed text (Chinese/English)
wf "Check this article 看这篇文章 http://example.com/article"

# Fast mode - quick content extraction
wf fast https://example.com

# Full mode - comprehensive extraction
wf full https://example.com

# Site mode - crawl entire website
wf site https://example.com

# Raw mode - get original HTML
wf raw https://example.com
```

## Features

### 🎯 Smart URL Extraction
Automatically extracts URLs from mixed language text, supporting various platforms including WeChat articles and Xiaohongshu posts.

### 🚀 Multiple Crawling Modes
- **Single Page**: Default mode for single page content
- **Fast Mode**: Quick extraction with minimal processing
- **Full Mode**: Comprehensive content extraction
- **Site Mode**: Complete website crawling
- **Raw Mode**: Original HTML without processing

### 🌐 Platform Support
- WeChat Articles (with JavaScript filtering)
- Xiaohongshu (with image extraction)
- Hugo/Jekyll static sites
- General web pages

### 📸 Image Handling
```bash
# Default - show image URLs only
wf https://example.com

# Download images
wf https://example.com --download-assets

# Legacy compatibility mode
WF_LEGACY_IMAGE_MODE=1 wf https://example.com
```

### 📁 Output Control
```bash
# Custom output directory
wf https://example.com -o ./my-output

# Verbose logging
wf https://example.com --verbose

# Raw HTML output
wf https://example.com --raw
```

## Common Use Cases

### Extract WeChat Article
```bash
wf "https://mp.weixin.qq.com/s/article-id"
```

### Crawl Documentation Site
```bash
wf site https://docs.example.com -o ./docs-backup
```

### Quick Content Check
```bash
wf fast https://news.example.com/latest
```

### Download Article with Images
```bash
wf https://blog.example.com/post --download-assets
```

## Advanced Usage

### Environment Variables
```bash
# Enable legacy image mode
export WF_LEGACY_IMAGE_MODE=1

# Set default output directory
export WF_OUTPUT_DIR=/path/to/output
```

### Batch Processing
```bash
# Process multiple URLs from a file
while IFS= read -r url; do
    wf "$url" -o ./batch-output
done < urls.txt
```

## Requirements

- Python 3.7+
- BeautifulSoup4
- Requests
- Other dependencies listed in requirements.txt

## Error Handling

The tool includes:
- Automatic retry mechanism for failed requests
- Intelligent content extraction fallbacks
- Comprehensive error logging with `--verbose` flag

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.