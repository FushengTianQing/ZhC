#!/usr/bin/env python3
"""
集成编译流水线

将所有功能整合到完整的编译流水线中：
1. AST 解析 (Lexer → Parser)
2. 语义验证（可选）
3. C 代码生成 (AST → CCodeGenerator)
4. 依赖解析 + 编译顺序计算
5. 缓存系统

架构：
中文代码 → AST解析 → 语义验证(可选) → C代码生成 → 依赖分析 → 编译排序 → C编译 → 可执行文件

作者：远
日期：2026-04-03

重构说明：
- 统一导入路径，使用正确的模块路径
- Phase 4: 切换到 AST 路径，替代 legacy CodeConverter
"""

import os
import sys
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any

# 使用绝对导入，清晰的模块路径
from ..parser.module import ModuleParser
from ..converter.error import ErrorHandler
from ..analyzer.dependency import DependencyResolver, MultiFileIntegrator

logger = logging.getLogger(__name__)


class CompilationPipeline:
    """集成编译流水线（AST 模式）"""
    
    def __init__(self, cache_dir: str = ".zhc_cache", enable_cache: bool = True,
                 skip_semantic: bool = False, warning_level: str = 'normal',
                 no_uninit: bool = False, no_unreachable: bool = False,
                 no_dataflow: bool = False, no_interprocedural: bool = False,
                 no_alias: bool = False, no_pointer: bool = False,
                 optimize_symbol_lookup: bool = False):
        """
        初始化编译流水线
        
        Args:
            cache_dir: 缓存目录
            enable_cache: 是否启用缓存
            skip_semantic: 是否跳过语义验证
            warning_level: 警告级别 (none/normal/all/error)
            no_uninit: 禁用未初始化变量检查
            no_unreachable: 禁用不可达代码检测
            no_dataflow: 禁用数据流分析
            no_interprocedural: 禁用过程间分析
            no_alias: 禁用别名分析
            no_pointer: 禁用指针分析
            optimize_symbol_lookup: 启用符号查找优化器
        """
        self.cache_dir = Path(cache_dir)
        self.enable_cache = enable_cache
        self.skip_semantic = skip_semantic
        self.warning_level = warning_level
        
        # Phase 6/7 分析器开关（与 CLI --no-* 参数对齐）
        self.no_uninit = no_uninit
        self.no_unreachable = no_unreachable
        self.no_dataflow = no_dataflow
        self.no_interprocedural = no_interprocedural
        self.no_alias = no_alias
        self.no_pointer = no_pointer
        self.optimize_symbol_lookup = optimize_symbol_lookup
        
        # 初始化各阶段处理器
        self.error_handler = ErrorHandler()
        self.module_parser = ModuleParser()
        self.dependency_resolver = DependencyResolver(self.error_handler)
        self.file_integrator = MultiFileIntegrator(self.dependency_resolver)
        
        # 缓存系统
        self.file_hash_cache: Dict[str, str] = {}
        self.compilation_cache: Dict[str, Any] = {}
        
        # 性能统计
        self.stats = {
            'total_files': 0,
            'cached_files': 0,
            'parsed_files': 0,
            'converted_files': 0,
            'dependency_analyzed': 0,
            'total_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # 确保缓存目录存在
        if enable_cache:
            self.cache_dir.mkdir(exist_ok=True)
            
    def _get_file_hash(self, filepath: Path) -> str:
        """计算文件内容的哈希值"""
        filepath_key = str(filepath)
        if filepath_key in self.file_hash_cache:
            return self.file_hash_cache[filepath_key]
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            file_hash = hashlib.md5(content.encode()).hexdigest()
            self.file_hash_cache[filepath_key] = file_hash
            return file_hash
            
    def _get_cache_key(self, filepath: Path, stage: str) -> str:
        """获取缓存键"""
        file_hash = self._get_file_hash(filepath)
        return f"{stage}_{file_hash}"
        
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if not self.enable_cache:
            return None
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            import pickle
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return None
        return None
        
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """保存数据到缓存"""
        if not self.enable_cache:
            return
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        import pickle
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
            
    def _generate_markdown_report(self, processed_files: List[Optional[Dict]], compilation_order: List[str], 
                                 integration_info: Dict, errors: List) -> str:
        """
        生成Markdown格式的编译报告
        
        Args:
            processed_files: 已处理的文件列表
            compilation_order: 编译顺序
            integration_info: 集成信息
            errors: 错误列表
            
        Returns:
            Markdown格式的报告
        """
        import datetime
        
        report = f"""# 中文C编译器编译报告

**生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**编译器版本**: Phase 4 - AST 编译流水线

## 📊 编译概览

**处理文件**: {len(processed_files)} 个
**编译顺序**: {' → '.join(compilation_order) if compilation_order else 'N/A'}
**模块总数**: {integration_info.get('statistics', {}).get('total_modules', 0)}
**总依赖数**: {integration_info.get('statistics', {}).get('total_dependencies', 0)}

## 📋 模块详情

### 模块统计
"""
        
        # 添加模块统计
        stats = integration_info.get('statistics', {})
        if stats:
            report += f"""
- **模块总数**: {stats.get('total_modules', 0)}
- **平均依赖数**: {stats.get('avg_dependencies_per_module', 0):.1f}
- **公开符号总数**: {stats.get('total_public_symbols', 0)}
- **私有符号总数**: {stats.get('total_private_symbols', 0)}
- **无依赖模块**: {stats.get('modules_without_deps', 0)} 个
"""
        
        # 添加依赖问题
        issues = integration_info.get('dependency_issues', {})
        if issues:
            report += f"""
## ⚠️ 依赖问题

**总问题数**: {issues.get('total_issues', 0)}

### 循环依赖
"""
            cycles = issues.get('cycles', [])
            if cycles:
                for i, cycle in enumerate(cycles, 1):
                    report += f"- {i}. {' → '.join(cycle)}\n"
            else:
                report += "- 无循环依赖\n"
            
            report += "\n### 缺失依赖\n"
            missing = issues.get('missing_dependencies', [])
            if missing:
                for i, (module, dep) in enumerate(missing, 1):
                    report += f"- {i}. 模块 `{module}` 缺失依赖: `{dep}`\n"
            else:
                report += "- 无缺失依赖\n"
        
        # 添加文件详情
        report += f"""
## 📁 文件详情

**总文件数**: {integration_info.get('files', {}).get('total_files', 0)}
"""
        
        module_files = integration_info.get('files', {}).get('module_files', [])
        if module_files:
            report += "\n### 模块文件列表\n"
            for i, module in enumerate(module_files, 1):
                report += f"- {i}. `{module}`\n"
        
        # 添加处理文件详情
        if processed_files:
            report += "\n### 处理文件详情\n"
            for i, file_info in enumerate(processed_files, 1):
                if file_info:
                    report += f"#### {i}. `{file_info.get('zhc_filepath', 'N/A')}`\n"
                    report += f"- **C头文件**: `{file_info.get('h_filepath', 'N/A')}`\n"
                    report += f"- **C源文件**: `{file_info.get('c_filepath', 'N/A')}`\n"
                    if 'conversion_stats' in file_info:
                        stats = file_info['conversion_stats']
                        report += f"- **转换统计**: {stats.get('total_converted', 0)} 个符号\n"
        
        # 添加错误和警告
        if errors:
            report += f"""
## ❌ 错误和警告

**总错误/警告数**: {len(errors)}

"""
            for i, error in enumerate(errors, 1):
                # ErrorRecord 对象，需要获取其属性
                severity = getattr(error, 'severity', 'UNKNOWN')
                message = getattr(error, 'message', 'N/A')
                line = getattr(error, 'line', None)
                
                report += f"### {i}. {severity}\n"
                report += f"- **消息**: {message}\n"
                if line:
                    report += f"- **行号**: {line}\n"
                report += "\n"
        else:
            report += f"""
## ✅ 编译状态

**所有检查通过** - 没有发现错误或警告！

## 📝 优化建议

"""
        
        # 添加优化建议
        recommendations = integration_info.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += "无优化建议。\n"
        
        report += f"""
## 🚀 性能统计

**总处理时间**: {self.stats.get('total_processing_time', 0):.2f} 秒
**缓存命中率**: {self.stats.get('cache_hit_rate', 0):.1f}%
**文件处理吞吐量**: {self.stats.get('files_per_second', 0):.2f} 文件/秒

---

*报告由中文C编译器 Phase 4 AST 编译流水线生成*
"""
        return report
            
    def process_file(self, filepath: Path, is_main: bool = False) -> Optional[Dict[str, Any]]:
        """
        处理单个文件（AST 模式）
        
        Args:
            filepath: 源文件路径
            is_main: 是否是主文件
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        self.stats['total_files'] += 1
        
        logger.info("处理文件: %s", filepath.name)
        
        # 1. 检查缓存
        parse_cache_key = self._get_cache_key(filepath, "ast_parse")
        cached_result = self._get_from_cache(parse_cache_key)
        
        if cached_result:
            self.stats['cached_files'] += 1
            logger.debug("缓存命中: AST解析结果")
            
            # 写入缓存的 C 代码
            c_filepath = filepath.with_suffix('.c')
            h_filepath = filepath.with_suffix('.h')
            with open(c_filepath, 'w', encoding='utf-8') as f:
                f.write(cached_result.get('c_code', ''))
            if cached_result.get('h_code'):
                with open(h_filepath, 'w', encoding='utf-8') as f:
                    f.write(cached_result['h_code'])
            
            # 注册到依赖解析器
            for module_info in cached_result.get('modules', []):
                self.dependency_resolver.add_module(module_info)
            
            processing_time = time.time() - start_time
            return {
                'filepath': filepath,
                'module_name': cached_result.get('first_module_name', 'global'),
                'c_filepath': c_filepath,
                'h_filepath': h_filepath,
                'imports': cached_result.get('imports', []),
                'processing_time': processing_time,
                'has_errors': False,
                'semantic_errors': cached_result.get('semantic_errors', 0),
                'semantic_warnings': cached_result.get('semantic_warnings', 0),
            }
        
        # 2. AST 解析 (Lexer → Parser → AST)
        from ..parser import parse as parse_source
        
        content = filepath.read_text(encoding='utf-8')
        ast, parse_errors = parse_source(content)
        
        if parse_errors:
            for err in parse_errors[:10]:
                logger.error("语法错误 %s: %s", filepath.name, err)
            self.stats['total_files'] -= 1  # 回退计数
            return None
        
        self.stats['parsed_files'] += 1
        
        # 3. 语义验证（可选）
        semantic_errors = 0
        semantic_warnings = 0
        
        if not self.skip_semantic:
            try:
                from ..semantic import SemanticAnalyzer
                validator = SemanticAnalyzer()
                # Phase 6/7: 配置分析器开关（与单文件模式 compile_single_file 一致）
                validator.cfg_enabled = not self.no_unreachable
                validator.uninit_enabled = not self.no_uninit
                validator.dataflow_enabled = not self.no_dataflow
                validator.interprocedural_enabled = not self.no_interprocedural
                validator.alias_enabled = not self.no_alias
                validator.pointer_enabled = not self.no_pointer
                validator.symbol_lookup_enabled = self.optimize_symbol_lookup
                validator.analyze_file(ast, filepath.name)
                
                semantic_errors = len(validator.get_errors())
                semantic_warnings = len(validator.get_warnings())
                
                if validator.get_errors():
                    for err in validator.get_errors()[:10]:
                        logger.error("语义错误 %s: %s", filepath.name, err)
                    if semantic_errors > 10:
                        logger.error("... 还有 %d 个错误未显示", semantic_errors - 10)
                    
                    # -Werror: 警告当错误处理
                    if self.warning_level == 'error' and semantic_warnings > 0:
                        logger.error("语义错误: -Werror 模式下 %d 个警告被当作错误", semantic_warnings)
                        semantic_errors += semantic_warnings
                        semantic_warnings = 0
                
                if self.warning_level != 'none' and semantic_warnings > 0:
                    for warn in validator.get_warnings()[:5]:
                        logger.warning("语义警告 %s: %s", filepath.name, warn)
            except Exception as e:
                logger.error("语义验证失败 %s: %s", filepath.name, e)
                semantic_errors += 1  # 异常计入错误，阻止生成错误的 C 代码
        
        if semantic_errors > 0:
            self.stats['total_files'] -= 1
            return None
        
        # 4. C 代码生成 (AST → C)
        from ..codegen import CCodeGenerator
        
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
        
        self.stats['converted_files'] += 1
        
        # 5. 写入 C 文件
        c_filepath = filepath.with_suffix('.c')
        h_filepath = filepath.with_suffix('.h')
        
        with open(c_filepath, 'w', encoding='utf-8') as f:
            f.write(c_code)
        
        # 6. 模块依赖分析
        module_declarations: List[Dict[str, Any]] = []
        first_module_name: Optional[str] = None
        all_imports: List[str] = []
        
        # 收集模块信息（从 AST 的 ImportDeclNode）
        for decl in ast.declarations:
            if hasattr(decl, 'node_type'):
                # 模块声明
                if decl.node_type.value == 'MODULE_DECL':
                    module_declarations.append({
                        'name': getattr(decl, 'name', filepath.stem),
                        'file_path': str(filepath),
                        'imports': [getattr(imp, 'module_name', '') for imp in getattr(decl, 'imports', [])],
                        'symbols': {
                            'public': {},
                            'private': {}
                        },
                        'line_number': getattr(decl, 'line', 1)
                    })
                    if first_module_name is None:
                        first_module_name = getattr(decl, 'name', filepath.stem)
                
                # 顶层导入（非模块内）
                elif decl.node_type.value == 'IMPORT_DECL':
                    all_imports.append(getattr(decl, 'module_name', ''))
        
        # 注册到依赖解析器
        for module_decl in module_declarations:
            self.dependency_resolver.add_module(module_decl)
            self.stats['dependency_analyzed'] += 1
        
        # 7. 保存到缓存
        cache_data = {
            'c_code': c_code,
            'h_code': '',  # AST 模式暂不生成独立头文件
            'modules': module_declarations,
            'first_module_name': first_module_name,
            'imports': all_imports,
            'semantic_errors': semantic_errors,
            'semantic_warnings': semantic_warnings,
        }
        self._save_to_cache(parse_cache_key, cache_data)
        
        # 注册 C 文件路径
        if first_module_name:
            self.file_integrator.register_c_file(
                first_module_name,
                str(c_filepath),
                str(h_filepath) if h_filepath.exists() else ''
            )
        
        processing_time = time.time() - start_time
        logger.debug("完成: %s (%.3fs)", c_filepath.name, processing_time)
        
        return {
            'filepath': filepath,
            'module_name': first_module_name if first_module_name else filepath.stem,
            'c_filepath': c_filepath,
            'h_filepath': h_filepath,
            'imports': all_imports,
            'processing_time': processing_time,
            'has_errors': False,
            'semantic_errors': semantic_errors,
            'semantic_warnings': semantic_warnings,
        }
        
    def compile_project(self, source_files: List[str], output_name: str = "a.out") -> bool:
        """
        编译整个项目
        
        Args:
            source_files: 源文件列表
            output_name: 输出文件名
            
        Returns:
            编译是否成功
        """
        total_start_time = time.time()
        logger.info("开始编译项目...")
        logger.info("源文件数: %d", len(source_files))
        
        # 重置统计
        self.stats = {k: 0 for k in self.stats.keys()}
        self.error_handler.reset()  # ErrorHandler 使用 reset() 而不是 clear_errors()
        
        # 1. 处理所有源文件
        processed_files = []
        source_paths = [Path(f) for f in source_files]
        
        for filepath in source_paths:
            if not filepath.exists():
                from ..converter.error import ErrorType
                self.error_handler.add_error(
                    ErrorType.FILE_NOT_FOUND,
                    f"文件不存在: {filepath}",
                    line_no=0
                )
                continue
                
            result = self.process_file(filepath)
            processed_files.append(result)
            
        # 2. 分析依赖关系 (Day 4)
        logger.info("分析模块依赖关系...")
        # 使用 export_dependency_graph 获取依赖图
        dependency_info = self.dependency_resolver.export_dependency_graph()
        dependency_graph = dependency_info.get('modules', {})
        logger.debug("发现模块: %s", list(dependency_graph.keys()))
        
        # 3. 检查循环依赖
        logger.info("检查循环依赖...")
        cycles = self.dependency_resolver.detect_cycles()
        if cycles:
            logger.warning("发现循环依赖: %s", cycles)
            for cycle in cycles:
                from ..converter.error import ErrorType
                self.error_handler.add_error(
                    ErrorType.DEPENDENCY_CYCLE,
                    f"循环依赖: {' -> '.join(cycle)}",
                    line_no=0
                )
        else:
            logger.info("无循环依赖")
            
        # 4. 计算编译顺序
        logger.info("计算编译顺序...")
        if cycles:
            logger.warning("存在循环依赖，无法计算编译顺序")
            compilation_order = list(dependency_graph.keys())
        else:
            # 使用 dependency_resolver 的编译顺序计算方法
            compilation_order = self.dependency_resolver.calculate_compilation_order()
            logger.info("编译顺序: %s", compilation_order)
            
        # 5. 生成Makefile
        logger.info("生成构建配置...")
        # 使用当前目录作为输出目录
        output_dir = "."
        makefile = self.file_integrator.generate_makefile(output_dir)
        
        makefile_path = Path("Makefile")
        with open(makefile_path, 'w') as f:
            f.write(makefile)
        logger.info("生成: %s", makefile_path)
        
        # 6. 生成集成报告
        integration_info = self.file_integrator.export_integration_report()
        report = self._generate_markdown_report(
            processed_files,
            compilation_order,
            integration_info,
            self.error_handler.get_errors()  # 直接使用列表，不需要 .values()
        )
        
        report_path = Path("compilation_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info("生成: %s", report_path)
        
        # 7. 显示错误和警告
        errors = self.error_handler.get_errors()
        if errors:
            logger.warning("发现 %d 个错误/警告", len(errors))
            for i, error in enumerate(errors, 1):
                # ErrorRecord 对象，需要获取其属性
                severity = getattr(error, 'severity', 'UNKNOWN')
                message = getattr(error, 'message', 'N/A')
                logger.warning("%d: %s (%s)", i, message, severity)
                
        # 8. 执行编译（如果无错误）
        has_errors = any(getattr(e, 'severity', '') == 'ERROR' for e in errors)
        
        # 在测试环境中，我们可以跳过实际的make步骤
        # 检查是否设置了TEST_MODE环境变量
        test_mode = os.environ.get('ZHCPP_TEST_MODE', '0') == '1'
        
        if not has_errors:
            logger.info("开始编译...")
            if test_mode:
                # 测试模式：不执行实际编译，只模拟成功
                logger.info("测试模式：跳过实际编译步骤")
                logger.info("模拟编译成功: %s", output_name)
            else:
                try:
                    import subprocess
                    compile_result = subprocess.run(
                        ["make", "-j4"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if compile_result.returncode == 0:
                        logger.info("编译成功: %s", output_name)
                        logger.debug("输出: %s", compile_result.stdout)
                    else:
                        logger.error("编译失败")
                        logger.error("错误: %s", compile_result.stderr)
                        has_errors = True
                except Exception as e:
                    logger.error("编译异常: %s", e)
                    has_errors = True
        else:
            logger.warning("由于存在错误，跳过编译步骤")
            
        # 9. 性能统计
        total_time = time.time() - total_start_time
        self.stats['total_time'] = total_time
        
        if self.stats['total_files'] > 0:
            self.stats['cache_hit_rate'] = (
                self.stats['cached_files'] / self.stats['total_files'] * 100
            )
            
        logger.info("性能统计: 总文件=%d, 缓存命中=%d (%.1f%%), 解析=%d, 转换=%d, 依赖分析=%d, 总用时=%.3fs",
                     self.stats['total_files'],
                     self.stats['cached_files'],
                     self.stats['cache_hit_rate'],
                     self.stats['parsed_files'],
                     self.stats['converted_files'],
                     self.stats['dependency_analyzed'],
                     total_time)
        
        if self.stats['total_files'] > 0:
            avg_time = total_time / self.stats['total_files']
            logger.info("平均文件处理时间: %.3fs", avg_time)
            
        return not has_errors
        
    def incremental_compile(self, source_files: List[str], output_name: str = "a.out") -> bool:
        """
        增量编译
        
        Args:
            source_files: 源文件列表
            output_name: 输出文件名
            
        Returns:
            编译是否成功
        """
        logger.info("增量编译模式...")
        
        # 检查哪些文件需要重新编译
        need_recompile = []
        source_paths = [Path(f) for f in source_files]
        
        for filepath in source_paths:
            # 检查文件是否已缓存
            parse_cache_key = self._get_cache_key(filepath, "parse")
            cached_data = self._get_from_cache(parse_cache_key)
            
            if cached_data is None:
                # 无缓存，需要编译
                need_recompile.append(filepath)
            else:
                # 检查文件是否已修改
                current_hash = self._get_file_hash(filepath)
                cached_hash = cached_data.get('file_hash', '')
                
                if current_hash != cached_hash:
                    # 文件已修改，需要重新编译
                    need_recompile.append(filepath)
                    
        if not need_recompile:
            logger.info("所有文件都是最新的，无需重新编译")
            return True
            
        logger.info("%d/%d 个文件需要重新编译", len(need_recompile), len(source_files))
        for f in need_recompile:
            logger.debug("  需要重新编译: %s", f.name)
            
        # 只重新编译需要的文件
        self.error_handler.reset()
        for filepath in need_recompile:
            self.process_file(filepath)
            
        # 重新分析依赖关系
        # 重新创建依赖解析器
        self.dependency_resolver = DependencyResolver(self.error_handler)
        self.file_integrator = MultiFileIntegrator(self.dependency_resolver)
        
        # 重新处理所有文件以建立依赖关系
        for filepath in source_paths:
            result = self.process_file(filepath)
            if result:
                # 从处理结果中提取模块信息并添加到依赖解析器
                module_decl = {
                    'name': result.get('module_name', filepath.stem),
                    'file_path': str(filepath),
                    'imports': result.get('imports', []),
                    'symbols': {'public': {}, 'private': {}},
                    'line_number': 1
                }
                self.dependency_resolver.add_module(module_decl)
            
        # 重新计算编译顺序并编译
        return self.compile_project(
            [str(f) for f in source_paths],
            output_name
        )

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='中文C编译器集成编译流水线')
    parser.add_argument('files', nargs='+', help='源文件列表')
    parser.add_argument('-o', '--output', default='a.out', help='输出文件名')
    parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    parser.add_argument('--incremental', action='store_true', help='增量编译模式')
    parser.add_argument('--clean', action='store_true', help='清理缓存')
    
    args = parser.parse_args()
    
    # 配置日志（main入口处才配置handler）
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # 清理缓存
    if args.clean:
        cache_dir = Path(".zhc_cache")
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            logger.info("已清理缓存目录: %s", cache_dir)
        return
    
    # 创建编译流水线
    pipeline = CompilationPipeline(
        enable_cache=not args.no_cache
    )
    
    # 编译项目
    if args.incremental:
        success = pipeline.incremental_compile(args.files, args.output)
    else:
        success = pipeline.compile_project(args.files, args.output)
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
