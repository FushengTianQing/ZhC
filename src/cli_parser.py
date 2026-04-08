#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行参数解析模块

职责：
1. 构建命令行参数解析器
2. 验证输入参数
3. 参数默认值处理

作者：远
日期：2026-04-07
"""

import argparse
from pathlib import Path
from typing import Optional


def build_arg_parser() -> argparse.ArgumentParser:
    """
    构建命令行参数解析器

    Returns:
        配置好的ArgumentParser实例
    """
    parser = argparse.ArgumentParser(
        description="中文C编译器 - 将中文语法的C代码编译为标准C代码",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s hello.zhc                  # 编译单文件
  %(prog)s hello.zhc -o hello.c       # 指定输出文件
  %(prog)s --project main.zhc         # 编译模块项目
  %(prog)s --clean-cache              # 清理缓存
        """,
    )

    parser.add_argument("input", nargs="?", help="输入文件 (.zhc)")
    parser.add_argument("-o", "--output", help="输出文件或目录")
    parser.add_argument("--project", action="store_true", help="编译模块项目")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="[已废弃] AST 是唯一编译路径，此选项不再生效",
    )
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="跳过语义验证（仅执行语法分析和代码生成）",
    )
    parser.add_argument(
        "-W",
        dest="warning_level",
        default="normal",
        choices=["none", "normal", "all", "error"],
        help="警告级别: none=无警告, normal=默认, all=全部, error=警告当错误",
    )
    parser.add_argument("--no-uninit", action="store_true", help="禁用未初始化变量检查")
    parser.add_argument(
        "--no-unreachable", action="store_true", help="禁用不可达代码检测"
    )
    parser.add_argument("--no-dataflow", action="store_true", help="禁用数据流分析")
    parser.add_argument(
        "--no-interprocedural", action="store_true", help="禁用过程间分析"
    )
    parser.add_argument("--no-alias", action="store_true", help="禁用别名分析")
    parser.add_argument("--no-pointer", action="store_true", help="禁用指针分析")
    parser.add_argument(
        "--optimize-symbol-lookup",
        action="store_true",
        help="启用符号查找优化器（热点缓存 + O(1)查找）",
    )
    parser.add_argument(
        "--profile", action="store_true", help="启用性能分析（测量各编译阶段耗时）"
    )
    parser.add_argument(
        "-g", "--debug",
        action="store_true",
        help="生成 DWARF 调试信息（支持 GDB/LLDB 调试）"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="运行静态分析（代码质量检查、安全漏洞检测等）"
    )
    parser.add_argument(
        "--analyze-format",
        dest="analyze_format",
        default="text",
        choices=["text", "markdown", "json", "html"],
        help="静态分析报告格式 (默认: text)"
    )
    parser.add_argument(
        "--analyze-output",
        dest="analyze_output",
        help="静态分析报告输出文件（默认输出到控制台）"
    )
    parser.add_argument("--clean-cache", action="store_true", help="清理编译缓存")
    parser.add_argument(
        "--backend",
        choices=["ast", "ir", "llvm", "wasm"],
        default="ast",
        help="编译后端: ast=直接AST生成C, ir=IR中间表示→C, llvm=LLVM IR, wasm=WebAssembly"
    )
    parser.add_argument(
        "--dump-ir",
        action="store_true",
        help="打印 IR 中间表示（仅 --backend ir/llvm 时有效）"
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="禁用 IR 优化（仅 --backend ir/llvm 时有效）"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--version", action="version", version="%(prog)s 3.0.0")

    return parser


def validate_input(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> Optional[Path]:
    """
    验证输入参数并返回输入文件路径

    Args:
        args: 解析后的命令行参数
        parser: 参数解析器（用于打印帮助信息）

    Returns:
        有效的输入文件Path，或None（表示验证失败）
    """
    if not args.input:
        parser.print_help()
        return None

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ 文件不存在: {input_file}")
        return None

    return input_file
