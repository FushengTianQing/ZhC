"""
Unicode 处理工具

提供 Unicode 字符处理、编码转换等功能。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from typing import List


class UnicodeUtils:
    """Unicode 处理工具类"""

    # CJK 统一汉字范围
    CJK_BASIC_RANGE = (0x4E00, 0x9FFF)  # 基本汉字
    CJK_EXT_A_RANGE = (0x3400, 0x4DBF)  # 扩展 A
    CJK_EXT_B_RANGE = (0x20000, 0x2A6DF)  # 扩展 B
    CJK_EXT_C_RANGE = (0x2A700, 0x2B73F)  # 扩展 C
    CJK_EXT_D_RANGE = (0x2B740, 0x2B81F)  # 扩展 D
    CJK_EXT_E_RANGE = (0x2B820, 0x2CEAF)  # 扩展 E

    @staticmethod
    def char_to_codepoint(char: str) -> int:
        """
        将字符转换为 Unicode 码点

        Args:
            char: 单个字符

        Returns:
            Unicode 码点
        """
        if not char:
            return 0
        return ord(char[0])

    @staticmethod
    def codepoint_to_char(codepoint: int) -> str:
        """
        将 Unicode 码点转换为字符

        Args:
            codepoint: Unicode 码点

        Returns:
            字符
        """
        return chr(codepoint)

    @staticmethod
    def string_to_codepoints(string: str) -> List[int]:
        """
        将字符串转换为 Unicode 码点列表

        Args:
            string: 字符串

        Returns:
            Unicode 码点列表
        """
        return [ord(c) for c in string]

    @staticmethod
    def codepoints_to_string(codepoints: List[int]) -> str:
        """
        将 Unicode 码点列表转换为字符串

        Args:
            codepoints: Unicode 码点列表

        Returns:
            字符串
        """
        return "".join(chr(cp) for cp in codepoints if cp)

    @staticmethod
    def is_chinese_char(char: str) -> bool:
        """
        判断是否为中文字符

        Args:
            char: 字符

        Returns:
            是否为中文
        """
        if not char:
            return False

        codepoint = ord(char[0])
        return UnicodeUtils._is_in_cjk_range(codepoint)

    @staticmethod
    def _is_in_cjk_range(codepoint: int) -> bool:
        """检查码点是否在 CJK 范围内"""
        in_basic = (
            UnicodeUtils.CJK_BASIC_RANGE[0]
            <= codepoint
            <= UnicodeUtils.CJK_BASIC_RANGE[1]
        )
        in_ext_a = (
            UnicodeUtils.CJK_EXT_A_RANGE[0]
            <= codepoint
            <= UnicodeUtils.CJK_EXT_A_RANGE[1]
        )
        in_ext_b = (
            UnicodeUtils.CJK_EXT_B_RANGE[0]
            <= codepoint
            <= UnicodeUtils.CJK_EXT_B_RANGE[1]
        )
        in_ext_c = (
            UnicodeUtils.CJK_EXT_C_RANGE[0]
            <= codepoint
            <= UnicodeUtils.CJK_EXT_C_RANGE[1]
        )
        in_ext_d = (
            UnicodeUtils.CJK_EXT_D_RANGE[0]
            <= codepoint
            <= UnicodeUtils.CJK_EXT_D_RANGE[1]
        )
        in_ext_e = (
            UnicodeUtils.CJK_EXT_E_RANGE[0]
            <= codepoint
            <= UnicodeUtils.CJK_EXT_E_RANGE[1]
        )

        return in_basic or in_ext_a or in_ext_b or in_ext_c or in_ext_d or in_ext_e

    @staticmethod
    def is_ascii_char(char: str) -> bool:
        """
        判断是否为 ASCII 字符

        Args:
            char: 字符

        Returns:
            是否为 ASCII
        """
        if not char:
            return False
        return ord(char[0]) < 128

    @staticmethod
    def is_cjk_string(string: str) -> bool:
        """
        判断字符串是否包含中文字符

        Args:
            string: 字符串

        Returns:
            是否包含中文
        """
        return any(UnicodeUtils.is_chinese_char(c) for c in string)

    @staticmethod
    def get_char_name(codepoint: int) -> str:
        """
        获取 Unicode 字符名称

        Args:
            codepoint: Unicode 码点

        Returns:
            字符名称
        """
        import unicodedata

        try:
            return unicodedata.name(chr(codepoint))
        except ValueError:
            return f"U+{codepoint:04X}"

    @staticmethod
    def get_char_category(codepoint: int) -> str:
        """
        获取 Unicode 字符类别

        Args:
            codepoint: Unicode 码点

        Returns:
            字符类别（如 'Lo' 表示汉字）
        """
        import unicodedata

        return unicodedata.category(chr(codepoint))

    @staticmethod
    def get_char_block(codepoint: int) -> str:
        """
        获取 Unicode 字符所在的区块

        Args:
            codepoint: Unicode 码点

        Returns:
            区块名称
        """
        import unicodedata

        return unicodedata.block(chr(codepoint))

    @staticmethod
    def utf8_encode(string: str) -> bytes:
        """
        将字符串编码为 UTF-8

        Args:
            string: 字符串

        Returns:
            UTF-8 字节序列
        """
        return string.encode("utf-8")

    @staticmethod
    def utf8_decode(data: bytes) -> str:
        """
        将 UTF-8 字节序列解码为字符串

        Args:
            data: UTF-8 字节序列

        Returns:
            字符串
        """
        return data.decode("utf-8")

    @staticmethod
    def to_utf32_list(string: str) -> List[int]:
        """
        将字符串转换为 UTF-32 码点列表（宽字符）

        Args:
            string: 字符串

        Returns:
            UTF-32 码点列表
        """
        return [ord(c) for c in string]

    @staticmethod
    def from_utf32_list(codepoints: List[int]) -> str:
        """
        将 UTF-32 码点列表转换为字符串

        Args:
            codepoints: UTF-32 码点列表

        Returns:
            字符串
        """
        return "".join(chr(cp) for cp in codepoints if cp)


# 导出公共 API
__all__ = [
    "UnicodeUtils",
]
