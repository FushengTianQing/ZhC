# -*- coding: utf-8 -*-
"""
encoding_binding.py - 编码转换的 Python 绑定

提供 C 接口的 Python 实现，使用 encoding_utils.py 的功能

作者：阿福
日期：2026-04-10
"""

from typing import Optional, Tuple

# 导入 encoding_utils 的功能
from ..utils.encoding_utils import (
    EncodingError,
    convert_encoding,
    detect_encoding,
)

# 编码类型映射
_ENCODING_MAP = {
    0: "auto",  # ZHC_ENCODING_AUTO
    1: "utf-8",  # ZHC_ENCODING_UTF8
    2: "gbk",  # ZHC_ENCODING_GBK
    3: "gb2312",  # ZHC_ENCODING_GB2312
    4: "gb18030",  # ZHC_ENCODING_GB18030
    5: "big5",  # ZHC_ENCODING_BIG5
    6: "shift-jis",  # ZHC_ENCODING_SHIFT_JIS
    7: "euc-kr",  # ZHC_ENCODING_EUC_KR
    8: "iso-8859-1",  # ZHC_ENCODING_ISO_8859_1
    9: "windows-1252",  # ZHC_ENCODING_WINDOWS_1252
    10: "ascii",  # ZHC_ENCODING_ASCII
    11: "utf-16",  # ZHC_ENCODING_UTF16
    12: "utf-16le",  # ZHC_ENCODING_UTF16LE
    13: "utf-16be",  # ZHC_ENCODING_UTF16BE
    14: "utf-32",  # ZHC_ENCODING_UTF32
}

_REVERSE_ENCODING_MAP = {v: k for k, v in _ENCODING_MAP.items()}


def get_encoding_name(encoding_id: int) -> str:
    """获取编码名称"""
    return _ENCODING_MAP.get(encoding_id, "unknown")


def get_encoding_id(encoding_name: str) -> Optional[int]:
    """根据编码名称获取 ID"""
    return _REVERSE_ENCODING_MAP.get(encoding_name.lower())


def py_convert_encoding(
    input_data: bytes,
    from_encoding: int,
    to_encoding: int,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Python 实现的编码转换

    Args:
        input_data: 输入字节数据
        from_encoding: 源编码 ID
        to_encoding: 目标编码 ID

    Returns:
        (转换后的数据, 错误信息)
    """
    source = _ENCODING_MAP.get(from_encoding, "utf-8")
    target = _ENCODING_MAP.get(to_encoding, "utf-8")

    try:
        result = convert_encoding(input_data, source, target)
        return result, None
    except EncodingError as e:
        return None, str(e)


def py_detect_encoding(data: bytes) -> Tuple[int, float]:
    """
    Python 实现的编码检测

    Args:
        data: 输入字节数据

    Returns:
        (编码 ID, 置信度)
    """
    detected = detect_encoding(data)

    # 映射到我们的编码 ID
    encoding_id = _REVERSE_ENCODING_MAP.get(detected.lower(), 1)  # 默认为 UTF-8

    # 根据检测结果的确定性设置置信度
    # 这是一个简化的实现
    confidence = 0.8 if detected in ("utf-8", "gbk", "big5") else 0.5

    return encoding_id, confidence


def py_normalize_unicode(
    input_str: str,
    form: int,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Python 实现的 Unicode 规范化

    Args:
        input_str: 输入字符串
        form: 规范化形式 (0=NFC, 1=NFD, 2=NFKC, 3=NFKD)

    Returns:
        (规范化后的字符串, 错误信息)
    """
    import unicodedata

    form_map = {
        0: "NFC",  # 标准组合
        1: "NFD",  # 标准分解
        2: "NFKC",  # 兼容组合
        3: "NFKD",  # 兼容分解
    }

    norm_form = form_map.get(form, "NFC")

    try:
        result = unicodedata.normalize(norm_form, input_str)
        return result, None
    except Exception as e:
        return None, str(e)


# ============================================================================
# 便捷函数
# ============================================================================


def utf8_to_gbk(text: str) -> bytes:
    """UTF-8 字符串转 GBK 字节"""
    from ..utils.encoding_utils import utf8_to_gbk as _utf8_to_gbk

    return _utf8_to_gbk(text)


def gbk_to_utf8(data: bytes) -> str:
    """GBK 字节转 UTF-8 字符串"""
    from ..utils.encoding_utils import gbk_to_utf8 as _gbk_to_utf8

    return _gbk_to_utf8(data)


def utf8_to_big5(text: str) -> bytes:
    """UTF-8 字符串转 Big5 字节"""
    from ..utils.encoding_utils import utf8_to_big5 as _utf8_to_big5

    return _utf8_to_big5(text)


def big5_to_utf8(data: bytes) -> str:
    """Big5 字节转 UTF-8 字符串"""
    from ..utils.encoding_utils import big5_to_utf8 as _big5_to_utf8

    return _big5_to_utf8(data)


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    # 测试编码转换
    text = "你好，世界！"
    print(f"原文: {text}")

    # UTF-8 转 GBK
    gbk_data = utf8_to_gbk(text)
    print(f"GBK: {gbk_data.hex()}")

    # GBK 转 UTF-8
    restored = gbk_to_utf8(gbk_data)
    print(f"恢复: {restored}")

    # 测试编码检测
    detected, confidence = py_detect_encoding(gbk_data)
    print(f"检测: {get_encoding_name(detected)} (置信度: {confidence:.1%})")

    # 测试 Unicode 规范化
    test_str = "café"
    print(f"\n规范化测试: {test_str}")

    for form, name in [(0, "NFC"), (1, "NFD"), (2, "NFKC"), (3, "NFKD")]:
        normalized, _ = py_normalize_unicode(test_str, form)
        print(f"  {name}: {repr(normalized)}")
