#!/usr/bin/env python3
"""测试套件3：函数、结构体、指针"""
import subprocess, sys, os

ZHPP = '/Users/yuan/Projects/zhc/src/zhpp.py'
TMPDIR = '/tmp/zhc_tests'
os.makedirs(TMPDIR, exist_ok=True)

def test(name, zhc_code, expect_exit=0):
    path = f'{TMPDIR}/t3_{name}.zhc'
    open(path, 'w').write(zhc_code)
    subprocess.run(['python3', ZHPP, path], capture_output=True)
    c_path = path.replace('.zhc', '.c')
    r = subprocess.run(['clang', c_path, '-o', f'{TMPDIR}/t3_{name}', '-w'], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: 编译失败 - {r.stderr[:100]}')
        return False
    r2 = subprocess.run([f'{TMPDIR}/t3_{name}'], capture_output=True, text=True)
    if r2.returncode != expect_exit:
        print(f'  ❌ {name}: 期望={expect_exit} 实际={r2.returncode}')
        return False
    print(f'  ✅ {name}')
    return True

print('=== 测试套件3：函数、结构体、指针 ===')
results = []

results.append(test('func_call', '''
整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}
整数型 主函数() {
    如果 (加法(3, 4) == 7) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('func_recursive', '''
整数型 阶乘(整数型 n) {
    如果 (n <= 1) { 返回 1; }
    返回 n * 阶乘(n - 1);
}
整数型 主函数() {
    如果 (阶乘(5) == 120) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('struct_basic', '''
结构体 点 {
    整数型 x;
    整数型 y;
};
整数型 主函数() {
    结构体 点 p;
    p.x = 3;
    p.y = 4;
    如果 (p.x + p.y == 7) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('typedef_alias', '''
别名 整数型 长整数;
长整数 主函数() {
    长整数 x = 100;
    如果 (x == 100) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('enum_type', '''
枚举 颜色 { 红, 绿, 蓝 };
整数型 主函数() {
    枚举 颜色 c = 绿;
    如果 (c == 1) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('pointer_basic', '''
整数型 主函数() {
    整数型 x = 42;
    整数型 *p = &x;
    如果 (*p == 42) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('malloc_free', '''
#include <stdlib.h>
整数型 主函数() {
    整数型 *p = (整数型*)申请(sizeof(整数型));
    *p = 99;
    如果 (*p == 99) { 释放(p); 返回 0; }
    释放(p);
    返回 1;
}
''', 0))

results.append(test('printf_output', '''
#include <stdio.h>
整数型 主函数() {
    打印("hello");
    返回 0;
}
''', 0))

passed = sum(results)
total = len(results)
print(f'\n结果: {passed}/{total}')
sys.exit(0 if passed == total else 1)
