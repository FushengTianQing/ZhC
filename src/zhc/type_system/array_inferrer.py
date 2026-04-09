"""
数组类型推导器
Array Type Inferrer

从数组字面量和数组访问表达式推导数组类型：
- 数组字面量类型推导
- 多维数组类型推导
- 下标访问类型推导
- 类型统一和提升

创建日期: 2026-04-09
"""

from typing import Optional, List, Any, Dict, Tuple
from dataclasses import dataclass

from .array_types import (
    ArrayTypeInfo,
    ArrayTypeFactory,
    TYPE_HIERARCHY,
    unify_element_types,
)
from .array_checker import ArrayBoundsChecker, BoundsError, Severity


@dataclass
class InferenceResult:
    """类型推导结果"""

    inferred_type: ArrayTypeInfo
    confidence: float = 1.0  # 0.0 ~ 1.0
    explanation: str = ""
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class InferenceContext:
    """
    推导上下文

    保存推导过程中需要的环境信息。
    """

    def __init__(
        self,
        type_env: Optional[Dict[str, str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        self.type_env = type_env or {}  # 变量名 -> 类型
        self.options = options or {}
        self.current_function: Optional[str] = None
        self.in_loop: bool = False

    def get_variable_type(self, name: str) -> Optional[str]:
        """获取变量类型"""
        return self.type_env.get(name)

    def set_variable_type(self, name: str, type_: str) -> None:
        """设置变量类型"""
        self.type_env[name] = type_


class ArrayTypeInferrer:
    """
    数组类型推导器

    负责从数组表达式和字面量推导数组类型。
    """

    def __init__(self, bounds_checker: Optional[ArrayBoundsChecker] = None):
        self.bounds_checker = bounds_checker
        self.unified_types_cache: Dict[str, str] = {}

    def infer_from_literal(
        self, elements: List[Any], context: Optional[InferenceContext] = None
    ) -> InferenceResult:
        """
        从数组字面量推导类型

        Examples:
            [1, 2, 3]      -> 整数型[3]
            [1.0, 2.0]     -> 浮点型[2]
            ["a", "b"]     -> 字符串型[2]
            []             -> 整数型[0]

        Args:
            elements: 数组元素列表
            context: 推导上下文

        Returns:
            推导结果
        """
        context = context or InferenceContext()

        if not elements:
            # 空数组默认为整数型
            return InferenceResult(
                inferred_type=ArrayTypeFactory.create_from_literal("整数型", 0),
                confidence=0.5,
                explanation="空数组默认为整数型数组",
                warnings=["空数组类型可能不符合预期"],
            )

        # 推导元素类型
        element_types: List[str] = []
        all_constant = True

        for elem in elements:
            # 这里处理 AST 节点类型
            elem_type = self._infer_element_type(elem, context)
            element_types.append(elem_type)

            # 检查是否为常量
            if all_constant and not self._is_constant(elem):
                all_constant = False

        # 统一元素类型（类型提升）
        unified_type = unify_element_types(element_types)

        # 检查类型一致性
        type_set = set(element_types)
        warnings = []
        if len(type_set) > 1:
            warnings.append(f"数组元素类型不一致: {type_set}，提升为 {unified_type}")

        # 创建数组类型
        array_type = ArrayTypeFactory.create_from_literal(unified_type, len(elements))

        return InferenceResult(
            inferred_type=array_type,
            confidence=1.0 if all_constant else 0.8,
            explanation=f"数组字面量，元素类型: {unified_type}，长度: {len(elements)}",
            warnings=warnings,
        )

    def infer_from_multidim_literal(
        self, rows: List[List[Any]], context: Optional[InferenceContext] = None
    ) -> InferenceResult:
        """
        从多维数组字面量推导类型

        Examples:
            [[1, 2], [3, 4]]     -> 整数型[2][2]
            [[1.0, 2.0]]         -> 浮点型[1][2]

        Args:
            rows: 二维数组元素列表
            context: 推导上下文

        Returns:
            推导结果
        """
        context = context or InferenceContext()

        if not rows:
            return InferenceResult(
                inferred_type=ArrayTypeFactory.create_static("整数型", 0, 0),
                confidence=0.5,
                explanation="空多维数组",
            )

        if not rows[0]:
            return InferenceResult(
                inferred_type=ArrayTypeFactory.create_static("整数型", len(rows), 0),
                confidence=0.5,
                explanation="空行多维数组",
            )

        # 递归推导第一个子数组的类型作为参考
        first_row_type = self.infer_from_literal(rows[0], context)

        # 检查所有行是否类型一致
        row_length = len(rows[0])
        element_type = first_row_type.inferred_type.element_type

        for i, row in enumerate(rows[1:], 1):
            if len(row) != row_length:
                return InferenceResult(
                    inferred_type=ArrayTypeFactory.create_static(
                        element_type, len(rows), len(row)
                    ),
                    confidence=0.3,
                    explanation=f"多维数组行长度不一致: 第0行{row_length}，第{i}行{len(row)}",
                    warnings=[f"第{i}行长度与其他行不一致"],
                )

        # 创建多维数组类型
        if first_row_type.inferred_type.rank == 1:
            # 第一行是普通元素，rows 是 2D
            array_type = ArrayTypeFactory.create_multidim(
                element_type, [len(rows), row_length]
            )
        else:
            # 第一行是子数组，递归处理
            inner_dims = first_row_type.inferred_type.dimensions
            array_type = ArrayTypeFactory.create_multidim(
                element_type, [len(rows)] + inner_dims
            )

        return InferenceResult(
            inferred_type=array_type,
            confidence=1.0,
            explanation=f"多维数组 {element_type}[{len(rows)}][{row_length}]",
        )

    def infer_subscript_type(
        self, array_type: ArrayTypeInfo, num_indices: int = 1
    ) -> str:
        """
        推导下标访问后的类型

        Examples:
            整数型[3][4] 下标访问一次 -> 整数型[4]
            整数型[3][4] 下标访问两次 -> 整数型
            整数型[10] 下标访问一次  -> 整数型

        Args:
            array_type: 数组类型
            num_indices: 下标访问次数

        Returns:
            访问后的类型字符串
        """
        if num_indices > len(array_type.dimensions):
            return "错误"  # 维度错误

        remaining_dims = array_type.dimensions[num_indices:]

        if not remaining_dims:
            return array_type.element_type

        dims_str = "".join(f"[{d if d else ''}]" for d in remaining_dims)
        return f"{array_type.element_type}{dims_str}"

    def infer_subscript_type_ex(
        self,
        array_type: ArrayTypeInfo,
        indices: List[Any],
        context: Optional[InferenceContext] = None,
    ) -> Tuple[str, List[BoundsError]]:
        """
        推导下标访问类型（带边界检查）

        Args:
            array_type: 数组类型
            indices: 索引表达式列表
            context: 推导上下文

        Returns:
            (结果类型, 错误列表)
        """
        errors = []
        context = context or InferenceContext()

        # 检查维度数量
        if len(indices) > len(array_type.dimensions):
            errors.append(
                BoundsError(
                    message=f"数组维度过多: 访问了 {len(indices)} 维，"
                    f"但数组只有 {len(array_type.dimensions)} 维",
                    severity=Severity.ERROR,
                )
            )
            return "错误", errors

        # 检查每个索引
        for dim, idx in enumerate(indices):
            if isinstance(idx, int):
                dim_size = array_type.dimensions[dim]
                if dim_size is not None:
                    if idx < 0:
                        errors.append(
                            BoundsError(
                                message=f"索引为负数: {idx}",
                                severity=Severity.ERROR,
                                index_value=idx,
                                valid_range=(0, dim_size - 1),
                            )
                        )
                    elif idx >= dim_size:
                        errors.append(
                            BoundsError(
                                message=f"索引 {idx} 超出范围 [0, {dim_size - 1}]",
                                severity=Severity.ERROR,
                                index_value=idx,
                                valid_range=(0, dim_size - 1),
                            )
                        )

        result_type = self.infer_subscript_type(array_type, len(indices))
        return result_type, errors

    def infer_function_param_type(self, declared_type: ArrayTypeInfo) -> ArrayTypeInfo:
        """
        推导函数参数类型

        规则：数组作为参数时自动退化为指针
        """
        if declared_type.can_decay_to_pointer():
            return declared_type.decay_to_pointer()
        return declared_type.copy()

    def infer_from_initialization(
        self,
        declared_type: Optional[ArrayTypeInfo],
        initializer: Any,
        context: Optional[InferenceContext] = None,
    ) -> InferenceResult:
        """
        从初始化表达式推导数组类型

        Args:
            declared_type: 声明的类型（可能不完整）
            initializer: 初始化表达式
            context: 推导上下文

        Returns:
            推导结果
        """
        context = context or InferenceContext()

        # 推导初始化值的类型
        if isinstance(initializer, list):
            # 数组字面量
            inferred = self.infer_from_literal(initializer, context)
        else:
            # 单个值（标量初始化）
            inferred = self._infer_from_scalar(initializer, context)

        if declared_type is None:
            return inferred

        # 合并声明类型和推导类型
        try:
            merged = ArrayTypeFactory.merge_types(declared_type, inferred.inferred_type)
            return InferenceResult(
                inferred_type=merged,
                confidence=inferred.confidence,
                explanation=f"合并类型: {merged.to_string()}",
                warnings=inferred.warnings,
            )
        except ValueError as e:
            return InferenceResult(
                inferred_type=declared_type.copy(),
                confidence=0.5,
                explanation=f"类型冲突: {str(e)}",
                warnings=[str(e)] + inferred.warnings,
            )

    def _infer_element_type(self, elem: Any, context: InferenceContext) -> str:
        """推导单个元素类型"""
        # 这里需要根据 AST 节点类型进行推导
        # 简化处理
        elem_type = getattr(elem, "inferred_type", None)
        if elem_type:
            return elem_type

        # 处理字面量
        if isinstance(elem, int):
            return "整数型"
        if isinstance(elem, float):
            return "浮点型"
        if isinstance(elem, str):
            if len(elem) == 1:
                return "字符型"
            return "字符串型"
        if isinstance(elem, bool):
            return "布尔型"

        # 递归处理数组
        if isinstance(elem, (list, tuple)):
            if elem:
                return self._infer_element_type(elem[0], context)
            return "整数型"  # 空数组默认

        return "未知"

    def _is_constant(self, elem: Any) -> bool:
        """检查表达式是否为常量"""
        if isinstance(elem, (int, float, str, bool)):
            return True
        if isinstance(elem, (list, tuple)):
            return all(self._is_constant(e) for e in elem)
        return False

    def _infer_from_scalar(
        self, value: Any, context: InferenceContext
    ) -> InferenceResult:
        """从标量值推导数组类型"""
        if isinstance(value, int):
            element_type = "整数型"
        elif isinstance(value, float):
            element_type = "浮点型"
        elif isinstance(value, str):
            if len(value) == 1:
                element_type = "字符型"
            else:
                element_type = "字符串型"
        else:
            element_type = "未知"

        return InferenceResult(
            inferred_type=ArrayTypeFactory.create_from_literal(element_type, 1),
            confidence=1.0,
            explanation=f"标量初始化: {element_type}",
        )

    def suggest_type_adjustment(
        self, target_type: str, actual_type: ArrayTypeInfo
    ) -> Optional[str]:
        """
        建议类型调整

        当实际类型与目标类型不匹配时，提供调整建议。

        Args:
            target_type: 目标类型（如函数参数）
            actual_type: 实际数组类型

        Returns:
            调整建议，如果不需要调整则返回 None
        """
        if target_type == actual_type.element_type:
            return None

        # 检查是否可以通过类型转换兼容
        target_hierarchy = TYPE_HIERARCHY.get(target_type, -1)
        actual_hierarchy = TYPE_HIERARCHY.get(actual_type.element_type, -1)

        if target_hierarchy > actual_hierarchy:
            return f"考虑将数组元素类型从 '{actual_type.element_type}' 转换为 '{target_type}'"
        elif target_hierarchy < actual_hierarchy:
            return f"可能存在数据精度损失：'{actual_type.element_type}' 转换为 '{target_type}'"

        return None


def infer_array_type_from_string(type_str: str) -> Optional[ArrayTypeInfo]:
    """
    从类型字符串推断数组类型

    Helper 函数，用于快速创建数组类型。

    Args:
        type_str: 类型字符串，如 "整数型[10]" 或 "整数型[]"

    Returns:
        ArrayTypeInfo 或 None
    """
    return ArrayTypeFactory.parse_from_string(type_str)
