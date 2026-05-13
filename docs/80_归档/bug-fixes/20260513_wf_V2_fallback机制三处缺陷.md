# wf V2 自动升级 fallback 机制三处缺陷

> 创建时间：2026-05-13 09:48
> 管线：superpower-chain Pipeline A · chain 1 · enhanced
> 状态：分析中
> 报告者：通过 ~/.config/webfetcher/extraction_log.jsonl 370 条日志统计 + 源码追踪发现

## 现象

V2 自动升级 fallback（urllib → cdp → selenium → manual_chrome）在以下三类场景失效：

1. **SPA 站点长 HTML 卡死在 cdp**：CDP 渲染后 HTML 比 urllib 长（因为 JS 注入了骨架），但提取出的正文分数仍然低（0.3~0.5），系统认为升级"成功"并 break，**不再继续升级到 selenium**
2. **重抓质量复检失效**：升级后即使重抓内容仍然差，永远不会触发"再升一级"的逻辑
3. **plain markdown 文件被误判**：直接抓 raw markdown 文件（如 GitHub raw CHANGELOG），评分器把纯文本评低分（< 0.5），触发不必要的升级，但 CDP 升级也救不回

## 复现条件

**环境**：
- macOS Darwin 25.5.0
- webfetcher 1.3.0
- Python 3.x + trafilatura + readability
- CDP fetcher 可用（headless Chrome on port 9222）

**典型复现 URL（从历史日志取）**：

| URL | 升级路径 | 终态 score | 终态状态 |
|-----|----------|-----------|---------|
| https://b8cfff2a4jquxdbmwbaj.wgetcloud.org/user/shop | cdp → cdp | 0.39 → 0.39 | 卡死 |
| https://www.tianyancha.com/search?key=... | urllib → cdp | 0.41 → 0.39 | 卡死 |
| https://www.interconnects.ai/archive | urllib → cdp | 0.45 → 0.45 | 卡死 |
| https://www.qcc.com/search?key=... | urllib → cdp | 0.00 → 0.29 | 卡死 |
| https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md | cdp | 0.42（chars=292712）| 误判触发升级 |

**复现步骤**：
1. `wf "https://www.interconnects.ai/archive" --stdout`
2. 期望：urllib → cdp 后继续升 selenium 拿到列表正文（或至少标识真实失败）
3. 实际：urllib quality_low → 升 cdp → cdp HTML 更长 → break，停止升级链
4. 日志中：`V2 auto-upgrade success: cdp` 但实际 score 仍 0.45

## 相关日志

`~/.config/webfetcher/extraction_log.jsonl` 全量统计（since 2026-04-01）：
- 总请求组 323
- 多次尝试（触发过升级）39
- **终态仍失败 30 条**
- 其中 15+ 条是"长但低分"的 SPA 站点
- 1 条是 raw markdown 误判（CHANGELOG.md）

## 影响范围

- **受影响功能**：wf CLI 抓取所有 SPA 风格站点（搜索结果页、列表页、JS 渲染内容站）
- **受影响调用方**：依赖 wf 的上游服务（claude-in-chrome 后端、其他自动化脚本）
- **严重程度**：**P1 严重** —— 不影响主干（80%+ 静态站正常），但每个 SPA 站点都踩坑，且无明显错误提示，用户感觉"wf 抓出来内容很烂"

---

## 根因分析（A2 填写）

### Bug 1 · 升级判定标准错误

**位置**：`src/webfetcher/core.py:5661,5676`

**代码**：
```python
# core.py:5661
if html2 and len(html2) > len(html):
    html = html2
    fetch_metrics = fm2
    url_metadata = um2
    args._v2_no_upgrade = True
    date_only, md, metadata = generic_v2(
        html, url, url_metadata=url_metadata, args=args)
    args._v2_no_upgrade = False
    logging.info(f"V2 auto-upgrade success: {next_mode}, "
                 f"HTML={len(html)} chars")
    # 质量已经改善，停止升级
    if not metadata.get('_v2_quality_low'):
        break
else:
    logging.warning(f"V2 auto-upgrade: {next_mode} "
                    f"returned {len(html2) if html2 else 0} chars "
                    f"(not better than {len(html)}), trying next")
```

**问题**：
1. 升级"成功"的判定用 **HTML 字符数** `len(html2) > len(html)`，而不是 **提取质量 score**
2. SPA 站点 CDP 渲染后 HTML 长度通常会涨（JS 骨架 + 数据），即使提取出来还是空骨架，也会进入 `if` 分支
3. 进入 if 分支后调 `generic_v2` 重抓解析（第 5667 行），由于 `args._v2_no_upgrade=True`，无法重置 `_v2_quality_low`（见 Bug 2）
4. 第 5673 行 `if not metadata.get('_v2_quality_low'): break` 永远为真 → break，不再升 selenium

**证据链**：
- `wgetcloud/user/shop`：日志显示 cdp → cdp 0.39→0.39，但 HTML 应该都涨了，所以进 if 分支 break
- `tianyancha/search`：urllib(0.41) → cdp(0.39)，CDP HTML 长但 score 反而降，仍然 break
- `interconnects.ai/archive`：urllib(0.45) → cdp(0.45)，分数没变，但 HTML 长了就接受

### Bug 2 · `_v2_quality_low` 永远不会被重新设置

**位置**：`src/webfetcher/parsing/engine_v2.py:130` + `core.py:5666-5673`

**代码（engine_v2.py:128-160）**：
```python
# 质量差时：返回升级信号（而非直接回退 legacy）
if quality_low and not getattr(args, '_v2_no_upgrade', False):
    upgrade_chain = {'urllib': 'cdp', 'cdp': 'selenium', ...}
    next_fetcher = upgrade_chain.get(current_fetcher)
    if next_fetcher:
        ...
        metadata['_v2_quality_low'] = True
        metadata['_v2_needs_upgrade'] = next_fetcher
        ...
        return date_only, md, metadata
```

**问题**：
1. `_v2_quality_low=True` 只在 `quality_low and not args._v2_no_upgrade` 同时满足时才会被设置
2. core.py 升级重抓前显式设 `args._v2_no_upgrade=True`（第 5666 行），目的是防止 generic_v2 内部触发二次升级
3. 但副作用：重抓后的 metadata 里**永远没有** `_v2_quality_low` 字段
4. 因此 core.py:5673 的 `if not metadata.get('_v2_quality_low'): break` 永远 True，第一次升级"看起来 HTML 变长"就 break

**联动效应**：Bug 1 + Bug 2 共同导致 fallback 链实际只能升一级。

### 问题 3 · 评分器对 plain markdown 不友好

**位置**：`src/webfetcher/parsing/extractors.py`（评分函数 `score_extraction`）

**问题**：
1. raw markdown 文件（`.md`、`.txt`、`raw.githubusercontent.com/.../*.md`）没有 HTML 结构
2. 评分函数基于 HTML 结构特征（段落标签、标题密度等）→ 纯文本 score 偏低
3. CHANGELOG.md 实测 chars=292712 但 score=0.425，触发升级
4. CDP 渲染纯文本和 urllib 没差别 → 升级救不回 → 浪费一次 CDP 调用

### 补充证据：评分函数对 plain markdown 不友好的具体机制

`extractors.py:30-77` `score_extraction()` 的 4 个评分因子：

| 因子 | 权重 | 对 plain markdown 的表现 |
|------|------|--------------------------|
| 长度分 | 30% | 长 markdown 满分 1.0 → 贡献 0.30 |
| 结构分 | 25% | markdown 自带 `##`/`- `/`\|`/```` 标签 → 通常满分 1.0 → 贡献 0.25 |
| 噪音分 | 25% | 长文档中容易出现 nav/menu/cookie 等噪音词 → 衰减到 0.4~0.6 |
| 段落质量 | 20% | markdown 段落平均长度通常 >300 字符 → 评分掉到 0.5~0.7 |

CHANGELOG.md 实测：长度+结构 = 0.55，噪音 0.10，段落 0.18 → 总 0.43。
即长 markdown 文档因为段落过长 + 偶现噪音词，**结构上不会触达 0.5 阈值**，被误判 quality_low。

trafilatura 本身处理 raw markdown 时是"原样输出"，CDP/selenium 渲染纯文本和 urllib 完全一样，所以升级注定救不回。

### 跨文件证据矩阵

| 现象 | 涉及文件 | 关键行号 | 类型 |
|------|---------|---------|------|
| 升级判定用 HTML 长度 | core.py | 5637, 5661, 5675 | Bug 1 主因 |
| `_v2_no_upgrade` 阻塞 `_v2_quality_low` 写入 | engine_v2.py | 130, 144 | Bug 2 主因 |
| 升级 break 依赖 `_v2_quality_low` | core.py | 5673 | Bug 1+2 联动点 |
| 评分函数对 plain text 不宽容 | extractors.py | 30-77 | 问题 3 主因 |
| 竞赛驱动入口（不区分输入类型） | extractors.py | 276-317 | 问题 3 触发点 |

### 修复方向论证

**Bug 1 修法选型**：
- 候选 A：完全用 score 判定升级（删除 `len(html2) > len(html)`）
  - 风险：fetch 层失败时 html2 可能为 None/空字符串 → score 必然降为 0，仍走 else 分支，OK
  - 但需要在 score 比较前确保 html2 至少能解析（非完全失败）
- 候选 B：保留长度作为兜底，主判定用 score
  - `if html2 and (new_score > prev_score OR len(html2) > 2*len(html))` —— 长度变化幅度大也接受
  - 过于复杂，不推荐
- **推荐 A**：`new_score = score_extraction_of(html2)`，如果 `new_score > prev_score + 0.05`（margin 防抖）才接受升级；如果接受后 `new_score >= 0.5`，认为质量改善，break；否则继续下一级

**Bug 2 修法选型**：
- 候选 A：把"本轮 quality_low 状态"总是写入 metadata（独立字段如 `_v2_score` + `_v2_quality_low`），不被 `_v2_no_upgrade` 影响
- 候选 B：保留 `_v2_no_upgrade` 阻塞返回升级信号，但额外**总是**写入 `_v2_quality_low`（仅作只读状态报告）
- **推荐 B**：影响最小，语义清晰——`_v2_no_upgrade` 控制"是否要求升级"，`_v2_quality_low` 仅描述"当前质量"

**问题 3 修法选型**：
- 候选 A：在 `score_extraction` 顶部判断纯文本（无 `<` 标签）→ 跳过结构分扣分，宽容评分
- 候选 B：在 `run_competition` 前检测 URL 后缀（.md/.txt/.json），命中则跳过竞赛，原样返回
- **推荐 B**：从根上避免对纯文本评分；A 治标不治本，万一未来出现 HTML 形式的 markdown 文件还是有问题

### 根因结论

**Bug 1**：升级成功判定用 HTML 长度而非提取质量。
**Bug 2**：`_v2_no_upgrade` 标志意外阻塞了 `_v2_quality_low` 的重新设置。
**问题 3**：评分函数对 plain text 输入不宽容（段落长度因子误伤）。

三者根因独立但 Bug 1+2 联动：单独修任一个都不彻底。Bug 1 修了但 Bug 2 没修 → 仍可能错误 break；Bug 2 修了但 Bug 1 没修 → 仍可能错把 SPA 骨架当升级成功。

**修复优先级**：
1. P0 · Bug 1 + Bug 2 必须**同时修复**（联动 bug，单修无效）
2. P1 · 问题 3 独立修复（影响窄但代价极低）
3. P2 · 增加单元测试覆盖三个场景

---

## 评审记录（A3 填写）

### Round 1 · 2026-05-13 09:55

#### 专家 A — Python 资深工程师（控制流 & 状态机视角）

- **评级**：🟡 建议（根因方向正确，但漏了一个隐藏副作用，且修法表述不够严谨）
- **要点**：
  - **Bug 1 根因准确**。`core.py:5661 if html2 and len(html2) > len(html)` 确实是用 HTML 字节长度做"升级成功"判定，而 SPA CDP 渲染后 HTML 几乎必然变长（注入了 `<div id="root"></div>` 之外的骨架/runtime/data island），所以 if 分支基本秒进，跟提取质量完全无关。
  - **Bug 2 根因准确，但漏写了"_v2_score 也一并失踪"**。看 engine_v2.py:130-147，`_v2_quality_low`、`_v2_needs_upgrade`、`_v2_current_fetcher`、`_v2_score` **四个字段全在同一个 `if quality_low and not _v2_no_upgrade` 块内**。重抓后由于 `_v2_no_upgrade=True`，这四个字段**全部不会被写**。这导致两个连锁问题：
    1. core.py:5673 的 `if not metadata.get('_v2_quality_low'): break` 永远 True（文档已写）；
    2. core.py:5620 的 `prev_score = metadata.get('_v2_score', 0)` 在第二轮升级时拿到 0，日志里 `prev_score=0.000` 看起来像"上一级完全失败"，但其实是状态丢了 —— 这是**未被文档识别的二阶 bug**，会让运维侧排查时被误导。
  - **联动效应描述正确**。Bug 1 提供了"错误的成功判定"，Bug 2 让"升级后的质量复检"完全失效，必须同时修。
  - **修法选型同意推荐 B（Bug 2）**：解耦 `_v2_no_upgrade`（升级请求开关）和 `_v2_score`/`_v2_quality_low`（只读质量描述）语义正交，是教科书式的状态机解耦。
- **反例/质疑**：
  - 对 Bug 1 修法推荐 A 的"`new_score > prev_score + 0.05` 才接受升级"提反例：**如果 prev_score 本身已经是 0.45（高位低分），CDP 拉到 0.48 也只差 0.03，按 margin 0.05 会被拒绝，但实际 0.48 接近 0.5 阈值已经算"接近合格"了**。建议改为"`new_score >= prev_score - 0.02`（不变差就接受） AND 同时检查 `new_score >= 0.5`（合格才 break，否则继续升）"——把"接受换 fetcher"和"判定是否合格"两个动作再次解耦。
  - 也质疑：CDP 返回 `html2` 后再次 `generic_v2` 会再跑一次完整的 `run_competition`，这本身是 O(竞赛+评分) 的成本，但 HTML 长度比较 0 成本。如果直接改成"score 比较"，意味着每次升级判定都得跑一次完整解析。需要 A2 文档明确**是否接受这个性能开销**（实际我认为可以接受，因为升级路径本身就是 5-30s 量级，几十 ms 解析忽略不计）。

#### 专家 B — 爬虫架构师（fetcher 升级策略 & SPA 经验视角）

- **评级**：🟢 通过（根因诊断准确，修法方向正确）+ 🟡 一个补强建议
- **要点**：
  - **Bug 1 根因绝对准确**。我在生产环境处理 SPA 抓取多年，`len(html2) > len(html)` 这种"长度即成功"的判定是**典型反模式**。原因：
    - urllib 抓 SPA：返回的是首屏 HTML，长度通常 5-30 KB（含 webpack runtime + `<div id="root"></div>` 骨架）；
    - CDP 抓 SPA：等 JS 执行后返回 100-500 KB（含全部 React Virtual DOM 序列化），HTML 长度增长 5-20×；
    - 但 trafilatura/readability 看到的"主内容"取决于是否有 `<article>`/`<main>`/语义化标签 —— SPA 大部分根本没这些，所以 score 几乎不变；
    - 文档表格里 `interconnects.ai/archive` urllib 0.45 → cdp 0.45 完美印证了这点。
  - **Bug 2 根因准确，文档分析到位**。这是个典型的"防护标志副作用泄露"bug —— `_v2_no_upgrade` 本意是"防止递归升级"，但顺便把"质量状态报告"也禁掉了。
  - **问题 3 根因准确**。CHANGELOG.md 那个例子是经典的"评分器假设输入是 HTML"的踩坑场景。看 extractors.py:30-77，4 个因子里有 2 个对 plain markdown 极不友好：
    - 段落质量分（20%）：markdown 文档段落动辄 500-2000 字符，落在 50-300 区间外 → para_score 衰减到 0.2-0.5；
    - 噪音分（25%）：长文档不可避免出现 "subscribe"/"sign in"/"more from" 之类词 → noise_score 衰减；
    - 双重打击下 0.43 完全合理。
  - **修法方向（B：URL 后缀短路）同意**。这是 industry-standard 做法：rsync/curl 都有 mime-type/extension-based content-handling。
- **反例/质疑**：
  - 质疑专家 A 对"score 比较成本"的担忧：generic_v2 在升级 if 分支里**反正都要重新调一次完整解析**（5667 行），所以 score 计算是顺带的产物，不是额外开销。专家 A 接受。
  - 对问题 3 修法 B 提**补强建议**（不阻塞）：仅靠 URL 后缀短路漏一类场景 —— **响应头 Content-Type: text/markdown 或 text/plain** 的情况。GitHub raw 是 `text/plain; charset=utf-8`，docs.python.org 的 .rst 也是 plain。建议改成"URL 后缀 OR Content-Type 命中 text/plain|text/markdown"。**或者**直接在 `score_extraction` 入口检测 `<` 标签密度 < 1% → 直接返回 `len(text)/500` 作为长度满分（实施成本更低）。
  - 对 Bug 1 提一个**潜在边界**：urllib 抓某些 CDN 站会返回 Cloudflare/WAF challenge 页面（约 5-15 KB），CDP 渲染等 challenge 通过后返回真实内容（几十 KB）—— 这种场景下 HTML 长度差异是有效信号。**如果完全废弃长度比较，会不会把这类"长度暴涨 = 拿到真实内容"的信号丢掉？** 我自问自答：不会，因为 score 也会同步暴涨，所以 score 比较照样工作。专家 C 待补充。

#### 专家 C — 静态分析专家（数据流 & 控制流耦合视角）

- **评级**：🟡 建议（根因都对，但发现一个文档没提的"清理过早"耦合 bug）
- **要点**：
  - **三处根因都成立，定位精确**。我用数据流的眼光看：
    - `_v2_quality_low` 这个字段在 engine_v2.py:144 被 set，在 core.py:5673 被 read，在 core.py:5684 被 pop —— 这是一个完整的"signal in, decision out, cleanup"流；
    - `_v2_no_upgrade` 在 core.py:5641, 5666 被 set，在 engine_v2.py:130 被 read —— 一个完整的"guard in, gate check, guard out"流；
    - **耦合点**：两个 flag 通过 engine_v2.py:130 的 `if quality_low and not _v2_no_upgrade:` 被**强行 AND 在一起**，副作用是把"质量信号写入"也门禁了。这是文档说的 Bug 2 主因。
  - **额外发现一个"清理过早"问题**（文档未提）：core.py:5683-5687 的清理在 for 循环**外面**，所以单次升级流程内的清理时机是对的。但如果 Bug 1 + Bug 2 修了之后，未来代码可能想在 break 之后做"最终质量再检查"或者把 `_v2_score` 暴露给上层日志/CLI verbose 输出 —— 此时 5684 行的 pop 会把字段干掉。**建议 A4 实施时考虑：是不是把 `_v2_score`（去掉下划线后改成 `extraction_score`）作为公开 metadata 字段保留，方便后续可观测性？**
  - **修法（B 案 for Bug 2）从控制流上是干净的**：把 `_v2_score`/`_v2_quality_low` 的写入移到 `if quality_low and not _v2_no_upgrade:` 块外面（即只要 `quality_low`，无论是否 no_upgrade，都把状态如实写入 metadata）。`_v2_needs_upgrade` 这个"升级请求"字段则保留在 if 内（只有真要升级时才请求）。这样语义最干净：**"质量描述"vs"升级请求"分两组**。
- **反例/质疑**：
  - 对专家 B 关于"score 暴涨可以替代长度暴涨信号"的论证基本同意，但加一个细节质疑：**如果 WAF challenge 页面恰好包含一些噪音词（"Verifying you are human", "Cloudflare"），score 可能反而被噪音分扣到 0.2**，这种情况下"真实页"score 0.5 vs "challenge 页"score 0.2 → 差 +0.3 远超 margin，所以 score 比较确实够用。**反例不成立，专家 B 的论证站得住。**
  - 对问题 3 修法 B 提推翻性反例：**raw.githubusercontent.com 的 URL 里 .md 后缀很显眼，但还有一类隐蔽场景 —— gist.github.com/xxx 的 raw view 也是 plain markdown 但 URL 没后缀**。所以纯靠 URL 后缀短路会漏一部分场景。**建议组合方案：URL 后缀短路 + Content-Type 兜底**（专家 B 提的）+ `score_extraction` 内部对纯文本宽容（专家 B 提的备选）。三层防御。
  - **对修法 B for Bug 1 持保留态度**：文档说"候选 B 过于复杂不推荐"我同意，但**修法 A 也需要补一个边界**：`html2` 不为 None 但解析失败/超时返回空字符串时，应该走 except/continue 分支，不应进入"比较 score"分支。文档第 162 行说"fetch 层失败时 html2 可能为 None/空字符串 → score 必然降为 0"是对的，但需要确保**不会在 html2='' 时调一次完整 generic_v2 浪费资源**。

### 辩论交锋

- **A vs B（关于 Bug 1 修法 margin 阈值）**：
  - A 认为 `new_score > prev_score + 0.05` 在 0.45 → 0.48 的临界场景会误拒；
  - B 反思后同意 A 的观点，建议改成 **"`new_score >= prev_score`（不退步就接受换 fetcher） + 同时判定 `new_score >= 0.5`（合格才 break）"** 两步走；
  - **共识**：把"换 fetcher 决策"和"链终止决策"解耦。换 fetcher 用宽松条件（不退步即接受新 HTML），终止用严格条件（达到 0.5 阈值才 break）。

- **B vs C（关于问题 3 修法粒度）**：
  - B 倾向"URL 后缀 + Content-Type 检测"；
  - C 指出 gist raw 等场景 URL 没后缀，且 Content-Type 也可能被代理改写；
  - **共识**：采用三层防御 ——（1）URL 后缀（含 `.md`/`.txt`/`.rst`）+ 路径匹配（`raw.githubusercontent.com`/`gist.githubusercontent.com`）→ 短路；（2）Content-Type 命中 `text/plain|text/markdown` → 短路；（3）`score_extraction` 入口检测 HTML 标签密度 < 1% → 走纯文本评分分支（长度+段落数为主，跳过结构分扣分）。

- **A vs C（关于 `_v2_score` 字段命名）**：
  - A 认为下划线前缀是"内部信号"约定，pop 掉是对的；
  - C 建议改名 `extraction_score` 作为公开 metadata 暴露给 CLI verbose；
  - **共识**：本次修复**不动**字段语义和暴露范围，保持下划线私有约定；可观测性改造作为独立后续优化项（不阻塞本次 A4），避免修复 PR 膨胀。

- **三方共识**：
  1. **根因诊断 100% 准确**（Bug 1/2/问题 3 三处定位都对）；
  2. **修法 B for Bug 2 完全 OK**（解耦 `_v2_no_upgrade` 和质量状态写入）；
  3. **修法 A for Bug 1 需要细化**（不退步即接受 + 合格才 break + html2 空字符串走 else）；
  4. **修法 B for 问题 3 需要扩展**（三层防御：URL 后缀 + 路径匹配 + Content-Type；可选辅以 score_extraction 入口的纯文本宽容分支）；
  5. **额外发现的二阶 bug**（`_v2_score` 在升级第二轮被丢失，prev_score 日志显示 0.000 误导排查）也由 Bug 2 的修法 B 顺带修复，无需独立处理。

### 结论

- **综合评级**：🟡 **修复后重审**（根因正确，可进入 A4，但 A4 需吸收下列细化要点）
- **行动项**（A4 必须明确处理）：
  1. **[Bug 1] 修法 A 细化**：升级判定改为 `score_extraction(extracted_content)` 比较，逻辑为：
     - 若 `html2` 为空或解析后 best 为空 → continue（不接受这一级，继续下一级）；
     - 若 `new_score >= prev_score`（不退步） → 接受新 HTML（替换 html、metrics、metadata）；
     - 接受后：`if new_score >= 0.5: break else: 继续 for 循环下一级`；
     - 移除现有 `len(html2) > len(html)` 条件；
  2. **[Bug 2] 修法 B**：把 engine_v2.py 中 `_v2_score`、`_v2_quality_low`、`_v2_current_fetcher` 三个**质量描述字段**的写入移到 `if quality_low and not _v2_no_upgrade:` 块外面（在 `quality_low` 判定后即写），只保留 `_v2_needs_upgrade` 在 if 内（升级请求字段）；
  3. **[问题 3] 三层防御**：
     - 在 engine_v2.py 入口（或 core.py 调 generic_v2 之前）增加 URL 后缀 + 路径 + Content-Type 短路判断，命中则跳过竞赛直接返回 plain content；
     - 兜底在 `score_extraction` 入口加一行：`if '<' not in text[:1000]: 走纯文本评分分支`（跳过结构分扣分、噪音权重减半）；
  4. **回归测试覆盖**（A4 实施时一并写）：
     - `interconnects.ai/archive` → 应升级到 selenium（或最终 manual_chrome），不应停在 cdp；
     - `wgetcloud/user/shop` → 同上；
     - `raw.githubusercontent.com/.../CHANGELOG.md` → 应短路，不应触发升级，最终 score 应 ≥ 0.6；
     - `tianyancha/search` 等 WAF 站 → 应升级到 selenium；
  5. **不在本次修复范围**（A4 显式标注 out-of-scope）：
     - `_v2_score` 字段重命名为公开字段（可观测性优化，独立 issue）；
     - 多层 fetcher 的 budget/timeout 重设计（独立 issue）。

---

## 实施方案

详见 `docs/20_设计/20260513_wf_V2_fallback修复方案.md`（A4 阶段创建）
