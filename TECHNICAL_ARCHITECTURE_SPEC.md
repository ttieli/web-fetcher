# 全站爬取优化技术架构规格

## 1. 系统架构概览

### 1.1 架构原则
- **渐进式升级**：保持API向后兼容，新功能可选启用
- **策略驱动**：通过配置参数选择爬取策略
- **性能优先**：优化内存使用和爬取效率
- **失败降级**：新策略失败时自动降级到默认策略

### 1.2 核心组件设计
```
┌─────────────────────────────────────────┐
│             Web Crawler                 │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   策略层     │  │     优化层       │   │
│  │ Strategy     │  │ Optimization    │   │
│  │ - Default    │  │ - Link Filter   │   │
│  │ - Category   │  │ - Memory Mgmt   │   │
│  │ - Fallback   │  │ - Batch Process │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   识别层     │  │     爬取层       │   │
│  │ Detection    │  │ Crawler Core    │   │
│  │ - Site Type  │  │ - BFS Engine    │   │
│  │ - Categories │  │ - Link Extract  │   │
│  │ - Structure  │  │ - Content Proc  │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│           基础网络层 (Network)           │
└─────────────────────────────────────────┘
```

## 2. 接口定义规格

### 2.1 主要接口契约

#### 核心爬取接口
```python
def crawl_site(
    start_url: str,
    user_agent: str = None,
    max_depth: int = 3,
    max_pages: int = 1000,
    delay: float = 0.5,
    # 新增参数 - 向后兼容
    crawl_strategy: str = 'default',
    enable_optimizations: bool = True,
    category_config: Optional[Dict] = None
) -> List[Tuple[str, str]]:
    """
    全站内容爬取函数
    
    Parameters:
    -----------
    start_url : str
        起始URL
    crawl_strategy : str
        爬取策略：'default' | 'category_first' | 'auto'
    enable_optimizations : bool
        是否启用性能优化
    category_config : dict, optional
        栏目配置参数
    
    Returns:
    --------
    List[Tuple[str, str]]
        (URL, 内容) 元组列表
        
    Raises:
    -------
    CrawlError
        爬取失败异常
    """
```

#### 政府网站检测接口
```python
def detect_government_site(url: str, html: str) -> bool:
    """
    检测是否为政府网站
    
    Parameters:
    -----------
    url : str
        网站URL
    html : str
        网页HTML内容
        
    Returns:
    --------
    bool
        是否为政府网站
        
    检测规则:
    - 域名检查：.gov.cn, .gov 等官方域名
    - HTML特征：政府网站特有的HTML结构和标识
    - 内容特征：政府机构名称、备案信息等
    """
```

#### 栏目识别接口
```python
@dataclass
class Category:
    """网站栏目数据结构"""
    name: str          # 栏目名称
    url: str           # 栏目URL
    level: int         # 栏目层级
    parent: str        # 父栏目名称
    priority: int      # 优先级 (1-10, 数字越小优先级越高)

def extract_site_categories(url: str, html: str) -> List[Category]:
    """
    提取网站栏目结构
    
    Parameters:
    -----------
    url : str
        网站首页URL
    html : str
        首页HTML内容
        
    Returns:
    --------
    List[Category]
        栏目列表，按优先级排序
        
    识别策略:
    - 主导航菜单识别
    - 侧边栏菜单识别
    - 面包屑导航识别
    - 站点地图识别
    """
```

#### 栏目优先爬取接口
```python
@dataclass
class CategoryResult:
    """栏目爬取结果"""
    category: Category
    pages: List[Tuple[str, str]]
    status: str  # 'completed' | 'partial' | 'failed'
    error_msg: Optional[str] = None

def crawl_site_by_categories(
    start_url: str,
    categories: List[Category],
    **kwargs
) -> Iterator[CategoryResult]:
    """
    按栏目优先顺序爬取网站
    
    Parameters:
    -----------
    start_url : str
        网站首页URL
    categories : List[Category]
        栏目列表
    **kwargs
        其他爬取参数
        
    Yields:
    -------
    CategoryResult
        每个栏目的爬取结果
        
    特性:
    - 按栏目优先级顺序爬取
    - 支持渐进式结果输出
    - 单个栏目失败不影响其他栏目
    """
```

### 2.2 优化模块接口

#### 链接预过滤器
```python
class LinkPrefilter:
    """链接预过滤器"""
    
    def __init__(self, base_url: str, filters: List[str]):
        """
        初始化过滤器
        
        Parameters:
        -----------
        base_url : str
            基础URL，用于相对链接解析
        filters : List[str]
            过滤规则列表
        """
    
    def should_crawl(self, url: str) -> bool:
        """
        判断链接是否应该爬取
        
        Parameters:
        -----------
        url : str
            待检查的URL
            
        Returns:
        --------
        bool
            是否应该爬取
        """
        
    def filter_links(self, links: List[str]) -> List[str]:
        """
        批量过滤链接
        
        Parameters:
        -----------
        links : List[str]
            链接列表
            
        Returns:
        --------
        List[str]
            过滤后的链接列表
        """
```

#### 内存管理器
```python
class MemoryManager:
    """内存管理器"""
    
    def __init__(self, max_memory_mb: int = 100):
        """
        初始化内存管理器
        
        Parameters:
        -----------
        max_memory_mb : int
            最大内存使用限制（MB）
        """
    
    def add_content(self, url: str, content: str) -> None:
        """
        添加内容到缓存
        
        Parameters:
        -----------
        url : str
            页面URL
        content : str
            页面内容
        """
    
    def flush_to_disk(self, filepath: str) -> None:
        """
        将缓存内容写入磁盘
        
        Parameters:
        -----------
        filepath : str
            输出文件路径
        """
    
    def get_memory_usage(self) -> Dict[str, int]:
        """
        获取内存使用统计
        
        Returns:
        --------
        Dict[str, int]
            内存使用统计信息
        """
```

## 3. 数据流设计

### 3.1 默认策略数据流
```
输入URL → 链接预过滤 → BFS队列 → 内容提取 → 批量输出
    ↓           ↓         ↓         ↓         ↓
  验证URL    过滤无效   去重处理   文本提取   内存管理
```

### 3.2 栏目优先策略数据流
```
输入URL → 网站类型检测 → 栏目识别 → 栏目优先队列 → 分栏目爬取 → 聚合输出
    ↓         ↓           ↓         ↓           ↓         ↓
  验证URL   检测政府站   提取导航   优先级排序   单栏目BFS   结果合并
```

## 4. 配置规格

### 4.1 爬取策略配置
```python
CRAWL_STRATEGIES = {
    'default': {
        'description': '默认BFS策略',
        'class': 'DefaultCrawlStrategy',
        'config': {
            'enable_prefilter': True,
            'enable_memory_opt': True
        }
    },
    'category_first': {
        'description': '栏目优先策略',
        'class': 'CategoryFirstStrategy', 
        'config': {
            'detect_government': True,
            'extract_categories': True,
            'fallback_strategy': 'default'
        }
    },
    'auto': {
        'description': '自动选择策略',
        'class': 'AutoStrategy',
        'config': {
            'government_use_category': True,
            'default_strategy': 'default'
        }
    }
}
```

### 4.2 优化配置
```python
OPTIMIZATION_CONFIG = {
    'link_prefilter': {
        'enabled': True,
        'rules': [
            'documentation_url_filter',
            'file_extension_filter',
            'external_link_filter'
        ]
    },
    'memory_management': {
        'enabled': True,
        'max_memory_mb': 100,
        'flush_threshold': 50,
        'batch_size': 10
    },
    'performance': {
        'batch_link_processing': True,
        'async_content_extraction': False,  # 保守配置
        'connection_pool': True
    }
}
```

### 4.3 政府网站配置
```python
GOVERNMENT_SITE_CONFIG = {
    'detection': {
        'domain_patterns': ['.gov.cn', '.gov'],
        'html_indicators': [
            'class="gov-header"',
            'id="government-nav"',
            '政府网站标识码',
            'ICP备案'
        ]
    },
    'category_extraction': {
        'nav_selectors': [
            '.main-nav ul li a',
            '.nav-menu a',
            '#navigation a',
            '.menu-item a'
        ],
        'priority_keywords': [
            '通知公告', '新闻动态', '政务公开',
            '办事服务', '政民互动'
        ]
    }
}
```

## 5. 错误处理规格

### 5.1 异常层次结构
```python
class CrawlError(Exception):
    """爬取异常基类"""

class StrategyError(CrawlError):
    """策略执行异常"""

class DetectionError(CrawlError):
    """网站检测异常"""

class CategoryError(CrawlError):
    """栏目识别异常"""

class NetworkError(CrawlError):
    """网络异常"""
```

### 5.2 错误处理策略
```python
ERROR_HANDLING_STRATEGY = {
    'detection_failure': {
        'action': 'fallback_to_default',
        'log_level': 'warning',
        'retry': False
    },
    'category_extraction_failure': {
        'action': 'fallback_to_default',
        'log_level': 'warning',
        'retry': True,
        'max_retries': 1
    },
    'network_timeout': {
        'action': 'retry',
        'log_level': 'info',
        'retry': True,
        'max_retries': 3,
        'backoff_factor': 1.5
    },
    'memory_overflow': {
        'action': 'flush_and_continue',
        'log_level': 'warning',
        'retry': False
    }
}
```

## 6. 性能指标和监控

### 6.1 性能指标定义
```python
@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    crawl_duration: float      # 爬取总时长（秒）
    pages_crawled: int         # 爬取页面数
    pages_per_second: float    # 爬取速度（页面/秒）
    memory_peak_mb: float      # 内存峰值使用（MB）
    memory_avg_mb: float       # 平均内存使用（MB）
    network_requests: int      # 网络请求总数
    failed_requests: int       # 失败请求数
    duplicate_urls: int        # 重复URL数
    filtered_urls: int         # 过滤URL数
    strategy_used: str         # 使用的策略
    fallback_count: int        # 降级次数
```

### 6.2 监控点设计
```python
class PerformanceMonitor:
    """性能监控器"""
    
    def start_monitoring(self) -> None:
        """开始监控"""
        
    def record_page_crawled(self, url: str, duration: float) -> None:
        """记录页面爬取"""
        
    def record_memory_usage(self) -> None:
        """记录内存使用"""
        
    def record_strategy_change(self, old: str, new: str) -> None:
        """记录策略变更"""
        
    def get_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        
    def generate_report(self) -> str:
        """生成性能报告"""
```

## 7. 实施检查点

### 7.1 阶段1检查点（基础优化）
- [ ] 链接预过滤器实现并测试
- [ ] 批量链接处理实现并测试
- [ ] 内存管理器实现并测试
- [ ] 性能基准测试通过
- [ ] 向后兼容性测试通过

### 7.2 阶段2检查点（栏目优先）
- [ ] 政府网站检测器实现并测试
- [ ] 栏目识别器实现并测试
- [ ] 栏目优先策略实现并测试
- [ ] 策略降级机制实现并测试
- [ ] 端到端集成测试通过

### 7.3 最终交付检查点
- [ ] 所有单元测试通过
- [ ] 性能测试达标
- [ ] 代码质量检查通过
- [ ] 文档完整
- [ ] 部署验证通过

这个架构规格提供了完整的技术实施蓝图，确保开发团队能够按照统一的标准和接口进行实施。