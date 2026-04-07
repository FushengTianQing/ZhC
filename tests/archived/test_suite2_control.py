#!/usr/bin/env python3
"""测试套件2：流程控制"""
import subprocess, sys, os

ZHPP = '/Users/yuan/Projects/zhc/src/zhpp.py'
TMPDIR = '/tmp/zhc_tests'
os.makedirs(TMPDIR, exist_ok=True)

def test(name, zhc_code, expect_exit=0):
    path = f'{TMPDIR}/t_{name}.zhc'
    open(path, 'w').write(zhc_code)
    subprocess.run(['python3', ZHPP, path], capture_output=True)
    c_path = path.replace('.zhc', '.c')
    r = subprocess.run(['clang', c_path, '-o', f'{TMPDIR}/t_{name}', '-w'], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: 编译失败')
        return False
    r2 = subprocess.run([f'{TMPDIR}/t_{name}'], capture_output=True, text=True)
    actual = r2.returncode
    if actual != expect_exit:
        print(f'  ❌ {name}: 期望退出码={expect_exit}, 实际={actual}')
        return False
    print(f'  ✅ {name}')
    return True

print('=== 测试套件2：流程控制 ===')
results = []

results.append(test('if_else', '''
整数型 主函数() {
    整数型 x = 5;
    如果 (x > 3) {
        返回 1;
    } 否则 {
        返回 0;
    }
}
''', 1))

results.append(test('if_false', '''
整数型 主函数() {
    整数型 x = 1;
    如果 (x > 3) {
        返回 1;
    } 否则 {
        返回 2;
    }
}
''', 2))

results.append(test('for_loop', '''
整数型 主函数() {
    整数型 sum = 0;
    循环 (整数型 i = 0; i < 5; i++) {
        sum += i;
    }
    如果 (sum == 10) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('while_loop', '''
整数型 主函数() {
    整数型 i = 0;
    判断 (i < 5) {
        i++;
    }
    如果 (i == 5) { 返回 0; }
    返回 1;
}
''', 0))

results.append(test('switch_case', '''
整数型 主函数() {
    整数型 x = 2;
    选择 (x) {
        分支 1: 返回 10;
        分支 2: 返回 20;
        默认: 返回 0;
    }
}
''', 20))

results.append(test('break_continue', '''
整数型 主函数() {
    整数型 sum = 0;
    循环 (整数型 i = 0; i < 10; i++) {
        如果 (i == 5) { 跳出; }
        如果 (i == 3) { 继续; }
        sum += i;
    }
    如果 (sum == 7) { 返回 0; }
    返回 1;
}
''', 0))

passed = sum(results)
total = len(results)
print(f'\n结果: {passed}/{total}')
sys.exit(0 if passed == total else 1)
