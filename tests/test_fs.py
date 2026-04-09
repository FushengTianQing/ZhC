#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_fs.py - 文件系统库测试套件

测试 zhc_fs.h 中的文件系统函数：
- 目录操作
- 文件属性
- 文件操作
- 路径处理

版本: 1.0
作者: ZHC编译器团队
"""

import unittest
import subprocess
import tempfile
import os
import sys
import shutil

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestDirectoryOperations(unittest.TestCase):
    """目录操作测试"""

    def test_mkdir(self):
        """测试创建目录"""
        print("\n📝 测试创建目录")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    const char* test_dir = "/tmp/zhc_fs_test_dir";

    // 清理可能存在的旧目录
    zhc_rmdir_recursive(test_dir);

    // 创建目录
    if (zhc_mkdir(test_dir, 0755) != 0) {
        printf("mkdir failed\\n");
        return 1;
    }

    // 验证目录存在
    if (!zhc_is_directory(test_dir)) {
        printf("not a directory\\n");
        zhc_rmdir(test_dir);
        return 1;
    }

    // 清理
    if (zhc_rmdir(test_dir) != 0) {
        printf("cleanup failed\\n");
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
                print("  ✅ 创建目录测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            if os.path.exists("/tmp/zhc_fs_test_dir"):
                shutil.rmtree("/tmp/zhc_fs_test_dir")

    def test_mkdir_recursive(self):
        """测试创建多级目录"""
        print("\n📝 测试创建多级目录")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>

int main() {
    const char* test_dir = "/tmp/zhc_fs_test/sub/dir";

    // 清理
    zhc_rmdir_recursive("/tmp/zhc_fs_test");

    // 创建多级目录
    if (zhc_mkdir_recursive(test_dir, 0755) != 0) {
        printf("mkdir_recursive failed\\n");
        return 1;
    }

    // 验证
    if (!zhc_is_directory(test_dir)) {
        printf("not created correctly\\n");
        return 1;
    }

    // 清理
    zhc_rmdir_recursive("/tmp/zhc_fs_test");

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
                print("  ✅ 创建多级目录测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            if os.path.exists("/tmp/zhc_fs_test"):
                shutil.rmtree("/tmp/zhc_fs_test")

    def test_dir_read(self):
        """测试目录遍历"""
        print("\n📝 测试目录遍历")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 创建测试目录
    const char* test_dir = "/tmp/zhc_fs_read_test";
    zhc_rmdir_recursive(test_dir);
    zhc_mkdir(test_dir, 0755);

    // 创建测试文件
    FILE* f = fopen("/tmp/zhc_fs_read_test/file1.txt", "w");
    if (f) fclose(f);
    f = fopen("/tmp/zhc_fs_read_test/file2.txt", "w");
    if (f) fclose(f);

    // 创建子目录
    zhc_mkdir("/tmp/zhc_fs_read_test/subdir", 0755);

    // 打开目录
    void* dir = zhc_opendir(test_dir);
    if (!dir) {
        printf("opendir failed\\n");
        zhc_rmdir_recursive(test_dir);
        return 1;
    }

    // 统计条目
    int count = 0;
    zhc_dirent_t entry;
    while (zhc_readdir(dir, &entry) == 0) {
        count++;
    }
    zhc_closedir(dir);

    // 应该有 5 个条目: ., .., file1.txt, file2.txt, subdir
    if (count != 5) {
        printf("expected 5 entries, got %d\\n", count);
        zhc_rmdir_recursive(test_dir);
        return 1;
    }

    // 清理
    zhc_rmdir_recursive(test_dir);

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
                print("  ✅ 目录遍历测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            if os.path.exists("/tmp/zhc_fs_read_test"):
                shutil.rmtree("/tmp/zhc_fs_read_test")

    def test_getcwd_chdir(self):
        """测试获取和切换目录"""
        print("\n📝 测试获取和切换目录")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    char buf[256];
    char buf2[256];

    // 获取当前目录
    if (zhc_getcwd(buf, sizeof(buf)) == NULL) {
        printf("getcwd failed\\n");
        return 1;
    }

    // 切换到 /tmp（macOS 上可能是 /private/tmp）
    if (zhc_chdir("/tmp") != 0) {
        printf("chdir to /tmp failed\\n");
        return 1;
    }

    // 验证切换成功
    if (zhc_getcwd(buf2, sizeof(buf2)) == NULL) {
        printf("getcwd after chdir failed\\n");
        return 1;
    }

    // 检查是否在 tmp 目录下
    if (strstr(buf2, "tmp") == NULL) {
        printf("chdir didn't work: %s\\n", buf2);
        return 1;
    }

    // 恢复原目录
    zhc_chdir(buf);

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
                print("  ✅ 获取和切换目录测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestFileOperations(unittest.TestCase):
    """文件操作测试"""

    def test_file_stat(self):
        """测试文件属性获取"""
        print("\n📝 测试文件属性获取")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 创建测试文件
    FILE* f = fopen("/tmp/zhc_fs_stat_test.txt", "w");
    if (!f) {
        printf("create file failed\\n");
        return 1;
    }
    const char* content = "Hello, World!";
    fwrite(content, 1, strlen(content), f);
    fclose(f);

    // 检查文件存在
    if (!zhc_file_exists("/tmp/zhc_fs_stat_test.txt")) {
        printf("file not exists\\n");
        return 1;
    }

    // 检查是普通文件
    if (!zhc_is_regular_file("/tmp/zhc_fs_stat_test.txt")) {
        printf("not a regular file\\n");
        return 1;
    }

    // 检查不是目录
    if (zhc_is_directory("/tmp/zhc_fs_stat_test.txt")) {
        printf("is a directory\\n");
        return 1;
    }

    // 获取文件大小
    long long size = zhc_file_size("/tmp/zhc_fs_stat_test.txt");
    if (size != 13) {
        printf("wrong size: %lld\\n", size);
        return 1;
    }

    // 获取详细状态
    zhc_file_stat_t stat;
    if (zhc_stat("/tmp/zhc_fs_stat_test.txt", &stat) != 0) {
        printf("stat failed\\n");
        return 1;
    }

    if (stat.size != 13) {
        printf("stat size wrong: %lld\\n", stat.size);
        return 1;
    }

    // 清理
    zhc_unlink("/tmp/zhc_fs_stat_test.txt");

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
                print("  ✅ 文件属性获取测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            if os.path.exists("/tmp/zhc_fs_stat_test.txt"):
                os.remove("/tmp/zhc_fs_stat_test.txt")

    def test_rename_unlink(self):
        """测试重命名和删除"""
        print("\n📝 测试重命名和删除")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>

int main() {
    // 创建测试文件
    FILE* f = fopen("/tmp/zhc_fs_old.txt", "w");
    if (!f) {
        printf("create file failed\\n");
        return 1;
    }
    fprintf(f, "test content");
    fclose(f);

    // 重命名
    if (zhc_rename("/tmp/zhc_fs_old.txt", "/tmp/zhc_fs_new.txt") != 0) {
        printf("rename failed\\n");
        return 1;
    }

    // 验证旧文件不存在
    if (zhc_file_exists("/tmp/zhc_fs_old.txt")) {
        printf("old file still exists\\n");
        return 1;
    }

    // 验证新文件存在
    if (!zhc_file_exists("/tmp/zhc_fs_new.txt")) {
        printf("new file not exists\\n");
        return 1;
    }

    // 删除
    if (zhc_unlink("/tmp/zhc_fs_new.txt") != 0) {
        printf("unlink failed\\n");
        return 1;
    }

    // 验证删除成功
    if (zhc_file_exists("/tmp/zhc_fs_new.txt")) {
        printf("file still exists after unlink\\n");
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
                print("  ✅ 重命名和删除测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            for f in ["/tmp/zhc_fs_old.txt", "/tmp/zhc_fs_new.txt"]:
                if os.path.exists(f):
                    os.remove(f)

    def test_copyfile(self):
        """测试文件复制"""
        print("\n📝 测试文件复制")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 创建源文件
    FILE* f = fopen("/tmp/zhc_fs_src.txt", "w");
    if (!f) {
        printf("create src failed\\n");
        return 1;
    }
    fprintf(f, "test content for copy");
    fclose(f);

    // 复制
    if (zhc_copyfile("/tmp/zhc_fs_src.txt", "/tmp/zhc_fs_dst.txt") != 0) {
        printf("copy failed\\n");
        return 1;
    }

    // 验证目标文件存在
    if (!zhc_file_exists("/tmp/zhc_fs_dst.txt")) {
        printf("dst not exists\\n");
        return 1;
    }

    // 验证大小相同
    if (zhc_file_size("/tmp/zhc_fs_src.txt") != zhc_file_size("/tmp/zhc_fs_dst.txt")) {
        printf("size mismatch\\n");
        return 1;
    }

    // 清理
    zhc_unlink("/tmp/zhc_fs_src.txt");
    zhc_unlink("/tmp/zhc_fs_dst.txt");

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
                print("  ✅ 文件复制测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            for f in ["/tmp/zhc_fs_src.txt", "/tmp/zhc_fs_dst.txt"]:
                if os.path.exists(f):
                    os.remove(f)


class TestPathOperations(unittest.TestCase):
    """路径处理测试"""

    def test_path_join(self):
        """测试路径拼接"""
        print("\n📝 测试路径拼接")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    char buf[256];

    // 测试基本拼接
    if (zhc_path_join(buf, sizeof(buf), "/home", "user", "data", NULL) != 0) {
        printf("join failed\\n");
        return 1;
    }

    if (strcmp(buf, "/home/user/data") != 0) {
        printf("wrong result: %s\\n", buf);
        return 1;
    }

    // 测试单部分
    if (zhc_path_join(buf, sizeof(buf), "/home", NULL) != 0) {
        printf("join single failed\\n");
        return 1;
    }

    if (strcmp(buf, "/home") != 0) {
        printf("wrong single: %s\\n", buf);
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
                print("  ✅ 路径拼接测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_path_dirname_basename(self):
        """测试目录名和文件名"""
        print("\n📝 测试目录名和文件名")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    char buf[256];

    // 测试目录名
    zhc_path_dirname("/home/user/file.txt", buf, sizeof(buf));
    if (strcmp(buf, "/home/user") != 0) {
        printf("dirname failed: %s\\n", buf);
        return 1;
    }

    // 测试文件名
    zhc_path_basename("/home/user/file.txt", buf, sizeof(buf));
    if (strcmp(buf, "file.txt") != 0) {
        printf("basename failed: %s\\n", buf);
        return 1;
    }

    // 测试根目录
    zhc_path_dirname("/file.txt", buf, sizeof(buf));
    if (strcmp(buf, "/") != 0) {
        printf("root dirname failed: %s\\n", buf);
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
                print("  ✅ 目录名和文件名测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_path_extname(self):
        """测试扩展名"""
        print("\n📝 测试扩展名")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 测试有扩展名
    if (strcmp(zhc_path_extname("/path/to/file.txt"), ".txt") != 0) {
        printf("ext .txt failed\\n");
        return 1;
    }

    // 测试无扩展名
    if (strcmp(zhc_path_extname("/path/to/file"), "") != 0) {
        printf("ext none failed\\n");
        return 1;
    }

    // 测试多层扩展名
    if (strcmp(zhc_path_extname("/path/to/file.tar.gz"), ".gz") != 0) {
        printf("ext .tar.gz failed\\n");
        return 1;
    }

    // 测试去除扩展名
    char buf[256];
    zhc_path_remove_ext("/path/to/file.txt", buf, sizeof(buf));
    if (strcmp(buf, "/path/to/file") != 0) {
        printf("remove_ext failed: %s\\n", buf);
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
                print("  ✅ 扩展名测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_path_is_absolute(self):
        """测试绝对路径判断"""
        print("\n📝 测试绝对路径判断")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>

int main() {
    // 绝对路径
    if (!zhc_path_is_absolute("/home/user")) {
        printf("/home/user should be absolute\\n");
        return 1;
    }

    // 相对路径
    if (zhc_path_is_absolute("home/user")) {
        printf("home/user should be relative\\n");
        return 1;
    }

    if (zhc_path_is_absolute("./file")) {
        printf("./file should be relative\\n");
        return 1;
    }

    if (zhc_path_is_absolute("../file")) {
        printf("../file should be relative\\n");
        return 1;
    }

    // 空指针
    if (zhc_path_is_absolute(NULL)) {
        printf("NULL should be relative\\n");
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
                print("  ✅ 绝对路径判断测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestSymlink(unittest.TestCase):
    """符号链接测试"""

    def test_symlink_operations(self):
        """测试符号链接创建和读取"""
        print("\n📝 测试符号链接")

        code = """
#define ZHC_FS_IMPLEMENTATION
#include "zhc_fs.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 创建测试文件
    FILE* f = fopen("/tmp/zhc_fs_target.txt", "w");
    if (!f) {
        printf("create target failed\\n");
        return 1;
    }
    fprintf(f, "target content");
    fclose(f);

    // 创建符号链接
    if (zhc_symlink("/tmp/zhc_fs_target.txt", "/tmp/zhc_fs_link.txt") != 0) {
        printf("symlink failed\\n");
        return 1;
    }

    // 验证链接存在
    if (!zhc_file_exists("/tmp/zhc_fs_link.txt")) {
        printf("link not exists\\n");
        return 1;
    }

    // 读取符号链接
    char buf[256];
    int len = zhc_readlink("/tmp/zhc_fs_link.txt", buf, sizeof(buf));
    if (len <= 0) {
        printf("readlink failed\\n");
        return 1;
    }
    buf[len] = '\\0';

    if (strcmp(buf, "/tmp/zhc_fs_target.txt") != 0) {
        printf("wrong link content: %s\\n", buf);
        return 1;
    }

    // 清理
    zhc_unlink("/tmp/zhc_fs_target.txt");
    zhc_unlink("/tmp/zhc_fs_link.txt");

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
                print("  ✅ 符号链接测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)
            for f in ["/tmp/zhc_fs_target.txt", "/tmp/zhc_fs_link.txt"]:
                if os.path.exists(f):
                    os.remove(f)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("文件系统库测试")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestDirectoryOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestPathOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestSymlink))

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
