"""
泛型类型系统 - Generic Type System

提供泛型编程支持：
- 泛型类型（Generic Types）
- 泛型函数（Generic Functions）
- 类型约束（Type Constraints）
- 单态化（Monomorphization）

Phase 4 - Stage 2 - Task 11.1

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, TYPE_CHECKING
from enum import Enum

# 类型检查时导入，避免循环依赖
if TYPE_CHECKING:
    from ..parser.ast_nodes import ASTNode
    from .type_checker import TypeInfo


class Variance(Enum):
    """类型参数的变性"""
    COVARIANT = "+"      # 协变：T 可以用 T 的子类型替代
    CONTRAVARIANT = "-"  # 逆变：T 可以用 T 的父类型替代
    INVARIANT = ""       # 不变：必须完全匹配


@dataclass
class TypeConstraint:
    """
    类型约束

    定义对类型参数的限制条件。
    例如：可比较约束要求类型实现 < 和 > 运算符。
    """
    name: str
    required_methods: List[MethodSignature] = field(default_factory=list)
    required_operators: List[OperatorSignature] = field(default_factory=list)
    super_constraints: List[str] = field(default_factory=list)  # 父约束名
    description: str = ""

    def __str__(self) -> str:
        return f"约束 {self.name}"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypeConstraint):
            return False
        return self.name == other.name


@dataclass
class MethodSignature:
    """方法签名"""
    name: str
    param_types: List[str] = field(default_factory=list)  # 类型名列表
    return_type: str = ""

    def __str__(self) -> str:
        params = ", ".join(self.param_types)
        return f"{self.name}({params}) -> {self.return_type}"


@dataclass
class OperatorSignature:
    """运算符签名"""
    operator: str  # 如 "+", "-", "<", ">"
    operand_type: str = "自身"  # 自身 表示类型参数本身
    return_type: str = "逻辑型"

    def __str__(self) -> str:
        return f"运算符 {self.operator}({self.operand_type}) -> {self.return_type}"


@dataclass
class TypeParameter:
    """
    类型参数

    泛型定义中的占位符类型，如 T、K、V 等。
    可以附带约束条件限制可用类型。
    """
    name: str
    constraints: List[TypeConstraint] = field(default_factory=list)
    default: Optional[str] = None  # 默认类型名
    variance: Variance = Variance.INVARIANT

    def __str__(self) -> str:
        if self.constraints:
            constraints_str = ", ".join(c.name for c in self.constraints)
            return f"{self.name}: {constraints_str}"
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypeParameter):
            return False
        return self.name == other.name


@dataclass
class GenericType:
    """
    泛型类型

    支持参数化的类型定义，如 列表<T>、映射<K, V>。
    """
    name: str
    type_params: List[TypeParameter] = field(default_factory=list)
    instantiations: Dict[Tuple[str, ...], 'GenericTypeInstance'] = field(default_factory=dict)
    definition: Optional['ASTNode'] = None  # 类型定义AST节点

    # 类型成员
    members: List['MemberInfo'] = field(default_factory=list)

    def instantiate(self, type_args: List[str]) -> 'GenericTypeInstance':
        """
        实例化泛型类型

        Args:
            type_args: 类型实参列表，如 ["整数型", "字符串型"]

        Returns:
            实例化后的具体类型

        Raises:
            TypeParameterCountError: 类型参数数量不匹配
            ConstraintViolationError: 类型不满足约束
        """
        # 1. 检查参数数量
        if len(type_args) != len(self.type_params):
            raise TypeParameterCountError(
                f"泛型类型 '{self.name}' 需要 {len(self.type_params)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )

        # 2. 检查约束
        for param, arg in zip(self.type_params, type_args):
            if param.constraints:
                for constraint in param.constraints:
                    if not self._check_constraint_satisfied(arg, constraint):
                        raise ConstraintViolationError(
                            f"类型 '{arg}' 不满足约束 '{constraint.name}'"
                        )

        # 3. 返回或创建实例
        cache_key = tuple(type_args)
        if cache_key not in self.instantiations:
            instance = GenericTypeInstance(
                generic_type=self,
                type_args=type_args,
                members=self._create_members(type_args)
            )
            self.instantiations[cache_key] = instance

        return self.instantiations[cache_key]

    def _check_constraint_satisfied(self, type_name: str, constraint: TypeConstraint) -> bool:
        """检查类型是否满足约束"""
        # 简化实现：检查标准类型的约束满足情况
        # 实际实现需要查询类型系统获取类型的运算符/方法信息
        satisfied = True

        for op_sig in constraint.required_operators:
            if not self._has_operator(type_name, op_sig.operator):
                satisfied = False
                break

        for method_sig in constraint.required_methods:
            if not self._has_method(type_name, method_sig.name):
                satisfied = False
                break

        return satisfied

    def _has_operator(self, type_name: str, operator: str) -> bool:
        """检查类型是否有指定运算符"""
        # 基础实现：常见类型都支持常见运算符
        basic_types = {"整数型", "浮点型", "双精度型", "字符型"}
        comparison_ops = {"<", ">", "<=", ">=", "==", "!="}
        arithmetic_ops = {"+", "-", "*", "/", "%"}

        if type_name in basic_types:
            if operator in comparison_ops or operator in arithmetic_ops:
                return True

        return False

    def _has_method(self, type_name: str, method_name: str) -> bool:
        """检查类型是否有指定方法"""
        # 简化实现
        return False

    def _create_members(self, type_args: List[str]) -> List['MemberInfo']:
        """创建实例化后的成员列表"""
        return [
            MemberInfo(
                name=m.name,
                type_name=self._substitute_type(m.type_name, type_args),
                is_static=m.is_static
            )
            for m in self.members
        ]

    def _substitute_type(self, type_name: str, type_args: List[str]) -> str:
        """替换类型中的类型参数"""
        result = type_name
        for param, arg in zip(self.type_params, type_args):
            result = result.replace(param.name, arg)
        return result

    def get_type_param_index(self, name: str) -> int:
        """获取类型参数的索引"""
        for i, param in enumerate(self.type_params):
            if param.name == name:
                return i
        raise ValueError(f"类型参数 '{name}' 不存在")

    def __str__(self) -> str:
        if self.type_params:
            params_str = ", ".join(str(p) for p in self.type_params)
            return f"{self.name}<{params_str}>"
        return self.name


@dataclass
class GenericTypeInstance:
    """
    泛型类型实例

    泛型类型经实例化后的具体类型。
    例如：列表<整数型> 是 列表<T> 的实例。
    """
    generic_type: GenericType
    type_args: List[str]
    members: List['MemberInfo'] = field(default_factory=list)

    @property
    def name(self) -> str:
        """实例化后的类型名"""
        args_str = ", ".join(self.type_args)
        return f"{self.generic_type.name}<{args_str}>"

    def get_member(self, name: str) -> Optional['MemberInfo']:
        """获取成员信息"""
        for member in self.members:
            if member.name == name:
                return member
        return None

    def __str__(self) -> str:
        return self.name


@dataclass
class MemberInfo:
    """成员信息"""
    name: str
    type_name: str
    is_static: bool = False
    is_const: bool = False


@dataclass
class GenericFunction:
    """
    泛型函数

    支持类型参数的函数定义。
    例如：<T> T 最大值(T a, T b)
    """
    name: str
    type_params: List[TypeParameter] = field(default_factory=list)
    params: List['ParamInfo'] = field(default_factory=list)
    return_type: str = "空型"
    body: Optional['ASTNode'] = None  # 函数体AST节点
    instantiations: Dict[Tuple[str, ...], 'FunctionInstance'] = field(default_factory=dict)
    constraints: List[TypeConstraint] = field(default_factory=list)

    def instantiate(self, type_args: List[str]) -> 'FunctionInstance':
        """
        实例化泛型函数

        Args:
            type_args: 类型实参列表

        Returns:
            实例化后的具体函数
        """
        # 1. 检查参数数量
        if len(type_args) != len(self.type_params):
            raise TypeParameterCountError(
                f"泛型函数 '{self.name}' 需要 {len(self.type_params)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )

        # 2. 检查约束
        for param, arg in zip(self.type_params, type_args):
            if param.constraints:
                for constraint in param.constraints:
                    if not self._check_constraint_satisfied(arg, constraint):
                        raise ConstraintViolationError(
                            f"类型 '{arg}' 不满足约束 '{constraint.name}'"
                        )

        # 3. 返回或创建实例
        cache_key = tuple(type_args)
        if cache_key not in self.instantiations:
            instance = FunctionInstance(
                generic_function=self,
                type_args=type_args,
                specialized_params=self._create_params(type_args),
                specialized_return_type=self._substitute_type(self.return_type, type_args),
                specialized_body=self._clone_body(type_args)
            )
            self.instantiations[cache_key] = instance

        return self.instantiations[cache_key]

    def _check_constraint_satisfied(self, type_name: str, constraint: TypeConstraint) -> bool:
        """检查类型是否满足约束"""
        for op_sig in constraint.required_operators:
            if not self._has_operator(type_name, op_sig.operator):
                return False

        for method_sig in constraint.required_methods:
            if not self._has_method(type_name, method_sig.name):
                return False

        return True

    def _has_operator(self, type_name: str, operator: str) -> bool:
        """检查类型是否有指定运算符"""
        basic_types = {"整数型", "浮点型", "双精度型", "字符型"}
        comparison_ops = {"<", ">", "<=", ">=", "==", "!="}
        arithmetic_ops = {"+", "-", "*", "/", "%"}

        if type_name in basic_types:
            if operator in comparison_ops or operator in arithmetic_ops:
                return True

        return False

    def _has_method(self, type_name: str, method_name: str) -> bool:
        """检查类型是否有指定方法"""
        return False

    def _create_params(self, type_args: List[str]) -> List['ParamInfo']:
        """创建实例化后的参数列表"""
        return [
            ParamInfo(
                name=p.name,
                type_name=self._substitute_type(p.type_name, type_args),
                is_reference=p.is_reference,
                is_const=p.is_const
            )
            for p in self.params
        ]

    def _substitute_type(self, type_name: str, type_args: List[str]) -> str:
        """替换类型中的类型参数"""
        result = type_name
        for param, arg in zip(self.type_params, type_args):
            result = result.replace(param.name, arg)
        return result

    def _clone_body(self, type_args: List[str]) -> Optional['ASTNode']:
        """克隆并替换函数体中的类型"""
        # 简化实现：返回原函数体
        # 实际实现需要深拷贝AST并进行类型替换
        return self.body

    def get_mangled_name(self, type_args: List[str]) -> str:
        """生成修饰后的函数名"""
        # 例如: 最大值__整数型
        args_str = "_".join(type_args)
        return f"{self.name}__{args_str}"

    def __str__(self) -> str:
        if self.type_params:
            params_str = ", ".join(str(p) for p in self.type_params)
            return f"{self.name}<{params_str}>({', '.join(p.type_name for p in self.params)}) -> {self.return_type}"
        return f"{self.name}({', '.join(p.type_name for p in self.params)}) -> {self.return_type}"


@dataclass
class ParamInfo:
    """参数信息"""
    name: str
    type_name: str
    is_reference: bool = False
    is_const: bool = False
    default_value: Optional[Any] = None


@dataclass
class FunctionInstance:
    """
    泛型函数实例

    泛型函数经实例化后的具体函数。
    """
    generic_function: GenericFunction
    type_args: List[str]
    specialized_params: List[ParamInfo]
    specialized_return_type: str
    specialized_body: Optional['ASTNode']

    @property
    def name(self) -> str:
        """实例化后的函数名"""
        return self.generic_function.get_mangled_name(self.type_args)

    def __str__(self) -> str:
        params_str = ", ".join(p.type_name for p in self.specialized_params)
        return f"{self.name}({params_str}) -> {self.specialized_return_type}"


# ===== 约束预定义 =====

class PredefinedConstraints:
    """预定义类型约束"""

    @staticmethod
    def comparable() -> TypeConstraint:
        """可比较约束"""
        return TypeConstraint(
            name="可比较",
            required_operators=[
                OperatorSignature(operator="<", return_type="逻辑型"),
                OperatorSignature(operator=">", return_type="逻辑型"),
                OperatorSignature(operator="==", return_type="逻辑型"),
            ],
            description="要求类型支持比较运算符"
        )

    @staticmethod
    def equatable() -> TypeConstraint:
        """可相等约束"""
        return TypeConstraint(
            name="可相等",
            required_operators=[
                OperatorSignature(operator="==", return_type="逻辑型"),
                OperatorSignature(operator="!=", return_type="逻辑型"),
            ],
            description="要求类型支持相等性比较"
        )

    @staticmethod
    def addable() -> TypeConstraint:
        """可加约束"""
        return TypeConstraint(
            name="可加",
            required_operators=[
                OperatorSignature(operator="+", return_type="自身"),
            ],
            description="要求类型支持加法运算符"
        )

    @staticmethod
    def printable() -> TypeConstraint:
        """可打印约束"""
        return TypeConstraint(
            name="可打印",
            required_methods=[
                MethodSignature(name="转字符串", return_type="字符串型"),
            ],
            description="要求类型可转换为字符串"
        )

    @staticmethod
    def numeric() -> TypeConstraint:
        """数值约束"""
        return TypeConstraint(
            name="数值型",
            required_operators=[
                OperatorSignature(operator="+", return_type="自身"),
                OperatorSignature(operator="-", return_type="自身"),
                OperatorSignature(operator="*", return_type="自身"),
                OperatorSignature(operator="/", return_type="自身"),
            ],
            description="要求类型支持基本算术运算"
        )


# ===== 异常定义 =====

class GenericError(Exception):
    """泛型相关错误基类"""
    pass


class TypeParameterCountError(GenericError):
    """类型参数数量错误"""
    pass


class ConstraintViolationError(GenericError):
    """类型约束违反错误"""
    pass


class TypeInferenceError(GenericError):
    """类型推导失败错误"""
    pass


class VarianceError(GenericError):
    """类型变性错误"""
    pass


# ===== 泛型管理器 =====

class GenericManager:
    """
    泛型管理器

    管理所有泛型类型和函数的注册与查找。
    """

    def __init__(self):
        # 泛型类型注册表
        self._generic_types: Dict[str, GenericType] = {}

        # 泛型函数注册表
        self._generic_functions: Dict[str, List[GenericFunction]] = {}

        # 约束注册表
        self._constraints: Dict[str, TypeConstraint] = {}

        # 初始化预定义约束
        self._init_predefined_constraints()

    def _init_predefined_constraints(self) -> None:
        """初始化预定义约束"""
        predefined = PredefinedConstraints()
        self._constraints["可比较"] = predefined.comparable()
        self._constraints["可相等"] = predefined.equatable()
        self._constraints["可加"] = predefined.addable()
        self._constraints["可打印"] = predefined.printable()
        self._constraints["数值型"] = predefined.numeric()

    def register_generic_type(self, generic_type: GenericType) -> None:
        """注册泛型类型"""
        self._generic_types[generic_type.name] = generic_type

    def register_generic_function(self, generic_func: GenericFunction) -> None:
        """注册泛型函数"""
        if generic_func.name not in self._generic_functions:
            self._generic_functions[generic_func.name] = []
        self._generic_functions[generic_func.name].append(generic_func)

    def register_constraint(self, constraint: TypeConstraint) -> None:
        """注册类型约束"""
        self._constraints[constraint.name] = constraint

    def get_generic_type(self, name: str) -> Optional[GenericType]:
        """获取泛型类型"""
        return self._generic_types.get(name)

    def get_generic_functions(self, name: str) -> List[GenericFunction]:
        """获取同名泛型函数列表"""
        return self._generic_functions.get(name, [])

    def get_constraint(self, name: str) -> Optional[TypeConstraint]:
        """获取类型约束"""
        return self._constraints.get(name)

    def is_generic_type(self, name: str) -> bool:
        """检查是否是泛型类型"""
        return name in self._generic_types

    def is_generic_function(self, name: str) -> bool:
        """检查是否是泛型函数"""
        return name in self._generic_functions

    def instantiate_type(
        self, type_name: str, type_args: List[str]
    ) -> GenericTypeInstance:
        """实例化泛型类型"""
        generic_type = self.get_generic_type(type_name)
        if generic_type is None:
            raise GenericError(f"泛型类型 '{type_name}' 未定义")
        return generic_type.instantiate(type_args)

    def instantiate_function(
        self, func_name: str, type_args: List[str]
    ) -> FunctionInstance:
        """实例化泛型函数"""
        generic_funcs = self.get_generic_functions(func_name)
        if not generic_funcs:
            raise GenericError(f"泛型函数 '{func_name}' 未定义")

        # 简化实现：使用第一个匹配的泛型函数
        # 实际实现需要根据参数类型选择最佳匹配
        for generic_func in generic_funcs:
            if len(generic_func.type_params) == len(type_args):
                return generic_func.instantiate(type_args)

        raise TypeParameterCountError(
            f"泛型函数 '{func_name}' 没有匹配 {len(type_args)} 个类型参数的版本"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "generic_types": len(self._generic_types),
            "generic_functions": sum(len(f) for f in self._generic_functions.values()),
            "constraints": len(self._constraints),
            "type_instances": sum(
                len(t.instantiations) for t in self._generic_types.values()
            ),
            "function_instances": sum(
                len(f.instantiations) for funcs in self._generic_functions.values()
                for f in funcs
            ),
        }


# ===== 模块级单例 =====

_generic_manager: Optional[GenericManager] = None


def get_generic_manager() -> GenericManager:
    """获取泛型管理器单例"""
    global _generic_manager
    if _generic_manager is None:
        _generic_manager = GenericManager()
    return _generic_manager


def reset_generic_manager() -> None:
    """重置泛型管理器"""
    global _generic_manager
    _generic_manager = None


# ===== 便捷函数 =====

def create_generic_type(
    name: str,
    type_params: List[TypeParameter],
    members: List[MemberInfo] = None
) -> GenericType:
    """
    创建泛型类型

    Args:
        name: 类型名
        type_params: 类型参数列表
        members: 成员列表

    Returns:
        泛型类型对象
    """
    generic_type = GenericType(
        name=name,
        type_params=type_params,
        members=members or []
    )
    get_generic_manager().register_generic_type(generic_type)
    return generic_type


def create_generic_function(
    name: str,
    type_params: List[TypeParameter],
    params: List[ParamInfo],
    return_type: str,
    body: 'ASTNode' = None
) -> GenericFunction:
    """
    创建泛型函数

    Args:
        name: 函数名
        type_params: 类型参数列表
        params: 参数列表
        return_type: 返回类型
        body: 函数体

    Returns:
        泛型函数对象
    """
    generic_func = GenericFunction(
        name=name,
        type_params=type_params,
        params=params,
        return_type=return_type,
        body=body
    )
    get_generic_manager().register_generic_function(generic_func)
    return generic_func


def create_constraint(
    name: str,
    operators: List[str] = None,
    methods: List[str] = None
) -> TypeConstraint:
    """
    创建类型约束

    Args:
        name: 约束名
        operators: 要求的运算符列表
        methods: 要求的方法列表

    Returns:
        类型约束对象
    """
    op_sigs = [
        OperatorSignature(operator=op, return_type="逻辑型")
        for op in (operators or [])
    ]
    method_sigs = [
        MethodSignature(name=method)
        for method in (methods or [])
    ]

    constraint = TypeConstraint(
        name=name,
        required_operators=op_sigs,
        required_methods=method_sigs
    )
    get_generic_manager().register_constraint(constraint)
    return constraint
