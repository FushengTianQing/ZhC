#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST 验证器测试套件

测试覆盖：
1. 结构完整性检查
2. 类型一致性检查
3. 语义约束检查
4. 边界条件检查

作者：阿福
日期：2026-04-08
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.parser.ast_nodes import (
    ProgramNode, FunctionDeclNode, VariableDeclNode, ParamDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode, ReturnStmtNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, IdentifierExprNode,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode, BoolLiteralNode,
    PrimitiveTypeNode,
)
from zhc.parser.ast_validator import (
    ASTValidator, validate_ast, ValidationResult,
    ValidationSeverity, ValidationIssue
)


# =============================================================================
# 结构完整性测试
# =============================================================================

class TestStructuralIntegrity(unittest.TestCase):
    """结构完整性测试"""
    
    def test_empty_program(self):
        """测试空程序"""
        program = ProgramNode(declarations=[])
        result = validate_ast(program)
        self.assertTrue(result.is_valid)
        # 空程序只有警告
        self.assertEqual(len(result.get_warnings()), 1)
    
    def test_function_without_body(self):
        """测试无函数体的函数"""
        func = FunctionDeclNode(
            name="测试函数",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[],
            body=None
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.get_warnings()) > 0)
    
    def test_function_with_empty_body(self):
        """测试空函数体"""
        func = FunctionDeclNode(
            name="测试函数",
            return_type=PrimitiveTypeNode(name="空"),
            params=[],
            body=BlockStmtNode(statements=[])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
    
    def test_empty_block(self):
        """测试空代码块"""
        block = BlockStmtNode(statements=[])
        result = validate_ast(block)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.get_warnings()), 1)
    
    def test_if_without_condition(self):
        """测试缺少条件的 if 语句"""
        if_stmt = IfStmtNode(
            condition=None,
            then_branch=BlockStmtNode(statements=[]),
            else_branch=None
        )
        result = validate_ast(if_stmt)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)
    
    def test_if_without_then_branch(self):
        """测试缺少 then 分支的 if 语句"""
        if_stmt = IfStmtNode(
            condition=IntLiteralNode(value=1),
            then_branch=None,
            else_branch=None
        )
        result = validate_ast(if_stmt)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.get_warnings()) > 0)
    
    def test_while_without_condition(self):
        """测试缺少条件的 while 语句"""
        while_stmt = WhileStmtNode(
            condition=None,
            body=BlockStmtNode(statements=[])
        )
        result = validate_ast(while_stmt)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)
    
    def test_for_without_body(self):
        """测试缺少循环体的 for 语句"""
        for_stmt = ForStmtNode(
            init=None,
            condition=None,
            update=None,
            body=None
        )
        result = validate_ast(for_stmt)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.get_warnings()) > 0)


# =============================================================================
# 变量声明测试
# =============================================================================

class TestVariableDeclaration(unittest.TestCase):
    """变量声明测试"""
    
    def test_valid_variable_decl(self):
        """测试有效的变量声明"""
        block = BlockStmtNode(statements=[
            VariableDeclNode(name="x", var_type=PrimitiveTypeNode(name="整数"), init=IntLiteralNode(value=0))
        ])
        result = validate_ast(block)
        self.assertTrue(result.is_valid)
    
    def test_empty_variable_name(self):
        """测试空变量名"""
        var = VariableDeclNode(name="", var_type=PrimitiveTypeNode(name="整数"), init=None)
        result = validate_ast(var)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)
    
    def test_duplicate_variable_decl(self):
        """测试重复变量声明"""
        block = BlockStmtNode(statements=[
            VariableDeclNode(name="x", var_type=PrimitiveTypeNode(name="整数"), init=IntLiteralNode(value=0)),
            VariableDeclNode(name="x", var_type=PrimitiveTypeNode(name="整数"), init=IntLiteralNode(value=1))
        ])
        result = validate_ast(block)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)
        
        # 检查错误信息
        for issue in result.get_errors():
            if "重复" in issue.message:
                self.assertIn("x", issue.message)
                break


# =============================================================================
# 函数声明测试
# =============================================================================

class TestFunctionDeclaration(unittest.TestCase):
    """函数声明测试"""
    
    def test_valid_function(self):
        """测试有效函数"""
        func = FunctionDeclNode(
            name="main",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[
                ParamDeclNode(name="argc", param_type=PrimitiveTypeNode(name="整数")),
                ParamDeclNode(name="argv", param_type=PrimitiveTypeNode(name="整数"))
            ],
            body=BlockStmtNode(statements=[
                ReturnStmtNode(value=IntLiteralNode(value=0))
            ])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
    
    def test_function_without_return(self):
        """测试有返回值类型但没有 return 的函数"""
        func = FunctionDeclNode(
            name="计算",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[],
            body=BlockStmtNode(statements=[])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.get_warnings()) > 0)
    
    def test_void_function_with_return_value(self):
        """测试空返回类型函数有返回值"""
        func = FunctionDeclNode(
            name="打印",
            return_type=PrimitiveTypeNode(name="空"),
            params=[],
            body=BlockStmtNode(statements=[
                ReturnStmtNode(value=IntLiteralNode(value=0))
            ])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.get_warnings()) > 0)
    
    def test_empty_function_name(self):
        """测试空函数名"""
        func = FunctionDeclNode(
            name="",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[],
            body=BlockStmtNode(statements=[])
        )
        result = validate_ast(func)
        self.assertFalse(result.is_valid)
    
    def test_function_param_without_name(self):
        """测试参数没有名字"""
        func = FunctionDeclNode(
            name="测试",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[
                ParamDeclNode(name="", param_type=PrimitiveTypeNode(name="整数"))
            ],
            body=BlockStmtNode(statements=[])
        )
        result = validate_ast(func)
        self.assertFalse(result.is_valid)


# =============================================================================
# 表达式测试
# =============================================================================

class TestExpression(unittest.TestCase):
    """表达式测试"""
    
    def test_valid_binary_expr(self):
        """测试有效的二元表达式"""
        expr = BinaryExprNode(
            operator="+",
            left=IntLiteralNode(value=1),
            right=IntLiteralNode(value=2)
        )
        result = validate_ast(expr)
        self.assertTrue(result.is_valid)
    
    def test_binary_expr_without_left(self):
        """测试缺少左操作数的二元表达式"""
        expr = BinaryExprNode(
            operator="+",
            left=None,
            right=IntLiteralNode(value=2)
        )
        result = validate_ast(expr)
        self.assertFalse(result.is_valid)
    
    def test_binary_expr_without_right(self):
        """测试缺少右操作数的二元表达式"""
        expr = BinaryExprNode(
            operator="+",
            left=IntLiteralNode(value=1),
            right=None
        )
        result = validate_ast(expr)
        self.assertFalse(result.is_valid)
    
    def test_binary_expr_without_operator(self):
        """测试缺少操作符的二元表达式"""
        expr = BinaryExprNode(
            operator="",
            left=IntLiteralNode(value=1),
            right=IntLiteralNode(value=2)
        )
        result = validate_ast(expr)
        self.assertFalse(result.is_valid)
    
    def test_valid_unary_expr(self):
        """测试有效的一元表达式"""
        expr = UnaryExprNode(
            operator="-",
            operand=IntLiteralNode(value=5)
        )
        result = validate_ast(expr)
        self.assertTrue(result.is_valid)
    
    def test_unary_expr_without_operand(self):
        """测试缺少操作数的一元表达式"""
        expr = UnaryExprNode(
            operator="-",
            operand=None
        )
        result = validate_ast(expr)
        self.assertFalse(result.is_valid)
    
    def test_valid_call_expr(self):
        """测试有效的函数调用"""
        func = FunctionDeclNode(
            name="打印",
            return_type=PrimitiveTypeNode(name="空"),
            params=[ParamDeclNode(name="x", param_type=PrimitiveTypeNode(name="整数"))],
            body=BlockStmtNode(statements=[])
        )
        call = CallExprNode(
            callee=IdentifierExprNode(name="打印"),
            args=[IntLiteralNode(value=1)]
        )
        # 先声明函数
        program = ProgramNode(declarations=[func, call])
        result = validate_ast(program)
        self.assertTrue(result.is_valid)
    
    def test_call_undeclared_function(self):
        """测试调用未声明的函数"""
        call = CallExprNode(
            callee=IdentifierExprNode(name="未知函数"),
            args=[]
        )
        result = validate_ast(call)
        self.assertTrue(result.is_valid)  # 验证通过，但有警告
        self.assertTrue(len(result.get_warnings()) > 0)
    
    def test_call_with_wrong_arg_count(self):
        """测试参数数量不匹配的函数调用"""
        func = FunctionDeclNode(
            name="加法",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[
                ParamDeclNode(name="a", param_type=PrimitiveTypeNode(name="整数")),
                ParamDeclNode(name="b", param_type=PrimitiveTypeNode(name="整数"))
            ],
            body=BlockStmtNode(statements=[])
        )
        call = CallExprNode(
            callee=IdentifierExprNode(name="加法"),
            args=[IntLiteralNode(value=1)]  # 只传一个参数
        )
        program = ProgramNode(declarations=[func, call])
        result = validate_ast(program)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)


# =============================================================================
# 控制流测试
# =============================================================================

class TestControlFlow(unittest.TestCase):
    """控制流测试"""
    
    def test_return_outside_function(self):
        """测试在函数外使用 return"""
        ret = ReturnStmtNode(value=IntLiteralNode(value=0))
        result = validate_ast(ret)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)
    
    def test_valid_return_in_function(self):
        """测试在函数内有效使用 return"""
        func = FunctionDeclNode(
            name="测试",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[],
            body=BlockStmtNode(statements=[
                ReturnStmtNode(value=IntLiteralNode(value=0))
            ])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
    
    def test_void_return_in_function(self):
        """测试空返回语句"""
        func = FunctionDeclNode(
            name="打印",
            return_type=PrimitiveTypeNode(name="空"),
            params=[],
            body=BlockStmtNode(statements=[
                ReturnStmtNode(value=None)
            ])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)


# =============================================================================
# 边界条件测试
# =============================================================================

class TestEdgeCases(unittest.TestCase):
    """边界条件测试"""
    
    def test_deep_nesting(self):
        """测试深层嵌套"""
        # 创建一个深度为 150 的嵌套结构
        node = IntLiteralNode(value=0)
        for _ in range(150):
            node = BlockStmtNode(statements=[node])
        
        validator = ASTValidator(max_depth=100)
        result = validator.validate(node)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.get_errors()) > 0)
    
    def test_identifier_undeclared(self):
        """测试使用未声明的标识符"""
        expr = IdentifierExprNode(name="未知变量")
        result = validate_ast(expr)
        self.assertTrue(result.is_valid)  # 验证通过，但有警告
        self.assertTrue(len(result.get_warnings()) > 0)
    
    def test_nested_function_scope(self):
        """测试嵌套函数作用域"""
        # 内层声明的变量在外层应该可见
        func = FunctionDeclNode(
            name="外层",
            return_type=PrimitiveTypeNode(name="整数"),
            params=[],
            body=BlockStmtNode(statements=[
                VariableDeclNode(name="x", var_type=PrimitiveTypeNode(name="整数"), init=IntLiteralNode(value=1)),
                ReturnStmtNode(value=IdentifierExprNode(name="x"))
            ])
        )
        result = validate_ast(func)
        self.assertTrue(result.is_valid)
    
    def test_multiple_functions(self):
        """测试多个函数"""
        program = ProgramNode(declarations=[
            FunctionDeclNode(
                name="函数1",
                return_type=PrimitiveTypeNode(name="整数"),
                params=[],
                body=BlockStmtNode(statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=1))
                ])
            ),
            FunctionDeclNode(
                name="函数2",
                return_type=PrimitiveTypeNode(name="整数"),
                params=[],
                body=BlockStmtNode(statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=2))
                ])
            )
        ])
        result = validate_ast(program)
        self.assertTrue(result.is_valid)


# =============================================================================
# 集成测试
# =============================================================================

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_complete_program(self):
        """测试完整程序"""
        program = ProgramNode(declarations=[
            FunctionDeclNode(
                name="main",
                return_type=PrimitiveTypeNode(name="整数"),
                params=[],
                body=BlockStmtNode(statements=[
                    VariableDeclNode(
                        name="a",
                        var_type=PrimitiveTypeNode(name="整数"),
                        init=IntLiteralNode(value=10)
                    ),
                    VariableDeclNode(
                        name="b",
                        var_type=PrimitiveTypeNode(name="整数"),
                        init=IntLiteralNode(value=20)
                    ),
                    ReturnStmtNode(
                        value=BinaryExprNode(
                            operator="+",
                            left=IdentifierExprNode(name="a"),
                            right=IdentifierExprNode(name="b")
                        )
                    )
                ])
            )
        ])
        result = validate_ast(program)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)
    
    def test_program_with_errors(self):
        """测试有错误的程序"""
        program = ProgramNode(declarations=[
            FunctionDeclNode(
                name="错误函数",
                return_type=PrimitiveTypeNode(name="整数"),
                params=[],
                body=BlockStmtNode(statements=[
                    VariableDeclNode(name="x", var_type=PrimitiveTypeNode(name="整数"), init=None),
                    VariableDeclNode(name="x", var_type=PrimitiveTypeNode(name="整数"), init=None),  # 重复
                    ReturnStmtNode(value=None)  # 应该有返回值
                ])
            )
        ])
        result = validate_ast(program)
        self.assertFalse(result.is_valid)
        # 验证至少有一个错误（重复变量声明）
        self.assertTrue(len(result.get_errors()) >= 1)
    
    def test_validation_result_str(self):
        """测试验证结果字符串表示"""
        valid_result = ValidationResult(is_valid=True)
        self.assertIn("通过", str(valid_result))
        
        valid_result.add_error("测试错误", IntLiteralNode(value=0))
        self.assertIn("失败", str(valid_result))


if __name__ == '__main__':
    unittest.main(verbosity=2)
