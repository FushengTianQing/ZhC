#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_trig_extended.py - 三角函数扩展库测试套件

测试 zhc_trig.h 中的度数版本、高精度版本、
向量化版本和查表优化版本三角函数。

版本: 1.0
作者: ZHC编译器团队
"""

import unittest
import subprocess
import tempfile
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestDegreeVersion(unittest.TestCase):
    """度数版本三角函数测试"""

    def test_sin_deg(self):
        """测试正弦度数版本"""
        print("\n📝 测试正弦度数版本")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // sin(30°) = 0.5
    double s1 = zhc_sin_deg(30.0);
    if (fabs(s1 - 0.5) > 1e-10) {
        printf("sin(30) failed: %f\\n", s1);
        return 1;
    }

    // sin(90°) = 1.0
    double s2 = zhc_sin_deg(90.0);
    if (fabs(s2 - 1.0) > 1e-10) {
        printf("sin(90) failed: %f\\n", s2);
        return 1;
    }

    // sin(0°) = 0.0
    double s3 = zhc_sin_deg(0.0);
    if (fabs(s3) > 1e-10) {
        printf("sin(0) failed: %f\\n", s3);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 正弦度数版本测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_cos_deg(self):
        """测试余弦度数版本"""
        print("\n📝 测试余弦度数版本")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

int main() {
    // cos(60°) = 0.5
    double c1 = zhc_cos_deg(60.0);
    if (fabs(c1 - 0.5) > 1e-10) {
        printf("cos(60) failed: %f\\n", c1);
        return 1;
    }

    // cos(0°) = 1.0
    double c2 = zhc_cos_deg(0.0);
    if (fabs(c2 - 1.0) > 1e-10) {
        printf("cos(0) failed: %f\\n", c2);
        return 1;
    }

    // cos(180°) = -1.0
    double c3 = zhc_cos_deg(180.0);
    if (fabs(c3 - (-1.0)) > 1e-10) {
        printf("cos(180) failed: %f\\n", c3);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 余弦度数版本测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_tan_deg(self):
        """测试正切度数版本"""
        print("\n📝 测试正切度数版本")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

int main() {
    // tan(45°) = 1.0
    double t1 = zhc_tan_deg(45.0);
    if (fabs(t1 - 1.0) > 1e-10) {
        printf("tan(45) failed: %f\\n", t1);
        return 1;
    }

    // tan(0°) = 0.0
    double t2 = zhc_tan_deg(0.0);
    if (fabs(t2) > 1e-10) {
        printf("tan(0) failed: %f\\n", t2);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 正切度数版本测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_inverse_deg(self):
        """测试反三角函数度数版本"""
        print("\n📝 测试反三角函数度数版本")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

int main() {
    // asin(0.5) = 30°
    double a1 = zhc_asin_deg(0.5);
    if (fabs(a1 - 30.0) > 1e-10) {
        printf("asin(0.5) failed: %f\\n", a1);
        return 1;
    }

    // acos(0.5) = 60°
    double a2 = zhc_acos_deg(0.5);
    if (fabs(a2 - 60.0) > 1e-10) {
        printf("acos(0.5) failed: %f\\n", a2);
        return 1;
    }

    // atan(1.0) = 45°
    double a3 = zhc_atan_deg(1.0);
    if (fabs(a3 - 45.0) > 1e-10) {
        printf("atan(1.0) failed: %f\\n", a3);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 反三角函数度数版本测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestPreciseVersion(unittest.TestCase):
    """高精度版本三角函数测试"""

    def test_precise_trig(self):
        """测试高精度三角函数"""
        print("\n📝 测试高精度三角函数")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 测试 long double 版本
    long double rad = M_PI / 6.0L;  // 30°

    // 正弦高精度
    long double s = zhc_sin_precise(rad);
    if (fabsl(s - 0.5L) > 1e-12L) {
        printf("sin_precise failed: %Lf\\n", s);
        return 1;
    }

    // 余弦高精度
    long double c = zhc_cos_precise(rad);
    if (fabsl(c - 0.8660254037844386L) > 1e-12L) {
        printf("cos_precise failed: %Lf\\n", c);
        return 1;
    }

    // 正切高精度
    long double t = zhc_tan_precise(M_PI / 4.0L);  // 45°
    if (fabsl(t - 1.0L) > 1e-12L) {
        printf("tan_precise failed: %Lf\\n", t);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 高精度三角函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestVectorizedVersion(unittest.TestCase):
    """向量化版本三角函数测试"""

    def test_sincos(self):
        """测试 sincos 组合函数"""
        print("\n📝 测试 sincos 组合函数")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    double sin_out, cos_out;

    // sin 和 cos(π/6) = (0.5, √3/2)
    zhc_sincos(M_PI / 6.0, &sin_out, &cos_out);

    if (fabs(sin_out - 0.5) > 1e-10 || fabs(cos_out - 0.8660254037844386) > 1e-10) {
        printf("sincos failed: sin=%f, cos=%f\\n", sin_out, cos_out);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ sincos 组合函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_vectorized_trig(self):
        """测试向量化三角函数"""
        print("\n📝 测试向量化三角函数")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    float arr[4] = {0.0f, (float)(M_PI/6), (float)(M_PI/4), (float)(M_PI/3)};

    // 保存原始值用于比较
    float original[4];
    memcpy(original, arr, sizeof(arr));

    // 测试正弦向量
    zhc_sin_vector(arr, 4);

    // 验证结果
    if (fabs(arr[0]) > 1e-6 || fabs(arr[1] - 0.5f) > 0.001f ||
        fabs(arr[2] - 0.707f) > 0.001f || fabs(arr[3] - 0.866f) > 0.001f) {
        printf("sin_vector failed: %f, %f, %f, %f\\n", arr[0], arr[1], arr[2], arr[3]);
        return 1;
    }

    // 恢复并测试余弦向量
    memcpy(arr, original, sizeof(arr));
    zhc_cos_vector(arr, 4);

    if (fabs(arr[0] - 1.0f) > 0.001f || fabs(arr[1] - 0.866f) > 0.001f ||
        fabs(arr[2] - 0.707f) > 0.001f || fabs(arr[3] - 0.5f) > 0.001f) {
        printf("cos_vector failed: %f, %f, %f, %f\\n", arr[0], arr[1], arr[2], arr[3]);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 向量化三角函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestTableLookupVersion(unittest.TestCase):
    """查表优化版本三角函数测试"""

    def test_trig_table(self):
        """测试查表三角函数"""
        print("\n📝 测试查表三角函数")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 初始化查找表
    zhc_init_trig_table(2048);

    // 测试 sin_table
    double s1 = zhc_sin_table(M_PI / 6);  // sin(30°)
    if (fabs(s1 - 0.5) > 0.001) {
        printf("sin_table(30°) failed: %f\\n", s1);
        return 1;
    }

    // 测试 cos_table
    double c1 = zhc_cos_table(M_PI / 3);  // cos(60°)
    if (fabs(c1 - 0.5) > 0.001) {
        printf("cos_table(60°) failed: %f\\n", c1);
        return 1;
    }

    // 测试特殊值
    double s0 = zhc_sin_table(0.0);
    if (fabs(s0) > 0.001) {
        printf("sin_table(0) failed: %f\\n", s0);
        return 1;
    }

    double c0 = zhc_cos_table(0.0);
    if (fabs(c0 - 1.0) > 0.001) {
        printf("cos_table(0) failed: %f\\n", c0);
        return 1;
    }

    // 销毁查找表
    zhc_destroy_trig_table();

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 查表三角函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_auto_init_table(self):
        """测试自动初始化查找表"""
        print("\n📝 测试自动初始化查找表")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 不手动初始化，直接使用查表函数
    double s = zhc_sin_table(M_PI / 4);
    if (fabs(s - 0.707) > 0.01) {
        printf("auto init sin_table failed: %f\\n", s);
        return 1;
    }

    double c = zhc_cos_table(M_PI / 4);
    if (fabs(c - 0.707) > 0.01) {
        printf("auto init cos_table failed: %f\\n", c);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 自动初始化查找表测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestApproxVersion(unittest.TestCase):
    """快速近似版本三角函数测试"""

    def test_approx_trig(self):
        """测试快速近似三角函数"""
        print("\n📝 测试快速近似三角函数")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 测试正弦近似
    double s = zhc_sin_approx(M_PI / 6);
    if (fabs(s - 0.5) > 1e-5) {
        printf("sin_approx failed: %f (expected 0.5)\\n", s);
        return 1;
    }

    // 测试余弦近似
    double c = zhc_cos_approx(M_PI / 3);
    if (fabs(c - 0.5) > 1e-5) {
        printf("cos_approx failed: %f (expected 0.5)\\n", c);
        return 1;
    }

    // 测试边界值
    double s0 = zhc_sin_approx(0.0);
    if (fabs(s0) > 1e-10) {
        printf("sin_approx(0) failed: %f\\n", s0);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 快速近似三角函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestUtilityFunctions(unittest.TestCase):
    """实用工具函数测试"""

    def test_normalize_angle(self):
        """测试角度归一化函数"""
        print("\n📝 测试角度归一化函数")

        code = """
#define ZHC_TRIG_IMPLEMENTATION
#include "zhc_trig.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 测试弧度归一化
    double r1 = zhc_normalize_angle(7.0 * M_PI);  // 3.5 * 2π 应该归一化到 π
    if (r1 < M_PI - 0.01 || r1 > M_PI + 0.01) {
        printf("normalize_angle(3.5π) failed: %f\\n", r1);
        return 1;
    }

    // 测试负角度归一化
    double r2 = zhc_normalize_angle(-M_PI / 2);  // -π/2 应该归一化到 3π/2
    if (r2 < 3*M_PI/2 - 0.01 || r2 > 3*M_PI/2 + 0.01) {
        printf("normalize_angle(-π/2) failed: %f\\n", r2);
        return 1;
    }

    // 测试度数归一化
    double d1 = zhc_normalize_angle_deg(450.0);  // 450° 应该归一化到 90°
    if (d1 < 89.0 || d1 > 91.0) {
        printf("normalize_angle_deg(450°) failed: %f\\n", d1);
        return 1;
    }

    // 测试负角度归一化
    double d2 = zhc_normalize_angle_deg(-90.0);  // -90° 应该归一化到 270°
    if (d2 < 269.0 || d2 > 271.0) {
        printf("normalize_angle_deg(-90°) failed: %f\\n", d2);
        return 1;
    }

    printf("OK\\n");
    return 0;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            include_dir = os.path.join(
                os.path.dirname(__file__), "..", "src", "zhc", "lib"
            )
            result = subprocess.run(
                [
                    "clang",
                    "-o",
                    temp_file.replace(".c", ""),
                    temp_file,
                    "-I",
                    include_dir,
                    "-lm",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 角度归一化函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("三角函数扩展库测试")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestDegreeVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestPreciseVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorizedVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestTableLookupVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestApproxVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityFunctions))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印结果
    print("\n" + "=" * 60)
    print(
        f"📊 测试结果: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} 通过"
    )
    print(f"   ✅ 通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ 失败: {len(result.failures)}")
    print(f"   ⚠️  错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
