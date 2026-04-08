# -*- coding: utf-8 -*-
"""LLVM JIT 执行引擎测试

测试 JIT 编译和执行功能。

作者：远
日期：2026-04-08
"""

import pytest


class TestLLVMJITImport:
    """JIT 导入测试"""
    
    def test_jit_available(self):
        """测试 llvmlite 是否可用"""
        try:
            from zhc.backend.llvm_jit import LLVMJIT
            available = True
        except ImportError:
            available = False
        
        if not available:
            pytest.skip("llvmlite 未安装，跳过测试")
        
        assert available


class TestLLVMJITCreation:
    """JIT 创建测试"""
    
    def test_jit_creation(self):
        """测试 JIT 创建"""
        try:
            from zhc.backend.llvm_jit import LLVMJIT
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        jit = LLVMJIT()
        assert jit is not None
        assert jit._compiled is False
    
    def test_jit_with_opt_level(self):
        """测试指定优化级别"""
        try:
            from zhc.backend.llvm_jit import LLVMJIT
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        jit = LLVMJIT(opt_level=3)
        assert jit.opt_level == 3


class TestLLVMJITCompilation:
    """JIT 编译测试"""
    
    def test_compile_simple_program(self):
        """测试编译简单程序"""
        try:
            from zhc.backend.llvm_jit import LLVMJIT
            from zhc.ir.program import IRProgram
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        jit = LLVMJIT()
        ir = IRProgram()
        
        # 空程序
        jit.compile(ir, "test_module")
        
        assert jit._compiled is True
        assert jit._module is not None
    
    def test_get_llvm_ir(self):
        """测试获取 LLVM IR"""
        try:
            from zhc.backend.llvm_jit import LLVMJIT
            from zhc.ir.program import IRProgram
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        jit = LLVMJIT()
        ir = IRProgram()
        
        jit.compile(ir, "test_module")
        
        llvm_ir = jit.get_llvm_ir()
        assert llvm_ir != ""


class TestLLVMJITExecution:
    """JIT 执行测试"""
    
    def test_jit_module_creation(self):
        """测试 JIT 模块创建"""
        try:
            from zhc.backend.llvm_jit import LLVMJIT
            from zhc.ir.program import IRProgram
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        jit = LLVMJIT()
        ir = IRProgram()
        
        jit.compile(ir)
        
        # 验证模块已创建
        assert jit._module is not None
        assert jit._compiled is True


class TestLLVMJITRunner:
    """JIT 运行器测试"""
    
    def test_runner_creation(self):
        """测试运行器创建"""
        try:
            from zhc.backend.llvm_jit import LLVMJITRunner
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        runner = LLVMJITRunner()
        assert runner is not None
    
    def test_load_ir(self):
        """测试加载 IR"""
        try:
            from zhc.backend.llvm_jit import LLVMJITRunner
            from zhc.ir.program import IRProgram
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        runner = LLVMJITRunner()
        ir = IRProgram()
        
        runner.load_ir(ir)
        
        # 列出函数（空程序）
        functions = runner.list_functions()
        assert isinstance(functions, list)


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_create_jit_runner(self):
        """测试创建运行器"""
        try:
            from zhc.backend.llvm_jit import create_jit_runner
            from zhc.ir.program import IRProgram
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        ir = IRProgram()
        
        # 创建运行器
        runner = create_jit_runner(ir)
        assert runner is not None
        
        # 列出函数（空程序）
        functions = runner.list_functions()
        assert isinstance(functions, list)