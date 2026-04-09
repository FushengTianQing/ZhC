"""
数组语义分析器
Array Semantic Analyzer

提供数组相关的语义分析功能：
- 数组声明分析
- 数组访问分析
- 数组参数分析
- 边界检查集成

创建日期: 2026-04-09
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from ..type_system.array_types import ArrayTypeInfo, ArrayKind, ArrayTypeFactory
from ..type_system.array_checker import ArrayBoundsChecker, BoundsError, Severity
from ..type_system.array_inferrer import ArrayTypeInferrer, InferenceContext


@dataclass
class ArrayAnalysisResult:
    """数组分析结果"""

    success: bool
    array_type: Optional[ArrayTypeInfo] = None
    errors: List[BoundsError] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ArraySemanticAnalyzer:
    """
    数组语义分析器

    负责数组相关的语义检查和分析。
    """

    def __init__(
        self,
        bounds_checker: Optional[ArrayBoundsChecker] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数组语义分析器

        Args:
            bounds_checker: 边界检查器
            options: 配置选项
                - enable_vla: 启用变长数组支持
                - enable_bounds_check: 启用边界检查
                - max_array_size: 最大数组大小
        """
        self.bounds_checker = bounds_checker or ArrayBoundsChecker()
        self.inferrer = ArrayTypeInferrer(self.bounds_checker)
        self.options = options or {}

        # 默认配置
        self.enable_vla = self.options.get("enable_vla", True)
        self.enable_bounds_check = self.options.get("enable_bounds_check", True)
        self.max_array_size = self.options.get("max_array_size", 10_000_000)

        # 分析状态
        self.current_scope_arrays: Dict[str, ArrayTypeInfo] = {}
        self.array_init_stack: List[str] = []  # 正在初始化的数组名栈

    def analyze_array_declaration(
        self,
        name: str,
        declared_type_str: str,
        initializer: Optional[Any] = None,
        source_location: Optional[Tuple[int, int]] = None,
    ) -> ArrayAnalysisResult:
        """
        分析数组声明

        Args:
            name: 数组名
            declared_type_str: 声明的类型字符串
            initializer: 初始化表达式
            source_location: 源码位置

        Returns:
            分析结果
        """
        errors: List[BoundsError] = []
        warnings: List[str] = []

        # 解析声明的数组类型
        declared_type = ArrayTypeFactory.parse_from_string(declared_type_str)

        if declared_type is None:
            # 不是数组类型，可能是普通变量
            return ArrayAnalysisResult(success=True, warnings=["非数组类型声明"])

        # 检查 VLA 支持
        if declared_type.kind == ArrayKind.DYNAMIC and not self.enable_vla:
            errors.append(
                BoundsError(
                    message="变长数组(VLA)需要启用 VLA 支持",
                    severity=Severity.ERROR,
                    source_line=source_location[0] if source_location else None,
                    source_column=source_location[1] if source_location else None,
                    suggestion="使用 --enable-vla 启用",
                )
            )
            return ArrayAnalysisResult(
                success=False, array_type=declared_type, errors=errors
            )

        # 检查数组大小
        if declared_type.is_complete:
            total = declared_type.total_elements
            if total and total > self.max_array_size:
                warnings.append(
                    f"数组大小 {total} 超过建议最大值 {self.max_array_size}"
                )

        # 如果有初始化，推导类型并合并
        final_type = declared_type
        if initializer is not None:
            context = InferenceContext()
            inference_result = self.inferrer.infer_from_initialization(
                declared_type, initializer, context
            )

            if inference_result.warnings:
                warnings.extend(inference_result.warnings)

            final_type = inference_result.inferred_type

            # 检查初始化元素数量
            if isinstance(initializer, list):
                init_size = len(initializer)
                if declared_type.first_dimension is not None:
                    if init_size > declared_type.first_dimension:
                        errors.append(
                            BoundsError(
                                message=f"初始化元素过多: {init_size} > {declared_type.first_dimension}",
                                severity=Severity.ERROR,
                                source_line=source_location[0]
                                if source_location
                                else None,
                                source_column=source_location[1]
                                if source_location
                                else None,
                            )
                        )

        # 注册到边界检查器
        self.bounds_checker.register_array(name, final_type)
        self.current_scope_arrays[name] = final_type

        return ArrayAnalysisResult(
            success=len(errors) == 0,
            array_type=final_type,
            errors=errors,
            warnings=warnings,
        )

    def analyze_subscript_access(
        self,
        array_name: str,
        indices: List[Any],
        source_location: Optional[Tuple[int, int]] = None,
    ) -> ArrayAnalysisResult:
        """
        分析数组下标访问

        Args:
            array_name: 数组名
            indices: 索引表达式列表
            source_location: 源码位置

        Returns:
            分析结果
        """
        errors: List[BoundsError] = []
        warnings: List[str] = []

        # 获取数组类型
        array_type = self.current_scope_arrays.get(array_name)
        if array_type is None:
            array_type = self.bounds_checker.get_array_info(array_name)

        if array_type is None:
            warnings.append(f"未知数组 '{array_name}'，无法进行边界检查")
            return ArrayAnalysisResult(success=True, warnings=warnings)

        # 检查维度数量
        if len(indices) > len(array_type.dimensions):
            errors.append(
                BoundsError(
                    message=f"数组 '{array_name}' 维度过多: 访问了 {len(indices)} 维，"
                    f"但数组只有 {len(array_type.dimensions)} 维",
                    severity=Severity.ERROR,
                    array_name=array_name,
                    source_line=source_location[0] if source_location else None,
                    source_column=source_location[1] if source_location else None,
                )
            )
            return ArrayAnalysisResult(
                success=False, array_type=array_type, errors=errors
            )

        # 检查每个索引
        for dim, idx in enumerate(indices):
            # 检查索引类型
            idx_type = self._get_expression_type(idx)
            if idx_type and idx_type not in (
                "整数型",
                "长整数型",
                "字符型",
                "短整数型",
            ):
                errors.append(
                    BoundsError(
                        message=f"数组索引类型错误: '{idx_type}' 不是整数类型",
                        severity=Severity.WARNING,
                        source_line=source_location[0] if source_location else None,
                        source_column=source_location[1] if source_location else None,
                        suggestion="数组索引应为整数类型",
                    )
                )

            # 静态边界检查
            if isinstance(idx, int):
                error = self.bounds_checker.check_access(
                    array_name, idx, dim, source_location
                )
                if error:
                    errors.append(error)

        return ArrayAnalysisResult(
            success=len([e for e in errors if e.severity == Severity.ERROR]) == 0,
            array_type=array_type,
            errors=errors,
            warnings=warnings,
        )

    def analyze_array_parameter(
        self,
        param_name: str,
        param_type_str: str,
        source_location: Optional[Tuple[int, int]] = None,
    ) -> ArrayAnalysisResult:
        """
        分析数组参数

        数组参数自动退化为指针。

        Args:
            param_name: 参数名
            param_type_str: 参数类型字符串
            source_location: 源码位置

        Returns:
            分析结果
        """
        param_type = ArrayTypeFactory.parse_from_string(param_type_str)

        if param_type is None:
            return ArrayAnalysisResult(success=True, warnings=["非数组参数"])

        # 数组参数退化为指针
        decayed_type = param_type.decay_to_pointer()

        # 注册到当前作用域
        self.current_scope_arrays[param_name] = decayed_type
        self.bounds_checker.register_array(param_name, decayed_type)

        return ArrayAnalysisResult(
            success=True,
            array_type=decayed_type,
            warnings=[f"数组参数 '{param_name}' 退化为指针"],
        )

    def analyze_array_assignment(
        self,
        target_name: str,
        value_type: ArrayTypeInfo,
        source_location: Optional[Tuple[int, int]] = None,
    ) -> ArrayAnalysisResult:
        """
        分析数组赋值

        Args:
            target_name: 目标数组名
            value_type: 值的数组类型
            source_location: 源码位置

        Returns:
            分析结果
        """
        errors: List[BoundsError] = []

        target_type = self.current_scope_arrays.get(target_name)
        if target_type is None:
            return ArrayAnalysisResult(success=True, warnings=["未知目标数组"])

        # 检查类型兼容性
        if not target_type.is_compatible_with(value_type):
            errors.append(
                BoundsError(
                    message=f"数组类型不兼容: 无法将 '{value_type}' 赋值给 '{target_type}'",
                    severity=Severity.ERROR,
                    source_line=source_location[0] if source_location else None,
                    source_column=source_location[1] if source_location else None,
                )
            )

        return ArrayAnalysisResult(
            success=len(errors) == 0, array_type=target_type, errors=errors
        )

    def analyze_array_size_expression(
        self, size_expr: Any, source_location: Optional[Tuple[int, int]] = None
    ) -> Tuple[Optional[int], List[BoundsError]]:
        """
        分析数组大小表达式

        Args:
            size_expr: 大小表达式
            source_location: 源码位置

        Returns:
            (大小值, 错误列表)
        """
        errors: List[BoundsError] = []

        # 常量大小
        if isinstance(size_expr, int):
            if size_expr < 0:
                errors.append(
                    BoundsError(
                        message=f"数组大小不能为负数: {size_expr}",
                        severity=Severity.ERROR,
                        source_line=source_location[0] if source_location else None,
                        source_column=source_location[1] if source_location else None,
                    )
                )
                return None, errors
            if size_expr == 0:
                errors.append(
                    BoundsError(
                        message="数组大小为零",
                        severity=Severity.WARNING,
                        source_line=source_location[0] if source_location else None,
                        source_column=source_location[1] if source_location else None,
                    )
                )
            return size_expr, errors

        # 变量大小（VLA）
        if hasattr(size_expr, "name"):
            # 变量表达式
            return None, []  # 动态大小

        # 无法确定
        return None, errors

    def enter_scope(self) -> None:
        """进入新作用域"""
        # 保存当前作用域的数组信息
        pass

    def leave_scope(self) -> None:
        """离开作用域"""
        # 清理当前作用域的数组信息
        for name in list(self.current_scope_arrays.keys()):
            self.bounds_checker.unregister_array(name)
            del self.current_scope_arrays[name]

    def get_array_type(self, name: str) -> Optional[ArrayTypeInfo]:
        """获取数组类型信息"""
        return self.current_scope_arrays.get(name)

    def _get_expression_type(self, expr: Any) -> Optional[str]:
        """获取表达式类型"""
        if hasattr(expr, "inferred_type"):
            return expr.inferred_type
        if isinstance(expr, int):
            return "整数型"
        if isinstance(expr, float):
            return "浮点型"
        if isinstance(expr, str):
            return "字符串型"
        return None

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            "arrays_in_scope": len(self.current_scope_arrays),
            "bounds_check_summary": self.bounds_checker.get_summary(),
        }


class ArrayTypeValidator:
    """
    数组类型验证器

    提供数组类型的各种验证功能。
    """

    @staticmethod
    def validate_element_type(element_type: str) -> bool:
        """验证元素类型是否有效"""
        valid_types = {
            "整数型",
            "长整数型",
            "短整数型",
            "字符型",
            "浮点型",
            "双精度浮点型",
            "布尔型",
            "字符串型",
            "空型",
        }
        return element_type in valid_types

    @staticmethod
    def validate_dimensions(dimensions: List[Optional[int]]) -> Tuple[bool, List[str]]:
        """
        验证维度是否有效

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        for i, dim in enumerate(dimensions):
            if dim is not None:
                if dim < 0:
                    errors.append(f"维度 {i} 大小为负数: {dim}")
                elif dim == 0:
                    errors.append(f"维度 {i} 大小为零")

        return len(errors) == 0, errors

    @staticmethod
    def check_initialization_size(
        declared_size: Optional[int], init_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        检查初始化大小是否匹配

        Returns:
            (是否匹配, 错误消息)
        """
        if declared_size is None:
            return True, None

        if init_size > declared_size:
            return False, f"初始化元素过多: {init_size} > {declared_size}"

        if init_size < declared_size:
            # 部分初始化，允许但警告
            return True, f"部分初始化: {init_size} < {declared_size}"

        return True, None

    @staticmethod
    def check_type_compatibility(
        source_type: ArrayTypeInfo, target_type: ArrayTypeInfo
    ) -> Tuple[bool, Optional[str]]:
        """
        检查类型兼容性

        Returns:
            (是否兼容, 错误消息)
        """
        # 元素类型必须相同
        if source_type.element_type != target_type.element_type:
            return False, (
                f"元素类型不匹配: '{source_type.element_type}' vs '{target_type.element_type}'"
            )

        # 维度数量必须相同
        if source_type.rank != target_type.rank:
            return False, (f"维度数量不匹配: {source_type.rank} vs {target_type.rank}")

        # 检查每个维度
        for i, (s_dim, t_dim) in enumerate(
            zip(source_type.dimensions, target_type.dimensions)
        ):
            if s_dim is not None and t_dim is not None and s_dim != t_dim:
                return False, f"维度 {i} 大小不匹配: {s_dim} vs {t_dim}"

        return True, None
