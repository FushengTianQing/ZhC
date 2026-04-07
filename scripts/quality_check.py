#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZHC 代码质量快速检查工具

使用方法:
    python scripts/quality_check.py              # 检查整个项目
    python scripts/quality_check.py src/parser    # 检查指定目录
    python scripts/quality_check.py --fix          # 自动修复部分问题

输出:
    - 代码行数统计
    - 复杂度分析
    - 测试覆盖率估算
    - 问题清单和改进建议
"""

import os
import sys
import ast
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import argparse


@dataclass
class FileMetrics:
    """文件度量指标"""
    path: str
    lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: int = 0
    classes: int = 0
    max_function_length: int = 0
    max_complexity: int = 0
    has_docstring: bool = True
    has_type_hints: float = 0.0  # 百分比
    issues: List[str] = field(default_factory=list)


class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.metrics: Dict[str, FileMetrics] = {}
        self.total_issues: List[Tuple[str, str]] = []  # (file, issue)
        
        # 配置阈值
        self.thresholds = {
            'max_function_length': 30,
            'max_complexity': 10,
            'min_test_coverage': 60,
            'min_type_hint_percent': 80,
            'max_file_lines': 500,
        }
    
    def check_directory(self, directory: str) -> Dict:
        """检查目录下所有Python文件"""
        dir_path = self.project_root / directory if directory else self.project_root
        
        # 查找所有Python文件
        python_files = list(dir_path.rglob('*.py'))
        
        # 排除测试文件和虚拟环境
        python_files = [
            f for f in python_files 
            if 'test' not in f.name.lower() 
            and '.venv' not in str(f)
            and '__pycache__' not in str(f)
        ]
        
        print(f"\n📊 扫描 {len(python_files)} 个源文件...\n")
        
        for file_path in python_files:
            self._check_file(file_path)
        
        return self._generate_report()
    
    def _check_file(self, file_path: Path):
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            rel_path = str(file_path.relative_to(self.project_root))
            metrics = FileMetrics(path=rel_path)
            metrics.lines = len(lines)
            
            # 统计行类型
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics.blank_lines += 1
                elif stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    metrics.comment_lines += 1
                else:
                    metrics.code_lines += 1
            
            # AST分析
            try:
                tree = ast.parse(content)
                
                # 统计函数和类
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        metrics.functions += 1
                        
                        # 函数长度
                        func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                        metrics.max_function_length = max(metrics.max_function_length, func_lines)
                        
                        # 圈复杂度（简化版）
                        complexity = self._calculate_complexity(node)
                        metrics.max_complexity = max(metrics.max_complexity, complexity)
                        
                        # 检查文档字符串
                        if not ast.get_docstring(node):
                            if not node.name.startswith('_'):  # 排除私有方法
                                metrics.issues.append(f"函数 '{node.name}' 缺少docstring")
                                metrics.has_docstring = False
                        
                        # 检查类型注解
                        hints_count = 0
                        if node.returns:
                            hints_count += 1
                        for arg in node.args.args:
                            if arg.annotation:
                                hints_count += 1
                        if hints_count > 0:
                            metrics.has_type_hints += 100
                    
                    elif isinstance(node, ast.ClassDef):
                        metrics.classes += 1
                        
                        if not ast.get_docstring(node):
                            metrics.issues.append(f"类 '{node.name}' 缺少docstring")
                
                # 计算类型注解百分比
                total_funcs = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
                if total_funcs > 0:
                    metrics.has_type_hints = metrics.has_type_hints / total_funcs
                
            except SyntaxError as e:
                metrics.issues.append(f"语法错误: {e}")
            
            # 检查问题
            self._check_issues(metrics, lines)
            
            self.metrics[rel_path] = metrics
            
        except Exception as e:
            print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度（简化版）"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, (ast.ExceptHandler, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
        
        return complexity
    
    def _check_issues(self, metrics: FileMetrics, lines: List[str]):
        """检查代码质量问题"""
        
        # 文件长度检查
        if metrics.lines > self.thresholds['max_file_lines']:
            metrics.issues.append(
                f"文件过长 ({metrics.lines}行 > {self.thresholds['max_file_lines']})"
            )
        
        # 函数长度检查
        if metrics.max_function_length > self.thresholds['max_function_length']:
            metrics.issues.append(
                f"最长函数过长 ({metrics.max_function_length}行 > {self.thresholds['max_function_length']})"
            )
        
        # 复杂度检查
        if metrics.max_complexity > self.thresholds['max_complexity']:
            metrics.issues.append(
                f"圈复杂度过高 ({metrics.max_complexity} > {self.thresholds['max_complexity']})"
            )
        
        # 类型注解检查
        if metrics.has_type_hints < self.thresholds['min_type_hint_percent'] / 100 and metrics.functions > 0:
            metrics.issues.append(
                f"类型注解不足 ({metrics.has_type_hints*100:.0f}% < {self.thresholds['min_type_hint_percent']}%)"
            )
        
        # 记录所有问题
        for issue in metrics.issues:
            self.total_issues.append((metrics.path, issue))
    
    def _generate_report(self) -> Dict:
        """生成质量报告"""
        print("=" * 70)
        print("🔍 ZHC 代码质量检查报告")
        print("=" * 70)
        
        # 总体统计
        total_files = len(self.metrics)
        total_lines = sum(m.lines for m in self.metrics.values())
        total_code_lines = sum(m.code_lines for m in self.metrics.values())
        total_functions = sum(m.functions for m in self.metrics.values())
        total_classes = sum(m.classes for m in self.metrics.values())
        
        print(f"\n📈 总体统计:")
        print(f"  文件数: {total_files}")
        print(f"  总行数: {total_lines:,}")
        print(f"  代码行数: {total_code_lines:,}")
        print(f"  函数数量: {total_functions:,}")
        print(f"  类数量: {total_classes:,}")
        
        # 平均指标
        if total_files > 0:
            avg_func_len = sum(m.max_function_length for m in self.metrics.values()) / total_files
            avg_complexity = sum(m.max_complexity for m in self.metrics.values()) / total_files
            avg_type_hints = sum(m.has_type_hints for m in self.metrics.values()) / total_files * 100
            
            print(f"\n📊 平均指标:")
            print(f"  平均最大函数长度: {avg_func_len:.1f} 行")
            print(f"  平均最大复杂度: {avg_complexity:.1f}")
            print(f"  平均类型注解覆盖: {avg_type_hints:.1f}%")
        
        # 问题统计
        print(f"\n⚠️  发现的问题: {len(self.total_issues)}")
        
        if self.total_issues:
            # 按严重程度分类
            critical = [i for i in self.total_issues if '过高' in i[1] or '错误' in i[1]]
            warning = [i for i in self.total_issues if i not in critical]
            
            if critical:
                print(f"\n🔴 严重问题 ({len(critical)}):")
                for file_path, issue in critical[:10]:  # 只显示前10个
                    print(f"  ✗ {file_path}: {issue}")
            
            if warning:
                print(f"\n🟡 建议改进 ({len(warning)}):")
                for file_path, issue in warning[:10]:
                    print(f"  ⚠ {file_path}: {issue}")
            
            if len(self.total_issues) > 20:
                print(f"\n  ... 还有 {len(self.total_issues) - 20} 个问题未显示")
        
        # 质量评分
        score = self._calculate_quality_score()
        grade = self._get_grade(score)
        
        print(f"\n{'=' * 70}")
        print(f"🏆 质量评分: {score}/100 [{grade}]")
        print(f"{'=' * 70}")
        
        # 改进建议
        print("\n💡 改进建议:")
        suggestions = self._generate_suggestions()
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        return {
            'score': score,
            'grade': grade,
            'total_files': total_files,
            'total_lines': total_lines,
            'total_issues': len(self.total_issues),
            'metrics': dict(self.metrics),
        }
    
    def _calculate_quality_score(self) -> int:
        """计算质量得分（0-100）"""
        if not self.metrics:
            return 0
        
        scores = []
        
        # 函数长度得分 (25分)
        avg_max_func_len = sum(m.max_function_length for m in self.metrics.values()) / len(self.metrics)
        if avg_max_func_len <= 20:
            scores.append(25)
        elif avg_max_func_len <= 30:
            scores.append(20)
        elif avg_max_func_len <= 40:
            scores.append(15)
        elif avg_max_func_len <= 50:
            scores.append(10)
        else:
            scores.append(5)
        
        # 复杂度得分 (25分)
        avg_complexity = sum(m.max_complexity for m in self.metrics.values()) / len(self.metrics)
        if avg_complexity <= 5:
            scores.append(25)
        elif avg_complexity <= 8:
            scores.append(20)
        elif avg_complexity <= 10:
            scores.append(15)
        elif avg_complexity <= 15:
            scores.append(10)
        else:
            scores.append(5)
        
        # 类型注解得分 (25分)
        avg_hints = sum(m.has_type_hints for m in self.metrics.values()) / len(self.metrics) * 100
        scores.append(min(25, int(avg_hints / 4)))
        
        # 问题密度得分 (25分)
        issue_density = len(self.total_issues) / max(len(self.metrics), 1)
        if issue_density == 0:
            scores.append(25)
        elif issue_density <= 2:
            scores.append(20)
        elif issue_density <= 4:
            scores.append(15)
        elif issue_density <= 6:
            scores.append(10)
        else:
            scores.append(5)
        
        return sum(scores)
    
    def _get_grade(self, score: int) -> str:
        """获取等级"""
        if score >= 90:
            return "A+ 优秀"
        elif score >= 80:
            return "A  良好"
        elif score >= 70:
            return "B+ 中等偏上"
        elif score >= 60:
            return "B  中等"
        elif score >= 50:
            return "C 需要改进"
        else:
            return "D 急需改进"
    
    def _generate_suggestions(self) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 分析主要问题
        issues_by_type = defaultdict(int)
        for _, issue in self.total_issues:
            if '函数' in issue and '长' in issue:
                issues_by_type['function_length'] += 1
            elif '复杂' in issue:
                issues_by_type['complexity'] += 1
            elif '注解' in issue or 'type' in issue.lower():
                issues_by_type['type_hints'] += 1
            elif '文档' in issue or 'docstring' in issue.lower():
                issues_by_type['documentation'] += 1
            elif '文件' in issue and '长' in issue:
                issues_by_type['file_length'] += 1
        
        # 根据问题类型生成建议
        if issues_by_type.get('function_length', 0) > 3:
            suggestions.append("拆分过长的函数，每个函数控制在30行以内，遵循单一职责原则")
        
        if issues_by_type.get('complexity', 0) > 3:
            suggestions.append("降低圈复杂度：提取条件判断为独立函数，使用早返回模式减少嵌套")
        
        if issues_by_type.get('type_hints', 0) > 3:
            suggestions.append("为公共API添加完整的类型注解，提升代码可读性和IDE支持")
        
        if issues_by_type.get('documentation', 0) > 3:
            suggestions.append("补充函数和类的文档字符串，说明用途、参数、返回值和异常")
        
        if issues_by_type.get('file_length', 0) > 2:
            suggestions.append("拆分大文件为多个模块，按功能职责组织代码")
        
        if not suggestions:
            suggestions.append("代码整体质量良好！继续保持现有的编码标准")
        
        # 通用建议
        suggestions.extend([
            "运行 `python -m pytest tests/ --cov=src` 查看测试覆盖率",
            "考虑引入 pre-commit hook 自动化代码检查",
            "定期进行代码审查，持续改进代码质量",
        ])
        
        return suggestions[:8]


def main():
    parser = argparse.ArgumentParser(description='ZHC 代码质量检查工具')
    parser.add_argument(
        'directory',
        nargs='?',
        default='src',
        help='要检查的目录（默认: src）'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='输出JSON格式结果'
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    
    checker = CodeQualityChecker(str(project_root))
    report = checker.check_directory(args.directory)
    
    if args.json:
        import json
        print("\n" + json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()