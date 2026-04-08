#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译器配置模块

职责：
1. 编译器配置参数定义
2. 配置分组（语义分析、输出、缓存、性能分析）
3. 从命令行参数构建配置
4. 配置验证

作者：远
日期：2026-04-07

重构说明：
- Phase 2 API 改进：使用配置分组减少构造函数参数
"""

import argparse
from dataclasses import dataclass, field
from typing import Literal, Optional


# =============================================================================
# 配置分组
# =============================================================================

@dataclass
class SemanticConfig:
    """语义分析配置"""
    enabled: bool = True
    check_uninit: bool = True
    check_unreachable: bool = True
    check_dataflow: bool = True
    check_interprocedural: bool = True
    check_alias: bool = True
    check_pointer: bool = True
    optimize_symbol_lookup: bool = False


@dataclass
class OutputConfig:
    """输出配置"""
    verbose: bool = False
    warning_level: Literal["none", "normal", "all", "error"] = "normal"
    backend: Literal["ir", "llvm", "wasm"] = "ir"
    dump_ir: bool = False
    optimize_ir: bool = True


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    max_display_errors: int = 20  # 最多显示的错误数


@dataclass
class ProfileConfig:
    """性能分析配置"""
    enabled: bool = False


@dataclass
class DebugConfig:
    """调试信息配置"""
    enabled: bool = False  # 是否生成调试信息
    dwarf_version: int = 5  # DWARF 版本


@dataclass
class AnalyzeConfig:
    """静态分析配置"""
    enabled: bool = False  # 是否运行静态分析
    format: str = "text"  # 报告格式: text, markdown, json, html
    output_file: Optional[str] = None  # 输出文件路径（None 表示输出到控制台）


# =============================================================================
# 编译器配置（重构版）
# =============================================================================

@dataclass
class CompilerConfig:
    """编译器配置
    
    使用配置分组，减少构造函数参数，提高可维护性。
    
    Attributes:
        output: 输出配置
        semantic: 语义分析配置
        cache: 缓存配置
        profile: 性能分析配置
        use_ast: 是否使用 AST 模式（仅用于向后兼容）
    
    Example:
        # 新方式（推荐）
        config = CompilerConfig(
            output=OutputConfig(verbose=True, warning_level="all"),
            semantic=SemanticConfig(enabled=True, check_uninit=False),
        )
        
        # 旧方式（向后兼容）
        config = CompilerConfig()
        config.verbose = True  # 通过兼容性属性访问
    """
    
    # 输出配置
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # 语义分析配置
    semantic: SemanticConfig = field(default_factory=SemanticConfig)
    
    # 缓存配置
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # 性能分析配置
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    
    # 调试信息配置
    debug: DebugConfig = field(default_factory=DebugConfig)
    
    # 静态分析配置
    analyze: AnalyzeConfig = field(default_factory=AnalyzeConfig)
    
    # 向后兼容参数（仅用于 legacy 模式）
    use_ast: bool = True
    
    # -------------------------------------------------------------------------
    # 兼容性属性
    # -------------------------------------------------------------------------
    
    @property
    def verbose(self) -> bool:
        """是否详细输出"""
        return self.output.verbose
    
    @verbose.setter
    def verbose(self, value: bool) -> None:
        self.output.verbose = value
    
    @property
    def warning_level(self) -> str:
        """警告级别"""
        return self.output.warning_level
    
    @warning_level.setter
    def warning_level(self, value: str) -> None:
        self.output.warning_level = value  # type: ignore
    
    @property
    def skip_semantic(self) -> bool:
        """是否跳过语义分析"""
        return not self.semantic.enabled
    
    @skip_semantic.setter
    def skip_semantic(self, value: bool) -> None:
        self.semantic.enabled = not value
    
    @property
    def enable_cache(self) -> bool:
        """是否启用缓存"""
        return self.cache.enabled
    
    @enable_cache.setter
    def enable_cache(self, value: bool) -> None:
        self.cache.enabled = value
    
    @property
    def backend(self) -> str:
        """后端类型"""
        return self.output.backend
    
    @backend.setter
    def backend(self, value: str) -> None:
        self.output.backend = value  # type: ignore
    
    @property
    def dump_ir(self) -> bool:
        """是否输出 IR"""
        return self.output.dump_ir
    
    @dump_ir.setter
    def dump_ir(self, value: bool) -> None:
        self.output.dump_ir = value
    
    @property
    def optimize_ir(self) -> bool:
        """是否优化 IR"""
        return self.output.optimize_ir
    
    @optimize_ir.setter
    def optimize_ir(self, value: bool) -> None:
        self.output.optimize_ir = value
    
    @property
    def profile_enabled(self) -> bool:
        """是否启用性能分析"""
        return self.profile.enabled
    
    @profile_enabled.setter
    def profile_enabled(self, value: bool) -> None:
        self.profile.enabled = value
    
    @property
    def debug_enabled(self) -> bool:
        """是否启用调试信息生成"""
        return self.debug.enabled
    
    @debug_enabled.setter
    def debug_enabled(self, value: bool) -> None:
        self.debug.enabled = value
    
    @property
    def analyze_enabled(self) -> bool:
        """是否启用静态分析"""
        return self.analyze.enabled
    
    @analyze_enabled.setter
    def analyze_enabled(self, value: bool) -> None:
        self.analyze.enabled = value
    
    @property
    def analyze_format(self) -> str:
        """静态分析报告格式"""
        return self.analyze.format
    
    @analyze_format.setter
    def analyze_format(self, value: str) -> None:
        self.analyze.format = value
    
    @property
    def analyze_output(self) -> Optional[str]:
        """静态分析报告输出文件"""
        return self.analyze.output_file
    
    @analyze_output.setter
    def analyze_output(self, value: Optional[str]) -> None:
        self.analyze.output_file = value
    
    @property
    def no_uninit(self) -> bool:
        """是否禁用未初始化检查"""
        return not self.semantic.check_uninit
    
    @no_uninit.setter
    def no_uninit(self, value: bool) -> None:
        self.semantic.check_uninit = not value
    
    @property
    def no_unreachable(self) -> bool:
        """是否禁用不可达代码检测"""
        return not self.semantic.check_unreachable
    
    @no_unreachable.setter
    def no_unreachable(self, value: bool) -> None:
        self.semantic.check_unreachable = not value
    
    @property
    def no_dataflow(self) -> bool:
        """是否禁用数据流分析"""
        return not self.semantic.check_dataflow
    
    @no_dataflow.setter
    def no_dataflow(self, value: bool) -> None:
        self.semantic.check_dataflow = not value
    
    @property
    def no_interprocedural(self) -> bool:
        """是否禁用过程间分析"""
        return not self.semantic.check_interprocedural
    
    @no_interprocedural.setter
    def no_interprocedural(self, value: bool) -> None:
        self.semantic.check_interprocedural = not value
    
    @property
    def no_alias(self) -> bool:
        """是否禁用别名分析"""
        return not self.semantic.check_alias
    
    @no_alias.setter
    def no_alias(self, value: bool) -> None:
        self.semantic.check_alias = not value
    
    @property
    def no_pointer(self) -> bool:
        """是否禁用指针分析"""
        return not self.semantic.check_pointer
    
    @no_pointer.setter
    def no_pointer(self, value: bool) -> None:
        self.semantic.check_pointer = not value
    
    @property
    def optimize_symbol_lookup(self) -> bool:
        """是否启用符号查找优化"""
        return self.semantic.optimize_symbol_lookup
    
    @optimize_symbol_lookup.setter
    def optimize_symbol_lookup(self, value: bool) -> None:
        self.semantic.optimize_symbol_lookup = value
    
    @property
    def MAX_DISPLAY_ERRORS(self) -> int:
        """最多显示的错误数"""
        return self.cache.max_display_errors
    
    # -------------------------------------------------------------------------
    # 工厂方法
    # -------------------------------------------------------------------------
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CompilerConfig":
        """
        从命令行参数创建配置
        
        Args:
            args: 解析后的命令行参数
            
        Returns:
            编译器配置实例
        """
        return cls(
            output=OutputConfig(
                verbose=getattr(args, 'verbose', False),
                warning_level=getattr(args, 'warning_level', 'normal'),
                backend=getattr(args, 'backend', 'ir'),
                dump_ir=getattr(args, 'dump_ir', False),
                optimize_ir=not getattr(args, 'no_optimize', False),
            ),
            semantic=SemanticConfig(
                enabled=not getattr(args, 'skip_semantic', False),
                check_uninit=not getattr(args, 'no_uninit', False),
                check_unreachable=not getattr(args, 'no_unreachable', False),
                check_dataflow=not getattr(args, 'no_dataflow', False),
                check_interprocedural=not getattr(args, 'no_interprocedural', False),
                check_alias=not getattr(args, 'no_alias', False),
                check_pointer=not getattr(args, 'no_pointer', False),
                optimize_symbol_lookup=getattr(args, 'optimize_symbol_lookup', False),
            ),
            cache=CacheConfig(
                enabled=True,
            ),
            profile=ProfileConfig(
                enabled=getattr(args, 'profile', False),
            ),
            debug=DebugConfig(
                enabled=getattr(args, 'debug', False),
            ),
            analyze=AnalyzeConfig(
                enabled=getattr(args, 'analyze', False),
                format=getattr(args, 'analyze_format', 'text'),
                output_file=getattr(args, 'analyze_output', None),
            ),
            use_ast=not getattr(args, 'legacy', False),
        )
    
    # -------------------------------------------------------------------------
    # 验证方法
    # -------------------------------------------------------------------------
    
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            配置是否有效
        """
        # 检查警告级别
        valid_warning_levels = {"none", "normal", "all", "error"}
        if self.warning_level not in valid_warning_levels:
            return False
        
        # 检查后端
        valid_backends = {"ir", "llvm", "wasm"}
        if self.backend not in valid_backends:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """
        转换为字典表示
        
        Returns:
            配置的字典表示
        """
        return {
            'output': {
                'verbose': self.output.verbose,
                'warning_level': self.output.warning_level,
                'backend': self.output.backend,
                'dump_ir': self.output.dump_ir,
                'optimize_ir': self.output.optimize_ir,
            },
            'semantic': {
                'enabled': self.semantic.enabled,
                'check_uninit': self.semantic.check_uninit,
                'check_unreachable': self.semantic.check_unreachable,
                'check_dataflow': self.semantic.check_dataflow,
                'check_interprocedural': self.semantic.check_interprocedural,
                'check_alias': self.semantic.check_alias,
                'check_pointer': self.semantic.check_pointer,
                'optimize_symbol_lookup': self.semantic.optimize_symbol_lookup,
            },
            'cache': {
                'enabled': self.cache.enabled,
                'max_display_errors': self.cache.max_display_errors,
            },
            'profile': {
                'enabled': self.profile.enabled,
            },
            'use_ast': self.use_ast,
        }
