"""
ZHC编译器 - 类型检查器(带缓存)

功能：
- 类型推导（带缓存）
- 类型兼容性检查
- 类型转换检查
- 类型错误报告

性能优化：
- 类型推导结果缓存
- 表达式类型缓存
- 函数签名缓存

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib

# 导入基础类型检查器
from .type_checker import TypeChecker, TypeInfo


@dataclass
class TypeCacheEntry:
    """类型缓存条目"""

    type_info: TypeInfo
    source_hash: str  # 源码哈希
    access_count: int = 0
    last_access: float = 0.0


class TypeCheckerCached(TypeChecker):
    """带缓存的类型检查器"""

    def __init__(self, cache_size: int = 1000):
        """
        初始化带缓存的类型检查器

        Args:
            cache_size: 缓存大小限制
        """
        super().__init__()

        # 缓存配置
        self.cache_size = cache_size

        # 类型推导缓存
        self._type_inference_cache: Dict[str, TypeCacheEntry] = {}

        # 表达式类型缓存
        self._expr_type_cache: Dict[str, TypeCacheEntry] = {}

        # 函数签名缓存
        self._func_sig_cache: Dict[str, TypeCacheEntry] = {}

        # 缓存命中率统计
        self._cache_hits = 0
        self._cache_misses = 0

        # 哈希缓存（避免重复计算）
        self._hash_cache: Dict[int, str] = {}

    def _compute_hash(self, source: str) -> str:
        """计算源码哈希"""
        source_id = id(source)

        if source_id in self._hash_cache:
            return self._hash_cache[source_id]

        hash_val = hashlib.md5(source.encode()).hexdigest()
        self._hash_cache[source_id] = hash_val
        return hash_val

    def _get_from_cache(
        self, cache: Dict[str, TypeCacheEntry], key: str, source: str
    ) -> Optional[TypeInfo]:
        """从缓存获取类型"""
        source_hash = self._compute_hash(source)

        if key in cache:
            entry = cache[key]
            if entry.source_hash == source_hash:
                # 缓存命中
                self._cache_hits += 1
                entry.access_count += 1
                entry.last_access = 0.0  # 简化：使用时间戳
                return entry.type_info

        # 缓存未命中
        self._cache_misses += 1
        return None

    def _put_to_cache(
        self,
        cache: Dict[str, TypeCacheEntry],
        key: str,
        type_info: TypeInfo,
        source: str,
    ):
        """将类型存入缓存"""
        # LRU淘汰
        if len(cache) >= self.cache_size:
            self._evict_lru(cache)

        source_hash = self._compute_hash(source)
        cache[key] = TypeCacheEntry(
            type_info=type_info,
            source_hash=source_hash,
            access_count=1,
            last_access=0.0,
        )

    def _evict_lru(self, cache: Dict[str, TypeCacheEntry]):
        """LRU淘汰策略"""
        if not cache:
            return

        # 找到访问次数最少的条目
        lru_key = min(cache.keys(), key=lambda k: cache[k].access_count)
        del cache[lru_key]

    # ==================== 带缓存的类型推导 ====================

    def infer_type_cached(self, expr_source: str, expr_id: str) -> Optional[TypeInfo]:
        """
        带缓存的类型推导

        Args:
            expr_source: 表达式源码
            expr_id: 表达式唯一标识

        Returns:
            推导的类型信息
        """
        # 尝试从缓存获取
        cached_type = self._get_from_cache(self._expr_type_cache, expr_id, expr_source)

        if cached_type:
            return cached_type

        # 执行类型推导（这里需要实际的推导逻辑）
        # 简化：返回None，实际实现需要调用语义分析器
        return None

    def check_binary_op_cached(
        self,
        line: int,
        op: str,
        left_type: TypeInfo,
        right_type: TypeInfo,
        expr_source: str = "",
    ) -> Optional[TypeInfo]:
        """
        带缓存的二元运算类型检查

        Args:
            line: 行号
            op: 运算符
            left_type: 左操作数类型
            right_type: 右操作数类型
            expr_source: 表达式源码

        Returns:
            结果类型
        """
        # 构建缓存键
        cache_key = f"binop:{op}:{left_type.name}:{right_type.name}"

        # 尝试从缓存获取
        if expr_source:
            cached_type = self._get_from_cache(
                self._type_inference_cache, cache_key, expr_source
            )

            if cached_type:
                return cached_type

        # 执行实际检查
        result_type = super().check_binary_op(line, op, left_type, right_type)

        # 存入缓存
        if result_type and expr_source:
            self._put_to_cache(
                self._type_inference_cache, cache_key, result_type, expr_source
            )

        return result_type

    def check_unary_op_cached(
        self, line: int, op: str, operand_type: TypeInfo, expr_source: str = ""
    ) -> Optional[TypeInfo]:
        """
        带缓存的一元运算类型检查

        Args:
            line: 行号
            op: 运算符
            operand_type: 操作数类型
            expr_source: 表达式源码

        Returns:
            结果类型
        """
        # 构建缓存键
        cache_key = f"unaryop:{op}:{operand_type.name}"

        # 尝试从缓存获取
        if expr_source:
            cached_type = self._get_from_cache(
                self._type_inference_cache, cache_key, expr_source
            )

            if cached_type:
                return cached_type

        # 执行实际检查
        result_type = super().check_unary_op(line, op, operand_type)

        # 存入缓存
        if result_type and expr_source:
            self._put_to_cache(
                self._type_inference_cache, cache_key, result_type, expr_source
            )

        return result_type

    # ==================== 函数签名缓存 ====================

    def cache_function_signature(
        self, func_name: str, return_type: TypeInfo, param_types: List[TypeInfo]
    ):
        """
        缓存函数签名

        Args:
            func_name: 函数名
            return_type: 返回类型
            param_types: 参数类型列表
        """
        # 创建函数类型
        func_type = self.create_function_type(return_type, param_types)

        # 构建缓存键
        param_str = ", ".join(t.name for t in param_types)
        cache_key = f"func:{func_name}({param_str})"

        # 存入缓存
        self._func_sig_cache[cache_key] = TypeCacheEntry(
            type_info=func_type,
            source_hash="",  # 函数签名不需要源码哈希
            access_count=1,
        )

    def get_function_signature(
        self, func_name: str, param_types: List[TypeInfo]
    ) -> Optional[TypeInfo]:
        """
        获取缓存的函数签名

        Args:
            func_name: 函数名
            param_types: 参数类型列表

        Returns:
            函数类型信息
        """
        param_str = ", ".join(t.name for t in param_types)
        cache_key = f"func:{func_name}({param_str})"

        if cache_key in self._func_sig_cache:
            entry = self._func_sig_cache[cache_key]
            entry.access_count += 1
            return entry.type_info

        return None

    # ==================== 缓存管理 ====================

    def clear_cache(self):
        """清空所有缓存"""
        self._type_inference_cache.clear()
        self._expr_type_cache.clear()
        self._func_sig_cache.clear()
        self._hash_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def invalidate_cache(self, source: str):
        """
        使指定源码相关的缓存失效

        Args:
            source: 源码内容
        """
        source_hash = self._compute_hash(source)

        # 删除所有哈希匹配的缓存条目
        keys_to_remove = []
        for key, entry in self._type_inference_cache.items():
            if entry.source_hash == source_hash:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._type_inference_cache[key]

    def get_cache_stats(self) -> Dict[str, float]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0

        return {
            "total_requests": total_requests,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "type_inference_cache_size": len(self._type_inference_cache),
            "expr_type_cache_size": len(self._expr_type_cache),
            "func_sig_cache_size": len(self._func_sig_cache),
        }

    def get_cache_report(self) -> str:
        """生成缓存报告"""
        stats = self.get_cache_stats()

        lines = [
            "=" * 60,
            "类型检查器缓存报告",
            "=" * 60,
            "",
            f"总请求数: {stats['total_requests']}",
            f"缓存命中: {stats['cache_hits']}",
            f"缓存未命中: {stats['cache_misses']}",
            f"命中率: {stats['hit_rate']:.2%}",
            "",
            f"类型推导缓存: {stats['type_inference_cache_size']} 条",
            f"表达式类型缓存: {stats['expr_type_cache_size']} 条",
            f"函数签名缓存: {stats['func_sig_cache_size']} 条",
            "",
            "=" * 60,
        ]

        return "\n".join(lines)


# 兼容性别名
TypeCheckerOptimized = TypeCheckerCached
