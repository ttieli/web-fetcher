# Web_Fetcher 架构指导文档
# Architecture Guidance Document

*文档版本：1.0*
*审查日期：2025-09-30*
*架构师：@agent-archy-principle-architect*

---

## 执行摘要 / Executive Summary

本文档提供Web_Fetcher项目TASKS目录中所有任务的完整架构审查结果和详细实施指导。经审查，Task 1需要调整实施路径以避免与现有代码冲突，Task 2方案合理但需要补充并发控制机制。

**关键结论：**
- Task 1（统一错误处理）：需要重构现有函数而非新增模块，避免代码重复
- Task 2（Chrome守护脚本）：方案可行，需增加锁机制防止并发问题
- 两个任务可并行开发，预计总工时：Task 1（6小时）+ Task 2（5小时）

---

## Task 1: 建立统一错误处理框架

### 架构评审结果

**评级：⚠️ 需要调整**

**识别的架构问题：**
1. **代码重复风险**：webfetcher.py已有`generate_failure_markdown()`（第4490行），新方案会造成功能重复
2. **集成路径不清晰**：未明确如何将新模块与现有5000行代码集成
3. **错误分类不完整**：缺少错误链处理和根因分析能力

### 调整后的实施方案

#### 项目结构变更

```
项目根目录/
├── error_handler.py            [新增] 统一错误处理模块
├── webfetcher.py               [修改] 第4490-4540行，4870-4925行
├── selenium_fetcher.py         [修改] 第120-135行，498-651行
└── tests/
    └── test_error_handler.py   [新增] 单元测试文件
```

#### 分阶段实施计划

**Phase 1: 基础架构搭建 [2小时]**

开发任务：
1. 创建error_handler.py，定义核心接口
2. 实现7类错误分类（NETWORK_CONNECTION, BROWSER_INIT等）
3. 编写错误链提取和根因分析逻辑

验证命令：
```bash
python -c "from error_handler import ErrorClassifier, ErrorCategory; print('Success')"
python -m pytest tests/test_error_handler.py::test_error_classification
```

**Phase 2: 代码集成 [3小时]**

修改要点：
- webfetcher.py第4490行：保留函数签名，内部调用error_handler
- selenium_fetcher.py第498-651行：在异常处理中添加分类逻辑
- 保持100%向后兼容

验证命令：
```bash
# 测试原有功能
python webfetcher.py https://example.com

# 测试增强功能
python wf.py -s https://example.com
```

**Phase 3: 测试与文档 [1小时]**

测试矩阵：
| 场景 | 命令 | 预期分类 |
|------|------|----------|
| Chrome未启动 | `pkill Chrome && python wf.py -s URL` | BROWSER_INIT |
| 页面超时 | `python wf.py -s httpstat.us/200?sleep=30000 --timeout 5` | TIMEOUT |
| SSL错误 | `python webfetcher.py https://expired.badssl.com/` | NETWORK_CONNECTION |

---

## Task 2: 新增Chrome调试守护脚本

### 架构评审结果

**评级：✅ 方案合理**

**需要补充的架构要素：**
1. **并发控制**：使用flock防止多实例启动
2. **PID管理**：实现僵尸进程清理
3. **权限处理**：提供清晰的macOS权限配置指导

### 完整实施方案

#### 项目结构变更

```
config/
├── chrome-debug.sh             [保持不变] 现有手动启动脚本
├── chrome-debug-launcher.sh    [新增] 后台启动器
├── ensure-chrome-debug.sh      [新增] 可用性保障脚本
└── ~/.chrome-wf/
    ├── chrome-debug.pid        [运行时] PID文件
    └── .chrome-debug.lock      [运行时] 进程锁
```

#### 分阶段实施计划

**Phase 1: 启动器开发 [1.5小时]**

脚本规范（chrome-debug-launcher.sh）：
```bash
#!/bin/bash
# 功能：安全启动Chrome调试实例
# 特性：
#   - flock防止并发
#   - PID文件管理
#   - 僵尸进程清理
#   - 返回码：0成功，非0失败
```

**Phase 2: 保障脚本开发 [2小时]**

脚本规范（ensure-chrome-debug.sh）：
```bash
#!/bin/bash
# 功能：确保Chrome调试实例可用
# 参数：
#   -t TIMEOUT  超时秒数（默认10）
#   -p PORT     端口号（默认9222）
# 流程：
#   1. 快速检测（0.1秒）
#   2. 必要时调用launcher
#   3. 健康检查循环（20次）
#   4. 错误处理和用户指导
```

**Phase 3: 系统集成 [1.5小时]**

wf.py集成点：
```python
# Selenium分支添加
if args.selenium:
    result = subprocess.run(['./config/ensure-chrome-debug.sh'])
    if result.returncode != 0:
        handle_chrome_failure()
```

测试场景：
1. Chrome未运行 → 自动启动
2. Chrome已运行 → 快速通过
3. 权限拒绝 → 用户指导
4. 并发调用 → 单实例保证

---

## 开发执行顺序

### 推荐的开发流程

1. **并行开发阶段**（可同时进行）
   - 开发者A：实施Task 1的Phase 1-2
   - 开发者B：实施Task 2的Phase 1-2

2. **集成测试阶段**（串行执行）
   - 完成Task 1的Phase 3测试
   - 完成Task 2的Phase 3集成
   - 执行端到端验证

3. **验收阶段**
   - 运行完整测试套件
   - 更新项目文档
   - 代码审查和合并

### 关键验收指标

**Task 1验收标准：**
- [ ] 错误分类准确率 > 95%
- [ ] 向后兼容性100%
- [ ] 测试覆盖率 > 80%
- [ ] 中英双语支持完整

**Task 2验收标准：**
- [ ] Chrome自动启动成功率100%
- [ ] 并发安全性验证通过
- [ ] 权限错误指导清晰
- [ ] 集成测试全部通过

---

## 风险管理

### 已识别风险

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| 修改5000行webfetcher.py造成回归 | 高 | 保持函数签名不变，充分测试 |
| Chrome版本兼容性问题 | 中 | 使用版本检测和回退机制 |
| macOS权限配置复杂 | 中 | 提供详细用户指导文档 |
| 并发启动Chrome冲突 | 低 | 使用flock锁机制 |

### 回滚计划

如果实施过程中发现严重问题：
1. Task 1：保留原generate_failure_markdown()函数
2. Task 2：回退到手动启动Chrome模式
3. 使用git分支隔离开发，确保主分支稳定

---

## 架构决策记录

### ADR-001: 重构vs新增模块

**决策：** 重构现有generate_failure_markdown()而非新增独立模块

**理由：**
1. 避免代码重复和维护负担
2. 保持向后兼容性
3. 减少集成复杂度

### ADR-002: Shell脚本vs Python实现

**决策：** 使用Shell脚本实现Chrome守护功能

**理由：**
1. 与现有chrome-debug.sh保持一致
2. 系统级进程管理更适合Shell
3. 减少Python依赖

---

## 附录：命令速查

### 开发常用命令

```bash
# Task 1 - 错误处理测试
python -m pytest tests/test_error_handler.py -v
python wf.py -s https://example.com 2>&1 | grep "Error Category"

# Task 2 - Chrome守护测试
./config/ensure-chrome-debug.sh -t 15
ps aux | grep -i "remote-debugging-port=9222"
curl -s http://localhost:9222/json/version | jq .

# 集成验证
python wf.py -s https://www.google.com
tail -f ~/.chrome-wf/chrome-debug.log
```

### Git提交规范

```bash
# Task 1提交
git commit -m "refactor: integrate unified error handling framework"

# Task 2提交
git commit -m "feat: add Chrome debug daemon scripts"
```

---

## 结论

两个任务的架构方案经过调整后均可实施。Task 1需要特别注意与现有代码的集成，Task 2需要完善并发控制机制。建议按照本文档的分阶段计划执行，确保每个阶段都有明确的验证点和回滚方案。

预计总工时：11小时（Task 1: 6小时，Task 2: 5小时）

---

*文档结束 - End of Document*