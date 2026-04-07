#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译统计数据类

类型安全的编译统计信息，包含计算属性。

作者：远
日期：2026-04-07
"""

from dataclasses import dataclass, field
import time


@dataclass
class CompilationStats:
    """编译统计数据类
    
    类型安全的编译统计信息，包含计算属性。
    
    Attributes:
        files_processed: 已处理文件数
        total_lines: 总行数
        cache_hits: 缓存命中次数
        cache_misses: 缓存未命中次数
        start_time: 开始时间戳
        parsed_files: 已解析文件数
        converted_files: 已转换文件数
        dependency_analyzed: 已分析依赖数
    
    Example:
        >>> stats = CompilationStats()
        >>> stats.files_processed = 10
        >>> stats.total_lines = 500
        >>> print(stats.summary())
    """
    
    # 文件统计
    files_processed: int = 0
    total_lines: int = 0
    
    # 缓存统计
    cache_hits: int = 0
    cache_misses: int = 0
    
    # 时间统计
    start_time: float = field(default_factory=time.time)
    
    # 解析统计
    parsed_files: int = 0
    converted_files: int = 0
    dependency_analyzed: int = 0
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率（百分比）"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    @property
    def avg_lines_per_file(self) -> float:
        """平均每文件行数"""
        if self.files_processed == 0:
            return 0.0
        return self.total_lines / self.files_processed
    
    @property
    def files_per_second(self) -> float:
        """文件处理吞吐量"""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.files_processed / elapsed
    
    def reset(self) -> None:
        """重置统计"""
        self.files_processed = 0
        self.total_lines = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.parsed_files = 0
        self.converted_files = 0
        self.dependency_analyzed = 0
        self.start_time = time.time()
    
    def summary(self) -> str:
        """生成统计摘要
        
        Returns:
            统计摘要字符串
        """
        return f"""📊 编译统计:
  文件数: {self.files_processed}
  总行数: {self.total_lines}
  缓存命中率: {self.cache_hit_rate:.1f}%
  平均行数/文件: {self.avg_lines_per_file:.1f}
  处理速度: {self.files_per_second:.2f} 文件/秒
  耗时: {self.elapsed_time:.2f}秒"""
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.summary()
    
    def to_dict(self) -> dict:
        """转换为字典
        
        Returns:
            包含所有统计信息的字典
        """
        return {
            'files_processed': self.files_processed,
            'total_lines': self.total_lines,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'elapsed_time': self.elapsed_time,
            'cache_hit_rate': self.cache_hit_rate,
            'avg_lines_per_file': self.avg_lines_per_file,
            'files_per_second': self.files_per_second,
            'parsed_files': self.parsed_files,
            'converted_files': self.converted_files,
            'dependency_analyzed': self.dependency_analyzed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CompilationStats":
        """从字典创建统计实例
        
        Args:
            data: 包含统计信息的字典
            
        Returns:
            CompilationStats 实例
        """
        return cls(
            files_processed=data.get('files_processed', 0),
            total_lines=data.get('total_lines', 0),
            cache_hits=data.get('cache_hits', 0),
            cache_misses=data.get('cache_misses', 0),
            parsed_files=data.get('parsed_files', 0),
            converted_files=data.get('converted_files', 0),
            dependency_analyzed=data.get('dependency_analyzed', 0),
        )
