# Web Fetcher 验证执行框架

## 验证执行基础设施

### 测试环境管理

#### 环境配置规范
```python
# validation_config.py
"""
验证执行环境配置管理
"""

@dataclass
class ValidationConfig:
    """验证配置数据类"""
    
    # 基础配置
    test_timeout: int = 300  # 5分钟超时
    max_concurrent_tests: int = 3
    retry_attempts: int = 2
    
    # 性能基准配置
    baseline_samples: int = 5  # 基准测试样本数
    performance_threshold: float = 0.15  # 15%性能提升阈值
    memory_threshold: float = 0.30  # 30%内存优化阈值
    
    # 政府网站测试配置
    gov_detection_threshold: float = 0.90  # 90%检测准确率
    category_recognition_threshold: float = 0.85  # 85%栏目识别率
    
    # 测试网站配置
    test_sites: Dict[str, Dict] = field(default_factory=lambda: {
        "simple": {
            "url": "http://example.com",
            "expected_pages": 1,
            "max_test_time": 30
        },
        "government": {
            "url": "https://hdqw.bjhd.gov.cn/qwyw/tzgg/",
            "expected_pages": 20,
            "max_test_time": 120
        },
        "commercial": {
            "url": "https://github.com",
            "expected_pages": 10,
            "max_test_time": 60
        }
    })
    
    # 报告配置
    report_formats: List[str] = field(default_factory=lambda: ["html", "json", "markdown"])
    report_detail_level: str = "detailed"  # minimal, standard, detailed
```

#### 测试数据管理架构
```python
# validation_data.py
"""
测试数据管理和基准数据维护
"""

class ValidationDataManager:
    """验证数据管理器"""
    
    def __init__(self, data_dir: str = "validation_data"):
        self.data_dir = Path(data_dir)
        self.baseline_file = self.data_dir / "performance_baseline.json"
        self.test_cases_file = self.data_dir / "test_cases.json"
        
    def setup_test_data(self) -> None:
        """初始化测试数据目录结构"""
        directories = [
            "baseline",
            "mock", 
            "real",
            "reports",
            "temp"
        ]
        
        for dir_name in directories:
            (self.data_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def load_performance_baseline(self) -> Dict:
        """加载性能基准数据"""
        if self.baseline_file.exists():
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        return self._create_default_baseline()
    
    def save_performance_baseline(self, baseline_data: Dict) -> None:
        """保存性能基准数据"""
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
    
    def _create_default_baseline(self) -> Dict:
        """创建默认基准数据"""
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "metrics": {
                "crawl_speed": {"pages_per_second": 2.0},
                "memory_usage": {"peak_mb": 100},
                "cpu_usage": {"average_percent": 20},
                "network_efficiency": {"requests_per_page": 3}
            }
        }
```

### 验证执行引擎

#### 验证任务调度器
```python
# validation_scheduler.py
"""
验证任务调度和执行管理
"""

class ValidationScheduler:
    """验证任务调度器"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.task_queue = deque()
        self.results = {}
        self.logger = logging.getLogger(__name__)
        
    def add_validation_task(self, task: ValidationTask) -> None:
        """添加验证任务到队列"""
        self.task_queue.append(task)
        self.logger.info(f"Added validation task: {task.name}")
    
    def execute_all_tasks(self) -> ValidationResults:
        """执行所有验证任务"""
        results = ValidationResults()
        
        while self.task_queue:
            task = self.task_queue.popleft()
            try:
                result = self._execute_task(task)
                results.add_result(task.name, result)
                
                if not result.passed and task.is_critical:
                    self.logger.error(f"Critical task failed: {task.name}")
                    results.critical_failure = True
                    break
                    
            except Exception as e:
                self.logger.error(f"Task execution failed: {task.name}, error: {e}")
                results.add_error(task.name, str(e))
        
        return results
    
    def _execute_task(self, task: ValidationTask) -> TaskResult:
        """执行单个验证任务"""
        start_time = time.time()
        
        try:
            # 设置超时
            with timeout(self.config.test_timeout):
                result = task.execute()
                
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_name=task.name,
                passed=result.success,
                metrics=result.metrics,
                execution_time=execution_time,
                details=result.details
            )
            
        except TimeoutError:
            return TaskResult(
                task_name=task.name,
                passed=False,
                error="Task execution timeout",
                execution_time=self.config.test_timeout
            )
```

#### 性能基准测试引擎
```python
# performance_benchmark.py
"""
性能基准测试执行引擎
"""

class PerformanceBenchmark:
    """性能基准测试引擎"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.metrics_collector = MetricsCollector()
        
    def run_baseline_benchmark(self, test_site: str) -> BenchmarkResult:
        """运行基准性能测试"""
        results = []
        
        for i in range(self.config.baseline_samples):
            self.logger.info(f"Running baseline sample {i+1}/{self.config.baseline_samples}")
            
            # 收集性能指标
            with self.metrics_collector.collect():
                pages = crawl_site(
                    test_site,
                    enable_optimizations=False,  # 基准测试不启用优化
                    max_pages=20,
                    max_depth=2
                )
            
            metrics = self.metrics_collector.get_metrics()
            results.append(metrics)
        
        return BenchmarkResult.from_samples(results)
    
    def run_optimized_benchmark(self, test_site: str) -> BenchmarkResult:
        """运行优化版本性能测试"""
        results = []
        
        for i in range(self.config.baseline_samples):
            self.logger.info(f"Running optimized sample {i+1}/{self.config.baseline_samples}")
            
            with self.metrics_collector.collect():
                pages = crawl_site(
                    test_site,
                    enable_optimizations=True,  # 启用所有优化
                    max_pages=20,
                    max_depth=2
                )
            
            metrics = self.metrics_collector.get_metrics()
            results.append(metrics)
        
        return BenchmarkResult.from_samples(results)
    
    def compare_performance(self, baseline: BenchmarkResult, optimized: BenchmarkResult) -> PerformanceComparison:
        """比较性能基准和优化版本"""
        return PerformanceComparison(
            speed_improvement=self._calculate_improvement(
                baseline.crawl_speed, optimized.crawl_speed
            ),
            memory_improvement=self._calculate_improvement(
                baseline.memory_peak, optimized.memory_peak, inverse=True
            ),
            cpu_improvement=self._calculate_improvement(
                baseline.cpu_usage, optimized.cpu_usage, inverse=True
            ),
            network_improvement=self._calculate_improvement(
                baseline.network_requests, optimized.network_requests, inverse=True
            )
        )
    
    def _calculate_improvement(self, baseline_value: float, optimized_value: float, inverse: bool = False) -> float:
        """计算性能改进百分比"""
        if baseline_value == 0:
            return 0.0
            
        if inverse:
            # 对于内存、CPU使用率等，越小越好
            improvement = (baseline_value - optimized_value) / baseline_value
        else:
            # 对于速度等，越大越好
            improvement = (optimized_value - baseline_value) / baseline_value
            
        return improvement * 100  # 转换为百分比
```

### 度量和监控系统

#### 指标收集器
```python
# metrics_collector.py
"""
性能指标收集和监控
"""

class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self):
        self.start_time = None
        self.peak_memory = 0
        self.cpu_samples = []
        self.network_requests = 0
        
    @contextmanager
    def collect(self):
        """性能指标收集上下文管理器"""
        # 开始收集
        self.start_time = time.time()
        
        if psutil:
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
        if tracemalloc:
            tracemalloc.start()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_resources)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            yield self
        finally:
            # 停止收集
            self.end_time = time.time()
            
            if tracemalloc:
                current, peak = tracemalloc.get_traced_memory()
                self.peak_memory = peak / 1024 / 1024  # MB
                tracemalloc.stop()
    
    def _monitor_resources(self):
        """监控系统资源使用"""
        if not psutil:
            return
            
        process = psutil.Process()
        
        while self.start_time and not hasattr(self, 'end_time'):
            try:
                cpu_percent = process.cpu_percent()
                self.cpu_samples.append(cpu_percent)
                time.sleep(0.1)  # 每100ms采样一次
            except:
                break
    
    def get_metrics(self) -> Dict:
        """获取收集的性能指标"""
        execution_time = getattr(self, 'end_time', time.time()) - self.start_time
        
        return {
            "execution_time": execution_time,
            "peak_memory_mb": self.peak_memory,
            "average_cpu_percent": np.mean(self.cpu_samples) if self.cpu_samples else 0,
            "network_requests": self.network_requests,
            "crawl_speed": 1 / execution_time if execution_time > 0 else 0
        }
```

### 报告生成系统

#### 验证报告生成器
```python
# report_generator.py
"""
验证报告生成系统
"""

class ValidationReportGenerator:
    """验证报告生成器"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.template_dir = Path("templates")
        
    def generate_comprehensive_report(self, results: ValidationResults) -> Dict[str, str]:
        """生成全面的验证报告"""
        reports = {}
        
        for format_type in self.config.report_formats:
            if format_type == "html":
                reports["html"] = self._generate_html_report(results)
            elif format_type == "json":
                reports["json"] = self._generate_json_report(results)
            elif format_type == "markdown":
                reports["markdown"] = self._generate_markdown_report(results)
        
        return reports
    
    def _generate_html_report(self, results: ValidationResults) -> str:
        """生成HTML格式验证报告"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Web Fetcher 验证报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; }
                .pass { color: green; font-weight: bold; }
                .fail { color: red; font-weight: bold; }
                .metrics { background: #fafafa; padding: 15px; border-left: 4px solid #007cba; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Web Fetcher 优化验证报告</h1>
                <p>生成时间: {timestamp}</p>
                <p>验证版本: {version}</p>
            </div>
            
            <div class="section">
                <h2>质量门禁状态</h2>
                <table>
                    <tr><th>门禁项</th><th>状态</th><th>详情</th></tr>
                    {quality_gates_rows}
                </table>
            </div>
            
            <div class="section">
                <h2>性能基准对比</h2>
                <div class="metrics">
                    {performance_metrics}
                </div>
            </div>
            
            <div class="section">
                <h2>详细测试结果</h2>
                {detailed_results}
            </div>
        </body>
        </html>
        """
        
        return template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            version=results.version,
            quality_gates_rows=self._format_quality_gates(results),
            performance_metrics=self._format_performance_metrics(results),
            detailed_results=self._format_detailed_results(results)
        )
    
    def _generate_markdown_report(self, results: ValidationResults) -> str:
        """生成Markdown格式验证报告"""
        template = """
# Web Fetcher 优化验证报告

## 执行概要
- **验证时间**: {timestamp}
- **验证版本**: {version}
- **测试环境**: {environment}
- **总体状态**: {overall_status}

## 质量门禁状态

| 门禁项目 | 状态 | 指标值 | 目标值 | 说明 |
|----------|------|--------|--------|------|
{quality_gates_table}

## 性能基准对比

| 性能指标 | 优化前 | 优化后 | 改进幅度 | 是否达标 |
|----------|--------|--------|----------|----------|
{performance_table}

## 分阶段验证结果

### 阶段1: 基础优化验证
{stage1_results}

### 阶段2: 政府网站策略验证  
{stage2_results}

## 发现的问题

{issues_list}

## 改进建议

{recommendations}

## 最终验收结论

{final_conclusion}

---
*本报告由 Web Fetcher 验证框架自动生成*
        """
        
        return template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            version=results.version,
            environment=results.environment,
            overall_status="✅ 通过" if results.overall_passed else "❌ 失败",
            quality_gates_table=self._format_quality_gates_markdown(results),
            performance_table=self._format_performance_markdown(results),
            stage1_results=self._format_stage_results_markdown(results, "stage1"),
            stage2_results=self._format_stage_results_markdown(results, "stage2"),
            issues_list=self._format_issues_markdown(results),
            recommendations=self._format_recommendations_markdown(results),
            final_conclusion=self._format_conclusion_markdown(results)
        )
```

### 自动化集成接口

#### CI/CD 集成规范
```yaml
# .github/workflows/validation.yml
name: Web Fetcher Validation

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  validation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test-requirements.txt
    
    - name: Run Stage 1 Validation
      run: |
        python -m validation.run_stage1_tests
        
    - name: Run Stage 2 Validation  
      run: |
        python -m validation.run_stage2_tests
        
    - name: Generate Validation Report
      run: |
        python -m validation.generate_report
        
    - name: Upload Report Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: validation-reports
        path: validation_data/reports/
```

## 验证执行命令规范

### 快速验证命令
```bash
# 完整验证流程
python -m validation.run_full_validation

# 分阶段验证
python -m validation.run_stage1_only
python -m validation.run_stage2_only

# 性能基准测试
python -m validation.run_performance_benchmark

# 生成报告
python -m validation.generate_report --format html,markdown,json
```

### 验证结果判断规范
```python
# 验证结果判断逻辑
class ValidationJudge:
    def __init__(self, config: ValidationConfig):
        self.config = config
    
    def judge_overall_result(self, results: ValidationResults) -> ValidationDecision:
        """判断整体验收结果"""
        
        # Must Pass 检查
        must_pass_items = [
            "api_compatibility",
            "functional_completeness", 
            "basic_performance",
            "error_handling"
        ]
        
        for item in must_pass_items:
            if not results.get_result(item).passed:
                return ValidationDecision(
                    passed=False,
                    reason=f"Must pass item failed: {item}",
                    recommendation="Fix critical issues before proceeding"
                )
        
        # Should Pass 检查
        should_pass_score = self._calculate_should_pass_score(results)
        if should_pass_score < 0.8:  # 80%的should pass项目需要通过
            return ValidationDecision(
                passed=False,
                reason=f"Should pass score too low: {should_pass_score:.2f}",
                recommendation="Address performance and quality issues"
            )
        
        return ValidationDecision(
            passed=True,
            reason="All critical and most important validations passed",
            recommendation="Ready for release"
        )
```

---

**框架设计原则**: 
- **模块化**: 每个组件职责清晰，可独立测试
- **可扩展**: 支持新增验证项目和报告格式
- **自动化**: 支持CI/CD集成和自动化执行
- **可观测**: 详细的日志记录和性能监控