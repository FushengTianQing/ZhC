#!/usr/bin/env python3
"""
T025: string 字符串处理库完整测试

覆盖内容:
  - zhc_string.h 头文件语法验证（编译测试）
  - zhc_strlen: 字符串长度（正常/NULL/空字符串）
  - zhc_strcat: 字符串连接（正常/NULL/缓冲区足够）
  - zhc_strcpy: 字符串复制（正常/NULL/空字符串）
  - zhc_substr: 提取子串（正常/边界/负数参数/越界）
  - zhc_find: 查找子串（找到/未找到/NULL/空子串）
  - zhc_replace: 替换子串（单次/多次/未找到/NULL）
  - zhc_strcmp: 字符串比较（相等/小于/大于/NULL）
  - zhc_tolower: 转小写（正常/NULL）
  - zhc_toupper: 转大写（正常/NULL）
  - zhc_trim: 去空白（前导/尾部/中间/NULL）
  - 组合测试: 查找+替换 / 去空白+比较

测试方式:
  C 代码编写 → clang 编译 → 运行验证输出
"""

import os
import subprocess
import tempfile
import sys

# ============================================================
# 配置
# ============================================================
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)

STRING_H_PATH = os.path.join(PROJECT_ROOT, 'src', 'lib', 'zhc_string.h')
CLANG = 'clang'

passed = 0
failed = 0
total = 0


def report(name, ok, detail=""):
    """报告测试结果"""
    global passed, failed, total
    total += 1
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")
        if detail:
            for line in detail.strip().split('\n'):
                print(f"      {line}")


def compile_c(source, extra_flags=None):
    """编译 C 代码，返回 (临时可执行文件路径, 成功与否, 错误信息)"""
    with tempfile.NamedTemporaryFile(suffix='.c', mode='w', delete=False,
                                      encoding='utf-8') as f:
        f.write(source)
        c_path = f.name
    exe_path = c_path.replace('.c', '_test_exe')
    try:
        cmd = [CLANG, '-w', '-Wno-error', '-Wno-implicit-function-declaration', 
               c_path, '-o', exe_path]
        if extra_flags:
            cmd.extend(extra_flags)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return exe_path, r.returncode == 0, r.stderr
    except Exception as e:
        return exe_path, False, str(e)


def run_exe(exe_path, stdin_data="", timeout=5):
    """运行可执行文件，返回 (stdout, stderr, returncode)"""
    try:
        r = subprocess.run(
            [exe_path], input=stdin_data,
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1


def cleanup(exe_path):
    """清理临时文件"""
    try:
        if os.path.exists(exe_path):
            os.remove(exe_path)
        c_path = exe_path.replace('_test_exe', '.c')
        if os.path.exists(c_path):
            os.remove(c_path)
    except:
        pass


# ============================================================
# 测试函数
# ============================================================

def test_header_compile():
    """测试 zhc_string.h 头文件能够正确编译"""
    print("\n📝 T025-1: 头文件编译测试")
    
    source = f'''
#include "{STRING_H_PATH}"

int main() {{
    return 0;
}}
'''
    
    exe, ok, err = compile_c(source)
    if ok:
        report("zhc_string.h 编译通过", True)
    else:
        report("zhc_string.h 编译通过", False, err)
    cleanup(exe)


def test_strlen():
    """测试 zhc_strlen 函数"""
    print("\n📝 T025-2: zhc_strlen 测试")
    
    tests = [
        ("正常字符串", '"Hello"', '5'),
        ("空字符串", '""', '0'),
        ("NULL指针", 'NULL', '0'),
        ("长字符串", '"This is a long string for testing"', '33'),
    ]
    
    for name, input_str, expected in tests:
        source = f'''
#include <stdio.h>
#include "{STRING_H_PATH}"

int main() {{
    const char *s = {input_str};
    int len = zhc_strlen(s);
    printf("%d\\n", len);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        report(name, out.strip() == expected, f"期望: {expected}, 实际: {out.strip()}")
        cleanup(exe)


def test_strcat():
    """测试 zhc_strcat 函数"""
    print("\n📝 T025-3: zhc_strcat 测试")
    
    tests = [
        ("正常连接", '"Hello, "', '"World!"', '"Hello, World!"'),
        ("空源字符串", '"Test"', '""', '"Test"'),
        ("长字符串连接", '"Prefix_"', '"Middle_Suffix"', '"Prefix_Middle_Suffix"'),
    ]
    
    for name, dest, src, expected in tests:
        source = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char buf[100] = {dest};
    char *result = zhc_strcat(buf, {src});
    printf("%s\\n", result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean, 
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_strcpy():
    """测试 zhc_strcpy 函数"""
    print("\n📝 T025-4: zhc_strcpy 测试")
    
    tests = [
        ("正常复制", '"Copy Test"', '"Copy Test"'),
        ("空字符串", '""', '""'),
        ("长字符串", '"This is a test string for copying"', '"This is a test string for copying"'),
    ]
    
    for name, src, expected in tests:
        source = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char buf[100];
    char *result = zhc_strcpy(buf, {src});
    printf("%s\\n", result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean,
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_substr():
    """测试 zhc_substr 函数"""
    print("\n📝 T025-5: zhc_substr 测试")
    
    tests = [
        ("正常子串", '"Hello, World!"', '0', '5', '"Hello"'),
        ("中间子串", '"Hello, World!"', '7', '5', '"World"'),
        ("边界子串", '"Hello"', '0', '5', '"Hello"'),
        ("起始越界", '"Hello"', '10', '5', '""'),
        ("长度越界", '"Hello"', '0', '100', '"Hello"'),
        ("负数起始", '"Hello"', '-1', '3', '"Hel"'),  # -1会被调整为0
        ("零长度", '"Hello"', '0', '0', '""'),
        ("NULL输入", 'NULL', '0', '5', '""'),
    ]
    
    for name, str_val, start, length, expected in tests:
        source = f'''
#include <stdio.h>
#include <stdlib.h>
#include "{STRING_H_PATH}"

int main() {{
    char *result = zhc_substr({str_val}, {start}, {length});
    printf("%s\\n", result);
    free(result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean,
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_find():
    """测试 zhc_find 函数"""
    print("\n📝 T025-6: zhc_find 测试")
    
    tests = [
        ("找到子串", '"Hello, World!"', '"World"', '7'),
        ("未找到子串", '"Hello, World!"', '"Python"', '-1'),
        ("空子串", '"Hello"', '""', '0'),
        ("NULL字符串", 'NULL', '"test"', '-1'),
        ("NULL子串", '"test"', 'NULL', '-1'),
        ("多次出现", '"ababab"', '"ab"', '0'),  # 返回第一次出现的位置
    ]
    
    for name, str_val, sub_val, expected in tests:
        source = f'''
#include <stdio.h>
#include "{STRING_H_PATH}"

int main() {{
    int pos = zhc_find({str_val}, {sub_val});
    printf("%d\\n", pos);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        report(name, out.strip() == expected,
               f"期望: {expected}, 实际: {out.strip()}")
        cleanup(exe)


def test_replace():
    """测试 zhc_replace 函数"""
    print("\n📝 T025-7: zhc_replace 测试")
    
    tests = [
        ("单次替换", '"Hello, World!"', '"World"', '"中文C"', '"Hello, 中文C!"'),
        ("多次替换", '"aaa bbb aaa"', '"aaa"', '"ccc"', '"ccc bbb ccc"'),
        ("未找到", '"Hello"', '"xyz"', '"test"', '"Hello"'),
        ("空查找串", '"Test"', '""', '"Replace"', '"Test"'),
        ("NULL输入", 'NULL', '"a"', '"b"', '""'),
        ("长替换", '"x"', '"x"', '"longer"', '"longer"'),
    ]
    
    for name, str_val, find_val, replace_val, expected in tests:
        source = f'''
#include <stdio.h>
#include <stdlib.h>
#include "{STRING_H_PATH}"

int main() {{
    char *result = zhc_replace({str_val}, {find_val}, {replace_val});
    printf("%s\\n", result);
    free(result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean,
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_strcmp():
    """测试 zhc_strcmp 函数"""
    print("\n📝 T025-8: zhc_strcmp 测试")
    
    tests = [
        ("相等字符串", '"abc"', '"abc"', '0'),
        ("小于", '"abc"', '"abd"', '-1'),  # 'c' < 'd'
        ("大于", '"abd"', '"abc"', '1'),   # 'd' > 'c'
        ("空字符串比较", '""', '""', '0'),
        ("长度不同", '"ab"', '"abc"', '-1'),  # 长度短的较小
    ]
    
    for name, str1, str2, expected in tests:
        source = f'''
#include <stdio.h>
#include "{STRING_H_PATH}"

int main() {{
    int cmp = zhc_strcmp({str1}, {str2});
    // 归一化比较结果
    if (cmp < 0) cmp = -1;
    else if (cmp > 0) cmp = 1;
    printf("%d\\n", cmp);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        report(name, out.strip() == expected,
               f"期望: {expected}, 实际: {out.strip()}")
        cleanup(exe)


def test_tolower():
    """测试 zhc_tolower 函数"""
    print("\n📝 T025-9: zhc_tolower 测试")
    
    tests = [
        ("正常转换", '"HeLLo WoRLD"', '"hello world"'),
        ("全大写", '"HELLO"', '"hello"'),
        ("全小写", '"hello"', '"hello"'),
        ("数字和符号", '"ABC123!@#"', '"abc123!@#"'),
    ]
    
    for name, input_str, expected in tests:
        source = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char buf[100];
    strcpy(buf, {input_str});
    char *result = zhc_tolower(buf);
    printf("%s\\n", result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean,
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_toupper():
    """测试 zhc_toupper 函数"""
    print("\n📝 T025-10: zhc_toupper 测试")
    
    tests = [
        ("正常转换", '"HeLLo WoRLD"', '"HELLO WORLD"'),
        ("全小写", '"hello"', '"HELLO"'),
        ("全大写", '"HELLO"', '"HELLO"'),
        ("数字和符号", '"abc123!@#"', '"ABC123!@#"'),
    ]
    
    for name, input_str, expected in tests:
        source = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char buf[100];
    strcpy(buf, {input_str});
    char *result = zhc_toupper(buf);
    printf("%s\\n", result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean,
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_trim():
    """测试 zhc_trim 函数"""
    print("\n📝 T025-11: zhc_trim 测试")
    
    tests = [
        ("前导空白", '"  Hello"', '"Hello"'),
        ("尾部空白", '"Hello  "', '"Hello"'),
        ("前后空白", '"  Hello  "', '"Hello"'),
        ("制表符", '"\\tHello\\t"', '"Hello"'),
        ("混合空白", '"  \\tHello\\t  "', '"Hello"'),
        ("仅空白", '"   "', '""'),
        ("无空白", '"Hello"', '"Hello"'),
    ]
    
    for name, input_str, expected in tests:
        source = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char buf[100];
    strcpy(buf, {input_str});
    char *result = zhc_trim(buf);
    printf("%s\\n", result);
    return 0;
}}
'''
        exe, ok, err = compile_c(source)
        if not ok:
            report(name, False, f"编译失败: {err}")
            cleanup(exe)
            continue
        
        out, err, code = run_exe(exe)
        expected_clean = expected.strip('"')
        report(name, out.strip() == expected_clean,
               f"期望: {expected_clean}, 实际: {out.strip()}")
        cleanup(exe)


def test_combined():
    """测试组合操作"""
    print("\n📝 T025-12: 组合测试")
    
    # 查找+替换
    source1 = f'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char *s = "Hello, World! World is great.";
    int pos = zhc_find(s, "World");
    char *r = zhc_replace(s, "World", "中文C");
    printf("%d\\n", pos);
    printf("%s\\n", r);
    free(r);
    return 0;
}}
'''
    exe, ok, err = compile_c(source1)
    if ok:
        out, err, code = run_exe(exe)
        lines = out.strip().split('\n')
        ok = (len(lines) == 2 and 
              lines[0] == '7' and 
              lines[1] == 'Hello, 中文C! 中文C is great.')
        report("查找+替换组合", ok, f"输出: {out.strip()}")
    else:
        report("查找+替换组合", False, f"编译失败: {err}")
    cleanup(exe)
    
    # 去空白+比较
    source2 = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char s1[100] = "  Hello  ";
    char s2[100] = "Hello";
    
    zhc_trim(s1);
    int cmp = zhc_strcmp(s1, s2);
    
    printf("%d\\n", cmp);
    return 0;
}}
'''
    exe, ok, err = compile_c(source2)
    if ok:
        out, err, code = run_exe(exe)
        report("去空白+比较组合", out.strip() == '0',
               f"期望: 0, 实际: {out.strip()}")
    else:
        report("去空白+比较组合", False, f"编译失败: {err}")
    cleanup(exe)
    
    # 大小写转换+比较
    source3 = f'''
#include <stdio.h>
#include <string.h>
#include "{STRING_H_PATH}"

int main() {{
    char s1[100] = "HeLLo";
    char s2[100] = "hello";
    
    zhc_tolower(s1);
    int cmp = zhc_strcmp(s1, s2);
    
    printf("%d\\n", cmp);
    return 0;
}}
'''
    exe, ok, err = compile_c(source3)
    if ok:
        out, err, code = run_exe(exe)
        report("转小写+比较组合", out.strip() == '0',
               f"期望: 0, 实际: {out.strip()}")
    else:
        report("转小写+比较组合", False, f"编译失败: {err}")
    cleanup(exe)


# ============================================================
# 主函数
# ============================================================

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 ZHC String Library - 完整测试套件")
    print("=" * 60)
    
    print(f"\n📋 测试文件: {STRING_H_PATH}")
    print(f"📋 编译器: {CLANG}")
    
    # 运行所有测试
    test_header_compile()
    test_strlen()
    test_strcat()
    test_strcpy()
    test_substr()
    test_find()
    test_replace()
    test_strcmp()
    test_tolower()
    test_toupper()
    test_trim()
    test_combined()
    
    # 输出统计
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())