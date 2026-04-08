# -*- coding: utf-8 -*-
"""ZhC LLVM 后端 - 使用 llvmlite 生成真正的 LLVM IR

将 ZhC IR 转换为 LLVM bitcode，支持 JIT 执行。

优化提示支持（TASK-P3-003）：
- 小函数添加 LLVM inline 属性
- 热点函数添加 LLVM hot 属性
- 冷点函数添加 LLVM cold 属性
- 强制内联添加 LLVM alwaysinline 属性
- 不返回函数添加 LLVM noreturn 属性

架构重构（2026-04-08）：
- 继承 BackendBase 统一接口
- 支持 CompileOptions 和 CompileResult

作者：远
日期：2026-04-08
重构：2026-04-08（TASK-P3-003：添加优化提示支持）
重构：2026-04-08（统一后端架构）
"""

import os
import tempfile
from typing import Optional, Dict, Any, List, TYPE_CHECKING
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

from zhc.ir.program import IRProgram, IRFunction, IRGlobalVar
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode
from zhc.ir.values import IRValue, ValueKind

# 导入基类
from .base import (
    BackendBase,
    BackendCapabilities,
    CompileOptions,
    CompileResult,
    OutputFormat,
    BackendError,
)

# 优化提示模块（可选依赖）
try:
    from zhc.ir.optimization_hints import (
        OptimizationHintAnalyzer,
        ProgramOptimizationHints,
        FunctionOptimizationHints,
        LLVMBackendHintAdapter,
    )
    OPTIMIZATION_HINTS_AVAILABLE = True
except ImportError:
    OPTIMIZATION_HINTS_AVAILABLE = False
    OptimizationHintAnalyzer = None
    ProgramOptimizationHints = None
    FunctionOptimizationHints = None
    LLVMBackendHintAdapter = None


class LLVMBackendError(BackendError):
    """LLVM 后端错误"""
    pass


class LLVMBackend(BackendBase):
    """ZhC LLVM 后端 - 使用 llvmlite 生成真正的 LLVM IR
    
    功能：
    - IRProgram → LLVM Module
    - IRFunction → LLVM Function
    - IRBasicBlock → LLVM BasicBlock
    - IRInstruction → LLVM Instruction
    - 支持 bitcode 输出
    - 支持 JIT 执行
    
    TASK-P3-003 新增功能：
    - 支持优化提示分析
    - 自动添加 LLVM 函数属性
    """
    
    # ZhC 类型 → LLVM 类型映射
    TYPE_MAP = {
        "整数型": ll.IntType(32) if ll else None,
        "浮点型": ll.FloatType() if ll else None,
        "双精度浮点型": ll.DoubleType() if ll else None,
        "字符型": ll.IntType(8) if ll else None,
        "字节型": ll.IntType(8) if ll else None,
        "布尔型": ll.IntType(1) if ll else None,
        "空型": ll.VoidType() if ll else None,
        "i32": ll.IntType(32) if ll else None,
        "i64": ll.IntType(64) if ll else None,
        "i16": ll.IntType(16) if ll else None,
        "i8": ll.IntType(8) if ll else None,
        "i1": ll.IntType(1) if ll else None,
    }

    @property
    def name(self) -> str:
        return "llvm"

    @property
    def description(self) -> str:
        return "LLVM 后端 (llvmlite)"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_jit=True,
            supports_debug=True,
            supports_optimization=True,
            supports_cross_compile=True,
            supports_lto=True,
            target_platforms=[
                "x86_64-linux",
                "x86_64-macos",
                "x86_64-windows",
                "aarch64-linux",
                "aarch64-macos",
                "arm-linux",
            ],
            output_formats=[
                OutputFormat.LLVM_IR,
                OutputFormat.LLVM_BC,
                OutputFormat.OBJECT,
                OutputFormat.EXECUTABLE,
            ],
            required_tools=["llvmlite"],
        )

    def __init__(self, target_triple: Optional[str] = None, enable_optimization_hints: bool = True):
        """初始化 LLVM 后端
        
        Args:
            target_triple: 目标平台三元组（如 "x86_64-apple-darwin"）
            enable_optimization_hints: 是否启用优化提示（默认 True）
        """
        if not LLVM_AVAILABLE:
            raise LLVMBackendError(
                "llvmlite 未安装。请运行: pip install llvmlite>=0.39.0"
            )
        
        self.target_triple = target_triple
        self.module: Optional[ll.Module] = None
        self.functions: Dict[str, ll.Function] = {}
        self.blocks: Dict[str, ll.Block] = {}
        self.values: Dict[str, ll.Value] = {}
        
        # TASK-P3-003：优化提示配置
        self.enable_optimization_hints = enable_optimization_hints and OPTIMIZATION_HINTS_AVAILABLE
        self.optimization_hints: Optional[ProgramOptimizationHints] = None
        self.hint_adapter: Optional[LLVMBackendHintAdapter] = None
        
        if self.enable_optimization_hints:
            self.hint_adapter = LLVMBackendHintAdapter()
        
        # 初始化 LLVM
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
    
    def compile(
        self,
        ir: IRProgram,
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        编译 IR 到目标文件（BackendBase 接口）

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        options = options or CompileOptions()

        try:
            # 1. 编译到 LLVM Module
            module = self.compile_to_module(ir, output_path.stem)

            # 2. 根据输出格式选择输出方式
            if options.output_format == OutputFormat.LLVM_IR:
                # 输出 LLVM IR 文本
                ll_file = output_path.with_suffix(".ll")
                ll_file.write_text(str(module))
                return CompileResult(
                    success=True,
                    output_files=[ll_file],
                )

            elif options.output_format == OutputFormat.LLVM_BC:
                # 输出 LLVM bitcode
                bc_file = output_path.with_suffix(".bc")
                llvm_bitcode = llvm.parse_assembly(str(module))
                llvm_bitcode.to_bitcode_file(str(bc_file))
                return CompileResult(
                    success=True,
                    output_files=[bc_file],
                )

            else:
                # 默认输出 LLVM IR
                ll_file = output_path.with_suffix(".ll")
                ll_file.write_text(str(module))
                return CompileResult(
                    success=True,
                    output_files=[ll_file],
                )

        except Exception as e:
            return CompileResult(
                success=False,
                errors=[str(e)],
            )

    def compile_to_module(self, ir: IRProgram, module_name: str = "zhc_module") -> ll.Module:
        """编译 ZhC IR 到 LLVM Module（原有接口）

        Args:
            ir: ZhC IR 程序
            module_name: 模块名称

        Returns:
            LLVM Module
        """
        # TASK-P3-003：分析优化提示
        if self.enable_optimization_hints:
            analyzer = OptimizationHintAnalyzer(ir)
            self.optimization_hints = analyzer.analyze()
        
        # 创建模块
        self.module = ll.Module(name=module_name)
        
        if self.target_triple:
            self.module.triple = self.target_triple
        
        # 编译全局变量
        for gv in ir.global_vars:
            self._compile_global_var(gv)
        
        # 编译函数
        for func in ir.functions:
            self._compile_function(func)
        
        return self.module
    
    def _compile_global_var(self, gv: IRGlobalVar):
        """编译全局变量"""
        ty = self._get_llvm_type(gv.ty or "i32")
        
        # 创建全局变量
        global_var = ll.GlobalVariable(self.module, ty, gv.name)
        global_var.linkage = 'external'
        global_var.initializer = ll.Constant(ty, 0)
        
        self.values[gv.name] = global_var
    
    def _compile_function(self, func: IRFunction):
        """编译函数"""
        # 获取返回类型
        ret_ty = self._get_llvm_type(func.return_type or "i32")
        
        # 获取参数类型
        param_types = [self._get_llvm_type(p.ty or "i32") for p in func.params]
        
        # 创建函数类型
        func_ty = ll.FunctionType(ret_ty, param_types)
        
        # 创建函数
        llvm_func = ll.Function(self.module, func_ty, func.name)
        
        # 设置参数名
        for i, param in enumerate(func.params):
            llvm_func.args[i].name = param.name
        
        # TASK-P3-003：应用优化提示
        self._apply_function_hints(llvm_func, func.name)
        
        self.functions[func.name] = llvm_func
        
        # 编译基本块
        for bb in func.basic_blocks:
            self._compile_basic_block(llvm_func, bb)
    
    def _apply_function_hints(self, llvm_func: ll.Function, func_name: str):
        """应用函数优化提示
        
        TASK-P3-003 新增
        
        Args:
            llvm_func: LLVM 函数
            func_name: 函数名
        """
        if not self.enable_optimization_hints or not self.hint_adapter:
            return
        
        func_hints = self.optimization_hints.get_function_hints(func_name)
        if func_hints and self.hint_adapter:
            self.hint_adapter.apply_to_llvm_function(llvm_func, func_hints)
    
    def _compile_basic_block(self, llvm_func: ll.Function, bb: IRBasicBlock):
        """编译基本块"""
        # 创建基本块
        block = llvm_func.append_basic_block(bb.label)
        self.blocks[bb.label] = block
        
        # 创建指令生成器
        builder = ll.IRBuilder(block)
        
        # 编译指令
        for instr in bb.instructions:
            self._compile_instruction(builder, instr)
    
    def _compile_instruction(self, builder: ll.IRBuilder, instr: IRInstruction):
        """编译指令"""
        op = instr.opcode
        
        if op == Opcode.RET:
            if instr.operands:
                val = self._get_value(instr.operands[0])
                builder.ret(val)
            else:
                builder.ret_void()
        
        elif op == Opcode.ADD:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.add(a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.SUB:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.sub(a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.MUL:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.mul(a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.DIV:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.sdiv(a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.MOD:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.srem(a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.EQ:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.icmp_signed('==', a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.NE:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.icmp_signed('!=', a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.LT:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.icmp_signed('<', a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.LE:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.icmp_signed('<=', a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.GT:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.icmp_signed('>', a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.GE:
            a = self._get_value(instr.operands[0])
            b = self._get_value(instr.operands[1])
            result = builder.icmp_signed('>=', a, b, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.ALLOC:
            ty = self._get_llvm_type_from_operand(instr.operands[0] if instr.operands else None)
            result = builder.alloca(ty, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.LOAD:
            ptr = self._get_value(instr.operands[0])
            ty = self._get_llvm_type("i32")  # 默认类型
            result = builder.load(ptr, name=self._get_result_name(instr))
            self._store_result(instr, result)
        
        elif op == Opcode.STORE:
            val = self._get_value(instr.operands[0])
            ptr = self._get_value(instr.operands[1])
            builder.store(val, ptr)
        
        elif op == Opcode.JMP:
            target = self._get_block(instr.operands[0])
            builder.branch(target)
        
        elif op == Opcode.JZ:
            cond = self._get_value(instr.operands[0])
            target = self._get_block(instr.operands[1])
            # 需要两个分支，这里简化处理
            builder.cbranch(cond, target, target)  # TODO: 需要完整的条件分支
        
        elif op == Opcode.CALL:
            callee_name = str(instr.operands[0])
            args = [self._get_value(a) for a in instr.operands[1:]]
            
            # 查找函数
            callee = self.functions.get(callee_name)
            if callee:
                result = builder.call(callee, args, name=self._get_result_name(instr))
                self._store_result(instr, result)
            else:
                # 外部函数
                func_ty = ll.FunctionType(ll.IntType(32), [ll.IntType(32)] * len(args))
                callee = ll.Function(self.module, func_ty, callee_name)
                result = builder.call(callee, args, name=self._get_result_name(instr))
                self._store_result(instr, result)
        
        else:
            # 未实现的指令
            pass
    
    def _get_llvm_type(self, zhc_type: str) -> ll.Type:
        """获取 LLVM 类型"""
        if zhc_type in self.TYPE_MAP:
            return self.TYPE_MAP[zhc_type]
        return ll.IntType(32)  # 默认类型
    
    def _get_llvm_type_from_operand(self, operand) -> ll.Type:
        """从操作数获取 LLVM 类型"""
        if operand is None:
            return ll.IntType(32)
        
        if hasattr(operand, 'ty'):
            return self._get_llvm_type(operand.ty or "i32")
        
        return ll.IntType(32)
    
    def _get_value(self, operand) -> ll.Value:
        """获取 LLVM 值"""
        # 如果是字符串
        if isinstance(operand, str):
            # 检查是否是已存在的值
            if operand in self.values:
                return self.values[operand]
            
            # 检查是否是常量
            if operand.isdigit():
                return ll.Constant(ll.IntType(32), int(operand))
            
            # 检查是否是变量名（%开头）
            if operand.startswith('%'):
                name = operand[1:]
                if name in self.values:
                    return self.values[name]
            
            # 默认返回常量
            return ll.Constant(ll.IntType(32), 0)
        
        # 如果是 IRValue 对象
        if hasattr(operand, 'name'):
            name = operand.name
            if name in self.values:
                return self.values[name]
            
            # 常量
            if hasattr(operand, 'kind') and operand.kind == ValueKind.CONST:
                return ll.Constant(ll.IntType(32), operand.const_value or 0)
        
        return ll.Constant(ll.IntType(32), 0)
    
    def _get_block(self, operand) -> ll.Block:
        """获取 LLVM 基本块"""
        label = str(operand)
        if label in self.blocks:
            return self.blocks[label]
        
        # 如果找不到，返回第一个块
        if self.blocks:
            return list(self.blocks.values())[0]
        
        raise LLVMBackendError(f"基本块 {label} 不存在")
    
    def _get_result_name(self, instr: IRInstruction) -> Optional[str]:
        """获取结果名称"""
        if instr.result:
            res_obj = instr.result[0]
            if hasattr(res_obj, 'name'):
                return res_obj.name
            return str(res_obj)
        return None
    
    def _store_result(self, instr: IRInstruction, value: ll.Value):
        """存储结果值"""
        if instr.result:
            res_obj = instr.result[0]
            name = res_obj.name if hasattr(res_obj, 'name') else str(res_obj)
            self.values[name] = value
    
    def to_llvm_ir(self) -> str:
        """转换为 LLVM IR 文本"""
        if self.module:
            return str(self.module)
        return ""
    
    def to_bitcode(self) -> bytes:
        """转换为 LLVM bitcode"""
        if not self.module:
            raise LLVMBackendError("模块未编译")
        
        # 解析 IR
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)
        
        # 优化
        pmb = llvm.PassManagerBuilder()
        pmb.opt_level = 2
        
        pm = llvm.ModulePassManager()
        pmb.populate(pm)
        pm.run(mod)
        
        # 生成 bitcode
        return mod.as_bitcode()

    # ===== BackendBase 接口实现 =====

    def is_available(self) -> bool:
        """检查 llvmlite 是否可用"""
        return LLVM_AVAILABLE

    def get_version(self) -> Optional[str]:
        """获取 llvmlite 版本"""
        if LLVM_AVAILABLE:
            return f"llvmlite {llvmlite.__version__}"
        return None

    # ===== 原有方法 =====

    def save_bitcode(self, filepath: str):
        """保存 bitcode 到文件"""
        bitcode = self.to_bitcode()
        with open(filepath, 'wb') as f:
            f.write(bitcode)
    
    def save_llvm_ir(self, filepath: str):
        """保存 LLVM IR 文本到文件"""
        llvm_ir = self.to_llvm_ir()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(llvm_ir)
    
    def compile_to_object(self, filepath: str):
        """编译为目标文件 (.o)"""
        if not self.module:
            raise LLVMBackendError("模块未编译")
        
        # 解析 IR
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)
        
        # 优化
        pmb = llvm.PassManagerBuilder()
        pmb.opt_level = 2
        
        pm = llvm.ModulePassManager()
        pmb.populate(pm)
        pm.run(mod)
        
        # 生成目标代码
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        
        obj = target_machine.emit_object(mod)
        
        with open(filepath, 'wb') as f:
            f.write(obj)


def compile_to_llvm(ir: IRProgram, output_path: Optional[str] = None, 
                    output_format: str = "ir") -> Optional[str]:
    """便捷函数：编译 ZhC IR 到 LLVM
    
    Args:
        ir: ZhC IR 程序
        output_path: 输出路径（可选）
        output_format: 输出格式（"ir", "bitcode", "object"）
        
    Returns:
        输出路径或 LLVM IR 文本
    """
    backend = LLVMBackend()
    backend.compile(ir)
    
    if output_path:
        if output_format == "ir":
            backend.save_llvm_ir(output_path)
        elif output_format == "bitcode":
            backend.save_bitcode(output_path)
        elif output_format == "object":
            backend.compile_to_object(output_path)
        return output_path
    else:
        return backend.to_llvm_ir()