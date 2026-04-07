#!/usr/bin/env python3
"""
ZHC 命令行入口

中文C编译器 - 将中文语法的C代码编译为标准C代码。

用法:
    python -m src.cli input.zhc -o output.c
    python -m src.cli --project main.zhc --output build/
"""

import sys
import argparse
import time
from pathlib import Path
from typing import Any, Optional

# 尝试导入高级功能
HAS_MODULE_SYSTEM = False
try:
    from zhc.compiler.pipeline import CompilationPipeline
    from zhc.compiler.cache import CompilationCache
    from zhc.compiler.optimizer import PerformanceMonitor

    HAS_MODULE_SYSTEM = True
except ImportError:
    pass


class CompilerConfig:
    """编译器配置（从命令行参数构建）"""

    # 语义分析相关配置
    MAX_DISPLAY_ERRORS = 20  # 最多显示的错误数

    def __init__(
        self,
        verbose: bool = False,
        use_ast: bool = True,
        skip_semantic: bool = False,
        warning_level: str = "normal",
        no_uninit: bool = False,
        no_unreachable: bool = False,
        no_dataflow: bool = False,
        no_interprocedural: bool = False,
        no_alias: bool = False,
        no_pointer: bool = False,
        optimize_symbol_lookup: bool = False,
        profile: bool = False,
        backend: str = "ast",
        dump_ir: bool = False,
        optimize_ir: bool = True,
        enable_cache: bool = True,
    ):
        self.enable_cache = enable_cache
        self.verbose = verbose
        self.use_ast = use_ast
        self.skip_semantic = skip_semantic
        self.warning_level = warning_level
        self.no_uninit = no_uninit
        self.no_unreachable = no_unreachable
        self.no_dataflow = no_dataflow
        self.no_interprocedural = no_interprocedural
        self.no_alias = no_alias
        self.no_pointer = no_pointer
        self.optimize_symbol_lookup = optimize_symbol_lookup
        self.profile_enabled = profile
        self.backend = backend
        self.dump_ir = dump_ir
        self.optimize_ir = optimize_ir

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CompilerConfig":
        """从命令行参数创建配置"""
        return cls(
            verbose=args.verbose,
            use_ast=not args.legacy,
            skip_semantic=args.skip_semantic,
            warning_level=args.warning_level,
            no_uninit=args.no_uninit,
            no_unreachable=args.no_unreachable,
            no_dataflow=args.no_dataflow,
            no_interprocedural=args.no_interprocedural,
            no_alias=args.no_alias,
            no_pointer=args.no_pointer,
            optimize_symbol_lookup=args.optimize_symbol_lookup,
            profile=args.profile,
        )


class ZHCCompiler:
    """中文C编译器主类

    负责协调词法分析、语法分析、语义分析和代码生成的完整流水线。
    支持单文件编译和模块项目编译两种模式。
    """

    def __init__(self, config: Optional[CompilerConfig] = None):
        self.config = config or CompilerConfig()

        # 高级功能组件
        self.cache = None
        self.pipeline = None
        self.performance_monitor = None
        self._prev_ast_by_file: dict = {}
        self._incremental_updater: Optional[Any] = None

        # 初始化可选的高级功能
        if HAS_MODULE_SYSTEM:
            self._init_advanced_features()

        # 编译统计
        self.stats = {
            "files_processed": 0,
            "total_lines": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "start_time": time.time(),
        }

    def _init_advanced_features(self) -> None:
        """初始化模块系统、缓存、Pipeline等高级功能"""
        cfg = self.config
        try:
            self.cache = CompilationCache(max_size_mb=100) if cfg.enable_cache else None
            self.pipeline = CompilationPipeline(
                enable_cache=cfg.enable_cache,
                skip_semantic=cfg.skip_semantic,
                warning_level=cfg.warning_level,
                no_uninit=cfg.no_uninit,
                no_unreachable=cfg.no_unreachable,
                no_dataflow=cfg.no_dataflow,
                no_interprocedural=cfg.no_interprocedural,
                no_alias=cfg.no_alias,
                no_pointer=cfg.no_pointer,
                optimize_symbol_lookup=cfg.optimize_symbol_lookup,
            )
            self.performance_monitor = PerformanceMonitor()
            if cfg.verbose:
                print("✅ 模块系统支持已启用（AST 模式）")
        except Exception as e:
            if cfg.verbose:
                print(f"⚠️ 高级功能初始化失败: {e}")

    def compile_single_file(
        self, input_file: Path, output_dir: Optional[Path] = None
    ) -> bool:
        """编译单个文件（AST 模式）

        完整流水线：读取源码 → 词法/语法分析 → 语义验证 → 代码生成 → 写入文件

        Args:
            input_file: 输入的.zhc文件路径
            output_dir: 输出目录（None则输出到同目录）

        Returns:
            编译是否成功
        """
        if self.config.verbose:
            print(f"📄 [AST] 编译: {input_file}")

        try:
            content = input_file.read_text(encoding="utf-8")

            # 阶段1：词法 + 语法分析 → AST
            ast, errors = self._parse_source(content, input_file)
            if errors:
                self._report_parse_errors(errors)
                return False

            # 阶段1.5：增量AST diff（与上次编译结果对比）
            self._run_incremental_diff(input_file, ast)

            # 阶段2：语义验证
            if not self._run_semantic_check(ast, input_file):
                return False

            # 阶段3：代码生成 (AST→C 或 AST→IR→C)
            c_code = self._generate_code(ast)
            if c_code is None:
                return False

            # 阶段4：写入输出
            output_file = self._resolve_output_path(input_file, output_dir)
            output_file.write_text(c_code, encoding="utf-8")

            # 缓存本次AST供增量diff使用
            self._cache_compiled_ast(input_file, ast)

            if self.config.verbose:
                print(f"  [AST] 转换完成: {input_file} -> {output_file}")

            self._update_stats(len(content.splitlines()))
            return True

        except Exception as e:
            self._handle_compile_error(e, input_file)
            return False

    def compile_module_project(
        self, input_file: Path, output_dir: Optional[Path] = None
    ) -> bool:
        """编译模块项目（AST 模式）

        使用 CompilationPipeline 处理多文件模块项目。

        Args:
            input_file: 项目入口文件
            output_dir: 输出目录

        Returns:
            编译是否成功
        """
        if self.config.verbose:
            print(f"📁 [AST 模块项目] 编译: {input_file}")

        pipeline = self._ensure_pipeline()

        try:
            success = pipeline.compile_project([str(input_file)])
            if self.config.verbose:
                print(f"  [AST 模块项目] {'成功' if success else '失败'}")
            return success
        except Exception as e:
            if self.config.verbose:
                import traceback

                traceback.print_exc()
            print(f"  [AST 模块项目] 编译失败: {e}")
            return False

    def clean_cache(self) -> None:
        """清理编译缓存（包括增量AST缓存）"""
        if self.cache:
            self.cache.clear()
        self._prev_ast_by_file.clear()
        if self.config.verbose:
            print("  🗑️ 编译缓存已清理（包括增量 AST 缓存）")

    def show_stats(self) -> None:
        """显示编译统计信息"""
        elapsed = time.time() - self.stats["start_time"]
        print("\n📊 编译统计:")
        print(f"  文件数: {self.stats['files_processed']}")
        print(f"  总行数: {self.stats['total_lines']}")
        print(f"  耗时: {elapsed:.2f}秒")

    # ------------------------------------------------------------------
    # 私有方法：各编译阶段
    # ------------------------------------------------------------------

    def _parse_source(self, content: str, input_file: Path):
        """阶段1：词法分析 + 语法分析，返回(ast, errors)"""
        from zhc.parser import parse as parse_source

        return parse_source(content)

    def _report_parse_errors(self, errors: list) -> None:
        """报告解析错误（最多显示10个）"""
        for err in errors[:10]:
            print(f"  错误: {err}")

    def _run_incremental_diff(self, input_file: Path, ast) -> None:
        """阶段1.5：计算AST增量变化（Phase 7）"""
        file_key = str(input_file.resolve())
        prev_ast = self._prev_ast_by_file.get(file_key)
        if prev_ast is None:
            return

        try:
            if self._incremental_updater is None:
                from zhc.analyzer.incremental_ast_updater import IncrementalASTUpdater

                self._incremental_updater = IncrementalASTUpdater()

            diffs = self._incremental_updater.compute_diff(prev_ast, ast)
            stats = self._incremental_updater.get_update_statistics(diffs)

            has_changes = (
                stats["update"] > 0 or stats["insert"] > 0 or stats["delete"] > 0
            )
            if has_changes and self.config.verbose:
                print(
                    f"  🔄 [增量] 更新={stats['update']} 插入={stats['insert']} 删除={stats['delete']}"
                )
                print(self._incremental_updater.generate_report(diffs))
        except Exception:
            pass  # 增量更新失败不影响正常编译

    def _run_semantic_check(self, ast, input_file: Path) -> bool:
        """阶段2：语义验证，返回True表示通过"""
        if self.config.skip_semantic:
            return True

        if self.config.verbose:
            print("  🔍 [语义验证] 分析中...")

        from zhc.semantic import SemanticAnalyzer

        validator = SemanticAnalyzer()
        validator.cfg_enabled = not self.config.no_unreachable
        validator.uninit_enabled = not self.config.no_uninit
        validator.dataflow_enabled = not self.config.no_dataflow
        validator.interprocedural_enabled = not self.config.no_interprocedural
        validator.alias_enabled = not self.config.no_alias
        validator.pointer_enabled = not self.config.no_pointer
        validator.symbol_lookup_enabled = self.config.optimize_symbol_lookup
        validator.analyze_file(ast, input_file.name)

        # 检查错误
        errors = validator.get_errors()
        if errors:
            print(validator.format_errors())
            if len(errors) > CompilerConfig.MAX_DISPLAY_ERRORS:
                print(
                    f"  ... 还有 {len(errors) - CompilerConfig.MAX_DISPLAY_ERRORS} 个错误未显示"
                )
            return False

        # 检查警告
        warnings = validator.get_warnings()
        if self.config.warning_level != "none" and warnings:
            print(validator.format_warnings())
            if self.config.warning_level == "error":
                print("  ❌ -Werror: 警告被当作错误处理")
                return False

        if self.config.verbose:
            stats = validator.get_statistics()
            print(
                f"  ✅ [语义验证] 通过 (访问 {stats['nodes_visited']} 个节点, "
                f"符号 {stats['symbols_added']} 个)"
            )
        return True

    def _generate_code(self, ast):
        """阶段3：代码生成，返回C代码字符串或None（IR验证失败时）"""
        perf_analyzer = None
        if self.config.profile_enabled:
            from zhc.analyzer.performance import PerformanceAnalyzer

            perf_analyzer = PerformanceAnalyzer()

        if self.config.backend == "ir":
            code = self._generate_via_ir(ast, perf_analyzer)
        else:
            code = self._generate_directly(ast, perf_analyzer)

        # 输出性能报告
        if perf_analyzer is not None:
            print("\n" + perf_analyzer.print_report())

        return code

    def _generate_directly(self, ast, perf_analyzer=None):
        """直接从AST生成C代码"""
        from zhc.codegen import CCodeGenerator

        def run_codegen():
            """通过 CCodeGenerator 直接从 AST 生成 C 代码"""
            g = CCodeGenerator()
            return g.generate(ast)

        if perf_analyzer:
            result, _ = perf_analyzer.measure_operation("代码生成", run_codegen)
            return result
        return run_codegen()

    def _generate_via_ir(self, ast, perf_analyzer=None):
        """通过IR中间表示生成C代码"""
        from zhc.ir.ir_generator import IRGenerator
        from zhc.ir.ir_verifier import IRVerifier
        from zhc.ir.optimizer import PassManager, ConstantFolding, DeadCodeElimination
        from zhc.ir.c_backend import CBackend

        def run_ir_gen():
            """通过 IR 管线生成 C 代码（生成→验证→优化→后端）"""
            gen = IRGenerator()
            ir = gen.generate(ast)

            if self.config.dump_ir:
                from zhc.ir.printer import IRPrinter

                printer = IRPrinter()
                print("=== IR 生成 ===")
                print(printer.print(ir))

            verifier = IRVerifier()
            verrors = verifier.verify(ir)
            if verrors:
                for e in verrors:
                    print(f"  IR 验证错误: {e.msg}")
                return None

            if self.config.optimize_ir:
                pm = PassManager()
                pm.register(ConstantFolding())
                pm.register(DeadCodeElimination())
                ir = pm.run(ir)

            backend = CBackend()
            return backend.generate(ir)

        if perf_analyzer:
            result, _ = perf_analyzer.measure_operation("IR代码生成", run_ir_gen)
            return result
        return run_ir_gen()

    def _resolve_output_path(
        self, input_file: Path, output_dir: Optional[Path]
    ) -> Path:
        """确定输出文件路径"""
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            return output_dir / input_file.name.replace(".zhc", ".c")
        return input_file.with_suffix(".c")

    def _cache_compiled_ast(self, input_file: Path, ast) -> None:
        """缓存本次编译成功的AST，供下次增量diff使用"""
        file_key = str(input_file.resolve())
        self._prev_ast_by_file[file_key] = ast

    def _update_stats(self, line_count: int) -> None:
        """更新编译统计"""
        self.stats["files_processed"] += 1
        self.stats["total_lines"] += line_count

    def _handle_compile_error(self, error: Exception, input_file: Path) -> None:
        """处理编译异常"""
        if self.config.verbose:
            import traceback

            traceback.print_exc()
        print(f"  [AST] 编译失败: {input_file}: {error}")

    def _ensure_pipeline(self):
        """确保Pipeline已初始化（延迟创建）"""
        if self.pipeline:
            return self.pipeline
        cfg = self.config
        self.pipeline = CompilationPipeline(
            enable_cache=cfg.enable_cache,
            skip_semantic=cfg.skip_semantic,
            warning_level=cfg.warning_level,
            no_uninit=cfg.no_uninit,
            no_unreachable=cfg.no_unreachable,
            no_dataflow=cfg.no_dataflow,
            no_interprocedural=cfg.no_interprocedural,
            no_alias=cfg.no_alias,
            no_pointer=cfg.no_pointer,
            optimize_symbol_lookup=cfg.optimize_symbol_lookup,
        )
        return self.pipeline


# ------------------------------------------------------------------
# 命令行参数解析
# ------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器

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
    parser.add_argument("--clean-cache", action="store_true", help="清理编译缓存")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--version", action="version", version="%(prog)s 3.0.0")

    return parser


def validate_input(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> Optional[Path]:
    """验证输入参数并返回输入文件路径

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


def main() -> int:
    """命令行入口函数

    Returns:
        退出码（0=成功, 1=失败）
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    # 从参数构建配置
    config = CompilerConfig.from_args(args)
    compiler = ZHCCompiler(config=config)

    # 处理清理缓存指令
    if args.clean_cache:
        compiler.clean_cache()
        return 0

    # 验证输入文件
    input_file = validate_input(args, parser)
    if input_file is None:
        return 1

    # 设置输出路径
    output_dir = Path(args.output) if args.output else None

    # 执行编译
    if args.project:
        success = compiler.compile_module_project(input_file, output_dir)
    else:
        success = compiler.compile_single_file(input_file, output_dir)

    if args.verbose:
        compiler.show_stats()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
