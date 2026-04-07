# -*- coding: utf-8 -*-
"""
ZhC 编译器 - 别名分析测试

测试过程间别名分析功能。

作者：阿福
日期：2026-04-08
"""

import pytest
from src.analyzer.interprocedural_alias import (
    InterproceduralAliasAnalyzer,
    AllocationSite,
    PointsToSet,
    AliasKind,
)


class TestAllocationSite:
    """分配点测试"""

    def test_allocation_site_creation(self):
        """测试分配点创建"""
        analyzer = InterproceduralAliasAnalyzer()
        
        site = analyzer.new_allocation_site(
            function="test_func",
            line=10,
            var_name="x",
            is_heap=False
        )
        
        assert site.id == 1
        assert site.function == "test_func"
        assert site.line == 10
        assert site.var_name == "x"
        assert not site.is_heap
        assert not site.is_param
        assert not site.is_global

    def test_allocation_site_equality(self):
        """测试分配点相等性"""
        site1 = AllocationSite(id=1, function="f", line=1)
        site2 = AllocationSite(id=1, function="f", line=1)
        site3 = AllocationSite(id=2, function="f", line=1)
        
        assert site1 == site2
        assert site1 != site3

    def test_heap_allocation_site(self):
        """测试堆分配点"""
        analyzer = InterproceduralAliasAnalyzer()
        
        site = analyzer.new_allocation_site(
            function="main",
            line=5,
            var_name="ptr",
            is_heap=True
        )
        
        assert site.is_heap
        assert site.var_name == "ptr"


class TestPointsToSet:
    """指向集合测试"""

    def test_points_to_set_add(self):
        """测试添加指向"""
        pts = PointsToSet()
        site = AllocationSite(id=1, function="f", line=1)
        
        pts.add(site)
        
        assert len(pts) == 1
        assert pts.may_point_to(site)

    def test_points_to_set_update(self):
        """测试更新指向集合"""
        pts1 = PointsToSet()
        pts2 = PointsToSet()
        
        site1 = AllocationSite(id=1, function="f", line=1)
        site2 = AllocationSite(id=2, function="f", line=2)
        
        pts1.add(site1)
        pts2.add(site2)
        
        pts1.update(pts2)
        
        assert len(pts1) == 2
        assert pts1.may_point_to(site1)
        assert pts1.may_point_to(site2)

    def test_points_to_set_copy(self):
        """测试指向集合复制"""
        pts = PointsToSet()
        site = AllocationSite(id=1, function="f", line=1)
        pts.add(site)
        
        pts_copy = pts.copy()
        
        assert pts_copy.may_point_to(site)
        assert pts_copy is not pts


class TestFunctionRegistration:
    """函数注册测试"""

    def test_register_function(self):
        """测试函数注册"""
        analyzer = InterproceduralAliasAnalyzer()
        
        func_info = analyzer.register_function("foo", ["a", "b"])
        
        assert func_info.name == "foo"
        assert func_info.params == ["a", "b"]
        assert "a" in func_info.param_sites
        assert "b" in func_info.param_sites

    def test_register_function_idempotent(self):
        """测试函数注册幂等性"""
        analyzer = InterproceduralAliasAnalyzer()
        
        func_info1 = analyzer.register_function("foo", ["a"])
        func_info2 = analyzer.register_function("foo", ["b"])
        
        assert func_info1 is func_info2
        assert func_info1.params == ["a"]

    def test_register_global_var(self):
        """测试全局变量注册"""
        analyzer = InterproceduralAliasAnalyzer()
        
        site = analyzer.register_global_var("global_x", line=1)
        
        assert "global_x" in analyzer.global_vars
        assert site.is_global
        assert site.var_name == "global_x"


class TestPointerOperations:
    """指针操作测试"""

    def test_address_of(self):
        """测试取地址操作"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        analyzer.process_address_of("main", "ptr", "x", line=5)
        
        func_info = analyzer.get_function("main")
        assert "ptr" in func_info.points_to
        assert len(func_info.points_to["ptr"]) == 1

    def test_pointer_assign(self):
        """测试指针赋值"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        analyzer.process_address_of("main", "ptr1", "x", line=5)
        analyzer.process_pointer_assign("main", "ptr2", "ptr1", line=6)
        
        func_info = analyzer.get_function("main")
        assert len(func_info.points_to["ptr2"]) == 1
        # ptr1 和 ptr2 应该指向同一个对象
        assert func_info.points_to["ptr1"].targets == func_info.points_to["ptr2"].targets

    def test_heap_alloc(self):
        """测试堆分配"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        analyzer.process_heap_alloc("main", "ptr", line=10)
        
        func_info = analyzer.get_function("main")
        assert "ptr" in func_info.points_to
        assert len(func_info.points_to["ptr"]) == 1
        
        pts = func_info.points_to["ptr"]
        assert any(s.is_heap for s in pts.targets)


class TestCallSiteAliasing:
    """调用点别名测试"""

    def test_call_propagates_alias(self):
        """测试调用传播别名"""
        analyzer = InterproceduralAliasAnalyzer()
        
        # 注册函数
        analyzer.register_function("foo", ["p"])
        analyzer.register_function("main")
        
        # main: q = &x
        analyzer.process_address_of("main", "q", "x", line=5)
        
        # main 调用 foo(q)
        analyzer.add_call(
            caller="main",
            callee="foo",
            line=10,
            arg_mapping={"p": "q"}
        )
        
        # 分析
        analyzer.solve()
        
        # foo 中的 p 应该指向 x
        foo_info = analyzer.get_function("foo")
        assert "p" in foo_info.points_to
        assert any(s.var_name == "x" for s in foo_info.points_to["p"].targets)

    def test_return_value_alias(self):
        """测试返回值别名传播"""
        analyzer = InterproceduralAliasAnalyzer()
        
        # 注册函数
        analyzer.register_function("get_ptr")
        analyzer.register_function("main")
        
        # get_ptr 返回指向全局的指针
        analyzer.process_address_of("get_ptr", "local", "global_var", line=5)
        analyzer.propagate_at_return("get_ptr", "local", 6)
        
        # main 调用 get_ptr，结果存到 result
        analyzer.add_call(
            caller="main",
            callee="get_ptr",
            line=10,
            arg_mapping={},
            return_var="result"
        )
        
        # 分析
        analyzer.solve()
        
        # result 应该指向 global_var
        main_info = analyzer.get_function("main")
        assert "result" in main_info.points_to
        assert any(s.var_name == "global_var" for s in main_info.points_to["result"].targets)


class TestAliasQuery:
    """别名查询测试"""

    def test_query_no_alias(self):
        """测试无别名"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        analyzer.process_address_of("main", "ptr1", "x", line=5)
        analyzer.process_address_of("main", "ptr2", "y", line=6)
        
        result = analyzer.query_alias("main", "ptr1", "ptr2")
        
        assert result == AliasKind.NO_ALIAS

    def test_query_must_alias(self):
        """测试必须别名"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        analyzer.process_address_of("main", "ptr1", "x", line=5)
        analyzer.process_pointer_assign("main", "ptr2", "ptr1", line=6)
        
        result = analyzer.query_alias("main", "ptr1", "ptr2")
        
        assert result == AliasKind.MUST_ALIAS

    def test_query_may_alias(self):
        """测试可能别名（两个指针可能指向同一对象）"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        func_info = analyzer.get_function("main")
        
        # 创建分配点
        site_x = analyzer.new_allocation_site("main", 5, "x")
        site_y = analyzer.new_allocation_site("main", 6, "y")
        
        # ptr1 指向 x 和 y（模拟条件分支后的状态）
        func_info.points_to["ptr1"] = PointsToSet({site_x, site_y})
        # ptr2 指向 x
        func_info.points_to["ptr2"] = PointsToSet({site_x})
        
        result = analyzer.query_alias("main", "ptr1", "ptr2")
        
        # ptr1 和 ptr2 有交集，但 ptr1 有多个可能值
        assert result == AliasKind.MAY_ALIAS

    def test_get_all_aliases(self):
        """测试获取所有别名"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        analyzer.process_address_of("main", "ptr1", "x", line=5)
        analyzer.process_pointer_assign("main", "ptr2", "ptr1", line=6)
        analyzer.process_pointer_assign("main", "ptr3", "ptr1", line=7)
        
        aliases = analyzer.get_all_aliases("main", "ptr1")
        
        assert "ptr2" in aliases
        assert "ptr3" in aliases
        assert "ptr1" not in aliases


class TestCallGraph:
    """调用图测试"""

    def test_add_call(self):
        """测试添加调用"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("foo")
        analyzer.register_function("main")
        
        call = analyzer.add_call(
            caller="main",
            callee="foo",
            line=10,
            arg_mapping={"a": "x"},
            return_var="result"
        )
        
        assert call.caller == "main"
        assert call.callee == "foo"
        assert call.arg_mapping == {"a": "x"}
        assert call.return_var == "result"
        
        # 检查调用关系
        main_info = analyzer.get_function("main")
        assert ("foo", {"a": "x"}) in main_info.calls
        
        foo_info = analyzer.get_function("foo")
        assert "main" in foo_info.called_by


class TestReportGeneration:
    """报告生成测试"""

    def test_generate_report(self):
        """测试报告生成"""
        analyzer = InterproceduralAliasAnalyzer()
        
        analyzer.register_function("main", ["argc", "argv"])
        analyzer.process_address_of("main", "ptr", "x", line=5)
        
        report = analyzer.generate_report()
        
        assert "过程间别名分析报告" in report
        assert "main" in report
        assert "argc" in report
        assert "argv" in report


class TestEdgeCases:
    """边界情况测试"""

    def test_undefined_function(self):
        """测试未定义函数"""
        analyzer = InterproceduralAliasAnalyzer()
        
        result = analyzer.query_alias("undefined_func", "ptr1", "ptr2")
        
        assert result == AliasKind.UNKNOWN

    def test_undefined_pointer(self):
        """测试未定义指针"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("main")
        
        result = analyzer.query_alias("main", "undefined_ptr", "ptr2")
        
        assert result == AliasKind.UNKNOWN

    def test_empty_function(self):
        """测试空函数"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("empty_func")
        
        func_info = analyzer.get_function("empty_func")
        
        assert func_info.name == "empty_func"
        assert len(func_info.points_to) == 0

    def test_self_call(self):
        """测试递归调用"""
        analyzer = InterproceduralAliasAnalyzer()
        analyzer.register_function("recursive", ["n"])
        
        analyzer.add_call(
            caller="recursive",
            callee="recursive",
            line=10,
            arg_mapping={"n": "n"}
        )
        
        # 分析应该能处理递归
        result = analyzer.solve()
        
        assert result is True  # 应该收敛
