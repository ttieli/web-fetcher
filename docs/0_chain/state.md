# Superpower Chain State · 当前活跃 chain

> **协议（立规 #54）**：本文件仅含当前活跃 chain · 已完结 chain 索引在 `docs/0_chain/history.md` · 详细产物在 `docs/80_归档/`。

## 当前活跃 chain：chain 1

## 基本信息

| 字段 | 值 |
|------|-----|
| 管线类型 | bug-fix |
| 项目路径 | . |
| 创建时间 | 2026-05-13 09:48 |
| 模式 | semi-auto |
| 版本 | enhanced |
| 当前步骤 | A9_QUEUE_CONSUME |
| heartbeat | 1778639018 |
| lease_ttl | 600 |
| 构建命令 | python -m py_compile src/webfetcher/core.py src/webfetcher/parsing/engine_v2.py src/webfetcher/parsing/extractors.py |
| 测试命令 | pytest tests/ -x |
| TDD 模式 | true |

## 步骤状态

| # | 步骤 | 状态 | 完成时间 | 产出物 |
|---|------|------|----------|--------|
| A1 | 问题记录 | ✅ | 2026-05-13 09:50 | docs/10_分析/20260513_wf_V2_fallback机制三处缺陷.md |
| A2 | 问题分析 | ✅ | 2026-05-13 09:52 | docs/10_分析/20260513_wf_V2_fallback机制三处缺陷.md（根因+证据矩阵+修法选型已写入） |
| A3 | 根因确认评审 | ✅ | 2026-05-13 09:55 | 评审记录追加在问题文档末尾（3 专家 / 根因 100% 通过 / 5 项细化转交 A4） |
| A4 | 修复方案 | ✅ | 2026-05-13 10:00 | docs/20_设计/20260513_wf_V2_fallback修复方案.md（4 Task / 17 Step / TDD 编排） |
| A5 | 方案评审 | ✅ | 2026-05-13 10:08 | 评审记录追加在方案文档末尾（Round 1: 🟡 7 项行动 → Round 1.5 修补全部落实 → 进 A6） |
| A6 | 代码实施 | ✅ | 2026-05-13 10:21 | 4 commits (07dd9a2/b73a30e/ca3e153/711c81c) · 11 unit tests PASS · 3 E2E PASS（raw github 短路/carnoc 救回/interconnects 完整升级链） |
| A7 | 版本 Bump | ✅ | 2026-05-13 10:22 | 1.3.0/1.3.1 → 1.3.2 (pyproject.toml + __init__.py + core.py 同步) + CHANGELOG · commit b395c54 |
| A8 | 归档 | ✅ | 2026-05-13 10:23 | 2 docs → docs/80_归档/bug-fixes/ · docs/status.md + 0_chain/history.md 新建 · project-memory.md 注入 superpower-chain |
| A9 | 队列消费 | 🔄 | - | - |

## 目录映射

| 用途 | 实际目录 |
|------|----------|
| 问题/需求 | docs/10_分析/ |
| 设计方案 | docs/20_设计/ |
| 实施方案 | docs/30_计划/ |
| 归档 | docs/80_归档/ |

## 文档索引

| 类型 | 路径 |
|------|------|
| 问题/需求文档 | docs/10_分析/20260513_wf_V2_fallback机制三处缺陷.md |
| 设计方案 | docs/20_设计/20260513_wf_V2_fallback修复方案.md |
| 实施方案 | - (Bug 修复无独立实施方案，复用 A4 方案) |
| 评审记录 | 内嵌在对应文档中 |
| 增强 Skill 产出 | {} |

## 预检动作

- mkdir docs/0_chain/
- 检测到 .claude/project-memory.md 替代 CLAUDE.md（符合用户全局规则）
- 复用既有方案 C 目录结构（10_分析 / 20_设计 / 30_计划 / 80_归档）

## 恢复上下文

**本次 chain 目标**：修复 wf 工具 V2 自动升级 fallback 机制的 3 个问题（来自 2026-05-13 上下游会话的根因定位）。

**已定位的核心 Bug**：
- Bug 1（核心）：`src/webfetcher/core.py:5661,5676` 升级成功用 `len(html2) > len(html)` 判定，SPA 站点骨架 HTML 长但低分会卡死
- Bug 2（联动）：`src/webfetcher/parsing/engine_v2.py:130` 与 `core.py:5666-5673` 的 `_v2_quality_low` 标志在重抓时永远不会重新设置，导致"重抓后质量仍差就继续升级"失效
- 问题 3：`src/webfetcher/parsing/extractors.py` 评分器对 plain markdown 不友好（raw .md 文件被误判 quality_low）

**验收标准**：
1. 30 条历史失败 URL 至少救回 5 条（score>=0.5）
2. SPA 站点（wgetcloud、tianyancha、interconnects）必须能继续升 selenium
3. raw markdown URL 不触发不必要升级
4. 单元测试覆盖 Bug 1 + Bug 2

**关键资源**：
- 抓取日志：`~/.config/webfetcher/extraction_log.jsonl`（370 条历史数据）
- 已知 git 未提交修改：`templates.py`、`config_loader.py`、`qcc_com template.yaml`（与本次 chain 无关，不动）

**A3 评审 5 项行动（A4 方案必须 100% 落实）**：
1. Bug 1 修法：`new_score = score_extraction(new_html_extraction)`，html2 空/解析空 → continue；new_score >= prev_score → 接受换 fetcher；接受后 new_score >= 0.5 → break，否则继续升下一级
2. Bug 2 修法：engine_v2.py:144-147 中 `_v2_score`、`_v2_quality_low`、`_v2_current_fetcher` 三个**质量描述字段**移到 `if quality_low and not _v2_no_upgrade:` 块**外面**；只保留 `_v2_needs_upgrade` 在 if 内
3. 问题 3 三层防御：URL 后缀（.md/.txt/.rst）+ 路径匹配（raw.githubusercontent.com/gist.githubusercontent.com） + Content-Type 命中 + 兜底纯文本评分分支
4. 回归测试覆盖：interconnects.ai/archive、wgetcloud/user/shop、tianyancha/search → 应升 selenium；raw github CHANGELOG → 应短路 score >= 0.6
5. out-of-scope：`_v2_score` 公开化、fetcher budget 重设计 → 独立 issue 不在本次
