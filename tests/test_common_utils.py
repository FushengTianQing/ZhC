#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共工具模块单元测试

测试 file_utils, string_utils, error_utils 的功能。

作者：远
日期：2026-04-07
"""

import os
import json
import tempfile
from pathlib import Path

import pytest

from zhc.utils.file_utils import (
    read_file,
    write_file,
    read_json_file,
    write_json_file,
    read_lines,
    ensure_directory,
    file_exists,
    get_file_hash,
)

from zhc.utils.string_utils import (
    normalize_whitespace,
    strip_lines,
    clean_empty_lines,
    indent_text,
    remove_prefix,
    remove_suffix,
    split_by_commas,
    camel_to_snake,
    snake_to_camel,
    truncate,
)

from zhc.utils.error_utils import (
    safe_execute,
    format_error_message,
    log_error,
    validate_type,
    validate_range,
    validate_not_empty,
    ErrorContext,
)


# =============================================================================
# 文件工具测试
# =============================================================================

class TestFileUtils:
    """文件工具测试"""
    
    def test_read_write_file(self, tmp_path):
        """测试文件读写"""
        filepath = tmp_path / "test.txt"
        content = "Hello, World!\n你好，世界！"
        
        # 写入文件
        write_file(filepath, content)
        
        # 读取文件
        result = read_file(filepath)
        
        assert result == content
        assert file_exists(filepath)
    
    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        with pytest.raises(IOError):
            read_file("nonexistent_file.txt")
    
    def test_read_write_json_file(self, tmp_path):
        """测试 JSON 文件读写"""
        filepath = tmp_path / "test.json"
        data = {
            "name": "ZHC",
            "version": "1.0.0",
            "features": ["lexer", "parser", "codegen"]
        }
        
        # 写入 JSON 文件
        write_json_file(filepath, data)
        
        # 读取 JSON 文件
        result = read_json_file(filepath)
        
        assert result == data
        assert result["name"] == "ZHC"
    
    def test_read_invalid_json(self, tmp_path):
        """测试读取无效的 JSON 文件"""
        filepath = tmp_path / "invalid.json"
        write_file(filepath, "not a valid json")
        
        with pytest.raises(json.JSONDecodeError):
            read_json_file(filepath)
    
    def test_read_lines(self, tmp_path):
        """测试读取文件行列表"""
        filepath = tmp_path / "lines.txt"
        content = "line1\nline2\nline3\n"
        
        write_file(filepath, content)
        
        lines = read_lines(filepath)
        
        assert len(lines) == 3
        assert lines[0] == "line1\n"
        assert lines[1] == "line2\n"
        assert lines[2] == "line3\n"
    
    def test_ensure_directory(self, tmp_path):
        """测试创建目录"""
        dirpath = tmp_path / "subdir" / "nested"
        
        result = ensure_directory(dirpath)
        
        assert result.exists()
        assert result.is_dir()
    
    def test_get_file_hash(self, tmp_path):
        """测试文件哈希计算"""
        filepath = tmp_path / "test.txt"
        content = "Hello, World!"
        
        write_file(filepath, content)
        
        hash_md5 = get_file_hash(filepath, 'md5')
        hash_sha256 = get_file_hash(filepath, 'sha256')
        
        assert len(hash_md5) == 32  # MD5 哈希长度
        assert len(hash_sha256) == 64  # SHA256 哈希长度
        assert hash_md5 != hash_sha256


# =============================================================================
# 字符串工具测试
# =============================================================================

class TestStringUtils:
    """字符串工具测试"""
    
    def test_normalize_whitespace(self):
        """测试规范化空白字符"""
        assert normalize_whitespace("  hello   world  ") == "hello world"
        assert normalize_whitespace("hello\t\tworld") == "hello world"
        assert normalize_whitespace("line1\n\nline2") == "line1 line2"
    
    def test_strip_lines(self):
        """测试去除行空白"""
        text = "  line1  \n  line2  \n  line3  "
        
        result = strip_lines(text)
        
        assert result == ["line1", "line2", "line3"]
    
    def test_clean_empty_lines(self):
        """测试清除空行"""
        text = "line1\n\nline2\n\n\nline3"
        
        result = clean_empty_lines(text)
        
        assert result == "line1\nline2\nline3"
    
    def test_indent_text(self):
        """测试添加缩进"""
        text = "line1\nline2\nline3"
        
        result = indent_text(text, spaces=4)
        
        assert result == "    line1\n    line2\n    line3"
    
    def test_remove_prefix(self):
        """测试移除前缀"""
        assert remove_prefix("hello_world", "hello_") == "world"
        assert remove_prefix("hello_world", "xyz") == "hello_world"
        assert remove_prefix("", "prefix") == ""
    
    def test_remove_suffix(self):
        """测试移除后缀"""
        assert remove_suffix("hello.py", ".py") == "hello"
        assert remove_suffix("hello", ".py") == "hello"
        assert remove_suffix("", ".py") == ""
    
    def test_split_by_commas(self):
        """测试按逗号分割"""
        assert split_by_commas("a, b, c") == ["a", "b", "c"]
        assert split_by_commas("x,y , z") == ["x", "y", "z"]
        assert split_by_commas("") == []
    
    def test_camel_to_snake(self):
        """测试驼峰转蛇形命名"""
        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("getHTTPResponse") == "get_http_response"
        assert camel_to_snake("simple") == "simple"
    
    def test_snake_to_camel(self):
        """测试蛇形转驼峰命名"""
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("snake_case", capitalize_first=True) == "SnakeCase"
        assert snake_to_camel("simple") == "simple"
    
    def test_truncate(self):
        """测试截断字符串"""
        assert truncate("Hello World", 8) == "Hello..."
        assert truncate("Hi", 8) == "Hi"
        assert truncate("Hello World", 11) == "Hello World"
        assert truncate("Hello World", 10, suffix="…") == "Hello Wor…"


# =============================================================================
# 错误处理工具测试
# =============================================================================

class TestErrorUtils:
    """错误处理工具测试"""
    
    def test_safe_execute_success(self):
        """测试安全执行成功"""
        def add(a, b):
            return a + b
        
        result = safe_execute(add, 1, 2, log_errors=False)
        
        assert result == 3
    
    def test_safe_execute_failure(self):
        """测试安全执行失败"""
        def divide(a, b):
            return a / b
        
        result = safe_execute(divide, 1, 0, default_return=None, log_errors=False)
        
        assert result is None
    
    def test_format_error_message(self):
        """测试格式化错误消息"""
        error = ValueError("测试错误")
        
        msg = format_error_message(error, context="测试上下文")
        
        assert "[ValueError]" in msg
        assert "测试错误" in msg
        assert "测试上下文" in msg
    
    def test_validate_type(self):
        """测试类型验证"""
        assert validate_type("hello", str) == "hello"
        assert validate_type(123, int) == 123
        
        with pytest.raises(TypeError):
            validate_type("hello", int)
    
    def test_validate_range(self):
        """测试范围验证"""
        assert validate_range(5, min_value=1, max_value=10) == 5
        
        with pytest.raises(ValueError):
            validate_range(0, min_value=1)
        
        with pytest.raises(ValueError):
            validate_range(11, max_value=10)
    
    def test_validate_not_empty(self):
        """测试非空验证"""
        assert validate_not_empty("hello") == "hello"
        
        with pytest.raises(ValueError):
            validate_not_empty("")
        
        with pytest.raises(ValueError):
            validate_not_empty("   ")
    
    def test_error_context(self):
        """测试错误上下文管理器"""
        with ErrorContext("测试上下文", log_errors=False) as ctx:
            raise ValueError("测试错误")
        
        assert ctx.has_error()
        assert isinstance(ctx.get_error(), ValueError)
        assert str(ctx.get_error()) == "测试错误"
    
    def test_error_context_no_error(self):
        """测试错误上下文管理器无异常"""
        with ErrorContext("测试上下文", log_errors=False) as ctx:
            pass
        
        assert not ctx.has_error()
        assert ctx.get_error() is None


# =============================================================================
# 集成测试
# =============================================================================

class TestIntegration:
    """集成测试"""
    
    def test_file_string_integration(self, tmp_path):
        """测试文件和字符串工具集成"""
        filepath = tmp_path / "test.txt"
        content = "  line1  \n\n  line2  \n\n\n  line3  "
        
        # 写入文件
        write_file(filepath, content)
        
        # 读取并处理
        lines = strip_lines(read_file(filepath))
        
        assert lines == ["line1", "line2", "line3"]
    
    def test_json_error_integration(self, tmp_path):
        """测试 JSON 和错误处理集成"""
        filepath = tmp_path / "config.json"
        
        # 使用错误上下文读取不存在的文件
        with ErrorContext("读取配置文件", log_errors=False) as ctx:
            config = safe_execute(read_json_file, filepath, default_return={}, log_errors=False)
        
        assert not ctx.has_error()  # safe_execute 捕获了异常
        assert config == {}
    
    def test_hash_file_integration(self, tmp_path):
        """测试文件哈希集成"""
        filepath = tmp_path / "test.txt"
        content = "Hello, World!"
        
        write_file(filepath, content)
        
        hash1 = get_file_hash(filepath)
        
        # 修改文件
        write_file(filepath, content + "!")
        
        hash2 = get_file_hash(filepath)
        
        assert hash1 != hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
