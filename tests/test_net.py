#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_net.py - 网络库测试套件

测试 zhc_net.h 中的网络函数：
- URL 解析
- DNS 解析
- TCP/UDP Socket 基本操作
- HTTP 客户端

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


class TestURLParsing(unittest.TestCase):
    """URL 解析测试"""

    def test_url_parse_basic(self):
        """测试基本 URL 解析"""
        print("\n📝 测试 URL 解析")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    zhc_url_t url;

    // 测试 HTTP URL
    if (zhc_url_parse("http://example.com/path", &url) != 0) {
        printf("parse failed\\n");
        return 1;
    }

    if (strcmp(url.protocol, "http") != 0) {
        printf("protocol failed: %s\\n", url.protocol);
        return 1;
    }

    if (strcmp(url.host, "example.com") != 0) {
        printf("host failed: %s\\n", url.host);
        return 1;
    }

    if (url.port != 80) {
        printf("port failed: %d\\n", url.port);
        return 1;
    }

    if (strcmp(url.path, "/path") != 0) {
        printf("path failed: %s\\n", url.path);
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
                print("  ✅ URL 解析测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_url_parse_with_port(self):
        """测试带端口的 URL 解析"""
        print("\n📝 测试带端口的 URL 解析")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    zhc_url_t url;

    if (zhc_url_parse("http://example.com:8080/path/to/page", &url) != 0) {
        printf("parse failed\\n");
        return 1;
    }

    if (url.port != 8080) {
        printf("port failed: %d\\n", url.port);
        return 1;
    }

    if (strcmp(url.path, "/path/to/page") != 0) {
        printf("path failed: %s\\n", url.path);
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
                print("  ✅ 带端口 URL 解析测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_url_parse_https(self):
        """测试 HTTPS URL"""
        print("\n📝 测试 HTTPS URL")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    zhc_url_t url;

    if (zhc_url_parse("https://api.example.com:443/v1/users", &url) != 0) {
        printf("parse failed\\n");
        return 1;
    }

    if (strcmp(url.protocol, "https") != 0) {
        printf("protocol failed: %s\\n", url.protocol);
        return 1;
    }

    if (strcmp(url.host, "api.example.com") != 0) {
        printf("host failed: %s\\n", url.host);
        return 1;
    }

    if (url.port != 443) {
        printf("port failed: %d\\n", url.port);
        return 1;
    }

    if (strcmp(url.path, "/v1/users") != 0) {
        printf("path failed: %s\\n", url.path);
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
                print("  ✅ HTTPS URL 解析测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestDNS(unittest.TestCase):
    """DNS 解析测试"""

    def test_get_local_ip(self):
        """测试获取本地 IP"""
        print("\n📝 测试获取本地 IP")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    const char* ip = zhc_get_local_ip();
    if (ip == NULL) {
        printf("get_local_ip failed\\n");
        return 1;
    }

    // 验证格式（简单检查）
    if (strlen(ip) < 7) {
        printf("ip too short: %s\\n", ip);
        return 1;
    }

    printf("local ip: %s\\n", ip);
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
                print("  ✅ 获取本地 IP 测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_resolve_host(self):
        """测试 DNS 解析"""
        print("\n📝 测试 DNS 解析")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 解析 localhost
    const char* ip = zhc_resolve_host("localhost");
    if (ip == NULL) {
        printf("resolve localhost failed\\n");
        return 1;
    }

    printf("localhost -> %s\\n", ip);

    // 解析一个已知的域名
    ip = zhc_resolve_host("example.com");
    if (ip == NULL) {
        printf("resolve example.com failed\\n");
        return 1;
    }

    printf("example.com -> %s\\n", ip);

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
                print("  ✅ DNS 解析测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestTCPSocket(unittest.TestCase):
    """TCP Socket 测试"""

    def test_tcp_socket_create_close(self):
        """测试 TCP 套接字创建和关闭"""
        print("\n📝 测试 TCP 套接字创建和关闭")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>

int main() {
    // 创建套接字
    int sock = zhc_tcp_socket();
    if (sock < 0) {
        printf("socket failed\\n");
        return 1;
    }

    printf("created socket: %d\\n", sock);

    // 关闭套接字
    if (zhc_tcp_close(sock) != 0) {
        printf("close failed\\n");
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
                print("  ✅ TCP 套接字创建和关闭测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_tcp_server(self):
        """测试 TCP 服务器基本操作"""
        print("\n📝 测试 TCP 服务器")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 创建套接字
    int sock = zhc_tcp_socket();
    if (sock < 0) {
        printf("socket failed\\n");
        return 1;
    }

    // 绑定端口
    if (zhc_tcp_bind(sock, 0) != 0) {
        printf("bind failed\\n");
        zhc_tcp_close(sock);
        return 1;
    }

    // 监听
    if (zhc_tcp_listen(sock, 5) != 0) {
        printf("listen failed\\n");
        zhc_tcp_close(sock);
        return 1;
    }

    printf("server ready on socket %d\\n", sock);

    zhc_tcp_close(sock);
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
                print("  ✅ TCP 服务器测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestUDPSocket(unittest.TestCase):
    """UDP Socket 测试"""

    def test_udp_socket_create_close(self):
        """测试 UDP 套接字创建和关闭"""
        print("\n📝 测试 UDP 套接字创建和关闭")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>

int main() {
    int sock = zhc_udp_socket();
    if (sock < 0) {
        printf("socket failed\\n");
        return 1;
    }

    printf("created UDP socket: %d\\n", sock);

    if (zhc_udp_close(sock) != 0) {
        printf("close failed\\n");
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
                print("  ✅ UDP 套接字测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)


class TestHTTP(unittest.TestCase):
    """HTTP 客户端测试"""

    def test_http_get(self):
        """测试 HTTP GET 请求"""
        print("\n📝 测试 HTTP GET")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    // 使用 httpbin.org 的测试接口
    zhc_http_response_t* resp = zhc_http_get("http://httpbin.org/get");
    if (resp == NULL) {
        printf("http_get failed\\n");
        return 1;
    }

    printf("status_code: %d\\n", resp->status_code);

    if (resp->status_code != 200) {
        printf("unexpected status: %d\\n", resp->status_code);
        zhc_http_response_free(resp);
        return 1;
    }

    if (resp->content == NULL || resp->content_length == 0) {
        printf("no content\\n");
        zhc_http_response_free(resp);
        return 1;
    }

    printf("content_length: %d\\n", resp->content_length);

    zhc_http_response_free(resp);
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
                timeout=15,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if "OK" in result.stdout:
                print("  ✅ HTTP GET 测试通过")
            else:
                print(f"  ❌ 运行失败: {result.stdout}")
                self.fail("运行失败")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            exe_file = temp_file.replace(".c", "")
            if os.path.exists(exe_file):
                os.remove(exe_file)

    def test_http_post(self):
        """测试 HTTP POST 请求"""
        print("\n📝 测试 HTTP POST")

        code = """
#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    zhc_http_response_t* resp = zhc_http_post(
        "http://httpbin.org/post",
        "name=test&value=123",
        "application/x-www-form-urlencoded"
    );

    if (resp == NULL) {
        printf("http_post failed\\n");
        return 1;
    }

    printf("status_code: %d\\n", resp->status_code);

    if (resp->status_code != 200) {
        printf("unexpected status: %d\\n", resp->status_code);
        zhc_http_response_free(resp);
        return 1;
    }

    // 检查响应内容
    if (strstr(resp->content, "test") == NULL) {
        printf("content doesn't echo our data\\n");
        zhc_http_response_free(resp);
        return 1;
    }

    zhc_http_response_free(resp);
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
                timeout=15,
            )

            if result.returncode != 0:
                print(f"  ❌ 编译失败: {result.stderr}")
                self.fail("编译失败")

            result = subprocess.run(
                [temp_file.replace(".c", "")],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if "OK" in result.stdout:
                print("  ✅ HTTP POST 测试通过")
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
    print("网络库测试")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestURLParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestDNS))
    suite.addTests(loader.loadTestsFromTestCase(TestTCPSocket))
    suite.addTests(loader.loadTestsFromTestCase(TestUDPSocket))
    suite.addTests(loader.loadTestsFromTestCase(TestHTTP))

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
