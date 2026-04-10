# -*- coding: utf-8 -*-
"""
ZHC IR - AST → IR 生成器

将 AST 转换为 ZHC IR。

使用 ASTVisitor 模式遍历 AST，生成 IR 指令。

设计原则：
- 非严格 SSA：变量可多次赋值，用 ALLOC + STORE 代替 phi 节点
- 表达式求值：结果存储在临时寄存器（%tempN）中
- 基本块：控制流语句（if/while/for）创建新基本块

作者：远
日期：2026-04-03
"""

from typing import Optional, List, Any, Dict

from zhc.parser.ast_nodes import (
    ASTVisitor,
    ASTNode,
    ProgramNode,
    ModuleDeclNode,
    ImportDeclNode,
    FunctionDeclNode,
    StructDeclNode,
    VariableDeclNode,
    ParamDeclNode,
    EnumDeclNode,
    UnionDeclNode,
    TypedefDeclNode,
    BlockStmtNode,
    IfStmtNode,
    WhileStmtNode,
    ForStmtNode,
    DoWhileStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
    ReturnStmtNode,
    SwitchStmtNode,
    CaseStmtNode,
    DefaultStmtNode,
    ExprStmtNode,
    GotoStmtNode,
    LabelStmtNode,
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
    LambdaExprNode,
    ArrayInitNode,
    StructInitNode,
    PrimitiveTypeNode,
    PointerTypeNode,
    ArrayTypeNode,
    FunctionTypeNode,
    StructTypeNode,
    TryStmtNode,
    CatchClauseNode,
    FinallyClauseNode,
    ThrowStmtNode,
    CoroutineDefNode,
    AwaitExprNode,
    ChannelExprNode,
    SpawnExprNode,
    YieldExprNode,
)

from zhc.ir.program import IRProgram, IRFunction, IRStructDef, IRGlobalVar
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.values import IRValue, ValueKind
from zhc.ir.opcodes import Opcode


class IRGenerator(ASTVisitor):
    """
    AST → IR 生成器

    Attributes:
        module: IRProgram - 生成的 IR 程序
        current_function: 当前正在处理的函数
        current_block: 当前基本块
        temp_counter: 临时变量计数器
        _bb_counter: 基本块计数器
        _label_counter: 标签计数器
        _break_targets: break 跳转目标栈（用于嵌套循环）
        _continue_targets: continue 跳转目标栈（用于嵌套循环）
        _in_switch: 是否在 switch 语句内
        _switch_cases: switch 的 case 值->目标基本块
    """

    def __init__(self, symbol_table=None):
        self.module = IRProgram()
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[IRBasicBlock] = None
        self.temp_counter = 0
        self._bb_counter = 0
        self._label_counter = 0
        self._break_targets: List[str] = []
        self._continue_targets: List[str] = []
        self._in_switch = False
        self._switch_cases: List[tuple] = []
        self.symbol_table = symbol_table
        # 变量名到指针的映射（用于 STORE 指令）
        self.var_ptr_map: Dict[str, IRValue] = {}

    # ========== 工具方法 ==========

    def generate(self, ast: ProgramNode) -> IRProgram:
        """执行 AST → IR 转换"""
        ast.accept(self)
        return self.module

    def _new_temp(self, ty: str = None) -> IRValue:
        """生成新的临时变量"""
        name = f"%{self.temp_counter}"
        self.temp_counter += 1
        return IRValue(name=name, ty=ty, kind=ValueKind.TEMP)

    def _new_bb_label(self, prefix: str = "bb") -> str:
        """生成新的基本块标签"""
        label = f"{prefix}{self._bb_counter}"
        self._bb_counter += 1
        return label

    def _emit(
        self,
        opcode: Opcode,
        operands: List[IRValue] = None,
        result: List[IRValue] = None,
    ) -> Optional[IRValue]:
        """发射 IR 指令

        发出 JMP/JZ 等跳转指令时，同时更新当前基本块的 successor 列表，
        以便后续分析（如 DCE）能够正确追踪控制流。
        """
        if operands is None:
            operands = []
        if result is None:
            result = []

        # 更新控制流图的 successor 边（JMP → 唯一后继，JZ → 两个后继）
        if opcode == Opcode.JMP and operands:
            # JMP：唯一后继是操作数中的块标签
            target = operands[0]
            if isinstance(target, str):
                self.current_block.add_successor(target)
        elif opcode == Opcode.JZ and operands:
            # JZ：两个后继——then分支（条件为真）和 else分支（条件为假）
            # operands[0] 是条件值，operands[1] 是 then_label，operands[2] 是 else_label
            if len(operands) >= 3:
                then_label = operands[1]
                else_label = operands[2]
                if isinstance(then_label, str):
                    self.current_block.add_successor(then_label)
                if isinstance(else_label, str):
                    self.current_block.add_successor(else_label)

        instr = IRInstruction(opcode=opcode, operands=operands, result=result)
        self.current_block.add_instruction(instr)
        # 返回结果值（如果有）
        if result:
            return result[0]
        return None

    def _ensure_block(self) -> IRBasicBlock:
        """确保当前有基本块可用"""
        if self.current_block is None:
            if self.current_function is not None:
                # 创建新基本块
                label = self._new_bb_label()
                bb = self.current_function.add_basic_block(label)
                self.current_block = bb
        return self.current_block

    def _switch_block(self, bb: IRBasicBlock):
        """切换到指定基本块"""
        self.current_block = bb

    def _push_break_target(self, target: str):
        self._break_targets.append(target)

    def _pop_break_target(self) -> str:
        return self._break_targets.pop()

    def _push_continue_target(self, target: str):
        self._continue_targets.append(target)

    def _pop_continue_target(self) -> str:
        return self._continue_targets.pop()

    def _get_type_name(self, type_node) -> str:
        """从 AST 类型节点获取类型名"""
        if type_node is None:
            return "空型"

        # 处理数组类型
        if hasattr(type_node, "node_type") and type_node.node_type.name == "ARRAY_TYPE":
            base_type = (
                self._get_type_name(type_node.element_type)
                if hasattr(type_node, "element_type")
                else "整数型"
            )
            size = ""
            if hasattr(type_node, "size") and type_node.size:
                if hasattr(type_node.size, "value"):
                    size = str(type_node.size.value)
                else:
                    size = "_"  # 动态大小
            return f"{base_type}[{size}]"

        # 处理指针类型
        if (
            hasattr(type_node, "node_type")
            and type_node.node_type.name == "POINTER_TYPE"
        ):
            base_type = (
                self._get_type_name(type_node.base_type)
                if hasattr(type_node, "base_type")
                else "整数型"
            )
            return f"{base_type}*"

        if hasattr(type_node, "name"):
            return type_node.name
        return str(type_node)

    def _resolve_function_name(self, name: str) -> str:
        """解析中文函数名为 C 函数名"""
        # 先使用 mappings.py 的标准库函数映射
        from .mappings import resolve_function_name as resolve_stdlib

        resolved = resolve_stdlib(name)
        if resolved != name:
            return resolved

        # 中文函数名映射（用户自定义函数）
        FUNCTION_MAP = {
            "主函数": "main",
            "主程序": "main",
            # 测试用例中的函数
            "阶乘": "factorial",
            "斐波那契": "fibonacci",
            "幂运算": "power",
            "是质数": "is_prime",
            "最大公约数": "gcd",
            "最小公倍数": "lcm",
            "数组总和": "array_sum",
            "数组最大值": "array_max",
            "数组最小值": "array_min",
            "数组排序": "array_sort",
            "打印数组": "print_array",
        }
        return FUNCTION_MAP.get(name, name)

    # ========== P0: 核心节点 ==========

    def visit_program(self, node: ProgramNode):
        """程序入口"""
        for decl in node.declarations:
            decl.accept(self)

    def visit_function_decl(self, node: FunctionDeclNode):
        """函数声明 → IRFunction"""
        name = self._resolve_function_name(node.name)
        ret_type = self._get_type_name(node.return_type)

        func = IRFunction(name=name, return_type=ret_type)
        self.current_function = func
        self.module.add_function(func)

        # 创建 entry 基本块
        entry_bb = func.entry_block
        self.current_block = entry_bb

        # 处理参数
        for p in node.params:
            p.accept(self)

        # 处理函数体
        if node.body:
            # 如果是 BlockStmtNode，直接处理；否则包装成块
            if isinstance(node.body, BlockStmtNode):
                node.body.accept(self)
            else:
                # 包装为临时块
                tmp_block = BlockStmtNode(statements=[node.body])
                tmp_block.accept(self)

        # 确保函数以 RET 结束
        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.RET)

        self.current_function = None
        self.current_block = None

    def visit_variable_decl(self, node: VariableDeclNode):
        """变量声明 → ALLOC + STORE"""
        self._ensure_block()
        ty = self._get_type_name(node.var_type)

        # 全局变量
        if self.current_block is None:
            gv = IRGlobalVar(name=node.name, ty=ty)
            self.module.add_global(gv)
            return

        # 局部变量: ALLOC
        alloc_result = self._new_temp(ty)
        var_value = IRValue(name=node.name, ty=ty, kind=ValueKind.VAR)
        self._emit(Opcode.ALLOC, [var_value], [alloc_result])

        # 维护变量名到指针的映射（用于 STORE 指令）
        self.var_ptr_map[node.name] = alloc_result

        # 初始化
        if node.init:
            init_node_type = (
                node.init.node_type.name if hasattr(node.init, "node_type") else None
            )

            # 处理数组初始化
            if init_node_type == "ARRAY_INIT":
                self._handle_array_init(node.init, alloc_result, var_value)
            else:
                init_result = self._eval_expr(node.init)
                if init_result:
                    # STORE 前修正常量类型，使 init_result 与目标指针类型匹配
                    init_result = self._coerce_store_value(init_result, ty)
                    self._emit(Opcode.STORE, [init_result, alloc_result])

    def _handle_array_init(
        self, array_init: "ArrayInitNode", alloc_result: IRValue, var_value: IRValue
    ):
        """处理数组初始化：为每个元素生成 STORE 指令"""
        elements = array_init.elements
        zero_val = IRValue("0", "整数型", ValueKind.CONST, const_value=0)
        for i, elem in enumerate(elements):
            # 计算元素地址：GEP 需要两个索引 [0, i]
            # 第一个 0 解引用数组指针，第二个是元素索引
            idx_val = IRValue(str(i), "整数型", ValueKind.CONST, const_value=i)
            elem_ptr = self._new_temp()
            # GEP 需要指针作为第一个操作数，使用 alloc_result（指针）而不是 var_value
            self._emit(Opcode.GEP, [alloc_result, zero_val, idx_val], [elem_ptr])

            # 求值元素值
            elem_val = self._eval_expr(elem)
            if elem_val:
                self._emit(Opcode.STORE, [elem_val, elem_ptr])

    def visit_param_decl(self, node: ParamDeclNode):
        """参数声明 → PARAM

        在 C 中，函数参数直接可用，不需要创建局部副本。
        注意：数组参数在 C 中是指针。
        """
        ty = self._get_type_name(node.param_type)

        # 数组参数在 C 中是指针，这里保留类型信息供后续处理
        # 注意：如果 ty 以 [] 结尾，表示数组参数

        # 1. 添加到函数参数列表（使用实际参数名）
        param_name = node.name
        pv = IRValue(name=param_name, ty=ty, kind=ValueKind.PARAM)
        self.current_function.params.append(pv)

        # 2. 维护变量名到指针的映射
        # 参数名可以直接使用，不需要额外的 ALLOC+STORE
        self.var_ptr_map[node.name] = pv

    def visit_block_stmt(self, node: BlockStmtNode):
        """代码块 → 递归处理"""
        for stmt in node.statements:
            stmt.accept(self)

    def visit_return_stmt(self, node: ReturnStmtNode):
        """返回语句 → RET"""
        self._ensure_block()
        if node.value:
            result = self._eval_expr(node.value)
            if result:
                # 将返回值强制转换为函数声明的返回类型
                result = self._coerce_return_value(result)
                self._emit(Opcode.RET, [result])
            else:
                self._emit(Opcode.RET)
        else:
            self._emit(Opcode.RET)

    # ========== P1: 表达式 ==========

    # =========================================================================
    # 表达式求值 — _eval_expr 分派 + 10个子方法
    # =========================================================================

    # 字面量类型到求值方法的映射
    LITERAL_EVALUATORS = {
        "INT_LITERAL": ("_eval_int_literal", "整数型", int),
        "FLOAT_LITERAL": ("_eval_float_literal", "双精度浮点型", float),
        "STRING_LITERAL": ("_eval_string_literal", "字符串型", None),
        "CHAR_LITERAL": ("_eval_char_literal", "字符型", None),
        "BOOL_LITERAL": ("_eval_bool_literal", "布尔型", None),
        "NULL_LITERAL": ("_eval_null_literal", "空型", None),
    }

    # 表达式类型到求值方法的映射
    EXPR_EVALUATORS = {
        "IDENTIFIER_EXPR": "_eval_identifier",
        "BINARY_EXPR": "_eval_binary",
        "UNARY_EXPR": "_eval_unary",
        "ASSIGN_EXPR": "_eval_assignment",
        "CALL_EXPR": "_eval_call",
        "MEMBER_EXPR": "_eval_member",
        "ARRAY_EXPR": "_eval_array",
        "TERNARY_EXPR": "_eval_ternary",
        "CAST_EXPR": "_eval_cast",
        "LAMBDA_EXPR": "_eval_lambda",
        "COROUTINE_DEF": "_eval_coroutine_def",
        "AWAIT_EXPR": "_eval_await",
        "CHANNEL_EXPR": "_eval_channel",
        "SPAWN_EXPR": "_eval_spawn",
        "YIELD_EXPR": "_eval_yield",
        # 内存管理
        "UNIQUE_PTR_DECL": "_eval_smart_ptr_decl",
        "SHARED_PTR_DECL": "_eval_smart_ptr_decl",
        "WEAK_PTR_DECL": "_eval_smart_ptr_decl",
        "MOVE_EXPR": "_eval_move",
    }

    def _eval_expr(self, node: ASTNode) -> Optional[IRValue]:
        """
        求值表达式，返回结果 IRValue。

        使用 dispatch table 将表达式分派到具体的求值方法。
        """
        if node is None:
            return None

        nt = node.node_type.name if hasattr(node, "node_type") else str(type(node))

        # 字面量求值
        if nt in self.LITERAL_EVALUATORS:
            method_name, type_name, converter = self.LITERAL_EVALUATORS[nt]
            # 调用对应的字面量求值方法
            evaluator = getattr(self, method_name, None)
            if evaluator:
                return evaluator(node)
            # 备用方案：直接在方法中处理
            if converter:
                value = converter(getattr(node, "value", 0))
            else:
                value = getattr(node, "value", "")
            return self._eval_literal(
                node,
                type_name,
                value,
                is_string=(nt in ("STRING_LITERAL", "CHAR_LITERAL")),
            )

        # 表达式求值
        evaluator_name = self.EXPR_EVALUATORS.get(nt)
        if evaluator_name:
            evaluator = getattr(self, evaluator_name, None)
            if evaluator:
                return evaluator(node)

        return None

    def _eval_int_literal(self, node: ASTNode) -> IRValue:
        """求值整数字面量"""
        return self._eval_literal(node, "整数型", int(getattr(node, "value", 0)))

    def _eval_float_literal(self, node: ASTNode) -> IRValue:
        """求值浮点字面量"""
        val = getattr(node, "value", "0.0")
        # 去掉 f/F 后缀（如 3.14f -> 3.14）
        if isinstance(val, str) and val.lower().endswith("f"):
            val = val[:-1]
        return self._eval_literal(
            node, "双精度浮点型", float(val) if isinstance(val, str) else val
        )

    def _eval_string_literal(self, node: ASTNode) -> IRValue:
        """求值字符串字面量"""
        val = getattr(node, "value", "")
        # 直接使用原始字符串值，不添加额外的引号
        # 字符串值本身已经包含正确的内容（包括转义字符）
        return self._eval_literal(node, "字符串型", val, is_string=True)

    def _eval_char_literal(self, node: ASTNode) -> IRValue:
        """求值字符字面量"""
        val = getattr(node, "value", "0")
        return self._eval_literal(node, "字符型", f"'{val}'", is_string=True)

    def _eval_bool_literal(self, node: ASTNode) -> IRValue:
        """求值布尔字面量"""
        return self._eval_literal(node, "布尔型", getattr(node, "value", False))

    def _eval_null_literal(self, node: ASTNode) -> IRValue:
        """求值空字面量"""
        # NullLiteralNode 没有 value 属性，直接返回 "0"
        return IRValue("0", "空型", ValueKind.CONST, const_value=0)

    def _eval_literal(
        self, node: ASTNode, type_name: str, value: Any, is_string: bool = False
    ) -> IRValue:
        """求值字面量：INT/FLOAT/STRING/CHAR/BOOL/NULL"""
        return IRValue(str(value), type_name, ValueKind.CONST, const_value=value)

    def _eval_identifier(self, node: ASTNode) -> IRValue:
        """求值标识符表达式

        返回值：
        - 如果是局部变量，返回指针（从 var_ptr_map 获取）
        - 如果是函数参数，直接返回参数引用
        - 如果是数组变量，直接返回数组指针（数组退化）
        """
        name = getattr(node, "name", "")

        # 检查是否是局部变量（有 ALLOC）
        if name in self.var_ptr_map:
            ptr = self.var_ptr_map[name]

            # 检查是否是数组类型（以 [] 结尾或包含 [N]）
            ptr_ty = getattr(ptr, "ty", "")
            is_array = ptr_ty.endswith("]") or ("[" in ptr_ty and ptr_ty.endswith("]"))

            if is_array:
                # 数组变量：直接返回数组指针（数组退化）
                # 不需要 LOAD，直接返回指针
                return ptr
            else:
                # 普通变量：生成 LOAD 指令
                # 优先使用指针的 ty（来自 ALLOC），其次用 node.inferred_type，最后用默认值
                # 这样确保 LOAD 结果的类型与变量的实际类型一致
                ty = ptr_ty or getattr(node, "inferred_type", "整数型")
                result = self._new_temp(ty)
                self._emit(Opcode.LOAD, [ptr], [result])
                return result

        # 检查是否是函数参数
        if self.current_function:
            for param in self.current_function.params:
                if param.name == name:
                    # 参数直接返回（不需要 LOAD）
                    return param

        # 默认返回变量引用
        ty = getattr(node, "inferred_type", "整数型")
        return IRValue(name, ty, ValueKind.VAR)

    # 类型宽度表（用于类型统一推断）
    _TYPE_WIDTHS = {
        "布尔型": 1,
        "字符型": 8,
        "字节型": 8,
        "整数型": 32,
        "浮点型": 32,
        "双精度浮点型": 64,
    }

    def _unify_binary_types(
        self, left: Optional[IRValue], right: Optional[IRValue]
    ) -> tuple:
        """推断二元运算的结果类型，并将常量操作数修正为正确类型。

        规则：
        - 两个操作数都是整数系（布尔/字符/字节/整数），取更宽的类型
        - 任一操作数是浮点系，取更宽的浮点类型
        - 常量操作数的 ty 字段修正为统一后的类型

        Returns:
            (left, right, result_type_name) — 可能返回修正后的新 IRValue
        """
        if left is None or right is None:
            return left, right, "整数型"

        left_ty = getattr(left, "ty", None) or "整数型"
        right_ty = getattr(right, "ty", None) or "整数型"

        left_width = self._TYPE_WIDTHS.get(left_ty)
        right_width = self._TYPE_WIDTHS.get(right_ty)

        # 如果任一方不在宽度表中（如字符串型、数组型等），不处理
        if left_width is None or right_width is None:
            return left, right, left_ty

        # 判断是否涉及浮点
        float_types = {"浮点型", "双精度浮点型"}
        left_is_float = left_ty in float_types
        right_is_float = right_ty in float_types

        if left_is_float or right_is_float:
            # 浮点统一：取更宽的浮点类型
            if left_ty == "双精度浮点型" or right_ty == "双精度浮点型":
                unified_ty = "双精度浮点型"
            else:
                unified_ty = "浮点型"
        else:
            # 整数系统一：取更宽的类型
            if left_width >= right_width:
                unified_ty = left_ty
            else:
                unified_ty = right_ty

        # 修正常量操作数的 ty
        left = self._coerce_const_type(left, unified_ty)
        right = self._coerce_const_type(right, unified_ty)

        # 对非常量操作数，生成类型转换指令（ZEXT/SEXT/TRUNC）
        left = self._emit_type_coercion(left, unified_ty)
        right = self._emit_type_coercion(right, unified_ty)

        return left, right, unified_ty

    def _emit_type_coercion(self, val: IRValue, target_ty: str) -> IRValue:
        """如果 val 是非常量且 ty 与 target_ty 不同，生成类型转换指令。

        整数类型间：窄→宽用 SEXT（符号扩展），宽→窄用 TRUNC（截断）。
        浮点类型间：由后端处理 fpext/fptrunc。
        """
        if val is None:
            return val
        kind = getattr(val, "kind", None)
        # 常量已由 _coerce_const_type 处理
        if kind == ValueKind.CONST:
            return val
        cur_ty = getattr(val, "ty", None)
        if cur_ty == target_ty or cur_ty is None:
            return val

        # 检查类型宽度是否不同
        cur_width = self._TYPE_WIDTHS.get(cur_ty)
        target_width = self._TYPE_WIDTHS.get(target_ty)
        if cur_width is None or target_width is None:
            return val

        if cur_width == target_width:
            return val

        # 生成转换指令
        result = self._new_temp(target_ty)
        # 创建一个仅携带目标类型的虚拟操作数，供后端 SextStrategy/TruncStrategy
        # 通过 instr.operands[1] 获取目标 LLVM 类型
        type_hint = IRValue(
            target_ty, target_ty, ValueKind.CONST, const_value=target_ty
        )
        if cur_width < target_width:
            # 窄→宽：符号扩展（SEXT）
            self._emit(Opcode.SEXT, [val, type_hint], [result])
        else:
            # 宽→窄：截断（TRUNC）
            self._emit(Opcode.TRUNC, [val, type_hint], [result])
        return result

    def _coerce_const_type(self, val: IRValue, target_ty: str) -> IRValue:
        """如果 val 是常量且 ty 与 target_ty 不同，创建一个修正类型的 IRValue"""
        if val is None:
            return val
        kind = getattr(val, "kind", None)
        if kind != ValueKind.CONST:
            return val
        cur_ty = getattr(val, "ty", None)
        if cur_ty == target_ty:
            return val
        # 常量类型需要修正 — 创建新的 IRValue
        const_val = getattr(val, "const_value", None)
        if const_val is None:
            const_val = val.name
        # 对于浮点系常量，确保 const_value 是浮点数
        if target_ty in ("浮点型", "双精度浮点型"):
            try:
                const_val = float(const_val)
            except (ValueError, TypeError):
                const_val = 0.0
        return IRValue(
            str(const_val), target_ty, ValueKind.CONST, const_value=const_val
        )

    def _coerce_store_value(self, val: IRValue, target_ty: str) -> IRValue:
        """STORE 前修正常量值类型。

        当常量的 ty 与目标变量类型不一致时（如 整数型常量 存入 字符型变量），
        修正常量的 ty 为目标类型，确保后端生成正确的 LLVM 常量。
        """
        if val is None:
            return val
        if getattr(val, "kind", None) != ValueKind.CONST:
            return val
        if getattr(val, "ty", None) == target_ty:
            return val
        return self._coerce_const_type(val, target_ty)

    def _coerce_return_value(self, val: IRValue) -> IRValue:
        """将返回值强制转换为函数声明的返回类型。

        当返回表达式的类型与函数声明的返回类型不匹配时（如 i32 返回值赋给 i8 返回函数），
        生成 TRUNC/ZEXT 指令进行类型转换。
        """
        if val is None or self.current_function is None:
            return val

        func_ret_ty = self.current_function.return_type
        val_ty = getattr(val, "ty", None)
        if val_ty == func_ret_ty:
            return val

        # 需要类型转换：生成 ZEXT/SEXT/TRUNC
        return self._emit_type_coercion(val, func_ret_ty)

    def _eval_binary(self, node: ASTNode) -> Optional[IRValue]:
        """求值二元表达式"""
        left = self._eval_expr(getattr(node, "left", None))
        right = self._eval_expr(getattr(node, "right", None))
        op = getattr(node, "operator", getattr(node, "op", "+"))

        # AST 运算符 → Opcode 枚举名映射
        # AST 使用符号（如 >, <, ==），Opcode 使用名称（如 GT, LT, EQ）
        op_map = {
            # 算术运算
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
            "/": "DIV",
            "%": "MOD",
            # 比较运算
            "==": "EQ",
            "!=": "NE",
            "<": "LT",
            "<=": "LE",
            ">": "GT",
            ">=": "GE",
            # 逻辑运算
            "&&": "L_AND",
            "||": "L_OR",
            # 位运算
            "&": "AND",
            "|": "OR",
            "^": "XOR",
            "<<": "SHL",
            ">>": "SHR",
            # 中文运算符
            "并且": "L_AND",
            "或者": "L_OR",
            "大于": "GT",
            "小于": "LT",
            "大于等于": "GE",
            "小于等于": "LE",
            "等于": "EQ",
            "不等于": "NE",
        }

        opcode_name = op_map.get(op, op.upper() if isinstance(op, str) else str(op))
        try:
            opcode = Opcode[opcode_name]
        except (KeyError, ValueError):
            opcode = Opcode.ADD

        # 类型推断：统一操作数类型，修正常量 ty
        left, right, result_ty = self._unify_binary_types(left, right)

        # 比较运算结果类型固定为布尔型
        if opcode in (
            Opcode.EQ,
            Opcode.NE,
            Opcode.LT,
            Opcode.LE,
            Opcode.GT,
            Opcode.GE,
            Opcode.L_AND,
            Opcode.L_OR,
        ):
            result_ty = "布尔型"

        result = self._new_temp(result_ty)
        self._emit(opcode, [left, right], [result])
        return result

    def _eval_unary(self, node: ASTNode) -> Optional[IRValue]:
        """求值一元表达式"""
        operand = self._eval_expr(getattr(node, "operand", None))
        op = getattr(node, "operator", getattr(node, "op", "-"))
        if op in ("-", "!"):
            opcode = Opcode.NEG if op == "-" else Opcode.L_NOT
            result = self._new_temp()
            self._emit(opcode, [operand] if operand else [], [result])
            return result
        return None

    def _eval_assignment(self, node: ASTNode) -> Optional[IRValue]:
        """求值赋值表达式

        对于数组赋值（如 数组[j] = 值），需要特殊处理：
        - target 只生成 GEP（获取地址），不生成 LOAD
        - STORE 写入这个地址

        对于普通赋值（如 a = b），使用 var_ptr_map 获取变量指针。
        """
        value = self._eval_expr(getattr(node, "value", None))

        # 检查 target 是否是数组访问
        target_node = getattr(node, "target", None)
        if target_node and hasattr(target_node, "node_type"):
            nt = target_node.node_type.name
            if nt == "ARRAY_EXPR":
                # 数组赋值：只生成 GEP，不生成 LOAD
                # 获取数组基址（参数或局部变量）
                array_node = getattr(target_node, "array", None) or getattr(
                    target_node, "object", None
                )
                array_name = getattr(array_node, "name", "") if array_node else ""

                # 检查是否是局部变量（有 ALLOC）
                if array_name in self.var_ptr_map:
                    base = self.var_ptr_map[array_name]
                else:
                    # 可能是函数参数，直接使用参数名
                    base = IRValue(array_name, kind=ValueKind.PARAM)

                index = self._eval_expr(getattr(target_node, "index", None))
                if base and index:
                    zero_val = IRValue("0", "整数型", ValueKind.CONST, const_value=0)
                    elem_ptr = self._new_temp()
                    self._emit(Opcode.GEP, [base, zero_val, index], [elem_ptr])
                    if value:
                        self._emit(Opcode.STORE, [value, elem_ptr])
                    return value
            elif nt == "IDENTIFIER_EXPR":
                # 普通标识符赋值：使用 var_ptr_map 获取变量指针
                var_name = getattr(target_node, "name", "")
                if var_name in self.var_ptr_map:
                    ptr = self.var_ptr_map[var_name]
                    if value:
                        # STORE 前修正常量类型，使 value 与目标变量类型匹配
                        target_ty = getattr(ptr, "ty", None)
                        value = self._coerce_store_value(value, target_ty)
                        self._emit(Opcode.STORE, [value, ptr])
                    return value
            elif nt == "MEMBER_EXPR":
                # 结构体字段赋值：p.x = 10
                obj_node = getattr(target_node, "obj", None)
                member_name = getattr(target_node, "member", "")
                obj_name = getattr(obj_node, "name", "") if obj_node else ""

                if obj_name in self.var_ptr_map:
                    ptr = self.var_ptr_map[obj_name]
                    ptr_ty = getattr(ptr, "ty", "")

                    # 通过查找结构体定义来检测是否是结构体类型
                    struct_def = None
                    for s in self.module.structs:
                        if s.name == ptr_ty:
                            struct_def = s
                            break

                    if struct_def and member_name in struct_def.members:
                        field_idx = list(struct_def.members.keys()).index(member_name)
                        idx_val = IRValue(
                            str(field_idx),
                            "整数型",
                            ValueKind.CONST,
                            const_value=field_idx,
                        )

                        # GEP 获取字段地址：需要两个索引 [0, field_idx]
                        zero_val = IRValue(
                            "0", "整数型", ValueKind.CONST, const_value=0
                        )
                        field_ptr = self._new_temp()
                        self._emit(Opcode.GEP, [ptr, zero_val, idx_val], [field_ptr])

                        # STORE 写入字段值
                        if value:
                            target_ty = struct_def.members[member_name]
                            value = self._coerce_store_value(value, target_ty)
                            self._emit(Opcode.STORE, [value, field_ptr])
                        return value

        # 回退：使用原始的 _eval_expr
        target = self._eval_expr(target_node)
        if value:
            self._emit(Opcode.STORE, [value, target] if target else [value])
        return value

    def _eval_call(self, node: ASTNode) -> Optional[IRValue]:
        """求值函数调用表达式"""
        callee = getattr(node, "callee", None)
        func_name = getattr(callee, "name", "unknown") if callee else "unknown"
        # 解析中文函数名为 C 函数名
        func_name = self._resolve_function_name(func_name)
        args = []
        for arg in getattr(node, "args", []):
            arg_val = self._eval_expr(arg)
            if arg_val:
                args.append(arg_val)
        result = self._new_temp()
        func_val = IRValue(func_name, kind=ValueKind.FUNCTION)
        self._emit(Opcode.CALL, [func_val] + args, [result])
        return result

    def _eval_member(self, node: ASTNode) -> Optional[IRValue]:
        """求值成员访问表达式

        结构体字段访问需要三步：
        1. 获取结构体指针（从 var_ptr_map，不 LOAD）
        2. GEP: 获取字段地址
        3. LOAD: 读取字段值
        """
        obj_node = getattr(node, "obj", None)
        member_name = getattr(node, "member", "")

        # 获取对象名
        obj_name = getattr(obj_node, "name", "") if obj_node else ""

        # 检查是否是局部变量（有 ALLOC）
        if obj_name in self.var_ptr_map:
            ptr = self.var_ptr_map[obj_name]
            ptr_ty = getattr(ptr, "ty", "")

            # 通过查找结构体定义来检测是否是结构体类型
            struct_def = None
            for s in self.module.structs:
                if s.name == ptr_ty:
                    struct_def = s
                    break

            if struct_def and member_name in struct_def.members:
                # 获取字段索引
                field_idx = list(struct_def.members.keys()).index(member_name)
                idx_val = IRValue(
                    str(field_idx), "整数型", ValueKind.CONST, const_value=field_idx
                )

                # GEP 获取字段地址：需要两个索引 [0, field_idx]
                # 第一个 0 解引用结构体指针，第二个是字段索引
                zero_val = IRValue("0", "整数型", ValueKind.CONST, const_value=0)
                field_ptr = self._new_temp()
                self._emit(Opcode.GEP, [ptr, zero_val, idx_val], [field_ptr])

                # LOAD 读取字段值
                field_ty = struct_def.members[member_name]
                result = self._new_temp(field_ty)
                self._emit(Opcode.LOAD, [field_ptr], [result])
                return result

        # 回退：使用原始逻辑
        obj = self._eval_expr(obj_node)
        result = self._new_temp()
        self._emit(Opcode.GETPTR, [obj] if obj else [], [result])
        return result

    def _eval_array(self, node: ASTNode) -> Optional[IRValue]:
        """求值数组访问表达式

        数组访问需要两步：
        1. GEP: 获取元素地址 (base + index)
        2. LOAD: 读取元素值 *(base + index)

        Phase 11: 如果启用边界检查，添加边界检查 IR
        """
        # ArrayExprNode 使用 array 属性，不是 object
        array_node = getattr(node, "array", None) or getattr(node, "object", None)
        array_name = getattr(array_node, "name", "") if array_node else ""

        # 检查是否是局部变量（有 ALLOC）
        if array_name in self.var_ptr_map:
            base = self.var_ptr_map[array_name]
        else:
            # 可能是函数参数，直接使用参数名
            base = IRValue(array_name, kind=ValueKind.PARAM)

        index = self._eval_expr(getattr(node, "index", None))

        if not base or not index:
            return None

        # Phase 11: 生成边界检查 IR
        self._generate_array_bounds_check(array_name, index, node)

        # 第一步：获取元素地址
        zero_val = IRValue("0", "整数型", ValueKind.CONST, const_value=0)
        addr = self._new_temp()
        self._emit(Opcode.GEP, [base, zero_val, index], [addr])

        # 第二步：读取元素值
        result = self._new_temp()
        self._emit(Opcode.LOAD, [addr], [result])

        return result

    def _generate_array_bounds_check(
        self,
        array_name: str,
        index: IRValue,
        node: ASTNode,
    ) -> None:
        """
        生成数组边界检查 IR

        Phase 11: 生成以下 IR 模式：
        ```
        bounds_check:
            %cond = icmp sge i32 %index, 0
            br i1 %cond, label %access_ok, label %bounds_error

        bounds_error:
            call @__zhc_bounds_error(i8* msg)
            unreachable

        access_ok:
            ; 继续正常访问
        ```

        注意：这里生成的是 IR 级别的高层表示，
        具体的目标代码生成由后端（如 LLVM）负责。
        """
        # 检查是否有数组大小信息
        array_size = self._get_array_size(array_name)
        if array_size is None:
            # 无法确定数组大小，跳过静态边界检查
            return

        # 生成边界检查
        check_bb_label = self._new_bb_label("bounds_check")
        error_bb_label = self._new_bb_label("bounds_error")
        ok_bb_label = self._new_bb_label("access_ok")

        # 创建基本块
        check_bb = IRBasicBlock(check_bb_label)
        error_bb = IRBasicBlock(error_bb_label)
        ok_bb = IRBasicBlock(ok_bb_label)

        self.current_function.basic_blocks.append(check_bb)
        self.current_function.basic_blocks.append(error_bb)
        self.current_function.basic_blocks.append(ok_bb)

        # 切换到检查块
        self._switch_block(check_bb)

        # 比较: index >= 0
        zero = IRValue("0", "整数型", ValueKind.CONST, const_value=0)
        gep_result = self._new_temp("布尔型")
        self._emit(Opcode.ICMP, [index, zero], [gep_result])
        self._emit(Opcode.JZ, [gep_result, error_bb_label, ok_bb_label])

        # 错误块：调用错误处理函数
        self._switch_block(error_bb)
        self._emit(Opcode.CALL, [], [])  # 错误处理调用
        self._emit(Opcode.UNREACHABLE, [], [])

        # 正常访问块
        self._switch_block(ok_bb)

    def _get_array_size(self, array_name: str) -> Optional[int]:
        """
        获取数组大小

        如果无法确定数组大小，返回 None。
        """
        # 检查是否是局部变量
        if array_name in self.var_ptr_map:
            # 尝试从符号表获取类型信息
            if self.symbol_table:
                symbol = self.symbol_table.lookup(array_name)
                if symbol and symbol.data_type:
                    # 解析类型字符串中的数组大小
                    type_str = symbol.data_type
                    if "[" in type_str and "]" in type_str:
                        import re

                        match = re.search(r"\[(\d+)\]", type_str)
                        if match:
                            return int(match.group(1))
        return None

    def _eval_ternary(self, node: ASTNode) -> Optional[IRValue]:
        """求值三元表达式（条件 ? then : else）"""
        cond = self._eval_expr(getattr(node, "condition", None))
        then_val = self._eval_expr(getattr(node, "then_expr", None))
        else_val = self._eval_expr(getattr(node, "else_expr", None))
        result = self._new_temp()
        # 实现为条件跳转
        then_bb_label = self._new_bb_label("ternary_then")
        else_bb_label = self._new_bb_label("ternary_else")
        merge_bb_label = self._new_bb_label("ternary_merge")
        self.current_function.basic_blocks.append(IRBasicBlock(then_bb_label))
        self.current_function.basic_blocks.append(IRBasicBlock(else_bb_label))
        self.current_function.basic_blocks.append(IRBasicBlock(merge_bb_label))
        # 条件跳转：cond 为真跳到 then，为假跳到 else
        if cond:
            self._emit(Opcode.JZ, [cond, then_bb_label, else_bb_label])
        # then 块
        self._switch_block(self.current_function.find_basic_block(then_bb_label))
        if then_val:
            self._emit(Opcode.STORE, [then_val], [result])
        self._emit(Opcode.JMP, [merge_bb_label])
        # else 块
        self._switch_block(self.current_function.find_basic_block(else_bb_label))
        if else_val:
            self._emit(Opcode.STORE, [else_val], [result])
        self._emit(Opcode.JMP, [merge_bb_label])
        # merge 块
        self._switch_block(self.current_function.find_basic_block(merge_bb_label))
        return result

    def _eval_cast(self, node: ASTNode) -> Optional[IRValue]:
        """求值类型转换表达式"""
        operand = self._eval_expr(getattr(node, "operand", None))
        target_type = self._get_type_name(getattr(node, "target_type", None))
        result = self._new_temp(target_type)
        if operand:
            self._emit(Opcode.BITCAST, [operand], [result])
        return result

    def _eval_lambda(self, node: LambdaExprNode) -> Optional[IRValue]:
        """求值 Lambda 表达式

        Lambda 表达式会创建一个闭包，包含：
        1. 函数指针
        2. upvalue 环境

        Returns:
            IRValue - 闭包值
        """
        # 获取返回类型
        return_type = "空型"
        if hasattr(node, "return_type") and node.return_type:
            return_type = self._get_type_name(node.return_type)

        # 获取参数类型
        param_types = []
        for param in node.params:
            if hasattr(param, "param_type") and param.param_type:
                param_types.append(self._get_type_name(param.param_type))
            else:
                param_types.append("整数型")  # 默认类型

        # 创建闭包类型签名
        closure_type = f"函数型({','.join(param_types)}) -> {return_type}"

        # 创建临时变量存储闭包
        result = self._new_temp(closure_type)

        # TODO: 实际创建闭包需要:
        # 1. 为闭包体创建一个内部函数
        # 2. 捕获外部变量（upvalue）
        # 3. 创建闭包结构体

        # 目前生成一条 LAMBDA 指令作为占位
        self._emit(Opcode.LAMBDA, [], [result])

        return result

    def _eval_coroutine_def(self, node) -> Optional[IRValue]:
        """求值协程定义

        协程定义创建一个协程函数。
        目前生成占位指令。

        Returns:
            IRValue - 协程函数值
        """
        # TODO: 实际创建协程需要：
        # 1. 为协程体创建一个内部函数
        # 2. 设置协程入口点和恢复点
        # 3. 创建协程上下文结构体

        result = self._new_temp("函数型")
        self._emit(Opcode.COROUTINE_CREATE, [], [result])
        return result

    def _eval_await(self, node) -> Optional[IRValue]:
        """求值等待表达式

        等待一个协程或任务完成。
        目前生成占位指令。

        Returns:
            IRValue - 等待的结果值
        """
        # 获取要等待的表达式
        expr = getattr(node, "expression", None)
        expr_value = self._eval_expr(expr) if expr else None

        result = self._new_temp("空型")
        self._emit(Opcode.COROUTINE_AWAIT, [expr_value] if expr_value else [], [result])
        return result

    def _eval_channel(self, node) -> Optional[IRValue]:
        """求值通道创建表达式

        创建一个用于协程间通信的通道。
        目前生成占位指令。

        Returns:
            IRValue - 通道值
        """
        # 获取元素类型
        element_type = getattr(node, "element_type", None)
        element_type_name = (
            self._get_type_name(element_type) if element_type else "空型"
        )

        result = self._new_temp(f"通道型[{element_type_name}]")
        self._emit(Opcode.CHANNEL_CREATE, [], [result])
        return result

    def _eval_spawn(self, node) -> Optional[IRValue]:
        """求值启动协程表达式

        启动一个新的协程。
        目前生成占位指令。

        Returns:
            IRValue - 任务/协程 ID
        """
        # 获取要启动的协程
        coroutine = getattr(node, "coroutine", None)
        coroutine_value = self._eval_expr(coroutine) if coroutine else None

        result = self._new_temp("任务型")
        self._emit(
            Opcode.COROUTINE_SPAWN,
            [coroutine_value] if coroutine_value else [],
            [result],
        )
        return result

    def _eval_yield(self, node) -> Optional[IRValue]:
        """求值让出表达式

        协程主动让出执行权。
        目前生成占位指令。

        Returns:
            None（yield 是终止指令）
        """
        # 获取让出的值
        value = getattr(node, "value", None)
        value_value = self._eval_expr(value) if value else None

        # yield 是终止指令，跳转到协程的恢复点
        self._emit(Opcode.COROUTINE_YIELD, [value_value] if value_value else [])
        return None

    # =========================================================================
    # 内存管理求值方法
    # =========================================================================

    def _eval_smart_ptr_decl(self, node) -> Optional[IRValue]:
        """求值智能指针声明

        生成 SMART_PTR_CREATE 指令，分配智能指针并初始化。
        """
        kind = getattr(node, "pointer_kind", "unique")
        name = getattr(node, "name", "")
        inner_type = getattr(node, "inner_type", None)
        initializer = getattr(node, "initializer", None)

        # 求值初始化表达式
        init_value = self._eval_expr(initializer) if initializer else None

        # 获取内部类型名
        inner_type_name = ""
        if inner_type:
            inner_type_name = getattr(inner_type, "type_name", str(inner_type))

        # 创建智能指针
        ptr = self._emit(
            Opcode.SMART_PTR_CREATE,
            [kind, inner_type_name, init_value],
        )

        # 注册到局部变量表
        if name:
            self._set_var(name, ptr)

        return ptr

    def _eval_move(self, node) -> Optional[IRValue]:
        """求值移动语义表达式

        生成 MOVE 指令，将资源的所有权从源转移到目标。
        """
        operand = getattr(node, "operand", None)
        operand_value = self._eval_expr(operand) if operand else None

        # 生成移动指令
        result = self._emit(Opcode.MOVE, [operand_value])

        # 如果操作数是标识符，清除源变量的引用
        if operand and hasattr(operand, "name"):
            self._set_var(operand.name, None)

        return result

    def visit_binary_expr(self, node: BinaryExprNode):
        """二元表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_unary_expr(self, node: UnaryExprNode):
        """一元表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_assign_expr(self, node: AssignExprNode):
        """赋值表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_call_expr(self, node: CallExprNode):
        """函数调用"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_identifier_expr(self, node: IdentifierExprNode):
        """标识符表达式"""
        self._eval_expr(node)

    def visit_int_literal(self, node: IntLiteralNode):
        """整数字面量"""
        self._eval_expr(node)

    def visit_float_literal(self, node: FloatLiteralNode):
        """浮点字面量"""
        self._eval_expr(node)

    def visit_string_literal(self, node: StringLiteralNode):
        """字符串字面量"""
        self._eval_expr(node)

    def visit_char_literal(self, node: CharLiteralNode):
        """字符字面量"""
        self._eval_expr(node)

    def visit_bool_literal(self, node: BoolLiteralNode):
        """布尔字面量"""
        self._eval_expr(node)

    def visit_null_literal(self, node: NullLiteralNode):
        """空指针字面量"""
        self._eval_expr(node)

    def visit_lambda_expr(self, node: LambdaExprNode):
        """Lambda 表达式"""
        self._ensure_block()
        result = self._eval_lambda(node)
        return result

    # ========== P2: 控制流 ==========

    def visit_if_stmt(self, node: IfStmtNode):
        """if 语句"""
        self._ensure_block()

        # 求值条件
        cond = self._eval_expr(node.condition)

        # 创建基本块
        then_bb = IRBasicBlock(self._new_bb_label("then"))
        else_bb = IRBasicBlock(self._new_bb_label("else"))
        merge_bb = IRBasicBlock(self._new_bb_label("ifmerge"))

        self.current_function.basic_blocks.append(then_bb)
        self.current_function.basic_blocks.append(else_bb)
        self.current_function.basic_blocks.append(merge_bb)

        # 条件跳转：cond 为真跳到 then，为假跳到 else
        if cond:
            self._emit(Opcode.JZ, [cond, then_bb.label, else_bb.label])

        # then 分支
        old_block = self.current_block
        self._switch_block(then_bb)
        node.then_branch.accept(self)
        then_terminated = self.current_block and self.current_block.is_terminated()
        if not then_terminated:
            self._emit(Opcode.JMP, [merge_bb.label])
        old_block.add_successor(then_bb.label)
        old_block.add_successor(else_bb.label)
        then_bb.add_predecessor(old_block.label)

        # else 分支
        self._switch_block(else_bb)
        if node.else_branch:
            node.else_branch.accept(self)
        else_terminated = self.current_block and self.current_block.is_terminated()
        if not else_terminated:
            self._emit(Opcode.JMP, [merge_bb.label])
        then_bb.add_successor(merge_bb.label)
        else_bb.add_predecessor(old_block.label)

        # merge 基本块：只有当至少一个分支未终止时才切换到 merge
        # 如果两个分支都终止（如都有 return），merge 块不可达，不应切换
        if not (then_terminated and else_terminated):
            self._switch_block(merge_bb)
        else:
            # 两个分支都终止，merge 块不可达
            # 移除 merge 块及其所有引用，避免 IR 验证器报错
            self.current_function.basic_blocks.remove(merge_bb)
            # 清理 then_bb 的 successor 引用（原来跳转到 merge）
            if merge_bb.label in then_bb.successors:
                then_bb.successors.remove(merge_bb.label)
            # 清理 entry 块中指向 merge 的 successor（如果有的话）
            if merge_bb.label in old_block.successors:
                old_block.successors.remove(merge_bb.label)
            self.current_block = None  # 标记当前块为空，避免函数结尾添加额外 ret

    def visit_while_stmt(self, node: WhileStmtNode):
        """while 循环"""
        self._ensure_block()

        cond_bb = IRBasicBlock(self._new_bb_label("while_cond"))
        body_bb = IRBasicBlock(self._new_bb_label("while_body"))
        end_bb = IRBasicBlock(self._new_bb_label("while_end"))

        self.current_function.basic_blocks.append(cond_bb)
        self.current_function.basic_blocks.append(body_bb)
        self.current_function.basic_blocks.append(end_bb)

        # 跳转到条件块
        self._emit(Opcode.JMP, [cond_bb.label])

        # 条件块
        self._switch_block(cond_bb)
        cond = self._eval_expr(node.condition)
        # 条件跳转：cond 为真跳到 body（继续循环），为假跳到 end（退出循环）
        if cond:
            self._emit(Opcode.JZ, [cond, body_bb.label, end_bb.label])

        # 循环体
        cond_bb.add_successor(body_bb.label)
        cond_bb.add_successor(end_bb.label)
        body_bb.add_predecessor(cond_bb.label)
        self._switch_block(body_bb)

        self._push_break_target(end_bb.label)
        self._push_continue_target(cond_bb.label)

        node.body.accept(self)

        self._pop_continue_target()
        self._pop_break_target()

        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [cond_bb.label])
        body_bb.add_successor(cond_bb.label)

        # 结束块
        self._switch_block(end_bb)

    def visit_for_stmt(self, node: ForStmtNode):
        """for 循环"""
        self._ensure_block()

        # 初始化
        if node.init:
            node.init.accept(self)

        # 创建 for 循环的 4 个基本块
        cond_bb, body_bb, update_bb, end_bb = self._create_for_loop_blocks()

        # 跳转到条件块
        self._emit(Opcode.JMP, [cond_bb.label])

        # 条件块
        self._switch_block(cond_bb)
        cond = self._eval_expr(node.condition) if node.condition else None
        # 条件跳转：cond 为真跳到 body（继续循环），为假跳到 end（退出循环）
        if cond:
            self._emit(Opcode.JZ, [cond, body_bb.label, end_bb.label])

        # 更新块
        update_bb.add_predecessor(body_bb.label)
        body_bb.add_successor(update_bb.label)
        self._switch_block(update_bb)
        if node.update:
            node.update.accept(self)
        self._emit(Opcode.JMP, [cond_bb.label])
        cond_bb.add_predecessor(update_bb.label)

        # 循环体
        cond_bb.add_successor(body_bb.label)
        cond_bb.add_successor(end_bb.label)
        body_bb.add_predecessor(cond_bb.label)
        self._switch_block(body_bb)

        self._push_break_target(end_bb.label)
        self._push_continue_target(update_bb.label)

        node.body.accept(self)

        self._pop_continue_target()
        self._pop_break_target()

        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [update_bb.label])
        update_bb.add_successor(cond_bb.label)

        # 结束块
        self._switch_block(end_bb)

    def _create_for_loop_blocks(self):
        """创建 for 循环的 4 个基本块：cond / body / update / end"""
        cond_bb = IRBasicBlock(self._new_bb_label("for_cond"))
        body_bb = IRBasicBlock(self._new_bb_label("for_body"))
        update_bb = IRBasicBlock(self._new_bb_label("for_update"))
        end_bb = IRBasicBlock(self._new_bb_label("for_end"))

        self.current_function.basic_blocks.append(cond_bb)
        self.current_function.basic_blocks.append(body_bb)
        self.current_function.basic_blocks.append(update_bb)
        self.current_function.basic_blocks.append(end_bb)

        return cond_bb, body_bb, update_bb, end_bb

    def visit_do_while_stmt(self, node: DoWhileStmtNode):
        """do-while 循环"""
        self._ensure_block()

        body_bb = IRBasicBlock(self._new_bb_label("do_body"))
        cond_bb = IRBasicBlock(self._new_bb_label("do_cond"))
        end_bb = IRBasicBlock(self._new_bb_label("do_end"))

        self.current_function.basic_blocks.append(body_bb)
        self.current_function.basic_blocks.append(cond_bb)
        self.current_function.basic_blocks.append(end_bb)

        self._emit(Opcode.JMP, [body_bb.label])

        # 循环体
        self._switch_block(body_bb)
        self._push_break_target(end_bb.label)
        self._push_continue_target(cond_bb.label)

        node.body.accept(self)

        self._pop_continue_target()
        self._pop_break_target()

        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [cond_bb.label])
        body_bb.add_successor(cond_bb.label)

        # 条件块
        self._switch_block(cond_bb)
        cond = self._eval_expr(node.condition)
        # do-while: 条件为真跳到 body（继续循环），为假跳到 end（退出循环）
        if cond:
            self._emit(Opcode.JZ, [cond, body_bb.label, end_bb.label])
        cond_bb.add_successor(body_bb.label)
        cond_bb.add_successor(end_bb.label)

        # 结束块
        self._switch_block(end_bb)

    def visit_break_stmt(self, node: BreakStmtNode):
        """break 语句"""
        self._ensure_block()
        if self._break_targets:
            target = self._break_targets[-1]
            self._emit(Opcode.JMP, [target])

    def visit_continue_stmt(self, node: ContinueStmtNode):
        """continue 语句"""
        self._ensure_block()
        if self._continue_targets:
            target = self._continue_targets[-1]
            self._emit(Opcode.JMP, [target])

    def visit_switch_stmt(self, node: SwitchStmtNode):
        """switch 语句 - 完整实现

        生成结构：
        1. 评估 switch 表达式
        2. 为每个 case/default 创建基本块
        3. 发射 switch IR 指令
        4. 处理每个 case 的语句体
        5. 跳转到 end_bb
        """
        self._ensure_block()

        # 保存上下文
        old_switch = self._in_switch
        old_switch_cases = self._switch_cases
        self._in_switch = True
        self._switch_cases = []

        # 1. 评估 switch 表达式
        cond_value = self._eval_expr(node.expr)

        # 2. 创建 end_bb（合并块）
        end_bb = IRBasicBlock(self._new_bb_label("switch_end"))
        self.current_function.basic_blocks.append(end_bb)

        # 3. 为每个 case/default 创建基本块并收集信息
        case_blocks = {}  # label -> basic_block
        default_label = None

        for case_node in node.cases:
            if isinstance(case_node, CaseStmtNode):
                # case 语句
                if case_node.value is None:
                    # value=None 表示 default（兼容旧设计）
                    case_label = self._new_bb_label("default")
                    default_label = case_label
                else:
                    # 正常 case 或范围 case
                    case_val = self._get_case_value(case_node.value)

                    if case_node.is_range:
                        # 【SW-005】范围 case：展开成多个 case 值，共享同一个基本块
                        end_val = self._get_case_value(case_node.end_value)
                        case_label = self._new_bb_label(
                            f"case_range_{case_val}_{end_val}"
                        )

                        # 展开范围值
                        try:
                            start_int = (
                                int(case_val)
                                if not isinstance(case_val, str)
                                else case_val
                            )
                            end_int = (
                                int(end_val)
                                if not isinstance(end_val, str)
                                else end_val
                            )
                            # 必须是整数才能展开范围
                            if isinstance(start_int, int) and isinstance(end_int, int):
                                for v in range(start_int, end_int + 1):
                                    self._switch_cases.append((v, case_label))
                            else:
                                # 非整数范围，只记录起止值
                                self._switch_cases.append((case_val, case_label))
                                self._switch_cases.append((end_val, case_label))
                        except (TypeError, ValueError):
                            # 无法展开，记录起止值
                            self._switch_cases.append((case_val, case_label))
                            self._switch_cases.append((end_val, case_label))
                    else:
                        # 单值 case
                        case_label = self._new_bb_label(f"case_{case_val}")
                        self._switch_cases.append((case_val, case_label))

                case_bb = IRBasicBlock(case_label)
                self.current_function.basic_blocks.append(case_bb)
                case_blocks[case_label] = case_bb
                # 将标签附加到节点，供 visit_case_stmt 使用
                case_node._target_label = case_label

            elif isinstance(case_node, DefaultStmtNode):
                # default 语句
                default_label = self._new_bb_label("default")
                default_bb = IRBasicBlock(default_label)
                self.current_function.basic_blocks.append(default_bb)
                case_blocks[default_label] = default_bb
                case_node._target_label = default_label

        # 4. 确定 default 标签
        if default_label is None:
            default_label = end_bb.label

        # 5. 发射 switch 指令
        # 格式: SWITCH cond, default_label, [case_val1, case_label1, case_val2, case_label2, ...]
        switch_operands = [cond_value, default_label]
        for case_val, case_label in self._switch_cases:
            switch_operands.extend([case_val, case_label])

        self._emit(Opcode.SWITCH, switch_operands)

        # 6. 设置 break 目标
        self._push_break_target(end_bb.label)

        # 7. 处理每个 case/default 的语句体
        for case_node in node.cases:
            case_node.accept(self)

        # 8. 恢复上下文
        self._pop_break_target()
        self._in_switch = old_switch
        self._switch_cases = old_switch_cases

        # 9. 确保当前块有终结指令
        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [end_bb.label])

        # 10. 切换到 end_bb
        self._switch_block(end_bb)

    def _get_case_value(self, value_node: ASTNode) -> Any:
        """从 AST 节点获取 case 值"""
        from zhc.parser.ast_nodes import (
            IntLiteralNode,
            FloatLiteralNode,
            CharLiteralNode,
            StringLiteralNode,
            IdentifierExprNode,
        )

        if isinstance(value_node, IntLiteralNode):
            # 整数字面量
            return value_node.value
        elif isinstance(value_node, FloatLiteralNode):
            # 浮点字面量
            return int(value_node.value)
        elif isinstance(value_node, CharLiteralNode):
            # 字符字面量
            return ord(value_node.value)
        elif isinstance(value_node, StringLiteralNode):
            # 字符串字面量（应该是字符）
            return ord(value_node.value[0]) if value_node.value else 0
        elif isinstance(value_node, IdentifierExprNode):
            # 标识符（可能是枚举值）
            return value_node.name
        else:
            # 其他情况，尝试获取值属性
            return getattr(value_node, "value", str(value_node))

    def visit_case_stmt(self, node: CaseStmtNode):
        """case 语句 - 生成 case 基本块的代码

        处理流程：
        1. 切换到 case 基本块
        2. 生成 case 体的代码
        3. 检查是否有 break（fall-through 处理）
        """
        # 获取目标标签
        target_label = getattr(node, "_target_label", None)
        if not target_label:
            # 如果没有预设标签，创建一个
            case_val = self._get_case_value(node.value) if node.value else "default"
            target_label = self._new_bb_label(f"case_{case_val}")
            case_bb = IRBasicBlock(target_label)
            self.current_function.basic_blocks.append(case_bb)

        # 切换到 case 基本块
        case_bb = None
        for bb in self.current_function.basic_blocks:
            if bb.label == target_label:
                case_bb = bb
                break

        if case_bb is None:
            case_bb = IRBasicBlock(target_label)
            self.current_function.basic_blocks.append(case_bb)

        self._switch_block(case_bb)

        # 生成 case 体的代码
        for stmt in node.statements:
            stmt.accept(self)

        # 检查是否需要 fall-through（没有 break 的情况下跳转到 end）
        has_break = any(self._has_break(stmt) for stmt in node.statements)
        if (
            not has_break
            and self.current_block
            and not self.current_block.is_terminated()
        ):
            # fall-through: 跳转到 switch_end
            if self._break_targets:
                self._emit(Opcode.JMP, [self._break_targets[-1]])

    def visit_default_stmt(self, node: DefaultStmtNode):
        """default 语句 - 生成 default 基本块的代码"""
        # 获取目标标签
        target_label = getattr(node, "_target_label", None)
        if not target_label:
            target_label = self._new_bb_label("default")
            default_bb = IRBasicBlock(target_label)
            self.current_function.basic_blocks.append(default_bb)

        # 切换到 default 基本块
        default_bb = None
        for bb in self.current_function.basic_blocks:
            if bb.label == target_label:
                default_bb = bb
                break

        if default_bb is None:
            default_bb = IRBasicBlock(target_label)
            self.current_function.basic_blocks.append(default_bb)

        self._switch_block(default_bb)

        # 生成 default 体的代码
        for stmt in node.statements:
            stmt.accept(self)

        # 检查是否需要 break
        has_break = any(self._has_break(stmt) for stmt in node.statements)
        if (
            not has_break
            and self.current_block
            and not self.current_block.is_terminated()
        ):
            if self._break_targets:
                self._emit(Opcode.JMP, [self._break_targets[-1]])

    def _has_break(self, stmt: ASTNode) -> bool:
        """检查语句是否包含 break"""
        from zhc.parser.ast_nodes import BreakStmtNode, BlockStmtNode

        if isinstance(stmt, BreakStmtNode):
            return True
        elif isinstance(stmt, BlockStmtNode):
            return any(self._has_break(s) for s in stmt.statements)
        return False

    def visit_goto_stmt(self, node: GotoStmtNode):
        """goto 语句"""
        self._ensure_block()
        label = getattr(node, "label", "")
        if label:
            self._emit(Opcode.JMP, [label])

    def visit_label_stmt(self, node: LabelStmtNode):
        """标签语句"""
        label = getattr(node, "name", "")
        if label:
            bb = IRBasicBlock(label)
            self.current_function.basic_blocks.append(bb)
            self._switch_block(bb)

    def visit_expr_stmt(self, node: ExprStmtNode):
        """表达式语句"""
        self._ensure_block()
        self._eval_expr(node.expr)

    # ========== P3: 高级特性 ==========

    def visit_struct_decl(self, node: StructDeclNode):
        """结构体声明"""
        struct_def = IRStructDef(name=node.name)
        for m in node.members:
            if hasattr(m, "name"):
                member_ty = self._get_type_name(getattr(m, "var_type", None))
                struct_def.add_member(m.name, member_ty)
        self.module.add_struct(struct_def)

    def visit_enum_decl(self, node: EnumDeclNode):
        """枚举声明"""
        # 枚举值作为常量处理，不生成 IR 指令
        pass

    def visit_union_decl(self, node: UnionDeclNode):
        """共用体声明"""
        struct_def = IRStructDef(name=node.name)
        for m in node.members:
            if hasattr(m, "name"):
                member_ty = self._get_type_name(getattr(m, "var_type", None))
                struct_def.add_member(m.name, member_ty)
        self.module.add_struct(struct_def)

    def visit_typedef_decl(self, node: TypedefDeclNode):
        """类型别名"""
        # typedef 不生成 IR 指令
        pass

    def visit_auto_type(self, node):
        """自动类型节点 - 类型推导在语义分析阶段完成"""
        # 自动类型节点不生成 IR 指令
        pass

    def visit_member_expr(self, node: MemberExprNode):
        """成员访问表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_array_expr(self, node: ArrayExprNode):
        """数组访问表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_cast_expr(self, node: CastExprNode):
        """类型转换表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_sizeof_expr(self, node: SizeofExprNode):
        """sizeof 表达式"""
        self._ensure_block()
        result = self._new_temp("整数型")
        # sizeof 结果为常量
        size_val = IRValue("8", "整数型", ValueKind.CONST, const_value=8)
        self._emit(Opcode.CONST, [size_val], [result])

    def visit_ternary_expr(self, node: TernaryExprNode):
        """三元表达式"""
        self._ensure_block()
        self._eval_expr(node)

    def visit_array_init(self, node: ArrayInitNode):
        """数组初始化"""
        # 数组初始化需要 ALLOC + 多个 STORE
        self._ensure_block()
        pass

    def visit_struct_init(self, node: StructInitNode):
        """结构体初始化"""
        self._ensure_block()
        pass

    # ========== P4: 模块/类型 ==========

    def visit_module_decl(self, node: ModuleDeclNode):
        """模块声明"""
        for body_node in node.body:
            body_node.accept(self)

    def visit_import_decl(self, node: ImportDeclNode):
        """导入声明"""
        # 导入声明不生成 IR 指令
        pass

    def visit_primitive_type(self, node: PrimitiveTypeNode):
        """基本类型"""
        pass

    def visit_pointer_type(self, node: PointerTypeNode):
        """指针类型"""
        pass

    def visit_array_type(self, node: ArrayTypeNode):
        """数组类型"""
        pass

    def visit_function_type(self, node: FunctionTypeNode):
        """函数类型"""
        pass

    def visit_struct_type(self, node: StructTypeNode):
        """结构体类型"""
        pass

    # ========== P5: 异常处理 ==========

    def visit_try_stmt(self, node: TryStmtNode):
        """try 语句 → 生成异常处理 IR

        生成结构：
        1. try_body 块：执行可能抛出异常的代码
        2. landingpad 块：异常分发
        3. catch 块：处理特定类型异常
        4. finally 块（如果有）：清理代码

        try 块使用 INVOKE 指令包装可能抛出异常的函数调用，
        正常返回时跳转到下一个块，异常时跳转到 landingpad。
        """
        self._ensure_block()

        # 创建异常处理所需的基本块
        try_label = self._new_bb_label("try")
        landingpad_label = self._new_bb_label("landingpad")
        catch_labels = []
        finally_label = self._new_bb_label("finally") if node.finally_clause else None
        merge_label = self._new_bb_label("try_merge")

        # 创建基本块
        try_bb = IRBasicBlock(try_label)
        landingpad_bb = IRBasicBlock(landingpad_label)
        self.current_function.basic_blocks.append(try_bb)
        self.current_function.basic_blocks.append(landingpad_bb)

        # 为每个 catch clause 创建基本块
        for i, catch_clause in enumerate(node.catch_clauses):
            catch_label = self._new_bb_label(f"catch_{i}")
            catch_bb = IRBasicBlock(catch_label)
            self.current_function.basic_blocks.append(catch_bb)
            catch_labels.append(catch_label)
            catch_clause._target_label = catch_label

        # 创建 finally 块
        if finally_label:
            finally_bb = IRBasicBlock(finally_label)
            self.current_function.basic_blocks.append(finally_bb)

        # 创建 merge 块
        merge_bb = IRBasicBlock(merge_label)
        self.current_function.basic_blocks.append(merge_bb)

        # 保存当前块，然后切换到 try 块
        self._switch_block(try_bb)

        # 生成 try body
        old_try_context = getattr(self, "_try_context", None)
        self._try_context = {
            "landingpad_label": landingpad_label,
            "catch_labels": catch_labels,
            "finally_label": finally_label,
            "merge_label": merge_label,
            "exception_var": "__exception",
        }

        node.body.accept(self)

        # try 块结束后跳转到 merge（如果没有异常）
        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [merge_label])

        self._try_context = old_try_context

        # landingpad 块：接收异常
        self._switch_block(landingpad_bb)

        # 生成 landingpad 指令
        lp_result = self._new_temp()
        # 使用 LANDINGPAD 操作码
        self._emit(Opcode.LANDINGPAD, [], [lp_result])

        # 根据异常类型分发到对应的 catch 块
        # 这里简化为直接跳转到第一个 catch 块（实际需要类型检查）
        if catch_labels:
            self._emit(Opcode.JMP, [catch_labels[0]])

        # 生成 catch 块
        for i, catch_clause in enumerate(node.catch_clauses):
            self.current_function.basic_blocks[
                self.current_function.basic_blocks.index(
                    next(
                        bb
                        for bb in self.current_function.basic_blocks
                        if bb.label == catch_labels[i]
                    )
                )
            ]
            self._switch_block(
                next(
                    bb
                    for bb in self.current_function.basic_blocks
                    if bb.label == catch_labels[i]
                )
            )
            catch_clause.accept(self)

            # catch 块结束后跳转到 finally 或 merge
            if self.current_block and not self.current_block.is_terminated():
                if finally_label:
                    self._emit(Opcode.JMP, [finally_label])
                else:
                    self._emit(Opcode.JMP, [merge_label])

        # 生成 finally 块
        if finally_label and node.finally_clause:
            self._switch_block(
                next(
                    bb
                    for bb in self.current_function.basic_blocks
                    if bb.label == finally_label
                )
            )
            node.finally_clause.accept(self)

            # finally 块结束后跳转到 merge
            if self.current_block and not self.current_block.is_terminated():
                self._emit(Opcode.JMP, [merge_label])

        # 切换到 merge 块
        self._switch_block(
            next(
                bb
                for bb in self.current_function.basic_blocks
                if bb.label == merge_label
            )
        )

    def visit_throw_stmt(self, node: ThrowStmtNode):
        """throw 语句 → 生成 throw IR

        抛出异常时，需要：
        1. 创建异常对象
        2. 使用 RESUME 指令恢复异常（或通过 landingpad 分发）
        """
        self._ensure_block()

        exception_value = None
        if node.exception:
            exception_value = self._eval_expr(node.exception)

        # 使用 THROW 操作码发射 IR
        if exception_value:
            self._emit(Opcode.THROW, [exception_value])
        else:
            self._emit(Opcode.THROW)

    def visit_catch_clause(self, node: CatchClauseNode):
        """catch 子句 → 生成 catch 处理器 IR

        catch 块负责：
        1. 接收异常对象
        2. 绑定到异常变量
        3. 执行处理代码
        """
        self._ensure_block()

        # 如果有异常变量，分配并存储
        if node.variable_name:
            # 分配异常变量
            var_value = IRValue(name=node.variable_name, ty="i8*", kind=ValueKind.VAR)
            alloc_result = self._new_temp("i8*")
            self._emit(Opcode.ALLOC, [var_value], [alloc_result])

            # 从当前上下文获取异常对象
            if hasattr(self, "_try_context") and self._try_context:
                exc_var = self._try_context.get("exception_var", "__exception")
                exc_ptr = self.var_ptr_map.get(exc_var)
                if exc_ptr:
                    self._emit(Opcode.STORE, [exc_ptr, alloc_result])

        # 生成 catch body
        if node.body:
            node.body.accept(self)

    def visit_finally_clause(self, node: FinallyClauseNode):
        """finally 子句 → 生成 finally 块 IR

        finally 块始终执行，用于清理资源。
        """
        self._ensure_block()

        # 生成 finally body
        if node.body:
            node.body.accept(self)

    # ========== 协程/异步表达式访问方法 ==========

    def visit_coroutine_def(self, node: "CoroutineDefNode"):
        """协程定义 → 生成协程 IR

        协程定义创建一个新的协程类型函数。
        """
        self._ensure_block()

        # 创建协程函数
        coroutine_name = f"coroutine_{node.name}"

        # 为协程参数创建形参
        param_values = []
        for param in node.params:
            param_value = self._new_temp()
            param_values.append(param_value)

        # 创建协程基本块
        entry_label = self._new_bb_label(f"{coroutine_name}_entry")
        entry_bb = IRBasicBlock(entry_label)
        self.current_function.basic_blocks.append(entry_bb)

        # 切换到入口块
        self._switch_block(entry_bb)

        # 生成函数体
        if node.body:
            node.body.accept(self)

    def visit_await_expr(self, node: "AwaitExprNode"):
        """等待表达式 → 生成等待协程 IR

        等待一个协程完成并获取其结果。
        """
        self._ensure_block()

        # 生成被等待的表达式
        node.expression.accept(self)

        # 创建协程等待指令
        result = self._new_temp()
        self._emit(Opcode.COROUTINE_AWAIT, [], [result])

        # 将结果存储为当前值
        self.current_value = result

    def visit_channel_expr(self, node: "ChannelExprNode"):
        """通道表达式 → 生成通道创建 IR

        创建一个新的通道。
        """
        self._ensure_block()

        # 创建通道元素类型
        node.element_type.accept(self)
        element_type_result = self.current_value

        # 创建通道创建指令
        result = self._new_temp()
        self._emit(
            Opcode.CHANNEL_CREATE,
            [element_type_result, self._make_integer_constant(node.buffer_size)],
            [result],
        )

        # 将结果存储为当前值
        self.current_value = result

    def visit_spawn_expr(self, node: "SpawnExprNode"):
        """启动协程表达式 → 生成启动协程 IR

        启动一个协程并返回其句柄。
        """
        self._ensure_block()

        # 生成协程表达式
        node.coroutine.accept(self)

        # 创建协程启动指令
        result = self._new_temp()
        self._emit(Opcode.COROUTINE_SPAWN, [], [result])

        # 将结果存储为当前值
        self.current_value = result

    def visit_yield_expr(self, node: "YieldExprNode"):
        """让出表达式 → 生成协程让出 IR

        让出协程执行权，可选地返回一个值。
        """
        self._ensure_block()

        # 如果有值，生成值表达式
        if node.value:
            node.value.accept(self)
            value_result = self.current_value
        else:
            value_result = None

        # 创建协程让出指令
        self._emit(Opcode.COROUTINE_YIELD, [value_result] if value_result else [])

    # ========== 宽字符/字符串支持（避免抽象类错误）==========

    def visit_wide_char_literal(self, node):
        """宽字符字面量"""
        pass

    def visit_wide_string_literal(self, node):
        """宽字符串字面量"""
        pass

    def visit_wide_char_type(self, node):
        """宽字符类型"""
        pass

    def visit_wide_string_type(self, node):
        """宽字符串类型"""
        pass

    def visit_complex_type(self, node):
        """复数类型"""
        pass

    def visit_complex_literal(self, node):
        """复数字面量"""
        pass

    def visit_fixed_point_type(self, node):
        """定点数类型"""
        pass

    # ========== 内存管理（智能指针/移动语义）==========

    def visit_smart_ptr_type(self, node):
        """智能指针类型 — 纯类型节点，无需生成 IR"""
        pass

    def visit_smart_ptr_decl(self, node):
        """智能指针声明"""
        self._ensure_block()
        self._eval_smart_ptr_decl(node)

    def visit_move_expr(self, node):
        """移动语义表达式"""
        self._ensure_block()
        self._eval_move(node)
