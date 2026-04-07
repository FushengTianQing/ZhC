# -*- coding: utf-8 -*-
"""
M3: test_c_backend.py - IR→C 后端测试

运行：
    python -m pytest tests/test_c_backend.py -v
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.ir import IRProgram, IRFunction, IRGlobalVar, Opcode, IRValue, ValueKind
from zhc.ir.c_backend import CBackend


class TestCBackendBasics(unittest.TestCase):
    """CBackend 基础测试"""

    def test_empty_function(self):
        """空函数"""
        backend = CBackend()
        ir = IRProgram()
        func = IRFunction("main", "整数型")
        ir.add_function(func)
        code = backend.generate(ir)
        self.assertIn("int main()", code)
        self.assertIn("{", code)
        self.assertIn("}", code)

    def test_global_var(self):
        """全局变量"""
        backend = CBackend()
        ir = IRProgram()
        gv = IRGlobalVar("x", "整数型")
        ir.add_global(gv)
        code = backend.generate(ir)
        self.assertIn("int x;", code)

    def test_alloc_instruction(self):
        """ALLOC 指令"""
        backend = CBackend()
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = func.entry_block
        # 添加 ALLOC 指令
        from zhc.ir.instructions import IRInstruction
        var = IRValue("x", "整数型", ValueKind.VAR)
        res = IRValue("%0", "整数型", ValueKind.TEMP)
        bb.add_instruction(IRInstruction(Opcode.ALLOC, [var], [res]))
        ir.add_function(func)
        code = backend.generate(ir)
        self.assertIn("int x;", code)

    def test_binary_op(self):
        """二元运算"""
        backend = CBackend()
        ir = IRProgram()
        func = IRFunction("add", "整数型")
        bb = func.entry_block
        from zhc.ir.instructions import IRInstruction
        a = IRValue("a", "整数型", ValueKind.VAR)
        b = IRValue("b", "整数型", ValueKind.VAR)
        res = IRValue("%0", "整数型", ValueKind.TEMP)
        bb.add_instruction(IRInstruction(Opcode.ALLOC, [IRValue("a", "整数型", ValueKind.VAR)], [IRValue("%t0", "整数型", ValueKind.TEMP)]))
        bb.add_instruction(IRInstruction(Opcode.ALLOC, [IRValue("b", "整数型", ValueKind.VAR)], [IRValue("%t1", "整数型", ValueKind.TEMP)]))
        bb.add_instruction(IRInstruction(Opcode.ADD, [a, b], [res]))
        ir.add_function(func)
        code = backend.generate(ir)
        self.assertIn("a + b", code)

    def test_call(self):
        """函数调用"""
        backend = CBackend()
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = func.entry_block
        from zhc.ir.instructions import IRInstruction
        res = IRValue("%0", "整数型", ValueKind.TEMP)
        func_val = IRValue("printf", kind=ValueKind.FUNCTION)
        arg = IRValue("x", kind=ValueKind.VAR)
        bb.add_instruction(IRInstruction(Opcode.CALL, [func_val, arg], [res]))
        ir.add_function(func)
        code = backend.generate(ir)
        self.assertIn("printf(x);", code)


if __name__ == "__main__":
    unittest.main()
