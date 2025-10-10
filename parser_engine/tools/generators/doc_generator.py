#!/usr/bin/env python3
"""
Documentation Generator / 文档生成器

Automatically generates documentation for parser templates.
自动为解析器模板生成文档。
"""

from typing import Dict, Any, List
import yaml
from pathlib import Path
from datetime import datetime


class DocGenerator:
    """Generates template documentation / 生成模板文档"""

    def __init__(self, template_path: str):
        """
        Initialize with template / 用模板初始化

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

        self.template_path = Path(template_path)

    def generate_markdown(self) -> str:
        """
        Generate Markdown documentation / 生成Markdown文档

        Returns:
            Markdown-formatted documentation
        """
        lines = []

        # Header
        template_name = self.template.get('name', 'Unnamed Template')
        lines.append(f"# {template_name}")
        lines.append("")
        lines.append(f"**Version:** {self.template.get('version', '1.0.0')}")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Template File:** `{self.template_path.name}`")
        lines.append("")

        # Description (if available in metadata)
        metadata = self.template.get('metadata', {})
        if 'description' in metadata:
            lines.append("## Description / 描述")
            lines.append("")
            lines.append(metadata['description'])
            lines.append("")

        # Domains
        lines.append("## Supported Domains / 支持的域名")
        lines.append("")
        domains = self.template.get('domains', [])
        if domains:
            for domain in domains:
                lines.append(f"- `{domain}`")
        else:
            lines.append("- [No domains specified / 未指定域名]")
        lines.append("")

        # Template Type
        template_type = self.template.get('type', 'unknown')
        lines.append("## Template Type / 模板类型")
        lines.append("")
        lines.append(f"**Type:** `{template_type}`")
        lines.append("")

        # Selectors
        selectors = self.template.get('selectors', {})
        if selectors:
            lines.append("## Selectors / 选择器")
            lines.append("")
            lines.append("This template defines the following extraction selectors:")
            lines.append("")

            for field, selector_list in selectors.items():
                lines.append(f"### {field.replace('_', ' ').title()}")
                lines.append("")

                if isinstance(selector_list, list) and selector_list:
                    lines.append("| Priority | Selector | Strategy | Attribute | Transform |")
                    lines.append("|----------|----------|----------|-----------|-----------|")

                    for i, sel in enumerate(selector_list, 1):
                        selector = sel.get('selector', 'N/A')
                        strategy = sel.get('strategy', 'css')
                        attribute = sel.get('attribute', 'text')
                        transform = sel.get('transform', '-')

                        # Escape pipe characters in selector
                        selector = selector.replace('|', '\\|')

                        lines.append(f"| {i} | `{selector}` | {strategy} | {attribute} | {transform} |")
                else:
                    lines.append("*No selectors defined / 未定义选择器*")

                lines.append("")

        # Transformations
        transformations = self.template.get('transformations', {})
        if transformations:
            lines.append("## Transformations / 转换规则")
            lines.append("")
            lines.append("| Field | Transformations |")
            lines.append("|-------|-----------------|")

            for field, transforms in transformations.items():
                if isinstance(transforms, list):
                    transform_str = ", ".join([f"`{t}`" for t in transforms])
                else:
                    transform_str = f"`{transforms}`"
                lines.append(f"| {field} | {transform_str} |")

            lines.append("")

        # Test Cases
        test_cases = self.template.get('test_cases', [])
        if test_cases:
            lines.append("## Test Cases / 测试用例")
            lines.append("")
            lines.append("The following test cases are defined for this template:")
            lines.append("")

            for i, test in enumerate(test_cases, 1):
                lines.append(f"### Test Case {i}")
                lines.append("")
                lines.append(f"**URL:** {test.get('url', 'N/A')}")
                lines.append("")

                # Display expected values if present
                expected = test.get('expected', {})
                if expected:
                    lines.append("**Expected Values:**")
                    lines.append("")
                    for key, value in expected.items():
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        lines.append(f"- **{key}:** {value_str}")
                    lines.append("")

        # Additional Metadata
        if metadata:
            lines.append("## Metadata / 元数据")
            lines.append("")

            for key, value in metadata.items():
                if key == 'description':
                    continue  # Already shown above

                lines.append(f"- **{key}:** {value}")

            lines.append("")

        # Usage Example
        lines.append("## Usage Example / 使用示例")
        lines.append("")
        lines.append("```python")
        lines.append("from parser_engine.template_parser import TemplateParser")
        lines.append("")
        lines.append("# Initialize parser")
        lines.append("parser = TemplateParser()")
        lines.append("")
        lines.append("# Parse HTML content")
        lines.append("result = parser.parse(html_content, url)")
        lines.append("")
        lines.append("# Access extracted data")
        lines.append("print(result.title)")
        lines.append("print(result.content)")
        lines.append("print(result.author)")
        lines.append("```")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Documentation auto-generated from `{self.template_path}`*")
        lines.append("")

        return "\n".join(lines)

    def save_markdown(self, output_path: str) -> None:
        """
        Save documentation to file / 保存文档到文件

        Args:
            output_path: Path to save the documentation file

        Raises:
            IOError: If file cannot be written
        """
        doc = self.generate_markdown()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(doc)

    def print_to_stdout(self) -> None:
        """Print documentation to stdout / 输出文档到标准输出"""
        doc = self.generate_markdown()
        print(doc)
