"""Web content parsing with template support."""
from .parser import (
    xhs_to_markdown,
    wechat_to_markdown,
    generic_to_markdown
)

__all__ = [
    'xhs_to_markdown',
    'wechat_to_markdown',
    'generic_to_markdown'
]
