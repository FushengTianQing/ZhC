#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表达式解析器 - Expression Parser

功能：
- 类型解析
- 表达式解析
- 赋值表达式解析
- 二元表达式解析（一元、二元）
- 优先级解析
- 函数调用解析
- 字面量解析

作者：远
日期：2026-04-03

重构说明：
- 从parser.py分离表达式解析相关功能
- 使用递归下降解析器处理运算符优先级
"""

from typing import List, Dict, Tuple, Optional, Set, Any
from .ast_nodes import (
    PrimitiveTypeNode as TypeNode,
    BinaryExprNode as BinaryOpNode,
    UnaryExprNode as UnaryOpNode,
    CallExprNode,
    ArrayExprNode as IndexExprNode,
    MemberExprNode,
    IntLiteralNode as LiteralNode,
    IdentifierExprNode as IdentifierNode,
    ASTNode,
    ASTNodeType,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode,
    CharLiteralNode, BoolLiteralNode, NullLiteralNode,
    PointerTypeNode, ArrayTypeNode,
)


class ExpressionParserMixin:
    """
    表达式解析混入类

    使用递归下降解析器处理表达式
    """

    def parse_type(self) -> ASTNode:
        """
        解析类型

        Returns:
            类型节点
        """
        token = self.current_token()

        # 内置类型
        type_map = {
            '整数型': 'int',
            '浮点型': 'float',
            '双精度型': 'double',
            '字符型': 'char',
            '逻辑型': 'bool',
            '短整型': 'short',
            '长整型': 'long',
            '无类型': 'void'
        }

        type_str = token.value if token else 'int'
        c_type = type_map.get(type_str, type_str)

        self.advance()

        # 检查指针
        pointer_count = 0
        while self.check('*'):
            pointer_count += 1
            self.advance()

        return TypeNode(
            name=c_type,
            pointer_depth=pointer_count
        )

    def parse_expression(self) -> ASTNode:
        """
        解析表达式

        Returns:
            表达式节点
        """
        return self.parse_assignment()

    def parse_assignment(self) -> ASTNode:
        """
        解析赋值表达式

        Returns:
            赋值表达式节点
        """
        # 使用递归下降解析赋值表达式
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        """
        解析逻辑或表达式

        Returns:
            逻辑或节点
        """
        left = self.parse_and()

        while self.check('或者'):
            operator = self.advance().value
            right = self.parse_and()
            left = BinaryOpNode(
                operator=operator,
                left=left,
                right=right
            )

        return left

    def parse_and(self) -> ASTNode:
        """
        解析逻辑与表达式

        Returns:
            逻辑与节点
        """
        left = self.parse_equality()

        while self.check('并且'):
            operator = self.advance().value
            right = self.parse_equality()
            left = BinaryOpNode(
                operator=operator,
                left=left,
                right=right
            )

        return left

    def parse_equality(self) -> ASTNode:
        """
        解析相等性比较表达式

        Returns:
            相等性比较节点
        """
        left = self.parse_comparison()

        while self.check('==', '!=', '等于', '不等于'):
            operator = self.advance().value
            right = self.parse_comparison()
            left = BinaryOpNode(
                operator=operator,
                left=left,
                right=right
            )

        return left

    def parse_comparison(self) -> ASTNode:
        """
        解析比较表达式

        Returns:
            比较节点
        """
        left = self.parse_addition()

        while self.check('<', '>', '<=', '>=', '小于', '大于', '小于等于', '大于等于'):
            operator = self.advance().value
            right = self.parse_addition()
            left = BinaryOpNode(
                operator=operator,
                left=left,
                right=right
            )

        return left

    def parse_addition(self) -> ASTNode:
        """
        解析加减表达式

        Returns:
            加减节点
        """
        left = self.parse_multiplication()

        while self.check('+', '-', '加', '减'):
            operator = self.advance().value
            right = self.parse_multiplication()
            left = BinaryOpNode(
                operator=operator,
                left=left,
                right=right
            )

        return left

    def parse_multiplication(self) -> ASTNode:
        """
        解析乘除模表达式

        Returns:
            乘除模节点
        """
        left = self.parse_unary()

        while self.check('*', '/', '%', '乘', '除', '取模'):
            operator = self.advance().value
            right = self.parse_unary()
            left = BinaryOpNode(
                operator=operator,
                left=left,
                right=right
            )

        return left

    def parse_unary(self) -> ASTNode:
        """
        解析一元表达式

        Returns:
            一元节点
        """
        if self.check('-', '负'):
            operator = self.advance().value
            operand = self.parse_unary()
            return UnaryOpNode(operator=operator, operand=operand)

        if self.check('!', '非'):
            operator = self.advance().value
            operand = self.parse_unary()
            return UnaryOpNode(operator=operator, operand=operand)

        if self.check('+', '正'):
            operator = self.advance().value
            operand = self.parse_unary()
            return UnaryOpNode(operator=operator, operand=operand)

        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        """
        解析后缀表达式

        Returns:
            后缀节点
        """
        expr = self.parse_primary()

        while True:
            if self.check('['):
                # 数组下标访问
                self.advance()
                index = self.parse_expression()
                self.expect(']', "数组访问的结束")
                expr = IndexExprNode(array=expr, index=index)
            elif self.check('.'):
                # 结构体成员访问
                self.advance()
                member = self.expect('标识符', "成员名")
                expr = MemberExprNode(object=expr, member=member.value if member else 'unknown')
            elif self.check('('):
                # 函数调用
                self.advance()
                args = []
                while not self.check(')') and not self.is_at_end():
                    args.append(self.parse_expression())
                    if self.check(','):
                        self.advance()
                self.expect(')', "函数调用的结束")
                expr = CallExprNode(callee=expr, args=args)
            else:
                break

        return expr

    def parse_primary(self) -> ASTNode:
        """
        解析基本表达式

        Returns:
            基本表达式节点
        """
        token = self.current_token()

        # 数字字面量
        if self.check('数字', '整数', '浮点数'):
            value = self.advance().value
            return LiteralNode(type='number', value=value)

        # 字符串字面量
        if self.check('字符串'):
            value = self.advance().value
            return LiteralNode(type='string', value=value)

        # 字符字面量
        if self.check('字符'):
            value = self.advance().value
            return LiteralNode(type='char', value=value)

        # 标识符
        if self.check('标识符'):
            name = self.advance().value
            return IdentifierNode(name=name)

        # 括号表达式
        if self.check('('):
            self.advance()
            expr = self.parse_expression()
            self.expect(')', "括号表达式的结束")
            return expr

        # 真假值
        if self.check('真', 'true', 'True'):
            self.advance()
            return LiteralNode(type='bool', value=True)

        if self.check('假', 'false', 'False'):
            self.advance()
            return LiteralNode(type='bool', value=False)

        # 空值
        if self.check('空', 'null', 'NULL'):
            self.advance()
            return LiteralNode(type='null', value=None)

        # 跳过无效token
        self.advance()
        return LiteralNode(type='unknown', value=None)

    # ==================== 辅助方法 ====================

    def check(self, *types) -> bool:
        """
        检查当前token是否是给定类型之一

        Args:
            *types: token类型

        Returns:
            是否匹配
        """
        if self.is_at_end():
            return False

        token = self.current_token()
        token_value = token.value if token else None

        for t in types:
            if token.type == t or token_value == t:
                return True

        return False