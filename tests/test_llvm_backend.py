# -*- coding: utf-8 -*-
"""LLVM Backend 测试

测试 LLVMPrinter 的基本功能。

作者：远
日期：2026-04-08
"""

import pytest
from zhc.ir.program import IRProgram, IRFunction, IRGlobalVar
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode
from zhc.ir.llvm_backend import LLVMPrinter


class TestLLVMPrinter:
    """LLVMPrinter 测试"""

    def test_llvm_printer_creation(self):
        """测试 LLVMPrinter 创建"""
        printer = LLVMPrinter()
        assert printer.lines == []

    def test_empty_program(self):
        """测试空程序"""
        printer = LLVMPrinter()
        ir = IRProgram()
        result = printer.print(ir)
        assert "; ZHC IR → LLVM IR" in result
        assert "source_filename = \"zhc_module\"" in result

    def test_simple_function(self):
        """测试简单函数"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        # 创建简单函数
        func = IRFunction(name="test_func", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["42"]))
        func.basic_blocks.append(bb)
        ir.functions.append(func)
        
        result = printer.print(ir)
        assert "define i32 @test_func()" in result
        assert "entry:" in result
        assert "ret 42" in result

    def test_arithmetic_instruction(self):
        """测试算术指令"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        func = IRFunction(name="add_func", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        
        # ADD 指令
        add_instr = IRInstruction(
            opcode=Opcode.ADD,
            operands=["%a", "%b"],
            result=["%c"]
        )
        bb.instructions.append(add_instr)
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["%c"]))
        
        func.basic_blocks.append(bb)
        ir.functions.append(func)
        
        result = printer.print(ir)
        assert "add i32 %a, %b" in result
        assert "%c = add i32 %a, %b" in result

    def test_comparison_instruction(self):
        """测试比较指令"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        func = IRFunction(name="cmp_func", return_type="布尔型")
        bb = IRBasicBlock(label="entry")
        
        # EQ 指令
        cmp_instr = IRInstruction(
            opcode=Opcode.EQ,
            operands=["%a", "%b"],
            result=["%result"]
        )
        bb.instructions.append(cmp_instr)
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["%result"]))
        
        func.basic_blocks.append(bb)
        ir.functions.append(func)
        
        result = printer.print(ir)
        assert "icmp eq i32 %a, %b" in result
        assert "%result = icmp eq i32 %a, %b" in result

    def test_global_variable(self):
        """测试全局变量"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        # 创建全局变量
        gv = IRGlobalVar(name="global_var", ty="整数型")
        ir.global_vars.append(gv)
        
        result = printer.print(ir)
        assert "@global_var = global i32 zeroinitializer" in result

    def test_branch_instruction(self):
        """测试分支指令"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        func = IRFunction(name="branch_func", return_type="整数型")
        
        # Entry block
        entry = IRBasicBlock(label="entry")
        entry.instructions.append(IRInstruction(opcode=Opcode.JMP, operands=["target"]))
        func.basic_blocks.append(entry)
        
        # Target block
        target = IRBasicBlock(label="target")
        target.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["42"]))
        func.basic_blocks.append(target)
        
        ir.functions.append(func)
        
        result = printer.print(ir)
        assert "br label %target" in result

    def test_conditional_branch(self):
        """测试条件分支"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        func = IRFunction(name="cond_branch_func", return_type="整数型")
        
        # Entry block
        entry = IRBasicBlock(label="entry")
        entry.instructions.append(
            IRInstruction(opcode=Opcode.JZ, operands=["%cond", "then"])
        )
        func.basic_blocks.append(entry)
        
        # Then block
        then = IRBasicBlock(label="then")
        then.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["1"]))
        func.basic_blocks.append(then)
        
        ir.functions.append(func)
        
        result = printer.print(ir)
        assert "br i1 %cond, label %then" in result

    def test_call_instruction(self):
        """测试函数调用"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        func = IRFunction(name="caller", return_type="整数型")
        bb = IRBasicBlock(label="entry")
        
        # CALL 指令
        call_instr = IRInstruction(
            opcode=Opcode.CALL,
            operands=["callee", "%arg1", "%arg2"],
            result=["%result"]
        )
        bb.instructions.append(call_instr)
        bb.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["%result"]))
        
        func.basic_blocks.append(bb)
        ir.functions.append(func)
        
        result = printer.print(ir)
        assert "call i32 @callee(%arg1, %arg2)" in result
        assert "%result = call i32 @callee(%arg1, %arg2)" in result

    def test_type_mapping(self):
        """测试类型映射"""
        from zhc.ir.llvm_backend import _llvm_type
        
        assert _llvm_type("整数型") == "i32"
        assert _llvm_type("浮点型") == "float"
        assert _llvm_type("双精度浮点型") == "double"
        assert _llvm_type("字符型") == "i8"
        assert _llvm_type("布尔型") == "i1"
        assert _llvm_type("空型") == "void"
        assert _llvm_type("i64") == "i64"
        assert _llvm_type("unknown") == "i32"  # 默认类型


class TestLLVMPrinterIntegration:
    """LLVMPrinter 集成测试"""

    def test_complete_program(self):
        """测试完整程序"""
        printer = LLVMPrinter()
        ir = IRProgram()
        
        # 全局变量
        ir.global_vars.append(IRGlobalVar(name="counter", ty="整数型"))
        
        # 主函数
        main = IRFunction(name="main", return_type="整数型")
        
        # Entry block
        entry = IRBasicBlock(label="entry")
        entry.instructions.append(
            IRInstruction(opcode=Opcode.ALLOC, operands=["整数型"], result=["%x"])
        )
        entry.instructions.append(
            IRInstruction(opcode=Opcode.STORE, operands=["10", "%x"])
        )
        entry.instructions.append(
            IRInstruction(opcode=Opcode.LOAD, operands=["%x"], result=["%val"])
        )
        entry.instructions.append(IRInstruction(opcode=Opcode.RET, operands=["%val"]))
        
        main.basic_blocks.append(entry)
        ir.functions.append(main)
        
        result = printer.print(ir)
        
        # 验证输出
        assert "@counter = global i32 zeroinitializer" in result
        assert "define i32 @main()" in result
        assert "entry:" in result
        assert "alloca i32" in result
        assert "store 10" in result
        assert "load i32" in result
        assert "ret %val" in result