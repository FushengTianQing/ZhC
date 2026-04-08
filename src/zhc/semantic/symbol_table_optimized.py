#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化符号表 - Optimized Symbol Table

性能优化策略：
1. 全局符号哈希表 - O(1) 直接查找
2. 符号查找缓存 - 缓存查找结果，避免重复遍历
3. 作用域链预计算 - 预计算作用域链路径
4. 查找统计 - 性能监控

作者：远
日期：2026-04-07
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class ScopeType(Enum):
    """作用域类型"""

    GLOBAL = "全局"
    MODULE = "模块"
    STRUCT = "结构体"
    FUNCTION = "函数"
    BLOCK = "代码块"
    LOOP = "循环"


@dataclass
class Symbol:
    """符号信息"""

    name: str = ""
    symbol_type: str = ""  # 变量、函数、结构体、参数等
    data_type: Optional[str] = None
    scope_level: int = 0
    scope_type: ScopeType = ScopeType.GLOBAL
    is_defined: bool = False
    is_used: bool = False
    definition_location: Optional[str] = None
    references: List[str] = field(default_factory=list)

    # 函数特有信息
    parameters: List["Symbol"] = field(default_factory=list)
    return_type: Optional[str] = None

    # 结构体特有信息
    members: List["Symbol"] = field(default_factory=list)
    methods: List["Symbol"] = field(default_factory=list)
    parent_struct: Optional[str] = None

    # 重载支持
    _overloads: List["Symbol"] = field(default_factory=list)


@dataclass
class LookupStats:
    """查找统计"""

    total_lookups: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    global_table_hits: int = 0
    scope_chain_lookups: int = 0
    total_time_ms: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        return self.cache_hits / self.total_lookups if self.total_lookups > 0 else 0.0

    @property
    def avg_time_ms(self) -> float:
        return (
            self.total_time_ms / self.total_lookups if self.total_lookups > 0 else 0.0
        )


class OptimizedScope:
    """优化作用域"""

    def __init__(
        self,
        scope_type: ScopeType = ScopeType.GLOBAL,
        scope_name: str = "",
        parent: Optional["OptimizedScope"] = None,
        level: int = 0,
    ):
        self.scope_type = scope_type
        self.scope_name = scope_name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.level = level

        # 性能优化：预计算作用域链
        self._scope_chain: Optional[List["OptimizedScope"]] = None
        self._scope_chain_ids: Optional[Tuple[int, ...]] = None

        # 子作用域
        self.children: List["OptimizedScope"] = []

    def add_symbol(self, symbol: Symbol) -> bool:
        """添加符号到当前作用域"""
        if symbol.name in self.symbols:
            return False
        symbol.scope_level = self.level
        symbol.scope_type = self.scope_type
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """仅在当前作用域查找符号"""
        return self.symbols.get(name)

    def get_scope_chain(self) -> List["OptimizedScope"]:
        """获取作用域链（预计算）"""
        if self._scope_chain is None:
            chain = [self]
            current = self.parent
            while current:
                chain.append(current)
                current = current.parent
            self._scope_chain = chain
        return self._scope_chain

    def get_scope_chain_ids(self) -> Tuple[int, ...]:
        """获取作用域链 ID（用于缓存键）"""
        if self._scope_chain_ids is None:
            chain = self.get_scope_chain()
            self._scope_chain_ids = tuple(id(s) for s in chain)
        return self._scope_chain_ids

    def invalidate_chain_cache(self) -> None:
        """清除作用域链缓存"""
        self._scope_chain = None
        self._scope_chain_ids = None


class OptimizedSymbolTable:
    """优化符号表

    性能优化：
    1. 全局符号哈希表 - O(1) 直接查找
    2. 符号查找缓存 - 缓存查找结果
    3. 作用域链预计算 - 减少遍历开销
    4. 查找统计 - 性能监控
    """

    # 缓存大小限制
    CACHE_SIZE = 1024

    def __init__(self):
        # 全局作用域
        self.global_scope = OptimizedScope(
            scope_type=ScopeType.GLOBAL, scope_name="全局", level=0
        )
        self.current_scope = self.global_scope
        self.scope_stack: List[OptimizedScope] = [self.global_scope]

        # 全局符号表（核心优化：O(1) 查找）
        self.all_symbols: Dict[str, Symbol] = {}

        # 符号到作用域的映射（快速定位）
        self._symbol_to_scope: Dict[str, OptimizedScope] = {}

        # 查找缓存（符号名 + 作用域链 ID -> 符号）
        self._lookup_cache: Dict[Tuple[str, Tuple[int, ...]], Symbol] = {}

        # 查找统计
        self.stats = LookupStats()

        # 性能监控开关
        self.enable_stats: bool = True

    def enter_scope(
        self, scope_type: ScopeType, scope_name: str = ""
    ) -> OptimizedScope:
        """进入新作用域"""
        new_scope = OptimizedScope(
            scope_type=scope_type,
            scope_name=scope_name,
            parent=self.current_scope,
            level=self.current_scope.level + 1,
        )
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope

        # 添加到父作用域的子列表
        if self.current_scope.parent:
            self.current_scope.parent.children.append(new_scope)

        return new_scope

    def exit_scope(self) -> OptimizedScope:
        """退出当前作用域"""
        if len(self.scope_stack) <= 1:
            raise RuntimeError("无法退出全局作用域")

        exited = self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]

        # 清除退出作用域的缓存
        self._clear_scope_cache(exited)

        return self.current_scope

    def add_symbol(self, symbol: Symbol) -> bool:
        """在当前作用域添加符号"""
        existing = self.current_scope.lookup_local(symbol.name)
        if existing:
            # 函数重载支持
            if (
                existing.symbol_type == "函数"
                and symbol.symbol_type == "函数"
                and symbol.name == existing.name
            ):
                existing_sig = tuple(p.data_type for p in existing.parameters)
                new_sig = tuple(p.data_type for p in symbol.parameters)
                if existing_sig != new_sig:
                    if not hasattr(existing, "_overloads"):
                        existing._overloads = [existing]
                    existing._overloads.append(symbol)
                    key = f"{self.current_scope.scope_name}.{symbol.name}_{len(existing._overloads)}"
                    self.all_symbols[key] = symbol
                    self._symbol_to_scope[key] = self.current_scope
                    return True
                return False
            return False

        symbol.scope_level = self.current_scope.level
        symbol.scope_type = self.current_scope.scope_type
        self.current_scope.symbols[symbol.name] = symbol

        # 更新全局符号表和映射
        key = f"{self.current_scope.scope_name}.{symbol.name}"
        self.all_symbols[key] = symbol
        self.all_symbols[symbol.name] = symbol  # 同时存储简短名称
        self._symbol_to_scope[symbol.name] = self.current_scope

        # 清除相关缓存
        self._invalidate_cache_for_symbol(symbol.name)

        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        """查找符号（优化版）

        查找策略：
        1. 先检查全局符号表（O(1)）
        2. 再检查查找缓存
        3. 最后遍历作用域链
        """
        start_time = time.time() if self.enable_stats else 0

        if self.enable_stats:
            self.stats.total_lookups += 1

        # 优化1：直接从全局符号表查找（O(1)）
        # 注意：全局符号表可能包含多个同名符号（不同作用域）
        # 我们需要找到当前作用域可见的那个
        if name in self.all_symbols:
            symbol = self.all_symbols[name]
            # 检查是否在当前作用域链中可见
            scope_chain = self.current_scope.get_scope_chain()
            symbol_scope = self._symbol_to_scope.get(name)

            if symbol_scope and symbol_scope in scope_chain:
                if self.enable_stats:
                    self.stats.global_table_hits += 1
                    self.stats.cache_hits += 1
                    self.stats.total_time_ms += (time.time() - start_time) * 1000
                return symbol

        # 优化2：检查查找缓存
        cache_key = (name, self.current_scope.get_scope_chain_ids())
        if cache_key in self._lookup_cache:
            if self.enable_stats:
                self.stats.cache_hits += 1
                self.stats.total_time_ms += (time.time() - start_time) * 1000
            return self._lookup_cache[cache_key]

        # 优化3：遍历作用域链（预计算）
        if self.enable_stats:
            self.stats.scope_chain_lookups += 1

        scope_chain = self.current_scope.get_scope_chain()
        for scope in scope_chain:
            symbol = scope.symbols.get(name)
            if symbol:
                # 缓存查找结果
                self._lookup_cache[cache_key] = symbol
                if self.enable_stats:
                    self.stats.cache_misses += 1
                    self.stats.total_time_ms += (time.time() - start_time) * 1000
                return symbol

        # 未找到
        if self.enable_stats:
            self.stats.cache_misses += 1
            self.stats.total_time_ms += (time.time() - start_time) * 1000
        return None

    def lookup_all(self, name: str) -> List[Symbol]:
        """查找所有同名符号（用于函数重载）"""
        symbol = self.lookup(name)
        if symbol is None:
            return []
        if hasattr(symbol, "_overloads"):
            return list(symbol._overloads)
        return [symbol]

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """仅在当前作用域查找"""
        return self.current_scope.lookup_local(name)

    def get_unused_symbols(self) -> List[Symbol]:
        """获取未使用的符号"""
        return [s for s in self.all_symbols.values() if not s.is_used and s.is_defined]

    def get_statistics(self) -> Dict[str, Any]:
        """获取符号表统计信息"""
        return {
            "total_symbols": len(self.all_symbols),
            "scope_count": len(self.scope_stack),
            "current_scope": self.current_scope.scope_name,
            "cache_size": len(self._lookup_cache),
            "lookup_stats": {
                "total_lookups": self.stats.total_lookups,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "global_table_hits": self.stats.global_table_hits,
                "scope_chain_lookups": self.stats.scope_chain_lookups,
                "cache_hit_rate": f"{self.stats.cache_hit_rate:.2%}",
                "avg_time_ms": f"{self.stats.avg_time_ms:.3f}",
            },
        }

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._lookup_cache.clear()
        for scope in self.scope_stack:
            scope.invalidate_chain_cache()

    def _clear_scope_cache(self, scope: OptimizedScope) -> None:
        """清除与特定作用域相关的缓存"""
        # 清除包含该作用域 ID 的查找缓存
        scope_id = id(scope)
        keys_to_remove = [key for key in self._lookup_cache if scope_id in key[1]]
        for key in keys_to_remove:
            del self._lookup_cache[key]

        # 清除作用域链缓存
        scope.invalidate_chain_cache()

    def _invalidate_cache_for_symbol(self, symbol_name: str) -> None:
        """清除与特定符号相关的缓存"""
        keys_to_remove = [key for key in self._lookup_cache if key[0] == symbol_name]
        for key in keys_to_remove:
            del self._lookup_cache[key]

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = LookupStats()


# 性能对比测试函数
def benchmark_symbol_lookup(
    iterations: int = 1000, scope_depth: int = 10, symbols_per_scope: int = 50
) -> Dict[str, Any]:
    """符号查找性能基准测试

    Args:
        iterations: 查找迭代次数
        scope_depth: 作用域深度
        symbols_per_scope: 每个作用域的符号数量

    Returns:
        性能测试结果
    """
    import time

    # 创建优化符号表
    table = OptimizedSymbolTable()
    table.enable_stats = True

    # 创建深层作用域结构
    for i in range(scope_depth):
        table.enter_scope(ScopeType.BLOCK, f"block_{i}")
        # 添加符号
        for j in range(symbols_per_scope):
            symbol = Symbol(
                name=f"var_{i}_{j}",
                symbol_type="变量",
                data_type="整数型",
                is_defined=True,
            )
            table.add_symbol(symbol)

    # 测试查找性能
    test_symbols = [
        f"var_{i}_{j}" for i in range(scope_depth) for j in range(symbols_per_scope)
    ]

    # 预热
    for _ in range(100):
        for name in test_symbols[:10]:
            table.lookup(name)

    table.reset_stats()

    # 正式测试
    start_time = time.time()
    for _ in range(iterations):
        for name in test_symbols:
            table.lookup(name)
    total_time = time.time() - start_time

    stats = table.get_statistics()

    return {
        "iterations": iterations,
        "scope_depth": scope_depth,
        "symbols_per_scope": symbols_per_scope,
        "total_symbols": len(test_symbols),
        "total_time_s": total_time,
        "avg_time_ms": (total_time * 1000) / (iterations * len(test_symbols)),
        "lookups_per_second": (iterations * len(test_symbols)) / total_time,
        "cache_hit_rate": stats["lookup_stats"]["cache_hit_rate"],
        "global_table_hits": stats["lookup_stats"]["global_table_hits"],
        "scope_chain_lookups": stats["lookup_stats"]["scope_chain_lookups"],
    }
