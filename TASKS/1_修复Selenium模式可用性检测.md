# 1.修复Selenium模式可用性检测

## 背景
- 当前 `webfetcher.py:829-907` 在 `-s/--fetch-mode selenium` 下仍可能误报 "Selenium integration not available"，并在失败后返回空字符串继续执行。
- `SELENIUM_AVAILABLE` 虽已恢复为 `True`，但流程缺少对 Chrome 调试端口、权限失败等情况的准确区分。

## 目标
- 当 Selenium 依赖齐备且 Chrome 调试会话正常时，`-s` 模式应成功抓取页面。
- 若 Selenium 无法使用，应直接返回明确错误（终端输出 + 非零退出码），而不是生成空内容。

## 验收标准
1. 在已启动 `./config/chrome-debug.sh` 的情况下运行 `./wf.py -s <URL>` 成功抓取并输出内容。
2. 当 Chrome 调试端口不可用时，命令行输出包含启动调试会话的指导，并以退出码 1 结束。
3. 当 Selenium 包缺失时，提示安装命令 `pip install -r requirements-selenium.txt`，同时退出码为 1。
4. 自动模式下，当 urllib 失败而 Selenium 可用时，会正确走到 Selenium 分支并尝试连接。

## 实施步骤
1. **可用性检测**：在 `webfetcher.py` 的 Selenium 分支中区分「依赖缺失」「Chrome 未启动」「权限错误」三种情况，确保各自的错误信息与日志准确。
2. **错误传播**：调整 `_try_selenium_fetch`，在失败时抛出自定义异常或返回显式错误状态，由调用方决定输出与退出码。
3. **命令行反馈**：在 `wf.py` 处理 Selenium 模式的入口，捕获上述错误并打印友好提示，同时返回非零退出码。
4. **测试验证**：编写或更新现有手动/自动脚本，覆盖成功与失败两类情景，确认 `FetchMetrics` 中的 `final_status` 与终端行为一致。

## 备注
- 依赖 `selenium_fetcher.py` 现有的版本检测与调试端口检查逻辑，无需额外改动。
- 完成后再评估是否需要加入 macOS Developer Tools 权限提示。
