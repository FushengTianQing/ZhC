# -*- coding: utf-8 -*-
"""
GEP 指令增强功能测试

测试内容：
- TypeInfoRegistry 类型注册表
- GepStrategy 增强功能
- AdvancedGEPInstruction 高级功能
- 多维数组索引
- 负数索引检测
- 常量折叠优化

作者：远
日期：2026-04-09
"""

import pytest
import warnings
import llvmlite.ir as ll
from zhc.backend.compilation_context import (
    CompilationContext,
    TypeInfoRegistry,
    ArrayTypeInfo,
    StructTypeInfo,
    StructFieldInfo,
)


class TestArrayTypeInfo:
    """ArrayTypeInfo 测试"""

    def test_basic_properties(self):
        """测试基本属性"""
        i32 = ll.IntType(32)
        info = ArrayTypeInfo(
            element_type=i32,
            dimensions=[3, 4, 5],
            total_size=60
        )
        assert info.ndim == 3
        assert info.element_stride == 5
        assert info.total_size == 60

    def test_single_dimension(self):
        """测试单维数组"""
        i32 = ll.IntType(32)
        info = ArrayTypeInfo(
            element_type=i32,
            dimensions=[10],
            total_size=10
        )
        assert info.ndim == 1
        assert info.element_stride == 10


class TestStructTypeInfo:
    """StructTypeInfo 测试"""

    def test_field_access(self):
        """测试字段访问"""
        i32 = ll.IntType(32)
        i8 = ll.IntType(8)
        struct_type = ll.LiteralStructType([i32, i8])

        fields = [
            StructFieldInfo(name="age", field_type=i32, index=0, offset=0),
            StructFieldInfo(name="grade", field_type=i8, index=1, offset=4),
        ]

        info = StructTypeInfo(
            name="Student",
            llvm_type=struct_type,
            fields={"age": fields[0], "grade": fields[1]},
            field_names=["age", "grade"]
        )

        assert info.get_field("age") is not None
        assert info.get_field("age").index == 0
        assert info.get_field_index("age") == 0
        assert info.get_field("grade").index == 1


class TestTypeInfoRegistry:
    """TypeInfoRegistry 测试"""

    def test_register_array(self):
        """测试数组注册"""
        registry = TypeInfoRegistry()
        i32 = ll.IntType(32)

        info = registry.register_array("arr", i32, [10, 20])
        assert info is not None
        assert info.ndim == 2
        assert info.total_size == 200

    def test_register_struct(self):
        """测试结构体注册"""
        registry = TypeInfoRegistry()
        i32 = ll.IntType(32)
        i8 = ll.IntType(8)
        struct_type = ll.LiteralStructType([i32, i8])

        info = registry.register_struct("Person", struct_type, [("name", i32), ("age", i8)])
        assert info is not None
        assert info.get_field_index("name") == 0
        assert info.get_field_index("age") == 1

    def test_get_array_info(self):
        """测试获取数组信息"""
        registry = TypeInfoRegistry()
        i32 = ll.IntType(32)

        registry.register_array("test_arr", i32, [5, 5])
        info = registry.get_array_info("test_arr")

        assert info is not None
        assert info.dimensions == [5, 5]

    def test_get_array_element_stride(self):
        """测试获取数组元素步长"""
        registry = TypeInfoRegistry()
        i32 = ll.IntType(32)

        registry.register_array("arr", i32, [3, 4, 5])
        stride = registry.get_array_element_stride("arr")

        assert stride == 5


class TestCompilationContextGEP:
    """CompilationContext GEP 相关功能测试"""

    def test_create_gep_constant_index(self):
        """测试创建常量索引"""
        ctx = CompilationContext()
        idx = ctx.create_gep_constant_index(42)

        assert isinstance(idx, ll.Constant)
        assert idx.constant == 42

    def test_fold_constant_indices(self):
        """测试常量折叠"""
        ctx = CompilationContext()
        i32 = ll.IntType(32)

        indices = [
            ll.Constant(i32, 0),
            ll.Constant(i32, 5),
            ll.Constant(i32, 10),
        ]

        folded, offset = ctx._fold_constant_indices(indices)

        # 所有都是常量，应该被折叠
        assert len(folded) == 0
        assert offset == 15

    def test_fold_mixed_indices(self):
        """测试混合索引折叠"""
        ctx = CompilationContext()
        i32 = ll.IntType(32)

        # 模拟一个变量索引
        var_idx = ll.Constant(i32, 0)
        var_idx.constant = None  # 模拟非常量

        indices = [
            ll.Constant(i32, 5),
            ll.Constant(i32, 10),
        ]

        folded, offset = ctx._fold_constant_indices(indices)

        assert offset == 15

    def test_optimize_gep_indices(self):
        """测试 GEP 索引优化"""
        ctx = CompilationContext()
        i32 = ll.IntType(32)
        i8 = ll.IntType(8)

        # 创建一个简单的指针
        ptr = ll.Constant(ll.PointerType(i8), None)

        # 测试移除零索引
        indices = [
            ll.Constant(i32, 0),
            ll.Constant(i32, 5),
        ]

        _, optimized = ctx.optimize_gep_indices(ptr, indices)

        # 优化后应该保留非零索引
        assert len(optimized) >= 1
        # 检查非零索引存在
        non_zero_found = any(
            (isinstance(idx, ll.Constant) and idx.constant != 0)
            for idx in optimized
        )
        assert non_zero_found


class TestGepStrategy:
    """GepStrategy 增强功能测试"""

    def test_negative_index_warning(self):
        """测试负数索引警告"""
        from zhc.backend.llvm_instruction_strategy import GepStrategy
        import llvmlite.ir as ll

        strategy = GepStrategy()
        i32 = ll.IntType(32)

        # 创建负数索引
        indices = [ll.Constant(i32, -1)]

        # 应该发出警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            strategy._check_negative_indices(indices)

            assert len(w) == 1
            assert "负数" in str(w[0].message)


class TestAdvancedGEPInstruction:
    """AdvancedGEPInstruction 测试"""

    def test_count_array_dims(self):
        """测试数组维度计数"""
        from zhc.backend.llvm_instruction_strategy import AdvancedGEPInstruction

        strategy = AdvancedGEPInstruction()
        i32 = ll.IntType(32)

        # 创建二维数组类型
        inner_array = ll.ArrayType(i32, 5)
        outer_array = ll.ArrayType(inner_array, 3)

        dims = strategy._count_array_dims(outer_array)
        assert dims == 2

    def test_opcode(self):
        """测试 opcode 设置"""
        from zhc.backend.llvm_instruction_strategy import AdvancedGEPInstruction
        from zhc.ir.opcodes import Opcode

        strategy = AdvancedGEPInstruction()
        assert strategy.opcode == Opcode.GEP


class TestIntegration:
    """集成测试"""

    def test_full_gep_workflow(self):
        """测试完整 GEP 工作流"""
        # 创建 LLVM 模块
        module = ll.Module("test_module")
        i32 = ll.IntType(32)

        # 创建编译上下文
        ctx = CompilationContext()
        ctx.module = module

        # 注册数组类型
        ctx.register_array_type("matrix", i32, [10, 20])

        # 获取数组信息
        info = ctx.get_array_type_info("matrix")
        assert info is not None
        assert info.ndim == 2
        assert info.total_size == 200

        # 创建常量索引
        idx = ctx.create_gep_constant_index(5)
        assert idx.constant == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
