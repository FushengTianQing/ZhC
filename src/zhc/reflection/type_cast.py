# -*- coding: utf-8 -*-
"""
ZhC 反射 - 类型转换

提供安全类型转换、动态类型转换、类型断言等功能。

设计原则：
- safe_cast: 安全转换，失败返回 None
- dynamic_cast: 动态转换，失败抛出异常
- static_cast: 静态转换（编译期检查，运行时无操作）
- require_type: 类型断言，失败抛出 TypeError

作者：远
日期：2026-04-11
"""

from typing import Optional, Any, TypeVar, Generic, List
from enum import Enum
from dataclasses import dataclass

from .type_check import TypeChecker

T = TypeVar("T")


# =============================================================================
# CastResult 泛型类（LLVM 风格）
# =============================================================================


@dataclass
class CastResult(Generic[T]):
    """类型转换结果（泛型类）

    类似 C++23 的 std::expected<T, E>，提供类型安全的转换结果。

    Attributes:
        success: 转换是否成功
        result: 转换后的对象（成功时）
        error: 错误信息（失败时）

    使用示例:
        result = safe_cast_as(obj, "狗")
        if result.success:
            dog = result.result
        else:
            print(result.error.message)
    """

    success: bool
    result: Optional[T] = None
    error: Optional["CastError"] = None

    def __bool__(self) -> bool:
        """支持 if result: 语法"""
        return self.success

    def unwrap(self) -> T:
        """获取结果，失败时抛出异常

        Raises:
            TypeCastError: 转换失败时
        """
        if not self.success:
            raise TypeCastError(
                self.error.source_type if self.error else "未知",
                self.error.target_type if self.error else "未知",
                self.error.message if self.error else "转换失败",
                error_type=self.error.error_type
                if self.error
                else CastErrorType.INVALID_CAST,
            )
        return self.result

    def unwrap_or(self, default: T) -> T:
        """获取结果，失败时返回默认值"""
        return self.result if self.success else default

    def is_ok(self) -> bool:
        """检查是否成功"""
        return self.success

    def is_err(self) -> bool:
        """检查是否失败"""
        return not self.success

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "success": self.success,
            "result": str(self.result) if self.result else None,
            "error": self.error.to_dict() if self.error else None,
        }


class CastErrorType(Enum):
    """转换错误类型"""

    NULL_SOURCE = "null_source"  # 源对象为空
    INVALID_CAST = "invalid_cast"  # 无效转换
    AMBIGUOUS_CAST = "ambiguous_cast"  # 歧义转换
    INTERFACE_NOT_FOUND = "interface_not_found"  # 接口未找到
    TYPE_MISMATCH = "type_mismatch"  # 类型不匹配
    NOT_SUBTYPE = "not_subtype"  # 不是子类型


@dataclass
class CastError:
    """转换错误详情

    提供详细的转换失败信息，包括：
    - 错误类型
    - 源类型和目标类型
    - 转换路径（如果存在）
    - 祖先类型列表
    - 建议的替代转换
    """

    error_type: CastErrorType
    message: str
    source_type: Optional[str] = None
    target_type: Optional[str] = None
    source_object: Optional[Any] = None
    cast_path: Optional[List[str]] = None
    ancestors: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None

    def __str__(self) -> str:
        return f"CastError({self.error_type.value}): {self.message}"

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "cast_path": self.cast_path,
            "ancestors": self.ancestors,
            "suggestions": self.suggestions,
        }


class TypeCastError(TypeError):
    """类型转换错误（兼容旧 API）"""

    def __init__(
        self,
        source_type: str,
        target_type: str,
        message: str = "",
        error_type: CastErrorType = CastErrorType.INVALID_CAST,
        cast_path: Optional[List[str]] = None,
        ancestors: Optional[List[str]] = None,
    ):
        self.source_type = source_type
        self.target_type = target_type
        self.error_type = error_type
        self.cast_path = cast_path
        self.ancestors = ancestors or []
        self.message = message or f"无法将 {source_type} 转换为 {target_type}"
        super().__init__(self.message)

    def to_cast_error(self) -> CastError:
        """转换为 CastError 对象"""
        return CastError(
            error_type=self.error_type,
            message=self.message,
            source_type=self.source_type,
            target_type=self.target_type,
            cast_path=self.cast_path,
            ancestors=self.ancestors,
        )


class TypeCast:
    """类型转换器

    提供多种类型转换方式：
    - safe_cast: 安全转换，失败返回 None
    - dynamic_cast: 动态转换，失败抛出异常
    - require_type: 类型断言，确保对象是指定类型
    - cast_to_interface: 转换为接口类型
    - get_cast_path: 获取类型转换路径
    """

    def __init__(self):
        self.checker = TypeChecker()

    def safe_cast(self, obj: Any, target_type: str) -> Optional[Any]:
        """安全类型转换

        如果对象类型兼容目标类型，返回对象本身；
        否则返回 None。

        Args:
            obj: 要转换的对象
            target_type: 目标类型名

        Returns:
            对象本身（如果类型兼容）或 None
        """
        if obj is None:
            return None

        # 获取对象的实际类型名
        obj_type = self._get_object_type(obj)
        if obj_type is None:
            return None

        # 检查类型兼容性
        if self.checker.is_type(obj_type, target_type):
            return obj
        return None

    def dynamic_cast(self, obj: Any, target_type: str) -> Any:
        """动态类型转换

        运行时检查类型兼容性，不兼容则抛出异常。

        Args:
            obj: 要转换的对象
            target_type: 目标类型名

        Returns:
            对象本身（如果类型兼容）

        Raises:
            TypeCastError: 类型不兼容时抛出
        """
        if obj is None:
            return None

        obj_type = self._get_object_type(obj)
        if obj_type is None:
            raise TypeCastError(
                "未知类型", target_type, error_type=CastErrorType.INVALID_CAST
            )

        if self.checker.is_type(obj_type, target_type):
            return obj

        # 获取转换路径用于错误信息
        path = self.get_cast_path(obj_type, target_type)
        ancestors = self._get_ancestors(obj_type)

        raise TypeCastError(
            obj_type,
            target_type,
            f"无法将 {obj_type} 向下转换为 {target_type}",
            error_type=CastErrorType.INVALID_CAST,
            cast_path=path,
            ancestors=ancestors,
        )

    def require_type(self, obj: Any, type_name: str) -> Any:
        """类型断言

        确保对象是指定类型，否则抛出 TypeError。

        Args:
            obj: 要检查的对象
            type_name: 期望的类型名

        Returns:
            对象本身（如果类型匹配）

        Raises:
            TypeError: 类型不匹配时抛出
        """
        if obj is None:
            raise TypeError(f"期望类型 {type_name}，实际为 None")

        obj_type = self._get_object_type(obj)
        if obj_type and self.checker.is_type(obj_type, type_name):
            return obj

        actual = obj_type or "未知类型"
        raise TypeError(f"期望类型 {type_name}，实际为 {actual}")

    def cast_to_interface(self, obj: Any, interface_name: str) -> Optional[Any]:
        """转换为接口类型

        检查对象是否实现了指定接口。

        Args:
            obj: 要转换的对象
            interface_name: 接口名

        Returns:
            对象本身（如果实现了接口）或 None
        """
        if obj is None:
            return None

        obj_type = self._get_object_type(obj)
        if obj_type and self.checker.implements_interface(obj_type, interface_name):
            return obj
        return None

    def try_cast(self, obj: Any, target_type: str) -> CastResult:
        """尝试类型转换（返回 CastResult）

        Args:
            obj: 要转换的对象
            target_type: 目标类型名

        Returns:
            CastResult: 转换结果（包含 success/result/error）
        """
        try:
            result = self.safe_cast(obj, target_type)
            if result is not None:
                return CastResult(success=True, result=result)
            # safe_cast 返回 None — 可能是类型不兼容
            obj_type = self._get_object_type(obj)
            return CastResult(
                success=False,
                error=CastError(
                    error_type=CastErrorType.TYPE_MISMATCH,
                    message=f"无法将 {obj_type or '未知类型'} 转换为 {target_type}",
                    source_type=obj_type,
                    target_type=target_type,
                ),
            )
        except Exception as e:
            return CastResult(
                success=False,
                error=CastError(
                    error_type=CastErrorType.INVALID_CAST,
                    message=str(e),
                    target_type=target_type,
                ),
            )

    def safe_cast_as(self, obj: Any, target_type: str) -> CastResult:
        """安全类型转换（返回 CastResult）

        等价于 try_cast，语义更明确。
        """
        return self.try_cast(obj, target_type)

    def dynamic_cast_as(self, obj: Any, target_type: str) -> CastResult:
        """动态类型转换（返回 CastResult）

        与 dynamic_cast 不同，失败时不抛异常，而是返回带错误的 CastResult。
        """
        try:
            result = self.dynamic_cast(obj, target_type)
            return CastResult(success=True, result=result)
        except TypeCastError as e:
            return CastResult(
                success=False,
                error=e.to_cast_error(),
            )

    def narrow_cast(self, obj: Any, target_type: str) -> Optional[Any]:
        """窄化转换（向下转型）

        将父类型转换为子类型。这是 safe_cast 的别名，
        但语义上强调这是"向下转型"。

        Args:
            obj: 要转换的对象（通常是父类型引用）
            target_type: 目标子类型名

        Returns:
            对象本身（如果实际类型是目标类型或其子类）或 None
        """
        return self.safe_cast(obj, target_type)

    def widen_cast(self, obj: Any, target_type: str) -> Any:
        """宽化转换（向上转型）

        将子类型转换为父类型。这总是安全的，
        因为子类型总是可以赋值给父类型。

        Args:
            obj: 要转换的对象
            target_type: 目标父类型名

        Returns:
            对象本身

        Raises:
            TypeCastError: 如果对象类型不是目标类型的子类型
        """
        return self.dynamic_cast(obj, target_type)

    def get_cast_path(self, source_type: str, target_type: str) -> Optional[List[str]]:
        """获取类型转换路径

        从源类型到目标类型的转换路径。如果不能转换，返回 None。

        Args:
            source_type: 源类型名
            target_type: 目标类型名

        Returns:
            转换路径列表（如 ["狗", "动物"]），或 None（如果无法转换）
        """
        if source_type == target_type:
            return [source_type]

        # 检查是否能转换
        if not self.checker.is_type(source_type, target_type):
            return None

        # 收集源类型的祖先链
        ancestors: List[str] = [source_type]
        current = source_type
        while True:
            parent = self.checker.hierarchy.get_parent(current)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        # 在祖先链中查找目标类型
        if target_type in ancestors:
            return ancestors[: ancestors.index(target_type) + 1]

        return None

    def can_cast(self, source_type: str, target_type: str) -> bool:
        """检查是否可以直接转换

        Args:
            source_type: 源类型名
            target_type: 目标类型名

        Returns:
            True 如果可以转换
        """
        return self.checker.is_type(source_type, target_type)

    def _get_object_type(self, obj: Any) -> Optional[str]:
        """获取对象的类型名

        Args:
            obj: 对象实例

        Returns:
            类型名字符串，或 None（如果无法确定）
        """
        # 尝试从对象的 __class__ 获取
        if hasattr(obj, "__class__"):
            cls = obj.__class__
            # 检查是否有 ZhC 类型名属性
            if hasattr(cls, "_zhc_type_name"):
                return cls._zhc_type_name
            # 使用 Python 类名
            return cls.__name__

        # 尝试从 type() 获取
        return type(obj).__name__

    def _get_ancestors(self, type_name: str) -> List[str]:
        """获取类型的祖先列表"""
        return self.checker.hierarchy.get_ancestors(type_name)


# ==================== 公共 API ====================

# 全局实例
_type_cast = TypeCast()


class CastValidator:
    """转换验证器

    提供转换前的验证和最佳转换匹配功能。
    """

    def __init__(self):
        self.caster = TypeCast()

    def validate(self, obj: Any, target_type: str) -> CastError:
        """验证转换是否有效

        Returns:
            CastError 如果有错误，否则 None（可以用 cast_error is not None 检查）
        """
        if obj is None:
            return CastError(
                error_type=CastErrorType.NULL_SOURCE,
                message="源对象为空",
                target_type=target_type,
            )

        obj_type = self.caster._get_object_type(obj)
        if obj_type is None:
            return CastError(
                error_type=CastErrorType.INVALID_CAST,
                message="无法确定源对象类型",
                target_type=target_type,
            )

        if self.caster.can_cast(obj_type, target_type):
            return None  # type: ignore

        ancestors = self.caster._get_ancestors(obj_type)
        return CastError(
            error_type=CastErrorType.INVALID_CAST,
            message=f"无法将 {obj_type} 转换为 {target_type}",
            source_type=obj_type,
            target_type=target_type,
            ancestors=ancestors,
        )

    def validate_all(self, obj: Any, target_types: List[str]) -> List[dict]:
        """验证对多个类型的转换

        Returns:
            列表，每项包含 {"target": str, "can_cast": bool, "error": Optional[CastError]}
        """
        results = []
        for target_type in target_types:
            error = self.validate(obj, target_type)
            results.append(
                {
                    "target": target_type,
                    "can_cast": error is None,
                    "error": error,
                }
            )
        return results

    def find_best_cast(self, obj: Any, target_types: List[str]) -> Optional[str]:
        """找到最佳转换目标

        按顺序检查目标类型列表，返回第一个可转换的类型。
        """
        for target_type in target_types:
            if self.validate(obj, target_type) is None:
                return target_type
        return None

    def get_suggestions(self, obj: Any) -> List[str]:
        """获取可转换的类型建议

        返回对象可以转换到的所有已知类型（包括自身和所有祖先）。
        """
        obj_type = self.caster._get_object_type(obj)
        if obj_type is None:
            return []

        suggestions = [obj_type]
        suggestions.extend(self.caster._get_ancestors(obj_type))
        return suggestions


# 全局验证器实例
_cast_validator = CastValidator()


def safe_cast(obj: Any, target_type: str) -> Optional[Any]:
    """安全类型转换（失败返回 None）"""
    return _type_cast.safe_cast(obj, target_type)


def dynamic_cast(obj: Any, target_type: str) -> Any:
    """动态类型转换（失败抛出异常）"""
    return _type_cast.dynamic_cast(obj, target_type)


def require_type(obj: Any, type_name: str) -> Any:
    """类型断言（确保对象是指定类型）"""
    return _type_cast.require_type(obj, type_name)


def cast_to_interface(obj: Any, interface_name: str) -> Optional[Any]:
    """转换为接口类型"""
    return _type_cast.cast_to_interface(obj, interface_name)


def try_cast(obj: Any, target_type: str) -> CastResult:
    """尝试类型转换，返回 CastResult"""
    return _type_cast.try_cast(obj, target_type)


def safe_cast_as(obj: Any, target_type: str) -> CastResult:
    """安全类型转换（返回 CastResult）"""
    return _type_cast.safe_cast_as(obj, target_type)


def dynamic_cast_as(obj: Any, target_type: str) -> CastResult:
    """动态类型转换（返回 CastResult，不抛异常）"""
    return _type_cast.dynamic_cast_as(obj, target_type)


def narrow_cast(obj: Any, target_type: str) -> Optional[Any]:
    """窄化转换（向下转型）"""
    return _type_cast.narrow_cast(obj, target_type)


def widen_cast(obj: Any, target_type: str) -> Any:
    """宽化转换（向上转型）"""
    return _type_cast.widen_cast(obj, target_type)


def get_cast_path(source_type: str, target_type: str) -> Optional[List[str]]:
    """获取类型转换路径"""
    return _type_cast.get_cast_path(source_type, target_type)


def can_cast(source_type: str, target_type: str) -> bool:
    """检查是否可以转换"""
    return _type_cast.can_cast(source_type, target_type)


def validate_cast(obj: Any, target_type: str) -> Optional[CastError]:
    """验证转换有效性"""
    return _cast_validator.validate(obj, target_type)


def find_best_cast(obj: Any, target_types: List[str]) -> Optional[str]:
    """找到最佳转换目标"""
    return _cast_validator.find_best_cast(obj, target_types)


__all__ = [
    # 泛型结果类
    "CastResult",
    # 错误类型
    "CastErrorType",
    "CastError",
    "TypeCastError",
    # 核心类
    "TypeCast",
    "CastValidator",
    # 转换 API
    "safe_cast",
    "dynamic_cast",
    "require_type",
    "cast_to_interface",
    "try_cast",
    "narrow_cast",
    "widen_cast",
    "safe_cast_as",
    "dynamic_cast_as",
    "get_cast_path",
    "can_cast",
    "validate_cast",
    "find_best_cast",
]
