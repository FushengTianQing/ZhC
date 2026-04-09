#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_time.py - 时间库测试套件

测试 zhc_time.h 中的时间函数：
- 时间获取
- 时间结构转换
- 时间格式化与解析
- 时间计算
- 计时器
- 延时

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


class TestTimeGetting(unittest.TestCase):
    """时间获取测试"""

    def test_time_now(self):
        """测试获取当前时间戳"""
        print("\n📝 测试当前时间戳")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <time.h>

int main() {
    zhc_timestamp_t t = zhc_time_now();

    // 时间戳应该大于 2020-01-01 的时间戳
    if (t < 1577836800) {
        printf("time_now too small: %lld\\n", t);
        return 1;
    }

    // 时间戳应该小于 2090-01-01 的时间戳
    if (t > 2288995200) {
        printf("time_now too large: %lld\\n", t);
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
                print("  ✅ 当前时间戳测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_time_now_us(self):
        """测试微秒级时间获取"""
        print("\n📝 测试微秒级时间获取")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>

int main() {
    long long t1 = zhc_time_now_us();

    // 简单延时
    volatile int sum = 0;
    for (int i = 0; i < 1000; i++) sum += i;

    long long t2 = zhc_time_now_us();

    // 微秒时间戳应该大于 1e12（2020年左右）
    if (t1 < 1000000000000LL) {
        printf("time_now_us too small: %lld\\n", t1);
        return 1;
    }

    // 两次调用之间应该有合理的间隔
    if (t2 <= t1) {
        printf("time not increasing: t1=%lld t2=%lld\\n", t1, t2);
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
                print("  ✅ 微秒级时间获取测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestTimeStruct(unittest.TestCase):
    """时间结构转换测试"""

    def test_timestamp_struct_conversion(self):
        """测试时间戳与时间结构互转"""
        print("\n📝 测试时间戳与时间结构互转")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main() {
    // 测试已知的固定时间戳: 2026-04-09 00:00:00 UTC
    zhc_timestamp_t ts = 1775664000LL;

    // 时间戳 -> 结构
    zhc_tm_t tm;
    zhc_time_to_struct(ts, &tm);

    // 验证各字段
    if (tm.year != 2026) {
        printf("year mismatch: %d\\n", tm.year);
        return 1;
    }
    if (tm.month != 4) {
        printf("month mismatch: %d\\n", tm.month);
        return 1;
    }
    if (tm.day != 9) {
        printf("day mismatch: %d\\n", tm.day);
        return 1;
    }

    // 结构 -> 时间戳
    zhc_timestamp_t ts2 = zhc_struct_to_time(&tm);
    if (ts2 != ts) {
        printf("round-trip failed: %lld -> %lld\\n", ts, ts2);
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
                print("  ✅ 时间戳与时间结构互转测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestTimeFormat(unittest.TestCase):
    """时间格式化测试"""

    def test_time_format(self):
        """测试时间格式化"""
        print("\n📝 测试时间格式化")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 2026-04-09 12:30:45
    zhc_tm_t tm = {
        .sec = 45,
        .min = 30,
        .hour = 12,
        .day = 9,
        .month = 4,
        .year = 2026,
        .wday = 4,  // Thursday
        .yday = 99,
        .isdst = 0
    };

    char buf[100];

    // 测试 Y-m-d H:M:S 格式
    int len = zhc_time_format(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm);
    if (strcmp(buf, "2026-04-09 12:30:45") != 0) {
        printf("format 1 failed: %s\\n", buf);
        return 1;
    }

    // 测试中文格式
    len = zhc_time_format(buf, sizeof(buf), "%Y年%m月%d日 %H:%M:%S", &tm);
    if (strcmp(buf, "2026年04月09日 12:30:45") != 0) {
        printf("format 2 failed: %s\\n", buf);
        return 1;
    }

    // 测试时分秒
    len = zhc_time_format(buf, sizeof(buf), "%H:%M:%S", &tm);
    if (strcmp(buf, "12:30:45") != 0) {
        printf("format 3 failed: %s\\n", buf);
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
                print("  ✅ 时间格式化测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_time_parse(self):
        """测试时间解析"""
        print("\n📝 测试时间解析")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 解析标准格式
    zhc_tm_t tm;
    zhc_timestamp_t ts = zhc_time_parse("2026-04-09 12:30:45", "%Y-%m-%d %H:%M:%S", &tm);

    if (ts < 0) {
        printf("parse failed\\n");
        return 1;
    }

    if (tm.year != 2026 || tm.month != 4 || tm.day != 9) {
        printf("date mismatch: %d-%d-%d\\n", tm.year, tm.month, tm.day);
        return 1;
    }

    if (tm.hour != 12 || tm.min != 30 || tm.sec != 45) {
        printf("time mismatch: %d:%d:%d\\n", tm.hour, tm.min, tm.sec);
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
                print("  ✅ 时间解析测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestTimeCalculation(unittest.TestCase):
    """时间计算测试"""

    def test_time_diff(self):
        """测试时间差计算"""
        print("\n📝 测试时间差计算")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <math.h>

int main() {
    zhc_timestamp_t t1 = 1000;
    zhc_timestamp_t t2 = 1060;

    double diff = zhc_time_diff(t2, t1);
    if (fabs(diff - 60.0) > 1e-9) {
        printf("diff failed: %f (expected 60)\\n", diff);
        return 1;
    }

    // 负数差
    diff = zhc_time_diff(t1, t2);
    if (fabs(diff + 60.0) > 1e-9) {
        printf("diff negative failed: %f\\n", diff);
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
                print("  ✅ 时间差计算测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_time_add(self):
        """测试时间加法"""
        print("\n📝 测试时间加法")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>

int main() {
    zhc_timestamp_t base = 1000000;  // 1970-01-12 13:46:40

    // 加秒
    if (zhc_time_add_seconds(base, 60) != 1000060) {
        printf("add_seconds failed\\n");
        return 1;
    }

    // 加分
    if (zhc_time_add_minutes(base, 5) != 1000300) {
        printf("add_minutes failed\\n");
        return 1;
    }

    // 加时
    if (zhc_time_add_hours(base, 2) != 1007200) {
        printf("add_hours failed\\n");
        return 1;
    }

    // 加天
    if (zhc_time_add_days(base, 1) != 1086400) {
        printf("add_days failed\\n");
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
                print("  ✅ 时间加法测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_leap_year(self):
        """测试闰年判断"""
        print("\n📝 测试闰年判断")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>

int main() {
    // 闰年
    if (!zhc_is_leap_year(2020)) { printf("2020 should be leap\\n"); return 1; }
    if (!zhc_is_leap_year(2024)) { printf("2024 should be leap\\n"); return 1; }
    if (!zhc_is_leap_year(2028)) { printf("2028 should be leap\\n"); return 1; }
    if (!zhc_is_leap_year(2000)) { printf("2000 should be leap\\n"); return 1; }

    // 平年
    if (zhc_is_leap_year(2021)) { printf("2021 should not be leap\\n"); return 1; }
    if (zhc_is_leap_year(2022)) { printf("2022 should not be leap\\n"); return 1; }
    if (zhc_is_leap_year(1900)) { printf("1900 should not be leap\\n"); return 1; }

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
                print("  ✅ 闰年判断测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_days_in_month(self):
        """测试月份天数"""
        print("\n📝 测试月份天数")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>

int main() {
    // 普通月份
    if (zhc_days_in_month(2026, 1) != 31) { printf("Jan failed\\n"); return 1; }
    if (zhc_days_in_month(2026, 2) != 28) { printf("Feb failed\\n"); return 1; }
    if (zhc_days_in_month(2026, 3) != 31) { printf("Mar failed\\n"); return 1; }
    if (zhc_days_in_month(2026, 4) != 30) { printf("Apr failed\\n"); return 1; }

    // 闰年2月
    if (zhc_days_in_month(2024, 2) != 29) { printf("Feb leap failed\\n"); return 1; }

    // 无效输入
    if (zhc_days_in_month(2026, 0) != 0) { printf("month 0 failed\\n"); return 1; }
    if (zhc_days_in_month(2026, 13) != 0) { printf("month 13 failed\\n"); return 1; }

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
                print("  ✅ 月份天数测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestTimer(unittest.TestCase):
    """计时器测试"""

    def test_timer_basic(self):
        """测试计时器基本功能"""
        print("\n📝 测试计时器基本功能")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <math.h>

int main() {
    zhc_timer_t timer = zhc_timer_start();

    // 短暂延时
    volatile int sum = 0;
    for (int i = 0; i < 10000; i++) sum += i;

    // 获取已用时间
    double elapsed = zhc_timer_elapsed(&timer);
    if (elapsed < 0.0) {
        printf("elapsed negative: %f\\n", elapsed);
        return 1;
    }

    // 结束计时
    double total = zhc_timer_end(&timer);
    if (total < 0.0) {
        printf("total negative: %f\\n", total);
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
                print("  ✅ 计时器基本功能测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_timer_reset(self):
        """测试计时器重置"""
        print("\n📝 测试计时器重置")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>

int main() {
    zhc_timer_t timer = zhc_timer_start();

    // 短暂延时
    volatile int sum = 0;
    for (int i = 0; i < 10000; i++) sum += i;

    double elapsed1 = zhc_timer_elapsed(&timer);

    // 重置
    zhc_timer_reset(&timer);

    double elapsed2 = zhc_timer_elapsed(&timer);

    // 重置后 elapsed 应该接近 0
    if (elapsed2 > 0.01) {
        printf("reset failed: %f\\n", elapsed2);
        return 1;
    }

    // 重置前的时间应该大于重置后
    if (elapsed1 <= elapsed2) {
        printf("timing order wrong\\n");
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
                print("  ✅ 计时器重置测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestSleep(unittest.TestCase):
    """延时测试"""

    def test_sleep_ms(self):
        """测试毫秒延时"""
        print("\n📝 测试毫秒延时")

        code = """
#define ZHC_TIME_IMPLEMENTATION
#include "zhc_time.h"
#include <stdio.h>
#include <math.h>

int main() {
    zhc_timer_t timer = zhc_timer_start();

    // 延时 50ms
    zhc_sleep_ms(50);

    double elapsed = zhc_timer_elapsed(&timer);

    // 延时应该在 40ms 到 200ms 之间
    if (elapsed < 0.04) {
        printf("sleep too short: %f\\n", elapsed);
        return 1;
    }
    if (elapsed > 0.2) {
        printf("sleep too long: %f\\n", elapsed);
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
                print("  ✅ 毫秒延时测试通过")
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
    print("时间库测试")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestTimeGetting))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeStruct))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestTimer))
    suite.addTests(loader.loadTestsFromTestCase(TestSleep))

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
