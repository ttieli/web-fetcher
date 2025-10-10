#!/usr/bin/env python3
"""
Template Tool - Executable Entry Point / 模板工具 - 可执行入口

This script provides a convenient entry point for the parser template CLI tool.
It ensures the project root is in the Python path and delegates to the main CLI module.

此脚本为解析模板CLI工具提供方便的入口点。
它确保项目根目录在Python路径中并委托给主CLI模块。

Usage / 用法:
    ./scripts/template_tool.py --help
    python scripts/template_tool.py init --domain example.com --type article
    python scripts/template_tool.py validate templates/sites/example/template.yaml

For detailed usage information, run with --help flag.
有关详细使用信息,请使用--help标志运行。
"""

import sys
from pathlib import Path

# Add project root to Python path
# This allows importing from parser_engine regardless of where the script is run from
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import and run the main CLI
from parser_engine.tools.cli.template_cli import main

if __name__ == '__main__':
    sys.exit(main())
