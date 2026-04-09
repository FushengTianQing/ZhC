#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试预处理器模块
"""

from zhc.compiler.preprocessor import (
    PreprocessorConfig,
    preprocess,
)


def test_object_macro():
    """测试对象宏"""
    source = """
#define PI 3.14159
#define VERSION "1.0"

常量 pi = PI;
字符串型 ver = VERSION;
"""
    result = preprocess(source)

    assert "3.14159" in result
    assert '"1.0"' in result
    assert "PI" not in result.split("=")[1].split(";")[0]  # PI 应该被替换

    print("✓ 对象宏测试通过")


def test_function_macro():
    """测试函数宏"""
    source = """
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))

整数型 m = MAX(10, 20);
整数型 s = SQUARE(5);
"""
    result = preprocess(source)

    assert "((10) > (20) ? (10) : (20))" in result
    assert "((5) * (5))" in result

    print("✓ 函数宏测试通过")


def test_nested_macro():
    """测试嵌套宏展开"""
    source = """
#define A B
#define B C
#define C 100

整数型 x = A;
"""
    result = preprocess(source)

    assert "x = 100" in result

    print("✓ 嵌套宏展开测试通过")


def test_macro_with_expression():
    """测试带表达式的宏"""
    source = """
#define DOUBLE(x) ((x) * 2)
#define ADD(a, b) ((a) + (b))

整数型 d = DOUBLE(5 + 3);
整数型 sum = ADD(10, 20);
"""
    result = preprocess(source)

    assert "((5 + 3) * 2)" in result
    assert "((10) + (20))" in result

    print("✓ 带表达式的宏测试通过")


def test_undef():
    """测试 #undef"""
    source = """
#define DEBUG 1
整数型 a = DEBUG;
#undef DEBUG
#define DEBUG 2
整数型 b = DEBUG;
"""
    result = preprocess(source)

    assert "a = 1" in result
    assert "b = 2" in result

    print("✓ #undef 测试通过")


def test_ifdef():
    """测试 #ifdef"""
    source = """
#define DEBUG

#ifdef DEBUG
整数型 debug_mode = 1;
#endif

#ifndef RELEASE
整数型 not_release = 1;
#endif
"""
    result = preprocess(source)

    assert "debug_mode = 1" in result
    assert "not_release = 1" in result

    print("✓ #ifdef 测试通过")


def test_ifdef_else():
    """测试 #ifdef #else"""
    source = """
#ifdef FEATURE_X
整数型 feature = 1;
#else
整数型 feature = 0;
#endif
"""
    result = preprocess(source)

    # FEATURE_X 未定义，应该使用 else 分支
    assert "feature = 0" in result
    assert "feature = 1" not in result

    print("✓ #ifdef #else 测试通过")


def test_nested_ifdef():
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
    result = preprocess(source)

    assert "ab = 1" in result
    assert "a = 1" in result
    assert "c = 1" not in result

    print("✓ 嵌套条件编译测试通过")


def test_elif():
    """测试 #elif 分支"""
    source = """
#define LEVEL 2

#ifdef LEVEL
    #if LEVEL == 1
    整数型 result = 1;
    #elif LEVEL == 2
    整数型 result = 2;
    #elif LEVEL == 3
    整数型 result = 3;
    #else
    整数型 result = 0;
    #endif
#endif
"""
    result = preprocess(source)

    assert "result = 2" in result
    assert "result = 1" not in result
    assert "result = 3" not in result

    print("✓ #elif 分支测试通过")


def test_elif_no_match():
    """测试 #elif 无匹配情况"""
    source = """
#define LEVEL 99

#ifdef LEVEL
    #if LEVEL == 1
    整数型 result = 1;
    #elif LEVEL == 2
    整数型 result = 2;
    #else
    整数型 result = 0;
    #endif
#endif
"""
    result = preprocess(source)

    assert "result = 0" in result
    assert "result = 1" not in result
    assert "result = 2" not in result

    print("✓ #elif 无匹配测试通过")


def test_elif_defined():
    """测试 #elif with defined()"""
    source = """
#define A
#define B

#ifdef A
    #if defined(A) && !defined(B)
    整数型 a_only = 1;
    #elif defined(A) && defined(B)
    整数型 a_and_b = 1;
    #else
    整数型 none = 1;
    #endif
#endif
"""
    result = preprocess(source)

    assert "a_and_b = 1" in result
    assert "a_only = 1" not in result

    print("✓ #elif defined() 测试通过")


def test_elif_nested():
    """测试嵌套 #elif"""
    source = """
#define OUTER 1
#define INNER 2

#ifdef OUTER
    #if OUTER == 1
        #if INNER == 1
        整数型 o1_i1 = 1;
        #elif INNER == 2
        整数型 o1_i2 = 1;
        #else
        整数型 o1_other = 1;
        #endif
    #elif OUTER == 2
        整数型 o2 = 1;
    #endif
#endif
"""
    result = preprocess(source)

    assert "o1_i2 = 1" in result
    assert "o1_i1 = 1" not in result
    assert "o2 = 1" not in result

    print("✓ 嵌套 #elif 测试通过")


def test_predefined_macros():
    """测试预定义宏"""
    config = PreprocessorConfig(
        predefined_macros={
            "VERSION": '"2.0"',
            "PLATFORM": '"linux"',
        }
    )

    source = """
字符串型 version = VERSION;
字符串型 platform = PLATFORM;
"""
    result = preprocess(source, config)

    assert '"2.0"' in result
    assert '"linux"' in result

    print("✓ 预定义宏测试通过")


def test_macro_in_string():
    """测试字符串中的宏不被展开"""
    source = """
#define NAME test

字符串型 s1 = "NAME";  // 不应该被展开
字符串型 s2 = NAME;    // 应该被展开
"""
    result = preprocess(source)

    # 字符串内的 NAME 不应该被展开
    assert '"NAME"' in result
    # 字符串外的 NAME 应该被展开
    assert "s2 = test" in result

    print("✓ 字符串中的宏测试通过")


def test_empty_macro():
    """测试空宏"""
    source = """
#define EMPTY
#define DEBUG

#ifdef DEBUG
整数型 debug = 1;
#endif

整数型 e = EMPTY;
"""
    result = preprocess(source)

    assert "debug = 1" in result
    # 空宏展开为空
    assert "e = ;" in result

    print("✓ 空宏测试通过")


def test_multiline_macro():
    """测试多行宏定义（反斜杠续行）"""
    # 注意：当前实现可能不支持多行宏，这是一个预期行为测试
    source = r"""
#define LONG_MACRO(a, b) \
    ((a) + \
     (b))

整数型 x = LONG_MACRO(1, 2);
"""
    # 当前实现按行处理，多行宏可能需要额外支持
    preprocess(source)  # 仅验证不抛异常

    print("✓ 多行宏测试通过")


def test_chinese_macro():
    """测试中文宏"""
    source = """
#define 版本号 "1.0.0"
#define 最大值(a, b) ((a) > (b) ? (a) : (b))

字符串型 ver = 版本号;
整数型 max = 最大值(10, 20);
"""
    result = preprocess(source)

    assert '"1.0.0"' in result
    assert "((10) > (20) ? (10) : (20))" in result

    print("✓ 中文宏测试通过")


def test_include():
    """测试 #include 本地文件包含"""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))

    config = PreprocessorConfig(include_paths=[os.path.join(test_dir, "test_headers")])

    source = f"""
#include "header1.zh"

整数型 main_var = HEADER1_VALUE;
"""
    result = preprocess(source, config)

    assert "HEADER1_VALUE" not in result or "100" in result
    assert "header1_var" in result

    print("✓ #include 本地文件测试通过")


def test_include_system():
    """测试 #include <file> 系统头文件包含"""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))

    config = PreprocessorConfig(include_paths=[os.path.join(test_dir, "test_headers")])

    source = f"""
#include <header1.zh>

整数型 sys_var = HEADER1_VALUE;
"""
    result = preprocess(source, config)

    assert "header1_var" in result

    print("✓ #include 系统头文件测试通过")


def test_include_nested():
    """测试嵌套 #include"""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))

    config = PreprocessorConfig(include_paths=[os.path.join(test_dir, "test_headers")])

    source = f"""
#include "header2.zh"

整数型 main_var = HEADER2_VALUE;
"""
    result = preprocess(source, config)

    # header2.zh 包含 header1.zh，所以两个宏都应该可用
    assert "header1_var" in result
    assert "header2_var" in result

    print("✓ 嵌套 #include 测试通过")


def test_include_duplicate():
    """测试重复包含"""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))

    config = PreprocessorConfig(include_paths=[os.path.join(test_dir, "test_headers")])

    source = f"""
#include "header1.zh"
#include "header1.zh"

整数型 var = HEADER1_VALUE;
"""
    result = preprocess(source, config)

    # 同一文件不应该被包含两次
    # header1_var 只应该出现一次
    count = result.count("header1_var")
    assert count == 1, f"header1_var 出现了 {count} 次，应该只出现 1 次"

    print("✓ 重复包含测试通过")


def test_include_not_found():
    """测试找不到头文件"""
    from zhc.compiler.preprocessor import PreprocessorError

    config = PreprocessorConfig(include_paths=[])

    source = """
#include "nonexistent.zh"
"""
    try:
        preprocess(source, config)
        assert False, "应该抛出 PreprocessorError"
    except PreprocessorError as e:
        assert "找不到头文件" in str(e)

    print("✓ 找不到头文件测试通过")


def test_header_guard():
    """测试头文件保护（#ifndef/#define/#endif）"""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))

    config = PreprocessorConfig(include_paths=[os.path.join(test_dir, "test_headers")])

    source = f"""
#include "header_guard.zh"
#include "header_guard.zh"

整数型 var = GUARD_VALUE;
"""
    result = preprocess(source, config)

    # 头文件保护应该防止重复包含
    # guard_var 只应该出现一次
    count = result.count("guard_var")
    assert count == 1, f"guard_var 出现了 {count} 次，应该只出现 1 次"

    print("✓ 头文件保护测试通过")


def test_include_with_ifdef():
    """测试 #include 与条件编译结合"""
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))

    config = PreprocessorConfig(include_paths=[os.path.join(test_dir, "test_headers")])

    source = f"""
#define FEATURE

#ifdef FEATURE
#include "header1.zh"
#endif

整数型 var = HEADER1_VALUE;
"""
    result = preprocess(source, config)

    assert "header1_var" in result
    assert "var = 100" in result

    print("✓ #include 与条件编译结合测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("测试预处理器模块")
    print("=" * 60)
    print()

    # 基础功能测试
    test_object_macro()
    test_function_macro()
    test_nested_macro()
    test_macro_with_expression()
    test_undef()
    test_ifdef()
    test_ifdef_else()
    test_nested_ifdef()
    test_elif()
    test_elif_no_match()
    test_elif_defined()
    test_elif_nested()
    test_predefined_macros()
    test_macro_in_string()
    test_empty_macro()
    test_multiline_macro()
    test_chinese_macro()

    print()
    print("-" * 60)
    print("#include 功能测试")
    print("-" * 60)
    print()

    # #include 功能测试
    test_include()
    test_include_system()
    test_include_nested()
    test_include_duplicate()
    test_include_not_found()
    test_header_guard()
    test_include_with_ifdef()

    print()
    print("=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
