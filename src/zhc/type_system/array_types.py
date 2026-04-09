"""
数组类型定义
Array Type Definitions

提供完整的数组类型信息管理，支持：
- 静态数组（固定大小）
- 动态数组（变长数组 VLA）
- 多维数组
- 不完整数组类型（函数参数）

创建日期: 2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class ArrayKind(Enum):
    """数组类型分类"""

    STATIC = "static"  # 静态数组（固定大小）
    DYNAMIC = "dynamic"  # 变长数组（VLA）
    INCOMPLETE = "incomplete"  # 不完整数组（函数参数，退化为指针）
    LITERAL = "literal"  # 数组字面量推导


@dataclass
class ArrayTypeInfo:
    """
    数组类型信息

    存储数组的完整类型信息，包括元素类型、维度、动态性等。

    Examples:
        整数型[10]       -> ArrayTypeInfo("整数型", [10], STATIC)
        整数型[3][4]     -> ArrayTypeInfo("整数型", [3, 4], STATIC)
        整数型[n]        -> ArrayTypeInfo("整数型", [None], DYNAMIC)
        整数型[]         -> ArrayTypeInfo("整数型", [None], INCOMPLETE)
    """

    element_type: str  # 元素类型（基础类型名）
    dimensions: List[Optional[int]]  # 各维度大小（None 表示未知/动态）
    kind: ArrayKind = ArrayKind.STATIC  # 数组类型分类
    is_pointer: bool = False  # 是否退化为指针（函数参数）
    source_location: Optional[Tuple[int, int]] = None  # 源码位置 (line, column)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def rank(self) -> int:
        """数组维度（秩）"""
        return len(self.dimensions)

    @property
    def is_complete(self) -> bool:
        """是否完整类型（所有维度已知）"""
        return all(d is not None for d in self.dimensions)

    @property
    def is_multidimensional(self) -> bool:
        """是否多维数组"""
        return len(self.dimensions) > 1

    @property
    def is_empty(self) -> bool:
        """是否空数组"""
        return self.dimensions and self.dimensions[0] == 0

    @property
    def total_elements(self) -> Optional[int]:
        """总元素数量"""
        if not self.is_complete:
            return None
        result = 1
        for d in self.dimensions:
            if d is not None:
                result *= d
        return result

    @property
    def first_dimension(self) -> Optional[int]:
        """第一维度大小"""
        return self.dimensions[0] if self.dimensions else None

    def get_inner_type(self) -> str:
        """
        获取内层类型（去掉第一维度）

        Examples:
            整数型[3][4] -> 整数型[4]
            整数型[10]  -> 整数型
        """
        if len(self.dimensions) <= 1:
            return self.element_type

        inner_dims = self.dimensions[1:]
        dims_str = "".join(f"[{d if d else ''}]" for d in inner_dims)
        return f"{self.element_type}{dims_str}"

    def get_element_at_depth(self, depth: int) -> str:
        """
        获取指定深度访问后的类型

        Args:
            depth: 下标访问次数

        Examples:
            整数型[3][4][5], depth=0 -> 整数型[3][4][5]
            整数型[3][4][5], depth=1 -> 整数型[4][5]
            整数型[3][4][5], depth=2 -> 整数型[5]
            整数型[3][4][5], depth=3 -> 整数型
        """
        if depth >= len(self.dimensions):
            return self.element_type

        remaining_dims = self.dimensions[depth:]
        if not remaining_dims:
            return self.element_type

        dims_str = "".join(f"[{d if d else ''}]" for d in remaining_dims)
        return f"{self.element_type}{dims_str}"

    def to_string(self) -> str:
        """转换为字符串表示"""
        dims_str = "".join(f"[{d if d else ''}]" for d in self.dimensions)
        return f"{self.element_type}{dims_str}"

    def to_c_string(self) -> str:
        """转换为 C 风格字符串（用于后端）"""
        if self.is_pointer:
            return f"{self.element_type}*"

        dims_str = "".join(f"[{d if d else ''}]" for d in self.dimensions)
        return f"{self.element_type}{dims_str}"

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        kind_str = self.kind.value
        return f"ArrayTypeInfo({self.element_type}, {self.dimensions}, {kind_str})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayTypeInfo):
            return False
        return (
            self.element_type == other.element_type
            and self.dimensions == other.dimensions
            and self.kind == other.kind
        )

    def __hash__(self) -> int:
        return hash((self.element_type, tuple(self.dimensions), self.kind))

    def is_compatible_with(self, other: "ArrayTypeInfo") -> bool:
        """
        检查类型兼容性

        规则：
        1. 元素类型必须相同
        2. 维度数量必须相同
        3. 已知维度大小必须匹配
        """
        if self.element_type != other.element_type:
            return False

        if self.rank != other.rank:
            return False

        # 检查每个维度
        for d1, d2 in zip(self.dimensions, other.dimensions):
            if d1 is not None and d2 is not None and d1 != d2:
                return False

        return True

    def can_decay_to_pointer(self) -> bool:
        """是否可以退化为指针"""
        return not self.is_pointer and self.kind != ArrayKind.INCOMPLETE

    def decay_to_pointer(self) -> "ArrayTypeInfo":
        """退化为指针类型（用于函数参数传递）"""
        return ArrayTypeInfo(
            element_type=self.element_type,
            dimensions=self.dimensions,  # 保持维度信息用于调试
            kind=ArrayKind.INCOMPLETE,
            is_pointer=True,
            metadata={"original_array": self.to_string()},
        )

    def copy(self) -> "ArrayTypeInfo":
        """创建副本"""
        return ArrayTypeInfo(
            element_type=self.element_type,
            dimensions=self.dimensions.copy(),
            kind=self.kind,
            is_pointer=self.is_pointer,
            source_location=self.source_location,
            metadata=self.metadata.copy(),
        )


class ArrayTypeFactory:
    """
    数组类型工厂

    提供便捷的数组类型创建方法。
    """

    @staticmethod
    def create_static(element_type: str, *dimensions: int) -> ArrayTypeInfo:
        """
        创建静态数组类型

        Args:
            element_type: 元素类型
            dimensions: 各维度大小

        Examples:
            create_static("整数型", 10)      -> 整数型[10]
            create_static("整数型", 3, 4)    -> 整数型[3][4]
        """
        return ArrayTypeInfo(
            element_type=element_type,
            dimensions=list(dimensions),
            kind=ArrayKind.STATIC,
        )

    @staticmethod
    def create_from_literal(element_type: str, size: int) -> ArrayTypeInfo:
        """
        从数组字面量创建类型

        Args:
            element_type: 推导出的元素类型
            size: 字面量元素数量
        """
        return ArrayTypeInfo(
            element_type=element_type, dimensions=[size], kind=ArrayKind.LITERAL
        )

    @staticmethod
    def create_dynamic(
        element_type: str, dimensions: List[Optional[int]]
    ) -> ArrayTypeInfo:
        """
        创建动态数组类型（VLA）

        Args:
            element_type: 元素类型
            dimensions: 维度列表（None 表示动态大小）
        """
        return ArrayTypeInfo(
            element_type=element_type, dimensions=dimensions, kind=ArrayKind.DYNAMIC
        )

    @staticmethod
    def create_incomplete(element_type: str) -> ArrayTypeInfo:
        """
        创建不完整数组类型（用于函数参数）

        数组作为参数时自动退化为指针。
        """
        return ArrayTypeInfo(
            element_type=element_type,
            dimensions=[None],
            kind=ArrayKind.INCOMPLETE,
            is_pointer=True,
        )

    @staticmethod
    def create_multidim(element_type: str, dimensions: List[int]) -> ArrayTypeInfo:
        """
        创建多维数组类型

        Args:
            element_type: 元素类型
            dimensions: 各维度大小列表
        """
        return ArrayTypeInfo(
            element_type=element_type, dimensions=dimensions, kind=ArrayKind.STATIC
        )

    @staticmethod
    def parse_from_string(type_str: str) -> Optional[ArrayTypeInfo]:
        """
        从字符串解析数组类型

        Args:
            type_str: 类型字符串，如 "整数型[10]" 或 "整数型[3][4]"

        Returns:
            解析成功返回 ArrayTypeInfo，否则返回 None
        """
        import re

        # 匹配类型名和维度
        pattern = r"^([^\[\]]+)((?:\[\d*\])+)$"
        match = re.match(pattern, type_str.strip())

        if not match:
            return None

        element_type = match.group(1).strip()
        dims_str = match.group(2)

        # 解析维度
        dims = []
        for dim_match in re.finditer(r"\[(\d*)\]", dims_str):
            size_str = dim_match.group(1)
            if size_str:
                dims.append(int(size_str))
            else:
                dims.append(None)  # 空维度

        if not dims:
            return None

        # 确定类型
        if all(d is not None for d in dims):
            kind = ArrayKind.STATIC
        else:
            kind = ArrayKind.INCOMPLETE

        return ArrayTypeInfo(
            element_type=element_type,
            dimensions=dims,
            kind=kind,
            is_pointer=(kind == ArrayKind.INCOMPLETE),
        )

    @staticmethod
    def merge_types(
        declared: Optional[ArrayTypeInfo], inferred: Optional[ArrayTypeInfo]
    ) -> ArrayTypeInfo:
        """
        合并声明类型和推导类型

        规则：
        1. 如果声明了大小，使用声明的大小
        2. 如果声明大小为空，使用推导的大小
        3. 元素类型必须一致

        Args:
            declared: 声明的数组类型
            inferred: 从初始化推导的类型

        Returns:
            合并后的类型

        Raises:
            ValueError: 类型不兼容时
        """
        if declared is None and inferred is None:
            raise ValueError("无法合并：两个类型都为空")

        if declared is None:
            return inferred.copy()

        if inferred is None:
            return declared.copy()

        # 检查元素类型
        if declared.element_type != inferred.element_type:
            raise ValueError(
                f"元素类型不匹配: 声明 '{declared.element_type}', "
                f"推导 '{inferred.element_type}'"
            )

        # 合并维度
        merged_dims = []
        for i, (d_decl, d_inf) in enumerate(
            zip(declared.dimensions, inferred.dimensions)
        ):
            if d_decl is not None:
                # 声明了大小，检查一致性
                if d_inf is not None and d_decl != d_inf:
                    raise ValueError(
                        f"维度 {i} 大小不匹配: 声明 {d_decl}, 推导 {d_inf}"
                    )
                merged_dims.append(d_decl)
            else:
                # 未声明大小，使用推导值
                merged_dims.append(d_inf)

        # 确定类型
        if all(d is not None for d in merged_dims):
            kind = ArrayKind.STATIC
        else:
            kind = ArrayKind.DYNAMIC

        return ArrayTypeInfo(
            element_type=declared.element_type, dimensions=merged_dims, kind=kind
        )


# 类型层次（用于类型提升）
TYPE_HIERARCHY: Dict[str, int] = {
    "布尔型": 0,
    "字符型": 1,
    "整数型": 2,
    "长整数型": 3,
    "浮点型": 4,
    "双精度浮点型": 5,
    "字符串型": 6,
}


def unify_element_types(types: List[str]) -> str:
    """
    统一元素类型（类型提升）

    选择最通用的类型作为数组元素类型。

    Args:
        types: 元素类型列表

    Returns:
        统一后的类型
    """
    if not types:
        return "整数型"  # 默认

    max_level = -1
    result_type = types[0]

    for t in types:
        level = TYPE_HIERARCHY.get(t, -1)
        if level > max_level:
            max_level = level
            result_type = t

    return result_type


def calculate_array_size(array_type: ArrayTypeInfo, element_size: int) -> Optional[int]:
    """
    计算数组总大小（字节）

    Args:
        array_type: 数组类型信息
        element_size: 单个元素大小（字节）

    Returns:
        总大小，如果维度未知则返回 None
    """
    if not array_type.is_complete:
        return None

    total = element_size
    for dim in array_type.dimensions:
        if dim is not None:
            total *= dim

    return total
