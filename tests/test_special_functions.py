#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_special_functions.py - 特殊数学函数测试套件

测试 zhc_special.h 中的特殊数学函数：
- Gamma 和 Beta 函数
- 误差函数
- 贝塞尔函数
- 椭圆积分
- 统计分布函数

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


class TestGammaBetaFunctions(unittest.TestCase):
    """Gamma 和 Beta 函数测试"""

    def test_gamma_function(self):
        """测试 Gamma 函数"""
        print("\n📝 测试 Gamma 函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // Gamma(1) = 1
    double g1 = zhc_gamma(1.0);
    if (fabs(g1 - 1.0) > 1e-10) {
        printf("gamma(1) failed: %f\\n", g1);
        return 1;
    }

    // Gamma(5) = 24 (4!)
    double g5 = zhc_gamma(5.0);
    if (fabs(g5 - 24.0) > 1e-10) {
        printf("gamma(5) failed: %f\\n", g5);
        return 1;
    }

    // Gamma(0.5) = sqrt(pi)
    double ghalf = zhc_gamma(0.5);
    if (fabs(ghalf - sqrt(M_PI)) > 1e-10) {
        printf("gamma(0.5) failed: %f (expected %f)\\n", ghalf, sqrt(M_PI));
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ Gamma 函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_lgamma_function(self):
        """测试对数 Gamma 函数"""
        print("\n📝 测试对数 Gamma 函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

int main() {
    // lgamma(5) = log(gamma(5)) = log(24)
    double lg5 = zhc_lgamma(5.0);
    if (fabs(lg5 - log(24.0)) > 1e-10) {
        printf("lgamma(5) failed: %f (expected %f)\\n", lg5, log(24.0));
        return 1;
    }

    // lgamma(1) = log(1) = 0
    double lg1 = zhc_lgamma(1.0);
    if (fabs(lg1) > 1e-10) {
        printf("lgamma(1) failed: %f\\n", lg1);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 对数 Gamma 函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_beta_function(self):
        """测试 Beta 函数"""
        print("\n📝 测试 Beta 函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

int main() {
    // Beta(1,1) = 1
    double b1 = zhc_beta(1.0, 1.0);
    if (fabs(b1 - 1.0) > 1e-10) {
        printf("beta(1,1) failed: %f\\n", b1);
        return 1;
    }

    // Beta(2,3) = Gamma(2)*Gamma(3)/Gamma(5) = 1*2/24 = 1/12
    double b23 = zhc_beta(2.0, 3.0);
    if (fabs(b23 - 1.0/12.0) > 1e-10) {
        printf("beta(2,3) failed: %f (expected %f)\\n", b23, 1.0/12.0);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ Beta 函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestErrorFunction(unittest.TestCase):
    """误差函数测试"""

    def test_erf(self):
        """测试误差函数"""
        print("\n📝 测试误差函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

int main() {
    // erf(0) = 0
    double e0 = zhc_erf(0.0);
    if (fabs(e0) > 1e-10) {
        printf("erf(0) failed: %f\\n", e0);
        return 1;
    }

    // erf(1) ≈ 0.8427
    double e1 = zhc_erf(1.0);
    if (fabs(e1 - 0.8427007929) > 1e-6) {
        printf("erf(1) failed: %f (expected 0.8427)\\n", e1);
        return 1;
    }

    // erf(-1) = -erf(1)
    double em1 = zhc_erf(-1.0);
    if (fabs(em1 + 0.8427007929) > 1e-6) {
        printf("erf(-1) failed: %f\\n", em1);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 误差函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_erfc(self):
        """测试互补误差函数"""
        print("\n📝 测试互补误差函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

int main() {
    // erfc(0) = 1
    double ec0 = zhc_erfc(0.0);
    if (fabs(ec0 - 1.0) > 1e-10) {
        printf("erfc(0) failed: %f\\n", ec0);
        return 1;
    }

    // erfc(1) = 1 - erf(1)
    double ec1 = zhc_erfc(1.0);
    double expected_ec1 = 1.0 - 0.8427007929;
    if (fabs(ec1 - expected_ec1) > 1e-6) {
        printf("erfc(1) failed: %f (expected %f)\\n", ec1, expected_ec1);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 互补误差函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestBesselFunctions(unittest.TestCase):
    """贝塞尔函数测试"""

    def test_bessel_j(self):
        """测试第一类贝塞尔函数"""
        print("\n📝 测试第一类贝塞尔函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

int main() {
    // J_0(0) = 1
    double j00 = zhc_bessel_j(0, 0.0);
    if (fabs(j00 - 1.0) > 1e-10) {
        printf("J_0(0) failed: %f\\n", j00);
        return 1;
    }

    // J_1(0) = 0
    double j10 = zhc_bessel_j(1, 0.0);
    if (fabs(j10) > 1e-10) {
        printf("J_1(0) failed: %f\\n", j10);
        return 1;
    }

    // J_0(1) ≈ 0.7652
    double j01 = zhc_bessel_j(0, 1.0);
    if (fabs(j01 - 0.7651976866) > 1e-6) {
        printf("J_0(1) failed: %f (expected 0.7652)\\n", j01);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 第一类贝塞尔函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestEllipticIntegrals(unittest.TestCase):
    """椭圆积分测试"""

    def test_elliptic_integrals(self):
        """测试完全椭圆积分"""
        print("\n📝 测试完全椭圆积分")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // K(0) = pi/2
    double k0 = zhc_elliptic_k(0.0);
    if (fabs(k0 - M_PI/2.0) > 1e-10) {
        printf("K(0) failed: %f (expected %f)\\n", k0, M_PI/2.0);
        return 1;
    }

    // E(0) = pi/2
    double e0 = zhc_elliptic_e(0.0);
    if (fabs(e0 - M_PI/2.0) > 1e-10) {
        printf("E(0) failed: %f (expected %f)\\n", e0, M_PI/2.0);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 完全椭圆积分测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestStatisticalDistributions(unittest.TestCase):
    """统计分布函数测试"""

    def test_normal_distribution(self):
        """测试正态分布函数"""
        print("\n📝 测试正态分布函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 标准正态分布在 x=0 处的 PDF = 1/sqrt(2*pi) ≈ 0.3989
    double pdf0 = zhc_normal_pdf(0.0, 0.0, 1.0);
    if (fabs(pdf0 - 0.3989422804) > 1e-6) {
        printf("normal_pdf(0) failed: %f (expected 0.3989)\\n", pdf0);
        return 1;
    }

    // 标准正态分布在 x=0 处的 CDF = 0.5
    double cdf0 = zhc_normal_cdf(0.0, 0.0, 1.0);
    if (fabs(cdf0 - 0.5) > 1e-10) {
        printf("normal_cdf(0) failed: %f\\n", cdf0);
        return 1;
    }

    // normal_cdf(1.96) ≈ 0.975
    double cdf196 = zhc_normal_cdf(1.96, 0.0, 1.0);
    if (fabs(cdf196 - 0.975) > 0.01) {
        printf("normal_cdf(1.96) failed: %f (expected 0.975)\\n", cdf196);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 正态分布函数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_chi2_distribution(self):
        """测试卡方分布函数"""
        print("\n📝 测试卡方分布函数")

        code = """
#define ZHC_SPECIAL_IMPLEMENTATION
#include "zhc_special.h"
#include <stdio.h>
#include <math.h>

int main() {
    // 卡方分布在 x=0 处为 0
    double pdf0 = zhc_chi2_pdf(0.0, 5);
    if (fabs(pdf0) > 1e-10) {
        printf("chi2_pdf(0) failed: %f\\n", pdf0);
        return 1;
    }

    // 累积分布函数在 x=0 处为 0
    double cdf0 = zhc_chi2_cdf(0.0, 5);
    if (fabs(cdf0) > 1e-10) {
        printf("chi2_cdf(0) failed: %f\\n", cdf0);
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
                timeout=10,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")], capture_output=True, text=True, timeout=5
            )

            if "OK" in result.stdout:
                print("  ✅ 卡方分布函数测试通过")
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
    print("特殊数学函数测试")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestGammaBetaFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestBesselFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestEllipticIntegrals))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticalDistributions))

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
