# 插件配置集成指南 / Plugin Configuration Integration Guide

> **目的**: 将配置驱动的插件管理集成到现有系统  
> **原则**: 保留所有代码，通过配置控制行为  
> **作者**: Archy-Principle-Architect  
> **日期**: 2025-09-25  

---

## 1. 核心改动：修改 plugins/registry.py

### 1.1 添加配置导入（在文件开头）

```python
# 在现有导入后添加
from .plugin_config import get_enabled_plugins, is_plugin_enabled
```

### 1.2 修改注册逻辑（register_plugins 方法）

**原代码结构**（大概位置）:
```python
def register_plugins(self):
    """注册所有插件"""
    # 导入并注册各个插件
    from .http_fetcher import HTTPFetcherPlugin
    from .curl import CurlFetcherPlugin
    from .safari.plugin import SafariFetcherPlugin
    # ... 其他插件导入
    
    self.register(HTTPFetcherPlugin())
    self.register(CurlFetcherPlugin())
    self.register(SafariFetcherPlugin())
    # ... 其他插件注册
```

**修改为配置驱动**:
```python
def register_plugins(self):
    """注册启用的插件（通过配置控制）"""
    # 导入所有插件（保持代码完整）
    from .http_fetcher import HTTPFetcherPlugin
    from .curl import CurlFetcherPlugin
    from .safari.plugin import SafariFetcherPlugin
    from .playwright import PlaywrightFetcherPlugin
    from .selenium.plugin import SeleniumFetcherPlugin  # 新增
    
    # 创建插件映射（所有插件都在这里）
    all_plugins = {
        'HTTPFetcherPlugin': HTTPFetcherPlugin(),
        'CurlFetcherPlugin': CurlFetcherPlugin(),
        'SafariFetcherPlugin': SafariFetcherPlugin(),
        'PlaywrightFetcherPlugin': PlaywrightFetcherPlugin(),
        'SeleniumFetcherPlugin': SeleniumFetcherPlugin()  # 新增
    }
    
    # 获取启用的插件列表
    enabled_plugins = get_enabled_plugins()
    
    # 只注册启用的插件
    for plugin_name in enabled_plugins:
        if plugin_name in all_plugins:
            plugin = all_plugins[plugin_name]
            self.register(plugin)
            print(f"✅ Registered: {plugin_name}")
        else:
            print(f"⚠️ Warning: Plugin {plugin_name} not found")
    
    # 显示禁用的插件（用于调试）
    for plugin_name, plugin in all_plugins.items():
        if plugin_name not in enabled_plugins:
            print(f"❌ Disabled: {plugin_name} (code preserved)")
```

### 1.3 添加运行时插件查询方法

```python
def get_active_plugins(self) -> List[str]:
    """获取当前活动的插件列表"""
    return [p.__class__.__name__ for p in self._plugins.values()]

def is_plugin_active(self, plugin_name: str) -> bool:
    """检查插件是否处于活动状态"""
    return plugin_name in self._plugins

def reload_plugins(self):
    """重新加载插件配置（用于运行时切换）"""
    self._plugins.clear()
    self.register_plugins()
    print(f"Plugins reloaded. Active: {self.get_active_plugins()}")
```

---

## 2. 使用示例

### 2.1 命令行切换模式

```bash
# 切换到极简模式（只有urllib和selenium）
./switch_plugin_mode.sh minimal

# 切换到开发模式（所有插件）
./switch_plugin_mode.sh dev

# 查看当前状态
./switch_plugin_mode.sh status
```

### 2.2 Python代码中切换

```python
from plugins.plugin_config import PluginConfig, ConfigModes

# 切换到极简模式
ConfigModes.apply_mode('minimal')

# 切换到开发模式
ConfigModes.apply_mode('development')

# 查看状态
PluginConfig.print_config_status()
```

### 2.3 环境变量控制

```bash
# 在shell中设置
export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin"

# 在Python中设置
import os
os.environ['WF_ENABLED_PLUGINS'] = "HTTPFetcherPlugin,SeleniumFetcherPlugin"
```

---

## 3. 测试验证

### 3.1 验证配置是否生效

```python
# test_plugin_config.py
import sys
sys.path.insert(0, '.')

from plugins.plugin_config import PluginConfig

def test_config():
    # 显示当前配置
    PluginConfig.print_config_status()
    
    # 测试极简模式
    PluginConfig.switch_to_minimal()
    enabled = PluginConfig.get_enabled_plugins()
    assert len(enabled) == 2
    assert 'HTTPFetcherPlugin' in enabled
    assert 'SeleniumFetcherPlugin' in enabled
    print("✅ Minimal mode test passed")
    
    # 测试开发模式
    PluginConfig.switch_to_development()
    enabled = PluginConfig.get_enabled_plugins()
    assert len(enabled) >= 4
    print("✅ Development mode test passed")

if __name__ == "__main__":
    test_config()
```

### 3.2 验证插件注册

```python
# 在webfetcher.py或测试文件中
from plugins.registry import PluginRegistry

# 创建注册表
registry = PluginRegistry()

# 检查活动插件
active = registry.get_active_plugins()
print(f"Active plugins: {active}")

# 验证极简模式
import os
os.environ['WF_ENABLED_PLUGINS'] = "HTTPFetcherPlugin,SeleniumFetcherPlugin"
registry.reload_plugins()
assert len(registry.get_active_plugins()) == 2
```

---

## 4. 回滚策略

### 4.1 快速回滚到原始配置

```bash
# 方法1: 使用切换脚本
./switch_plugin_mode.sh original

# 方法2: 直接设置环境变量
export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,CurlFetcherPlugin,SafariFetcherPlugin,PlaywrightFetcherPlugin"

# 方法3: 清除配置使用默认值
unset WF_ENABLED_PLUGINS
```

### 4.2 临时测试特定插件

```bash
# 只测试curl插件
WF_ENABLED_PLUGINS="CurlFetcherPlugin" python webfetcher.py "https://example.com"

# 测试urllib + curl组合
WF_ENABLED_PLUGINS="HTTPFetcherPlugin,CurlFetcherPlugin" python webfetcher.py "https://example.com"
```

---

## 5. 优势总结

### 5.1 代码完整性
- ✅ 所有插件代码保留
- ✅ 便于理解系统全貌
- ✅ 方便未来维护和扩展

### 5.2 配置灵活性
- ✅ 运行时切换，无需修改代码
- ✅ 不同环境使用不同配置
- ✅ 支持A/B测试和灰度发布

### 5.3 风险控制
- ✅ 随时可逆，降低风险
- ✅ 快速回滚到任何配置
- ✅ 保留所有功能选项

### 5.4 用户体验
- ✅ 默认极简，降低选择困难
- ✅ 高级用户可自定义配置
- ✅ 透明的配置管理

---

## 6. 注意事项

### 6.1 配置优先级
1. 环境变量 `WF_ENABLED_PLUGINS`
2. 配置文件 `plugin_config.py` 中的默认值
3. 代码中的硬编码（应避免）

### 6.2 插件依赖
- 确保启用的插件所需依赖已安装
- selenium插件需要：`pip install selenium webdriver-manager`
- playwright插件需要：`pip install playwright`

### 6.3 性能考虑
- 禁用的插件不会被实例化，零性能开销
- 配置检查只在启动时执行一次
- 运行时切换需要调用 `reload_plugins()`

---

## 7. 常见问题

### Q1: 如何永久保存配置？
**A**: 使用 `switch_plugin_mode.sh` 脚本，它会自动保存到shell配置文件。

### Q2: 如何知道哪些插件可用？
**A**: 运行 `python -c "from plugins.plugin_config import PluginConfig; PluginConfig.print_config_status()"`

### Q3: 配置不生效怎么办？
**A**: 
1. 检查环境变量：`echo $WF_ENABLED_PLUGINS`
2. 重新source配置：`source ~/.bashrc` 或 `source ~/.zshrc`
3. 验证Python可以读取：`python -c "import os; print(os.getenv('WF_ENABLED_PLUGINS'))"`

### Q4: 如何添加新插件？
**A**: 
1. 在 `plugin_config.py` 的 `ALL_AVAILABLE_PLUGINS` 中添加插件名
2. 在 `registry.py` 的 `all_plugins` 字典中添加插件映射
3. 根据需要将其加入 `ENABLED_PLUGINS` 或 `DISABLED_PLUGINS`

---

**最后更新**: 2025-09-25  
**架构师**: Archy-Principle-Architect  
**核心理念**: 配置驱动简化，代码保持完整