#!/usr/bin/env python3
"""
Parser Template CLI Tool / 解析模板CLI工具

Provides commands for creating, validating, and managing parser templates.
提供创建、验证和管理解析模板的命令。

This tool helps developers:
- Initialize new parser templates with proper structure
- Validate templates against schema
- Preview extraction results before deployment
- Generate documentation from templates

此工具帮助开发者:
- 使用正确结构初始化新的解析模板
- 根据schema验证模板
- 在部署前预览提取结果
- 从模板生成文档
"""

import argparse
import sys
from typing import Optional
from pathlib import Path


def cmd_init(args) -> int:
    """
    Initialize a new parser template / 初始化新的解析模板

    Creates a new template file with the basic structure based on the domain
    and type specified. The template will be created in the appropriate
    directory under parser_engine/templates/sites/.

    根据指定的域名和类型创建具有基本结构的新模板文件。
    模板将在parser_engine/templates/sites/下的相应目录中创建。

    Args:
        args: Parsed command-line arguments containing:
            - domain: Target domain name (e.g., example.com)
            - type: Template type (article, list, or generic)
            - output: Optional output path

    Returns:
        int: 0 on success, 1 on failure
    """
    print(f"Initializing template for domain: {args.domain}")
    print(f"Template type: {args.type}")
    if hasattr(args, 'output') and args.output:
        print(f"Output path: {args.output}")
    print("\n✗ Not implemented yet / 尚未实现")
    return 1


def cmd_validate(args) -> int:
    """
    Validate a parser template / 验证解析模板

    Validates a template file against the schema definition to ensure:
    - All required fields are present
    - Field types are correct
    - Selectors are properly formatted
    - No conflicting configurations

    根据schema定义验证模板文件以确保:
    - 所有必需字段都存在
    - 字段类型正确
    - 选择器格式正确
    - 没有冲突的配置

    Args:
        args: Parsed command-line arguments containing:
            - template: Path to template file to validate
            - strict: Enable strict validation mode

    Returns:
        int: 0 if valid, 1 if invalid or error
    """
    print(f"Validating template: {args.template}")
    if hasattr(args, 'strict') and args.strict:
        print("Strict mode: enabled")
    print("\n✗ Not implemented yet / 尚未实现")
    return 1


def cmd_preview(args) -> int:
    """
    Preview template extraction results / 预览模板提取结果

    Tests a template against a sample HTML file or URL to preview what
    content would be extracted. This helps verify the template works
    correctly before deploying it to production.

    对示例HTML文件或URL测试模板以预览将提取的内容。
    这有助于在部署到生产环境之前验证模板是否正常工作。

    Args:
        args: Parsed command-line arguments containing:
            - template: Path to template file
            - html: Path to HTML file OR
            - url: URL to fetch and preview
            - output: Optional output format (json, yaml, text)

    Returns:
        int: 0 on success, 1 on failure
    """
    print(f"Preview mode for template: {args.template}")
    if hasattr(args, 'html') and args.html:
        print(f"HTML file: {args.html}")
    elif hasattr(args, 'url') and args.url:
        print(f"URL: {args.url}")
    if hasattr(args, 'output') and args.output:
        print(f"Output format: {args.output}")
    print("\n✗ Not implemented yet / 尚未实现")
    return 1


def cmd_doc(args) -> int:
    """
    Generate documentation from template / 从模板生成文档

    Generates human-readable documentation from a template file,
    including:
    - Template metadata (name, version, domains)
    - Selector documentation
    - Usage examples
    - Field descriptions

    从模板文件生成人类可读的文档,包括:
    - 模板元数据(名称、版本、域名)
    - 选择器文档
    - 使用示例
    - 字段描述

    Args:
        args: Parsed command-line arguments containing:
            - template: Path to template file
            - output: Output directory for generated docs
            - format: Documentation format (markdown, html)

    Returns:
        int: 0 on success, 1 on failure
    """
    print(f"Generating documentation for: {args.template}")
    if hasattr(args, 'output') and args.output:
        print(f"Output directory: {args.output}")
    if hasattr(args, 'format') and args.format:
        print(f"Format: {args.format}")
    print("\n✗ Not implemented yet / 尚未实现")
    return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser / 创建并配置参数解析器

    Returns:
        argparse.ArgumentParser: Configured parser with all subcommands
    """
    parser = argparse.ArgumentParser(
        prog='template_tool',
        description='Parser Template CLI Tool / 解析模板CLI工具\n\n'
                   'Manage parser templates for the Web_Fetcher project.\n'
                   '管理Web_Fetcher项目的解析模板。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples / 示例:
  # Initialize a new article template for a domain
  # 为域名初始化新的文章模板
  %(prog)s init --domain example.com --type article

  # Validate an existing template
  # 验证现有模板
  %(prog)s validate templates/sites/example/template.yaml

  # Preview extraction with a local HTML file
  # 使用本地HTML文件预览提取
  %(prog)s preview --html sample.html --template template.yaml

  # Preview extraction from a URL
  # 从URL预览提取
  %(prog)s preview --url https://example.com/article --template template.yaml

  # Generate documentation
  # 生成文档
  %(prog)s doc --template template.yaml --output docs/ --format markdown

For more information, see the project documentation.
更多信息请参见项目文档。
        '''
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands / 可用命令',
        required=False
    )

    # ==================== INIT Command ====================
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize new template / 初始化新模板',
        description='Create a new parser template with the basic structure.\n'
                   '创建具有基本结构的新解析模板。'
    )
    init_parser.add_argument(
        '--domain',
        required=True,
        help='Target domain name (e.g., example.com) / 目标域名'
    )
    init_parser.add_argument(
        '--type',
        choices=['article', 'list', 'generic'],
        default='article',
        help='Template type (default: article) / 模板类型(默认:article)'
    )
    init_parser.add_argument(
        '--output',
        '-o',
        help='Output path for template file / 模板文件输出路径'
    )
    init_parser.set_defaults(func=cmd_init)

    # ==================== VALIDATE Command ====================
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate template / 验证模板',
        description='Validate a template file against the schema.\n'
                   '根据schema验证模板文件。'
    )
    validate_parser.add_argument(
        'template',
        help='Path to template file / 模板文件路径'
    )
    validate_parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict validation mode / 启用严格验证模式'
    )
    validate_parser.set_defaults(func=cmd_validate)

    # ==================== PREVIEW Command ====================
    preview_parser = subparsers.add_parser(
        'preview',
        help='Preview extraction / 预览提取',
        description='Preview template extraction results on sample content.\n'
                   '在示例内容上预览模板提取结果。'
    )
    preview_parser.add_argument(
        '--template',
        required=True,
        help='Path to template file / 模板文件路径'
    )

    # Input source: either HTML file or URL
    input_group = preview_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--html',
        help='Path to HTML file / HTML文件路径'
    )
    input_group.add_argument(
        '--url',
        help='URL to fetch and preview / 要获取和预览的URL'
    )

    preview_parser.add_argument(
        '--output',
        '-o',
        choices=['json', 'yaml', 'text'],
        default='text',
        help='Output format (default: text) / 输出格式(默认:text)'
    )
    preview_parser.set_defaults(func=cmd_preview)

    # ==================== DOC Command ====================
    doc_parser = subparsers.add_parser(
        'doc',
        help='Generate documentation / 生成文档',
        description='Generate documentation from a template file.\n'
                   '从模板文件生成文档。'
    )
    doc_parser.add_argument(
        '--template',
        required=True,
        help='Path to template file / 模板文件路径'
    )
    doc_parser.add_argument(
        '--output',
        '-o',
        help='Output directory for docs (default: stdout) / 文档输出目录(默认:stdout)'
    )
    doc_parser.add_argument(
        '--format',
        '-f',
        choices=['markdown', 'html'],
        default='markdown',
        help='Documentation format (default: markdown) / 文档格式(默认:markdown)'
    )
    doc_parser.set_defaults(func=cmd_doc)

    return parser


def main() -> int:
    """
    Main entry point for the CLI tool / CLI工具的主入口

    Parses command-line arguments and dispatches to the appropriate
    subcommand handler.

    解析命令行参数并分派到相应的子命令处理程序。

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args()

    # If no command specified, show help
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    # Execute the command
    try:
        return args.func(args)
    except Exception as e:
        print(f"\n✗ Error / 错误: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
