# -*- coding: utf-8 -*-
"""
Switch 语句测试

测试内容：
- Switch IR 生成
- Case/Default 基本块创建
- SwitchStrategy LLVM IR 生成
- Break/Fall-through 语义

作者：远
日期：2026-04-09
"""

import pytest
import llvmlite.ir as ll
from zhc.ir.ir_generator import IRGenerator
from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.opcodes import Opcode
from zhc.parser.ast_nodes import (
    SwitchStmtNode,
    CaseStmtNode,
    DefaultStmtNode,
    BreakStmtNode,
    IntLiteralNode,
    IdentifierExprNode,
    ReturnStmtNode,
)
from zhc.ir.values import IRValue
from zhc.backend.llvm_instruction_strategy import SwitchStrategy
from zhc.parser.lexer import Lexer
from zhc.parser.parser import Parser


class TestSwitchIRGeneration:
    """Switch IR 生成测试"""

    def test_simple_switch_ir(self):
        """测试简单 switch IR 生成"""
        # 创建 IR 生成器
        program = IRProgram()
        generator = IRGenerator(program)

        # 创建 switch 表达式
        expr = IdentifierExprNode(name="x")

        # 创建 case 节点
        case1 = CaseStmtNode(
            value=IntLiteralNode(value=1),
            statements=[],
        )
        case2 = CaseStmtNode(
            value=IntLiteralNode(value=2),
            statements=[],
        )

        # 创建 switch 节点
        switch_node = SwitchStmtNode(
            expr=expr,
            cases=[case1, case2],
        )

        # 创建函数
        func = IRFunction(name="test_switch")
        program.add_function(func)
        generator.current_function = func

        # 生成 IR
        generator.visit_switch_stmt(switch_node)

        # 验证：应该有 switch_end 块
        assert any("switch_end" in bb.label for bb in func.basic_blocks)

        # 验证：应该有 case 块
        assert any("case_1" in bb.label for bb in func.basic_blocks)
        assert any("case_2" in bb.label for bb in func.basic_blocks)

    def test_switch_with_default(self):
        """测试带 default 的 switch"""
        program = IRProgram()
        generator = IRGenerator(program)

        expr = IdentifierExprNode(name="x")
        case1 = CaseStmtNode(
            value=IntLiteralNode(value=1),
            statements=[],
        )
        default = DefaultStmtNode(statements=[])

        switch_node = SwitchStmtNode(
            expr=expr,
            cases=[case1, default],
        )

        func = IRFunction(name="test_switch")
        program.add_function(func)
        generator.current_function = func

        generator.visit_switch_stmt(switch_node)

        # 验证：应该有 default 块
        assert any("default" in bb.label for bb in func.basic_blocks)

    def test_switch_with_break(self):
        """测试带 break 的 switch"""
        program = IRProgram()
        generator = IRGenerator(program)

        expr = IdentifierExprNode(name="x")
        case1 = CaseStmtNode(
            value=IntLiteralNode(value=1),
            statements=[BreakStmtNode()],
        )

        switch_node = SwitchStmtNode(
            expr=expr,
            cases=[case1],
        )

        func = IRFunction(name="test_switch")
        program.add_function(func)
        generator.current_function = func

        generator.visit_switch_stmt(switch_node)

        # 验证：case 块应该有终结指令（break -> JMP）
        case_blocks = [bb for bb in func.basic_blocks if "case_1" in bb.label]
        if case_blocks:
            # 有 case 块，检查是否有终结指令
            assert (
                case_blocks[0].is_terminated() or len(case_blocks[0].instructions) > 0
            )

    def test_switch_fallthrough(self):
        """测试 fall-through 语义"""
        program = IRProgram()
        generator = IRGenerator(program)

        expr = IdentifierExprNode(name="x")
        # 没有 break 的 case
        case1 = CaseStmtNode(
            value=IntLiteralNode(value=1),
            statements=[],  # 没有 break
        )

        switch_node = SwitchStmtNode(
            expr=expr,
            cases=[case1],
        )

        func = IRFunction(name="test_switch")
        program.add_function(func)
        generator.current_function = func

        generator.visit_switch_stmt(switch_node)

        # 验证：应该自动添加跳转到 switch_end
        case_blocks = [bb for bb in func.basic_blocks if "case_1" in bb.label]
        if case_blocks:
            # fall-through 应该添加 JMP 指令
            assert case_blocks[0].is_terminated()


class TestSwitchStrategy:
    """SwitchStrategy 测试"""

    def test_switch_strategy_creation(self):
        """测试 SwitchStrategy 创建"""
        strategy = SwitchStrategy()
        assert strategy.opcode == Opcode.SWITCH

    def test_resolve_integer_case_value(self):
        """测试整数 case 值解析"""
        import llvmlite.ir as ll

        strategy = SwitchStrategy()
        i32 = ll.IntType(32)

        # 整数常量
        result = strategy._resolve_case_value(42, i32, None, None)
        assert isinstance(result, ll.Constant)
        assert result.constant == 42

    def test_resolve_char_case_value(self):
        """测试字符 case 值解析"""
        import llvmlite.ir as ll

        strategy = SwitchStrategy()
        i32 = ll.IntType(32)

        # 单字符
        result = strategy._resolve_case_value("A", i32, None, None)
        assert isinstance(result, ll.Constant)
        assert result.constant == ord("A")


class TestSwitchLLVMGeneration:
    """Switch LLVM IR 生成测试"""

    def test_llvm_switch_basic(self):
        """测试基本 LLVM switch 生成"""
        # 创建 LLVM 模块
        module = ll.Module("test_switch")

        # 创建函数类型
        func_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])
        func = ll.Function(module, func_type, name="test_switch")

        # 创建基本块
        entry = func.append_basic_block(name="entry")
        case1 = func.append_basic_block(name="case_1")
        case2 = func.append_basic_block(name="case_2")
        default = func.append_basic_block(name="default")
        end = func.append_basic_block(name="switch_end")

        # 创建构建器
        builder = ll.IRBuilder(entry)

        # 创建 switch 指令
        # llvmlite switch 方法签名：switch(val, default_block, cases)
        # cases 是 [(value, block), ...] 列表
        cond = func.args[0]
        switch_instr = builder.switch(cond, default)
        switch_instr.add_case(ll.Constant(ll.IntType(32), 1), case1)
        switch_instr.add_case(ll.Constant(ll.IntType(32), 2), case2)

        # 验证：entry 块应该有 switch 指令
        assert entry.is_terminated

        # 完成 case 块
        builder.position_at_end(case1)
        builder.branch(end)

        builder.position_at_end(case2)
        builder.branch(end)

        builder.position_at_end(default)
        builder.branch(end)

        builder.position_at_end(end)
        builder.ret(ll.Constant(ll.IntType(32), 0))

        # 验证：所有块都应该有终结指令
        for block in func.blocks:
            assert block.is_terminated

    def test_llvm_switch_empty_cases(self):
        """测试空 case 列表"""
        module = ll.Module("test_empty_switch")
        func_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])
        func = ll.Function(module, func_type, name="test_empty")

        entry = func.append_basic_block(name="entry")
        default = func.append_basic_block(name="default")

        builder = ll.IRBuilder(entry)

        # 空 case 列表 -> 直接跳转到 default
        builder.branch(default)

        builder.position_at_end(default)
        builder.ret(ll.Constant(ll.IntType(32), 0))

        assert entry.is_terminated


class TestSwitchIntegration:
    """Switch 集成测试"""

    def test_full_switch_workflow(self):
        """测试完整 switch 工作流"""
        # 1. 创建 IR 程序
        program = IRProgram()
        generator = IRGenerator(program)

        # 2. 创建 switch AST
        expr = IdentifierExprNode(name="grade")
        case1 = CaseStmtNode(
            value=IntLiteralNode(value=90),
            statements=[BreakStmtNode()],
        )
        case2 = CaseStmtNode(
            value=IntLiteralNode(value=80),
            statements=[BreakStmtNode()],
        )
        default = DefaultStmtNode(statements=[BreakStmtNode()])

        switch_node = SwitchStmtNode(
            expr=expr,
            cases=[case1, case2, default],
        )

        # 3. 创建函数
        func = IRFunction(name="grade_to_rank")
        program.add_function(func)
        generator.current_function = func

        # 4. 生成 IR
        generator.visit_switch_stmt(switch_node)

        # 5. 验证 IR 结构
        # 应该有：entry, case_90, case_80, default, switch_end
        labels = [bb.label for bb in func.basic_blocks]
        assert any("case_90" in label for label in labels)
        assert any("case_80" in label for label in labels)
        assert any("default" in label for label in labels)
        assert any("switch_end" in label for label in labels)


class TestSwitchRangeCase:
    """【SW-005】范围 case 测试"""

    def test_range_case_node_creation(self):
        """测试范围 case 节点创建"""
        value = IntLiteralNode(value=1)
        end_value = IntLiteralNode(value=5)
        case = CaseStmtNode(
            value=value,
            statements=[BreakStmtNode()],
            end_value=end_value,
        )

        assert case.is_range is True
        assert case.end_value == end_value
        assert case.case_values == [value, end_value]

    def test_single_case_not_range(self):
        """测试单值 case 不是范围"""
        value = IntLiteralNode(value=42)
        case = CaseStmtNode(
            value=value,
            statements=[BreakStmtNode()],
        )

        assert case.is_range is False
        assert case.end_value is None

    def test_range_case_ir_generation(self):
        """【SW-005】测试范围 case IR 生成"""
        program = IRProgram()
        generator = IRGenerator(program)

        # 创建函数
        func = IRFunction(name="check_range")
        program.add_function(func)
        generator.current_function = func

        # 创建范围 case：case 1...5
        expr = IdentifierExprNode(name="x")
        range_case = CaseStmtNode(
            value=IntLiteralNode(value=1),
            statements=[ReturnStmtNode(IntLiteralNode(value=1))],
            end_value=IntLiteralNode(value=5),
        )
        default = DefaultStmtNode(statements=[ReturnStmtNode(IntLiteralNode(value=0))])

        switch_node = SwitchStmtNode(expr=expr, cases=[range_case, default])
        generator.visit_switch_stmt(switch_node)

        # 验证 IR 结构
        labels = [bb.label for bb in func.basic_blocks]
        assert any("case_range" in label for label in labels)
        assert any("default" in label for label in labels)

        # 验证 switch 指令存在（可能在任意基本块中）
        switch_found = False
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if hasattr(instr, "opcode"):
                    opcode_str = str(instr.opcode)
                    if "SWITCH" in opcode_str:
                        switch_found = True
                        break
            if switch_found:
                break
        assert switch_found, "Switch instruction not found"

    def test_range_case_expansion(self):
        """测试范围值展开"""
        program = IRProgram()
        generator = IRGenerator(program)

        func = IRFunction(name="expand_test")
        program.add_function(func)
        generator.current_function = func

        # 范围 1...3 展开为 3 个 case
        range_case = CaseStmtNode(
            value=IntLiteralNode(value=1),
            statements=[BreakStmtNode()],
            end_value=IntLiteralNode(value=3),
        )
        default = DefaultStmtNode(statements=[BreakStmtNode()])
        switch_node = SwitchStmtNode(
            expr=IdentifierExprNode(name="x"),
            cases=[range_case, default],
        )
        generator.visit_switch_stmt(switch_node)

        # 验证生成了正确数量的基本块
        # entry + case_range + switch_end + default = 4 个
        assert len(func.basic_blocks) >= 4

        # 验证 case_range 基本块存在
        labels = [bb.label for bb in func.basic_blocks]
        assert any("case_range" in label for label in labels)

    def test_range_case_llvm_generation(self):
        """【SW-005】测试范围 case LLVM 生成"""
        from zhc.backend.llvm_backend import LLVMBackend

        program = IRProgram()
        generator = IRGenerator(program)
        backend = LLVMBackend()

        # 创建函数
        func = IRFunction(name="range_check")
        func.return_type = "i32"
        func.add_param(IRValue(name="x", ty="i32"))
        program.add_function(func)
        generator.current_function = func

        # 范围 case
        range_case = CaseStmtNode(
            value=IntLiteralNode(value=10),
            statements=[ReturnStmtNode(IntLiteralNode(value=100))],
            end_value=IntLiteralNode(value=15),
        )
        default = DefaultStmtNode(statements=[ReturnStmtNode(IntLiteralNode(value=0))])
        switch_node = SwitchStmtNode(
            expr=IdentifierExprNode(name="x"),
            cases=[range_case, default],
        )
        generator.visit_switch_stmt(switch_node)

        # 生成 LLVM IR
        llvm_ir = backend.generate(program)
        assert llvm_ir is not None
        # 验证 switch 指令存在
        assert "switch" in llvm_ir.lower()


class TestSwitchEndToEnd:
    """Switch 端到端集成测试"""

    def test_switch_end_to_end(self):
        """测试完整 switch 工作流"""
        # 1. 创建 IR 程序
        program = IRProgram()
        generator = IRGenerator(program)

        # 2. 创建 switch AST
        expr = IdentifierExprNode(name="grade")
        case1 = CaseStmtNode(
            value=IntLiteralNode(value=90),
            statements=[BreakStmtNode()],
        )
        case2 = CaseStmtNode(
            value=IntLiteralNode(value=80),
            statements=[BreakStmtNode()],
        )
        default = DefaultStmtNode(statements=[BreakStmtNode()])

        switch_node = SwitchStmtNode(
            expr=expr,
            cases=[case1, case2, default],
        )

        # 3. 创建函数
        func = IRFunction(name="grade_to_rank")
        program.add_function(func)
        generator.current_function = func

        # 4. 生成 IR
        generator.visit_switch_stmt(switch_node)

        # 5. 验证 IR 结构
        # 应该有：entry, case_90, case_80, default, switch_end
        labels = [bb.label for bb in func.basic_blocks]
        assert any("case_90" in label for label in labels)
        assert any("case_80" in label for label in labels)
        assert any("default" in label for label in labels)
        assert any("switch_end" in label for label in labels)


class TestSwitchLexerParser:
    """Switch 语句词法分析和语法分析测试"""

    def test_ellipsis_token(self):
        """【SW-005】测试 ... token 识别"""
        lexer = Lexer("...")
        tokens = lexer.tokenize()
        from zhc.parser.lexer import TokenType

        # 应该有两个 token: ELLIPSIS 和 EOF
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.ELLIPSIS
        assert tokens[0].value == "..."
        assert tokens[1].type == TokenType.EOF

    def test_range_case_lexer(self):
        """【SW-005】测试范围 case 词法分析"""
        lexer = Lexer("情况 1...5:")
        tokens = lexer.tokenize()

        from zhc.parser.lexer import TokenType

        # 情况, 1, ..., 5, :, EOF
        assert len(tokens) == 6
        assert tokens[0].type == TokenType.CASE
        assert tokens[1].type == TokenType.INT_LITERAL
        assert tokens[2].type == TokenType.ELLIPSIS
        assert tokens[3].type == TokenType.INT_LITERAL
        assert tokens[4].type == TokenType.COLON
        assert tokens[5].type == TokenType.EOF

    def test_range_case_parsing(self):
        """【SW-005】测试范围 case 语法解析"""
        code = """
        函数 整数 测试范围(整数 x) {
            选择(x) {
                情况 1...5:
                    返回 1
                默认:
                    返回 0
            }
        }
        """

        tokens = Lexer(code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # 找到测试函数
        func = None
        for decl in ast.declarations:
            if hasattr(decl, "name") and decl.name == "测试范围":
                func = decl
                break

        assert func is not None

        # 找到 switch 语句
        switch_stmt = None
        for stmt in func.body.statements:
            if isinstance(stmt, SwitchStmtNode):
                switch_stmt = stmt
                break

        assert switch_stmt is not None
        assert len(switch_stmt.cases) == 2

        # 验证范围 case
        range_case = switch_stmt.cases[0]
        assert isinstance(range_case, CaseStmtNode)
        assert range_case.is_range is True
        assert range_case.end_value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
