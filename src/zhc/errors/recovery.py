"""
错误恢复机制

提供编译器错误恢复策略，允许在遇到错误后继续编译，
收集所有错误而不是在第一个错误处停止。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ZHCError, ErrorCollection


class RecoveryAction(Enum):
    """
    恢复动作类型

    定义了编译器在遇到错误后可以采取的恢复策略。
    """

    SKIP_TOKEN = auto()  # 跳过当前 Token
    SKIP_TO_SYNC = auto()  # 跳到同步点
    INSERT_TOKEN = auto()  # 插入缺失 Token
    REPLACE_TOKEN = auto()  # 替换错误 Token
    CREATE_PLACEHOLDER = auto()  # 创建占位节点
    ABORT = auto()  # 中止当前分析


@dataclass
class RecoveryContext:
    """
    恢复上下文

    包含错误恢复所需的所有上下文信息。
    """

    tokens: List[Any] = field(default_factory=list)  # Token 列表
    current_idx: int = 0  # 当前索引
    parser_state: Optional[Dict[str, Any]] = None  # 解析器状态
    source_file: Optional[str] = None  # 源文件路径
    scope_stack: Optional[List[Any]] = None  # 作用域栈

    def get_current_token(self) -> Optional[Any]:
        """获取当前 Token"""
        if 0 <= self.current_idx < len(self.tokens):
            return self.tokens[self.current_idx]
        return None

    def get_next_token(self) -> Optional[Any]:
        """获取下一个 Token"""
        if 0 <= self.current_idx + 1 < len(self.tokens):
            return self.tokens[self.current_idx + 1]
        return None


class ErrorRecoveryStrategy:
    """
    错误恢复策略

    根据错误类型选择合适的恢复策略，使编译器能够继续分析。

    Example:
        >>> from zhc.errors import ErrorCollection
        >>> errors = ErrorCollection()
        >>> strategy = ErrorRecoveryStrategy(errors)
        >>> action = strategy.recover(error, context)
    """

    # 同步点 Token（用于恢复）
    SYNC_TOKENS = {
        "statement": ["分号", "右花括号", "SEMICOLON", "RBRACE"],
        "declaration": [
            "整数型",
            "浮点型",
            "字符型",
            "字符串型",
            "布尔型",
            "空型",
            "INT",
            "FLOAT",
            "CHAR",
            "STRING",
            "BOOL",
            "VOID",
        ],
        "expression": [
            "分号",
            "右括号",
            "右花括号",
            "逗号",
            "SEMICOLON",
            "RPAREN",
            "RBRACE",
            "COMMA",
        ],
        "block": ["右花括号", "RBRACE"],
        "function": [
            "整数型",
            "浮点型",
            "字符型",
            "字符串型",
            "布尔型",
            "空型",
            "右花括号",
            "INT",
            "FLOAT",
            "CHAR",
            "STRING",
            "BOOL",
            "VOID",
            "RBRACE",
        ],
        "class": ["类", "结构体", "右花括号", "CLASS", "STRUCT", "RBRACE"],
    }

    def __init__(self, error_collection: "ErrorCollection", max_errors: int = 100):
        """
        初始化错误恢复策略

        Args:
            error_collection: 错误集合
            max_errors: 最大错误数量限制
        """
        self.errors = error_collection
        self.max_errors = max_errors
        self._recovery_points: List[Dict[str, Any]] = []

    def recover(self, error: "ZHCError", context: RecoveryContext) -> RecoveryAction:
        """
        根据错误类型选择恢复策略

        Args:
            error: 错误对象
            context: 恢复上下文

        Returns:
            恢复动作
        """
        # 检查是否达到最大错误数
        if self.errors.error_count() >= self.max_errors:
            return RecoveryAction.ABORT

        # 根据错误类型选择策略
        error_code = error.error_code or ""

        if error_code.startswith("PARSER_") or error_code.startswith(
            "PIPELINE_SYNTAX_"
        ):
            return self._recover_parser_error(error, context)
        elif error_code.startswith("SEMANTIC_") or error_code.startswith(
            "PIPELINE_SEMANTIC_"
        ):
            return self._recover_semantic_error(error, context)
        elif error_code.startswith("LEXER_"):
            return self._recover_lexer_error(error, context)
        else:
            return RecoveryAction.SKIP_TOKEN

    def _recover_lexer_error(
        self, error: "ZHCError", context: RecoveryContext
    ) -> RecoveryAction:
        """词法错误恢复"""
        error_code = error.error_code or ""

        # 非法字符：跳过
        if "ILLEGAL" in error_code or "INVALID" in error_code:
            return RecoveryAction.SKIP_TOKEN

        # 未终止的字符串/注释：跳到行尾或文件尾
        if "UNTERMINATED" in error_code:
            return RecoveryAction.SKIP_TO_SYNC

        return RecoveryAction.SKIP_TOKEN

    def _recover_parser_error(
        self, error: "ZHCError", context: RecoveryContext
    ) -> RecoveryAction:
        """语法错误恢复"""
        error_code = error.error_code or ""

        # 缺失 Token：尝试插入
        if "MISSING" in error_code:
            return RecoveryAction.INSERT_TOKEN

        # 意外 Token：跳到同步点
        if "UNEXPECTED" in error_code:
            return RecoveryAction.SKIP_TO_SYNC

        # 不平衡括号：跳到匹配点
        if "UNBALANCED" in error_code:
            return RecoveryAction.SKIP_TO_SYNC

        # 无效声明/语句：跳到下一个声明/语句
        if "INVALID" in error_code:
            return RecoveryAction.SKIP_TO_SYNC

        return RecoveryAction.SKIP_TOKEN

    def _recover_semantic_error(
        self, error: "ZHCError", context: RecoveryContext
    ) -> RecoveryAction:
        """语义错误恢复"""
        error_code = error.error_code or ""

        # 未定义符号：创建占位符
        if "UNDEFINED" in error_code:
            return RecoveryAction.CREATE_PLACEHOLDER

        # 类型不匹配：继续分析
        if "TYPE_MISMATCH" in error_code or "INCOMPATIBLE" in error_code:
            return RecoveryAction.SKIP_TOKEN

        # 重复定义：跳过
        if "DUPLICATE" in error_code:
            return RecoveryAction.SKIP_TOKEN

        return RecoveryAction.SKIP_TOKEN

    def find_sync_point(
        self, tokens: List[Any], current_idx: int, sync_type: str = "statement"
    ) -> int:
        """
        查找同步点

        从当前位置开始查找下一个同步点 Token。

        Args:
            tokens: Token 列表
            current_idx: 当前索引
            sync_type: 同步点类型

        Returns:
            同步点索引，如果未找到则返回最后一个索引
        """
        sync_tokens = self.SYNC_TOKENS.get(sync_type, self.SYNC_TOKENS["statement"])

        for i in range(current_idx, len(tokens)):
            token = tokens[i]
            token_type = self._get_token_type(token)

            if token_type in sync_tokens:
                return i

        return len(tokens) - 1

    def _get_token_type(self, token: Any) -> str:
        """获取 Token 类型字符串"""
        if hasattr(token, "type"):
            token_type = token.type
            if hasattr(token_type, "name"):
                return token_type.name
            return str(token_type)
        elif hasattr(token, "token_type"):
            return str(token.token_type)
        else:
            return str(token)

    def save_recovery_point(self, context: RecoveryContext) -> int:
        """
        保存恢复点

        保存当前解析状态，以便在错误恢复后回退。

        Args:
            context: 恢复上下文

        Returns:
            恢复点索引
        """
        point = {
            "idx": context.current_idx,
            "parser_state": context.parser_state,
        }
        self._recovery_points.append(point)
        return len(self._recovery_points) - 1

    def restore_recovery_point(self, point_idx: int, context: RecoveryContext) -> bool:
        """
        恢复到指定恢复点

        Args:
            point_idx: 恢复点索引
            context: 恢复上下文

        Returns:
            是否成功恢复
        """
        if 0 <= point_idx < len(self._recovery_points):
            point = self._recovery_points[point_idx]
            context.current_idx = point["idx"]
            context.parser_state = point["parser_state"]
            return True
        return False

    def get_sync_type_for_error(self, error: "ZHCError") -> str:
        """
        根据错误类型获取同步点类型

        Args:
            error: 错误对象

        Returns:
            同步点类型
        """
        error_code = error.error_code or ""
        error_code_lower = error_code.lower()

        if "declaration" in error_code_lower:
            return "declaration"
        elif "statement" in error_code_lower:
            return "statement"
        elif "expression" in error_code_lower:
            return "expression"
        elif "function" in error_code_lower:
            return "function"
        elif "class" in error_code_lower or "struct" in error_code_lower:
            return "class"
        else:
            return "block"


class CompilationAbortedError(Exception):
    """
    编译中止异常

    当错误数量超过限制时抛出。
    """

    def __init__(self, message: str = "错误数量过多，编译中止"):
        super().__init__(message)
        self.message = message


# 导出公共API
__all__ = [
    "RecoveryAction",
    "RecoveryContext",
    "ErrorRecoveryStrategy",
    "CompilationAbortedError",
]
