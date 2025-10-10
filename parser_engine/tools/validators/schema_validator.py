#!/usr/bin/env python3
"""
Schema Validator / Schema校验器

Validates parser templates against the schema definition.
根据schema定义验证解析器模板。
"""

from typing import Tuple, List, Dict, Any
import yaml
import re
import os


class SchemaValidator:
    """Validates templates against schema / 根据schema验证模板"""

    def __init__(self, schema: Dict[str, Any] = None):
        """
        Initialize validator with schema / 用schema初始化校验器

        Args:
            schema: Schema dictionary from schema.yaml (optional)
                   If not provided, will load from default location
        """
        if schema is None:
            schema = self._load_default_schema()
        self.schema = schema

    def _load_default_schema(self) -> Dict[str, Any]:
        """
        Load schema from default location / 从默认位置加载schema

        Returns:
            Schema dictionary

        Raises:
            FileNotFoundError: If schema.yaml is not found
        """
        # Find schema.yaml relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(
            current_dir, '..', '..', 'templates', 'schema.yaml'
        )
        schema_path = os.path.normpath(schema_path)

        if not os.path.exists(schema_path):
            raise FileNotFoundError(
                f"Schema file not found at: {schema_path}\n"
                "Please ensure parser_engine/templates/schema.yaml exists."
            )

        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def validate(self, template: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate template / 验证模板

        Args:
            template: Template dictionary to validate

        Returns:
            (is_valid, error_messages)
            - is_valid: True if valid, False otherwise
            - error_messages: List of error messages (empty if valid)
        """
        errors = []

        # Check if template is a dictionary
        if not isinstance(template, dict):
            errors.append("Template must be a dictionary/object")
            return (False, errors)

        # Check required fields
        required_fields = self.schema.get('required_fields', [])
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: '{field}'")

        # Validate field types
        if 'name' in template:
            if not isinstance(template['name'], str):
                errors.append("Field 'name' must be a string")
            elif len(template['name'].strip()) == 0:
                errors.append("Field 'name' cannot be empty")

        if 'version' in template:
            if not isinstance(template['version'], str):
                errors.append("Field 'version' must be a string")
            elif not self._validate_version(template['version']):
                errors.append(
                    f"Field 'version' has invalid format: '{template['version']}'. "
                    "Expected format: '1.0' or '1.0.0'"
                )

        if 'domains' in template:
            if not isinstance(template['domains'], list):
                errors.append("Field 'domains' must be a list/array")
            elif len(template['domains']) == 0:
                errors.append("Field 'domains' cannot be empty")
            else:
                for i, domain in enumerate(template['domains']):
                    if not isinstance(domain, str):
                        errors.append(f"Domain at index {i} must be a string")

        # Validate selectors structure
        if 'selectors' in template:
            if not isinstance(template['selectors'], dict):
                errors.append("Field 'selectors' must be a dictionary/object")
            else:
                selector_errors = self._validate_selectors(template['selectors'])
                errors.extend(selector_errors)

        # Validate test_cases if present
        if 'test_cases' in template:
            if not isinstance(template['test_cases'], list):
                errors.append("Field 'test_cases' must be a list/array")
            else:
                test_errors = self._validate_test_cases(template['test_cases'])
                errors.extend(test_errors)

        # Validate extends field if present
        if 'extends' in template:
            if not isinstance(template['extends'], str):
                errors.append("Field 'extends' must be a string")

        return (len(errors) == 0, errors)

    def _validate_version(self, version: str) -> bool:
        """
        Validate version string format / 验证版本字符串格式

        Args:
            version: Version string to validate

        Returns:
            True if valid, False otherwise
        """
        # Accept formats like "1.0", "1.0.0", "2.1", etc.
        pattern = r'^\d+\.\d+(\.\d+)?$'
        return bool(re.match(pattern, version))

    def _validate_selectors(self, selectors: Dict[str, Any]) -> List[str]:
        """
        Validate selectors structure / 验证选择器结构

        Args:
            selectors: Selectors dictionary to validate

        Returns:
            List of error messages
        """
        errors = []

        for key, value in selectors.items():
            # Each selector can be a list of selector definitions
            # or a dictionary of nested selectors (for metadata)
            if isinstance(value, list):
                for i, selector in enumerate(value):
                    if not isinstance(selector, dict):
                        errors.append(
                            f"Selector '{key}[{i}]' must be a dictionary/object"
                        )
                    else:
                        selector_errors = self._validate_selector_item(
                            selector, f"{key}[{i}]"
                        )
                        errors.extend(selector_errors)
            elif isinstance(value, dict):
                # This could be a nested selector group (like metadata)
                # Recursively validate
                nested_errors = self._validate_selectors(value)
                errors.extend([f"{key}.{e}" for e in nested_errors])
            else:
                errors.append(
                    f"Selector '{key}' must be a list or dictionary"
                )

        return errors

    def _validate_selector_item(
        self, selector: Dict[str, str], path: str
    ) -> List[str]:
        """
        Validate individual selector item / 验证单个选择器项

        Args:
            selector: Selector dictionary to validate
            path: Path for error reporting

        Returns:
            List of error messages
        """
        errors = []

        # Check required selector field
        if 'selector' not in selector:
            errors.append(f"Selector '{path}' missing 'selector' field")

        # Check strategy field
        if 'strategy' in selector:
            valid_strategies = ['css', 'xpath', 'regex', 'text_pattern']
            if selector['strategy'] not in valid_strategies:
                errors.append(
                    f"Selector '{path}' has invalid strategy: '{selector['strategy']}'. "
                    f"Must be one of: {', '.join(valid_strategies)}"
                )

        # Check for common typos in field names
        known_fields = {'selector', 'strategy', 'attribute', 'regex', 'extract'}
        unknown_fields = set(selector.keys()) - known_fields
        if unknown_fields:
            errors.append(
                f"Selector '{path}' has unknown fields: {', '.join(unknown_fields)}. "
                f"Did you mean one of: {', '.join(known_fields)}?"
            )

        return errors

    def _validate_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[str]:
        """
        Validate test cases structure / 验证测试用例结构

        Args:
            test_cases: List of test cases to validate

        Returns:
            List of error messages
        """
        errors = []

        for i, test_case in enumerate(test_cases):
            if not isinstance(test_case, dict):
                errors.append(f"Test case at index {i} must be a dictionary/object")
                continue

            # Check for recommended fields
            if 'name' not in test_case:
                errors.append(f"Test case at index {i} should have a 'name' field")

            if 'url' not in test_case and 'html' not in test_case:
                errors.append(
                    f"Test case at index {i} should have either 'url' or 'html' field"
                )

        return errors

    def validate_file(self, template_path: str) -> Tuple[bool, List[str]]:
        """
        Validate template file / 验证模板文件

        Args:
            template_path: Path to template file to validate

        Returns:
            (is_valid, error_messages)
        """
        try:
            # Check if file exists
            if not os.path.exists(template_path):
                return (False, [f"Template file not found: {template_path}"])

            # Load template
            with open(template_path, 'r', encoding='utf-8') as f:
                template = yaml.safe_load(f)

            # Validate template
            return self.validate(template)

        except yaml.YAMLError as e:
            return (False, [f"Failed to parse YAML: {str(e)}"])
        except Exception as e:
            return (False, [f"Failed to load template: {str(e)}"])

    def get_validation_report(
        self, template: Dict[str, Any], verbose: bool = False
    ) -> str:
        """
        Generate a detailed validation report / 生成详细验证报告

        Args:
            template: Template to validate
            verbose: Include additional information

        Returns:
            Formatted validation report string
        """
        is_valid, errors = self.validate(template)

        report = []
        report.append("=" * 60)
        report.append("Template Validation Report / 模板验证报告")
        report.append("=" * 60)

        if verbose and 'name' in template:
            report.append(f"\nTemplate: {template['name']}")
            if 'version' in template:
                report.append(f"Version: {template['version']}")

        report.append(f"\nStatus: {'✓ VALID' if is_valid else '✗ INVALID'}")

        if errors:
            report.append(f"\nErrors found: {len(errors)}")
            report.append("-" * 60)
            for i, error in enumerate(errors, 1):
                report.append(f"{i}. {error}")
        else:
            report.append("\n✓ No errors found. Template is valid.")

        report.append("=" * 60)

        return "\n".join(report)
