# -*- coding: utf-8 -*-
"""
M5: test_ir_optimizer.py - IR 优化 Pass 测试

运行：
    python -m pytest tests/test_ir_optimizer.py -v
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.ir import IRProgram, IRFunction, Opcode, IRValue, ValueKind
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.optimizer import ConstantFolding, DeadCodeElimination, PassManager


class TestConstantFolding(unittest.TestCase):
    """常量折叠测试"""

    def test_add_two_consts(self):
        """1 + 2 -> 3"""
        from zhc.ir.optimizer import ConstantFolding
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = func.entry_block

        a = IRValue("1", "整数型", ValueKind.CONST, const_value=1)
        b = IRValue("2", "整数型", ValueKind.CONST, const_value=2)
        res = IRValue("%0", "整数型", ValueKind.TEMP)
        bb.add_instruction(IRInstruction(Opcode.ADD, [a, b], [res]))
        ir.add_function(func)

        opt = ConstantFolding()
        opt.run(ir)

        # ADD 应该被替换为 CONST
        const_instrs = [i for i in bb.instructions if i.opcode == Opcode.CONST]
        self.assertGreater(len(const_instrs), 0)

    def test_no_fold_with_vars(self):
        """变量不能折叠"""
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = func.entry_block

        a = IRValue("x", "整数型", ValueKind.VAR)
        b = IRValue("y", "整数型", ValueKind.VAR)
        res = IRValue("%0", "整数型", ValueKind.TEMP)
        bb.add_instruction(IRInstruction(Opcode.ADD, [a, b], [res]))
        ir.add_function(func)

        opt = ConstantFolding()
        opt.run(ir)

        # ADD 保留（变量不能折叠）
        add_instrs = [i for i in bb.instructions if i.opcode == Opcode.ADD]
        self.assertEqual(len(add_instrs), 1)


class TestDeadCodeElimination(unittest.TestCase):
    """死代码消除测试"""

    def test_remove_unreachable_block(self):
        """删除不可达基本块"""
        ir = IRProgram()
        func = IRFunction("test", "整数型")

        bb1 = IRBasicBlock("entry")
        bb2 = IRBasicBlock("dead")
        bb1.add_successor("dead")
        # bb2 没有前驱可达

        func.basic_blocks.append(bb1)
        func.basic_blocks.append(bb2)
        ir.add_function(func)

        opt = DeadCodeElimination()
        opt.run(ir)

        # dead 块应该被删除
        labels = {bb.label for bb in func.basic_blocks}
        self.assertIn("entry", labels)
        self.assertNotIn("dead", labels)


class TestPassManager(unittest.TestCase):
    """PassManager 测试"""

    def test_register_and_run(self):
        """注册并执行多个 Pass"""
        pm = PassManager()
        pm.register(ConstantFolding())
        pm.register(DeadCodeElimination())

        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = func.entry_block
        ir.add_function(func)

        result = pm.run(ir)
        self.assertIsInstance(result, IRProgram)

    def test_chaining(self):
        """链式调用"""
        pm = PassManager()
        pm.register(ConstantFolding()).register(DeadCodeElimination())
        self.assertEqual(len(pm.passes), 2)


if __name__ == "__main__":
    unittest.main()
