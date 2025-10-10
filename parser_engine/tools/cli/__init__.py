"""
CLI Package Initialization / CLI包初始化

This module provides shared resources for the CLI tools, including:
- Schema loading from templates/schema.yaml
- Common constants and utilities
- Shared configuration

此模块为CLI工具提供共享资源,包括:
- 从templates/schema.yaml加载Schema
- 公共常量和实用程序
- 共享配置
"""

from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import sys


def load_schema() -> Optional[Dict[str, Any]]:
    """
    Load the parser template schema from templates/schema.yaml
    从templates/schema.yaml加载解析模板schema

    The schema defines the structure and validation rules for parser templates.
    It includes required fields, field types, and documentation.

    Schema定义了解析模板的结构和验证规则。
    它包括必需字段、字段类型和文档。

    Returns:
        Optional[Dict[str, Any]]: Schema dictionary if found, None otherwise

    Raises:
        No exceptions - returns None if schema file is not found or cannot be parsed
    """
    try:
        # Navigate from parser_engine/tools/cli/ to parser_engine/templates/schema.yaml
        # Path structure: cli/ -> tools/ -> parser_engine/ -> templates/schema.yaml
        schema_path = Path(__file__).resolve().parent.parent.parent / 'templates' / 'schema.yaml'

        if not schema_path.exists():
            print(f"Warning: Schema file not found at {schema_path}", file=sys.stderr)
            return None

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        return schema

    except Exception as e:
        print(f"Warning: Failed to load schema: {e}", file=sys.stderr)
        return None


def get_schema_version() -> str:
    """
    Get the current schema version / 获取当前schema版本

    Returns:
        str: Schema version string, or "unknown" if not available
    """
    schema = load_schema()
    if schema and 'version' in schema:
        return schema['version']
    return "unknown"


def get_required_fields() -> list:
    """
    Get list of required fields from schema / 从schema获取必需字段列表

    Returns:
        list: List of required field names, or empty list if schema not available
    """
    schema = load_schema()
    if schema and 'required_fields' in schema:
        return schema['required_fields']
    return []


# Shared constants / 共享常量
SCHEMA = load_schema()
SCHEMA_VERSION = get_schema_version()
REQUIRED_FIELDS = get_required_fields()

# Template type constants / 模板类型常量
TEMPLATE_TYPES = ['article', 'list', 'generic']

# Output format constants / 输出格式常量
OUTPUT_FORMATS = ['json', 'yaml', 'text']
DOC_FORMATS = ['markdown', 'html']

# Default paths / 默认路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / 'parser_engine' / 'templates'
SITES_DIR = TEMPLATES_DIR / 'sites'


__all__ = [
    'load_schema',
    'get_schema_version',
    'get_required_fields',
    'SCHEMA',
    'SCHEMA_VERSION',
    'REQUIRED_FIELDS',
    'TEMPLATE_TYPES',
    'OUTPUT_FORMATS',
    'DOC_FORMATS',
    'PROJECT_ROOT',
    'TEMPLATES_DIR',
    'SITES_DIR',
]
