"""
自动类型推导器
Auto Type Inference Module

实现自动类型推导功能（类似 C++ auto 关键字）：
- 变量类型自动推导
- 函数返回类型自动推导
- 表达式类型自动推导

作者: 阿福
日期: 2026-04-09
"""

from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass

from ..parser.ast_nodes import (
    ASTNode,
    ASTNodeType,
    VariableDeclNode,
    FunctionDeclNode,
    ReturnStmtNode,
    BlockStmtNode,
    AutoTypeNode,
    PrimitiveTypeNode,
    ArrayInitNode,
    BinaryExprNode,
    IdentifierExprNode,
)
from .engine import (
    Type,
    TypeVariable,
    BaseType,
    TypeEnv,
    TypeInferenceEngine,
    FunctionType,
    ArrayType,
)

if TYPE_CHECKING:
    from ..errors.base import ErrorHandler


@dataclass
class InferenceResult:
    """推导结果"""

    inferred_type: str  # 推导出的类型名称
    confidence: float = 1.0  # 置信度 (0-1)
    explanation: Optional[str] = None  # 推导说明


class AutoTypeInferencer:
    """
    自动类型推导器

    支持：
    1. 变量自动类型推导：`自动 x = 42;`
    2. 函数返回类型自动推导：`自动型 加(a, b) { 返回 a + b; }`
    3. 复杂表达式类型推导
    """

    # 中文类型名称到 C 类型名称的映射
    TYPE_NAME_MAP = {
        "整数型": "int",
        "浮点型": "float",
        "双精度浮点型": "double",
        "字符型": "char",
        "字符串型": "char*",
        "布尔型": "_Bool",
        "空型": "void",
    }

    def __init__(self, type_engine: Optional[TypeInferenceEngine] = None):
        self.type_engine = type_engine or TypeInferenceEngine()
        self.type_env = TypeEnv()
        self.error_handler: Optional["ErrorHandler"] = None

    def infer_variable_type(
        self, node: VariableDeclNode, source_location: Optional[str] = None
    ) -> InferenceResult:
        """
        推导变量类型

        Args:
            node: 变量声明节点
            source_location: 源代码位置（用于错误报告）

        Returns:
            InferenceResult: 包含推导结果的元组

        Raises:
            SemanticError: 无法推导类型时
        """
        if not node.is_auto:
            # 非自动类型，直接返回声明的类型
            return InferenceResult(
                inferred_type=self._get_type_name(node.var_type),
                confidence=1.0,
                explanation="显式类型声明",
            )

        if node.init is None:
            # 自动类型必须有初始化表达式
            return InferenceResult(
                inferred_type="未知",
                confidence=0.0,
                explanation="自动类型变量必须有初始化表达式",
            )

        # 推导初始化表达式的类型
        inferred = self._infer_expression_type(node.init)

        # 记录推导结果
        node.inferred_type = inferred.inferred_type

        return InferenceResult(
            inferred_type=inferred.inferred_type,
            confidence=inferred.confidence,
            explanation=f"从初始化表达式推导: {inferred.explanation}",
        )

    def infer_function_return_type(
        self, node: FunctionDeclNode, source_location: Optional[str] = None
    ) -> InferenceResult:
        """
        推导函数返回类型

        Args:
            node: 函数声明节点
            source_location: 源代码位置（用于错误报告）

        Returns:
            InferenceResult: 包含推导结果的元组

        Raises:
            SemanticError: 无法推导返回类型时
        """
        if not node.is_auto_return:
            # 非自动返回类型，直接返回声明的类型
            return InferenceResult(
                inferred_type=self._get_type_name(node.return_type),
                confidence=1.0,
                explanation="显式返回类型声明",
            )

        if node.body is None:
            return InferenceResult(
                inferred_type="空型",
                confidence=0.5,
                explanation="函数无函数体，无法推导返回类型",
            )

        # 收集所有返回语句的类型
        return_types: List[InferenceResult] = []
        for ret_node in self._find_return_statements(node.body):
            if ret_node.value is not None:
                inferred = self._infer_expression_type(ret_node.value)
                return_types.append(inferred)

        if not return_types:
            # 没有返回语句，返回 void
            node.return_type = PrimitiveTypeNode("空型")
            return InferenceResult(
                inferred_type="空型",
                confidence=0.8,
                explanation="函数无返回语句，推导为空型",
            )

        # 检查所有返回类型是否一致
        first_type = return_types[0].inferred_type
        all_same = all(r.inferred_type == first_type for r in return_types)

        if not all_same:
            # 类型不一致
            type_list = ", ".join(set(r.inferred_type for r in return_types))
            return InferenceResult(
                inferred_type="未知",
                confidence=0.0,
                explanation=f"返回类型不一致: {type_list}",
            )

        # 统一返回类型
        node.return_type = self._create_type_node(first_type)
        node.inferred_type = first_type

        return InferenceResult(
            inferred_type=first_type,
            confidence=1.0,
            explanation=f"从返回语句推导: {first_type}",
        )

    def _infer_expression_type(self, node: ASTNode) -> InferenceResult:
        """
        推导表达式类型

        Args:
            node: 表达式 AST 节点

        Returns:
            InferenceResult: 推导结果
        """
        nt = node.node_type

        # 字面量类型
        if nt == ASTNodeType.INT_LITERAL:
            return InferenceResult(
                inferred_type="整数型",
                confidence=1.0,
                explanation=f"整数字面量 {node.value}",
            )

        elif nt == ASTNodeType.FLOAT_LITERAL:
            return InferenceResult(
                inferred_type="浮点型",
                confidence=1.0,
                explanation=f"浮点字面量 {node.value}",
            )

        elif nt == ASTNodeType.STRING_LITERAL:
            return InferenceResult(
                inferred_type="字符串型",
                confidence=1.0,
                explanation="字符串字面量",
            )

        elif nt == ASTNodeType.CHAR_LITERAL:
            return InferenceResult(
                inferred_type="字符型",
                confidence=1.0,
                explanation=f"字符字面量 '{node.value}'",
            )

        elif nt == ASTNodeType.BOOL_LITERAL:
            return InferenceResult(
                inferred_type="布尔型",
                confidence=1.0,
                explanation=f"布尔字面量 {node.value}",
            )

        # 数组初始化
        elif nt == ASTNodeType.ARRAY_INIT:
            return self._infer_array_type(node)

        # 标识符
        elif nt == ASTNodeType.IDENTIFIER_EXPR:
            # 查找变量类型
            var_type = self.type_env.lookup(node.name)
            if var_type is not None:
                type_str = self._type_to_string(var_type)
                return InferenceResult(
                    inferred_type=type_str,
                    confidence=1.0,
                    explanation=f"变量 '{node.name}' 的类型",
                )
            # 如果类型环境没有，返回未知
            return InferenceResult(
                inferred_type="未知",
                confidence=0.0,
                explanation=f"变量 '{node.name}' 类型未知",
            )

        # 二元表达式
        elif nt == ASTNodeType.BINARY_EXPR:
            return self._infer_binary_type(node)

        # 一元表达式
        elif nt == ASTNodeType.UNARY_EXPR:
            return self._infer_unary_type(node)

        # 其他表达式，返回未知
        else:
            return InferenceResult(
                inferred_type="未知",
                confidence=0.5,
                explanation=f"无法推导 {nt.name} 类型",
            )

    def _infer_binary_type(self, node: BinaryExprNode) -> InferenceResult:
        """推导二元表达式类型"""
        left = self._infer_expression_type(node.left)
        right = self._infer_expression_type(node.right)
        operator = node.operator

        # 算术运算符
        if operator in ["+", "-", "*", "/"]:
            # 数值运算
            if "浮点型" in [left.inferred_type, right.inferred_type]:
                return InferenceResult(
                    inferred_type="浮点型",
                    confidence=0.9,
                    explanation=f"浮点运算: {left.inferred_type} {operator} {right.inferred_type}",
                )
            elif "整数型" in [left.inferred_type, right.inferred_type]:
                return InferenceResult(
                    inferred_type="整数型",
                    confidence=0.9,
                    explanation=f"整数运算: {left.inferred_type} {operator} {right.inferred_type}",
                )

        # 比较运算符
        elif operator in ["<", ">", "<=", ">=", "==", "!="]:
            return InferenceResult(
                inferred_type="布尔型",
                confidence=0.9,
                explanation=f"比较运算: {left.inferred_type} {operator} {right.inferred_type}",
            )

        # 逻辑运算符
        elif operator in ["并且", "或者"]:
            return InferenceResult(
                inferred_type="布尔型",
                confidence=0.9,
                explanation=f"逻辑运算: {left.inferred_type} {operator} {right.inferred_type}",
            )

        return InferenceResult(
            inferred_type="未知",
            confidence=0.5,
            explanation=f"未知运算符: {operator}",
        )

    def _infer_unary_type(self, node) -> InferenceResult:
        """推导一元表达式类型"""
        operand = self._infer_expression_type(node.operand)
        operator = node.operator

        if operator == "非":
            return InferenceResult(
                inferred_type="布尔型",
                confidence=0.9,
                explanation="逻辑非运算",
            )
        elif operator == "-":
            return InferenceResult(
                inferred_type=operand.inferred_type,
                confidence=0.9,
                explanation="负号运算",
            )

        return InferenceResult(
            inferred_type="未知",
            confidence=0.5,
            explanation=f"未知一元运算符: {operator}",
        )

    def _infer_array_type(self, node: ArrayInitNode) -> InferenceResult:
        """推导数组字面量类型"""
        if not node.elements:
            return InferenceResult(
                inferred_type="整数型[]",
                confidence=0.5,
                explanation="空数组默认为整数型数组",
            )

        # 推导第一个元素的类型作为数组元素类型
        first_elem_type = self._infer_expression_type(node.elements[0])
        size = len(node.elements)

        return InferenceResult(
            inferred_type=f"{first_elem_type.inferred_type}[{size}]",
            confidence=0.8,
            explanation=f"数组字面量，元素类型: {first_elem_type.inferred_type}, 长度: {size}",
        )

    def _find_return_statements(self, node: ASTNode) -> List[ReturnStmtNode]:
        """递归查找所有返回语句"""
        returns: List[ReturnStmtNode] = []

        if isinstance(node, ReturnStmtNode):
            returns.append(node)
        elif isinstance(node, BlockStmtNode):
            for stmt in node.statements:
                returns.extend(self._find_return_statements(stmt))
        elif hasattr(node, "body") and node.body is not None:
            returns.extend(self._find_return_statements(node.body))
        elif hasattr(node, "then_branch"):
            returns.extend(self._find_return_statements(node.then_branch))
            if hasattr(node, "else_branch") and node.else_branch is not None:
                returns.extend(self._find_return_statements(node.else_branch))
        elif hasattr(node, "statements"):
            for stmt in node.statements:
                returns.extend(self._find_return_statements(stmt))

        return returns

    def _get_type_name(self, type_node: ASTNode) -> str:
        """获取类型节点的类型名称"""
        if isinstance(type_node, PrimitiveTypeNode):
            return type_node.name
        elif isinstance(type_node, AutoTypeNode):
            return type_node.resolved_type or "自动"
        elif isinstance(type_node, IdentifierExprNode):
            return type_node.name
        else:
            return str(type_node)

    def _create_type_node(self, type_name: str) -> PrimitiveTypeNode:
        """根据类型名称创建类型节点"""
        return PrimitiveTypeNode(type_name)

    def _type_to_string(self, type_: Type) -> str:
        """将类型对象转换为字符串"""
        if isinstance(type_, BaseType):
            return type_.value
        elif isinstance(type_, ArrayType):
            return f"{self._type_to_string(type_.element_type)}[]"
        elif isinstance(type_, FunctionType):
            params = ", ".join(self._type_to_string(p) for p in type_.param_types)
            return f"({params}) -> {self._type_to_string(type_.return_type)}"
        elif isinstance(type_, TypeVariable):
            return f"未知(T{type_.id})"
        else:
            return str(type_)

    def register_variable(self, name: str, type_name: str) -> None:
        """注册变量到类型环境"""
        type_map = {
            "整数型": BaseType.INT,
            "浮点型": BaseType.FLOAT,
            "字符型": BaseType.CHAR,
            "字符串型": BaseType.STRING,
            "布尔型": BaseType.BOOL,
            "空型": BaseType.VOID,
        }
        type_ = type_map.get(type_name, BaseType.UNKNOWN)
        self.type_env = self.type_env.extend(name, type_)


def infer_auto_type(
    node: VariableDeclNode, source_location: Optional[str] = None
) -> str:
    """
    便捷函数：推导变量自动类型

    Args:
        node: 变量声明节点
        source_location: 源代码位置

    Returns:
        str: 推导出的类型名称
    """
    inferencer = AutoTypeInferencer()
    result = inferencer.infer_variable_type(node, source_location)
    return result.inferred_type


def infer_function_return(
    node: FunctionDeclNode, source_location: Optional[str] = None
) -> str:
    """
    便捷函数：推导函数返回类型

    Args:
        node: 函数声明节点
        source_location: 源代码位置

    Returns:
        str: 推导出的返回类型名称
    """
    inferencer = AutoTypeInferencer()
    result = inferencer.infer_function_return_type(node, source_location)
    return result.inferred_type
