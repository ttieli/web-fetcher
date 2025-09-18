# Web_Fetcher 全局安装指南

## 快速开始

```bash
# 使脚本可执行
chmod +x setup_global.sh

# 运行安装程序
./setup_global.sh
```

选择选项1（快速安装）即可完成全局配置。

## 安装方式对比

### 方式1：符号链接（推荐）
**优势**：
- 全局可用，任何目录都能使用wf命令
- 修改代码后立即生效，无需重新安装
- 符合macOS标准实践

**实现**：
```bash
/usr/local/bin/wf -> /你的项目路径/wf.py
```

### 方式2：Shell别名（备用）
**优势**：
- 不需要sudo权限
- 用户级别配置

**限制**：
- 仅在交互式终端可用
- 脚本中无法调用

## 核心特性

### 1. 实时同步
修改项目中的 `wf.py` 或 `webfetcher.py` 后，更改立即生效：

```bash
# 编辑项目文件
vim /你的项目路径/webfetcher.py

# 无需重新安装，直接使用
wf https://example.com  # 已使用最新代码
```

### 2. 灵活的输出目录管理

优先级从高到低：
1. 命令行指定：`wf URL ~/Desktop/`
2. 环境变量：`export WF_OUTPUT_DIR=~/Documents/web`
3. 默认值：`./output/`

### 3. 安全的卸载

```bash
# 完全卸载
./setup_global.sh uninstall

# 或使用独立卸载脚本
./uninstall.sh
```

## 验证安装

```bash
# 验证所有组件
./setup_global.sh verify

# 手动检查
which wf                    # 应显示 /usr/local/bin/wf
ls -la /usr/local/bin/wf   # 应显示指向wf.py的符号链接
wf help                    # 应显示帮助信息
```

## 故障排除

### 问题1：权限错误
```bash
# 如果/usr/local/bin需要权限
sudo ./setup_global.sh
```

### 问题2：命令未找到
```bash
# 重新加载Shell配置
source ~/.zshrc  # 或 ~/.bashrc

# 检查PATH
echo $PATH | grep -q "/usr/local/bin" || echo "PATH missing /usr/local/bin"
```

### 问题3：符号链接失效
```bash
# 重新创建链接
./setup_global.sh
# 选择选项2（最小安装）
```

## 开发工作流

1. **全局使用**：在任何目录运行 `wf URL`
2. **本地开发**：在项目目录编辑代码
3. **即时测试**：修改立即生效，无需重装

```bash
# 工作流示例
cd ~/任意目录
wf https://example.com output/  # 使用全局命令

cd /你的项目路径
vim webfetcher.py              # 修改代码
wf https://test.com             # 立即测试新代码
```

## 安全考虑

- 符号链接指向用户目录，不在系统关键路径
- 脚本使用 `#!/usr/bin/env python3` 确保Python版本一致性
- 卸载只删除链接和配置，不删除项目文件

## 最佳实践建议

1. **使用快速安装**：适合大多数用户
2. **设置默认输出目录**：避免文件散落各处
3. **定期验证**：`./setup_global.sh verify`
4. **保持项目路径稳定**：避免移动项目目录

## 架构原则

本安装系统遵循以下架构原则：

- **渐进式胜过大爆炸**：提供多种安装级别
- **务实胜过教条**：混合使用符号链接和别名
- **清晰意图胜过巧妙代码**：每个步骤都有明确说明
- **选择无聊但明确的方案**：使用标准的/usr/local/bin路径