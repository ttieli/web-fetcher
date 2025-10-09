"""Template loading and matching engine."""
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse
from parsers.utils.validators import TemplateValidator


class TemplateLoader:
    """Loads and manages parser templates."""

    def __init__(self, template_dir: str = None):
        """Initialize template loader."""
        if template_dir is None:
            # Default to parsers/templates directory
            base_dir = Path(__file__).parent.parent
            template_dir = base_dir / "templates"

        self.template_dir = Path(template_dir)
        self.validator = TemplateValidator()
        self._templates = {}  # Cache loaded templates
        self._load_all_templates()

    def _load_all_templates(self):
        """Scan and load all template files."""
        if not self.template_dir.exists():
            return

        # Find all YAML files in templates directory
        for template_path in self.template_dir.rglob("*.yaml"):
            try:
                self._load_template_file(template_path)
            except Exception as e:
                print(f"Warning: Failed to load {template_path}: {e}")

    def _load_template_file(self, path: Path):
        """Load a single template file."""
        with open(path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)

        # Validate template
        is_valid, errors = self.validator.validate_template(template)
        if not is_valid:
            raise ValueError(f"Invalid template: {errors}")

        # Store by name
        name = template.get('name', path.stem)
        self._templates[name] = {
            'template': template,
            'path': str(path)
        }

    def get_template_for_url(self, url: str) -> Optional[Dict]:
        """
        Find the best matching template for a URL.

        Args:
            url: URL to match against templates

        Returns:
            Template dict or None
        """
        # Parse URL to get domain
        parsed = urlparse(url)
        domain = parsed.netloc

        # Try exact domain match first
        for name, info in self._templates.items():
            template = info['template']
            domains = template.get('domains', [])

            # Check exact match
            if domain in domains:
                return template

            # Check wildcard match
            for pattern in domains:
                if pattern == '*':  # Universal match
                    continue
                if pattern.startswith('*.'):
                    # Wildcard subdomain match
                    base = pattern[2:]  # Remove *.
                    if domain.endswith(base):
                        return template

        # Fallback to generic template
        return self.get_template_by_name('Generic Web Template')

    def get_template_by_name(self, name: str) -> Optional[Dict]:
        """Get template by name."""
        info = self._templates.get(name)
        return info['template'] if info else None

    def list_templates(self) -> List[str]:
        """List all loaded template names."""
        return list(self._templates.keys())
