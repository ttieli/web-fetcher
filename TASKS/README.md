# TASKS Directory - Task Management Center
# TASKS目录 - 任务管理中心

## Current Status / 当前状态
*Last Updated / 最后更新: 2025-10-10*

| Priority / 优先级 | Pending / 待办 | Completed / 已完成 | Deferred / 延期 |
|-------------------|----------------|--------------------|------------------|
| P1 (Critical) | 0 | 8 | 0 |
| P2 (Important) | 2 | 2 | 0 |
| P3 (Stability) | 0 | 1 | 0 |
| Deferred | 0 | 0 | 1 |

## 🚀 Active Tasks / 当前任务

### **Task 2: ChromeDriver Version Management** *(P2)*
- **Status / 状态**: Pending / 待实施
- **Goal / 目标**: Automate Chrome & ChromeDriver version alignment / 自动同步 Chrome 与 ChromeDriver 版本
- **Value / 价值**: 保证 Selenium 与手动 Chrome 兜底稳定
- **Deliverables / 交付物**: `drivers/version_manager.py`、`manage_chromedriver.py` CLI、诊断集成

### **Task 2: Core Module Pruning Plan** *(P2)* 🆕
- **Status / 状态**: Pending / 待实施
- **Goal / 目标**: Use pydeps to map wf 核心依赖，规划删除非核心代码的安全路径
- **Value / 价值**: 精简代码量，降低维护成本，同时确保 wf 工具依赖完整
- **Deliverables / 交付物**: Core cleanup 方案文档、保留/删除清单、验证与回滚步骤

### Deferred / 延期
- `deferred/task-005-error-system-phase3-4.md`：错误系统高级特性，待收集生产数据后再评估。

## ✅ Recently Completed / 最近完成

### Task-002: Regression Test Harness ✅ *(NEW)*
- **Status:** Completed 2025-10-10
- **Grade:** A+ (97/100)
- **Archive:** [task-002](archive/completed/task-002-regression-test-harness/)
- **Key Features:**
  - Automated regression testing across 16+ URLs
  - Baseline comparison and trend tracking
  - CI/CD integration (GitHub Actions, GitLab CI, Jenkins)
  - Multi-format reporting (Markdown/JSON/Text)
  - Docker support and 2,500+ lines of documentation

### Task-001: Parser Template Creator Tools ✅
- **Status:** Completed 2025-10-09
- **Grade:** A (94/100)
- **Archive:** [task-001](archive/completed/task-001-parser-template-creator/)
- **Key Features:**
  - CLI toolchain for no-code template creation
  - Schema validation and synchronization
  - Template generation and preview tools

### Previous Completions
- **Task 1: Config-Driven Routing System (A+)** – YAML 路由体系已投产，决策 <5ms。详见 `archive/completed/task-001-config-driven-routing-v2/`
- **Task 000 / 001 / 002 / 004 / 006 / 007 / 010** – 核心抓取与错误处理优化均已归档，参见 `archive/completed/`

## 📚 Archive Structure / 归档结构
```
archive/
├── completed/                 # 已完成任务
├── documents/
│   ├── reports/
│   │   ├── cebbank/           # 光大银行调查原始材料
│   │   └── general/           # 综合报告
│   └── specs/                 # 技术规范
└── deferred/                  # 延期任务
```

## 🧭 Next Steps / 下一步计划
1. ✅ ~~完成 Task 1 Phase 4，交付模板工具链。~~ (COMPLETED 2025-10-09)
2. ✅ ~~实施 Task 2 回归测试平台，为后续精简与回归提供保障。~~ (COMPLETED 2025-10-10)
3. 启动 Task 2 ChromeDriver 版本管理，锁定兜底稳定性。
4. 基于 pydeps 结果编制核心模块精简方案，准备执行阶段。

## 📝 Maintenance Notes / 维护指引
- 新增任务需中英双语描述，命名遵循 `task-[优先级编号]-[英文名称].md`。
- 完成任务请归档至 `archive/completed/` 并更新本 README。
- 删除/精简前务必评估依赖并准备回滚方案。
- `pydeps` 生成图像需安装 graphviz，可使用 `--show-deps --no-show` 获取 JSON 结果。
