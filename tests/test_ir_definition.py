# -*- coding: utf-8 -*-
"""
M1: test_ir_definition.py - IR 数据结构定义测试

运行：
    python -m pytest tests/test_ir_definition.py -v
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.ir import (
    Opcode, IRValue, ValueKind, IRInstruction, IRBasicBlock,
    IRProgram, IRFunction, IRGlobalVar, IRStructDef, IRPrinter
)


class TestOpcode(unittest.TestCase):
    """Opcode 枚举测试"""

    def test_opcode_count(self):
        """Opcode 数量 >= 35"""
        self.assertGreaterEqual(len(list(Opcode)), 35)

    def test_all_opcodes_have_category(self):
        """所有 Opcode 有 category"""
        for op in Opcode:
            self.assertIsNotNone(op.category)

    def test_all_opcodes_have_chinese(self):
        """所有 Opcode 有 chinese 名称"""
        for op in Opcode:
            self.assertIsNotNone(op.chinese)

    def test_terminators(self):
        """终止指令标记正确"""
        terminators = [Opcode.JMP, Opcode.JZ, Opcode.RET, Opcode.SWITCH]
        for op in terminators:
            self.assertTrue(op.is_terminator, f"{op.name} 应该是终止指令")

    def test_has_result(self):
        """结果标记正确"""
        # 有结果的指令
        result_ops = [Opcode.ALLOC, Opcode.LOAD, Opcode.ADD, Opcode.CALL]
        for op in result_ops:
            self.assertTrue(op.has_result, f"{op.name} 应该 has_result")

    def test_categories(self):
        """所有类别都存在"""
        categories = {"算术", "比较", "位运算", "逻辑", "内存", "控制流", "转换", "其他"}
        found = {op.category for op in Opcode}
        self.assertEqual(categories, found & categories)


class TestIRValue(unittest.TestCase):
    """IRValue 测试"""

    def test_create_var(self):
        """创建变量值"""
        v = IRValue("x", "整数型", ValueKind.VAR)
        self.assertEqual(v.name, "x")
        self.assertEqual(v.ty, "整数型")
        self.assertEqual(v.kind, ValueKind.VAR)

    def test_create_temp(self):
        """创建临时变量"""
        v = IRValue("%0", "整数型", ValueKind.TEMP)
        self.assertTrue(v.name.startswith("%"))

    def test_create_const(self):
        """创建常量"""
        v = IRValue("42", "整数型", ValueKind.CONST, const_value=42)
        self.assertEqual(v.const_value, 42)


class TestIRBasicBlock(unittest.TestCase):
    """IRBasicBlock 测试"""

    def test_create(self):
        bb = IRBasicBlock("entry")
        self.assertEqual(bb.label, "entry")
        self.assertEqual(len(bb.instructions), 0)

    def test_add_instruction(self):
        bb = IRBasicBlock("test")
        instr = IRInstruction(Opcode.ADD)
        bb.add_instruction(instr)
        self.assertEqual(len(bb.instructions), 1)

    def test_is_terminated_false_empty(self):
        """空基本块不是终止"""
        bb = IRBasicBlock("empty")
        self.assertFalse(bb.is_terminated())

    def test_is_terminated_true(self):
        """RET 终止基本块"""
        bb = IRBasicBlock("test")
        bb.add_instruction(IRInstruction(Opcode.RET))
        self.assertTrue(bb.is_terminated())

    def test_predecessors(self):
        bb = IRBasicBlock("test")
        bb.add_predecessor("entry")
        bb.add_predecessor("entry")  # 重复
        self.assertEqual(len(bb.predecessors), 1)
        self.assertIn("entry", bb.predecessors)

    def test_successors(self):
        bb = IRBasicBlock("test")
        bb.add_successor("next")
        self.assertIn("next", bb.successors)


class TestIRFunction(unittest.TestCase):
    """IRFunction 测试"""

    def test_create(self):
        func = IRFunction("foo", "整数型")
        self.assertEqual(func.name, "foo")
        self.assertEqual(func.return_type, "整数型")

    def test_entry_block_empty(self):
        """默认创建 entry 基本块"""
        func = IRFunction("foo")
        self.assertIsNotNone(func.entry_block)
        self.assertEqual(func.entry_block.label, "entry")

    def test_add_basic_blocks(self):
        func = IRFunction("foo")
        bb = func.add_basic_block("loop")
        self.assertEqual(len(func.basic_blocks), 2)  # entry + loop
        self.assertEqual(bb.label, "loop")

    def test_find_function(self):
        func = IRFunction("bar")
        program = IRProgram()
        program.add_function(func)
        found = program.find_function("bar")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "bar")

    def test_find_function_not_found(self):
        program = IRProgram()
        found = program.find_function("nonexistent")
        self.assertIsNone(found)


class TestIRProgram(unittest.TestCase):
    """IRProgram 测试"""

    def test_create_empty(self):
        program = IRProgram()
        self.assertEqual(len(program.functions), 0)
        self.assertEqual(len(program.global_vars), 0)
        self.assertEqual(len(program.structs), 0)

    def test_add_function(self):
        func = IRFunction("test")
        program = IRProgram()
        program.add_function(func)
        self.assertEqual(len(program.functions), 1)

    def test_add_global(self):
        gv = IRGlobalVar("x", "整数型")
        program = IRProgram()
        program.add_global(gv)
        self.assertEqual(len(program.global_vars), 1)


class TestIRPrinter(unittest.TestCase):
    """IRPrinter 测试"""

    def test_print_empty_program(self):
        program = IRProgram()
        printer = IRPrinter()
        output = printer.print(program)
        self.assertIsInstance(output, str)

    def test_print_function(self):
        program = IRProgram()
        func = IRFunction("主函数", "整数型")
        program.add_function(func)

        printer = IRPrinter()
        output = printer.print(program)
        self.assertIn("主函数", output)
        self.assertIn("define", output)


if __name__ == "__main__":
    unittest.main()
