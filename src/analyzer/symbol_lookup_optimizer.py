#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符号查找优化器 - Symbol Lookup Optimizer

功能：
1. 全局符号哈希表 - O(1)查找
2. 符号访问热点分析
3. 查找路径缓存
4. 增量符号表更新

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import time


@dataclass
class SymbolAccess:
    """符号访问记录"""
    symbol_name: str
    scope_chain: List[str]  # 作用域链
    timestamp: float
    found: bool
    lookup_time_ms: float  # 查找耗时（毫秒）


@dataclass
class HotSymbol:
    """热点符号"""
    name: str
    access_count: int
    avg_lookup_time_ms: float
    last_access: float
    scope_path: List[str]


@dataclass
class LookupStatistics:
    """查找统计"""
    total_lookups: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time_ms: float = 0.0
    hot_symbols: List[str] = field(default_factory=list)
    
    @property
    def avg_time_ms(self) -> float:
        """平均查找时间"""
        return self.total_time_ms / self.total_lookups if self.total_lookups > 0 else 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        return self.cache_hits / self.total_lookups if self.total_lookups > 0 else 0.0


class SymbolLookupOptimizer:
    """符号查找优化器
    
    优化策略：
    1. 全局符号哈希表 - 直接映射，O(1)查找
    2. 热点符号缓存 - 缓存频繁访问的符号
    3. 查找路径记忆 - 记住成功查找的路径
    4. 增量更新 - 只更新变化的符号
    """
    
    def __init__(self):
        """初始化符号查找优化器"""
        # 全局符号哈希表（核心优化）
        self._global_symbol_table: Dict[str, Any] = {}
        
        # 符号到作用域的映射
        self._symbol_to_scopes: Dict[str, Set[str]] = defaultdict(set)
        
        # 作用域到符号的映射
        self._scope_to_symbols: Dict[str, Set[str]] = defaultdict(set)
        
        # 访问记录
        self._access_history: List[SymbolAccess] = []
        
        # 热点符号缓存（访问次数 > 阈值）
        self._hot_symbols: Dict[str, HotSymbol] = {}
        self._hot_threshold = 5  # 热点阈值
        
        # 查找路径缓存（记住成功查找的路径）
        self._lookup_path_cache: Dict[str, List[str]] = {}
        
        # 统计信息
        self.stats = LookupStatistics()
        
        # 作用域层次结构
        self._scope_hierarchy: Dict[str, str] = {}  # child -> parent
    
    # ==================== 核心优化接口 ====================
    
    def register_symbol(
        self,
        symbol_name: str,
        scope_name: str,
        symbol_info: Any,
        parent_scope: Optional[str] = None
    ) -> None:
        """
        注册符号（O(1)复杂度）
        
        Args:
            symbol_name: 符号名
            scope_name: 所在作用域名
            symbol_info: 符号信息
            parent_scope: 父作用域名
        """
        # 添加到全局符号表
        self._global_symbol_table[symbol_name] = symbol_info
        
        # 更新映射关系
        self._symbol_to_scopes[symbol_name].add(scope_name)
        self._scope_to_symbols[scope_name].add(symbol_name)
        
        # 更新作用域层次
        if parent_scope:
            self._scope_hierarchy[scope_name] = parent_scope
    
    def lookup_symbol(self, symbol_name: str) -> Optional[Any]:
        """
        查找符号（优化版）
        
        Args:
            symbol_name: 符号名
            
        Returns:
            符号信息，未找到返回None
        """
        start_time = time.time()
        self.stats.total_lookups += 1
        
        # 1. 先在热点缓存中查找
        if symbol_name in self._hot_symbols:
            self.stats.cache_hits += 1
            lookup_time = (time.time() - start_time) * 1000
            self._record_access(symbol_name, [], True, lookup_time)
            return self._global_symbol_table.get(symbol_name)
        
        # 2. 在全局符号表中查找
        if symbol_name in self._global_symbol_table:
            self.stats.cache_hits += 1
            lookup_time = (time.time() - start_time) * 1000
            self._record_access(symbol_name, [], True, lookup_time)
            return self._global_symbol_table[symbol_name]
        
        # 3. 未找到
        self.stats.cache_misses += 1
        lookup_time = (time.time() - start_time) * 1000
        self._record_access(symbol_name, [], False, lookup_time)
        return None
    
    def lookup_symbol_in_scope(
        self,
        symbol_name: str,
        current_scope: str,
        scope_chain: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        在作用域链中查找符号
        
        Args:
            symbol_name: 符号名
            current_scope: 当前作用域
            scope_chain: 作用域链（可选，用于优化）
            
        Returns:
            符号信息，未找到返回None
        """
        start_time = time.time()
        self.stats.total_lookups += 1
        
        # 1. 检查查找路径缓存
        cache_key = f"{symbol_name}@{current_scope}"
        if cache_key in self._lookup_path_cache:
            # 使用缓存的路径直接查找
            cached_path = self._lookup_path_cache[cache_key]
            for scope in cached_path:
                if scope in self._scope_to_symbols:
                    if symbol_name in self._scope_to_symbols[scope]:
                        self.stats.cache_hits += 1
                        lookup_time = (time.time() - start_time) * 1000
                        self._record_access(symbol_name, cached_path, True, lookup_time)
                        return self._global_symbol_table.get(symbol_name)
        
        # 2. 遍历作用域链查找
        if scope_chain is None:
            scope_chain = self._build_scope_chain(current_scope)
        
        for scope in scope_chain:
            if scope in self._scope_to_symbols:
                if symbol_name in self._scope_to_symbols[scope]:
                    # 找到了，缓存查找路径
                    self._lookup_path_cache[cache_key] = scope_chain
                    self.stats.cache_hits += 1
                    lookup_time = (time.time() - start_time) * 1000
                    self._record_access(symbol_name, scope_chain, True, lookup_time)
                    return self._global_symbol_table.get(symbol_name)
        
        # 3. 未找到
        self.stats.cache_misses += 1
        lookup_time = (time.time() - start_time) * 1000
        self._record_access(symbol_name, scope_chain, False, lookup_time)
        return None
    
    # ==================== 增量更新 ====================
    
    def update_symbol(
        self,
        symbol_name: str,
        symbol_info: Any
    ) -> None:
        """
        更新符号（增量更新）
        
        Args:
            symbol_name: 符号名
            symbol_info: 新的符号信息
        """
        self._global_symbol_table[symbol_name] = symbol_info
    
    def remove_symbol(self, symbol_name: str) -> bool:
        """
        移除符号
        
        Args:
            symbol_name: 符号名
            
        Returns:
            是否成功移除
        """
        if symbol_name not in self._global_symbol_table:
            return False
        
        # 从全局表中移除
        del self._global_symbol_table[symbol_name]
        
        # 从映射中移除
        if symbol_name in self._symbol_to_scopes:
            scopes = self._symbol_to_scopes[symbol_name]
            for scope in scopes:
                if scope in self._scope_to_symbols:
                    self._scope_to_symbols[scope].discard(symbol_name)
            del self._symbol_to_scopes[symbol_name]
        
        # 从热点中移除
        if symbol_name in self._hot_symbols:
            del self._hot_symbols[symbol_name]
        
        # 清除查找路径缓存
        keys_to_remove = [
            key for key in self._lookup_path_cache
            if symbol_name in key
        ]
        for key in keys_to_remove:
            del self._lookup_path_cache[key]
        
        return True
    
    def clear_scope(self, scope_name: str) -> int:
        """
        清空作用域中的所有符号
        
        Args:
            scope_name: 作用域名
            
        Returns:
            移除的符号数量
        """
        if scope_name not in self._scope_to_symbols:
            return 0
        
        removed = 0
        symbols = list(self._scope_to_symbols[scope_name])
        
        for symbol_name in symbols:
            if self.remove_symbol(symbol_name):
                removed += 1
        
        return removed
    
    # ==================== 热点分析 ====================
    
    def analyze_hot_symbols(self, top_n: int = 10) -> List[HotSymbol]:
        """
        分析热点符号
        
        Args:
            top_n: 返回前N个热点符号
            
        Returns:
            热点符号列表
        """
        # 统计访问次数
        access_counts: Dict[str, List[float]] = defaultdict(list)
        
        for access in self._access_history:
            if access.found:
                access_counts[access.symbol_name].append(access.lookup_time_ms)
        
        # 计算热点符号
        hot_list = []
        for symbol_name, times in access_counts.items():
            if len(times) >= self._hot_threshold:
                avg_time = sum(times) / len(times)
                last_access = max(
                    (a.timestamp for a in self._access_history 
                     if a.symbol_name == symbol_name),
                    default=0
                )
                
                hot_symbol = HotSymbol(
                    name=symbol_name,
                    access_count=len(times),
                    avg_lookup_time_ms=avg_time,
                    last_access=last_access,
                    scope_path=list(self._symbol_to_scopes.get(symbol_name, []))
                )
                hot_list.append(hot_symbol)
                
                # 更新热点缓存
                self._hot_symbols[symbol_name] = hot_symbol
        
        # 按访问次数排序
        hot_list.sort(key=lambda x: x.access_count, reverse=True)
        
        # 更新统计
        self.stats.hot_symbols = [s.name for s in hot_list[:top_n]]
        
        return hot_list[:top_n]
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取查找统计信息"""
        return {
            "total_lookups": self.stats.total_lookups,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            "cache_hit_rate": f"{self.stats.cache_hit_rate:.2%}",
            "avg_lookup_time_ms": f"{self.stats.avg_time_ms:.3f}",
            "total_time_ms": f"{self.stats.total_time_ms:.1f}",
            "global_symbol_count": len(self._global_symbol_table),
            "hot_symbol_count": len(self._hot_symbols),
            "hot_symbols": self.stats.hot_symbols[:10],
            "scope_count": len(self._scope_to_symbols)
        }
    
    def print_statistics(self) -> None:
        """打印查找统计信息"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print("符号查找优化器统计")
        print("=" * 70)
        
        print(f"\n📊 查找性能:")
        print(f"  总查找: {stats['total_lookups']}")
        print(f"  缓存命中: {stats['cache_hits']}")
        print(f"  缓存未中: {stats['cache_misses']}")
        print(f"  命中率: {stats['cache_hit_rate']}")
        print(f"  平均耗时: {stats['avg_lookup_time_ms']} ms")
        print(f"  总耗时: {stats['total_time_ms']} ms")
        
        print(f"\n🔥 热点符号:")
        for i, symbol in enumerate(stats['hot_symbols'], 1):
            print(f"  {i}. {symbol}")
        
        print(f"\n📦 符号表大小:")
        print(f"  全局符号: {stats['global_symbol_count']}")
        print(f"  热点符号: {stats['hot_symbol_count']}")
        print(f"  作用域数: {stats['scope_count']}")
        
        print("=" * 70)
    
    # ==================== 内部方法 ====================
    
    def _record_access(
        self,
        symbol_name: str,
        scope_chain: List[str],
        found: bool,
        lookup_time_ms: float
    ) -> None:
        """记录访问"""
        access = SymbolAccess(
            symbol_name=symbol_name,
            scope_chain=scope_chain,
            timestamp=time.time(),
            found=found,
            lookup_time_ms=lookup_time_ms
        )
        
        self._access_history.append(access)
        self.stats.total_time_ms += lookup_time_ms
        
        # 限制历史记录大小
        if len(self._access_history) > 10000:
            # 保留最近的一半
            self._access_history = self._access_history[-5000:]
    
    def _build_scope_chain(self, current_scope: str) -> List[str]:
        """构建作用域链"""
        chain = [current_scope]
        
        # 向上查找父作用域
        scope = current_scope
        while scope in self._scope_hierarchy:
            scope = self._scope_hierarchy[scope]
            chain.append(scope)
        
        return chain
    
    def reset(self) -> None:
        """重置优化器"""
        self._global_symbol_table.clear()
        self._symbol_to_scopes.clear()
        self._scope_to_symbols.clear()
        self._access_history.clear()
        self._hot_symbols.clear()
        self._lookup_path_cache.clear()
        self._scope_hierarchy.clear()
        
        self.stats = LookupStatistics()


# 全局符号查找优化器实例
_global_symbol_optimizer: Optional[SymbolLookupOptimizer] = None


def get_global_optimizer() -> SymbolLookupOptimizer:
    """获取全局符号查找优化器"""
    global _global_symbol_optimizer
    if _global_symbol_optimizer is None:
        _global_symbol_optimizer = SymbolLookupOptimizer()
    return _global_symbol_optimizer


def reset_global_optimizer() -> None:
    """重置全局符号查找优化器"""
    global _global_symbol_optimizer
    if _global_symbol_optimizer:
        _global_symbol_optimizer.reset()
    _global_symbol_optimizer = None