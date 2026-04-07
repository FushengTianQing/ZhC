"""
clang-format集成模块
Clang-Format Integration

提供代码格式化功能，集成clang-format工具。

核心功能：
1. 代码格式化：使用clang-format格式化代码
2. 配置管理：支持.clang-format配置文件
3. 风格检查：检查代码风格是否符合规范
4. 批量格式化：支持批量格式化多个文件

使用场景：
- 代码提交前自动格式化
- CI/CD代码风格检查
- IDE集成格式化
"""

import subprocess
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json


@dataclass
class FormatResult:
    """格式化结果"""
    success: bool              # 是否成功
    original: str             # 原始代码
    formatted: str            # 格式化后代码
    changed: bool             # 是否有变化
    errors: List[str]         # 错误信息
    warnings: List[str]       # 警告信息
    metadata: Dict = None     # 元数据
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ClangFormatIntegration:
    """
    clang-format集成
    
    提供代码格式化功能
    
    示例：
    >>> formatter = ClangFormatIntegration()
    >>> result = formatter.format_code("int main(){return 0;}")
    >>> print(result.formatted)
    """
    
    def __init__(self,
                 clang_format_path: str = "clang-format",
                 style: str = "LLVM",
                 fallback_on_missing: bool = True):
        """
        初始化clang-format集成
        
        Args:
            clang_format_path: clang-format路径
            style: 格式化风格（LLVM, Google, Chromium, Mozilla, WebKit等）
            fallback_on_missing: clang-format缺失时是否回退到简单格式化
        """
        self.clang_format_path = clang_format_path
        self.style = style
        self.fallback_on_missing = fallback_on_missing
        
        # 检查clang-format是否可用
        self.available = self._check_availability()
        
        # 统计信息
        self.stats = {
            'total_formats': 0,
            'successful_formats': 0,
            'failed_formats': 0,
            'fallback_formats': 0
        }
    
    def _check_availability(self) -> bool:
        """检查clang-format是否可用"""
        try:
            result = subprocess.run(
                [self.clang_format_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def format_code(self,
                   code: str,
                   filename: Optional[str] = None) -> FormatResult:
        """
        格式化代码
        
        Args:
            code: 原始代码
            filename: 文件名（用于推断语言）
            
        Returns:
            FormatResult: 格式化结果
        """
        self.stats['total_formats'] += 1
        
        if self.available:
            # 使用clang-format
            try:
                args = [
                    self.clang_format_path,
                    f"--style={self.style}"
                ]
                
                if filename:
                    args.append(f"--assume-filename={filename}")
                
                result = subprocess.run(
                    args,
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    formatted = result.stdout
                    changed = formatted != code
                    
                    self.stats['successful_formats'] += 1
                    
                    return FormatResult(
                        success=True,
                        original=code,
                        formatted=formatted,
                        changed=changed,
                        errors=[],
                        warnings=[]
                    )
                else:
                    self.stats['failed_formats'] += 1
                    
                    return FormatResult(
                        success=False,
                        original=code,
                        formatted=code,
                        changed=False,
                        errors=[result.stderr],
                        warnings=[]
                    )
            
            except subprocess.TimeoutExpired:
                self.stats['failed_formats'] += 1
                
                return FormatResult(
                    success=False,
                    original=code,
                    formatted=code,
                    changed=False,
                    errors=["格式化超时"],
                    warnings=[]
                )
        
        elif self.fallback_on_missing:
            # 回退到简单格式化
            formatted = self._simple_format(code)
            changed = formatted != code
            
            self.stats['fallback_formats'] += 1
            
            return FormatResult(
                success=True,
                original=code,
                formatted=formatted,
                changed=changed,
                errors=[],
                warnings=["使用简单格式化（clang-format不可用）"]
            )
        
        else:
            self.stats['failed_formats'] += 1
            
            return FormatResult(
                success=False,
                original=code,
                formatted=code,
                changed=False,
                errors=["clang-format不可用"],
                warnings=[]
            )
    
    def _simple_format(self, code: str) -> str:
        """简单格式化（回退方案）"""
        # 基本的缩进和空格处理
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # 减少缩进（在}之前）
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
            
            # 添加缩进
            if stripped:
                formatted_lines.append('    ' * indent_level + stripped)
            else:
                formatted_lines.append('')
            
            # 增加缩进（在{之后）
            if stripped.endswith('{'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def check_style(self, code: str) -> Tuple[bool, List[str]]:
        """
        检查代码风格
        
        Args:
            code: 代码
            
        Returns:
            (是否符合, 问题列表)
        """
        result = self.format_code(code)
        
        if not result.success:
            return False, result.errors
        
        if result.changed:
            issues = ["代码风格不符合规范"]
            return False, issues
        
        return True, []
    
    def format_file(self, filepath: str, inplace: bool = False) -> FormatResult:
        """
        格式化文件
        
        Args:
            filepath: 文件路径
            inplace: 是否原地修改
            
        Returns:
            FormatResult: 格式化结果
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = self.format_code(code, Path(filepath).name)
            
            if inplace and result.success and result.changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result.formatted)
            
            return result
        
        except IOError as e:
            return FormatResult(
                success=False,
                original="",
                formatted="",
                changed=False,
                errors=[f"文件读取失败: {e}"],
                warnings=[]
            )
    
    def generate_config(self, config: Dict) -> str:
        """
        生成.clang-format配置文件
        
        Args:
            config: 配置字典
            
        Returns:
            YAML格式配置文件内容
        """
        # 基本配置
        default_config = {
            'BasedOnStyle': self.style,
            'Language': 'C',
            'IndentWidth': 4,
            'TabWidth': 4,
            'UseTab': 'Never',
            'ColumnLimit': 100,
            'AllowShortFunctionsOnASingleLine': 'Empty',
            'AllowShortIfStatementsOnASingleLine': 'false',
            'AllowShortLoopsOnASingleLine': 'false',
            'BreakBeforeBraces': 'Attach',
            'SpaceBeforeParens': 'ControlStatements',
            'AlignConsecutiveAssignments': 'true',
            'AlignConsecutiveDeclarations': 'true'
        }
        
        # 合并用户配置
        final_config = {**default_config, **config}
        
        # 转换为YAML格式
        lines = []
        for key, value in final_config.items():
            if isinstance(value, bool):
                lines.append(f"{key}: {'true' if value else 'false'}")
            elif isinstance(value, str):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {value}")
        
        return '\n'.join(lines)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'available': self.available,
            'success_rate': (
                self.stats['successful_formats'] /
                max(1, self.stats['total_formats'])
            )
        }


# 便捷函数
def format_code(code: str, style: str = "LLVM") -> str:
    """便捷函数：格式化代码"""
    formatter = ClangFormatIntegration(style=style)
    result = formatter.format_code(code)
    return result.formatted


if __name__ == "__main__":
    # 示例用法
    formatter = ClangFormatIntegration()
    
    # 格式化代码
    code = "int main(){int x=1;if(x>0){return x;}return 0;}"
    result = formatter.format_code(code)
    
    print("原始代码:")
    print(code)
    print("\n格式化后:")
    print(result.formatted)
    print(f"\n变化: {result.changed}")
    
    # 生成配置
    print("\n.clang-format配置:")
    print(formatter.generate_config({'IndentWidth': 2}))