#!/usr/bin/env python3
"""
编码修复验证测试脚本
用于验证第一阶段编码处理修复是否成功
"""

import sys
import time
import logging
from typing import Dict, List, Tuple
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 测试用例定义
TEST_CASES = [
    {
        "name": "人民网GB2312页面",
        "url": "http://cpc.people.com.cn/n/2012/1119/c352110-19621695.html",
        "expected_encoding": ["gb2312", "gbk", "gb18030"],  # 任一即可
        "expected_content": ["十八届中央政治局", "中央政治局会议"],
        "must_not_contain": ["ä¸­", "æ–‡", "ï¿½", "???"],  # 乱码标志
        "critical": True  # 必须通过的测试
    },
    {
        "name": "新浪UTF-8页面",
        "url": "https://www.sina.com.cn",
        "expected_encoding": ["utf-8"],
        "expected_content": ["新浪"],
        "must_not_contain": ["ä¸­", "æ–‡", "ï¿½"],
        "critical": True
    },
    {
        "name": "共产党员网UTF-8页面",
        "url": "https://www.12371.cn/2023/11/28/STUD1701138144744927.shtml",
        "expected_encoding": ["utf-8"],
        "expected_content": ["中国共产党", "党员"],
        "must_not_contain": ["ä¸­", "æ–‡", "ï¿½"],
        "critical": True
    },
    {
        "name": "Example.com ASCII页面",
        "url": "http://example.com",
        "expected_encoding": ["utf-8", "ascii"],
        "expected_content": ["Example Domain"],
        "must_not_contain": ["ï¿½"],
        "critical": False  # 兼容性测试
    }
]

class EncodingTestValidator:
    """编码修复测试验证器"""
    
    def __init__(self):
        self.results: List[Dict] = []
        self.performance_metrics: Dict = {
            "encoding_detect_times": [],
            "total_fetch_times": []
        }
    
    def validate_encoding_detection(self, html: str, test_case: Dict) -> Tuple[bool, List[str]]:
        """
        验证编码检测结果
        
        Returns:
            Tuple[bool, List[str]]: (是否通过, 错误信息列表)
        """
        errors = []
        
        # 检查必须包含的内容
        for expected in test_case.get("expected_content", []):
            if expected not in html:
                errors.append(f"未找到期望内容: '{expected}'")
        
        # 检查不应包含的内容（乱码）
        for forbidden in test_case.get("must_not_contain", []):
            if forbidden in html:
                errors.append(f"发现乱码特征: '{forbidden}'")
        
        # 检查是否有明显的解码错误
        if self._has_mojibake(html):
            errors.append("检测到可能的编码错误（mojibake）")
        
        return (len(errors) == 0, errors)
    
    def _has_mojibake(self, text: str) -> bool:
        """检测常见的中文乱码模式"""
        # 常见的UTF-8被错误解码为Latin-1的模式
        mojibake_patterns = [
            r'Ã[\x80-\xBF]',  # UTF-8的中文被当作Latin-1
            r'â[\x80-\x99]',  # 另一种常见模式
            r'ï¿½{3,}',  # 连续的替换字符
            r'[Â][^\x00-\x7F]{2,}',  # 其他乱码模式
        ]
        
        for pattern in mojibake_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def test_single_url(self, test_case: Dict) -> Dict:
        """测试单个URL"""
        result = {
            "name": test_case["name"],
            "url": test_case["url"],
            "passed": False,
            "errors": [],
            "encoding_time": None,
            "total_time": None
        }
        
        try:
            # 导入webfetcher模块
            sys.path.insert(0, '/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher')
            import webfetcher
            
            # 测试获取HTML
            start_time = time.time()
            html = webfetcher.fetch_html(test_case["url"])
            total_time = time.time() - start_time
            
            result["total_time"] = total_time * 1000  # 转换为毫秒
            
            # 验证编码处理
            passed, errors = self.validate_encoding_detection(html, test_case)
            result["passed"] = passed
            result["errors"] = errors
            
            # 记录性能指标
            self.performance_metrics["total_fetch_times"].append(result["total_time"])
            
            # 输出测试结果
            if passed:
                logging.info(f"✅ {test_case['name']}: 通过 (耗时: {result['total_time']:.2f}ms)")
            else:
                logging.error(f"❌ {test_case['name']}: 失败")
                for error in errors:
                    logging.error(f"   - {error}")
            
        except Exception as e:
            result["errors"] = [f"测试异常: {str(e)}"]
            logging.error(f"❌ {test_case['name']}: 异常 - {str(e)}")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logging.info("="*60)
        logging.info("开始编码修复验证测试")
        logging.info("="*60)
        
        all_passed = True
        critical_passed = True
        
        for test_case in TEST_CASES:
            result = self.test_single_url(test_case)
            
            if not result["passed"]:
                all_passed = False
                if test_case.get("critical", False):
                    critical_passed = False
        
        # 输出总结
        self._print_summary(all_passed, critical_passed)
        
        return critical_passed  # 返回关键测试是否全部通过
    
    def _print_summary(self, all_passed: bool, critical_passed: bool):
        """打印测试总结"""
        logging.info("="*60)
        logging.info("测试总结")
        logging.info("="*60)
        
        # 统计结果
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        logging.info(f"总测试数: {total}")
        logging.info(f"通过: {passed}")
        logging.info(f"失败: {failed}")
        
        # 性能统计
        if self.performance_metrics["total_fetch_times"]:
            avg_time = sum(self.performance_metrics["total_fetch_times"]) / len(self.performance_metrics["total_fetch_times"])
            max_time = max(self.performance_metrics["total_fetch_times"])
            logging.info(f"平均响应时间: {avg_time:.2f}ms")
            logging.info(f"最大响应时间: {max_time:.2f}ms")
        
        # 最终判定
        if all_passed:
            logging.info("🎉 所有测试通过！")
        elif critical_passed:
            logging.warning("⚠️ 关键测试通过，但有非关键测试失败")
        else:
            logging.error("❌ 关键测试失败！请检查编码处理实现")
        
        logging.info("="*60)
    
    def generate_report(self, filename: str = "encoding_test_report.md"):
        """生成测试报告"""
        report = []
        report.append("# 编码修复测试报告\n")
        report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("\n## 测试结果\n")
        
        for result in self.results:
            status = "✅ 通过" if result["passed"] else "❌ 失败"
            report.append(f"\n### {result['name']} - {status}\n")
            report.append(f"- URL: {result['url']}\n")
            report.append(f"- 耗时: {result.get('total_time', 'N/A'):.2f}ms\n")
            
            if result["errors"]:
                report.append("- 错误:\n")
                for error in result["errors"]:
                    report.append(f"  - {error}\n")
        
        # 写入文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(report)
        
        logging.info(f"测试报告已生成: {filename}")


def main():
    """主函数"""
    validator = EncodingTestValidator()
    
    # 运行测试
    success = validator.run_all_tests()
    
    # 生成报告
    validator.generate_report()
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()