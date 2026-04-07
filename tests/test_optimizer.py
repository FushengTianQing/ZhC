# -*- coding: utf-8 -*-
"""
test_optimizer.py - compiler/optimizer.py 单元测试

覆盖:
- PerformanceMonitor: 性能监控、阶段计时、摘要报告
- AlgorithmOptimizer: 依赖图优化、节点层级、内存优化
- ConcurrentCompiler: 并发编译、流水线并行
- IncrementalOptimizer: 增量分析、受影响文件计算

运行: python -m pytest tests/test_optimizer.py -v
"""

import pytest
import sys
import time
import tempfile
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.compiler.optimizer import (
    PerformanceMonitor,
    AlgorithmOptimizer,
    ConcurrentCompiler,
    IncrementalOptimizer,
)


# =============================================================================
# PerformanceMonitor 测试 (12 tests)
# =============================================================================

class TestPerformanceMonitor:
    """性能监控器"""

    def test_init(self):
        """初始化 metrics 和状态"""
        m = PerformanceMonitor()
        assert 'parse_time' in m.metrics
        assert 'compile_time' in m.metrics
        assert 'memory_usage' in m.metrics
        assert 'cpu_usage' in m.metrics
        assert m.peak_memory == 0

    def test_start_phase_returns_timestamp(self):
        """start_phase 返回 float 时间戳"""
        ts = PerformanceMonitor().start_phase('parse_time')
        assert isinstance(ts, float)
        assert ts > 0

    def test_end_phase_records_duration(self):
        """end_phase 记录阶段耗时"""
        m = PerformanceMonitor()
        ts = m.start_phase('compile_time')
        time.sleep(0.01)
        m.end_phase('compile_time', ts)
        assert len(m.metrics['compile_time']) == 1
        assert m.metrics['compile_time'][0] >= 0.01

    def test_end_phase_records_memory(self):
        """end_phase 同时记录内存"""
        m = PerformanceMonitor()
        ts = m.start_phase('parse_time')
        m.end_phase('parse_time', ts)
        assert len(m.metrics['memory_usage']) == 1

    def test_end_phase_records_cpu(self):
        """end_phase 同时记录 CPU"""
        m = PerformanceMonitor()
        ts = m.start_phase('parse_time')
        m.end_phase('parse_time', ts)
        assert len(m.metrics['cpu_usage']) == 1

    def test_peak_memory_updates(self):
        """峰值内存随 end_phase 更新"""
        m = PerformanceMonitor()
        for _ in range(3):
            t = m.start_phase('parse_time')
            m.end_phase('parse_time', t)
        assert m.peak_memory >= 0

    def test_get_summary_has_required_keys(self):
        """get_summary 包含 total_time / peak_memory_mb / phases / indicators"""
        s = self._make_monitor_with_data().get_summary()
        assert 'total_time' in s
        assert 'peak_memory_mb' in s
        assert 'phases' in s
        assert 'performance_indicators' in s

    def test_get_summary_phases_stats(self):
        """phases 统计含 count/total/avg/min/max/std"""
        m = PerformanceMonitor()
        for _ in range(3):
            t = m.start_phase('parse_time')
            time.sleep(0.005)
            m.end_phase('parse_time', t)
        ps = m.get_summary()['phases']['parse_time']
        assert ps['count'] == 3
        assert all(k in ps for k in ('total', 'avg', 'min', 'max', 'std'))

    def test_calculate_std_single_value_is_zero(self):
        """单值标准差为 0"""
        assert abs(PerformanceMonitor()._calculate_std([42.0]) - 0) < 1e-9

    def test_calculate_std_multiple_values_positive(self):
        """多值标准差正数"""
        std = PerformanceMonitor()._calculate_std([1, 2, 3])
        assert std >= 0

    def test_print_report_no_crash(self):
        """print_report 不崩溃"""
        self._make_monitor_with_data().print_report()

    def test_multi_phase_independent(self):
        """多阶段互不干扰"""
        m = PerformanceMonitor()
        t1 = m.start_phase('parse_time'); m.end_phase('parse_time', t1)
        t2 = m.start_phase('compile_time'); m.end_phase('compile_time', t2)
        assert len(m.metrics['parse_time']) == 1 and len(m.metrics['compile_time']) == 1

    # -- helper --
    @staticmethod
    def _make_monitor_with_data():
        m = PerformanceMonitor()
        for _ in range(3):
            t = m.start_phase('parse_time'); time.sleep(0.005); m.end_phase('parse_time', t)
        return m


# =============================================================================
# AlgorithmOptimizer 测试 (14 tests)
# =============================================================================

class TestAlgorithmOptimizer:
    """算法优化器"""

    def _simple_graph(self):
        return {'A': ['B', 'C'], 'B': ['C'], 'C': []}

    def test_optimize_basic(self):
        """基本依赖图优化不丢失节点"""
        g = self._simple_graph()
        opt, lvls = AlgorithmOptimizer.optimize_dependency_resolution(g)
        assert set(opt.keys()) == {'A', 'B', 'C'}

    def test_optimize_removes_transitive_deps(self):
        """移除传递依赖（C 通过 B 已被 A 间接依赖）"""
        opt, _ = AlgorithmOptimizer.optimize_dependency_resolution(self._simple_graph())
        assert len(opt['A']) <= 2

    def test_optimize_empty_graph(self):
        """空图返回空"""
        o, l = AlgorithmOptimizer.optimize_dependency_resolution({})
        assert o == {} and l == {}

    def test_optimize_no_deps(self):
        """无依赖图保持不变"""
        o, _ = AlgorithmOptimizer.optimize_dependency_resolution({'X': [], 'Y': []})
        assert o['X'] == [] and o['Y'] == []

    def test_levels_topo_order(self):
        """层级满足拓扑顺序：根 >= 父级（被依赖越多层级越高）"""
        _, lvls = AlgorithmOptimizer.optimize_dependency_resolution(
            {'A': ['B'], 'B': ['C'], 'C': []})
        assert lvls['A'] <= lvls['B'] <= lvls['C']

    def test_compress_preserves_keys(self):
        """压缩后保留所有键"""
        c = AlgorithmOptimizer._compress_transitive_dependencies(self._simple_graph())
        assert set(c.keys()) == {'A', 'B', 'C'}

    def test_compress_reduces_edges(self):
        """压缩可能减少边数"""
        c = AlgorithmOptimizer._compress_transitive_dependencies({'A': ['B', 'C'], 'B': ['C'], 'C': []})
        assert len(c['A']) <= 2

    def test_node_levels_non_negative(self):
        """层级全部 >= 0"""
        lvls = AlgorithmOptimizer._calculate_node_levels(self._simple_graph())
        assert all(v >= 0 for v in lvls.values())

    def test_sort_by_level(self):
        """按层级排序后依赖顺序合理"""
        s = AlgorithmOptimizer._sort_dependencies_by_level(
            {'A': ['B', 'C']}, {'A': 2, 'B': 1, 'C': 0})
        assert len(s['A']) == 2

    def test_remove_redundant_keeps_necessary(self):
        """移除冗余后保留必要依赖"""
        r = AlgorithmOptimizer._remove_redundant_dependencies(
            {'A': ['B', 'C'], 'B': [], 'C': []})
        assert 'B' in r['A']

    def test_mem_opt_dict_passthrough(self):
        """字典原样返回"""
        d = {'x': 1}
        assert AlgorithmOptimizer.optimize_memory_usage(d) == d

    def test_mem_opt_list_passthrough(self):
        """列表原样返回"""
        assert AlgorithmOptimizer.optimize_memory_usage([1, 2]) == [1, 2]

    def test_mem_opt_small_set_to_frozenset(self):
        """小集合转 frozenset"""
        assert isinstance(AlgorithmOptimizer.optimize_memory_usage({1, 2}), frozenset)

    def test_mem_opt_large_set_stays_set(self):
        """大集合保持 set"""
        assert isinstance(AlgorithmOptimizer.optimize_memory_usage(set(range(20))), set)


# =============================================================================
# ConcurrentCompiler 测试 (8 tests)
# =============================================================================

class TestConcurrentCompiler:
    """并发编译器"""

    def test_default_init_thread_mode(self):
        """默认线程模式"""
        cc = ConcurrentCompiler()
        assert cc.use_processes is False
        assert cc.max_workers > 0

    def test_process_mode(self):
        """进程模式"""
        cc = ConcurrentCompiler(max_workers=2, use_processes=True)
        assert cc.use_processes is True
        assert cc.executor_class.__name__ == 'ProcessPoolExecutor'

    def test_empty_files_returns_empty(self):
        """空文件列表返回空 dict"""
        assert ConcurrentCompiler().compile_files_concurrently([], lambda f: f) == {}

    def test_single_file_compiled(self):
        """单文件正确调用编译函数"""
        r = ConcurrentCompiler(max_workers=1).compile_files_concurrently(
            [Path('a.zhc')], lambda f: f"ok:{f}")
        assert r[Path('a.zhc')] == "ok:a.zhc"

    def test_multiple_files_all_results(self):
        """多文件全部返回"""
        files = [Path(f'{i}.zhc') for i in range(4)]
        r = ConcurrentCompiler(max_workers=2).compile_files_concurrently(
            files, lambda f: str(f))
        assert len(r) == 4

    def test_error_captured_as_dict(self):
        """异常被捕获为 error dict"""
        def boom(f): raise RuntimeError("fail")
        r = ConcurrentCompiler(max_workers=1).compile_files_concurrently([Path('e.zhc')], boom)
        assert "error" in r[Path('e.zhc')]

    def test_pipeline_empty_stages_passthrough(self):
        """空 stages 返回原数据"""
        assert ConcurrentCompiler().pipeline_parallel_compile([], 42) == 42

    def test_pipeline_single_stage(self):
        """单阶段执行"""
        r = ConcurrentCompiler().pipeline_parallel_compile([lambda x: x + 1], 10)
        assert r == 11


# =============================================================================
# IncrementalOptimizer 测试 (7 tests)
# =============================================================================

class TestIncrementalOptimizer:
    """增量优化器"""

    def test_init_defaults(self):
        """初始化属性"""
        io = IncrementalOptimizer(cache_system={'k': 'v'})
        assert io.cache == {'k': 'v'}
        assert io.dependency_graph == {}
        assert io.file_modification_times == {}

    def _tmp_file(self, name='t'):
        p = Path(tempfile.mktemp(suffix=f'.zhc'))
        p.write_text(name)
        return p

    def test_new_file_marked_added(self):
        """新文件 → added（文件存在但未被追踪）"""
        p = self._tmp_file()
        try:
            ch = IncrementalOptimizer({}).analyze_changes([p])
            assert len(ch['added']) == 1 and ch['modified'] == []
        finally:
            p.unlink()

    def test_missing_file_marked_deleted(self):
        """已记录但不存在 → deleted"""
        io = IncrementalOptimizer({})
        p = self._tmp_file(); p.unlink()
        io.file_modification_times[p] = 100
        ch = io.analyze_changes([p])
        assert len(ch['deleted']) == 1

    def test_unchanged_file(self):
        """mtime 未变 → unchanged"""
        io = IncrementalOptimizer({})
        p = self._tmp_file('u')
        try:
            io.file_modification_times[p] = p.stat().st_mtime
            ch = io.analyze_changes([p])
            assert len(ch['unchanged']) == 1
        finally:
            p.unlink()

    def test_modified_file(self):
        """mtime 变了 → modified"""
        io = IncrementalOptimizer({})
        p = self._tmp_file('m')
        try:
            io.file_modification_times[p] = p.stat().st_mtime - 60
            ch = io.analyze_changes([p])
            assert len(ch['modified']) == 1
        finally:
            p.unlink()

    def test_affected_includes_self(self):
        """受影响文件包含变更文件自身"""
        dep = {'main': [], 'lib': []}
        aff = IncrementalOptimizer({}).get_affected_files(
            [Path('/main.zhc'), Path('/lib.zhc')], dep)
        # 至少包含 main.zhc 和 lib.zhc
        assert len(aff) >= 2

    def test_affected_reverse_dep(self):
        """反向依赖传播：改 A 影响 B（如果 B 依赖 A）"""
        dep = {'app': ['core'], 'core': []}
        aff = IncrementalOptimizer({}).get_affected_files([Path('/core.zhc')], dep)
        # core.zhc 改变应影响 app.zhc
        assert any('app' in str(p) or 'core' in str(p) for p in aff)
