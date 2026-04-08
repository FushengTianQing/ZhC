# -*- coding: utf-8 -*-
"""ZhC LLVM JIT 执行引擎

支持即时编译和执行 ZhC IR 程序。

作者：远
日期：2026-04-08
"""

import os
import sys
import tempfile
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path

try:
    import llvmlite
    import llvmlite.ir as ll
    import llvmlite.binding as llvm
    LLVM_AVAILABLE = True
except ImportError:
    LLVM_AVAILABLE = False
    ll = None
    llvm = None

from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode


class JITError(Exception):
    """JIT 执行错误"""
    pass


class LLVMJIT:
    """LLVM JIT 执行引擎
    
    功能：
    - 编译 ZhC IR 到 LLVM Module
    - JIT 执行函数
    - 支持参数传递
    - 支持返回值获取
    """
    
    def __init__(self, opt_level: int = 2):
        """初始化 JIT 引擎
        
        Args:
            opt_level: 优化级别 (0-3)
        """
        if not LLVM_AVAILABLE:
            raise JITError(
                "llvmlite 未安装。请运行: pip install llvmlite>=0.39.0"
            )
        
        self.opt_level = opt_level
        self._execution_engine: Optional[llvm.ExecutionEngine] = None
        self._module: Optional[ll.Module] = None
        self._compiled: bool = False
        
        # 初始化 LLVM
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
    
    def compile(self, ir: IRProgram, module_name: str = "zhc_jit_module"):
        """编译 ZhC IR
        
        Args:
            ir: ZhC IR 程序
            module_name: 模块名称
        """
        from zhc.backend.llvm_backend import LLVMBackend
        
        # 使用 LLVMBackend 编译
        backend = LLVMBackend()
        self._module = backend.compile(ir, module_name)
        
        # 解析 IR
        llvm_ir = str(self._module)
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()
        
        # 创建执行引擎
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine(
            opt=self.opt_level
        )
        
        # 创建模块提供者
        backing_mod = llvm.parse_assembly(str(self._module))
        
        # 创建执行引擎
        self._execution_engine = llvm.create_mcjit_compiler(
            backing_mod, target_machine
        )
        
        # JIT 编译
        self._execution_engine.finalize_object()
        
        self._compiled = True
    
    def get_function(self, name: str) -> Callable:
        """获取 JIT 编译的函数
        
        Args:
            name: 函数名
            
        Returns:
            可调用的函数
        """
        if not self._compiled or not self._execution_engine:
            raise JITError("尚未编译")
        
        # 获取函数地址
        func_ptr = self._execution_engine.get_function_address(name)
        
        # 创建 Python 包装器
        return self._create_python_wrapper(func_ptr, name)
    
    def _create_python_wrapper(self, func_ptr: int, name: str) -> Callable:
        """创建 Python 函数包装器
        
        Args:
            func_ptr: 函数指针
            name: 函数名
            
        Returns:
            Python 可调用函数
        """
        import ctypes
        
        # 简化处理：假设函数接受 i32 参数并返回 i32
        func_type = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)
        func = func_type(func_ptr)
        
        def wrapper(*args):
            """包装函数"""
            # 转换参数
            if len(args) == 0:
                return func(0)
            elif len(args) == 1:
                return func(ctypes.c_int32(args[0]))
            else:
                # 简化处理：只支持单参数
                raise JITError(f"不支持 {len(args)} 个参数")
        
        wrapper.__name__ = name
        return wrapper
    
    def call(self, name: str, *args) -> Any:
        """调用 JIT 编译的函数
        
        Args:
            name: 函数名
            *args: 参数
            
        Returns:
            函数返回值
        """
        func = self.get_function(name)
        return func(*args)
    
    def execute_main(self, *args) -> int:
        """执行 main 函数
        
        Args:
            *args: 参数
            
        Returns:
            返回值
        """
        return self.call("main", *args)
    
    def get_llvm_ir(self) -> str:
        """获取 LLVM IR 文本
        
        Returns:
            LLVM IR 字符串
        """
        if self._module:
            return str(self._module)
        return ""


class LLVMJITRunner:
    """LLVM JIT 运行器
    
    提供更高级的 JIT 执行功能。
    """
    
    def __init__(self):
        """初始化运行器"""
        if not LLVM_AVAILABLE:
            raise JITError("llvmlite 未安装")
        
        self.jit = LLVMJIT()
        self._functions: Dict[str, Callable] = {}
    
    def load_ir(self, ir: IRProgram):
        """加载 IR 程序
        
        Args:
            ir: ZhC IR 程序
        """
        self.jit.compile(ir)
        
        # 预加载所有函数
        for func in ir.functions:
            try:
                self._functions[func.name] = self.jit.get_function(func.name)
            except Exception:
                pass  # 忽略无法加载的函数
    
    def call(self, name: str, *args) -> Any:
        """调用函数
        
        Args:
            name: 函数名
            *args: 参数
            
        Returns:
            函数返回值
        """
        if name in self._functions:
            return self._functions[name](*args)
        
        return self.jit.call(name, *args)
    
    def list_functions(self) -> List[str]:
        """列出所有可用函数
        
        Returns:
            函数名列表
        """
        return list(self._functions.keys())


def jit_compile_and_run(ir: IRProgram, func_name: str = "main", 
                        *args) -> Any:
    """便捷函数：JIT 编译并执行
    
    Args:
        ir: ZhC IR 程序
        func_name: 函数名
        *args: 参数
        
    Returns:
        函数返回值
    """
    jit = LLVMJIT()
    jit.compile(ir)
    return jit.call(func_name, *args)


def create_jit_runner(ir: IRProgram) -> LLVMJITRunner:
    """便捷函数：创建 JIT 运行器
    
    Args:
        ir: ZhC IR 程序
        
    Returns:
        JIT 运行器
    """
    runner = LLVMJITRunner()
    runner.load_ir(ir)
    return runner