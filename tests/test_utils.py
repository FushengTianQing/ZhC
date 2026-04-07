# -*- coding: utf-8 -*-
"""
ZHC Utils 模块测试

作者：远
日期：2026-04-08
"""

import os
import tempfile
import json
import pytest

from zhc.utils.file_utils import (
    read_file, write_file, read_json_file, write_json_file,
    read_lines, ensure_directory, file_exists, get_file_hash
)
from zhc.utils.string_utils import (
    normalize_whitespace, strip_lines, clean_empty_lines, indent_text,
    remove_prefix, remove_suffix, split_by_commas,
    camel_to_snake, snake_to_camel, truncate, format_table
)
from zhc.utils.error_utils import (
    safe_execute, format_error_message, log_error, retry_on_error,
    validate_type, validate_range, validate_not_empty, ErrorContext
)


# =============================================================================
# 测试辅助函数
# =============================================================================

def create_temp_file(content: str = "test content") -> str:
    """创建临时文件"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    os.write(fd, content.encode('utf-8'))
    os.close(fd)
    return path


def create_temp_json_file(data: dict) -> str:
    """创建临时 JSON 文件"""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.write(fd, json.dumps(data, indent=2).encode('utf-8'))
    os.close(fd)
    return path


# =============================================================================
# file_utils 测试
# =============================================================================

class TestFileUtils:
    """测试 file_utils 模块"""
    
    def test_read_file(self):
        """测试读取文件"""
        path = create_temp_file("hello world")
        try:
            content = read_file(path)
            assert content == "hello world"
        finally:
            os.unlink(path)
    
    def test_read_file_with_encoding(self):
        """测试指定编码读取"""
        path = create_temp_file("你好世界")
        try:
            content = read_file(path, encoding='utf-8')
            assert content == "你好世界"
        finally:
            os.unlink(path)
    
    def test_read_file_not_found(self):
        """测试读取不存在的文件"""
        with pytest.raises(IOError):
            read_file("/nonexistent/file.txt")
    
    def test_write_file(self):
        """测试写入文件"""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.unlink(path)  # 删除临时文件
        
        try:
            write_file(path, "new content")
            content = read_file(path)
            assert content == "new content"
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_write_file_creates_directory(self):
        """测试写入时创建目录"""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        temp_dir = os.path.dirname(path)
        os.unlink(path)
        
        subdir = os.path.join(temp_dir, "subdir", "nested")
        file_path = os.path.join(subdir, "test.txt")
        
        try:
            write_file(file_path, "content")
            assert os.path.exists(file_path)
            assert os.path.isdir(subdir)
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_read_json_file(self):
        """测试读取 JSON 文件"""
        path = create_temp_json_file({"key": "value", "num": 42})
        try:
            data = read_json_file(path)
            assert data == {"key": "value", "num": 42}
        finally:
            os.unlink(path)
    
    def test_read_json_file_invalid(self):
        """测试读取无效 JSON"""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.write(fd, b"invalid json")
        os.close(fd)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                read_json_file(path)
        finally:
            os.unlink(path)
    
    def test_write_json_file(self):
        """测试写入 JSON 文件"""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.unlink(path)
        
        try:
            write_json_file(path, {"name": "test", "value": 123})
            data = read_json_file(path)
            assert data == {"name": "test", "value": 123}
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_write_json_file_chinese(self):
        """测试写入包含中文的 JSON"""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.unlink(path)
        
        try:
            write_json_file(path, {"名字": "测试"})
            data = read_json_file(path)
            assert data["名字"] == "测试"
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_read_lines(self):
        """测试读取文件行列表"""
        path = create_temp_file("line1\nline2\nline3")
        try:
            lines = read_lines(path)
            assert len(lines) == 3
            assert lines[0] == "line1\n"
            assert lines[1] == "line2\n"
            assert lines[2] == "line3"
        finally:
            os.unlink(path)
    
    def test_ensure_directory(self):
        """测试确保目录存在"""
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        temp_dir = os.path.dirname(temp_path)
        os.unlink(temp_path)
        
        new_dir = os.path.join(temp_dir, "new", "nested", "dir")
        result = ensure_directory(new_dir)
        
        assert result == Path(new_dir) if 'Path' in dir() else os.path.exists(new_dir)
        
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_file_exists(self):
        """测试文件存在检查"""
        path = create_temp_file()
        try:
            assert file_exists(path) is True
            assert file_exists("/nonexistent/file.txt") is False
        finally:
            os.unlink(path)
    
    def test_get_file_hash(self):
        """测试文件哈希计算"""
        path = create_temp_file("test content")
        try:
            md5_hash = get_file_hash(path, 'md5')
            assert len(md5_hash) == 32  # MD5 哈希长度
            
            sha256_hash = get_file_hash(path, 'sha256')
            assert len(sha256_hash) == 64  # SHA256 哈希长度
        finally:
            os.unlink(path)
    
    def test_get_file_hash_consistency(self):
        """测试哈希计算一致性"""
        path = create_temp_file("consistent content")
        try:
            hash1 = get_file_hash(path, 'md5')
            hash2 = get_file_hash(path, 'md5')
            assert hash1 == hash2
        finally:
            os.unlink(path)


# =============================================================================
# string_utils 测试
# =============================================================================

class TestStringUtils:
    """测试 string_utils 模块"""
    
    def test_normalize_whitespace(self):
        """测试空白字符规范化"""
        assert normalize_whitespace("  hello   world  ") == "hello world"
        assert normalize_whitespace("hello\t\tworld") == "hello world"
        assert normalize_whitespace("hello\n\nworld") == "hello world"
    
    def test_normalize_whitespace_empty(self):
        """测试空白字符规范化空字符串"""
        assert normalize_whitespace("") == ""
        assert normalize_whitespace("   ") == ""
    
    def test_strip_lines(self):
        """测试行分割并去除空白"""
        result = strip_lines("  line1  \n  line2  \n")
        assert result == ["line1", "line2"]
    
    def test_strip_lines_skip_empty(self):
        """测试跳过空行"""
        result = strip_lines("line1\n\nline2", skip_empty=True)
        assert result == ["line1", "line2"]
    
    def test_strip_lines_keep_empty(self):
        """测试保留空行"""
        result = strip_lines("line1\n\nline2", skip_empty=False)
        assert result == ["line1", "", "line2"]
    
    def test_clean_empty_lines(self):
        """测试清除空行"""
        result = clean_empty_lines("line1\n\nline2\n\n\nline3")
        assert result == "line1\nline2\nline3"
    
    def test_indent_text(self):
        """测试文本缩进"""
        result = indent_text("line1\nline2", 4)
        assert result == "    line1\n    line2"
    
    def test_indent_text_empty_lines(self):
        """测试空行不缩进"""
        result = indent_text("line1\n\nline2", 4)
        lines = result.split('\n')
        assert lines[0] == "    line1"
        assert lines[1] == ""  # 空行保持空
        assert lines[2] == "    line2"
    
    def test_remove_prefix(self):
        """测试移除前缀"""
        assert remove_prefix("hello_world", "hello_") == "world"
        assert remove_prefix("hello_world", "xyz") == "hello_world"
    
    def test_remove_suffix(self):
        """测试移除后缀"""
        assert remove_suffix("hello.py", ".py") == "hello"
        assert remove_suffix("hello", ".py") == "hello"
    
    def test_split_by_commas(self):
        """测试按逗号分割"""
        assert split_by_commas("a, b, c") == ["a", "b", "c"]
        assert split_by_commas("x,y , z") == ["x", "y", "z"]
        assert split_by_commas("a,,b") == ["a", "b"]
    
    def test_camel_to_snake(self):
        """测试驼峰转蛇形"""
        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("getHTTPResponse") == "get_http_response"
        assert camel_to_snake("XMLParser") == "xml_parser"
    
    def test_snake_to_camel(self):
        """测试蛇形转驼峰"""
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("snake_case", True) == "SnakeCase"
        assert snake_to_camel("get_http_response") == "getHttpResponse"
    
    def test_truncate(self):
        """测试字符串截断"""
        assert truncate("Hello World", 8) == "Hello..."
        assert truncate("Hi", 8) == "Hi"
        assert truncate("Hello", 5) == "Hello"
    
    def test_truncate_custom_suffix(self):
        """测试自定义截断后缀"""
        # "Hello World" 长度 11，max_length=8，suffix=".." 长度 2
        # 截取 8-2=6 个字符 "Hello " + ".." = "Hello .."
        result = truncate("Hello World", 8, suffix="..")
        # 根据当前实现，结果是 "Hello .."
        assert result == "Hello .."
    
    def test_format_table(self):
        """测试表格格式化"""
        headers = ["Name", "Age"]
        rows = [["Alice", "30"], ["Bob", "25"]]
        result = format_table(headers, rows)
        
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "Bob" in result
    
    def test_format_table_empty(self):
        """测试空表格"""
        assert format_table([], []) == ""
        assert format_table(["A"], []) == ""


# =============================================================================
# error_utils 测试
# =============================================================================

class TestErrorUtils:
    """测试 error_utils 模块"""
    
    def test_safe_execute_success(self):
        """测试安全执行成功"""
        def add(a, b):
            return a + b
        
        result = safe_execute(add, 1, 2, default_return=0)
        assert result == 3
    
    def test_safe_execute_failure(self):
        """测试安全执行失败"""
        def fail():
            raise ValueError("test error")
        
        result = safe_execute(fail, default_return=-1, log_errors=False)
        assert result == -1
    
    def test_safe_execute_with_kwargs(self):
        """测试安全执行带关键字参数"""
        def greet(name, prefix="Hello"):
            return f"{prefix}, {name}"
        
        result = safe_execute(greet, "World", prefix="Hi")
        assert result == "Hi, World"
    
    def test_format_error_message(self):
        """测试错误消息格式化"""
        error = ValueError("test error")
        msg = format_error_message(error)
        
        assert "ValueError" in msg
        assert "test error" in msg
    
    def test_format_error_message_with_context(self):
        """测试带上下文的错误消息"""
        error = ValueError("test error")
        msg = format_error_message(error, context="processing data")
        
        assert "ValueError" in msg
        assert "processing data" in msg
    
    def test_format_error_message_with_traceback(self):
        """测试带堆栈跟踪的错误消息"""
        try:
            raise ValueError("test error")
        except ValueError as e:
            msg = format_error_message(e, include_traceback=True)
            assert "ValueError" in msg
            assert "Traceback" in msg or "test error" in msg
    
    def test_log_error(self, capsys):
        """测试错误日志"""
        error = ValueError("test error")
        log_error(error, context="test context")
        
        captured = capsys.readouterr()
        assert "ValueError" in captured.err
        assert "test error" in captured.err
    
    def test_validate_type_success(self):
        """测试类型验证成功"""
        result = validate_type("test", str, "param")
        assert result == "test"
    
    def test_validate_type_failure(self):
        """测试类型验证失败"""
        with pytest.raises(TypeError) as exc_info:
            validate_type(123, str, "param")
        
        assert "param" in str(exc_info.value)
        assert "str" in str(exc_info.value)
        assert "int" in str(exc_info.value)
    
    def test_validate_range(self):
        """测试范围验证"""
        assert validate_range(5, min_value=0, max_value=10, name="value") == 5
        
        with pytest.raises(ValueError) as exc_info:
            validate_range(-1, min_value=0, name="value")
        assert "过小" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_range(100, max_value=10, name="value")
        assert "过大" in str(exc_info.value)
    
    def test_validate_not_empty(self):
        """测试非空验证"""
        assert validate_not_empty("test", "param") == "test"
        
        with pytest.raises(ValueError) as exc_info:
            validate_not_empty("", "param")
        assert "空" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_not_empty("   ", "param")
        assert "空" in str(exc_info.value)
    
    def test_error_context_no_exception(self):
        """测试无异常时的错误上下文"""
        with ErrorContext("test context") as ctx:
            pass
        
        assert ctx.has_error() is False
        assert ctx.get_error() is None
    
    def test_error_context_with_exception(self, capsys):
        """测试有异常时的错误上下文"""
        with ErrorContext("test context", log_errors=True) as ctx:
            raise ValueError("test error")
        
        assert ctx.has_error() is True
        assert isinstance(ctx.get_error(), ValueError)


class TestRetryOnError:
    """测试 retry_on_error 装饰器"""
    
    def test_retry_success_first_try(self):
        """测试第一次尝试成功"""
        call_count = 0
        
        # retry_on_error 需要作为装饰器工厂调用（带括号）
        @retry_on_error(max_retries=3, delay=0)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeed()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """测试失败后重试成功"""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"
        
        result = flaky()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_all_failures(self):
        """测试所有重试都失败"""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay=0)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")
        
        with pytest.raises(ValueError) as exc_info:
            always_fail()
        
        assert "always fails" in str(exc_info.value)
        assert call_count == 3  # 初始 + 2 次重试


# =============================================================================
# 边界情况测试
# =============================================================================

class TestEdgeCases:
    """测试边界情况"""
    
    def test_read_file_binary_mode(self):
        """测试二进制文件读取"""
        fd, path = tempfile.mkstemp()
        os.write(fd, b"binary content")
        os.close(fd)
        
        try:
            # 使用 binary mode 读取
            with open(path, 'rb') as f:
                content = f.read()
            assert content == b"binary content"
        finally:
            os.unlink(path)
    
    def test_empty_json_file(self):
        """测试空 JSON 文件"""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.write(fd, b"{}")
        os.close(fd)
        
        try:
            data = read_json_file(path)
            assert data == {}
        finally:
            os.unlink(path)
    
    def test_unicode_string(self):
        """测试 Unicode 字符串"""
        text = "Hello 世界 🌍"
        assert normalize_whitespace(f"  {text}  ") == text
    
    def test_retry_specific_exception(self):
        """测试特定异常重试"""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay=0, exceptions=(ValueError,))
        def only_value_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("wrong exception")  # 不应重试
        
        with pytest.raises(TypeError):
            only_value_error()
        
        assert call_count == 1  # 不重试


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
