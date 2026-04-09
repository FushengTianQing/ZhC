"""
错误模式管理

提供编译器的错误处理模式配置，支持严格/宽松/恢复三种模式。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ZHCError
    from .recovery import RecoveryAction, RecoveryContext, ErrorRecoveryStrategy


class ErrorMode(Enum):
    """
    错误处理模式

    - STRICT: 严格模式 - 遇到错误立即停止
    - LENIENT: 宽松模式 - 收集所有错误继续编译
    - RECOVER: 恢复模式 - 尝试恢复并继续
    """

    STRICT = auto()  # 严格模式：遇到错误立即停止
    LENIENT = auto()  # 宽松模式：收集所有错误继续
    RECOVER = auto()  # 恢复模式：尝试恢复并继续

    @property
    def description(self) -> str:
        """获取模式描述"""
        descriptions = {
            ErrorMode.STRICT: "严格模式 - 遇到错误立即停止编译",
            ErrorMode.LENIENT: "宽松模式 - 收集所有错误继续编译",
            ErrorMode.RECOVER: "恢复模式 - 尝试恢复错误并继续编译",
        }
        return descriptions.get(self, "未知模式")

    @property
    def should_stop_on_error(self) -> bool:
        """是否在遇到错误时停止"""
        return self == ErrorMode.STRICT

    @property
    def should_collect_all(self) -> bool:
        """是否收集所有错误"""
        return self in (ErrorMode.LENIENT, ErrorMode.RECOVER)

    @property
    def should_recover(self) -> bool:
        """是否尝试恢复"""
        return self == ErrorMode.RECOVER


@dataclass
class ErrorModeConfig:
    """
    错误模式配置

    包含错误处理模式的所有配置选项。
    """

    mode: ErrorMode = ErrorMode.LENIENT  # 错误处理模式
    max_errors: int = 100  # 最大错误数量
    max_warnings: int = 500  # 最大警告数量
    continue_on_warning: bool = True  # 遇到警告是否继续
    continue_on_info: bool = True  # 遇到信息是否继续
    show_recovery_info: bool = False  # 是否显示恢复信息

    def should_continue(self, error: "ZHCError") -> bool:
        """
        判断遇到指定错误后是否应该继续

        Args:
            error: 错误对象

        Returns:
            是否继续编译
        """

        # 严格模式：任何错误都停止
        if self.mode == ErrorMode.STRICT:
            return False

        # 检查错误数量
        if error.is_error() and hasattr(error, "_collection"):
            return error._collection.error_count() < self.max_errors

        if error.is_warning():
            return True  # 警告总是可以继续（除非达到上限）

        return True

    def create_summary_message(self, error_count: int, warning_count: int) -> str:
        """
        创建错误摘要消息

        Args:
            error_count: 错误数量
            warning_count: 警告数量

        Returns:
            摘要消息
        """
        parts = []

        if error_count > 0:
            parts.append(f"{error_count} 个错误")

        if warning_count > 0:
            parts.append(f"{warning_count} 个警告")

        if not parts:
            return "编译成功，无错误或警告"

        if error_count > 0:
            return "编译发现 " + ", ".join(parts) + "。"
        else:
            return "编译成功，发现 " + ", ".join(parts) + "。"


class ErrorModeManager:
    """
    错误模式管理器

    管理编译器的错误处理模式和恢复策略。

    Example:
        >>> manager = ErrorModeManager(ErrorMode.LENIENT)
        >>> manager.handle_error(error, context)
        >>> if not manager.should_continue():
        ...     return CompileResult(success=False, errors=manager.errors)
    """

    def __init__(self, mode: ErrorMode = ErrorMode.LENIENT, max_errors: int = 100):
        """
        初始化错误模式管理器

        Args:
            mode: 错误处理模式
            max_errors: 最大错误数量
        """
        self.config = ErrorModeConfig(mode=mode, max_errors=max_errors)
        self.errors: list["ZHCError"] = []
        self.warnings: list["ZHCError"] = []
        self.infos: list["ZHCError"] = []
        self._recovery_strategy: Optional["ErrorRecoveryStrategy"] = None
        self._error_callbacks: list[Callable[["ZHCError"], None]] = []
        self._recovery_callbacks: list[
            Callable[["RecoveryAction", "ZHCError"], None]
        ] = []
        self._total_errors = 0
        self._total_warnings = 0
        self._aborted = False

    @property
    def mode(self) -> ErrorMode:
        """获取当前模式"""
        return self.config.mode

    @mode.setter
    def mode(self, value: ErrorMode):
        """设置当前模式"""
        self.config.mode = value

    @property
    def recovery_strategy(self) -> Optional["ErrorRecoveryStrategy"]:
        """获取恢复策略"""
        return self._recovery_strategy

    @recovery_strategy.setter
    def recovery_strategy(self, value: "ErrorRecoveryStrategy"):
        """设置恢复策略"""
        self._recovery_strategy = value

    def register_error_callback(self, callback: Callable[["ZHCError"], None]):
        """
        注册错误回调

        Args:
            callback: 回调函数
        """
        self._error_callbacks.append(callback)

    def register_recovery_callback(
        self, callback: Callable[["RecoveryAction", "ZHCError"], None]
    ):
        """
        注册恢复回调

        Args:
            callback: 回调函数 (action, error)
        """
        self._recovery_callbacks.append(callback)

    def handle_error(
        self, error: "ZHCError", context: Optional["RecoveryContext"] = None
    ) -> Optional["RecoveryAction"]:
        """
        处理错误

        根据当前模式和上下文决定如何处理错误。

        Args:
            error: 错误对象
            context: 恢复上下文（可选）

        Returns:
            如果需要恢复，返回恢复动作；否则返回 None
        """
        # 记录错误
        self._record_error(error)

        # 调用错误回调
        for callback in self._error_callbacks:
            callback(error)

        # 严格模式：抛出异常
        if self.config.mode == ErrorMode.STRICT:
            raise error

        # 宽松/恢复模式：决定是否继续
        if not self._should_continue():
            self._aborted = True
            return None

        # 恢复模式：尝试恢复
        if (
            self.config.mode == ErrorMode.RECOVER
            and context
            and self._recovery_strategy
        ):
            action = self._recovery_strategy.recover(error, context)

            # 调用恢复回调
            for callback in self._recovery_callbacks:
                callback(action, error)

            return action

        return None

    def _record_error(self, error: "ZHCError"):
        """记录错误"""
        if error.is_error():
            self.errors.append(error)
            self._total_errors += 1
        elif error.is_warning():
            self.warnings.append(error)
            self._total_warnings += 1
        else:
            self.infos.append(error)

    def _should_continue(self) -> bool:
        """判断是否应该继续编译"""
        if self._aborted:
            return False

        if self._total_errors >= self.config.max_errors:
            return False

        if self._total_warnings >= self.config.max_warnings:
            return not self.config.continue_on_warning

        return True

    def should_continue(self) -> bool:
        """
        公开的继续判断方法

        Returns:
            是否应该继续编译
        """
        return self._should_continue() and not self._aborted

    def get_error_count(self) -> int:
        """获取错误数量"""
        return len(self.errors)

    def get_warning_count(self) -> int:
        """获取警告数量"""
        return len(self.warnings)

    def get_info_count(self) -> int:
        """获取信息数量"""
        return len(self.infos)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """
        获取错误摘要

        Returns:
            错误摘要字符串
        """
        return self.config.create_summary_message(
            self.get_error_count(), self.get_warning_count()
        )

    def get_all_errors(self) -> list["ZHCError"]:
        """获取所有错误"""
        return self.errors.copy()

    def get_all_warnings(self) -> list["ZHCError"]:
        """获取所有警告"""
        return self.warnings.copy()

    def get_all_infos(self) -> list["ZHCError"]:
        """获取所有信息"""
        return self.infos.copy()

    def get_all_messages(self) -> list["ZHCError"]:
        """获取所有消息"""
        return self.errors + self.warnings + self.infos

    def clear(self):
        """清空所有消息"""
        self.errors.clear()
        self.warnings.clear()
        self.infos.clear()
        self._aborted = False

    def is_aborted(self) -> bool:
        """是否已中止"""
        return self._aborted

    def abort(self, message: Optional[str] = None):
        """
        中止编译

        Args:
            message: 中止消息
        """
        self._aborted = True
        if message:
            self.handle_error(
                type(
                    "AbortError",
                    (),
                    {
                        "message": message,
                        "is_error": lambda self: True,
                        "is_warning": lambda self: False,
                        "is_info": lambda self: False,
                    },
                )()
            )


class ErrorRecoveryContext:
    """
    错误恢复上下文管理器

    辅助管理错误恢复过程中的上下文状态。
    """

    def __init__(self):
        """初始化"""
        self._states: list[dict] = []
        self._current_idx: int = -1

    def push_state(self, state: dict):
        """
        推入状态

        Args:
            state: 状态字典
        """
        self._states.append(state)
        self._current_idx = len(self._states) - 1

    def pop_state(self) -> Optional[dict]:
        """
        弹出状态

        Returns:
            状态字典
        """
        if self._states:
            state = self._states.pop()
            self._current_idx = len(self._states) - 1
            return state
        return None

    def get_current_state(self) -> Optional[dict]:
        """
        获取当前状态

        Returns:
            状态字典
        """
        if 0 <= self._current_idx < len(self._states):
            return self._states[self._current_idx]
        return None

    def rollback(self, checkpoint: int):
        """
        回滚到指定检查点

        Args:
            checkpoint: 检查点索引
        """
        if 0 <= checkpoint < len(self._states):
            self._states = self._states[:checkpoint]
            self._current_idx = len(self._states) - 1


# 导出公共API
__all__ = [
    "ErrorMode",
    "ErrorModeConfig",
    "ErrorModeManager",
    "ErrorRecoveryContext",
]
