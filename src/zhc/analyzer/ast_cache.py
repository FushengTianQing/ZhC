#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST缓存管理器 - AST Cache Manager

功能：
1. AST节点缓存（避免重复遍历）
2. 类型推导结果缓存
3. 分析结果缓存（CFG、数据流等）
4. 缓存失效管理
5. 性能统计

作者：远
日期：2026-04-03
"""

from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import weakref


class CacheType(Enum):
    """缓存类型"""

    TYPE_INFERENCE = "type_inference"  # 类型推导结果
    CONTROL_FLOW = "control_flow"  # 控制流图
    DATA_FLOW = "data_flow"  # 数据流分析
    SYMBOL_LOOKUP = "symbol_lookup"  # 符号查找
    CONSTANT_PROP = "constant_propagation"  # 常量传播
    NODE_VISIT = "node_visit"  # 节点访问结果


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    cache_type: CacheType
    timestamp: float
    hit_count: int = 0
    node_id: Optional[int] = None  # AST节点ID
    dependencies: Set[str] = field(default_factory=set)

    def touch(self):
        """标记访问"""
        self.hit_count += 1


@dataclass
class ASTCacheStatistics:
    """缓存统计"""

    total_hits: int = 0
    total_misses: int = 0
    total_entries: int = 0
    total_memory_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0

    def reset(self):
        """重置统计"""
        self.total_hits = 0
        self.total_misses = 0
        self.total_entries = 0
        self.total_memory_bytes = 0


class ASTCacheManager:
    """AST缓存管理器

    提供多级缓存机制：
    1. 节点级缓存 - 针对单个AST节点的结果
    2. 函数级缓存 - 针对整个函数的分析结果
    3. 模块级缓存 - 针对整个模块的分析结果
    """

    def __init__(self, max_size_mb: int = 100):
        """
        初始化缓存管理器

        Args:
            max_size_mb: 最大缓存大小（MB）
        """
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节

        # 多级缓存
        self._node_cache: Dict[str, CacheEntry] = {}  # 节点级缓存
        self._func_cache: Dict[str, CacheEntry] = {}  # 函数级缓存
        self._module_cache: Dict[str, CacheEntry] = {}  # 模块级缓存

        # 类型推导缓存（专门优化）
        self._type_cache: Dict[int, Any] = {}  # node_id -> TypeInfo

        # 符号查找缓存
        self._symbol_cache: Dict[str, Any] = {}  # symbol_name -> Symbol

        # CFG缓存
        self._cfg_cache: Dict[str, Any] = {}  # func_name -> ControlFlowGraph

        # 弱引用映射（用于跟踪AST节点）
        self._node_refs: Dict[int, weakref.ref] = {}

        # 统计信息
        self.stats = ASTCacheStatistics()

        # 缓存版本（用于失效检测）
        self._version = 0
        self._module_versions: Dict[str, int] = {}

    # ==================== 核心缓存接口 ====================

    def get_node_result(self, node_id: int, cache_type: CacheType) -> Optional[Any]:
        """
        获取节点缓存结果

        Args:
            node_id: AST节点ID
            cache_type: 缓存类型

        Returns:
            缓存结果，未命中返回None
        """
        key = self._make_node_key(node_id, cache_type)

        if key in self._node_cache:
            entry = self._node_cache[key]
            entry.touch()
            self.stats.total_hits += 1
            return entry.value

        self.stats.total_misses += 1
        return None

    def set_node_result(
        self,
        node_id: int,
        cache_type: CacheType,
        value: Any,
        dependencies: Optional[Set[str]] = None,
    ) -> None:
        """
        设置节点缓存结果

        Args:
            node_id: AST节点ID
            cache_type: 缓存类型
            value: 缓存值
            dependencies: 依赖项（用于失效管理）
        """
        key = self._make_node_key(node_id, cache_type)

        # 检查是否需要驱逐
        self._evict_if_needed()

        entry = CacheEntry(
            key=key,
            value=value,
            cache_type=cache_type,
            timestamp=datetime.now().timestamp(),
            node_id=node_id,
            dependencies=dependencies or set(),
        )

        self._node_cache[key] = entry
        self.stats.total_entries += 1

    # ==================== 类型推导缓存 ====================

    def get_type(self, node_id: int) -> Optional[Any]:
        """
        获取类型推导结果

        Args:
            node_id: AST节点ID

        Returns:
            类型信息，未命中返回None
        """
        if node_id in self._type_cache:
            self.stats.total_hits += 1
            return self._type_cache[node_id]

        self.stats.total_misses += 1
        return None

    def set_type(self, node_id: int, type_info: Any) -> None:
        """
        设置类型推导结果

        Args:
            node_id: AST节点ID
            type_info: 类型信息
        """
        self._type_cache[node_id] = type_info
        self.stats.total_entries += 1

    def invalidate_type(self, node_id: int) -> None:
        """使类型缓存失效"""
        if node_id in self._type_cache:
            del self._type_cache[node_id]

    # ==================== 符号查找缓存 ====================

    def get_symbol(self, symbol_name: str) -> Optional[Any]:
        """
        获取符号缓存

        Args:
            symbol_name: 符号名

        Returns:
            符号信息，未命中返回None
        """
        if symbol_name in self._symbol_cache:
            self.stats.total_hits += 1
            return self._symbol_cache[symbol_name]

        self.stats.total_misses += 1
        return None

    def set_symbol(self, symbol_name: str, symbol_info: Any) -> None:
        """
        设置符号缓存

        Args:
            symbol_name: 符号名
            symbol_info: 符号信息
        """
        self._symbol_cache[symbol_name] = symbol_info
        self.stats.total_entries += 1

    def invalidate_symbol(self, symbol_name: str) -> None:
        """使符号缓存失效"""
        if symbol_name in self._symbol_cache:
            del self._symbol_cache[symbol_name]

    # ==================== CFG缓存 ====================

    def get_cfg(self, func_name: str) -> Optional[Any]:
        """
        获取控制流图缓存

        Args:
            func_name: 函数名

        Returns:
            控制流图，未命中返回None
        """
        if func_name in self._cfg_cache:
            self.stats.total_hits += 1
            return self._cfg_cache[func_name]

        self.stats.total_misses += 1
        return None

    def set_cfg(self, func_name: str, cfg: Any) -> None:
        """
        设置控制流图缓存

        Args:
            func_name: 函数名
            cfg: 控制流图
        """
        self._cfg_cache[func_name] = cfg
        self.stats.total_entries += 1

    def invalidate_cfg(self, func_name: str) -> None:
        """使CFG缓存失效"""
        if func_name in self._cfg_cache:
            del self._cfg_cache[func_name]

    # ==================== 函数级缓存 ====================

    def get_function_result(
        self, func_name: str, cache_type: CacheType
    ) -> Optional[Any]:
        """
        获取函数级缓存结果

        Args:
            func_name: 函数名
            cache_type: 缓存类型

        Returns:
            缓存结果，未命中返回None
        """
        key = self._make_func_key(func_name, cache_type)

        if key in self._func_cache:
            entry = self._func_cache[key]
            entry.touch()
            self.stats.total_hits += 1
            return entry.value

        self.stats.total_misses += 1
        return None

    def set_function_result(
        self,
        func_name: str,
        cache_type: CacheType,
        value: Any,
        dependencies: Optional[Set[str]] = None,
    ) -> None:
        """
        设置函数级缓存结果

        Args:
            func_name: 函数名
            cache_type: 缓存类型
            value: 缓存值
            dependencies: 依赖项
        """
        key = self._make_func_key(func_name, cache_type)

        self._evict_if_needed()

        entry = CacheEntry(
            key=key,
            value=value,
            cache_type=cache_type,
            timestamp=datetime.now().timestamp(),
            dependencies=dependencies or set(),
        )

        self._func_cache[key] = entry
        self.stats.total_entries += 1

    # ==================== 失效管理 ====================

    def invalidate_node(self, node_id: int) -> int:
        """
        使节点相关的所有缓存失效

        Args:
            node_id: AST节点ID

        Returns:
            失效的缓存条目数
        """
        invalidated = 0

        # 失效节点级缓存
        keys_to_remove = [
            key for key, entry in self._node_cache.items() if entry.node_id == node_id
        ]

        for key in keys_to_remove:
            del self._node_cache[key]
            invalidated += 1

        # 失效类型缓存
        if node_id in self._type_cache:
            del self._type_cache[node_id]
            invalidated += 1

        return invalidated

    def invalidate_function(self, func_name: str) -> int:
        """
        使函数相关的所有缓存失效

        Args:
            func_name: 函数名

        Returns:
            失效的缓存条目数
        """
        invalidated = 0

        # 失效函数级缓存
        keys_to_remove = [key for key in self._func_cache if func_name in key]

        for key in keys_to_remove:
            del self._func_cache[key]
            invalidated += 1

        # 失效CFG缓存
        if func_name in self._cfg_cache:
            del self._cfg_cache[func_name]
            invalidated += 1

        return invalidated

    def invalidate_module(self, module_name: str) -> int:
        """
        使模块相关的所有缓存失效

        Args:
            module_name: 模块名

        Returns:
            失效的缓存条目数
        """
        invalidated = 0

        # 失效模块级缓存
        keys_to_remove = [key for key in self._module_cache if module_name in key]

        for key in keys_to_remove:
            del self._module_cache[key]
            invalidated += 1

        # 更新版本号
        self._version += 1
        self._module_versions[module_name] = self._version

        return invalidated

    def clear_all(self) -> None:
        """清空所有缓存"""
        self._node_cache.clear()
        self._func_cache.clear()
        self._module_cache.clear()
        self._type_cache.clear()
        self._symbol_cache.clear()
        self._cfg_cache.clear()
        self._node_refs.clear()

        self.stats.reset()
        self._version += 1

    # ==================== 统计信息 ====================

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "total_hits": self.stats.total_hits,
            "total_misses": self.stats.total_misses,
            "hit_rate": f"{self.stats.hit_rate:.2%}",
            "total_entries": self.stats.total_entries,
            "node_cache_size": len(self._node_cache),
            "func_cache_size": len(self._func_cache),
            "type_cache_size": len(self._type_cache),
            "symbol_cache_size": len(self._symbol_cache),
            "cfg_cache_size": len(self._cfg_cache),
            "current_version": self._version,
        }

    def print_stats(self) -> None:
        """打印缓存统计信息"""
        stats = self.get_stats()

        print("\n" + "=" * 70)
        print("AST缓存管理器统计")
        print("=" * 70)

        print("\n📊 缓存性能:")
        print(f"  总命中: {stats['total_hits']}")
        print(f"  总未中: {stats['total_misses']}")
        print(f"  命中率: {stats['hit_rate']}")
        print(f"  总条目: {stats['total_entries']}")

        print("\n📦 各级缓存大小:")
        print(f"  节点缓存: {stats['node_cache_size']}")
        print(f"  函数缓存: {stats['func_cache_size']}")
        print(f"  类型缓存: {stats['type_cache_size']}")
        print(f"  符号缓存: {stats['symbol_cache_size']}")
        print(f"  CFG缓存: {stats['cfg_cache_size']}")

        print("\n🔄 版本信息:")
        print(f"  当前版本: {stats['current_version']}")

        print("=" * 70)

    # ==================== 内部方法 ====================

    def _make_node_key(self, node_id: int, cache_type: CacheType) -> str:
        """生成节点缓存键"""
        return f"node:{node_id}:{cache_type.value}"

    def _make_func_key(self, func_name: str, cache_type: CacheType) -> str:
        """生成函数缓存键"""
        return f"func:{func_name}:{cache_type.value}"

    def _make_module_key(self, module_name: str, cache_type: CacheType) -> str:
        """生成模块缓存键"""
        return f"module:{module_name}:{cache_type.value}"

    def _evict_if_needed(self) -> None:
        """如果需要，驱逐缓存条目（LRU策略）"""
        # 简化版本：只检查条目数量
        max_entries = 10000

        total_entries = (
            len(self._node_cache)
            + len(self._func_cache)
            + len(self._module_cache)
            + len(self._type_cache)
            + len(self._symbol_cache)
            + len(self._cfg_cache)
        )

        if total_entries > max_entries:
            # 按命中次数排序，删除最少使用的条目
            all_entries = list(self._node_cache.items())
            all_entries.sort(key=lambda x: x[1].hit_count)

            # 删除10%的条目
            to_remove = max_entries // 10
            for key, _ in all_entries[:to_remove]:
                del self._node_cache[key]

            self.stats.total_entries -= to_remove


# 全局缓存管理器实例
_global_cache_manager: Optional[ASTCacheManager] = None


def get_global_cache() -> ASTCacheManager:
    """获取全局缓存管理器"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = ASTCacheManager()
    return _global_cache_manager


def reset_global_cache() -> None:
    """重置全局缓存管理器"""
    global _global_cache_manager
    if _global_cache_manager:
        _global_cache_manager.clear_all()
    _global_cache_manager = None


# 装饰器：自动缓存函数结果
def cached_result(cache_type: CacheType, key_func=None):
    """
    缓存装饰器

    Args:
        cache_type: 缓存类型
        key_func: 生成缓存键的函数

    Example:
        @cached_result(CacheType.TYPE_INFERENCE)
        def infer_type(node):
            # ... 推导类型
            return type_info
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取缓存管理器
            cache = get_global_cache()

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用第一个参数（通常是节点）
                node_id = id(args[0]) if args else 0
                cache_key = (node_id, cache_type)

            # 检查缓存
            if isinstance(cache_key, tuple):
                cached = cache.get_node_result(cache_key[0], cache_key[1])
            else:
                cached = cache.get_node_result(cache_key, cache_type)

            if cached is not None:
                return cached

            # 未命中，执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            if isinstance(cache_key, tuple):
                cache.set_node_result(cache_key[0], cache_key[1], result)
            else:
                cache.set_node_result(cache_key, cache_type, result)

            return result

        return wrapper

    return decorator
