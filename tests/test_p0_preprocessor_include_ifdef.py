# -*- coding: utf-8 -*-
"""
P0-预处理器-#include头文件 和 P0-预处理器-#ifdef条件编译 测试

测试预处理器的 #include 和条件编译功能。
"""

import pytest
import tempfile
from pathlib import Path

from zhc.compiler.preprocessor import (
    Preprocessor,
    PreprocessorConfig,
    PreprocessorError,
)


class TestIncludeBasic:
    """测试 #include 基本功能"""

    def test_include_double_quotes(self):
        """测试双引号形式的 #include"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件（使用宏定义）
            header_path = Path(tmpdir) / "header.zh"
            header_path.write_text("#define HEADER_VALUE 42")

            # 创建源文件
            source = f'#include "header.zh"\n整数型 x = HEADER_VALUE;'

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            # #define 语句会被移除，但宏应该被展开
            assert "整数型 x = 42;" in result

    def test_include_angle_brackets(self):
        """测试尖括号形式的 #include"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件（使用宏定义）
            header_path = Path(tmpdir) / "stdlib.zh"
            header_path.write_text("#define NULL 0")

            # 创建源文件
            source = "#include <stdlib.zh>\n整数型 x = NULL;"

            config = PreprocessorConfig(stdlib_path=tmpdir)
            result = Preprocessor(config).process(source, "<main.zh>")

            # #define 语句会被移除，但宏应该被展开
            assert "整数型 x = 0;" in result

    def test_include_relative_path(self):
        """测试相对路径的 #include"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建子目录和头文件
            subdir = Path(tmpdir) / "utils"
            subdir.mkdir()
            header_path = subdir / "helper.zh"
            header_path.write_text("#define HELPER_VALUE 1")

            # 创建源文件
            source = '#include "utils/helper.zh"\n整数型 x = HELPER_VALUE;'

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            # #define 语句会被移除，但宏应该被展开
            assert "整数型 x = 1;" in result


class TestIncludeSearchPaths:
    """测试 #include 搜索路径优先级"""

    def test_search_priority_current_dir_first(self):
        """测试双引号形式优先搜索当前目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 在当前目录创建 header.zh
            current_dir = Path(tmpdir) / "current"
            current_dir.mkdir()
            header1 = current_dir / "header.zh"
            header1.write_text("常量 VALUE = 1;")

            # 在 include 路径创建同名文件
            include_dir = Path(tmpdir) / "include"
            include_dir.mkdir()
            header2 = include_dir / "header.zh"
            header2.write_text("常量 VALUE = 2;")

            source = '#include "header.zh"\n整数型 x = VALUE;'

            config = PreprocessorConfig(include_paths=[str(include_dir)])
            result = Preprocessor(config).process(source, str(current_dir / "main.zh"))

            # 应该优先使用当前目录的文件
            assert "常量 VALUE = 1;" in result
            assert "常量 VALUE = 2;" not in result

    def test_include_paths_order(self):
        """测试 -I 路径的搜索顺序"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个 include 目录
            dir1 = Path(tmpdir) / "dir1"
            dir1.mkdir()
            header1 = dir1 / "header.zh"
            header1.write_text("常量 VALUE = 1;")

            dir2 = Path(tmpdir) / "dir2"
            dir2.mkdir()
            header2 = dir2 / "header.zh"
            header2.write_text("常量 VALUE = 2;")

            source = '#include "header.zh"\n整数型 x = VALUE;'

            # dir1 应该先被搜索
            config = PreprocessorConfig(include_paths=[str(dir1), str(dir2)])
            result = Preprocessor(config).process(source, "<main.zh>")

            assert "常量 VALUE = 1;" in result

    def test_stdlib_path_search(self):
        """测试标准库路径搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建标准库目录
            stdlib_dir = Path(tmpdir) / "stdlib"
            stdlib_dir.mkdir()
            header = stdlib_dir / "math.zh"
            header.write_text("常量 PI = 3.14159;")

            source = "#include <math.zh>\n浮点型 pi = PI;"

            config = PreprocessorConfig(stdlib_path=str(stdlib_dir))
            result = Preprocessor(config).process(source, "<main.zh>")

            assert "常量 PI = 3.14159;" in result


class TestIncludeProtection:
    """测试 #include 包含保护"""

    def test_duplicate_include_prevention(self):
        """测试防止重复包含"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件
            header_path = Path(tmpdir) / "header.zh"
            header_path.write_text("常量 VALUE = 42;")

            source = f"""#include "header.zh"
#include "header.zh"
整数型 x = VALUE;"""

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            # header 内容只应该出现一次
            assert result.count("常量 VALUE = 42;") == 1

    def test_ifndef_guard(self):
        """测试 #ifndef 包含保护"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建带包含保护的头文件
            header_path = Path(tmpdir) / "header.zh"
            header_path.write_text("""#ifndef HEADER_ZH
#define HEADER_ZH
常量 VALUE = 42;
#endif""")

            source = f"""#include "header.zh"
#include "header.zh"
整数型 x = VALUE;"""

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            # header 内容只应该出现一次
            assert result.count("常量 VALUE = 42;") == 1

    def test_pragma_once(self):
        """测试 #pragma once"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建带 #pragma once 的头文件
            header_path = Path(tmpdir) / "header.zh"
            header_path.write_text("""#pragma once
常量 VALUE = 42;""")

            source = f"""#include "header.zh"
#include "header.zh"
整数型 x = VALUE;"""

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            # header 内容只应该出现一次
            assert result.count("常量 VALUE = 42;") == 1


class TestIncludeCircular:
    """测试循环包含检测"""

    def test_circular_include_a_to_b(self):
        """测试 A -> B -> A 循环包含"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建循环包含的文件
            a_path = Path(tmpdir) / "a.zh"
            a_path.write_text('#include "b.zh"\n常量 A = 1;')

            b_path = Path(tmpdir) / "b.zh"
            b_path.write_text('#include "a.zh"\n常量 B = 2;')

            source = '#include "a.zh"'

            config = PreprocessorConfig(include_paths=[tmpdir])
            with pytest.raises(PreprocessorError) as exc_info:
                Preprocessor(config).process(source, "<main.zh>")

            assert (
                "循环包含" in str(exc_info.value)
                or "circular" in str(exc_info.value).lower()
            )

    def test_include_depth_limit(self):
        """测试包含深度限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建深度嵌套的包含链
            for i in range(15):
                file_path = Path(tmpdir) / f"level{i}.zh"
                if i < 14:
                    file_path.write_text(
                        f'#include "level{i+1}.zh"\n常量 LEVEL{i} = {i};'
                    )
                else:
                    file_path.write_text(f"常量 LEVEL{i} = {i};")

            source = '#include "level0.zh"'

            # 设置较小的深度限制
            config = PreprocessorConfig(include_paths=[tmpdir], max_include_depth=5)
            with pytest.raises(PreprocessorError) as exc_info:
                Preprocessor(config).process(source, "<main.zh>")

            assert (
                "深度" in str(exc_info.value) or "depth" in str(exc_info.value).lower()
            )


class TestConditionalBasic:
    """测试条件编译基本功能"""

    def test_ifdef_true(self):
        """测试 #ifdef 条件为真"""
        source = """#define DEBUG

#ifdef DEBUG
常量 MODE = "debug";
#endif
整数型 x = 1;"""

        result = Preprocessor().process(source)
        assert '常量 MODE = "debug";' in result
        assert "整数型 x = 1;" in result

    def test_ifdef_false(self):
        """测试 #ifdef 条件为假"""
        source = """#ifdef RELEASE
常量 MODE = "release";
#endif
整数型 x = 1;"""

        result = Preprocessor().process(source)
        assert '常量 MODE = "release";' not in result
        assert "整数型 x = 1;" in result

    def test_ifndef_true(self):
        """测试 #ifndef 条件为真"""
        source = """#ifndef RELEASE
常量 MODE = "debug";
#endif
整数型 x = 1;"""

        result = Preprocessor().process(source)
        assert '常量 MODE = "debug";' in result

    def test_ifndef_false(self):
        """测试 #ifndef 条件为假"""
        source = """#define RELEASE

#ifndef RELEASE
常量 MODE = "debug";
#endif
整数型 x = 1;"""

        result = Preprocessor().process(source)
        assert '常量 MODE = "debug";' not in result


class TestConditionalElse:
    """测试 #else 分支"""

    def test_ifdef_else(self):
        """测试 #ifdef ... #else"""
        source = """#define DEBUG

#ifdef DEBUG
常量 MODE = "debug";
#else
常量 MODE = "release";
#endif
整数型 x = 1;"""

        result = Preprocessor().process(source)
        assert '常量 MODE = "debug";' in result
        assert '常量 MODE = "release";' not in result

    def test_ifdef_else_false(self):
        """测试 #ifdef ... #else (条件为假)"""
        source = """#ifdef DEBUG
常量 MODE = "debug";
#else
常量 MODE = "release";
#endif
整数型 x = 1;"""

        result = Preprocessor().process(source)
        assert '常量 MODE = "debug";' not in result
        assert '常量 MODE = "release";' in result


class TestConditionalElif:
    """测试 #elif 分支"""

    def test_elif_true(self):
        """测试 #elif 条件为真"""
        source = """#define FEATURE_B

#ifdef FEATURE_A
常量 FEATURE = "A";
#elif defined(FEATURE_B)
常量 FEATURE = "B";
#elif defined(FEATURE_C)
常量 FEATURE = "C";
#else
常量 FEATURE = "NONE";
#endif"""

        result = Preprocessor().process(source)
        assert '常量 FEATURE = "B";' in result

    def test_elif_multiple(self):
        """测试多个 #elif 分支"""
        source = """#define FEATURE_C

#ifdef FEATURE_A
常量 FEATURE = "A";
#elif defined(FEATURE_B)
常量 FEATURE = "B";
#elif defined(FEATURE_C)
常量 FEATURE = "C";
#else
常量 FEATURE = "NONE";
#endif"""

        result = Preprocessor().process(source)
        assert '常量 FEATURE = "C";' in result

    def test_elif_else_fallback(self):
        """测试 #elif 都不满足时走 #else"""
        source = """#ifdef FEATURE_A
常量 FEATURE = "A";
#elif defined(FEATURE_B)
常量 FEATURE = "B";
#else
常量 FEATURE = "NONE";
#endif"""

        result = Preprocessor().process(source)
        assert '常量 FEATURE = "NONE";' in result


class TestConditionalNested:
    """测试嵌套条件编译"""

    def test_nested_ifdef(self):
        """测试嵌套的 #ifdef"""
        source = """#define DEBUG
#define VERBOSE

#ifdef DEBUG
  #ifdef VERBOSE
常量 LOG_LEVEL = "verbose";
  #else
常量 LOG_LEVEL = "debug";
  ##endif
#else
常量 LOG_LEVEL = "none";
#endif"""

        result = Preprocessor().process(source)
        assert '常量 LOG_LEVEL = "verbose";' in result

    def test_nested_ifdef_inner_false(self):
        """测试嵌套 #ifdef 内层为假"""
        source = """#define DEBUG

#ifdef DEBUG
  #ifdef VERBOSE
常量 LOG_LEVEL = "verbose";
  #else
常量 LOG_LEVEL = "debug";
  #endif
#else
常量 LOG_LEVEL = "none";
#endif"""

        result = Preprocessor().process(source)
        assert '常量 LOG_LEVEL = "debug";' in result

    def test_nested_ifdef_outer_false(self):
        """测试嵌套 #ifdef 外层为假"""
        source = """#ifdef DEBUG
  #ifdef VERBOSE
常量 LOG_LEVEL = "verbose";
  #else
常量 LOG_LEVEL = "debug";
  #endif
#else
常量 LOG_LEVEL = "none";
#endif"""

        result = Preprocessor().process(source)
        assert '常量 LOG_LEVEL = "none";' in result


class TestConditionalDefined:
    """测试 defined() 操作符"""

    def test_defined_true(self):
        """测试 defined() 条件为真"""
        source = """#define FEATURE

#if defined(FEATURE)
常量 HAS_FEATURE = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 HAS_FEATURE = 1;" in result

    def test_defined_false(self):
        """测试 defined() 条件为假"""
        source = """#if defined(FEATURE)
常量 HAS_FEATURE = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 HAS_FEATURE = 1;" not in result

    def test_not_defined(self):
        """测试 !defined() 条件"""
        source = """#if !defined(FEATURE)
常量 NO_FEATURE = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 NO_FEATURE = 1;" in result

    def test_defined_combined_and(self):
        """测试 defined() 组合条件 AND"""
        source = """#define FEATURE_A
#define FEATURE_B

#if defined(FEATURE_A) && defined(FEATURE_B)
常量 BOTH = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 BOTH = 1;" in result

    def test_defined_combined_or(self):
        """测试 defined() 组合条件 OR"""
        source = """#define FEATURE_B

#if defined(FEATURE_A) || defined(FEATURE_B)
常量 EITHER = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 EITHER = 1;" in result

    def test_defined_combined_complex(self):
        """测试 defined() 复杂组合条件"""
        source = """#define FEATURE_A
#undef FEATURE_B

#if defined(FEATURE_A) && !defined(FEATURE_B)
常量 ONLY_A = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 ONLY_A = 1;" in result


class TestPredefinedMacros:
    """测试预定义宏"""

    def test_zhc_macro(self):
        """测试 __ZHC__ 预定义宏"""
        source = """#ifdef __ZHC__
常量 IS_ZHC = 1;
#endif"""

        result = Preprocessor().process(source)
        assert "常量 IS_ZHC = 1;" in result

    def test_zhc_version_macro(self):
        """测试 __ZHC_VERSION__ 预定义宏"""
        source = """#if defined(__ZHC_VERSION__)
常量 VERSION = __ZHC_VERSION__;
#endif"""

        result = Preprocessor().process(source)
        assert '常量 VERSION = "0.1.0";' in result

    def test_file_macro(self):
        """测试 __FILE__ 预定义宏"""
        source = """常量 FILE = __FILE__;"""

        result = Preprocessor().process(source, "<test.zh>")
        # __FILE__ 应该被替换为当前文件名
        assert "__FILE__" not in result


class TestIncludeWithConditional:
    """测试 #include 与条件编译的交互"""

    def test_conditional_include(self):
        """测试条件包含"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建头文件（使用宏定义）
            debug_header = Path(tmpdir) / "debug.zh"
            debug_header.write_text("#define DEBUG_MODE 1")

            release_header = Path(tmpdir) / "release.zh"
            release_header.write_text("#define RELEASE_MODE 1")

            source = """#define DEBUG

#ifdef DEBUG
#include "debug.zh"
#else
#include "release.zh"
#endif

整数型 x = DEBUG_MODE;"""

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            # debug.zh 中的宏应该被展开
            assert "整数型 x = 1;" in result
            # release.zh 不应该被包含
            assert "RELEASE_MODE" not in result

    def test_include_with_ifdef_guard(self):
        """测试包含带条件编译的头文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建带条件编译的头文件
            header_path = Path(tmpdir) / "config.zh"
            header_path.write_text("""#ifdef FEATURE_A
常量 FEATURE_A_ENABLED = 1;
#endif

#ifdef FEATURE_B
常量 FEATURE_B_ENABLED = 1;
#endif""")

            source = """#define FEATURE_A

#include "config.zh"

整数型 x = FEATURE_A_ENABLED;"""

            config = PreprocessorConfig(include_paths=[tmpdir])
            result = Preprocessor(config).process(source, "<main.zh>")

            assert "常量 FEATURE_A_ENABLED = 1;" in result
            assert "常量 FEATURE_B_ENABLED = 1;" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
