# -*- coding: utf-8 -*-
"""
M4: test_ir_verifier.py - IR 验证器测试

运行：
    python -m pytest tests/test_ir_verifier.py -v
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.ir import IRProgram, IRFunction, Opcode, IRValue, ValueKind
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.ir_verifier import IRVerifier, VerificationError


class TestIRVerifier(unittest.TestCase):
    """IRVerifier 测试"""

    def test_valid_program(self):
        """合法程序"""
        verifier = IRVerifier()
        ir = IRProgram()
        func = IRFunction("main", "整数型")
        bb = func.entry_block
        bb.add_instruction(IRInstruction(Opcode.RET))
        ir.add_function(func)
        errors = verifier.verify(ir)
        self.assertEqual(len(errors), 0)

    def test_undefined_block_reference(self):
        """V6: 引用未定义的基本块"""
        verifier = IRVerifier()
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = IRBasicBlock("entry")
        func.basic_blocks.append(bb)
        # entry 跳转到不存在的块
        bb.add_successor("nonexistent")
        bb.add_instruction(IRInstruction(Opcode.JMP))
        ir.add_function(func)
        errors = verifier.verify(ir)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any(e.error_type == "未定义基本块" for e in errors))

    def test_ret_mid_block(self):
        """V1: RET 不在末尾"""
        verifier = IRVerifier()
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = IRBasicBlock("entry")
        bb.add_instruction(IRInstruction(Opcode.RET))
        bb.add_instruction(IRInstruction(Opcode.ADD))  # RET 后还有指令
        func.basic_blocks.append(bb)
        ir.add_function(func)
        errors = verifier.verify(ir)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any(e.error_type == "RET位置错误" for e in errors))

    def test_call_without_function(self):
        """V4: CALL 缺少函数操作数"""
        verifier = IRVerifier()
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = IRBasicBlock("entry")
        bb.add_instruction(IRInstruction(Opcode.CALL))  # 无操作数
        bb.add_instruction(IRInstruction(Opcode.RET))
        func.basic_blocks.append(bb)
        ir.add_function(func)
        errors = verifier.verify(ir)
        self.assertGreater(len(errors), 0)

    def test_phi_instruction(self):
        """phi 指令存在即通过"""
        verifier = IRVerifier()
        ir = IRProgram()
        func = IRFunction("test", "整数型")
        bb = func.entry_block
        # phi 节点（简单构造，不验证操作数细节）
        val = IRValue("42", "整数型", ValueKind.CONST)
        phi_args = [val, IRValue("v", "整数型"), IRValue("bb1", "整数型")]
        bb.add_instruction(IRInstruction(Opcode.PHI, phi_args))
        bb.add_instruction(IRInstruction(Opcode.RET))
        ir.add_function(func)
        errors = verifier.verify(ir)
        # phi 存在即可，不做严格操作数验证
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
