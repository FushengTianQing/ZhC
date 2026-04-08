"""
AST 遍历工具函数

提供通用的 AST 节点查找和处理功能。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import List, Any, Optional, Dict, Set
from zhc.parser.ast_nodes import (
    ASTNodeType,
    VariableDeclNode,
    IdentifierExprNode,
    FunctionDeclNode,
    StructDeclNode,
)


def get_node_location(node: Any) -> Optional[Any]:
    """
    从 AST 节点获取位置信息

    Args:
        node: AST 节点

    Returns:
        SourceLocation 或 None
    """
    from zhc.analysis.base_analyzer import SourceLocation

    if hasattr(node, "location") and node.location:
        loc = node.location
        if isinstance(loc, SourceLocation):
            return loc
        elif isinstance(loc, tuple) and len(loc) >= 2:
            return SourceLocation(
                file_path=str(loc[0]) if len(loc) > 0 else "",
                line=int(loc[1]) if len(loc) > 1 else 0,
                column=int(loc[2]) if len(loc) > 2 else 0,
            )
    elif hasattr(node, "line") and hasattr(node, "column"):
        return SourceLocation(
            file_path=getattr(node, "source_file", getattr(node, "file_path", "")),
            line=int(node.line),
            column=int(node.column),
        )

    return None


def get_node_name(node: Any) -> str:
    """从 AST 节点获取名称"""
    if hasattr(node, "name"):
        return str(node.name)
    return node.__class__.__name__


def get_variable_name(node: Any) -> Optional[str]:
    """从变量声明或引用节点获取变量名"""
    if hasattr(node, "name"):
        return str(node.name)
    if hasattr(node, "identifier") and node.identifier:
        if hasattr(node.identifier, "name"):
            return str(node.identifier.name)
    return None


def find_all_nodes(
    ast: Any, node_type: Any = None, recursive: bool = True
) -> List[Any]:
    """
    查找所有指定类型的节点

    Args:
        ast: AST 根节点
        node_type: 节点类型（类或 ASTNodeType 枚举）
        recursive: 是否递归查找

    Returns:
        匹配节点的列表
    """
    results = []
    visited: Set[int] = set()  # 防止循环引用
    _walk_nodes(ast, results, node_type, recursive, visited)
    return results


def _walk_nodes(
    node: Any, results: List[Any], node_type: Any, recursive: bool, visited: Set[int]
) -> None:
    """递归遍历节点"""
    if node is None:
        return

    # 防止循环引用
    node_id = id(node)
    if node_id in visited:
        return
    visited.add(node_id)

    # 检查类型匹配
    if node_type is None:
        results.append(node)
    elif isinstance(node_type, type):
        if isinstance(node, node_type):
            results.append(node)
    elif hasattr(node, "node_type") and node.node_type == node_type:
        results.append(node)

    if not recursive:
        return

    # 遍历属性
    for attr_name in dir(node):
        if attr_name.startswith("_"):
            continue

        try:
            attr = getattr(node, attr_name)
        except (AttributeError, TypeError):
            continue

        if isinstance(attr, list):
            for child in attr:
                _walk_nodes(child, results, node_type, recursive, visited)
        elif isinstance(attr, dict):
            for child in attr.values():
                _walk_nodes(child, results, node_type, recursive, visited)
        elif hasattr(attr, "__dict__") and not isinstance(
            attr, (str, int, float, bool, type(None))
        ):
            _walk_nodes(attr, results, node_type, recursive, visited)


def find_variable_declarations(ast: Any) -> List[Any]:
    """查找所有变量声明"""
    return find_all_nodes(ast, VariableDeclNode)


def find_variable_references(ast: Any) -> List[Any]:
    """查找所有变量引用"""
    return find_all_nodes(ast, IdentifierExprNode)


def find_function_declarations(ast: Any) -> List[Any]:
    """查找所有函数声明"""
    return find_all_nodes(ast, FunctionDeclNode)


def find_struct_declarations(ast: Any) -> List[Any]:
    """查找所有结构体声明"""
    return find_all_nodes(ast, StructDeclNode)


def get_function_symbols(ast: Any) -> Dict[str, Dict[str, Any]]:
    """
    获取函数符号表

    Args:
        ast: AST 节点

    Returns:
        符号表字典 {函数名: {node, params, return_type, ...}}
    """
    symbols = {}

    for func in find_function_declarations(ast):
        func_name = get_variable_name(func) if hasattr(func, "name") else None
        if func_name:
            params = []
            if hasattr(func, "params"):
                for param in func.params:
                    param_info = {
                        "name": get_variable_name(param),
                        "type": getattr(param, "param_type", None),
                    }
                    params.append(param_info)

            symbols[func_name] = {
                "node": func,
                "name": func_name,
                "params": params,
                "return_type": getattr(func, "return_type", None),
                "location": get_node_location(func),
            }

    return symbols


def get_scope_variables(node: Any) -> Dict[str, Any]:
    """
    获取当前作用域中的变量

    Args:
        node: AST 节点

    Returns:
        变量字典
    """
    variables = {}

    # 向上遍历找最近的块
    current = node
    while current:
        # 检查块中的变量声明
        if hasattr(current, "statements"):
            for stmt in current.statements:
                if isinstance(stmt, VariableDeclNode):
                    var_name = get_variable_name(stmt)
                    if var_name:
                        variables[var_name] = stmt

        current = getattr(current, "parent", None)

    return variables


def has_return_statement(node: Any) -> bool:
    """检查节点是否包含 return 语句"""
    returns = find_all_nodes(node, ASTNodeType.RETURN)
    return len(returns) > 0


def get_function_depth(node: Any) -> int:
    """获取节点在函数中的嵌套深度"""
    depth = 0
    current = node

    while current:
        if getattr(current, "node_type", None) == ASTNodeType.FUNCTION_DECL:
            break
        if getattr(current, "node_type", None) in (
            ASTNodeType.IF,
            ASTNodeType.WHILE,
            ASTNodeType.FOR,
            ASTNodeType.FUNCTION_DECL,
        ):
            depth += 1
        current = getattr(current, "parent", None)

    return depth
