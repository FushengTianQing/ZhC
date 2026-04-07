#!/usr/bin/env python3
"""
集成测试套件：基础功能端到端测试

使用pytest框架重新实现test_suite1-6的集成测试
这些测试验证完整的编译流程：预处理 → C代码生成 → clang编译
"""

import subprocess
import sys
import os
import tempfile
import pytest
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
ZHPP_MODULE = PROJECT_ROOT / "src" / "zhpp"
ZHPP_CLI = PROJECT_ROOT / "src" / "zhpp" / "__main__.py"


class TestBasicTypes:
    """测试套件1：基础类型"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前设置临时目录"""
        self.tmpdir = tmp_path
        # 使用python -m zhpp方式，需要设置PYTHONPATH
        self.zhpp_cmd = [sys.executable, "-m", "zhpp"]
        self.env = os.environ.copy()
        # 确保src目录在PYTHONPATH中
        pythonpath = str(PROJECT_ROOT / 'src')
        if 'PYTHONPATH' in self.env:
            self.env['PYTHONPATH'] = f"{pythonpath}:{self.env['PYTHONPATH']}"
        else:
            self.env['PYTHONPATH'] = pythonpath
    
    def run_compiler(self, zhc_code: str, test_name: str) -> tuple:
        """运行编译器并返回结果"""
        # 写入中文源码
        zhc_file = self.tmpdir / f"{test_name}.zhc"
        zhc_file.write_text(zhc_code, encoding='utf-8')
        
        # 运行预处理器
        result = subprocess.run(
            self.zhpp_cmd + [str(zhc_file)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=self.env
        )
        
        if result.returncode != 0:
            return False, f"预处理器失败: {result.stderr}"
        
        # 检查生成的C代码
        c_file = zhc_file.with_suffix('.c')
        if not c_file.exists():
            return False, "未生成C文件"
        
        c_code = c_file.read_text()
        
        # 编译C代码
        exe_file = zhc_file.with_suffix('')
        compile_result = subprocess.run(
            ['clang', str(c_file), '-o', str(exe_file), '-w'],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            return False, f"C编译失败: {compile_result.stderr[:100]}"
        
        return True, c_code
    
    def test_int_basic(self):
        """测试整数型基础"""
        success, output = self.run_compiler('''
整数型 主函数() {
    整数型 x = 42;
    返回 0;
}
''', 'int_basic')
        assert success, output
        assert 'int x = 42' in output or 'int x=42' in output
    
    def test_char_type(self):
        """测试字符型"""
        success, output = self.run_compiler('''
字符型 主函数() {
    字符型 c = 65;
    返回 c - 65;
}
''', 'char_type')
        assert success, output
        assert 'char c' in output
    
    def test_float_type(self):
        """测试浮点型"""
        success, output = self.run_compiler('''
浮点型 主函数() {
    浮点型 f = 3.14f;
    返回 0.0f;
}
''', 'float_type')
        assert success, output
        assert 'float f' in output
    
    def test_double_type(self):
        """测试双精度浮点型"""
        success, output = self.run_compiler('''
双精度浮点型 主函数() {
    双精度浮点型 d = 3.14159;
    返回 0.0;
}
''', 'double_type')
        assert success, output
        assert 'double d' in output
    
    def test_array_basic(self):
        """测试数组基础"""
        success, output = self.run_compiler('''
整数型 主函数() {
    整数型 arr[5] = {1, 2, 3, 4, 5};
    返回 arr[0];
}
''', 'array_basic')
        assert success, output


class TestControlFlow:
    """测试套件2：流程控制"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前设置临时目录"""
        self.tmpdir = tmp_path
        self.zhpp_cmd = [sys.executable, "-m", "zhpp"]
        self.env = os.environ.copy()
        pythonpath = str(PROJECT_ROOT / 'src')
        if 'PYTHONPATH' in self.env:
            self.env['PYTHONPATH'] = f"{pythonpath}:{self.env['PYTHONPATH']}"
        else:
            self.env['PYTHONPATH'] = pythonpath
    
    def run_compiler(self, zhc_code: str, test_name: str) -> tuple:
        """运行编译器并返回结果"""
        zhc_file = self.tmpdir / f"{test_name}.zhc"
        zhc_file.write_text(zhc_code, encoding='utf-8')
        
        result = subprocess.run(
            self.zhpp_cmd + [str(zhc_file)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=self.env
        )
        
        if result.returncode != 0:
            return False, f"预处理器失败: {result.stderr}"
        
        c_file = zhc_file.with_suffix('.c')
        if not c_file.exists():
            return False, "未生成C文件"
        
        c_code = c_file.read_text()
        
        exe_file = zhc_file.with_suffix('')
        compile_result = subprocess.run(
            ['clang', str(c_file), '-o', str(exe_file), '-w'],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            return False, f"C编译失败: {compile_result.stderr[:100]}"
        
        return True, c_code
    
    def test_if_else(self):
        """测试if-else语句"""
        success, output = self.run_compiler('''
整数型 主函数() {
    整数型 x = 10;
    如果 (x > 5) {
        返回 1;
    } 否则 {
        返回 0;
    }
}
''', 'if_else')
        assert success, output
        assert 'if' in output
    
    def test_while_loop(self):
        """测试while循环"""
        success, output = self.run_compiler('''
整数型 主函数() {
    整数型 i = 0;
    当 (i < 10) {
        i = i + 1;
    }
    返回 i;
}
''', 'while_loop')
        assert success, output
        assert 'while' in output
    
    def test_for_loop(self):
        """测试for循环"""
        success, output = self.run_compiler('''
整数型 主函数() {
    整数型 总和 = 0;
    循环 (整数型 i = 0; i < 10; i = i + 1) {
        总和 = 总和 + i;
    }
    返回 总和;
}
''', 'for_loop')
        assert success, output


class TestFunctions:
    """测试套件3：函数"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前设置临时目录"""
        self.tmpdir = tmp_path
        self.zhpp_cmd = [sys.executable, "-m", "zhpp"]
        self.env = os.environ.copy()
        pythonpath = str(PROJECT_ROOT / 'src')
        if 'PYTHONPATH' in self.env:
            self.env['PYTHONPATH'] = f"{pythonpath}:{self.env['PYTHONPATH']}"
        else:
            self.env['PYTHONPATH'] = pythonpath
    
    def run_compiler(self, zhc_code: str, test_name: str) -> tuple:
        """运行编译器并返回结果"""
        zhc_file = self.tmpdir / f"{test_name}.zhc"
        zhc_file.write_text(zhc_code, encoding='utf-8')
        
        result = subprocess.run(
            self.zhpp_cmd + [str(zhc_file)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=self.env
        )
        
        if result.returncode != 0:
            return False, f"预处理器失败: {result.stderr}"
        
        c_file = zhc_file.with_suffix('.c')
        if not c_file.exists():
            return False, "未生成C文件"
        
        c_code = c_file.read_text()
        
        exe_file = zhc_file.with_suffix('')
        compile_result = subprocess.run(
            ['clang', str(c_file), '-o', str(exe_file), '-w'],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            return False, f"C编译失败: {compile_result.stderr[:100]}"
        
        return True, c_code
    
    def test_function_definition(self):
        """测试函数定义"""
        success, output = self.run_compiler('''
整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}

整数型 主函数() {
    整数型 结果 = 加法(3, 5);
    返回 结果;
}
''', 'func_def')
        assert success, output
        assert 'int' in output  # 函数返回类型
    
    def test_void_function(self):
        """测试无返回值函数"""
        success, output = self.run_compiler('''
空型 打招呼() {
    返回;
}

整数型 主函数() {
    打招呼();
    返回 0;
}
''', 'void_func')
        assert success, output
        assert 'void' in output


class TestAdvancedFeatures:
    """测试套件4：高级特性"""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前设置临时目录"""
        self.tmpdir = tmp_path
        self.zhpp_cmd = [sys.executable, "-m", "zhpp"]
        self.env = os.environ.copy()
        pythonpath = str(PROJECT_ROOT / 'src')
        if 'PYTHONPATH' in self.env:
            self.env['PYTHONPATH'] = f"{pythonpath}:{self.env['PYTHONPATH']}"
        else:
            self.env['PYTHONPATH'] = pythonpath
    
    def run_compiler(self, zhc_code: str, test_name: str) -> tuple:
        """运行编译器并返回结果"""
        zhc_file = self.tmpdir / f"{test_name}.zhc"
        zhc_file.write_text(zhc_code, encoding='utf-8')
        
        result = subprocess.run(
            self.zhpp_cmd + [str(zhc_file)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=self.env
        )
        
        if result.returncode != 0:
            return False, f"预处理器失败: {result.stderr}"
        
        c_file = zhc_file.with_suffix('.c')
        if not c_file.exists():
            return False, "未生成C文件"
        
        c_code = c_file.read_text()
        
        exe_file = zhc_file.with_suffix('')
        compile_result = subprocess.run(
            ['clang', str(c_file), '-o', str(exe_file), '-w'],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            return False, f"C编译失败: {compile_result.stderr[:100]}"
        
        return True, c_code
    
    def test_pointer(self):
        """测试指针"""
        success, output = self.run_compiler('''
整数型 主函数() {
    整数型 x = 42;
    整数型* ptr = &x;
    返回 *ptr;
}
''', 'pointer')
        assert success, output
    
    def test_struct(self):
        """测试结构体"""
        success, output = self.run_compiler('''
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
''', 'struct')
        assert success, output
        assert 'struct' in output


# 可以继续添加test_suite5和test_suite6的测试...


if __name__ == "__main__":
    """直接运行此文件进行测试"""
    pytest.main([__file__, "-v", "--tb=short"])