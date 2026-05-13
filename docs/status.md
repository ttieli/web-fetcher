# 项目状态

## 当前活跃管线

无（chain 1 已完成）

## 最近完成

### chain 1 · 2026-05-13 · V2 fallback 机制修复

- 管线：superpower-chain Pipeline A · enhanced · semi-auto
- 范围：修复 wf 工具 V2 自动升级 fallback 三处联动缺陷
- 版本：1.3.0/1.3.1 → 1.3.2
- 提交：07dd9a2 / b73a30e / ca3e153 / 711c81c / b395c54（5 个 commits）
- 测试：11 unit tests PASS + 3 E2E PASS
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

## 历史记录

完整 chain 历史见 `docs/0_chain/history.md`（如有）；详细文档见 `docs/80_归档/`。
