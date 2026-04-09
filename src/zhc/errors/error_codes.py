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

# 词法错误代码
ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="L001",
        category="词法错误",
        severity="error",
        brief_message="非法字符 '{character}'",
        detailed_message=(
            "在位置发现了无法识别的字符\n"
            "  字符: '{character}'\n"
            "  位置: {location}"
        ),
        common_causes=[
            "输入了非法的特殊字符",
            "复制粘贴时带入了不可见字符",
            "编码问题",
        ],
        suggestions=[
            {"description": "检查是否使用了正确的中文字符"},
            {"description": "检查是否有隐藏的不可见字符"},
            {"description": "确保文件使用 UTF-8 编码"},
        ],
        documentation_url="/docs/errors/L001.md",
        examples=[
            "整数型 x = 1;  // 正确",
            "整数型 y = @;  // 错误：@ 是非法字符",
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="L002",
        category="词法错误",
        severity="error",
        brief_message="字符串未闭合",
        detailed_message=("字符串字面量缺少结束引号\n" "  位置: {location}"),
        common_causes=["忘记添加结束引号", "引号不匹配", "字符串跨多行"],
        suggestions=[
            {"description": "确保字符串以配对的引号结束"},
            {"description": "使用三引号表示多行字符串"},
            {"description": "检查是否混用了不同类型的引号"},
        ],
        documentation_url="/docs/errors/L002.md",
        examples=[
            '字符串型 s = "hello";  // 正确',
            '字符串型 s = "hello;   // 错误：缺少结束引号',
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="L003",
        category="词法错误",
        severity="error",
        brief_message="注释未闭合",
        detailed_message=("块注释缺少结束标记\n" "  位置: {location}"),
        common_causes=["忘记添加 */ 结束注释", "注释嵌套错误"],
        suggestions=[
            {"description": "确保每个 /* 都有对应的 */"},
            {"description": "检查注释是否正确嵌套"},
        ],
        documentation_url="/docs/errors/L003.md",
        examples=[
            "/* 这是一个注释 */  // 正确",
            "/* 这是一个未闭合的注释  // 错误",
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="L004",
        category="词法错误",
        severity="error",
        brief_message="无效的数字格式 '{number}'",
        detailed_message=(
            "数字字面量的格式不正确\n" "  值: '{number}'\n" "  位置: {location}"
        ),
        common_causes=["数字格式错误", "十六进制/二进制前缀使用错误", "小数点位置错误"],
        suggestions=[
            {"description": "检查数字格式是否正确"},
            {"description": "十六进制使用 0x 前缀，二进制使用 0b 前缀"},
        ],
        documentation_url="/docs/errors/L004.md",
        examples=[
            "整数型 x = 42;       // 十进制",
            "整数型 y = 0xFF;     // 十六进制",
            "整数型 z = 0b1010;   // 二进制",
        ],
    )
)

# 语法错误代码
ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="P001",
        category="语法错误",
        severity="error",
        brief_message="缺少 '{expected}'",
        detailed_message=(
            "语法分析器期望但未找到\n"
            "  期望: {expected}\n"
            "  实际: {actual}\n"
            "  位置: {location}"
        ),
        common_causes=["忘记添加标点符号", "语句结构不完整", "括号不匹配"],
        suggestions=[
            {"description": "检查是否缺少必要的标点符号"},
            {"description": "确保所有括号、引号都正确配对"},
        ],
        documentation_url="/docs/errors/P001.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="P002",
        category="语法错误",
        severity="error",
        brief_message="意外的 token '{token}'",
        detailed_message=(
            "语法分析器遇到了意外的 token\n" "  Token: {token}\n" "  位置: {location}"
        ),
        common_causes=["token 顺序错误", "缺少必要的 token", "多余的 token"],
        suggestions=[
            {"description": "检查 token 的顺序是否正确"},
            {"description": "删除多余的 token 或添加缺少的 token"},
        ],
        documentation_url="/docs/errors/P002.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="P003",
        category="语法错误",
        severity="error",
        brief_message="期望类型声明",
        detailed_message=("期望类型声明但未找到\n" "  位置: {location}"),
        common_causes=["变量声明缺少类型", "函数返回类型缺失"],
        suggestions=[
            {"description": "为变量声明添加类型"},
            {"description": "使用 '自动' 关键字进行类型推导"},
        ],
        documentation_url="/docs/errors/P003.md",
        examples=[
            "整数型 x = 10;   // 正确：显式类型",
            "自动 x = 10;     // 正确：自动推导",
        ],
    )
)

# 语义错误代码
ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S001",
        category="语义错误",
        severity="error",
        brief_message="类型不匹配：期望 '{expected}'，实际 '{actual}'",
        detailed_message=(
            "表达式的类型与期望不符\n"
            "  期望类型: {expected}\n"
            "  实际类型: {actual}\n"
            "  位置: {location}"
        ),
        common_causes=["忘记类型转换", "使用了类型不兼容的变量", "函数返回类型不匹配"],
        suggestions=[
            {"description": "使用类型转换函数进行转换"},
            {"description": "检查变量类型是否正确"},
            {"description": "考虑使用 '自动' 关键字"},
        ],
        documentation_url="/docs/errors/S001.md",
        examples=[
            '整数型 x = 字符串转整数("42");  // 正确',
            '整数型 x = "42";  // 错误：需要类型转换',
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S002",
        category="语义错误",
        severity="error",
        brief_message="未定义的变量 '{name}'",
        detailed_message=(
            "使用了未声明的变量\n" "  变量名: {name}\n" "  位置: {location}"
        ),
        common_causes=["变量未声明", "变量名拼写错误", "变量在另一个作用域中"],
        suggestions=[
            {"description": "声明变量后再使用"},
            {"description": "检查变量名拼写是否正确"},
            {"description": "使用 '自动' 关键字简化声明"},
        ],
        documentation_url="/docs/errors/S002.md",
        examples=[
            "整数型 x = 10; 打印(x);  // 正确",
            "打印(y);  // 错误：y 未定义",
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S003",
        category="语义错误",
        severity="error",
        brief_message="未定义的函数 '{name}'",
        detailed_message=(
            "调用了未声明的函数\n" "  函数名: {name}\n" "  位置: {location}"
        ),
        common_causes=["函数未定义", "函数名拼写错误", "忘记引入头文件"],
        suggestions=[
            {"description": "定义函数后再调用"},
            {"description": "检查函数名拼写是否正确"},
            {"description": "确保函数已正确引入"},
        ],
        documentation_url="/docs/errors/S003.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S004",
        category="语义错误",
        severity="error",
        brief_message="重复定义 '{name}'",
        detailed_message=(
            "符号已在其他位置定义\n"
            "  符号名: {name}\n"
            "  首次定义: {first_location}\n"
            "  当前位置: {location}"
        ),
        common_causes=["复制粘贴代码时忘记修改变量名", "在同一个作用域中重复声明"],
        suggestions=[
            {"description": "使用不同的名称"},
            {"description": "删除重复定义"},
        ],
        documentation_url="/docs/errors/S004.md",
        examples=[
            "整数型 x = 1;\n整数型 x = 2;  // 错误：重复定义",
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S005",
        category="语义错误",
        severity="error",
        brief_message="函数 '{name}' 缺少返回语句",
        detailed_message=(
            "非空返回类型的函数必须包含返回语句\n"
            "  函数名: {name}\n"
            "  位置: {location}"
        ),
        common_causes=[
            "忘记添加返回语句",
            "所有代码路径都未返回",
            "返回语句在条件分支中",
        ],
        suggestions=[
            {"description": "添加返回语句"},
            {"description": "如果函数不需要返回值，使用空型返回类型"},
        ],
        documentation_url="/docs/errors/S005.md",
        examples=[
            "整数型 加法(整数型 a, 整数型 b) { 返回 a + b; }  // 正确",
            "整数型 加法(整数型 a, 整数型 b) { a + b; }  // 错误：缺少返回",
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S006",
        category="语义错误",
        severity="error",
        brief_message="参数类型不匹配：函数 '{name}'",
        detailed_message=(
            "提供的参数类型与函数签名不匹配\n"
            "  函数名: {name}\n"
            "  期望: {expected}\n"
            "  实际: {actual}\n"
            "  位置: {location}"
        ),
        common_causes=["传递了错误类型的参数", "参数顺序错误", "函数签名已更改"],
        suggestions=[
            {"description": "检查参数类型是否正确"},
            {"description": "检查参数顺序是否正确"},
        ],
        documentation_url="/docs/errors/S006.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S007",
        category="语义错误",
        severity="error",
        brief_message="数组索引越界",
        detailed_message=(
            "数组索引超出有效范围\n"
            "  数组大小: {size}\n"
            "  访问索引: {index}\n"
            "  位置: {location}"
        ),
        common_causes=["索引计算错误", "循环边界错误", "数组大小理解错误"],
        suggestions=[
            {"description": "确保索引在有效范围内 [0, size-1]"},
            {"description": "使用循环时注意边界条件"},
        ],
        documentation_url="/docs/errors/S007.md",
        examples=[
            "整数型 数组[5]; 数组[0] = 1;  // 正确",
            "整数型 数组[5]; 数组[5] = 1;  // 错误：越界",
        ],
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S008",
        category="语义错误",
        severity="error",
        brief_message="除零错误",
        detailed_message=("检测到除以零的操作\n" "  位置: {location}"),
        common_causes=["除数可能为零", "循环计数错误导致除数为零"],
        suggestions=[
            {"description": "在除法前检查除数是否为零"},
            {"description": "使用条件判断保护除法运算"},
        ],
        documentation_url="/docs/errors/S008.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S009",
        category="语义错误",
        severity="error",
        brief_message="空指针解引用",
        detailed_message=("试图访问空指针指向的数据\n" "  位置: {location}"),
        common_causes=["指针未初始化", "函数返回空指针", "内存分配失败"],
        suggestions=[
            {"description": "在使用指针前检查是否为空"},
            {"description": "确保内存分配成功后再使用"},
        ],
        documentation_url="/docs/errors/S009.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="S010",
        category="语义错误",
        severity="error",
        brief_message="赋值类型不匹配：'{from_type}' 不能赋值给 '{to_type}'",
        detailed_message=(
            "赋值运算符的左右两边类型不兼容\n"
            "  期望: {to_type}\n"
            "  实际: {from_type}\n"
            "  位置: {location}"
        ),
        common_causes=["忘记类型转换", "使用了错误的变量"],
        suggestions=[
            {"description": "使用类型转换"},
            {"description": "确保变量类型正确"},
        ],
        documentation_url="/docs/errors/S010.md",
    )
)

# 代码生成错误代码
ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="C001",
        category="代码生成错误",
        severity="error",
        brief_message="不支持的特性 '{feature}'",
        detailed_message=(
            "目标平台不支持此特性\n"
            "  特性: {feature}\n"
            "  目标: {target}\n"
            "  位置: {location}"
        ),
        common_causes=["使用了目标平台不支持的语法", "平台特定功能在不支持的平台使用"],
        suggestions=[
            {"description": "使用跨平台的替代实现"},
            {"description": "检查目标平台的文档"},
        ],
        documentation_url="/docs/errors/C001.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="C002",
        category="代码生成错误",
        severity="error",
        brief_message="IR 生成失败",
        detailed_message=("中间表示生成过程中发生错误\n" "  位置: {location}"),
        common_causes=["AST 结构错误", "类型系统错误", "内部实现错误"],
        suggestions=[
            {"description": "检查代码是否有语法或语义错误"},
            {"description": "尝试简化代码结构"},
        ],
        documentation_url="/docs/errors/C002.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="C003",
        category="代码生成错误",
        severity="error",
        brief_message="后端编译失败",
        detailed_message=(
            "目标代码生成失败\n"
            "  后端: {backend}\n"
            "  错误: {error}\n"
            "  位置: {location}"
        ),
        common_causes=["目标代码生成错误", "优化失败", "汇编器错误"],
        suggestions=[
            {"description": "检查生成的中间代码是否正确"},
            {"description": "尝试禁用优化"},
        ],
        documentation_url="/docs/errors/C003.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="C004",
        category="代码生成错误",
        severity="error",
        brief_message="链接失败",
        detailed_message=("目标文件链接失败\n" "  错误: {error}"),
        common_causes=["未定义的符号", "重复定义的符号", "库文件缺失"],
        suggestions=[
            {"description": "检查是否链接了所有需要的库"},
            {"description": "确保所有符号都已定义"},
        ],
        documentation_url="/docs/errors/C004.md",
    )
)

ErrorCodeRegistry.register(
    ErrorCodeDefinition(
        code="C005",
        category="代码生成错误",
        severity="error",
        brief_message="文件输出失败",
        detailed_message=(
            "无法写入输出文件\n" "  文件: {filename}\n" "  错误: {error}"
        ),
        common_causes=["磁盘空间不足", "权限问题", "路径不存在"],
        suggestions=[
            {"description": "检查目录是否存在"},
            {"description": "检查磁盘空间和权限"},
        ],
        documentation_url="/docs/errors/C005.md",
    )
)


# 导出公共API
__all__ = [
    "ErrorCodeDefinition",
    "ErrorCodeRegistry",
]
