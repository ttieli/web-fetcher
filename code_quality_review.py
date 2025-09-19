#!/usr/bin/env python3
"""
代码质量审查脚本
评估智能编码检测实现的代码质量
"""

import ast
import re
from typing import Dict, List, Tuple

def review_error_handling():
    """审查错误处理机制"""
    print("\n错误处理审查")
    print("-" * 50)
    
    # 读取实现代码
    with open('webfetcher.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 检查关键函数的错误处理
    functions_to_check = [
        'extract_charset_from_headers',
        'extract_charset_from_html',
        'try_decode_with_fallback',
        'smart_decode'
    ]
    
    issues = []
    for func_name in functions_to_check:
        # 查找函数定义
        pattern = rf'def {func_name}\([^)]*\):[^#]*?(?=\ndef|\nclass|\Z)'
        match = re.search(pattern, code, re.DOTALL)
        
        if match:
            func_code = match.group(0)
            
            # 检查是否有try-except块
            if 'try:' in func_code:
                print(f"  ✓ {func_name}: 包含异常处理")
                
                # 检查是否有日志记录
                if 'logging' in func_code:
                    print(f"    - 有日志记录")
                else:
                    print(f"    - 警告: 无日志记录")
                    issues.append(f"{func_name}: 缺少日志记录")
                
                # 检查是否有裸露的except
                if re.search(r'\nexcept:\s*\n', func_code):
                    print(f"    - 警告: 发现裸露的except语句")
                    issues.append(f"{func_name}: 使用了裸露的except")
            else:
                print(f"  ✗ {func_name}: 缺少异常处理")
                issues.append(f"{func_name}: 缺少try-except块")
        else:
            print(f"  ? {func_name}: 未找到函数定义")
    
    return issues

def review_code_structure():
    """审查代码结构和可维护性"""
    print("\n代码结构审查")
    print("-" * 50)
    
    with open('webfetcher.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 解析AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"  ✗ 语法错误: {e}")
        return ["语法错误"]
    
    issues = []
    
    # 检查函数复杂度
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 计算圈复杂度（简化版）
            complexity = 1  # 基础复杂度
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While)):
                    complexity += 1
                elif isinstance(child, ast.ExceptHandler):
                    complexity += 1
            
            if node.name in ['smart_decode', 'try_decode_with_fallback']:
                if complexity > 10:
                    print(f"  ✗ {node.name}: 圈复杂度过高 ({complexity})")
                    issues.append(f"{node.name}: 圈复杂度={complexity}")
                else:
                    print(f"  ✓ {node.name}: 圈复杂度合理 ({complexity})")
    
    # 检查函数文档
    func_patterns = [
        (r'def extract_charset_from_headers.*?"""(.*?)"""', 'extract_charset_from_headers'),
        (r'def extract_charset_from_html.*?"""(.*?)"""', 'extract_charset_from_html'),
        (r'def smart_decode.*?"""(.*?)"""', 'smart_decode'),
    ]
    
    print("\n文档完整性:")
    for pattern, func_name in func_patterns:
        match = re.search(pattern, code, re.DOTALL)
        if match:
            docstring = match.group(1)
            if 'Args:' in docstring and 'Returns:' in docstring:
                print(f"  ✓ {func_name}: 文档完整")
            else:
                print(f"  △ {func_name}: 文档不完整")
                issues.append(f"{func_name}: 文档不完整")
        else:
            print(f"  ✗ {func_name}: 缺少文档")
            issues.append(f"{func_name}: 缺少文档")
    
    return issues

def review_encoding_fallback():
    """审查编码降级链的实现"""
    print("\n编码降级链审查")
    print("-" * 50)
    
    with open('webfetcher.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 查找降级链定义
    pattern = r"fallback_encodings\s*=\s*\[(.*?)\]"
    match = re.search(pattern, code)
    
    if match:
        encodings_str = match.group(1)
        encodings = [e.strip().strip("'\"") for e in encodings_str.split(',')]
        
        print(f"  降级链: {' → '.join(encodings)}")
        
        # 验证降级链顺序
        expected_order = ['gb2312', 'gbk', 'gb18030']
        actual_order = [e for e in encodings if e in expected_order]
        
        if actual_order == expected_order:
            print(f"  ✓ 中文编码降级顺序正确")
        else:
            print(f"  ✗ 中文编码降级顺序错误")
            return ["编码降级链顺序不正确"]
        
        if 'utf-8' in encodings:
            print(f"  ✓ 包含UTF-8后备")
        else:
            print(f"  ✗ 缺少UTF-8后备")
            return ["缺少UTF-8后备编码"]
    else:
        print(f"  ✗ 未找到降级链定义")
        return ["未找到降级链定义"]
    
    return []

def review_integration_points():
    """审查集成点的实现"""
    print("\n集成点审查")
    print("-" * 50)
    
    with open('webfetcher.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    issues = []
    
    # 检查fetch_html_original中的集成
    pattern = r'def fetch_html_original.*?return.*?smart_decode\(data.*?\)'
    if re.search(pattern, code, re.DOTALL):
        print(f"  ✓ fetch_html_original: 已集成smart_decode")
    else:
        print(f"  ✗ fetch_html_original: 未正确集成smart_decode")
        issues.append("fetch_html_original未正确集成")
    
    # 检查curl fallback中的集成
    pattern = r'def fetch_html_with_curl.*?return.*?smart_decode\(.*?\)'
    if re.search(pattern, code, re.DOTALL):
        print(f"  ✓ fetch_html_with_curl: 已集成smart_decode")
    else:
        print(f"  ✗ fetch_html_with_curl: 未正确集成smart_decode")
        issues.append("fetch_html_with_curl未正确集成")
    
    return issues

def generate_quality_report(all_issues: Dict[str, List[str]]):
    """生成质量报告"""
    print("\n" + "=" * 60)
    print("代码质量评估报告")
    print("=" * 60)
    
    total_issues = sum(len(issues) for issues in all_issues.values())
    
    print(f"\n发现的问题总数: {total_issues}")
    
    if total_issues > 0:
        print("\n详细问题列表:")
        for category, issues in all_issues.items():
            if issues:
                print(f"\n{category}:")
                for issue in issues:
                    print(f"  - {issue}")
    
    # 评分
    score = 100 - (total_issues * 5)  # 每个问题扣5分
    score = max(0, min(100, score))
    
    print(f"\n代码质量评分: {score}/100")
    
    # 评级
    if score >= 90:
        grade = "A - 优秀"
    elif score >= 80:
        grade = "B - 良好"
    elif score >= 70:
        grade = "C - 及格"
    else:
        grade = "D - 需要改进"
    
    print(f"质量等级: {grade}")
    
    # 建议
    print("\n改进建议:")
    if total_issues == 0:
        print("  ✓ 代码质量优秀，继续保持")
    else:
        if 'error_handling' in all_issues and all_issues['error_handling']:
            print("  - 增强错误处理和日志记录")
        if 'code_structure' in all_issues and all_issues['code_structure']:
            print("  - 简化复杂函数，改善代码结构")
        if 'encoding_fallback' in all_issues and all_issues['encoding_fallback']:
            print("  - 优化编码降级链实现")
        if 'integration' in all_issues and all_issues['integration']:
            print("  - 确保所有集成点正确实现")
    
    return score >= 70

def main():
    """主审查流程"""
    
    print("=" * 60)
    print("智能编码检测系统 - 代码质量审查")
    print("=" * 60)
    
    all_issues = {}
    
    # 1. 错误处理审查
    all_issues['error_handling'] = review_error_handling()
    
    # 2. 代码结构审查
    all_issues['code_structure'] = review_code_structure()
    
    # 3. 编码降级链审查
    all_issues['encoding_fallback'] = review_encoding_fallback()
    
    # 4. 集成点审查
    all_issues['integration'] = review_integration_points()
    
    # 5. 生成报告
    passed = generate_quality_report(all_issues)
    
    # 最终结论
    print("\n" + "=" * 60)
    print("代码质量验证结论")
    print("=" * 60)
    
    if passed:
        print("\n✓ 代码质量验证通过：实现满足基本质量要求")
        return 0
    else:
        print("\n✗ 代码质量需要改进")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())