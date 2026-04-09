"""
错误代码注册表

定义所有错误代码的元数据，支持智能错误提示和详细解释。

创建日期: 2026-04-09
最后更新: 2026-04-09
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ErrorCodeDefinition:
    """
    错误代码定义

    Attributes:
        code: 错误代码，如 "E001"
        category: 类别：类型错误、作用域错误等
        severity: 严重程度（error/warning/info）
        brief_message: 简短消息模板
        detailed_message: 详细消息模板
        common_causes: 常见原因列表
        suggestions: 修复建议列表
        documentation_url: 文档链接
        examples: 正确示例
    """

    code: str
    category: str
    severity: str = "error"
    brief_message: str = ""
    detailed_message: str = ""
    common_causes: List[str] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)

    def get_message(self, **kwargs) -> str:
        """
        获取格式化的消息

        Args:
            **kwargs: 模板变量

        Returns:
            格式化后的消息
        """
        try:
            return self.brief_message.format(**kwargs)
        except KeyError:
            return self.brief_message

    def get_detailed_message(self, **kwargs) -> str:
        """
        获取格式化的详细消息

        Args:
            **kwargs: 模板变量

        Returns:
            格式化后的详细消息
        """
        try:
            return self.detailed_message.format(**kwargs)
        except KeyError:
            return self.detailed_message


class ErrorCodeRegistry:
    """
    错误代码注册表

    管理所有错误代码的定义和查询。

    Example:
        >>> registry = ErrorCodeRegistry()
        >>> definition = registry.get("E001")
        >>> print(definition.brief_message)
        类型不匹配
    """

    # 错误代码定义
    _codes: Dict[str, ErrorCodeDefinition] = {}

    @classmethod
    def register(cls, definition: ErrorCodeDefinition) -> None:
        """
        注册错误代码

        Args:
            definition: 错误代码定义
        """
        cls._codes[definition.code] = definition

    @classmethod
    def get(cls, code: str) -> Optional[ErrorCodeDefinition]:
        """
        获取错误代码定义

        Args:
            code: 错误代码

        Returns:
            错误代码定义，如果不存在返回 None
        """
        return cls._codes.get(code)

    @classmethod
    def has(cls, code: str) -> bool:
        """
        检查错误代码是否存在

        Args:
            code: 错误代码

        Returns:
            是否存在
        """
        return code in cls._codes

    @classmethod
    def get_by_category(cls, category: str) -> List[ErrorCodeDefinition]:
        """
        按类别获取错误代码

        Args:
            category: 类别名称

        Returns:
            该类别的所有错误代码定义
        """
        return [d for d in cls._codes.values() if d.category == category]

    @classmethod
    def get_all_codes(cls) -> List[str]:
        """
        获取所有错误代码

        Returns:
            所有错误代码列表
        """
        return list(cls._codes.keys())

    @classmethod
    def get_all_definitions(cls) -> List[ErrorCodeDefinition]:
        """
        获取所有错误代码定义

        Returns:
            所有错误代码定义列表
        """
        return list(cls._codes.values())


# ============================================================================
# 预定义错误代码
# ============================================================================

# 类型错误
ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="E001",
        category="类型错误",
        severity="error",
        brief_message="类型不匹配",
        detailed_message=(
            "运算符 '{operator}' 的操作数类型不兼容\n"
            "  期望: {expected}\n"
            "  实际: {actual}"
        ),
        common_causes=["忘记类型转换", "使用了错误的变量", "函数返回类型不匹配"],
        suggestions=[
            {
                "description": "使用类型转换函数",
                "code_example": "整数型 结果 = 字符串转整数(str_var) + 1;",
            },
            {"description": "检查变量类型声明"},
        ],
        documentation_url="/docs/errors/E001.md",
        examples=[
            "整数型 x = 42;",
            "浮点型 y = 3.14;",
            '整数型 z = 字符串转整数("42");',
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="E002",
        category="作用域错误",
        severity="error",
        brief_message="未定义的符号 '{symbol}'",
        detailed_message=(
            "符号 '{symbol}' 在当前作用域中未定义\n" "  行: {line}\n" "  列: {column}"
        ),
        common_causes=["变量名拼写错误", "变量未声明", "变量在另一个作用域中"],
        suggestions=[
            {"description": "检查符号名称是否正确"},
            {"description": "添加变量声明", "code_example": "整数型 {symbol} = 0;"},
        ],
        documentation_url="/docs/errors/E002.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="E003",
        category="声明错误",
        severity="error",
        brief_message="重复声明 '{symbol}'",
        detailed_message=(
            "符号 '{symbol}' 在 {first_location} 首次声明\n"
            "  又在 {second_location} 重复声明"
        ),
        common_causes=[
            "复制粘贴代码时忘记修改变量名",
            "在同一个作用域中声明了同名变量",
        ],
        suggestions=[
            {"description": "使用不同的名称"},
            {"description": "删除重复声明"},
        ],
        documentation_url="/docs/errors/E003.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="E004",
        category="类型错误",
        severity="error",
        brief_message="无效的类型转换",
        detailed_message=(
            "无法将 '{from_type}' 转换为 '{to_type}'\n" "  位置: {location}"
        ),
        common_causes=["类型之间不兼容", "缺少转换函数"],
        suggestions=[{"description": "使用显式类型转换"}],
        documentation_url="/docs/errors/E004.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="E005",
        category="函数错误",
        severity="error",
        brief_message="参数数量不匹配",
        detailed_message=(
            "函数 '{function}' 期望 {expected} 个参数，但提供了 {actual} 个\n"
            "  位置: {location}"
        ),
        common_causes=["忘记传递某些参数", "传递了多余的参数", "函数签名已更改"],
        suggestions=[
            {
                "description": "检查函数定义",
                "code_example": "// 函数签名: {function}({params})",
            }
        ],
        documentation_url="/docs/errors/E005.md",
    )
)

# 警告代码
ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="W001",
        category="未使用警告",
        severity="warning",
        brief_message="变量 '{variable}' 未使用",
        detailed_message=("变量 '{variable}' 已声明但从未使用\n" "  位置: {location}"),
        common_causes=["开发过程中的临时变量", "重构后遗留的变量"],
        suggestions=[
            {"description": "删除未使用的变量"},
            {
                "description": "使用下划线前缀表示有意未使用的变量",
                "code_example": "整数型 _临时 = 0;  // 明确表示不使用",
            },
        ],
        documentation_url="/docs/errors/W001.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="W002",
        category="潜在问题",
        severity="warning",
        brief_message="可能的整数溢出",
        detailed_message=("表达式可能导致整数溢出\n" "  位置: {location}"),
        common_causes=["大数相乘", "累加操作未检查边界"],
        suggestions=[
            {
                "description": "使用更大的整数类型",
                "code_example": "长整型 result = a * b;",
            }
        ],
        documentation_url="/docs/errors/W002.md",
    )
)


# 导出公共API
__all__ = [
    "ErrorCodeDefinition",
    "ErrorCodeRegistry",
]
