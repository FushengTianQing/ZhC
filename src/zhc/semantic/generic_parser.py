#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泛型语法解析器 - Generic Syntax Parser

扩展词法分析器和语法分析器以支持泛型语法。

支持的语法：
1. 泛型类型声明：
   泛型类型 列表<类型 T> { ... }

2. 泛型函数声明：
   泛型函数 T 最大值<类型 T>(T a, T b) { ... }

3. 类型参数约束：
   泛型类型 Pair<类型 K, 类型 V: 可比较> { ... }

4. Where 子句约束：
   泛型函数 T 最大值(T a, T b)
       其中 类型 T: 可比较
   { ... }

Phase 4 - Stage 2 - Task 11.1

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Any, TYPE_CHECKING
from enum import Enum
import hashlib

# 导入核心组件
from ..parser.lexer import Lexer, Token, TokenType
from ..parser.ast_nodes import ASTNode, ASTNodeType

# 导入泛型类型系统
from ..semantic.generics import (
    TypeParameter,
    TypeConstraint,
    GenericType,
    GenericFunction,
    Variance,
    PredefinedConstraints,
)

if TYPE_CHECKING:
    pass


# ===== 泛型 Token 类型扩展 =====


class GenericTokenType(Enum):
    """泛型相关的Token类型（用于上下文分析）"""

    TYPE_ARGUMENT_START = "类型参数开始"  # <
    TYPE_ARGUMENT_END = "类型参数结束"  # >
    TYPE_PARAMETER = "类型参数"  # 类型
    WHERE_CLAUSE = "其中子句"  # 其中


# ===== 泛型 AST 节点 =====


class GenericTypeNode(ASTNode):
    """
    泛型类型节点

    表示一个带有类型参数的泛型类型，如 列表<整数型>。
    """

    def __init__(
        self,
        base_type: str,
        type_args: List["TypeNode"] = None,
        type_params: List[TypeParameter] = None,
        constraints: List[TypeConstraint] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.STRUCT_TYPE, line, column)
        self.base_type = base_type
        self.type_args = type_args or []
        self.type_params = type_params or []
        self.constraints = constraints or []

    @property
    def name(self) -> str:
        """获取完整类型名"""
        if self.type_args:
            args_str = ", ".join(
                arg.name if hasattr(arg, "name") else str(arg) for arg in self.type_args
            )
            return f"{self.base_type}<{args_str}>"
        return self.base_type

    def get_children(self) -> List[ASTNode]:
        """获取子节点"""
        return self.type_args

    def get_hash(self) -> str:
        """计算节点哈希"""
        content = f"GenericType:{self.base_type}:{','.join(arg.get_hash() if hasattr(arg, 'get_hash') else str(arg) for arg in self.type_args)}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def accept(self, visitor):
        """接受访问者"""
        return visitor.visit_generic_type(self)


class TypeNode(ASTNode):
    """
    类型节点

    支持基本类型和泛型类型。
    """

    def __init__(
        self,
        type_name: str,
        is_generic: bool = False,
        generic_args: List["TypeNode"] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.PRIMITIVE_TYPE, line, column)
        self.type_name = type_name
        self.is_generic = is_generic
        self.generic_args = generic_args or []

    @property
    def name(self) -> str:
        """获取类型名"""
        if self.is_generic and self.generic_args:
            args_str = ", ".join(arg.name for arg in self.generic_args)
            return f"{self.type_name}<{args_str}>"
        return self.type_name

    def get_children(self) -> List[ASTNode]:
        """获取子节点"""
        return self.generic_args

    def get_hash(self) -> str:
        """计算节点哈希"""
        content = f"Type:{self.type_name}:{self.is_generic}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def accept(self, visitor):
        """接受访问者"""
        return visitor.visit_type(self)


class TypeParameterNode(ASTNode):
    """
    类型参数节点

    表示声明中的类型参数，如 T, K, V: 可比较。
    """

    def __init__(
        self,
        name: str,
        variance: Variance = Variance.INVARIANT,
        constraints: List[str] = None,
        default_type: Optional[str] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.PARAM_DECL, line, column)
        self.name = name
        self.variance = variance
        self.constraints = constraints or []
        self.default_type = default_type

    def to_type_parameter(self) -> TypeParameter:
        """转换为语义层的 TypeParameter"""
        type_constraints = []
        for constraint_name in self.constraints:
            # 尝试从预定义约束获取
            predefined_methods = {
                "可比较": PredefinedConstraints.comparable,
                "可相等": PredefinedConstraints.equatable,
                "可加": PredefinedConstraints.addable,
                "可打印": PredefinedConstraints.printable,
                "数值型": PredefinedConstraints.numeric,
            }

            if constraint_name in predefined_methods:
                type_constraints.append(predefined_methods[constraint_name]())
            else:
                # 自定义约束，需要从管理器获取
                from ..semantic.generics import get_generic_manager

                manager = get_generic_manager()
                custom_constraint = manager.get_constraint(constraint_name)
                if custom_constraint:
                    type_constraints.append(custom_constraint)

        return TypeParameter(
            name=self.name,
            constraints=type_constraints,
            default=self.default_type,
            variance=self.variance,
        )

    def get_children(self) -> List[ASTNode]:
        return []

    def get_hash(self) -> str:
        content = f"TypeParam:{self.name}:{self.variance.value}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def accept(self, visitor):
        """接受访问者"""
        return visitor.visit_type_parameter(self)


class WhereClauseNode(ASTNode):
    """
    Where 子句节点

    表示泛型约束的 where 子句。
    语法：其中 类型 T: 可比较, 可打印
    """

    def __init__(
        self, constraints: List[Tuple[str, str]] = None, line: int = 0, column: int = 0
    ):
        super().__init__(ASTNodeType.PARAM_DECL, line, column)
        self.constraints = constraints or []

    def get_children(self) -> List[ASTNode]:
        return []

    def get_hash(self) -> str:
        content = f"Where:{','.join(f'{t}:{c}' for t, c in self.constraints)}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def accept(self, visitor):
        """接受访问者"""
        return visitor.visit_where_clause(self)


class GenericTypeDeclNode(ASTNode):
    """
    泛型类型声明节点

    表示完整的泛型类型声明。
    语法：泛型类型 列表<类型 T> { 成员... }
    """

    def __init__(
        self,
        name: str,
        type_params: List[TypeParameterNode] = None,
        members: List[ASTNode] = None,
        where_clause: Optional[WhereClauseNode] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.STRUCT_DECL, line, column)
        self.name = name
        self.type_params = type_params or []
        self.members = members or []
        self.where_clause = where_clause

    def to_generic_type(self) -> GenericType:
        """转换为语义层的 GenericType"""
        params = [tp.to_type_parameter() for tp in self.type_params]
        return GenericType(name=self.name, type_params=params, definition=self)

    def get_children(self) -> List[ASTNode]:
        return self.members

    def get_hash(self) -> str:
        content = f"GenericTypeDecl:{self.name}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def accept(self, visitor):
        """接受访问者"""
        return visitor.visit_generic_type_decl(self)


class GenericFunctionDeclNode(ASTNode):
    """
    泛型函数声明节点

    表示完整的泛型函数声明。
    语法：泛型函数 T 最大值<类型 T>(T a, T b) -> T { ... }
    """

    def __init__(
        self,
        name: str,
        type_params: List[TypeParameterNode] = None,
        params: List[ASTNode] = None,
        return_type: Optional[TypeNode] = None,
        body: Optional[ASTNode] = None,
        where_clause: Optional[WhereClauseNode] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(ASTNodeType.FUNCTION_DECL, line, column)
        self.name = name
        self.type_params = type_params or []
        self.params = params or []
        self.return_type = return_type or TypeNode("空型")
        self.body = body
        self.where_clause = where_clause

    def to_generic_function(self) -> GenericFunction:
        """转换为语义层的 GenericFunction"""
        from ..semantic.generics import ParamInfo

        params = [tp.to_type_parameter() for tp in self.type_params]
        param_infos = [
            ParamInfo(
                name=p.name if hasattr(p, "name") else "unknown",
                type_name=p.type_name if hasattr(p, "type_name") else "未知",
            )
            for p in self.params
        ]
        return GenericFunction(
            name=self.name,
            type_params=params,
            params=param_infos,
            return_type=self.return_type.type_name if self.return_type else "空型",
            body=self.body,
        )

    def get_children(self) -> List[ASTNode]:
        children = list(self.params)
        if self.body:
            children.append(self.body)
        return children

    def get_hash(self) -> str:
        content = f"GenericFuncDecl:{self.name}:{len(self.type_params)}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def accept(self, visitor):
        """接受访问者"""
        return visitor.visit_generic_function_decl(self)


# ===== 泛型解析器 =====


class GenericParserMixin:
    """
    泛型解析混入类

    提供泛型语法解析的方法，供 Parser 类组合使用。
    """

    def __init__(self):
        # 泛型嵌套深度，用于区分 < 是泛型还是小于运算符
        self._generic_depth: int = 0

    def parse_generic_type(self) -> TypeNode:
        """
        解析泛型类型

        语法：类型名<类型实参, 类型实参, ...>

        Returns:
            TypeNode with is_generic=True
        """
        # 获取基础类型名
        base_type_token = self.expect(TokenType.IDENTIFIER, "泛型类型名")
        base_type = base_type_token.value if base_type_token else "unknown"

        # 检查是否有泛型参数
        type_args: List[TypeNode] = []

        if self.match(TokenType.LT) or (self.current_token().type == TokenType.LT):
            self.advance()  # 消耗 <
            self._generic_depth += 1
            type_args = self._parse_type_argument_list()
            self._generic_depth -= 1

        return TypeNode(
            type_name=base_type,
            is_generic=len(type_args) > 0,
            generic_args=type_args,
            line=base_type_token.line if base_type_token else 0,
            column=base_type_token.column if base_type_token else 0,
        )

    def _parse_type_argument_list(self) -> List[TypeNode]:
        """
        解析类型实参列表

        语法：<类型, 类型, ...>

        Returns:
            TypeNode 列表
        """
        type_args: List[TypeNode] = []

        while not self.is_at_end() and not self.check(TokenType.GT):
            type_arg = self.parse_type_reference()
            if type_arg:
                type_args.append(type_arg)

            # 消费逗号
            if self.match(TokenType.COMMA):
                self.advance()
            elif not self.check(TokenType.GT):
                # 可能是语法错误，但尝试继续
                break

        # 消费 >
        self.expect(TokenType.GT, "类型参数列表结束 '>'")

        return type_args

    def parse_type_reference(self) -> TypeNode:
        """
        解析类型引用

        支持：
        - 基本类型：整数型、浮点型
        - 泛型类型：列表<整数型>
        - 嵌套泛型：映射<字符串型, 列表<整数型>>

        Returns:
            TypeNode
        """
        token = self.current_token()

        # 基本类型关键字
        if self.match(
            TokenType.INT,
            TokenType.FLOAT,
            TokenType.CHAR,
            TokenType.BOOL,
            TokenType.VOID,
            TokenType.STRING,
            TokenType.DOUBLE,
            TokenType.LONG,
            TokenType.SHORT,
            TokenType.BYTE,
        ):
            type_name = self.advance().value
            return TypeNode(type_name=type_name, line=token.line, column=token.column)

        # 标识符（可能是基本类型或泛型类型）
        if self.match(TokenType.IDENTIFIER):
            type_name = self.advance().value

            # 检查是否是泛型类型
            if self.match(TokenType.LT) or self.current_token().type == TokenType.LT:
                self.advance()  # 消耗 <
                self._generic_depth += 1
                type_args = self._parse_type_argument_list()
                self._generic_depth -= 1
                return TypeNode(
                    type_name=type_name,
                    is_generic=True,
                    generic_args=type_args,
                    line=token.line,
                    column=token.column,
                )

            return TypeNode(type_name=type_name, line=token.line, column=token.column)

        # 未知类型，返回空型
        return TypeNode(type_name="空型", line=token.line, column=token.column)

    def parse_type_parameter_declaration(self) -> TypeParameterNode:
        """
        解析类型参数声明

        语法：
        - T
        - 类型 T
        - 类型 T: 可比较
        - +T (协变)
        - -T (逆变)
        - 类型 T: 可比较, 可打印 = 整数型 (带默认值)

        Returns:
            TypeParameterNode
        """
        token = self.current_token()
        variance = Variance.INVARIANT
        constraints: List[str] = []
        default_type: Optional[str] = None
        name = ""

        # 解析类型参数名
        if self.match(TokenType.TYPE_PARAM):
            self.advance()  # 消耗 '类型' 关键字
            name_token = self.expect(TokenType.IDENTIFIER, "类型参数名")
            name = name_token.value if name_token else "T"
        elif self.match(TokenType.IDENTIFIER):
            name = self.advance().value
        else:
            # 解析变性标记
            if self.match(TokenType.PLUS):
                self.advance()
                variance = Variance.COVARIANT
                name_token = self.expect(TokenType.IDENTIFIER, "类型参数名")
                name = name_token.value if name_token else "T"
            elif self.match(TokenType.MINUS):
                self.advance()
                variance = Variance.CONTRAVARIANT
                name_token = self.expect(TokenType.IDENTIFIER, "类型参数名")
                name = name_token.value if name_token else "T"
            else:
                self.errors.append(self._create_error("期望类型参数名"))
                return TypeParameterNode(name="T", line=token.line, column=token.column)

        # 解析约束
        if self.match(TokenType.COLON):
            self.advance()  # 消耗 :
            # 解析约束列表
            while (
                not self.check(TokenType.COMMA)
                and not self.check(TokenType.GT)
                and not self.check(TokenType.EQ)
                and not self.is_at_end()
            ):
                constraint_token = self.expect(TokenType.IDENTIFIER, "约束名")
                if constraint_token:
                    constraints.append(constraint_token.value)

                if self.match(TokenType.COMMA):
                    self.advance()
                else:
                    break

        # 解析默认值
        if self.match(TokenType.EQ):
            self.advance()  # 消耗 =
            default_type = self.current_token().value
            self.advance()

        return TypeParameterNode(
            name=name,
            variance=variance,
            constraints=constraints,
            default_type=default_type,
            line=token.line,
            column=token.column,
        )

    def parse_type_parameter_list(self) -> List[TypeParameterNode]:
        """
        解析类型参数列表

        语法：<类型 T, 类型 V: 可比较>

        Returns:
            TypeParameterNode 列表
        """
        type_params: List[TypeParameterNode] = []

        # 消费 <
        self.expect(TokenType.LT, "类型参数列表开始 '<'")

        while not self.is_at_end() and not self.check(TokenType.GT):
            param = self.parse_type_parameter_declaration()
            type_params.append(param)

            if self.match(TokenType.COMMA):
                self.advance()
            elif not self.check(TokenType.GT):
                break

        # 消费 >
        self.expect(TokenType.GT, "类型参数列表结束 '>'")

        return type_params

    def parse_generic_type_declaration(self) -> GenericTypeDeclNode:
        """
        解析泛型类型声明

        语法：泛型类型 名字<类型参数> { 成员... }

        Returns:
            GenericTypeDeclNode
        """
        # 消费 '泛型类型' 关键字
        start_token = self.expect(TokenType.GENERIC_TYPE, "泛型类型声明")

        # 获取类型名
        name_token = self.expect(TokenType.IDENTIFIER, "泛型类型名")
        name = name_token.value if name_token else "UnknownGeneric"

        # 解析类型参数
        type_params: List[TypeParameterNode] = []
        if self.match(TokenType.LT) or self.current_token().type == TokenType.LT:
            type_params = self.parse_type_parameter_list()

        # 解析 Where 子句（可选）
        where_clause: Optional[WhereClauseNode] = None
        if self.match(TokenType.WHERE):
            where_clause = self.parse_where_clause()

        # 解析结构体成员
        members: List[ASTNode] = []
        self.expect(TokenType.LBRACE, "泛型类型定义开始 '{'")

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            member = self.parse_variable_decl()
            if member:
                members.append(member)

        self.expect(TokenType.RBRACE, "泛型类型定义结束 '}'")

        # 消费可选的分号
        if self.match(TokenType.SEMICOLON):
            self.advance()

        return GenericTypeDeclNode(
            name=name,
            type_params=type_params,
            members=members,
            where_clause=where_clause,
            line=start_token.line if start_token else 0,
            column=start_token.column if start_token else 0,
        )

    def parse_generic_function_declaration(self) -> GenericFunctionDeclNode:
        """
        解析泛型函数声明

        语法：泛型函数 返回类型 名字<类型参数>(参数列表) -> 返回类型 { ... }

        Returns:
            GenericFunctionDeclNode
        """
        # 消费 '泛型函数' 关键字
        start_token = self.expect(TokenType.GENERIC_FUNC, "泛型函数声明")

        # 解析返回类型
        return_type = self.parse_type_reference()

        # 获取函数名
        name_token = self.expect(TokenType.IDENTIFIER, "函数名")
        name = name_token.value if name_token else "unknown_func"

        # 解析类型参数
        type_params: List[TypeParameterNode] = []
        if self.match(TokenType.LT) or self.current_token().type == TokenType.LT:
            type_params = self.parse_type_parameter_list()

        # 解析参数列表
        self.expect(TokenType.LPAREN, "参数列表开始 '('")
        params: List[ASTNode] = []

        while not self.check(TokenType.RPAREN) and not self.is_at_end():
            param = self.parse_param_decl()
            if param:
                params.append(param)

            if self.match(TokenType.COMMA):
                self.advance()
            elif not self.check(TokenType.RPAREN):
                break

        self.expect(TokenType.RPAREN, "参数列表结束 ')'")

        # 检查返回类型标注
        if self.match(TokenType.ARROW):
            self.advance()
            return_type = self.parse_type_reference()

        # 解析 Where 子句（可选）
        where_clause: Optional[WhereClauseNode] = None
        if self.match(TokenType.WHERE):
            where_clause = self.parse_where_clause()

        # 解析函数体
        body: Optional[ASTNode] = None
        if self.match(TokenType.LBRACE):
            body = self.parse_block()

        return GenericFunctionDeclNode(
            name=name,
            type_params=type_params,
            params=params,
            return_type=return_type,
            body=body,
            where_clause=where_clause,
            line=start_token.line if start_token else 0,
            column=start_token.column if start_token else 0,
        )

    def parse_where_clause(self) -> WhereClauseNode:
        """
        解析 Where 子句

        语法：其中 类型 T: 可比较, 可打印

        Returns:
            WhereClauseNode
        """
        start_token = self.expect(TokenType.WHERE, "'其中' 子句")

        constraints: List[Tuple[str, str]] = []

        while not self.check(TokenType.LBRACE) and not self.is_at_end():
            # 解析类型参数名
            type_param_token = self.expect(TokenType.IDENTIFIER, "类型参数名")
            type_param_name = type_param_token.value if type_param_token else ""

            # 消费 :
            self.expect(TokenType.COLON, "约束分隔符 ':'")

            # 解析约束列表
            while (
                not self.check(TokenType.COMMA)
                and not self.check(TokenType.LBRACE)
                and not self.is_at_end()
            ):
                constraint_token = self.expect(TokenType.IDENTIFIER, "约束名")
                if constraint_token:
                    constraints.append((type_param_name, constraint_token.value))

                if self.match(TokenType.COMMA):
                    self.advance()
                else:
                    break

            if self.check(TokenType.COMMA):
                self.advance()
            else:
                break

        return WhereClauseNode(
            constraints=constraints,
            line=start_token.line if start_token else 0,
            column=start_token.column if start_token else 0,
        )

    def is_in_generic_context(self) -> bool:
        """检查是否在泛型上下文中"""
        return self._generic_depth > 0


# ===== 便捷函数 =====


def tokenize_generic(source: str) -> Tuple[List[Token], List[Any]]:
    """
    词法分析泛型代码

    Args:
        source: 源代码

    Returns:
        (Token列表, 错误列表)
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    return tokens, lexer.get_errors()


# ===== 测试代码 =====

if __name__ == "__main__":
    # 测试泛型类型
    test_code_1 = """
    泛型类型 列表<类型 T> {
        T[] 数据;
        整数型 长度;
    };
    """

    print("=" * 70)
    print("测试 1: 泛型类型声明")
    print("=" * 70)
    print(test_code_1)
    print()

    # 测试泛型函数
    test_code_2 = """
    泛型函数 T 最大值<类型 T: 可比较>(T a, T b) -> T {
        如果 (a > b) {
            返回 a;
        }
        返回 b;
    }
    """

    print("=" * 70)
    print("测试 2: 泛型函数声明")
    print("=" * 70)
    print(test_code_2)
    print()

    # 测试 Where 子句
    test_code_3 = """
    泛型函数 T 打印最大值<类型 T>(T a, T b)
        其中 类型 T: 可打印
    {
        T 最大 = (a > b) ? a : b;
        打印(最大);
        返回 最大;
    }
    """

    print("=" * 70)
    print("测试 3: Where 子句")
    print("=" * 70)
    print(test_code_3)
    print()

    # 测试嵌套泛型
    test_code_4 = """
    泛型类型 映射<类型 K, 类型 V> {
        K[] 键列表;
        V[] 值列表;
    };

    泛型函数 映射<字符串型, 整数型> 创建映射() {
        返回 空指针;
    }
    """

    print("=" * 70)
    print("测试 4: 嵌套泛型")
    print("=" * 70)
    print(test_code_4)
    print()
