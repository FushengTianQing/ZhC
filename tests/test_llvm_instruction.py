# -*- coding: utf-8 -*-
"""LLVM 指令生成器测试

测试 ZhC IR Opcode 到 LLVM IR 指令的映射。

作者：远
日期：2026-04-08
"""

import pytest


class TestLLVMInstructionGeneratorImport:
    """指令生成器导入测试"""
    
    def test_generator_available(self):
        """测试 llvmlite 是否可用"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            available = True
        except ImportError:
            available = False
        
        if not available:
            pytest.skip("llvmlite 未安装，跳过测试")
        
        assert available


class TestLLVMInstructionGeneratorCreation:
    """指令生成器创建测试"""
    
    def test_generator_creation(self):
        """测试生成器创建"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        assert generator is not None


class TestInstructionMapping:
    """指令映射测试"""
    
    def test_arithmetic_instructions(self):
        """测试算术指令映射"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 算术指令
        assert generator.is_supported(Opcode.ADD)
        assert generator.is_supported(Opcode.SUB)
        assert generator.is_supported(Opcode.MUL)
        assert generator.is_supported(Opcode.DIV)
        assert generator.is_supported(Opcode.MOD)
    
    def test_comparison_instructions(self):
        """测试比较指令映射"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 比较指令
        assert generator.is_supported(Opcode.EQ)
        assert generator.is_supported(Opcode.NE)
        assert generator.is_supported(Opcode.LT)
        assert generator.is_supported(Opcode.LE)
        assert generator.is_supported(Opcode.GT)
        assert generator.is_supported(Opcode.GE)
    
    def test_bitwise_instructions(self):
        """测试位运算指令映射"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 位运算指令
        assert generator.is_supported(Opcode.AND)
        assert generator.is_supported(Opcode.OR)
        assert generator.is_supported(Opcode.XOR)
    
    def test_memory_instructions(self):
        """测试内存指令映射"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 内存指令
        assert generator.is_supported(Opcode.ALLOC)
        assert generator.is_supported(Opcode.LOAD)
        assert generator.is_supported(Opcode.STORE)
    
    def test_control_flow_instructions(self):
        """测试控制流指令映射"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 控制流指令
        assert generator.is_supported(Opcode.JMP)
        assert generator.is_supported(Opcode.JZ)
        assert generator.is_supported(Opcode.RET)
        assert generator.is_supported(Opcode.CALL)
    
    def test_conversion_instructions(self):
        """测试类型转换指令映射"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 类型转换指令
        assert generator.is_supported(Opcode.ZEXT)
        assert generator.is_supported(Opcode.SEXT)
        assert generator.is_supported(Opcode.TRUNC)


class TestInstructionInfo:
    """指令信息测试"""
    
    def test_get_instruction_info(self):
        """测试获取指令信息"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # ADD 指令
        info = generator.get_instruction_info(Opcode.ADD)
        assert info is not None
        assert info.opcode == Opcode.ADD
        assert info.llvm_op == "add"
        assert info.category == "算术"
        assert info.has_result is True
        
        # RET 指令
        info = generator.get_instruction_info(Opcode.RET)
        assert info is not None
        assert info.opcode == Opcode.RET
        assert info.llvm_op == "ret"
        assert info.category == "控制流"
        assert info.has_result is False
    
    def test_instruction_categories(self):
        """测试指令类别"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.opcodes import Opcode
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 算术类
        assert generator.get_instruction_info(Opcode.ADD).category == "算术"
        assert generator.get_instruction_info(Opcode.SUB).category == "算术"
        
        # 比较类
        assert generator.get_instruction_info(Opcode.EQ).category == "比较"
        assert generator.get_instruction_info(Opcode.LT).category == "比较"
        
        # 内存类
        assert generator.get_instruction_info(Opcode.ALLOC).category == "内存"
        assert generator.get_instruction_info(Opcode.LOAD).category == "内存"
        
        # 控制流类
        assert generator.get_instruction_info(Opcode.JMP).category == "控制流"
        assert generator.get_instruction_info(Opcode.RET).category == "控制流"


class TestInstructionGeneration:
    """指令生成测试"""
    
    def test_generate_add_instruction(self):
        """测试生成加法指令"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.instructions import IRInstruction
            from zhc.ir.opcodes import Opcode
            import llvmlite.ir as ll
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 创建模块和函数
        module = ll.Module(name="test")
        func_type = ll.FunctionType(ll.IntType(32), [])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)
        
        # 创建 ADD 指令
        instr = IRInstruction(
            opcode=Opcode.ADD,
            operands=["10", "20"],
            result=["%result"]
        )
        
        # 生成指令
        values = {}
        blocks = {}
        functions = {}
        result = generator.generate(builder, instr, values, blocks, functions)
        
        assert result is not None
        assert "add" in str(result)
    
    def test_generate_ret_instruction(self):
        """测试生成返回指令"""
        try:
            from zhc.backend.llvm_instruction import LLVMInstructionGenerator
            from zhc.ir.instructions import IRInstruction
            from zhc.ir.opcodes import Opcode
            import llvmlite.ir as ll
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        generator = LLVMInstructionGenerator()
        
        # 创建模块和函数
        module = ll.Module(name="test")
        func_type = ll.FunctionType(ll.IntType(32), [])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)
        
        # 创建 RET 指令
        instr = IRInstruction(
            opcode=Opcode.RET,
            operands=["42"]
        )
        
        # 生成指令
        values = {}
        blocks = {}
        functions = {}
        result = generator.generate(builder, instr, values, blocks, functions)
        
        # RET 指令不返回值
        assert result is None


class TestConvenienceFunction:
    """便捷函数测试"""
    
    def test_generate_llvm_instruction_function(self):
        """测试便捷函数"""
        try:
            from zhc.backend.llvm_instruction import generate_llvm_instruction
            from zhc.ir.instructions import IRInstruction
            from zhc.ir.opcodes import Opcode
            import llvmlite.ir as ll
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        # 创建模块和函数
        module = ll.Module(name="test")
        func_type = ll.FunctionType(ll.IntType(32), [])
        func = ll.Function(module, func_type, "test_func")
        block = func.append_basic_block("entry")
        builder = ll.IRBuilder(block)
        
        # 创建 ADD 指令
        instr = IRInstruction(
            opcode=Opcode.ADD,
            operands=["5", "10"],
            result=["%sum"]
        )
        
        # 生成指令
        values = {}
        blocks = {}
        functions = {}
        result = generate_llvm_instruction(builder, instr, values, blocks, functions)
        
        assert result is not None