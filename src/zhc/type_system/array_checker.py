"""
数组边界检查器
Array Bounds Checker

提供编译时和运行时的数组边界检查功能：
- 静态分析：检查常量索引是否越界
- 运行时检查：生成边界检查代码
- 负数索引检查

创建日期: 2026-04-09
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum

from .array_types import ArrayTypeInfo


class Severity(Enum):
    """错误严重程度"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class BoundsError:
    """边界错误信息"""

    message: str
    severity: Severity = Severity.ERROR
    array_name: Optional[str] = None
    index_value: Optional[int] = None
    valid_range: Optional[Tuple[int, int]] = None
    source_line: Optional[int] = None
    source_column: Optional[int] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.severity.value}] {self.message}"


@dataclass
class ArrayAccessInfo:
    """数组访问信息"""

    array_name: str
    array_type: ArrayTypeInfo
    indices: List[Any]  # 索引表达式或值
    access_line: int
    access_column: int


class ArrayBoundsChecker:
    """
    数组边界检查器

    负责检查数组访问是否越界，支持：
    - 静态检查（编译时）
    - 运行时检查代码生成
    - 多维数组边界检查
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        初始化边界检查器

        Args:
            options: 配置选项
                - enable_runtime_check: 启用运行时检查
                - enable_negative_check: 启用负数索引检查
                - max_warnings: 最大警告数量
        """
        self.array_sizes: Dict[str, ArrayTypeInfo] = {}
        self.options = options or {}
        self.errors: List[BoundsError] = []
        self.warnings: List[BoundsError] = []

        # 默认配置
        self.enable_runtime_check = self.options.get("enable_runtime_check", True)
        self.enable_negative_check = self.options.get("enable_negative_check", True)
        self.max_warnings = self.options.get("max_warnings", 100)

    def register_array(self, name: str, array_type: ArrayTypeInfo) -> None:
        """
        注册数组大小信息

        Args:
            name: 数组名
            array_type: 数组类型信息
        """
        self.array_sizes[name] = array_type

    def unregister_array(self, name: str) -> None:
        """注销数组（离开作用域时）"""
        if name in self.array_sizes:
            del self.array_sizes[name]

    def get_array_info(self, name: str) -> Optional[ArrayTypeInfo]:
        """获取数组类型信息"""
        return self.array_sizes.get(name)

    def check_access(
        self,
        array_name: str,
        index_value: Any,
        dimension: int = 0,
        source_location: Optional[Tuple[int, int]] = None,
    ) -> Optional[BoundsError]:
        """
        检查数组访问是否越界

        Args:
            array_name: 数组名
            index_value: 索引值（整数或表达式）
            dimension: 维度索引（0 表示第一维）
            source_location: 源码位置 (line, column)

        Returns:
            如果越界返回 BoundsError，否则返回 None
        """
        array_info = self.array_sizes.get(array_name)
        if array_info is None:
            # 未知数组，无法检查
            return None

        # 检查维度是否有效
        if dimension >= len(array_info.dimensions):
            return BoundsError(
                message=f"数组 '{array_name}' 维度错误: 访问了第 {dimension + 1} 维，"
                f"但数组只有 {len(array_info.dimensions)} 维",
                severity=Severity.ERROR,
                array_name=array_name,
                source_line=source_location[0] if source_location else None,
                source_column=source_location[1] if source_location else None,
            )

        dim_size = array_info.dimensions[dimension]

        # 动态数组或未知大小，无法静态检查
        if dim_size is None:
            return None

        # 如果索引是常量，进行静态检查
        if isinstance(index_value, int):
            return self._check_constant_index(
                array_name, index_value, dim_size, source_location
            )

        # 非常量索引，需要运行时检查
        return None

    def _check_constant_index(
        self,
        array_name: str,
        index: int,
        dim_size: int,
        source_location: Optional[Tuple[int, int]],
    ) -> Optional[BoundsError]:
        """
        检查常量索引

        Args:
            array_name: 数组名
            index: 索引值
            dim_size: 维度大小
            source_location: 源码位置
        """
        # 检查负数索引
        if index < 0:
            error = BoundsError(
                message=f"数组 '{array_name}' 索引为负数: {index}",
                severity=Severity.ERROR,
                array_name=array_name,
                index_value=index,
                valid_range=(0, dim_size - 1),
                source_line=source_location[0] if source_location else None,
                source_column=source_location[1] if source_location else None,
                suggestion="数组索引必须是非负整数",
            )
            self.errors.append(error)
            return error

        # 检查上界
        if index >= dim_size:
            error = BoundsError(
                message=f"数组 '{array_name}' 越界: 索引 {index} 超出范围 [0, {dim_size - 1}]",
                severity=Severity.ERROR,
                array_name=array_name,
                index_value=index,
                valid_range=(0, dim_size - 1),
                source_line=source_location[0] if source_location else None,
                source_column=source_location[1] if source_location else None,
                suggestion=f"有效索引范围: 0 到 {dim_size - 1}",
            )
            self.errors.append(error)
            return error

        return None

    def check_multidim_access(
        self,
        array_name: str,
        indices: List[Any],
        source_location: Optional[Tuple[int, int]] = None,
    ) -> List[BoundsError]:
        """
        检查多维数组访问

        Args:
            array_name: 数组名
            indices: 各维度索引列表
            source_location: 源码位置

        Returns:
            错误列表
        """
        errors = []
        array_info = self.array_sizes.get(array_name)

        if array_info is None:
            return errors

        # 检查维度数量
        if len(indices) > len(array_info.dimensions):
            errors.append(
                BoundsError(
                    message=f"数组 '{array_name}' 维度过多: 访问了 {len(indices)} 维，"
                    f"但数组只有 {len(array_info.dimensions)} 维",
                    severity=Severity.ERROR,
                    array_name=array_name,
                    source_line=source_location[0] if source_location else None,
                    source_column=source_location[1] if source_location else None,
                )
            )
            return errors

        # 检查每个维度
        for dim, index in enumerate(indices):
            error = self.check_access(array_name, index, dim, source_location)
            if error:
                errors.append(error)

        return errors

    def generate_runtime_check(
        self, array_name: str, index_expr: Any, dimension: int = 0
    ) -> Optional[str]:
        """
        生成运行时边界检查代码

        Args:
            array_name: 数组名
            index_expr: 索引表达式
            dimension: 维度索引

        Returns:
            生成的检查代码字符串，如果不需要检查则返回 None
        """
        array_info = self.array_sizes.get(array_name)
        if array_info is None:
            return None

        dim_size = array_info.dimensions[dimension]
        if dim_size is None:
            # 动态大小，需要从变量获取
            return f"__zhc_bounds_check_dynamic({array_name}_size, {index_expr})"

        # 静态大小
        return f"__zhc_bounds_check({dim_size}, {index_expr})"

    def check_index_type(
        self, index_type: str, source_location: Optional[Tuple[int, int]] = None
    ) -> Optional[BoundsError]:
        """
        检查索引类型是否有效

        Args:
            index_type: 索引类型
            source_location: 源码位置
        """
        valid_types = {"整数型", "长整数型", "字符型", "短整数型"}

        if index_type not in valid_types:
            error = BoundsError(
                message=f"数组索引类型错误: '{index_type}' 不是整数类型",
                severity=Severity.WARNING,
                source_line=source_location[0] if source_location else None,
                source_column=source_location[1] if source_location else None,
                suggestion="数组索引应为整数类型",
            )
            self.warnings.append(error)
            return error

        return None

    def clear_errors(self) -> None:
        """清除所有错误和警告"""
        self.errors.clear()
        self.warnings.clear()

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_all_issues(self) -> List[BoundsError]:
        """获取所有问题（错误和警告）"""
        return self.errors + self.warnings

    def get_summary(self) -> Dict[str, int]:
        """获取检查摘要"""
        return {
            "arrays_registered": len(self.array_sizes),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }


class RuntimeBoundsCheckGenerator:
    """
    运行时边界检查代码生成器

    生成 LLVM IR 或 C 代码进行运行时边界检查。
    """

    @staticmethod
    def generate_c_check(array_size: int, index_var: str) -> str:
        """
        生成 C 语言边界检查代码

        Args:
            array_size: 数组大小
            index_var: 索引变量名
        """
        return f"""
if ({index_var} < 0 || {index_var} >= {array_size}) {{
    fprintf(stderr, "数组越界: 索引 %d 超出范围 [0, {array_size - 1}]\\n", {index_var});
    exit(1);
}}
"""

    @staticmethod
    def generate_llvm_check(
        builder: Any, array_ptr: Any, index: Any, array_size: int, array_name: str
    ) -> Any:
        """
        生成 LLVM IR 边界检查

        Args:
            builder: LLVM IR builder
            array_ptr: 数组指针
            index: 索引值
            array_size: 数组大小
            array_name: 数组名（用于错误消息）

        Returns:
            检查通过后的元素指针
        """
        # 这里是伪代码，实际实现需要 llvmlite
        # 1. 比较 index < 0
        # 2. 比较 index >= array_size
        # 3. 如果越界，调用运行时错误函数
        # 4. 否则继续访问
        pass

    @staticmethod
    def get_runtime_check_function() -> str:
        """获取运行时检查函数定义"""
        return """
// ZhC 运行时数组边界检查
#include <stdio.h>
#include <stdlib.h>

void __zhc_bounds_check(int size, int index) {
    if (index < 0 || index >= size) {
        fprintf(stderr, "运行时错误: 数组越界 (索引 %d, 大小 %d)\\n", index, size);
        exit(1);
    }
}

void __zhc_bounds_check_dynamic(int size, int index) {
    __zhc_bounds_check(size, index);
}
"""


class ArrayAccessTracker:
    """
    数组访问追踪器

    用于数据流分析，追踪数组访问模式。
    """

    def __init__(self):
        self.accesses: Dict[str, List[ArrayAccessInfo]] = {}
        self.max_accessed: Dict[
            str, Dict[int, int]
        ] = {}  # array_name -> {dim -> max_index}

    def record_access(
        self,
        array_name: str,
        array_type: ArrayTypeInfo,
        indices: List[Any],
        line: int,
        column: int,
    ) -> None:
        """记录数组访问"""
        access_info = ArrayAccessInfo(
            array_name=array_name,
            array_type=array_type,
            indices=indices,
            access_line=line,
            access_column=column,
        )

        if array_name not in self.accesses:
            self.accesses[array_name] = []
        self.accesses[array_name].append(access_info)

        # 更新最大访问索引
        if array_name not in self.max_accessed:
            self.max_accessed[array_name] = {}

        for dim, idx in enumerate(indices):
            if isinstance(idx, int):
                current_max = self.max_accessed[array_name].get(dim, -1)
                if idx > current_max:
                    self.max_accessed[array_name][dim] = idx

    def get_max_accessed_index(
        self, array_name: str, dimension: int = 0
    ) -> Optional[int]:
        """获取指定维度的最大访问索引"""
        if array_name not in self.max_accessed:
            return None
        return self.max_accessed[array_name].get(dimension)

    def get_access_count(self, array_name: str) -> int:
        """获取数组访问次数"""
        return len(self.accesses.get(array_name, []))

    def analyze_usage_pattern(self, array_name: str) -> Dict[str, Any]:
        """分析数组使用模式"""
        accesses = self.accesses.get(array_name, [])

        if not accesses:
            return {"pattern": "unused", "access_count": 0}

        # 分析访问模式
        sequential = self._is_sequential_access(accesses)
        constant_indices = self._count_constant_indices(accesses)

        return {
            "pattern": "sequential" if sequential else "random",
            "access_count": len(accesses),
            "constant_indices": constant_indices,
            "max_indices": self.max_accessed.get(array_name, {}),
        }

    def _is_sequential_access(self, accesses: List[ArrayAccessInfo]) -> bool:
        """检查是否为顺序访问"""
        if len(accesses) < 2:
            return True

        # 简单检查：连续访问的索引是否递增
        prev_index = None
        for access in accesses:
            if access.indices and isinstance(access.indices[0], int):
                if prev_index is not None:
                    if access.indices[0] != prev_index + 1:
                        return False
                prev_index = access.indices[0]

        return True

    def _count_constant_indices(self, accesses: List[ArrayAccessInfo]) -> int:
        """统计常量索引访问次数"""
        count = 0
        for access in accesses:
            if all(isinstance(idx, int) for idx in access.indices):
                count += 1
        return count
