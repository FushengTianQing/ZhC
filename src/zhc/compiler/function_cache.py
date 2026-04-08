#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
函数级编译缓存 - Function Level Compilation Cache

功能：
1. 函数级编译缓存，避免完整重编译
2. 函数内容哈希计算
3. 增量编译支持

性能优化：
- 小修改只触发单个函数重编译
- 缓存复用减少编译时间
- 依赖追踪精准化

作者：远
日期：2026-04-03
"""

import hashlib
import pickle
import time
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class CacheStatus(Enum):
    """缓存状态"""

    HIT = "hit"  # 缓存命中
    MISS = "miss"  # 缓存未命中
    STALE = "stale"  # 缓存过期
    INVALID = "invalid"  # 缓存无效


@dataclass
class FunctionHash:
    """函数哈希信息"""

    content_hash: str  # 函数体内容哈希
    dependency_hash: str  # 依赖符号哈希
    full_hash: str  # 完整哈希 (content + dependency)
    timestamp: float  # 计算时间戳

    def is_valid(self, other: "FunctionHash") -> bool:
        """检查哈希是否仍然有效"""
        return self.full_hash == other.full_hash


@dataclass
class CachedFunction:
    """缓存的函数编译结果"""

    func_name: str
    func_hash: str
    compiled_code: str
    ast_json: str  # 序列化的AST
    dependencies: Set[str]  # 依赖的函数
    symbols_used: Set[str]  # 使用的符号
    compile_time: float  # 编译耗时
    cache_time: float  # 缓存时间
    hit_count: int = 0  # 命中次数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "func_name": self.func_name,
            "func_hash": self.func_hash,
            "compiled_code": self.compiled_code,
            "ast_json": self.ast_json,
            "dependencies": list(self.dependencies),
            "symbols_used": list(self.symbols_used),
            "compile_time": self.compile_time,
            "cache_time": self.cache_time,
            "hit_count": self.hit_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedFunction":
        """从字典创建"""
        return cls(
            func_name=data["func_name"],
            func_hash=data["func_hash"],
            compiled_code=data["compiled_code"],
            ast_json=data["ast_json"],
            dependencies=set(data["dependencies"]),
            symbols_used=set(data["symbols_used"]),
            compile_time=data["compile_time"],
            cache_time=data["cache_time"],
            hit_count=data.get("hit_count", 0),
        )


@dataclass
class FunctionCacheStatistics:
    """缓存统计"""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_stales: int = 0
    total_saved_time: float = 0.0  # 节省的时间

    @property
    def hit_rate(self) -> float:
        """命中率"""
        return self.cache_hits / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def time_saved_ms(self) -> float:
        """节省的时间（毫秒）"""
        return self.total_saved_time * 1000


class FunctionLevelCache:
    """
    函数级编译缓存

    核心功能：
    1. 函数内容哈希计算
    2. 缓存查找和存储
    3. 增量编译支持
    4. 依赖追踪
    """

    def __init__(self, cache_dir: str = ".zhc_function_cache", max_entries: int = 1000):
        """
        初始化函数级缓存

        Args:
            cache_dir: 缓存目录
            max_entries: 最大缓存条目数
        """
        self.cache_dir = Path(cache_dir)
        self.max_entries = max_entries

        # 内存缓存
        self._memory_cache: Dict[str, CachedFunction] = {}

        # 缓存索引 (func_name -> cache_key)
        self._cache_index: Dict[str, str] = {}

        # 统计
        self.stats = FunctionCacheStatistics()

        # 依赖追踪
        self._dependency_graph: Dict[str, Set[str]] = {}  # func -> dependencies

        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 加载已有缓存
        self._load_index()

    def _load_index(self):
        """加载缓存索引"""
        index_file = self.cache_dir / "index.pkl"
        if index_file.exists():
            try:
                with open(index_file, "rb") as f:
                    data = pickle.load(f)
                    self._cache_index = data.get("index", {})
                    self._dependency_graph = data.get("deps", {})
            except Exception:
                pass

    def _save_index(self):
        """保存缓存索引"""
        index_file = self.cache_dir / "index.pkl"
        try:
            with open(index_file, "wb") as f:
                pickle.dump(
                    {
                        "index": self._cache_index,
                        "deps": self._dependency_graph,
                    },
                    f,
                )
        except Exception:
            pass

    def compute_function_hash(
        self,
        func_name: str,
        func_body: str,
        params: str = "",
        return_type: str = "",
        symbols_used: Set[str] = None,
    ) -> FunctionHash:
        """
        计算函数的完整哈希

        Args:
            func_name: 函数名
            func_body: 函数体内容
            params: 参数签名
            return_type: 返回类型
            symbols_used: 使用的符号集合

        Returns:
            函数哈希信息
        """
        time.time()

        # 内容哈希
        content_str = f"{func_name}|{params}|{return_type}|{func_body}"
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # 依赖哈希
        symbols_used = symbols_used or set()
        dep_str = "|".join(sorted(symbols_used))
        dependency_hash = hashlib.sha256(dep_str.encode()).hexdigest()

        # 完整哈希
        full_str = f"{content_hash}|{dependency_hash}"
        full_hash = hashlib.sha256(full_str.encode()).hexdigest()

        return FunctionHash(
            content_hash=content_hash,
            dependency_hash=dependency_hash,
            full_hash=full_hash,
            timestamp=time.time(),
        )

    def get_cache_key(self, func_name: str) -> str:
        """获取缓存键"""
        # 使用缓存索引
        if func_name in self._cache_index:
            return self._cache_index[func_name]

        # 生成新的缓存键
        return hashlib.md5(func_name.encode()).hexdigest()[:16]

    def get(
        self,
        func_name: str,
        func_body: str,
        params: str = "",
        return_type: str = "",
        symbols_used: Set[str] = None,
    ) -> Tuple[Optional[CachedFunction], CacheStatus]:
        """
        获取缓存的函数

        Args:
            func_name: 函数名
            func_body: 函数体内容
            params: 参数签名
            return_type: 返回类型
            symbols_used: 使用的符号集合

        Returns:
            (缓存的函数, 缓存状态)
        """
        self.stats.total_requests += 1

        cache_key = self.get_cache_key(func_name)

        # 检查内存缓存
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]

            # 验证哈希
            func_hash = self.compute_function_hash(
                func_name, func_body, params, return_type, symbols_used
            )

            if cached.func_hash == func_hash.full_hash:
                # 缓存命中
                cached.hit_count += 1
                self.stats.cache_hits += 1
                return cached, CacheStatus.HIT
            else:
                # 缓存过期
                self.stats.cache_stales += 1
                return cached, CacheStatus.STALE

        # 检查磁盘缓存
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    cached = pickle.load(f)

                # 验证哈希
                func_hash = self.compute_function_hash(
                    func_name, func_body, params, return_type, symbols_used
                )

                if cached.func_hash == func_hash.full_hash:
                    # 加载到内存
                    self._memory_cache[cache_key] = cached
                    cached.hit_count += 1
                    self.stats.cache_hits += 1
                    return cached, CacheStatus.HIT
                else:
                    self.stats.cache_stales += 1
                    return cached, CacheStatus.STALE

            except Exception:
                pass

        # 缓存未命中
        self.stats.cache_misses += 1
        return None, CacheStatus.MISS

    def put(
        self,
        func_name: str,
        compiled_code: str,
        func_body: str,
        params: str = "",
        return_type: str = "",
        dependencies: Set[str] = None,
        symbols_used: Set[str] = None,
        ast_json: str = "",
    ) -> CachedFunction:
        """
        存入缓存

        Args:
            func_name: 函数名
            compiled_code: 编译后的代码
            func_body: 函数体内容
            params: 参数签名
            return_type: 返回类型
            dependencies: 依赖的函数
            symbols_used: 使用的符号
            ast_json: AST序列化

        Returns:
            缓存的函数对象
        """
        # 计算哈希
        func_hash = self.compute_function_hash(
            func_name, func_body, params, return_type, symbols_used
        )

        cache_key = self.get_cache_key(func_name)

        # 创建缓存对象
        cached = CachedFunction(
            func_name=func_name,
            func_hash=func_hash.full_hash,
            compiled_code=compiled_code,
            ast_json=ast_json,
            dependencies=dependencies or set(),
            symbols_used=symbols_used or set(),
            compile_time=0.0,  # 编译时间由调用者提供
            cache_time=time.time(),
        )

        # 存入内存缓存
        self._memory_cache[cache_key] = cached

        # 更新索引
        self._cache_index[func_name] = cache_key

        # 更新依赖图
        if dependencies:
            self._dependency_graph[func_name] = dependencies

        # LRU淘汰
        if len(self._memory_cache) > self.max_entries:
            self._evict_lru()

        # 存入磁盘
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, "wb") as f:
                pickle.dump(cached, f)
        except Exception:
            pass

        # 保存索引
        self._save_index()

        return cached

    def _evict_lru(self):
        """LRU淘汰策略"""
        if not self._memory_cache:
            return

        # 找到最少使用的条目
        lru_key = min(
            self._memory_cache.keys(), key=lambda k: self._memory_cache[k].hit_count
        )

        del self._memory_cache[lru_key]

    def invalidate(self, func_name: str):
        """
        使函数缓存失效

        Args:
            func_name: 函数名
        """
        cache_key = self.get_cache_key(func_name)

        # 从内存缓存删除
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        # 从索引删除
        if func_name in self._cache_index:
            del self._cache_index[func_name]

        # 从磁盘删除
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            cache_file.unlink()

        # 使依赖此函数的函数也失效
        self._invalidate_dependents(func_name)

        # 保存索引
        self._save_index()

    def _invalidate_dependents(self, func_name: str):
        """使依赖指定函数的函数失效"""
        dependents = [
            name for name, deps in self._dependency_graph.items() if func_name in deps
        ]

        for dependent in dependents:
            self.invalidate(dependent)

    def get_or_compile(
        self,
        func_name: str,
        func_body: str,
        params: str,
        return_type: str,
        symbols_used: Set[str],
        compiler_func,  # 编译函数
        dependencies: Set[str] = None,
    ) -> Tuple[str, bool, float]:
        """
        获取缓存或重新编译

        Args:
            func_name: 函数名
            func_body: 函数体
            params: 参数签名
            return_type: 返回类型
            symbols_used: 使用的符号
            compiler_func: 编译函数 (func_body) -> compiled_code
            dependencies: 依赖的函数

        Returns:
            (编译后的代码, 是否使用缓存, 编译时间)
        """
        start_time = time.time()

        # 尝试获取缓存
        cached, status = self.get(
            func_name, func_body, params, return_type, symbols_used
        )

        if status == CacheStatus.HIT:
            # 缓存命中
            compile_time = time.time() - start_time
            self.stats.total_saved_time += cached.compile_time
            return cached.compiled_code, True, compile_time

        if status == CacheStatus.STALE:
            # 缓存过期，使失效
            self.invalidate(func_name)

        # 重新编译
        compile_start = time.time()
        compiled_code = compiler_func(func_body)
        compile_time = time.time() - compile_start

        # 存入缓存
        self.put(
            func_name=func_name,
            compiled_code=compiled_code,
            func_body=func_body,
            params=params,
            return_type=return_type,
            dependencies=dependencies,
            symbols_used=symbols_used,
        )

        total_time = time.time() - start_time

        # 更新缓存的编译时间
        cache_key = self.get_cache_key(func_name)
        if cache_key in self._memory_cache:
            self._memory_cache[cache_key].compile_time = compile_time

        return compiled_code, False, total_time

    def clear(self):
        """清空所有缓存"""
        self._memory_cache.clear()
        self._cache_index.clear()
        self._dependency_graph.clear()

        # 删除磁盘缓存
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

        # 重置统计
        self.stats = FunctionCacheStatistics()

    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "total_requests": self.stats.total_requests,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            "cache_stales": self.stats.cache_stales,
            "hit_rate": f"{self.stats.hit_rate:.2%}",
            "time_saved_ms": f"{self.stats.time_saved_ms:.2f}",
            "cached_functions": len(self._memory_cache),
            "dependency_count": len(self._dependency_graph),
        }

    def get_report(self) -> str:
        """生成缓存报告"""
        stats = self.get_statistics()

        lines = [
            "=" * 60,
            "函数级编译缓存报告",
            "=" * 60,
            "",
            f"总请求数: {stats['total_requests']}",
            f"缓存命中: {stats['cache_hits']}",
            f"缓存未命中: {stats['cache_misses']}",
            f"缓存过期: {stats['cache_stales']}",
            f"命中率: {stats['hit_rate']}",
            f"节省时间: {stats['time_saved_ms']}ms",
            "",
            f"缓存函数数: {stats['cached_functions']}",
            f"依赖关系数: {stats['dependency_count']}",
            "",
            "=" * 60,
        ]

        return "\n".join(lines)


# 兼容性简化
FunctionCache = FunctionLevelCache
