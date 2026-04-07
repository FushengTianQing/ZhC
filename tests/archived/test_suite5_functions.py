#!/usr/bin/env python3
"""测试套件5：函数语法（10个测试用例）"""

import os
import subprocess
import tempfile
import sys

def run_test(test_num, description, zhc_code, expected_output=None, should_compile=True):
    """运行单个测试"""
    print(f"测试 {test_num}: {description}")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.zhc', delete=False, encoding='utf-8') as f:
        f.write(zhc_code)
        zhc_file = f.name
    
    c_file = zhc_file.replace('.zhc', '.c')
    exe_file = zhc_file.replace('.zhc', '.exe')
    
    try:
        # 转换
        result = subprocess.run(
            ['python3', 'src/zhpp_v4_fixed.py', zhc_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/..'
        )
        
        if result.returncode != 0:
            print(f"  ❌ 转换失败: {result.stderr}")
            return False
        
        print(f"  ✓ 转换成功")
        
        # 读取转换结果
        with open(c_file, 'r', encoding='utf-8') as f:
            converted = f.read()
        
        # 检查转换结果
        if '函数 ' in converted and '->' in converted:
            print(f"  ❌ 函数声明未完全转换")
            print(f"    转换结果片段: {converted[:100]}...")
            return False
        
        # 编译
        compile_result = subprocess.run(
            ['clang', c_file, '-o', exe_file],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            if should_compile:
                print(f"  ❌ 编译失败: {compile_result.stderr}")
                return False
            else:
                print(f"  ✓ 编译失败（预期）")
                return True
        
        if not should_compile:
            print(f"  ❌ 预期编译失败但编译成功")
            return False
        
        print(f"  ✓ 编译成功")
        
        # 运行
        if expected_output is not None:
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True
            )
            
            if run_result.returncode != 0:
                print(f"  ❌ 运行失败: {run_result.stderr}")
                return False
            
            actual_output = run_result.stdout.strip()
            if actual_output != expected_output:
                print(f"  ❌ 输出不匹配")
                print(f"    预期: {expected_output}")
                print(f"    实际: {actual_output}")
                return False
            
            print(f"  ✓ 输出正确: {actual_output}")
        
        return True
        
    finally:
        # 清理临时文件
        for file in [zhc_file, c_file, exe_file]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass

def main():
    print("=" * 60)
    print("测试套件5：函数语法（10个测试用例）")
    print("=" * 60)
    
    tests = [
        # 测试1：简单函数
        (1, "简单加法函数",
         """#include <stdio.h>
函数 加(整数型 a, 整数型 b) -> 整数型 {
    返回 a + b;
}
整数型 主函数() {
    整数型 结果 = 加(5, 3);
    打印("%d", 结果);
    返回 0;
}""", "8"),
        
        # 测试2：无参数函数
        (2, "无参数问候函数",
         """#include <stdio.h>
函数 问候() -> 无类型 {
    打印("Hello");
}
整数型 主函数() {
    问候();
    返回 0;
}""", "Hello"),
        
        # 测试3：中文类型函数
        (3, "使用中文类型",
         """#include <stdio.h>
函数 中文加(中文整数型 a, 中文整数型 b) -> 中文整数型 {
    返回 a + b;
}
整数型 主函数() {
    打印("%d", 中文加(10, 20));
    返回 0;
}""", "30"),
        
        # 测试4：数组参数
        (4, "数组参数函数",
         """#include <stdio.h>
函数 求和数组(整数型 数组[], 整数型 长度) -> 整数型 {
    整数型 和 = 0;
    循环 (整数型 i = 0; i < 长度; i++) {
        和 += 数组[i];
    }
    返回 和;
}
整数型 主函数() {
    整数型 数组[3] = {1, 2, 3};
    打印("%d", 求和数组(数组, 3));
    返回 0;
}""", "6"),
        
        # 测试5：递归函数
        (5, "递归阶乘函数",
         """#include <stdio.h>
函数 阶乘(整数型 n) -> 整数型 {
    如果 (n <= 1) {
        返回 1;
    }
    返回 n * 阶乘(n - 1);
}
整数型 主函数() {
    打印("%d", 阶乘(5));
    返回 0;
}""", "120"),
        
        # 测试6：多个函数
        (6, "多个函数调用",
         """#include <stdio.h>
函数 平方(整数型 x) -> 整数型 {
    返回 x * x;
}
函数 立方(整数型 x) -> 整数型 {
    返回 x * 平方(x);
}
整数型 主函数() {
    打印("平方=%d 立方=%d", 平方(3), 立方(3));
    返回 0;
}""", "平方=9 立方=27"),
        
        # 测试7：结构体参数
        (7, "结构体参数函数",
         """#include <stdio.h>
结构体 点 {
    浮点型 x;
    浮点型 y;
};
函数 打印点(结构体 点 p) -> 无类型 {
    打印("%.1f,%.1f", p.x, p.y);
}
整数型 主函数() {
    结构体 点 点1 = {2.5, 3.5};
    打印点(点1);
    返回 0;
}""", "2.5,3.5"),
        
        # 测试8：void函数
        (8, "void返回类型",
         """#include <stdio.h>
函数 打印星号(整数型 数量) -> 无类型 {
    循环 (整数型 i = 0; i < 数量; i++) {
        打印("*");
    }
}
整数型 主函数() {
    打印星号(5);
    返回 0;
}""", "*****"),
        
        # 测试9：函数指针语法（应该失败）
        (9, "复杂函数语法（应编译失败）",
         """#include <stdio.h>
函数 复杂函数(整数型 (*回调)(整数型)) -> 整数型 {
    返回 回调(42);
}
整数型 主函数() {
    返回 0;
}""", None, False),  # 预期编译失败
        
        # 测试10：混合使用
        (10, "混合关键字和函数",
         """#include <stdio.h>
函数 最大值(整数型 a, 整数型 b) -> 整数型 {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}
整数型 主函数() {
    整数型 x = 10;
    整数型 y = 20;
    整数型 最大 = 最大值(x, y);
    
    循环 (整数型 i = 0; i < 最大; i++) {
        如果 (i % 2 == 0) {
            继续;
        }
        打印("%d ", i);
    }
    返回 0;
}""", "1 3 5 7 9 11 13 15 17 19 "),
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if len(test) == 4:
            test_num, desc, code, expected = test
            should_compile = True
        else:
            test_num, desc, code, expected, should_compile = test
        
        if run_test(test_num, desc, code, expected, should_compile):
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"通过率: {passed/len(tests)*100:.1f}%")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())