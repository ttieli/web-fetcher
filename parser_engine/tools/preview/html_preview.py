#!/usr/bin/env python3
"""
HTML Preview Tool / HTML预览工具

Previews what content would be extracted from HTML using a template.
预览使用模板从HTML中提取的内容。
"""

from typing import Dict, Any, Optional
import yaml
import json
from pathlib import Path


class HTMLPreviewer:
    """Preview template extraction / 预览模板提取"""

    def __init__(self, template_path: str):
        """
        Initialize previewer with template / 用模板初始化预览器

        Args:
            template_path: Path to template YAML file

        Raises:
            FileNotFoundError: If template file doesn't exist
            yaml.YAMLError: If template YAML is invalid
        """
        template_file = Path(template_path)
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

        self.template_path = template_path

    def preview_from_file(self, html_path: str, output_format: str = 'text') -> str:
        """
        Preview extraction from HTML file / 从HTML文件预览提取

        Args:
            html_path: Path to HTML file
            output_format: Output format ('text', 'json', 'yaml')

        Returns:
            Formatted preview output

        Raises:
            FileNotFoundError: If HTML file doesn't exist
        """
        html_file = Path(html_path)
        if not html_file.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        return self.preview_from_html(html, output_format)

    def preview_from_html(self, html: str, output_format: str = 'text') -> str:
        """
        Preview extraction from HTML string / 从HTML字符串预览提取

        Args:
            html: HTML content
            output_format: Output format ('text', 'json', 'yaml')

        Returns:
            Formatted preview output

        Raises:
            ImportError: If TemplateParser is not available
            Exception: If extraction fails
        """
        # Import TemplateParser
        try:
            from ...template_parser import TemplateParser
        except ImportError as e:
            raise ImportError(f"Failed to import TemplateParser: {e}")

        # Create a custom TemplateParser that uses our specific template
        # We'll pass None for template_dir and override the template directly
        parser = TemplateParser(template_dir=None)
        parser.current_template = self.template

        # Parse the HTML
        result = parser.parse(html, url="preview://local")

        # Convert ParseResult to dictionary
        result_dict = {
            'title': result.title,
            'content': result.content,
            'metadata': result.metadata,
            'success': result.success,
            'errors': result.errors,
            'parser_name': result.parser_name,
            'template_name': result.template_name
        }

        # Format output based on requested format
        if output_format == 'json':
            return json.dumps(result_dict, indent=2, ensure_ascii=False)
        elif output_format == 'yaml':
            return yaml.dump(result_dict, allow_unicode=True, default_flow_style=False)
        else:  # text
            return self._format_text(result_dict)

    def _format_text(self, result: Dict[str, Any]) -> str:
        """
        Format result as readable text / 将结果格式化为可读文本

        Args:
            result: Extraction result dictionary

        Returns:
            Formatted text output
        """
        lines = []
        lines.append("=" * 60)
        lines.append("EXTRACTION PREVIEW / 提取预览")
        lines.append("=" * 60)
        lines.append(f"\nTemplate: {Path(self.template_path).name}")
        lines.append(f"Template Name: {self.template.get('name', 'Unknown')}")
        lines.append(f"Template Version: {self.template.get('version', 'Unknown')}")
        lines.append(f"Parser: {result.get('parser_name', 'Unknown')}")
        lines.append(f"Success: {'Yes' if result.get('success') else 'No'}")

        # Display errors if any
        if result.get('errors'):
            lines.append("\n" + "-" * 60)
            lines.append("ERRORS / 错误")
            lines.append("-" * 60)
            for error in result['errors']:
                lines.append(f"  - {error}")

        lines.append("\n" + "-" * 60)
        lines.append("EXTRACTED FIELDS / 提取的字段")
        lines.append("-" * 60)

        # Display key fields
        for key, value in result.items():
            if key in ['metadata', 'success', 'errors', 'parser_name', 'template_name']:
                continue  # Skip these for main display

            if value is None or value == '':
                lines.append(f"\n{key.upper()}: [Not extracted / 未提取]")
            elif isinstance(value, list):
                if len(value) == 0:
                    lines.append(f"\n{key.upper()}: [Empty list / 空列表]")
                else:
                    lines.append(f"\n{key.upper()}:")
                    for i, item in enumerate(value, 1):
                        item_str = str(item)
                        if len(item_str) > 100:
                            item_str = item_str[:100] + "..."
                        lines.append(f"  {i}. {item_str}")
            else:
                value_str = str(value)
                if len(value_str) > 500:
                    preview_str = value_str[:500] + f"\n  ... (truncated, total length: {len(value_str)} chars)"
                    lines.append(f"\n{key.upper()}:")
                    lines.append(f"  {preview_str}")
                else:
                    lines.append(f"\n{key.upper()}:")
                    # Split long content into lines for better readability
                    if len(value_str) > 100:
                        lines.append(f"  {value_str}")
                    else:
                        lines.append(f"  {value_str}")

        # Display metadata if present
        if result.get('metadata'):
            lines.append("\n" + "-" * 60)
            lines.append("METADATA / 元数据")
            lines.append("-" * 60)
            if isinstance(result['metadata'], dict):
                for key, value in result['metadata'].items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append(f"  {result['metadata']}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
