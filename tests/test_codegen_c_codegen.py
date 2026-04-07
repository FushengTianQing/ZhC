#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCodeGenerator 单元测试

测试 CCodeGenerator 类的核心功能：
- 类型转换
- 函数声明生成
- 变量声明生成
- 表达式生成
- 语句生成

作者: 阿福
日期: 2026-04-08
"""

import pytest
from zhc.parser.ast_nodes import (
    ProgramNode, ModuleDeclNode, ImportDeclNode,
    FunctionDeclNode, StructDeclNode, EnumDeclNode, UnionDeclNode,
    VariableDeclNode, ParamDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    ReturnStmtNode, ExprStmtNode,
    BinaryExprNode, UnaryExprNode, AssignExprNode, CallExprNode,
    IdentifierExprNode, IntLiteralNode, FloatLiteralNode, StringLiteralNode,
    BoolLiteralNode, NullLiteralNode,
    PrimitiveTypeNode, PointerTypeNode, ArrayTypeNode, FunctionTypeNode,
)
from zhc.codegen.c_codegen import CCodeGenerator


class TestCCodeGeneratorInit:
    """测试 CCodeGenerator 初始化"""

    def test_default_init(self):
        """测试默认初始化"""
        gen = CCodeGenerator()
        assert gen.indent == 0
        assert gen.indent_str == "    "
        assert gen.output_lines == []
        assert gen._debug_manager is None

    def test_custom_indent(self):
        """测试自定义缩进"""
        gen = CCodeGenerator(indent_str="  ")
        assert gen.indent_str == "  "

    def test_with_debug_manager(self):
        """测试带调试管理器初始化"""
        # Mock debug manager
        debug_mgr = object()
        gen = CCodeGenerator(debug_manager=debug_mgr)
        assert gen._debug_manager is debug_mgr


class TestTypeEmission:
    """测试类型转换"""

    def test_primitive_type_int(self):
        """测试整数类型"""
        gen = CCodeGenerator()
        type_node = PrimitiveTypeNode(name="整数型")
        result = gen._emit_type(type_node)
        assert result == "int"

    def test_primitive_type_float(self):
        """测试浮点类型"""
        gen = CCodeGenerator()
        type_node = PrimitiveTypeNode(name="浮点型")
        result = gen._emit_type(type_node)
        assert result == "float"

    def test_primitive_type_char(self):
        """测试字符类型"""
        gen = CCodeGenerator()
        type_node = PrimitiveTypeNode(name="字符型")
        result = gen._emit_type(type_node)
        assert result == "char"

    def test_primitive_type_void(self):
        """测试空类型"""
        gen = CCodeGenerator()
        type_node = PrimitiveTypeNode(name="空型")
        result = gen._emit_type(type_node)
        assert result == "void"

    def test_pointer_type(self):
        """测试指针类型"""
        gen = CCodeGenerator()
        base_type = PrimitiveTypeNode(name="整数型")
        type_node = PointerTypeNode(base_type=base_type)
        result = gen._emit_type(type_node)
        assert result == "int*"

    def test_array_type_with_size(self):
        """测试数组类型（有大小）"""
        gen = CCodeGenerator()
        elem_type = PrimitiveTypeNode(name="整数型")
        size = IntLiteralNode(value=10)
        type_node = ArrayTypeNode(element_type=elem_type, size=size)
        result = gen._emit_type(type_node)
        assert result == "int[10]"

    def test_array_type_no_size(self):
        """测试数组类型（无大小）"""
        gen = CCodeGenerator()
        elem_type = PrimitiveTypeNode(name="字符型")
        type_node = ArrayTypeNode(element_type=elem_type, size=None)
        result = gen._emit_type(type_node)
        assert result == "char[]"

    def test_function_type(self):
        """测试函数指针类型"""
        gen = CCodeGenerator()
        ret_type = PrimitiveTypeNode(name="整数型")
        param_types = [PrimitiveTypeNode(name="整数型"), PrimitiveTypeNode(name="浮点型")]
        type_node = FunctionTypeNode(return_type=ret_type, param_types=param_types)
        result = gen._emit_type(type_node)
        assert result == "int (*)(int, float)"


class TestFunctionDeclaration:
    """测试函数声明生成"""

    def test_simple_function(self):
        """测试简单函数"""
        gen = CCodeGenerator()
        ret_type = PrimitiveTypeNode(name="整数型")
        body = BlockStmtNode(statements=[
            ReturnStmtNode(value=IntLiteralNode(value=42))
        ])
        func = FunctionDeclNode(
            name="测试函数",
            return_type=ret_type,
            params=[],
            body=body
        )
        code = gen.generate(ProgramNode(declarations=[func]))
        assert "int 测试函数(void)" in code
        assert "return 42" in code

    def test_function_with_params(self):
        """测试带参数函数"""
        gen = CCodeGenerator()
        ret_type = PrimitiveTypeNode(name="整数型")
        params = [
            ParamDeclNode(name="a", param_type=PrimitiveTypeNode(name="整数型")),
            ParamDeclNode(name="b", param_type=PrimitiveTypeNode(name="浮点型")),
        ]
        body = BlockStmtNode(statements=[
            ReturnStmtNode(value=IdentifierExprNode(name="a"))
        ])
        func = FunctionDeclNode(
            name="加法",
            return_type=ret_type,
            params=params,
            body=body
        )
        code = gen.generate(ProgramNode(declarations=[func]))
        assert "int 加法(int a, float b)" in code

    def test_void_function(self):
        """测试空返回函数"""
        gen = CCodeGenerator()
        ret_type = PrimitiveTypeNode(name="空型")
        body = BlockStmtNode(statements=[])
        func = FunctionDeclNode(
            name="打印",
            return_type=ret_type,
            params=[],
            body=body
        )
        code = gen.generate(ProgramNode(declarations=[func]))
        # 函数名会被解析为 printf
        assert "void printf(void)" in code or "void 打印(void)" in code


class TestVariableDeclaration:
    """测试变量声明生成"""

    def test_simple_variable(self):
        """测试简单变量"""
        gen = CCodeGenerator()
        var = VariableDeclNode(
            name="x",
            var_type=PrimitiveTypeNode(name="整数型"),
            init=IntLiteralNode(value=10),
            is_const=False
        )
        code = gen.generate(ProgramNode(declarations=[var]))
        assert "int x = 10" in code

    def test_const_variable(self):
        """测试常量"""
        gen = CCodeGenerator()
        var = VariableDeclNode(
            name="PI",
            var_type=PrimitiveTypeNode(name="浮点型"),
            init=FloatLiteralNode(value=3.14),
            is_const=True
        )
        code = gen.generate(ProgramNode(declarations=[var]))
        assert "const float PI = 3.14" in code

    def test_pointer_variable(self):
        """测试指针变量"""
        gen = CCodeGenerator()
        var = VariableDeclNode(
            name="ptr",
            var_type=PointerTypeNode(base_type=PrimitiveTypeNode(name="整数型")),
            init=NullLiteralNode(),
            is_const=False
        )
        code = gen.generate(ProgramNode(declarations=[var]))
        assert "int* ptr = NULL" in code

    def test_array_variable(self):
        """测试数组变量"""
        gen = CCodeGenerator()
        var = VariableDeclNode(
            name="arr",
            var_type=ArrayTypeNode(
                element_type=PrimitiveTypeNode(name="整数型"),
                size=IntLiteralNode(value=5)
            ),
            init=None,
            is_const=False
        )
        code = gen.generate(ProgramNode(declarations=[var]))
        assert "int arr[5]" in code


class TestExpressionGeneration:
    """测试表达式生成"""

    def test_int_literal(self):
        """测试整数字面量"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=IntLiteralNode(value=42))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "42" in code

    def test_float_literal(self):
        """测试浮点字面量"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=FloatLiteralNode(value=3.14))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "3.14" in code

    def test_string_literal(self):
        """测试字符串字面量"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=StringLiteralNode(value="hello"))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert '"hello"' in code

    def test_bool_literal_true(self):
        """测试布尔字面量（真）"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=BoolLiteralNode(value=True))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "true" in code or "1" in code

    def test_bool_literal_false(self):
        """测试布尔字面量（假）"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=BoolLiteralNode(value=False))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "false" in code or "0" in code

    def test_null_literal(self):
        """测试空指针字面量"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=NullLiteralNode())
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "NULL" in code

    def test_identifier(self):
        """测试标识符"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=IdentifierExprNode(name="x"))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "x" in code

    def test_binary_add(self):
        """测试二元加法"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=BinaryExprNode(
            operator="+",
            left=IntLiteralNode(value=1),
            right=IntLiteralNode(value=2)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "1 + 2" in code

    def test_binary_sub(self):
        """测试二元减法"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=BinaryExprNode(
            operator="-",
            left=IntLiteralNode(value=5),
            right=IntLiteralNode(value=3)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "5 - 3" in code

    def test_binary_mul(self):
        """测试二元乘法"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=BinaryExprNode(
            operator="*",
            left=IntLiteralNode(value=2),
            right=IntLiteralNode(value=3)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "2 * 3" in code

    def test_binary_div(self):
        """测试二元除法"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=BinaryExprNode(
            operator="/",
            left=IntLiteralNode(value=10),
            right=IntLiteralNode(value=2)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "10 / 2" in code

    def test_unary_neg(self):
        """测试一元负号"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=UnaryExprNode(
            operator="-",
            operand=IntLiteralNode(value=5)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "-5" in code

    def test_unary_not(self):
        """测试一元逻辑非"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=UnaryExprNode(
            operator="!",
            operand=BoolLiteralNode(value=True)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "!" in code

    def test_call_expr(self):
        """测试函数调用"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=CallExprNode(
            callee=IdentifierExprNode(name="打印"),
            args=[StringLiteralNode(value="hello")]
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        # 函数名会被解析为 printf
        assert "printf" in code or "打印" in code

    def test_assign_expr(self):
        """测试赋值表达式"""
        gen = CCodeGenerator()
        expr = ExprStmtNode(expr=AssignExprNode(
            target=IdentifierExprNode(name="x"),
            value=IntLiteralNode(value=10)
        ))
        code = gen.generate(ProgramNode(declarations=[expr]))
        assert "x = 10" in code


class TestStatementGeneration:
    """测试语句生成"""

    def test_if_stmt(self):
        """测试 if 语句"""
        gen = CCodeGenerator()
        stmt = IfStmtNode(
            condition=BoolLiteralNode(value=True),
            then_branch=BlockStmtNode(statements=[
                ExprStmtNode(expr=IntLiteralNode(value=1))
            ]),
            else_branch=None
        )
        code = gen.generate(ProgramNode(declarations=[stmt]))
        assert "if" in code

    def test_if_else_stmt(self):
        """测试 if-else 语句"""
        gen = CCodeGenerator()
        stmt = IfStmtNode(
            condition=BoolLiteralNode(value=True),
            then_branch=BlockStmtNode(statements=[
                ExprStmtNode(expr=IntLiteralNode(value=1))
            ]),
            else_branch=BlockStmtNode(statements=[
                ExprStmtNode(expr=IntLiteralNode(value=2))
            ])
        )
        code = gen.generate(ProgramNode(declarations=[stmt]))
        assert "if" in code
        assert "else" in code

    def test_while_stmt(self):
        """测试 while 语句"""
        gen = CCodeGenerator()
        stmt = WhileStmtNode(
            condition=BoolLiteralNode(value=True),
            body=BlockStmtNode(statements=[
                ExprStmtNode(expr=IntLiteralNode(value=1))
            ])
        )
        code = gen.generate(ProgramNode(declarations=[stmt]))
        assert "while" in code

    def test_for_stmt(self):
        """测试 for 语句"""
        gen = CCodeGenerator()
        stmt = ForStmtNode(
            init=VariableDeclNode(
                name="i",
                var_type=PrimitiveTypeNode(name="整数型"),
                init=IntLiteralNode(value=0),
                is_const=False
            ),
            condition=BinaryExprNode(
                operator="<",
                left=IdentifierExprNode(name="i"),
                right=IntLiteralNode(value=10)
            ),
            update=AssignExprNode(
                target=IdentifierExprNode(name="i"),
                value=BinaryExprNode(
                    operator="+",
                    left=IdentifierExprNode(name="i"),
                    right=IntLiteralNode(value=1)
                )
            ),
            body=BlockStmtNode(statements=[
                ExprStmtNode(expr=IdentifierExprNode(name="i"))
            ])
        )
        code = gen.generate(ProgramNode(declarations=[stmt]))
        assert "for" in code

    def test_return_stmt(self):
        """测试 return 语句"""
        gen = CCodeGenerator()
        stmt = ReturnStmtNode(value=IntLiteralNode(value=42))
        code = gen.generate(ProgramNode(declarations=[stmt]))
        assert "return 42" in code

    def test_return_void(self):
        """测试空 return"""
        gen = CCodeGenerator()
        stmt = ReturnStmtNode(value=None)
        code = gen.generate(ProgramNode(declarations=[stmt]))
        assert "return" in code


class TestStructDeclaration:
    """测试结构体声明生成"""

    def test_simple_struct(self):
        """测试简单结构体"""
        gen = CCodeGenerator()
        struct = StructDeclNode(
            name="Point",
            members=[
                VariableDeclNode(
                    name="x",
                    var_type=PrimitiveTypeNode(name="整数型"),
                    init=None,
                    is_const=False
                ),
                VariableDeclNode(
                    name="y",
                    var_type=PrimitiveTypeNode(name="整数型"),
                    init=None,
                    is_const=False
                ),
            ]
        )
        code = gen.generate(ProgramNode(declarations=[struct]))
        assert "struct Point" in code
        assert "int x" in code
        assert "int y" in code


class TestEnumDeclaration:
    """测试枚举声明生成"""

    def test_simple_enum(self):
        """测试简单枚举"""
        gen = CCodeGenerator()
        enum = EnumDeclNode(
            name="Color",
            values=[
                ("RED", IntLiteralNode(value=0)),
                ("GREEN", IntLiteralNode(value=1)),
                ("BLUE", IntLiteralNode(value=2)),
            ]
        )
        code = gen.generate(ProgramNode(declarations=[enum]))
        assert "enum Color" in code
        assert "RED = 0" in code
        assert "GREEN = 1" in code
        assert "BLUE = 2" in code


class TestModuleDeclaration:
    """测试模块声明生成"""

    def test_module_with_imports(self):
        """测试带导入的模块"""
        gen = CCodeGenerator()
        module = ModuleDeclNode(
            name="标准输入输出",
            imports=["标准库"],
            exports=["打印"],
            body=[]
        )
        code = gen.generate(ProgramNode(declarations=[module]))
        assert "#include <stdio.h>" in code
        assert "#include <stdlib.h>" in code

    def test_import_decl(self):
        """测试导入声明"""
        gen = CCodeGenerator()
        import_decl = ImportDeclNode(
            module_name="标准输入输出",
            symbols=[]
        )
        code = gen.generate(ProgramNode(declarations=[import_decl]))
        assert "#include <stdio.h>" in code


class TestIndentation:
    """测试缩进控制"""

    def test_indent_increase(self):
        """测试缩进增加"""
        gen = CCodeGenerator()
        gen.indent = 0
        gen._emit("line1")
        gen.indent += 1
        gen._emit("line2")
        assert gen.output_lines[0] == "line1"
        assert gen.output_lines[1] == "    line2"

    def test_indent_decrease(self):
        """测试缩进减少"""
        gen = CCodeGenerator()
        gen.indent = 1
        gen._emit("line1")
        gen.indent -= 1
        gen._emit("line2")
        assert gen.output_lines[0] == "    line1"
        assert gen.output_lines[1] == "line2"


class TestGenerateMethod:
    """测试 generate 方法"""

    def test_generate_clears_output(self):
        """测试 generate 清空输出"""
        gen = CCodeGenerator()
        gen.output_lines = ["old content"]
        program = ProgramNode(declarations=[])
        code = gen.generate(program)
        assert "old content" not in code

    def test_generate_returns_string(self):
        """测试 generate 返回字符串"""
        gen = CCodeGenerator()
        program = ProgramNode(declarations=[
            VariableDeclNode(
                name="x",
                var_type=PrimitiveTypeNode(name="整数型"),
                init=IntLiteralNode(value=1),
                is_const=False
            )
        ])
        code = gen.generate(program)
        assert isinstance(code, str)
        assert "int x = 1" in code


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_program(self):
        """测试空程序"""
        gen = CCodeGenerator()
        program = ProgramNode(declarations=[])
        code = gen.generate(program)
        assert code == ""

    def test_nested_blocks(self):
        """测试嵌套块"""
        gen = CCodeGenerator()
        stmt = IfStmtNode(
            condition=BoolLiteralNode(value=True),
            then_branch=BlockStmtNode(statements=[
                IfStmtNode(
                    condition=BoolLiteralNode(value=False),
                    then_branch=BlockStmtNode(statements=[
                        ExprStmtNode(expr=IntLiteralNode(value=1))
                    ]),
                    else_branch=None
                )
            ]),
            else_branch=None
        )
        code = gen.generate(ProgramNode(declarations=[stmt]))
        # 检查有嵌套的 if 语句
        assert code.count("if") >= 2

    def test_function_pointer_param(self):
        """测试函数指针参数"""
        gen = CCodeGenerator()
        func_type = FunctionTypeNode(
            return_type=PrimitiveTypeNode(name="整数型"),
            param_types=[PrimitiveTypeNode(name="整数型")]
        )
        ptr_type = PointerTypeNode(base_type=func_type)
        params = [ParamDeclNode(name="callback", param_type=ptr_type)]
        func = FunctionDeclNode(
            name="注册",
            return_type=PrimitiveTypeNode(name="空型"),
            params=params,
            body=BlockStmtNode(statements=[])
        )
        code = gen.generate(ProgramNode(declarations=[func]))
        assert "int (*callback)(int)" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])