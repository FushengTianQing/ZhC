# -*- coding: utf-8 -*-
"""
ZHC IR - 优化提示系统测试

作者：远
日期：2026-04-08
"""

import pytest

from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.values import IRValue, ValueKind
from zhc.ir.opcodes import Opcode
from zhc.ir.optimization_hints import (
    OptimizationHint,
    FunctionOptimizationHints,
    ProgramOptimizationHints,
    OptimizationHintAnalyzer,
    CBackendHintAdapter,
    LLVMBackendHintAdapter,
    analyze_optimization_hints,
    get_c_function_prefix,
    get_llvm_attributes,
)


# =============================================================================
# 测试辅助函数
# =============================================================================

def create_simple_function(name: str, instruction_count: int = 5) -> IRFunction:
    """创建简单的测试函数
    
    注意：
    - IRFunction 在 __init__ 中自动创建一个空的 entry 基本块
    - 我们需要在已存在的基本块上添加指令
    - RET 指令不计入 instruction_count
    """
    func = IRFunction(name=name)
    
    # 添加参数
    func.add_param(IRValue(name="x", ty="整数型", kind=ValueKind.PARAM))
    func.add_param(IRValue(name="y", ty="整数型", kind=ValueKind.PARAM))
    
    # 获取已存在的 entry 基本块
    entry = func.basic_blocks[0]
    
    # 跟踪最后一个结果值
    last_result = None
    
    # 添加指令（非 RET）
    for i in range(instruction_count):
        result = IRValue(name=f"%r{i}", ty="整数型")
        entry.add_instruction(IRInstruction(
            opcode=Opcode.ADD,
            operands=[
                IRValue(name="x", ty="整数型"),
                IRValue(name="y", ty="整数型")
            ],
            result=[result]
        ))
        last_result = result
    
    # 添加返回指令（不计入 instruction_count）
    if last_result:
        entry.add_instruction(IRInstruction(
            opcode=Opcode.RET,
            operands=[last_result]
        ))
    else:
        entry.add_instruction(IRInstruction(
            opcode=Opcode.RET,
            operands=[IRValue(name="0", ty="整数型", kind=ValueKind.CONST, const_value=0)]
        ))
    
    return func


def create_caller_function(name: str, callee_name: str) -> IRFunction:
    """创建调用其他函数的测试函数"""
    func = IRFunction(name=name)
    entry = IRBasicBlock(f"{name}.entry")
    
    # 添加参数
    func.add_param(IRValue(name="a", ty="整数型", kind=ValueKind.PARAM))
    func.add_param(IRValue(name="b", ty="整数型", kind=ValueKind.PARAM))
    
    # 调用函数
    call_result = IRValue(name=f"%call_result", ty="整数型")
    entry.add_instruction(IRInstruction(
        opcode=Opcode.CALL,
        operands=[
            IRValue(name=f"@{callee_name}", ty="函数型"),
            IRValue(name="a", ty="整数型"),
            IRValue(name="b", ty="整数型")
        ],
        result=[call_result]
    ))
    
    # 返回结果
    entry.add_instruction(IRInstruction(
        opcode=Opcode.RET,
        operands=[call_result]
    ))
    
    func.add_basic_block(entry.label)
    return func


def create_program_with_calls() -> IRProgram:
    """创建带有函数调用的测试程序"""
    program = IRProgram()
    
    # 添加小函数
    small_func = create_simple_function("small_func", instruction_count=5)
    program.add_function(small_func)
    
    # 添加大函数
    large_func = create_simple_function("large_func", instruction_count=150)
    program.add_function(large_func)
    
    # 添加调用者函数
    caller = create_caller_function("caller", "small_func")
    program.add_function(caller)
    
    return program


# =============================================================================
# OptimizationHint 测试
# =============================================================================

class TestOptimizationHint:
    """测试 OptimizationHint 枚举"""
    
    def test_hint_values(self):
        """测试提示值"""
        assert OptimizationHint.INLINE.value == 1
        assert OptimizationHint.ALWAYS_INLINE.value == 2
        assert OptimizationHint.HOT.value == 3
        assert OptimizationHint.COLD.value == 4
        assert OptimizationHint.NORETURN.value == 5
        assert OptimizationHint.OPTSIZE.value == 6
        assert OptimizationHint.MINSIZE.value == 7


# =============================================================================
# FunctionOptimizationHints 测试
# =============================================================================

class TestFunctionOptimizationHints:
    """测试 FunctionOptimizationHints 数据类"""
    
    def test_creation(self):
        """测试创建"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE, OptimizationHint.HOT},
            reason={
                OptimizationHint.INLINE: "小函数",
                OptimizationHint.HOT: "热点",
            },
            confidence={
                OptimizationHint.INLINE: 0.9,
                OptimizationHint.HOT: 0.8,
            }
        )
        
        assert hints.function_name == "test_func"
        assert len(hints.hints) == 2
        assert OptimizationHint.INLINE in hints.hints
        assert OptimizationHint.HOT in hints.hints
    
    def test_has_hint(self):
        """测试 has_hint 方法"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        assert hints.has_hint(OptimizationHint.INLINE) is True
        assert hints.has_hint(OptimizationHint.HOT) is False
    
    def test_get_reason(self):
        """测试 get_reason 方法"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={OptimizationHint.INLINE: "小函数（5 条指令）"},
            confidence={}
        )
        
        assert hints.get_reason(OptimizationHint.INLINE) == "小函数（5 条指令）"
        assert hints.get_reason(OptimizationHint.HOT) is None
    
    def test_get_confidence(self):
        """测试 get_confidence 方法"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={OptimizationHint.INLINE: 0.9}
        )
        
        assert hints.get_confidence(OptimizationHint.INLINE) == 0.9
        assert hints.get_confidence(OptimizationHint.HOT) == 0.0


# =============================================================================
# ProgramOptimizationHints 测试
# =============================================================================

class TestProgramOptimizationHints:
    """测试 ProgramOptimizationHints 数据类"""
    
    def test_creation(self):
        """测试创建"""
        func_hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        program_hints = ProgramOptimizationHints(
            function_hints={"test_func": func_hints}
        )
        
        assert len(program_hints.function_hints) == 1
        assert "test_func" in program_hints.function_hints
    
    def test_get_function_hints(self):
        """测试 get_function_hints 方法"""
        func_hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        program_hints = ProgramOptimizationHints(
            function_hints={"test_func": func_hints}
        )
        
        result = program_hints.get_function_hints("test_func")
        assert result is not None
        assert result.function_name == "test_func"
        
        # 不存在的函数
        result = program_hints.get_function_hints("nonexistent")
        assert result is None
    
    def test_has_function_hints(self):
        """测试 has_function_hints 方法"""
        func_hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        program_hints = ProgramOptimizationHints(
            function_hints={"test_func": func_hints}
        )
        
        assert program_hints.has_function_hints("test_func") is True
        assert program_hints.has_function_hints("nonexistent") is False


# =============================================================================
# OptimizationHintAnalyzer 测试
# =============================================================================

class TestOptimizationHintAnalyzer:
    """测试 OptimizationHintAnalyzer 分析器"""
    
    def test_initialization(self):
        """测试初始化"""
        program = create_program_with_calls()
        analyzer = OptimizationHintAnalyzer(program)
        
        assert analyzer.program is program
        assert isinstance(analyzer.call_counts, dict)
    
    def test_analyze(self):
        """测试分析"""
        program = create_program_with_calls()
        analyzer = OptimizationHintAnalyzer(program)
        
        hints = analyzer.analyze()
        
        assert isinstance(hints, ProgramOptimizationHints)
        assert len(hints.function_hints) > 0
    
    def test_small_function_detection(self):
        """测试小函数检测"""
        program = IRProgram()
        small_func = create_simple_function("small_func", instruction_count=5)
        program.add_function(small_func)
        
        analyzer = OptimizationHintAnalyzer(program)
        hints = analyzer.analyze()
        
        func_hints = hints.get_function_hints("small_func")
        assert func_hints is not None
        assert func_hints.has_hint(OptimizationHint.INLINE)
    
    def test_large_function_detection(self):
        """测试大函数检测"""
        program = IRProgram()
        large_func = create_simple_function("large_func", instruction_count=150)
        program.add_function(large_func)
        
        analyzer = OptimizationHintAnalyzer(program)
        hints = analyzer.analyze()
        
        func_hints = hints.get_function_hints("large_func")
        assert func_hints is not None
        assert func_hints.has_hint(OptimizationHint.OPTSIZE)
    
    def test_hot_function_detection(self):
        """测试热点函数检测"""
        program = IRProgram()
        
        # 创建被调用多次的函数
        hot_func = create_simple_function("hot_func", instruction_count=20)
        program.add_function(hot_func)
        
        # 创建多个调用者（使用显式函数名）
        for i in range(6):
            caller = IRFunction(name=f"caller_{i}")
            entry = caller.basic_blocks[0]
            
            # 添加调用指令
            call_result = IRValue(name="%result", ty="整数型")
            entry.add_instruction(IRInstruction(
                opcode=Opcode.CALL,
                operands=[
                    IRValue(name="hot_func", ty="函数型"),
                    IRValue(name="1", ty="整数型"),
                    IRValue(name="2", ty="整数型")
                ],
                result=[call_result]
            ))
            
            entry.add_instruction(IRInstruction(
                opcode=Opcode.RET,
                operands=[call_result]
            ))
            
            program.add_function(caller)
        
        analyzer = OptimizationHintAnalyzer(program)
        hints = analyzer.analyze()
        
        func_hints = hints.get_function_hints("hot_func")
        assert func_hints is not None
        assert func_hints.has_hint(OptimizationHint.HOT)
    
    def test_single_call_site_detection(self):
        """测试单调用点函数检测"""
        program = IRProgram()
        
        # 创建只被调用一次的函数
        single_func = create_simple_function("single_func", instruction_count=20)
        program.add_function(single_func)
        
        # 创建一个调用者
        caller = IRFunction(name="caller")
        entry = caller.basic_blocks[0]
        
        # 添加调用指令
        call_result = IRValue(name="%result", ty="整数型")
        entry.add_instruction(IRInstruction(
            opcode=Opcode.CALL,
            operands=[
                IRValue(name="single_func", ty="函数型"),
                IRValue(name="1", ty="整数型"),
                IRValue(name="2", ty="整数型")
            ],
            result=[call_result]
        ))
        
        entry.add_instruction(IRInstruction(
            opcode=Opcode.RET,
            operands=[call_result]
        ))
        
        program.add_function(caller)
        
        analyzer = OptimizationHintAnalyzer(program)
        hints = analyzer.analyze()
        
        func_hints = hints.get_function_hints("single_func")
        assert func_hints is not None
        assert func_hints.has_hint(OptimizationHint.ALWAYS_INLINE)


# =============================================================================
# CBackendHintAdapter 测试
# =============================================================================

class TestCBackendHintAdapter:
    """测试 CBackendHintAdapter 适配器"""
    
    def test_inline_prefix(self):
        """测试 inline 前缀"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        adapter = CBackendHintAdapter()
        prefix = adapter.get_function_prefix(hints)
        
        assert "inline" in prefix
    
    def test_always_inline_prefix(self):
        """测试 always_inline 前缀"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.ALWAYS_INLINE},
            reason={},
            confidence={}
        )
        
        adapter = CBackendHintAdapter()
        prefix = adapter.get_function_prefix(hints)
        
        assert "inline" in prefix
        assert "always_inline" in prefix
    
    def test_hot_prefix(self):
        """测试 hot 前缀"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.HOT},
            reason={},
            confidence={}
        )
        
        adapter = CBackendHintAdapter()
        prefix = adapter.get_function_prefix(hints)
        
        assert "hot" in prefix
    
    def test_multiple_hints(self):
        """测试多个提示"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE, OptimizationHint.HOT},
            reason={},
            confidence={}
        )
        
        adapter = CBackendHintAdapter()
        prefix = adapter.get_function_prefix(hints)
        
        assert "inline" in prefix
        assert "hot" in prefix
    
    def test_generate_function_declaration(self):
        """测试生成函数声明"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        adapter = CBackendHintAdapter()
        declaration = adapter.generate_function_declaration(
            "test_func", hints, "int", "int a, int b"
        )
        
        assert "inline" in declaration
        assert "int test_func(int a, int b)" in declaration


# =============================================================================
# LLVMBackendHintAdapter 测试
# =============================================================================

class TestLLVMBackendHintAdapter:
    """测试 LLVMBackendHintAdapter 适配器"""
    
    def test_always_inline_attribute(self):
        """测试 always_inline 属性"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.ALWAYS_INLINE},
            reason={},
            confidence={}
        )
        
        adapter = LLVMBackendHintAdapter()
        attrs = adapter.get_llvm_attributes(hints)
        
        assert "alwaysinline" in attrs
    
    def test_hot_attribute(self):
        """测试 hot 属性"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.HOT},
            reason={},
            confidence={}
        )
        
        adapter = LLVMBackendHintAdapter()
        attrs = adapter.get_llvm_attributes(hints)
        
        assert "hot" in attrs
    
    def test_multiple_attributes(self):
        """测试多个属性"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.ALWAYS_INLINE, OptimizationHint.HOT},
            reason={},
            confidence={}
        )
        
        adapter = LLVMBackendHintAdapter()
        attrs = adapter.get_llvm_attributes(hints)
        
        assert "alwaysinline" in attrs
        assert "hot" in attrs


# =============================================================================
# 便捷函数测试
# =============================================================================

class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_analyze_optimization_hints(self):
        """测试 analyze_optimization_hints 函数"""
        program = create_program_with_calls()
        hints = analyze_optimization_hints(program)
        
        assert isinstance(hints, ProgramOptimizationHints)
    
    def test_get_c_function_prefix(self):
        """测试 get_c_function_prefix 函数"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.INLINE},
            reason={},
            confidence={}
        )
        
        prefix = get_c_function_prefix(hints)
        assert "inline" in prefix
    
    def test_get_llvm_attributes(self):
        """测试 get_llvm_attributes 函数"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints={OptimizationHint.HOT},
            reason={},
            confidence={}
        )
        
        attrs = get_llvm_attributes(hints)
        assert "hot" in attrs


# =============================================================================
# 边界情况测试
# =============================================================================

class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_program(self):
        """测试空程序"""
        program = IRProgram()
        analyzer = OptimizationHintAnalyzer(program)
        hints = analyzer.analyze()
        
        assert len(hints.function_hints) == 0
    
    def test_no_hints(self):
        """测试没有提示的函数"""
        hints = FunctionOptimizationHints(
            function_name="test_func",
            hints=set(),
            reason={},
            confidence={}
        )
        
        adapter = CBackendHintAdapter()
        prefix = adapter.get_function_prefix(hints)
        
        assert prefix == ""
    
    def test_very_large_function(self):
        """测试超大函数"""
        program = IRProgram()
        very_large_func = create_simple_function("very_large_func", instruction_count=250)
        program.add_function(very_large_func)
        
        analyzer = OptimizationHintAnalyzer(program)
        hints = analyzer.analyze()
        
        func_hints = hints.get_function_hints("very_large_func")
        assert func_hints is not None
        assert func_hints.has_hint(OptimizationHint.MINSIZE)


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])