#!/usr/bin/env python3
"""测试套件6：标准库函数（30个测试用例）"""

import os
import subprocess
import tempfile
import sys

def run_test(test_num, category, description, zhc_code, expected_output=None, compile_flags=""):
    """运行单个测试"""
    print(f"测试 {test_num:2d} ({category:6s}): {description}")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.zhc', delete=False, encoding='utf-8') as f:
        f.write(zhc_code)
        zhc_file = f.name
    
    c_file = zhc_file.replace('.zhc', '.c')
    exe_file = zhc_file.replace('.zhc', '.exe')
    
    try:
        # 转换
        result = subprocess.run(
            ['python3', 'src/zhpp_v5.py', zhc_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) + '/..'
        )
        
        if result.returncode != 0:
            print(f"  ❌ 转换失败: {result.stderr[:100]}")
            return False
        
        # 读取转换结果
        with open(c_file, 'r', encoding='utf-8') as f:
            converted = f.read()
        
        # 检查转换结果
        if '函数 ' in converted and '->' in converted:
            print(f"  ❌ 函数声明未完全转换")
            return False
        
        # 编译
        compile_cmd = ['clang', c_file, '-o', exe_file]
        if compile_flags:
            compile_cmd.extend(compile_flags.split())
        
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            print(f"  ❌ 编译失败: {compile_result.stderr[:200]}")
            return False
        
        # 运行
        if expected_output is not None:
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True
            )
            
            if run_result.returncode != 0:
                print(f"  ❌ 运行失败: {run_result.stderr[:100]}")
                return False
            
            actual_output = run_result.stdout.strip()
            if actual_output != expected_output:
                print(f"  ❌ 输出不匹配")
                print(f"    预期: {expected_output}")
                print(f"    实际: {actual_output}")
                return False
            
            print(f"  ✓ 通过")
        else:
            print(f"  ✓ 编译通过")
        
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
    print("=" * 70)
    print("测试套件6：标准库函数（30个测试用例）")
    print("=" * 70)
    
    tests = [
        # 1-5: 内存管理测试
        (1, "内存", "malloc和free",
         """#include <stdlib.h>
int main() {
    int* p = (int*)malloc(sizeof(int));
    *p = 42;
    free(p);
    return 0;
}""", None),
        
        (2, "内存", "calloc初始化",
         """#include <stdlib.h>
#include <stdio.h>
int main() {
    int* arr = (int*)calloc(5, sizeof(int));
    printf("%d", arr[0] + arr[4]);
    free(arr);
    return 0;
}""", "0"),
        
        (3, "内存", "realloc扩展",
         """#include <stdlib.h>
#include <stdio.h>
int main() {
    int* p = (int*)malloc(2 * sizeof(int));
    p[0] = 1; p[1] = 2;
    p = (int*)realloc(p, 4 * sizeof(int));
    p[2] = 3; p[3] = 4;
    printf("%d", p[0] + p[3]);
    free(p);
    return 0;
}""", "5"),
        
        (4, "内存", "memset清零",
         """#include <string.h>
#include <stdio.h>
int main() {
    char buf[10];
    memset(buf, 0, 10);
    printf("%d", buf[5] == 0);
    return 0;
}""", "1"),
        
        (5, "内存", "memcpy复制",
         """#include <string.h>
#include <stdio.h>
int main() {
    char src[] = "hello";
    char dest[6];
    memcpy(dest, src, 6);
    printf("%s", dest);
    return 0;
}""", "hello"),
        
        # 6-10: 字符串操作测试
        (6, "字符串", "strlen长度",
         """#include <string.h>
#include <stdio.h>
int main() {
    printf("%d", strlen("hello"));
    return 0;
}""", "5"),
        
        (7, "字符串", "strcpy复制",
         """#include <string.h>
#include <stdio.h>
int main() {
    char dest[10];
    strcpy(dest, "world");
    printf("%s", dest);
    return 0;
}""", "world"),
        
        (8, "字符串", "strcat连接",
         """#include <string.h>
#include <stdio.h>
int main() {
    char str[20] = "Hello, ";
    strcat(str, "World!");
    printf("%s", str);
    return 0;
}""", "Hello, World!"),
        
        (9, "字符串", "strcmp比较",
         """#include <string.h>
#include <stdio.h>
int main() {
    printf("%d", strcmp("apple", "banana"));
    return 0;
}""", "-1"),
        
        (10, "字符串", "strstr查找",
         """#include <string.h>
#include <stdio.h>
int main() {
    char* found = strstr("hello world", "world");
    printf("%d", found != NULL);
    return 0;
}""", "1"),
        
        # 11-15: 输入输出测试
        (11, "IO", "printf格式化",
         """#include <stdio.h>
int main() {
    printf("%d+%d=%d", 2, 3, 5);
    return 0;
}""", "2+3=5"),
        
        (12, "IO", "putchar输出字符",
         """#include <stdio.h>
int main() {
    putchar('A');
    return 0;
}""", "A"),
        
        (13, "IO", "sprintf格式化到字符串",
         """#include <stdio.h>
int main() {
    char buf[50];
    sprintf(buf, "value=%d", 100);
    printf("%s", buf);
    return 0;
}""", "value=100"),
        
        (14, "IO", "文件操作fopen/fclose",
         """#include <stdio.h>
int main() {
    FILE* f = fopen("/tmp/test.txt", "w");
    printf("%d", f != NULL);
    if (f) fclose(f);
    return 0;
}""", "1"),
        
        (15, "IO", "fprintf到文件",
         """#include <stdio.h>
int main() {
    FILE* f = fopen("/tmp/test_fprintf.txt", "w");
    fprintf(f, "test");
    fclose(f);
    printf("done");
    return 0;
}""", "done"),
        
        # 16-20: 数学函数测试
        (16, "数学", "sqrt平方根",
         """#include <math.h>
#include <stdio.h>
int main() {
    printf("%.1f", sqrt(25.0));
    return 0;
}""", "5.0", "-lm"),
        
        (17, "数学", "pow幂函数",
         """#include <math.h>
#include <stdio.h>
int main() {
    printf("%.0f", pow(2.0, 3.0));
    return 0;
}""", "8", "-lm"),
        
        (18, "数学", "sin正弦",
         """#include <math.h>
#include <stdio.h>
int main() {
    printf("%.4f", sin(3.14159/6));
    return 0;
}""", "0.5000", "-lm"),
        
        (19, "数学", "abs绝对值",
         """#include <stdlib.h>
#include <stdio.h>
int main() {
    printf("%d", abs(-10));
    return 0;
}""", "10"),
        
        (20, "数学", "ceil向上取整",
         """#include <math.h>
#include <stdio.h>
int main() {
    printf("%.0f", ceil(3.2));
    return 0;
}""", "4", "-lm"),
        
        # 21-25: 字符处理测试
        (21, "字符", "isalpha字母检测",
         """#include <ctype.h>
#include <stdio.h>
int main() {
    printf("%d", isalpha('A') != 0);
    return 0;
}""", "1"),
        
        (22, "字符", "isdigit数字检测",
         """#include <ctype.h>
#include <stdio.h>
int main() {
    printf("%d", isdigit('5') != 0);
    return 0;
}""", "1"),
        
        (23, "字符", "islower小写检测",
         """#include <ctype.h>
#include <stdio.h>
int main() {
    printf("%d", islower('a') != 0);
    return 0;
}""", "1"),
        
        (24, "字符", "toupper转大写",
         """#include <ctype.h>
#include <stdio.h>
int main() {
    printf("%c", toupper('x'));
    return 0;
}""", "X"),
        
        (25, "字符", "isspace空格检测",
         """#include <ctype.h>
#include <stdio.h>
int main() {
    printf("%d", isspace(' ') != 0);
    return 0;
}""", "1"),
        
        # 26-30: 时间函数和其他测试
        (26, "时间", "time获取时间",
         """#include <time.h>
#include <stdio.h>
int main() {
    time_t t = time(NULL);
    printf("%d", t > 0);
    return 0;
}""", "1"),
        
        (27, "时间", "clock计时",
         """#include <time.h>
#include <stdio.h>
int main() {
    clock_t start = clock();
    int sum = 0;
    for (int i = 0; i < 1000; i++) sum += i;
    clock_t end = clock();
    printf("%d", (end - start) >= 0);
    return 0;
}""", "1"),
        
        (28, "系统", "exit退出程序",
         """#include <stdlib.h>
int main() {
    exit(0);
    return 1;
}""", None),
        
        (29, "系统", "getenv环境变量",
         """#include <stdlib.h>
#include <stdio.h>
int main() {
    char* home = getenv("HOME");
    printf("%d", home != NULL);
    return 0;
}""", "1"),
        
        (30, "组合", "综合使用多个库函数",
         """#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
int main() {
    // 内存
    int* arr = (int*)malloc(3 * sizeof(int));
    memset(arr, 0, 3 * sizeof(int));
    
    // 数学
    arr[0] = (int)sqrt(64.0);
    arr[1] = (int)pow(2.0, 4.0);
    
    // 字符串
    char msg[50];
    sprintf(msg, "values: %d,%d", arr[0], arr[1]);
    
    // 输出
    printf("%s", msg);
    
    free(arr);
    return 0;
}""", "values: 8,16"),
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if len(test) == 4:
            test_num, category, desc, code = test
            expected = None
            flags = ""
        elif len(test) == 5:
            test_num, category, desc, code, expected = test
            flags = ""
        else:
            test_num, category, desc, code, expected, flags = test
        
        if run_test(test_num, category, desc, code, expected, flags):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"通过率: {passed/len(tests)*100:.1f}%")
    print("=" * 70)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())