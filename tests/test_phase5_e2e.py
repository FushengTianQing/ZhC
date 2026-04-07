"""
Phase 5 端到端测试
通过子进程调用 python -m src.__main__，验证完整的编译流程
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def run_compiler(code: str, extra_args=None):
    """运行编译器，返回 (returncode, stdout, stderr)"""
    with tempfile.NamedTemporaryFile(suffix='.zhc', mode='w', delete=False,
                                     encoding='utf-8') as f:
        f.write(code)
        f.flush()
        tmp_file = f.name

    cmd = [sys.executable, "-m", "src.__main__", tmp_file]
    if extra_args:
        cmd.extend(extra_args)

    env = {**__import__('os').environ, 'PYTHONPATH': str(PROJECT_ROOT / 'src')}
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT,
                           env=env, timeout=10)

    Path(tmp_file).unlink(missing_ok=True)
    return result.returncode, result.stdout, result.stderr


class TestE2EErrorDetection(unittest.TestCase):
    """端到端错误检测测试"""

    def test_valid_code_compiles(self):
        """有效代码应编译成功"""
        code = '整数型 主函数() { 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        self.assertEqual(rc, 0, f"Valid code should compile. stdout: {stdout}, stderr: {stderr}")

    def test_duplicate_var_reports_error(self):
        """重复变量定义应报错"""
        code = '整数型 主函数() { 整数型 x = 1; 整数型 x = 2; 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertNotEqual(rc, 0, "Duplicate var should fail")
        self.assertIn("重复定义", output)

    def test_undefined_symbol_reports_error(self):
        """未定义符号应报错"""
        code = '整数型 主函数() { 整数型 y = 不存在; 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertNotEqual(rc, 0, "Undefined symbol should fail")
        self.assertIn("未定义", output)

    def test_break_outside_loop_reports_error(self):
        """循环外 break 应报错"""
        code = '整数型 主函数() { 跳出; 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertNotEqual(rc, 0, "break outside loop should fail")
        self.assertIn("非法跳出", output)

    def test_error_includes_filename(self):
        """错误信息应包含文件名"""
        code = '整数型 主函数() { 整数型 x = 1; 整数型 x = 2; 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertIn(".zhc:", output)

    def test_multiple_errors_all_reported(self):
        """多个错误应全部报告"""
        code = '''整数型 主函数() {
    整数型 x = 1;
    整数型 x = 2;
    整数型 y = abc;
    返回 0;
}'''
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertNotEqual(rc, 0)
        # 至少应有重复定义和未定义两个错误
        self.assertIn("重复定义", output)
        self.assertIn("未定义", output)


class TestE2EFlags(unittest.TestCase):
    """端到端命令行参数测试"""

    def test_skip_semantic_flag(self):
        """--skip-semantic 应跳过验证"""
        code = '整数型 主函数() { 整数型 x = 1; 整数型 x = 2; 返回 0; }'
        rc, stdout, stderr = run_compiler(code, ['--skip-semantic'])
        self.assertEqual(rc, 0, "--skip-semantic should allow compilation")

    def test_verbose_shows_semantic_info(self):
        """-v 应显示语义验证信息"""
        code = '整数型 主函数() { 返回 0; }'
        rc, stdout, stderr = run_compiler(code, ['-v'])
        output = stdout + stderr
        self.assertIn("语义验证", output)

    def test_warning_none_suppresses_warnings(self):
        """-W none 应抑制警告"""
        code = '整数型 主函数() { 整数型 x = 1.5; 返回 0; }'
        rc, stdout, stderr = run_compiler(code, ['-W', 'none'])
        output = stdout + stderr
        self.assertEqual(rc, 0, "-W none should still compile")
        # 不应有类型警告输出
        self.assertNotIn("类型警告", output)

    def test_warning_error_treats_warnings_as_errors(self):
        """-W error 应将警告当错误处理"""
        code = '整数型 主函数() { 整数型 x = 1.5; 返回 0; }'
        rc, stdout, stderr = run_compiler(code, ['-W', 'error'])
        output = stdout + stderr
        self.assertNotEqual(rc, 0, "-W error should fail on warnings")
        self.assertIn("Werror", output)


class TestE2ETypeChecking(unittest.TestCase):
    """端到端类型检查测试"""

    def test_void_assignment_error(self):
        """空型赋值应报错"""
        code = '整数型 主函数() { 空型 x = 42; 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertNotEqual(rc, 0)
        self.assertIn("类型不匹配", output)

    def test_float_to_int_warning(self):
        """浮点转整数应有警告"""
        code = '整数型 主函数() { 整数型 x = 1.5; 返回 0; }'
        rc, stdout, stderr = run_compiler(code)
        output = stdout + stderr
        self.assertEqual(rc, 0, "Warning should not prevent compilation")
        self.assertIn("精度", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
