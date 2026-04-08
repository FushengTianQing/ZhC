#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法分析包

作者: 阿福
日期: 2026-04-03

重构说明 (2026-04-03):
- parser.py 拆分为多个子模块
- declarations.py: 声明解析器
- statements.py: 语句解析器
- expressions.py: 表达式解析器
"""

from .lexer import Lexer, Token, TokenType, LexerError, tokenize
from .parser import Parser, parse
from zhc.errors import ParserError
from .ast_nodes import (
    # 基类
    ASTNode,
    ASTNodeType,
    ASTVisitor,
    # 程序结构
    ProgramNode,
    ModuleDeclNode,
    ImportDeclNode,
    # 声明
    FunctionDeclNode,
    StructDeclNode,
    VariableDeclNode,
    ParamDeclNode,
    EnumDeclNode,
    UnionDeclNode,
    TypedefDeclNode,
    # 语句
    BlockStmtNode,
    IfStmtNode,
    WhileStmtNode,
    ForStmtNode,
    DoWhileStmtNode,
    SwitchStmtNode,
    CaseStmtNode,
    DefaultStmtNode,
    GotoStmtNode,
    LabelStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
    ReturnStmtNode,
    ExprStmtNode,
    # 表达式
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
    TernaryExprNode,
    SizeofExprNode,
    CastExprNode,
    ArrayInitNode,
    StructInitNode,
    # 类型
    PrimitiveTypeNode,
    PointerTypeNode,
    ArrayTypeNode,
    FunctionTypeNode,
    StructTypeNode,
    # 工具
    ASTPrinter,
)

# 重构新增的子模块
from .declarations import DeclarationParserMixin
from .statements import StatementParserMixin
from .expressions import ExpressionParserMixin

__all__ = [
    # Lexer
    "Lexer",
    "Token",
    "TokenType",
    "LexerError",
    "tokenize",
    # Parser
    "Parser",
    "ParserError",
    "parse",
    # AST Nodes
    "ASTNode",
    "ASTNodeType",
    "ASTVisitor",
    "ProgramNode",
    "ModuleDeclNode",
    "ImportDeclNode",
    "FunctionDeclNode",
    "StructDeclNode",
    "VariableDeclNode",
    "ParamDeclNode",
    "EnumDeclNode",
    "UnionDeclNode",
    "TypedefDeclNode",
    "BlockStmtNode",
    "IfStmtNode",
    "WhileStmtNode",
    "ForStmtNode",
    "DoWhileStmtNode",
    "SwitchStmtNode",
    "CaseStmtNode",
    "DefaultStmtNode",
    "GotoStmtNode",
    "LabelStmtNode",
    "BreakStmtNode",
    "ContinueStmtNode",
    "ReturnStmtNode",
    "ExprStmtNode",
    "BinaryExprNode",
    "UnaryExprNode",
    "AssignExprNode",
    "CallExprNode",
    "MemberExprNode",
    "ArrayExprNode",
    "IdentifierExprNode",
    "IntLiteralNode",
    "FloatLiteralNode",
    "StringLiteralNode",
    "CharLiteralNode",
    "BoolLiteralNode",
    "NullLiteralNode",
    "TernaryExprNode",
    "SizeofExprNode",
    "CastExprNode",
    "ArrayInitNode",
    "StructInitNode",
    "PrimitiveTypeNode",
    "PointerTypeNode",
    "ArrayTypeNode",
    "FunctionTypeNode",
    "StructTypeNode",
    "ASTPrinter",
    # Parser Mixins (重构新增)
    "DeclarationParserMixin",
    "StatementParserMixin",
    "ExpressionParserMixin",
]
