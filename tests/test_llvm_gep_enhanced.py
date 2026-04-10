# -*- coding: utf-8 -*-
"""
GEP 指令增强功能测试 - 增强版

测试内容：
- GEP-001: 多维数组索引首元素索引 0 自动插入
- GEP-002: 嵌套结构体字段访问
- GEP-003: 可选的运行时边界检查
- 类型信息注册表
- 常量折叠优化

作者：远
日期：2026-04-09
"""

import pytest
import llvmlite.ir as ll
from zhc.backend.compilation_context import (
    CompilationContext,
    TypeInfoRegistry,
)
from zhc.backend.llvm_instruction_strategy import (
    GepStrategy,
    AdvancedGEPInstruction,
    InstructionStrategyFactory,
)
from zhc.ir.opcodes import Opcode


class TestGEP001MultiDimensionalArray:
    """GEP-001: 多维数组索引测试"""

    def test_ensure_first_index_zero(self):
        """测试自动插入首元素索引 0"""
        strategy = GepStrategy()
        i32 = ll.IntType(32)

        # 创建模拟的 builder 和 context
        module = ll.Module("test")
        func_type = ll.FunctionType(i32, [])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)

        ctx = CompilationContext()
        ctx.module = module
        ctx.builder = builder

        # 测试索引列表不以零开头
        indices = [ll.Constant(i32, 5), ll.Constant(i32, 10)]
        result_indices = strategy._ensure_first_index(indices, builder, ctx)

        # 应该在开头插入零索引
        assert len(result_indices) == 3
        assert isinstance(result_indices[0], ll.Constant)
        assert result_indices[0].constant == 0

    def test_first_index_already_zero(self):
        """测试首元素索引已经是零的情况"""
        strategy = GepStrategy()
        i32 = ll.IntType(32)

        module = ll.Module("test")
        func_type = ll.FunctionType(i32, [])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)

        ctx = CompilationContext()
        ctx.module = module
        ctx.builder = builder

        # 测试索引列表已经以零开头
        indices = [ll.Constant(i32, 0), ll.Constant(i32, 5)]
        result_indices = strategy._ensure_first_index(indices, builder, ctx)

        # 应该保持不变
        assert len(result_indices) == 2
        assert result_indices[0].constant == 0
        assert result_indices[1].constant == 5

    def test_empty_indices(self):
        """测试空索引列表"""
        strategy = GepStrategy()
        i32 = ll.IntType(32)

        module = ll.Module("test")
        func_type = ll.FunctionType(i32, [])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)

        ctx = CompilationContext()
        ctx.module = module
        ctx.builder = builder

        # 测试空索引列表
        indices = []
        result_indices = strategy._ensure_first_index(indices, builder, ctx)

        # 空列表应该保持不变
        assert len(result_indices) == 0


class TestGEP002NestedStructAccess:
    """GEP-002: 嵌套结构体字段访问测试"""

    def test_resolve_nested_field_index(self):
        """测试解析嵌套字段索引"""
        strategy = AdvancedGEPInstruction()
        i32 = ll.IntType(32)
        i8 = ll.IntType(8)

        # 创建嵌套结构体类型
        inner_struct = ll.LiteralStructType([i32, i8])  # { i32, i8 }
        outer_struct = ll.LiteralStructType([inner_struct, i32])  # { { i32, i8 }, i32 }

        module = ll.Module("test")
        ctx = CompilationContext()
        ctx.module = module

        # 注册结构体类型信息
        ctx.register_struct_type(
            "Outer", outer_struct, [("inner", inner_struct), ("z", i32)]
        )

        ctx.register_struct_type("Inner", inner_struct, [("x", i32), ("y", i8)])

        # 创建基指针
        ptr_type = ll.PointerType(outer_struct)
        ptr = ll.Constant(ptr_type, None)

        # 测试嵌套字段访问
        indices = strategy._resolve_nested_field_index("inner.x", ptr, ctx)

        # 应该返回两个索引
        assert len(indices) == 2
        assert all(isinstance(idx, ll.Constant) for idx in indices)

    def test_resolve_single_field_index(self):
        """测试解析单个字段索引"""
        strategy = AdvancedGEPInstruction()

        module = ll.Module("test")
        ctx = CompilationContext()
        ctx.module = module

        # 测试单个字段
        idx = strategy._resolve_single_index('"field_name"', ctx)

        assert isinstance(idx, ll.Constant)
        # 由于没有实际的结构体信息，应该返回 0
        assert idx.constant == 0

    def test_ensure_first_index_gep(self):
        """测试高级 GEP 的首元素索引确保"""
        strategy = AdvancedGEPInstruction()
        i32 = ll.IntType(32)

        module = ll.Module("test")
        ctx = CompilationContext()
        ctx.module = module

        # 测试不以零开头的索引
        indices = [ll.Constant(i32, 5), ll.Constant(i32, 10)]
        result_indices = strategy._ensure_first_index_gep(indices, ctx)

        # 应该在开头插入零索引
        assert len(result_indices) == 3
        assert result_indices[0].constant == 0


class TestGEP003BoundsCheck:
    """GEP-003: 边界检查测试"""

    def test_generate_bounds_check(self):
        """测试生成边界检查代码"""
        i32 = ll.IntType(32)

        module = ll.Module("test_bounds_check")
        func_type = ll.FunctionType(i32, [i32])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)

        ctx = CompilationContext()
        ctx.module = module

        # 创建索引参数
        index = func.args[0]

        # 生成边界检查
        array_size = 10
        result = ctx.generate_bounds_check(builder, index, array_size, ctx)

        # 应该返回索引值
        assert result is not None
        assert result == index

        # 检查生成的 IR 包含边界检查块
        ir_str = str(module)
        assert "bounds_check" in ir_str
        assert "bounds_ok" in ir_str
        assert "bounds_panic" in ir_str

    def test_panic_function_declaration(self):
        """测试 panic 函数声明"""
        module = ll.Module("test_panic")
        ctx = CompilationContext()
        ctx.module = module

        # 获取或声明 panic 函数
        panic_func = ctx._get_or_declare_panic_function(module)

        assert panic_func is not None
        assert panic_func.name == "__zhc_panic"

        # 检查函数类型
        assert isinstance(panic_func, ll.Function)


class TestTypeInfoRegistryEnhanced:
    """TypeInfoRegistry 增强测试"""

    def test_register_nested_struct(self):
        """测试注册嵌套结构体"""
        registry = TypeInfoRegistry()
        i32 = ll.IntType(32)
        i8 = ll.IntType(8)

        # 创建嵌套结构体
        inner_struct = ll.LiteralStructType([i32, i8])
        outer_struct = ll.LiteralStructType([inner_struct, i32])

        # 注册内部结构体
        inner_info = registry.register_struct(
            "Inner", inner_struct, [("x", i32), ("y", i8)]
        )

        # 注册外部结构体
        outer_info = registry.register_struct(
            "Outer", outer_struct, [("inner", inner_struct), ("z", i32)]
        )

        assert inner_info is not None
        assert outer_info is not None
        assert outer_info.get_field_index("inner") == 0
        assert outer_info.get_field_index("z") == 1

    def test_infer_gep_result_type(self):
        """测试推断 GEP 结果类型"""
        registry = TypeInfoRegistry()
        i32 = ll.IntType(32)

        # 创建数组类型
        array_type = ll.ArrayType(i32, 10)
        ptr_type = ll.PointerType(array_type)

        # 推断结果类型
        result_type = registry.infer_gep_result_type(
            ptr_type, [ll.IntType(32), ll.IntType(32)]
        )

        # 应该推断出元素类型
        assert result_type is not None


class TestGepStrategyIntegration:
    """GepStrategy 集成测试"""

    def test_full_gep_workflow_with_first_index(self):
        """测试完整的 GEP 工作流（包含首元素索引）"""
        i32 = ll.IntType(32)

        # 创建模块和函数
        module = ll.Module("test_integration")

        # 创建数组类型
        array_type = ll.ArrayType(i32, 10)
        ptr_type = ll.PointerType(array_type)
        func_type = ll.FunctionType(i32, [ptr_type])
        func = ll.Function(module, func_type, "array_access")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)

        # 创建编译上下文
        ctx = CompilationContext()
        ctx.module = module
        ctx.builder = builder
        ctx.current_function = func

        # 将函数参数存储到上下文中
        ctx.values["arg_ptr"] = func.args[0]

        # 注册数组类型
        ctx.register_array_type("arr", i32, [10])

        # 创建 GEP 策略
        strategy = GepStrategy()

        # 创建模拟的指令，使用值名称
        class MockInstruction:
            def __init__(self):
                self.opcode = Opcode.GEP
                self.operands = ["arg_ptr", "5"]  # 使用值名称而不是直接传递指针
                self.result = ["ptr"]

        instr = MockInstruction()

        # 编译 GEP 指令
        result = strategy.compile(builder, instr, ctx)

        assert result is not None

        # 检查生成的 IR
        ir_str = str(module)
        assert "getelementptr" in ir_str


class TestAdvancedGEPInstructionIntegration:
    """AdvancedGEPInstruction 集成测试"""

    def test_nested_struct_access_workflow(self):
        """测试嵌套结构体访问工作流"""
        i32 = ll.IntType(32)
        i8 = ll.IntType(8)

        # 创建嵌套结构体
        inner_struct = ll.LiteralStructType([i32, i8])
        outer_struct = ll.LiteralStructType([inner_struct, i32])

        # 创建模块和函数
        module = ll.Module("test_nested_struct")

        # 创建正确的指针类型
        outer_ptr_type = ll.PointerType(outer_struct)
        func_type = ll.FunctionType(i32, [outer_ptr_type])
        func = ll.Function(module, func_type, "struct_access")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)

        # 创建编译上下文
        ctx = CompilationContext()
        ctx.module = module
        ctx.builder = builder
        ctx.current_function = func

        # 将函数参数存储到上下文中
        ctx.values["struct_ptr"] = func.args[0]

        # 注册结构体类型
        ctx.register_struct_type("Inner", inner_struct, [("x", i32), ("y", i8)])
        ctx.register_struct_type(
            "Outer", outer_struct, [("inner", inner_struct), ("z", i32)]
        )

        # 创建高级 GEP 策略
        strategy = AdvancedGEPInstruction()

        # 创建模拟的指令，使用值名称
        class MockInstruction:
            def __init__(self):
                self.opcode = Opcode.GEP
                self.operands = ["struct_ptr", '"inner"', '"x"']  # 使用值名称
                self.result = ["field_ptr"]

        instr = MockInstruction()

        # 编译 GEP 指令
        result = strategy.compile(builder, instr, ctx)

        assert result is not None

        # 检查生成的 IR
        ir_str = str(module)
        assert "getelementptr" in ir_str


class TestInstructionStrategyFactoryWithGEP:
    """InstructionStrategyFactory GEP 策略测试"""

    def test_gep_strategy_registered(self):
        """测试 GEP 策略已注册"""
        # 重置工厂
        InstructionStrategyFactory.reset()

        # 获取 GEP 策略
        strategy = InstructionStrategyFactory.get_strategy(Opcode.GEP)

        assert strategy is not None
        assert isinstance(strategy, GepStrategy)

    def test_gep_strategy_singleton(self):
        """测试 GEP 策略单例"""
        InstructionStrategyFactory.reset()

        strategy1 = InstructionStrategyFactory.get_strategy(Opcode.GEP)
        strategy2 = InstructionStrategyFactory.get_strategy(Opcode.GEP)

        # 应该是同一个实例
        assert strategy1 is strategy2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
