"""
类型推导引擎
Type Inference Engine

实现Hindley-Milner类型推导算法
支持类型变量、类型约束、类型统一等功能

更新: 2026-04-03 统一使用 parser.ast_nodes
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

from ..parser.ast_nodes import (
    ASTNode,
    ASTNodeType,
    BinaryExprNode,
    UnaryExprNode,
    CallExprNode,
    IdentifierExprNode,
    IfStmtNode,
)


class BaseType(Enum):
    """基础类型"""

    INT = "整数型"
    FLOAT = "浮点型"
    STRING = "字符串型"
    BOOL = "布尔型"
    CHAR = "字符型"
    VOID = "空型"
    UNKNOWN = "未知"
    NULL = "空"

    def __str__(self) -> str:
        return self.value


@dataclass
class TypeVariable:
    """
    类型变量

    用于类型推导过程中的临时类型变量
    """

    id: int
    name: Optional[str] = None
    instance: Optional["Type"] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, TypeVariable):
            return self.id == other.id
        return False

    def __str__(self) -> str:
        if self.instance:
            return str(self.instance)
        return f"T{self.id}"


@dataclass
class FunctionType:
    """函数类型"""

    param_types: List["Type"]
    return_type: "Type"

    def __str__(self) -> str:
        params = " × ".join(str(t) for t in self.param_types)
        return f"({params}) → {self.return_type}"


@dataclass
class ArrayType:
    """数组类型"""

    element_type: "Type"
    size: Optional[int] = None

    def __str__(self) -> str:
        if self.size:
            return f"{self.element_type}[{self.size}]"
        return f"{self.element_type}[]"


# 类型定义（可以是基础类型、类型变量、函数类型或数组类型）
Type = Union[BaseType, TypeVariable, FunctionType, ArrayType]


@dataclass
class TypeConstraint:
    """
    类型约束

    表示两个类型应该相等
    """

    type1: Type
    type2: Type
    location: str = ""

    def __str__(self) -> str:
        return f"{self.type1} = {self.type2} @{self.location}"


class TypeEnv:
    """
    类型环境

    管理变量名到类型的映射
    """

    def __init__(self, parent: Optional["TypeEnv"] = None):
        self.bindings: Dict[str, Type] = {}
        self.parent = parent

    def extend(self, name: str, type_: Type) -> "TypeEnv":
        """
        扩展类型环境
        """
        new_env = TypeEnv(self)
        new_env.bindings = {**self.bindings, name: type_}
        return new_env

    def lookup(self, name: str) -> Optional[Type]:
        """
        查找变量类型
        """
        if name in self.bindings:
            return self.bindings[name]

        if self.parent:
            return self.parent.lookup(name)

        return None

    def __str__(self) -> str:
        parts = []
        for name, type_ in self.bindings.items():
            parts.append(f"{name}: {type_}")
        return "{" + ", ".join(parts) + "}"


class TypeInferenceEngine:
    """
    类型推导引擎

    实现基于约束的类型推导算法
    """

    def __init__(self):
        self.type_var_counter = 0
        self.constraints: List[TypeConstraint] = []
        self.substitution: Dict[int, Type] = {}
        self.type_env = TypeEnv()

        # 统计信息
        self.stats = {
            "type_vars_created": 0,
            "constraints_generated": 0,
            "substitutions_applied": 0,
            "nodes_analyzed": 0,
        }

    def fresh_type_var(self) -> TypeVariable:
        """生成新的类型变量"""
        var = TypeVariable(id=self.type_var_counter)
        self.type_var_counter += 1
        self.stats["type_vars_created"] += 1
        return var

    def add_constraint(self, type1: Type, type2: Type, location: str = "") -> None:
        """添加类型约束"""
        constraint = TypeConstraint(type1, type2, location)
        self.constraints.append(constraint)
        self.stats["constraints_generated"] += 1

    def _node_location(self, node: ASTNode) -> str:
        """获取节点的位置描述"""
        return f"{node.line}:{node.column}"

    def infer(self, node: ASTNode, env: Optional[TypeEnv] = None) -> Type:
        """
        推导表达式类型

        Args:
            node: AST节点（来自 parser.ast_nodes）
            env: 类型环境
        """
        if env is None:
            env = self.type_env

        self.stats["nodes_analyzed"] += 1
        nt = node.node_type
        self._node_location(node)

        # 字面量类型推导
        if nt == ASTNodeType.INT_LITERAL:
            return BaseType.INT
        elif nt == ASTNodeType.FLOAT_LITERAL:
            return BaseType.FLOAT
        elif nt == ASTNodeType.STRING_LITERAL:
            return BaseType.STRING
        elif nt == ASTNodeType.CHAR_LITERAL:
            return BaseType.CHAR
        elif nt == ASTNodeType.BOOL_LITERAL:
            return BaseType.BOOL
        elif nt == ASTNodeType.NULL_LITERAL:
            return BaseType.NULL

        # 标识符
        elif nt == ASTNodeType.IDENTIFIER_EXPR:
            return self._infer_identifier(node, env)

        # 二元表达式
        elif nt == ASTNodeType.BINARY_EXPR:
            return self._infer_binary(node, env)

        # 一元表达式
        elif nt == ASTNodeType.UNARY_EXPR:
            return self._infer_unary(node, env)

        # 函数调用
        elif nt == ASTNodeType.CALL_EXPR:
            return self._infer_call(node, env)

        # 赋值表达式
        elif nt == ASTNodeType.ASSIGN_EXPR:
            return self._infer_assign(node, env)

        # 成员访问
        elif nt == ASTNodeType.MEMBER_EXPR:
            return self._infer_member(node, env)

        # 数组访问
        elif nt == ASTNodeType.ARRAY_EXPR:
            return self._infer_array_access(node, env)

        # 如果语句（作为表达式）
        elif nt == ASTNodeType.IF_STMT:
            return self._infer_if(node, env)

        else:
            return self.fresh_type_var()

    def _infer_identifier(self, node: IdentifierExprNode, env: TypeEnv) -> Type:
        """推导标识符类型"""
        type_ = env.lookup(node.name)

        if type_ is None:
            return self.fresh_type_var()

        return type_

    def _infer_binary(self, node: BinaryExprNode, env: TypeEnv) -> Type:
        """推导二元表达式类型"""
        left_type = self.infer(node.left, env)
        right_type = self.infer(node.right, env)
        loc = self._node_location(node)
        operator = node.operator

        if operator in ["+", "-", "*", "/"]:
            self.add_constraint(left_type, right_type, loc)

            if left_type == BaseType.FLOAT or right_type == BaseType.FLOAT:
                return BaseType.FLOAT
            return BaseType.INT

        elif operator in ["<", ">", "<=", ">="]:
            self.add_constraint(left_type, right_type, loc)
            return BaseType.BOOL

        elif operator in ["==", "!="]:
            self.add_constraint(left_type, right_type, loc)
            return BaseType.BOOL

        elif operator in ["并且", "或者"]:
            self.add_constraint(left_type, BaseType.BOOL, loc)
            self.add_constraint(right_type, BaseType.BOOL, loc)
            return BaseType.BOOL

        else:
            return self.fresh_type_var()

    def _infer_unary(self, node: UnaryExprNode, env: TypeEnv) -> Type:
        """推导一元表达式类型"""
        operand_type = self.infer(node.operand, env)
        loc = self._node_location(node)
        operator = node.operator

        if operator == "非":
            self.add_constraint(operand_type, BaseType.BOOL, loc)
            return BaseType.BOOL

        elif operator == "-":
            self.add_constraint(operand_type, BaseType.INT, loc)
            return BaseType.INT

        elif operator == "*":
            return self.fresh_type_var()

        elif operator == "&":
            return self.fresh_type_var()

        else:
            return self.fresh_type_var()

    def _infer_call(self, node: CallExprNode, env: TypeEnv) -> Type:
        """推导调用表达式类型"""
        callee_type = self.infer(node.callee, env)

        param_types = [self.infer(arg, env) for arg in node.args]

        result_type = self.fresh_type_var()

        func_type = FunctionType(param_types, result_type)
        self.add_constraint(callee_type, func_type, self._node_location(node))

        return result_type

    def _infer_assign(self, node: ASTNode, env: TypeEnv) -> Type:
        """推导赋值表达式类型"""
        if hasattr(node, "target"):
            target_type = self.infer(node.target, env)
            value_type = self.infer(node.value, env)
            self.add_constraint(target_type, value_type, self._node_location(node))
            return value_type
        return self.fresh_type_var()

    def _infer_member(self, node: ASTNode, env: TypeEnv) -> Type:
        """推导成员访问类型"""
        self.infer(node.obj, env)
        return self.fresh_type_var()

    def _infer_array_access(self, node: ASTNode, env: TypeEnv) -> Type:
        """推导数组访问类型"""
        self.infer(node.array, env)
        self.add_constraint(
            self.infer(node.index, env), BaseType.INT, self._node_location(node)
        )
        return self.fresh_type_var()

    def _infer_if(self, node: IfStmtNode, env: TypeEnv) -> Type:
        """推导条件表达式类型"""
        cond_type = self.infer(node.condition, env)
        self.add_constraint(cond_type, BaseType.BOOL, self._node_location(node))

        then_type = self.infer(node.then_branch, env)
        else_type = (
            self.infer(node.else_branch, env) if node.else_branch else BaseType.VOID
        )

        self.add_constraint(then_type, else_type, self._node_location(node))

        return then_type

    def unify(self, type1: Type, type2: Type) -> bool:
        """统一两个类型"""
        type1 = self._prune(type1)
        type2 = self._prune(type2)

        if type1 == type2:
            return True

        if isinstance(type1, TypeVariable):
            if self._occurs_in(type1, type2):
                return False
            type1.instance = type2
            self.substitution[type1.id] = type2
            self.stats["substitutions_applied"] += 1
            return True

        if isinstance(type2, TypeVariable):
            if self._occurs_in(type2, type1):
                return False
            type2.instance = type1
            self.substitution[type2.id] = type1
            self.stats["substitutions_applied"] += 1
            return True

        if isinstance(type1, FunctionType) and isinstance(type2, FunctionType):
            if len(type1.param_types) != len(type2.param_types):
                return False
            for p1, p2 in zip(type1.param_types, type2.param_types):
                if not self.unify(p1, p2):
                    return False
            return self.unify(type1.return_type, type2.return_type)

        if isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
            return self.unify(type1.element_type, type2.element_type)

        if isinstance(type1, BaseType) and isinstance(type2, BaseType):
            return type1 == type2

        return False

    def _prune(self, type_: Type) -> Type:
        """规范化类型"""
        if isinstance(type_, TypeVariable) and type_.instance:
            type_.instance = self._prune(type_.instance)
            return type_.instance
        return type_

    def _occurs_in(self, var: TypeVariable, type_: Type) -> bool:
        """检查类型变量是否出现在类型中"""
        type_ = self._prune(type_)

        if isinstance(type_, TypeVariable):
            return var == type_

        if isinstance(type_, FunctionType):
            return any(
                self._occurs_in(var, t) for t in type_.param_types
            ) or self._occurs_in(var, type_.return_type)

        if isinstance(type_, ArrayType):
            return self._occurs_in(var, type_.element_type)

        return False

    def solve_constraints(self) -> bool:
        """求解所有约束"""
        for constraint in self.constraints:
            if not self.unify(constraint.type1, constraint.type2):
                return False
        return True

    def get_type(self, node: ASTNode) -> Type:
        """获取节点的推导类型"""
        if node.inferred_type:
            return node.inferred_type

        inferred_type = self.infer(node)

        if isinstance(inferred_type, TypeVariable):
            return self._prune(inferred_type)

        return inferred_type

    def annotate_ast(self, node: ASTNode) -> None:
        """为AST节点添加类型标注"""
        inferred_type = self.infer(node)
        node.inferred_type = str(inferred_type)

        # 递归标注子节点
        for child in node.get_children():
            self.annotate_ast(child)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "constraints_count": len(self.constraints),
            "substitutions_count": len(self.substitution),
        }

    def print_report(self) -> None:
        """打印推导报告"""
        print("=" * 60)
        print("📊 类型推导报告")
        print("=" * 60)

        print("\n📈 统计:")
        print(f"  创建类型变量: {self.stats['type_vars_created']}")
        print(f"  生成约束: {self.stats['constraints_generated']}")
        print(f"  应用替换: {self.stats['substitutions_applied']}")
        print(f"  分析节点: {self.stats['nodes_analyzed']}")

        if self.constraints:
            print("\n📋 类型约束:")
            for constraint in self.constraints[:10]:
                print(f"  {constraint}")

        if self.substitution:
            print("\n🔄 类型替换:")
            for var_id, type_ in list(self.substitution.items())[:10]:
                print(f"  T{var_id} → {type_}")

        print("=" * 60)
