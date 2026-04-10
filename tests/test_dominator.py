# -*- coding: utf-8 -*-
"""
ZhC IR - Lengauer-Tarjan 支配树算法测试

作者: 阿福
日期: 2026-04-08
"""

from zhc.ir.dominator import (
    LengauerTarjanDominator,
    build_dominator_tree_iterative,
)


class TestLengauerTarjanDominator:
    """Lengauer-Tarjan 支配树算法测试"""

    def test_single_block(self):
        """测试单个基本块"""
        blocks = {"entry": ([], [])}

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"

    def test_linear_chain(self):
        """测试线性链"""
        blocks = {
            "entry": ([], ["b1"]),
            "b1": (["entry"], ["b2"]),
            "b2": (["b1"], ["b3"]),
            "b3": (["b2"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["b1"] == "entry"
        assert idom["b2"] == "b1"
        assert idom["b3"] == "b2"

    def test_diamond_flowgraph(self):
        """测试菱形控制流图"""
        # entry -> a -> (b1, b2) -> b3 -> exit
        #           |     \   /
        #           +------+ |
        #                  v
        #                 exit
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b1", "b2"]),
            "b1": (["a"], ["b3"]),
            "b2": (["a"], ["b3"]),
            "b3": (["b1", "b2"], ["exit"]),
            "exit": (["b3"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["a"] == "entry"
        # b3 的直接支配者是 a
        assert idom["b3"] == "a"
        assert idom["exit"] == "b3"

    def test_loop_flowgraph(self):
        """测试带循环的控制流图"""
        # entry -> loop_body -> loop_exit
        #             ^    |
        #             +----+
        blocks = {
            "entry": ([], ["loop_body"]),
            "loop_body": (["entry", "loop_body"], ["loop_exit"]),
            "loop_exit": (["loop_body"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        # loop_body 的直接支配者是 entry
        assert idom["loop_body"] == "entry"
        # loop_exit 的直接支配者是 loop_body
        assert idom["loop_exit"] == "loop_body"

    def test_complex_flowgraph(self):
        """测试复杂控制流图（if-else 结构）"""
        blocks = {
            "entry": ([], ["cond"]),
            "cond": (["entry"], ["then", "else"]),
            "then": (["cond"], ["merge"]),
            "else": (["cond"], ["merge"]),
            "merge": (["then", "else"], ["exit"]),
            "exit": (["merge"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["cond"] == "entry"
        assert idom["then"] == "cond"
        assert idom["else"] == "cond"
        assert idom["merge"] == "cond"
        assert idom["exit"] == "merge"

    def test_multiple_entry_unreachable(self):
        """测试存在不可达节点的情况"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b"]),
            "b": (["a"], []),
            "unreachable": (["b"], ["c"]),
            "c": (["unreachable"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        # 可达节点
        assert idom["entry"] == "entry"
        assert idom["a"] == "entry"
        assert idom["b"] == "a"

    def test_get_dominators(self):
        """测试获取支配者集合"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b"]),
            "b": (["a"], ["c"]),
            "c": (["b"], []),
        }

        builder = LengauerTarjanDominator()
        builder.build("entry", blocks)

        # 检查每个节点的支配者
        assert builder.get_dominators("entry") == {"entry"}
        assert builder.get_dominators("a") == {"entry", "a"}
        assert builder.get_dominators("b") == {"entry", "a", "b"}
        assert builder.get_dominators("c") == {"entry", "a", "b", "c"}

    def test_dominates_relation(self):
        """测试支配关系"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b"]),
            "b": (["a"], ["c"]),
            "c": (["b"], []),
        }

        builder = LengauerTarjanDominator()
        builder.build("entry", blocks)

        # entry 支配所有节点
        assert builder.dominates("entry", "entry")
        assert builder.dominates("entry", "a")
        assert builder.dominates("entry", "b")
        assert builder.dominates("entry", "c")

        # a 支配 b 和 c
        assert builder.dominates("a", "b")
        assert builder.dominates("a", "c")
        assert not builder.dominates("a", "entry")

        # b 不支配 a
        assert not builder.dominates("b", "a")

    def test_get_dominator_tree(self):
        """测试获取支配树"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b", "c"]),
            "b": (["a"], ["d"]),
            "c": (["a"], ["d"]),
            "d": (["b", "c"], []),
        }

        builder = LengauerTarjanDominator()
        builder.build("entry", blocks)

        dom_tree = builder.get_dominator_tree()

        # 检查支配树结构
        # entry 的子节点是 a
        assert "entry" in dom_tree
        assert "a" in dom_tree["entry"]
        # a 的子节点是 b, c, d（因为 a 直接支配所有这些节点）
        assert "a" in dom_tree
        assert "b" in dom_tree["a"]
        assert "c" in dom_tree["a"]
        assert "d" in dom_tree["a"]

    def test_get_dominator_depth(self):
        """测试获取支配树深度"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b"]),
            "b": (["a"], ["c"]),
            "c": (["b"], []),
        }

        builder = LengauerTarjanDominator()
        builder.build("entry", blocks)

        depth = builder.get_dominator_depth()

        assert depth["entry"] == 0
        assert depth["a"] == 1
        assert depth["b"] == 2
        assert depth["c"] == 3


class TestBuildDominatorTreeIterative:
    """迭代算法测试"""

    def test_single_block(self):
        """测试单个基本块"""
        blocks = {"entry": ([], [])}

        idom, dom_children = build_dominator_tree_iterative("entry", blocks)

        assert idom["entry"] == "entry"

    def test_linear_chain(self):
        """测试线性链"""
        blocks = {
            "entry": ([], ["b1"]),
            "b1": (["entry"], ["b2"]),
            "b2": (["b1"], []),
        }

        idom, dom_children = build_dominator_tree_iterative("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["b1"] == "entry"
        assert idom["b2"] == "b1"

    def test_diamond_flowgraph(self):
        """测试菱形控制流图"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b1", "b2"]),
            "b1": (["a"], ["b3"]),
            "b2": (["a"], ["b3"]),
            "b3": (["b1", "b2"], []),
        }

        idom, dom_children = build_dominator_tree_iterative("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["a"] == "entry"
        assert idom["b3"] == "a"


class TestAlgorithmComparison:
    """两种算法对比测试"""

    def test_linear_chain_equivalence(self):
        """测试线性链两种算法结果一致"""
        blocks = {
            "entry": ([], ["b1"]),
            "b1": (["entry"], ["b2"]),
            "b2": (["b1"], ["b3"]),
            "b3": (["b2"], []),
        }

        lt_builder = LengauerTarjanDominator()
        lt_idom = lt_builder.build("entry", blocks)

        it_idom, _ = build_dominator_tree_iterative("entry", blocks)

        # 比较直接支配者
        assert lt_idom == it_idom

    def test_diamond_equivalence(self):
        """测试菱形图两种算法结果一致"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], ["b1", "b2"]),
            "b1": (["a"], ["b3"]),
            "b2": (["a"], ["b3"]),
            "b3": (["b1", "b2"], []),
        }

        lt_builder = LengauerTarjanDominator()
        lt_idom = lt_builder.build("entry", blocks)

        it_idom, _ = build_dominator_tree_iterative("entry", blocks)

        # 比较直接支配者
        assert lt_idom == it_idom

    def test_complex_graph_equivalence(self):
        """测试复杂图两种算法结果一致"""
        blocks = {
            "entry": ([], ["cond"]),
            "cond": (["entry"], ["then", "else"]),
            "then": (["cond"], ["merge"]),
            "else": (["cond"], ["merge"]),
            "merge": (["then", "else"], ["exit"]),
            "exit": (["merge"], []),
        }

        lt_builder = LengauerTarjanDominator()
        lt_idom = lt_builder.build("entry", blocks)

        it_idom, _ = build_dominator_tree_iterative("entry", blocks)

        # 比较直接支配者
        assert lt_idom == it_idom

    def test_loop_graph_equivalence(self):
        """测试循环图两种算法结果一致"""
        blocks = {
            "entry": ([], ["loop_body"]),
            "loop_body": (["entry", "loop_body"], ["loop_exit"]),
            "loop_exit": (["loop_body"], []),
        }

        lt_builder = LengauerTarjanDominator()
        lt_idom = lt_builder.build("entry", blocks)

        it_idom, _ = build_dominator_tree_iterative("entry", blocks)

        # 比较直接支配者
        assert lt_idom == it_idom


class TestEdgeCases:
    """边界情况测试"""

    def test_block_with_no_predecessors(self):
        """测试没有前驱的基本块（应该是入口）"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], []),
            "orphan": ([], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["a"] == "entry"

    def test_block_with_no_successors(self):
        """测试没有后继的基本块"""
        blocks = {
            "entry": ([], ["a"]),
            "a": (["entry"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["a"] == "entry"

    def test_self_loop(self):
        """测试自循环"""
        # 注意：loop 的前驱应该包含 entry，因为 entry -> loop
        blocks = {
            "entry": ([], ["loop"]),
            "loop": (["entry", "loop"], ["exit"]),  # 前驱包含 entry 和自己
            "exit": (["loop"], []),
        }

        builder = LengauerTarjanDominator()
        idom = builder.build("entry", blocks)

        assert idom["entry"] == "entry"
        assert idom["loop"] == "entry"
        assert idom["exit"] == "loop"
