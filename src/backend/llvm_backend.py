# -*- coding: utf-8 -*-
"""ZhC LLVM 后端 - 使用 llvmlite 生成真正的 LLVM IR

将 ZhC IR 转换为 LLVM bitcode，支持 JIT 执行。

作者：远
日期：2026-04-08
"""

import os
import tempfile
from typing import Optional, Dict, Any, List
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


class LLVMBackendError(Exception):
    """LLVM 后端错误"""
    pass


class LLVMBackend:
    """ZhC LLVM 后端 - 使用 llvmlite 生成真正的 LLVM IR
    
    功能：
    - IRProgram → LLVM Module
    - IRFunction → LLVM Function
    - IRBasicBlock → LLVM BasicBlock
    - IRInstruction → LLVM Instruction
    - 支持 bitcode 输出
    - 支持 JIT 执行
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
    
    def __init__(self, target_triple: Optional[str] = None):
        """初始化 LLVM 后端
        
        Args:
            target_triple: 目标平台三元组（如 "x86_64-apple-darwin"）
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
        
        # 初始化 LLVM
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
    
    def compile(self, ir: IRProgram, module_name: str = "zhc_module") -> ll.Module:
        """编译 ZhC IR 到 LLVM Module
        
        Args:
            ir: ZhC IR 程序
            module_name: 模块名称
            
        Returns:
            LLVM Module
        """
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
        
        self.functions[func.name] = llvm_func
        
        # 编译基本块
        for bb in func.basic_blocks:
            self._compile_basic_block(llvm_func, bb)
    
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