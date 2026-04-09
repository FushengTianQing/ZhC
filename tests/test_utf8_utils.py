#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 UTF-8 编码处理工具
"""

from zhc.utils.utf8_utils import (
    utf8_char_length,
    utf8_encode,
    utf8_decode,
    utf8_char_count,
    utf8_byte_length,
    utf8_chars,
    utf8_substring,
    utf8_slice,
    utf8_index_to_byte,
    utf8_byte_to_index,
    utf8_char_at,
    utf8_char_bytes,
    utf8_validate,
    utf8_truncate,
    utf8_reverse,
    utf8_ljust,
    utf8_rjust,
    utf8_center,
)


def test_utf8_char_length():
    """测试 UTF-8 字符长度判断"""
    # ASCII
    assert utf8_char_length(0x41) == 1  # 'A'
    assert utf8_char_length(0x7F) == 1  # DEL

    # 2 字节字符
    assert utf8_char_length(0xC2) == 2  # 带重音的字符
    assert utf8_char_length(0xDF) == 2

    # 3 字节字符 (中文等)
    assert utf8_char_length(0xE4) == 3  # 中文字符首字节
    assert utf8_char_length(0xEF) == 3

    # 4 字节字符 (emoji等)
    assert utf8_char_length(0xF0) == 4
    assert utf8_char_length(0xF4) == 4

    print("✓ utf8_char_length 测试通过")


def test_utf8_encode_decode():
    """测试编码和解码"""
    text = "你好世界Hello"
    encoded = utf8_encode(text)
    decoded = utf8_decode(encoded)

    assert decoded == text
    assert isinstance(encoded, bytes)
    assert isinstance(decoded, str)

    print(f"✓ utf8_encode/decode 测试通过: {repr(encoded)}")


def test_utf8_char_count():
    """测试字符计数"""
    assert utf8_char_count("你好") == 2
    assert utf8_char_count("Hello") == 5
    assert utf8_char_count("Hello你好") == 7
    assert utf8_char_count("") == 0

    print("✓ utf8_char_count 测试通过")


def test_utf8_byte_length():
    """测试字节长度"""
    # "你" = 3 字节, "好" = 3 字节
    assert utf8_byte_length("你好") == 6
    # ASCII 每字符 1 字节
    assert utf8_byte_length("Hello") == 5
    # 混合
    assert utf8_byte_length("Hi你好") == 8  # 2 + 6

    print("✓ utf8_byte_length 测试通过")


def test_utf8_chars():
    """测试字符拆分"""
    assert utf8_chars("你好") == ["你", "好"]
    assert utf8_chars("Hello") == ["H", "e", "l", "l", "o"]
    assert utf8_chars("Hello世界") == ["H", "e", "l", "l", "o", "世", "界"]

    print("✓ utf8_chars 测试通过")


def test_utf8_substring():
    """测试子字符串截取"""
    assert utf8_substring("你好世界", 0, 2) == "你好"
    assert utf8_substring("你好世界", 2) == "世界"
    # "Hello你好": H(0), e(1), l(2), l(3), o(4), 你(5), 好(6)
    assert utf8_substring("Hello你好", 0, 5) == "Hello"
    assert utf8_substring("Hello你好", 5, 2) == "你好"
    assert utf8_substring("Hello你好", 3, 2) == "lo"
    assert utf8_substring("测试", 0, 1) == "测"

    print("✓ utf8_substring 测试通过")


def test_utf8_slice():
    """测试切片"""
    assert utf8_slice("你好世界", 1, 3) == "好世"
    assert utf8_slice("Hello世界", 4, 6) == "o世"

    print("✓ utf8_slice 测试通过")


def test_utf8_index_conversion():
    """测试字符索引和字节索引转换"""
    text = "你好"
    # "你" 起始字节 = 0, "好" 起始字节 = 3
    assert utf8_index_to_byte(text, 0) == 0
    assert utf8_index_to_byte(text, 1) == 3

    assert utf8_byte_to_index(text, 0) == 0
    assert utf8_byte_to_index(text, 3) == 1

    print("✓ utf8_index_to_byte/byte_to_index 测试通过")


def test_utf8_char_at():
    """测试获取指定位置字符"""
    assert utf8_char_at("你好", 0) == "你"
    assert utf8_char_at("你好", 1) == "好"
    assert utf8_char_at("你好", 2) is None
    assert utf8_char_at("你好", -1) is None

    print("✓ utf8_char_at 测试通过")


def test_utf8_char_bytes():
    """测试获取字符字节"""
    # "你" 的 UTF-8 编码
    assert utf8_char_bytes("你", 0) == b"\xe4\xbd\xa0"
    # "A" 的 UTF-8 编码
    assert utf8_char_bytes("A", 0) == b"A"

    print("✓ utf8_char_bytes 测试通过")


def test_utf8_validate():
    """测试 UTF-8 验证"""
    # 有效 UTF-8
    valid, positions = utf8_validate(b"Hello")
    assert valid and positions == []

    valid, positions = utf8_validate("你好".encode("utf-8"))
    assert valid and positions == []

    # 无效 UTF-8
    valid, positions = utf8_validate(b"\x80\x90")  # 非法续字节
    assert not valid

    print("✓ utf8_validate 测试通过")


def test_utf8_truncate():
    """测试字符串截断"""
    # 不需要截断的情况（文本长度 <= max_chars）
    assert utf8_truncate("你好世界", 4) == "你好世界"  # 4字符，max=4，不截断
    assert utf8_truncate("你好世界", 5) == "你好世界"  # 4字符，max=5，不截断
    assert utf8_truncate("你好世界", 6) == "你好世界"  # 4字符，max=6，不截断
    assert utf8_truncate("Hello你好", 10) == "Hello你好"  # 7字符，max=10，不截断

    # 需要截断的情况（文本长度 > max_chars）
    # "你好世界" 有 4 个字符
    # max_chars=3, suffix="..."(3 chars), available=0, 只返回后缀
    assert utf8_truncate("你好世界", 3) == "..."
    # max_chars=2, suffix="..."(3 chars), suffix太长，截断后缀
    assert utf8_truncate("你好世界", 2) == ".."

    # "Hello你好" 有 7 个字符
    # max_chars=6, suffix="..."(3 chars), available=3, 截取3个字符
    assert utf8_truncate("Hello你好", 6) == "Hel..."
    # max_chars=5, suffix="..."(3 chars), available=2, 截取2个字符
    assert utf8_truncate("Hello你好", 5) == "He..."

    print("✓ utf8_truncate 测试通过")


def test_utf8_reverse():
    """测试字符串反转"""
    assert utf8_reverse("你好") == "好你"
    assert utf8_reverse("Hello世界") == "界世olleH"

    print("✓ utf8_reverse 测试通过")


def test_utf8_alignment():
    """测试字符串对齐"""
    # 左对齐（按字符数）
    # "你好" 有 2 个字符，padding = 6 - 2 = 4
    assert utf8_ljust("你好", 6) == "你好    "
    assert utf8_ljust("Hi", 6) == "Hi    "

    # 右对齐
    assert utf8_rjust("你好", 6) == "    你好"
    assert utf8_rjust("Hi", 6) == "    Hi"

    # 居中
    assert utf8_center("你好", 6) == "  你好  "
    result = utf8_center("Hi", 7)
    assert result == "  Hi   " or result == "   Hi  "  # 允许不同的填充方式

    print("✓ utf8_ljust/rjust/center 测试通过")


def test_mixed_content():
    """测试混合内容"""
    text = "Hello你好World世界"

    # 字符计数: Hello(5) + 你好(2) + World(5) + 世界(2) = 14
    assert utf8_char_count(text) == 14

    # 字节长度: Hello(5) + 你好(6) + World(5) + 世界(6) = 22
    byte_len = utf8_byte_length(text)
    assert byte_len == 22

    # 切片
    assert utf8_slice(text, 5, 7) == "你好"

    # 反转: 界世dlroW好你olleH (注意 W 是大写)
    reversed_text = utf8_reverse(text)
    assert reversed_text == "界世dlroW好你olleH"

    print("✓ 混合内容测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 UTF-8 编码处理工具")
    print("=" * 60)
    print()

    test_utf8_char_length()
    test_utf8_encode_decode()
    test_utf8_char_count()
    test_utf8_byte_length()
    test_utf8_chars()
    test_utf8_substring()
    test_utf8_slice()
    test_utf8_index_conversion()
    test_utf8_char_at()
    test_utf8_char_bytes()
    test_utf8_validate()
    test_utf8_truncate()
    test_utf8_reverse()
    test_utf8_alignment()
    test_mixed_content()

    print()
    print("=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
