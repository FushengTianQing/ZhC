#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字符编码转换工具
"""

from zhc.utils.encoding_utils import (
    detect_encoding,
    convert_encoding,
    utf8_to_gbk,
    gbk_to_utf8,
    utf8_to_big5,
    big5_to_utf8,
    is_valid_encoding,
    get_encoding_name,
    safe_decode,
    safe_encode,
    get_bom,
    strip_bom,
    get_supported_encodings,
)


def test_utf8_to_gbk():
    """测试 UTF-8 到 GBK 转换"""
    text = "你好世界Hello"
    gbk_data = utf8_to_gbk(text)

    assert isinstance(gbk_data, bytes)
    # 解码回 GBK 应该得到相同内容
    assert gbk_data.decode("gbk") == text

    print(f"✓ UTF-8 到 GBK: '{text}' -> {repr(gbk_data)}")


def test_gbk_to_utf8():
    """测试 GBK 到 UTF-8 转换"""
    original = "你好世界Hello"
    gbk_data = original.encode("gbk")
    utf8_text = gbk_to_utf8(gbk_data)

    assert isinstance(utf8_text, str)
    assert utf8_text == original

    print(f"✓ GBK 到 UTF-8: {repr(gbk_data)} -> '{utf8_text}'")


def test_utf8_to_big5():
    """测试 UTF-8 到 Big5 转换"""
    text = "繁體中文"
    big5_data = utf8_to_big5(text)

    assert isinstance(big5_data, bytes)
    # 解码回 Big5 应该得到相同内容
    assert big5_data.decode("big5") == text

    print(f"✓ UTF-8 到 Big5: '{text}' -> {repr(big5_data)}")


def test_big5_to_utf8():
    """测试 Big5 到 UTF-8 转换"""
    original = "繁體中文"
    big5_data = original.encode("big5")
    utf8_text = big5_to_utf8(big5_data)

    assert isinstance(utf8_text, str)
    assert utf8_text == original

    print(f"✓ Big5 到 UTF-8: {repr(big5_data)} -> '{utf8_text}'")


def test_convert_encoding():
    """测试通用编码转换"""
    text = "你好"
    # UTF-8 -> GBK -> UTF-8
    gbk = convert_encoding(text.encode("utf-8"), "utf-8", "gbk")
    back = convert_encoding(gbk, "gbk", "utf-8")

    assert back.decode("utf-8") == text

    print(f"✓ 通用编码转换: UTF-8 -> GBK -> UTF-8")


def test_detect_encoding():
    """测试编码检测"""
    # UTF-8
    utf8_data = "你好".encode("utf-8")
    detected = detect_encoding(utf8_data)
    assert detected == "utf-8"
    print(f"✓ 编码检测: UTF-8 字符串检测为 '{detected}'")

    # 带 BOM 的 UTF-8
    bom_utf8 = b"\xef\xbb\xbfHello"
    detected = detect_encoding(bom_utf8)
    assert detected == "utf-8-sig"
    print(f"✓ 编码检测: BOM UTF-8 检测为 '{detected}'")


def test_is_valid_encoding():
    """测试编码有效性检查"""
    assert is_valid_encoding("utf-8") == True
    assert is_valid_encoding("gbk") == True
    assert is_valid_encoding("invalid-encoding") == False

    print("✓ 编码有效性检查")


def test_get_encoding_name():
    """测试获取编码友好名称"""
    assert "GBK (简体中文)" in get_encoding_name("gbk")
    assert "UTF-8" in get_encoding_name("utf-8")

    print("✓ 获取编码友好名称")


def test_safe_decode():
    """测试安全解码"""
    # 正常情况
    data = "你好".encode("utf-8")
    text = safe_decode(data, "utf-8")
    assert text == "你好"

    # 损坏的 UTF-8，使用 latin-1 回退
    corrupted = b"\xff\xfe\xfd\xfc"
    text = safe_decode(corrupted, "utf-8", "latin-1")
    assert isinstance(text, str)

    print("✓ 安全解码")


def test_safe_encode():
    """测试安全编码"""
    # 正常情况
    text = "你好"
    data = safe_encode(text, "utf-8")
    assert data == "你好".encode("utf-8")

    print("✓ 安全编码")


def test_bom_handling():
    """测试 BOM 处理"""
    # UTF-8 BOM
    bom = get_bom("utf-8-sig")
    assert bom == b"\xef\xbb\xbf"

    # 移除 BOM
    data = b"\xef\xbb\xbfHello"
    stripped, encoding = strip_bom(data)
    assert stripped == b"Hello"
    assert encoding == "utf-8-sig"

    print("✓ BOM 处理")


def test_supported_encodings():
    """测试支持的编码列表"""
    encodings = get_supported_encodings()
    assert "utf-8" in encodings
    assert "gbk" in encodings
    assert "big5" in encodings

    print(f"✓ 支持 {len(encodings)} 种编码")


def test_round_trip():
    """测试往返转换"""
    test_cases = [
        ("你好", "utf-8", "gbk"),
        ("繁體中文", "utf-8", "big5"),
        ("Hello World", "utf-8", "ascii"),
        ("Ça fait 200 ans", "utf-8", "latin-1"),
    ]

    for text, src_enc, dst_enc in test_cases:
        data = text.encode(src_enc)
        converted = convert_encoding(data, src_enc, dst_enc)
        back = converted.decode(dst_enc)
        assert back == text, f"往返转换失败: {text} -> {dst_enc}"
        print(f"✓ 往返转换: '{text}' -> {dst_enc}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试字符编码转换工具")
    print("=" * 60)
    print()

    test_utf8_to_gbk()
    test_gbk_to_utf8()
    test_utf8_to_big5()
    test_big5_to_utf8()
    test_convert_encoding()
    test_detect_encoding()
    test_is_valid_encoding()
    test_get_encoding_name()
    test_safe_decode()
    test_safe_encode()
    test_bom_handling()
    test_supported_encodings()
    test_round_trip()

    print()
    print("=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
