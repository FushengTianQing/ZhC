#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部C函数调用测试

测试外部函数声明语法解析功能

作者: 阿福
日期: 2026-04-10
"""

import pytest
from zhc.parser import Lexer, Parser
from zhc.parser.ast_nodes import (
    ExternalBlockNode,
    ExternalFunctionDeclNode,
    ProgramNode,
    PrimitiveTypeNode,
)


class TestExternalFunctionParsing:
    """外部函数解析测试"""

    def test_extern_token_recognition(self):
        """测试 EXTERN token 识别"""
        code = '外部 "C" { }'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 第一个 token 应该是 EXTERN
        assert tokens[0].type.name == "EXTERN"
        assert tokens[0].value == "外部"

    def test_simple_external_block(self):
        """测试简单的外部块解析"""
        code = """
        外部 "C" {
            整数型 系统调用(整数型 命令);
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, ProgramNode)
        assert len(ast.declarations) == 1

        external_block = ast.declarations[0]
        assert isinstance(external_block, ExternalBlockNode)
        assert external_block.language == "C"
        assert len(external_block.declarations) == 1

    def test_multiple_external_functions(self):
        """测试多个外部函数声明"""
        code = """
        外部 "C" {
            整数型 系统调用(整数型 命令);
            无类型 退出程序(整数型 状态码);
            整数型 写入(整数型 文件描述符, 字符指针型 缓冲, 整数型 长度);
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        assert isinstance(external_block, ExternalBlockNode)
        assert len(external_block.declarations) == 3

        # 检查第一个函数
        func1 = external_block.declarations[0]
        assert isinstance(func1, ExternalFunctionDeclNode)
        assert func1.name == "系统调用"
        assert isinstance(func1.return_type, PrimitiveTypeNode)
        assert len(func1.parameters) == 1

        # 检查第二个函数
        func2 = external_block.declarations[1]
        assert func2.name == "退出程序"
        assert len(func2.parameters) == 1

        # 检查第三个函数
        func3 = external_block.declarations[2]
        assert func3.name == "写入"
        assert len(func3.parameters) == 3

    def test_external_function_with_multiple_params(self):
        """测试带多个参数的外部函数"""
        code = """
        外部 "C" {
            整数型 获取环境变量(字符指针型 名称, 字符指针型 缓冲, 整数型 大小);
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        func = external_block.declarations[0]

        assert func.name == "获取环境变量"
        assert len(func.parameters) == 3
        assert func.parameters[0].name == "名称"
        assert func.parameters[1].name == "缓冲"
        assert func.parameters[2].name == "大小"

    def test_external_function_void_return(self):
        """测试无返回值的外部函数"""
        code = """
        外部 "C" {
            无类型 打印消息(字符指针型 消息);
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        func = external_block.declarations[0]

        assert func.name == "打印消息"
        assert isinstance(func.return_type, PrimitiveTypeNode)
        assert func.return_type.name == "无类型"

    def test_external_function_no_params(self):
        """测试无参数的外部函数"""
        code = """
        外部 "C" {
            整数型 获取时间();
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        func = external_block.declarations[0]

        assert func.name == "获取时间"
        assert len(func.parameters) == 0

    def test_external_block_with_other_declarations(self):
        """测试外部块与其他声明混合"""
        code = """
        外部 "C" {
            整数型 系统调用(整数型 命令);
        }

        整数型 主函数() {
            返回 0;
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert len(ast.declarations) == 2

        # 第一个应该是外部块
        assert isinstance(ast.declarations[0], ExternalBlockNode)

        # 第二个应该是函数声明
        assert ast.declarations[1].name == "主函数"

    def test_external_function_with_pointer_type(self):
        """测试带指针类型的外部函数"""
        code = """
        外部 "C" {
            字符指针型 获取字符串(整数型 索引);
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        func = external_block.declarations[0]

        assert func.name == "获取字符串"
        # 返回类型应该是指针类型
        assert func.return_type is not None

    def test_external_block_language_attribute(self):
        """测试外部块的语言属性"""
        code = '外部 "C" { 整数型 测试(); }'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        assert external_block.language == "C"

    def test_external_function_get_children(self):
        """测试外部函数节点的子节点获取"""
        code = """
        外部 "C" {
            整数型 测试(整数型 参数);
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        external_block = ast.declarations[0]
        func = external_block.declarations[0]

        children = func.get_children()
        assert len(children) == 2  # 返回类型 + 1个参数
        assert children[0] == func.return_type
        assert children[1] == func.parameters[0]


class TestExternalFunctionAST:
    """外部函数 AST 节点测试"""

    def test_external_block_node_creation(self):
        """测试外部块节点创建"""
        from zhc.parser.ast_nodes import ASTNodeType

        func_decl = ExternalFunctionDeclNode(
            name="测试函数",
            return_type=PrimitiveTypeNode("整数型"),
            parameters=[],
            line=1,
            column=1,
        )

        external_block = ExternalBlockNode(
            language="C",
            declarations=[func_decl],
            line=1,
            column=1,
        )

        assert external_block.node_type == ASTNodeType.EXTERNAL_BLOCK
        assert external_block.language == "C"
        assert len(external_block.declarations) == 1

    def test_external_function_decl_node_creation(self):
        """测试外部函数声明节点创建"""
        from zhc.parser.ast_nodes import ASTNodeType, ParamDeclNode

        param = ParamDeclNode(
            name="参数1",
            param_type=PrimitiveTypeNode("整数型"),
            line=1,
            column=5,
        )

        func_decl = ExternalFunctionDeclNode(
            name="测试函数",
            return_type=PrimitiveTypeNode("整数型"),
            parameters=[param],
            c_name="test_func",
            library="libtest",
            line=1,
            column=1,
        )

        assert func_decl.node_type == ASTNodeType.EXTERNAL_FUNCTION_DECL
        assert func_decl.name == "测试函数"
        assert func_decl.c_name == "test_func"
        assert func_decl.library == "libtest"
        assert len(func_decl.parameters) == 1

    def test_external_block_accept_visitor(self):
        """测试外部块节点接受访问者"""
        from zhc.parser.ast_nodes import ASTVisitor

        class TestVisitor(ASTVisitor):
            def __init__(self):
                self.visited_external_block = False
                self.visited_external_func = False

            def visit_external_block(self, node):
                self.visited_external_block = True
                for decl in node.declarations:
                    decl.accept(self)
                return None

            def visit_external_function_decl(self, node):
                self.visited_external_func = True
                return None

            # 实现所有抽象方法（简化实现）
            def visit_program(self, node):
                return None

            def visit_function_decl(self, node):
                return None

            def visit_variable_decl(self, node):
                return None

            def visit_param_decl(self, node):
                return None

            def visit_struct_decl(self, node):
                return None

            def visit_enum_decl(self, node):
                return None

            def visit_union_decl(self, node):
                return None

            def visit_typedef_decl(self, node):
                return None

            def visit_module_decl(self, node):
                return None

            def visit_import_decl(self, node):
                return None

            def visit_block_stmt(self, node):
                return None

            def visit_if_stmt(self, node):
                return None

            def visit_while_stmt(self, node):
                return None

            def visit_for_stmt(self, node):
                return None

            def visit_do_while_stmt(self, node):
                return None

            def visit_return_stmt(self, node):
                return None

            def visit_break_stmt(self, node):
                return None

            def visit_continue_stmt(self, node):
                return None

            def visit_switch_stmt(self, node):
                return None

            def visit_case_stmt(self, node):
                return None

            def visit_default_stmt(self, node):
                return None

            def visit_goto_stmt(self, node):
                return None

            def visit_label_stmt(self, node):
                return None

            def visit_expr_stmt(self, node):
                return None

            def visit_binary_expr(self, node):
                return None

            def visit_unary_expr(self, node):
                return None

            def visit_ternary_expr(self, node):
                return None

            def visit_call_expr(self, node):
                return None

            def visit_assign_expr(self, node):
                return None

            def visit_member_expr(self, node):
                return None

            def visit_array_expr(self, node):
                return None

            def visit_cast_expr(self, node):
                return None

            def visit_sizeof_expr(self, node):
                return None

            def visit_identifier_expr(self, node):
                return None

            def visit_int_literal(self, node):
                return None

            def visit_float_literal(self, node):
                return None

            def visit_char_literal(self, node):
                return None

            def visit_string_literal(self, node):
                return None

            def visit_bool_literal(self, node):
                return None

            def visit_null_literal(self, node):
                return None

            def visit_array_init(self, node):
                return None

            def visit_struct_init(self, node):
                return None

            def visit_primitive_type(self, node):
                return None

            def visit_pointer_type(self, node):
                return None

            def visit_array_type(self, node):
                return None

            def visit_struct_type(self, node):
                return None

            def visit_function_type(self, node):
                return None

            def visit_auto_type(self, node):
                return None

        func_decl = ExternalFunctionDeclNode(
            name="测试",
            return_type=PrimitiveTypeNode("整数型"),
            parameters=[],
        )

        external_block = ExternalBlockNode(
            language="C",
            declarations=[func_decl],
        )

        visitor = TestVisitor()
        external_block.accept(visitor)

        assert visitor.visited_external_block
        assert visitor.visited_external_func


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
