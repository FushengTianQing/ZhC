#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译器配置模块

职责：
1. 编译器配置参数定义
2. 从命令行参数构建配置
3. 配置验证

作者：远
日期：2026-04-07
"""

import argparse
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompilerConfig:
    """编译器配置（从命令行参数构建）"""
    
    # 语义分析相关配置
    MAX_DISPLAY_ERRORS: int = 20  # 最多显示的错误数
    
    # 配置参数
    verbose: bool = False
    use_ast: bool = True
    skip_semantic: bool = False
    warning_level: str = "normal"
    no_uninit: bool = False
    no_unreachable: bool = False
    no_dataflow: bool = False
    no_interprocedural: bool = False
    no_alias: bool = False
    no_pointer: bool = False
    optimize_symbol_lookup: bool = False
    profile_enabled: bool = False
    backend: str = "ast"
    dump_ir: bool = False
    optimize_ir: bool = True
    enable_cache: bool = True
    
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
            verbose=getattr(args, 'verbose', False),
            use_ast=not getattr(args, 'legacy', False),
            skip_semantic=getattr(args, 'skip_semantic', False),
            warning_level=getattr(args, 'warning_level', 'normal'),
            no_uninit=getattr(args, 'no_uninit', False),
            no_unreachable=getattr(args, 'no_unreachable', False),
            no_dataflow=getattr(args, 'no_dataflow', False),
            no_interprocedural=getattr(args, 'no_interprocedural', False),
            no_alias=getattr(args, 'no_alias', False),
            no_pointer=getattr(args, 'no_pointer', False),
            optimize_symbol_lookup=getattr(args, 'optimize_symbol_lookup', False),
            profile_enabled=getattr(args, 'profile', False),
        )
    
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
        valid_backends = {"ast", "ir"}
        if self.backend not in valid_backends:
            return False
        
        return True