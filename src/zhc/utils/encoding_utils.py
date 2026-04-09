# -*- coding: utf-8 -*-
"""
字符编码转换工具

提供常用编码之间的转换功能，支持中文编码（GBK、Big5）和 UTF-8。

作者：阿福
日期：2026-04-09
"""

from typing import Optional, Tuple, List
import codecs


class EncodingError(Exception):
    """编码转换错误"""

    def __init__(
        self, message: str, source_encoding: str = None, target_encoding: str = None
    ):
        self.message = message
        self.source_encoding = source_encoding
        self.target_encoding = target_encoding
        super().__init__(self.message)


# 支持的编码列表
SUPPORTED_ENCODINGS = {
    "utf-8": "UTF-8",
    "utf8": "UTF-8",
    "gbk": "GBK (简体中文)",
    "gb2312": "GB2312 (简体中文)",
    "gb18030": "GB18030 (中文超集)",
    "big5": "Big5 (繁体中文)",
    "utf-16": "UTF-16",
    "utf-16le": "UTF-16 Little Endian",
    "utf-16be": "UTF-16 Big Endian",
    "utf-32": "UTF-32",
    "ascii": "ASCII",
    "latin-1": "Latin-1 (ISO-8859-1)",
    "iso-8859-1": "ISO-8859-1",
}


def get_supported_encodings() -> List[str]:
    """
    获取支持的编码列表

    Returns:
        编码名称列表
    """
    return list(SUPPORTED_ENCODINGS.keys())


def detect_encoding(data: bytes, default: str = "utf-8") -> str:
    """
    尝试检测字节序列的编码

    Args:
        data: 字节数据
        default: 默认编码

    Returns:
        检测到的编码名称

    Note:
        这是一个简单的启发式检测，不保证100%准确。
        对于精确检测，建议使用 chardet 库。
    """
    # 检查 BOM (Byte Order Mark)
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if data.startswith(b"\xff\xfe"):
        return "utf-16le"
    if data.startswith(b"\xfe\xff"):
        return "utf-16be"

    # 尝试 UTF-8
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # 尝试 GBK (简体中文)
    try:
        data.decode("gbk")
        # 检查是否包含常见中文字符
        decoded = data.decode("gbk")
        if any("\u4e00" <= c <= "\u9fff" for c in decoded):
            return "gbk"
    except UnicodeDecodeError:
        pass

    # 尝试 Big5 (繁体中文)
    try:
        data.decode("big5")
        decoded = data.decode("big5")
        if any("\u4e00" <= c <= "\u9fff" for c in decoded):
            return "big5"
    except UnicodeDecodeError:
        pass

    # 尝试 Latin-1 (总是成功)
    try:
        data.decode("latin-1")
        return "latin-1"
    except UnicodeDecodeError:
        pass

    return default


def convert_encoding(
    data: bytes, source_encoding: str, target_encoding: str, errors: str = "strict"
) -> bytes:
    """
    转换字节序列的编码

    Args:
        data: 源字节数据
        source_encoding: 源编码
        target_encoding: 目标编码
        errors: 错误处理方式 ('strict', 'ignore', 'replace')

    Returns:
        转换后的字节数据

    Raises:
        EncodingError: 编码转换失败
    """
    try:
        # 先解码为 Unicode
        text = data.decode(source_encoding, errors=errors)
        # 再编码为目标编码
        return text.encode(target_encoding, errors=errors)
    except UnicodeDecodeError as e:
        raise EncodingError(
            f"解码失败: {e}",
            source_encoding=source_encoding,
            target_encoding=target_encoding,
        )
    except UnicodeEncodeError as e:
        raise EncodingError(
            f"编码失败: {e}",
            source_encoding=source_encoding,
            target_encoding=target_encoding,
        )


def utf8_to_gbk(text: str, errors: str = "strict") -> bytes:
    """
    将 UTF-8 字符串转换为 GBK 编码

    Args:
        text: UTF-8 字符串
        errors: 错误处理方式

    Returns:
        GBK 编码的字节
    """
    return text.encode("gbk", errors=errors)


def gbk_to_utf8(data: bytes, errors: str = "strict") -> str:
    """
    将 GBK 编码的字节转换为 UTF-8 字符串

    Args:
        data: GBK 编码的字节
        errors: 错误处理方式

    Returns:
        UTF-8 字符串
    """
    return data.decode("gbk", errors=errors)


def utf8_to_big5(text: str, errors: str = "strict") -> bytes:
    """
    将 UTF-8 字符串转换为 Big5 编码

    Args:
        text: UTF-8 字符串
        errors: 错误处理方式

    Returns:
        Big5 编码的字节
    """
    return text.encode("big5", errors=errors)


def big5_to_utf8(data: bytes, errors: str = "strict") -> str:
    """
    将 Big5 编码的字节转换为 UTF-8 字符串

    Args:
        data: Big5 编码的字节
        errors: 错误处理方式

    Returns:
        UTF-8 字符串
    """
    return data.decode("big5", errors=errors)


def is_valid_encoding(encoding: str) -> bool:
    """
    检查编码名称是否有效

    Args:
        encoding: 编码名称

    Returns:
        是否有效
    """
    try:
        codecs.lookup(encoding)
        return True
    except LookupError:
        return False


def get_encoding_name(encoding: str) -> str:
    """
    获取编码的友好名称

    Args:
        encoding: 编码名称

    Returns:
        友好名称
    """
    encoding_lower = encoding.lower()
    return SUPPORTED_ENCODINGS.get(encoding_lower, encoding)


def safe_decode(data: bytes, encoding: str = "utf-8", fallback: str = "latin-1") -> str:
    """
    安全解码字节序列，失败时使用备用编码

    Args:
        data: 字节数据
        encoding: 首选编码
        fallback: 备用编码

    Returns:
        解码后的字符串
    """
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        try:
            return data.decode(fallback)
        except UnicodeDecodeError:
            # 最后尝试忽略错误
            return data.decode(fallback, errors="replace")


def safe_encode(text: str, encoding: str = "utf-8", fallback: str = "latin-1") -> bytes:
    """
    安全编码字符串，失败时使用备用编码

    Args:
        text: 字符串
        encoding: 首选编码
        fallback: 备用编码

    Returns:
        编码后的字节
    """
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        try:
            return text.encode(fallback)
        except UnicodeEncodeError:
            # 最后尝试忽略错误
            return text.encode(fallback, errors="replace")


def convert_file_encoding(
    input_path: str,
    output_path: str,
    source_encoding: str,
    target_encoding: str,
    errors: str = "strict",
) -> Tuple[int, int]:
    """
    转换文件的编码

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        source_encoding: 源编码
        target_encoding: 目标编码
        errors: 错误处理方式

    Returns:
        (读取字节数, 写入字节数)

    Raises:
        EncodingError: 编码转换失败
        IOError: 文件操作失败
    """
    # 读取源文件
    with open(input_path, "rb") as f:
        data = f.read()

    # 转换编码
    converted = convert_encoding(data, source_encoding, target_encoding, errors)

    # 写入目标文件
    with open(output_path, "wb") as f:
        f.write(converted)

    return len(data), len(converted)


def get_bom(encoding: str) -> Optional[bytes]:
    """
    获取编码的 BOM (Byte Order Mark)

    Args:
        encoding: 编码名称

    Returns:
        BOM 字节，如果没有则返回 None
    """
    boms = {
        "utf-8-sig": b"\xef\xbb\xbf",
        "utf-16le": b"\xff\xfe",
        "utf-16be": b"\xfe\xff",
        "utf-32le": b"\xff\xfe\x00\x00",
        "utf-32be": b"\x00\x00\xfe\xff",
    }
    return boms.get(encoding.lower())


def strip_bom(data: bytes) -> Tuple[bytes, Optional[str]]:
    """
    移除字节序列的 BOM

    Args:
        data: 字节数据

    Returns:
        (移除 BOM 后的数据, 检测到的编码)
    """
    # UTF-8 BOM
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:], "utf-8-sig"

    # UTF-16 LE BOM
    if data.startswith(b"\xff\xfe"):
        return data[2:], "utf-16le"

    # UTF-16 BE BOM
    if data.startswith(b"\xfe\xff"):
        return data[2:], "utf-16be"

    # UTF-32 LE BOM
    if data.startswith(b"\xff\xfe\x00\x00"):
        return data[4:], "utf-32le"

    # UTF-32 BE BOM
    if data.startswith(b"\x00\x00\xfe\xff"):
        return data[4:], "utf-32be"

    return data, None
