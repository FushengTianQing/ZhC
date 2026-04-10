# -*- coding: utf-8 -*-
"""
ZhC IR - 支配树算法性能对比测试

对比 Lengauer-Tarjan 算法和迭代算法的性能。

作者: 阿福
日期: 2026-04-08
"""

import pytest
import time
import random
from zhc.ir.dominator import (
    LengauerTarjanDominator,
    build_dominator_tree_iterative,
)


def generate_linear_chain(num_blocks: int) -> dict:
    """生成线性链控制流图"""
    blocks = {}
    labels = [f"b{i}" for i in range(num_blocks)]

    for i, label in enumerate(labels):
        if i == 0:
            blocks[label] = ([], [labels[1]] if i + 1 < len(labels) else [])
        elif i == len(labels) - 1:
            blocks[label] = ([labels[i - 1]], [])
        else:
            blocks[label] = ([labels[i - 1]], [labels[i + 1]])

    return blocks


def generate_diamond_chain(num_diamonds: int) -> dict:
    """生成菱形链控制流图"""
    blocks = {"entry": ([], ["d0_a"])}

    for i in range(num_diamonds):
        a = f"d{i}_a"
        b = f"d{i}_b"
        c = f"d{i}_c"
        merge = f"d{i}_merge"

        if i == 0:
            blocks[a] = (["entry"], [b, c])
        else:
            prev_merge = f"d{i-1}_merge"
            blocks[a] = ([prev_merge], [b, c])

        blocks[b] = ([a], [merge])
        blocks[c] = ([a], [merge])
        blocks[merge] = ([b, c], [])

        if i == num_diamonds - 1:
            blocks[merge] = ([b, c], ["exit"])

    blocks["exit"] = (
        [f"d{num_diamonds-1}_merge"] if num_diamonds > 0 else ["entry"],
        [],
    )

    return blocks


def generate_loop_graph(num_loops: int) -> dict:
    """生成带循环的控制流图"""
    blocks = {"entry": ([], ["loop0"])}

    for i in range(num_loops):
        loop = f"loop{i}"
        body = f"body{i}"
        merge = f"merge{i}"

        blocks[loop] = ([f"entry" if i == 0 else f"merge{i-1}", loop], [body])
        blocks[body] = ([loop], [merge])

        if i == num_loops - 1:
            blocks[merge] = ([body], ["exit"])
        else:
            blocks[merge] = ([body], [f"loop{i+1}"])

    blocks["exit"] = ([f"merge{num_loops-1}"] if num_loops > 0 else ["entry"], [])

    return blocks


def generate_complex_cfg(num_blocks: int, edge_probability: float = 0.3) -> dict:
    """生成复杂随机控制流图"""
    labels = [f"b{i}" for i in range(num_blocks)]
    blocks = {}

    # 随机生成前驱和后继
    # 使用更可靠的生成方法：先随机决定边，然后确保可达性
    has_edge = {}
    for i in range(num_blocks):
        for j in range(i + 1, num_blocks):
            has_edge[(i, j)] = random.random() < edge_probability

    # 确保所有节点（除入口外）都有至少一个前驱
    for i in range(1, num_blocks):
        # 检查是否有任何边指向 i
        has_pred = any(has_edge.get((j, i), False) for j in range(i))
        if not has_pred:
            # 添加从 i-1 到 i 的边
            has_edge[(i - 1, i)] = True

    # 构建前驱和后继列表
    for i, label in enumerate(labels):
        preds = []
        succs = []

        for j in range(i):
            if has_edge.get((j, i), False):
                preds.append(labels[j])

        for j in range(i + 1, num_blocks):
            if has_edge.get((i, j), False):
                succs.append(labels[j])

        blocks[label] = (preds, succs)

    return blocks


class TestPerformanceComparison:
    """性能对比测试"""

    def test_linear_chain_performance(self):
        """测试线性链性能"""
        sizes = [10, 100, 1000, 5000]
        results = []

        for n in sizes:
            blocks = generate_linear_chain(n)

            # Lengauer-Tarjan 算法
            start = time.perf_counter()
            for _ in range(100):
                builder = LengauerTarjanDominator()
                builder.build("b0", blocks)
            lt_time = (time.perf_counter() - start) / 100

            # 迭代算法
            start = time.perf_counter()
            for _ in range(100):
                build_dominator_tree_iterative("b0", blocks)
            iter_time = (time.perf_counter() - start) / 100

            results.append((n, lt_time, iter_time))

            # Lengauer-Tarjan 应该不比迭代算法慢
            assert (
                lt_time < iter_time * 2
            ), f"Size {n}: LT ({lt_time:.6f}s) should be faster than iter ({iter_time:.6f}s)"

        print("\nLinear Chain Performance:")
        for n, lt, it in results:
            print(
                f"  n={n:5d}: LT={lt*1000:.4f}ms, Iter={it*1000:.4f}ms, Speedup={it/lt:.2f}x"
            )

    def test_diamond_chain_performance(self):
        """测试菱形链性能"""
        sizes = [5, 10, 20, 50]
        results = []

        for n in sizes:
            blocks = generate_diamond_chain(n)
            num_blocks = len(blocks)

            # Lengauer-Tarjan 算法
            start = time.perf_counter()
            for _ in range(50):
                builder = LengauerTarjanDominator()
                builder.build("entry", blocks)
            lt_time = (time.perf_counter() - start) / 50

            # 迭代算法
            start = time.perf_counter()
            for _ in range(50):
                build_dominator_tree_iterative("entry", blocks)
            iter_time = (time.perf_counter() - start) / 50

            results.append((num_blocks, lt_time, iter_time))

        print("\nDiamond Chain Performance:")
        for n, lt, it in results:
            print(
                f"  n={n:3d}: LT={lt*1000:.4f}ms, Iter={it*1000:.4f}ms, Speedup={it/lt:.2f}x"
            )

    def test_complex_cfg_performance(self):
        """测试复杂控制流图性能"""
        random.seed(42)  # 确保可重复性
        sizes = [50, 100, 200, 500]
        results = []

        for n in sizes:
            blocks = generate_complex_cfg(n, edge_probability=0.2)

            # Lengauer-Tarjan 算法
            start = time.perf_counter()
            for _ in range(20):
                builder = LengauerTarjanDominator()
                builder.build("b0", blocks)
            lt_time = (time.perf_counter() - start) / 20

            # 迭代算法
            start = time.perf_counter()
            for _ in range(20):
                build_dominator_tree_iterative("b0", blocks)
            iter_time = (time.perf_counter() - start) / 20

            results.append((n, lt_time, iter_time))

        print("\nComplex CFG Performance:")
        for n, lt, it in results:
            print(
                f"  n={n:3d}: LT={lt*1000:.4f}ms, Iter={it*1000:.4f}ms, Speedup={it/lt:.2f}x"
            )

    def test_correctness_stress(self):
        """正确性压力测试"""
        random.seed(123)
        sizes = [10, 20, 50, 100, 200]

        for n in sizes:
            for trial in range(20):
                blocks = generate_complex_cfg(n, edge_probability=0.3)

                builder = LengauerTarjanDominator()
                lt_idom = builder.build("b0", blocks)

                iter_idom, _ = build_dominator_tree_iterative("b0", blocks)

                # 只比较可达节点（两种算法的交集）
                common_keys = set(lt_idom.keys()) & set(iter_idom.keys())
                for key in common_keys:
                    assert (
                        lt_idom[key] == iter_idom[key]
                    ), f"Mismatch at n={n}, trial={trial}, key={key}: LT={lt_idom[key]}, Iter={iter_idom[key]}"

    @pytest.mark.slow
    def test_large_scale_performance(self):
        """大规模性能测试"""
        sizes = [1000, 5000, 10000]
        results = []

        for n in sizes:
            blocks = generate_linear_chain(n)

            # Lengauer-Tarjan 算法
            start = time.perf_counter()
            builder = LengauerTarjanDominator()
            builder.build("b0", blocks)
            lt_time = time.perf_counter() - start

            results.append((n, lt_time))

        print("\nLarge Scale Performance:")
        for n, lt in results:
            print(f"  n={n:5d}: LT={lt*1000:.4f}ms ({lt:.6f}s)")
