"""
语义分析错误恢复

提供语义分析阶段的错误恢复策略，包括：
- 未定义符号处理
- 类型不匹配处理
- 重复定义处理
- 占位符符号创建

创建日期: 2026-04-10
最后更新: 2026-04-10
维护者: ZHC开发团队
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..parser.ast_nodes import ASTNode
    from .semantic_analyzer import Symbol
    from ..errors.base import ZHCError, SourceLocation
    from ..errors.recovery import ErrorRecoveryStrategy


@dataclass
class PlaceholderSymbol:
    """
    占位符号

    用于错误恢复时创建临时符号，以便继续分析后续代码。
    """

    name: str
    symbol_type: str
    data_type: str = "未知"
    is_placeholder: bool = True
    definition_location: str = ""

    def to_symbol(self) -> "Symbol":
        """
        转换为标准 Symbol 对象

        Returns:
            Symbol 对象
        """
        from .semantic_analyzer import Symbol, ScopeType

        return Symbol(
            name=self.name,
            symbol_type=self.symbol_type,
            data_type=self.data_type,
            scope_level=0,
            scope_type=ScopeType.GLOBAL,
            is_defined=False,
            definition_location=self.definition_location,
        )


@dataclass
class SemanticRecoveryContext:
    """
    语义恢复上下文

    包含语义分析错误恢复所需的所有上下文信息。
    """

    current_function: Optional[str] = None  # 当前分析的函数名
    current_struct: Optional[str] = None  # 当前分析的结构体名
    current_scope: int = 0  # 当前作用域深度
    loop_depth: int = 0  # 循环嵌套深度
    symbol_table: Dict[str, Any] = field(default_factory=dict)  # 符号表快照
    type_hints: Dict[str, str] = field(default_factory=dict)  # 类型提示
    expected_types: Dict[str, str] = field(default_factory=dict)  # 期望类型


class SemanticErrorRecovery:
    """
    语义分析错误恢复

    处理语义分析阶段的错误，提供恢复策略使分析能够继续进行。
    """

    def __init__(
        self,
        analyzer: Any,
        recovery_strategy: "ErrorRecoveryStrategy",
    ):
        """
        初始化语义错误恢复

        Args:
            analyzer: 语义分析器实例
            recovery_strategy: 错误恢复策略
        """
        self.analyzer = analyzer
        self.strategy = recovery_strategy
        self._placeholder_symbols: Dict[str, PlaceholderSymbol] = {}
        self._recovery_count = 0

    def handle_undefined_symbol(
        self,
        name: str,
        node: "ASTNode",
        symbol_type: str = "变量",
    ) -> "PlaceholderSymbol":
        """
        处理未定义符号

        Args:
            name: 符号名称
            node: AST 节点
            symbol_type: 符号类型（变量/函数/类型等）

        Returns:
            占位符号对象
        """
        # 创建占位符号
        placeholder = PlaceholderSymbol(
            name=name,
            symbol_type=symbol_type,
            data_type="未知",
            is_placeholder=True,
            definition_location=f"{node.line}:{node.column}",
        )

        # 记录到缓存
        self._placeholder_symbols[name] = placeholder
        self._recovery_count += 1

        return placeholder

    def handle_type_mismatch(
        self,
        expected: str,
        actual: str,
        node: "ASTNode",
        context: str = "",
    ) -> str:
        """
        处理类型不匹配

        Args:
            expected: 期望的类型
            actual: 实际类型
            node: AST 节点
            context: 上下文信息

        Returns:
            兼容类型（用于继续分析）
        """
        self._recovery_count += 1

        # 返回一个兼容类型以便继续分析
        # 如果两者都是数值类型，返回数值类型的公共父类型
        numeric_types = {"整数型", "浮点型", "短整数型", "长整数型", "INT", "FLOAT"}
        if expected in numeric_types and actual in numeric_types:
            # 优先使用期望类型
            return expected

        # 如果两者都是指针类型，返回期望类型
        if expected.endswith("*") or actual.endswith("*"):
            return expected if expected.endswith("*") else actual

        # 否则返回 "未知" 类型
        return "未知"

    def handle_duplicate_definition(
        self,
        name: str,
        node: "ASTNode",
        original_location: str,
    ) -> None:
        """
        处理重复定义

        Args:
            name: 符号名称
            node: AST 节点
            original_location: 原定义位置
        """
        self._recovery_count += 1
        # 重复定义通常跳过即可，不需要创建占位符

    def handle_missing_return(
        self,
        function_name: str,
        node: "ASTNode",
    ) -> None:
        """
        处理缺失返回语句

        Args:
            function_name: 函数名
            node: AST 节点
        """
        self._recovery_count += 1
        # 缺失返回语句不需要创建占位符

    def handle_invalid_operation(
        self,
        operation: str,
        left_type: str,
        right_type: str,
        node: "ASTNode",
    ) -> str:
        """
        处理无效操作

        Args:
            operation: 操作符
            left_type: 左操作数类型
            right_type: 右操作数类型
            node: AST 节点

        Returns:
            结果类型
        """
        self._recovery_count += 1

        # 根据操作类型推断结果类型
        if operation in {"+", "-", "*", "/", "%"}:
            # 算术操作
            if "浮点" in left_type or "浮点" in right_type:
                return "浮点型"
            return "整数型"
        elif operation in {"==", "!=", "<", ">", "<=", ">="}:
            # 比较操作
            return "布尔型"
        elif operation in {"&&", "||", "!"}:
            # 逻辑操作
            return "布尔型"
        else:
            return "未知"

    def handle_uninitialized_use(
        self,
        name: str,
        node: "ASTNode",
    ) -> None:
        """
        处理使用未初始化变量

        Args:
            name: 变量名
            node: AST 节点
        """
        self._recovery_count += 1
        # 标记为已使用，但不阻止继续分析

    def handle_unreachable_code(
        self,
        node: "ASTNode",
    ) -> None:
        """
        处理不可达代码

        Args:
            node: AST 节点
        """
        # 不可达代码是警告级别，不增加恢复计数
        pass

    def get_placeholder_symbol(self, name: str) -> Optional[PlaceholderSymbol]:
        """
        获取占位符号

        Args:
            name: 符号名称

        Returns:
            占位符号对象，如果不存在则返回 None
        """
        return self._placeholder_symbols.get(name)

    def get_recovery_count(self) -> int:
        """
        获取恢复次数

        Returns:
            恢复次数
        """
        return self._recovery_count

    def clear_placeholders(self) -> None:
        """清空所有占位符号"""
        self._placeholder_symbols.clear()

    def create_recovery_context(
        self,
        current_function: Optional[str] = None,
        current_struct: Optional[str] = None,
    ) -> SemanticRecoveryContext:
        """
        创建恢复上下文

        Args:
            current_function: 当前函数名
            current_struct: 当前结构体名

        Returns:
            恢复上下文对象
        """
        return SemanticRecoveryContext(
            current_function=current_function,
            current_struct=current_struct,
            current_scope=0,
            loop_depth=0,
            symbol_table={},
            type_hints={},
            expected_types={},
        )


class SemanticErrorCollector:
    """
    语义错误收集器

    收集语义分析过程中的错误，支持批量处理。
    """

    def __init__(self):
        """初始化错误收集器"""
        self._errors: list["ZHCError"] = []
        self._warnings: list["ZHCError"] = []
        self._infos: list["ZHCError"] = []
        self._error_by_node: Dict[int, list["ZHCError"]] = {}

    def add_error(
        self,
        message: str,
        location: Optional["SourceLocation"] = None,
        error_code: Optional[str] = None,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> "ZHCError":
        """
        添加错误

        Args:
            message: 错误消息
            location: 错误位置
            error_code: 错误代码
            context: 上下文信息
            suggestion: 修复建议

        Returns:
            创建的错误对象
        """
        from ..errors import ZHCError

        error = ZHCError(
            message=message,
            location=location,
            error_code=error_code,
            severity=ZHCError.SEVERITY_ERROR,
            context=context,
            suggestion=suggestion,
        )

        self._errors.append(error)

        # 按节点索引错误
        if location:
            node_key = hash((location.line, location.column))
            if node_key not in self._error_by_node:
                self._error_by_node[node_key] = []
            self._error_by_node[node_key].append(error)

        return error

    def add_warning(
        self,
        message: str,
        location: Optional["SourceLocation"] = None,
        error_code: Optional[str] = None,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> "ZHCError":
        """
        添加警告

        Args:
            message: 警告消息
            location: 警告位置
            error_code: 警告代码
            context: 上下文信息
            suggestion: 修复建议

        Returns:
            创建的警告对象
        """
        from ..errors import ZHCError

        warning = ZHCError(
            message=message,
            location=location,
            error_code=error_code,
            severity=ZHCError.SEVERITY_WARNING,
            context=context,
            suggestion=suggestion,
        )

        self._warnings.append(warning)
        return warning

    def get_errors(self) -> list["ZHCError"]:
        """获取所有错误"""
        return self._errors.copy()

    def get_warnings(self) -> list["ZHCError"]:
        """获取所有警告"""
        return self._warnings.copy()

    def get_infos(self) -> list["ZHCError"]:
        """获取所有信息"""
        return self._infos.copy()

    def get_all(self) -> list["ZHCError"]:
        """获取所有消息"""
        return self._errors + self._warnings + self._infos

    def error_count(self) -> int:
        """获取错误数量"""
        return len(self._errors)

    def warning_count(self) -> int:
        """获取警告数量"""
        return len(self._warnings)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self._errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self._warnings) > 0

    def clear(self) -> None:
        """清空所有错误"""
        self._errors.clear()
        self._warnings.clear()
        self._infos.clear()
        self._error_by_node.clear()

    def get_errors_at(self, line: int, column: int) -> list["ZHCError"]:
        """
        获取指定位置的错误

        Args:
            line: 行号
            column: 列号

        Returns:
            错误列表
        """
        node_key = hash((line, column))
        return self._error_by_node.get(node_key, [])

    def get_summary(self) -> str:
        """
        获取错误摘要

        Returns:
            错误摘要字符串
        """
        parts = []

        if self.error_count() > 0:
            parts.append(f"{self.error_count()} 个错误")

        if self.warning_count() > 0:
            parts.append(f"{self.warning_count()} 个警告")

        if not parts:
            return "无错误或警告"

        return "发现 " + ", ".join(parts) + "。"


# 导出公共 API
__all__ = [
    "PlaceholderSymbol",
    "SemanticRecoveryContext",
    "SemanticErrorRecovery",
    "SemanticErrorCollector",
]
