"""Unified error handling framework."""
from .handler import (
    ChromeDebugError, ChromePortConflictError,
    ChromePermissionError, ChromeTimeoutError,
    ChromeLaunchError, ChromeErrorMessages
)
from .classifier import UnifiedErrorClassifier
from .types import ErrorType, ErrorClassification
from .cache import ErrorCache

__all__ = [
    'ChromeDebugError', 'ChromePortConflictError',
    'ChromePermissionError', 'ChromeTimeoutError',
    'ChromeLaunchError', 'ChromeErrorMessages',
    'UnifiedErrorClassifier',
    'ErrorType', 'ErrorClassification',
    'ErrorCache'
]
