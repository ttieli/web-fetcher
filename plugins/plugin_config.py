"""
Plugin Configuration Manager
============================
配置驱动的插件管理机制，通过配置控制插件启用/禁用
保留所有插件代码完整性，仅在运行时控制行为

Author: Archy-Principle-Architect
Date: 2025-09-25
"""

import os
from typing import List, Set


class PluginConfig:
    """
    插件配置管理器
    
    设计原则：
    1. 保持所有插件代码完整
    2. 通过配置控制运行时行为
    3. 支持环境变量覆盖
    4. 提供简单的切换机制
    """
    
    # ============= 默认配置：极简模式 =============
    # 用户只看到这两个选择
    ENABLED_PLUGINS = [
        'HTTPFetcherPlugin',      # urllib - 轻量快速
        'SeleniumFetcherPlugin'   # selenium - 处理复杂场景
    ]
    
    # ============= 保留但禁用的插件 =============
    # 代码完整保留，未来可通过配置重新启用
    DISABLED_PLUGINS = [
        'CurlFetcherPlugin',       # curl命令行工具
        'SafariFetcherPlugin',     # Safari浏览器集成
        'PlaywrightFetcherPlugin'  # Playwright自动化
    ]
    
    # ============= 所有可用插件 =============
    ALL_AVAILABLE_PLUGINS = ENABLED_PLUGINS + DISABLED_PLUGINS
    
    @classmethod
    def get_enabled_plugins(cls) -> List[str]:
        """
        获取启用的插件列表
        
        优先级：
        1. 环境变量 WF_ENABLED_PLUGINS
        2. 配置文件默认值 ENABLED_PLUGINS
        
        Returns:
            启用的插件名称列表
        """
        # 检查环境变量
        env_plugins = os.getenv('WF_ENABLED_PLUGINS')
        if env_plugins:
            # 解析逗号分隔的插件列表
            plugins = [p.strip() for p in env_plugins.split(',') if p.strip()]
            # 验证插件名称有效
            valid_plugins = [p for p in plugins if p in cls.ALL_AVAILABLE_PLUGINS]
            if valid_plugins:
                return valid_plugins
            print(f"Warning: Invalid plugins in WF_ENABLED_PLUGINS. Using defaults.")
        
        # 返回默认配置
        return cls.ENABLED_PLUGINS
    
    @classmethod
    def is_plugin_enabled(cls, plugin_name: str) -> bool:
        """
        检查特定插件是否启用
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            True if enabled, False otherwise
        """
        return plugin_name in cls.get_enabled_plugins()
    
    @classmethod
    def get_disabled_plugins(cls) -> List[str]:
        """
        获取被禁用的插件列表
        
        Returns:
            禁用的插件名称列表
        """
        enabled = set(cls.get_enabled_plugins())
        return [p for p in cls.ALL_AVAILABLE_PLUGINS if p not in enabled]
    
    @classmethod
    def enable_all_plugins(cls) -> None:
        """
        管理员模式：启用所有插件
        通过设置环境变量实现
        """
        all_plugins = ','.join(cls.ALL_AVAILABLE_PLUGINS)
        os.environ['WF_ENABLED_PLUGINS'] = all_plugins
        print(f"All plugins enabled: {all_plugins}")
    
    @classmethod
    def switch_to_minimal(cls) -> None:
        """
        切换到极简模式（只有urllib和selenium）
        """
        minimal = ','.join(['HTTPFetcherPlugin', 'SeleniumFetcherPlugin'])
        os.environ['WF_ENABLED_PLUGINS'] = minimal
        print(f"Switched to minimal mode: {minimal}")
    
    @classmethod
    def switch_to_development(cls) -> None:
        """
        切换到开发模式（启用所有插件用于测试）
        """
        cls.enable_all_plugins()
    
    @classmethod
    def print_config_status(cls) -> None:
        """
        打印当前配置状态
        """
        print("\n" + "="*50)
        print("Plugin Configuration Status")
        print("="*50)
        
        enabled = cls.get_enabled_plugins()
        disabled = cls.get_disabled_plugins()
        
        print(f"\nEnabled Plugins ({len(enabled)}):")
        for plugin in enabled:
            print(f"  ✅ {plugin}")
        
        if disabled:
            print(f"\nDisabled Plugins ({len(disabled)}):")
            for plugin in disabled:
                print(f"  ❌ {plugin}")
        
        # 检查环境变量
        env_value = os.getenv('WF_ENABLED_PLUGINS')
        if env_value:
            print(f"\n📌 Configuration source: Environment variable")
            print(f"   WF_ENABLED_PLUGINS={env_value}")
        else:
            print(f"\n📌 Configuration source: Default settings")
        
        print("="*50 + "\n")


# ============= 便捷函数 =============

def get_enabled_plugins() -> List[str]:
    """获取启用的插件列表"""
    return PluginConfig.get_enabled_plugins()


def is_plugin_enabled(plugin_name: str) -> bool:
    """检查插件是否启用"""
    return PluginConfig.is_plugin_enabled(plugin_name)


def print_status():
    """打印配置状态"""
    PluginConfig.print_config_status()


# ============= 预设配置模式 =============

class ConfigModes:
    """预定义的配置模式"""
    
    # 极简模式：用户日常使用
    MINIMAL = ['HTTPFetcherPlugin', 'SeleniumFetcherPlugin']
    
    # 兼容模式：添加Curl作为备选
    COMPATIBLE = ['HTTPFetcherPlugin', 'SeleniumFetcherPlugin', 'CurlFetcherPlugin']
    
    # 开发模式：所有插件
    DEVELOPMENT = PluginConfig.ALL_AVAILABLE_PLUGINS
    
    # 测试模式：用于CI/CD
    TESTING = ['HTTPFetcherPlugin', 'CurlFetcherPlugin']
    
    # 性能模式：只用最快的
    PERFORMANCE = ['HTTPFetcherPlugin']
    
    @classmethod
    def apply_mode(cls, mode_name: str):
        """
        应用预设模式
        
        Args:
            mode_name: 模式名称 (minimal/compatible/development/testing/performance)
        """
        modes = {
            'minimal': cls.MINIMAL,
            'compatible': cls.COMPATIBLE,
            'development': cls.DEVELOPMENT,
            'testing': cls.TESTING,
            'performance': cls.PERFORMANCE
        }
        
        if mode_name.lower() in modes:
            plugins = ','.join(modes[mode_name.lower()])
            os.environ['WF_ENABLED_PLUGINS'] = plugins
            print(f"Applied {mode_name} mode: {plugins}")
        else:
            print(f"Unknown mode: {mode_name}. Available: {', '.join(modes.keys())}")


if __name__ == "__main__":
    # 测试配置管理器
    print("Testing Plugin Configuration Manager")
    print("-" * 40)
    
    # 显示当前状态
    PluginConfig.print_config_status()
    
    # 测试不同模式
    print("\nTesting mode switches:")
    print("-" * 40)
    
    # 极简模式
    print("\n1. Minimal mode:")
    PluginConfig.switch_to_minimal()
    print(f"   Enabled: {PluginConfig.get_enabled_plugins()}")
    
    # 开发模式
    print("\n2. Development mode:")
    PluginConfig.switch_to_development()
    print(f"   Enabled: {PluginConfig.get_enabled_plugins()}")
    
    # 恢复默认
    print("\n3. Back to defaults:")
    if 'WF_ENABLED_PLUGINS' in os.environ:
        del os.environ['WF_ENABLED_PLUGINS']
    print(f"   Enabled: {PluginConfig.get_enabled_plugins()}")