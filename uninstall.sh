#!/bin/bash
#
# Web_Fetcher 卸载脚本
# 安全地移除所有全局配置
#

# 直接调用setup_global.sh的卸载功能
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
"$SCRIPT_DIR/setup_global.sh" uninstall