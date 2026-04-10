"""
ZHC编译器 - 类型检查器

功能：
- 类型推导
- 类型兼容性检查
- 类型转换检查
- 类型错误报告

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TypeCategory(Enum):
    """类型类别"""

    PRIMITIVE = "primitive"  # 基本类型
    POINTER = "pointer"  # 指针类型
    ARRAY = "array"  # 数组类型
    FUNCTION = "function"  # 函数类型
    STRUCT = "struct"  # 结构体类型
    VOID = "void"  # 空类型
    UNKNOWN = "unknown"  # 未知类型
    COMPLEX = "complex"  # 复数类型
    FIXED_POINT = "fixed_point"  # 定点数类型


@dataclass
class TypeInfo:
    """类型信息"""

    name: str  # 类型名称
    category: TypeCategory  # 类型类别
    size: int = 0  # 类型大小（字节）
    is_const: bool = False  # 是否const
    is_volatile: bool = False  # 是否volatile
    is_signed: bool = True  # 是否有符号（数值类型）
    pointer_depth: int = 0  # 指针深度（0=非指针，1=一级指针）
    array_size: Optional[int] = None  # 数组大小
    base_type: Optional["TypeInfo"] = None  # 基础类型（指针/数组）

    # 函数类型特有属性
    return_type: Optional["TypeInfo"] = None
    param_types: Optional[List["TypeInfo"]] = None

    # 结构体类型特有属性
    members: Optional[Dict[str, "TypeInfo"]] = None

    # 复数类型特有属性
    complex_element_type: Optional[str] = (
        None  # 元素类型: "float", "double", "long double"
    )

    # 定点数类型特有属性
    fixed_point_format: Optional[str] = None  # 定点数格式: "fract", "accum" 等
    fixed_point_total_bits: Optional[int] = None  # 总位宽
    fixed_point_frac_bits: Optional[int] = None  # 小数位

    def __str__(self) -> str:
        """类型字符串表示"""
        if self.category == TypeCategory.VOID:
            return "空型"

        if self.category == TypeCategory.POINTER:
            return f"{self.base_type}指针" if self.base_type else "指针"

        if self.category == TypeCategory.ARRAY:
            size_str = f"[{self.array_size}]" if self.array_size else "[]"
            return (
                f"{self.base_type}{size_str}" if self.base_type else f"数组{size_str}"
            )

        if self.category == TypeCategory.FUNCTION:
            params = ", ".join(str(p) for p in (self.param_types or []))
            return f"函数({params}) -> {self.return_type}"

        if self.category == TypeCategory.COMPLEX:
            return f"{self.complex_element_type or '双精度'}复数型"

        if self.category == TypeCategory.FIXED_POINT:
            return self.name

        return self.name

    def is_numeric(self) -> bool:
        """是否数值类型"""
        return self.category == TypeCategory.PRIMITIVE and self.name in [
            "整数型",
            "短整型",
            "长整型",
            "浮点型",
            "双精度型",
            "字符型",
            "逻辑型",  # Phase 6: 逻辑型参与数值运算
        ]

    def is_integer(self) -> bool:
        """是否整数类型"""
        return self.category == TypeCategory.PRIMITIVE and self.name in [
            "整数型",
            "短整型",
            "长整型",
            "字符型",
        ]

    def is_float(self) -> bool:
        """是否浮点类型"""
        return self.category == TypeCategory.PRIMITIVE and self.name in [
            "浮点型",
            "双精度型",
        ]

    def is_pointer(self) -> bool:
        """是否指针类型"""
        return self.category == TypeCategory.POINTER

    def is_array(self) -> bool:
        """是否数组类型"""
        return self.category == TypeCategory.ARRAY

    def is_function(self) -> bool:
        """是否函数类型"""
        return self.category == TypeCategory.FUNCTION

    def is_void(self) -> bool:
        """是否空类型"""
        return self.category == TypeCategory.VOID

    def is_complex(self) -> bool:
        """是否复数类型"""
        return self.category == TypeCategory.COMPLEX

    def is_fixed_point(self) -> bool:
        """是否定点数类型"""
        return self.category == TypeCategory.FIXED_POINT

    def can_cast_to(self, target: "TypeInfo") -> bool:
        """是否可以转换到目标类型"""
        # 相同类型
        if self.equals(target):
            return True

        # void可以转换为任意指针类型
        if self.is_void() and target.is_pointer():
            return True

        # 数值类型可以相互转换
        if self.is_numeric() and target.is_numeric():
            return True

        # 指针可以转换为void*
        if self.is_pointer() and target.name == "空型指针":
            return True

        # 数组可以转换为指针
        if self.is_array() and target.is_pointer():
            return self.base_type and self.base_type.equals(target.base_type)

        return False

    def equals(self, other: "TypeInfo") -> bool:
        """类型相等判断"""
        if self.category != other.category:
            return False

        if self.name != other.name:
            return False

        if self.is_const != other.is_const:
            return False

        if self.is_volatile != other.is_volatile:
            return False

        if self.category == TypeCategory.POINTER:
            return (
                self.base_type
                and other.base_type
                and self.base_type.equals(other.base_type)
            )

        if self.category == TypeCategory.ARRAY:
            if self.array_size != other.array_size:
                return False
            return (
                self.base_type
                and other.base_type
                and self.base_type.equals(other.base_type)
            )

        return True


class TypeChecker:
    """类型检查器"""

    def __init__(self):
        """初始化类型检查器"""
        self.type_registry: Dict[str, TypeInfo] = {}
        self.errors: List[Tuple[int, str, str]] = []  # (行号, 错误类型, 错误消息)
        self.warnings: List[Tuple[int, str, str]] = []  # (行号, 警告类型, 警告消息)

        # 初始化基本类型
        self._init_builtin_types()

    def _init_builtin_types(self):
        """初始化内置类型"""
        # 整数类型
        self.type_registry["整数型"] = TypeInfo(
            name="整数型", category=TypeCategory.PRIMITIVE, size=4, is_signed=True
        )

        self.type_registry["短整型"] = TypeInfo(
            name="短整型", category=TypeCategory.PRIMITIVE, size=2, is_signed=True
        )

        self.type_registry["长整型"] = TypeInfo(
            name="长整型", category=TypeCategory.PRIMITIVE, size=8, is_signed=True
        )

        # 浮点类型
        self.type_registry["浮点型"] = TypeInfo(
            name="浮点型", category=TypeCategory.PRIMITIVE, size=4
        )

        self.type_registry["双精度型"] = TypeInfo(
            name="双精度型", category=TypeCategory.PRIMITIVE, size=8
        )

        # 字符类型
        self.type_registry["字符型"] = TypeInfo(
            name="字符型", category=TypeCategory.PRIMITIVE, size=1, is_signed=True
        )

        # 空类型
        self.type_registry["空型"] = TypeInfo(
            name="空型", category=TypeCategory.VOID, size=0
        )

        # Phase 6 T1.1: 逻辑型 (_Bool)
        self.type_registry["逻辑型"] = TypeInfo(
            name="逻辑型", category=TypeCategory.PRIMITIVE, size=1, is_signed=False
        )

        # Phase 6 T1.1: 字符串型 (char*)
        self.type_registry["字符串型"] = TypeInfo(
            name="字符串型",
            category=TypeCategory.POINTER,
            size=8,
            is_signed=False,
            base_type=TypeInfo(
                name="字符型", category=TypeCategory.PRIMITIVE, size=1, is_signed=True
            ),
        )

        # Phase 6 T1.1: 空型指针 (void*)
        self.type_registry["空型指针"] = TypeInfo(
            name="空型指针",
            category=TypeCategory.POINTER,
            size=8,
            is_signed=False,
            base_type=TypeInfo(name="空型", category=TypeCategory.VOID, size=0),
        )

        # Phase 6 T1.1: 类型别名兼容
        self.type_registry["双精度浮点型"] = self.type_registry["双精度型"]
        self.type_registry["长整数型"] = self.type_registry["长整型"]
        self.type_registry["短整数型"] = self.type_registry["短整型"]

    def register_type(self, type_info: TypeInfo):
        """注册自定义类型"""
        self.type_registry[type_info.name] = type_info

    def get_type(self, name: str) -> Optional[TypeInfo]:
        """获取类型信息"""
        return self.type_registry.get(name)

    def check_type_decl(
        self, line: int, type_name: str, var_name: str
    ) -> Optional[TypeInfo]:
        """
        检查类型声明

        Args:
            line: 行号
            type_name: 类型名称
            var_name: 变量名称

        Returns:
            类型信息，如果类型无效则返回None
        """
        # 检查类型是否存在
        type_info = self.get_type(type_name)

        if not type_info:
            self.errors.append(
                (line, "未知类型", f"变量 '{var_name}' 使用了未知类型 '{type_name}'")
            )
            return None

        return type_info

    def check_assignment(
        self, line: int, target_type: TypeInfo, value_type: TypeInfo, context: str = ""
    ) -> bool:
        """
        检查赋值类型兼容性

        Args:
            line: 行号
            target_type: 目标类型
            value_type: 值类型
            context: 上下文描述

        Returns:
            是否类型兼容
        """
        # 类型完全匹配
        if target_type.equals(value_type):
            return True

        # 检查隐式转换
        if value_type.can_cast_to(target_type):
            # 可能产生警告
            if value_type.is_numeric() and target_type.is_numeric():
                # 数值类型转换可能丢失精度
                if value_type.size > target_type.size:
                    self.warnings.append(
                        (
                            line,
                            "精度丢失",
                            f"{context}: 从 '{value_type}' 转换到 '{target_type}' 可能丢失精度",
                        )
                    )
                elif value_type.is_float() and target_type.is_integer():
                    self.warnings.append(
                        (
                            line,
                            "浮点转整数",
                            f"{context}: 从浮点类型 '{value_type}' 转换到整数类型 '{target_type}' 会截断小数部分",
                        )
                    )

            return True

        # 类型不兼容
        self.errors.append(
            (
                line,
                "类型不匹配",
                f"{context}: 无法将类型 '{value_type}' 赋值给类型 '{target_type}'",
            )
        )

        return False

    def check_binary_op(
        self, line: int, op: str, left_type: TypeInfo, right_type: TypeInfo
    ) -> Optional[TypeInfo]:
        """
        检查二元运算类型

        Args:
            line: 行号
            op: 运算符
            left_type: 左操作数类型
            right_type: 右操作数类型

        Returns:
            结果类型，如果运算不合法则返回None
        """
        # 算术运算符
        if op in ["+", "-", "*", "/", "%"]:
            # 两个操作数都必须是数值类型
            if not (left_type.is_numeric() and right_type.is_numeric()):
                self.errors.append(
                    (
                        line,
                        "运算类型错误",
                        f"运算符 '{op}' 需要数值类型，但得到 '{left_type}' 和 '{right_type}'",
                    )
                )
                return None

            # 结果类型：取较大的类型
            if left_type.is_float() or right_type.is_float():
                # 结果是浮点类型
                if left_type.name == "双精度型" or right_type.name == "双精度型":
                    return self.get_type("双精度型")
                else:
                    return self.get_type("浮点型")
            else:
                # 结果是整数类型
                if left_type.name == "长整型" or right_type.name == "长整型":
                    return self.get_type("长整型")
                else:
                    return self.get_type("整数型")

        # 比较运算符
        elif op in ["==", "!=", "<", ">", "<=", ">="]:
            # 可以比较数值或指针
            if left_type.is_numeric() and right_type.is_numeric():
                return self.get_type("整数型")

            if left_type.is_pointer() and right_type.is_pointer():
                if left_type.base_type and right_type.base_type:
                    if left_type.base_type.equals(right_type.base_type):
                        return self.get_type("整数型")
                    else:
                        self.warnings.append(
                            (
                                line,
                                "指针类型不匹配",
                                f"比较不同类型的指针 '{left_type}' 和 '{right_type}'",
                            )
                        )
                        return self.get_type("整数型")

            self.errors.append(
                (line, "比较类型错误", f"无法比较类型 '{left_type}' 和 '{right_type}'")
            )
            return None

        # 逻辑运算符
        elif op in ["&&", "||"]:
            # 操作数应该是整数或指针类型
            if not (left_type.is_integer() or left_type.is_pointer()):
                self.errors.append(
                    (
                        line,
                        "逻辑运算类型错误",
                        f"逻辑运算符 '{op}' 需要整数或指针类型，但得到 '{left_type}'",
                    )
                )
                return None

            if not (right_type.is_integer() or right_type.is_pointer()):
                self.errors.append(
                    (
                        line,
                        "逻辑运算类型错误",
                        f"逻辑运算符 '{op}' 需要整数或指针类型，但得到 '{right_type}'",
                    )
                )
                return None

            return self.get_type("整数型")

        # 位运算符
        elif op in ["&", "|", "^", "<<", ">>"]:
            # 操作数必须是整数类型
            if not (left_type.is_integer() and right_type.is_integer()):
                self.errors.append(
                    (
                        line,
                        "位运算类型错误",
                        f"位运算符 '{op}' 需要整数类型，但得到 '{left_type}' 和 '{right_type}'",
                    )
                )
                return None

            return left_type

        # 未知运算符
        else:
            self.errors.append((line, "未知运算符", f"未知运算符 '{op}'"))
            return None

    def check_unary_op(
        self, line: int, op: str, operand_type: TypeInfo
    ) -> Optional[TypeInfo]:
        """
        检查一元运算类型

        Args:
            line: 行号
            op: 运算符
            operand_type: 操作数类型

        Returns:
            结果类型，如果运算不合法则返回None
        """
        # 算术一元运算
        if op == "-":
            if not operand_type.is_numeric():
                self.errors.append(
                    (
                        line,
                        "运算类型错误",
                        f"一元运算符 '{op}' 需要数值类型，但得到 '{operand_type}'",
                    )
                )
                return None
            return operand_type

        # 逻辑非
        elif op == "!":
            if not (operand_type.is_integer() or operand_type.is_pointer()):
                self.errors.append(
                    (
                        line,
                        "逻辑运算类型错误",
                        f"逻辑非运算需要整数或指针类型，但得到 '{operand_type}'",
                    )
                )
                return None
            return self.get_type("整数型")

        # 按位取反
        elif op == "~":
            if not operand_type.is_integer():
                self.errors.append(
                    (
                        line,
                        "位运算类型错误",
                        f"按位取反需要整数类型，但得到 '{operand_type}'",
                    )
                )
                return None
            return operand_type

        # 取地址
        elif op == "&":
            # 可以对任何左值取地址
            ptr_type = TypeInfo(
                name=f"{operand_type}指针",
                category=TypeCategory.POINTER,
                size=8,
                base_type=operand_type,
            )
            return ptr_type

        # 解引用
        elif op == "*":
            if not operand_type.is_pointer():
                self.errors.append(
                    (
                        line,
                        "解引用错误",
                        f"解引用运算符 '*' 需要指针类型，但得到 '{operand_type}'",
                    )
                )
                return None

            if not operand_type.base_type:
                self.errors.append((line, "解引用错误", "无法解引用空类型指针"))
                return None

            return operand_type.base_type

        # 自增/自减
        elif op in ["++", "--"]:
            if not (operand_type.is_integer() or operand_type.is_pointer()):
                self.errors.append(
                    (
                        line,
                        "运算类型错误",
                        f"运算符 '{op}' 需要整数或指针类型，但得到 '{operand_type}'",
                    )
                )
                return None
            return operand_type

        else:
            self.errors.append((line, "未知运算符", f"未知一元运算符 '{op}'"))
            return None

    def check_function_call(
        self, line: int, func_type: TypeInfo, arg_types: List[TypeInfo]
    ) -> Optional[TypeInfo]:
        """
        检查函数调用类型

        Args:
            line: 行号
            func_type: 函数类型
            arg_types: 参数类型列表

        Returns:
            返回值类型，如果调用不合法则返回None
        """
        if not func_type.is_function():
            self.errors.append(
                (line, "非函数调用", f"'{func_type}' 不是函数类型，无法调用")
            )
            return None

        # 检查参数数量
        if func_type.param_types:
            expected_count = len(func_type.param_types)
            actual_count = len(arg_types)

            if expected_count != actual_count:
                self.errors.append(
                    (
                        line,
                        "参数数量不匹配",
                        f"函数期望 {expected_count} 个参数，但提供了 {actual_count} 个",
                    )
                )
                return None

            # 检查每个参数类型
            for i, (expected, actual) in enumerate(
                zip(func_type.param_types, arg_types)
            ):
                if not self.check_assignment(line, expected, actual, f"参数 {i + 1}"):
                    return None

        return func_type.return_type

    def create_pointer_type(self, base_type: TypeInfo) -> TypeInfo:
        """创建指针类型"""
        ptr_name = f"{base_type.name}指针"

        # 检查是否已存在
        if ptr_name in self.type_registry:
            return self.type_registry[ptr_name]

        # 创建新的指针类型
        ptr_type = TypeInfo(
            name=ptr_name, category=TypeCategory.POINTER, size=8, base_type=base_type
        )

        self.type_registry[ptr_name] = ptr_type
        return ptr_type

    def create_array_type(
        self, base_type: TypeInfo, size: Optional[int] = None
    ) -> TypeInfo:
        """创建数组类型"""
        size_str = str(size) if size else ""
        array_name = f"{base_type.name}[{size_str}]"

        # 检查是否已存在
        if array_name in self.type_registry:
            return self.type_registry[array_name]

        # 创建新的数组类型
        array_type = TypeInfo(
            name=array_name,
            category=TypeCategory.ARRAY,
            size=(base_type.size * size) if size else 0,
            base_type=base_type,
            array_size=size,
        )

        self.type_registry[array_name] = array_type
        return array_type

    def create_function_type(
        self, return_type: TypeInfo, param_types: List[TypeInfo]
    ) -> TypeInfo:
        """创建函数类型"""
        param_str = ", ".join(t.name for t in param_types)
        func_name = f"函数({param_str})->{return_type.name}"

        # 创建函数类型
        func_type = TypeInfo(
            name=func_name,
            category=TypeCategory.FUNCTION,
            size=0,
            return_type=return_type,
            param_types=param_types,
        )

        return func_type

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_errors(self) -> List[Tuple[int, str, str]]:
        """获取所有错误"""
        return self.errors

    def get_warnings(self) -> List[Tuple[int, str, str]]:
        """获取所有警告"""
        return self.warnings

    def clear(self):
        """清空错误和警告"""
        self.errors.clear()
        self.warnings.clear()

    def report(self) -> str:
        """生成类型检查报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("类型检查报告")
        lines.append("=" * 60)

        if self.errors:
            lines.append(f"\n错误 ({len(self.errors)}):")
            for line, error_type, message in self.errors:
                lines.append(f"  行 {line}: [{error_type}] {message}")
        else:
            lines.append("\n✅ 无类型错误")

        if self.warnings:
            lines.append(f"\n警告 ({len(self.warnings)}):")
            for line, warning_type, message in self.warnings:
                lines.append(f"  行 {line}: [{warning_type}] {message}")
        else:
            lines.append("\n✅ 无类型警告")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)
