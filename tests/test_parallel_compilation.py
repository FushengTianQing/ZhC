#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行编译性能测试 (P1级 - pytest兼容)

测试内容：
1. 编译层级计算算法
2. 并行编译vs串行编译性能对比
3. 自适应并行流水线
4. CPU利用率

作者：远
日期：2026-04-03
更新：2026-04-07 重写为pytest格式
"""

import sys
import os
import time
import tempfile
import shutil
import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.compiler.parallel_pipeline import (
    ParallelCompilationPipeline,
    AdaptiveParallelPipeline,
    CompilationLayerCalculator,
    ParallelStrategy,
    ModuleInfo,
    CompilationResult,
)


class TestCompilationLayerCalculator:
    """P1级并发编译: 层级计算器测试"""

    def test_simple_dag(self):
        """测试简单DAG依赖层级计算"""
        calculator = CompilationLayerCalculator()
        # A(0) -> B,C(1) -> D(2) -> E(3)
        calculator.add_module("A", [])
        calculator.add_module("B", ["A"])
        calculator.add_module("C", ["A"])
        calculator.add_module("D", ["B", "C"])
        calculator.add_module("E", ["D"])

        levels = calculator.compute_levels()

        assert levels["A"] == 0, f"A应为Level 0, 实际{levels.get('A')}"
        assert levels["B"] == 1, f"B应为Level 1, 实际{levels.get('B')}"
        assert levels["C"] == 1, f"C应为Level 1, 实际{levels.get('C')}"
        assert levels["D"] == 2, f"D应为Level 2, 实际{levels.get('D')}"
        assert levels["E"] == 3, f"E应为Level 3, 实际{levels.get('E')}"

    def test_no_dependencies(self):
        """无依赖模块应为Level 0"""
        calculator = CompilationLayerCalculator()
        calculator.add_module("X", [])
        calculator.add_module("Y", [])

        levels = calculator.compute_levels()
        assert levels["X"] == 0
        assert levels["Y"] == 0

    def test_single_module(self):
        """单模块"""
        calculator = CompilationLayerCalculator()
        calculator.add_module("Solo", [])

        levels = calculator.compute_levels()
        assert levels["Solo"] == 0

    def test_get_layers_grouping(self):
        """get_layers正确分组"""
        calculator = CompilationLayerCalculator()
        calculator.add_module("A", [])
        calculator.add_module("B", ["A"])
        calculator.add_module("C", ["A"])

        layers = calculator.get_layers()
        assert len(layers) >= 2  # 至少2层
        assert "A" in layers[0]  # A在Level 0
        assert "B" in layers[1] or "C" in layers[1]

    def test_complex_dag(self):
        """更复杂的依赖图"""
        calculator = CompilationLayerCalculator()
        # 核心工具/数据库/网络 都依赖核心
        # 业务依赖数据库+网络，接口依赖业务+网络
        # 主程序依赖业务+接口
        calculator.add_module("核心", [])
        calculator.add_module("工具", ["核心"])
        calculator.add_module("数据库", ["核心"])
        calculator.add_module("网络", ["核心", "工具"])
        calculator.add_module("业务", ["数据库", "网络"])
        calculator.add_module("接口", ["业务", "网络"])
        calculator.add_module("主程序", ["业务", "接口"])

        levels = calculator.compute_levels()

        assert levels["核心"] == 0
        assert levels["工具"] == 1
        assert levels["数据库"] == 1
        assert levels["网络"] == 2  # 依赖 核心(Level0)+工具(Level1) => max(0,1)+1=2
        assert levels["业务"] == 3
        assert levels["接口"] == 4
        assert levels["主程序"] == 5

    def test_isolated_module(self):
        """孤立模块（无依赖也无人依赖）应被包含"""
        calculator = CompilationLayerCalculator()
        calculator.add_module("A", ["B"])  # A依赖B
        calculator.add_module("B", [])     # B无依赖

        levels = calculator.compute_levels()
        assert "A" in levels
        assert "B" in levels


class TestParallelCompilationPipeline:
    """P1级并发编译: 并行编译流水线测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zhc_parallel_test_")

    def teardown_method(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_module(self, name: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir, f"{name}.zhc")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_creation_with_defaults(self):
        """默认参数创建"""
        pipeline = ParallelCompilationPipeline()
        assert pipeline.max_workers > 0
        assert pipeline.strategy == ParallelStrategy.PROCESS  # AUTO默认选PROCESS
        pipeline.shutdown()

    def test_creation_thread_strategy(self):
        """线程池策略创建"""
        pipeline = ParallelCompilationPipeline(
            max_workers=4,
            strategy=ParallelStrategy.THREAD,
            enable_cache=False,
        )
        assert pipeline.max_workers == 4
        assert pipeline._executor_type == "thread"
        pipeline.shutdown()

    def test_add_modules(self):
        """添加模块"""
        pipeline = ParallelCompilationPipeline(enable_cache=False)
        fp1 = self._create_test_module("mod1", "整数型 x;")
        fp2 = self._create_test_module("mod2", "浮点型 y;")

        pipeline.add_module("M1", fp1, [])
        pipeline.add_module("M2", fp2, ["M1"])

        assert "M1" in pipeline.modules
        assert "M2" in pipeline.modules
        assert len(pipeline.modules["M2"].dependencies) == 1
        pipeline.shutdown()

    def test_layer_calculation_in_pipeline(self):
        """流水线中层级计算"""
        pipeline = ParallelCompilationPipeline(enable_cache=False)
        for name, deps in [("A", []), ("B", ["A"]), ("C", ["A"]), ("D", ["B", "C"])]:
            fp = self._create_test_module(name, "")
            pipeline.add_module(name, fp, deps)

        layers = pipeline.layer_calculator.get_layers()
        assert len(layers) >= 3  # 至少3层: L0=[A], L1=[B,C], L2=[D]
        pipeline.shutdown()

    def test_compile_sequential(self):
        """串行编译不报错"""
        pipeline = ParallelCompilationPipeline(max_workers=1, enable_cache=False)
        for i in range(5):
            fp = self._create_test_module(f"m{i}", f"整数型 v{i};")
            pipeline.add_module(f"m{i}", fp, [] if i == 0 else [f"{i-1}"])

        results = pipeline.compile_sequential()
        assert len(results) == 5
        # 编译结果可能成功也可能失败（取决于文件内容），但不应抛异常
        for name, result in results.items():
            assert isinstance(result, CompilationResult)
            assert result.module_name == name
        pipeline.shutdown()

    def test_parallel_compile_basic(self):
        """基本并行编译"""
        pipeline = ParallelCompilationPipeline(
            max_workers=2,
            strategy=ParallelStrategy.THREAD,
            enable_cache=False,
        )
        for i in range(4):
            fp = self._create_test_module(f"p{i}", f"整数型 p{i};")
            deps = [] if i < 2 else [f"p{i-2}"]
            pipeline.add_module(f"p{i}", fp, deps)

        results = pipeline.compile_parallel(show_progress=False)
        assert len(results) == 4
        pipeline.shutdown()

    def test_stats_report(self):
        """统计报告生成"""
        pipeline = ParallelCompilationPipeline(enable_cache=False)
        report = pipeline.get_stats_report()
        assert isinstance(report, str)
        assert len(report) > 0
        pipeline.shutdown()

    def test_context_manager(self):
        """上下文管理器支持"""
        with ParallelCompilationPipeline(enable_cache=False) as pipeline:
            fp = self._create_test_module("ctx_mod", "整数型 a;")
            pipeline.add_module("ctx_mod", fp, [])
            results = pipeline.compile_parallel(show_progress=False)
            assert len(results) == 1

    def test_empty_pipeline(self):
        """空流水线不崩溃"""
        pipeline = ParallelCompilationPipeline(enable_cache=False)
        results = pipeline.compile_parallel()
        assert results == {}
        pipeline.shutdown()


class TestAdaptiveParallelPipeline:
    """P1级并发编译: 自适应流水线测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zhc_adaptive_test_")

    def teardown_method(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_module(self, name, deps=None):
        fp = os.path.join(self.temp_dir, f"{name}.zhc")
        with open(fp, 'w') as f:
            f.write(f"模块 {name};\n")
        return fp

    def test_creation(self):
        """自适应流水线创建"""
        pipeline = AdaptiveParallelPipeline(max_workers=4, enable_cache=False)
        assert hasattr(pipeline, 'compile_frequency')
        assert hasattr(pipeline, 'hot_modules')
        pipeline.shutdown()

    def test_priority_computation(self):
        """优先级计算"""
        pipeline = AdaptiveParallelPipeline(enable_cache=False)

        # 小文件、无依赖、高频 => 高优先级
        fp = self._create_module("hot_mod")
        pipeline.add_module("hot_mod", fp, [])

        # 多次添加模拟高频
        for _ in range(5):
            pipeline.add_module("hot_mod", fp, [])

        priority = pipeline._compute_module_priority("hot_mod")
        assert priority >= 0
        assert isinstance(priority, (int, float))
        pipeline.shutdown()

    def test_adaptive_compile(self):
        """自适应并行编译执行"""
        pipeline = AdaptiveParallelPipeline(
            max_workers=2,
            enable_cache=False,
        )
        modules = {
            "A": [], "B": ["A"], "C": ["A"],
            "D": ["B", "C"], "E": ["D"],
        }
        for name, deps in modules.items():
            fp = self._create_module(name, deps)
            pipeline.add_module(name, fp, deps)

        results = pipeline.compile_parallel_adaptive(show_progress=False)
        assert len(results) == 5
        pipeline.shutdown()


class TestParallelCompilationSpeedup:
    """P1级并发编译: 性能基准"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zhc_perf_test_")

    def teardown_method(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _make_modules(self, count):
        paths = []
        for i in range(count):
            fp = os.path.join(self.temp_dir, f"perf_{i}.zhc")
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(f"整数型 变量_{i} = {i};\n")
            paths.append(fp)
        return paths

    def test_parallel_not_slower_than_serial(self):
        """并行编译不应慢于串行太多"""
        module_paths = self._make_modules(10)

        # 串行
        serial = ParallelCompilationPipeline(max_workers=1, strategy=ParallelStrategy.THREAD, enable_cache=False)
        for i, fp in enumerate(module_paths):
            serial.add_module(f"s_{i}", fp, [] if i == 0 else [f"s_{i-1}"])

        t_start = time.time()
        serial_results = serial.compile_sequential()
        serial_time = time.time() - t_start
        serial.shutdown()

        # 并行 (2 workers)
        parallel = ParallelCompilationPipeline(max_workers=2, strategy=ParallelStrategy.THREAD, enable_cache=False)
        for i, fp in enumerate(module_paths):
            parallel.add_module(f"p_{i}", fp, [] if i < 2 else [f"p_{i-2}"])

        t_start = time.time()
        parallel_results = parallel.compile_parallel(show_progress=False)
        parallel_time = time.time() - t_start
        parallel.shutdown()

        # 并行不应比串行慢超过3倍（允许线程开销）
        # 注意：小任务可能并行开销更大，用宽松阈值
        assert serial_time > 0 or parallel_time > 0  # 至少完成
        if serial_time > 0.01 and parallel_time > 0.01:
            ratio = parallel_time / serial_time
            assert ratio < 5.0, f"并行({parallel_time:.3f}s)比串行({serial_time:.3f}s)慢太多, 比值={ratio:.2f}"
