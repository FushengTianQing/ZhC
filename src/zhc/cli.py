#!/usr/bin/env python3
"""
ZHC 命令行入口

中文C编译器 - 将中文语法的C代码编译为标准C代码。

用法:
    python -m src.cli input.zhc -o output.c
    python -m src.cli --project main.zhc --output build/
"""

import sys
import time
from pathlib import Path
from typing import Any, Optional, List

from .config import CompilerConfig
from .cli_parser import build_arg_parser, validate_input
from .api.result import CompilationResult

# 尝试导入高级功能
HAS_MODULE_SYSTEM = False
try:
    from zhc.compiler.pipeline import CompilationPipeline
    from zhc.compiler.cache import CompilationCache
    from zhc.compiler.optimizer import PerformanceMonitor

    HAS_MODULE_SYSTEM = True
except ImportError:
    pass


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
            self.pipeline = self._create_pipeline()
            self.performance_monitor = PerformanceMonitor()
            if cfg.verbose:
                print("✅ 模块系统支持已启用（AST 模式）")
        except Exception as e:
            if cfg.verbose:
                print(f"⚠️ 高级功能初始化失败: {e}")

    def _create_pipeline(self):
        """创建 CompilationPipeline 实例 - 工厂方法，消除重复代码"""
        cfg = self.config
        return CompilationPipeline(
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

    def compile_single_file(
        self, input_file: Path, output_dir: Optional[Path] = None
    ) -> CompilationResult:
        """编译单个文件（AST 模式）

        完整流水线：读取源码 → 词法/语法分析 → 语义验证 → 代码生成 → 写入文件

        Args:
            input_file: 输入的.zhc文件路径
            output_dir: 输出目录（None则输出到同目录）

        Returns:
            CompilationResult 包含编译结果、错误、警告等信息
        """
        start_time = time.time()
        errors: List[str] = []
        warnings: List[str] = []

        if self.config.verbose:
            print(f"📄 [AST] 编译: {input_file}")

        try:
            content = input_file.read_text(encoding="utf-8")

            # 阶段1：词法 + 语法分析 → AST
            ast, parse_errors = self._parse_source(content, input_file)
            if parse_errors:
                errors.extend(str(e) for e in parse_errors[:10])
                self._report_parse_errors(parse_errors)
                return CompilationResult.failure_result(
                    input_file=input_file,
                    errors=errors,
                    elapsed_time=time.time() - start_time,
                )

            # 阶段1.5：增量AST diff（与上次编译结果对比）
            self._run_incremental_diff(input_file, ast)

            # 阶段2：语义验证
            semantic_result = self._run_semantic_check_with_result(ast, input_file)
            if not semantic_result["success"]:
                errors.extend(semantic_result.get("errors", []))
                warnings.extend(semantic_result.get("warnings", []))
                return CompilationResult.failure_result(
                    input_file=input_file,
                    errors=errors,
                    warnings=warnings,
                    elapsed_time=time.time() - start_time,
                )
            warnings.extend(semantic_result.get("warnings", []))

            # 阶段2.5：安全分析（默认启用，ERROR 级别阻止编译）
            from zhc.analysis import create_security_scheduler, Severity

            security_scheduler = create_security_scheduler()
            context = {"source_file": str(input_file), "file_name": input_file.name}
            security_scheduler.run_all(ast, context)

            if security_scheduler.has_errors():
                error_results = security_scheduler.filter_by_severity(Severity.ERROR)
                errors.extend([str(r) for r in error_results])
                print(f"  [安全分析] 发现 {len(error_results)} 个错误，阻止编译")
                return CompilationResult.failure_result(
                    input_file=input_file,
                    errors=errors,
                    warnings=warnings,
                    elapsed_time=time.time() - start_time,
                )

            if security_scheduler.has_warnings() and self.config.verbose:
                warning_results = security_scheduler.filter_by_severity(
                    Severity.WARNING
                )
                print(f"  [安全分析] 发现 {len(warning_results)} 个警告")

            # 阶段3：代码生成 (AST→C 或 AST→IR→C)
            c_code = self._generate_code(ast)
            if c_code is None:
                errors.append("代码生成失败")
                return CompilationResult.failure_result(
                    input_file=input_file,
                    errors=errors,
                    warnings=warnings,
                    elapsed_time=time.time() - start_time,
                )

            # 阶段4：写入输出
            output_file = self._resolve_output_path(input_file, output_dir)
            output_file.write_text(c_code, encoding="utf-8")

            # 缓存本次AST供增量diff使用
            self._cache_compiled_ast(input_file, ast)

            if self.config.verbose:
                print(f"  [AST] 转换完成: {input_file} -> {output_file}")

            self._update_stats(len(content.splitlines()))

            return CompilationResult.success_result(
                input_file=input_file,
                output_files=[output_file],
                elapsed_time=time.time() - start_time,
                stats={"lines_processed": len(content.splitlines())},
            )

        except Exception as e:
            self._handle_compile_error(e, input_file)
            errors.append(str(e))
            return CompilationResult.failure_result(
                input_file=input_file,
                errors=errors,
                elapsed_time=time.time() - start_time,
            )

    def compile_module_project(
        self, input_file: Path, output_dir: Optional[Path] = None
    ) -> CompilationResult:
        """编译模块项目（AST 模式）

        使用 CompilationPipeline 处理多文件模块项目。

        Args:
            input_file: 项目入口文件
            output_dir: 输出目录

        Returns:
            CompilationResult 包含编译结果、错误、警告等信息
        """
        start_time = time.time()

        if self.config.verbose:
            print(f"📁 [AST 模块项目] 编译: {input_file}")

        pipeline = self._ensure_pipeline()

        try:
            success = pipeline.compile_project([str(input_file)])
            if self.config.verbose:
                print(f"  [AST 模块项目] {'成功' if success else '失败'}")

            if success:
                output_files = []
                if output_dir:
                    output_files = [output_dir / input_file.name.replace(".zhc", ".c")]
                else:
                    output_files = [input_file.with_suffix(".c")]

                return CompilationResult.success_result(
                    input_file=input_file,
                    output_files=output_files,
                    elapsed_time=time.time() - start_time,
                )
            else:
                return CompilationResult.failure_result(
                    input_file=input_file,
                    errors=["模块项目编译失败"],
                    elapsed_time=time.time() - start_time,
                )
        except Exception as e:
            if self.config.verbose:
                import traceback

                traceback.print_exc()
            print(f"  [AST 模块项目] 编译失败: {e}")
            return CompilationResult.failure_result(
                input_file=input_file,
                errors=[str(e)],
                elapsed_time=time.time() - start_time,
            )

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

    def run_static_analysis(self, ast: Any, input_file: Path) -> bool:
        """
        运行静态分析

        Args:
            ast: AST 树
            input_file: 输入文件路径

        Returns:
            是否成功（无错误）
        """
        if not self.config.analyze_enabled:
            return True

        if self.config.verbose:
            print("  🔍 [静态分析] 运行中...")

        try:
            # 导入静态分析模块
            from zhc.analysis import (
                AnalysisScheduler,  # noqa: F401
                ReportGenerator,
                create_default_scheduler,
            )

            # 创建调度器
            scheduler = create_default_scheduler()

            # 创建上下文
            context = {
                "source_file": str(input_file),
                "file_name": input_file.name,
            }

            # 运行分析
            scheduler.run_all(ast, context)

            # 生成报告
            all_results = scheduler.get_all_results()

            if all_results:
                if self.config.verbose or scheduler.has_errors():
                    generator = ReportGenerator(scheduler.results, scheduler.stats)

                    # 根据格式生成报告
                    format = self.config.analyze_format
                    if format == "text":
                        report = generator.generate_text()
                    elif format == "markdown":
                        report = generator.generate_markdown()
                    elif format == "json":
                        report = generator.generate_json()
                    elif format == "html":
                        report = generator.generate_html()
                    else:
                        report = generator.generate_text()

                    # 输出到文件或控制台
                    output_file = self.config.analyze_output
                    if output_file:
                        Path(output_file).write_text(report, encoding="utf-8")
                        if self.config.verbose:
                            print(f"  📄 报告已写入: {output_file}")
                    else:
                        print("\n" + report)
            else:
                if self.config.verbose:
                    print("  ✅ [静态分析] 未发现问题")

            if self.config.verbose:
                stats = scheduler.stats
                print(
                    f"  📊 [静态分析] 完成: "
                    f"{stats.errors} 错误, {stats.warnings} 警告, "
                    f"{stats.infos} 提示"
                )

            # 如果有错误且 warning_level == "error"，返回 False
            if scheduler.has_errors() and self.config.warning_level == "error":
                return False

            return not scheduler.has_errors()

        except ImportError as e:
            if self.config.verbose:
                print(f"  ⚠️ 静态分析模块未安装: {e}")
            return True
        except Exception as e:
            if self.config.verbose:
                print(f"  ⚠️ 静态分析执行失败: {e}")
            return True

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
        self._configure_validator(validator)
        validator.analyze_file(ast, input_file.name)

        # 检查错误
        errors = validator.get_errors()
        if errors:
            print(validator.format_errors())
            if len(errors) > self.config.MAX_DISPLAY_ERRORS:
                print(
                    f"  ... 还有 {len(errors) - self.config.MAX_DISPLAY_ERRORS} 个错误未显示"
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

    def _run_semantic_check_with_result(self, ast, input_file: Path) -> dict:
        """阶段2：语义验证，返回包含错误和警告的结果字典

        Returns:
            dict: {"success": bool, "errors": List[str], "warnings": List[str]}
        """
        result = {"success": True, "errors": [], "warnings": []}

        if self.config.skip_semantic:
            return result

        if self.config.verbose:
            print("  🔍 [语义验证] 分析中...")

        from zhc.semantic import SemanticAnalyzer

        validator = SemanticAnalyzer()
        self._configure_validator(validator)
        validator.analyze_file(ast, input_file.name)

        # 检查错误
        errors = validator.get_errors()
        if errors:
            result["errors"] = [str(e) for e in errors[:10]]
            print(validator.format_errors())
            if len(errors) > self.config.MAX_DISPLAY_ERRORS:
                print(
                    f"  ... 还有 {len(errors) - self.config.MAX_DISPLAY_ERRORS} 个错误未显示"
                )
            result["success"] = False

        # 检查警告
        warnings = validator.get_warnings()
        if warnings:
            result["warnings"] = [str(w) for w in warnings]
        if self.config.warning_level != "none" and warnings:
            print(validator.format_warnings())
            if self.config.warning_level == "error":
                print("  ❌ -Werror: 警告被当作错误处理")
                result["errors"].append("-Werror: 警告被当作错误处理")
                result["success"] = False

        if result["success"] and self.config.verbose:
            stats = validator.get_statistics()
            print(
                f"  ✅ [语义验证] 通过 (访问 {stats['nodes_visited']} 个节点, "
                f"符号 {stats['symbols_added']} 个)"
            )
        return result

    def _configure_validator(self, validator) -> None:
        """配置语义分析器 - 使用 dispatch table 模式"""
        # 配置映射表：配置项 -> validator 属性
        config_map = {
            "no_unreachable": ("cfg_enabled", False),
            "no_uninit": ("uninit_enabled", False),
            "no_dataflow": ("dataflow_enabled", False),
            "no_interprocedural": ("interprocedural_enabled", False),
            "no_alias": ("alias_enabled", False),
            "no_pointer": ("pointer_enabled", False),
            "optimize_symbol_lookup": ("symbol_lookup_enabled", True),
        }

        for config_key, (attr_name, enabled_when_true) in config_map.items():
            config_value = getattr(self.config, config_key)
            # enabled_when_true 表示当 config_value 为 True 时启用该功能
            setattr(
                validator,
                attr_name,
                enabled_when_true if config_value else not enabled_when_true,
            )

    def _generate_code(self, ast):
        """阶段3：代码生成，返回C代码字符串或None（IR验证失败时）"""
        perf_analyzer = None
        if self.config.profile_enabled:
            from zhc.analyzer.performance import PerformanceAnalyzer

            perf_analyzer = PerformanceAnalyzer()

        backend = self.config.backend

        if backend == "ir":
            # 通过 IR → C 后端
            code = self._generate_via_ir(ast, perf_analyzer, target="c")
        elif backend == "llvm":
            # 通过 IR → LLVM 后端
            code = self._generate_via_ir(ast, perf_analyzer, target="llvm")
        elif backend == "wasm":
            # 通过 IR → WASM 后端
            code = self._generate_via_ir(ast, perf_analyzer, target="wasm")
        else:
            # 默认使用 IR → C 后端
            code = self._generate_via_ir(ast, perf_analyzer, target="c")

        # 输出性能报告
        if perf_analyzer is not None:
            print("\n" + perf_analyzer.print_report())

        return code

    def _generate_via_ir(self, ast, perf_analyzer=None, target: str = "c"):
        """通过IR中间表示生成代码

        Args:
            ast: 抽象语法树
            perf_analyzer: 性能分析器
            target: 目标后端 ("c", "llvm", "wasm")

        Returns:
            生成的代码字符串
        """
        from zhc.ir.ir_generator import IRGenerator
        from zhc.ir.ir_verifier import IRVerifier
        from zhc.ir.optimizer import PassManager, ConstantFolding, DeadCodeElimination
        from zhc.ir.c_backend import CBackend

        def run_ir_gen():
            """通过 IR 管线生成代码（生成→验证→优化→后端）"""
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
                    print(f"  IR 验证错误: {e.message}")
                return None

            if self.config.optimize_ir:
                pm = PassManager()
                pm.register(ConstantFolding())
                pm.register(DeadCodeElimination())
                ir = pm.run(ir)

            # 根据目标选择后端
            if target == "llvm":
                # LLVM 后端
                try:
                    from zhc.backend.llvm_backend import LLVMBackend

                    backend = LLVMBackend()
                    return backend.generate(ir)
                except ImportError:
                    print(
                        "❌ LLVM 后端不可用，请安装 llvmlite: pip install llvmlite>=0.39.0"
                    )
                    # 回退到 C 后端
                    backend = CBackend()
                    return backend.generate(ir)

            elif target == "wasm":
                # WASM 后端
                try:
                    from zhc.backend.wasm_backend import WebAssemblyBackend

                    backend = WebAssemblyBackend()
                    return backend.generate(ir)
                except ImportError:
                    print("❌ WASM 后端不可用")
                    # 回退到 C 后端
                    backend = CBackend()
                    return backend.generate(ir)

            else:
                # 默认 C 后端
                backend = CBackend()
                return backend.generate(ir)

        if perf_analyzer:
            result, _ = perf_analyzer.measure_operation("IR代码生成", run_ir_gen)
            return result
        return run_ir_gen()

    def _resolve_output_path(
        self, input_file: Path, output_dir: Optional[Path] = None
    ) -> Path:
        """确定输出文件路径（根据后端类型选择扩展名）"""
        # 根据后端类型确定扩展名
        backend = self.config.backend if self.config else "ir"
        suffix_map = {
            "llvm": ".ll",
            "wasm": ".wasm",
            "ir": ".ll",
        }
        suffix = suffix_map.get(backend, ".c")

        base_name = input_file.stem
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            return output_dir / f"{base_name}{suffix}"
        return input_file.parent / f"{base_name}{suffix}"

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
        self.pipeline = self._create_pipeline()
        return self.pipeline


# ------------------------------------------------------------------
# 命令行入口
# ------------------------------------------------------------------


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

    # 如果只运行静态分析（不编译）
    if args.analyze and not args.output:
        try:
            content = input_file.read_text(encoding="utf-8")
            ast, parse_errors = compiler._parse_source(content, input_file)

            if parse_errors:
                print(f"解析错误: {parse_errors[:10]}")
                return 1

            success = compiler.run_static_analysis(ast, input_file)
            return 0 if success else 1
        except Exception as e:
            print(f"静态分析失败: {e}")
            return 1

    # 执行编译
    if args.project:
        result = compiler.compile_module_project(input_file, output_dir)
    else:
        result = compiler.compile_single_file(input_file, output_dir)

    if args.verbose:
        compiler.show_stats()
        print(result.summary())

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
