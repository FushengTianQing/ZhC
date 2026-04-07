#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_stdlib_math.py - 标准库和数学库测试套件

测试 stdlib 和 math 模块的所有函数实现。

版本: 1.0
作者: ZHC编译器团队
"""

import unittest
import subprocess
import tempfile
import os
import math
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestStdlib(unittest.TestCase):
    """stdlib.h 标准库测试"""
    
    def test_memory_management(self):
        """测试内存管理函数"""
        print("\n📝 测试内存管理函数")
        
        # 测试代码
        code = '''
#include "zhc_stdlib.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 测试分配内存
    int *p = (int*)zhc_malloc(10 * sizeof(int));
    if (p == NULL) {
        printf("malloc failed\\n");
        return 1;
    }
    
    // 初始化数组
    for (int i = 0; i < 10; i++) {
        p[i] = i * 10;
    }
    
    // 验证数据
    if (p[5] != 50) {
        printf("malloc data error\\n");
        zhc_free(p);
        return 1;
    }
    
    // 测试分配清零内存
    int *arr = (int*)zhc_calloc(10, sizeof(int));
    if (arr == NULL) {
        printf("calloc failed\\n");
        zhc_free(p);
        return 1;
    }
    
    // 验证清零
    for (int i = 0; i < 10; i++) {
        if (arr[i] != 0) {
            printf("calloc zero error\\n");
            zhc_free(p);
            zhc_free(arr);
            return 1;
        }
    }
    
    // 测试重新分配内存
    int *new_p = (int*)zhc_realloc(p, 20 * sizeof(int));
    if (new_p != NULL) {
        p = new_p;
        // 验证原数据
        if (p[5] != 50) {
            printf("realloc data error\\n");
            zhc_free(p);
            zhc_free(arr);
            return 1;
        }
    }
    
    zhc_free(p);
    zhc_free(arr);
    
    printf("OK\\n");
    return 0;
}
'''
        
        # 编写测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 编译
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            # 运行
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 内存管理测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            # 清理
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_type_conversion(self):
        """测试类型转换函数"""
        print("\n📝 测试类型转换函数")
        
        code = '''
#include "zhc_stdlib.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 测试字符串转整数
    if (zhc_atoi("123") != 123) {
        printf("atoi failed\\n");
        return 1;
    }
    if (zhc_atoi("-456") != -456) {
        printf("atoi negative failed\\n");
        return 1;
    }
    if (zhc_atoi(NULL) != 0) {
        printf("atoi null failed\\n");
        return 1;
    }
    
    // 测试字符串转长整数
    if (zhc_atol("1234567890") != 1234567890L) {
        printf("atol failed\\n");
        return 1;
    }
    
    // 测试字符串转浮点数
    double d1 = zhc_atof("3.14");
    if (d1 < 3.13 || d1 > 3.15) {
        printf("atof failed: %f\\n", d1);
        return 1;
    }
    
    double d2 = zhc_atof("1.5e10");
    if (d2 < 1.49e10 || d2 > 1.51e10) {
        printf("atof sci failed: %f\\n", d2);
        return 1;
    }
    
    // 测试整数转字符串
    char buf[20];
    zhc_itoa(123, buf, 20);
    if (strcmp(buf, "123") != 0) {
        printf("itoa failed: %s\\n", buf);
        return 1;
    }
    
    zhc_itoa(-456, buf, 20);
    if (strcmp(buf, "-456") != 0) {
        printf("itoa negative failed: %s\\n", buf);
        return 1;
    }
    
    // 测试浮点数转字符串
    zhc_ftoa(3.14159, buf, 20, 2);
    if (strcmp(buf, "3.14") != 0) {
        printf("ftoa failed: %s\\n", buf);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 类型转换测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_random_functions(self):
        """测试随机数函数"""
        print("\n📝 测试随机数函数")
        
        code = '''
#include "zhc_stdlib.h"
#include <stdio.h>

int main() {
    // 初始化种子
    zhc_srand(12345);
    
    // 测试随机数生成
    int r1 = zhc_rand();
    int r2 = zhc_rand();
    
    // 相同种子应产生相同序列
    zhc_srand(12345);
    if (zhc_rand() != r1 || zhc_rand() != r2) {
        printf("rand sequence error\\n");
        return 1;
    }
    
    // 测试随机范围
    int pass = 1;
    for (int i = 0; i < 100; i++) {
        int val = zhc_rand_range(1, 6);
        if (val < 1 || val > 6) {
            printf("rand_range out of range: %d\\n", val);
            pass = 0;
            break;
        }
    }
    
    if (!pass) {
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 随机数函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_abs_functions(self):
        """测试绝对值函数"""
        print("\n📝 测试绝对值函数")
        
        code = '''
#include "zhc_stdlib.h"
#include <stdio.h>
#include <math.h>

int main() {
    // 测试整数绝对值
    if (zhc_abs(-5) != 5) {
        printf("abs failed\\n");
        return 1;
    }
    if (zhc_abs(3) != 3) {
        printf("abs positive failed\\n");
        return 1;
    }
    
    // 测试长整数绝对值
    if (zhc_labs(-123456L) != 123456L) {
        printf("labs failed\\n");
        return 1;
    }
    
    // 测试浮点数绝对值
    double d = zhc_fabs(-3.14);
    if (d < 3.13 || d > 3.15) {
        printf("fabs failed: %f\\n", d);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir, '-lm'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 绝对值函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestMath(unittest.TestCase):
    """math.h 数学库测试"""
    
    def test_trigonometric_functions(self):
        """测试三角函数"""
        print("\n📝 测试三角函数")
        
        code = '''
#include "zhc_math.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 测试正弦函数
    double sin30 = zhc_sin(M_PI / 6);
    if (sin30 < 0.49 || sin30 > 0.51) {
        printf("sin30 failed: %f\\n", sin30);
        return 1;
    }
    
    // 测试余弦函数
    double cos60 = zhc_cos(M_PI / 3);
    if (cos60 < 0.49 || cos60 > 0.51) {
        printf("cos60 failed: %f\\n", cos60);
        return 1;
    }
    
    // 测试正切函数
    double tan45 = zhc_tan(M_PI / 4);
    if (tan45 < 0.99 || tan45 > 1.01) {
        printf("tan45 failed: %f\\n", tan45);
        return 1;
    }
    
    // 测试反正弦函数
    double asin05 = zhc_asin(0.5);
    if (asin05 < M_PI/6 - 0.01 || asin05 > M_PI/6 + 0.01) {
        printf("asin0.5 failed: %f\\n", asin05);
        return 1;
    }
    
    // 测试反余弦函数
    double acos05 = zhc_acos(0.5);
    if (acos05 < M_PI/3 - 0.01 || acos05 > M_PI/3 + 0.01) {
        printf("acos0.5 failed: %f\\n", acos05);
        return 1;
    }
    
    // 测试反正切函数
    double atan1 = zhc_atan(1.0);
    if (atan1 < M_PI/4 - 0.01 || atan1 > M_PI/4 + 0.01) {
        printf("atan1 failed: %f\\n", atan1);
        return 1;
    }
    
    // 测试atan2函数
    double atan2_val = zhc_atan2(1.0, 1.0);
    if (atan2_val < M_PI/4 - 0.01 || atan2_val > M_PI/4 + 0.01) {
        printf("atan2 failed: %f\\n", atan2_val);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir, '-lm'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 三角函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_exponential_logarithmic_functions(self):
        """测试指数对数函数"""
        print("\n📝 测试指数对数函数")
        
        code = '''
#include "zhc_math.h"
#include <stdio.h>
#include <math.h>

#ifndef M_E
#define M_E 2.7182818284590452354
#endif

int main() {
    // 测试自然指数函数
    double exp1 = zhc_exp(1.0);
    if (exp1 < M_E - 0.01 || exp1 > M_E + 0.01) {
        printf("exp1 failed: %f\\n", exp1);
        return 1;
    }
    
    // 测试自然对数函数
    double log_e = zhc_log(M_E);
    if (log_e < 0.99 || log_e > 1.01) {
        printf("log(e) failed: %f\\n", log_e);
        return 1;
    }
    
    // 测试常用对数函数
    double log10_100 = zhc_log10(100.0);
    if (log10_100 < 1.99 || log10_100 > 2.01) {
        printf("log10(100) failed: %f\\n", log10_100);
        return 1;
    }
    
    // 测试二进制对数函数
    double log2_8 = zhc_log2(8.0);
    if (log2_8 < 2.99 || log2_8 > 3.01) {
        printf("log2(8) failed: %f\\n", log2_8);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir, '-lm'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 指数对数函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_power_functions(self):
        """测试幂运算函数"""
        print("\n📝 测试幂运算函数")
        
        code = '''
#include "zhc_math.h"
#include <stdio.h>
#include <math.h>

int main() {
    // 测试幂函数
    double pow_2_10 = zhc_pow(2.0, 10.0);
    if (pow_2_10 < 1023.0 || pow_2_10 > 1025.0) {
        printf("pow(2, 10) failed: %f\\n", pow_2_10);
        return 1;
    }
    
    // 测试平方根函数
    double sqrt_16 = zhc_sqrt(16.0);
    if (sqrt_16 < 3.99 || sqrt_16 > 4.01) {
        printf("sqrt(16) failed: %f\\n", sqrt_16);
        return 1;
    }
    
    // 测试负数平方根
    double sqrt_neg = zhc_sqrt(-1.0);
    if (!isnan(sqrt_neg)) {
        printf("sqrt(-1) should be NaN\\n");
        return 1;
    }
    
    // 测试立方根函数
    double cbrt_27 = zhc_cbrt(27.0);
    if (cbrt_27 < 2.99 || cbrt_27 > 3.01) {
        printf("cbrt(27) failed: %f\\n", cbrt_27);
        return 1;
    }
    
    // 测试n次方根函数
    double nroot_81_4 = zhc_nroot(81.0, 4.0);
    if (nroot_81_4 < 2.99 || nroot_81_4 > 3.01) {
        printf("nroot(81, 4) failed: %f\\n", nroot_81_4);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir, '-lm'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 幂运算函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_rounding_functions(self):
        """测试取整函数"""
        print("\n📝 测试取整函数")
        
        code = '''
#include "zhc_math.h"
#include <stdio.h>
#include <math.h>

int main() {
    // 测试向上取整
    if (zhc_ceil(3.2) != 4.0) {
        printf("ceil(3.2) failed\\n");
        return 1;
    }
    if (zhc_ceil(-3.2) != -3.0) {
        printf("ceil(-3.2) failed\\n");
        return 1;
    }
    
    // 测试向下取整
    if (zhc_floor(3.8) != 3.0) {
        printf("floor(3.8) failed\\n");
        return 1;
    }
    if (zhc_floor(-3.8) != -4.0) {
        printf("floor(-3.8) failed\\n");
        return 1;
    }
    
    // 测试四舍五入
    if (zhc_round(3.4) != 3.0) {
        printf("round(3.4) failed\\n");
        return 1;
    }
    if (zhc_round(3.5) != 4.0) {
        printf("round(3.5) failed\\n");
        return 1;
    }
    
    // 测试截断取整
    if (zhc_trunc(3.7) != 3.0) {
        printf("trunc(3.7) failed\\n");
        return 1;
    }
    if (zhc_trunc(-3.7) != -3.0) {
        printf("trunc(-3.7) failed\\n");
        return 1;
    }
    
    // 测试浮点取余
    double fmod_val = zhc_fmod(10.5, 3.0);
    if (fmod_val < 1.49 || fmod_val > 1.51) {
        printf("fmod(10.5, 3.0) failed: %f\\n", fmod_val);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir, '-lm'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 取整函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)
    
    def test_other_functions(self):
        """测试其他数学函数"""
        print("\n📝 测试其他数学函数")
        
        code = '''
#include "zhc_math.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 测试最大值最小值
    if (zhc_fmax(3.14, 2.71) != 3.14) {
        printf("fmax failed\\n");
        return 1;
    }
    if (zhc_fmin(3.14, 2.71) != 2.71) {
        printf("fmin failed\\n");
        return 1;
    }
    
    // 测试NaN判断
    if (!zhc_isnan(NAN)) {
        printf("isnan failed\\n");
        return 1;
    }
    if (zhc_isnan(1.0)) {
        printf("isnan normal failed\\n");
        return 1;
    }
    
    // 测试无穷大判断
    if (!zhc_isinf(INFINITY)) {
        printf("isinf failed\\n");
        return 1;
    }
    if (zhc_isinf(1.0)) {
        printf("isinf normal failed\\n");
        return 1;
    }
    
    // 测试角度弧度转换
    double rad = zhc_deg2rad(180.0);
    if (rad < M_PI - 0.01 || rad > M_PI + 0.01) {
        printf("deg2rad failed: %f\\n", rad);
        return 1;
    }
    
    double deg = zhc_rad2deg(M_PI);
    if (deg < 179.0 || deg > 181.0) {
        printf("rad2deg failed: %f\\n", deg);
        return 1;
    }
    
    printf("OK\\n");
    return 0;
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            include_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'lib')
            result = subprocess.run(
                ['clang', '-o', temp_file.replace('.c', ''), temp_file, '-I', include_dir, '-lm'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")
            
            result = subprocess.run(
                [temp_file.replace('.c', '')],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "OK" in result.stdout:
                print("  ✅ 其他数学函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")
                
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace('.c', '')
            if os.path.exists(exe_file):
                os.remove(exe_file)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("stdlib.h 和 math.h 标准库测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestStdlib))
    suite.addTests(loader.loadTestsFromTestCase(TestMath))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印结果
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} 通过")
    print(f"   ✅ 通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ 失败: {len(result.failures)}")
    print(f"   ⚠️  错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())