#!/usr/bin/env python3
"""
Error Type Definitions and Classification Data Structures
错误类型定义和分类数据结构
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ErrorType(Enum):
    """Core error type classifications / 核心错误类型分类"""
    PERMANENT = "permanent"              # Never retry
    TEMPORARY = "temporary"              # Retry immediately
    RATE_LIMIT = "rate_limit"           # Retry with long backoff
    RETRY_WITH_BACKOFF = "backoff"      # Retry with exponential backoff
    SSL_CONFIG = "ssl_config"           # SSL issues (use Selenium)
    UNKNOWN = "unknown"                 # Conservative retry

@dataclass
class ErrorClassification:
    """Complete error classification result / 完整的错误分类结果"""
    error_type: ErrorType
    should_retry: bool
    recommended_wait: float
    max_retries: int
    fallback_method: Optional[str]
    reason: str
    confidence: float
    cache_duration: Optional[int] = None
