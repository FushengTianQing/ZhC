#!/usr/bin/env python3
"""
简单的模块系统测试

注意: 此测试依赖 conftest.py 设置的路径
"""

import sys
import os
from pathlib import Path

# 添加项目路径（依赖conftest.py统一处理）
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

print("=== 简单模块系统测试 ===")

# 测试1: 导入模块解析器
print("\n测试1: 导入模块解析器...")
try:
    # 由于文件名中有点，我们需要特殊处理
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(
        "zhpp_v4_module",
        os.path.join(os.path.dirname(__file__), '../../src/phase3/zhpp_v4_module.py')
    )
    zhpp_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(zhpp_module)
    
    from zhpp_v4_module import ModuleParser
    
    print("✓ 模块解析器导入成功")
    
    # 测试解析功能
    print("\n测试2: 解析简单模块...")
    parser = ModuleParser()
    
    test_code = """
模块 数学库 {
    公开:
        函数 加法(整数型 a, 整数型 b) -> 整数型 {
            返回 a + b;
        }
}
"""
    lines = test_code.strip().split('\n')
    for i, line in enumerate(lines, 1):
        parser.parse_line(line.strip(), i)
        
    print(f"✓ 解析成功! 发现模块数: {len(parser.modules)}")
    if parser.modules:
        print(f"  模块名: {list(parser.modules.keys())[0]}")
        print(f"  公开符号: {list(parser.modules['数学库'].public_symbols)}")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")

# 测试2: 导入作用域管理器
print("\n测试3: 导入作用域管理器...")
try:
    spec = importlib.util.spec_from_file_location(
        "scope_manager",
        os.path.join(os.path.dirname(__file__), '../../src/phase3/scope_manager.py')
    )
    scope_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scope_module)
    
    from scope_manager import ScopeManager, Visibility, ScopeType
    
    print("✓ 作用域管理器导入成功")
    
    # 测试作用域管理功能
    print("\n测试4: 作用域管理测试...")
    manager = ScopeManager()
    
    manager.enter_scope("数学库", ScopeType.MODULE)
    manager.add_symbol("圆周率", Visibility.PUBLIC, 10)
    manager.add_symbol("内部变量", Visibility.PRIVATE, 12)
    manager.exit_scope()
    
    stats = manager.get_statistics()
    print(f"✓ 作用域测试成功!")
    print(f"  模块数: {stats['modules']}")
    print(f"  公开符号: {stats['public_symbols']}")
    print(f"  私有符号: {stats['private_symbols']}")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")

print("\n=== 测试完成 ===")