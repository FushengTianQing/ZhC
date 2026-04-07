#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步代码生成器测试 - Async Code Generator Tests

测试异步代码生成器的功能：
1. 状态枚举生成
2. 状态结构体生成
3. 状态机函数生成
4. Future/Promise 结构生成
5. 辅助函数生成

Phase 4 - Stage 2 - Task 11.3 - Day 3

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
from zhc.codegen.async_codegen import (
    AsyncCodeGenerator,
    AsyncFunctionContext,
    GeneratedAsyncCode,
    AsyncState,
    generate_async_code,
)


class TestAsyncCodeGenerator:
    """测试异步代码生成器"""

    def test_create_generator(self):
        """测试创建生成器"""
        generator = AsyncCodeGenerator()
        
        assert generator.contexts == {}
        assert generator.generated_code == {}
        assert generator._current_context is None

    def test_generate_simple_async_function(self):
        """测试生成简单的异步函数"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="fetch_data",
            return_type="char*",
            parameters=[
                {"name": "url", "type": "char*"}
            ],
            body_statements=[]
        )
        
        # 检查生成的代码
        assert isinstance(code, GeneratedAsyncCode)
        assert code.state_enum != ""
        assert code.state_struct != ""
        assert len(code.state_functions) > 0
        assert code.future_struct != ""

    def test_generate_state_enum(self):
        """测试生成状态枚举"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="test_func",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 检查状态枚举
        assert "typedef enum" in code.state_enum
        assert "test_func_state" in code.state_enum
        assert "STATE_0" in code.state_enum
        assert "STATE_COMPLETED" in code.state_enum

    def test_generate_state_struct(self):
        """测试生成状态结构体"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="compute",
            return_type="int",
            parameters=[
                {"name": "x", "type": "int"},
                {"name": "y", "type": "int"}
            ],
            body_statements=[]
        )
        
        # 检查状态结构体
        assert "typedef struct" in code.state_struct
        assert "compute_context" in code.state_struct
        assert "current_state" in code.state_struct
        assert "int x" in code.state_struct
        assert "int y" in code.state_struct
        assert "int result" in code.state_struct

    def test_generate_state_functions(self):
        """测试生成状态机函数"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="async_task",
            return_type="void",
            parameters=[],
            body_statements=[]
        )
        
        # 检查状态机函数
        assert len(code.state_functions) >= 3  # resume, init, cancel
        
        # 检查 resume 函数
        resume_func = code.state_functions[0]
        assert "async_task_resume" in resume_func
        assert "switch" in resume_func
        
        # 检查 init 函数
        init_func = code.state_functions[1]
        assert "async_task_create" in init_func
        assert "malloc" in init_func
        
        # 检查 cancel 函数
        cancel_func = code.state_functions[2]
        assert "async_task_cancel" in cancel_func
        assert "free" in cancel_func

    def test_generate_future_struct(self):
        """测试生成 Future 结构体"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="get_value",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 检查 Future 结构体
        assert "typedef struct" in code.future_struct
        assert "get_value_future" in code.future_struct
        assert "state" in code.future_struct
        assert "int value" in code.future_struct
        assert "callback" in code.future_struct

    def test_generate_helper_functions(self):
        """测试生成辅助函数"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="process",
            return_type="char*",
            parameters=[],
            body_statements=[]
        )
        
        # 检查辅助函数
        assert len(code.helper_functions) >= 3  # create, complete, await
        
        # 检查 Future 创建函数
        create_func = code.helper_functions[0]
        assert "process_future_create" in create_func
        assert "malloc" in create_func
        
        # 检查 Future 完成函数
        complete_func = code.helper_functions[1]
        assert "process_future_complete" in complete_func
        assert "COMPLETED" in complete_func
        
        # 检查 Await 函数
        await_func = code.helper_functions[2]
        assert "process_await" in await_func
        assert "while" in await_func

    def test_generate_runtime_support(self):
        """测试生成运行时支持代码"""
        generator = AsyncCodeGenerator()
        
        runtime_code = generator.generate_runtime_support()
        
        # 检查运行时支持代码
        assert "AsyncState" in runtime_code
        assert "Future" in runtime_code
        assert "Promise" in runtime_code
        assert "AsyncScheduler" in runtime_code
        assert "async_scheduler_init" in runtime_code
        assert "async_scheduler_run" in runtime_code

    def test_context_management(self):
        """测试上下文管理"""
        generator = AsyncCodeGenerator()
        
        # 生成第一个函数
        generator.generate_async_function(
            function_name="func1",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 生成第二个函数
        generator.generate_async_function(
            function_name="func2",
            return_type="char*",
            parameters=[],
            body_statements=[]
        )
        
        # 检查上下文
        assert "func1" in generator.contexts
        assert "func2" in generator.contexts
        assert "func1" in generator.generated_code
        assert "func2" in generator.generated_code

    def test_get_generated_code(self):
        """测试获取已生成的代码"""
        generator = AsyncCodeGenerator()
        
        generator.generate_async_function(
            function_name="test_func",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 获取已生成的代码
        code = generator.get_generated_code("test_func")
        assert code is not None
        assert isinstance(code, GeneratedAsyncCode)
        
        # 获取不存在的代码
        code = generator.get_generated_code("nonexistent")
        assert code is None


class TestAsyncFunctionContext:
    """测试异步函数上下文"""

    def test_create_context(self):
        """测试创建上下文"""
        context = AsyncFunctionContext(
            function_name="test",
            return_type="int",
            state_enum_name="test_state",
            state_struct_name="test_context"
        )
        
        assert context.function_name == "test"
        assert context.return_type == "int"
        assert context.state_enum_name == "test_state"
        assert context.state_struct_name == "test_context"
        assert context.states == []
        assert context.local_variables == []
        assert context.await_points == []

    def test_context_with_states(self):
        """测试带状态的上下文"""
        context = AsyncFunctionContext(
            function_name="test",
            return_type="int",
            state_enum_name="test_state",
            state_struct_name="test_context",
            states=["STATE_0", "STATE_1", "STATE_COMPLETED"],
            await_points=[1]
        )
        
        assert len(context.states) == 3
        assert len(context.await_points) == 1
        assert 1 in context.await_points


class TestGeneratedAsyncCode:
    """测试生成的异步代码"""

    def test_create_generated_code(self):
        """测试创建生成的代码"""
        code = GeneratedAsyncCode()
        
        assert code.state_enum == ""
        assert code.state_struct == ""
        assert code.state_functions == []
        assert code.future_struct == ""
        assert code.promise_struct == ""
        assert code.helper_functions == []

    def test_generated_code_with_content(self):
        """测试带内容的生成代码"""
        code = GeneratedAsyncCode(
            state_enum="enum { STATE_0 };",
            state_struct="struct { int state; };",
            state_functions=["void func1() {}", "void func2() {}"],
            future_struct="struct Future { int state; };",
            helper_functions=["void helper1() {}"]
        )
        
        assert code.state_enum == "enum { STATE_0 };"
        assert code.state_struct == "struct { int state; };"
        assert len(code.state_functions) == 2
        assert len(code.helper_functions) == 1


class TestAsyncState:
    """测试异步状态枚举"""

    def test_async_state_values(self):
        """测试异步状态值"""
        assert AsyncState.INITIAL.value == 1
        assert AsyncState.RUNNING.value == 2
        assert AsyncState.SUSPENDED.value == 3
        assert AsyncState.COMPLETED.value == 4
        assert AsyncState.FAILED.value == 5

    def test_async_state_names(self):
        """测试异步状态名称"""
        assert AsyncState.INITIAL.name == "INITIAL"
        assert AsyncState.RUNNING.name == "RUNNING"
        assert AsyncState.SUSPENDED.name == "SUSPENDED"
        assert AsyncState.COMPLETED.name == "COMPLETED"
        assert AsyncState.FAILED.name == "FAILED"


class TestConvenienceFunction:
    """测试便捷函数"""

    def test_generate_async_code_function(self):
        """测试 generate_async_code 便捷函数"""
        code = generate_async_code(
            function_name="test",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        assert isinstance(code, GeneratedAsyncCode)
        assert code.state_enum != ""
        assert code.state_struct != ""

    def test_generate_async_code_with_parameters(self):
        """测试带参数的 generate_async_code 函数"""
        code = generate_async_code(
            function_name="compute",
            return_type="int",
            parameters=[
                {"name": "a", "type": "int"},
                {"name": "b", "type": "int"}
            ],
            body_statements=[]
        )
        
        assert "int a" in code.state_struct
        assert "int b" in code.state_struct


class TestComplexScenarios:
    """测试复杂场景"""

    def test_multiple_async_functions(self):
        """测试多个异步函数"""
        generator = AsyncCodeGenerator()
        
        # 生成多个函数
        for i in range(5):
            generator.generate_async_function(
                function_name=f"func_{i}",
                return_type="int",
                parameters=[],
                body_statements=[]
            )
        
        # 检查所有函数都已生成
        for i in range(5):
            assert f"func_{i}" in generator.contexts
            assert f"func_{i}" in generator.generated_code

    def test_async_function_with_multiple_parameters(self):
        """测试带多个参数的异步函数"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="complex_func",
            return_type="char*",
            parameters=[
                {"name": "url", "type": "char*"},
                {"name": "timeout", "type": "int"},
                {"name": "retries", "type": "int"},
                {"name": "callback", "type": "void*"}
            ],
            body_statements=[]
        )
        
        # 检查所有参数都在结构体中
        assert "char* url" in code.state_struct
        assert "int timeout" in code.state_struct
        assert "int retries" in code.state_struct
        assert "void* callback" in code.state_struct

    def test_async_function_with_different_return_types(self):
        """测试不同返回类型的异步函数"""
        generator = AsyncCodeGenerator()
        
        # 整数返回类型
        code1 = generator.generate_async_function(
            function_name="get_int",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        assert "int result" in code1.state_struct
        assert "int value" in code1.future_struct
        
        # 字符串返回类型
        code2 = generator.generate_async_function(
            function_name="get_string",
            return_type="char*",
            parameters=[],
            body_statements=[]
        )
        assert "char* result" in code2.state_struct
        assert "char* value" in code2.future_struct
        
        # 浮点返回类型
        code3 = generator.generate_async_function(
            function_name="get_float",
            return_type="float",
            parameters=[],
            body_statements=[]
        )
        assert "float result" in code3.state_struct
        assert "float value" in code3.future_struct


class TestCodeQuality:
    """测试代码质量"""

    def test_generated_code_syntax(self):
        """测试生成代码的语法"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="test",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 检查基本语法元素
        # typedef enum 以 "} enum_name;" 结尾，这是正确的 C 语法
        assert "} test_state;" in code.state_enum
        # typedef struct 以 "} struct_name;" 结尾，这是正确的 C 语法
        assert "} test_context;" in code.state_struct
        
        for func in code.state_functions:
            # 检查函数有开始和结束括号
            assert "{" in func
            assert "}" in func

    def test_generated_code_consistency(self):
        """测试生成代码的一致性"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="consistent_func",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 检查命名一致性
        assert "consistent_func_state" in code.state_enum
        assert "consistent_func_context" in code.state_struct
        assert "consistent_func_future" in code.future_struct
        assert "consistent_func_resume" in code.state_functions[0]
        assert "consistent_func_create" in code.state_functions[1]

    def test_generated_code_completeness(self):
        """测试生成代码的完整性"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="complete_func",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 检查所有必要的代码都已生成
        assert code.state_enum != ""
        assert code.state_struct != ""
        assert len(code.state_functions) >= 3
        assert code.future_struct != ""
        assert len(code.helper_functions) >= 3


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_function_name(self):
        """测试空函数名"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 应该仍然生成代码
        assert code.state_enum != ""

    def test_empty_parameters(self):
        """测试空参数列表"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="no_params",
            return_type="int",
            parameters=[],
            body_statements=[]
        )
        
        # 检查结构体中没有参数字段（除了状态和结果）
        lines = code.state_struct.split("\n")
        param_count = sum(1 for line in lines if "int " in line and "result" not in line and "state" not in line)
        assert param_count == 0

    def test_void_return_type(self):
        """测试 void 返回类型"""
        generator = AsyncCodeGenerator()
        
        code = generator.generate_async_function(
            function_name="void_func",
            return_type="void",
            parameters=[],
            body_statements=[]
        )
        
        # 检查 void 返回类型
        assert "void result" in code.state_struct
        assert "void value" in code.future_struct


if __name__ == "__main__":
    pytest.main([__file__, "-v"])