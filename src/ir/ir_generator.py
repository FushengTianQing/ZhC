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

from typing import Optional, List, Any

from zhpp.parser.ast_nodes import (
    ASTVisitor, ASTNode,
    ProgramNode, ModuleDeclNode, ImportDeclNode,
    FunctionDeclNode, StructDeclNode, VariableDeclNode, ParamDeclNode,
    EnumDeclNode, UnionDeclNode, TypedefDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    DoWhileStmtNode, BreakStmtNode, ContinueStmtNode, ReturnStmtNode,
    SwitchStmtNode, CaseStmtNode, DefaultStmtNode, ExprStmtNode,
    GotoStmtNode, LabelStmtNode,
    BinaryExprNode, UnaryExprNode, AssignExprNode, CallExprNode,
    MemberExprNode, ArrayExprNode, IdentifierExprNode,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode, CharLiteralNode,
    BoolLiteralNode, NullLiteralNode,
    TernaryExprNode, SizeofExprNode, CastExprNode,
    ArrayInitNode, StructInitNode,
    PrimitiveTypeNode, PointerTypeNode, ArrayTypeNode,
    FunctionTypeNode, StructTypeNode,
)

from zhpp.ir.program import IRProgram, IRFunction, IRStructDef, IRGlobalVar
from zhpp.ir.instructions import IRBasicBlock, IRInstruction
from zhpp.ir.values import IRValue, ValueKind
from zhpp.ir.opcodes import Opcode


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

    def _emit(self, opcode: Opcode, operands: List[IRValue] = None,
              result: List[IRValue] = None) -> Optional[IRValue]:
        """发射 IR 指令"""
        if operands is None:
            operands = []
        if result is None:
            result = []
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
        if hasattr(type_node, 'name'):
            return type_node.name
        return str(type_node)

    def _resolve_function_name(self, name: str) -> str:
        """解析中文函数名为 C 函数名"""
        # 中文函数名映射
        FUNCTION_MAP = {
            '主函数': 'main',
            '主程序': 'main',
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

        # 初始化
        if node.init:
            init_result = self._eval_expr(node.init)
            if init_result:
                self._emit(Opcode.STORE, [init_result, alloc_result])

    def visit_param_decl(self, node: ParamDeclNode):
        """参数声明 → PARAM"""
        ty = self._get_type_name(node.param_type)
        pv = IRValue(name=node.name, ty=ty, kind=ValueKind.PARAM)
        self.current_function.params.append(pv)

        # 也在基本块中声明
        alloc_result = self._new_temp(ty)
        self._emit(Opcode.ALLOC, [pv], [alloc_result])
        self._emit(Opcode.STORE, [pv], [alloc_result])

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
                self._emit(Opcode.RET, [result])
            else:
                self._emit(Opcode.RET)
        else:
            self._emit(Opcode.RET)

    # ========== P1: 表达式 ==========

    # =========================================================================
    # 表达式求值 — _eval_expr 分派 + 10个子方法
    # =========================================================================

    def _eval_expr(self, node: ASTNode) -> Optional[IRValue]:
        """
        求值表达式，返回结果 IRValue。

        将表达式分派到具体的求值方法。
        """
        if node is None:
            return None

        nt = node.node_type.name if hasattr(node, 'node_type') else str(type(node))

        # 字面量
        if nt == 'INT_LITERAL':
            return self._eval_literal(node, '整数型', int(getattr(node, 'value', 0)))
        if nt == 'FLOAT_LITERAL':
            return self._eval_literal(node, '双精度浮点型', float(getattr(node, 'value', 0.0)))
        if nt == 'STRING_LITERAL':
            val = getattr(node, 'value', '')
            return self._eval_literal(node, '字符串型', f'"{val}"', is_string=True)
        if nt == 'CHAR_LITERAL':
            val = getattr(node, 'value', '0')
            return self._eval_literal(node, '字符型', f"'{val}'", is_string=True)
        if nt == 'BOOL_LITERAL':
            return self._eval_literal(node, '布尔型', getattr(node, 'value', False))
        if nt == 'NULL_LITERAL':
            return self._eval_literal(node, '空型', 0)

        # 标识符
        if nt == 'IDENTIFIER_EXPR':
            return self._eval_identifier(node)

        # 二元表达式
        if nt == 'BINARY_EXPR':
            return self._eval_binary(node)

        # 一元表达式
        if nt == 'UNARY_EXPR':
            return self._eval_unary(node)

        # 赋值表达式
        if nt == 'ASSIGN_EXPR':
            return self._eval_assignment(node)

        # 函数调用
        if nt == 'CALL_EXPR':
            return self._eval_call(node)

        # 成员访问
        if nt == 'MEMBER_EXPR':
            return self._eval_member(node)

        # 数组访问
        if nt == 'ARRAY_EXPR':
            return self._eval_array(node)

        # 三元表达式
        if nt == 'TERNARY_EXPR':
            return self._eval_ternary(node)

        # 类型转换
        if nt == 'CAST_EXPR':
            return self._eval_cast(node)

        return None

    def _eval_literal(self, node: ASTNode, type_name: str, value: Any, is_string: bool = False) -> IRValue:
        """求值字面量：INT/FLOAT/STRING/CHAR/BOOL/NULL"""
        return IRValue(str(value), type_name, ValueKind.CONST, const_value=value)

    def _eval_identifier(self, node: ASTNode) -> IRValue:
        """求值标识符表达式"""
        name = getattr(node, 'name', '')
        ty = getattr(node, 'inferred_type', '整数型')
        return IRValue(name, ty, ValueKind.VAR)

    def _eval_binary(self, node: ASTNode) -> Optional[IRValue]:
        """求值二元表达式"""
        left = self._eval_expr(getattr(node, 'left', None))
        right = self._eval_expr(getattr(node, 'right', None))
        op = getattr(node, 'operator', getattr(node, 'op', '+'))
        op = op.upper() if isinstance(op, str) else str(op)
        try:
            opcode = Opcode[op]
        except (KeyError, ValueError):
            opcode = Opcode.ADD
        result = self._new_temp()
        self._emit(opcode, [left, right], [result])
        return result

    def _eval_unary(self, node: ASTNode) -> Optional[IRValue]:
        """求值一元表达式"""
        operand = self._eval_expr(getattr(node, 'operand', None))
        op = getattr(node, 'operator', getattr(node, 'op', '-'))
        if op in ('-', '!'):
            opcode = Opcode.NEG if op == '-' else Opcode.L_NOT
            result = self._new_temp()
            self._emit(opcode, [operand] if operand else [], [result])
            return result
        return None

    def _eval_assignment(self, node: ASTNode) -> Optional[IRValue]:
        """求值赋值表达式"""
        value = self._eval_expr(getattr(node, 'value', None))
        target = self._eval_expr(getattr(node, 'target', None))
        if value:
            self._emit(Opcode.STORE, [value, target] if target else [value])
        return value

    def _eval_call(self, node: ASTNode) -> Optional[IRValue]:
        """求值函数调用表达式"""
        callee = getattr(node, 'callee', None)
        func_name = getattr(callee, 'name', 'unknown') if callee else 'unknown'
        args = []
        for arg in getattr(node, 'args', []):
            arg_val = self._eval_expr(arg)
            if arg_val:
                args.append(arg_val)
        result = self._new_temp()
        func_val = IRValue(func_name, kind=ValueKind.FUNCTION)
        self._emit(Opcode.CALL, [func_val] + args, [result])
        return result

    def _eval_member(self, node: ASTNode) -> Optional[IRValue]:
        """求值成员访问表达式"""
        obj = self._eval_expr(getattr(node, 'obj', None))
        result = self._new_temp()
        self._emit(Opcode.GETPTR, [obj] if obj else [], [result])
        return result

    def _eval_array(self, node: ASTNode) -> Optional[IRValue]:
        """求值数组访问表达式"""
        base = self._eval_expr(getattr(node, 'object', None))
        index = self._eval_expr(getattr(node, 'index', None))
        result = self._new_temp()
        self._emit(Opcode.GEP, [base, index] if index else [base], [result])
        return result

    def _eval_ternary(self, node: ASTNode) -> Optional[IRValue]:
        """求值三元表达式（条件 ? then : else）"""
        cond = self._eval_expr(getattr(node, 'condition', None))
        then_val = self._eval_expr(getattr(node, 'then_expr', None))
        else_val = self._eval_expr(getattr(node, 'else_expr', None))
        result = self._new_temp()
        # 实现为条件跳转
        then_bb_label = self._new_bb_label("ternary_then")
        else_bb_label = self._new_bb_label("ternary_else")
        merge_bb_label = self._new_bb_label("ternary_merge")
        self.current_function.basic_blocks.append(IRBasicBlock(then_bb_label))
        self.current_function.basic_blocks.append(IRBasicBlock(else_bb_label))
        self.current_function.basic_blocks.append(IRBasicBlock(merge_bb_label))
        self._emit(Opcode.JZ, [cond, else_bb_label] if cond else [])
        self._emit(Opcode.JMP, [then_bb_label])
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
        operand = self._eval_expr(getattr(node, 'operand', None))
        target_type = self._get_type_name(getattr(node, 'target_type', None))
        result = self._new_temp(target_type)
        if operand:
            self._emit(Opcode.BITCAST, [operand], [result])
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

        # 条件跳转
        if cond:
            self._emit(Opcode.JZ, [cond, else_bb.label])
        self._emit(Opcode.JMP, [then_bb.label])

        # then 分支
        old_block = self.current_block
        self._switch_block(then_bb)
        node.then_branch.accept(self)
        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [merge_bb.label])
        old_block.add_successor(then_bb.label)
        old_block.add_successor(else_bb.label)
        then_bb.add_predecessor(old_block.label)

        # else 分支
        self._switch_block(else_bb)
        if node.else_branch:
            node.else_branch.accept(self)
        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [merge_bb.label])
        then_bb.add_successor(merge_bb.label)
        else_bb.add_predecessor(old_block.label)

        # merge 基本块
        self._switch_block(merge_bb)

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
        old_block = self.current_block
        self._emit(Opcode.JMP, [cond_bb.label])

        # 条件块
        self._switch_block(cond_bb)
        cond = self._eval_expr(node.condition)
        if cond:
            self._emit(Opcode.JZ, [cond, body_bb.label])
        self._emit(Opcode.JMP, [end_bb.label])

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
        if cond:
            self._emit(Opcode.JZ, [cond, body_bb.label])
        self._emit(Opcode.JMP, [end_bb.label])

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

        old_block = self.current_block
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
        if cond:
            self._emit(Opcode.JZ, [cond, body_bb.label])
        self._emit(Opcode.JMP, [end_bb.label])
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
        """switch 语句"""
        self._ensure_block()
        old_switch = self._in_switch
        self._in_switch = True

        expr = self._eval_expr(node.expr)

        end_bb = IRBasicBlock(self._new_bb_label("switch_end"))
        self.current_function.basic_blocks.append(end_bb)
        self._push_break_target(end_bb.label)

        old_block = self.current_block

        # 处理 case
        if node.cases:
            for case in node.cases:
                case.accept(self)

        self._pop_break_target()
        self._in_switch = old_switch

        if self.current_block and not self.current_block.is_terminated():
            self._emit(Opcode.JMP, [end_bb.label])

        self._switch_block(end_bb)

    def visit_case_stmt(self, node: CaseStmtNode):
        """case 语句"""
        # case 不生成独立基本块，由 switch_stmt 处理
        pass

    def visit_default_stmt(self, node: DefaultStmtNode):
        """default 语句"""
        pass

    def visit_goto_stmt(self, node: GotoStmtNode):
        """goto 语句"""
        self._ensure_block()
        label = getattr(node, 'label', '')
        if label:
            self._emit(Opcode.JMP, [label])

    def visit_label_stmt(self, node: LabelStmtNode):
        """标签语句"""
        label = getattr(node, 'name', '')
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
            if hasattr(m, 'name'):
                member_ty = self._get_type_name(getattr(m, 'var_type', None))
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
            if hasattr(m, 'name'):
                member_ty = self._get_type_name(getattr(m, 'var_type', None))
                struct_def.add_member(m.name, member_ty)
        self.module.add_struct(struct_def)

    def visit_typedef_decl(self, node: TypedefDeclNode):
        """类型别名"""
        # typedef 不生成 IR 指令
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
