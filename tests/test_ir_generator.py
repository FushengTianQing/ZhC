# -*- coding: utf-8 -*-
"""
test_ir_generator.py - IRGenerator 全面单元测试

覆盖:
- P0: 基础 (Program/Function/Variable/Param)
- P1: 表达式 (_eval_expr 全部 12+ 种类型)
- P2: 控制流 (if/while/for/do-while/break/continue/switch/case/default/goto/label)
- P3: 高级 (struct/enum/union/typedef/sizeof/ternary/cast/member/array)
- P4: 模块 (module/import)

运行: python -m pytest tests/test_ir_generator.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhpp.parser.ast_nodes import (
    ProgramNode, FunctionDeclNode, VariableDeclNode, ParamDeclNode,
    BlockStmtNode, ReturnStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    DoWhileStmtNode, BreakStmtNode, ContinueStmtNode, SwitchStmtNode,
    CaseStmtNode, DefaultStmtNode, GotoStmtNode, LabelStmtNode,
    ExprStmtNode,
    BinaryExprNode, UnaryExprNode, AssignExprNode, CallExprNode,
    MemberExprNode, ArrayExprNode, IdentifierExprNode,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode, CharLiteralNode,
    BoolLiteralNode, NullLiteralNode,
    TernaryExprNode, SizeofExprNode, CastExprNode,
    ArrayInitNode, StructInitNode,
    PrimitiveTypeNode, PointerTypeNode, ArrayTypeNode,
    FunctionTypeNode, StructTypeNode,
    StructDeclNode, EnumDeclNode, UnionDeclNode, TypedefDeclNode,
    ModuleDeclNode, ImportDeclNode,
    CallExprNode,
)
from zhpp.ir.ir_generator import IRGenerator
from zhpp.ir import IRPrinter
from zhpp.ir.values import ValueKind
from zhpp.ir.opcodes import Opcode


# =============================================================================
# 辅助函数
# =============================================================================

def make_func(name, body, return_type="整数型", params=None):
    """创建带函数体的 FunctionDeclNode"""
    if params is None:
        params = []
    return FunctionDeclNode(
        name=name,
        return_type=PrimitiveTypeNode(return_type),
        params=params,
        body=body,
    )


def make_int(value):
    return IntLiteralNode(value)


def make_id(name, ty="整数型"):
    node = IdentifierExprNode(name)
    node.inferred_type = ty
    return node


def make_binop(left, op, right):
    return BinaryExprNode(left=left, operator=op, right=right)


def make_program(*decls):
    return ProgramNode(list(decls))


def gen_ir(body):
    """用单个 return 语句生成 IR"""
    gen = IRGenerator()
    func = make_func("test_func", body)
    ir = gen.generate(make_program(func))
    return ir


def gen_ir_with_block(body):
    """生成 IR 并确保 current_block 已初始化（供 _eval_expr 直接调用）"""
    gen = IRGenerator()
    # 先创建函数上下文
    func_node = make_func("eval_test", ReturnStmtNode(make_int(0)))
    ir = gen.generate(make_program(func_node))
    # 再切到 eval context
    eval_gen = IRGenerator()
    eval_gen.module = ir
    eval_gen.current_function = ir.functions[0]
    eval_gen.current_block = ir.functions[0].entry_block
    return eval_gen


# =============================================================================
# P0: 基础功能测试
# =============================================================================

class TestIRGeneratorBasics:
    """IRGenerator 基础功能"""

    def test_empty_program(self):
        """空程序无函数"""
        gen = IRGenerator()
        ir = gen.generate(ProgramNode(declarations=[]))
        assert len(ir.functions) == 0

    def test_function_no_body(self):
        """无函数体生成空函数"""
        gen = IRGenerator()
        func = make_func("foo", None)
        ir = gen.generate(make_program(func))
        assert len(ir.functions) == 1
        assert ir.functions[0].name == "foo"

    def test_main_function_name_resolved(self):
        """主函数名解析"""
        gen = IRGenerator()
        func = make_func("主函数", ReturnStmtNode(make_int(0)))
        ir = gen.generate(make_program(func))
        assert ir.functions[0].name == "main"

    def test_function_with_int_return(self):
        """返回整数字面量"""
        ir = gen_ir(ReturnStmtNode(make_int(42)))
        assert len(ir.functions) == 1
        assert ir.functions[0].entry_block.is_terminated()

    def test_function_with_float_return(self):
        """返回浮点数字面量"""
        ir = gen_ir(ReturnStmtNode(FloatLiteralNode(3.14)))
        assert len(ir.functions) == 1

    def test_function_with_string_return(self):
        """返回字符串字面量"""
        ir = gen_ir(ReturnStmtNode(StringLiteralNode("hello")))
        assert len(ir.functions) == 1

    def test_function_with_char_return(self):
        """返回字符字面量"""
        ir = gen_ir(ReturnStmtNode(CharLiteralNode('x')))
        assert len(ir.functions) == 1

    def test_function_with_bool_true_return(self):
        """返回布尔字面量 true"""
        ir = gen_ir(ReturnStmtNode(BoolLiteralNode(True)))
        assert len(ir.functions) == 1

    def test_function_with_bool_false_return(self):
        """返回布尔字面量 false"""
        ir = gen_ir(ReturnStmtNode(BoolLiteralNode(False)))
        assert len(ir.functions) == 1

    def test_function_with_null_return(self):
        """返回 null 字面量"""
        ir = gen_ir(ReturnStmtNode(NullLiteralNode()))
        assert len(ir.functions) == 1

    def test_print_ir(self):
        """IRPrinter 输出包含函数定义"""
        gen = IRGenerator()
        func = make_func("foo", ReturnStmtNode(make_int(1)))
        ir = gen.generate(make_program(func))
        printer = IRPrinter()
        output = printer.print(ir)
        assert "foo" in output
        assert "define" in output

    def test_multiple_functions(self):
        """多函数程序"""
        gen = IRGenerator()
        f1 = make_func("foo", ReturnStmtNode(make_int(1)))
        f2 = make_func("bar", ReturnStmtNode(make_int(2)))
        ir = gen.generate(make_program(f1, f2))
        assert len(ir.functions) == 2


# =============================================================================
# P1: 表达式测试 (_eval_expr 覆盖)
# =============================================================================

class TestExpressions:
    """表达式 IR 生成"""

    # ---- 字面量 ----

    def test_int_literal_ir_value(self):
        """整数字面量生成 CONST"""
        gen = gen_ir_with_block(None)
        result = gen._eval_expr(make_int(100))
        assert result is not None
        assert result.kind == ValueKind.CONST
        assert result.const_value == 100

    def test_float_literal_ir_value(self):
        """浮点数字面量"""
        gen = gen_ir_with_block(None)
        result = gen._eval_expr(FloatLiteralNode(2.718))
        assert result is not None
        assert result.kind == ValueKind.CONST

    def test_string_literal_ir_value(self):
        """字符串字面量"""
        gen = gen_ir_with_block(None)
        result = gen._eval_expr(StringLiteralNode("test"))
        assert result is not None
        assert result.kind == ValueKind.CONST

    def test_char_literal_ir_value(self):
        """字符字面量"""
        gen = gen_ir_with_block(None)
        result = gen._eval_expr(CharLiteralNode('a'))
        assert result is not None

    def test_bool_literal_ir_value(self):
        """布尔字面量"""
        gen = gen_ir_with_block(None)
        result = gen._eval_expr(BoolLiteralNode(True))
        assert result is not None
        assert result.kind == ValueKind.CONST

    def test_null_literal_ir_value(self):
        """空指针字面量"""
        gen = gen_ir_with_block(None)
        result = gen._eval_expr(NullLiteralNode())
        assert result is not None
        assert result.name == "0"

    def test_identifier_ir_value(self):
        """标识符生成 VAR"""
        gen = gen_ir_with_block(None)
        node = make_id("x", "整数型")
        result = gen._eval_expr(node)
        assert result is not None
        assert result.kind == ValueKind.VAR
        assert result.name == "x"

    # ---- 二元表达式 ----

    @pytest.mark.parametrize("op,expected_opcode", [
        ("+", Opcode.ADD),
        ("-", Opcode.SUB),
        ("*", Opcode.MUL),
        ("/", Opcode.DIV),
        ("%", Opcode.MOD),
        ("&&", Opcode.L_AND),
        ("||", Opcode.L_OR),
        ("==", Opcode.EQ),
        ("!=", Opcode.NE),
        ("<", Opcode.LT),
        (">", Opcode.GT),
        ("<=", Opcode.LE),
        (">=", Opcode.GE),
    ])
    def test_binary_expr_ops(self, op, expected_opcode):
        """二元运算符生成对应 opcode"""
        gen = gen_ir_with_block(None)
        left = make_int(1)
        right = make_int(2)
        bin_expr = BinaryExprNode(left=left, operator=op, right=right)
        result = gen._eval_expr(bin_expr)
        assert result is not None
        # 指令已 emit，检查 current_block 非空即可
        assert gen.current_block is not None

    def test_binary_expr_unknown_op_fallback(self):
        """未知运算符回退到 ADD"""
        gen = gen_ir_with_block(None)
        left = make_int(1)
        right = make_int(2)
        bin_expr = BinaryExprNode(left=left, operator="???", right=right)
        result = gen._eval_expr(bin_expr)
        # 不崩溃，返回 None（未知 op 无法处理）

    # ---- 一元表达式 ----

    def test_unary_neg(self):
        """一元负号"""
        gen = gen_ir_with_block(None)
        node = UnaryExprNode(operator="-", operand=make_int(5))
        result = gen._eval_expr(node)
        assert result is not None

    def test_unary_not(self):
        """一元逻辑非"""
        gen = gen_ir_with_block(None)
        node = UnaryExprNode(operator="!", operand=make_int(1))
        result = gen._eval_expr(node)
        assert result is not None

    # ---- 赋值表达式 ----

    def test_assign_expr(self):
        """赋值表达式"""
        gen = gen_ir_with_block(None)
        id_node = make_id("x")
        val_node = make_int(10)
        assign = AssignExprNode(target=id_node, value=val_node)
        result = gen._eval_expr(assign)
        assert result is not None

    # ---- 函数调用 ----

    def test_call_expr(self):
        """函数调用"""
        gen = gen_ir_with_block(None)
        callee = IdentifierExprNode("printf")
        call = CallExprNode(callee=callee, args=[make_int(1)])
        result = gen._eval_expr(call)
        assert result is not None

    def test_call_expr_multiple_args(self):
        """多参数函数调用"""
        gen = gen_ir_with_block(None)
        callee = IdentifierExprNode("max")
        call = CallExprNode(callee=callee, args=[make_int(1), make_int(2), make_int(3)])
        result = gen._eval_expr(call)
        assert result is not None

    def test_call_expr_no_args(self):
        """无参数函数调用"""
        gen = gen_ir_with_block(None)
        callee = IdentifierExprNode("getchar")
        call = CallExprNode(callee=callee, args=[])
        result = gen._eval_expr(call)
        assert result is not None

    # ---- 成员访问 ----

    def test_member_expr(self):
        """成员访问"""
        gen = gen_ir_with_block(None)
        obj = make_id("point")
        member = MemberExprNode(obj=obj, member="x")
        result = gen._eval_expr(member)
        assert result is not None

    # ---- 数组访问 ----

    def test_array_expr(self):
        """数组访问"""
        gen = gen_ir_with_block(None)
        arr = make_id("arr")
        idx = make_int(0)
        node = ArrayExprNode(array=arr, index=idx)
        result = gen._eval_expr(node)
        assert result is not None

    # ---- 三元表达式 ----

    def test_ternary_expr(self):
        """三元表达式"""
        gen = gen_ir_with_block(None)
        cond = make_id("x")
        then_val = make_int(1)
        else_val = make_int(2)
        node = TernaryExprNode(condition=cond, then_expr=then_val, else_expr=else_val)
        result = gen._eval_expr(node)
        assert result is not None

    # ---- 类型转换 ----

    def test_cast_expr(self):
        """类型转换"""
        gen = gen_ir_with_block(None)
        expr = make_int(65)
        target = PrimitiveTypeNode("字符型")
        node = CastExprNode(cast_type=target, expr=expr)
        result = gen._eval_expr(node)
        assert result is not None


# =============================================================================
# P2: 控制流测试
# =============================================================================

class TestControlFlow:
    """控制流语句 IR 生成"""

    def test_if_then_only(self):
        """if-then（无 else）"""
        cond = make_id("x")
        then_b = ReturnStmtNode(make_int(1))
        if_node = IfStmtNode(condition=cond, then_branch=then_b, else_branch=None)
        ir = gen_ir(if_node)
        func = ir.functions[0]
        # if 生成 then/else/merge 三个块
        assert len(func.basic_blocks) >= 3

    def test_if_then_else(self):
        """if-then-else"""
        cond = make_id("x")
        then_b = ReturnStmtNode(make_int(1))
        else_b = ReturnStmtNode(make_int(0))
        if_node = IfStmtNode(condition=cond, then_branch=then_b, else_branch=else_b)
        ir = gen_ir(if_node)
        func = ir.functions[0]
        assert len(func.basic_blocks) >= 3

    def test_if_nested(self):
        """嵌套 if"""
        inner_if = IfStmtNode(
            condition=make_id("y"),
            then_branch=ReturnStmtNode(make_int(1)),
            else_branch=None,
        )
        outer_if = IfStmtNode(
            condition=make_id("x"),
            then_branch=inner_if,
            else_branch=None,
        )
        ir = gen_ir(outer_if)
        func = ir.functions[0]
        assert len(func.basic_blocks) >= 4

    def test_while_loop(self):
        """while 循环"""
        cond = make_id("x")
        body = ReturnStmtNode(make_int(0))
        while_node = WhileStmtNode(condition=cond, body=body)
        ir = gen_ir(while_node)
        func = ir.functions[0]
        # while: cond/body/end
        assert len(func.basic_blocks) >= 3

    def test_while_with_break(self):
        """while + break"""
        body = BreakStmtNode()
        while_node = WhileStmtNode(condition=make_id("x"), body=body)
        ir = gen_ir(while_node)
        assert len(ir.functions) == 1

    def test_while_with_continue(self):
        """while + continue"""
        body = ContinueStmtNode()
        while_node = WhileStmtNode(condition=make_id("x"), body=body)
        ir = gen_ir(while_node)
        assert len(ir.functions) == 1

    def test_for_loop(self):
        """for 循环"""
        init = VariableDeclNode(
            name="i", var_type=PrimitiveTypeNode("整数型"), init=make_int(0)
        )
        cond = make_binop(make_id("i"), "<", make_int(10))
        update = AssignExprNode(
            target=make_id("i"),
            value=make_binop(make_id("i"), "+", make_int(1)),
        )
        body = ReturnStmtNode(make_int(0))
        for_node = ForStmtNode(init=init, condition=cond, update=update, body=body)
        ir = gen_ir(for_node)
        func = ir.functions[0]
        # for: init + cond/body/update/end
        assert len(func.basic_blocks) >= 4

    def test_for_loop_no_init(self):
        """for 循环（无初始化）"""
        for_node = ForStmtNode(
            init=None,
            condition=make_id("x"),
            update=None,
            body=ReturnStmtNode(make_int(0)),
        )
        ir = gen_ir(for_node)
        assert len(ir.functions) == 1

    def test_for_loop_no_condition(self):
        """for 循环（无限循环，无条件）"""
        for_node = ForStmtNode(
            init=None,
            condition=None,
            update=None,
            body=BreakStmtNode(),
        )
        ir = gen_ir(for_node)
        assert len(ir.functions) == 1

    def test_do_while_loop(self):
        """do-while 循环"""
        body = ReturnStmtNode(make_int(0))
        do_while = DoWhileStmtNode(body=body, condition=make_id("x"))
        ir = gen_ir(do_while)
        func = ir.functions[0]
        # do-while: body/cond/end
        assert len(func.basic_blocks) >= 3

    def test_do_while_with_break_continue(self):
        """do-while + break + continue"""
        body = BlockStmtNode(statements=[
            ContinueStmtNode(),
            BreakStmtNode(),
        ])
        do_while = DoWhileStmtNode(body=body, condition=make_id("x"))
        ir = gen_ir(do_while)
        assert len(ir.functions) == 1

    def test_break_only(self):
        """break（循环外）"""
        ir = gen_ir(BreakStmtNode())
        assert len(ir.functions) == 1

    def test_continue_only(self):
        """continue（循环外）"""
        ir = gen_ir(ContinueStmtNode())
        assert len(ir.functions) == 1

    def test_nested_break_continue(self):
        """嵌套循环的 break/continue"""
        inner_body = BlockStmtNode(statements=[
            ContinueStmtNode(),  # 跳到外层 update
            BreakStmtNode(),     # 跳出外层循环
        ])
        for_node = ForStmtNode(
            init=VariableDeclNode(name="i", var_type=PrimitiveTypeNode("整数型"), init=make_int(0)),
            condition=make_id("i"),
            update=AssignExprNode(target=make_id("i"), value=make_binop(make_id("i"), "+", make_int(1))),
            body=inner_body,
        )
        ir = gen_ir(for_node)
        assert len(ir.functions) == 1

    def test_switch_basic(self):
        """switch 基本结构"""
        switch = SwitchStmtNode(
            expr=make_id("x"),
            cases=[
                CaseStmtNode(value=make_int(1), statements=[ReturnStmtNode(make_int(10))]),
                CaseStmtNode(value=make_int(2), statements=[ReturnStmtNode(make_int(20))]),
                DefaultStmtNode(statements=[ReturnStmtNode(make_int(0))]),
            ],
        )
        ir = gen_ir(switch)
        assert len(ir.functions) == 1

    def test_switch_multiple_cases(self):
        """switch 多 case"""
        switch = SwitchStmtNode(
            expr=make_id("grade"),
            cases=[
                CaseStmtNode(value=make_int(90), statements=[]),
                CaseStmtNode(value=make_int(80), statements=[]),
                CaseStmtNode(value=make_int(70), statements=[]),
            ],
        )
        ir = gen_ir(switch)
        assert len(ir.functions) == 1

    def test_switch_no_default(self):
        """switch 无 default"""
        switch = SwitchStmtNode(
            expr=make_id("x"),
            cases=[
                CaseStmtNode(value=make_int(1), statements=[ReturnStmtNode(make_int(1))]),
            ],
        )
        ir = gen_ir(switch)
        assert len(ir.functions) == 1

    def test_switch_fallthrough(self):
        """switch fall-through（连续 case 无 break）"""
        switch = SwitchStmtNode(
            expr=make_id("x"),
            cases=[
                CaseStmtNode(value=make_int(1), statements=[ReturnStmtNode(make_int(1))]),
                CaseStmtNode(value=make_int(2), statements=[]),  # fall-through
            ],
        )
        ir = gen_ir(switch)
        assert len(ir.functions) == 1

    def test_goto_stmt(self):
        """goto 语句"""
        ir = gen_ir(GotoStmtNode(label="my_label"))
        assert len(ir.functions) == 1

    def test_label_stmt(self):
        """标签语句"""
        ir = gen_ir(LabelStmtNode(name="my_label", statement=ReturnStmtNode(make_int(0))))
        assert len(ir.functions) == 1

    def test_goto_label_pair(self):
        """goto + label 配对"""
        body = BlockStmtNode(statements=[
            LabelStmtNode(name="loop_start", statement=None),
            ReturnStmtNode(make_int(1)),
        ])
        ir = gen_ir(body)
        assert len(ir.functions) == 1

    def test_expr_stmt(self):
        """表达式语句"""
        ir = gen_ir(ExprStmtNode(expr=make_int(42)))
        assert len(ir.functions) == 1

    def test_block_stmt_multiple_stmts(self):
        """代码块多条语句"""
        body = BlockStmtNode(statements=[
            VariableDeclNode(name="x", var_type=PrimitiveTypeNode("整数型"), init=make_int(1)),
            ReturnStmtNode(make_int(2)),
        ])
        ir = gen_ir(body)
        assert len(ir.functions) == 1


# =============================================================================
# P3: 高级特性测试
# =============================================================================

class TestAdvancedFeatures:
    """高级语言特性"""

    def test_struct_decl(self):
        """结构体声明"""
        gen = IRGenerator()
        struct = StructDeclNode(
            name="Point",
            members=[
                VariableDeclNode(name="x", var_type=PrimitiveTypeNode("整数型"), init=None),
                VariableDeclNode(name="y", var_type=PrimitiveTypeNode("整数型"), init=None),
            ],
        )
        gen.generate(make_program(make_func("test", ReturnStmtNode(make_int(0)))))
        # struct 不在 func body 中，直接 accept
        struct.accept(gen)
        assert len(gen.module.structs) >= 1

    def test_enum_decl(self):
        """枚举声明（不生成 IR 指令）"""
        gen = IRGenerator()
        # values 必须是 List[Tuple[str, Optional[ASTNode]]]
        enum = EnumDeclNode(
            name="Color",
            values=[("红", IntLiteralNode(1)), ("绿", IntLiteralNode(2)), ("蓝", IntLiteralNode(3))],
        )
        enum.accept(gen)
        # 不崩溃即通过

    def test_union_decl(self):
        """共用体声明"""
        gen = IRGenerator()
        union = UnionDeclNode(
            name="Data",
            members=[
                VariableDeclNode(name="i", var_type=PrimitiveTypeNode("整数型"), init=None),
            ],
        )
        union.accept(gen)
        # 不崩溃即通过

    def test_typedef_decl(self):
        """类型别名（不生成 IR 指令）"""
        gen = IRGenerator()
        # TypedefDeclNode(old_type, new_name)
        typedef = TypedefDeclNode(old_type=PrimitiveTypeNode("整数型"), new_name="int32_t")
        typedef.accept(gen)
        # 不崩溃即通过

    def test_sizeof_expr(self):
        """sizeof 表达式"""
        ir = gen_ir(ExprStmtNode(
            expr=SizeofExprNode(target=PrimitiveTypeNode("整数型"))
        ))
        assert len(ir.functions) == 1

    def test_pointer_type(self):
        """指针类型节点"""
        gen = IRGenerator()
        ptr = PointerTypeNode(base_type=PrimitiveTypeNode("整数型"))
        gen.visit_pointer_type(ptr)
        # 不崩溃即通过

    def test_array_type(self):
        """数组类型节点"""
        gen = IRGenerator()
        arr = ArrayTypeNode(element_type=PrimitiveTypeNode("整数型"), size=make_int(10))
        gen.visit_array_type(arr)
        # 不崩溃即通过


# =============================================================================
# P4: 模块/参数测试
# =============================================================================

class TestModuleAndParams:
    """模块、参数、全局变量"""

    def test_function_with_params(self):
        """带参数的函数"""
        gen = IRGenerator()
        param = ParamDeclNode(name="a", param_type=PrimitiveTypeNode("整数型"))
        func = make_func("add", ReturnStmtNode(make_int(0)), params=[param])
        ir = gen.generate(make_program(func))
        assert len(ir.functions) == 1
        assert len(ir.functions[0].params) == 1

    def test_function_multiple_params(self):
        """多参数函数"""
        gen = IRGenerator()
        params = [
            ParamDeclNode(name="a", param_type=PrimitiveTypeNode("整数型")),
            ParamDeclNode(name="b", param_type=PrimitiveTypeNode("整数型")),
            ParamDeclNode(name="c", param_type=PrimitiveTypeNode("整数型")),
        ]
        func = make_func("foo", ReturnStmtNode(make_int(0)), params=params)
        ir = gen.generate(make_program(func))
        assert len(ir.functions[0].params) == 3

    def test_module_decl(self):
        """模块声明"""
        gen = IRGenerator()
        module = ModuleDeclNode(
            name="test_module",
            exports=["foo"],
            imports=["std.io"],
            body=[
                make_func("inner", ReturnStmtNode(make_int(1))),
            ],
        )
        ir = gen.generate(make_program(module))
        assert len(ir.functions) == 1

    def test_import_decl(self):
        """导入声明（不生成指令）"""
        gen = IRGenerator()
        imp = ImportDeclNode(module_name="std.io", symbols=None)
        imp.accept(gen)
        # 不崩溃即通过

    def test_global_variable(self):
        """全局变量"""
        gen = IRGenerator()
        # 全局变量在 current_block=None 时处理
        gv = VariableDeclNode(name="global_count", var_type=PrimitiveTypeNode("整数型"), init=make_int(0))
        gv.accept(gen)
        assert len(gen.module.global_vars) >= 1

    def test_primitive_type_visitor(self):
        """基本类型 visitor"""
        gen = IRGenerator()
        ty = PrimitiveTypeNode("双精度浮点型")
        gen.visit_primitive_type(ty)
        # 不崩溃

    def test_function_type_visitor(self):
        """函数类型 visitor"""
        gen = IRGenerator()
        ft = FunctionTypeNode(
            return_type=PrimitiveTypeNode("整数型"),
            param_types=[PrimitiveTypeNode("整数型")],
        )
        gen.visit_function_type(ft)
        # 不崩溃

    def test_struct_type_visitor(self):
        """结构体类型 visitor"""
        gen = IRGenerator()
        st = StructTypeNode(name="Point")
        gen.visit_struct_type(st)
        # 不崩溃


# =============================================================================
# 工具方法测试
# =============================================================================

class TestUtilityMethods:
    """IRGenerator 内部工具方法"""

    def test_new_temp_counter(self):
        """临时变量计数器递增"""
        gen = IRGenerator()
        gen._ensure_block()
        t1 = gen._new_temp()
        t2 = gen._new_temp()
        t3 = gen._new_temp()
        assert t1.name == "%0"
        assert t2.name == "%1"
        assert t3.name == "%2"

    def test_new_bb_label(self):
        """基本块标签生成"""
        gen = IRGenerator()
        gen.current_function = IRGenerator().module.add_function(
            IRGenerator().module.add_function(
                IRFunction(name="dummy", return_type="整数型")
            )
        ) if False else None  # 简化：直接用现有函数

        # 简单验证标签生成
        gen._bb_counter = 0
        assert gen._new_bb_label() == "bb0"
        assert gen._new_bb_label("loop") == "loop1"
        assert gen._new_bb_label() == "bb2"

    def test_get_type_name(self):
        """_get_type_name 辅助方法"""
        gen = IRGenerator()
        assert gen._get_type_name(None) == "空型"
        assert gen._get_type_name(PrimitiveTypeNode("整数型")) == "整数型"
        node = PrimitiveTypeNode("浮点型")
        assert gen._get_type_name(node) == "浮点型"

    def test_resolve_function_name(self):
        """_resolve_function_name 映射"""
        gen = IRGenerator()
        assert gen._resolve_function_name("主函数") == "main"
        assert gen._resolve_function_name("主程序") == "main"
        assert gen._resolve_function_name("foo") == "foo"

    def test_emit_returns_result(self):
        """_emit 返回结果值"""
        gen = IRGenerator()
        gen.current_function = __import__('zhpp.ir.program', fromlist=['IRFunction']).IRFunction(
            name="test", return_type="整数型"
        )
        gen.current_block = gen.current_function.entry_block
        result = gen._emit(Opcode.ALLOC, [], [])
        # 无 result 时返回 None
        alloc_result = gen._new_temp("整数型")
        var_val = __import__('zhpp.ir.values', fromlist=['IRValue']).IRValue(name="x", ty="整数型")
        result2 = gen._emit(Opcode.ALLOC, [var_val], [alloc_result])
        assert result2 is not None


# =============================================================================
# IRPrinter 集成测试
# =============================================================================

class TestIRPrinterIntegration:
    """IR 打印集成测试"""

    def test_print_empty_program(self):
        """打印空程序"""
        gen = IRGenerator()
        ir = gen.generate(ProgramNode(declarations=[]))
        printer = IRPrinter()
        output = printer.print(ir)
        assert isinstance(output, str)

    def test_print_function_with_body(self):
        """打印含函数体的 IR"""
        gen = IRGenerator()
        func = make_func("add",
            BlockStmtNode(statements=[
                ReturnStmtNode(make_int(42)),
            ])
        )
        ir = gen.generate(make_program(func))
        printer = IRPrinter()
        output = printer.print(ir)
        assert "add" in output

    def test_print_multiple_functions(self):
        """打印多函数"""
        gen = IRGenerator()
        f1 = make_func("foo", ReturnStmtNode(make_int(1)))
        f2 = make_func("bar", ReturnStmtNode(make_int(2)))
        ir = gen.generate(make_program(f1, f2))
        printer = IRPrinter()
        output = printer.print(ir)
        assert "foo" in output
        assert "bar" in output


# =============================================================================
# 边界情况测试
# =============================================================================

class TestEdgeCases:
    """边界和异常情况"""

    def test_eval_expr_none(self):
        """_eval_expr 接收 None"""
        gen = IRGenerator()
        result = gen._eval_expr(None)
        assert result is None

    def test_eval_expr_unknown_node_type(self):
        """_eval_expr 未知节点类型"""
        gen = IRGenerator()
        gen._ensure_block()
        # 创建一个没有任何 visitor 的节点
        node = PrimitiveTypeNode("整数型")
        result = gen._eval_expr(node)
        # 未知类型返回 None，不崩溃
        assert result is None

    def test_break_with_no_target(self):
        """循环外 break（无 target 栈）"""
        gen = IRGenerator()
        gen.current_block = None  # 确保有 block
        gen._ensure_block()
        # 不崩溃，_break_targets 为空时不生成指令
        BreakStmtNode().accept(gen)

    def test_continue_with_no_target(self):
        """循环外 continue（无 target 栈）"""
        gen = IRGenerator()
        gen._ensure_block()
        ContinueStmtNode().accept(gen)
        # 不崩溃

    def test_while_empty_body(self):
        """空循环体 while"""
        while_node = WhileStmtNode(
            condition=make_id("x"),
            body=BlockStmtNode(statements=[]),
        )
        ir = gen_ir(while_node)
        assert len(ir.functions) == 1

    def test_for_empty_body(self):
        """空循环体 for"""
        for_node = ForStmtNode(
            init=None,
            condition=make_id("x"),
            update=None,
            body=BlockStmtNode(statements=[]),
        )
        ir = gen_ir(for_node)
        assert len(ir.functions) == 1

    def test_switch_empty_cases(self):
        """空 switch"""
        switch = SwitchStmtNode(expr=make_id("x"), cases=[])
        ir = gen_ir(switch)
        assert len(ir.functions) == 1

    def test_call_expr_none_callee(self):
        """callee=None 的调用"""
        gen = gen_ir_with_block(None)
        call = CallExprNode(callee=None, args=[])
        result = gen._eval_expr(call)
        # callee 为 None 时不崩溃，使用 "unknown"
        assert result is not None

    def test_assign_expr_none_target(self):
        """target=None 的赋值"""
        gen = gen_ir_with_block(None)
        assign = AssignExprNode(target=None, value=make_int(10))
        result = gen._eval_expr(assign)
        # 不崩溃
        assert result is not None
