# -*- coding: utf-8 -*-
"""ZhC LLVM 类型映射器

将 ZhC 类型系统映射到 LLVM 类型。

作者：远
日期：2026-04-08
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

try:
    import llvmlite.ir as ll

    LLVM_AVAILABLE = True
except ImportError:
    LLVM_AVAILABLE = False
    ll = None


@dataclass
class TypeInfo:
    """类型信息"""

    zhc_type: str  # ZhC 类型名
    llvm_type: str  # LLVM 类型名
    size_bits: int  # 位宽
    is_signed: bool  # 是否有符号
    is_float: bool  # 是否浮点
    is_pointer: bool  # 是否指针
    description: str  # 描述


class LLVMTypeMapper:
    """ZhC → LLVM 类型映射器

    支持的类型：
    - 基本类型：整数、浮点、布尔、字符
    - 指针类型：指针、数组指针
    - 复合类型：结构体、数组
    - 函数类型：函数签名
    """

    # 基本类型映射表
    BASIC_TYPES: Dict[str, TypeInfo] = {
        # 整数类型
        "整数型": TypeInfo("整数型", "i32", 32, True, False, False, "32位有符号整数"),
        "长整数型": TypeInfo(
            "长整数型", "i64", 64, True, False, False, "64位有符号整数"
        ),
        "短整数型": TypeInfo(
            "短整数型", "i16", 16, True, False, False, "16位有符号整数"
        ),
        "字节型": TypeInfo("字节型", "i8", 8, True, False, False, "8位有符号整数"),
        "无符号整数型": TypeInfo(
            "无符号整数型", "i32", 32, False, False, False, "32位无符号整数"
        ),
        "无符号长整数型": TypeInfo(
            "无符号长整数型", "i64", 64, False, False, False, "64位无符号整数"
        ),
        # 浮点类型
        "浮点型": TypeInfo("浮点型", "float", 32, False, True, False, "32位单精度浮点"),
        "双精度浮点型": TypeInfo(
            "双精度浮点型", "double", 64, False, True, False, "64位双精度浮点"
        ),
        # 字符类型
        "字符型": TypeInfo("字符型", "i8", 8, False, False, False, "8位字符"),
        "宽字符型": TypeInfo("宽字符型", "i32", 32, False, False, False, "32位宽字符"),
        # 布尔类型
        "布尔型": TypeInfo("布尔型", "i1", 1, False, False, False, "布尔值"),
        # 空类型
        "空型": TypeInfo("空型", "void", 0, False, False, False, "空类型"),
        # LLVM 原始类型透传
        "i1": TypeInfo("i1", "i1", 1, False, False, False, "1位整数"),
        "i8": TypeInfo("i8", "i8", 8, False, False, False, "8位整数"),
        "i16": TypeInfo("i16", "i16", 16, False, False, False, "16位整数"),
        "i32": TypeInfo("i32", "i32", 32, False, False, False, "32位整数"),
        "i64": TypeInfo("i64", "i64", 64, False, False, False, "64位整数"),
        "float": TypeInfo("float", "float", 32, False, True, False, "单精度浮点"),
        "double": TypeInfo("double", "double", 64, False, True, False, "双精度浮点"),
        "void": TypeInfo("void", "void", 0, False, False, False, "空类型"),
    }

    def __init__(self):
        """初始化类型映射器"""
        if not LLVM_AVAILABLE:
            raise ImportError("llvmlite 未安装")

        self._llvm_types: Dict[str, ll.Type] = {}
        self._build_llvm_types()

    def _build_llvm_types(self):
        """构建 LLVM 类型对象"""
        # 基本类型
        self._llvm_types["i1"] = ll.IntType(1)
        self._llvm_types["i8"] = ll.IntType(8)
        self._llvm_types["i16"] = ll.IntType(16)
        self._llvm_types["i32"] = ll.IntType(32)
        self._llvm_types["i64"] = ll.IntType(64)
        self._llvm_types["float"] = ll.FloatType()
        self._llvm_types["double"] = ll.DoubleType()
        self._llvm_types["void"] = ll.VoidType()

        # ZhC 类型别名
        self._llvm_types["整数型"] = self._llvm_types["i32"]
        self._llvm_types["长整数型"] = self._llvm_types["i64"]
        self._llvm_types["短整数型"] = self._llvm_types["i16"]
        self._llvm_types["字节型"] = self._llvm_types["i8"]
        self._llvm_types["无符号整数型"] = self._llvm_types["i32"]
        self._llvm_types["无符号长整数型"] = self._llvm_types["i64"]
        self._llvm_types["浮点型"] = self._llvm_types["float"]
        self._llvm_types["双精度浮点型"] = self._llvm_types["double"]
        self._llvm_types["字符型"] = self._llvm_types["i8"]
        self._llvm_types["宽字符型"] = self._llvm_types["i32"]
        self._llvm_types["布尔型"] = self._llvm_types["i1"]
        self._llvm_types["空型"] = self._llvm_types["void"]

    def map_type(self, zhc_type: str) -> ll.Type:
        """映射 ZhC 类型到 LLVM 类型

        Args:
            zhc_type: ZhC 类型名

        Returns:
            LLVM 类型对象
        """
        # 检查基本类型
        if zhc_type in self._llvm_types:
            return self._llvm_types[zhc_type]

        # 检查指针类型（以"*"结尾）
        if zhc_type.endswith("*"):
            base_type = zhc_type[:-1]
            base_llvm = self.map_type(base_type)
            return ll.PointerType(base_llvm)

        # 检查数组类型（如"整数型[10]"）
        if "[" in zhc_type and zhc_type.endswith("]"):
            base_type = zhc_type.split("[")[0]
            size = int(zhc_type.split("[")[1].rstrip("]"))
            base_llvm = self.map_type(base_type)
            return ll.ArrayType(base_llvm, size)

        # 默认返回 i32
        return self._llvm_types["i32"]

    def map_function_type(
        self, return_type: str, param_types: List[str]
    ) -> ll.FunctionType:
        """映射函数类型

        Args:
            return_type: 返回类型
            param_types: 参数类型列表

        Returns:
            LLVM 函数类型
        """
        ret_ty = self.map_type(return_type)
        param_tys = [self.map_type(pt) for pt in param_types]
        return ll.FunctionType(ret_ty, param_tys)

    def get_type_info(self, zhc_type: str) -> Optional[TypeInfo]:
        """获取类型信息

        Args:
            zhc_type: ZhC 类型名

        Returns:
            类型信息（如果存在）
        """
        return self.BASIC_TYPES.get(zhc_type)

    def get_size_bits(self, zhc_type: str) -> int:
        """获取类型位宽

        Args:
            zhc_type: ZhC 类型名

        Returns:
            位宽
        """
        info = self.get_type_info(zhc_type)
        if info:
            return info.size_bits

        # 指针类型
        if zhc_type.endswith("*"):
            return 64  # 64位指针

        # 数组类型
        if "[" in zhc_type and zhc_type.endswith("]"):
            base_type = zhc_type.split("[")[0]
            size = int(zhc_type.split("[")[1].rstrip("]"))
            base_size = self.get_size_bits(base_type)
            return base_size * size

        return 32  # 默认

    def is_signed(self, zhc_type: str) -> bool:
        """判断是否是有符号类型"""
        info = self.get_type_info(zhc_type)
        return info.is_signed if info else False

    def is_float(self, zhc_type: str) -> bool:
        """判断是否是浮点类型"""
        info = self.get_type_info(zhc_type)
        return info.is_float if info else False

    def is_pointer(self, zhc_type: str) -> bool:
        """判断是否是指针类型"""
        info = self.get_type_info(zhc_type)
        if info and info.is_pointer:
            return True
        return zhc_type.endswith("*")

    def create_pointer_type(self, base_type: str) -> ll.PointerType:
        """创建指针类型

        Args:
            base_type: 基础类型

        Returns:
            LLVM 指针类型
        """
        base_llvm = self.map_type(base_type)
        return ll.PointerType(base_llvm)

    def create_array_type(self, base_type: str, size: int) -> ll.ArrayType:
        """创建数组类型

        Args:
            base_type: 元素类型
            size: 数组大小

        Returns:
            LLVM 数组类型
        """
        base_llvm = self.map_type(base_type)
        return ll.ArrayType(base_llvm, size)

    def create_struct_type(
        self, name: str, fields: List[Tuple[str, str]]
    ) -> ll.LiteralStructType:
        """创建结构体类型

        Args:
            name: 结构体名称
            fields: 字段列表 [(字段名, 类型名), ...]

        Returns:
            LLVM 结构体类型
        """
        field_types = [self.map_type(ft[1]) for ft in fields]
        return ll.LiteralStructType(field_types)

    def type_to_string(self, llvm_type: ll.Type) -> str:
        """将 LLVM 类型转换为字符串

        Args:
            llvm_type: LLVM 类型

        Returns:
            类型字符串
        """
        return str(llvm_type)


def map_zhc_type_to_llvm(zhc_type: str) -> ll.Type:
    """便捷函数：映射 ZhC 类型到 LLVM 类型

    Args:
        zhc_type: ZhC 类型名

    Returns:
        LLVM 类型对象
    """
    mapper = LLVMTypeMapper()
    return mapper.map_type(zhc_type)


def get_type_size_bits(zhc_type: str) -> int:
    """便捷函数：获取类型位宽

    Args:
        zhc_type: ZhC 类型名

    Returns:
        位宽
    """
    mapper = LLVMTypeMapper()
    return mapper.get_size_bits(zhc_type)
