"""
C 类型映射器

提供 ZhC 类型与 C/LLVM 类型之间的映射。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import llvmlite.ir as ll


@dataclass
class CTypeInfo:
    """C 类型信息"""

    c_name: str  # C 类型名
    llvm_type: ll.Type  # LLVM 类型
    size: int  # 大小（字节）
    alignment: int  # 对齐（字节）


class CTypeMapper:
    """
    C 类型映射器

    提供 ZhC 类型到 C/LLVM 类型的双向映射。
    """

    # ZhC 类型到 C 类型的基本映射
    ZHC_TO_C: Dict[str, str] = {
        "整数型": "int",
        "短整型": "short",
        "长整型": "long",
        "长长整型": "long long",
        "字符型": "char",
        "布尔型": "bool",
        "浮点型": "float",
        "双精度浮点型": "double",
        "空型": "void",
        "无符号整数型": "unsigned int",
        "无符号短整型": "unsigned short",
        "无符号长整型": "unsigned long",
        "无符号长长整型": "unsigned long long",
        "无符号字符型": "unsigned char",
    }

    def __init__(self, target_platform: str = "linux"):
        """
        初始化映射器

        Args:
            target_platform: 目标平台
        """
        self.target_platform = target_platform
        self._zhc_to_llvm_cache: Dict[str, ll.Type] = {}
        self._init_llvm_type_cache()

    def _init_llvm_type_cache(self):
        """初始化 LLVM 类型缓存"""
        self._llvm_types: Dict[str, ll.Type] = {
            # 整数类型
            "整数型": ll.IntType(32),
            "短整型": ll.IntType(16),
            "长整型": ll.IntType(64),
            "长长整型": ll.IntType(64),
            "字符型": ll.IntType(8),
            "布尔型": ll.IntType(8),
            # 浮点类型
            "浮点型": ll.FloatType(),
            "双精度浮点型": ll.DoubleType(),
            # 特殊类型
            "空型": ll.VoidType(),
            # 无符号类型
            "无符号整数型": ll.IntType(32),
            "无符号短整型": ll.IntType(16),
            "无符号长整型": ll.IntType(64),
            "无符号长长整型": ll.IntType(64),
            "无符号字符型": ll.IntType(8),
        }

        # 平台特定调整
        if self.target_platform == "windows":
            self._llvm_types["长整型"] = ll.IntType(32)  # Windows long 是 32 位
        elif self.target_platform == "macos":
            self._llvm_types["长整型"] = ll.IntType(64)  # macOS long 是 64 位

    def zhc_to_llvm(self, zh_type: str) -> ll.Type:
        """
        将 ZhC 类型转换为 LLVM 类型

        Args:
            zh_type: ZhC 类型名

        Returns:
            LLVM 类型
        """
        if zh_type in self._llvm_types:
            return self._llvm_types[zh_type]

        # 处理指针类型
        if zh_type.endswith("指针") or zh_type.endswith("*"):
            base_type_name = zh_type.rstrip("指针").rstrip("*").strip()
            base_type = self.zhc_to_llvm(base_type_name)
            return ll.PointerType(base_type)

        # 处理数组类型
        if zh_type.startswith("数组<"):
            # 简化处理，实际需要解析数组元素类型
            element_type = self.zhc_to_llvm("整数型")
            return ll.PointerType(element_type)

        # 默认返回 i32
        return ll.IntType(32)

    def zhc_to_c(self, zh_type: str) -> str:
        """
        将 ZhC 类型转换为 C 类型名

        Args:
            zh_type: ZhC 类型名

        Returns:
            C 类型名
        """
        # 处理指针类型
        if zh_type.endswith("指针") or zh_type.endswith("*"):
            base_type_name = zh_type.rstrip("指针").rstrip("*").strip()
            base_c_type = self.zhc_to_c(base_type_name)
            if base_c_type == "void":
                return "void*"
            return f"{base_c_type}*"

        return self.ZHC_TO_C.get(zh_type, zh_type)

    def llvm_to_zhc(self, llvm_type: ll.Type) -> str:
        """
        将 LLVM 类型转换为 ZhC 类型

        Args:
            llvm_type: LLVM 类型

        Returns:
            ZhC 类型名
        """
        if isinstance(llvm_type, ll.IntType):
            if llvm_type.width == 8:
                return "字符型"
            elif llvm_type.width == 16:
                return "短整型"
            elif llvm_type.width == 32:
                return "整数型"
            elif llvm_type.width == 64:
                return "长整型"
        elif isinstance(llvm_type, ll.FloatType):
            return "浮点型"
        elif isinstance(llvm_type, ll.DoubleType):
            return "双精度浮点型"
        elif isinstance(llvm_type, ll.VoidType):
            return "空型"
        elif isinstance(llvm_type, ll.PointerType):
            pointee = llvm_type.pointee
            base_type = self.llvm_to_zhc(pointee)
            return f"{base_type}指针"

        return "整数型"

    def c_to_llvm(self, c_type: str) -> ll.Type:
        """
        将 C 类型名转换为 LLVM 类型

        Args:
            c_type: C 类型名

        Returns:
            LLVM 类型
        """
        # 基本 C 类型映射
        c_type_map = {
            "int": ll.IntType(32),
            "short": ll.IntType(16),
            "long": ll.IntType(64),
            "long long": ll.IntType(64),
            "char": ll.IntType(8),
            "bool": ll.IntType(8),
            "float": ll.FloatType(),
            "double": ll.DoubleType(),
            "void": ll.VoidType(),
            "unsigned int": ll.IntType(32),
            "unsigned short": ll.IntType(16),
            "unsigned long": ll.IntType(64),
            "unsigned long long": ll.IntType(64),
            "unsigned char": ll.IntType(8),
        }

        # 处理指针
        if c_type.endswith("*"):
            base_type_name = c_type.rstrip("*").strip()
            base_type = self.c_to_llvm(base_type_name)
            return ll.PointerType(base_type)

        return c_type_map.get(c_type, ll.IntType(32))

    def get_type_size(self, zh_type: str) -> int:
        """
        获取类型大小（字节）

        Args:
            zh_type: ZhC 类型名

        Returns:
            大小（字节）
        """
        size_map = {
            "字符型": 1,
            "短整型": 2,
            "整数型": 4,
            "长整型": 8,  # 平台相关，这里假设 64 位
            "长长整型": 8,
            "布尔型": 1,
            "浮点型": 4,
            "双精度浮点型": 8,
            "空型": 1,
            "无符号字符型": 1,
            "无符号短整型": 2,
            "无符号整数型": 4,
            "无符号长整型": 8,
            "无符号长长整型": 8,
        }

        if zh_type.endswith("指针") or zh_type.endswith("*"):
            return 8  # 指针大小

        return size_map.get(zh_type, 8)

    def is_compatible(self, type1: str, type2: str) -> bool:
        """
        检查两个 ZhC 类型是否兼容

        Args:
            type1: 类型 1
            type2: 类型 2

        Returns:
            是否兼容
        """
        # 完全匹配
        if type1 == type2:
            return True

        # 去掉 const/volatile 等限定词进行对比
        t1 = type1.replace("常", "").replace(" volatile", "").strip()
        t2 = type2.replace("常", "").replace(" volatile", "").strip()

        if t1 == t2:
            return True

        # 整数和浮点类型之间的兼容性
        int_types = {
            "整数型",
            "短整型",
            "长整型",
            "长长整型",
            "字符型",
            "布尔型",
            "无符号整数型",
            "无符号短整型",
            "无符号长整型",
            "无符号长长整型",
            "无符号字符型",
        }
        float_types = {"浮点型", "双精度浮点型"}

        if t1 in int_types and t2 in int_types:
            return True
        if t1 in float_types and t2 in float_types:
            return True

        return False

    def create_function_type(
        self, return_type: str, param_types: List[str]
    ) -> ll.FunctionType:
        """
        创建 LLVM 函数类型

        Args:
            return_type: 返回类型
            param_types: 参数类型列表

        Returns:
            LLVM 函数类型
        """
        llvm_return = self.zhc_to_llvm(return_type)
        llvm_params = [self.zhc_to_llvm(pt) for pt in param_types]
        return ll.FunctionType(llvm_return, llvm_params)


# 全局实例
_c_type_mapper: Optional[CTypeMapper] = None


def get_c_type_mapper(target_platform: str = "linux") -> CTypeMapper:
    """
    获取全局 C 类型映射器

    Args:
        target_platform: 目标平台

    Returns:
        C 类型映射器
    """
    global _c_type_mapper
    if _c_type_mapper is None:
        _c_type_mapper = CTypeMapper(target_platform)
    return _c_type_mapper


# 导出公共 API
__all__ = [
    "CTypeInfo",
    "CTypeMapper",
    "get_c_type_mapper",
]
