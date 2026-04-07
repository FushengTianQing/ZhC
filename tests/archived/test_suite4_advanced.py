#!/usr/bin/env python3
"""测试套件4：预处理指令、数组、前缀兼容"""
import subprocess, sys, os

ZHPP = '/Users/yuan/Projects/zhc/src/zhpp.py'
TMPDIR = '/tmp/zhc_tests'
os.makedirs(TMPDIR, exist_ok=True)

def test(name, zhc_code, expect_exit=0):
    path = f'{TMPDIR}/t4_{name}.zhc'
    open(path, 'w').write(zhc_code)
    subprocess.run(['python3', ZHPP, path], capture_output=True)
    c_path = path.replace('.zhc', '.c')
    r = subprocess.run(['clang', c_path, '-o', f'{TMPDIR}/t4_{name}', '-w'], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: 编译失败 - {r.stderr[:100]}')
        return False
    r2 = subprocess.run([f'{TMPDIR}/t4_{name}'], capture_output=True, text=True)
    if r2.returncode != expect_exit:
        print(f'  ❌ {name}: 期望={expect_exit} 实际={r2.returncode}')
        return False
    print(f'  ✅ {name}')
    return True

print('=== 测试套件4：预处理、数组、前缀 ===')
results = []

results.append(test('array_basic', '''
整数型 主函数() {
    整数型 arr[5] = {10, 20, 30, 40, 50};
    如果 (arr[2] == 30) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('array_loop', '''
整数型 主函数() {
    整数型 arr[5];
    整数型 i;
    循环 (i = 0; i < 5; i++) {
        arr[i] = i * 10;
    }
    如果 (arr[3] == 30) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('string_array', '''
#include <string.h>
整数型 主函数() {
    字符型 s[] = "hello";
    如果 (s[0] == 104) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('define_macro', '''
#define MAX 100
整数型 主函数() {
    如果 (MAX == 100) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('include_header', '''
#include <stdio.h>
整数型 主函数() {
    打印("test");
    返回 0;
}
''', 0))

results.append(test('multi_line', '''
整数型 主函数() {
    整数型 a = 1;
    整数型 b = 2;
    整数型 c = 3;
    整数型 d = a + b + c;
    如果 (d == 6) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('mixed_identifiers', '''
整数型 计算(整数型 a, 整数型 b) {
    返回 a + b;
}
整数型 主函数() {
    整数型 result = 计算(10, 20);
    如果 (result == 30) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('unsigned_type', '''
无符号 整数型 主函数() {
    无符号 整数型 x = 4294967295U;
    返回 0;
}
''', 0))

passed = sum(results)
total = len(results)
print(f'\n结果: {passed}/{total}')
sys.exit(0 if passed == total else 1)
