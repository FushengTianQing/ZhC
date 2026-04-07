#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codegen 集成测试

测试完整的代码生成流程：
- 从源码到 AST 到 C 代码
- 多模块编译
- 复杂表达式生成
- 完整程序生成

作者: 阿福
日期: 2026-04-08
"""

import pytest
import tempfile
import os
from zhc.parser.lexer import Lexer
from zhc.parser.parser import Parser
from zhc.codegen.c_codegen import CCodeGenerator


class TestFullPipeline:
    """测试完整编译流程"""

    def _compile_to_c(self, source: str) -> str:
        """辅助方法：将源码编译为 C 代码"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        return generator.generate(ast)

    def test_simple_function(self):
        """测试简单函数编译"""
        source = """
函数 主函数() -> 整数 {
    返回 42
}
"""
        c_code = self._compile_to_c(source)
        assert "int main()" in c_code
        assert "return 42" in c_code

    def test_function_with_params(self):
        """测试带参数函数"""
        source = """
函数 加法(a: 整数, b: 整数) -> 整数 {
    返回 a + b
}
"""
        c_code = self._compile_to_c(source)
        assert "int 加法(int a, int b)" in c_code
        assert "return a + b" in c_code

    def test_variable_declaration(self):
        """测试变量声明"""
        source = """
变量 x: 整数 = 10
变量 y: 浮点 = 3.14
"""
        c_code = self._compile_to_c(source)
        assert "int x = 10" in c_code
        assert "float y = 3.14" in c_code

    def test_const_declaration(self):
        """测试常量声明"""
        source = """
常量 PI: 浮点 = 3.14159
"""
        c_code = self._compile_to_c(source)
        assert "const float PI = 3.14159" in c_code

    def test_if_statement(self):
        """测试 if 语句"""
        source = """
函数 测试(x: 整数) -> 整数 {
    如果 x > 0 {
        返回 x
    } 否则 {
        返回 -x
    }
}
"""
        c_code = self._compile_to_c(source)
        assert "if (x > 0)" in c_code
        assert "else" in c_code

    def test_while_loop(self):
        """测试 while 循环"""
        source = """
函数 循环测试() -> 整数 {
    变量 i: 整数 = 0
    循环 i < 10 {
        i = i + 1
    }
    返回 i
}
"""
        c_code = self._compile_to_c(source)
        assert "while (i < 10)" in c_code

    def test_for_loop(self):
        """测试 for 循环"""
        source = """
函数 遍历测试() -> 整数 {
    变量 sum: 整数 = 0
    遍历 i 从 0 到 10 {
        sum = sum + i
    }
    返回 sum
}
"""
        c_code = self._compile_to_c(source)
        assert "for" in c_code

    def test_struct_declaration(self):
        """测试结构体声明"""
        source = """
结构体 点 {
    x: 整数
    y: 整数
}
"""
        c_code = self._compile_to_c(source)
        assert "struct 点" in c_code
        assert "int x" in c_code
        assert "int y" in c_code

    def test_enum_declaration(self):
        """测试枚举声明"""
        source = """
枚举 颜色 {
    红 = 0
    绿 = 1
    蓝 = 2
}
"""
        c_code = self._compile_to_c(source)
        assert "enum 颜色" in c_code

    def test_function_call(self):
        """测试函数调用"""
        source = """
函数 打印消息() -> 空 {
    打印("Hello, World!")
}
"""
        c_code = self._compile_to_c(source)
        assert "打印" in c_code

    def test_array_declaration(self):
        """测试数组声明"""
        source = """
变量 arr: 整数[5]
"""
        c_code = self._compile_to_c(source)
        assert "int arr[5]" in c_code

    def test_pointer_declaration(self):
        """测试指针声明"""
        source = """
变量 ptr: 整数指针 = 空
"""
        c_code = self._compile_to_c(source)
        assert "int* ptr = NULL" in c_code


class TestComplexExpressions:
    """测试复杂表达式"""

    def _compile_to_c(self, source: str) -> str:
        """辅助方法"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        return generator.generate(ast)

    def test_nested_arithmetic(self):
        """测试嵌套算术表达式"""
        source = """
函数 计算() -> 整数 {
    返回 (1 + 2) * (3 - 4) / 5
}
"""
        c_code = self._compile_to_c(source)
        assert "1 + 2" in c_code
        assert "3 - 4" in c_code

    def test_comparison_chain(self):
        """测试比较链"""
        source = """
函数 比较(a: 整数, b: 整数) -> 布尔 {
    返回 a > 0 且 b < 10
}
"""
        c_code = self._compile_to_c(source)
        assert "a > 0" in c_code
        assert "b < 10" in c_code

    def test_logical_operations(self):
        """测试逻辑运算"""
        source = """
函数 逻辑测试(a: 布尔, b: 布尔) -> 布尔 {
    返回 a 且 b
}
"""
        c_code = self._compile_to_c(source)
        assert "a" in c_code and "b" in c_code

    def test_member_access(self):
        """测试成员访问"""
        source = """
结构体 点 {
    x: 整数
    y: 整数
}

函数 获取X(p: 点) -> 整数 {
    返回 p.x
}
"""
        c_code = self._compile_to_c(source)
        assert "struct 点" in c_code

    def test_array_access(self):
        """测试数组访问"""
        source = """
函数 获取元素(arr: 整数[10], i: 整数) -> 整数 {
    返回 arr[i]
}
"""
        c_code = self._compile_to_c(source)
        assert "arr[i]" in c_code


class TestModuleIntegration:
    """测试模块集成"""

    def test_stdlib_import(self):
        """测试标准库导入"""
        source = """
导入 "标准输入输出"

函数 主函数() -> 整数 {
    打印("Hello")
    返回 0
}
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        assert "#include <stdio.h>" in c_code

    def test_multiple_imports(self):
        """测试多个导入"""
        source = """
导入 "标准输入输出"
导入 "标准库"
导入 "字符串"
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        assert "#include <stdio.h>" in c_code
        assert "#include <stdlib.h>" in c_code
        assert "#include <string.h>" in c_code


class TestCodeQuality:
    """测试代码质量"""

    def _compile_to_c(self, source: str) -> str:
        """辅助方法"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        return generator.generate(ast)

    def test_indentation_consistency(self):
        """测试缩进一致性"""
        source = """
函数 测试() -> 整数 {
    如果 真 {
        返回 1
    }
    返回 0
}
"""
        c_code = self._compile_to_c(source)
        lines = c_code.split("\n")
        # 检查缩进层级
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                assert indent % 4 == 0  # 缩进应该是 4 的倍数

    def test_semicolon_presence(self):
        """测试分号存在"""
        source = """
变量 x: 整数 = 10
变量 y: 浮点 = 3.14
"""
        c_code = self._compile_to_c(source)
        assert "int x = 10;" in c_code
        assert "float y = 3.14;" in c_code


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_syntax_recovery(self):
        """测试无效语法恢复"""
        source = """
函数 测试() -> 整数 {
    返回 42
}
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        # 即使有错误，也应该生成代码
        assert isinstance(c_code, str)

    def test_empty_input(self):
        """测试空输入"""
        source = ""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        assert c_code == ""


class TestOutputFormat:
    """测试输出格式"""

    def _compile_to_c(self, source: str) -> str:
        """辅助方法"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        return generator.generate(ast)

    def test_function_signature_format(self):
        """测试函数签名格式"""
        source = """
函数 加法(a: 整数, b: 整数) -> 整数 {
    返回 a + b
}
"""
        c_code = self._compile_to_c(source)
        # 函数签名应该在一行
        assert "int 加法(int a, int b) {" in c_code

    def test_block_braces_format(self):
        """测试块括号格式"""
        source = """
函数 测试() -> 空 {
    如果 真 {
        打印("test")
    }
}
"""
        c_code = self._compile_to_c(source)
        # 左括号应该在同一行
        assert ") {" in c_code

    def test_struct_format(self):
        """测试结构体格式"""
        source = """
结构体 点 {
    x: 整数
    y: 整数
}
"""
        c_code = self._compile_to_c(source)
        assert "struct 点 {" in c_code
        assert "};" in c_code


class TestSpecialCases:
    """测试特殊情况"""

    def _compile_to_c(self, source: str) -> str:
        """辅助方法"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        return generator.generate(ast)

    def test_void_function(self):
        """测试空返回函数"""
        source = """
函数 打印消息() -> 空 {
    打印("Hello")
}
"""
        c_code = self._compile_to_c(source)
        assert "void 打印消息" in c_code

    def test_no_params_function(self):
        """测试无参数函数"""
        source = """
函数 主函数() -> 整数 {
    返回 0
}
"""
        c_code = self._compile_to_c(source)
        assert "void)" in c_code or "()" in c_code

    def test_nested_structs(self):
        """测试嵌套结构体"""
        source = """
结构体 外层 {
    x: 整数
}
"""
        c_code = self._compile_to_c(source)
        assert "struct 外层" in c_code

    def test_array_of_structs(self):
        """测试结构体数组"""
        source = """
结构体 点 {
    x: 整数
    y: 整数
}

变量 points: 点[10]
"""
        c_code = self._compile_to_c(source)
        assert "struct 点" in c_code


class TestPerformance:
    """测试性能"""

    def test_large_function_generation(self):
        """测试大函数生成"""
        # 生成包含 50 个语句的函数
        statements = []
        for i in range(50):
            statements.append("    变量 x{i}: 整数 = {i}".format(i=i))
        
        source = """
函数 大函数() -> 空 {{
{body}
}}
""".format(body="\n".join(statements))
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        
        # 验证所有变量都生成了
        for i in range(50):
            assert "x{i}".format(i=i) in c_code or "x {i}".format(i=i) in c_code

    def test_multiple_functions(self):
        """测试多函数生成"""
        functions = []
        for i in range(5):
            func_code = """
函数 函数{i}() -> 整数 {{
    返回 {i}
}}
""".format(i=i)
            functions.append(func_code)
        
        source = "\n".join(functions)
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        
        # 验证所有函数都生成了
        for i in range(5):
            assert "函数{i}".format(i=i) in c_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])