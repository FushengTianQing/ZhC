# -*- coding: utf-8 -*-
"""
ZhC 后端类型系统 - 统一类型映射

提供统一的类型映射接口，支持多种后端。

作者：远
日期：2026-04-09
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TargetBackend(Enum):
    """目标后端类型"""

    C = "c"
    LLVM = "llvm"
    WASM = "wasm"


@dataclass
class TypeInfo:
    """类型信息"""

    zhc_type: str  # ZhC 类型名（如 "整数型"）
    c_type: str  # C 类型名（如 "int"）
    llvm_type: Any  # LLVM 类型对象
    wasm_type: str  # WASM 类型名
    size_bits: int  # 位宽
    is_signed: bool  # 是否有符号
    is_float: bool  # 是否浮点数
    is_pointer: bool  # 是否指针


class TypeMapper:
    """
    统一类型映射器

    提供从 ZhC 类型到各后端类型的映射。

    使用方式：
        mapper = TypeMapper()

        # 获取 C 类型
        c_type = mapper.to_c("整数型")  # "int"

        # 获取 LLVM 类型
        llvm_type = mapper.to_llvm("浮点型")  # ll.FloatType()

        # 获取类型信息
        info = mapper.get_type_info("整数型")
    """

    # ZhC 类型到 C 类型的映射
    ZHC_TO_C: Dict[str, str] = {
        # 整数类型
        "整数型": "int",
        "短整型": "short",
        "长整型": "long",
        "长长整型": "long long",
        "无符号整数型": "unsigned int",
        "无符号短整型": "unsigned short",
        "无符号长整型": "unsigned long",
        # 字符类型
        "字符型": "char",
        "无符号字符型": "unsigned char",
        # 浮点类型
        "浮点型": "float",
        "双精度浮点型": "double",
        # 其他类型
        "布尔型": "int",  # C 没有 bool，用 int
        "空类型": "void",
        "字符串型": "char*",
        # 别名
        "i8": "int8_t",
        "i16": "int16_t",
        "i32": "int32_t",
        "i64": "int64_t",
        "u8": "uint8_t",
        "u16": "uint16_t",
        "u32": "uint32_t",
        "u64": "uint64_t",
        "f32": "float",
        "f64": "double",
    }

    # ZhC 类型到位宽的映射
    TYPE_SIZES: Dict[str, int] = {
        "整数型": 32,
        "短整型": 16,
        "长整型": 64,
        "字符型": 8,
        "浮点型": 32,
        "双精度浮点型": 64,
        "布尔型": 1,
        "i8": 8,
        "i16": 16,
        "i32": 32,
        "i64": 64,
        "f32": 32,
        "f64": 64,
    }

    # 有符号类型集合
    SIGNED_TYPES: set = {
        "整数型",
        "短整型",
        "长整型",
        "字符型",
        "i8",
        "i16",
        "i32",
        "i64",
    }

    # 浮点类型集合
    FLOAT_TYPES: set = {
        "浮点型",
        "双精度浮点型",
        "f32",
        "f64",
    }

    def __init__(self):
        """初始化类型映射器"""
        self._llvm_types: Dict[str, Any] = {}
        self._init_llvm_types()

    def _init_llvm_types(self) -> None:
        """初始化 LLVM 类型映射（延迟加载）"""
        try:
            import llvmlite.ir as ll

            self._llvm_types = {
                "整数型": ll.IntType(32),
                "短整型": ll.IntType(16),
                "长整型": ll.IntType(64),
                "字符型": ll.IntType(8),
                "浮点型": ll.FloatType(),
                "双精度浮点型": ll.DoubleType(),
                "布尔型": ll.IntType(1),
                "空类型": ll.VoidType(),
                "i8": ll.IntType(8),
                "i16": ll.IntType(16),
                "i32": ll.IntType(32),
                "i64": ll.IntType(64),
                "f32": ll.FloatType(),
                "f64": ll.DoubleType(),
            }
            self._llvm_available = True
        except ImportError:
            self._llvm_available = False

    def to_c(self, zhc_type: str) -> str:
        """
        转换 ZhC 类型到 C 类型

        Args:
            zhc_type: ZhC 类型名

        Returns:
            str: C 类型名
        """
        # 处理 ARRAY_TYPE 占位符（数组参数）
        if zhc_type.startswith("ARRAY_TYPE"):
            # 数组参数在 C 中作为指针传递
            return "int*"  # 默认为 int*

        # 处理指针类型（如 "整数型*"）
        if zhc_type.endswith("*"):
            base_type = zhc_type[:-1].strip()
            return self.to_c(base_type) + "*"

        # 处理数组类型
        if zhc_type.endswith("]"):
            # 例如: "整数型[10]" -> "int[10]"
            import re

            match = re.match(r"(.+)\[(\d+)\]$", zhc_type)
            if match:
                base_type = match.group(1)
                size = match.group(2)
                return f"{self.to_c(base_type)}[{size}]"

        return self.ZHC_TO_C.get(zhc_type, zhc_type)

    def to_llvm(self, zhc_type: str) -> Optional[Any]:
        """
        转换 ZhC 类型到 LLVM 类型

        Args:
            zhc_type: ZhC 类型名

        Returns:
            LLVM 类型对象，如果 llvmlite 不可用则返回 None
        """
        if not self._llvm_available:
            return None

        # 处理指针类型
        if zhc_type.endswith("*"):
            if not self._llvm_available:
                return None
            import llvmlite.ir as ll

            base_type = zhc_type[:-1].strip()
            return ll.PointerType(self.to_llvm(base_type))

        return self._llvm_types.get(zhc_type)

    def to_wasm(self, zhc_type: str) -> str:
        """
        转换 ZhC 类型到 WASM 类型

        Args:
            zhc_type: ZhC 类型名

        Returns:
            str: WASM 类型名
        """
        # WASM 类型系统较简单
        WASM_TYPES = {
            "整数型": "i32",
            "长整型": "i64",
            "浮点型": "f32",
            "双精度浮点型": "f64",
            "i32": "i32",
            "i64": "i64",
            "f32": "f32",
            "f64": "f64",
        }
        return WASM_TYPES.get(zhc_type, "i32")

    def get_type_info(self, zhc_type: str) -> TypeInfo:
        """
        获取类型详细信息

        Args:
            zhc_type: ZhC 类型名

        Returns:
            TypeInfo: 类型信息对象
        """
        return TypeInfo(
            zhc_type=zhc_type,
            c_type=self.to_c(zhc_type),
            llvm_type=self.to_llvm(zhc_type),
            wasm_type=self.to_wasm(zhc_type),
            size_bits=self.TYPE_SIZES.get(zhc_type, 32),
            is_signed=zhc_type in self.SIGNED_TYPES,
            is_float=zhc_type in self.FLOAT_TYPES,
            is_pointer=zhc_type.endswith("*"),
        )

    def is_llvm_available(self) -> bool:
        """检查 LLVM 是否可用"""
        return self._llvm_available

    def register_type(
        self, zhc_type: str, c_type: str, llvm_type: Any = None, wasm_type: str = "i32"
    ) -> None:
        """
        注册自定义类型映射

        Args:
            zhc_type: ZhC 类型名
            c_type: C 类型名
            llvm_type: LLVM 类型对象
            wasm_type: WASM 类型名
        """
        self.ZHC_TO_C[zhc_type] = c_type
        if llvm_type:
            self._llvm_types[zhc_type] = llvm_type


# 全局类型映射器实例
_type_mapper: Optional[TypeMapper] = None


def get_type_mapper() -> TypeMapper:
    """获取全局类型映射器实例"""
    global _type_mapper
    if _type_mapper is None:
        _type_mapper = TypeMapper()
    return _type_mapper
