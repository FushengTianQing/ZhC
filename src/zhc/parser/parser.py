#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法分析器 - Parser
将Token流转换为AST

作者: 阿福
日期: 2026-04-03
"""

from typing import List, Optional
from .lexer import Token, TokenType, Lexer
from .ast_nodes import *

# 导入统一异常类
from zhc.errors import (
    ParserError,
    SourceLocation,
    unexpected_token,
)

# 导入泛型解析混入类
from ..semantic.generic_parser import GenericParserMixin


class ErrorRecovery:
    """错误恢复管理器

    提供多种错误恢复策略：
    1. 同步恢复：跳到下一个语句边界
    2. 嵌套恢复：跟踪嵌套结构深度
    3. 恐慌恢复：跳过多余Token直到找到同步点
    4. 插入恢复：自动插入缺失Token
    """

    def __init__(self, parser: "Parser"):
        self.parser = parser
        self.brace_depth = 0  # 大括号深度
        self.paren_depth = 0  # 小括号深度
        self.bracket_depth = 0  # 中括号深度
        self.recovery_stats = {
            "synchronize": 0,  # 同步恢复次数
            "panic_skip": 0,  # 恐慌跳过Token数
            "brace_recover": 0,  # 大括号恢复次数
        }

    def enter_brace(self):
        """进入大括号"""
        self.brace_depth += 1

    def exit_brace(self):
        """退出大括号"""
        if self.brace_depth > 0:
            self.brace_depth -= 1

    def enter_paren(self):
        """进入小括号"""
        self.paren_depth += 1

    def exit_paren(self):
        """退出小括号"""
        if self.paren_depth > 0:
            self.paren_depth -= 1

    def enter_bracket(self):
        """进入中括号"""
        self.bracket_depth += 1

    def exit_bracket(self):
        """退出中括号"""
        if self.bracket_depth > 0:
            self.bracket_depth -= 1

    def is_balanced(self) -> bool:
        """检查嵌套结构是否平衡"""
        return (
            self.brace_depth == 0 and self.paren_depth == 0 and self.bracket_depth == 0
        )

    def skip_to_matching_brace(self):
        """跳到匹配的右大括号"""
        start_depth = self.brace_depth
        while not self.parser.is_at_end() and self.brace_depth >= start_depth:
            token = self.parser.current_token()
            if token.type == TokenType.LBRACE:
                self.brace_depth += 1
            elif token.type == TokenType.RBRACE:
                if self.brace_depth == start_depth:
                    break
                self.brace_depth -= 1
            self.parser.advance()
            self.recovery_stats["panic_skip"] += 1
        self.recovery_stats["brace_recover"] += 1

    def skip_to_matching_paren(self):
        """跳到匹配的右小括号"""
        start_depth = self.paren_depth
        while not self.parser.is_at_end() and self.paren_depth >= start_depth:
            token = self.parser.current_token()
            if token.type == TokenType.LPAREN:
                self.paren_depth += 1
            elif token.type == TokenType.RPAREN:
                if self.paren_depth == start_depth:
                    break
                self.paren_depth -= 1
            self.parser.advance()
            self.recovery_stats["panic_skip"] += 1

    def get_stats(self) -> dict:
        """获取恢复统计信息"""
        return self.recovery_stats.copy()


class Parser(GenericParserMixin):
    """语法分析器"""

    def __init__(self, tokens: List[Token]):
        """初始化语法分析器

        Args:
            tokens: Token列表
        """
        self.tokens = tokens
        self.pos = 0
        self.errors: List[ParserError] = []
        self.recovery = ErrorRecovery(self)  # 错误恢复管理器

        # 初始化泛型解析混入类
        GenericParserMixin.__init__(self)

    def current_token(self) -> Token:
        """获取当前Token"""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # 返回EOF
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Token:
        """查看偏移位置的Token"""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # 返回EOF
        return self.tokens[pos]

    def advance(self) -> Token:
        """前进一个Token"""
        token = self.current_token()
        if not self.is_at_end():
            self.pos += 1
        return token

    def is_at_end(self) -> bool:
        """是否到达文件末尾"""
        return self.current_token().type == TokenType.EOF

    def match(self, *types: TokenType) -> bool:
        """检查当前Token类型是否匹配（不消耗Token）"""
        return self.current_token().type in types

    def check(self, token_type: TokenType) -> bool:
        """检查当前Token类型是否匹配（不消耗Token）- 单类型版本"""
        return self.current_token().type == token_type

    def consume(self, *types: TokenType) -> bool:
        """检查并消耗Token（如果匹配）"""
        if self.match(*types):
            self.advance()
            return True
        return False

    def expect(self, token_type: TokenType, message: str) -> Token:
        """期望特定类型的Token"""
        if self.current_token().type == token_type:
            return self.advance()

        token = self.current_token()
        error = unexpected_token(
            token=token.value,
            location=SourceLocation(line=token.line, column=token.column),
            expected=[message],
        )
        self.errors.append(error)

        # 错误恢复：尝试跳过当前Token
        self.advance()
        return self.current_token()

    def _create_error(self, message: str) -> ParserError:
        """创建解析器错误（供 Mixin 使用）"""
        token = self.current_token()
        return ParserError(
            message=message,
            location=SourceLocation(line=token.line, column=token.column)
            if token
            else None,
        )

    def consume_if_match(self, token_type: TokenType) -> bool:
        """如果匹配则消耗Token"""
        if self.current_token().type == token_type:
            self.advance()
            return True
        return False

    def synchronize(self):
        """错误恢复：跳到下一个语句

        采用多级恢复策略：
        1. 首先尝试在分号处恢复（语句结束）
        2. 然后尝试在关键字处恢复（新语句开始）
        3. 最后尝试在嵌套结构边界处恢复

        同时跟踪嵌套深度，避免跨越结构边界
        """
        self.recovery.recovery_stats["synchronize"] += 1

        while not self.is_at_end():
            token = self.current_token()

            # 在分号处恢复（语句结束）
            if token.type == TokenType.SEMICOLON:
                self.advance()
                return

            # 在关键字处恢复（新语句开始）
            if token.type in (
                TokenType.FUNCTION,
                TokenType.STRUCT,
                TokenType.IF,
                TokenType.ELSE,
                TokenType.WHILE,
                TokenType.FOR,
                TokenType.RETURN,
                TokenType.BREAK,
                TokenType.CONTINUE,
                TokenType.INT,
                TokenType.FLOAT,
                TokenType.CHAR,
                TokenType.BOOL,
                TokenType.VOID,
                TokenType.STRING,
                TokenType.BYTE,
                TokenType.CONST,
                TokenType.DOUBLE,
                TokenType.BOOL_TYPE,
                TokenType.LONG,
                TokenType.SHORT,
                TokenType.UNSIGNED,
                TokenType.SIGNED,
                TokenType.MODULE,
                TokenType.IMPORT,
                TokenType.EXPORT,
                TokenType.PRIVATE,
                TokenType.DO,
                TokenType.SWITCH,
                TokenType.GOTO,
            ):
                return

            # 跟踪嵌套结构
            if token.type == TokenType.LBRACE:
                self.recovery.enter_brace()
            elif token.type == TokenType.RBRACE:
                # 如果嵌套深度为0，说明到达代码块边界
                if self.recovery.brace_depth == 0:
                    return
                self.recovery.exit_brace()
            elif token.type == TokenType.LPAREN:
                self.recovery.enter_paren()
            elif token.type == TokenType.RPAREN:
                if self.recovery.paren_depth == 0:
                    return  # 到达表达式边界
                self.recovery.exit_paren()
            elif token.type == TokenType.LBRACKET:
                self.recovery.enter_bracket()
            elif token.type == TokenType.RBRACKET:
                if self.recovery.bracket_depth == 0:
                    return  # 到达数组边界
                self.recovery.exit_bracket()

            self.advance()
            self.recovery.recovery_stats["panic_skip"] += 1

    def synchronize_to_brace(self):
        """恢复到匹配的右大括号

        用于函数体、结构体等嵌套结构的错误恢复
        """
        self.recovery.skip_to_matching_brace()

    def synchronize_to_paren(self):
        """恢复到匹配的右小括号

        用于参数列表、表达式等嵌套结构的错误恢复
        """
        self.recovery.skip_to_matching_paren()

    def safe_parse(self, parse_func, *args, **kwargs):
        """安全解析包装器

        包装解析函数，在出错时自动恢复并返回默认值

        Args:
            parse_func: 解析函数
            *args, **kwargs: 解析函数参数

        Returns:
            解析结果，出错时返回None
        """
        try:
            return parse_func(*args, **kwargs)
        except ParserError as e:
            self.errors.append(e)
            self.synchronize()
            return None

    # ========================================================================
    # 解析入口
    # ========================================================================

    def parse(self) -> ProgramNode:
        """解析程序"""
        declarations = []

        while not self.is_at_end():
            try:
                decl = self.parse_declaration()
                if decl:
                    declarations.append(decl)
            except ParserError as e:
                self.errors.append(e)
                self.synchronize()

        return ProgramNode(declarations)

    # ========================================================================
    # 声明解析
    # ========================================================================

    def parse_declaration(self) -> Optional[ASTNode]:
        """解析声明（dispatch table 分派）"""
        # --- 泛型声明 ---
        if self.match(TokenType.GENERIC_TYPE):
            return self.parse_generic_type_declaration()
        if self.match(TokenType.GENERIC_FUNC):
            return self.parse_generic_function_declaration()

        # --- 直接分派的 token ---
        if self.match(TokenType.MODULE):
            return self.parse_module_decl()
        if self.match(TokenType.IMPORT):
            return self.parse_import_decl()
        if self.match(TokenType.TYPEDEF):
            return self.parse_typedef_decl()
        if self.match(TokenType.CONST):
            return self.parse_const_decl()
        if self.match(TokenType.FUNCTION):
            return self.parse_function_decl()
        if self.match(TokenType.EXTERN):
            return self.parse_external_block()

        # --- 需要 lookahead 的 token ---
        if self.match(TokenType.STRUCT):
            return self._dispatch_struct_or_var()
        if self.match(TokenType.UNION):
            return self._dispatch_union_or_var()
        if self.match(TokenType.ENUM):
            return self._dispatch_enum_or_var()

        # --- 类型关键字：函数声明 vs 变量声明 ---
        if self.match(
            TokenType.INT,
            TokenType.FLOAT,
            TokenType.CHAR,
            TokenType.BOOL,
            TokenType.VOID,
            TokenType.STRING,
            TokenType.BYTE,
            TokenType.DOUBLE,
            TokenType.BOOL_TYPE,
            TokenType.LONG,
            TokenType.SHORT,
            TokenType.UNSIGNED,
            TokenType.SIGNED,
            TokenType.AUTO,  # 自动类型推导
        ):
            return self._dispatch_func_or_var()

        # 其他情况：表达式语句
        return self.parse_statement()

    # =========================================================================
    # parse_declaration 的 lookahead 分派辅助方法
    # =========================================================================

    def _dispatch_struct_or_var(self) -> Optional[ASTNode]:
        """STRUCT lookahead: 结构体定义 vs 变量声明"""
        next_tok = self.peek_token(1)
        next_next_tok = self.peek_token(2)
        if (
            next_tok.type == TokenType.IDENTIFIER
            and next_next_tok.type == TokenType.LBRACE
        ):
            return self.parse_struct_decl()
        return self.parse_variable_decl()

    def _dispatch_union_or_var(self) -> Optional[ASTNode]:
        """UNION lookahead: 共用体定义 vs 变量声明"""
        next_tok = self.peek_token(1)
        next_next_tok = self.peek_token(2)
        if (
            next_tok.type == TokenType.IDENTIFIER
            and next_next_tok.type == TokenType.LBRACE
        ):
            return self.parse_union_decl()
        return self.parse_variable_decl()

    def _dispatch_enum_or_var(self) -> Optional[ASTNode]:
        """ENUM lookahead: 枚举定义 / 枚举变量 / 匿名枚举"""
        next_tok = self.peek_token(1)
        if next_tok.type == TokenType.IDENTIFIER:
            next_next_tok = self.peek_token(2)
            if next_next_tok.type == TokenType.LBRACE:
                return self.parse_enum_decl()
            self.advance()
            return self.parse_variable_decl()
        elif next_tok.type == TokenType.LBRACE:
            return self.parse_enum_decl()
        else:
            self.advance()
            return self.parse_variable_decl()

    def _dispatch_func_or_var(self) -> Optional[ASTNode]:
        """类型关键字 lookahead: 函数声明 vs 变量声明"""
        if (
            self.peek_token().type == TokenType.IDENTIFIER
            and self.peek_token(2).type == TokenType.LPAREN
        ):
            return self.parse_function_decl_with_type()
        return self.parse_variable_decl()

    def parse_module_decl(self) -> ModuleDeclNode:
        """解析模块声明"""
        self.advance()  # 消耗 '模块'

        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望模块名")

        imports = []
        exports = []
        body = []

        # 解析导入
        while self.match(TokenType.IMPORT):
            imports.append(self.parse_import_decl())

        # 解析公开/私有声明
        while not self.is_at_end() and not self.match(TokenType.EOF):
            if self.match(TokenType.EXPORT):
                self.advance()
                exports.append(self.current_token().value)
                decl = self.parse_declaration()
                if decl:
                    body.append(decl)
            elif self.match(TokenType.PRIVATE):
                self.advance()
                decl = self.parse_declaration()
                if decl:
                    body.append(decl)
            else:
                decl = self.parse_declaration()
                if decl:
                    body.append(decl)

        return ModuleDeclNode(
            name, exports, imports, body, self.tokens[0].line, self.tokens[0].column
        )

    def parse_import_decl(self) -> ImportDeclNode:
        """解析导入声明"""
        self.advance()  # 消耗 '导入'

        module_name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望模块名")

        symbols = None
        if self.match(TokenType.LPAREN):
            self.advance()  # 消耗 '('
            symbols = []
            while not self.match(TokenType.RPAREN) and not self.is_at_end():
                symbols.append(self.current_token().value)
                self.expect(TokenType.IDENTIFIER, "期望标识符")
                if self.match(TokenType.COMMA):
                    self.advance()
            self.expect(TokenType.RPAREN, "期望 ')'")

        return ImportDeclNode(
            module_name,
            symbols,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_function_decl(self) -> FunctionDeclNode:
        """解析函数声明（使用'函数'关键字的旧语法）"""
        self.advance()  # 消耗 '函数'

        # 解析返回类型
        return_type = self.parse_type()

        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望函数名")

        # 参数列表
        self.expect(TokenType.LPAREN, "期望 '('")
        params = []
        if not self.match(TokenType.RPAREN):
            params.append(self.parse_param_decl())
            while self.match(TokenType.COMMA):
                self.advance()
                params.append(self.parse_param_decl())
        self.expect(TokenType.RPAREN, "期望 ')'")

        # 函数体
        body = None
        if self.match(TokenType.LBRACE):
            body = self.parse_block()

        return FunctionDeclNode(
            name,
            return_type,
            params,
            body,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_function_decl_with_type(self) -> FunctionDeclNode:
        """解析函数声明（新语法：类型 函数名(参数)）

        增强错误恢复：参数列表解析出错时正确恢复
        """
        # 解析返回类型
        return_type = self.parse_type()

        # 函数名
        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望函数名")

        # 参数列表（带错误恢复）
        params = []
        if self.expect(TokenType.LPAREN, "期望 '('"):
            self.recovery.enter_paren()

            if not self.match(TokenType.RPAREN):
                # 解析参数列表
                while True:
                    try:
                        params.append(self.parse_param_decl())
                        if self.match(TokenType.COMMA):
                            self.advance()
                        elif self.match(TokenType.RPAREN):
                            break
                        else:
                            # 意外的Token，尝试恢复
                            self.errors.append(
                                ParserError(
                                    f"期望 ',' 或 ')'，但找到 '{self.current_token().value}'",
                                    self.current_token(),
                                )
                            )
                            # 跳过Token继续解析
                            self.advance()
                            self.recovery.recovery_stats["panic_skip"] += 1
                            if self.match(TokenType.RPAREN):
                                break
                    except ParserError as e:
                        self.errors.append(e)
                        # 尝试跳到下一个参数或右括号
                        while (
                            not self.match(TokenType.COMMA, TokenType.RPAREN)
                            and not self.is_at_end()
                        ):
                            self.advance()
                            self.recovery.recovery_stats["panic_skip"] += 1
                        if self.match(TokenType.COMMA):
                            self.advance()
                        elif self.match(TokenType.RPAREN):
                            break

            self.expect(TokenType.RPAREN, "期望 ')'")
            self.recovery.exit_paren()

        # 函数体
        body = None
        if self.match(TokenType.LBRACE):
            body = self.parse_block()

        return FunctionDeclNode(
            name,
            return_type,
            params,
            body,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_external_block(self) -> ExternalBlockNode:
        """
        解析外部块

        语法：
            外部 "C" {
                函数声明1;
                函数声明2;
            }
        """
        start_line = self.current_token().line
        start_column = self.current_token().column

        # 消耗 '外部'
        self.advance()

        # 解析语言字符串
        language_token = self.current_token()
        if language_token.type != TokenType.STRING_LITERAL:
            self.errors.append(
                ParserError(
                    f"期望外部语言字符串，但找到 '{language_token.value}'",
                    language_token,
                )
            )
            language = "C"  # 默认使用 C
        else:
            language = language_token.value.strip('"')
            self.advance()

        # 目前只支持 "C"
        if language != "C":
            self.errors.append(
                ParserError(
                    f"不支持的外部语言: {language}，目前仅支持 C",
                    language_token,
                )
            )

        # 解析 '{'
        self.expect(TokenType.LBRACE, "期望 '{'")

        # 解析函数声明列表
        declarations = []
        while not self.match(TokenType.RBRACE) and not self.is_at_end():
            decl = self.parse_external_function_decl()
            if decl:
                declarations.append(decl)

        # 解析 '}'
        self.expect(TokenType.RBRACE, "期望 '}'")

        return ExternalBlockNode(
            language=language,
            declarations=declarations,
            line=start_line,
            column=start_column,
        )

    def parse_external_function_decl(self) -> Optional[ExternalFunctionDeclNode]:
        """
        解析外部函数声明

        语法：返回类型 函数名(参数列表);
        """
        start_line = self.current_token().line
        start_column = self.current_token().column

        # 解析返回类型
        return_type = self.parse_type()

        # 解析函数名
        name_token = self.current_token()
        if name_token.type != TokenType.IDENTIFIER:
            self.errors.append(
                ParserError(
                    f"期望函数名，但找到 '{name_token.value}'",
                    name_token,
                )
            )
            # 尝试恢复：跳到下一个分号
            while not self.match(TokenType.SEMICOLON) and not self.is_at_end():
                self.advance()
            if self.match(TokenType.SEMICOLON):
                self.advance()
            return None

        name = name_token.value
        self.advance()

        # 解析参数列表
        self.expect(TokenType.LPAREN, "期望 '('")

        parameters = []
        if not self.match(TokenType.RPAREN):
            parameters.append(self.parse_param_decl())
            while self.match(TokenType.COMMA):
                self.advance()
                parameters.append(self.parse_param_decl())

        self.expect(TokenType.RPAREN, "期望 ')'")

        # 解析 ';'
        self.expect(TokenType.SEMICOLON, "期望 ';'")

        return ExternalFunctionDeclNode(
            name=name,
            return_type=return_type,
            parameters=parameters,
            line=start_line,
            column=start_column,
        )

    def parse_struct_decl(self) -> StructDeclNode:
        """解析结构体声明"""
        self.advance()  # 消耗 '结构体'

        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望结构体名")

        self.expect(TokenType.LBRACE, "期望 '{'")

        members = []
        while not self.match(TokenType.RBRACE) and not self.is_at_end():
            members.append(self.parse_variable_decl())

        self.expect(TokenType.RBRACE, "期望 '}'")

        # 消费可选的 ';'（C风格: } 或 }; 均合法）
        if self.match(TokenType.SEMICOLON):
            self.advance()

        return StructDeclNode(
            name,
            members,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_union_decl(self) -> UnionDeclNode:
        """解析共用体声明：共用体 名字 { 成员... }"""
        self.advance()  # 消耗 '共用体'

        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望共用体名")

        self.expect(TokenType.LBRACE, "期望 '{'")

        members = []
        while not self.match(TokenType.RBRACE) and not self.is_at_end():
            members.append(self.parse_variable_decl())

        self.expect(TokenType.RBRACE, "期望 '}'")

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return UnionDeclNode(
            name,
            members,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_enum_decl(self) -> EnumDeclNode:
        """解析枚举声明：枚举 名字 { A, B, C } 或 匿名枚举 { A, B, C }"""
        self.advance()  # 消耗 '枚举'

        name = None
        # 检查是否有命名
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value

        self.expect(TokenType.LBRACE, "期望 '{'")

        values = []
        while not self.match(TokenType.RBRACE) and not self.is_at_end():
            val_name = self.current_token().value
            self.expect(TokenType.IDENTIFIER, "期望枚举值名称")

            val_expr = None
            if self.match(TokenType.ASSIGN):
                self.advance()
                val_expr = self.parse_expression()

            values.append((val_name, val_expr))

            # 逗号分隔
            if self.match(TokenType.COMMA):
                self.advance()

        self.expect(TokenType.RBRACE, "期望 '}'")

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return EnumDeclNode(
            name,
            values,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_typedef_decl(self) -> TypedefDeclNode:
        """解析别名声明：别名 类型 新名字;"""
        self.advance()  # 消耗 '别名'

        old_type = self.parse_type()

        new_name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望别名名称")

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return TypedefDeclNode(
            old_type,
            new_name,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_variable_decl(self) -> VariableDeclNode:
        """解析变量声明（包括函数指针变量）"""
        var_type = self.parse_type()

        # 检查是否是函数指针声明: 类型 (*名字)(参数列表)
        fp_result = self.try_parse_function_pointer(var_type)
        if fp_result is not None:
            name, var_type = fp_result

            # 初始化（函数指针可以有初始值）
            init = None
            if self.match(TokenType.ASSIGN):
                self.advance()
                if self.match(TokenType.LBRACE):
                    init = self.parse_init_list()
                else:
                    init = self.parse_expression()

            if self.match(TokenType.SEMICOLON):
                self.advance()

            return VariableDeclNode(
                name,
                var_type,
                init,
                False,
                self.tokens[self.pos - 1].line,
                self.tokens[self.pos - 1].column,
            )

        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望变量名")

        # 数组大小
        if self.match(TokenType.LBRACKET):
            self.advance()
            if not self.match(TokenType.RBRACKET):
                size = self.parse_expression()
            else:
                size = None
            self.expect(TokenType.RBRACKET, "期望 ']'")
            var_type = ArrayTypeNode(var_type, size)

        # 初始化
        init = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            # 检查是否是初始化列表 {1, 2, 3}
            if self.match(TokenType.LBRACE):
                init = self.parse_init_list()
            else:
                init = self.parse_expression()

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return VariableDeclNode(
            name,
            var_type,
            init,
            False,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_const_decl(self) -> VariableDeclNode:
        """解析常量声明"""
        self.advance()  # 消耗 '常量'

        var_type = self.parse_type()

        name = self.current_token().value
        self.expect(TokenType.IDENTIFIER, "期望常量名")

        # 初始化
        self.expect(TokenType.ASSIGN, "常量必须有初始值")
        init = self.parse_expression()

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return VariableDeclNode(
            name,
            var_type,
            init,
            True,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_param_decl(self) -> ParamDeclNode:
        """解析参数声明（包括函数指针参数）"""
        param_type = self.parse_type()

        # 检查是否是函数指针参数: 类型 (*名字)(参数列表)
        fp_result = self.try_parse_function_pointer(param_type)
        if fp_result is not None:
            name, param_type = fp_result
        else:
            name = self.current_token().value
            self.expect(TokenType.IDENTIFIER, "期望参数名")

        # 数组参数
        if self.match(TokenType.LBRACKET):
            self.advance()
            self.expect(TokenType.RBRACKET, "期望 ']'")
            param_type = ArrayTypeNode(param_type, None)

        # 默认值
        default_value = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            default_value = self.parse_expression()

        return ParamDeclNode(
            name,
            param_type,
            default_value,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    # ========================================================================
    # 语句解析
    # ========================================================================

    def parse_statement(self) -> Optional[ASTNode]:
        """解析语句"""
        # 代码块
        if self.match(TokenType.LBRACE):
            return self.parse_block()

        # 如果语句
        if self.match(TokenType.IF):
            return self.parse_if_stmt()

        # 当循环
        if self.match(TokenType.WHILE):
            return self.parse_while_stmt()

        # 循环语句
        if self.match(TokenType.FOR):
            return self.parse_for_stmt()

        # Phase 6 T1.3: 执行-当循环
        if self.match(TokenType.DO):
            return self.parse_do_while_stmt()

        # Phase 6 T1.3: 选择语句
        if self.match(TokenType.SWITCH):
            return self.parse_switch_stmt()

        # 跳出语句
        if self.match(TokenType.BREAK):
            return self.parse_break_stmt()

        # 继续语句
        if self.match(TokenType.CONTINUE):
            return self.parse_continue_stmt()

        # 返回语句
        if self.match(TokenType.RETURN):
            return self.parse_return_stmt()

        # Phase 6 T1.3: 去向语句
        if self.match(TokenType.GOTO):
            return self.parse_goto_stmt()

        # Phase 6 T1.3: 标签检测（标识符 + 冒号）
        if (
            self.match(TokenType.IDENTIFIER)
            and not self.is_at_end()
            and self.peek_token().type == TokenType.COLON
        ):
            label_token = self.current_token()
            self.advance()  # 消耗标识符
            self.advance()  # 消耗 ':'
            stmt = self.parse_statement()
            return LabelStmtNode(
                label_token.value, stmt, label_token.line, label_token.column
            )

        # 表达式语句
        return self.parse_expr_stmt()

    def parse_block(self) -> BlockStmtNode:
        """解析代码块

        增强错误恢复：跟踪嵌套深度，出错时跳到匹配的右大括号
        """
        self.advance()  # 消耗 '{'
        self.recovery.enter_brace()  # 跟踪嵌套深度

        statements = []
        while not self.match(TokenType.RBRACE) and not self.is_at_end():
            try:
                stmt = self.parse_declaration()
                if stmt:
                    statements.append(stmt)
            except ParserError as e:
                self.errors.append(e)
                # 在代码块内使用增强恢复
                self.synchronize()

        self.expect(TokenType.RBRACE, "期望 '}'")
        self.recovery.exit_brace()  # 退出嵌套

        return BlockStmtNode(
            statements, self.tokens[self.pos - 1].line, self.tokens[self.pos - 1].column
        )

    def parse_if_stmt(self) -> IfStmtNode:
        """解析如果语句"""
        self.advance()  # 消耗 '如果'

        self.expect(TokenType.LPAREN, "期望 '('")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "期望 ')'")

        then_branch = self.parse_statement()

        else_branch = None
        if self.match(TokenType.ELSE):
            self.advance()
            else_branch = self.parse_statement()

        return IfStmtNode(
            condition,
            then_branch,
            else_branch,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_while_stmt(self) -> WhileStmtNode:
        """解析当循环"""
        self.advance()  # 消耗 '当'

        self.expect(TokenType.LPAREN, "期望 '('")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "期望 ')'")

        body = self.parse_statement()

        return WhileStmtNode(
            condition,
            body,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_for_stmt(self) -> ForStmtNode:
        """解析循环语句"""
        self.advance()  # 消耗 '循环'

        self.expect(TokenType.LPAREN, "期望 '('")

        # 初始化
        init = None
        if not self.match(TokenType.SEMICOLON):
            init = self.parse_variable_decl()
        else:
            self.advance()

        # 条件
        condition = None
        if not self.match(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "期望 ';'")

        # 更新
        update = None
        if not self.match(TokenType.RPAREN):
            update = self.parse_expression()
        self.expect(TokenType.RPAREN, "期望 ')'")

        body = self.parse_statement()

        return ForStmtNode(
            init,
            condition,
            update,
            body,
            self.tokens[self.pos - 1].line,
            self.tokens[self.pos - 1].column,
        )

    def parse_break_stmt(self) -> BreakStmtNode:
        """解析跳出语句"""
        self.advance()  # 消耗 '跳出'

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return BreakStmtNode(
            self.tokens[self.pos - 1].line, self.tokens[self.pos - 1].column
        )

    def parse_continue_stmt(self) -> ContinueStmtNode:
        """解析继续语句"""
        self.advance()  # 消耗 '继续'

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return ContinueStmtNode(
            self.tokens[self.pos - 1].line, self.tokens[self.pos - 1].column
        )

    def parse_return_stmt(self) -> ReturnStmtNode:
        """解析返回语句"""
        self.advance()  # 消耗 '返回'

        value = None
        if not self.match(TokenType.SEMICOLON):
            value = self.parse_expression()

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return ReturnStmtNode(
            value, self.tokens[self.pos - 1].line, self.tokens[self.pos - 1].column
        )

    # ===== Phase 6 T1.3: 新增语句解析方法 =====

    def parse_do_while_stmt(self) -> DoWhileStmtNode:
        """解析执行-当循环语句"""
        do_token = self.current_token()
        self.advance()  # 消耗 '执行'

        # 循环体
        if self.match(TokenType.LBRACE):
            body = self.parse_block()
        else:
            body = self.parse_statement()

        # 期望 '当'
        if self.match(TokenType.WHILE):
            self.advance()
        else:
            self.errors.append(
                ParserError("执行-当循环缺少 '当' 关键字", do_token, "ERROR")
            )
            self.synchronize()
            return DoWhileStmtNode(
                body, IntLiteralNode(1), do_token.line, do_token.column
            )

        # 期望 '('
        self.expect(TokenType.LPAREN, "期望 '('")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "期望 ')'")

        # 期望 ';'
        if self.match(TokenType.SEMICOLON):
            self.advance()

        return DoWhileStmtNode(body, condition, do_token.line, do_token.column)

    def parse_switch_stmt(self) -> SwitchStmtNode:
        """解析选择语句"""
        switch_token = self.current_token()
        self.advance()  # 消耗 '选择'

        # 期望 '('
        self.expect(TokenType.LPAREN, "期望 '('")
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN, "期望 ')'")

        # 期望 '{'
        self.expect(TokenType.LBRACE, "期望 '{'")
        self.recovery.enter_brace()

        cases = []
        while not self.match(TokenType.RBRACE) and not self.is_at_end():
            if self.match(TokenType.CASE):
                cases.append(self.parse_case_stmt())
            elif self.match(TokenType.DEFAULT):
                cases.append(self.parse_default_stmt())
            elif self.match(TokenType.SEMICOLON):
                self.advance()  # 跳过多余分号
            else:
                # 未知 token，尝试恢复
                self.errors.append(
                    ParserError(
                        f"选择语句中意外的Token: '{self.current_token().value}'",
                        self.current_token(),
                        "ERROR",
                    )
                )
                self.synchronize()

        # 期望 '}'
        if self.match(TokenType.RBRACE):
            self.advance()
            self.recovery.exit_brace()

        return SwitchStmtNode(expr, cases, switch_token.line, switch_token.column)

    def parse_case_stmt(self) -> CaseStmtNode:
        """解析情况语句

        支持两种语法：
        1. 单值 case: 分支 1:
        2. 范围 case: 分支 1...5:
        """
        case_token = self.current_token()
        self.advance()  # 消耗 '情况'

        # 期望常量表达式
        value = self.parse_expression()

        # 检查是否为范围 case
        end_value = None
        if self.match(TokenType.ELLIPSIS):
            self.advance()  # 消耗 '...'
            end_value = self.parse_expression()

        # 期望 ':'
        self.expect(TokenType.COLON, "期望 ':'")

        # 收集语句直到下一个情况/默认/右大括号
        statements = []
        while (
            not self.is_at_end()
            and not self.match(TokenType.CASE)
            and not self.match(TokenType.DEFAULT)
            and not self.match(TokenType.RBRACE)
        ):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return CaseStmtNode(
            value, statements, case_token.line, case_token.column, end_value
        )

    def parse_default_stmt(self) -> DefaultStmtNode:
        """解析默认语句"""
        default_token = self.current_token()
        self.advance()  # 消耗 '默认'

        # 期望 ':'
        self.expect(TokenType.COLON, "期望 ':'")

        # 收集语句直到情况/右大括号
        statements = []
        while (
            not self.is_at_end()
            and not self.match(TokenType.CASE)
            and not self.match(TokenType.DEFAULT)
            and not self.match(TokenType.RBRACE)
        ):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return DefaultStmtNode(statements, default_token.line, default_token.column)

    def parse_goto_stmt(self) -> GotoStmtNode:
        """解析去向语句"""
        goto_token = self.current_token()
        self.advance()  # 消耗 '去向'

        # 期望标识符（标签名）
        label_token = self.current_token()
        self.expect(TokenType.IDENTIFIER, "期望标签名")

        # 期望 ';'
        if self.match(TokenType.SEMICOLON):
            self.advance()

        return GotoStmtNode(label_token.value, goto_token.line, goto_token.column)

    def parse_expr_stmt(self) -> ExprStmtNode:
        """解析表达式语句"""
        expr = self.parse_expression()

        if self.match(TokenType.SEMICOLON):
            self.advance()

        return ExprStmtNode(
            expr, self.tokens[self.pos - 1].line, self.tokens[self.pos - 1].column
        )

    # ========================================================================
    # 类型解析
    # ========================================================================

    def parse_type(self) -> ASTNode:
        """解析类型"""
        # 函数指针类型: 返回类型 (*名字)(参数列表)
        # 注意: parse_variable_decl 会消费函数指针中的名字部分
        # 这里只处理无名的函数指针类型: 返回类型 (*)()
        # 完整的函数指针声明在 parse_function_pointer_decl() 中处理

        # 基本类型
        if self.match(
            TokenType.INT,
            TokenType.FLOAT,
            TokenType.CHAR,
            TokenType.BOOL,
            TokenType.VOID,
            TokenType.STRING,
            TokenType.BYTE,
            TokenType.DOUBLE,
            TokenType.BOOL_TYPE,
            TokenType.LONG,
            TokenType.SHORT,
            TokenType.UNSIGNED,
            TokenType.SIGNED,
        ):
            token = self.advance()
            type_node = PrimitiveTypeNode(token.value, token.line, token.column)
        elif self.match(TokenType.AUTO):
            # 自动类型推导
            token = self.advance()
            type_node = AutoTypeNode(token.line, token.column)
        elif self.match(TokenType.STRUCT):
            self.advance()
            name = self.current_token().value
            self.expect(TokenType.IDENTIFIER, "期望结构体名")
            type_node = StructTypeNode(name)
        elif self.match(TokenType.ENUM):
            self.advance()
            if self.match(TokenType.IDENTIFIER):
                name = self.advance().value
                type_node = StructTypeNode(name)  # 枚举类型作为命名类型处理
            else:
                token = self.current_token()
                self.errors.append(ParserError("期望枚举类型名", token))
                type_node = PrimitiveTypeNode("整数型")
        elif self.match(TokenType.IDENTIFIER):
            # 可能是自定义类型（typedef或结构体）
            name = self.advance().value
            type_node = StructTypeNode(name)  # 暂时作为结构体类型处理
        else:
            # 未知的类型，返回空类型并记录错误
            token = self.current_token()
            self.errors.append(ParserError(f"未知的类型: '{token.value}'", token))
            type_node = PrimitiveTypeNode("空型")

        # 指针（支持多级指针）
        while self.match(TokenType.STAR):
            self.advance()
            type_node = PointerTypeNode(type_node)

        return type_node

    def try_parse_function_pointer(
        self, base_type: ASTNode
    ) -> Optional[Tuple[str, ASTNode]]:
        """尝试解析函数指针声明: 基础类型 (*名字)(参数列表)

        在 parse_type() 返回后调用，检查当前 token 是否为 '('，
        如果是则检查是否为函数指针模式 (*名字)(...)。

        Args:
            base_type: 已解析的基础类型（如 整数型）

        Returns:
            如果是函数指针: (名字, PointerTypeNode(FunctionTypeNode(...)))
            如果不是: None
        """
        # 检查是否是 (*名字) 模式
        if not self.match(TokenType.LPAREN):
            return None

        # 保存位置以便回退
        saved_pos = self.pos

        # 尝试: ( * 名字 )
        if self.peek_token(1).type == TokenType.STAR:
            self.advance()  # 消耗 '('
            self.advance()  # 消耗 '*'

            if self.match(TokenType.IDENTIFIER):
                name = self.advance().value

                if self.match(TokenType.RPAREN):
                    self.advance()  # 消耗 ')'

                    # 检查是否有参数列表 (...)
                    if self.match(TokenType.LPAREN):
                        self.advance()  # 消耗 '('

                        # 解析参数类型列表（支持可选参数名，如 整数型 a, 整数型 b）
                        param_types = []
                        while not self.match(TokenType.RPAREN) and not self.is_at_end():
                            param_types.append(self.parse_type())
                            # 用户可能写了参数名，静默跳过（不影响语义）
                            if self.match(TokenType.IDENTIFIER):
                                self.advance()
                            if self.match(TokenType.COMMA):
                                self.advance()

                        self.expect(TokenType.RPAREN, "期望 ')' 结束函数指针参数列表")

                        # 构造 FunctionTypeNode 并包装为指针
                        func_type = FunctionTypeNode(
                            return_type=base_type,
                            param_types=param_types,
                        )
                        ptr_type = PointerTypeNode(func_type)

                        return (name, ptr_type)
                    else:
                        # 没有 (...)，不是函数指针，回退
                        self.pos = saved_pos
                        return None
                else:
                    self.pos = saved_pos
                    return None
            else:
                self.pos = saved_pos
                return None
        else:
            # 不是 (*...) 模式，回退
            return None

    def parse_init_list(self) -> ASTNode:
        """解析初始化列表 {1, 2, 3} 或 {.x = 1, .y = 2}"""
        self.expect(TokenType.LBRACE, "期望 '{'")
        elements = []

        while not self.match(TokenType.RBRACE) and self.pos < len(self.tokens):
            # 检查是否是指定字段初始化 .field = value
            if self.match(TokenType.DOT):
                # 暂时按简单表达式处理
                elements.append(self.parse_expression())
            else:
                elements.append(self.parse_expression())

            if self.match(TokenType.COMMA):
                self.advance()

        self.expect(TokenType.RBRACE, "期望 '}'")
        return ArrayInitNode(elements)

    # ========================================================================
    # 表达式解析
    # ========================================================================

    def parse_expression(self) -> ASTNode:
        """解析表达式"""
        return self.parse_assignment()

    def parse_assignment(self) -> ASTNode:
        """解析赋值表达式"""
        expr = self.parse_or()

        # 赋值运算符
        if self.match(
            TokenType.ASSIGN,
            TokenType.PLUS_ASSIGN,
            TokenType.MINUS_ASSIGN,
            TokenType.STAR_ASSIGN,
            TokenType.SLASH_ASSIGN,
            TokenType.PERCENT_ASSIGN,
        ):
            operator = self.advance().value
            value = self.parse_assignment()
            return AssignExprNode(expr, value, operator, expr.line, expr.column)

        return expr

    def parse_or(self) -> ASTNode:
        """解析或表达式"""
        left = self.parse_and()

        while self.match(TokenType.OR):
            operator = self.advance().value
            right = self.parse_and()
            left = BinaryExprNode(operator, left, right, left.line, left.column)

        return left

    def parse_and(self) -> ASTNode:
        """解析与表达式"""
        left = self.parse_equality()

        while self.match(TokenType.AND):
            operator = self.advance().value
            right = self.parse_equality()
            left = BinaryExprNode(operator, left, right, left.line, left.column)

        return left

    def parse_equality(self) -> ASTNode:
        """解析相等性表达式"""
        left = self.parse_comparison()

        while self.match(TokenType.EQ, TokenType.NE):
            operator = self.advance().value
            right = self.parse_comparison()
            left = BinaryExprNode(operator, left, right, left.line, left.column)

        return left

    def parse_comparison(self) -> ASTNode:
        """解析比较表达式"""
        left = self.parse_addition()

        while self.match(TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            operator = self.advance().value
            right = self.parse_addition()
            left = BinaryExprNode(operator, left, right, left.line, left.column)

        return left

    def parse_addition(self) -> ASTNode:
        """解析加减表达式"""
        left = self.parse_multiplication()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.advance().value
            right = self.parse_multiplication()
            left = BinaryExprNode(operator, left, right, left.line, left.column)

        return left

    def parse_multiplication(self) -> ASTNode:
        """解析乘除表达式"""
        left = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self.advance().value
            right = self.parse_unary()
            left = BinaryExprNode(operator, left, right, left.line, left.column)

        return left

    def parse_unary(self) -> ASTNode:
        """解析一元表达式"""
        # 前缀运算符
        if self.match(
            TokenType.MINUS,
            TokenType.NOT,
            TokenType.BIT_NOT,
            TokenType.INCREMENT,
            TokenType.DECREMENT,
            TokenType.BIT_AND,
            TokenType.STAR,
        ):
            operator = self.advance().value
            operand = self.parse_unary()
            return UnaryExprNode(
                operator,
                operand,
                True,
                self.tokens[self.pos - 1].line,
                self.tokens[self.pos - 1].column,
            )

        # 后缀运算符
        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        """解析后缀表达式"""
        expr = self.parse_primary()

        while True:
            # 函数调用
            if self.match(TokenType.LPAREN):
                self.advance()
                args = []
                if not self.match(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN, "期望 ')'")
                expr = CallExprNode(expr, args, expr.line, expr.column)

            # 成员访问
            elif self.match(TokenType.DOT, TokenType.ARROW):
                operator = self.advance().value
                member = self.current_token().value
                self.expect(TokenType.IDENTIFIER, "期望成员名")
                expr = MemberExprNode(expr, member, expr.line, expr.column)

            # 数组访问
            elif self.match(TokenType.LBRACKET):
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "期望 ']'")
                expr = ArrayExprNode(expr, index, expr.line, expr.column)

            # 后缀自增/自减
            elif self.match(TokenType.INCREMENT, TokenType.DECREMENT):
                operator = self.advance().value
                expr = UnaryExprNode(operator, expr, False, expr.line, expr.column)

            else:
                break

        return expr

    def parse_primary(self) -> ASTNode:
        """解析基本表达式

        增强错误恢复：意外Token时尝试恢复到表达式边界
        """
        token = self.current_token()

        # 整数字面量
        if self.match(TokenType.INT_LITERAL):
            self.advance()
            return IntLiteralNode(int(token.value), token.line, token.column)

        # 浮点字面量
        if self.match(TokenType.FLOAT_LITERAL):
            self.advance()
            return FloatLiteralNode(float(token.value), token.line, token.column)

        # 字符串字面量
        if self.match(TokenType.STRING_LITERAL):
            self.advance()
            return StringLiteralNode(token.value, token.line, token.column)

        # 宽字符字面量
        if self.match(TokenType.WIDE_CHAR_LITERAL):
            self.advance()
            return WideCharLiteralNode(
                chr(token.value), token.value, token.line, token.column
            )

        # 宽字符串字面量
        if self.match(TokenType.WIDE_STRING_LITERAL):
            self.advance()
            return WideStringLiteralNode(
                "".join(chr(cp) for cp in token.value),
                token.value,
                token.line,
                token.column,
            )

        # 布尔字面量
        if self.match(TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return BoolLiteralNode(
                token.type == TokenType.TRUE, token.line, token.column
            )

        # 空字面量
        if self.match(TokenType.NULL):
            self.advance()
            return NullLiteralNode(token.line, token.column)

        # 标识符
        if self.match(TokenType.IDENTIFIER):
            self.advance()
            return IdentifierExprNode(token.value, token.line, token.column)

        # 括号表达式
        if self.match(TokenType.LPAREN):
            self.advance()
            self.recovery.enter_paren()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "期望 ')'")
            self.recovery.exit_paren()
            return expr

        # 错误恢复：尝试跳到表达式边界
        error = ParserError(f"意外的Token: '{token.value}'", token)
        self.errors.append(error)

        # 智能恢复：跳到可能的表达式结束点
        self.recovery.recovery_stats["panic_skip"] += 1
        self.advance()

        # 返回一个空节点而不是None，避免上层代码崩溃
        return NullLiteralNode(token.line, token.column)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def get_errors(self) -> List[ParserError]:
        """获取错误列表"""
        return self.errors

    def report(self) -> str:
        """生成分析报告

        包含：Token数量、错误列表、恢复统计
        """
        lines = [
            "=" * 70,
            "语法分析报告",
            "=" * 70,
            "",
            f"Token数量: {len(self.tokens)}",
            f"错误数量: {len(self.errors)}",
            "",
        ]

        if self.errors:
            lines.append("错误列表:")
            lines.append("-" * 70)
            for error in self.errors:
                error_prefix = "✗"
                if hasattr(error, "error_level"):
                    if error.error_level == "WARNING":
                        error_prefix = "⚠"
                    elif error.error_level == "INFO":
                        error_prefix = "ℹ"
                lines.append(f"  {error_prefix} {error}")
            lines.append("")

        # 添加恢复统计
        stats = self.recovery.get_stats()
        if any(stats.values()):
            lines.append("错误恢复统计:")
            lines.append("-" * 70)
            lines.append(f"  同步恢复次数: {stats['synchronize']}")
            lines.append(f"  恐慌跳过Token数: {stats['panic_skip']}")
            lines.append(f"  大括号恢复次数: {stats['brace_recover']}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)


def parse(source: str) -> tuple:
    """解析源代码

    Args:
        source: 源代码字符串

    Returns:
        (AST, 错误列表)
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    errors = lexer.get_errors() + parser.get_errors()

    return ast, errors


if __name__ == "__main__":
    # 测试示例
    test_code = """
    整数型 主函数() {
        整数型 计数 = 0;
        浮点型 数值 = 3.14;

        如果 (计数 < 10) {
            计数 += 1;
        } 否则 {
            计数 -= 1;
        }

        返回 0;
    }
    """

    ast, errors = parse(test_code)

    print("=" * 70)
    print("AST结构")
    print("=" * 70)

    printer = ASTPrinter()
    ast.accept(printer)

    print("\n" + "=" * 70)
    print("错误信息")
    print("=" * 70)

    for error in errors:
        print(f"✗ {error}")
