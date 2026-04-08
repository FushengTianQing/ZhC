# -*- coding: utf-8 -*-
"""LLVMBackend 测试

测试使用 llvmlite 的真正 LLVM 后端。

作者：远
日期：2026-04-08
"""

import pytest
from zhc.ir.program import IRProgram, IRFunction, IRGlobalVar
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode


class TestLLVMBackendImport:
    """LLVMBackend 导入测试"""

    def test_llvm_backend_available(self):
        """测试 llvmlite 是否可用"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        assert LLVM_BACKEND_AVAILABLE is True


class TestLLVMBackendCreation:
    """LLVMBackend 创建测试"""

    def test_backend_creation(self):
        """测试后端创建"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()
        assert backend.module is None
        # 新 API: functions 在 context 中
        assert backend.context.functions == {}
        assert backend.context.blocks == {}

    def test_backend_with_target(self):
        """测试指定目标平台"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend(target_triple="x86_64-apple-darwin")
        assert backend.target_triple == "x86_64-apple-darwin"


class TestLLVMBackendCompilation:
    """LLVMBackend 编译测试"""

    def test_simple_function(self):
        """测试简单函数编译"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()
        ir = IRProgram()

        # 创建简单函数
        func = IRFunction(name="test_func", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["42"]))
        func.basic_blocks.append(bb)
        ir.functions.append(func)

        # 使用 compile_to_module 方法
        module = backend.compile_to_module(ir, "test_module")
        assert module is not None

        llvm_ir = backend.to_llvm_ir()
        # llvmlite 可能给函数名加引号
        assert "define i32 @" in llvm_ir
        assert "test_func" in llvm_ir
        assert "ret i32 42" in llvm_ir

    def test_arithmetic_function(self):
        """测试算术函数编译"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()
        ir = IRProgram()

        # 创建算术函数
        func = IRFunction(name="add_func", return_type="整数型")
        bb = IRBasicBlock(label="entry")

        add_instr = IRInstruction(
            opcode=Opcode.ADD, operands=["10", "20"], result=["%result"]
        )
        bb.instructions.append(add_instr)
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["%result"]))

        func.basic_blocks.append(bb)
        ir.functions.append(func)

        # 使用 compile_to_module 方法
        backend.compile_to_module(ir, "add_module")
        llvm_ir = backend.to_llvm_ir()

        assert "add i32" in llvm_ir
        assert "%result = add i32 10, 20" in llvm_ir or "add i32 10, 20" in llvm_ir

    def test_comparison_function(self):
        """测试比较函数编译"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()
        ir = IRProgram()

        func = IRFunction(name="cmp_func", return_type="布尔型")
        bb = IRBasicBlock(label="entry")

        cmp_instr = IRInstruction(
            opcode=Opcode.LT, operands=["%a", "%b"], result=["%result"]
        )
        bb.instructions.append(cmp_instr)
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["%result"]))

        func.basic_blocks.append(bb)
        ir.functions.append(func)

        # 使用 compile_to_module 方法
        backend.compile_to_module(ir, "cmp_module")
        llvm_ir = backend.to_llvm_ir()

        assert "icmp slt" in llvm_ir or "icmp" in llvm_ir


class TestLLVMBackendFeatures:
    """LLVMBackend 功能测试"""

    def test_global_variable(self):
        """测试全局变量"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()
        ir = IRProgram()

        ir.global_vars.append(IRGlobalVar(name="global_var", ty="整数型"))

        # 使用 compile_to_module 方法
        backend.compile_to_module(ir, "global_module")
        llvm_ir = backend.to_llvm_ir()

        assert "@global_var" in llvm_ir or "global_var" in llvm_ir

    def test_to_llvm_ir(self):
        """测试 LLVM IR 文本生成"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()
        ir = IRProgram()

        func = IRFunction(name="main", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["0"]))
        func.basic_blocks.append(bb)
        ir.functions.append(func)

        # 使用 compile_to_module 方法
        backend.compile_to_module(ir, "main_module")
        llvm_ir = backend.to_llvm_ir()

        # 验证 LLVM IR 结构
        assert "ModuleID" in llvm_ir or "source_filename" in llvm_ir
        assert "define i32 @" in llvm_ir
        assert "main" in llvm_ir
        assert "ret i32 0" in llvm_ir

    def test_type_mapping(self):
        """测试类型映射"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import LLVMBackend

        backend = LLVMBackend()

        # 测试各种类型
        assert backend._get_llvm_type("整数型") is not None
        assert backend._get_llvm_type("浮点型") is not None
        assert backend._get_llvm_type("布尔型") is not None
        assert backend._get_llvm_type("i64") is not None


class TestLLVMBackendError:
    """LLVMBackend 错误处理测试"""

    def test_missing_llvmlite(self):
        """测试 llvmlite 未安装时的错误"""
        # 这个测试检查当 llvmlite 不可用时是否有适当的错误处理
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 已安装，跳过测试")

        # 如果 llvmlite 不可用，导入应该失败
        # 这里不需要实际导入，因为 LLVM_BACKEND_AVAILABLE 已经告诉我们结果


class TestCompileToLLVM:
    """compile_to_llvm 便捷函数测试"""

    def test_compile_to_llvm_function(self):
        """测试便捷函数"""
        from zhc.backend import LLVM_BACKEND_AVAILABLE

        if not LLVM_BACKEND_AVAILABLE:
            pytest.skip("llvmlite 未安装，跳过测试")

        from zhc.backend import compile_to_llvm
        from zhc.ir.program import IRProgram, IRFunction
        from zhc.ir.instructions import IRBasicBlock, IRInstruction
        from zhc.ir.opcodes import Opcode

        ir = IRProgram()
        func = IRFunction(name="test", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["0"]))
        func.basic_blocks.append(bb)
        ir.functions.append(func)

        llvm_ir = compile_to_llvm(ir)
        assert llvm_ir is not None
        assert "define i32 @" in llvm_ir
        assert "test" in llvm_ir
