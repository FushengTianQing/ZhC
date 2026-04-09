"""
Parser 错误恢复模块

提供语法分析阶段的错误恢复策略，包括：
- Token 插入恢复
- 同步点跳转
- 占位节点创建
- 恐慌模式恢复

创建日期: 2026-04-10
最后更新: 2026-04-10
维护者: ZHC开发团队
"""

from typing import Optional, List, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .lexer import Token
    from .ast_nodes import ASTNode
    from ..errors.base import ZHCError
    from ..errors.recovery import ErrorRecoveryStrategy


@dataclass
class ParserRecoveryContext:
    """
    Parser 恢复上下文

    包含语法分析错误恢复所需的所有上下文信息。
    """

    tokens: List[Any] = field(default_factory=list)  # Token 列表
    current_idx: int = 0  # 当前索引
    parser_state: dict = field(default_factory=dict)  # 解析器状态
    expected_tokens: List[str] = field(default_factory=list)  # 期望的 Token 类型
    recovery_depth: int = 0  # 恢复嵌套深度
    last_sync_point: int = -1  # 上次同步点位置


@dataclass
class PlaceholderNode:
    """
    占位 AST 节点

    用于错误恢复时创建临时节点，以便继续分析后续代码。
    """

    node_type: str = "ERROR_NODE"
    line: int = 0
    column: int = 0
    error_message: str = ""
    is_placeholder: bool = True

    def to_ast_node(self) -> "ASTNode":
        """
        转换为标准 ASTNode 对象

        Returns:
            ASTNode 对象
        """
        from .ast_nodes import ASTNodeType, IdentifierExprNode

        # 使用 IdentifierExprNode 作为占位节点的具体实现
        # 因为 ASTNode 是抽象类，不能直接实例化
        node = IdentifierExprNode(name="__error_placeholder__")
        node.node_type = ASTNodeType.ERROR_NODE
        node.line = self.line
        node.column = self.column
        node.attributes["error_message"] = self.error_message
        node.attributes["is_placeholder"] = True
        return node


class ParserErrorRecovery:
    """
    Parser 错误恢复

    处理语法分析阶段的错误，提供恢复策略使分析能够继续进行。
    """

    def __init__(
        self,
        parser: Any,
        recovery_strategy: "ErrorRecoveryStrategy",
    ):
        """
        初始化 Parser 错误恢复

        Args:
            parser: Parser 实例
            recovery_strategy: 错误恢复策略
        """
        self.parser = parser
        self.strategy = recovery_strategy
        self._placeholder_nodes: List[PlaceholderNode] = []
        self._recovery_count = 0
        self._inserted_tokens: List[Tuple[int, Any]] = []
        self._skipped_tokens: List[Tuple[int, Any]] = []

    def handle_error(
        self,
        error: "ZHCError",
        tokens: List["Token"],
        current_idx: int,
    ) -> Tuple[Optional["ASTNode"], int]:
        """
        处理语法错误并恢复

        Args:
            error: 错误对象
            tokens: Token 列表
            current_idx: 当前索引

        Returns:
            (ASTNode, 新索引) 元组
        """
        # 记录错误
        self.strategy.errors.add(error)
        self._recovery_count += 1

        # 创建恢复上下文
        context = ParserRecoveryContext(
            tokens=tokens,
            current_idx=current_idx,
            parser_state={},
            expected_tokens=[],
            recovery_depth=0,
            last_sync_point=-1,
        )

        # 选择恢复策略
        action = self.strategy.recover(error, context)

        # 执行恢复动作
        if action.name == "INSERT_TOKEN":
            return self._insert_token(error, tokens, current_idx)
        elif action.name == "SKIP_TO_SYNC":
            sync_type = self._get_sync_type(error)
            sync_idx = self.strategy.find_sync_point(tokens, current_idx, sync_type)
            self._skipped_tokens.extend(
                [(i, tokens[i]) for i in range(current_idx, sync_idx)]
            )
            return None, sync_idx + 1
        elif action.name == "CREATE_PLACEHOLDER":
            return self._create_placeholder(error), current_idx + 1
        elif action.name == "ABORT":
            from ..errors.recovery import CompilationAbortedError

            raise CompilationAbortedError("错误数量过多，编译中止")
        else:
            # SKIP_TOKEN 或默认
            return None, current_idx + 1

    def _insert_token(
        self,
        error: "ZHCError",
        tokens: List["Token"],
        current_idx: int,
    ) -> Tuple[Optional["ASTNode"], int]:
        """
        插入缺失的 Token

        Args:
            error: 错误对象
            tokens: Token 列表
            current_idx: 当前索引

        Returns:
            (None, 新索引) 元组
        """
        # 从错误上下文中获取期望的 Token 类型
        expected_token_type = (
            error.context.get("expected_token") if error.context else None
        )

        if expected_token_type:
            # 创建虚拟 Token
            from .lexer import Token

            virtual_token = Token(
                type=expected_token_type,
                value="",
                line=tokens[current_idx].line if current_idx < len(tokens) else 0,
                column=tokens[current_idx].column if current_idx < len(tokens) else 0,
            )

            # 记录插入的 Token
            self._inserted_tokens.append((current_idx, virtual_token))

            # 插入并继续解析
            tokens.insert(current_idx, virtual_token)
            return None, current_idx

        return None, current_idx + 1

    def _create_placeholder(self, error: "ZHCError") -> "ASTNode":
        """
        创建占位节点

        Args:
            error: 错误对象

        Returns:
            占位 AST 节点
        """
        placeholder = PlaceholderNode(
            node_type="ERROR_NODE",
            line=error.location.line if error.location else 0,
            column=error.location.column if error.location else 0,
            error_message=error.message,
            is_placeholder=True,
        )

        self._placeholder_nodes.append(placeholder)
        return placeholder.to_ast_node()

    def _get_sync_type(self, error: "ZHCError") -> str:
        """
        根据错误类型获取同步点类型

        Args:
            error: 错误对象

        Returns:
            同步点类型
        """
        return self.strategy.get_sync_type_for_error(error)

    def get_recovery_count(self) -> int:
        """
        获取恢复次数

        Returns:
            恢复次数
        """
        return self._recovery_count

    def get_inserted_tokens(self) -> List[Tuple[int, Any]]:
        """
        获取插入的 Token 列表

        Returns:
            插入的 Token 列表
        """
        return self._inserted_tokens.copy()

    def get_skipped_tokens(self) -> List[Tuple[int, Any]]:
        """
        获取跳过的 Token 列表

        Returns:
            跳过的 Token 列表
        """
        return self._skipped_tokens.copy()

    def clear(self) -> None:
        """清空恢复状态"""
        self._placeholder_nodes.clear()
        self._inserted_tokens.clear()
        self._skipped_tokens.clear()
        self._recovery_count = 0


class ParserErrorCollector:
    """
    Parser 错误收集器

    收集语法分析过程中的错误，支持批量处理。
    """

    def __init__(self):
        """初始化错误收集器"""
        self._errors: list["ZHCError"] = []
        self._warnings: list["ZHCError"] = []
        self._error_by_line: dict[int, list["ZHCError"]] = {}

    def add_error(
        self,
        message: str,
        location: Optional[Any] = None,
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

        # 按行索引错误
        if location:
            line = location.line
            if line not in self._error_by_line:
                self._error_by_line[line] = []
            self._error_by_line[line].append(error)

        return error

    def add_warning(
        self,
        message: str,
        location: Optional[Any] = None,
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

    def get_all(self) -> list["ZHCError"]:
        """获取所有消息"""
        return self._errors + self._warnings

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
        self._error_by_line.clear()

    def get_errors_at_line(self, line: int) -> list["ZHCError"]:
        """
        获取指定行的错误

        Args:
            line: 行号

        Returns:
            错误列表
        """
        return self._error_by_line.get(line, [])

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
    "ParserRecoveryContext",
    "PlaceholderNode",
    "ParserErrorRecovery",
    "ParserErrorCollector",
]
