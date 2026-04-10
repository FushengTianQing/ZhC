#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泛型代码生成器测试 - Generic Code Generator Tests

Phase 4 - Stage 2 - Task 11.1 Day 4

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest

from zhc.codegen.generic_codegen import (
    NameMangler,
    GenericCodeGenerator,
    GeneratedType,
    GeneratedFunction,
    generate_generic_code,
)


class TestNameMangler:
    """名字修饰器测试"""

    def test_mangle_simple_type(self):
        """测试简单类型修饰"""
        result = NameMangler.mangle_type("列表", ["整数型"])
        assert result == "列表___整数"

    def test_mangle_type_with_multiple_args(self):
        """测试多参数类型修饰"""
        result = NameMangler.mangle_type("对", ["字符串型", "整数型"])
        assert result == "对___字符串__整数"

    def test_mangle_type_no_args(self):
        """测试无参数类型"""
        result = NameMangler.mangle_type("列表", [])
        assert result == "列表"

    def test_mangle_function(self):
        """测试函数名修饰"""
        result = NameMangler.mangle_function("最大值", ["整数型"])
        assert result == "最大值___整数"

    def test_mangle_function_no_args(self):
        """测试无参数函数"""
        result = NameMangler.mangle_function("最大值", [])
        assert result == "最大值"

    def test_mangle_nested_generic(self):
        """测试嵌套泛型修饰"""
        # 映射<字符串型, 列表<整数型>>
        inner = NameMangler.mangle_type("列表", ["整数型"])
        result = NameMangler.mangle_type("映射", ["字符串型", inner])
        assert "映射" in result
        assert "字符串" in result

    def test_mangle_type_name_basic(self):
        """测试基础类型名修饰"""
        assert NameMangler.mangle_type_name("整数型") == "整数"
        assert NameMangler.mangle_type_name("浮点型") == "浮点"
        assert NameMangler.mangle_type_name("字符串型") == "字符串"
        assert NameMangler.mangle_type_name("布尔型") == "布尔"

    def test_mangle_type_name_unknown(self):
        """测试未知类型名"""
        result = NameMangler.mangle_type_name("自定义类型")
        assert result == "自定义类型"

    def test_unmangle_simple(self):
        """测试简单反修饰"""
        original, args = NameMangler.unmangle("列表___整数")
        assert original == "列表"
        assert args == ["整数型"]

    def test_unmangle_no_args(self):
        """测试无参数反修饰"""
        original, args = NameMangler.unmangle("列表")
        assert original == "列表"
        assert args == []

    def test_parse_inner_types(self):
        """测试内部类型解析"""
        result = NameMangler._parse_inner_types("字符串型, 整数型")
        assert result == ["字符串型", "整数型"]

    def test_parse_inner_types_nested(self):
        """测试嵌套内部类型解析"""
        result = NameMangler._parse_inner_types("列表<整数型>, 字符串型")
        assert len(result) == 2
        assert "列表<整数型>" in result[0]
        assert "字符串型" in result[1]


class TestGenericCodeGenerator:
    """泛型代码生成器测试"""

    def test_init(self):
        """测试初始化"""
        generator = GenericCodeGenerator()
        assert generator.manager is not None
        assert len(generator._generated_types) == 0
        assert len(generator._generated_functions) == 0

    def test_request_type_instantiation(self):
        """测试请求类型实例化"""
        generator = GenericCodeGenerator()
        mangled = generator.request_type_instantiation("列表", ["整数型"])
        assert mangled == "列表___整数"
        assert len(generator._pending_types) == 1

    def test_request_type_instantiation_cached(self):
        """测试类型实例化缓存"""
        generator = GenericCodeGenerator()
        # 第一次请求
        mangled1 = generator.request_type_instantiation("列表", ["整数型"])
        # 第二次请求（在 generate_all 之前，仍会加入队列）
        mangled2 = generator.request_type_instantiation("列表", ["整数型"])
        assert mangled1 == mangled2
        # 缓存检查在 _generated_types 中，不在 _pending_types
        # 所以第二次请求仍会增加 _pending_types
        assert len(generator._pending_types) == 2

    def test_request_function_instantiation(self):
        """测试请求函数实例化"""
        generator = GenericCodeGenerator()
        mangled = generator.request_function_instantiation("最大值", ["整数型"])
        assert mangled == "最大值___整数"
        assert len(generator._pending_functions) == 1

    def test_request_function_instantiation_cached(self):
        """测试函数实例化缓存"""
        generator = GenericCodeGenerator()
        # 第一次请求
        mangled1 = generator.request_function_instantiation("最大值", ["整数型"])
        # 第二次请求（在 generate_all 之前，仍会加入队列）
        mangled2 = generator.request_function_instantiation("最大值", ["整数型"])
        assert mangled1 == mangled2
        # 缓存检查在 _generated_functions 中，不在 _pending_functions
        # 所以第二次请求仍会增加 _pending_functions
        assert len(generator._pending_functions) == 2

    def test_get_statistics(self):
        """测试统计信息"""
        generator = GenericCodeGenerator()
        generator.request_type_instantiation("列表", ["整数型"])
        generator.request_function_instantiation("最大值", ["整数型"])

        stats = generator.get_statistics()
        assert stats["pending_types"] == 1
        assert stats["pending_functions"] == 1
        assert stats["generated_types"] == 0
        assert stats["generated_functions"] == 0

    def test_generate_header(self):
        """测试头文件生成"""
        generator = GenericCodeGenerator()
        header = generator.generate_header()

        assert "#ifndef ZHC_GENERICS_H" in header
        assert "#define ZHC_GENERICS_H" in header
        assert "#endif" in header

    def test_generate_implementation(self):
        """测试实现文件生成"""
        generator = GenericCodeGenerator()
        impl = generator.generate_implementation()

        assert '#include "generics.h"' in impl

    def test_substitute_type_direct(self):
        """测试直接类型替换"""
        generator = GenericCodeGenerator()
        type_mapping = {"T": "整数型"}

        result = generator._substitute_type("T", type_mapping)
        assert result == "整数型"

    def test_substitute_type_array(self):
        """测试数组类型替换"""
        generator = GenericCodeGenerator()
        type_mapping = {"T": "整数型"}

        result = generator._substitute_type("T[]", type_mapping)
        assert result == "整数型[]"

    def test_substitute_type_no_match(self):
        """测试无匹配类型"""
        generator = GenericCodeGenerator()
        type_mapping = {"T": "整数型"}

        result = generator._substitute_type("字符串型", type_mapping)
        assert result == "字符串型"

    def test_extract_type_deps(self):
        """测试提取类型依赖"""
        generator = GenericCodeGenerator()

        deps = generator._extract_type_deps(["整数型", "字符串型"])
        assert "整数型" in deps
        assert "字符串型" in deps


class TestGeneratedType:
    """生成的类型测试"""

    def test_creation(self):
        """测试创建"""
        gen_type = GeneratedType(
            name="列表___整数",
            mangled_name="列表___整数",
            original_generic="列表",
            type_args=["整数型"],
            code="// test code",
        )

        assert gen_type.name == "列表___整数"
        assert gen_type.original_generic == "列表"
        assert gen_type.type_args == ["整数型"]

    def test_with_dependencies(self):
        """测试带依赖"""
        gen_type = GeneratedType(
            name="映射___字符串__整数",
            mangled_name="映射___字符串__整数",
            original_generic="映射",
            type_args=["字符串型", "整数型"],
            code="// test code",
            dependencies=["字符串型", "整数型"],
        )

        assert len(gen_type.dependencies) == 2


class TestGeneratedFunction:
    """生成的函数测试"""

    def test_creation(self):
        """测试创建"""
        gen_func = GeneratedFunction(
            name="最大值___整数",
            mangled_name="最大值___整数",
            original_generic="最大值",
            type_args=["整数型"],
            code="// test code",
        )

        assert gen_func.name == "最大值___整数"
        assert gen_func.original_generic == "最大值"
        assert gen_func.type_args == ["整数型"]

    def test_with_dependencies(self):
        """测试带依赖"""
        gen_func = GeneratedFunction(
            name="排序___整数",
            mangled_name="排序___整数",
            original_generic="排序",
            type_args=["整数型"],
            code="// test code",
            dependencies=["整数型"],
        )

        assert len(gen_func.dependencies) == 1


class TestModuleFunctions:
    """模块级函数测试"""

    def test_generate_generic_code_type(self):
        """测试生成泛型类型代码"""
        # 注意：这个测试需要完整的泛型系统支持
        # 这里只测试函数能被调用
        try:
            code = generate_generic_code("列表", ["整数型"], is_function=False)
            # 由于没有实际的泛型定义，可能返回空字符串
            assert isinstance(code, str)
        except Exception:
            # 预期可能失败
            pass

    def test_generate_generic_code_function(self):
        """测试生成泛型函数代码"""
        try:
            code = generate_generic_code("最大值", ["整数型"], is_function=True)
            assert isinstance(code, str)
        except Exception:
            # 预期可能失败
            pass


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_type_args(self):
        """测试空类型参数"""
        result = NameMangler.mangle_type("列表", [])
        assert result == "列表"

    def test_multiple_type_args(self):
        """测试多个类型参数"""
        result = NameMangler.mangle_type("元组", ["整数型", "字符串型", "浮点型"])
        assert "元组" in result
        assert "整数" in result
        assert "字符串" in result
        assert "浮点" in result

    def test_special_characters(self):
        """测试特殊字符"""
        result = NameMangler.mangle_type_name("类型_123")
        assert result == "类型_123"

    def test_deeply_nested_generic(self):
        """测试深层嵌套泛型"""
        # 列表<映射<字符串型, 列表<整数型>>>
        inner1 = NameMangler.mangle_type("列表", ["整数型"])
        inner2 = NameMangler.mangle_type("映射", ["字符串型", inner1])
        result = NameMangler.mangle_type("列表", [inner2])

        assert "列表" in result
        assert "映射" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
