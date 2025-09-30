# 2_新增Chrome调试守护脚本
# Introduce Chrome Debug Guard Script

## 任务目标 / Objective
- 保持现有 `config/chrome-debug.sh` 的手动复用行为不变。
- 新增后台启动脚本，缺省情况下自动确保 `--remote-debugging-port=9222` 的 Chrome 调试实例存在。

## 完成标准 / Acceptance Criteria
1. 新增 `config/chrome-debug-launcher.sh`，若未检测到调试实例，可在后台启动 Chrome，并输出 PID 记录；若失败需返回非零状态。  
   `config/chrome-debug-launcher.sh` launches Chrome in background when debug instance is absent, records PID, and returns non-zero on failure.
2. 新增 `config/ensure-chrome-debug.sh`，先检测 9222 端口，若未运行则调用 launcher，并在可配置的等待时间内轮询 `http://localhost:9222/json/version` 直至成功或超时。  
   `config/ensure-chrome-debug.sh` checks port 9222, invokes the launcher if needed, and polls `/json/version` until ready or timeout.
3. 若检测或启动因 macOS 权限被拦截，脚本需输出提示（例如授权开发者工具、AppleScript），并返回错误码。  
   When macOS permissions block startup, the script prints guidance (Developer Tools, AppleScript) and exits with error.
4. 自动流程（如 `wf -s`）可调用 `ensure-chrome-debug.sh` 并在调试实例就绪后继续执行。  
   Automated flows (e.g., `wf -s`) rely on `ensure-chrome-debug.sh` to guarantee the debug instance before proceeding.

## 架构评审结果 / Architecture Review Result

✅ **方案合理，需补充细节** - 整体方案可行，需要增加并发控制和异常处理机制

**需要补充的内容 / Additional Requirements:**
1. PID文件的清理机制
2. Chrome异常退出的处理
3. 并发启动的锁机制

## 实施步骤 / Implementation Steps

### Phase 1: 创建启动器脚本 [1.5小时]

**文件变更清单 / File Changes:**
```
新增文件 / New Files:
├── config/chrome-debug-launcher.sh    # Chrome后台启动脚本
├── config/ensure-chrome-debug.sh      # Chrome调试保障脚本
└── ~/.chrome-wf/.chrome-debug.lock    # 进程锁文件（运行时生成）

修改文件 / Modified Files:
├── wf.py
│   └── Selenium分支: 添加ensure-chrome-debug.sh调用
└── selenium_fetcher.py
    └── 行386-434: 增强Chrome连接重试逻辑
```

**1. chrome-debug-launcher.sh实现规范:**
```bash
#!/bin/bash
# 位置：config/chrome-debug-launcher.sh
# 功能：后台启动Chrome调试实例

# 接口定义：
# 输入：无
# 输出：成功返回0，失败返回非0
# 副作用：
#   - 启动Chrome进程
#   - 写入PID到~/.chrome-wf/chrome-debug.pid
#   - 创建锁文件防止并发

# 核心逻辑（伪代码）：
# 1. 使用flock获取排他锁
# 2. 检查现有PID文件和进程
# 3. 清理僵尸PID
# 4. 启动Chrome：
#    open -a "Google Chrome" --args \
#      --remote-debugging-port=9222 \
#      --user-data-dir=~/.chrome-wf \
#      --no-first-run \
#      --no-default-browser-check
# 5. 记录PID并验证
```

### Phase 2: 创建保障脚本 [2小时]

**2. ensure-chrome-debug.sh实现规范:**
```bash
#!/bin/bash
# 位置：config/ensure-chrome-debug.sh
# 功能：确保Chrome调试实例可用

# 接口定义：
# 输入参数：
#   -t TIMEOUT  等待超时秒数（默认10）
#   -p PORT     调试端口（默认9222）
# 输出：成功返回0，失败返回非0

# 核心功能实现：
# 1. 快速检测（0.1秒超时）：
#    curl -s --max-time 0.1 http://localhost:9222/json/version
#
# 2. 如果未运行，调用launcher：
#    ./chrome-debug-launcher.sh
#
# 3. 健康检查循环（20次，每次0.5秒）：
#    for i in {1..20}; do
#      if curl -s http://localhost:9222/json/version; then
#        echo "Chrome debug ready"
#        exit 0
#      fi
#      sleep 0.5
#    done
#
# 4. 错误处理：
#    - 权限错误 → 输出macOS设置指南
#    - 超时 → 输出诊断信息
#    - 端口占用 → 提示进程冲突
```

**3. 权限错误处理模板:**
```bash
# 检测到权限错误时输出：
echo "❌ Chrome启动失败：权限被拒绝"
echo ""
echo "请按以下步骤启用权限："
echo "1. 打开 系统设置 → 隐私与安全 → 开发者工具"
echo "2. 启用 Terminal 或 iTerm"
echo ""
echo "或运行以下命令："
echo "  sudo DevToolsSecurity -enable"
echo ""
echo "完成后重新运行此命令"
exit 1
```

### Phase 3: 集成与测试 [1.5小时]

**修改wf.py集成点:**
```python
# 位置：wf.py中的Selenium分支
# 伪代码示例：
if args.selenium:
    # 新增：确保Chrome调试实例
    import subprocess
    result = subprocess.run(
        ['./config/ensure-chrome-debug.sh', '-t', '15'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("Failed to ensure Chrome debug instance")
        print(result.stderr)
        sys.exit(1)

    # 继续原有Selenium逻辑
    selenium_fetcher = SeleniumFetcher(config)
    # ...
```

**测试验证方案:**
```bash
# 测试场景1：Chrome未运行时自动启动
pkill -f "remote-debugging-port=9222"
./config/ensure-chrome-debug.sh
echo "Exit code: $?"
# 预期：启动Chrome，返回0

# 测试场景2：Chrome已运行时快速通过
./config/chrome-debug.sh  # 先手动启动
./config/ensure-chrome-debug.sh
echo "Exit code: $?"
# 预期：立即返回0

# 测试场景3：集成测试
python wf.py -s https://example.com
# 预期：自动启动Chrome（如需要），完成抓取

# 测试场景4：并发安全测试
./config/ensure-chrome-debug.sh &
./config/ensure-chrome-debug.sh &
wait
# 预期：只启动一个Chrome实例
```

## 注意事项 / Notes
- 现有 `config/chrome-debug.sh` 不做任何修改；手动启动习惯保持不变。  
  Keep `config/chrome-debug.sh` untouched for manual workflows.
- 新脚本需考虑路径中包含空格的情况（建议使用绝对路径或引用）。  
  Handle spaces in paths (prefer absolute paths or quoting).
- 若未来引入 Playwright 等新引擎，可复用 `ensure-chrome-debug.sh` 的检测逻辑。  
  Future engines (e.g., Playwright) can reuse the detection logic.
