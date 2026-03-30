# wf 多策略内容提取需求

> 来源：Skills-Factory `20260215_url-to-markdown-vs-wf对比分析.md`
> 日期：2026-02-20（需求转移）
> 注意：本项目 docs/ 下已有详细升级方案（20260215-20260217），本文仅为需求索引

---

## 背景

对比 baoyu-url-to-markdown 和 wf，发现 wf 在抓取、站点适配、输出格式上全面领先，但**内容提取**（HTML → 正文）这一环 baoyu 更强——6 种提取策略竞赛打分，而 wf 主要依赖 trafilatura 单引擎。

## 需求清单（按优先级）

| 优先级 | 需求 | 说明 | 已有方案 |
|--------|------|------|---------|
| P1 | 多策略内容提取 | readability + trafilatura 竞赛，多引擎打分选最优 | `20260215_wf内容提取升级方案.md` |
| P1 | Next.js `__NEXT_DATA__` 提取器 | 从 SSR JSON 数据直接提取，比解析 DOM 更干净 | `20260215_wf内容提取升级方案.md` |
| P2 | JSON-LD 结构化数据提取 | 提取 Schema.org articleBody | 同上 |
| P2 | YAML front matter 输出选项 | `--frontmatter yaml`，Hugo/Jekyll/Obsidian 通用格式 | 未设计 |
| P3 | Readability 双模式 | 严格模式内容不足时回退宽松模式 | 同上 |

## 关联文档

本项目已有的相关升级方案：
- `20260215_wf内容提取升级方案.md` — baoyu 对比 + 多策略竞赛设计
- `20260216_竞赛机制在抓取层的适用性分析.md` — 抓取层适用性 + 域名记忆方案
- `20260217_V2引擎测试报告.md` — V2 引擎测试
- `20260217_wf完整升级方案_SuperPower排序.md` — V2 引擎 + SuperPower 排序
