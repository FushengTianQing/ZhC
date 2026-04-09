# -*- coding: utf-8 -*-
"""
UTF-8 编码处理工具

提供 UTF-8 字符串的字节级操作和字符级操作的工具函数。
支持中文字符等多字节 UTF-8 字符的正确处理。

作者：阿福
日期：2026-04-09
"""

from typing import List, Tuple, Optional


def utf8_char_length(first_byte: int) -> int:
    """
    根据 UTF-8 首字节判断字符占用的字节数

    Args:
        first_byte: UTF-8 字符的首字节

    Returns:
        字符占用的字节数 (1-4)，无效首字节返回 1

    UTF-8 编码规则:
        0xxxxxxx     - 1 字节 (ASCII)
        110xxxxx     - 2 字节
        1110xxxx     - 3 字节 (中文、日文、韩文等)
        11110xxx     - 4 字节 (emoji、部分生僻字)
    """
    if first_byte < 0x80:
        # ASCII: 0xxxxxxx
        return 1
    elif first_byte < 0xC0:
        # 非法首字节 (续字节)
        return 1
    elif first_byte < 0xE0:
        # 110xxxxx - 2 字节
        return 2
    elif first_byte < 0xF0:
        # 1110xxxx - 3 字节
        return 3
    elif first_byte < 0xF8:
        # 11110xxx - 4 字节
        return 4
    else:
        # 非法首字节
        return 1


def utf8_encode(text: str) -> bytes:
    """
    将字符串编码为 UTF-8 字节

    Args:
        text: 输入字符串

    Returns:
        UTF-8 编码的字节串

    Example:
        >>> utf8_encode("你好")
        b'\\xe4\\xbd\\xa0\\xe5\\xa5\\xbd'
    """
    return text.encode("utf-8")


def utf8_decode(data: bytes) -> str:
    """
    将 UTF-8 字节解码为字符串

    Args:
        data: UTF-8 字节串

    Returns:
        解码后的字符串

    Example:
        >>> utf8_decode(b'\\xe4\\xbd\\xa0\\xe5\\xa5\\xbd')
        '你好'
    """
    return data.decode("utf-8")


def utf8_char_count(text: str) -> int:
    """
    计算字符串中的字符数量（按字符而非字节）

    Args:
        text: 输入字符串

    Returns:
        字符数量

    Example:
        >>> utf8_char_count("你好世界")
        4
        >>> utf8_char_count("Hello")
        5
        >>> utf8_char_count("Hello你好")
        7
    """
    return len(text)


def utf8_byte_length(text: str) -> int:
    """
    计算字符串的 UTF-8 字节长度

    Args:
        text: 输入字符串

    Returns:
        UTF-8 字节长度

    Example:
        >>> utf8_byte_length("你好")  # "你"=3字节, "好"=3字节
        6
        >>> utf8_byte_length("A")  # ASCII=1字节
        1
    """
    return len(text.encode("utf-8"))


def utf8_chars(text: str) -> List[str]:
    """
    将字符串拆分为字符列表

    Args:
        text: 输入字符串

    Returns:
        字符列表

    Example:
        >>> utf8_chars("你好")
        ['你', '好']
        >>> utf8_chars("Hello世界")
        ['H', 'e', 'l', 'l', 'o', '世', '界']
    """
    return list(text)


def utf8_substring(text: str, start: int, length: Optional[int] = None) -> str:
    """
    按字符数截取子字符串

    Args:
        text: 输入字符串
        start: 起始字符位置（从 0 开始）
        length: 截取字符数，None 表示到末尾

    Returns:
        截取后的子字符串

    Example:
        >>> utf8_substring("你好世界", 0, 2)
        '你好'
        >>> utf8_substring("你好世界", 2)
        '世界'
        >>> utf8_substring("Hello你好", 3, 2)
        'lo你'
    """
    chars = list(text)
    if length is None:
        return "".join(chars[start:])
    return "".join(chars[start : start + length])


def utf8_slice(text: str, start: int, end: int) -> str:
    """
    按字符位置切片字符串

    Args:
        text: 输入字符串
        start: 起始位置（包含）
        end: 结束位置（不包含）

    Returns:
        切片后的子字符串

    Example:
        >>> utf8_slice("你好世界", 1, 3)
        '好世'
    """
    chars = list(text)
    return "".join(chars[start:end])


def utf8_index_to_byte(text: str, char_index: int) -> int:
    """
    将字符索引转换为字节索引

    Args:
        text: 输入字符串
        char_index: 字符索引（从 0 开始）

    Returns:
        对应的字节索引

    Example:
        >>> s = "你好"
        >>> utf8_index_to_byte(s, 0)  # "你"的起始字节
        0
        >>> utf8_index_to_byte(s, 1)  # "好"的起始字节
        3
    """
    encoded = text.encode("utf-8")
    char_count = 0
    byte_index = 0

    while byte_index < len(encoded) and char_count < char_index:
        byte_index += utf8_char_length(encoded[byte_index])
        char_count += 1

    return byte_index


def utf8_byte_to_index(text: str, byte_index: int) -> int:
    """
    将字节索引转换为字符索引

    Args:
        text: 输入字符串
        byte_index: 字节索引（从 0 开始）

    Returns:
        对应的字符索引

    Example:
        >>> s = "你好"
        >>> utf8_byte_to_index(s, 0)  # "你"的起始字节
        0
        >>> utf8_byte_to_index(s, 3)  # "好"的起始字节
        1
    """
    encoded = text.encode("utf-8")
    char_index = 0
    current_byte = 0

    while current_byte < byte_index and current_byte < len(encoded):
        char_len = utf8_char_length(encoded[current_byte])
        current_byte += char_len
        if current_byte <= byte_index:
            char_index += 1

    return char_index


def utf8_char_at(text: str, index: int) -> Optional[str]:
    """
    获取指定位置的字符

    Args:
        text: 输入字符串
        index: 字符索引（从 0 开始）

    Returns:
        字符，如果索引越界返回 None

    Example:
        >>> utf8_char_at("你好", 0)
        '你'
        >>> utf8_char_at("你好", 1)
        '好'
        >>> utf8_char_at("你好", 2)
        None
    """
    if index < 0 or index >= len(text):
        return None
    return text[index]


def utf8_char_bytes(text: str, index: int) -> Optional[bytes]:
    """
    获取指定位置字符的 UTF-8 字节

    Args:
        text: 输入字符串
        index: 字符索引（从 0 开始）

    Returns:
        字符的 UTF-8 字节，如果索引越界返回 None

    Example:
        >>> utf8_char_bytes("你", 0)
        b'\\xe4\\xbd\\xa0'
    """
    char = utf8_char_at(text, index)
    if char is None:
        return None
    return char.encode("utf-8")


def utf8_validate(data: bytes) -> Tuple[bool, List[int]]:
    """
    验证 UTF-8 字节序列的有效性

    Args:
        data: UTF-8 字节数据

    Returns:
        (是否有效, 无效字节位置列表)

    Example:
        >>> utf8_validate(b"Hello")
        (True, [])
        >>> utf8_validate(b"\\xe4\\xbd\\xa0\\xe5\\xa5\\xbd")
        (True, [])
        >>> utf8_validate(b"\\x80\\x90")  # 非法字节
        (False, [0, 1])
    """
    invalid_positions = []
    i = 0

    while i < len(data):
        byte = data[i]

        if byte < 0x80:
            # ASCII
            i += 1
        elif byte < 0xC0:
            # 非法：续字节出现在首字节位置
            invalid_positions.append(i)
            i += 1
        elif byte < 0xE0:
            # 2 字节序列
            expected = 2
            if i + 1 >= len(data) or not (0x80 <= data[i + 1] < 0xC0):
                invalid_positions.append(i)
            i += expected
        elif byte < 0xF0:
            # 3 字节序列
            expected = 3
            if (
                i + 2 >= len(data)
                or not (0x80 <= data[i + 1] < 0xC0)
                or not (0x80 <= data[i + 2] < 0xC0)
            ):
                invalid_positions.append(i)
            i += expected
        elif byte < 0xF8:
            # 4 字节序列
            expected = 4
            if (
                i + 3 >= len(data)
                or not (0x80 <= data[i + 1] < 0xC0)
                or not (0x80 <= data[i + 2] < 0xC0)
                or not (0x80 <= data[i + 3] < 0xC0)
            ):
                invalid_positions.append(i)
            i += expected
        else:
            # 非法首字节
            invalid_positions.append(i)
            i += 1

    return len(invalid_positions) == 0, invalid_positions


def utf8_truncate(text: str, max_chars: int, suffix: str = "...") -> str:
    """
    按字符数截断字符串

    Args:
        text: 输入字符串
        max_chars: 最大字符数（包含后缀）
        suffix: 截断后缀

    Returns:
        截断后的字符串

    Example:
        >>> utf8_truncate("你好世界", 4)
        '你好世界'
        >>> utf8_truncate("你好世界", 3)
        '你好...'
        >>> utf8_truncate("Hello你好", 7)
        'Hello你好'
        >>> utf8_truncate("Hello你好", 6)
        'Hello你...'
    """
    # 如果文本长度小于等于最大字符数，不需要截断
    if len(text) <= max_chars:
        return text

    suffix_len = len(suffix)

    # 如果后缀比最大长度还长，直接截断后缀
    if suffix_len > max_chars:
        return suffix[:max_chars]

    # 计算可用字符数（留出后缀的空间）
    available = max_chars - suffix_len

    # 截断到可用字符数并添加后缀
    return utf8_substring(text, 0, available) + suffix


def utf8_reverse(text: str) -> str:
    """
    反转字符串（按字符）

    Args:
        text: 输入字符串

    Returns:
        反转后的字符串

    Example:
        >>> utf8_reverse("你好")
        '好你'
        >>> utf8_reverse("Hello世界")
        '界世olleH'
    """
    return "".join(reversed(list(text)))


def utf8_ljust(text: str, width: int, fillchar: str = " ") -> str:
    """
    左对齐字符串到指定宽度（按字符数）

    Args:
        text: 输入字符串
        width: 总宽度
        fillchar: 填充字符

    Returns:
        对齐后的字符串

    Example:
        >>> utf8_ljust("你好", 6)
        '你好  '
        >>> utf8_ljust("Hi", 6)
        'Hi    '
    """
    padding = max(0, width - len(text))
    return text + fillchar * padding


def utf8_rjust(text: str, width: int, fillchar: str = " ") -> str:
    """
    右对齐字符串到指定宽度（按字符数）

    Args:
        text: 输入字符串
        width: 总宽度
        fillchar: 填充字符

    Returns:
        对齐后的字符串

    Example:
        >>> utf8_rjust("你好", 6)
        '  你好'
        >>> utf8_rjust("Hi", 6)
        '    Hi'
    """
    padding = max(0, width - len(text))
    return fillchar * padding + text


def utf8_center(text: str, width: int, fillchar: str = " ") -> str:
    """
    居中对齐字符串到指定宽度（按字符数）

    Args:
        text: 输入字符串
        width: 总宽度
        fillchar: 填充字符

    Returns:
        对齐后的字符串

    Example:
        >>> utf8_center("你好", 6)
        ' 你好 '
        >>> utf8_center("Hi", 7)
        '  Hi  '
    """
    padding = max(0, width - len(text))
    left = padding // 2
    right = padding - left
    return fillchar * left + text + fillchar * right
