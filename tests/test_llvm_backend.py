# -*- coding: utf-8 -*-
"""LLVM Backend 测试

测试 LLVMBackend (llvmlite) 的基本功能。

作者：远
日期：2026-04-09
"""

import pytest

from zhc.ir.program import IRProgram, IRFunction, IRGlobalVar
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode

from zhc.backend.llvm_backend import LLVMBackend, LLVM_AVAILABLE


@pytest.mark.skipif(not LLVM_AVAILABLE, reason="llvmlite not available")
class TestLLVMBackend:
    """LLVMBackend 测试"""

    def test_backend_creation(self):
        """测试 LLVMBackend 创建"""
        backend = LLVMBackend()
        assert backend is not None
        assert backend.is_available()

    def test_empty_program(self):
        """测试空程序"""
        backend = LLVMBackend()
        ir = IRProgram()
        result = backend.generate(ir)
        # llvmlite 输出 ModuleID 而不是 source_filename
        assert "ModuleID" in result
        assert "zhc_module" in result

    def test_simple_function(self):
        """测试简单函数"""
        backend = LLVMBackend()
        ir = IRProgram()

        # 创建简单函数：int test_func() { return 42; }
        func = IRFunction(name="test_func", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["42"]))
        func.basic_blocks.append(bb)
        ir.functions.append(func)

        result = backend.generate(ir)
        # llvmlite 可能用引号包围函数名
        assert "test_func" in result
        assert "i32" in result
        assert "ret i32 42" in result

    def test_global_variable(self):
        """测试全局变量"""
        backend = LLVMBackend()
        ir = IRProgram()

        # 全局变量
        gv = IRGlobalVar(name="counter", ty="整数型")
        ir.global_vars.append(gv)

        result = backend.generate(ir)
        assert "counter" in result


@pytest.mark.skipif(not LLVM_AVAILABLE, reason="llvmlite not available")
class TestLLVMBackendIntegration:
    """LLVMBackend 集成测试"""

    def test_complete_program(self):
        """测试完整程序"""
        backend = LLVMBackend()
        ir = IRProgram()

        # 全局变量
        ir.global_vars.append(IRGlobalVar(name="counter", ty="整数型"))

        # int main() { return 0; }
        main = IRFunction(name="main", return_type="整数型")
        entry = IRBasicBlock(label="entry")
        entry.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["0"]))
        main.basic_blocks.append(entry)
        ir.functions.append(main)

        result = backend.generate(ir)

        # 验证输出
        assert "counter" in result
        assert "main" in result
        assert "define i32" in result


@pytest.mark.skipif(not LLVM_AVAILABLE, reason="llvmlite not available")
class TestLLVMBackendVersion:
    """测试版本信息"""

    def test_version(self):
        """测试版本获取"""
        backend = LLVMBackend()
        version = backend.get_version()
        assert version is not None
        assert "llvmlite" in version
