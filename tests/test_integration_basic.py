#!/usr/bin/env python3
"""
集成测试套件：基础功能端到端测试

使用pytest框架重新实现test_suite1-6的集成测试
这些测试验证完整的编译流程：源码 → LLVM IR 生成

注意：CLI 已从直接编译模式改为子命令模式（zhc compile），
输出格式也从 C 代码变为 LLVM IR（.ll 文件）。
"""

import subprocess
import sys
import os
import pytest
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 确保子进程使用与当前相同的 Python 解释器
_PYTHON = sys.executable

# 使用 python -m zhc compile 作为编译器入口（CLI 子命令模式）
ZHC_CMD = [_PYTHON, "-m", "zhc", "compile"]


def _run_zhc_compile(zhc_code: str, tmp_path, test_name: str) -> tuple:
    """
    统一的编译运行函数：
    写入 .zhc 源码 → 调用 zhc compile → 检查 .ll 输出 → 返回 (成功, 内容)
    """
    # 写入中文源码
    zhc_file = tmp_path / f"{test_name}.zhc"
    zhc_file.write_text(zhc_code, encoding="utf-8")

    # 输出目录（CLI compile 命令将 .ll 文件输出到此目录）
    out_dir = tmp_path / "output"

    # 运行编译器：使用 zhc compile 子命令
    cmd = ZHC_CMD + [str(zhc_file), "-o", str(out_dir)]
    env = os.environ.copy()
    src_path = str(PROJECT_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{src_path}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = src_path

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env
    )

    if result.returncode != 0:
        return False, f"编译失败: {result.stderr}\n{result.stdout}"

    # 检查生成的 LLVM IR 文件
    ll_files = list(out_dir.rglob("*.ll"))
    if not ll_files:
        return False, f"未生成LLVM IR文件，stdout: {result.stdout[:500]}"

    ir_content = ll_files[0].read_text()
    return True, ir_content


class TestBasicTypes:
    """测试套件1：基础类型"""

    def test_int_basic(self, tmp_path):
        """测试整数型基础"""
        success, output = _run_zhc_compile(
            """
整数型 主函数() {
    整数型 x = 42;
    返回 0;
}
""",
            tmp_path,
            "int_basic",
        )
        assert success, output
        assert "i32" in output

    @pytest.mark.xfail(
        reason="已知后端Bug: char类型变量存储时类型不匹配(i32→i8*) — TypeError: cannot store i32 to i8*"
    )
    def test_char_type(self, tmp_path):
        """测试字符型"""
        success, output = _run_zhc_compile(
            """
字符型 主函数() {
    字符型 c = 65;
    返回 c - 65;
}
""",
            tmp_path,
            "char_type",
        )
        assert success, output
        assert "i8" in output or "i32" in output

    @pytest.mark.xfail(
        reason="已知后端Bug: float类型处理异常 — 编译器后端未完全支持float字面量"
    )
    def test_float_type(self, tmp_path):
        """测试浮点型"""
        success, output = _run_zhc_compile(
            """
浮点型 主函数() {
    浮点型 f = 3.14f;
    返回 0.0f;
}
""",
            tmp_path,
            "float_type",
        )
        assert success, output
        assert "float" in output.lower()

    @pytest.mark.xfail(
        reason="已知后端Bug: double类型处理异常 — 编译器后端未完全支持double字面量"
    )
    def test_double_type(self, tmp_path):
        """测试双精度浮点型"""
        success, output = _run_zhc_compile(
            """
双精度浮点型 主函数() {
    双精度浮点型 d = 3.14159;
    返回 0.0;
}
""",
            tmp_path,
            "double_type",
        )
        assert success, output
        assert "double" in output

    @pytest.mark.xfail(reason="已知后端Bug: 数组初始化列表语法处理异常")
    def test_array_basic(self, tmp_path):
        """测试数组基础"""
        success, output = _run_zhc_compile(
            """
整数型 主函数() {
    整数型 arr[5] = {1, 2, 3, 4, 5};
    返回 arr[0];
}
""",
            tmp_path,
            "array_basic",
        )
        assert success, output


class TestControlFlow:
    """测试套件2：流程控制"""

    def test_if_else(self, tmp_path):
        """测试if-else语句"""
        success, output = _run_zhc_compile(
            """
整数型 主函数() {
    整数型 x = 10;
    如果 (x > 5) {
        返回 1;
    } 否则 {
        返回 0;
    }
}
""",
            tmp_path,
            "if_else",
        )
        assert success, output
        assert "br" in output or "icmp" in output

    def test_while_loop(self, tmp_path):
        """测试while循环"""
        success, output = _run_zhc_compile(
            """
整数型 主函数() {
    整数型 i = 0;
    当 (i < 10) {
        i = i + 1;
    }
    返回 i;
}
""",
            tmp_path,
            "while_loop",
        )
        assert success, output
        assert "br label" in output or "br\tlabel" in output

    def test_for_loop(self, tmp_path):
        """测试for循环"""
        success, output = _run_zhc_compile(
            """
整数型 主函数() {
    整数型 总和 = 0;
    循环 (整数型 i = 0; i < 10; i = i + 1) {
        总和 = 总和 + i;
    }
    返回 总和;
}
""",
            tmp_path,
            "for_loop",
        )
        assert success, output


class TestFunctions:
    """测试套件3：函数"""

    @pytest.mark.xfail(reason="已知后端Bug: 多函数定义时后端处理异常")
    def test_function_definition(self, tmp_path):
        """测试函数定义"""
        success, output = _run_zhc_compile(
            """
整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}

整数型 主函数() {
    整数型 结果 = 加法(3, 5);
    返回 结果;
}
""",
            tmp_path,
            "func_def",
        )
        assert success, output
        assert "define" in output

    def test_void_function(self, tmp_path):
        """测试无返回值函数"""
        success, output = _run_zhc_compile(
            """
空型 打招呼() {
    返回;
}

整数型 主函数() {
    打招呼();
    返回 0;
}
""",
            tmp_path,
            "void_func",
        )
        assert success, output
        assert "define" in output


class TestAdvancedFeatures:
    """测试套件4：高级特性"""

    def test_pointer(self, tmp_path):
        """测试指针"""
        success, output = _run_zhc_compile(
            """
整数型 主函数() {
    整数型 x = 42;
    整数型* ptr = &x;
    返回 *ptr;
}
""",
            tmp_path,
            "pointer",
        )
        assert success, output

    @pytest.mark.xfail(reason="已知后端Bug: 结构体字段访问/赋值时类型不匹配")
    def test_struct(self, tmp_path):
        """测试结构体"""
        success, output = _run_zhc_compile(
            """
结构体 点 {
    整数型 x;
    整数型 y;
};

整数型 主函数() {
    结构体 点 p;
    p.x = 10;
    p.y = 20;
    返回 p.x + p.y;
}
""",
            tmp_path,
            "struct",
        )
        assert success, output
        assert "%" in output or "{" in output


if __name__ == "__main__":
    """直接运行此文件进行测试"""
    pytest.main([__file__, "-v", "--tb=short"])
