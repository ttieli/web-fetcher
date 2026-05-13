# 项目状态

## 当前版本：1.3.4

## 当前活跃管线

无（chain 1 已完成 + 1.3.3/1.3.4 后续修复 + 公有 repo 清理已推送）

## 最近完成

### 2026-05-13 · 1.3.4 公有 repo 清理 + history 重写 + force push

- 删除 `tests/url_suite.txt` 中 4 个含工作查询关键词的搜索 URL
- 扩展 `.gitignore`：sample/、备份文件、机器特定脚本、`.claude/` 个人配置
- 入库公共工具：routing_schema.json、routing_ctl.py、template_tool.py、run_regression_suite.py
- `git filter-repo` 重写全 340 commits 抹去 `/Users/tieli/...iCloud...` 路径
- `git push --force origin main` 推送，远端 history 验证完全干净
- commit: e98e5b9

### 2026-05-13 · 1.3.3 补 git 状态修复

- `src/webfetcher/memory.py` 入库（V2 引擎核心依赖）
- `apply_yaml_frontmatter()` 入库（`--frontmatter yaml` 实现）
- qcc YAML 类型修正 + routing 日志降噪
- commit: 386e581

### chain 1 · 2026-05-13 · V2 fallback 机制修复（→ 1.3.2）

- 管线：superpower-chain Pipeline A · enhanced · semi-auto
- 范围：修复 wf 工具 V2 自动升级 fallback 三处联动缺陷
- 版本：1.3.0/1.3.1 → 1.3.2
- 测试：11 unit tests + 18 V2 行为验证（short-circuit 2/2 + spa-stuck 8/8 + fallback-rescue 8/8）+ 3 E2E
- 归档：
  - `docs/80_归档/bug-fixes/20260513_wf_V2_fallback机制三处缺陷.md`
  - `docs/80_归档/bug-fixes/20260513_wf_V2_fallback修复方案.md`

**修复要点**：
- Bug 1（core.py）：升级判定从 HTML 长度改为提取 score
- Bug 2（engine_v2.py）：质量字段写入解耦 `_v2_no_upgrade`
- 问题 3（extractors.py）：plain-text URL 短路 + `<pre>`-wrapped raw markdown 解包

**E2E 验证**：
- ✅ raw github CHANGELOG → 短路（无 CDP 调用）
- ✅ carnoc → urllib(0) → cdp(0.75) → break
- ✅ interconnects.ai/archive → urllib → cdp → selenium → manual_chrome（之前永久卡在 cdp）

## 回归测试体系

| 工具 | 命令 | 用途 |
|------|------|------|
| 单元测试 | `pytest tests/unit/` | 11 个用例，1.5s |
| smoke 回归 | `python3 scripts/run_regression_suite.py --tags fast` | 13 URL，29s |
| 完整 suite | `python3 scripts/run_regression_suite.py` | 29 URL，~5min |
| V2 行为验证 | `python3 scripts/verify_v2_fallback.py --tags <cat>` | 按类别断言升级链/短路 |
| Suite 重建 | `python3 scripts/build_regression_suite.py > tests/url_suite.txt` | 从历史日志生成 |

## 历史记录

完整 chain 历史见 `docs/0_chain/history.md`；详细文档见 `docs/80_归档/`。
