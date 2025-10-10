#!/usr/bin/env python3
"""
Integration tests for template tool CLI / 模板工具CLI集成测试

Tests the complete workflow of template creation, validation,
preview, and documentation generation.

测试模板创建、验证、预览和文档生成的完整工作流程。

Author: Cody (Full-Stack Engineer)
Date: 2025-10-10
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import json
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parser_engine.tools.generators.template_generator import TemplateGenerator
from parser_engine.tools.validators.schema_validator import SchemaValidator
from parser_engine.tools.preview.html_preview import HTMLPreviewer
from parser_engine.tools.generators.doc_generator import DocGenerator


class TestTemplateToolIntegration:
    """Integration test suite for template tools / 模板工具集成测试套件"""

    def __init__(self):
        """Initialize test suite / 初始化测试套件"""
        self.temp_dir = None
        self.test_results = []

    def setup(self):
        """Set up test environment / 设置测试环境"""
        self.temp_dir = tempfile.mkdtemp(prefix="template_tool_test_")
        print(f"Test environment created: {self.temp_dir}")

    def teardown(self):
        """Clean up test environment / 清理测试环境"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"Test environment cleaned: {self.temp_dir}")

    def record_result(self, test_name, passed, message=""):
        """Record test result / 记录测试结果"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  → {message}")

    def test_init_command(self):
        """Test template initialization / 测试模板初始化"""
        test_name = "Template Initialization (init)"
        try:
            # Test article template creation
            generator = TemplateGenerator()
            template_data = generator.generate(
                domain="test.site.com",
                template_type="article"
            )

            # Verify template content
            required_fields = ['version', 'name', 'domains']
            for field in required_fields:
                if field not in template_data:
                    self.record_result(test_name, False, f"Missing required field: {field}")
                    return False

            # Save to file to verify it's valid YAML
            output_dir = os.path.join(self.temp_dir, "test_site_com")
            os.makedirs(output_dir, exist_ok=True)
            template_path = os.path.join(output_dir, "template.yaml")

            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)

            self.record_result(test_name, True, f"Created template at {template_path}")
            return True

        except Exception as e:
            self.record_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_validate_command(self):
        """Test template validation / 测试模板验证"""
        test_name = "Template Validation (validate)"
        try:
            # Create a test template first
            generator = TemplateGenerator()
            template_data = generator.generate(
                domain="validate.test.com",
                template_type="article"
            )

            output_dir = os.path.join(self.temp_dir, "validate_test")
            os.makedirs(output_dir, exist_ok=True)
            template_path = os.path.join(output_dir, "template.yaml")

            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)

            # Validate the template
            validator = SchemaValidator()
            is_valid, errors = validator.validate_file(template_path)

            if not is_valid:
                self.record_result(test_name, False, f"Validation failed: {errors}")
                return False

            self.record_result(test_name, True, "Template validated successfully")
            return True

        except Exception as e:
            self.record_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_preview_command(self):
        """Test template preview / 测试模板预览"""
        test_name = "Template Preview (preview)"
        try:
            # Create a test template
            generator = TemplateGenerator()
            template_data = generator.generate(
                domain="preview.test.com",
                template_type="article"
            )

            output_dir = os.path.join(self.temp_dir, "preview_test")
            os.makedirs(output_dir, exist_ok=True)
            template_path = os.path.join(output_dir, "template.yaml")

            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)

            # Create sample HTML
            sample_html = """
            <!DOCTYPE html>
            <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Test Article Title</h1>
                    <div class="author">John Doe</div>
                    <time>2025-10-10</time>
                    <div class="content">
                        <p>This is test content.</p>
                    </div>
                </article>
            </body>
            </html>
            """

            html_path = os.path.join(self.temp_dir, "sample.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(sample_html)

            # Preview extraction
            preview = HTMLPreviewer(template_path)
            result = preview.preview_from_file(html_path, output_format='text')

            if not result:
                self.record_result(test_name, False, "Preview returned no results")
                return False

            self.record_result(test_name, True, "Preview executed successfully")
            return True

        except Exception as e:
            self.record_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_doc_command(self):
        """Test documentation generation / 测试文档生成"""
        test_name = "Documentation Generation (doc)"
        try:
            # Create a test template
            generator = TemplateGenerator()
            template_data = generator.generate(
                domain="doc.test.com",
                template_type="article"
            )

            output_dir = os.path.join(self.temp_dir, "doc_test")
            os.makedirs(output_dir, exist_ok=True)
            template_path = os.path.join(output_dir, "template.yaml")

            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)

            # Generate documentation
            doc_gen = DocGenerator(template_path)
            doc_content = doc_gen.generate_markdown()

            if not doc_content or len(doc_content) < 100:
                self.record_result(test_name, False, "Documentation too short or empty")
                return False

            # Verify documentation contains key sections
            required_sections = ['Parser', 'Domain', 'Selector']
            for section in required_sections:
                if section not in doc_content:
                    self.record_result(test_name, False, f"Missing section: {section}")
                    return False

            self.record_result(test_name, True, f"Generated {len(doc_content)} chars of documentation")
            return True

        except Exception as e:
            self.record_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_full_workflow(self):
        """Test complete template tool workflow / 测试完整模板工具工作流程"""
        test_name = "Full Workflow Integration"
        try:
            workflow_dir = os.path.join(self.temp_dir, "workflow_test")
            os.makedirs(workflow_dir, exist_ok=True)

            # Step 1: Create template
            generator = TemplateGenerator()
            template_data = generator.generate(
                domain="news.example.com",
                template_type="article"
            )

            template_dir = os.path.join(workflow_dir, "news_example_com")
            os.makedirs(template_dir, exist_ok=True)
            template_path = os.path.join(template_dir, "template.yaml")

            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)

            # Step 2: Validate template
            validator = SchemaValidator()
            is_valid, errors = validator.validate_file(template_path)
            if not is_valid:
                self.record_result(test_name, False, f"Workflow validation failed: {errors}")
                return False

            # Step 3: Create sample HTML and preview
            sample_html = """
            <!DOCTYPE html>
            <html>
            <body>
                <article>
                    <h1>Breaking News</h1>
                    <div class="author">Reporter Name</div>
                    <time>2025-10-10</time>
                    <div class="content"><p>News content here.</p></div>
                </article>
            </body>
            </html>
            """
            html_path = os.path.join(workflow_dir, "news.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(sample_html)

            preview = HTMLPreviewer(template_path)
            preview_result = preview.preview_from_file(html_path, output_format='text')

            # Step 4: Generate documentation
            doc_gen = DocGenerator(template_path)
            doc_content = doc_gen.generate_markdown()

            doc_path = os.path.join(workflow_dir, "template_doc.md")
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)

            # Verify all outputs exist
            if not all([
                os.path.exists(template_path),
                os.path.exists(doc_path),
                preview_result is not None
            ]):
                self.record_result(test_name, False, "Workflow incomplete - missing outputs")
                return False

            self.record_result(test_name, True, "Complete workflow executed successfully")
            return True

        except Exception as e:
            self.record_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_cli_commands(self):
        """Test CLI commands via subprocess / 测试CLI命令"""
        test_name = "CLI Command Execution"
        try:
            script_path = os.path.join(PROJECT_ROOT, "scripts", "template_tool.py")

            if not os.path.exists(script_path):
                self.record_result(test_name, False, f"CLI script not found: {script_path}")
                return False

            # Test init command - output is a file, not a directory
            template_path = os.path.join(self.temp_dir, "cli_test.yaml")
            result = subprocess.run([
                sys.executable,
                script_path,
                "init",
                "--domain", "cli.test.com",
                "--type", "article",
                "--output", template_path
            ], capture_output=True, text=True)

            if result.returncode != 0:
                self.record_result(test_name, False, f"CLI init failed: {result.stderr}")
                return False

            # Verify template file was created
            if not os.path.exists(template_path):
                self.record_result(test_name, False, f"Template file not created: {template_path}")
                return False

            # Test validate command
            result = subprocess.run([
                sys.executable,
                script_path,
                "validate",
                template_path
            ], capture_output=True, text=True)

            if result.returncode != 0:
                self.record_result(test_name, False, f"CLI validate failed: {result.stderr}")
                return False

            self.record_result(test_name, True, "CLI commands executed successfully")
            return True

        except Exception as e:
            self.record_result(test_name, False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all integration tests / 运行所有集成测试"""
        print("\n" + "="*70)
        print("PARSER TEMPLATE TOOL - INTEGRATION TEST SUITE")
        print("解析模板工具 - 集成测试套件")
        print("="*70 + "\n")

        self.setup()

        try:
            # Run individual tests
            self.test_init_command()
            self.test_validate_command()
            self.test_preview_command()
            self.test_doc_command()
            self.test_full_workflow()
            self.test_cli_commands()

            # Print summary
            print("\n" + "="*70)
            print("TEST SUMMARY / 测试摘要")
            print("="*70)

            passed = sum(1 for r in self.test_results if r['passed'])
            total = len(self.test_results)

            for result in self.test_results:
                status = "✓" if result['passed'] else "✗"
                print(f"{status} {result['test']}")

            print(f"\nPassed: {passed}/{total}")
            print(f"Success Rate: {(passed/total)*100:.1f}%")

            if passed == total:
                print("\n🎉 ALL TESTS PASSED! / 所有测试通过!")
                return True
            else:
                print(f"\n⚠️  {total - passed} test(s) failed / 测试失败")
                return False

        finally:
            self.teardown()


def main():
    """Main test execution / 主测试执行"""
    test_suite = TestTemplateToolIntegration()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
