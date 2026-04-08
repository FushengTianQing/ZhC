#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
声明解析器 - Declaration Parser

功能：
- 模块声明解析
- 导入语句解析
- 函数声明解析
- 结构体声明解析
- 变量声明解析
- 常量声明解析
- 参数声明解析

作者：远
日期：2026-04-03

重构说明：
- 从parser.py分离声明解析相关功能
- 单一职责原则
"""

from typing import Optional
from .ast_nodes import (
    ModuleDeclNode,
    ImportDeclNode,
    FunctionDeclNode,
    StructDeclNode,
    VariableDeclNode,
    ParamDeclNode,
    ASTNode,
)


class DeclarationParserMixin:
    """
    声明解析混入类

    提供声明解析的方法，供Parser类组合使用
    """

    def parse_declaration(self) -> Optional[ASTNode]:
        """
        解析声明

        Returns:
            声明节点，如果遇到错误返回None
        """
        # 同步机制
        if self.current_token() is None:
            return None

        token = self.current_token()

        # 根据token类型选择解析方法
        if self.match_module_keyword(token):
            return self.parse_module_decl()
        elif self.match_import_keyword(token):
            return self.parse_import_decl()
        elif self.match_function_keyword(token):
            return self.parse_function_decl()
        elif self.match_struct_keyword(token):
            return self.parse_struct_decl()
        elif self.match_variable_keyword(token):
            return self.parse_variable_decl()
        elif self.match_const_keyword(token):
            return self.parse_const_decl()
        else:
            # 尝试作为语句解析
            return self.parse_statement()

    def parse_module_decl(self) -> ModuleDeclNode:
        """
        解析模块声明

        语法：模块 模块名 { ... }

        Returns:
            模块声明节点
        """
        # 跳过'模块'关键字
        self.advance()

        # 获取模块名
        module_name_token = self.expect("标识符", "模块名")
        module_name = module_name_token.value if module_name_token else "anonymous"

        # 期望左花括号
        self.expect("{", "模块声明的开始")

        # 解析模块体
        public_declarations = []
        private_declarations = []

        current_section = "private"

        while not self.is_at_end() and not self.check("}"):
            # 检查可见性标记
            if self.check("公开"):
                current_section = "public"
                self.advance()
                continue
            elif self.check("私有"):
                current_section = "private"
                self.advance()
                continue

            # 解析声明
            declaration = self.parse_declaration()
            if declaration:
                if current_section == "public":
                    public_declarations.append(declaration)
                else:
                    private_declarations.append(declaration)

        # 期望右花括号
        self.expect("}", "模块声明的结束")

        return ModuleDeclNode(
            name=module_name,
            public_declarations=public_declarations,
            private_declarations=private_declarations,
        )

    def parse_import_decl(self) -> ImportDeclNode:
        """
        解析导入语句

        语法：导入 模块名

        Returns:
            导入声明节点
        """
        # 跳过'导入'关键字
        self.advance()

        # 获取模块名
        module_name_token = self.expect("标识符", "导入的模块名")
        module_name = module_name_token.value if module_name_token else "unknown"

        return ImportDeclNode(module_name=module_name)

    def parse_function_decl(self) -> FunctionDeclNode:
        """
        解析函数声明

        语法：函数 返回类型 函数名(参数列表) -> 返回类型 { ... }

        Returns:
            函数声明节点
        """
        # 跳过'函数'关键字
        self.advance()

        # 获取返回类型
        return_type = self.parse_type()

        # 获取函数名
        func_name_token = self.expect("标识符", "函数名")
        func_name = func_name_token.value if func_name_token else "anonymous"

        # 期望左括号
        self.expect("(", "参数列表的开始")

        # 解析参数列表
        params = []
        while not self.check(")") and not self.is_at_end():
            param = self.parse_param_decl()
            if param:
                params.append(param)

            # 检查逗号
            if self.check(","):
                self.advance()
            else:
                break

        # 期望右括号
        self.expect(")", "参数列表的结束")

        # 检查返回类型标注
        if self.check("->"):
            self.advance()
            return_type = self.parse_type()

        # 解析函数体
        body = self.parse_block()

        return FunctionDeclNode(
            name=func_name, return_type=return_type, params=params, body=body
        )

    def parse_function_decl_with_type(self) -> FunctionDeclNode:
        """
        解析带类型的函数声明

        语法：函数 返回类型 函数名(参数列表) { ... }

        Returns:
            函数声明节点
        """
        return self.parse_function_decl()

    def parse_struct_decl(self) -> StructDeclNode:
        """
        解析结构体声明

        语法：结构体 结构体名 { 成员声明... }

        Returns:
            结构体声明节点
        """
        # 跳过'结构体'关键字
        self.advance()

        # 获取结构体名
        struct_name_token = self.expect("标识符", "结构体名")
        struct_name = struct_name_token.value if struct_name_token else "anonymous"

        # 期望左花括号
        self.expect("{", "结构体定义的开始")

        # 解析成员
        members = []
        while not self.check("}") and not self.is_at_end():
            member = self.parse_variable_decl()
            if member:
                members.append(member)

        # 期望右花括号
        self.expect("}", "结构体定义的结束")

        return StructDeclNode(name=struct_name, members=members)

    def parse_variable_decl(self) -> VariableDeclNode:
        """
        解析变量声明

        语法：类型 变量名;

        Returns:
            变量声明节点
        """
        # 获取变量类型
        var_type = self.parse_type()

        # 获取变量名
        var_name_token = self.expect("标识符", "变量名")
        var_name = var_name_token.value if var_name_token else "anonymous"

        # 检查初始化
        initial_value = None
        if self.check("="):
            self.advance()
            initial_value = self.parse_expression()

        # 期望分号
        self.expect(";", "变量声明的结束")

        return VariableDeclNode(
            name=var_name, var_type=var_type, initial_value=initial_value
        )

    def parse_const_decl(self) -> VariableDeclNode:
        """
        解析常量声明

        语法：常量 类型 常量名 = 值;

        Returns:
            常量声明节点
        """
        # 跳过'常量'关键字
        self.advance()

        # 获取常量类型
        const_type = self.parse_type()

        # 获取常量名
        const_name_token = self.expect("标识符", "常量名")
        const_name = const_name_token.value if const_name_token else "anonymous"

        # 期望等号
        self.expect("=", "常量初始化的开始")

        # 获取值
        const_value = self.parse_expression()

        # 期望分号
        self.expect(";", "常量声明的结束")

        return VariableDeclNode(
            name=const_name,
            var_type=const_type,
            initial_value=const_value,
            is_const=True,
        )

    def parse_param_decl(self) -> ParamDeclNode:
        """
        解析参数声明

        语法：类型 参数名

        Returns:
            参数声明节点
        """
        # 获取参数类型
        param_type = self.parse_type()

        # 获取参数名
        param_name_token = self.expect("标识符", "参数名")
        param_name = param_name_token.value if param_name_token else "anonymous"

        return ParamDeclNode(name=param_name, param_type=param_type)

    # ==================== 辅助方法 ====================

    def match_module_keyword(self, token) -> bool:
        """检查是否是模块关键字"""
        return token and token.type == "MODULE"

    def match_import_keyword(self, token) -> bool:
        """检查是否是导入关键字"""
        return token and token.type == "IMPORT"

    def match_function_keyword(self, token) -> bool:
        """检查是否是函数关键字"""
        return token and token.type == "FUNCTION"

    def match_struct_keyword(self, token) -> bool:
        """检查是否是结构体关键字"""
        return token and token.type == "STRUCT"

    def match_variable_keyword(self, token) -> bool:
        """检查是否是变量关键字"""
        return token and token.type in ["INT", "FLOAT", "CHAR", "DOUBLE", "VOID"]

    def match_const_keyword(self, token) -> bool:
        """检查是否是常量关键字"""
        return token and token.type == "CONST"
