#!/usr/bin/env python3
"""测试套件1：基础类型"""
import subprocess, sys, os

ZHPP = '/Users/yuan/Projects/zhc/src/zhpp.py'
TMPDIR = '/tmp/zhc_tests'
os.makedirs(TMPDIR, exist_ok=True)

def test(name, zhc_code, expected_in_output=None):
    path = f'{TMPDIR}/t_{name}.zhc'
    open(path, 'w').write(zhc_code)
    r = subprocess.run(['python3', ZHPP, path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: 预处理器失败 - {r.stderr}')
        return False
    c_path = path.replace('.zhc', '.c')
    c_code = open(c_path).read()
    if expected_in_output and expected_in_output not in c_code:
        print(f'  ❌ {name}: 缺少 {expected_in_output}')
        return False
    r2 = subprocess.run(['clang', c_path, '-o', f'{TMPDIR}/t_{name}', '-w'], capture_output=True, text=True)
    if r2.returncode != 0:
        print(f'  ❌ {name}: 编译失败 - {r2.stderr[:100]}')
        return False
    print(f'  ✅ {name}')
    return True

print('=== 测试套件1：基础类型 ===')
results = []

# T1: 基础整数型
results.append(test('int_basic', '''
整数型 主函数() {
    整数型 x = 42;
    返回 0;
}
''', 'int x = 42'))

# T2: 字符型
results.append(test('char_type', '''
字符型 主函数() {
    字符型 c = 65;
    返回 c - 65;
}
''', 'char c'))

# T3: 浮点型
results.append(test('float_type', '''
浮点型 主函数() {
    浮点型 f = 3.14f;
    返回 0;
}
''', 'float f'))

# T4: 双精度
results.append(test('double_type', '''
中文双精度浮点型 主函数() {
    中文双精度浮点型 d = 2.718;
    返回 0;
}
''', 'double d'))

# T5: 长整数
results.append(test('long_type', '''
长整数型 主函数() {
    长整数型 l = 99999L;
    返回 0;
}
''', 'long l'))

# T6: 逻辑型
results.append(test('bool_type', '''
中文逻辑型 主函数() {
    中文逻辑型 b = 1;
    返回 b ? 0 : 1;
}
''', '_Bool b'))

# T7: 无类型
results.append(test('void_type', '''
无类型 测试函数(无类型) {
    返回;
}
整数型 主函数() {
    返回 0;
}
''', 'void'))

# T8: const/static
results.append(test('const_static', '''
整数型 主函数() {
    常量 整数型 x = 10;
    静态 整数型 y = 20;
    返回 x + y - 30;
}
''', 'const int x'))

passed = sum(results)
total = len(results)
print(f'\n结果: {passed}/{total}')
sys.exit(0 if passed == total else 1)
