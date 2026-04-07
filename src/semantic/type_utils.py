"""
AST 类型节点 → TypeInfo 转换工具
Phase 5 T2.1

桥接 AST 节点体系（PrimitiveTypeNode 等）与 TypeChecker 的 TypeInfo 体系。
"""

from typing import Optional

from ..parser.ast_nodes import (
    ASTNode, ASTNodeType,
    PrimitiveTypeNode, PointerTypeNode, ArrayTypeNode, FunctionTypeNode,
)
from ..analyzer.type_checker import TypeChecker, TypeInfo


# 模块级单例（TypeInfo 是纯数据，TypeChecker 初始化成本极低）
_tc = TypeChecker()


def ast_type_to_typeinfo(node: ASTNode) -> Optional[TypeInfo]:
    """将 AST 类型节点转换为 TypeInfo

    Args:
        node: AST 类型节点（PrimitiveTypeNode / PointerTypeNode / ArrayTypeNode / FunctionTypeNode）

    Returns:
        TypeInfo 对象，如果无法转换则返回 None
    """
    if node is None:
        return None

    nt = node.node_type

    if nt == ASTNodeType.PRIMITIVE_TYPE:
        # PrimitiveTypeNode.name 是中文名如 "整数型"
        return _tc.get_type(node.name)

    elif nt == ASTNodeType.POINTER_TYPE:
        # PointerTypeNode.base_type 是基础类型节点
        if not hasattr(node, 'base_type') or node.base_type is None:
            return None
        base = ast_type_to_typeinfo(node.base_type)
        if base is None:
            return None
        return _tc.create_pointer_type(base)

    elif nt == ASTNodeType.ARRAY_TYPE:
        # ArrayTypeNode.element_type 是元素类型，size 是可选的 ASTNode
        if not hasattr(node, 'element_type') or node.element_type is None:
            return None
        base = ast_type_to_typeinfo(node.element_type)
        if base is None:
            return None
        # size 可能是 ASTNode（表达式）或 None
        size_val = None
        if hasattr(node, 'size') and node.size is not None:
            if isinstance(node.size, int):
                size_val = node.size
            elif hasattr(node.size, 'value'):
                size_val = node.size.value
        return _tc.create_array_type(base, size_val)

    elif nt == ASTNodeType.FUNCTION_TYPE:
        # FunctionTypeNode: return_type + param_types
        ret = None
        if hasattr(node, 'return_type') and node.return_type:
            ret = ast_type_to_typeinfo(node.return_type)
        params = []
        if hasattr(node, 'param_types') and node.param_types:
            for p in node.param_types:
                pt = ast_type_to_typeinfo(p)
                if pt:
                    params.append(pt)
        if ret:
            return _tc.create_function_type(ret, params)
        return None

    return None


def type_name_to_typeinfo(name: str) -> Optional[TypeInfo]:
    """通过中文名获取 TypeInfo

    Args:
        name: 中文类型名，如 "整数型"、"浮点型"

    Returns:
        TypeInfo 对象，如果类型不存在则返回 None
    """
    return _tc.get_type(name)


def get_type_checker() -> TypeChecker:
    """获取模块级 TypeChecker 单例"""
    return _tc
