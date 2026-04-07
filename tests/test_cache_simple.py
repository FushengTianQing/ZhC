#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存基础功能测试 (pytest)

P2 级 — 测试 ASTCacheManager 的核心缓存操作：
1. 缓存创建与配置
2. 类型结果存取 (set_type / get_type / invalidate_type)
3. 符号查找缓存 (set_symbol / get_symbol / invalidate_symbol)
4. CFG 控制流缓存 (set_cfg / get_cfg)
5. 节点级通用缓存 (set_node_result / get_node_result)
6. 函数级通用缓存 (set_function_result / get_function_result)
7. 失效管理 (invalidate_node / invalidate_function / clear_all)
8. 统计信息 (get_stats)
9. LRU 淘汰策略
10. 全局缓存 (get_global_cache / reset_global_cache)

作者：远
日期：2026-04-03 / 2026-04-07 重构为 pytest 格式
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.analyzer.ast_cache import (
    ASTCacheManager,
    CacheType,
    CacheEntry,
    ASTCacheStatistics,
    get_global_cache,
    reset_global_cache,
    cached_result,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def cache():
    """提供已初始化的 ASTCacheManager 实例（每次测试独立）"""
    return ASTCacheManager(max_size_mb=100)


@pytest.fixture
def populated_cache(cache):
    """已预填数据的缓存"""
    cache.set_type(1, {"type": "int", "is_const": False})
    cache.set_type(2, {"type": "str", "is_const": True})
    cache.set_symbol("x", {"kind": "var", "type": "int"})
    cache.set_cfg("main_func", {"entries": [0, 5], "exits": [10]})
    return cache


# ============================================================
# 测试：缓存初始化
# ============================================================

class TestCacheInit:
    """ASTCacheManager 初始化"""

    def test_default_creation(self):
        """默认参数创建应正常工作"""
        c = ASTCacheManager()
        assert c is not None
        assert isinstance(c.stats, ASTCacheStatistics)

    def test_custom_max_size(self):
        """自定义 max_size_mb 生效"""
        c = ASTCacheManager(max_size_mb=50)
        assert c.max_size == 50 * 1024 * 1024

    def test_initial_stats_are_zero(self, cache):
        """初始统计全为零"""
        s = cache.get_stats()
        assert s['total_hits'] == 0
        assert s['total_misses'] == 0
        assert s['total_entries'] == 0


# ============================================================
# 测试：类型结果缓存
# ============================================================

class TestTypeCache:
    """类型推导结果的 set / get / invalidate"""

    def test_set_and_get_type(self, cache):
        """存入和取出类型结果"""
        node_id = 42
        type_info = {"type": "int", "nullable": False}

        cache.set_type(node_id, type_info)
        result = cache.get_type(node_id)

        assert result is not None
        assert result["type"] == "int"
        assert result["nullable"] is False

    def test_get_nonexistent_type_returns_none(self, cache):
        """获取不存在的节点返回 None"""
        assert cache.get_type(99999) is None

    def test_invalidate_type(self, cache):
        """invalidate_type 后再获取返回 None"""
        cache.set_type(1, {"type": "float"})
        assert cache.get_type(1) is not None

        cache.invalidate_type(1)
        assert cache.get_type(1) is None

    def test_invalidate_nonexistent_is_safe(self, cache):
        """对不存在的 key 调用 invalidate 不报错"""
        cache.invalidate_type(99999)  # 不应抛异常


# ============================================================
# 测试：符号查找缓存
# ============================================================

class TestSymbolCache:
    """符号查找结果的缓存"""

    def test_set_and_get_symbol(self, cache):
        """符号的存取"""
        symbol_info = {"name": "count", "kind": "variable", "scope": "local"}

        cache.set_symbol("count", symbol_info)
        result = cache.get_symbol("count")

        assert result is not None
        assert result["name"] == "count"
        assert result["kind"] == "variable"

    def test_get_nonexistent_symbol_returns_none(self, cache):
        assert cache.get_symbol("nonexistent_var") is None

    def test_invalidate_symbol(self, cache):
        cache.set_symbol("temp_var", {})
        assert cache.get_symbol("temp_var") is not None

        cache.invalidate_symbol("temp_var")
        assert cache.get_symbol("temp_var") is None

    def test_overwrite_symbol(self, cache):
        """同名覆盖应使用最新值"""
        cache.set_symbol("v", {"ver": 1})
        cache.set_symbol("v", {"ver": 2})

        assert cache.get_symbol("v")["ver"] == 2


# ============================================================
# 测试：CFG 控制流图缓存
# ============================================================

class TestCFGCache:
    """控制流图的缓存"""

    def test_set_and_get_cfg(self, cache):
        cfg = {"blocks": ["entry", "loop", "exit"], "edges": [(0, 1), (1, 2), (1, 0)]}

        cache.set_cfg("my_func", cfg)
        result = cache.get_cfg("my_func")

        assert result is not None
        assert result["blocks"] == ["entry", "loop", "exit"]

    def test_get_nonexistent_cfg_returns_none(self, cache):
        assert cache.get_cfg("missing_func") is None

    def test_invalidate_cfg(self, cache):
        cache.set_cfg("f", {})
        assert cache.get_cfg("f") is not None

        cache.invalidate_cfg("f")
        assert cache.get_cfg("f") is None


# ============================================================
# 测试：节点级通用缓存
# ============================================================

class TestNodeResultCache:
    """基于 node_id + CacheType 的通用缓存"""

    def test_set_and_get_node_result(self, cache):
        value = {"inferred_type": "bool"}
        cache.set_node_result(node_id=10, cache_type=CacheType.TYPE_INFERENCE, value=value)

        result = cache.get_node_result(10, CacheType.TYPE_INFERENCE)
        assert result is not None
        assert result["inferred_type"] == "bool"

    def test_different_cache_types_are_separate(self, cache):
        """同一节点不同 CacheType 应互不影响"""
        cache.set_node_result(1, CacheType.TYPE_INFERENCE, {"t": "int"})
        cache.set_node_result(1, CacheType.CONTROL_FLOW, {"loops": 2})

        t = cache.get_node_result(1, CacheType.TYPE_INFERENCE)
        cf = cache.get_node_result(1, CacheType.CONTROL_FLOW)

        assert t["t"] == "int"
        assert cf["loops"] == 2

    def test_miss_returns_none(self, cache):
        assert cache.get_node_result(999, CacheType.DATA_FLOW) is None


# ============================================================
# 测试：函数级通用缓存
# ============================================================

class TestFunctionResultCache:
    """基于 func_name + CacheType 的函数缓存"""

    def test_set_and_get_function_result(self, cache):
        info = {"params": 3, "locals": 5}
        cache.set_function_result("analyze", CacheType.DATA_FLOW, info)

        result = cache.get_function_result("analyze", CacheType.DATA_FLOW)
        assert result is not None
        assert result["params"] == 3

    def test_miss_returns_none(self, cache):
        assert cache.get_function_result("missing_fn", CacheType.SYMBOL_LOOKUP) is None


# ============================================================
# 测试：失效管理
# ============================================================

class TestInvalidation:
    """各种失效操作"""

    def test_clear_all_empties_everything(self, populated_cache):
        """clear_all 应清空所有子缓存"""
        populated_cache.clear_all()

        stats = populated_cache.get_stats()
        assert stats['total_entries'] == 0
        assert stats['type_cache_size'] == 0
        assert stats['symbol_cache_size'] == 0
        assert stats['cfg_cache_size'] == 0

        assert populated_cache.get_type(1) is None
        assert populated_cache.get_symbol("x") is None
        assert populated_cache.get_cfg("main_func") is None

    def test_invalidate_node_removes_type_and_node_cache(self, cache):
        """invalidate_node 删除该节点的类型和节点缓存"""
        cache.set_type(99, {"type": "char"})
        cache.set_node_result(99, CacheType.NODE_VISIT, {"visited": True})

        count = cache.invalidate_node(99)
        assert count >= 1  # 至少删除了 type_cache 条目
        assert cache.get_type(99) is None

    def test_invalidate_function_removes_func_and_cfg_cache(self, cache):
        """invalidate_function 删除函数相关缓存"""
        cache.set_function_result("foo", CacheType.CONTROL_FLOW, {})
        cache.set_cfg("foo", {})

        count = cache.invalidate_function("foo")
        assert count >= 1
        assert cache.get_cfg("foo") is None


# ============================================================
# 测试：统计信息
# ============================================================

class TestStatistics:
    """统计信息的准确性"""

    def test_ops_update_hit_miss_counts(self, populated_cache):
        """get 操作更新 hits/misses"""
        populated_cache.get_type(1)   # HIT
        populated_cache.get_type(2)   # HIT
        populated_cache.get_type(99)  # MISS

        s = populated_cache.get_stats()
        assert s['total_hits'] >= 2
        assert s['total_misses'] >= 1

    def test_hit_rate_calculation(self, cache):
        """命中率计算正确（hit_rate 是 property）"""
        cache.stats.total_hits = 8
        cache.stats.total_misses = 2
        rate = cache.stats.hit_rate  # property，不是方法调用
        assert abs(rate - 0.8) < 0.001

    def test_zero_rate_when_no_lookups(self, cache):
        """无查询时命中率为 0"""
        assert cache.stats.hit_rate == 0.0

    def test_get_stats_contains_all_keys(self, populated_cache):
        """返回的统计字典包含预期字段"""
        s = populated_cache.get_stats()
        expected_keys = {
            'total_hits', 'total_misses', 'hit_rate', 'total_entries',
            'node_cache_size', 'func_cache_size',
            'type_cache_size', 'symbol_cache_size', 'cfg_cache_size',
        }
        assert expected_keys.issubset(s.keys())

    def test_print_stats_runs_without_error(self, cache):
        """print_stats 不抛异常（仅验证可调用）"""
        cache.print_stats()  # 不应抛出


# ============================================================
# 测试：全局缓存实例
# ============================================================

class TestGlobalCache:
    """get_global_cache / reset_global_cache"""

    def setup_method(self):
        """每个测试前重置全局缓存"""
        reset_global_cache()

    def teardown_method(self):
        """清理"""
        reset_global_cache()

    def test_get_global_returns_instance(self):
        """应返回 ASTCacheManager 实例"""
        c = get_global_cache()
        assert isinstance(c, ASTCacheManager)

    def test_get_global_same_instance(self):
        """多次调用返回同一单例"""
        a = get_global_cache()
        b = get_global_cache()
        assert a is b

    def test_reset_creates_new_instance(self):
        """reset 后获取的是新实例"""
        old = get_global_cache()
        old.set_type(1, {"marker": True})

        reset_global_cache()
        new = get_global_cache()

        assert old is not new
        assert new.get_type(1) is None


# ============================================================
# 测试：装饰器 cached_result
# ============================================================

class TestCachedDecorator:
    """@cached_result 装饰器的基本行为"""

    def test_decorator_caches_result(self):
        """装饰后的函数第二次调用应返回缓存值"""
        call_count = [0]

        # 使用全局缓存
        reset_global_cache()

        @cached_result(CacheType.TYPE_INFERENCE)
        def mock_infer(node_id):
            call_count[0] += 1
            return f"type_for_{node_id}"

        r1 = mock_infer(42)
        r2 = mock_infer(42)

        assert r1 == "type_for_42"
        assert r2 == "type_for_42"
        assert call_count[0] == 1, "装饰器应避免重复计算"

        reset_global_cache()


# ============================================================
# 测试：CacheEntry 数据类
# ============================================================

class TestCacheEntry:
    """CacheEntry 数据类的行为"""

    def test_touch_increments_hit_count(self):
        entry = CacheEntry(
            key="test_key", value={"data": 1},
            cache_type=CacheType.TYPE_INFERENCE,
            timestamp=1000.0,
        )
        assert entry.hit_count == 0
        entry.touch()
        assert entry.hit_count == 1
        entry.touch()
        entry.touch()
        assert entry.hit_count == 3

    def test_fields_preserved(self):
        entry = CacheEntry(
            key="k", value=42, cache_type=CacheType.DATA_FLOW,
            timestamp=123.456, hit_count=5, node_id=77,
            dependencies={"dep_a", "dep_b"},
        )
        assert entry.node_id == 77
        assert len(entry.dependencies) == 2
