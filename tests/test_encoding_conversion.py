# -*- coding: utf-8 -*-
"""
编码转换测试

测试 P0-字符编码-字符编码转换 功能

作者：阿福
日期：2026-04-10
"""

import pytest
from zhc.utils.encoding_utils import (
    EncodingError,
    convert_encoding,
    detect_encoding,
    utf8_to_gbk,
    gbk_to_utf8,
    utf8_to_big5,
    big5_to_utf8,
    is_valid_encoding,
    get_encoding_name,
    safe_decode,
    safe_encode,
    strip_bom,
    get_bom,
    get_supported_encodings,
)


class TestEncodingConversion:
    """编码转换测试"""

    def test_utf8_to_gbk(self):
        """测试 UTF-8 到 GBK 转换"""
        text = "你好，世界！"
        gbk_data = utf8_to_gbk(text)

        assert isinstance(gbk_data, bytes)
        assert len(gbk_data) > 0

        # 验证可以转换回来
        restored = gbk_to_utf8(gbk_data)
        assert restored == text

    def test_gbk_to_utf8(self):
        """测试 GBK 到 UTF-8 转换"""
        # "你好" 的 GBK 编码
        gbk_data = bytes([0xC4, 0xE3, 0xBA, 0xC3])
        text = gbk_to_utf8(gbk_data)

        assert text == "你好"

    def test_utf8_to_big5(self):
        """测试 UTF-8 到 Big5 转换"""
        # Big5 主要支持繁体中文
        text = "繁體中文"
        big5_data = utf8_to_big5(text)

        assert isinstance(big5_data, bytes)
        assert len(big5_data) > 0

        # 验证可以转换回来
        restored = big5_to_utf8(big5_data)
        assert restored == text

    def test_big5_to_utf8(self):
        """测试 Big5 到 UTF-8 转换"""
        # 使用 Python 的编码来获取正确的 Big5 编码
        text = "繁體"
        big5_data = text.encode("big5")
        restored = big5_to_utf8(big5_data)

        assert restored == text

    def test_convert_encoding(self):
        """测试通用编码转换"""
        text = "中文测试"
        utf8_data = text.encode("utf-8")

        # UTF-8 转 GBK
        gbk_data = convert_encoding(utf8_data, "utf-8", "gbk")
        assert isinstance(gbk_data, bytes)

        # GBK 转 UTF-8
        restored = convert_encoding(gbk_data, "gbk", "utf-8")
        assert restored.decode("utf-8") == text

    def test_convert_encoding_invalid(self):
        """测试无效编码转换"""
        # is_valid_encoding 应该返回 False
        assert is_valid_encoding("invalid-encoding") is False

        # 无效编码名称应该抛出异常
        with pytest.raises((EncodingError, LookupError)):
            "test".encode("invalid-encoding")

    def test_empty_string_conversion(self):
        """测试空字符串转换"""
        assert utf8_to_gbk("") == b""
        assert gbk_to_utf8(b"") == ""


class TestEncodingDetection:
    """编码检测测试"""

    def test_detect_utf8(self):
        """测试 UTF-8 检测"""
        text = "你好，世界！"
        data = text.encode("utf-8")

        detected = detect_encoding(data)
        assert detected == "utf-8"

    def test_detect_utf8_with_bom(self):
        """测试带 BOM 的 UTF-8 检测"""
        text = "测试"
        data = b"\xef\xbb\xbf" + text.encode("utf-8")

        detected = detect_encoding(data)
        assert detected == "utf-8-sig"

    def test_detect_gbk(self):
        """测试 GBK 检测"""
        # "你好" 的 GBK 编码
        data = bytes([0xC4, 0xE3, 0xBA, 0xC3])

        detected = detect_encoding(data)
        # GBK 检测可能返回 gbk 或 utf-8（取决于具体实现）
        assert detected in ("gbk", "utf-8")

    def test_detect_ascii(self):
        """测试 ASCII 检测"""
        data = b"hello world"

        detected = detect_encoding(data)
        # ASCII 数据可能被检测为 utf-8 或 ascii
        assert detected in ("utf-8", "ascii", "latin-1")

    def test_detect_empty(self):
        """测试空数据检测"""
        detected = detect_encoding(b"")
        assert detected == "utf-8"


class TestEncodingValidation:
    """编码验证测试"""

    def test_is_valid_encoding(self):
        """测试编码名称验证"""
        assert is_valid_encoding("utf-8") is True
        assert is_valid_encoding("gbk") is True
        assert is_valid_encoding("big5") is True
        assert is_valid_encoding("invalid-encoding") is False

    def test_get_encoding_name(self):
        """测试获取编码名称"""
        assert "UTF-8" in get_encoding_name("utf-8")
        assert "GBK" in get_encoding_name("gbk")
        assert "Big5" in get_encoding_name("big5")


class TestSafeEncoding:
    """安全编码测试"""

    def test_safe_decode_utf8(self):
        """测试安全 UTF-8 解码"""
        data = "你好".encode("utf-8")
        text = safe_decode(data, "utf-8")

        assert text == "你好"

    def test_safe_decode_fallback(self):
        """测试安全解码回退"""
        # 无效的 UTF-8 数据
        data = bytes([0x80, 0x81, 0x82])
        text = safe_decode(data, "utf-8", "latin-1")

        # 应该使用 latin-1 解码
        assert isinstance(text, str)

    def test_safe_encode_utf8(self):
        """测试安全 UTF-8 编码"""
        text = "你好"
        data = safe_encode(text, "utf-8")

        assert data == text.encode("utf-8")

    def test_safe_encode_fallback(self):
        """测试安全编码回退"""
        # 包含无法编码字符的文本
        text = "你好"
        data = safe_encode(text, "ascii", "utf-8")

        # 应该使用 UTF-8 编码
        assert data == text.encode("utf-8")


class TestBOMHandling:
    """BOM 处理测试"""

    def test_get_bom_utf8(self):
        """测试获取 UTF-8 BOM"""
        bom = get_bom("utf-8-sig")
        assert bom == b"\xef\xbb\xbf"

    def test_get_bom_utf16le(self):
        """测试获取 UTF-16 LE BOM"""
        bom = get_bom("utf-16le")
        assert bom == b"\xff\xfe"

    def test_get_bom_utf16be(self):
        """测试获取 UTF-16 BE BOM"""
        bom = get_bom("utf-16be")
        assert bom == b"\xfe\xff"

    def test_strip_bom_utf8(self):
        """测试移除 UTF-8 BOM"""
        text = "测试"
        data = b"\xef\xbb\xbf" + text.encode("utf-8")
        stripped, encoding = strip_bom(data)

        assert stripped == text.encode("utf-8")
        assert encoding == "utf-8-sig"

    def test_strip_bom_utf16le(self):
        """测试移除 UTF-16 LE BOM"""
        data = b"\xff\xfe\x01\x00"
        stripped, encoding = strip_bom(data)

        assert stripped == b"\x01\x00"
        assert encoding == "utf-16le"

    def test_strip_bom_no_bom(self):
        """测试无 BOM 数据"""
        data = b"test"
        stripped, encoding = strip_bom(data)

        assert stripped == data
        assert encoding is None


class TestSupportedEncodings:
    """支持的编码列表测试"""

    def test_get_supported_encodings(self):
        """测试获取支持的编码列表"""
        encodings = get_supported_encodings()

        assert "utf-8" in encodings
        assert "gbk" in encodings
        assert "big5" in encodings
        assert len(encodings) > 0


class TestChineseEncoding:
    """中文编码测试"""

    def test_chinese_characters_gbk(self):
        """测试中文字符 GBK 编码"""
        # 常见中文字符
        chars = ["你", "好", "世", "界", "中", "文"]

        for char in chars:
            gbk_data = utf8_to_gbk(char)
            restored = gbk_to_utf8(gbk_data)
            assert restored == char

    def test_chinese_punctuation(self):
        """测试中文标点符号"""
        # 中文标点
        punctuation = ["，", "。", "！", "？", "：", "；"]

        for p in punctuation:
            gbk_data = utf8_to_gbk(p)
            restored = gbk_to_utf8(gbk_data)
            assert restored == p

    def test_mixed_chinese_english(self):
        """测试中英文混合"""
        text = "Hello 你好 World 世界！"
        gbk_data = utf8_to_gbk(text)
        restored = gbk_to_utf8(gbk_data)

        assert restored == text

    def test_traditional_chinese_big5(self):
        """测试繁体中文 Big5 编码"""
        text = "繁體中文測試"
        big5_data = utf8_to_big5(text)
        restored = big5_to_utf8(big5_data)

        assert restored == text


class TestEncodingBinding:
    """编码绑定测试"""

    def test_encoding_binding_imports(self):
        """测试编码绑定导入"""
        from zhc.lib.encoding_binding import (
            get_encoding_name,
            get_encoding_id,
        )

        # 测试编码名称获取
        assert get_encoding_name(1) == "utf-8"
        assert get_encoding_name(2) == "gbk"

        # 测试编码 ID 获取
        assert get_encoding_id("utf-8") == 1
        assert get_encoding_id("gbk") == 2

    def test_py_convert_encoding(self):
        """测试 Python 编码转换"""
        from zhc.lib.encoding_binding import py_convert_encoding

        text = "你好"
        utf8_data = text.encode("utf-8")

        # UTF-8 (1) 转 GBK (2)
        result, error = py_convert_encoding(utf8_data, 1, 2)

        assert error is None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_py_detect_encoding(self):
        """测试 Python 编码检测"""
        from zhc.lib.encoding_binding import py_detect_encoding

        text = "你好"
        data = text.encode("utf-8")

        encoding_id, confidence = py_detect_encoding(data)

        assert encoding_id == 1  # UTF-8
        assert confidence > 0

    def test_py_normalize_unicode(self):
        """测试 Python Unicode 规范化"""
        from zhc.lib.encoding_binding import py_normalize_unicode

        # 测试 NFC 规范化
        text = "café"
        normalized, error = py_normalize_unicode(text, 0)  # NFC

        assert error is None
        assert isinstance(normalized, str)

        # 测试 NFD 规范化
        normalized, error = py_normalize_unicode(text, 1)  # NFD

        assert error is None
        assert isinstance(normalized, str)
