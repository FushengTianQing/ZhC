#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCodeGenerator 单元测试

作者: 阿福
日期: 2026-04-03
"""

import sys
sys.path.insert(0, 'src')

import pytest
from zhpp.parser import *
from zhpp.codegen import CCodeGenerator


@pytest.fixture
def gen():
    """创建代码生成器"""
    return CCodeGenerator()


def gen_expr(expr_node):
    """辅助函数：生成表达式字符串"""
    g = CCodeGenerator()
    return g._expr_to_string(expr_node)


# ============================================================================
# 类型生成测试
# ============================================================================

class TestTypeGeneration:
    """类型映射测试"""

    def test_primitive_int(self, gen):
        t = PrimitiveTypeNode('整数型')
        assert gen._emit_type(t) == 'int'

    def test_primitive_float(self, gen):
        t = PrimitiveTypeNode('浮点型')
        assert gen._emit_type(t) == 'float'

    def test_primitive_double(self, gen):
        t = PrimitiveTypeNode('双精度浮点型')
        assert gen._emit_type(t) == 'double'

    def test_primitive_char(self, gen):
        t = PrimitiveTypeNode('字符型')
        assert gen._emit_type(t) == 'char'

    def test_primitive_bool(self, gen):
        t = PrimitiveTypeNode('布尔型')
        assert gen._emit_type(t) == '_Bool'

    def test_primitive_void(self, gen):
        t = PrimitiveTypeNode('空型')
        assert gen._emit_type(t) == 'void'

    def test_primitive_string(self, gen):
        t = PrimitiveTypeNode('字符串型')
        assert gen._emit_type(t) == 'char*'

    def test_pointer_type(self, gen):
        t = PointerTypeNode(PrimitiveTypeNode('整数型'))
        assert gen._emit_type(t) == 'int*'

    def test_pointer_to_pointer(self, gen):
        t = PointerTypeNode(PointerTypeNode(PrimitiveTypeNode('字符型')))
        assert gen._emit_type(t) == 'char**'

    def test_array_type(self, gen):
        t = ArrayTypeNode(PrimitiveTypeNode('整数型'), IntLiteralNode(10))
        assert gen._emit_type(t) == 'int[10]'

    def test_struct_type(self, gen):
        t = StructTypeNode('点')
        assert gen._emit_type(t) == 'struct 点'


# ============================================================================
# 声明生成测试
# ============================================================================

class TestDeclarationGeneration:
    """声明生成测试"""

    def test_function_decl_no_params(self, gen):
        func = FunctionDeclNode('主函数', PrimitiveTypeNode('整数型'), [],
                                BlockStmtNode([ReturnStmtNode(IntLiteralNode(0))]))
        code = gen.generate(ProgramNode([func]))
        assert 'int main(void)' in code
        assert 'return 0;' in code

    def test_function_decl_with_params(self, gen):
        params = [
            ParamDeclNode('a', PrimitiveTypeNode('整数型')),
            ParamDeclNode('b', PrimitiveTypeNode('整数型')),
        ]
        func = FunctionDeclNode('加法', PrimitiveTypeNode('整数型'), params,
                                BlockStmtNode([ReturnStmtNode(BinaryExprNode('+', IdentifierExprNode('a'), IdentifierExprNode('b')))]))
        code = gen.generate(ProgramNode([func]))
        assert 'int 加法(int a, int b)' in code
        assert 'return (a + b);' in code

    def test_variable_decl_simple(self, gen):
        var = VariableDeclNode('x', PrimitiveTypeNode('整数型'), None)
        code = gen.generate(ProgramNode([FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([var]))]))
        assert 'int x;' in code

    def test_variable_decl_with_init(self, gen):
        var = VariableDeclNode('x', PrimitiveTypeNode('整数型'), IntLiteralNode(42))
        code = gen.generate(ProgramNode([FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([var]))]))
        assert 'int x = 42;' in code

    def test_variable_decl_const(self, gen):
        var = VariableDeclNode('PI', PrimitiveTypeNode('浮点型'), FloatLiteralNode(3.14), is_const=True)
        code = gen.generate(ProgramNode([FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([var]))]))
        assert 'const float PI = 3.14;' in code

    def test_struct_decl(self, gen):
        members = [
            VariableDeclNode('x', PrimitiveTypeNode('整数型'), None),
            VariableDeclNode('y', PrimitiveTypeNode('整数型'), None),
        ]
        struct = StructDeclNode('点', members)
        code = gen.generate(ProgramNode([struct]))
        assert 'struct 点' in code
        assert 'int x;' in code
        assert 'int y;' in code


# ============================================================================
# 语句生成测试
# ============================================================================

class TestStatementGeneration:
    """语句生成测试"""

    def test_if_stmt(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([
            IfStmtNode(
                BinaryExprNode('>', IdentifierExprNode('x'), IntLiteralNode(0)),
                BlockStmtNode([ExprStmtNode(CallExprNode(IdentifierExprNode('打印'), [StringLiteralNode('positive')]))]),
                None
            )
        ]))
        code = gen.generate(ProgramNode([func]))
        assert 'if (x > 0)' in code
        assert 'printf("positive");' in code

    def test_if_else_stmt(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([
            IfStmtNode(
                BinaryExprNode('>', IdentifierExprNode('x'), IntLiteralNode(0)),
                BlockStmtNode([ReturnStmtNode(IntLiteralNode(1))]),
                BlockStmtNode([ReturnStmtNode(IntLiteralNode(-1))])
            )
        ]))
        code = gen.generate(ProgramNode([func]))
        assert '} else {' in code
        assert 'return 1;' in code
        assert 'return -1;' in code

    def test_while_stmt(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([
            WhileStmtNode(
                BinaryExprNode('<', IdentifierExprNode('i'), IntLiteralNode(10)),
                BlockStmtNode([ExprStmtNode(AssignExprNode(IdentifierExprNode('i'), BinaryExprNode('+', IdentifierExprNode('i'), IntLiteralNode(1))))])
            )
        ]))
        code = gen.generate(ProgramNode([func]))
        assert 'while (i < 10)' in code
        assert 'i = (i + 1);' in code

    def test_for_stmt(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([
            ForStmtNode(
                VariableDeclNode('i', PrimitiveTypeNode('整数型'), IntLiteralNode(0)),
                BinaryExprNode('<', IdentifierExprNode('i'), IntLiteralNode(10)),
                AssignExprNode(IdentifierExprNode('i'), BinaryExprNode('+', IdentifierExprNode('i'), IntLiteralNode(1))),
                BlockStmtNode([ExprStmtNode(CallExprNode(IdentifierExprNode('打印'), [IdentifierExprNode('i')]))])
            )
        ]))
        code = gen.generate(ProgramNode([func]))
        assert 'for (int i = 0; (i < 10); i = (i + 1))' in code

    def test_break_continue(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([
            WhileStmtNode(BoolLiteralNode(True), BlockStmtNode([BreakStmtNode()])),
            ContinueStmtNode(),
        ]))
        code = gen.generate(ProgramNode([func]))
        assert 'break;' in code
        assert 'continue;' in code

    def test_return_stmt(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('整数型'), [], BlockStmtNode([ReturnStmtNode(IntLiteralNode(42))]))
        code = gen.generate(ProgramNode([func]))
        assert 'return 42;' in code

    def test_return_void(self, gen):
        func = FunctionDeclNode('f', PrimitiveTypeNode('空型'), [], BlockStmtNode([ReturnStmtNode(None)]))
        code = gen.generate(ProgramNode([func]))
        assert 'return;' in code


# ============================================================================
# 表达式生成测试
# ============================================================================

class TestExpressionGeneration:
    """表达式生成测试"""

    def test_binary_expr(self):
        expr = BinaryExprNode('+', IntLiteralNode(1), IntLiteralNode(2))
        assert gen_expr(expr) == '(1 + 2)'

    def test_binary_nested(self):
        expr = BinaryExprNode('+', BinaryExprNode('*', IntLiteralNode(1), IntLiteralNode(2)), IntLiteralNode(3))
        assert gen_expr(expr) == '((1 * 2) + 3)'

    def test_unary_prefix(self):
        expr = UnaryExprNode('-', IntLiteralNode(5), is_prefix=True)
        assert gen_expr(expr) == '-5'

    def test_unary_postfix(self):
        expr = UnaryExprNode('++', IdentifierExprNode('i'), is_prefix=False)
        assert gen_expr(expr) == 'i++'

    def test_assign_expr(self):
        expr = AssignExprNode(IdentifierExprNode('x'), IntLiteralNode(10))
        assert gen_expr(expr) == 'x = 10'

    def test_assign_compound(self):
        expr = AssignExprNode(IdentifierExprNode('x'), IntLiteralNode(5), '+=')
        assert gen_expr(expr) == 'x += 5'

    def test_call_expr(self):
        expr = CallExprNode(IdentifierExprNode('打印'), [StringLiteralNode('hello')])
        assert gen_expr(expr) == 'printf("hello")'

    def test_call_expr_chinese_func(self):
        expr = CallExprNode(IdentifierExprNode('平方根'), [IntLiteralNode(16)])
        assert gen_expr(expr) == 'sqrt(16)'

    def test_member_expr(self):
        expr = MemberExprNode(IdentifierExprNode('p'), 'x')
        assert gen_expr(expr) == 'p.x'

    def test_array_expr(self):
        expr = ArrayExprNode(IdentifierExprNode('arr'), IntLiteralNode(0))
        assert gen_expr(expr) == 'arr[0]'

    def test_int_literal(self):
        assert gen_expr(IntLiteralNode(42)) == '42'

    def test_float_literal(self):
        assert gen_expr(FloatLiteralNode(3.14)) == '3.14'

    def test_string_literal(self):
        assert gen_expr(StringLiteralNode('hello')) == '"hello"'

    def test_string_literal_escape(self):
        assert gen_expr(StringLiteralNode('hello\nworld')) == '"hello\\nworld"'

    def test_char_literal(self):
        assert gen_expr(CharLiteralNode('A')) == "'A'"

    def test_bool_literal_true(self):
        assert gen_expr(BoolLiteralNode(True)) == '1'

    def test_bool_literal_false(self):
        assert gen_expr(BoolLiteralNode(False)) == '0'

    def test_null_literal(self):
        assert gen_expr(NullLiteralNode()) == 'NULL'

    def test_ternary_expr(self):
        expr = TernaryExprNode(BoolLiteralNode(True), IntLiteralNode(1), IntLiteralNode(0))
        assert gen_expr(expr) == '(1 ? 1 : 0)'

    def test_sizeof_expr(self):
        expr = SizeofExprNode(PrimitiveTypeNode('整数型'))
        assert gen_expr(expr) == 'sizeof(int)'


# ============================================================================
# 完整程序测试
# ============================================================================

class TestCompleteProgram:
    """完整程序生成测试"""

    def test_hello_world(self):
        main = FunctionDeclNode('主函数', PrimitiveTypeNode('整数型'), [], BlockStmtNode([
            ExprStmtNode(CallExprNode(IdentifierExprNode('打印'), [StringLiteralNode('Hello, World!')])),
            ReturnStmtNode(IntLiteralNode(0)),
        ]))
        gen = CCodeGenerator()
        code = gen.generate(ProgramNode([main]))
        assert 'int main(void)' in code
        assert 'printf("Hello, World!");' in code
        assert 'return 0;' in code

    def test_function_with_two_calls(self):
        add = FunctionDeclNode('加法', PrimitiveTypeNode('整数型'), [
            ParamDeclNode('a', PrimitiveTypeNode('整数型')),
            ParamDeclNode('b', PrimitiveTypeNode('整数型')),
        ], BlockStmtNode([
            ReturnStmtNode(BinaryExprNode('+', IdentifierExprNode('a'), IdentifierExprNode('b')))
        ]))
        main = FunctionDeclNode('主函数', PrimitiveTypeNode('整数型'), [], BlockStmtNode([
            VariableDeclNode('result', PrimitiveTypeNode('整数型'),
                             CallExprNode(IdentifierExprNode('加法'), [IntLiteralNode(3), IntLiteralNode(4)])),
            ExprStmtNode(CallExprNode(IdentifierExprNode('打印'), [IdentifierExprNode('result')])),
            ReturnStmtNode(IntLiteralNode(0)),
        ]))
        gen = CCodeGenerator()
        code = gen.generate(ProgramNode([add, main]))
        assert 'int 加法(int a, int b)' in code
        assert 'int result = 加法(3, 4);' in code

    def test_struct_usage(self):
        struct = StructDeclNode('点', [
            VariableDeclNode('x', PrimitiveTypeNode('浮点型'), None),
            VariableDeclNode('y', PrimitiveTypeNode('浮点型'), None),
        ])
        main = FunctionDeclNode('主函数', PrimitiveTypeNode('整数型'), [], BlockStmtNode([
            VariableDeclNode('p', StructTypeNode('点'), None),
            ExprStmtNode(AssignExprNode(MemberExprNode(IdentifierExprNode('p'), 'x'), FloatLiteralNode(1.0))),
            ReturnStmtNode(IntLiteralNode(0)),
        ]))
        gen = CCodeGenerator()
        code = gen.generate(ProgramNode([struct, main]))
        assert 'struct 点' in code
        assert 'struct 点 p;' in code
        assert 'p.x = 1.0;' in code

    def test_pointer_usage(self):
        main = FunctionDeclNode('主函数', PrimitiveTypeNode('整数型'), [], BlockStmtNode([
            VariableDeclNode('x', PrimitiveTypeNode('整数型'), IntLiteralNode(42)),
            VariableDeclNode('ptr', PointerTypeNode(PrimitiveTypeNode('整数型')), None),
            ExprStmtNode(AssignExprNode(IdentifierExprNode('ptr'), IdentifierExprNode('x'))),
            ReturnStmtNode(IntLiteralNode(0)),
        ]))
        gen = CCodeGenerator()
        code = gen.generate(ProgramNode([main]))
        assert 'int x = 42;' in code
        assert 'int* ptr;' in code
