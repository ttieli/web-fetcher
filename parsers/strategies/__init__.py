"""Extraction strategies for content parsing.

This package provides different strategies for extracting content from HTML:
- CSS selectors (CSSStrategy)
- XPath expressions (XPathStrategy)
- Regular expression patterns (TextPatternStrategy)
"""

from .base_strategy import (
    ExtractionStrategy,
    StrategyError,
    SelectionError,
    ExtractionError
)
from .css_strategy import CSSStrategy
from .xpath_strategy import XPathStrategy
from .text_pattern_strategy import TextPatternStrategy

__all__ = [
    'ExtractionStrategy',
    'StrategyError',
    'SelectionError',
    'ExtractionError',
    'CSSStrategy',
    'XPathStrategy',
    'TextPatternStrategy',
]
