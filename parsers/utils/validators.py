"""Template validation utilities."""
import yaml
from typing import Dict, Tuple, List
from pathlib import Path


class TemplateValidator:
    """Validates template files against schema."""

    def __init__(self, schema_path: str = None):
        """Initialize validator with schema."""
        if schema_path is None:
            # Default schema location
            base_dir = Path(__file__).parent.parent
            schema_path = base_dir / "templates" / "schema.yaml"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict:
        """Load schema from YAML file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load schema: {e}")

    def validate_template(self, template: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a template against the schema.

        Args:
            template: Template dictionary to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        required = self.schema.get('required_fields', [])
        for field in required:
            if field not in template:
                errors.append(f"Missing required field: {field}")

        # Check field types (basic validation)
        field_types = self.schema.get('field_types', {})
        for field, type_info in field_types.items():
            if field not in template:
                # Skip if optional
                if type_info.get('optional', False):
                    continue
                # Already caught by required check
                continue

            value = template[field]
            expected_type = type_info.get('type', 'string')

            # Type checking
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{field}' must be an array")
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be an object")

        # Specific validation for selectors
        if 'selectors' in template:
            selectors = template['selectors']
            if not isinstance(selectors, dict):
                errors.append("'selectors' must be an object")
            else:
                # Must have at least title or content
                if 'title' not in selectors and 'content' not in selectors:
                    errors.append("'selectors' must contain at least 'title' or 'content'")

        return (len(errors) == 0, errors)

    def validate_file(self, template_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a template file.

        Args:
            template_path: Path to template YAML file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = yaml.safe_load(f)
            return self.validate_template(template)
        except Exception as e:
            return (False, [f"Failed to load template file: {e}"])


# Convenience function
def validate_template(template: Dict) -> Tuple[bool, List[str]]:
    """Validate a template dictionary."""
    validator = TemplateValidator()
    return validator.validate_template(template)
