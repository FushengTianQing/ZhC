#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语句解析器 - Statement Parser

功能：
- 块语句解析
- if语句解析
- while语句解析
- for语句解析
- break语句解析
- continue语句解析
- return语句解析
- 表达式语句解析

作者：远
日期：2026-04-03

重构说明：
- 从parser.py分离语句解析相关功能
- 单一职责原则
"""

from typing import Optional
from .ast_nodes import (
    BlockStmtNode,
    IfStmtNode,
    WhileStmtNode,
    ForStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
    ReturnStmtNode,
    ExprStmtNode,
    ASTNode,
)


class StatementParserMixin:
    """
    语句解析混入类

    提供语句解析的方法，供Parser类组合使用
    """

    def parse_statement(self) -> Optional[ASTNode]:
        """
        解析语句

        Returns:
            语句节点
        """
        # 空语句
        if self.check(";"):
            self.advance()
            return None

        # 块语句
        if self.check("{"):
            return self.parse_block()

        # if语句
        if self.check("如果"):
            return self.parse_if_stmt()

        # while语句
        if self.check("当"):
            return self.parse_while_stmt()

        # for语句
        if self.check("循环"):
            return self.parse_for_stmt()

        # break语句
        if self.check("跳出"):
            return self.parse_break_stmt()

        # continue语句
        if self.check("继续"):
            return self.parse_continue_stmt()

        # return语句
        if self.check("返回"):
            return self.parse_return_stmt()

        # 默认作为表达式语句解析
        return self.parse_expr_stmt()

    def parse_block(self) -> BlockStmtNode:
        """
        解析块语句

        语法：{ 语句... }

        Returns:
            块语句节点
        """
        # 期望左花括号
        self.expect("{", "块的开始")

        # 解析语句列表
        statements = []
        while not self.check("}") and not self.is_at_end():
            statement = self.parse_statement()
            if statement:
                statements.append(statement)

        # 期望右花括号
        self.expect("}", "块的结束")

        return BlockStmtNode(statements=statements)

    def parse_if_stmt(self) -> IfStmtNode:
        """
        解析if语句

        语法：如果 条件 { then_body } 否则 { else_body }

        Returns:
            if语句节点
        """
        # 跳过'如果'关键字
        self.advance()

        # 解析条件
        condition = self.parse_expression()

        # 解析then分支
        then_body = self.parse_block()

        # 检查else分支
        else_body = None
        if self.check("否则"):
            self.advance()
            else_body = self.parse_block()

        return IfStmtNode(condition=condition, then_body=then_body, else_body=else_body)

    def parse_while_stmt(self) -> WhileStmtNode:
        """
        解析while语句

        语法：当 条件 { body }

        Returns:
            while语句节点
        """
        # 跳过'当'关键字
        self.advance()

        # 解析条件
        condition = self.parse_expression()

        # 解析循环体
        body = self.parse_block()

        return WhileStmtNode(condition=condition, body=body)

    def parse_for_stmt(self) -> ForStmtNode:
        """
        解析for语句

        语法：循环 初始化; 条件; 更新 { body }

        Returns:
            for语句节点
        """
        # 跳过'循环'关键字
        self.advance()

        # 解析初始化
        init = None
        if not self.check(";"):
            init = self.parse_expression()
        self.expect(";", "for初始化后的分号")

        # 解析条件
        condition = None
        if not self.check(";"):
            condition = self.parse_expression()
        self.expect(";", "for条件后的分号")

        # 解析更新
        update = None
        if not self.check("{"):
            update = self.parse_expression()

        # 解析循环体
        body = self.parse_block()

        return ForStmtNode(init=init, condition=condition, update=update, body=body)

    def parse_break_stmt(self) -> BreakStmtNode:
        """
        解析break语句

        语法：跳出;

        Returns:
            break语句节点
        """
        # 跳过'跳出'关键字
        self.advance()

        # 期望分号
        self.expect(";", "break语句后的分号")

        return BreakStmtNode()

    def parse_continue_stmt(self) -> ContinueStmtNode:
        """
        解析continue语句

        语法：继续;

        Returns:
            continue语句节点
        """
        # 跳过'继续'关键字
        self.advance()

        # 期望分号
        self.expect(";", "continue语句后的分号")

        return ContinueStmtNode()

    def parse_return_stmt(self) -> ReturnStmtNode:
        """
        解析return语句

        语法：返回 表达式;

        Returns:
            return语句节点
        """
        # 跳过'返回'关键字
        self.advance()

        # 解析返回值
        value = None
        if not self.check(";"):
            value = self.parse_expression()

        # 期望分号
        self.expect(";", "return语句后的分号")

        return ReturnStmtNode(value=value)

    def parse_expr_stmt(self) -> ExprStmtNode:
        """
        解析表达式语句

        语法：表达式;

        Returns:
            表达式语句节点
        """
        # 解析表达式
        expression = self.parse_expression()

        # 期望分号
        self.expect(";", "表达式语句后的分号")

        return ExprStmtNode(expression=expression)
