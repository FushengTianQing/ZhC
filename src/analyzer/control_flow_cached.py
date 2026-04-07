"""
ZHC编译器 - 控制流分析器(带缓存)

功能：
1. 构建控制流图（CFG）（带缓存）
2. 分析基本块（带缓存）
3. 检测不可达代码（带缓存）
4. 识别循环结构（带缓存）
5. 计算复杂度指标（带缓存）

性能优化：
- CFG缓存避免重复构建
- 分析结果缓存避免重复计算
- 增量更新支持

作者：阿福
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time

# 导入基础控制流分析器
from .control_flow import (
    ControlFlowAnalyzer,
    ControlFlowGraph,
    CFGNode,
    BasicBlock,
    NodeType,
    EdgeType,
    LoopInfo,
    FlowIssue
)


@dataclass
class CFGCacheEntry:
    """CFG缓存条目"""
    cfg: ControlFlowGraph
    source_hash: str
    build_time: float
    access_count: int = 0
    last_access: float = 0.0


@dataclass
class AnalysisCacheEntry:
    """分析结果缓存条目"""
    result: any  # 分析结果
    cfg_hash: str  # CFG状态哈希
    compute_time: float
    access_count: int = 0


class ControlFlowAnalyzerCached(ControlFlowAnalyzer):
    """带缓存的控制流分析器"""
    
    def __init__(self, cache_size: int = 100):
        """
        初始化带缓存的控制流分析器
        
        Args:
            cache_size: CFG缓存大小限制
        """
        super().__init__()
        
        # 缓存配置
        self.cache_size = cache_size
        
        # CFG缓存
        self._cfg_cache: Dict[str, CFGCacheEntry] = {}
        
        # 分析结果缓存
        self._unreachable_cache: Dict[str, AnalysisCacheEntry] = {}
        self._complexity_cache: Dict[str, AnalysisCacheEntry] = {}
        self._dominance_cache: Dict[str, AnalysisCacheEntry] = {}
        self._loops_cache: Dict[str, AnalysisCacheEntry] = {}
        
        # 缓存统计
        self._cache_hits = 0
        self._cache_misses = 0
        
        # 哈希缓存
        self._hash_cache: Dict[int, str] = {}
    
    def _compute_hash(self, source: str) -> str:
        """计算源码哈希"""
        source_id = id(source)
        
        if source_id in self._hash_cache:
            return self._hash_cache[source_id]
        
        hash_val = hashlib.md5(source.encode()).hexdigest()
        self._hash_cache[source_id] = hash_val
        return hash_val
    
    def _get_cfg_from_cache(
        self,
        func_name: str,
        source: str
    ) -> Optional[ControlFlowGraph]:
        """从缓存获取CFG"""
        source_hash = self._compute_hash(source)
        
        if func_name in self._cfg_cache:
            entry = self._cfg_cache[func_name]
            if entry.source_hash == source_hash:
                # 缓存命中
                self._cache_hits += 1
                entry.access_count += 1
                entry.last_access = time.time()
                return entry.cfg
        
        # 缓存未命中
        self._cache_misses += 1
        return None
    
    def _put_cfg_to_cache(
        self,
        func_name: str,
        cfg: ControlFlowGraph,
        source: str
    ):
        """将CFG存入缓存"""
        # LRU淘汰
        if len(self._cfg_cache) >= self.cache_size:
            self._evict_lru(self._cfg_cache)
        
        source_hash = self._compute_hash(source)
        self._cfg_cache[func_name] = CFGCacheEntry(
            cfg=cfg,
            source_hash=source_hash,
            build_time=time.time(),
            access_count=1,
            last_access=time.time()
        )
    
    def _evict_lru(self, cache: Dict[str, CFGCacheEntry]):
        """LRU淘汰策略"""
        if not cache:
            return
        
        # 找到访问次数最少的条目
        lru_key = min(cache.keys(), key=lambda k: cache[k].access_count)
        del cache[lru_key]
    
    # ==================== 带缓存的CFG构建 ====================
    
    def build_cfg_cached(
        self,
        func_name: str,
        statements: List[dict],
        source: str = ""
    ) -> ControlFlowGraph:
        """
        带缓存的CFG构建
        
        Args:
            func_name: 函数名
            statements: 语句列表
            source: 源码内容（用于缓存）
        
        Returns:
            控制流图
        """
        # 如果提供了源码，尝试从缓存获取
        if source:
            cached_cfg = self._get_cfg_from_cache(func_name, source)
            if cached_cfg:
                return cached_cfg
        
        # 构建CFG
        cfg = super().build_cfg(func_name, statements)
        
        # 存入缓存
        if source:
            self._put_cfg_to_cache(func_name, cfg, source)
        
        return cfg
    
    # ==================== 带缓存的分析方法 ====================
    
    def detect_unreachable_code_cached(
        self,
        cfg: ControlFlowGraph
    ) -> List[FlowIssue]:
        """
        带缓存的不可达代码检测
        
        Args:
            cfg: 控制流图
        
        Returns:
            不可达代码问题列表
        """
        cache_key = f"{cfg.func_name}:unreachable"
        cfg_hash = self._compute_cfg_hash(cfg)
        
        # 尝试从缓存获取
        if cache_key in self._unreachable_cache:
            entry = self._unreachable_cache[cache_key]
            if entry.cfg_hash == cfg_hash:
                self._cache_hits += 1
                entry.access_count += 1
                return entry.result
        
        # 执行分析
        self._cache_misses += 1
        start_time = time.time()
        result = super().detect_unreachable_code(cfg)
        compute_time = time.time() - start_time
        
        # 存入缓存
        self._unreachable_cache[cache_key] = AnalysisCacheEntry(
            result=result,
            cfg_hash=cfg_hash,
            compute_time=compute_time,
            access_count=1
        )
        
        return result
    
    def compute_cyclomatic_complexity_cached(
        self,
        cfg: ControlFlowGraph
    ) -> int:
        """
        带缓存的圈复杂度计算
        
        Args:
            cfg: 控制流图
        
        Returns:
            圈复杂度
        """
        cache_key = f"{cfg.func_name}:complexity"
        cfg_hash = self._compute_cfg_hash(cfg)
        
        # 尝试从缓存获取
        if cache_key in self._complexity_cache:
            entry = self._complexity_cache[cache_key]
            if entry.cfg_hash == cfg_hash:
                self._cache_hits += 1
                entry.access_count += 1
                return entry.result
        
        # 执行计算
        self._cache_misses += 1
        start_time = time.time()
        result = super().compute_cyclomatic_complexity(cfg)
        compute_time = time.time() - start_time
        
        # 存入缓存
        self._complexity_cache[cache_key] = AnalysisCacheEntry(
            result=result,
            cfg_hash=cfg_hash,
            compute_time=compute_time,
            access_count=1
        )
        
        return result
    
    def detect_infinite_loops_cached(
        self,
        cfg: ControlFlowGraph
    ) -> List[FlowIssue]:
        """
        带缓存的无限循环检测
        
        Args:
            cfg: 控制流图
        
        Returns:
            无限循环问题列表
        """
        cache_key = f"{cfg.func_name}:loops"
        cfg_hash = self._compute_cfg_hash(cfg)
        
        # 尝试从缓存获取
        if cache_key in self._loops_cache:
            entry = self._loops_cache[cache_key]
            if entry.cfg_hash == cfg_hash:
                self._cache_hits += 1
                entry.access_count += 1
                return entry.result
        
        # 执行分析
        self._cache_misses += 1
        start_time = time.time()
        result = super().detect_infinite_loops(cfg)
        compute_time = time.time() - start_time
        
        # 存入缓存
        self._loops_cache[cache_key] = AnalysisCacheEntry(
            result=result,
            cfg_hash=cfg_hash,
            compute_time=compute_time,
            access_count=1
        )
        
        return result
    
    def compute_dominance_tree_cached(
        self,
        cfg: ControlFlowGraph
    ) -> Dict[str, Set[str]]:
        """
        带缓存的支配树计算
        
        Args:
            cfg: 控制流图
        
        Returns:
            支配关系字典
        """
        cache_key = f"{cfg.func_name}:dominance"
        cfg_hash = self._compute_cfg_hash(cfg)
        
        # 尝试从缓存获取
        if cache_key in self._dominance_cache:
            entry = self._dominance_cache[cache_key]
            if entry.cfg_hash == cfg_hash:
                self._cache_hits += 1
                entry.access_count += 1
                return entry.result
        
        # 执行计算
        self._cache_misses += 1
        start_time = time.time()
        result = super().compute_dominance_tree(cfg)
        compute_time = time.time() - start_time
        
        # 存入缓存
        self._dominance_cache[cache_key] = AnalysisCacheEntry(
            result=result,
            cfg_hash=cfg_hash,
            compute_time=compute_time,
            access_count=1
        )
        
        return result
    
    # ==================== 辅助方法 ====================
    
    def _compute_cfg_hash(self, cfg: ControlFlowGraph) -> str:
        """
        计算CFG状态哈希
        
        Args:
            cfg: 控制流图
        
        Returns:
            CFG状态哈希
        """
        # 简化：使用节点数和边数计算哈希
        state = f"{cfg.func_name}:{len(cfg.nodes)}:{len(cfg.loops)}"
        
        # 添加边信息
        for node_id, node in sorted(cfg.nodes.items()):
            state += f":{node_id}:{len(node.successors)}"
        
        return hashlib.md5(state.encode()).hexdigest()
    
    # ==================== 缓存管理 ====================
    
    def clear_cache(self):
        """清空所有缓存"""
        self._cfg_cache.clear()
        self._unreachable_cache.clear()
        self._complexity_cache.clear()
        self._dominance_cache.clear()
        self._loops_cache.clear()
        self._hash_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def invalidate_function(self, func_name: str):
        """
        使指定函数的缓存失效
        
        Args:
            func_name: 函数名
        """
        # 删除CFG缓存
        if func_name in self._cfg_cache:
            del self._cfg_cache[func_name]
        
        # 删除分析结果缓存
        prefix = f"{func_name}:"
        for cache in [
            self._unreachable_cache,
            self._complexity_cache,
            self._dominance_cache,
            self._loops_cache
        ]:
            keys_to_remove = [k for k in cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del cache[key]
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'total_requests': total_requests,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'cfg_cache_size': len(self._cfg_cache),
            'unreachable_cache_size': len(self._unreachable_cache),
            'complexity_cache_size': len(self._complexity_cache),
            'dominance_cache_size': len(self._dominance_cache),
            'loops_cache_size': len(self._loops_cache),
        }
    
    def get_cache_report(self) -> str:
        """生成缓存报告"""
        stats = self.get_cache_stats()
        
        lines = [
            "=" * 70,
            "控制流分析器缓存报告",
            "=" * 70,
            "",
            f"总请求数: {stats['total_requests']}",
            f"缓存命中: {stats['cache_hits']}",
            f"缓存未命中: {stats['cache_misses']}",
            f"命中率: {stats['hit_rate']:.2%}",
            "",
            f"CFG缓存: {stats['cfg_cache_size']} 个",
            f"不可达代码缓存: {stats['unreachable_cache_size']} 个",
            f"圈复杂度缓存: {stats['complexity_cache_size']} 个",
            f"支配树缓存: {stats['dominance_cache_size']} 个",
            f"循环检测缓存: {stats['loops_cache_size']} 个",
            "",
            "=" * 70,
        ]
        
        return "\n".join(lines)


# 兼容性别名
ControlFlowAnalyzerOptimized = ControlFlowAnalyzerCached