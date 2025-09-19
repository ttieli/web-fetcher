# Web Fetcher 性能基准测试协议

## 基准测试架构设计

### 测试目标分层

```
┌─────────────────────────────────────────┐
│            业务影响层                   │
│    (用户感知的整体性能改进)             │
├─────────────────────────────────────────┤
│            系统性能层                   │
│    (爬取速度、内存、CPU使用)           │
├─────────────────────────────────────────┤
│            组件性能层                   │
│    (链接过滤、批处理、网络效率)         │
├─────────────────────────────────────────┤
│            基础度量层                   │
│    (响应时间、吞吐量、资源利用)         │
└─────────────────────────────────────────┘
```

### 性能度量维度

#### 1. 核心性能指标 (Core Performance Metrics)

**爬取效率指标**
- **页面爬取速度** (pages/second): 单位时间内成功爬取的页面数量
- **内容提取速度** (KB/second): 单位时间内提取的有效内容量
- **链接发现效率** (links/page): 每页面发现的有效链接数量

**资源利用指标**
- **内存峰值使用** (MB): 爬取过程中的最大内存占用
- **内存增长率** (MB/page): 每增加一个页面的内存增长
- **CPU使用率** (%): 爬取过程中的平均CPU占用

**网络效率指标**
- **请求成功率** (%): 网络请求的成功比例
- **平均响应时间** (ms): 网络请求的平均响应时间
- **带宽利用率** (KB/s): 网络带宽的有效利用

#### 2. 优化特定指标 (Optimization-Specific Metrics)

**阶段1基础优化指标**
```python
stage1_metrics = {
    "link_filtering": {
        "total_links_found": int,
        "filtered_out_links": int, 
        "filtering_accuracy": float,  # 过滤掉的无效链接比例
        "filtering_time_per_page": float  # 每页面链接过滤耗时
    },
    "batch_processing": {
        "batch_size": int,
        "batches_processed": int,
        "batch_processing_time": float,
        "memory_saved_per_batch": float
    },
    "memory_optimization": {
        "baseline_memory": float,
        "optimized_memory": float,
        "memory_reduction_percent": float,
        "gc_frequency": int  # 垃圾回收频率
    }
}
```

**阶段2政府网站策略指标**
```python
stage2_metrics = {
    "government_detection": {
        "detection_accuracy": float,  # 检测准确率
        "detection_time": float,      # 检测耗时
        "false_positive_rate": float, # 误报率
        "false_negative_rate": float  # 漏报率
    },
    "category_extraction": {
        "categories_found": int,
        "extraction_success_rate": float,
        "high_priority_categories": int,
        "extraction_time": float
    },
    "category_crawling": {
        "category_coverage": float,   # 栏目覆盖率
        "category_depth": float,      # 平均栏目深度
        "content_quality_score": float  # 内容质量评分
    }
}
```

## 基准测试协议

### 测试环境标准化

#### 硬件环境规范
```yaml
hardware_requirements:
  cpu:
    minimum: "2 cores, 2.0GHz"
    recommended: "4 cores, 2.5GHz"
  memory:
    minimum: "4GB RAM"
    recommended: "8GB RAM"
  network:
    minimum: "10Mbps"
    recommended: "100Mbps"
  storage:
    minimum: "1GB free space"
    type: "SSD preferred"
```

#### 软件环境规范
```yaml
software_environment:
  python_version: "3.9+"
  operating_system: 
    - "Ubuntu 20.04+"
    - "macOS 10.15+"
    - "Windows 10+"
  dependencies:
    - "requests>=2.25.0"
    - "beautifulsoup4>=4.9.0"
    - "playwright>=1.20.0"
  testing_tools:
    - "psutil>=5.8.0"
    - "memory-profiler>=0.60.0"
    - "pytest>=6.0.0"
```

### 基准测试数据集

#### 标准测试网站分类
```python
BENCHMARK_SITES = {
    "simple_sites": [
        {
            "url": "http://example.com",
            "category": "static_simple",
            "expected_pages": 1,
            "max_crawl_time": 10,
            "description": "静态单页面网站"
        }
    ],
    
    "government_sites": [
        {
            "url": "https://hdqw.bjhd.gov.cn/qwyw/tzgg/",
            "category": "government_complex",
            "expected_pages": 50,
            "max_crawl_time": 300,
            "description": "北京海淀区政府通知公告"
        },
        {
            "url": "https://www.beijing.gov.cn",
            "category": "government_portal",
            "expected_pages": 100,
            "max_crawl_time": 600,
            "description": "北京市政府门户网站"
        }
    ],
    
    "commercial_sites": [
        {
            "url": "https://github.com",
            "category": "tech_platform",
            "expected_pages": 20,
            "max_crawl_time": 120,
            "description": "技术平台网站"
        }
    ],
    
    "stress_test_sites": [
        {
            "url": "https://news.ycombinator.com",
            "category": "high_volume",
            "expected_pages": 200,
            "max_crawl_time": 1200,
            "description": "高容量新闻站点"
        }
    ]
}
```

### 基准测试执行协议

#### 预热和稳定性协议
```python
class BenchmarkProtocol:
    """基准测试执行协议"""
    
    def __init__(self):
        self.warmup_runs = 3      # 预热轮次
        self.measurement_runs = 5  # 测量轮次
        self.cooldown_time = 30   # 冷却时间(秒)
        
    def execute_benchmark_suite(self, test_site: str) -> BenchmarkSuite:
        """执行完整的基准测试套件"""
        
        # 1. 环境预检
        self._verify_environment()
        
        # 2. 预热阶段
        self._warmup_phase(test_site)
        
        # 3. 基准测试阶段
        baseline_results = self._baseline_phase(test_site)
        
        # 4. 冷却时间
        time.sleep(self.cooldown_time)
        
        # 5. 优化测试阶段
        optimized_results = self._optimized_phase(test_site)
        
        # 6. 结果分析
        return self._analyze_results(baseline_results, optimized_results)
    
    def _warmup_phase(self, test_site: str) -> None:
        """预热阶段 - 稳定测试环境"""
        logging.info("Starting warmup phase...")
        
        for i in range(self.warmup_runs):
            logging.info(f"Warmup run {i+1}/{self.warmup_runs}")
            
            # 简单爬取，不记录结果
            try:
                crawl_site(
                    test_site,
                    max_pages=5,
                    max_depth=1,
                    enable_optimizations=False
                )
            except Exception as e:
                logging.warning(f"Warmup run failed: {e}")
            
            time.sleep(5)  # 短暂休息
    
    def _baseline_phase(self, test_site: str) -> List[BenchmarkResult]:
        """基准测试阶段 - 未优化版本"""
        logging.info("Starting baseline measurement phase...")
        results = []
        
        for i in range(self.measurement_runs):
            logging.info(f"Baseline run {i+1}/{self.measurement_runs}")
            
            with MetricsCollector() as collector:
                try:
                    pages = crawl_site(
                        test_site,
                        max_pages=20,
                        max_depth=2,
                        enable_optimizations=False,  # 关键: 不启用优化
                        delay=0.5
                    )
                    
                    result = BenchmarkResult(
                        run_id=f"baseline_{i+1}",
                        success=True,
                        pages_crawled=len(pages),
                        metrics=collector.get_metrics()
                    )
                    
                except Exception as e:
                    result = BenchmarkResult(
                        run_id=f"baseline_{i+1}",
                        success=False,
                        error=str(e)
                    )
                
                results.append(result)
            
            time.sleep(10)  # 运行间隔
        
        return results
    
    def _optimized_phase(self, test_site: str) -> List[BenchmarkResult]:
        """优化测试阶段 - 启用所有优化"""
        logging.info("Starting optimized measurement phase...")
        results = []
        
        for i in range(self.measurement_runs):
            logging.info(f"Optimized run {i+1}/{self.measurement_runs}")
            
            with MetricsCollector() as collector:
                try:
                    pages = crawl_site(
                        test_site,
                        max_pages=20,
                        max_depth=2,
                        enable_optimizations=True,   # 关键: 启用优化
                        crawl_strategy='category_first',  # 启用政府网站策略
                        memory_efficient=True,       # 启用内存优化
                        delay=0.5
                    )
                    
                    result = BenchmarkResult(
                        run_id=f"optimized_{i+1}",
                        success=True,
                        pages_crawled=len(pages),
                        metrics=collector.get_metrics()
                    )
                    
                except Exception as e:
                    result = BenchmarkResult(
                        run_id=f"optimized_{i+1}",
                        success=False,
                        error=str(e)
                    )
                
                results.append(result)
            
            time.sleep(10)  # 运行间隔
        
        return results
```

### 统计分析协议

#### 性能度量统计方法
```python
class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.confidence_level = 0.95
        self.significance_threshold = 0.05
        
    def analyze_performance_improvement(self, 
                                      baseline_results: List[BenchmarkResult],
                                      optimized_results: List[BenchmarkResult]) -> PerformanceAnalysis:
        """分析性能改进情况"""
        
        # 1. 基础统计分析
        baseline_stats = self._calculate_statistics(baseline_results)
        optimized_stats = self._calculate_statistics(optimized_results)
        
        # 2. 改进率计算
        improvements = self._calculate_improvements(baseline_stats, optimized_stats)
        
        # 3. 统计显著性检验
        significance_tests = self._perform_significance_tests(
            baseline_results, optimized_results
        )
        
        # 4. 置信区间计算
        confidence_intervals = self._calculate_confidence_intervals(
            baseline_results, optimized_results
        )
        
        return PerformanceAnalysis(
            baseline_stats=baseline_stats,
            optimized_stats=optimized_stats,
            improvements=improvements,
            significance_tests=significance_tests,
            confidence_intervals=confidence_intervals,
            overall_assessment=self._assess_overall_performance(improvements)
        )
    
    def _calculate_statistics(self, results: List[BenchmarkResult]) -> PerformanceStats:
        """计算性能统计指标"""
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return PerformanceStats(valid=False)
        
        # 提取关键指标
        crawl_speeds = [r.metrics['crawl_speed'] for r in successful_results]
        memory_peaks = [r.metrics['peak_memory_mb'] for r in successful_results]
        cpu_usages = [r.metrics['average_cpu_percent'] for r in successful_results]
        
        return PerformanceStats(
            valid=True,
            sample_count=len(successful_results),
            crawl_speed=StatsSummary(
                mean=np.mean(crawl_speeds),
                median=np.median(crawl_speeds),
                std=np.std(crawl_speeds),
                min=np.min(crawl_speeds),
                max=np.max(crawl_speeds)
            ),
            memory_usage=StatsSummary(
                mean=np.mean(memory_peaks),
                median=np.median(memory_peaks),
                std=np.std(memory_peaks),
                min=np.min(memory_peaks),
                max=np.max(memory_peaks)
            ),
            cpu_usage=StatsSummary(
                mean=np.mean(cpu_usages),
                median=np.median(cpu_usages),
                std=np.std(cpu_usages),
                min=np.min(cpu_usages),
                max=np.max(cpu_usages)
            )
        )
    
    def _calculate_improvements(self, baseline: PerformanceStats, optimized: PerformanceStats) -> ImprovementSummary:
        """计算性能改进情况"""
        
        if not (baseline.valid and optimized.valid):
            return ImprovementSummary(valid=False)
        
        # 爬取速度改进 (越高越好)
        speed_improvement = (
            (optimized.crawl_speed.mean - baseline.crawl_speed.mean) / 
            baseline.crawl_speed.mean * 100
        )
        
        # 内存使用改进 (越低越好)
        memory_improvement = (
            (baseline.memory_usage.mean - optimized.memory_usage.mean) / 
            baseline.memory_usage.mean * 100
        )
        
        # CPU使用改进 (越低越好)
        cpu_improvement = (
            (baseline.cpu_usage.mean - optimized.cpu_usage.mean) / 
            baseline.cpu_usage.mean * 100
        )
        
        return ImprovementSummary(
            valid=True,
            speed_improvement_percent=speed_improvement,
            memory_improvement_percent=memory_improvement,
            cpu_improvement_percent=cpu_improvement,
            overall_score=self._calculate_overall_score(
                speed_improvement, memory_improvement, cpu_improvement
            )
        )
    
    def _calculate_overall_score(self, speed: float, memory: float, cpu: float) -> float:
        """计算综合性能评分"""
        # 加权平均：速度40%，内存35%，CPU25%
        weights = [0.4, 0.35, 0.25]
        improvements = [speed, memory, cpu]
        
        return sum(w * i for w, i in zip(weights, improvements))
```

### 基准数据管理

#### 历史基准数据维护
```python
class BenchmarkDataManager:
    """基准数据管理器"""
    
    def __init__(self, data_dir: str = "benchmark_data"):
        self.data_dir = Path(data_dir)
        self.baseline_file = self.data_dir / "performance_baselines.json"
        
    def save_benchmark_baseline(self, 
                               site_category: str,
                               results: PerformanceAnalysis,
                               version: str) -> None:
        """保存基准测试结果"""
        
        baseline_data = self._load_baseline_data()
        
        # 更新基准数据
        baseline_data[site_category] = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "baseline_performance": {
                "crawl_speed": results.baseline_stats.crawl_speed.__dict__,
                "memory_usage": results.baseline_stats.memory_usage.__dict__,
                "cpu_usage": results.baseline_stats.cpu_usage.__dict__
            },
            "optimized_performance": {
                "crawl_speed": results.optimized_stats.crawl_speed.__dict__,
                "memory_usage": results.optimized_stats.memory_usage.__dict__,
                "cpu_usage": results.optimized_stats.cpu_usage.__dict__
            },
            "improvements": results.improvements.__dict__
        }
        
        self._save_baseline_data(baseline_data)
    
    def compare_with_historical_baseline(self, 
                                       site_category: str,
                                       current_results: PerformanceAnalysis) -> BaselineComparison:
        """与历史基准数据比较"""
        
        baseline_data = self._load_baseline_data()
        
        if site_category not in baseline_data:
            return BaselineComparison(
                has_historical_data=False,
                message="No historical baseline data found"
            )
        
        historical = baseline_data[site_category]
        
        # 比较改进趋势
        trend_analysis = self._analyze_performance_trend(
            historical["improvements"],
            current_results.improvements.__dict__
        )
        
        return BaselineComparison(
            has_historical_data=True,
            historical_version=historical["version"],
            historical_improvements=historical["improvements"],
            current_improvements=current_results.improvements.__dict__,
            trend_analysis=trend_analysis
        )
```

## 性能目标和阈值定义

### 性能目标分级

#### 第一级：必须达到的基础性能目标
```python
MUST_PASS_PERFORMANCE_TARGETS = {
    "compatibility": {
        "performance_regression": 0.0,  # 不允许性能倒退
        "memory_regression": 0.0,       # 不允许内存使用增加
        "stability": 0.95              # 95%的测试运行必须成功
    }
}
```

#### 第二级：期望达到的优化目标
```python
SHOULD_PASS_PERFORMANCE_TARGETS = {
    "stage1_optimization": {
        "crawl_speed_improvement": 15.0,     # 15%爬取速度提升
        "memory_usage_reduction": 20.0,      # 20%内存使用降低
        "link_filtering_efficiency": 25.0    # 25%链接过滤效率
    },
    "stage2_government": {
        "government_detection_accuracy": 90.0,  # 90%政府网站检测准确率
        "category_recognition_rate": 85.0,      # 85%栏目识别成功率
        "category_crawl_efficiency": 30.0       # 30%栏目爬取效率提升
    }
}
```

#### 第三级：理想达到的卓越目标
```python
COULD_PASS_PERFORMANCE_TARGETS = {
    "excellence": {
        "crawl_speed_improvement": 30.0,      # 30%爬取速度提升
        "memory_usage_reduction": 40.0,       # 40%内存使用降低
        "overall_user_experience": 25.0,      # 25%整体用户体验提升
        "code_maintainability": 20.0          # 20%代码可维护性提升
    }
}
```

### 性能阈值监控

#### 性能劣化告警阈值
```python
PERFORMANCE_ALERT_THRESHOLDS = {
    "degradation_warning": {
        "speed_degradation": -5.0,      # 速度下降5%告警
        "memory_increase": 10.0,        # 内存增加10%告警
        "error_rate_increase": 2.0      # 错误率增加2%告警
    },
    "degradation_critical": {
        "speed_degradation": -10.0,     # 速度下降10%严重告警
        "memory_increase": 25.0,        # 内存增加25%严重告警
        "error_rate_increase": 5.0      # 错误率增加5%严重告警
    }
}
```

---

**基准测试原则**:
- **可重复性**: 测试结果可在相同条件下重现
- **客观性**: 基于量化指标，避免主观判断
- **全面性**: 覆盖所有关键性能维度
- **渐进性**: 支持分阶段性能验证和改进