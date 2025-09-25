# Chrome 调试端口常驻配置指南

> 目标：将 Chrome 设置为默认以 `--remote-debugging-port=9222` 模式启动，方便 Selenium 通过 debuggerAddress 复用登录态，同时不影响日常浏览体验。本指南提供脚本与图形界面两种方式，均在当前目录 (`config/`) 内完成配置。

---

## 1. 准备执行脚本（一次性）
1. **脚本位置**：`config/chrome-debug.sh` （已随仓库提供）。
2. **脚本特性**：✨ **智能实例管理** - 避免重复启动，已运行时只打开新标签页
   ```bash
   #!/bin/bash
   # 启动带远程调试端口的 Chrome，会复用指定的用户配置目录
   # 如果Chrome已经运行，则只打开新标签页而不启动新实例
   set -euo pipefail
   
   CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
   PROFILE_DIR="${HOME}/.chrome-wf"
   PORT="9222"
   
   # 智能检测：如果Chrome debug实例已运行，只打开新标签页
   if check_chrome_debug_running; then
       # 使用AppleScript打开新标签页，支持URL参数
       echo "Chrome debug实例已运行，已打开新标签页"
   else
       # 启动新的Chrome debug实例
       echo "启动Chrome debug实例..."
       exec "${CHROME_APP}" --remote-debugging-port="${PORT}" ...
   fi
   ```
3. **赋权**（如首次拉取仓库请执行一次）：
   ```bash
   chmod +x config/chrome-debug.sh
   ```
4. **用户配置目录**：脚本会自动使用 `~/.chrome-wf` 作为独立 profile，确保调试浏览与日常浏览互不干扰。

---

## 2. 方式一：替换 Dock 图标（推荐）
1. 打开 **Automator**（应用程序 → Automator）。
2. 选择 **“应用程序”** 类型，点击创建。
3. 在搜索栏输入 **“运行 Shell 脚本”**，双击添加到工作流。
4. 将 Shell 命令替换为：
   ```bash
   "${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/config/chrome-debug.sh"
   ```
   > 如果需要传递参数，可改为 `".../chrome-debug.sh" "$@"`。
5. 保存为 `Chrome Debug.app`（建议存到 `~/Applications/` 或 `Applications` 内）。
6. 将 `Chrome Debug.app` 拖入 Dock，并将原有 Chrome 图标从 Dock 移除。
7. **验证**：点击新图标启动 Chrome，地址栏访问 `http://127.0.0.1:9222/json/version`，若看到 JSON 即表示调试端口已开启。

---

## 3. 方式二：命令行别名（可选）
将以下别名加入 `~/.zshrc` 或 `~/.bash_profile`：
```bash
alias chrome-debug='"${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/config/chrome-debug.sh"'
```
执行 `source ~/.zshrc` 后即可通过 `chrome-debug` 命令启动调试版 Chrome。

---

## 4. 方式三：替换系统快捷方式（可选）
1. 复制 `Chrome Debug.app` 到 `/Applications`（需管理员权限）。
2. 在 Finder 中选中原 `Google Chrome.app`，按 `Command+Delete` 移除 Dock 快捷方式（不会卸载应用）。
3. 将 `Chrome Debug.app` 重命名为 `Google Chrome.app` 并拖入 Dock。
4. 之后从 Dock、Spotlight、Launchpad 启动都会默认带上调试端口。

> 如果公司策略禁止替换系统应用，可仅在个人账户下保留 `Chrome Debug.app`，或通过别名方式启动。

---

## 5. 常见问题
- **如何恢复原始模式？**
  - 直接启动系统自带的 `/Applications/Google Chrome.app` 即可，或关闭 `Chrome Debug.app`。
- **如何确认脚本正在使用独立 profile？**
  - 首次启动会在 `~/.chrome-wf` 下创建新的 Chrome 用户数据目录，查看该目录是否生成即可。
- **端口被占用怎么办？**
  - 修改脚本中的 `PORT` 变量（9223、9333 等），并在 `wf.py` 中使用相同端口。
- **能否在多用户环境使用？**
  - 可以，每个用户执行一次上述步骤即可，互不影响。

---

完成以上配置后，Chrome 会在日常启动时自动打开调试端口；抓取脚本只需指定 `--remote-debug 127.0.0.1:9222` 即可接管，完全不影响正常浏览体验。
---

## 6. 新增优化功能 ✨

### 智能实例管理
- **问题**：每次点击Chrome Debug图标都会启动新的Chrome进程，导致资源浪费
- **解决方案**：优化脚本添加进程检测机制
- **效果**：
  - 首次点击：启动Chrome debug实例
  - 后续点击：仅打开新标签页到`chrome://newtab/`
  - 支持URL参数：`chrome-debug.sh "https://example.com"`

### 技术实现
```bash
# 进程检测机制
check_chrome_debug_running() {
    pgrep -f "remote-debugging-port=9222.*user-data-dir=${PROFILE_DIR}" >/dev/null 2>&1
}

# AppleScript控制新标签页
osascript -e "tell application \"Google Chrome\" to make new tab..."
```

---

## 进度与下一步

### ✅ 已完成
- [x] 提供 `config/chrome-debug.sh` 启动脚本并授予执行权限
- [x] 完成 Automator 应用、命令行别名与系统快捷方式的详细操作指南
- [x] **方式一验证完成**：Chrome Debug.app 成功创建并添加到Dock
- [x] **脚本优化完成**：智能实例管理，避免重复启动
- [x] **用户体验提升**：首次启动debug模式，后续仅打开新标签

### 🎯 下一阶段目标
- [ ] 将 `Chrome Debug.app` 打包/共享给团队并在 README 中补充链接
- [ ] 在 `wf.py` 文档更新中加入"默认以调试模式启动"的说明
- [ ] 集成到Web_Fetcher爬取架构优化方案中测试selenium接管功能

### 📊 配置状态
- **脚本路径**：`/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/config/chrome-debug.sh`
- **应用位置**：`/Applications/Chrome Debug.app`  
- **Dock集成**：✅ 已添加
- **调试端口**：9222
- **独立Profile**：`~/.chrome-wf`


