#!/usr/bin/env python3
"""
类型注解覆盖率检查工具

扫描 Python 文件，统计类型注解覆盖率。
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def check_type_coverage(file_path: Path) -> Dict[str, any]:
    """
    检查单个文件的类型注解覆盖率
    
    Returns:
        包含统计信息的字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return {'error': 'SyntaxError'}
    
    stats = {
        'functions': 0,
        'typed_functions': 0,
        'methods': 0,
        'typed_methods': 0,
        'classes': 0,
        'total_params': 0,
        'typed_params': 0,
        'returns': 0,
        'typed_returns': 0,
    }
    
    for node in ast.walk(tree):
        # 函数和方法
        if isinstance(node, ast.FunctionDef):
            is_method = False
            
            # 检查是否是方法（在类中）
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef) and node in parent.body:
                    is_method = True
                    break
            
            if is_method:
                stats['methods'] += 1
            else:
                stats['functions'] += 1
            
            # 检查参数类型注解
            params = [arg for arg in node.args.args if arg.arg != 'self']
            stats['total_params'] += len(params)
            typed_params = sum(1 for arg in params if arg.annotation is not None)
            stats['typed_params'] += typed_params
            
            # 检查返回值类型注解
            stats['returns'] += 1
            if node.returns is not None:
                stats['typed_returns'] += 1
            
            # 判断函数是否有完整类型注解
            has_param_types = typed_params == len(params)
            has_return_type = node.returns is not None
            
            if has_param_types and has_return_type:
                if is_method:
                    stats['typed_methods'] += 1
                else:
                    stats['typed_functions'] += 1
        
        # 类
        elif isinstance(node, ast.ClassDef):
            stats['classes'] += 1
    
    # 计算覆盖率
    stats['function_coverage'] = (
        stats['typed_functions'] / stats['functions'] * 100
        if stats['functions'] > 0 else 0
    )
    
    stats['method_coverage'] = (
        stats['typed_methods'] / stats['methods'] * 100
        if stats['methods'] > 0 else 0
    )
    
    stats['param_coverage'] = (
        stats['typed_params'] / stats['total_params'] * 100
        if stats['total_params'] > 0 else 0
    )
    
    stats['return_coverage'] = (
        stats['typed_returns'] / stats['returns'] * 100
        if stats['returns'] > 0 else 0
    )
    
    stats['overall_coverage'] = (
        (stats['typed_functions'] + stats['typed_methods']) /
        (stats['functions'] + stats['methods']) * 100
        if (stats['functions'] + stats['methods']) > 0 else 0
    )
    
    return stats


def scan_directory(directory: Path) -> Tuple[Dict, List[Path]]:
    """
    扫描目录下所有 Python 文件
    
    Returns:
        (总统计, 文件列表)
    """
    total_stats = {
        'files': 0,
        'functions': 0,
        'typed_functions': 0,
        'methods': 0,
        'typed_methods': 0,
        'classes': 0,
        'total_params': 0,
        'typed_params': 0,
        'returns': 0,
        'typed_returns': 0,
    }
    
    python_files = list(directory.rglob('*.py'))
    
    for file_path in python_files:
        # 跳过测试文件和特殊目录
        if 'test' in str(file_path).lower() or 'archived' in str(file_path):
            continue
        
        stats = check_type_coverage(file_path)
        
        if 'error' not in stats:
            total_stats['files'] += 1
            for key in ['functions', 'typed_functions', 'methods', 'typed_methods',
                       'classes', 'total_params', 'typed_params', 'returns', 'typed_returns']:
                total_stats[key] += stats[key]
    
    # 计算总覆盖率
    total_stats['function_coverage'] = (
        total_stats['typed_functions'] / total_stats['functions'] * 100
        if total_stats['functions'] > 0 else 0
    )
    
    total_stats['method_coverage'] = (
        total_stats['typed_methods'] / total_stats['methods'] * 100
        if total_stats['methods'] > 0 else 0
    )
    
    total_stats['param_coverage'] = (
        total_stats['typed_params'] / total_stats['total_params'] * 100
        if total_stats['total_params'] > 0 else 0
    )
    
    total_stats['return_coverage'] = (
        total_stats['typed_returns'] / total_stats['returns'] * 100
        if total_stats['returns'] > 0 else 0
    )
    
    total_stats['overall_coverage'] = (
        (total_stats['typed_functions'] + total_stats['typed_methods']) /
        (total_stats['functions'] + total_stats['methods']) * 100
        if (total_stats['functions'] + total_stats['methods']) > 0 else 0
    )
    
    return total_stats, python_files


def main():
    """主函数"""
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path('src')
    
    if not directory.exists():
        print(f"❌ 目录不存在: {directory}")
        sys.exit(1)
    
    print(f"📊 扫描目录: {directory}")
    print("=" * 60)
    
    stats, files = scan_directory(directory)
    
    print(f"\n📁 文件统计:")
    print(f"  扫描文件: {stats['files']} 个")
    print(f"  类数量: {stats['classes']} 个")
    print(f"  函数数量: {stats['functions']} 个")
    print(f"  方法数量: {stats['methods']} 个")
    
    print(f"\n📝 类型注解统计:")
    print(f"  函数覆盖率: {stats['function_coverage']:.1f}% ({stats['typed_functions']}/{stats['functions']})")
    print(f"  方法覆盖率: {stats['method_coverage']:.1f}% ({stats['typed_methods']}/{stats['methods']})")
    print(f"  参数覆盖率: {stats['param_coverage']:.1f}% ({stats['typed_params']}/{stats['total_params']})")
    print(f"  返回值覆盖率: {stats['return_coverage']:.1f}% ({stats['typed_returns']}/{stats['returns']})")
    
    print(f"\n🎯 总体覆盖率: {stats['overall_coverage']:.1f}%")
    print("=" * 60)
    
    # 评分
    score = stats['overall_coverage']
    if score >= 90:
        grade = "A+ 优秀"
    elif score >= 80:
        grade = "A 良好"
    elif score >= 70:
        grade = "B 中等"
    elif score >= 60:
        grade = "C 及格"
    else:
        grade = "D 不及格"
    
    print(f"📈 类型注解评分: {score:.0f}/100 [{grade}]")
    
    return 0 if score >= 60 else 1


if __name__ == '__main__':
    sys.exit(main())
