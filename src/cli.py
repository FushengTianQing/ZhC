#!/usr/bin/env python3
"""
zhpp 命令行入口

中文C预处理器 - 将中文C代码转换为标准C代码。

用法:
    python -m zhpp input.zhc -o output.c
    python -m zhpp --project main.zhc --output build/
"""

import sys
import argparse
import time
import json
from pathlib import Path
from typing import Optional

# 尝试导入高级功能
HAS_MODULE_SYSTEM = False
try:
    from .compiler.pipeline import CompilationPipeline
    from .compiler.cache import CompilationCache
    from .compiler.optimizer import PerformanceMonitor
    HAS_MODULE_SYSTEM = True
except ImportError:
    pass


class ZHCCompiler:
    """中文C编译器主类"""
    
    def __init__(self, enable_cache: bool = True, verbose: bool = False, use_ast: bool = True,
                 skip_semantic: bool = False, warning_level: str = 'normal',
                 no_uninit: bool = False, no_unreachable: bool = False,
                 no_dataflow: bool = False, no_interprocedural: bool = False,
                 no_alias: bool = False, no_pointer: bool = False,
                 optimize_symbol_lookup: bool = False,
                 profile: bool = False,
                 backend: str = "ast",   # M6: ir 或 ast
                 dump_ir: bool = False,        # M6: 打印 IR
                 optimize_ir: bool = True):    # M6: 启用 IR 优化
        self.enable_cache = enable_cache
        self.verbose = verbose
        self.use_ast = use_ast  # Phase 4: 默认使用 AST 路径
        self.skip_semantic = skip_semantic  # Phase 5: 跳过语义验证
        self.warning_level = warning_level  # Phase 5 T3.5: 警告级别
        self.no_uninit = no_uninit        # Phase 6 M3: 禁用未初始化变量检查
        self.no_unreachable = no_unreachable  # Phase 6 M3: 禁用不可达代码检测
        self.no_dataflow = no_dataflow          # Phase 6 M5: 禁用数据流分析
        self.no_interprocedural = no_interprocedural  # Phase 6 M5: 禁用过程间分析
        self.no_alias = no_alias                # Phase 6 M5: 禁用别名分析
        self.no_pointer = no_pointer            # Phase 6 M5: 禁用指针分析
        self.optimize_symbol_lookup = optimize_symbol_lookup  # Phase 7: 符号查找优化器
        self.profile_enabled = profile              # Phase 7: 性能分析
        self.backend = backend                  # M6: 代码生成后端
        self.dump_ir = dump_ir                  # M6: 打印 IR
        self.optimize_ir = optimize_ir          # M6: IR 优化
        self.cache = None
        self.pipeline = None
        self.performance_monitor = None
        
        # Phase 7: 增量AST更新器 — 缓存上次成功编译的 AST（按文件路径分别缓存）
        self._prev_ast_by_file: dict = {}
        self._incremental_updater: Optional[Any] = None
        
        # 初始化高级功能（如果可用）
        if HAS_MODULE_SYSTEM:
            try:
                self.cache = CompilationCache(max_size_mb=100) if enable_cache else None
                self.pipeline = CompilationPipeline(
                    enable_cache=enable_cache,
                    skip_semantic=skip_semantic,
                    warning_level=warning_level,
                    no_uninit=no_uninit,
                    no_unreachable=no_unreachable,
                    no_dataflow=no_dataflow,
                    no_interprocedural=no_interprocedural,
                    no_alias=no_alias,
                    no_pointer=no_pointer,
                    optimize_symbol_lookup=optimize_symbol_lookup,
                )
                self.performance_monitor = PerformanceMonitor()
                if verbose:
                    print("✅ 模块系统支持已启用（AST 模式）")
            except Exception as e:
                if verbose:
                    print(f"⚠️ 高级功能初始化失败: {e}")
        
        # 基础转换统计
        self.stats = {
            'files_processed': 0,
            'total_lines': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': time.time()
        }
    
    def compile_single_file(self, input_file: Path, output_dir: Optional[Path] = None) -> bool:
        """编译单个文件（AST 模式）"""
        if self.verbose:
            print(f"📄 [AST] 编译: {input_file}")
        
        try:
            from .parser import parse as parse_source
            from .codegen import CCodeGenerator
            
            # Phase 7: 性能分析器初始化
            perf_analyzer = None
            if self.profile_enabled:
                from .analyzer.performance import PerformanceAnalyzer
                perf_analyzer = PerformanceAnalyzer()
            
            content = input_file.read_text(encoding='utf-8')
            
            # 1. 词法分析 + 语法分析
            if perf_analyzer:
                result, _ = perf_analyzer.measure_operation("词法/语法分析", parse_source, content)
                ast, errors = result
            else:
                ast, errors = parse_source(content)
            
            if errors:
                for err in errors[:10]:
                    print(f"  错误: {err}")
                return False
            
            # 1.5. 增量 AST 更新（Phase 7: diff 同文件两轮编译间的 AST 变化）
            file_key = str(input_file.resolve())
            prev_ast = self._prev_ast_by_file.get(file_key)
            
            if prev_ast is not None:
                try:
                    if self._incremental_updater is None:
                        from .analyzer.incremental_ast_updater import IncrementalASTUpdater
                        self._incremental_updater = IncrementalASTUpdater()
                    
                    diffs = self._incremental_updater.compute_diff(prev_ast, ast)
                    stats = self._incremental_updater.get_update_statistics(diffs)
                    
                    if stats['update'] > 0 or stats['insert'] > 0 or stats['delete'] > 0:
                        if self.verbose:
                            print(f"  🔄 [增量] 更新={stats['update']} 插入={stats['insert']} 删除={stats['delete']}")
                            print(self._incremental_updater.generate_report(diffs))
                except Exception:
                    pass  # 增量更新失败不影响正常编译
            
            # 2. 语义验证（Phase 5 新增）
            if not self.skip_semantic:
                if self.verbose:
                    print(f"  🔍 [语义验证] 分析中...")
                
                from .semantic import SemanticAnalyzer
                
                def run_semantic():
                    v = SemanticAnalyzer()
                    v.cfg_enabled = not self.no_unreachable
                    v.uninit_enabled = not self.no_uninit
                    v.dataflow_enabled = not self.no_dataflow
                    v.interprocedural_enabled = not self.no_interprocedural
                    v.alias_enabled = not self.no_alias
                    v.pointer_enabled = not self.no_pointer
                    v.symbol_lookup_enabled = self.optimize_symbol_lookup
                    v.analyze_file(ast, input_file.name)
                    return v
                
                if perf_analyzer:
                    validator, _ = perf_analyzer.measure_operation("语义验证", run_semantic)
                else:
                    validator = run_semantic()
                
                if validator.get_errors():
                    # 输出所有语义错误（格式化输出，最多20个）
                    print(validator.format_errors())
                    if len(validator.get_errors()) > 20:
                        print(f"  ... 还有 {len(validator.get_errors()) - 20} 个错误未显示")
                    return False
                
                # 输出警告（不阻止编译，受 warning_level 控制）
                warnings = validator.get_warnings()
                if self.warning_level != 'none' and warnings:
                    print(validator.format_warnings())
                    if self.warning_level == 'error':
                        print("  ❌ -Werror: 警告被当作错误处理")
                        return False
                
                if self.verbose:
                    stats = validator.get_statistics()
                    print(f"  ✅ [语义验证] 通过 (访问 {stats['nodes_visited']} 个节点, "
                          f"符号 {stats['symbols_added']} 个)")
            
            # 3. 代码生成
            def run_codegen():
                g = CCodeGenerator()
                return g.generate(ast)

            def run_ir_gen():
                from .ir.ir_generator import IRGenerator
                from .ir.ir_verifier import IRVerifier
                from .ir.optimizer import PassManager, ConstantFolding, DeadCodeElimination
                from .ir.c_backend import CBackend

                gen = IRGenerator()
                ir = gen.generate(ast)

                if self.dump_ir:
                    from .ir.printer import IRPrinter
                    printer = IRPrinter()
                    print("=== IR 生成 ===")
                    print(printer.print(ir))

                verifier = IRVerifier()
                errors = verifier.verify(ir)
                if errors:
                    for e in errors:
                        print(f"  IR 验证错误: {e.msg}")
                    return None

                if self.optimize_ir:
                    pm = PassManager()
                    pm.register(ConstantFolding())
                    pm.register(DeadCodeElimination())
                    ir = pm.run(ir)

                backend = CBackend()
                return backend.generate(ir)

            if self.backend == "ir":
                op_name = "IR代码生成"
                gen_func = run_ir_gen
            else:
                op_name = "代码生成"
                gen_func = run_codegen

            if perf_analyzer:
                c_code, _ = perf_analyzer.measure_operation(op_name, gen_func)
            else:
                c_code = gen_func()
            
            # 4. 写入输出文件
            if output_dir:
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / input_file.name.replace('.zhc', '.c')
            else:
                output_file = input_file.with_suffix('.c')
            
            output_file.write_text(c_code, encoding='utf-8')
            
            # Phase 7: 编译成功后缓存 AST，供下次增量 diff 使用（仅单文件模式）
            self._prev_ast_by_file[file_key] = ast
            
            if self.verbose:
                print(f"  [AST] 转换完成: {input_file} -> {output_file}")
            
            # Phase 7: 性能分析报告
            if perf_analyzer is not None:
                print("\n" + perf_analyzer.print_report())
            
            self.stats['files_processed'] += 1
            self.stats['total_lines'] += len(content.splitlines())
            return True
            
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"  [AST] 编译失败: {input_file}: {e}")
            return False
    
    def compile_module_project(self, input_file: Path, output_dir: Optional[Path] = None) -> bool:
        """编译模块项目（AST 模式）
        
        使用 CompilationPipeline 处理多文件模块项目。
        
        Args:
            input_file: 项目入口文件
            output_dir: 输出目录
            
        Returns:
            编译是否成功
        """
        if self.verbose:
            print(f"📁 [AST 模块项目] 编译: {input_file}")
        
        if not self.pipeline:
            # 初始化 Pipeline（如果之前未初始化）
            self.pipeline = CompilationPipeline(
                enable_cache=self.enable_cache,
                skip_semantic=self.skip_semantic,
                warning_level=self.warning_level,
                no_uninit=self.no_uninit,
                no_unreachable=self.no_unreachable,
                no_dataflow=self.no_dataflow,
                no_interprocedural=self.no_interprocedural,
                no_alias=self.no_alias,
                no_pointer=self.no_pointer,
                optimize_symbol_lookup=self.optimize_symbol_lookup,
            )
        
        try:
            success = self.pipeline.compile_project([str(input_file)])
            
            if self.verbose:
                print(f"  [AST 模块项目] {'成功' if success else '失败'}")
            
            return success
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            print(f"  [AST 模块项目] 编译失败: {e}")
            return False
    
    def clean_cache(self):
        """清理编译缓存（包括增量 AST 缓存）"""
        if self.cache:
            self.cache.clear()
        self._prev_ast_by_file.clear()
        if self.verbose:
            print("  🗑️ 编译缓存已清理（包括增量 AST 缓存）")
    
    def show_stats(self):
        """显示统计信息"""
        elapsed = time.time() - self.stats['start_time']
        print("\n📊 编译统计:")
        print(f"  文件数: {self.stats['files_processed']}")
        print(f"  总行数: {self.stats['total_lines']}")
        print(f"  耗时: {elapsed:.2f}秒")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='中文C预处理器 - 将中文C代码转换为标准C代码',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s hello.zhc                  # 编译单文件
  %(prog)s hello.zhc -o hello.c       # 指定输出文件
  %(prog)s --project main.zhc         # 编译模块项目
  %(prog)s --clean-cache              # 清理缓存
        """
    )
    
    parser.add_argument('input', nargs='?', help='输入文件 (.zhc)')
    parser.add_argument('-o', '--output', help='输出文件或目录')
    parser.add_argument('--project', action='store_true', help='编译模块项目')
    parser.add_argument('--legacy', action='store_true', help='[已废弃] AST 是唯一编译路径，此选项不再生效')
    parser.add_argument('--skip-semantic', action='store_true',
                        help='跳过语义验证（仅执行语法分析和代码生成）')
    parser.add_argument('-W', dest='warning_level', default='normal',
                        choices=['none', 'normal', 'all', 'error'],
                        help='警告级别: none=无警告, normal=默认, all=全部, error=警告当错误')
    parser.add_argument('--no-uninit', action='store_true',
                        help='禁用未初始化变量检查')
    parser.add_argument('--no-unreachable', action='store_true',
                        help='禁用不可达代码检测')
    parser.add_argument('--no-dataflow', action='store_true',
                        help='禁用数据流分析')
    parser.add_argument('--no-interprocedural', action='store_true',
                        help='禁用过程间分析')
    parser.add_argument('--no-alias', action='store_true',
                        help='禁用别名分析')
    parser.add_argument('--no-pointer', action='store_true',
                        help='禁用指针分析')
    parser.add_argument('--optimize-symbol-lookup', action='store_true',
                        help='启用符号查找优化器（热点缓存 + O(1)查找）')
    parser.add_argument('--profile', action='store_true',
                        help='启用性能分析（测量各编译阶段耗时）')
    parser.add_argument('--clean-cache', action='store_true', help='清理编译缓存')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--version', action='version', version='%(prog)s 3.0.0')
    
    args = parser.parse_args()
    
    # 创建编译器实例
    compiler = ZHCCompiler(verbose=args.verbose, use_ast=not args.legacy,
                           skip_semantic=args.skip_semantic,
                           warning_level=args.warning_level,
                           no_uninit=args.no_uninit,
                           no_unreachable=args.no_unreachable,
                           no_dataflow=args.no_dataflow,
                           no_interprocedural=args.no_interprocedural,
                           no_alias=args.no_alias,
                           no_pointer=args.no_pointer,
                           optimize_symbol_lookup=args.optimize_symbol_lookup,
                           profile=args.profile)
    
    # 清理缓存
    if args.clean_cache:
        compiler.clean_cache()
        return 0
    
    # 检查输入文件
    if not args.input:
        parser.print_help()
        return 1
    
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ 文件不存在: {input_file}")
        return 1
    
    # 设置输出路径
    output_dir = Path(args.output) if args.output else None
    
    # 编译
    if args.project:
        success = compiler.compile_module_project(input_file, output_dir)
    else:
        success = compiler.compile_single_file(input_file, output_dir)
    
    if args.verbose:
        compiler.show_stats()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())