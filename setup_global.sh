#!/bin/bash
#
# Web_Fetcher 全局安装脚本
# 提供多种安装方式，确保wf命令全局可用
# 
# 架构原则：
# - 渐进式安装（可选择安装级别）
# - 实时同步（修改立即生效）
# - 清晰意图（每个步骤都有说明）
# - 可回滚（提供卸载方法）
#

set -e  # 遇到错误立即退出

# ==================== 配置区 ====================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WF_PY="$SCRIPT_DIR/wf.py"
WEBFETCHER_PY="$SCRIPT_DIR/webfetcher.py"
INSTALL_MARKER="$SCRIPT_DIR/.wf_installed"
BACKUP_DIR="$HOME/.wf_backup"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 工具函数 ====================
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}    Web_Fetcher 全局安装管理器${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# 检查先决条件
check_prerequisites() {
    local errors=0
    
    print_info "检查先决条件..."
    
    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        print_error "未找到Python3，请先安装Python3"
        ((errors++))
    else
        print_success "Python3已安装: $(python3 --version)"
    fi
    
    # 检查必要文件
    if [ ! -f "$WF_PY" ]; then
        print_error "未找到 wf.py"
        ((errors++))
    else
        print_success "找到 wf.py"
    fi
    
    if [ ! -f "$WEBFETCHER_PY" ]; then
        print_error "未找到 webfetcher.py"
        ((errors++))
    else
        print_success "找到 webfetcher.py"
    fi
    
    # 检查 /usr/local/bin 权限
    if [ -d "/usr/local/bin" ]; then
        if [ -w "/usr/local/bin" ]; then
            print_success "/usr/local/bin 可写（无需sudo）"
        else
            print_warning "/usr/local/bin 需要sudo权限"
        fi
    else
        print_warning "/usr/local/bin 不存在，将尝试创建"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "先决条件检查失败，请解决上述问题后重试"
        exit 1
    fi
    
    echo ""
}

# 检测Shell配置文件
detect_shell_config() {
    local config_file=""
    
    # 检测当前使用的shell
    if [ -n "$ZSH_VERSION" ]; then
        config_file="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        # macOS Catalina+ 默认使用zsh，但用户可能仍使用bash
        if [ -f "$HOME/.bash_profile" ]; then
            config_file="$HOME/.bash_profile"
        else
            config_file="$HOME/.bashrc"
        fi
    else
        # 检查默认shell
        case "$SHELL" in
            */zsh)
                config_file="$HOME/.zshrc"
                ;;
            */bash)
                if [ -f "$HOME/.bash_profile" ]; then
                    config_file="$HOME/.bash_profile"
                else
                    config_file="$HOME/.bashrc"
                fi
                ;;
            *)
                print_warning "未知shell类型: $SHELL，使用默认.zshrc"
                config_file="$HOME/.zshrc"
                ;;
        esac
    fi
    
    echo "$config_file"
}

# 创建包装脚本（增强版）
create_wrapper_script() {
    local wrapper_path="$1"
    
    cat > "$wrapper_path" << 'EOF'
#!/bin/bash
#
# wf - WebFetcher全局命令包装器
# 自动生成，请勿手动编辑
#

# 获取真实路径
WF_REAL_PATH="$(readlink -f "$0" 2>/dev/null || readlink "$0" 2>/dev/null || echo "$0")"
WF_DIR="$(dirname "$WF_REAL_PATH")"

# 查找wf.py的实际位置
if [ -L "$0" ]; then
    # 如果是符号链接，获取链接目标
    LINK_TARGET="$(readlink "$0")"
    if [[ "$LINK_TARGET" = /* ]]; then
        # 绝对路径
        WF_PY="$LINK_TARGET"
    else
        # 相对路径
        WF_PY="$(dirname "$0")/$LINK_TARGET"
    fi
else
    # 直接执行的脚本
    WF_PY="$WF_DIR/wf.py"
fi

# 验证wf.py存在
if [ ! -f "$WF_PY" ]; then
    echo "错误: 找不到 wf.py at $WF_PY" >&2
    echo "请检查安装是否正确" >&2
    exit 1
fi

# 执行Python脚本
exec python3 "$WF_PY" "$@"
EOF
    
    chmod +x "$wrapper_path"
}

# 安装符号链接
install_symlink() {
    print_info "安装符号链接到 /usr/local/bin..."
    
    # 确保/usr/local/bin存在
    if [ ! -d "/usr/local/bin" ]; then
        print_warning "创建 /usr/local/bin 目录..."
        sudo mkdir -p /usr/local/bin
    fi
    
    # 备份现有文件（如果存在）
    if [ -e "/usr/local/bin/wf" ] && [ ! -L "/usr/local/bin/wf" ]; then
        print_warning "备份现有的 /usr/local/bin/wf..."
        mkdir -p "$BACKUP_DIR"
        sudo mv "/usr/local/bin/wf" "$BACKUP_DIR/wf.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 创建符号链接
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$WF_PY" /usr/local/bin/wf
    else
        sudo ln -sf "$WF_PY" /usr/local/bin/wf
    fi
    
    # 确保脚本可执行
    chmod +x "$WF_PY"
    chmod +x "$WEBFETCHER_PY"
    
    print_success "符号链接已创建: /usr/local/bin/wf -> $WF_PY"
}

# 安装Shell别名
install_alias() {
    local shell_config="$(detect_shell_config)"
    
    print_info "安装Shell别名到 $shell_config..."
    
    # 检查是否已经存在别名
    if grep -q "alias wf=" "$shell_config" 2>/dev/null; then
        print_warning "别名已存在，将更新..."
        # 删除旧的别名配置
        sed -i.bak '/# Web_Fetcher 便捷命令/,/alias wf=/d' "$shell_config"
    fi
    
    # 添加新的别名
    cat >> "$shell_config" << EOF

# Web_Fetcher 便捷命令 (由setup_global.sh自动生成)
alias wf='python3 "$WF_PY"'
EOF
    
    print_success "别名已添加到 $shell_config"
    print_info "需要运行 'source $shell_config' 或重启终端生效"
}

# 安装环境变量
install_env_vars() {
    local shell_config="$(detect_shell_config)"
    local output_dir="$1"
    
    print_info "设置默认输出目录环境变量..."
    
    # 删除旧的环境变量设置
    sed -i.bak '/# Web_Fetcher 默认输出目录/,/export WF_OUTPUT_DIR=/d' "$shell_config"
    
    # 添加新的环境变量
    cat >> "$shell_config" << EOF

# Web_Fetcher 默认输出目录 (由setup_global.sh自动生成)
export WF_OUTPUT_DIR="$output_dir"
EOF
    
    # 创建输出目录
    mkdir -p "$output_dir"
    
    print_success "默认输出目录设置为: $output_dir"
}

# 记录安装信息
record_installation() {
    local install_type="$1"
    
    cat > "$INSTALL_MARKER" << EOF
{
  "install_date": "$(date -Iseconds)",
  "install_type": "$install_type",
  "wf_py": "$WF_PY",
  "webfetcher_py": "$WEBFETCHER_PY",
  "shell_config": "$(detect_shell_config)",
  "symlink": $([ -L "/usr/local/bin/wf" ] && echo "true" || echo "false")
}
EOF
    
    print_success "安装信息已记录"
}

# 卸载功能
uninstall() {
    print_header
    print_warning "准备卸载 Web_Fetcher..."
    echo ""
    
    # 删除符号链接
    if [ -L "/usr/local/bin/wf" ]; then
        print_info "删除符号链接 /usr/local/bin/wf..."
        if [ -w "/usr/local/bin" ]; then
            rm -f /usr/local/bin/wf
        else
            sudo rm -f /usr/local/bin/wf
        fi
        print_success "符号链接已删除"
    fi
    
    # 清理Shell配置
    local shell_config="$(detect_shell_config)"
    if [ -f "$shell_config" ]; then
        print_info "清理 $shell_config 中的配置..."
        
        # 创建备份
        cp "$shell_config" "$shell_config.wf_uninstall.bak"
        
        # 删除别名和环境变量
        sed -i.bak '/# Web_Fetcher/,/^$/d' "$shell_config"
        sed -i.bak '/alias wf=/d' "$shell_config"
        sed -i.bak '/export WF_OUTPUT_DIR=/d' "$shell_config"
        
        print_success "Shell配置已清理（备份: $shell_config.wf_uninstall.bak）"
    fi
    
    # 删除安装标记
    if [ -f "$INSTALL_MARKER" ]; then
        rm -f "$INSTALL_MARKER"
        print_success "安装标记已删除"
    fi
    
    echo ""
    print_success "卸载完成！"
    print_info "项目文件未被删除，仍可在项目目录中使用"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    echo ""
    
    local success=true
    
    # 检查符号链接
    if [ -L "/usr/local/bin/wf" ]; then
        local link_target=$(readlink "/usr/local/bin/wf")
        if [ "$link_target" = "$WF_PY" ]; then
            print_success "符号链接正确: /usr/local/bin/wf -> $WF_PY"
        else
            print_warning "符号链接指向: $link_target (预期: $WF_PY)"
        fi
    else
        print_warning "符号链接未安装"
    fi
    
    # 检查命令可用性
    if command -v wf &> /dev/null; then
        print_success "wf命令可用: $(which wf)"
    else
        print_warning "wf命令暂不可用（可能需要重启终端）"
        success=false
    fi
    
    # 检查别名
    local shell_config="$(detect_shell_config)"
    if grep -q "alias wf=" "$shell_config" 2>/dev/null; then
        print_success "Shell别名已配置"
    else
        print_warning "Shell别名未配置"
    fi
    
    # 检查环境变量
    if [ -n "$WF_OUTPUT_DIR" ]; then
        print_success "默认输出目录: $WF_OUTPUT_DIR"
    else
        print_info "未设置默认输出目录（将使用./output）"
    fi
    
    echo ""
    if [ "$success" = true ]; then
        print_success "安装验证通过！"
    else
        print_warning "部分功能可能需要重启终端才能生效"
    fi
}

# 主菜单
main_menu() {
    print_header
    
    # 检查是否已安装
    if [ -f "$INSTALL_MARKER" ]; then
        print_info "检测到已安装的Web_Fetcher"
        echo ""
    fi
    
    echo "请选择操作："
    echo ""
    echo "  1) 🚀 快速安装（推荐）"
    echo "     - 创建符号链接到 /usr/local/bin"
    echo "     - 添加Shell别名作为备份"
    echo "     - 设置默认输出目录"
    echo ""
    echo "  2) 📦 最小安装"
    echo "     - 仅创建符号链接"
    echo ""
    echo "  3) 🔧 自定义安装"
    echo "     - 选择安装组件"
    echo "     - 自定义输出目录"
    echo ""
    echo "  4) 🔍 验证安装"
    echo "     - 检查所有组件状态"
    echo ""
    echo "  5) 🗑️  卸载"
    echo "     - 完全移除全局配置"
    echo ""
    echo "  6) 退出"
    echo ""
    read -p "请选择 [1-6]: " choice
    
    case "$choice" in
        1)
            # 快速安装
            check_prerequisites
            install_symlink
            install_alias
            
            # 设置默认输出目录
            echo ""
            print_info "选择默认输出目录："
            echo "  1) ~/Documents/web-content"
            echo "  2) 当前项目的output目录"
            echo "  3) 不设置（使用./output）"
            read -p "请选择 [1-3]: " dir_choice
            
            case "$dir_choice" in
                1)
                    install_env_vars "$HOME/Documents/web-content"
                    ;;
                2)
                    install_env_vars "$SCRIPT_DIR/output"
                    ;;
                *)
                    print_info "跳过默认输出目录设置"
                    ;;
            esac
            
            record_installation "quick"
            echo ""
            verify_installation
            ;;
            
        2)
            # 最小安装
            check_prerequisites
            install_symlink
            record_installation "minimal"
            echo ""
            verify_installation
            ;;
            
        3)
            # 自定义安装
            check_prerequisites
            
            echo ""
            read -p "安装符号链接？[Y/n]: " install_sym
            if [[ "$install_sym" != "n" && "$install_sym" != "N" ]]; then
                install_symlink
            fi
            
            echo ""
            read -p "安装Shell别名？[Y/n]: " install_ali
            if [[ "$install_ali" != "n" && "$install_ali" != "N" ]]; then
                install_alias
            fi
            
            echo ""
            read -p "设置默认输出目录？[Y/n]: " set_output
            if [[ "$set_output" != "n" && "$set_output" != "N" ]]; then
                read -p "输入目录路径（或按Enter使用默认）: " custom_dir
                if [ -z "$custom_dir" ]; then
                    custom_dir="$HOME/Documents/web-content"
                fi
                # 展开~
                custom_dir="${custom_dir/#\~/$HOME}"
                install_env_vars "$custom_dir"
            fi
            
            record_installation "custom"
            echo ""
            verify_installation
            ;;
            
        4)
            # 验证安装
            verify_installation
            ;;
            
        5)
            # 卸载
            echo ""
            print_warning "确定要卸载Web_Fetcher的全局配置吗？"
            read -p "输入 'yes' 确认卸载: " confirm
            if [ "$confirm" = "yes" ]; then
                uninstall
            else
                print_info "取消卸载"
            fi
            ;;
            
        6)
            print_info "退出安装程序"
            exit 0
            ;;
            
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac
}

# 显示使用提示
show_usage_tips() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}    使用提示${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
    echo "基本用法："
    echo "  wf <URL>                    # 抓取网页到默认目录"
    echo "  wf <URL> <output_dir>       # 指定输出目录"
    echo "  wf fast <URL>               # 快速模式"
    echo "  wf help                     # 查看帮助"
    echo ""
    echo "高级功能："
    echo "  wf batch urls.txt           # 批量抓取"
    echo "  wf <URL> -o ~/Desktop       # 使用-o指定输出"
    echo "  export WF_OUTPUT_DIR=~/docs # 设置默认输出目录"
    echo ""
    echo "项目开发："
    echo "  修改 $SCRIPT_DIR/wf.py 或 webfetcher.py"
    echo "  更改会立即生效，无需重新安装"
    echo ""
}

# ==================== 主程序 ====================

# 解析命令行参数
if [ "$1" = "uninstall" ]; then
    uninstall
    exit 0
elif [ "$1" = "verify" ]; then
    verify_installation
    exit 0
elif [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_header
    echo "用法: $0 [选项]"
    echo ""
    echo "选项："
    echo "  无参数        进入交互式安装菜单"
    echo "  uninstall    卸载Web_Fetcher全局配置"
    echo "  verify       验证安装状态"
    echo "  help         显示此帮助信息"
    echo ""
    show_usage_tips
    exit 0
fi

# 运行主菜单
main_menu

# 显示后续步骤
echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}    安装完成！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo "后续步骤："
echo ""
echo "1. 重启终端或运行："
echo "   source $(detect_shell_config)"
echo ""
echo "2. 测试命令："
echo "   wf help"
echo "   wf https://example.com"
echo ""
echo "3. 验证安装："
echo "   $0 verify"
echo ""

show_usage_tips