#!/usr/bin/env python3
"""
Template Generator / 模板生成器

Generates parser template scaffolding from domain and type parameters.
从域名和类型参数生成解析器模板脚手架。
"""

from typing import Dict, Any, List
from datetime import datetime
import os
import yaml


class TemplateGenerator:
    """Generates parser templates / 生成解析器模板"""

    def __init__(self):
        """Initialize template generator / 初始化模板生成器"""
        self.template_types = {
            'article': self._generate_article_selectors,
            'list': self._generate_list_selectors,
            'generic': self._generate_generic_selectors
        }

    def generate(self, domain: str, template_type: str = 'article') -> Dict[str, Any]:
        """
        Generate template dictionary / 生成模板字典

        Args:
            domain: Target domain (e.g., "example.com")
            template_type: Template type ('article', 'list', 'generic')

        Returns:
            Template dictionary ready to be saved as YAML

        Raises:
            ValueError: If template_type is not supported
        """
        if template_type not in self.template_types:
            raise ValueError(
                f"Unsupported template type: {template_type}. "
                f"Must be one of: {', '.join(self.template_types.keys())}"
            )

        # Generate base template structure
        template = {
            'name': f"{domain.title()} Parser",
            'version': "1.0.0",
            'domains': [domain],
            'selectors': self.template_types[template_type]()
        }

        # Add metadata section with creation info
        template['metadata'] = {
            'created': datetime.now().isoformat(),
            'template_type': template_type,
            'generator_version': '1.0.0'
        }

        # Add test_cases placeholder
        template['test_cases'] = [
            {
                'name': 'Basic extraction test',
                'url': f'https://{domain}/sample-page',
                'expected': {
                    'title': 'Sample Title',
                    'content': 'Sample content...'
                }
            }
        ]

        return template

    def _generate_article_selectors(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Generate selectors for article template type / 生成文章类型选择器

        Returns:
            Dictionary containing article-specific selectors
        """
        return {
            'title': [
                {
                    'selector': "meta[property='og:title']",
                    'strategy': 'css',
                    'attribute': 'content'
                },
                {
                    'selector': 'h1',
                    'strategy': 'css'
                },
                {
                    'selector': '.article-title',
                    'strategy': 'css'
                }
            ],
            'content': [
                {
                    'selector': 'article',
                    'strategy': 'css'
                },
                {
                    'selector': '.article-content',
                    'strategy': 'css'
                },
                {
                    'selector': '.post-content',
                    'strategy': 'css'
                }
            ],
            'author': [
                {
                    'selector': "meta[name='author']",
                    'strategy': 'css',
                    'attribute': 'content'
                },
                {
                    'selector': '.author',
                    'strategy': 'css'
                },
                {
                    'selector': '.byline',
                    'strategy': 'css'
                }
            ],
            'date': [
                {
                    'selector': "meta[property='article:published_time']",
                    'strategy': 'css',
                    'attribute': 'content'
                },
                {
                    'selector': 'time[datetime]',
                    'strategy': 'css',
                    'attribute': 'datetime'
                },
                {
                    'selector': '.published-date',
                    'strategy': 'css'
                }
            ],
            'images': [
                {
                    'selector': "meta[property='og:image']",
                    'strategy': 'css',
                    'attribute': 'content'
                },
                {
                    'selector': 'article img',
                    'strategy': 'css',
                    'attribute': 'src'
                }
            ]
        }

    def _generate_list_selectors(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Generate selectors for list template type / 生成列表类型选择器

        Returns:
            Dictionary containing list-specific selectors
        """
        return {
            'items': [
                {
                    'selector': '.item',
                    'strategy': 'css'
                },
                {
                    'selector': 'li',
                    'strategy': 'css'
                },
                {
                    'selector': '.list-item',
                    'strategy': 'css'
                }
            ],
            'title': [
                {
                    'selector': 'h1',
                    'strategy': 'css'
                },
                {
                    'selector': '.page-title',
                    'strategy': 'css'
                }
            ],
            'link': [
                {
                    'selector': 'a',
                    'strategy': 'css',
                    'attribute': 'href'
                }
            ]
        }

    def _generate_generic_selectors(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Generate selectors for generic template type / 生成通用类型选择器

        Returns:
            Dictionary containing generic selectors
        """
        return {
            'title': [
                {
                    'selector': "meta[property='og:title']",
                    'strategy': 'css',
                    'attribute': 'content'
                },
                {
                    'selector': 'title',
                    'strategy': 'css'
                },
                {
                    'selector': 'h1',
                    'strategy': 'css'
                }
            ],
            'content': [
                {
                    'selector': 'main',
                    'strategy': 'css'
                },
                {
                    'selector': 'article',
                    'strategy': 'css'
                },
                {
                    'selector': '#content',
                    'strategy': 'css'
                }
            ]
        }


def generate_template_file(domain: str, template_type: str, output_path: str) -> None:
    """
    Generate and save template to file / 生成并保存模板到文件

    Args:
        domain: Target domain (e.g., "example.com")
        template_type: Template type ('article', 'list', 'generic')
        output_path: Path where template file should be saved

    Raises:
        IOError: If file cannot be written
        ValueError: If parameters are invalid
    """
    # Validate inputs
    if not domain:
        raise ValueError("Domain cannot be empty")

    if not output_path:
        raise ValueError("Output path cannot be empty")

    # Create generator and generate template
    generator = TemplateGenerator()
    template = generator.generate(domain, template_type)

    # Create parent directories if they don't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Add comment header to YAML file
    comment_header = f"""# Parser Template for {domain}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Template Type: {template_type}
# Version: 1.0.0
#
# This is an automatically generated template. Please customize the selectors
# according to your target website's structure.
#
# 这是一个自动生成的模板。请根据目标网站的结构自定义选择器。

"""

    # Save template to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(comment_header)
        yaml.safe_dump(
            template,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2
        )
