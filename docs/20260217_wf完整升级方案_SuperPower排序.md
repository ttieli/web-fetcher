# wf 完整升级方案 — V2 引擎 + SuperPower 排序

> 日期：2026-02-17（更新：V2 引擎切换方案）
> 基于前置分析：
> - `20260215_wf内容提取升级方案.md` — baoyu 对比分析 + 多策略竞赛设计
> - `20260216_竞赛机制在抓取层的适用性分析.md` — 抓取层适用性 + 实测 + 域名记忆方案
> - `tests/test_extraction_competition.py` — 竞赛独立测试脚本

---

## 一、V2 引擎切换方案

### 1.1 核心思路

在完全不影响现有逻辑（V1）的前提下，新增一套独立的 V2 解析引擎。通过 CLI 参数切换：

```bash
# V1（默认，当前所有逻辑不变）
wf "https://example.com"
wf fast "https://example.com"

# V2（新引擎：竞赛提取 + 质量检测 + 域名记忆）
wf v2 "https://example.com"
wf "https://example.com" --engine v2

# 将来测试成熟后，切换默认：
# V2 成为默认
wf "https://example.com"              # → V2
# V1 作为备选
wf "https://example.com" --engine v1  # → 老逻辑
```

### 1.2 可行性分析

**结论：完全可行。**

| 检查项 | 状态 | 说明 |
|--------|------|------|
| CLI 入口能否干净切换？ | ✅ | `cli.py` 按 `cmd` 分发（fast/full/raw/site），新增 `v2` 模式即可 |
| core.py 能否并存两套？ | ✅ | V2 解析逻辑放在独立文件，V1 的 `generic_to_markdown()` 不动 |
| argparse 冲突？ | ✅ | 新增 `--engine` 参数，默认 `v1`，不影响现有参数 |
| 抓取层需要改吗？ | ❌ | V2 复用现有的 `fetch_html_with_retry()`，只改**解析**后的流程 |
| 站点特化（微信/小红书）？ | ❌ | 微信和小红书已有专用解析器，V2 只替换 **generic** 路径 |

### 1.3 架构对比

```
V1（当前，不动）:
fetch_html_with_retry() → urllib/CDP/Selenium 降级
    ↓
parser 选择: WeChat / XHS / generic_to_markdown()
    ↓
generic: TemplateParser → trafilatura → legacy
    ↓
输出 markdown

V2（新增，并行存在）:
fetch_html_with_retry() → 完全复用 V1 抓取层
    ↓
parser 选择: WeChat / XHS / generic_v2()  ← 仅替换 generic 路径
    ↓
generic_v2:
├─ Step 0: 查询域名记忆 → 优先策略
├─ Step 1: TemplateParser（复用现有）
├─ Step 2: 多策略竞赛（trafilatura + readability + __NEXT_DATA__ + JSON-LD）
├─ Step 3: 评分选优
├─ Step 4: 质量检测 → 低分时触发 CDP 重试
├─ Step 5: 记录域名记忆 + 结构化日志
└─ 输出 markdown
```

**关键设计**：V2 只替换 `generic_to_markdown()` 的调用路径，微信和小红书解析器不受影响。

### 1.4 CLI 入口设计

#### 方式一：`wf v2` 子命令（推荐）

与现有 `wf fast` / `wf full` / `wf raw` 风格一致：

```python
# cli.py 新增分支（约 15 行）
elif cmd == 'v2':
    if len(raw_args) < 2:
        print("错误: v2模式需要提供URL")
        print("用法: wf v2 <URL> [输出目录]")
        sys.exit(1)
    url = _prepare_url('V2模式', raw_args[1])
    _prepare_and_run(webfetcher_module, url, raw_args[2:], stdout_mode,
                     extra_args=['--engine', 'v2'])
```

#### 方式二：`--engine` 参数

```python
# core.py argparse 新增（约 3 行）
ap.add_argument('--engine', choices=['v1', 'v2'], default='v1',
                help='Parsing engine: v1 (current), v2 (competition + memory) (default: v1)')
```

**两种方式并存**：`wf v2 URL` 等价于 `wf URL --engine v2`。

#### 后续默认切换

当 V2 测试成熟后，只需改一行：

```python
# 从
ap.add_argument('--engine', choices=['v1', 'v2'], default='v1', ...)
# 改为
ap.add_argument('--engine', choices=['v1', 'v2'], default='v2', ...)
```

此时 `wf URL` 默认走 V2，`wf URL --engine v1` 走老逻辑。

### 1.5 解析调度切换点

**core.py:5072-5076** 是唯一需要插入切换逻辑的位置：

```python
# 当前 V1 代码（不动）:
else:
    logging.info("Selected parser: Generic")
    parser_name = "Generic"
    date_only, md, metadata = generic_to_markdown(html, url, ...)

# 新增 V2 分支:
else:
    if getattr(args, 'engine', 'v1') == 'v2':
        logging.info("Selected parser: Generic V2 (competition engine)")
        parser_name = "Generic_V2"
        from webfetcher.parsing.engine_v2 import generic_v2
        date_only, md, metadata = generic_v2(
            html, url,
            fetch_metrics=fetch_metrics,
            url_metadata=url_metadata,
            args=args,
        )
    else:
        logging.info("Selected parser: Generic")
        parser_name = "Generic"
        date_only, md, metadata = generic_to_markdown(html, url, ...)
```

**影响范围**：core.py 仅改 5 行 if/else 判断。V1 路径零修改。

---

## 二、V2 引擎模块设计

### 2.1 文件结构

```
src/webfetcher/
├── parsing/
│   ├── templates.py          # V1 解析（不动）
│   ├── legacy.py             # V1 legacy（不动）
│   ├── engine_v2.py          # ← 新增：V2 引擎主入口
│   └── extractors.py         # ← 新增：多策略提取器 + 评分器
├── memory.py                 # ← 新增：域名记忆 + 结构化日志
├── core.py                   # 修改：+5 行 if/else 切换
└── cli.py                    # 修改：+15 行 v2 子命令
```

### 2.2 engine_v2.py 主流程

```python
"""V2 解析引擎 — 多策略竞赛 + 质量检测 + 域名记忆"""

def generic_v2(html: str, url: str, *,
               fetch_metrics=None, url_metadata=None, args=None
               ) -> tuple[str, str, dict]:
    """
    V2 通用解析器，返回值与 V1 的 generic_to_markdown() 完全兼容：
    (date_only, markdown_content, metadata)
    """
    from .extractors import run_competition, score_extraction
    from webfetcher.memory import DomainMemory, ExtractionLogger

    memory = DomainMemory()
    logger = ExtractionLogger()

    # Step 0: 查询域名记忆
    hint = memory.lookup(url)
    if hint and hint['confidence'] == 'high' and hint.get('needs_cdp'):
        # 已知需要 CDP 的域名，直接建议抓取层升级
        # （但不在这里触发，由 core.py 的调用方决定）
        pass

    # Step 1: TemplateParser（复用 V1）
    tp_result = _run_template_parser(html, url)
    if tp_result:
        return tp_result  # 站点特定模板命中，直接返回

    # Step 2: 多策略竞赛
    results = run_competition(html, url)
    best = results[0] if results else None

    # Step 3: 质量检测
    if best and best.score < 0.5:
        quality_low = True
        # 检测 SPA 特征
        if _is_spa_shell(html):
            # 标记需要 CDP 重试（由调用方处理）
            pass
    else:
        quality_low = False

    # Step 4: 构建输出（复用 V1 的 _build_generic_output）
    from .templates import _build_generic_output
    title = best.title if best else '未命名'
    content = best.content if best else ''
    date_only, md, metadata = _build_generic_output(
        title=title,
        author=best.author if best else '',
        publish_time=best.date if best else '',
        content=content,
        images=[],
        url=url,
        template_name=f'v2/{best.strategy}' if best else 'v2/none',
    )

    # Step 5: 记录域名记忆 + 日志
    fetcher = (url_metadata or {}).get('fetch_mode', 'urllib')
    memory.update(url, fetcher=fetcher,
                  extractor=best.strategy if best else 'none',
                  score=best.score if best else 0,
                  all_scores={r.strategy: r.score for r in results})
    logger.log(
        url=url, domain=memory.get_domain(url),
        fetcher=fetcher,
        fetch_ms=getattr(fetch_metrics, 'fetch_duration', 0) * 1000,
        extractor_results={r.strategy: {'score': r.score, 'chars': len(r.content)} for r in results},
        winner=best.strategy if best else 'none',
        winner_score=best.score if best else 0,
        quality_low=quality_low,
    )

    return date_only, md, metadata
```

### 2.3 extractors.py（提取器 + 评分器）

直接从已验证的 `test_extraction_competition.py` 提取核心代码：

| 函数 | 来源 | 说明 |
|------|------|------|
| `score_extraction()` | 测试脚本已验证 | 4 维评分器 |
| `extract_trafilatura()` | 测试脚本已验证 | 复用现有依赖 |
| `extract_readability()` | 测试脚本已验证 | readability-lxml 已安装 |
| `extract_next_data()` | 测试脚本已验证 | JSON 解析 |
| `extract_json_ld()` | 复用 legacy.py | 已有代码封装 |
| `run_competition()` | 测试脚本已验证 | 竞赛调度器 |

### 2.4 memory.py（域名记忆 + 日志）

直接使用前文设计的 `DomainMemory` + `ExtractionLogger`，详见 `20260216_竞赛机制在抓取层的适用性分析.md` 第八节。

---

## 三、SuperPower 排序（集成到 V2 引擎的实施顺序）

| Wave | 编号 | 功能 | SuperPower | V2 角色 |
|------|------|------|------------|---------|
| **1** | S4 | 评分器 | 20 | extractors.py 核心 |
| **1** | S2 | 域名记忆 | 20 | memory.py |
| **1** | S3 | 结构化日志 | 20 | memory.py |
| **1** | — | V2 引擎框架 | — | engine_v2.py + CLI 切换 |
| **2** | S1 | SPA 质量降级 | 20 | engine_v2.py 质量检测 |
| **3** | S5 | `__NEXT_DATA__` | 15 | extractors.py 新增策略 |
| **3** | S6 | JSON-LD 增强 | 15 | extractors.py 新增策略 |
| **4** | S8 | `wf stats` | 9 | cli.py 新增子命令 |
| **4** | S7 | readability | 8 | extractors.py 新增策略 |
| **5** | S9 | YAML front matter | 8 | engine_v2.py 输出选项 |
| **5** | S10 | 自动路由提升 | 6 | memory.py + cli.py |
| 默认切换 | — | V2 设为默认 | — | core.py 改 1 行 default |

---

## 四、完整改动矩阵

### Wave 1（V2 引擎基础 + 基础设施）

| 文件 | 类型 | 改动量 | 内容 |
|------|------|--------|------|
| `src/webfetcher/parsing/engine_v2.py` | **新增** | ~150 行 | V2 主入口 `generic_v2()` |
| `src/webfetcher/parsing/extractors.py` | **新增** | ~200 行 | 评分器 + 4 个提取器 + 竞赛调度 |
| `src/webfetcher/memory.py` | **新增** | ~150 行 | DomainMemory + ExtractionLogger |
| `src/webfetcher/core.py` | 修改 | **+5 行** | if/else 引擎切换（行 5072） |
| `src/webfetcher/cli.py` | 修改 | **+15 行** | `wf v2` 子命令 |
| `pyproject.toml` | 修改 | +1 行 | 添加 `readability-lxml` 依赖 |

**总计**：新增 3 个文件（~500 行），修改 3 个文件（~20 行改动）

### 不修改的文件

| 文件 | 说明 |
|------|------|
| `templates.py` | V1 解析逻辑完全不动 |
| `legacy.py` | V1 legacy 完全不动 |
| `routing.yaml` | 路由配置不动 |
| `template_parser.py` | 模板引擎不动（V2 复用） |
| 所有 YAML 模板 | 站点模板不动 |

### 运行时新增文件

| 文件 | 说明 |
|------|------|
| `~/.config/webfetcher/domain_memory.json` | 域名策略记忆（自动生成） |
| `~/.config/webfetcher/extraction_log.jsonl` | 结构化日志（自动追加） |

---

## 五、演进路线

```
Phase A: V2 引擎上线（默认关闭）
├─ 实现 Wave 1 全部内容
├─ wf v2 URL 可用
├─ wf URL 仍走 V1（零影响）
└─ 开始积累域名记忆数据

Phase B: V2 补充策略
├─ 实现 Wave 2-3（SPA 检测 + __NEXT_DATA__ + JSON-LD）
├─ 用 wf v2 跑更多测试 URL
└─ 对比 V1 vs V2 提取质量

Phase C: V2 成为默认
├─ core.py: default='v1' → default='v2'
├─ wf URL 默认走 V2
├─ wf URL --engine v1 走老逻辑
└─ 观察一段时间后移除 V1 代码（可选）

Phase D: 持续优化
├─ wf stats CLI
├─ 自动路由提升
└─ 评分权重调优
```

### 默认切换时间线（建议）

| 阶段 | 触发条件 | 操作 |
|------|----------|------|
| 上线 | Wave 1 完成 | `wf v2` 可用 |
| 测试 | 50+ URL 测试对比 | 收集 V1 vs V2 数据 |
| 切换 | V2 在 80%+ URL 上 ≥ V1 | 改 default 为 v2 |
| 清理 | 切换后 30 天无回退 | 可选移除 V1 代码 |

---

## 六、风险控制

| 风险 | 缓解措施 |
|------|----------|
| V2 有 bug 影响用户 | 默认 V1，V2 需手动 `--engine v2` 才启用 |
| V2 性能退化 | 竞赛仅跑纯内存操作（<100ms），不增加网络请求 |
| V2 评分器偏差 | 评分器已在 test_extraction_competition.py 实测验证 |
| domain_memory.json 损坏 | 文件不存在/损坏时 graceful fallback 到正常流程 |
| readability-lxml 依赖冲突 | 已测试安装成功，依赖 lxml（已有） |
| 切换 V2 默认后 V1 回退 | `--engine v1` 永久可用 |

---

## 七、一句话总结

**新增 `wf v2` 命令（和 `--engine v2` 参数），启用竞赛提取 + 质量检测 + 域名记忆的新引擎。V1 完全不动，默认不变。等 V2 验证成熟后，改一行代码切换默认。**
