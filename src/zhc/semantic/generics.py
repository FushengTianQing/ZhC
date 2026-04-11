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
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from enum import Enum

# 类型检查时导入，避免循环依赖
if TYPE_CHECKING:
    from ..parser.ast_nodes import ASTNode
    from ..semantic.generic_instantiator import InstantiationContext
    from ..semantic.generic_parser import GenericFunctionDeclNode, GenericTypeDeclNode


class Variance(Enum):
    """类型参数的变性"""

    COVARIANT = "+"  # 协变：T 可以用 T 的子类型替代
    CONTRAVARIANT = "-"  # 逆变：T 可以用 T 的父类型替代
    INVARIANT = ""  # 不变：必须完全匹配


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
    instantiations: Dict[Tuple[str, ...], "GenericTypeInstance"] = field(
        default_factory=dict
    )
    definition: Optional["ASTNode"] = None  # 类型定义AST节点

    # 类型成员
    members: List["MemberInfo"] = field(default_factory=list)

    def instantiate(self, type_args: List[str]) -> "GenericTypeInstance":
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
                members=self._create_members(type_args),
            )
            self.instantiations[cache_key] = instance

        return self.instantiations[cache_key]

    def _check_constraint_satisfied(
        self, type_name: str, constraint: TypeConstraint
    ) -> bool:
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

    def _create_members(self, type_args: List[str]) -> List["MemberInfo"]:
        """创建实例化后的成员列表"""
        return [
            MemberInfo(
                name=m.name,
                type_name=self._substitute_type(m.type_name, type_args),
                is_static=m.is_static,
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
    members: List["MemberInfo"] = field(default_factory=list)

    @property
    def name(self) -> str:
        """实例化后的类型名"""
        args_str = ", ".join(self.type_args)
        return f"{self.generic_type.name}<{args_str}>"

    def get_member(self, name: str) -> Optional["MemberInfo"]:
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
    params: List["ParamInfo"] = field(default_factory=list)
    return_type: str = "空型"
    body: Optional["ASTNode"] = None  # 函数体AST节点
    instantiations: Dict[Tuple[str, ...], "FunctionInstance"] = field(
        default_factory=dict
    )
    constraints: List[TypeConstraint] = field(default_factory=list)

    def instantiate(self, type_args: List[str]) -> "FunctionInstance":
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
                specialized_return_type=self._substitute_type(
                    self.return_type, type_args
                ),
                specialized_body=self._clone_body(type_args),
            )
            self.instantiations[cache_key] = instance

        return self.instantiations[cache_key]

    def _check_constraint_satisfied(
        self, type_name: str, constraint: TypeConstraint
    ) -> bool:
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

    def _create_params(self, type_args: List[str]) -> List["ParamInfo"]:
        """创建实例化后的参数列表"""
        return [
            ParamInfo(
                name=p.name,
                type_name=self._substitute_type(p.type_name, type_args),
                is_reference=p.is_reference,
                is_const=p.is_const,
            )
            for p in self.params
        ]

    def _substitute_type(self, type_name: str, type_args: List[str]) -> str:
        """替换类型中的类型参数"""
        result = type_name
        for param, arg in zip(self.type_params, type_args):
            result = result.replace(param.name, arg)
        return result

    def _clone_body(self, type_args: List[str]) -> Optional["ASTNode"]:
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
    specialized_body: Optional["ASTNode"]

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
            description="要求类型支持比较运算符",
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
            description="要求类型支持相等性比较",
        )

    @staticmethod
    def addable() -> TypeConstraint:
        """可加约束"""
        return TypeConstraint(
            name="可加",
            required_operators=[
                OperatorSignature(operator="+", return_type="自身"),
            ],
            description="要求类型支持加法运算符",
        )

    @staticmethod
    def printable() -> TypeConstraint:
        """可打印约束"""
        return TypeConstraint(
            name="可打印",
            required_methods=[
                MethodSignature(name="转字符串", return_type="字符串型"),
            ],
            description="要求类型可转换为字符串",
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
            description="要求类型支持基本算术运算",
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
                len(f.instantiations)
                for funcs in self._generic_functions.values()
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
    name: str, type_params: List[TypeParameter], members: List[MemberInfo] = None
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
        name=name, type_params=type_params, members=members or []
    )
    get_generic_manager().register_generic_type(generic_type)
    return generic_type


def create_generic_function(
    name: str,
    type_params: List[TypeParameter],
    params: List[ParamInfo],
    return_type: str,
    body: "ASTNode" = None,
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
        body=body,
    )
    get_generic_manager().register_generic_function(generic_func)
    return generic_func


def create_constraint(
    name: str, operators: List[str] = None, methods: List[str] = None
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
        OperatorSignature(operator=op, return_type="逻辑型") for op in (operators or [])
    ]
    method_sigs = [MethodSignature(name=method) for method in (methods or [])]

    constraint = TypeConstraint(
        name=name, required_operators=op_sigs, required_methods=method_sigs
    )
    get_generic_manager().register_constraint(constraint)
    return constraint


# ===== 泛型解析器（Phase 8 — G.01） =====


class GenericResolver:
    """
    泛型解析器

    负责从 AST 中收集泛型声明并注册到 GenericManager，
    以及在泛型调用点执行实例化。

    作为 AST 泛型节点与 GenericManager/GenericInstantiator 之间的桥梁。
    """

    def __init__(
        self,
        manager: Optional[GenericManager] = None,
    ):
        self.manager = manager or get_generic_manager()
        # 收集到的泛型函数声明: {name: [GenericFunctionDeclNode, ...]}
        self._generic_functions: Dict[str, List[Any]] = {}
        # 收集到的泛型类型声明: {name: GenericTypeDeclNode}
        self._generic_types: Dict[str, Any] = {}
        # 已实例化的函数缓存，避免重复实例化
        self._instantiated_functions: Dict[str, FunctionInstance] = {}

    def resolve(self, node: Any) -> None:
        """
        解析 AST 中的所有泛型声明

        遍历 ProgramNode（或任意 AST 节点），收集：
        - GenericFunctionDeclNode → 注册到 GenericManager
        - GenericTypeDeclNode → 注册到 GenericManager

        Args:
            node: 根 AST 节点（通常是 ProgramNode）
        """
        from ..parser.ast_nodes import (
            ASTNodeType,
        )
        from ..semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
        )

        # 获取节点类型
        nt = getattr(node, "node_type", None)

        # 处理程序根节点
        if nt == ASTNodeType.PROGRAM:
            declarations = getattr(node, "declarations", [])
            for decl in declarations:
                self._resolve_node(decl)

        # 处理单个泛型函数声明
        elif isinstance(node, GenericFunctionDeclNode):
            self._register_function_from_ast(node)

        # 处理单个泛型类型声明
        elif isinstance(node, GenericTypeDeclNode):
            self._register_type_from_ast(node)

        else:
            # 递归处理子节点
            children = node.get_children() if hasattr(node, "get_children") else []
            for child in children:
                self.resolve(child)

    def _resolve_node(self, node: Any) -> None:
        """
        分发单个节点的解析
        """
        from ..parser.ast_nodes import GenericFunctionDeclNode, GenericTypeDeclNode

        if isinstance(node, GenericFunctionDeclNode):
            self._register_function_from_ast(node)
        elif isinstance(node, GenericTypeDeclNode):
            self._register_type_from_ast(node)
        else:
            # 递归进入子节点
            children = node.get_children() if hasattr(node, "get_children") else []
            for child in children:
                self._resolve_node(child)

    def _register_function_from_ast(
        self, node: "GenericFunctionDeclNode"
    ) -> GenericFunction:
        """
        从 AST 节点注册泛型函数到 GenericManager

        利用 GenericFunctionDeclNode.to_generic_method() 方法进行转换。
        """
        # 复用已有的转换方法
        generic_func = node.to_generic_function()

        # 注册到管理器
        self.manager.register_generic_function(generic_func)

        # 缓存原始 AST 节点
        name = node.name
        if name not in self._generic_functions:
            self._generic_functions[name] = []
        self._generic_functions[name].append(node)

        return generic_func

    def _register_type_from_ast(self, node: "GenericTypeDeclNode") -> GenericType:
        """
        从 AST 节点注册泛型类型到 GenericManager

        利用 GenericTypeDeclNode.to_generic_type() 方法进行转换。
        """
        # 复用已有的转换方法
        generic_type = node.to_generic_type()

        # 处理 Where 子句约束（如果存在）
        if node.where_clause and node.where_clause.constraints:
            for type_param_name, constraint_name in node.where_clause.constraints:
                # 查找对应的 TypeParameter 并追加约束
                for tp in generic_type.type_params:
                    if tp.name == type_param_name:
                        constraint = self.manager.get_constraint(constraint_name)
                        if constraint and constraint not in tp.constraints:
                            tp.constraints.append(constraint)
                        break

        # 注册到管理器
        self.manager.register_generic_type(generic_type)

        # 缓存
        self._generic_types[node.name] = node

        return generic_type

    def resolve_type_parameters(
        self, type_param_nodes: List[Any]
    ) -> List[TypeParameter]:
        """
        将 TypeParameterNode 列表转换为 TypeParameter 列表

        Args:
            type_param_nodes: AST 层的 TypeParameterNode 对象列表

        Returns:
            语义层的 TypeParameter 对象列表
        """
        result = []
        for tp_node in type_param_nodes:
            # TypeParameterNode 有 to_type_parameter() 方法
            if hasattr(tp_node, "to_type_parameter"):
                result.append(tp_node.to_type_parameter())
            else:
                # 回退：手动构造
                result.append(
                    TypeParameter(
                        name=getattr(tp_node, "name", "T"),
                        constraints=getattr(tp_node, "constraints", []),
                        default=getattr(tp_node, "default_type", None),
                        variance=getattr(tp_node, "variance", Variance.INVARIANT),
                    )
                )
        return result

    def resolve_constraints(
        self, where_clause: Optional[Any]
    ) -> List[Tuple[str, TypeConstraint]]:
        """
        解析 WhereClauseNode 为 (type_param_name, TypeConstraint) 元组列表

        Args:
           _where_clause: WhereClauseNode 或 None

        Returns:
            [(类型参数名, 约束对象), ...]
        """
        if not where_clause:
            return []

        result = []
        constraints_attr = getattr(where_clause, "constraints", [])
        for item in constraints_attr:
            if isinstance(item, tuple) and len(item) >= 2:
                param_name, constraint_name = item[0], item[1]
                constraint = self.manager.get_constraint(constraint_name)
                if constraint:
                    result.append((param_name, constraint))
                else:
                    # 尝试用预定义约束创建
                    predefined_map = {
                        "可比较": PredefinedConstraints.comparable,
                        "可相等": PredefinedConstraints.equatable,
                        "可加": PredefinedConstraints.addable,
                        "可打印": PredefinedConstraints.printable,
                        "数值型": PredefinedConstraints.numeric,
                    }
                    if constraint_name in predefined_map:
                        c = predefined_map[constraint_name]()
                        result.append((param_name, c))
                    else:
                        # 创建一个占位约束
                        c = TypeConstraint(name=constraint_name)
                        result.append((param_name, c))

        return result

    def instantiate_generic(
        self,
        func_name: str,
        type_args: List[str],
        context: Optional["InstantiationContext"] = None,
    ) -> Optional[FunctionInstance]:
        """
        实例化泛型函数

        给定函数名和类型实参列表，从 GenericManager 获取泛型定义，
        通过 GenericInstantiator 执行实例化。

        Args:
            func_name: 泛型函数名（如 "最大值"）
            type_args: 类型实参列表（如 ["整数型"]）
            context: 可选的实例化上下文

        Returns:
            FunctionInstance 实例，失败返回 None
        """
        from .generic_instantiator import GenericInstantiator

        generic_funcs = self.manager.get_generic_functions(func_name)
        if not generic_funcs:
            return None

        instantiator = GenericInstantiator(self.manager)

        # 选择参数数量匹配的泛型函数
        for generic_func in generic_funcs:
            if len(generic_func.type_params) == len(type_args):
                try:
                    instance = instantiator.instantiate_function(
                        generic_func, type_args, context
                    )

                    # 缓存结果
                    cache_key = f"{func_name}__{'_'.join(type_args)}"
                    self._instantiated_functions[cache_key] = instance

                    return instance
                except (
                    GenericError,
                    TypeParameterCountError,
                    ConstraintViolationError,
                ):
                    # 尝试下一个重载版本
                    continue

        return None

    def instantiate_generic_type(
        self,
        type_name: str,
        type_args: List[str],
        context: Optional["InstantiationContext"] = None,
    ) -> Optional[GenericTypeInstance]:
        """
        实例化泛型类型

        Args:
            type_name: 泛型类型名（如 "列表"）
            type_args: 类型实参列表（如 ["整数型"]）
            context: 可选的实例化上下文

        Returns:
            GenericTypeInstance 实例，失败返回 None
        """
        from .generic_instantiator import GenericInstantiator

        generic_type = self.manager.get_generic_type(type_name)
        if not generic_type:
            return None

        try:
            instantiator = GenericInstantiator(self.manager)
            return instantiator.instantiate_type(generic_type, type_args, context)
        except (GenericError, TypeParameterCountError, ConstraintViolationError):
            return None

    def check_constraints_satisfied(
        self, type_param: TypeParameter, type_arg: str
    ) -> Tuple[bool, List[str]]:
        """
        检查类型实参是否满足类型形参的所有约束

        Args:
            type_param: 类型形参（含约束列表）
            type_arg: 类型实参名称

        Returns:
            (是否全部满足, 未满足的约束描述列表)
        """
        if not type_param.constraints:
            return True, []

        violations = []
        for constraint in type_param.constraints:
            # 使用已有 GenericType._check_constraint_satisfied 的逻辑
            satisfied = self._check_single_constraint(type_arg, constraint)
            if not satisfied:
                violations.append(f"类型 '{type_arg}' 不满足约束 '{constraint.name}'")

        return len(violations) == 0, violations

    def _check_single_constraint(
        self, type_name: str, constraint: TypeConstraint
    ) -> bool:
        """
        检查单个约束是否被满足

        委托给 GenericType 中已实现的约束检查逻辑。
        """
        basic_types = {
            "整数型": {"可比较", "可相等", "可加", "数值型"},
            "浮点型": {"可比较", "可相等", "可加", "数值型"},
            "双精度型": {"可比较", "可相等", "可加", "数值型"},
            "字符型": {"可比较", "可相等"},
            "字符串型": {"可比较", "可相等"},
            "布尔型": {"可相等"},
        }

        if type_name in basic_types:
            return constraint.name in basic_types[type_name]

        # 对于自定义类型，检查运算符和方法
        for op_sig in constraint.required_operators:
            if not self._type_has_operator(type_name, op_sig.operator):
                return False

        for method_sig in constraint.required_methods:
            if not self._type_has_method(type_name, method_sig.name):
                return False

        return True

    @staticmethod
    def _type_has_operator(type_name: str, operator: str) -> bool:
        """检查类型是否有指定运算符"""
        basic_types = {"整数型", "浮点型", "双精度型", "字符型"}
        comparison_ops = {"<", ">", "<=", ">=", "==", "!=", "+"}
        arithmetic_ops = {"-", "*", "/", "%"}

        if type_name in basic_types:
            return operator in comparison_ops or operator in arithmetic_ops

        return False

    @staticmethod
    def _type_has_method(type_name: str, method_name: str) -> bool:
        """检查类型是否有指定方法"""
        # 简化实现：基本类型无方法（除了通过标准库扩展）
        known_methods = {
            "字符串型": {"转字符串", "长度", "子串"},
            "数组": {"长度", "添加", "获取", "包含"},
        }

        methods_for_type = known_methods.get(type_name, set())
        return method_name in methods_for_type

    def get_statistics(self) -> Dict[str, Any]:
        """获取解析器统计信息"""
        total_funcs = sum(len(v) for v in self._generic_functions.values())
        return {
            "resolved_generic_functions": total_funcs,
            "resolved_generic_types": len(self._generic_types),
            "instantiated_functions": len(self._instantiated_functions),
            "function_names": list(self._generic_functions.keys()),
            "type_names": list(self._generic_types.keys()),
        }


# ===== 单态化引擎（G.02 预留接口 — G.01 时仅做基础框架） =====


class Monomorphizer:
    """
    单态化引擎（G.02 完整实现）

    在编译期将泛型函数/类的所有调用点替换为具体特化版本。

    工作流程：
    1. monomorphize() 扫描 AST 收集所有泛型声明和调用点
    2. 对每个调用点做类型推导，确定类型实参
    3. 调用 _generate_specialized_copy() 深拷贝 AST 并替换类型参数
    4. 将特化后的函数/类插入回 AST（使用 mangled name）
    5. 将原始泛型声明替换为特化版本或移除

    核心方法：
    - monomorphize(program) — 主入口
    - monomorphize_function(func_decl, type_args) — 函数单态化
    - monomorphize_class(class_decl, type_args) — 类单态化
    - _generate_specialized_copy(node, substitutions) — AST 深拷贝+替换引擎
    """

    def __init__(
        self,
        manager: Optional[GenericManager] = None,
        resolver: Optional[GenericResolver] = None,
    ):
        self.manager = manager or get_generic_manager()
        self.resolver = resolver or GenericResolver(manager)
        # 特化函数缓存: {mangled_name: specialized FunctionDeclNode}
        self._specialized_functions: Dict[str, Any] = {}
        # 特化类型缓存: {mangled_name: specialized StructDeclNode}
        self._specialized_types: Dict[str, Any] = {}

    def monomorphize(self, program: Any) -> Any:
        """
        主入口：对整个程序执行单态化变换

        扫描 AST 中的所有泛型声明和调用点，生成特化版本并替换。

        Args:
            program: ProgramNode AST 节点

        Returns:
            变换后的 ProgramNode（声明列表可能被修改）
        """
        from ..semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
        )

        # 第一步：预注册所有泛型声明到管理器
        self.resolver.resolve(program)

        # 第二步：收集需要处理的声明和新声明列表
        new_declarations = []
        generic_call_sites = []  # (index, call_node)

        if not hasattr(program, "declarations"):
            return program

        for decl in program.declarations:
            # 处理泛型函数声明 → 保留原声明 + 为已知调用点生成特化版本
            if isinstance(decl, GenericFunctionDeclNode):
                new_declarations.append(decl)
                # 尝试基于约束信息生成常见特化版本
                # （完整调用点收集需要在语义分析之后）

            # 处理泛型类型声明 → 保留原声明
            elif isinstance(decl, GenericTypeDeclNode):
                new_declarations.append(decl)

            else:
                new_declarations.append(decl)

        # 第三步：扫描表达式中的泛型调用点（递归搜索）
        self._collect_generic_calls(new_declarations, generic_call_sites)

        # 第四步：为每个调用点生成特化版本
        for call_info in generic_call_sites:
            self._process_call_site(call_info, new_declarations)

        # 更新程序的声明列表
        program.declarations = new_declarations
        return program

    def _collect_generic_calls(self, nodes: List[Any], results: List[Any]) -> None:
        """递归收集 AST 中的泛型调用点"""
        from ..semantic.generic_parser import GenericTypeNode

        for node in nodes:
            children = getattr(node, "get_children", lambda: [])()
            if children:
                self._collect_generic_calls(children, results)

            # 检测泛型类型引用节点（GenericTypeNode 表示 泛型<实参> 用法）
            if isinstance(node, GenericTypeNode):
                if node.type_args:
                    results.append(("type_ref", node))

    def _process_call_site(self, call_info: tuple, declarations: List[Any]) -> None:
        """处理单个泛型调用点，生成特化版本"""
        call_type, node = call_info
        if call_type == "type_ref":
            base_type = getattr(node, "base_type", "")
            type_args = [
                getattr(arg, "type_name", str(arg))
                for arg in getattr(node, "type_args", [])
            ]
            if base_type and type_args:
                mangled = f"{base_type}__{'_'.join(type_args)}"
                if mangled not in self._specialized_types:
                    # 查找对应的泛型类型定义
                    gen_type = self.manager.get_generic_type(base_type)
                    if gen_type:
                        spec_struct = self._specialize_type(gen_type, type_args)
                        if spec_struct:
                            self._specialized_types[mangled] = spec_struct
                            declarations.append(spec_struct)

    def _specialize_type(self, generic_type: GenericType, type_args: List[str]) -> Any:
        """为泛型类型生成特化的 StructDeclNode"""
        from ..parser.ast_nodes import StructDeclNode

        try:
            generic_type.instantiate(type_args)
        except (TypeParameterCountError, ConstraintViolationError):
            return None

        # 构建类型参数映射
        sub_map = {tp.name: arg for tp, arg in zip(generic_type.type_params, type_args)}

        mangled_name = f"{generic_type.name}__{'_'.join(type_args)}"

        # 使用原始定义中的成员来构建特化版本
        definition = generic_type.definition  # noqa: F841
        if definition:
            from ..semantic.generic_parser import GenericTypeDeclNode

            if isinstance(definition, GenericTypeDeclNode):
                specialized_members = []
                for member in definition.members:
                    copied = self._generate_specialized_copy(member, sub_map)
                    if copied:
                        specialized_members.append(copied)

                return StructDeclNode(
                    name=mangled_name,
                    members=specialized_members,
                )

        return StructDeclNode(name=mangled_name, members=[])

    def monomorphize_function(self, func_decl: Any, type_args: List[str]) -> Any:
        """
        为给定泛型函数和类型参数生成特化副本

        将 GenericFunctionDeclNode 转换为普通的 FunctionDeclNode，
        其中所有类型参数名被替换为实际类型名。

        Args:
            func_decl: GenericFunctionDeclNode
            type_args: 类型实参列表（如 ["整数型"]）

        Returns:
            特化后的普通 FunctionDeclNode（使用 mangled name）
        """
        from ..parser.ast_nodes import FunctionDeclNode
        from ..semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeNode,
        )

        if not isinstance(func_decl, GenericFunctionDeclNode):
            raise TypeError(
                f"期望 GenericFunctionDeclNode，收到 {type(func_decl).__name__}"
            )

        # 构建类型参数映射
        type_param_names = [tp.name for tp in func_decl.type_params]
        if len(type_param_names) != len(type_args):
            raise TypeParameterCountError(
                f"泛型函数 '{func_decl.name}' 需要 "
                f"{len(type_param_names)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )

        sub_map = dict(zip(type_param_names, type_args))

        # 生成修饰后的函数名：最大值__整数型
        mangled_name = f"{func_decl.name}__{'_'.join(type_args)}"

        # 缓存检查
        if mangled_name in self._specialized_functions:
            return self._specialized_functions[mangled_name]

        # 替换返回类型
        specialized_return_type = (
            self._generate_specialized_copy(func_decl.return_type, sub_map)
            if func_decl.return_type
            else TypeNode("空型")
        )

        # 替换参数列表
        specialized_params = []
        for param in func_decl.params:
            copied_param = self._generate_specialized_copy(param, sub_map)
            if copied_param:
                specialized_params.append(copied_param)

        # 替换函数体
        specialized_body = (
            self._generate_specialized_copy(func_decl.body, sub_map)
            if func_decl.body
            else None
        )

        # 创建特化后的普通 FunctionDeclNode
        specialized_func = FunctionDeclNode(
            name=mangled_name,
            return_type=specialized_return_type,
            params=specialized_params,
            body=specialized_body,
        )

        # 缓存结果
        self._specialized_functions[mangled_name] = specialized_func

        return specialized_func

    def monomorphize_class(self, class_decl: Any, type_args: List[str]) -> Any:
        """
        为给定泛型类和类型参数生成特化副本

        将 GenericTypeDeclNode 转换为普通的 StructDeclNode，
        其中所有成员的类型参数名被替换为实际类型名。

        Args:
            class_decl: GenericTypeDeclNode
            type_args: 类型实参列表

        Returns:
            特化后的普通 StructDeclNode
        """
        from ..parser.ast_nodes import StructDeclNode
        from ..semantic.generic_parser import GenericTypeDeclNode

        if not isinstance(class_decl, GenericTypeDeclNode):
            raise TypeError(
                f"期望 GenericTypeDeclNode，收到 {type(class_decl).__name__}"
            )

        # 构建类型参数映射
        type_param_names = [tp.name for tp in class_decl.type_params]
        if len(type_param_names) != len(type_args):
            raise TypeParameterCountError(
                f"泛型类型 '{class_decl.name}' 需要 "
                f"{len(type_param_names)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )

        sub_map = dict(zip(type_param_names, type_args))

        # 生成修饰后的类型名：列表__整数型
        mangled_name = f"{class_decl.name}__{'_'.join(type_args)}"

        # 缓存检查
        if mangled_name in self._specialized_types:
            return self._specialized_types[mangled_name]

        # 替换成员列表
        specialized_members = []
        for member in class_decl.members:
            copied_member = self._generate_specialized_copy(member, sub_map)
            if copied_member:
                specialized_members.append(copied_member)

        # 创建特化后的普通 StructDeclNode
        specialized_struct = StructDeclNode(
            name=mangled_name,
            members=specialized_members,
        )

        # 缓存结果
        self._specialized_types[mangled_name] = specialized_struct

        return specialized_struct

    def _generate_specialized_copy(
        self, node: Any, substitutions: Dict[str, str]
    ) -> Any:
        """
        生成 AST 节点的深拷贝，并将其中所有类型参数替换为实际类型

        这是单态化引擎的核心方法。根据节点类型分发到具体的克隆逻辑。
        支持完整的 ZhC AST 节点集。

        Args:
            node: 要复制的 AST 节点
            substitutions: {类型参数名: 实际类型名} 映射（如 {"T": "整数型"}）

        Returns:
            替换后的新 AST 节点；如果节点为 None 则返回 None
        """
        if node is None:
            return None

        # ===== 导入 AST 节点类型 =====
        from ..parser.ast_nodes import (
            # 声明节点
            FunctionDeclNode,
            StructDeclNode,
            VariableDeclNode,
            ParamDeclNode,
            # 语句节点
            BlockStmtNode,
            ReturnStmtNode,
            ExprStmtNode,
            IfStmtNode,
            WhileStmtNode,
            ForStmtNode,
            DoWhileStmtNode,
            BreakStmtNode,
            ContinueStmtNode,
            TryStmtNode,
            CatchClauseNode,
            FinallyClauseNode,
            ThrowStmtNode,
            # 表达式节点
            BinaryExprNode,
            UnaryExprNode,
            AssignExprNode,
            CallExprNode,
            MemberExprNode,
            ArrayExprNode,
            IdentifierExprNode,
            IntLiteralNode,
            FloatLiteralNode,
            StringLiteralNode,
            CharLiteralNode,
            BoolLiteralNode,
            NullLiteralNode,
            ArrayInitNode,
            StructInitNode,
            TernaryExprNode,
            SizeofExprNode,
            CastExprNode,
            AsExprNode,
            IsExprNode,
            # 类型节点
            PrimitiveTypeNode,
            PointerTypeNode,
            ArrayTypeNode,
            StructTypeNode,
            AutoTypeNode,
            LambdaExprNode,
            # 其他
            SwitchStmtNode,
            CaseStmtNode,
            DefaultStmtNode,
            GotoStmtNode,
            LabelStmtNode,
        )
        from ..semantic.generic_parser import (
            TypeNode,
            TypeParameterNode,
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            GenericTypeNode,
        )

        # ===== 分发到具体的克隆逻辑 =====

        # --- 类型节点 ---

        if isinstance(node, TypeNode):
            new_name = self._substitute_type_name(node.type_name, substitutions)
            new_args = [
                self._generate_specialized_copy(a, substitutions)
                for a in (node.generic_args or [])
            ]
            return TypeNode(
                type_name=new_name,
                is_generic=node.is_generic,
                generic_args=new_args,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, PrimitiveTypeNode):
            new_name = self._substitute_type_name(node.name, substitutions)
            return PrimitiveTypeNode(name=new_name, line=node.line, column=node.column)

        if isinstance(node, PointerTypeNode):
            new_base = self._generate_specialized_copy(node.base_type, substitutions)
            return PointerTypeNode(
                base_type=new_base, line=node.line, column=node.column
            )

        if isinstance(node, ArrayTypeNode):
            new_element = self._generate_specialized_copy(
                node.element_type, substitutions
            )
            new_size = self._generate_specialized_copy(node.size, substitutions)
            return ArrayTypeNode(
                element_type=new_element,
                size=new_size,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, StructTypeNode):
            new_name = self._substitute_type_name(node.name, substitutions)
            return StructTypeNode(name=new_name, line=node.line, column=node.column)

        if isinstance(node, AutoTypeNode):
            new_node = AutoTypeNode(line=node.line, column=node.column)
            if hasattr(node, "resolved_type") and node.resolved_type:
                new_node.resolved_type = self._substitute_type_name(
                    node.resolved_type, substitutions
                )
            return new_node

        # --- 泛型特殊节点 ---

        if isinstance(node, GenericTypeNode):
            new_base = self._substitute_type_name(node.base_type, substitutions)
            new_args = [
                self._generate_specialized_copy(a, substitutions)
                for a in (node.type_args or [])
            ]
            return GenericTypeNode(
                base_type=new_base,
                type_args=new_args,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, TypeParameterNode):
            # 类型参数节点：如果名称在映射中，替换为具体类型节点
            if node.name in substitutions:
                return PrimitiveTypeNode(
                    name=substitutions[node.name],
                    line=node.line,
                    column=node.column,
                )
            # 不在映射中则保留原样
            return TypeParameterNode(
                name=node.name,
                variance=node.variance,
                constraints=list(node.constraints or []),
                default_type=node.default_type,
                line=node.line,
                column=node.column,
            )

        # --- 声明节点 ---

        if isinstance(node, ParamDeclNode):
            new_type = self._generate_specialized_copy(node.param_type, substitutions)
            new_default = self._generate_specialized_copy(
                node.default_value, substitutions
            )
            return ParamDeclNode(
                name=node.name,
                param_type=new_type,
                default_value=new_default,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, VariableDeclNode):
            new_var_type = self._generate_specialized_copy(node.var_type, substitutions)
            new_init = self._generate_specialized_copy(node.init, substitutions)
            return VariableDeclNode(
                name=node.name,
                var_type=new_var_type,
                init=new_init,
                is_const=node.is_const,
                is_auto=node.is_auto,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, FunctionDeclNode):
            new_return = self._generate_specialized_copy(
                node.return_type, substitutions
            )
            new_params = [
                self._generate_specialized_copy(p, substitutions) for p in node.params
            ]
            new_body = self._generate_specialized_copy(node.body, substitutions)
            return FunctionDeclNode(
                name=node.name,
                return_type=new_return,
                params=new_params,
                body=new_body,
                is_auto_return=node.is_auto_return,
                line=node.line,
                column=node.column,
            )

        # 泛型函数声明 → 转换为普通函数声明（用于内联特化场景）
        if isinstance(node, GenericFunctionDeclNode):
            new_return = self._generate_specialized_copy(
                node.return_type, substitutions
            )
            new_params = [
                self._generate_specialized_copy(p, substitutions)
                for p in (node.params or [])
            ]
            new_body = self._generate_specialized_copy(node.body, substitutions)
            new_name = self._substitute_type_name(node.name, substitutions)
            return FunctionDeclNode(
                name=new_name,
                return_type=new_return,
                params=new_params,
                body=new_body,
                is_auto_return=False,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, StructDeclNode):
            new_members = [
                self._generate_specialized_copy(m, substitutions) for m in node.members
            ]
            new_name = self._substitute_type_name(node.name, substitutions)
            return StructDeclNode(
                name=new_name,
                members=new_members,
                base_class=node.base_class,
                is_exception_class=node.is_exception_class,
                line=node.line,
                column=node.column,
            )

        # 泛型类型声明 → 转换为普通结构体声明
        if isinstance(node, GenericTypeDeclNode):
            new_members = [
                self._generate_specialized_copy(m, substitutions)
                for m in (node.members or [])
            ]
            new_name = self._substitute_type_name(node.name, substitutions)
            return StructDeclNode(
                name=new_name,
                members=new_members,
                line=node.line,
                column=node.column,
            )

        # --- 语句节点 ---

        if isinstance(node, BlockStmtNode):
            new_stmts = [
                self._generate_specialized_copy(s, substitutions)
                for s in node.statements
            ]
            return BlockStmtNode(
                statements=new_stmts, line=node.line, column=node.column
            )

        if isinstance(node, ReturnStmtNode):
            new_value = self._generate_specialized_copy(node.value, substitutions)
            return ReturnStmtNode(value=new_value, line=node.line, column=node.column)

        if isinstance(node, ExprStmtNode):
            new_expr = self._generate_specialized_copy(node.expr, substitutions)
            return ExprStmtNode(expr=new_expr, line=node.line, column=node.column)

        if isinstance(node, IfStmtNode):
            new_cond = self._generate_specialized_copy(node.condition, substitutions)
            new_then = self._generate_specialized_copy(node.then_branch, substitutions)
            new_else = self._generate_specialized_copy(node.else_branch, substitutions)
            return IfStmtNode(
                condition=new_cond,
                then_branch=new_then,
                else_branch=new_else,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, WhileStmtNode):
            new_cond = self._generate_specialized_copy(node.condition, substitutions)
            new_body = self._generate_specialized_copy(node.body, substitutions)
            return WhileStmtNode(
                condition=new_cond, body=new_body, line=node.line, column=node.column
            )

        if isinstance(node, ForStmtNode):
            new_init = self._generate_specialized_copy(node.init, substitutions)
            new_cond = self._generate_specialized_copy(node.condition, substitutions)
            new_update = self._generate_specialized_copy(node.update, substitutions)
            new_body = self._generate_specialized_copy(node.body, substitutions)
            return ForStmtNode(
                init=new_init,
                condition=new_cond,
                update=new_update,
                body=new_body,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, DoWhileStmtNode):
            new_body = self._generate_specialized_copy(node.body, substitutions)
            new_cond = self._generate_specialized_copy(node.condition, substitutions)
            return DoWhileStmtNode(
                body=new_body, condition=new_cond, line=node.line, column=node.column
            )

        if isinstance(node, TryStmtNode):
            new_body = self._generate_specialized_copy(node.body, substitutions)
            new_catches = [
                self._generate_specialized_copy(c, substitutions)
                for c in node.catch_clauses
            ]
            new_finally = self._generate_specialized_copy(
                node.finally_clause, substitutions
            )
            return TryStmtNode(
                body=new_body,
                catch_clauses=new_catches,
                finally_clause=new_finally,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, CatchClauseNode):
            new_body = self._generate_specialized_copy(node.body, substitutions)
            return CatchClauseNode(
                exception_type=node.exception_type,
                variable_name=node.variable_name,
                body=new_body,
                is_default=node.is_default,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, FinallyClauseNode):
            new_body = self._generate_specialized_copy(node.body, substitutions)
            return FinallyClauseNode(body=new_body, line=node.line, column=node.column)

        if isinstance(node, ThrowStmtNode):
            new_exc = self._generate_specialized_copy(node.exception, substitutions)
            return ThrowStmtNode(
                exception=new_exc,
                message=node.message,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, SwitchStmtNode):
            new_expr = self._generate_specialized_copy(node.expr, substitutions)
            new_cases = [
                self._generate_specialized_copy(c, substitutions) for c in node.cases
            ]
            return SwitchStmtNode(
                expr=new_expr, cases=new_cases, line=node.line, column=node.column
            )

        if isinstance(node, CaseStmtNode):
            new_val = self._generate_specialized_copy(node.value, substitutions)
            new_end = self._generate_specialized_copy(node.end_value, substitutions)
            new_stmts = [
                self._generate_specialized_copy(s, substitutions)
                for s in node.statements
            ]
            return CaseStmtNode(
                value=new_val,
                statements=new_stmts,
                end_value=new_end,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, DefaultStmtNode):
            new_stmts = [
                self._generate_specialized_copy(s, substitutions)
                for s in node.statements
            ]
            return DefaultStmtNode(
                statements=new_stmts, line=node.line, column=node.column
            )

        # 简单语句（无子节点或仅有位置信息）
        simple_stmt_classes = (
            BreakStmtNode,
            ContinueStmtNode,
        )
        if isinstance(node, simple_stmt_classes):
            return type(node)(line=node.line, column=node.column)

        if isinstance(node, GotoStmtNode):
            return GotoStmtNode(label=node.label, line=node.line, column=node.column)

        if isinstance(node, LabelStmtNode):
            new_stmt = self._generate_specialized_copy(node.statement, substitutions)
            return LabelStmtNode(
                name=node.name, statement=new_stmt, line=node.line, column=node.column
            )

        # --- 表达式节点 ---

        if isinstance(node, BinaryExprNode):
            new_left = self._generate_specialized_copy(node.left, substitutions)
            new_right = self._generate_specialized_copy(node.right, substitutions)
            return BinaryExprNode(
                operator=node.operator,
                left=new_left,
                right=new_right,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, UnaryExprNode):
            new_operand = self._generate_specialized_copy(node.operand, substitutions)
            return UnaryExprNode(
                operator=node.operator,
                operand=new_operand,
                is_prefix=node.is_prefix,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, AssignExprNode):
            new_target = self._generate_specialized_copy(node.target, substitutions)
            new_value = self._generate_specialized_copy(node.value, substitutions)
            return AssignExprNode(
                target=new_target,
                value=new_value,
                operator=node.operator,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, CallExprNode):
            new_callee = self._generate_specialized_copy(node.callee, substitutions)
            new_args = [
                self._generate_specialized_copy(a, substitutions) for a in node.args
            ]
            return CallExprNode(
                callee=new_callee, args=new_args, line=node.line, column=node.column
            )

        if isinstance(node, MemberExprNode):
            new_obj = self._generate_specialized_copy(node.obj, substitutions)
            return MemberExprNode(
                obj=new_obj, member=node.member, line=node.line, column=node.column
            )

        if isinstance(node, ArrayExprNode):
            new_array = self._generate_specialized_copy(node.array, substitutions)
            new_index = self._generate_specialized_copy(node.index, substitutions)
            return ArrayExprNode(
                array=new_array, index=new_index, line=node.line, column=node.column
            )

        if isinstance(node, TernaryExprNode):
            new_cond = self._generate_specialized_copy(node.condition, substitutions)
            new_then = self._generate_specialized_copy(node.then_expr, substitutions)
            new_else = self._generate_specialized_copy(node.else_expr, substitutions)
            return TernaryExprNode(
                condition=new_cond,
                then_expr=new_then,
                else_expr=new_else,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, CastExprNode):
            new_cast_type = self._generate_specialized_copy(
                node.cast_type, substitutions
            )
            new_expr = self._generate_specialized_copy(node.expr, substitutions)
            return CastExprNode(
                cast_type=new_cast_type,
                expr=new_expr,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, AsExprNode):
            new_expr = self._generate_specialized_copy(node.expr, substitutions)
            new_target = self._generate_specialized_copy(
                node.target_type, substitutions
            )
            return AsExprNode(
                expr=new_expr,
                target_type=new_target,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, IsExprNode):
            new_expr = self._generate_specialized_copy(node.expr, substitutions)
            new_target = self._generate_specialized_copy(
                node.target_type, substitutions
            )
            return IsExprNode(
                expr=new_expr,
                target_type=new_target,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, SizeofExprNode):
            new_target = self._generate_specialized_copy(node.target, substitutions)
            return SizeofExprNode(target=new_target, line=node.line, column=node.column)

        if isinstance(node, LambdaExprNode):
            new_params = [
                self._generate_specialized_copy(p, substitutions) for p in node.params
            ]
            new_body = self._generate_specialized_copy(node.body, substitutions)
            new_ret = self._generate_specialized_copy(node.return_type, substitutions)
            return LambdaExprNode(
                params=new_params,
                body=new_body,
                return_type=new_ret,
                line=node.line,
                column=node.column,
            )

        # --- 字面量节点（不可变值，直接复制）---

        if isinstance(node, IdentifierExprNode):
            return IdentifierExprNode(
                name=node.name, line=node.line, column=node.column
            )

        if isinstance(node, IntLiteralNode):
            return IntLiteralNode(value=node.value, line=node.line, column=node.column)

        if isinstance(node, FloatLiteralNode):
            return FloatLiteralNode(
                value=node.value, line=node.line, column=node.column
            )

        if isinstance(node, StringLiteralNode):
            return StringLiteralNode(
                value=node.value, line=node.line, column=node.column
            )

        if isinstance(node, CharLiteralNode):
            return CharLiteralNode(value=node.value, line=node.line, column=node.column)

        if isinstance(node, BoolLiteralNode):
            return BoolLiteralNode(value=node.value, line=node.line, column=node.column)

        if isinstance(node, NullLiteralNode):
            return NullLiteralNode(line=node.line, column=node.column)

        if isinstance(node, ArrayInitNode):
            new_elements = [
                self._generate_specialized_copy(e, substitutions) for e in node.elements
            ]
            return ArrayInitNode(
                elements=new_elements, line=node.line, column=node.column
            )

        if isinstance(node, StructInitNode):
            new_values = [
                self._generate_specialized_copy(v, substitutions) for v in node.values
            ]
            return StructInitNode(
                values=new_values,
                field_names=node.field_names,
                line=node.line,
                column=node.column,
            )

        # --- 未知/不支持的节点：尝试通用处理 ---
        # 尝试通过 get_children() 递归处理子节点
        if hasattr(node, "get_children"):
            children = node.get_children()
            if children:
                # 有子节点但无法识别类型——返回原节点
                # （避免数据丢失，但不执行替换）
                pass
            return node

        # 完全未知的节点，原样返回
        return node

    @staticmethod
    def _substitute_type_name(type_name: str, substitutions: Dict[str, str]) -> str:
        """
        在类型名字符串中替换类型参数

        支持简单名称替换（如 "T" → "整数型"）和复合类型中的替换
        （如 "T[]" → "整数型[]", "(T, V)" → "(字符串型, 整数型)"）

        Args:
            type_name: 原始类型名
            substitutions: 类型参数映射

        Returns:
            替换后的类型名
        """
        result = type_name
        # 按键长度降序排列，确保长键优先匹配（如 "Key" 先于 "K"）
        sorted_keys = sorted(substitutions.keys(), key=len, reverse=True)
        for param_name in sorted_keys:
            result = result.replace(param_name, substitutions[param_name])
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取单态化统计信息"""
        return {
            "specialized_functions": len(self._specialized_functions),
            "specialized_types": len(self._specialized_types),
            "function_cache_keys": list(self._specialized_functions.keys()),
            "type_cache_keys": list(self._specialized_types.keys()),
            "resolver_stats": self.resolver.get_statistics(),
        }


def get_generic_resolver() -> GenericResolver:
    """获取泛型解析器实例"""
    return GenericResolver()


def get_monomorphizer() -> Monomorphizer:
    """获取单态化引擎实例"""
    return Monomorphizer()


# ===== 泛型增强特性（G.08） =====


# ---------------------------------------------------------------
# G.08a: 变性检查 (Variance Checking)
# ---------------------------------------------------------------


class VarianceChecker:
    """
    变性检查器

    验证泛型类型赋值时类型参数的变性是否合法。

    核心规则：
    - 协变 (+): 只允许子类型替换（如 列表<猫> → 列表<动物>）
    - 逆变 (-): 只允许父类型替换（如 比较器<动物> → 比较器<猫>）
    - 不变 (): 必须精确匹配

    使用场景：
    - 泛型类型之间的赋值合法性检查
    - 函数参数传递时的变性验证
    - 重载决议中的变性约束

    示例：
        checker = VarianceChecker()
        checker.check_assignment(
            source_type="列表<猫>",
            target_type="列表<动物>",
            type_params=[TypeParameter("T", variance=Variance.COVARIANT)]
        )
        # 返回 True：列表是协变的，猫是动物的子类型
    """

    # 简化的类型层次关系（实际实现应从类型系统查询）
    _subtype_map: Dict[str, set] = {}

    def __init__(self, subtype_map: Optional[Dict[str, set]] = None):
        """
        Args:
            subtype_map: 类型子类型映射 {父类型: {子类型集合}}
                          默认使用内置基础类型关系
        """
        self._subtype_map = subtype_map or self._default_subtype_map()

    @staticmethod
    def _default_subtype_map() -> Dict[str, set]:
        """默认的类型继承关系"""
        return {
            "数值型": {
                "整数型",
                "浮点型",
                "双精度型",
                "字符型",
                "长整型",
                "短整型",
                "字节型",
            },
            "整数型": {"长整型", "短整型", "字节型"},
            "浮点型": {"双精度型"},
            "可比较": {"整数型", "浮点型", "字符型", "字符串型"},
            "对象": {"字符串型", "数组"},
        }

    def check_assignment(
        self,
        source_generic_name: str,
        target_generic_name: str,
        type_args_source: List[str],
        type_args_target: List[str],
        type_params: List["TypeParameter"],
    ) -> Tuple[bool, List[str]]:
        """
        检查泛型类型赋值的变性合法性

        当将一个泛型实例赋值给另一个泛型实例时，
        验证每个类型参数的替换是否符合其变性声明。

        Args:
            source_generic_name: 源泛型的基础名（如 "列表"）
            target_generic_name: 目标泛型的基础名（如 "列表"）
            type_args_source: 源的类型实参列表（如 ["猫"]）
            type_args_target: 目标的类型实参列表（如 ["动物"]）
            type_params: 泛型的类型参数声明（含 variance 信息）

        Returns:
            (是否合法, 违反描述列表)

        Raises:
            VarianceError: 变性违反错误
        """
        if len(type_args_source) != len(type_args_target):
            return False, [
                f"类型参数数量不匹配: "
                f"源有 {len(type_args_source)} 个，目标有 {len(type_args_target)} 个"
            ]

        violations = []

        # 确保每个位置都有对应的类型参数声明
        for i, (src_arg, tgt_arg) in enumerate(zip(type_args_source, type_args_target)):
            if i >= len(type_params):
                continue

            param = type_params[i]
            variance = getattr(param, "variance", Variance.INVARIANT)

            if src_arg == tgt_arg:
                # 完全相同，任何变性都允许
                continue

            is_subtype = self._is_subtype(src_arg, tgt_arg)
            is_supertype = self._is_subtype(tgt_arg, src_arg)

            if variance == Variance.INVARIANT:
                # 不变：必须完全相同
                if src_arg != tgt_arg:
                    violations.append(
                        f"不变类型参数 '{param.name}' 要求精确匹配，"
                        f"但 '{src_arg}' ≠ '{tgt_arg}'"
                    )

            elif variance == Variance.COVARIANT:
                # 协变：只允许子类型→父类型（源是目标的子类型）
                if not is_subtype and src_arg != tgt_arg:
                    violations.append(
                        f"协变类型参数 '{param.name}' 要求源类型是目标类型的子类型，"
                        f"但 '{src_arg}' 不是 '{tgt_arg}' 的子类型"
                    )

            elif variance == Variance.CONTRAVARIANT:
                # 逆变：只允许父类型→子类型（目标是源的子类型）
                if not is_supertype and src_arg != tgt_arg:
                    violations.append(
                        f"逆变类型参数 '{param.name}' 要求目标类型是源类型的子类型，"
                        f"但 '{tgt_arg}' 不是 '{src_arg}' 的子类型"
                    )

        return len(violations) == 0, violations

    def check_function_argument_variance(
        self,
        func_type_params: List["TypeParameter"],
        arg_types: List[str],
        param_types: List[str],
    ) -> Tuple[bool, List[str]]:
        """
        检查函数调用时实参到形参的变性兼容性

        对于泛型函数调用 f<T>(x: T)，当 T 声明为协变时，
        实参可以是形参类型的子类型。

        Args:
            func_type_params: 函数的类型参数声明
            arg_types: 调用点的实参类型列表
            param_types: 函数声明的形参类型列表

        Returns:
            (是否兼容, 违反描述列表)
        """
        violations = []

        # 构建从类型参数名到其索引和变性信息的映射
        tp_info = {}
        for i, tp in enumerate(func_type_params):
            tp_info[tp.name] = (i, getattr(tp, "variance", Variance.INVARIANT))

        # 对每一对实参/形参检查变性
        for arg_type, param_type in zip(arg_types, param_types):
            # 检查形参中引用了哪些类型参数
            for tp_name, (tp_idx, variance) in tp_info.items():
                if tp_name in param_type:
                    # 形参使用了类型参数 tp_name
                    if arg_type == param_type.replace(tp_name, ""):
                        continue

                    is_sub = self._is_subtype(arg_type, param_type.replace(tp_name, ""))
                    is_super = self._is_subtype(
                        param_type.replace(tp_name, ""), arg_type
                    )

                    if variance == Variance.COVARIANT and not is_sub:
                        violations.append(
                            f"协变参数 '{tp_name}': '{arg_type}' 不是 '{param_type}' 的子类型"
                        )
                    elif variance == Variance.CONTRAVARIANT and not is_super:
                        violations.append(
                            f"逆变参数 '{tp_name}': '{arg_type}' 不是 '{param_type}' 的父类型"
                        )
                    elif variance == Variance.INVARIANT and arg_type != param_type:
                        violations.append(
                            f"不变参数 '{tp_name}': '{arg_type}' ≠ '{param_type}'"
                        )

        return len(violations) == 0, violations

    def _is_subtype(self, child: str, parent: str) -> bool:
        """检查 child 是否为 parent 的子类型（含自身）"""
        if child == parent:
            return True

        # 直接子类型
        children = self._subtype_map.get(parent, set())
        if child in children:
            return True

        # 递归检查间接子类型
        for c in children:
            if self._is_subtype(child, c):
                return True

        return False

    def get_variance_description(self, variance: Variance) -> str:
        """获取变性的中文描述"""
        descriptions = {
            Variance.COVARIANT: "协变(+) — 子类型可以替代",
            Variance.CONTRAVARIANT: "逆变(-) — 父类型可以替代",
            Variance.INVARIANT: "不变 — 必须精确匹配",
        }
        return descriptions.get(variance, "未知")

    @classmethod
    def register_subtype(cls, parent: str, child: str) -> None:
        """注册子类型关系（类方法，修改全局默认映射）"""
        if parent not in cls._subtype_map:
            cls._subtype_map[parent] = set()
        cls._subtype_map[parent].add(child)


# ---------------------------------------------------------------
# G.08b: 高阶类型 (Higher-Kinded Types / Type Constructors)
# ---------------------------------------------------------------


class TypeKind(Enum):
    """
    类型种类 — 区分具体类型和高阶类型（类型构造器）

    - CONCRETE: 具体类型，如 整数型、字符串型
    - TYPE_CONSTRUCTOR: 类型构造器，如 列表、映射（需要类型参数才能成为完整类型）
    - HIGHER_KINDED: 高阶类型，接受类型构造器作为参数（如 Monad<M> where M: TypeConstructor）
    """

    CONCRETE = "concrete"  # * — 具体类型
    TYPE_CONSTRUCTOR = "constructor"  # * -> * — 一阶类型构造器
    HIGHER_KINDED = "higher_kinded"  # (* -> *) -> * — 高阶类型（预留）


@dataclass
class TypeInfo:
    """
    类型信息描述符 — 补充 TypeParameter 以支持高阶类型

    与 TypeParameter 配合使用：
    - TypeParameter.name = "T"
    - TypeParameter.kind = TypeKind.TYPE_CONSTRUCTOR
    - 表示 T 必须是一个类型构造器（如 列表、映射），而非具体类型
    """

    kind: TypeKind = TypeKind.CONCRETE
    required_arity: int = 0  # 类型构造器需要的类型参数数量（0 = 具体类型）
    constructor_constraints: List[str] = field(
        default_factory=list
    )  # 对构造器的额外约束

    def accepts_type(
        self, type_name: str, known_constructors: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        检查给定类型是否符合此 TypeInfo 的要求

        Args:
            type_name: 要检查的类型名
            known_constructors: 已知的类型构造器及其所需参数数量

        Returns:
            是否符合
        """
        if self.kind == TypeKind.CONCRETE:
            # 具体类型：任何非构造器名称都接受
            constructors = known_constructors or {}
            return type_name not in constructors or constructors.get(type_name, 0) == 0

        elif self.kind == TypeKind.TYPE_CONSTRUCTOR:
            # 类型构造器：必须是已知构造器且 arity 匹配
            constructors = known_constructors or {}
            arity = constructors.get(type_name, -1)
            if arity < 0:
                return self.required_arity == 0  # 未知类型，按需决定
            return arity == self.required_arity

        elif self.kind == TypeKind.HIGHER_KINDED:
            # 高阶类型：预留支持
            return True

        return True


# 增强 TypeParameter 使其支持 kind 字段（通过 monkey-patch 避免破坏现有代码）
# 注意：TypeParameter 是 dataclass，不能直接添加字段，所以使用 TypeInfo 作为伴随类


# ---------------------------------------------------------------
# G.08c: 默认类型参数支持 (Default Type Parameters)
# ---------------------------------------------------------------


class DefaultTypeResolver:
    """
    默认类型参数解析器

    当泛型实例化时未提供完整的类型实参列表时，
    使用 TypeParameter.default 字段填充缺失的参数。

    使用场景：
    - 泛型函数调用省略部分类型参数：f<整数型>() 代替 f<整数型, 字符串型>()
    - 泛型类型的便捷别名：列表<> 等同于 列表<任意类型>

    示例：
        resolver = DefaultTypeResolver()
        resolved = resolver.resolve_defaults(
            type_params=[TypeParameter("T"), TypeParameter("U", default="整数型")],
            provided_args=["字符串型"]
        )
        # resolved = ["字符串型", "整数型"]
    """

    @staticmethod
    def resolve_defaults(
        type_params: List[TypeParameter],
        provided_args: List[str],
    ) -> Tuple[List[str], List[str]]:
        """
        解析并补全缺失的类型参数

        Args:
            type_params: 泛型声明的所有类型参数
            provided_args: 调用时提供的类型实参（可能少于 type_params 数量）

        Returns:
            (完整类型参数列表, [使用的默认值描述])

        Raises:
            TypeParameterCountError: 提供的参数过多或缺少默认值无法补全
        """
        if len(provided_args) > len(type_params):
            raise TypeParameterCountError(
                f"提供了 {len(provided_args)} 个类型参数，"
                f"但泛型只需要 {len(type_params)} 个"
            )

        result = list(provided_args)
        used_defaults = []

        for i in range(len(result), len(type_params)):
            param = type_params[i]
            if param.default is not None:
                result.append(param.default)
                used_defaults.append(f"{param.name}={param.default}")
            else:
                raise TypeParameterCountError(
                    f"类型参数 '{param.name}' 缺失且无默认值。"
                    f"请显式提供该参数，或在声明中指定默认值"
                )

        return result, used_defaults

    @staticmethod
    def has_sufficient_defaults(
        type_params: List[TypeParameter],
        provided_count: int,
    ) -> bool:
        """检查是否有足够的默认值来补全缺失的参数"""
        if provided_count >= len(type_params):
            return True
        for i in range(provided_count, len(type_params)):
            if type_params[i].default is None:
                return False
        return True


# Monkey-patch GenericType.instantiate 和 GenericFunction.instantiate
# 以支持默认类型参数
_original_gt_instantiate = GenericType.instantiate
_original_gf_instantiate = GenericFunction.instantiate


def _enhanced_instantiate_type(
    self: GenericType, type_args: List[str]
) -> "GenericTypeInstance":
    """增强版 instantiate，支持默认类型参数"""
    try:
        return _original_gt_instantiate(self, type_args)
    except TypeParameterCountError:
        if len(type_args) < len(self.type_params):
            # 尝试用默认值补全
            resolved, defaults_used = DefaultTypeResolver.resolve_defaults(
                self.type_params, type_args
            )
            return _original_gt_instantiate(self, resolved)
        raise


def _enhanced_instantiate_function(
    self: GenericFunction, type_args: List[str]
) -> "FunctionInstance":
    """增强版 instantiate，支持默认类型参数"""
    try:
        return _original_gf_instantiate(self, type_args)
    except TypeParameterCountError:
        if len(type_args) < len(self.type_params):
            # 尝试用默认值补全
            resolved, defaults_used = DefaultTypeResolver.resolve_defaults(
                self.type_params, type_args
            )
            return _original_gf_instantiate(self, resolved)
        raise


# 应用 monkey-patch（启用默认类型参数支持）
GenericType.instantiate = _enhanced_instantiate_type
GenericFunction.instantiate = _enhanced_instantiate_function


# 同样增强 Monomorphizer 的 monomorphize_function/class 以支持默认参数
_original_mono_func = Monomorphizer.monomorphize_function
_original_mono_class = Monomorphizer.monomorphize_class


def _enhanced_monomorphize_function(self, func_decl, type_args):
    """增强版 monomorphize_function，自动补全默认参数"""
    from ..semantic.generic_parser import GenericFunctionDeclNode

    if isinstance(func_decl, GenericFunctionDeclNode):
        if len(type_args) < len(func_decl.type_params):
            params = [tp.to_type_parameter() for tp in func_decl.type_params]
            resolved, _ = DefaultTypeResolver.resolve_defaults(params, type_args)
            type_args = resolved

    return _original_mono_func(self, func_decl, type_args)


def _enhanced_monomorphize_class(self, class_decl, type_args):
    """增强版 monomorphize_class，自动补全默认参数"""
    from ..semantic.generic_parser import GenericTypeDeclNode

    if isinstance(class_decl, GenericTypeDeclNode):
        if len(type_args) < len(class_decl.type_params):
            params = [tp.to_type_parameter() for tp in class_decl.type_params]
            resolved, _ = DefaultTypeResolver.resolve_defaults(params, type_args)
            type_args = resolved

    return _original_mono_class(self, class_decl, type_args)


Monomorphizer.monomorphize_function = _enhanced_monomorphize_function
Monomorphizer.monomorphize_class = _enhanced_monomorphize_class


# ---------------------------------------------------------------
# G.08d: 约束推理 (Constraint Inference)
# ---------------------------------------------------------------


class ConstraintInferrer:
    """
    约束推理器

    从泛型函数体的 AST 自动推导最小必要约束集。

    核心思想：
    分析泛型类型参数 T 在函数体中的使用方式，推断 T 必须满足的最小约束集。
    例如：
    - 如果函数体中有 a + b（T 类型的变量做加法）→ 推导 T 需要 可加 约束
    - 如果函数体中有 a > b（比较操作）→ 推导 T 需要 可比较 约束
    - 如果函数体中有 打印(a) 或 转字符串(a) → 推导 T 需要 可打印 约束

    用途：
    1. 开发者忘记写约束时自动补全警告
    2. IDE 提供约束建议
    3. 编译优化：知道约束后可以做更强的假设

    示例：
        inferrer = ConstraintInferrer()
        constraints = inferrer.infer_constraints_from_body(
            body_node=func_body,
            type_param_names=["T"]
        )
        # 可能返回 [PredefinedConstraints.comparable(), PredefinedConstraints.addable()]
    """

    # 运算符到预定义约束的映射
    _OPERATOR_TO_CONSTRAINT: Dict[str, str] = {
        "+": "可加",
        "-": "数值型",
        "*": "数值型",
        "/": "数值型",
        "%": "数值型",
        "<": "可比较",
        ">": "可比较",
        "<=": "可比较",
        ">=": "可比较",
        "==": "可相等",
        "!=": "可相等",
    }

    # 方法名到约束的映射
    _METHOD_TO_CONSTRAINT: Dict[str, str] = {
        "转字符串": "可打印",
        "打印": "可打印",
        "长度": "可相等",
        "哈希码": "可相等",
    }

    def __init__(
        self,
        predefined: Optional["PredefinedConstraints"] = None,
    ):
        self._predefined = predefined or PredefinedConstraints()

    def infer_constraints_from_body(
        self,
        body: Any,
        type_param_names: List[str],
    ) -> List[TypeConstraint]:
        """
        从函数体 AST 推导类型参数需要的最小约束集

        Args:
            body: 函数体 AST 节点（通常是 BlockStmtNode）
            type_param_names: 要分析的类型参数名列表（如 ["T", "K"]）

        Returns:
            推导出的 TypeConstraint 列表（去重后的最小集）
        """
        if body is None:
            return []

        # 收集所有运算符和方法使用
        operator_usages: Dict[str, Set[str]] = {}  # {type_param: {operators}}
        method_usages: Dict[str, Set[str]] = {}  # {type_param: {methods}}

        self._scan_ast(body, type_param_names, operator_usages, method_usages)

        # 将使用情况转换为约束
        inferred: Dict[str, TypeConstraint] = {}

        for tp_name in type_param_names:
            ops = operator_usages.get(tp_name, set())
            methods = method_usages.get(tp_name, set())

            constraint = self._usages_to_constraint(tp_name, ops, methods)
            if constraint is not None:
                inferred[constraint.name] = constraint

        return list(inferred.values())

    def infer_and_check(
        self,
        body: Any,
        type_params: List[TypeParameter],
    ) -> Tuple[
        List[TypeConstraint],  # 显式声明的约束
        List[TypeConstraint],  # 推导出的约束
        List[str],  # 缺失约束的警告
    ]:
        """
        推导约束并与显式声明的约束对比

        找出开发者遗漏的约束和多余的约束。

        Args:
            body: 函数体 AST
            type_params: 函数声明的类型参数列表（含已声明的约束）

        Returns:
            (显式约束, 推导出的约束, 缺失约束警告列表)
        """
        type_param_names = [tp.name for tp in type_params]

        # 收集显式声明的约束
        explicit_constraints: Dict[str, TypeConstraint] = {}
        for tp in type_params:
            for c in tp.constraints:
                explicit_constraints[c.name] = c

        # 推导约束
        inferred = self.infer_constraints_from_body(body, type_param_names)

        # 对比找出缺失
        warnings = []
        for inferred_c in inferred:
            if inferred_c.name not in explicit_constraints:
                warnings.append(
                    f"类型参数可能需要约束 '{inferred.cname}' 但未声明"
                    if hasattr(inferred_c, "cname")
                    else f"类型参数可能需要约束 '{inferred_c.name}' 但未声明"
                )

        return (
            list(explicit_constraints.values()),
            inferred,
            warnings,
        )

    def _scan_ast(
        self,
        node: Any,
        type_param_names: List[str],
        operator_usages: Dict[str, Set[str]],
        method_usages: Dict[str, Set[str]],
    ) -> None:
        """
        递归扫描 AST，收集类型参数相关的运算符和方法使用
        """
        if node is None:
            return

        from ..parser.ast_nodes import BinaryExprNode, CallExprNode, MemberExprNode

        # 二元表达式：检测运算符使用
        if isinstance(node, BinaryExprNode):
            # 检查左右操作数是否涉及类型参数
            left_params = self._get_involved_type_params(
                getattr(node, "left", None), type_param_names
            )
            right_params = self._get_involved_type_params(
                getattr(node, "right", None), type_param_names
            )
            involved_params = left_params + right_params

            op = node.operator
            if op and involved_params and op in self._OPERATOR_TO_CONSTRAINT:
                for param_name in involved_params:
                    if param_name not in operator_usages:
                        operator_usages[param_name] = set()
                    operator_usages[param_name].add(op)

        # 成员访问：检测方法调用
        elif isinstance(node, MemberExprNode):
            member = getattr(node, "member", "")
            obj = getattr(node, "obj", None)
            if obj and member:
                involved_params = self._get_involved_type_params(obj, type_param_names)
                if involved_params and member in self._METHOD_TO_CONSTRAINT:
                    for param_name in involved_params:
                        if param_name not in method_usages:
                            method_usages[param_name] = set()
                        method_usages[param_name].add(member)

        # 函数调用表达式
        elif isinstance(node, CallExprNode):
            callee = getattr(node, "callee", None)
            if isinstance(callee, MemberExprNode):
                member = getattr(callee, "member", "")
                obj = getattr(callee, "obj", None)
                if obj and member:
                    involved_params = self._get_involved_type_params(
                        obj, type_param_names
                    )
                    if involved_params and member in self._METHOD_TO_CONSTRAINT:
                        for param_name in involved_params:
                            if param_name not in method_usages:
                                method_usages[param_name] = set()
                            method_usages[param_name].add(member)

        # 递归处理子节点
        children = getattr(node, "get_children", lambda: [])()
        for child in children:
            self._scan_ast(child, type_param_names, operator_usages, method_usages)

    def _get_involved_type_params(
        self, node: Any, type_param_names: List[str]
    ) -> List[str]:
        """
        判断一个 AST 节点涉及哪些类型参数

        通过节点中的标识符名称来判断是否引用了类型参数对应的变量。
        这是一个简化实现——真正的实现需要符号表解析来确定变量类型。
        """
        from ..parser.ast_nodes import IdentifierExprNode

        if isinstance(node, IdentifierExprNode):
            name = node.name
            # 如果标识符名恰好与类型参数名一致，认为它引用了该类型
            # （这是简化的启发式方法；完整实现应通过符号表查找）
            if name in type_param_names:
                return [name]

        # 也检查节点的 name 属性
        name_attr = getattr(node, "name", None)
        if name_attr and name_attr in type_param_names:
            return [name_attr]

        return []

    def _usages_to_constraint(
        self,
        type_param: str,
        operators: Set[str],
        methods: Set[str],
    ) -> Optional[TypeConstraint]:
        """
        将收集到的运算符和方法使用转换为具体的约束对象

        策略：找到能覆盖所有使用情况的最小约束集。
        数值型 包含 可比较+可相等+可加 的全部能力，
        所以如果同时有 + 和 < ，直接推荐数值型。
        """
        if not operators and not methods:
            return None

        # 收集所有需要的约束名
        needed_constraints: Set[str] = set()

        for op in operators:
            cname = self._OPERATOR_TO_CONSTRAINT.get(op)
            if cname:
                needed_constraints.add(cname)

        for method in methods:
            cname = self._METHOD_TO_CONSTRAINT.get(method)
            if cname:
                needed_constraints.add(cname)

        if not needed_constraints:
            return None

        # 简化策略：选择覆盖范围最大的约束
        # 数值型 > 可比较 > 可加 > 可相等 > 可打印
        coverage_order = [
            ("数值型", {"数值型", "可比较", "可相等", "可加"}),
            ("可比较", {"可比较", "可相等"}),
            ("可加", {"可加"}),
            ("可相等", {"可相等"}),
            ("可打印", {"可打印"}),
        ]

        best_constraint = None
        best_coverage = set()

        for cname, covers in coverage_order:
            if needed_constraints.issubset(covers) and len(covers) > len(best_coverage):
                best_constraint = cname
                best_coverage = covers

        if best_constraint:
            return self._get_predefined(best_constraint)

        # 回退：返回第一个需要的约束
        first_needed = next(iter(needed_constraints), None)
        if first_needed:
            return self._get_predefined(first_needed)

        return None

    def _get_predefined(self, name: str) -> Optional[TypeConstraint]:
        """获取预定义约束"""
        getters = {
            "可比较": PredefinedConstraints.comparable,
            "可相等": PredefinedConstraints.equatable,
            "可加": PredefinedConstraints.addable,
            "可打印": PredefinedConstraints.printable,
            "数值型": PredefinedConstraints.numeric,
        }
        getter = getters.get(name)
        return getter() if getter else None

    @staticmethod
    def get_required_operators_for_constraint(constraint_name: str) -> List[str]:
        """获取指定约束要求的运算符列表"""
        op_map = {
            "可比较": ["<", ">", "<=", ">=", "==", "!="],
            "可相等": ["==", "!="],
            "可加": ["+"],
            "数值型": ["+", "-", "*", "/"],
            "可打印": [],  # 方法约束
        }
        return op_map.get(constraint_name, [])

    @staticmethod
    def get_required_methods_for_constraint(constraint_name: str) -> List[str]:
        """获取指定约束要求的方法列表"""
        method_map = {
            "可比较": [],
            "可相等": [],
            "可加": [],
            "数值型": [],
            "可打印": ["转字符串"],
        }
        return method_map.get(constraint_name, [])


# ===== G.08 便捷工厂函数 =====


def create_variance_checker(subtype_map=None) -> VarianceChecker:
    """创建变性检查器实例"""
    return VarianceChecker(subtype_map)


def create_constraint_inferrer(predefined=None) -> ConstraintInferrer:
    """创建约束推理器实例"""
    return ConstraintInferrer(predefined)


def resolve_default_type_params(
    type_params: List[TypeParameter], provided_args: List[str]
) -> Tuple[List[str], List[str]]:
    """
    解析默认类型参数的便捷函数

    Args:
        type_params: 类型参数列表
        provided_args: 已提供的类型实参

    Returns:
        (完整参数列表, 使用了哪些默认值)
    """
    return DefaultTypeResolver.resolve_defaults(type_params, provided_args)
