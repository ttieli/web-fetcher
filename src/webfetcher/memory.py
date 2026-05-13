"""
V2 域名记忆 + 结构化日志

- DomainMemory: 记录每个域名的最佳提取策略和抓取方式
- ExtractionLogger: JSONL 格式结构化日志
"""

import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# 配置目录
CONFIG_DIR = Path(os.path.expanduser('~/.config/webfetcher'))
MEMORY_FILE = CONFIG_DIR / 'domain_memory.json'
LOG_FILE = CONFIG_DIR / 'extraction_log.jsonl'


class DomainMemory:
    """域名级策略记忆：记录每个域名的最佳 fetcher + extractor 组合"""

    def __init__(self, path: Path = None):
        self.path = path or MEMORY_FILE
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if self.path.exists():
                return json.loads(self.path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load domain memory: {e}")
        return {}

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
        except OSError as e:
            logger.warning(f"Failed to save domain memory: {e}")

    @staticmethod
    def get_domain(url: str) -> str:
        """提取主域名（去掉 www 前缀）"""
        try:
            host = urlparse(url).hostname or ''
            if host.startswith('www.'):
                host = host[4:]
            return host
        except Exception:
            return ''

    def lookup(self, url: str) -> dict | None:
        """
        查询域名记忆。

        Returns:
            dict with keys: best_extractor, best_fetcher, score, confidence,
                            needs_cdp, sample_count, last_updated
            or None if no record.
        """
        domain = self.get_domain(url)
        if not domain:
            return None
        record = self._data.get(domain)
        if not record:
            return None

        # 计算 confidence 等级
        sample_count = record.get('sample_count', 0)
        age_days = (time.time() - record.get('last_updated', 0)) / 86400
        confidence = self._calc_confidence(sample_count, age_days)
        return {**record, 'confidence': confidence}

    @staticmethod
    def _calc_confidence(sample_count: int, age_days: float) -> str:
        """
        置信度衰减：
        - high: ≥5 次且 <7 天
        - medium: ≥3 次且 <30 天
        - low: ≥1 次且 <90 天
        - stale: 超过 90 天
        """
        if sample_count >= 5 and age_days < 7:
            return 'high'
        if sample_count >= 3 and age_days < 30:
            return 'medium'
        if sample_count >= 1 and age_days < 90:
            return 'low'
        return 'stale'

    def update(self, url: str, *, fetcher: str, extractor: str,
               score: float, all_scores: dict = None):
        """
        更新域名记忆。

        Args:
            url: 来源 URL
            fetcher: 使用的抓取方式 (urllib/cdp/selenium)
            extractor: 竞赛优胜策略名
            score: 优胜分数
            all_scores: 所有策略的分数 {strategy: score}
        """
        domain = self.get_domain(url)
        if not domain:
            return

        existing = self._data.get(domain, {})
        sample_count = existing.get('sample_count', 0) + 1

        # 如果新分数更好或首次记录，更新最佳策略
        if score >= existing.get('score', 0) or sample_count == 1:
            self._data[domain] = {
                'best_extractor': extractor,
                'best_fetcher': fetcher,
                'score': score,
                'sample_count': sample_count,
                'needs_cdp': fetcher in ('cdp', 'selenium'),
                'all_scores': all_scores or {},
                'last_updated': time.time(),
            }
        else:
            # 仅更新采样次数和时间
            existing['sample_count'] = sample_count
            existing['last_updated'] = time.time()
            self._data[domain] = existing

        self._save()

    def get_stats(self) -> dict:
        """返回统计信息"""
        total = len(self._data)
        needs_cdp = sum(1 for r in self._data.values() if r.get('needs_cdp'))
        extractors = {}
        for r in self._data.values():
            ext = r.get('best_extractor', 'unknown')
            extractors[ext] = extractors.get(ext, 0) + 1
        return {
            'total_domains': total,
            'needs_cdp': needs_cdp,
            'extractor_distribution': extractors,
        }


class ExtractionLogger:
    """JSONL 格式结构化日志，用于事后分析"""

    def __init__(self, path: Path = None):
        self.path = path or LOG_FILE

    def log(self, *, url: str, domain: str, fetcher: str,
            fetch_ms: float, extractor_results: dict,
            winner: str, winner_score: float,
            quality_low: bool = False):
        """
        追加一条提取日志。

        Args:
            url: 来源 URL
            domain: 主域名
            fetcher: 抓取方式
            fetch_ms: 抓取耗时 (ms)
            extractor_results: {strategy: {score, chars}} 各策略结果摘要
            winner: 优胜策略名
            winner_score: 优胜分数
            quality_low: 是否检测到低质量
        """
        record = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'url': url,
            'domain': domain,
            'fetcher': fetcher,
            'fetch_ms': round(fetch_ms, 1),
            'results': extractor_results,
            'winner': winner,
            'winner_score': round(winner_score, 3),
            'quality_low': quality_low,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except OSError as e:
            logger.warning(f"Failed to write extraction log: {e}")

    def read_recent(self, n: int = 50) -> list[dict]:
        """读取最近 n 条日志"""
        try:
            if not self.path.exists():
                return []
            lines = self.path.read_text(encoding='utf-8').strip().split('\n')
            records = []
            for line in lines[-n:]:
                if line.strip():
                    records.append(json.loads(line))
            return records
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read extraction log: {e}")
            return []
