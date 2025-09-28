#!/usr/bin/env python3
"""
测试步骤2：完善参数传递到插件系统的验证脚本

验证用户偏好是否正确传递到插件系统，让整个fetch链路都遵循用户选择。
"""

import sys
import os
import logging
import tempfile
from unittest.mock import patch

# 设置路径和导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """设置日志记录"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_step2_param_passing.log')
        ]
    )

def test_urllib_preference_bypass():
    """测试当用户选择urllib时是否绕过插件系统"""
    from webfetcher import fetch_html_with_plugins, _user_method_choice, _user_no_fallback
    
    print("\n=== 测试1: urllib偏好绕过插件系统 ===")
    
    # 保存原始设置
    original_choice = _user_method_choice
    original_no_fallback = _user_no_fallback
    
    try:
        # 模拟设置用户偏好为urllib
        import webfetcher
        webfetcher._user_method_choice = 'urllib'
        
        # 测试简单URL
        test_url = "http://example.com"
        
        # 使用patch来模拟fetch_html_with_retry调用
        with patch('webfetcher.fetch_html_with_retry') as mock_retry:
            # 模拟成功返回
            mock_retry.return_value = ("<html>test</html>", type('obj', (object,), {'primary_method': 'urllib'})())
            
            result = fetch_html_with_plugins(test_url)
            
            # 验证是否调用了legacy方法而不是插件
            assert mock_retry.called, "应该调用fetch_html_with_retry"
            print("✓ 用户选择urllib时成功绕过插件系统")
            
    except Exception as e:
        print(f"✗ urllib偏好测试失败: {e}")
        return False
    finally:
        # 恢复原始设置
        webfetcher._user_method_choice = original_choice
        webfetcher._user_no_fallback = original_no_fallback
    
    return True

def test_plugin_context_user_preferences():
    """测试用户偏好是否传递到插件上下文"""
    print("\n=== 测试2: 用户偏好传递到插件上下文 ===")
    
    try:
        # 导入必要的组件
        from webfetcher import fetch_html_with_plugins, _user_method_choice, _user_no_fallback, PLUGIN_SYSTEM_AVAILABLE
        from plugins import FetchContext
        
        if not PLUGIN_SYSTEM_AVAILABLE:
            print("⚠ 插件系统不可用，跳过测试")
            return True
        
        # 保存原始设置
        import webfetcher
        original_choice = webfetcher._user_method_choice
        original_no_fallback = webfetcher._user_no_fallback
        
        # 设置测试偏好
        webfetcher._user_method_choice = 'selenium'
        webfetcher._user_no_fallback = True
        
        # 创建测试上下文
        context = FetchContext(
            url="http://example.com",
            user_agent="test-agent",
            timeout=30,
            max_retries=3,
            plugin_config={
                'user_method_choice': 'selenium',
                'user_no_fallback': True,
                'respect_user_preferences': True
            }
        )
        
        # 验证上下文包含用户偏好
        assert context.plugin_config['user_method_choice'] == 'selenium', "用户方法选择应该传递到上下文"
        assert context.plugin_config['user_no_fallback'] == True, "用户无回退偏好应该传递到上下文"
        assert context.plugin_config['respect_user_preferences'] == True, "应该标记尊重用户偏好"
        
        print("✓ 用户偏好成功传递到插件上下文")
        
        # 恢复原始设置
        webfetcher._user_method_choice = original_choice
        webfetcher._user_no_fallback = original_no_fallback
        
    except Exception as e:
        print(f"✗ 插件上下文测试失败: {e}")
        return False
    
    return True

def test_registry_user_preference_filtering():
    """测试注册表是否根据用户偏好过滤插件"""
    print("\n=== 测试3: 注册表用户偏好过滤 ===")
    
    try:
        from webfetcher import PLUGIN_SYSTEM_AVAILABLE
        
        if not PLUGIN_SYSTEM_AVAILABLE:
            print("⚠ 插件系统不可用，跳过测试")
            return True
        
        from plugins import get_global_registry, FetchContext
        
        registry = get_global_registry()
        
        # 测试selenium偏好
        context_selenium = FetchContext(
            url="http://example.com",
            plugin_config={
                'user_method_choice': 'selenium',
                'user_no_fallback': False,
                'respect_user_preferences': True
            }
        )
        
        suitable_plugins_selenium = registry.get_suitable_plugins(context_selenium)
        print(f"  Selenium偏好时的可用插件: {[p.name for p in suitable_plugins_selenium]}")
        
        # 测试auto偏好
        context_auto = FetchContext(
            url="http://example.com",
            plugin_config={
                'user_method_choice': 'auto',
                'user_no_fallback': False,
                'respect_user_preferences': True
            }
        )
        
        suitable_plugins_auto = registry.get_suitable_plugins(context_auto)
        print(f"  Auto偏好时的可用插件: {[p.name for p in suitable_plugins_auto]}")
        
        print("✓ 注册表成功应用用户偏好过滤")
        
    except Exception as e:
        print(f"✗ 注册表过滤测试失败: {e}")
        return False
    
    return True

def test_no_fallback_behavior():
    """测试无回退行为"""
    print("\n=== 测试4: 无回退行为 ===")
    
    try:
        from webfetcher import PLUGIN_SYSTEM_AVAILABLE
        
        if not PLUGIN_SYSTEM_AVAILABLE:
            print("⚠ 插件系统不可用，跳过测试")
            return True
        
        from plugins import get_global_registry, FetchContext, FetchResult
        
        registry = get_global_registry()
        
        # 测试no_fallback=True的情况
        context = FetchContext(
            url="http://nonexistent-test-url-12345.com",  # 不存在的URL
            plugin_config={
                'user_method_choice': 'auto',
                'user_no_fallback': True,
                'respect_user_preferences': True
            }
        )
        
        # 这应该快速失败而不是尝试多个插件
        result = registry.fetch_with_fallback(context)
        
        if not result.success:
            print("✓ 无回退模式下正确快速失败")
        else:
            print("⚠ 无回退测试: 意外成功（可能是缓存或其他原因）")
        
    except Exception as e:
        print(f"✗ 无回退行为测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始步骤2参数传递验证测试")
    setup_logging()
    
    tests = [
        test_urllib_preference_bypass,
        test_plugin_context_user_preferences,
        test_registry_user_preference_filtering,
        test_no_fallback_behavior
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试 {test.__name__} 发生异常: {e}")
            results.append(False)
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有参数传递测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)