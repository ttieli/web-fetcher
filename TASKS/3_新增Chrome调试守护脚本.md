# 4.新增Chrome调试守护脚本
# 4. Introduce Chrome Debug Guard Script

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

## 实施步骤 / Implementation Steps
1. **检测逻辑 / Detection**  
   - 在 `ensure-chrome-debug.sh` 中复用 `pgrep -f "remote-debugging-port=9222"` 或 `curl /json/version` 来判断调试实例是否存在。  
   - Use `pgrep -f "remote-debugging-port=9222"` or `curl /json/version` inside `ensure-chrome-debug.sh` to detect active debug sessions.

2. **后台启动 / Background Launch**  
   - `chrome-debug-launcher.sh` 通过 `nohup ".../Google Chrome" --remote-debugging-port=9222 --user-data-dir=~/.chrome-wf &` 或 `open -a "Google Chrome" --args ...` 启动，并把 PID 写入 `~/.chrome-wf/chrome-debug.pid`。  
   - Launch Chrome via `nohup ".../Google Chrome" --remote-debugging-port=9222 --user-data-dir=~/.chrome-wf &` or `open -a "Google Chrome" --args ...`, storing PID in `~/.chrome-wf/chrome-debug.pid`.

3. **状态轮询 / Readiness Polling**  
   - 启动后在 `ensure-chrome-debug.sh` 中循环检查 `/json/version`，默认重试 10 秒（0.5 秒间隔）；成功则输出 "Chrome debug ready"，超时则给出失败原因。  
   - Poll `/json/version` for up to ~10 seconds (0.5s interval); print success or timeout message accordingly.

4. **权限处理 / Permissions Handling**  
   - 捕获 AppleScript 或 Developer Tools 相关错误，提示用户开启“系统设置 → 隐私与安全 → 开发者工具”或运行 `sudo DevToolsSecurity -enable`。  
   - Catch AppleScript/Developer Tools failures and guide the user to enable permissions (System Settings → Privacy & Security → Developer Tools or `sudo DevToolsSecurity -enable`).

5. **集成与验证 / Integration & Validation**  
   - 在 `wf.py` 的 Selenium 分支调用新脚本，按任务 1 的逻辑处理错误与退出码。  
   - 运行三种测试场景：已有实例、自动启动成功、权限受阻。记录日志并确保终端输出清晰。  
   - Invoke the new script from Selenium workflow (task 1). Test three scenarios: already running, auto-start success, permission blocked.

## 注意事项 / Notes
- 现有 `config/chrome-debug.sh` 不做任何修改；手动启动习惯保持不变。  
  Keep `config/chrome-debug.sh` untouched for manual workflows.
- 新脚本需考虑路径中包含空格的情况（建议使用绝对路径或引用）。  
  Handle spaces in paths (prefer absolute paths or quoting).
- 若未来引入 Playwright 等新引擎，可复用 `ensure-chrome-debug.sh` 的检测逻辑。  
  Future engines (e.g., Playwright) can reuse the detection logic.
