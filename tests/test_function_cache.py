#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
函数级缓存测试 (pytest)

P2 级 — 测试 function_cache 模块的完整功能：
1. 函数哈希计算
2. 缓存存取与命中/未命中
3. 缓存失效（含级联依赖失效）
4. get_or_compile 增量编译模式
5. 依赖追踪
6. 统计报告

作者：远
日期：2026-04-03 / 2026-04-07 重构为 pytest 格式
"""

import sys
import os
import time
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.compiler.function_cache import (
    FunctionLevelCache,
    CacheStatus,
    CachedFunction,
    FunctionHash,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def cache_dir():
    """提供临时缓存目录"""
    d = tempfile.mkdtemp(prefix="zhc_func_cache_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def cache(cache_dir):
    """提供已初始化的 FunctionLevelCache 实例"""
    return FunctionLevelCache(cache_dir=cache_dir)


# ============================================================
# 测试：函数哈希计算
# ============================================================

class TestFunctionHash:
    """函数哈希计算的确定性和区分性"""

    def test_same_function_same_hash(self, cache):
        """相同函数应产生相同哈希"""
        h1 = cache.compute_function_hash(
            func_name="add", func_body="return a + b;",
            params="整数型 a, 整数型 b", return_type="整数型"
        )
        h2 = cache.compute_function_hash(
            func_name="add", func_body="return a + b;",
            params="整数型 a, 整数型 b", return_type="整数型"
        )
        assert h1.full_hash == h2.full_hash

    def test_different_functions_different_hashes(self, cache):
        """不同函数应产生不同哈希"""
        h1 = cache.compute_function_hash(
            func_name="add", func_body="return a + b;",
            params="整数型 a, 整数型 b", return_type="整数型"
        )
        h2 = cache.compute_function_hash(
            func_name="sub", func_body="return a - b;",
            params="整数型 a, 整数型 b", return_type="整数型"
        )
        assert h1.full_hash != h2.full_hash

    def test_body_change_changes_hash(self, cache):
        """函数体变化应改变哈希"""
        h1 = cache.compute_function_hash("foo", "body_v1")
        h2 = cache.compute_function_hash("foo", "body_v2")
        assert h1.full_hash != h2.full_hash

    def test_symbols_affect_dependency_hash(self, cache):
        """使用的符号应影响依赖哈希"""
        h1 = cache.compute_function_hash("f", "b", symbols_used={"int"})
        h2 = cache.compute_function_hash("f", "b", symbols_used={"float"})
        # content_hash 相同但 full_hash 应不同（因为 dependency_hash 不同）
        assert h1.content_hash == h2.content_hash
        assert h1.dependency_hash != h2.dependency_hash
        assert h1.full_hash != h2.full_hash

    def test_is_valid(self, cache):
        """is_valid 应正确比较哈希"""
        h1 = cache.compute_function_hash("f", "b")
        h2 = cache.compute_function_hash("f", "b")
        assert h1.is_valid(h2)
        h3 = cache.compute_function_hash("g", "b")
        assert not h1.is_valid(h3)


# ============================================================
# 测试：缓存存取
# ============================================================

class TestCachePutGet:
    """put / get 的基本功能"""

    FUNC_BODY = """
函数 整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}
"""

    def test_put_and_hit(self, cache):
        """存入后应能命中获取"""
        cached = cache.put(
            func_name="加法",
            compiled_code="int add(int a, int b) { return a + b; }",
            func_body=self.FUNC_BODY,
            params="整数型 a, 整数型 b",
            return_type="整数型",
            dependencies=set(),
            symbols_used={"整数型", "+"},
        )

        result, status = cache.get(
            "加法", self.FUNC_BODY,
            params="整数型 a, 整数型 b", return_type="整数型",
            symbols_used={"整数型", "+"}
        )
        assert status == CacheStatus.HIT
        assert result is not None
        assert result.compiled_code == "int add(int a, int b) { return a + b; }"

    def test_get_nonexistent_returns_miss(self, cache):
        """获取不存在的函数应返回 MISS"""
        result, status = cache.get("不存在的函数", "")
        assert status == CacheStatus.MISS
        assert result is None


# ============================================================
# 测试：缓存失效
# ============================================================

class TestCacheInvalidation:
    """invalidate 的行为"""

    def test_invalidate_removes_cached_entry(self, cache):
        """invalidate 后再获取应 MISS"""
        cache.put("test_func", "compiled_code", "original_body")
        result_before, status_before = cache.get("test_func", "original_body")
        assert status_before == CacheStatus.HIT

        cache.invalidate("test_func")

        result_after, status_after = cache.get("test_func", "original_body")
        assert status_after == CacheStatus.MISS
        assert result_after is None

    def test_invalidate_cascade_to_dependents(self, cache):
        """使被依赖的函数失效，依赖它的函数也应失效"""
        cache.put("func_a", "code_a", "body_a")
        cache.put("func_b", "code_b", "body_b", dependencies={"func_a"})

        # 验证两者都存在
        _, s_a = cache.get("func_a", "body_a")
        _, s_b = cache.get("func_b", "body_b")
        assert s_a == CacheStatus.HIT
        assert s_b == CacheStatus.HIT

        # 使 func_a 失效 → func_b 也应被级联删除
        cache.invalidate("func_a")

        _, s_b_after = cache.get("func_b", "body_b")
        assert s_b_after == CacheStatus.MISS, \
            "依赖已失效函数的缓存也应被清除"


# ============================================================
# 测试：get_or_compile 增量编译
# ============================================================

class TestGetOrCompile:
    """get_or_compile 的增量编译逻辑"""

    def test_first_call_compiles(self, cache):
        """首次调用应触发编译，不使用缓存"""
        compile_count = [0]

        def mock_compiler(func_body):
            compile_count[0] += 1
            return f"compiled: {func_body[:20]}..."

        body = "这是一个测试函数体"
        result, used_cache, elapsed = cache.get_or_compile(
            func_name="test_fn", func_body=body,
            params="", return_type="", symbols_used=set(),
            compiler_func=mock_compiler,
        )
        assert compile_count[0] == 1
        assert not used_cache
        assert "compiled:" in result

    def test_second_call_uses_cache(self, cache):
        """第二次调用应使用缓存，不再编译"""
        compile_count = [0]

        def mock_compiler(func_body):
            compile_count[0] += 1
            return f"compiled: {func_body[:20]}..."

        body = "这是一个测试函数体"

        # 第一次 — 编译
        r1, c1, _ = cache.get_or_compile(
            "test_fn", body, "", "", set(), mock_compiler)
        assert not c1

        # 第二次 — 缓存
        r2, c2, _ = cache.get_or_compile(
            "test_fn", body, "", "", set(), mock_compiler)
        assert c2, "第二次调用应该使用缓存"
        assert r1 == r2
        assert compile_count[0] == 1, "不应重新编译"


# ============================================================
# 测试：依赖追踪
# ============================================================

class TestDependencyTracking:
    """依赖图的构建和查询"""

    def test_dependencies_stored_in_graph(self, cache):
        """put 时记录依赖关系"""
        cache.put("main_fn", "code", "body", dependencies={"helper_fn"})
        # 内部的 _dependency_graph 应包含此关系
        assert "helper_fn" in cache._dependency_graph["main_fn"]

    def test_invalidate_propagates_through_chain(self, cache):
        """A <- B <- C，使 A 失效则 B、C 都应失效"""
        cache.put("a", "ca", "ba")
        cache.put("b", "cb", "bb", dependencies={"a"})
        cache.put("c", "cc", "bc", dependencies={"b"})

        cache.invalidate("a")

        # b 依赖 a，a 已删除 → b 被级联删除
        _, sb = cache.get("b", "bb")
        assert sb == CacheStatus.MISS

        # c 依赖 b，b 已删除 → c 被级联删除
        _, sc = cache.get("c", "bc")
        assert sc == CacheStatus.MISS


# ============================================================
# 测试：统计信息
# ============================================================

class TestStatistics:
    """get_statistics 和 get_report"""

    def test_statistics_reflects_operations(self, cache):
        """统计应反映实际操作"""
        cache.put("f1", "c1", "b1")       # put 不计入 request
        cache.get("f1", "b1")              # HIT
        cache.get("f2", "b2")              # MISS

        stats = cache.get_statistics()
        assert stats['total_requests'] == 2
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1

    def test_report_is_string(self, cache):
        """get_report 返回非空字符串"""
        report = cache.get_report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "函数级编译缓存报告" in report

    def test_clear_resets_statistics(self, cache):
        """clear 后统计应重置"""
        cache.put("f", "c", "b")
        cache.get("f", "b")
        cache.clear()

        stats = cache.get_statistics()
        assert stats['total_requests'] == 0
        assert stats['cache_hits'] == 0
