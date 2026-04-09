#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST节点定义 - Abstract Syntax Tree Nodes
定义所有语法树节点类型

支持增量更新功能：
- node_id: 节点唯一标识，用于diff和缓存
- parent: 父节点引用，用于路径追溯
- get_children(): 获取子节点列表，用于统一遍历
- get_hash(): 计算节点内容哈希，用于增量比较

作者: 阿福
日期: 2026-04-03
更新: 2026-04-03 合并增量AST功能（parent/get_children/get_hash）
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Tuple
from enum import Enum, auto
import hashlib
import uuid


class ASTNodeType(Enum):
    """AST节点类型枚举"""

    # 程序结构
    PROGRAM = auto()  # 程序
    MODULE_DECL = auto()  # 模块声明
    IMPORT_DECL = auto()  # 导入声明

    # 声明
    FUNCTION_DECL = auto()  # 函数声明
    STRUCT_DECL = auto()  # 结构体声明
    VARIABLE_DECL = auto()  # 变量声明
    PARAM_DECL = auto()  # 参数声明
    ENUM_DECL = auto()  # 枚举声明
    UNION_DECL = auto()  # 共用体声明
    TYPEDEF_DECL = auto()  # 别名声明

    # 语句
    BLOCK_STMT = auto()  # 代码块
    IF_STMT = auto()  # 如果语句
    WHILE_STMT = auto()  # 当循环
    FOR_STMT = auto()  # 循环语句
    DO_WHILE_STMT = auto()  # 执行-当循环
    BREAK_STMT = auto()  # 跳出语句
    CONTINUE_STMT = auto()  # 继续语句
    RETURN_STMT = auto()  # 返回语句
    SWITCH_STMT = auto()  # 选择语句
    CASE_STMT = auto()  # 情况语句
    DEFAULT_STMT = auto()  # 默认语句
    EXPR_STMT = auto()  # 表达式语句
    GOTO_STMT = auto()  # 去向语句
    LABEL_STMT = auto()  # 标签语句

    # 表达式
    BINARY_EXPR = auto()  # 二元表达式
    UNARY_EXPR = auto()  # 一元表达式
    ASSIGN_EXPR = auto()  # 赋值表达式
    CALL_EXPR = auto()  # 函数调用
    MEMBER_EXPR = auto()  # 成员访问
    ARRAY_EXPR = auto()  # 数组访问
    IDENTIFIER_EXPR = auto()  # 标识符
    INT_LITERAL = auto()  # 整数字面量
    FLOAT_LITERAL = auto()  # 浮点字面量
    STRING_LITERAL = auto()  # 字符串字面量
    CHAR_LITERAL = auto()  # 字符字面量
    BOOL_LITERAL = auto()  # 布尔字面量
    NULL_LITERAL = auto()  # 空字面量
    ARRAY_INIT = auto()  # 数组初始化
    STRUCT_INIT = auto()  # 结构体初始化
    TERNARY_EXPR = auto()  # 三元表达式 (a ? b : c)
    SIZEOF_EXPR = auto()  # sizeof 表达式
    CAST_EXPR = auto()  # 类型转换表达式

    # 类型
    PRIMITIVE_TYPE = auto()  # 基本类型
    POINTER_TYPE = auto()  # 指针类型
    ARRAY_TYPE = auto()  # 数组类型
    FUNCTION_TYPE = auto()  # 函数类型
    STRUCT_TYPE = auto()  # 结构体类型
    AUTO_TYPE = auto()  # 自动类型（自动推导）


class ASTNode(ABC):
    """AST节点基类

    支持增量更新功能：
    - node_id: 节点唯一标识，用于diff和缓存
    - parent: 父节点引用，用于路径追溯
    - get_children(): 获取子节点列表，用于统一遍历
    - get_hash(): 计算节点内容哈希，用于增量比较
    - end_line, end_column: 结束位置，用于精确错误定位
    """

    def __init__(
        self,
        node_type: ASTNodeType,
        line: int = 0,
        column: int = 0,
        end_line: Optional[int] = None,
        end_column: Optional[int] = None,
    ):
        self.node_type = node_type
        self.line = line
        self.column = column
        self.end_line = end_line  # 结束行号（可选，用于多行错误）
        self.end_column = end_column  # 结束列号（可选，用于多列错误）
        self.node_id: str = uuid.uuid4().hex[:8]  # 节点唯一标识
        self.parent: Optional["ASTNode"] = None  # 父节点引用
        self.attributes: Dict[str, Any] = {}
        # 类型推断结果（由类型推断引擎/语义分析器设置）
        self.inferred_type: Optional[str] = None

    @abstractmethod
    def accept(self, visitor: "ASTVisitor") -> Any:
        """接受访问者"""
        pass

    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """获取属性"""
        return self.attributes.get(key, default)

    def get_children(self) -> List["ASTNode"]:
        """获取所有子节点列表（按定义顺序）

        子类应重写此方法来提供子节点，
        用于增量AST更新、树遍历等通用操作。
        默认返回空列表（叶子节点）。
        """
        return []

    def get_path(self) -> List[str]:
        """获取从根到当前节点的路径（node_id列表）"""
        path = []
        node = self
        while node is not None:
            path.append(node.node_id)
            node = node.parent
        return list(reversed(path))

    def get_hash(self) -> str:
        """计算节点及其子树的内容哈希（MD5）

        用于增量AST更新时快速判断节点是否变化。
        默认实现基于 node_type + 子节点哈希。
        字面量节点等会重写此方法以包含值信息。
        """
        parts = [self.node_type.name]
        for child in self.get_children():
            parts.append(child.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _set_parent(self, child: Optional["ASTNode"]):
        """设置单个子节点的parent引用"""
        if child is not None:
            child.parent = self

    def _set_parent_list(self, children: List["ASTNode"]):
        """设置子节点列表的parent引用"""
        for child in children:
            if child is not None:
                child.parent = self

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于调试、序列化、可视化等）

        子类可以重写此方法以包含更多语义信息。
        """
        result: Dict[str, Any] = {
            "node_type": self.node_type.name,
            "node_id": self.node_id,
            "line": self.line,
            "column": self.column,
        }
        if self.end_line is not None:
            result["end_line"] = self.end_line
        if self.end_column is not None:
            result["end_column"] = self.end_column
        if self.inferred_type is not None:
            result["inferred_type"] = self.inferred_type
        if self.attributes:
            result["attributes"] = self.attributes
        children = self.get_children()
        if children:
            result["children"] = [child.to_dict() for child in children]
        return result

    def get_location_range(self) -> tuple[int, int, Optional[int], Optional[int]]:
        """获取位置范围

        Returns:
            (line, column, end_line, end_column) 元组
        """
        return (self.line, self.column, self.end_line, self.end_column)

    def is_multiline(self) -> bool:
        """判断是否为多行节点"""
        return self.end_line is not None and self.end_line != self.line

    def __repr__(self):
        if self.end_line is not None and self.end_column is not None:
            return f"{self.node_type.name}(line={self.line}:{self.column}-{self.end_line}:{self.end_column})"
        return f"{self.node_type.name}(line={self.line}, col={self.column})"


# ============================================================================
# 程序结构节点
# ============================================================================


class ProgramNode(ASTNode):
    """程序节点"""

    def __init__(self, declarations: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.PROGRAM, line, column)
        self.declarations = declarations
        self._set_parent_list(declarations)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_program(self)

    def get_children(self) -> List["ASTNode"]:
        return self.declarations


class ModuleDeclNode(ASTNode):
    """模块声明节点"""

    def __init__(
        self,
        name: str,
        exports: List[str],
        imports: List[str],
        body: List[ASTNode],
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.MODULE_DECL, line, column)
        self.name = name
        self.exports = exports
        self.imports = imports
        self.body = body
        self._set_parent_list(body)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_module_decl(self)

    def get_children(self) -> List["ASTNode"]:
        return self.body


class ImportDeclNode(ASTNode):
    """导入声明节点"""

    def __init__(
        self,
        module_name: str,
        symbols: Optional[List[str]],
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.IMPORT_DECL, line, column)
        self.module_name = module_name
        self.symbols = symbols  # None表示导入全部

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_import_decl(self)


# ============================================================================
# 声明节点
# ============================================================================


class FunctionDeclNode(ASTNode):
    """函数声明节点"""

    def __init__(
        self,
        name: str,
        return_type: ASTNode,
        params: List[ASTNode],
        body: Optional[ASTNode],
        is_auto_return: bool = False,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.FUNCTION_DECL, line, column)
        self.name = name
        self.return_type = return_type
        self.params = params
        self.body = body
        self.is_auto_return = is_auto_return  # 是否为自动返回类型
        self._set_parent(return_type)
        self._set_parent_list(params)
        self._set_parent(body)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_function_decl(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = [self.return_type] + self.params
        if self.body is not None:
            children.append(self.body)
        return children

    def get_hash(self) -> str:
        parts = [
            self.node_type.name,
            f"name:{self.name}",
            f"auto_return:{self.is_auto_return}",
        ]
        for child in self.get_children():
            parts.append(child.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class StructDeclNode(ASTNode):
    """结构体声明节点"""

    def __init__(
        self, name: str, members: List[ASTNode], line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.STRUCT_DECL, line, column)
        self.name = name
        self.members = members
        self._set_parent_list(members)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_struct_decl(self)

    def get_children(self) -> List["ASTNode"]:
        return self.members

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"name:{self.name}"]
        for child in self.get_children():
            parts.append(child.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class EnumDeclNode(ASTNode):
    """枚举声明节点"""

    def __init__(
        self,
        name: Optional[str],
        values: List[Tuple[str, Optional[ASTNode]]],
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.ENUM_DECL, line, column)
        self.name = name  # 匿名枚举为 None
        self.values = values  # [(名称, 可选值表达式), ...]
        for _, expr in values:
            self._set_parent(expr)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_enum_decl(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = []
        for _, expr in self.values:
            if expr is not None:
                children.append(expr)
        return children

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"name:{self.name}"]
        for name, expr in self.values:
            parts.append(f"{name}")
            if expr is not None:
                parts.append(expr.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class UnionDeclNode(ASTNode):
    """共用体声明节点"""

    def __init__(
        self, name: str, members: List[ASTNode], line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.UNION_DECL, line, column)
        self.name = name
        self.members = members
        self._set_parent_list(members)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_union_decl(self)

    def get_children(self) -> List["ASTNode"]:
        return self.members

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"name:{self.name}"]
        for child in self.get_children():
            parts.append(child.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class TypedefDeclNode(ASTNode):
    """别名声明节点 (typedef)"""

    def __init__(
        self, old_type: ASTNode, new_name: str, line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.TYPEDEF_DECL, line, column)
        self.old_type = old_type
        self.new_name = new_name
        self._set_parent(old_type)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_typedef_decl(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.old_type]

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"new_name:{self.new_name}"]
        parts.append(self.old_type.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class VariableDeclNode(ASTNode):
    """变量声明节点"""

    def __init__(
        self,
        name: str,
        var_type: ASTNode,
        init: Optional[ASTNode],
        is_const: bool = False,
        is_auto: bool = False,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.VARIABLE_DECL, line, column)
        self.name = name
        self.var_type = var_type
        self.init = init
        self.is_const = is_const
        self.is_auto = is_auto  # 是否为自动类型声明
        self._set_parent(var_type)
        self._set_parent(init)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_variable_decl(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = [self.var_type]
        if self.init is not None:
            children.append(self.init)
        return children

    def get_hash(self) -> str:
        parts = [
            self.node_type.name,
            f"name:{self.name}",
            f"const:{self.is_const}",
            f"auto:{self.is_auto}",
        ]
        for child in self.get_children():
            parts.append(child.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class ParamDeclNode(ASTNode):
    """参数声明节点"""

    def __init__(
        self,
        name: str,
        param_type: ASTNode,
        default_value: Optional[ASTNode] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.PARAM_DECL, line, column)
        self.name = name
        self.param_type = param_type
        self.default_value = default_value
        self._set_parent(param_type)
        self._set_parent(default_value)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_param_decl(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = [self.param_type]
        if self.default_value is not None:
            children.append(self.default_value)
        return children

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"name:{self.name}"]
        for child in self.get_children():
            parts.append(child.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


# ============================================================================
# 语句节点
# ============================================================================


class BlockStmtNode(ASTNode):
    """代码块节点"""

    def __init__(self, statements: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.BLOCK_STMT, line, column)
        self.statements = statements
        self._set_parent_list(statements)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_block_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        return self.statements


class IfStmtNode(ASTNode):
    """如果语句节点"""

    def __init__(
        self,
        condition: ASTNode,
        then_branch: ASTNode,
        else_branch: Optional[ASTNode],
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.IF_STMT, line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self._set_parent(condition)
        self._set_parent(then_branch)
        self._set_parent(else_branch)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_if_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = [self.condition, self.then_branch]
        if self.else_branch is not None:
            children.append(self.else_branch)
        return children


class WhileStmtNode(ASTNode):
    """当循环节点"""

    def __init__(
        self, condition: ASTNode, body: ASTNode, line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.WHILE_STMT, line, column)
        self.condition = condition
        self.body = body
        self._set_parent(condition)
        self._set_parent(body)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_while_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.condition, self.body]


class ForStmtNode(ASTNode):
    """循环语句节点"""

    def __init__(
        self,
        init: Optional[ASTNode],
        condition: Optional[ASTNode],
        update: Optional[ASTNode],
        body: ASTNode,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.FOR_STMT, line, column)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body
        self._set_parent(init)
        self._set_parent(condition)
        self._set_parent(update)
        self._set_parent(body)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_for_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = []
        if self.init is not None:
            children.append(self.init)
        if self.condition is not None:
            children.append(self.condition)
        if self.update is not None:
            children.append(self.update)
        children.append(self.body)
        return children


class BreakStmtNode(ASTNode):
    """跳出语句节点"""

    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.BREAK_STMT, line, column)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_break_stmt(self)


class ContinueStmtNode(ASTNode):
    """继续语句节点"""

    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.CONTINUE_STMT, line, column)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_continue_stmt(self)


class ReturnStmtNode(ASTNode):
    """返回语句节点"""

    def __init__(self, value: Optional[ASTNode], line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.RETURN_STMT, line, column)
        self.value = value
        self._set_parent(value)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_return_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        if self.value is not None:
            return [self.value]
        return []


class ExprStmtNode(ASTNode):
    """表达式语句节点"""

    def __init__(self, expr: ASTNode, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.EXPR_STMT, line, column)
        self.expr = expr
        self._set_parent(expr)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_expr_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.expr]


class DoWhileStmtNode(ASTNode):
    """执行-当循环节点"""

    def __init__(
        self, body: ASTNode, condition: ASTNode, line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.DO_WHILE_STMT, line, column)
        self.body = body
        self.condition = condition
        self._set_parent(body)
        self._set_parent(condition)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_do_while_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.body, self.condition]


class SwitchStmtNode(ASTNode):
    """选择语句节点"""

    def __init__(
        self, expr: ASTNode, cases: List[ASTNode], line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.SWITCH_STMT, line, column)
        self.expr = expr
        self.cases = cases
        self._set_parent(expr)
        self._set_parent_list(cases)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_switch_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.expr] + self.cases


class CaseStmtNode(ASTNode):
    """情况语句节点

    支持范围语法：
        分支 1...5:  # 范围 case，从 1 到 5
            statements
    """

    def __init__(
        self,
        value: Optional[ASTNode],
        statements: List[ASTNode],
        line: int = 0,
        column: int = 0,
        end_value: Optional[ASTNode] = None,
    ):
        super().__init__(ASTNodeType.CASE_STMT, line, column)
        self.value = value  # None 表示 default
        self.statements = statements
        self.end_value = end_value  # 范围 case 的结束值，None 表示单值
        self._set_parent(value)
        self._set_parent_list(statements)
        if end_value:
            self._set_parent(end_value)

    @property
    def is_range(self) -> bool:
        """判断是否为范围 case"""
        return self.end_value is not None

    @property
    def case_values(self) -> List[Any]:
        """获取展开后的所有 case 值"""

        if not self.is_range:
            return [self.value]
        return [self.value, self.end_value]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_case_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = []
        if self.value is not None:
            children.append(self.value)
        if self.end_value is not None:
            children.append(self.end_value)
        children.extend(self.statements)
        return children


class DefaultStmtNode(ASTNode):
    """默认语句节点"""

    def __init__(self, statements: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.DEFAULT_STMT, line, column)
        self.statements = statements
        self._set_parent_list(statements)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_default_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        return self.statements


class GotoStmtNode(ASTNode):
    """去向语句节点"""

    def __init__(self, label: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.GOTO_STMT, line, column)
        self.label = label

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_goto_stmt(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:label:{self.label}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class LabelStmtNode(ASTNode):
    """标签语句节点"""

    def __init__(
        self, name: str, statement: Optional[ASTNode], line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.LABEL_STMT, line, column)
        self.name = name
        self.statement = statement
        self._set_parent(statement)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_label_stmt(self)

    def get_children(self) -> List["ASTNode"]:
        if self.statement is not None:
            return [self.statement]
        return []

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:name:{self.name}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


# ============================================================================
# 表达式节点
# ============================================================================


class BinaryExprNode(ASTNode):
    """二元表达式节点"""

    def __init__(
        self,
        operator: str,
        left: ASTNode,
        right: ASTNode,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.BINARY_EXPR, line, column)
        self.operator = operator
        self.left = left
        self.right = right
        self._set_parent(left)
        self._set_parent(right)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_binary_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.left, self.right]

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"op:{self.operator}"]
        parts.append(self.left.get_hash())
        parts.append(self.right.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class UnaryExprNode(ASTNode):
    """一元表达式节点"""

    def __init__(
        self,
        operator: str,
        operand: ASTNode,
        is_prefix: bool = True,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.UNARY_EXPR, line, column)
        self.operator = operator
        self.operand = operand
        self.is_prefix = is_prefix
        self._set_parent(operand)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_unary_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.operand]

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"op:{self.operator}", f"prefix:{self.is_prefix}"]
        parts.append(self.operand.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class AssignExprNode(ASTNode):
    """赋值表达式节点"""

    def __init__(
        self,
        target: ASTNode,
        value: ASTNode,
        operator: str = "=",
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.ASSIGN_EXPR, line, column)
        self.target = target
        self.value = value
        self.operator = operator
        self._set_parent(target)
        self._set_parent(value)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_assign_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.target, self.value]

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"op:{self.operator}"]
        parts.append(self.target.get_hash())
        parts.append(self.value.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class CallExprNode(ASTNode):
    """函数调用节点"""

    def __init__(
        self, callee: ASTNode, args: List[ASTNode], line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.CALL_EXPR, line, column)
        self.callee = callee
        self.args = args
        self._set_parent(callee)
        self._set_parent_list(args)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_call_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.callee] + self.args


class MemberExprNode(ASTNode):
    """成员访问节点"""

    def __init__(self, obj: ASTNode, member: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.MEMBER_EXPR, line, column)
        self.obj = obj
        self.member = member
        self._set_parent(obj)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_member_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.obj]

    def get_hash(self) -> str:
        parts = [self.node_type.name, f"member:{self.member}"]
        parts.append(self.obj.get_hash())
        content = ":".join(parts)
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class ArrayExprNode(ASTNode):
    """数组访问节点"""

    def __init__(self, array: ASTNode, index: ASTNode, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.ARRAY_EXPR, line, column)
        self.array = array
        self.index = index
        self._set_parent(array)
        self._set_parent(index)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_array_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.array, self.index]


class IdentifierExprNode(ASTNode):
    """标识符节点"""

    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.IDENTIFIER_EXPR, line, column)
        self.name = name

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_identifier_expr(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:name:{self.name}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class IntLiteralNode(ASTNode):
    """整数字面量节点"""

    def __init__(self, value: int, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.INT_LITERAL, line, column)
        self.value = value

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_int_literal(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:value:{self.value}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class FloatLiteralNode(ASTNode):
    """浮点字面量节点"""

    def __init__(self, value: float, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.FLOAT_LITERAL, line, column)
        self.value = value

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_float_literal(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:value:{self.value}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class StringLiteralNode(ASTNode):
    """字符串字面量节点"""

    def __init__(self, value: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.STRING_LITERAL, line, column)
        self.value = value

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_string_literal(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:value:{self.value}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class CharLiteralNode(ASTNode):
    """字符字面量节点"""

    def __init__(self, value: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.CHAR_LITERAL, line, column)
        self.value = value

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_char_literal(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:value:{self.value}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class BoolLiteralNode(ASTNode):
    """布尔字面量节点"""

    def __init__(self, value: bool, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.BOOL_LITERAL, line, column)
        self.value = value

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_bool_literal(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:value:{self.value}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class NullLiteralNode(ASTNode):
    """空字面量节点"""

    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.NULL_LITERAL, line, column)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_null_literal(self)


class TernaryExprNode(ASTNode):
    """三元表达式节点 (cond ? then_expr : else_expr)"""

    def __init__(
        self,
        condition: ASTNode,
        then_expr: ASTNode,
        else_expr: ASTNode,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.TERNARY_EXPR, line, column)
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr
        self._set_parent(condition)
        self._set_parent(then_expr)
        self._set_parent(else_expr)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_ternary_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.condition, self.then_expr, self.else_expr]


class SizeofExprNode(ASTNode):
    """sizeof 表达式节点"""

    def __init__(self, target: ASTNode, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.SIZEOF_EXPR, line, column)
        self.target = target  # 可以是类型节点或表达式节点
        self._set_parent(target)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_sizeof_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.target]


class CastExprNode(ASTNode):
    """类型转换表达式节点"""

    def __init__(
        self, cast_type: ASTNode, expr: ASTNode, line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.CAST_EXPR, line, column)
        self.cast_type = cast_type
        self.expr = expr
        self._set_parent(cast_type)
        self._set_parent(expr)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_cast_expr(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.cast_type, self.expr]


class ArrayInitNode(ASTNode):
    """数组初始化节点 {1, 2, 3}"""

    def __init__(self, elements: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.ARRAY_INIT, line, column)
        self.elements = elements
        self._set_parent_list(elements)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_array_init(self)

    def get_children(self) -> List["ASTNode"]:
        return self.elements


class StructInitNode(ASTNode):
    """结构体初始化节点 {.x = 1, .y = 2} 或 {1, 2}"""

    def __init__(
        self,
        values: List[ASTNode],
        field_names: Optional[List[str]] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.STRUCT_INIT, line, column)
        self.values = values
        self.field_names = field_names  # 指定字段名初始化
        self._set_parent_list(values)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_struct_init(self)

    def get_children(self) -> List["ASTNode"]:
        return self.values


# ============================================================================
# 类型节点
# ============================================================================


class PrimitiveTypeNode(ASTNode):
    """基本类型节点"""

    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.PRIMITIVE_TYPE, line, column)
        self.name = name

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_primitive_type(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:name:{self.name}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class PointerTypeNode(ASTNode):
    """指针类型节点"""

    def __init__(self, base_type: ASTNode, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.POINTER_TYPE, line, column)
        self.base_type = base_type
        self._set_parent(base_type)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_pointer_type(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.base_type]


class ArrayTypeNode(ASTNode):
    """数组类型节点"""

    def __init__(
        self,
        element_type: ASTNode,
        size: Optional[ASTNode],
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.ARRAY_TYPE, line, column)
        self.element_type = element_type
        self.size = size
        self._set_parent(element_type)
        self._set_parent(size)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_array_type(self)

    def get_children(self) -> List["ASTNode"]:
        children: List["ASTNode"] = [self.element_type]
        if self.size is not None:
            children.append(self.size)
        return children


class FunctionTypeNode(ASTNode):
    """函数类型节点"""

    def __init__(
        self,
        return_type: ASTNode,
        param_types: List[ASTNode],
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.FUNCTION_TYPE, line, column)
        self.return_type = return_type
        self.param_types = param_types
        self._set_parent(return_type)
        self._set_parent_list(param_types)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_function_type(self)

    def get_children(self) -> List["ASTNode"]:
        return [self.return_type] + self.param_types


class StructTypeNode(ASTNode):
    """结构体类型节点"""

    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.STRUCT_TYPE, line, column)
        self.name = name

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_struct_type(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:name:{self.name}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class AutoTypeNode(ASTNode):
    """自动类型节点（用于自动类型推导）"""

    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(ASTNodeType.AUTO_TYPE, line, column)
        self.resolved_type: Optional[str] = None  # 解析后的实际类型

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_auto_type(self)

    def get_hash(self) -> str:
        content = f"{self.node_type.name}:resolved:{self.resolved_type}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


# ============================================================================
# AST访问者
# ============================================================================


class ASTVisitor(ABC):
    """AST访问者基类"""

    @abstractmethod
    def visit_program(self, node: ProgramNode) -> Any:
        pass

    @abstractmethod
    def visit_module_decl(self, node: ModuleDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_import_decl(self, node: ImportDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_variable_decl(self, node: VariableDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_param_decl(self, node: ParamDeclNode) -> Any:
        pass

    @abstractmethod
    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_break_stmt(self, node: BreakStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_continue_stmt(self, node: ContinueStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        pass

    @abstractmethod
    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        pass

    @abstractmethod
    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        pass

    @abstractmethod
    def visit_assign_expr(self, node: AssignExprNode) -> Any:
        pass

    @abstractmethod
    def visit_call_expr(self, node: CallExprNode) -> Any:
        pass

    @abstractmethod
    def visit_member_expr(self, node: MemberExprNode) -> Any:
        pass

    @abstractmethod
    def visit_array_expr(self, node: ArrayExprNode) -> Any:
        pass

    @abstractmethod
    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        pass

    @abstractmethod
    def visit_int_literal(self, node: IntLiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_float_literal(self, node: FloatLiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_string_literal(self, node: StringLiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_char_literal(self, node: CharLiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_bool_literal(self, node: BoolLiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_null_literal(self, node: NullLiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_primitive_type(self, node: PrimitiveTypeNode) -> Any:
        pass

    @abstractmethod
    def visit_pointer_type(self, node: PointerTypeNode) -> Any:
        pass

    @abstractmethod
    def visit_array_type(self, node: ArrayTypeNode) -> Any:
        pass

    @abstractmethod
    def visit_function_type(self, node: FunctionTypeNode) -> Any:
        pass

    @abstractmethod
    def visit_struct_type(self, node: StructTypeNode) -> Any:
        pass

    @abstractmethod
    def visit_auto_type(self, node: "AutoTypeNode") -> Any:
        pass

    @abstractmethod
    def visit_do_while_stmt(self, node: "DoWhileStmtNode") -> Any:
        pass

    @abstractmethod
    def visit_switch_stmt(self, node: "SwitchStmtNode") -> Any:
        pass

    @abstractmethod
    def visit_case_stmt(self, node: "CaseStmtNode") -> Any:
        pass

    @abstractmethod
    def visit_default_stmt(self, node: "DefaultStmtNode") -> Any:
        pass

    @abstractmethod
    def visit_goto_stmt(self, node: "GotoStmtNode") -> Any:
        pass

    @abstractmethod
    def visit_label_stmt(self, node: "LabelStmtNode") -> Any:
        pass

    @abstractmethod
    def visit_enum_decl(self, node: "EnumDeclNode") -> Any:
        pass

    @abstractmethod
    def visit_union_decl(self, node: "UnionDeclNode") -> Any:
        pass

    @abstractmethod
    def visit_typedef_decl(self, node: "TypedefDeclNode") -> Any:
        pass

    @abstractmethod
    def visit_ternary_expr(self, node: "TernaryExprNode") -> Any:
        pass

    @abstractmethod
    def visit_sizeof_expr(self, node: "SizeofExprNode") -> Any:
        pass

    @abstractmethod
    def visit_cast_expr(self, node: "CastExprNode") -> Any:
        pass

    @abstractmethod
    def visit_array_init(self, node: "ArrayInitNode") -> Any:
        pass

    @abstractmethod
    def visit_struct_init(self, node: "StructInitNode") -> Any:
        pass


class ASTPrinter(ASTVisitor):
    """AST打印器"""

    def __init__(self):
        self.indent = 0

    def _print(self, text: str):
        print("  " * self.indent + text)

    def visit_program(self, node: ProgramNode) -> Any:
        self._print("Program")
        self.indent += 1
        for decl in node.declarations:
            decl.accept(self)
        self.indent -= 1

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        self._print(f"FunctionDecl: {node.name}")
        self.indent += 1
        self._print("ReturnType:")
        self.indent += 1
        node.return_type.accept(self)
        self.indent -= 1
        self._print("Params:")
        self.indent += 1
        for param in node.params:
            param.accept(self)
        self.indent -= 1
        if node.body:
            self._print("Body:")
            self.indent += 1
            node.body.accept(self)
            self.indent -= 1
        self.indent -= 1

    def visit_variable_decl(self, node: VariableDeclNode) -> Any:
        const_str = "const " if node.is_const else ""
        self._print(f"VariableDecl: {const_str}{node.name}")
        self.indent += 1
        self._print("Type:")
        self.indent += 1
        node.var_type.accept(self)
        self.indent -= 1
        if node.init:
            self._print("Init:")
            self.indent += 1
            node.init.accept(self)
            self.indent -= 1
        self.indent -= 1

    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        self._print(f"BinaryExpr: {node.operator}")
        self.indent += 1
        node.left.accept(self)
        node.right.accept(self)
        self.indent -= 1

    def visit_int_literal(self, node: IntLiteralNode) -> Any:
        self._print(f"IntLiteral: {node.value}")

    def visit_float_literal(self, node: FloatLiteralNode) -> Any:
        self._print(f"FloatLiteral: {node.value}")

    def visit_string_literal(self, node: StringLiteralNode) -> Any:
        self._print(f'StringLiteral: "{node.value}"')

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        self._print(f"Identifier: {node.name}")

    def visit_primitive_type(self, node: PrimitiveTypeNode) -> Any:
        self._print(f"PrimitiveType: {node.name}")

    # 其他visit方法
    def visit_module_decl(self, node: ModuleDeclNode) -> Any:
        self._print(f"ModuleDecl: {node.name}")

    def visit_import_decl(self, node: ImportDeclNode) -> Any:
        self._print(f"ImportDecl: {node.module_name}")

    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        self._print(f"StructDecl: {node.name}")

    def visit_param_decl(self, node: ParamDeclNode) -> Any:
        self._print(f"ParamDecl: {node.name}")

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        self._print("BlockStmt")

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        self._print("IfStmt")

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        self._print("WhileStmt")

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        self._print("ForStmt")

    def visit_break_stmt(self, node: BreakStmtNode) -> Any:
        self._print("BreakStmt")

    def visit_continue_stmt(self, node: ContinueStmtNode) -> Any:
        self._print("ContinueStmt")

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        self._print("ReturnStmt")

    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        self._print("ExprStmt")

    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        self._print(f"UnaryExpr: {node.operator}")

    def visit_assign_expr(self, node: AssignExprNode) -> Any:
        self._print(f"AssignExpr: {node.operator}")

    def visit_call_expr(self, node: CallExprNode) -> Any:
        self._print("CallExpr")

    def visit_member_expr(self, node: MemberExprNode) -> Any:
        self._print(f"MemberExpr: {node.member}")

    def visit_array_expr(self, node: ArrayExprNode) -> Any:
        self._print("ArrayExpr")

    def visit_char_literal(self, node: CharLiteralNode) -> Any:
        self._print(f"CharLiteral: '{node.value}'")

    def visit_bool_literal(self, node: BoolLiteralNode) -> Any:
        self._print(f"BoolLiteral: {node.value}")

    def visit_null_literal(self, node: NullLiteralNode) -> Any:
        self._print("NullLiteral")

    def visit_pointer_type(self, node: PointerTypeNode) -> Any:
        self._print("PointerType")

    def visit_array_type(self, node: ArrayTypeNode) -> Any:
        self._print("ArrayType")

    def visit_function_type(self, node: FunctionTypeNode) -> Any:
        self._print("FunctionType")

    def visit_struct_type(self, node: StructTypeNode) -> Any:
        self._print(f"StructType: {node.name}")

    def visit_auto_type(self, node: "AutoTypeNode") -> Any:
        resolved = f" -> {node.resolved_type}" if node.resolved_type else ""
        self._print(f"AutoType{resolved}")

    def visit_do_while_stmt(self, node: "DoWhileStmtNode") -> Any:
        self._print("DoWhileStmt")

    def visit_switch_stmt(self, node: "SwitchStmtNode") -> Any:
        self._print("SwitchStmt")

    def visit_case_stmt(self, node: "CaseStmtNode") -> Any:
        self._print("CaseStmt")

    def visit_default_stmt(self, node: "DefaultStmtNode") -> Any:
        self._print("DefaultStmt")

    def visit_goto_stmt(self, node: "GotoStmtNode") -> Any:
        self._print(f"GotoStmt: {node.label}")

    def visit_label_stmt(self, node: "LabelStmtNode") -> Any:
        self._print(f"LabelStmt: {node.name}")

    def visit_enum_decl(self, node: "EnumDeclNode") -> Any:
        self._print(f"EnumDecl: {node.name}")

    def visit_union_decl(self, node: "UnionDeclNode") -> Any:
        self._print(f"UnionDecl: {node.name}")

    def visit_typedef_decl(self, node: "TypedefDeclNode") -> Any:
        self._print(f"TypedefDecl: {node.new_name}")

    def visit_ternary_expr(self, node: "TernaryExprNode") -> Any:
        self._print("TernaryExpr")

    def visit_sizeof_expr(self, node: "SizeofExprNode") -> Any:
        self._print("SizeofExpr")

    def visit_cast_expr(self, node: "CastExprNode") -> Any:
        self._print("CastExpr")

    def visit_array_init(self, node: "ArrayInitNode") -> Any:
        self._print("ArrayInit")

    def visit_struct_init(self, node: "StructInitNode") -> Any:
        self._print("StructInit")


if __name__ == "__main__":
    # 测试AST构建
    print("=" * 70)
    print("AST节点测试")
    print("=" * 70)

    # 创建一个简单的程序
    int_type = PrimitiveTypeNode("整数型")
    count_var = VariableDeclNode("计数", int_type, IntLiteralNode(0))

    printer = ASTPrinter()
    count_var.accept(printer)

    # 测试增量功能
    print()
    print("=" * 70)
    print("增量功能测试")
    print("=" * 70)

    # 测试 parent 引用
    print(f"count_var.parent: {count_var.parent}")
    print(f"int_type.parent: {int_type.parent}")
    print(f"IntLiteralNode.parent: {count_var.init.parent}")
    assert count_var.init.parent is count_var, "parent引用应正确设置"
    assert count_var.var_type.parent is count_var, "parent引用应正确设置"
    print("✅ parent 引用正常")

    # 测试 get_children
    children = count_var.get_children()
    assert len(children) == 2, f"应有2个子节点，实际{len(children)}"
    print(f"✅ get_children: {[type(c).__name__ for c in children]}")

    # 测试 get_hash
    hash1 = count_var.get_hash()
    print(f"✅ get_hash: {hash1[:16]}...")

    # 测试 get_path
    path = count_var.init.get_path()
    print(f"✅ get_path: {' -> '.join(path)}")

    # 测试相同值不同节点的哈希
    int_type2 = PrimitiveTypeNode("整数型")
    hash2 = int_type2.get_hash()
    assert hash1 != hash2, "不同节点应有不同哈希"

    # 测试相同结构不同值的哈希
    int_type3 = PrimitiveTypeNode("浮点型")
    hash3 = int_type3.get_hash()
    assert hash2 != hash3, "不同类型应有不同哈希"
    print("✅ 哈希区分正常")

    print()
    print("=" * 70)
    print("🎉 所有测试通过!")
    print("=" * 70)
