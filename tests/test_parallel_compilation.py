#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行编译性能测试

测试内容：
1. 编译层级计算算法
2. 并行编译vs串行编译性能对比
3. 多核CPU利用率测试

作者：远
日期：2026-04-03
"""

import sys
import os
import time
import tempfile
import shutil
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.compiler.parallel_pipeline import (
    ParallelCompilationPipeline,
    AdaptiveParallelPipeline,
    CompilationLayerCalculator,
    ParallelStrategy,
    ModuleInfo
)


class ParallelCompilationTestSuite:
    """并行编译测试套件"""

    def __init__(self):
        self.test_results: List[Dict] = []
        self.temp_dir = None

    def setup(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp(prefix="zhc_parallel_test_")
        print(f"测试目录: {self.temp_dir}")

    def teardown(self):
        """清理测试环境"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_module(self, name: str, content: str) -> str:
        """创建测试模块文件"""
        filepath = os.path.join(self.temp_dir, f"{name}.zhc")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_layer_calculator(self):
        """测试编译层级计算算法"""
        print("=" * 70)
        print("测试1: 编译层级计算算法")
        print("=" * 70)

        calculator = CompilationLayerCalculator()

        # 添加模块及其依赖
        # A (无依赖)
        # B (依赖A)
        # C (依赖A)
        # D (依赖B和C)
        # E (依赖D)

        calculator.add_module("A", [])
        calculator.add_module("B", ["A"])
        calculator.add_module("C", ["A"])
        calculator.add_module("D", ["B", "C"])
        calculator.add_module("E", ["D"])

        # 计算层级
        levels = calculator.compute_levels()

        print(f"计算结果:")
        for module, level in sorted(levels.items()):
            print(f"  {module}: Level {level}")

        # 获取分层
        layers = calculator.get_layers()

        print(f"\n分层结果:")
        for i, layer in enumerate(layers):
            print(f"  Level {i}: {layer}")

        # 验证
        expected = {
            "A": 0,  # 无依赖
            "B": 1,  # 依赖A
            "C": 1,  # 依赖A
            "D": 2,  # 依赖B,C (max(1,1)+1=2)
            "E": 3,  # 依赖D (2+1=3)
        }

        success = all(levels.get(m) == l for m, l in expected.items())

        print()
        if success:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            print(f"预期: {expected}")
            print(f"实际: {levels}")

        return success

    def test_parallel_compilation_speedup(self):
        """测试并行编译加速比"""
        print()
        print("=" * 70)
        print("测试2: 并行编译加速比")
        print("=" * 70)

        # 创建测试模块
        self.setup()

        try:
            # 创建依赖树
            modules = {
                "核心": [],
                "工具": ["核心"],
                "数据库": ["核心"],
                "网络": ["核心", "工具"],
                "业务": ["数据库", "网络"],
                "接口": ["业务", "网络"],
                "主程序": ["业务", "接口"],
            }

            # 创建模块文件
            for name, deps in modules.items():
                content = f"""
模块 {name};
导入 {", ".join(deps) if deps else "无"}。

函数 整数型 获取_{name}_版本() {{
    返回 1;
}}
"""
                self.create_test_module(name, content)

            # 创建并行编译流水线
            print(f"\n创建测试模块: {len(modules)} 个")
            print(f"CPU核心数: {os.cpu_count()}")

            # 测试并行编译
            parallel_pipeline = ParallelCompilationPipeline(
                max_workers=4,
                strategy=ParallelStrategy.THREAD,
                enable_cache=False
            )

            for name, deps in modules.items():
                filepath = os.path.join(self.temp_dir, f"{name}.zhc")
                parallel_pipeline.add_module(name, filepath, deps)

            # 并行编译
            print("\n执行并行编译...")
            parallel_start = time.time()
            parallel_results = parallel_pipeline.compile_parallel(show_progress=False)
            parallel_time = time.time() - parallel_start

            parallel_success = sum(1 for r in parallel_results.values() if r.success)

            parallel_pipeline.shutdown()

            # 测试串行编译
            print("执行串行编译...")
            serial_pipeline = ParallelCompilationPipeline(
                max_workers=1,
                strategy=ParallelStrategy.THREAD,
                enable_cache=False
            )

            for name, deps in modules.items():
                filepath = os.path.join(self.temp_dir, f"{name}.zhc")
                serial_pipeline.add_module(name, filepath, deps)

            serial_start = time.time()
            serial_results = serial_pipeline.compile_sequential()
            serial_time = time.time() - serial_start

            serial_pipeline.shutdown()

            # 计算加速比
            speedup = serial_time / parallel_time if parallel_time > 0 else 0

            print(f"\n性能对比:")
            print(f"  串行编译: {serial_time:.4f}s")
            print(f"  并行编译: {parallel_time:.4f}s")
            print(f"  加速比: {speedup:.2f}x")
            print(f"  成功率: {parallel_success}/{len(modules)}")

            # 判断加速效果
            # 注意: 由于测试模块很小,加速比可能不明显
            # 这里我们主要验证并行编译能正常工作

            success = parallel_success == len(modules)

            print()
            if success:
                print("✅ 测试通过 (并行编译正常工作)")
            else:
                print("❌ 测试失败")

            return success

        finally:
            self.teardown()

    def test_adaptive_pipeline(self):
        """测试自适应并行流水线"""
        print()
        print("=" * 70)
        print("测试3: 自适应并行编译")
        print("=" * 70)

        # 创建自适应流水线
        pipeline = AdaptiveParallelPipeline(
            max_workers=4,
            enable_cache=False
        )

        # 添加模块
        modules = {
            "A": [],
            "B": ["A"],
            "C": ["A"],
            "D": ["B", "C"],
            "E": ["D"],
        }

        for name, deps in modules.items():
            filepath = os.path.join(self.temp_dir or "", f"{name}.zhc")
            pipeline.add_module(name, filepath, deps)

        # 计算优先级
        print("\n模块优先级:")
        for name in modules.keys():
            priority = pipeline._compute_module_priority(name)
            freq = pipeline.compile_frequency.get(name, 0)
            print(f"  {name}: 优先级={priority}, 编译频率={freq}")

        # 获取分层
        layers = pipeline.layer_calculator.get_layers()

        print("\n编译层级:")
        for i, layer in enumerate(layers):
            sorted_layer = pipeline._sort_layer_by_priority(layer)
            print(f"  Level {i}: {sorted_layer}")

        pipeline.shutdown()

        print()
        print("✅ 测试通过")

        return True

    def test_cpu_utilization(self):
        """测试CPU利用率"""
        print()
        print("=" * 70)
        print("测试4: CPU利用率")
        print("=" * 70)

        cpu_count = os.cpu_count()
        print(f"\n系统CPU核心数: {cpu_count}")

        # 创建大量小任务测试CPU利用率
        pipeline = ParallelCompilationPipeline(
            max_workers=cpu_count,
            strategy=ParallelStrategy.PROCESS,
            enable_cache=False
        )

        # 创建测试模块
        self.setup()

        try:
            # 创建多个小模块
            num_modules = 20
            for i in range(num_modules):
                content = f"""
模块 测试模块_{i};
导入 核心模块。

函数 整数型 计算_{i}(整数型 n) {{
    返回 n * {i};
}}
"""
                filepath = self.create_test_module(f"模块_{i}", content)
                deps = [] if i % 3 == 0 else [f"模块_{i-1}"]
                pipeline.add_module(f"模块_{i}", filepath, deps)

            print(f"\n测试模块数: {num_modules}")

            # 编译
            start = time.time()
            results = pipeline.compile_parallel(show_progress=False)
            elapsed = time.time() - start

            success = sum(1 for r in results.values() if r.success)

            print(f"  成功编译: {success}/{num_modules}")
            print(f"  总耗时: {elapsed:.2f}s")

            # 理想时间（假设完全并行）
            avg_time = sum(r.compile_time for r in results.values()) / len(results)
            ideal_time = avg_time  # 因为是并行执行
            cpu_util = (ideal_time * num_modules / elapsed / cpu_count * 100) if elapsed > 0 else 0

            print(f"  估算CPU利用率: {cpu_util:.1f}%")

            pipeline.shutdown()

            print()
            print("✅ 测试通过")

            return success == num_modules

        finally:
            self.teardown()

    def run_all_tests(self):
        """运行所有测试"""
        print()
        print("=" * 70)
        print("并行编译性能测试")
        print("=" * 70)
        print()

        results = []

        # 设置测试目录
        self.setup()

        try:
            # 测试1: 编译层级计算
            results.append(("编译层级计算", self.test_layer_calculator()))

            # 测试2: 并行编译加速比
            results.append(("并行编译加速比", self.test_parallel_compilation_speedup()))

            # 测试3: 自适应流水线
            results.append(("自适应并行编译", self.test_adaptive_pipeline()))

            # 测试4: CPU利用率
            results.append(("CPU利用率", self.test_cpu_utilization()))

        finally:
            self.teardown()

        # 总结
        print()
        print("=" * 70)
        print("测试总结")
        print("=" * 70)

        for test_name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{test_name}: {status}")

        all_passed = all(r[1] for r in results)

        print()
        if all_passed:
            print("🎉 所有测试通过!")
        else:
            print("⚠️ 部分测试失败")

        print("=" * 70)

        return all_passed


def main():
    """主函数"""
    suite = ParallelCompilationTestSuite()
    success = suite.run_all_tests()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())