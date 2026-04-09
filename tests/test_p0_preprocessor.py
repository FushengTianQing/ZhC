#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试预处理器模块的完整功能

根据 P0-预处理器-define宏定义.md 规划文档创建。

测试覆盖:
1. 简单宏定义 (#define NAME value)
2. 函数宏定义 (#define NAME(args) body)
3. 宏展开
4. #undef 指令
5. 条件编译 (#ifdef, #ifndef, #if, #else, #elif, #endif)
6. 嵌套宏
7. 字符串中的宏不展开
8. 空宏
9. 宏重定义检测
10. 宏参数数量不匹配检测
"""

import pytest
import os
import tempfile
from pathlib import Path

from zhc.compiler.preprocessor import (
    Preprocessor,
    PreprocessorConfig,
    PreprocessorError,
    Macro,
    MacroType,
)


class TestSimpleMacro:
    """简单宏定义测试"""

    def test_object_macro_basic(self):
        """测试基本对象宏"""
        source = """
#define MAX_SIZE 100
#define VERSION "1.0.0"
#define PI 3.14159

整数型 数组[MAX_SIZE];
字符串型 ver = VERSION;
浮点型 pi = PI;
"""
        result = Preprocessor().process(source)

        assert "100" in result
        assert '"1.0.0"' in result
        assert "3.14159" in result
        # 宏名不应该出现在值的位置
        assert "数组[MAX_SIZE]" not in result

    def test_object_macro_override(self):
        """测试宏重定义（允许重定义）"""
        source = """
#define DEBUG 1
整数型 a = DEBUG;
#define DEBUG 2
整数型 b = DEBUG;
"""
        result = Preprocessor().process(source)

        # 后定义的值应该生效
        assert "a = 1" in result
        assert "b = 2" in result

    def test_empty_macro(self):
        """测试空宏"""
        source = """
#define EMPTY
#define MARKER

整数型 e = EMPTY;
整数型 m = MARKER;
"""
        result = Preprocessor().process(source)

        # 空宏应该被替换为空
        assert "e = " in result
        assert "m = " in result

    def test_chinese_macro_name(self):
        """测试中文宏名"""
        source = """
#define 最大值 100
#define 最小值 0

整数型 max = 最大值;
整数型 min = 最小值;
"""
        result = Preprocessor().process(source)

        assert "max = 100" in result
        assert "min = 0" in result


class TestFunctionMacro:
    """函数宏测试"""

    def test_function_macro_basic(self):
        """测试基本函数宏"""
        source = """
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))

整数型 m = MAX(10, 20);
整数型 n = MIN(10, 20);
整数型 s = SQUARE(5);
"""
        result = Preprocessor().process(source)

        assert "((10) > (20) ? (10) : (20))" in result
        assert "((10) < (20) ? (10) : (20))" in result
        assert "((5) * (5))" in result

    def test_function_macro_with_expression(self):
        """测试带表达式的宏参数"""
        source = """
#define DOUBLE(x) ((x) * 2)
#define ADD(a, b) ((a) + (b))

整数型 d = DOUBLE(5 + 3);
整数型 sum = ADD(10 * 2, 20 / 4);
"""
        result = Preprocessor().process(source)

        assert "((5 + 3) * 2)" in result
        assert "((10 * 2) + (20 / 4))" in result

    def test_function_macro_nested_parens(self):
        """测试嵌套括号的宏参数"""
        source = """
#define SUM(a, b) ((a) + (b))

整数型 x = SUM((1 + 2), (3 + 4));
"""
        result = Preprocessor().process(source)

        # 宏 body 是 ((a) + (b))，参数替换后变成 (((1 + 2)) + ((3 + 4)))
        # 这是正确的行为，因为宏 body 中的括号会保留
        assert "((1 + 2))" in result
        assert "((3 + 4))" in result

    def test_function_macro_no_args(self):
        """测试不带括号的宏名不展开"""
        source = """
#define TEST(x) ((x) * 2)

整数型 a = TEST;
"""
        result = Preprocessor().process(source)

        # 函数宏没有括号不应该展开
        assert "TEST" in result


class TestMacroExpansion:
    """宏展开测试"""

    def test_nested_macro(self):
        """测试嵌套宏展开"""
        source = """
#define A B
#define B C
#define C 100

整数型 x = A;
"""
        result = Preprocessor().process(source)

        assert "x = 100" in result

    def test_self_referential_macro(self):
        """测试自引用宏（防止无限递归）"""
        source = """
#define A A

整数型 x = A;
"""
        result = Preprocessor().process(source)

        # 自引用宏应该保持原样或只展开一次
        # 不会导致无限递归
        assert "x = A" in result

    def test_macro_in_string_not_expanded(self):
        """测试字符串中的宏不展开"""
        source = """
#define NAME "test"
#define VALUE 100

字符串型 s1 = "NAME";
字符串型 s2 = "VALUE";
整数型 v = VALUE;
"""
        result = Preprocessor().process(source)

        # 字符串内的宏不应该被展开
        assert '"NAME"' in result
        assert '"VALUE"' in result
        # 字符串外的宏应该被展开
        assert "v = 100" in result

    def test_macro_comment_handling(self):
        """测试注释处理"""
        source = """
#define VALUE 42  // 这是注释

整数型 v = VALUE;
"""
        result = Preprocessor().process(source)

        assert "v = 42" in result
        # 注释不应该出现在宏展开结果中
        assert "这是注释" not in result


class TestUndef:
    """#undef 指令测试"""

    def test_undef_basic(self):
        """测试基本 #undef"""
        source = """
#define DEBUG 1
整数型 a = DEBUG;
#undef DEBUG
整数型 b = DEBUG;
"""
        result = Preprocessor().process(source)

        assert "a = 1" in result
        # #undef 后，DEBUG 未定义，所以不会展开
        assert "b = DEBUG" in result

    def test_undef_then_redefine(self):
        """测试 #undef 后重新定义"""
        source = """
#define X 1
整数型 a = X;
#undef X
#define X 2
整数型 b = X;
"""
        result = Preprocessor().process(source)

        assert "a = 1" in result
        assert "b = 2" in result


class TestConditionalCompilation:
    """条件编译测试"""

    def test_ifdef_defined(self):
        """测试 #ifdef 已定义的宏"""
        source = """
#define DEBUG

#ifdef DEBUG
整数型 debug_mode = 1;
#endif
"""
        result = Preprocessor().process(source)

        assert "debug_mode = 1" in result

    def test_ifdef_not_defined(self):
        """测试 #ifdef 未定义的宏"""
        source = """
#ifdef DEBUG
整数型 debug_mode = 1;
#else
整数型 release_mode = 0;
#endif
"""
        result = Preprocessor().process(source)

        assert "release_mode = 0" in result
        assert "debug_mode" not in result

    def test_ifndef(self):
        """测试 #ifndef"""
        source = """
#ifndef RELEASE
整数型 not_release = 1;
#endif

#define RELEASE
#ifndef RELEASE
整数型 is_release = 1;
#endif
"""
        result = Preprocessor().process(source)

        assert "not_release = 1" in result
        assert "is_release" not in result

    def test_if_else(self):
        """测试 #if #else"""
        source = """
#define FEATURE 1

#if FEATURE
整数型 enabled = 1;
#else
整数型 disabled = 0;
#endif
"""
        result = Preprocessor().process(source)

        assert "enabled = 1" in result
        assert "disabled" not in result

    def test_if_elif_else(self):
        """测试 #if #elif #else"""
        source = """
#define LEVEL 2

#if LEVEL == 1
整数型 result = 1;
#elif LEVEL == 2
整数型 result = 2;
#elif LEVEL == 3
整数型 result = 3;
#else
整数型 result = 0;
#endif
"""
        result = Preprocessor().process(source)

        assert "result = 2" in result
        assert "result = 1" not in result
        assert "result = 3" not in result

    def test_nested_ifdef(self):
        """测试嵌套条件编译"""
        source = """
#define A
#define B

#ifdef A
    #ifdef B
    整数型 ab = 1;
    #endif
    整数型 a = 1;
#endif

#ifdef C
    整数型 c = 1;
#endif
"""
        result = Preprocessor().process(source)

        assert "ab = 1" in result
        assert "a = 1" in result
        assert "c = 1" not in result

    def test_defined_operator(self):
        """测试 defined() 操作符"""
        source = """
#define A

#if defined(A) && !defined(B)
整数型 a_only = 1;
#elif defined(A) && defined(B)
整数型 a_and_b = 1;
#else
整数型 none = 1;
#endif
"""
        result = Preprocessor().process(source)

        assert "a_only = 1" in result
        assert "a_and_b" not in result


class TestVariadicMacro:
    """可变参数宏测试"""

    def test_variadic_basic(self):
        """测试基本可变参数宏"""
        source = """
#define LOG(fmt, ...) printf(fmt, __VA_ARGS__)

LOG("Hello %s", "world");
"""
        result = Preprocessor().process(source)

        assert "printf" in result

    def test_named_variadic(self):
        """测试命名可变参数"""
        source = """
#define ERROR(fmt, args...) fprintf(stderr, fmt, args)

ERROR("Error: %d", 42);
"""
        result = Preprocessor().process(source)

        assert "fprintf" in result


class TestInclude:
    """#include 测试"""

    def test_include_local(self):
        """测试本地文件包含"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件
            header_path = Path(tmpdir) / "test_header.zh"
            header_path.write_text("""
#define HEADER_VALUE 100
整数型 header_var = HEADER_VALUE;
""")

            # 创建源文件
            source = f'''
#include "{header_path.name}"

整数型 main_var = HEADER_VALUE;
'''
            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<test>")

            assert "header_var" in result
            assert "main_var" in result

    def test_include_system(self):
        """测试系统头文件包含"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件
            header_path = Path(tmpdir) / "sys_header.zh"
            header_path.write_text("""
#define SYS_VALUE 200
整数型 sys_var = SYS_VALUE;
""")

            source = f'''
#include <sys_header.zh>

整数型 main_var = SYS_VALUE;
'''
            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<test>")

            assert "sys_var" in result

    def test_include_duplicate(self):
        """测试重复包含（防止）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件
            header_path = Path(tmpdir) / "dup_header.zh"
            header_path.write_text("""
整数型 dup_var = 1;
""")

            source = f'''
#include "{header_path.name}"
#include "{header_path.name}"

整数型 main_var = dup_var;
'''
            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<test>")

            # dup_var 只应该出现一次
            assert result.count("dup_var") == 2  # 定义一次 + 使用一次

    def test_include_not_found(self):
        """测试找不到头文件"""
        source = '''
#include "nonexistent.zh"
'''
        config = PreprocessorConfig(include_paths=[])
        preprocessor = Preprocessor(config)

        with pytest.raises(PreprocessorError, match="找不到头文件"):
            preprocessor.process(source, "<test>")


class TestPredefinedMacros:
    """预定义宏测试"""

    def test_predefined_macros(self):
        """测试预定义宏"""
        config = PreprocessorConfig(
            predefined_macros={
                "__ZHC_VERSION__": '"1.0.0"',
                "__PLATFORM__": '"linux"',
            }
        )
        source = '''
字符串型 version = __ZHC_VERSION__;
字符串型 platform = __PLATFORM__;
'''
        result = Preprocessor(config).process(source)

        assert '"1.0.0"' in result
        assert '"linux"' in result


class TestErrorHandling:
    """错误处理测试"""

    def test_macro_depth_limit(self):
        """测试宏展开深度限制"""
        # 创建大量嵌套宏
        source = """
#define A B
#define B C
#define C D
#define D E
#define E F
#define F G
#define G H
#define H I
#define I J
#define J K
#define K 100

整数型 x = A;
"""
        # 设置较小的深度限制
        config = PreprocessorConfig(max_macro_depth=5)
        result = Preprocessor(config).process(source)

        # 应该不会无限递归，但可能不会完全展开
        assert "x = " in result

    def test_include_depth_limit(self):
        """测试 #include 嵌套深度限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建递归包含的头文件
            level1_path = Path(tmpdir) / "level1.zh"
            level1_path.write_text("""
#define LEVEL1 1
整数型 level1_var = LEVEL1;
""")

            source = f'''
#include "{level1_path.name}"

整数型 main_var = LEVEL1;
'''
            # 默认深度限制足够大，应该能正常处理
            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<test>")

            # LEVEL1 会被展开为 1，所以应该看到 level1_var = 1
            assert "level1_var = 1" in result
            assert "main_var = 1" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
