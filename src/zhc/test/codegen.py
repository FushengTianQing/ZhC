#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代码生成器

将测试 AST 转换为 C 代码
"""

from typing import List
from .parser import (
    TestModuleNode,
    TestSuiteNode,
    TestFunctionNode,
    AssertionNode,
    ImportNode,
)


class TestCodeGenerator:
    """测试代码生成器"""

    def __init__(self):
        self.includes: List[str] = []
        self.global_setup: List[str] = []
        self.global_teardown: List[str] = []

    def generate(self, module: TestModuleNode) -> str:
        """
        生成完整的测试代码

        Args:
            module: 测试模块 AST

        Returns:
            C 代码字符串
        """
        lines = []

        # 生成头文件包含
        lines.extend(self._generate_includes())

        # 生成宏定义
        lines.extend(self._generate_macros())

        # 生成全局变量
        lines.extend(self._generate_globals())

        # 生成导入
        lines.extend(self._generate_imports(module.imports))

        # 生成测试函数声明
        lines.extend(self._generate_function_declarations(module.suites))

        # 生成测试函数实现
        lines.extend(self._generate_function_implementations(module.suites))

        # 生成测试运行器
        lines.extend(self._generate_test_runner(module))

        return "\n".join(lines)

    def _generate_includes(self) -> List[str]:
        """生成头文件包含"""
        return [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "#include <math.h>",
            "#include <time.h>",
            '#include "zhc_test.h"',
            "",
        ]

    def _generate_macros(self) -> List[str]:
        """生成宏定义"""
        return [
            "// 测试宏定义",
            "#define TEST_START() do { \\",
            '    printf("Running %s... ", __func__); \\',
            "    _zhc_test_start(__FILE__, __LINE__); \\",
            "} while(0)",
            "",
            "#define TEST_END() _zhc_test_end()",
            "",
        ]

    def _generate_globals(self) -> List[str]:
        """生成全局变量"""
        return [
            "// 全局测试状态",
            "int _test_pass_count = 0;",
            "int _test_fail_count = 0;",
            "int _test_skip_count = 0;",
            "",
        ]

    def _generate_imports(self, imports: List[ImportNode]) -> List[str]:
        """生成导入"""
        lines = ["// 导入模块", ""]
        for imp in imports:
            lines.append(f"// 导入: {imp.module_name}")
            if imp.alias:
                lines.append(f"// 别名: {imp.alias}")
        lines.append("")
        return lines

    def _generate_function_declarations(self, suites: List[TestSuiteNode]) -> List[str]:
        """生成测试函数声明"""
        lines = ["// 测试函数声明", ""]
        for suite in suites:
            for func in suite.functions:
                func_name = self._sanitize_name(f"{suite.name}_{func.name}")
                lines.append(f"void {func_name}(void);")
        lines.append("")
        return lines

    def _generate_function_implementations(
        self, suites: List[TestSuiteNode]
    ) -> List[str]:
        """生成测试函数实现"""
        lines = ["// 测试函数实现", ""]
        for suite in suites:
            for func in suite.functions:
                lines.extend(self._generate_function(suite.name, func))
                lines.append("")
            # 如果没有函数，也需要处理
            if not suite.functions:
                pass
        return lines

    def _generate_function(self, suite_name: str, func: TestFunctionNode) -> List[str]:
        """生成单个测试函数"""
        func_name = self._sanitize_name(f"{suite_name}_{func.name}")
        lines = [
            f"void {func_name}(void) {{",
            "    TEST_START();",
        ]

        # 处理跳过标记
        if func.skip:
            lines.append(f'    _zhc_test_skip("{func.skip_reason}");')
            lines.append("    return;")
        else:
            # 处理函数体中的断言
            for assertion in func.body.statements:
                if isinstance(assertion, AssertionNode):
                    lines.append(self._generate_assertion(assertion))
                else:
                    # 普通语句
                    content = assertion.content.rstrip(";")
                    lines.append(f"    {content};")

        lines.append("    TEST_END();")
        lines.append("}")
        return lines

    def _generate_assertion(self, assertion: AssertionNode) -> str:
        """生成断言代码"""
        assertion_map = {
            "assert_equal": "断言等于",
            "assert_not_equal": "断言不等于",
            "assert_true": "断言为真",
            "assert_false": "断言为假",
            "assert_null": "断言为空",
            "assert_not_null": "断言非空",
            "assert_float_equal": "断言浮点等于",
            "assert_string_equal": "断言字符串等于",
            "assert_greater": "断言大于",
            "assert_greater_equal": "断言大于等于",
            "assert_less": "断言小于",
            "assert_less_equal": "断言小于等于",
            "assert_in": "断言包含",
            "assert_not_in": "断言不包含",
            "assert_type": "断言类型",
            "assert_length": "断言长度",
            "assert_empty": "断言为空集合",
            "assert_not_empty": "断言不为空集合",
        }

        macro_name = assertion_map.get(
            assertion.assertion_type, assertion.assertion_type
        )

        if not assertion.args:
            return f"    {macro_name}();"

        args_str = ", ".join(assertion.args)

        if assertion.message:
            return f'    {macro_name}({args_str}, "{assertion.message}");'
        else:
            return f"    {macro_name}({args_str});"

    def _generate_test_runner(self, module: TestModuleNode) -> List[str]:
        """生成测试运行器"""
        lines = [
            "// 测试运行器",
            "int main(int argc, char* argv[]) {",
            '    printf("========================================\\n");',
            f'    printf("测试模块: {module.name}\\n");',
            '    printf("========================================\\n\\n");',
            "",
            "    _zhc_test_suite_start();",
            "",
        ]

        # 添加测试用例调用
        for suite in module.suites:
            lines.append(f'    printf("  [Suite: {suite.name}]\\n");')
            for func in suite.functions:
                full_name = self._sanitize_name(f"{suite.name}_{func.name}")
                lines.append(f"    {full_name}();")
            lines.append("")

        lines.extend(
            [
                "    _zhc_test_suite_end();",
                "",
                '    printf("========================================\\n");',
                '    printf("测试汇总:\\n");',
                '    printf("  通过: %d\\n", _test_pass_count);',
                '    printf("  失败: %d\\n", _test_fail_count);',
                '    printf("  跳过: %d\\n", _test_skip_count);',
                '    printf("========================================\\n");',
                "",
                "    return (_test_fail_count > 0) ? 1 : 0;",
                "}",
            ]
        )

        return lines

    def _sanitize_name(self, name: str) -> str:
        """清理函数名（替换非法字符）"""
        # 替换空格和特殊字符
        name = name.replace(" ", "_")
        name = name.replace("-", "_")
        name = name.replace("::", "_")
        name = name.replace("(", "")
        name = name.replace(")", "")
        name = name.replace('"', "")
        return name


def generate_test_code(module: TestModuleNode) -> str:
    """
    生成测试代码

    Args:
        module: 测试模块 AST

    Returns:
        C 代码字符串
    """
    generator = TestCodeGenerator()
    return generator.generate(module)


def generate_test_file(module: TestModuleNode, output_path: str) -> None:
    """
    生成测试文件

    Args:
        module: 测试模块 AST
        output_path: 输出文件路径
    """
    code = generate_test_code(module)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
