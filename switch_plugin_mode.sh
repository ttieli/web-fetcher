#!/bin/bash

# Plugin Mode Switcher
# ====================
# 快速切换插件模式的脚本
# 通过配置控制插件启用/禁用，不删除任何代码
#
# Author: Archy-Principle-Architect
# Date: 2025-09-25

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置文件路径
CONFIG_FILE="plugins/plugin_config.py"
BASHRC="$HOME/.bashrc"
ZSHRC="$HOME/.zshrc"

# 获取当前shell配置文件
get_shell_config() {
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo "$ZSHRC"
    else
        echo "$BASHRC"
    fi
}

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 显示当前状态
show_status() {
    print_message "$BLUE" "\n=== 当前插件配置状态 ==="
    
    if [ -n "$WF_ENABLED_PLUGINS" ]; then
        print_message "$GREEN" "环境变量已设置: WF_ENABLED_PLUGINS=$WF_ENABLED_PLUGINS"
        IFS=',' read -ra PLUGINS <<< "$WF_ENABLED_PLUGINS"
        print_message "$GREEN" "启用的插件:"
        for plugin in "${PLUGINS[@]}"; do
            echo "  ✅ $plugin"
        done
    else
        print_message "$YELLOW" "使用默认配置 (极简模式):"
        echo "  ✅ HTTPFetcherPlugin (urllib)"
        echo "  ✅ SeleniumFetcherPlugin (selenium)"
    fi
}

# 切换到极简模式
switch_to_minimal() {
    print_message "$GREEN" "\n切换到极简模式..."
    export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin"
    
    # 保存到shell配置
    local shell_config=$(get_shell_config)
    grep -v "WF_ENABLED_PLUGINS" "$shell_config" > "$shell_config.tmp" 2>/dev/null || true
    echo 'export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin"' >> "$shell_config.tmp"
    mv "$shell_config.tmp" "$shell_config"
    
    print_message "$GREEN" "✅ 已切换到极简模式 (urllib + selenium)"
    print_message "$YELLOW" "   其他插件已禁用但代码保留"
}

# 切换到兼容模式
switch_to_compatible() {
    print_message "$GREEN" "\n切换到兼容模式..."
    export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin,CurlFetcherPlugin"
    
    # 保存到shell配置
    local shell_config=$(get_shell_config)
    grep -v "WF_ENABLED_PLUGINS" "$shell_config" > "$shell_config.tmp" 2>/dev/null || true
    echo 'export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin,CurlFetcherPlugin"' >> "$shell_config.tmp"
    mv "$shell_config.tmp" "$shell_config"
    
    print_message "$GREEN" "✅ 已切换到兼容模式 (urllib + selenium + curl)"
}

# 切换到开发模式
switch_to_development() {
    print_message "$GREEN" "\n切换到开发模式..."
    export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin,CurlFetcherPlugin,SafariFetcherPlugin,PlaywrightFetcherPlugin"
    
    # 保存到shell配置
    local shell_config=$(get_shell_config)
    grep -v "WF_ENABLED_PLUGINS" "$shell_config" > "$shell_config.tmp" 2>/dev/null || true
    echo 'export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,SeleniumFetcherPlugin,CurlFetcherPlugin,SafariFetcherPlugin,PlaywrightFetcherPlugin"' >> "$shell_config.tmp"
    mv "$shell_config.tmp" "$shell_config"
    
    print_message "$GREEN" "✅ 已切换到开发模式 (所有插件启用)"
}

# 切换到性能模式
switch_to_performance() {
    print_message "$GREEN" "\n切换到性能模式..."
    export WF_ENABLED_PLUGINS="HTTPFetcherPlugin"
    
    # 保存到shell配置
    local shell_config=$(get_shell_config)
    grep -v "WF_ENABLED_PLUGINS" "$shell_config" > "$shell_config.tmp" 2>/dev/null || true
    echo 'export WF_ENABLED_PLUGINS="HTTPFetcherPlugin"' >> "$shell_config.tmp"
    mv "$shell_config.tmp" "$shell_config"
    
    print_message "$GREEN" "✅ 已切换到性能模式 (仅urllib)"
    print_message "$YELLOW" "   最快速度，但功能受限"
}

# 恢复原始配置
restore_original() {
    print_message "$GREEN" "\n恢复到原始多插件配置..."
    export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,CurlFetcherPlugin,SafariFetcherPlugin,PlaywrightFetcherPlugin"
    
    # 保存到shell配置
    local shell_config=$(get_shell_config)
    grep -v "WF_ENABLED_PLUGINS" "$shell_config" > "$shell_config.tmp" 2>/dev/null || true
    echo 'export WF_ENABLED_PLUGINS="HTTPFetcherPlugin,CurlFetcherPlugin,SafariFetcherPlugin,PlaywrightFetcherPlugin"' >> "$shell_config.tmp"
    mv "$shell_config.tmp" "$shell_config"
    
    print_message "$GREEN" "✅ 已恢复原始配置 (不包含Selenium)"
    print_message "$YELLOW" "   注意：这是迁移前的配置"
}

# 清除配置
clear_config() {
    print_message "$YELLOW" "\n清除插件配置..."
    unset WF_ENABLED_PLUGINS
    
    # 从shell配置中移除
    local shell_config=$(get_shell_config)
    grep -v "WF_ENABLED_PLUGINS" "$shell_config" > "$shell_config.tmp" 2>/dev/null || true
    mv "$shell_config.tmp" "$shell_config"
    
    print_message "$GREEN" "✅ 已清除配置，将使用代码默认值"
}

# 显示帮助
show_help() {
    cat << EOF
$(print_message "$BLUE" "Web Fetcher 插件模式切换器")
$(print_message "$BLUE" "================================")

用法: $0 [选项]

选项:
  status      显示当前配置状态
  minimal     切换到极简模式 (urllib + selenium) [推荐]
  compatible  切换到兼容模式 (urllib + selenium + curl)
  dev         切换到开发模式 (所有插件)
  perf        切换到性能模式 (仅urllib)
  original    恢复原始配置 (迁移前)
  clear       清除配置，使用默认值
  help        显示此帮助信息

模式说明:
  极简模式 (minimal):    用户日常使用，只有两个选择
  兼容模式 (compatible): 添加curl作为额外选项
  开发模式 (dev):        启用所有插件用于开发测试
  性能模式 (perf):       只用最快的urllib
  原始模式 (original):   迁移前的多插件配置

注意:
  - 所有插件代码都保留，只是通过配置控制启用/禁用
  - 配置会保存到 shell 配置文件中
  - 重新打开终端后配置仍然有效

示例:
  $0 minimal    # 切换到推荐的极简模式
  $0 status     # 查看当前状态
  $0 dev        # 开发时启用所有插件

EOF
}

# 主程序
main() {
    case "${1:-}" in
        status)
            show_status
            ;;
        minimal)
            switch_to_minimal
            show_status
            ;;
        compatible)
            switch_to_compatible
            show_status
            ;;
        dev|development)
            switch_to_development
            show_status
            ;;
        perf|performance)
            switch_to_performance
            show_status
            ;;
        original)
            restore_original
            show_status
            ;;
        clear)
            clear_config
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_message "$RED" "错误: 未知选项 '${1:-}'"
            show_help
            exit 1
            ;;
    esac
    
    # 提醒用户
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "-h" && "$1" != "status" ]]; then
        print_message "$YELLOW" "\n提示: 配置已更新。如果在当前shell中使用，请运行:"
        print_message "$GREEN" "  source $(get_shell_config)"
        print_message "$YELLOW" "或重新打开终端使配置生效。"
    fi
}

# 运行主程序
main "$@"