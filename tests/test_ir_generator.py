# -*- coding: utf-8 -*-
"""
M2: test_ir_generator.py - AST→IR 生成器测试

运行：
    python -m pytest tests/test_ir_generator.py -v
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhpp.parser.ast_nodes import (
    ProgramNode, FunctionDeclNode, VariableDeclNode, ParamDeclNode,
    BlockStmtNode, ReturnStmtNode, IfStmtNode, WhileStmtNode,
    IntLiteralNode, FloatLiteralNode, IdentifierExprNode,
    PrimitiveTypeNode, BinaryExprNode, CallExprNode,
)
from zhpp.ir.ir_generator import IRGenerator
from zhpp.ir import IRPrinter, Opcode


class TestIRGeneratorBasics(unittest.TestCase):
    """IRGenerator 基础功能测试"""

    def test_empty_program(self):
        """空程序"""
        gen = IRGenerator()
        ast = ProgramNode(declarations=[])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 0)

    def test_function_no_body(self):
        """无函数体"""
        gen = IRGenerator()
        func = FunctionDeclNode(
            name="foo",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=None,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 1)
        self.assertEqual(ir.functions[0].name, "foo")

    def test_function_with_return_int_literal(self):
        """返回整数字面量"""
        gen = IRGenerator()
        ret_stmt = ReturnStmtNode(IntLiteralNode(42))
        func = FunctionDeclNode(
            name="foo",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=ret_stmt,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 1)
        func_ir = ir.functions[0]
        entry = func_ir.entry_block
        self.assertIsNotNone(entry)
        self.assertTrue(entry.is_terminated())

    def test_main_function(self):
        """主函数"""
        gen = IRGenerator()
        ret_stmt = ReturnStmtNode(IntLiteralNode(0))
        func = FunctionDeclNode(
            name="主函数",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=ret_stmt,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 1)
        # 主函数名被解析为 main
        self.assertEqual(ir.functions[0].name, "main")

    def test_if_stmt_structure(self):
        """if 语句生成基本块"""
        gen = IRGenerator()
        cond = IdentifierExprNode("x")
        then_b = ReturnStmtNode(IntLiteralNode(1))
        if_node = IfStmtNode(condition=cond, then_branch=then_b, else_branch=None)
        func = FunctionDeclNode(
            name="test_if",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=if_node,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 1)
        func_ir = ir.functions[0]
        # if 语句应创建多个基本块（then/else/merge）
        self.assertGreater(len(func_ir.basic_blocks), 1)

    def test_while_loop(self):
        """while 循环"""
        gen = IRGenerator()
        cond = IdentifierExprNode("x")
        body = ReturnStmtNode(IntLiteralNode(0))
        while_node = WhileStmtNode(condition=cond, body=body)
        func = FunctionDeclNode(
            name="test_while",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=while_node,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 1)
        func_ir = ir.functions[0]
        # while 循环创建 cond/body/end 基本块
        self.assertGreaterEqual(len(func_ir.basic_blocks), 3)

    def test_binary_expr(self):
        """二元表达式"""
        gen = IRGenerator()
        left = IntLiteralNode(1)
        right = IntLiteralNode(2)
        bin_expr = BinaryExprNode(left=left, right=right, operator="+")
        ret_stmt = ReturnStmtNode(bin_expr)
        func = FunctionDeclNode(
            name="test_binop",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=ret_stmt,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        self.assertEqual(len(ir.functions), 1)

    def test_variable_decl(self):
        """变量声明"""
        gen = IRGenerator()
        var = VariableDeclNode(
            name="x",
            var_type=PrimitiveTypeNode("整数型"),
            init=IntLiteralNode(10),
        )
        # 直接调用 visit_variable_decl
        var.accept(gen)
        # 不崩溃即通过

    def test_print_ir(self):
        """打印 IR"""
        gen = IRGenerator()
        ret_stmt = ReturnStmtNode(IntLiteralNode(42))
        func = FunctionDeclNode(
            name="foo",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=ret_stmt,
        )
        ast = ProgramNode([func])
        ir = gen.generate(ast)
        printer = IRPrinter()
        output = printer.print(ir)
        self.assertIn("foo", output)
        self.assertIn("define", output)


if __name__ == "__main__":
    unittest.main()
