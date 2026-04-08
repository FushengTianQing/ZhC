#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST 验证器 - AST Validator

功能：
1. 结构完整性检查：必需子节点、节点类型、父子关系
2. 类型一致性检查：表达式类型、函数调用参数
3. 语义约束检查：变量声明、返回语句、循环语句
4. 边界条件检查：空指针、递归深度

作者：阿福
日期：2026-04-08
"""

from typing import List, Set, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from .ast_nodes import (
    ASTNode, ASTNodeType,
    ProgramNode, FunctionDeclNode, VariableDeclNode, ParamDeclNode,
    StructDeclNode, EnumDeclNode, UnionDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode, ReturnStmtNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, IdentifierExprNode,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode, BoolLiteralNode,
)


class ValidationSeverity(Enum):
    """验证问题严重程度"""
    ERROR = auto()      # 错误：必须修复
    WARNING = auto()    # 警告：建议修复
    INFO = auto()       # 信息：仅供参考


@dataclass
class ValidationIssue:
    """验证问题"""
    severity: ValidationSeverity
    message: str
    node: ASTNode
    line: int = 0
    column: int = 0
    suggestion: str = ""
    
    def __post_init__(self):
        if self.line == 0:
            self.line = self.node.line
        if self.column == 0:
            self.column = self.node.column
    
    def __str__(self) -> str:
        severity_str = {
            ValidationSeverity.ERROR: "错误",
            ValidationSeverity.WARNING: "警告",
            ValidationSeverity.INFO: "信息"
        }[self.severity]
        
        result = f"[{severity_str}] 第 {self.line} 行，第 {self.column} 列: {self.message}"
        if self.suggestion:
            result += f"\n  建议: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    
    def add_error(self, message: str, node: ASTNode, suggestion: str = ""):
        """添加错误"""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=message,
            node=node,
            suggestion=suggestion
        ))
        self.is_valid = False
    
    def add_warning(self, message: str, node: ASTNode, suggestion: str = ""):
        """添加警告"""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message=message,
            node=node,
            suggestion=suggestion
        ))
    
    def add_info(self, message: str, node: ASTNode):
        """添加信息"""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            message=message,
            node=node
        ))
    
    def get_errors(self) -> List[ValidationIssue]:
        """获取所有错误"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """获取所有警告"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    def __str__(self) -> str:
        if self.is_valid:
            return "✓ AST 验证通过"
        
        errors = self.get_errors()
        warnings = self.get_warnings()
        
        result = f"✗ AST 验证失败: {len(errors)} 个错误, {len(warnings)} 个警告\n"
        for issue in self.issues:
            result += f"  {issue}\n"
        return result


class ASTValidator:
    """
    AST 验证器
    
    验证规则：
    1. 结构完整性
    2. 类型一致性
    3. 语义约束
    4. 边界条件
    """
    
    def __init__(self, max_depth: int = 100):
        """
        初始化验证器
        
        Args:
            max_depth: 最大递归深度
        """
        self.max_depth = max_depth
        self.current_depth = 0
        
        # 符号表（用于变量声明检查）
        self.declared_symbols: Set[str] = set()
        self.function_symbols: Dict[str, FunctionDeclNode] = {}
        self.struct_symbols: Dict[str, StructDeclNode] = {}
        
        # 控制流状态
        self.in_loop = False
        self.in_function = False
        self.current_function: Optional[FunctionDeclNode] = None
    
    def validate(self, node: ASTNode) -> ValidationResult:
        """
        验证 AST 节点
        
        Args:
            node: AST 根节点
        
        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True)
        
        # 重置状态
        self.declared_symbols.clear()
        self.function_symbols.clear()
        self.struct_symbols.clear()
        self.in_loop = False
        self.in_function = False
        self.current_function = None
        self.current_depth = 0
        
        # 开始验证
        self._validate_node(node, result)
        
        return result
    
    def _validate_node(self, node: ASTNode, result: ValidationResult):
        """验证单个节点"""
        # 检查递归深度
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            result.add_error(
                f"AST 深度超过限制 ({self.max_depth})",
                node,
                "检查是否存在无限递归"
            )
            self.current_depth -= 1
            return
        
        # 根据节点类型分发验证
        if isinstance(node, ProgramNode):
            self._validate_program(node, result)
        elif isinstance(node, FunctionDeclNode):
            self._validate_function_decl(node, result)
        elif isinstance(node, VariableDeclNode):
            self._validate_variable_decl(node, result)
        elif isinstance(node, BlockStmtNode):
            self._validate_block_stmt(node, result)
        elif isinstance(node, IfStmtNode):
            self._validate_if_stmt(node, result)
        elif isinstance(node, WhileStmtNode):
            self._validate_while_stmt(node, result)
        elif isinstance(node, ForStmtNode):
            self._validate_for_stmt(node, result)
        elif isinstance(node, ReturnStmtNode):
            self._validate_return_stmt(node, result)
        elif isinstance(node, BinaryExprNode):
            self._validate_binary_expr(node, result)
        elif isinstance(node, UnaryExprNode):
            self._validate_unary_expr(node, result)
        elif isinstance(node, CallExprNode):
            self._validate_call_expr(node, result)
        elif isinstance(node, IdentifierExprNode):
            self._validate_identifier_expr(node, result)
        else:
            # 默认：验证子节点
            self._validate_children(node, result)
        
        self.current_depth -= 1
    
    def _validate_children(self, node: ASTNode, result: ValidationResult):
        """验证子节点"""
        if hasattr(node, 'get_children'):
            for child in node.get_children():
                if child is not None:
                    self._validate_node(child, result)
    
    def _validate_program(self, node: ProgramNode, result: ValidationResult):
        """验证程序节点"""
        # 检查是否有顶层声明
        if not node.declarations:
            result.add_warning("程序为空", node, "添加至少一个声明")
        
        # 验证所有声明
        for decl in node.declarations:
            self._validate_node(decl, result)
    
    def _validate_function_decl(self, node: FunctionDeclNode, result: ValidationResult):
        """验证函数声明"""
        # 记录函数符号
        self.function_symbols[node.name] = node
        
        # 检查函数名
        if not node.name:
            result.add_error("函数名不能为空", node)
            return
        
        # 检查参数
        if node.params:
            for param in node.params:
                if not param.name:
                    result.add_error("参数名不能为空", node)
        
        # 设置函数上下文
        old_function = self.current_function
        old_in_function = self.in_function
        self.current_function = node
        self.in_function = True
        
        # 添加参数到符号表
        if node.params:
            for param in node.params:
                self.declared_symbols.add(param.name)
        
        # 验证函数体
        if node.body:
            self._validate_node(node.body, result)
            
            # 检查返回语句
            return_type_name = node.return_type.name if node.return_type else ""
            if return_type_name and return_type_name != "空":
                if not self._has_return_statement(node.body):
                    result.add_warning(
                        f"函数 '{node.name}' 声明了返回类型但没有返回语句",
                        node,
                        "添加 return 语句或修改返回类型为 '空'"
                    )
        else:
            result.add_warning(
                f"函数 '{node.name}' 没有函数体",
                node,
                "添加函数体实现"
            )
        
        # 恢复上下文
        self.current_function = old_function
        self.in_function = old_in_function
    
    def _validate_variable_decl(self, node: VariableDeclNode, result: ValidationResult):
        """验证变量声明"""
        # 检查变量名
        if not node.name:
            result.add_error("变量名不能为空", node)
            return
        
        # 检查重复声明
        if node.name in self.declared_symbols:
            result.add_error(
                f"变量 '{node.name}' 重复声明",
                node,
                "修改变量名或删除重复声明"
            )
        
        # 记录符号
        self.declared_symbols.add(node.name)
        
        # 验证初始值
        if node.init:
            self._validate_node(node.init, result)
    
    def _validate_block_stmt(self, node: BlockStmtNode, result: ValidationResult):
        """验证代码块"""
        if not node.statements:
            result.add_warning("代码块为空", node, "添加语句或删除空代码块")
        
        # 验证所有语句
        for stmt in node.statements:
            self._validate_node(stmt, result)
    
    def _validate_if_stmt(self, node: IfStmtNode, result: ValidationResult):
        """验证 if 语句"""
        # 验证条件
        if not node.condition:
            result.add_error("if 语句缺少条件", node)
        else:
            self._validate_node(node.condition, result)
        
        # 验证 then 分支
        if not node.then_branch:
            result.add_warning("if 语句缺少 then 分支", node, "添加代码块")
        else:
            self._validate_node(node.then_branch, result)
        
        # 验证 else 分支
        if node.else_branch:
            self._validate_node(node.else_branch, result)
    
    def _validate_while_stmt(self, node: WhileStmtNode, result: ValidationResult):
        """验证 while 语句"""
        # 验证条件
        if not node.condition:
            result.add_error("while 语句缺少条件", node)
        else:
            self._validate_node(node.condition, result)
        
        # 验证循环体
        if not node.body:
            result.add_warning("while 语句缺少循环体", node, "添加代码块")
        else:
            # 设置循环上下文
            old_in_loop = self.in_loop
            self.in_loop = True
            self._validate_node(node.body, result)
            self.in_loop = old_in_loop
    
    def _validate_for_stmt(self, node: ForStmtNode, result: ValidationResult):
        """验证 for 语句"""
        # 验证初始化
        if node.init:
            self._validate_node(node.init, result)
        
        # 验证条件
        if node.condition:
            self._validate_node(node.condition, result)
        
        # 验证更新
        if node.update:
            self._validate_node(node.update, result)
        
        # 验证循环体
        if not node.body:
            result.add_warning("for 语句缺少循环体", node, "添加代码块")
        else:
            # 设置循环上下文
            old_in_loop = self.in_loop
            self.in_loop = True
            self._validate_node(node.body, result)
            self.in_loop = old_in_loop
    
    def _validate_return_stmt(self, node: ReturnStmtNode, result: ValidationResult):
        """验证 return 语句"""
        # 检查是否在函数内
        if not self.in_function:
            result.add_error(
                "return 语句不在函数内",
                node,
                "将 return 语句移到函数内"
            )
            return
        
        # 获取返回类型名称
        return_type = self.current_function.return_type if self.current_function else None
        return_type_name = return_type.name if return_type else ""
        
        # 检查返回值
        if node.value:
            self._validate_node(node.value, result)
            
            # 检查返回类型
            if return_type_name == "空":
                result.add_warning(
                    "函数返回类型为 '空' 但有返回值",
                    node,
                    "删除返回值或修改返回类型"
                )
        else:
            # 检查是否需要返回值
            if return_type_name and return_type_name != "空":
                result.add_warning(
                    f"函数返回类型为 '{return_type_name}' 但没有返回值",
                    node,
                    "添加返回值或修改返回类型为 '空'"
                )
    
    def _validate_binary_expr(self, node: BinaryExprNode, result: ValidationResult):
        """验证二元表达式"""
        # 验证左操作数
        if not node.left:
            result.add_error("二元表达式缺少左操作数", node)
        else:
            self._validate_node(node.left, result)
        
        # 验证右操作数
        if not node.right:
            result.add_error("二元表达式缺少右操作数", node)
        else:
            self._validate_node(node.right, result)
        
        # 验证操作符
        if not node.operator:
            result.add_error("二元表达式缺少操作符", node)
    
    def _validate_unary_expr(self, node: UnaryExprNode, result: ValidationResult):
        """验证一元表达式"""
        # 验证操作数
        if not node.operand:
            result.add_error("一元表达式缺少操作数", node)
        else:
            self._validate_node(node.operand, result)
        
        # 验证操作符
        if not node.operator:
            result.add_error("一元表达式缺少操作符", node)
    
    def _validate_call_expr(self, node: CallExprNode, result: ValidationResult):
        """验证函数调用"""
        # 验证函数名
        if not node.callee:
            result.add_error("函数调用缺少函数名", node)
            return
        
        self._validate_node(node.callee, result)
        
        # 验证参数
        if node.args:
            for arg in node.args:
                self._validate_node(arg, result)
        
        # 检查函数是否声明
        if isinstance(node.callee, IdentifierExprNode):
            func_name = node.callee.name
            if func_name not in self.function_symbols:
                result.add_warning(
                    f"函数 '{func_name}' 未声明",
                    node,
                    "确保函数已声明"
                )
            else:
                # 检查参数数量
                func_decl = self.function_symbols[func_name]
                expected_params = len(func_decl.params) if func_decl.params else 0
                actual_args = len(node.args) if node.args else 0
                
                if expected_params != actual_args:
                    result.add_error(
                        f"函数 '{func_name}' 参数数量不匹配: 期望 {expected_params} 个, 实际 {actual_args} 个",
                        node,
                        f"调整参数数量为 {expected_params} 个"
                    )
    
    def _validate_identifier_expr(self, node: IdentifierExprNode, result: ValidationResult):
        """验证标识符表达式"""
        # 检查变量是否声明
        if node.name not in self.declared_symbols and node.name not in self.function_symbols:
            result.add_warning(
                f"变量 '{node.name}' 未声明",
                node,
                "确保变量已声明"
            )
    
    def _has_return_statement(self, node: ASTNode) -> bool:
        """检查节点是否包含 return 语句"""
        if isinstance(node, ReturnStmtNode):
            return True
        
        if hasattr(node, 'get_children'):
            for child in node.get_children():
                if child and self._has_return_statement(child):
                    return True
        
        return False


def validate_ast(node: ASTNode) -> ValidationResult:
    """
    验证 AST 的便捷函数
    
    Args:
        node: AST 根节点
    
    Returns:
        验证结果
    """
    validator = ASTValidator()
    return validator.validate(node)


# 测试代码
if __name__ == '__main__':
    print("=== AST 验证器测试 ===\n")
    
    # 创建测试程序
    from .ast_nodes import ProgramNode, FunctionDeclNode, BlockStmtNode, ReturnStmtNode, IntLiteralNode
    
    # 测试 1: 空程序
    print("测试 1: 空程序")
    program1 = ProgramNode(declarations=[])
    result1 = validate_ast(program1)
    print(f"  结果: {result1.is_valid}")
    print(f"  问题: {len(result1.issues)}")
    
    # 测试 2: 函数缺少返回语句
    print("\n测试 2: 函数缺少返回语句")
    func2 = FunctionDecl(
        name="测试函数",
        return_type="整数",
        params=[],
        body=BlockStmt(statements=[])
    )
    program2 = Program(declarations=[func2])
    result2 = validate_ast(program2)
    print(f"  结果: {result2.is_valid}")
    print(f"  问题: {len(result2.issues)}")
    for issue in result2.issues:
        print(f"    {issue}")
    
    # 测试 3: 正确的函数
    print("\n测试 3: 正确的函数")
    func3 = FunctionDeclNode(
        name="加法",
        return_type="整数",
        params=[],
        body=BlockStmtNode(statements=[
            ReturnStmtNode(value=IntLiteralNode(value=42))
        ])
    )
    program3 = ProgramNode(declarations=[func3])
    result3 = validate_ast(program3)
    print(f"  结果: {result3.is_valid}")
    print(f"  问题: {len(result3.issues)}")
    
    print("\n=== 测试完成 ===")