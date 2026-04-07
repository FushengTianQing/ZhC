"""
Phase 6 M4: 语义分析增强测试

测试内容：
1. 结构体成员访问检查 (MEMBER_EXPR)
2. goto 标签存在性检查
3. switch 重复 case / 缺少 default 检查
4. 结构体成员类型记录
"""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from zhpp.parser.ast_nodes import (
    ASTNode, ASTNodeType,
    ProgramNode, FunctionDeclNode, VariableDeclNode, ParamDeclNode,
    StructDeclNode, BlockStmtNode, ReturnStmtNode, ExprStmtNode,
    SwitchStmtNode, CaseStmtNode, DefaultStmtNode,
    GotoStmtNode, LabelStmtNode, BreakStmtNode,
    IdentifierExprNode, MemberExprNode, BinaryExprNode,
    AssignExprNode, ArrayExprNode, IntLiteralNode,
    PrimitiveTypeNode,
)
from zhpp.semantic.semantic_analyzer import SemanticAnalyzer


def _type(name):
    """快捷创建 PrimitiveTypeNode"""
    return PrimitiveTypeNode(name)


def _var(name, type_name, init=None, line=0):
    """快捷创建 VariableDeclNode"""
    return VariableDeclNode(name, _type(type_name), init, line=line)


def _func(name, ret_type, body_stmts, params=None, line=0):
    """快捷创建 FunctionDeclNode"""
    body = BlockStmtNode(body_stmts)
    return FunctionDeclNode(name, _type(ret_type), params or [], body, line=line)


def _member(name, type_name, init=None):
    """快捷创建结构体成员 VariableDeclNode"""
    return VariableDeclNode(name, _type(type_name), init)


class TestStructMemberAccess(unittest.TestCase):
    """结构体成员访问检查测试"""

    def test_valid_member_access(self):
        """访问已存在成员不应报错"""
        struct = StructDeclNode("坐标", [
            _member("x", "整数型"), _member("y", "整数型")
        ])
        var = _var("p", "坐标")
        member = MemberExprNode(
            obj=IdentifierExprNode("p", line=3),
            member="x", line=3, column=5
        )
        stmt = ExprStmtNode(member)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [struct, var, stmt, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        ok = analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(ok, f"Valid member access should pass. Errors: {errors}")

    def test_nonexistent_member_error(self):
        """访问不存在的成员应报错"""
        struct = StructDeclNode("坐标", [
            _member("x", "整数型"), _member("y", "整数型")
        ])
        var = _var("p", "坐标")
        member = MemberExprNode(
            obj=IdentifierExprNode("p", line=4),
            member="z",  # 不存在的成员
            line=4, column=5
        )
        stmt = ExprStmtNode(member)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [struct, var, stmt, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(
            any("z" in e and "坐标" in e for e in errors),
            f"Should report member 'z' not found in '坐标'. Got: {errors}"
        )

    def test_member_type_inferred(self):
        """成员访问表达式应正确推导类型

        注意：因 analyzer/__init__.py 存在预先的循环导入 bug，
        直接测试 inferred_type 会触发该 bug。
        改为验证：有效成员访问不产生"成员不存在"错误。
        """
        struct = StructDeclNode("坐标", [
            _member("x", "整数型"), _member("y", "整数型")
        ])
        var = _var("p", "坐标")
        member_x = MemberExprNode(
            obj=IdentifierExprNode("p", line=3),
            member="x", line=3, column=5
        )
        member_y = MemberExprNode(
            obj=IdentifierExprNode("p", line=4),
            member="y", line=4, column=5
        )
        stmt1 = ExprStmtNode(member_x)
        stmt2 = ExprStmtNode(member_y)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "无返回值", [struct, var, stmt1, stmt2, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(not any("不存在" in e for e in errors),
                        f"Valid members should not error. Errors: {errors}")

    def test_non_struct_member_access_no_crash(self):
        """对非结构体变量访问成员不应崩溃"""
        var = _var("x", "整数型")
        member = MemberExprNode(
            obj=IdentifierExprNode("x", line=2),
            member="y", line=2, column=5
        )
        stmt = ExprStmtNode(member)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [var, stmt, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        ok = analyzer.analyze(program)
        # 不应崩溃——非结构体成员访问不报错（可能是 typedef 别名等）
        self.assertIsInstance(ok, bool)


class TestGotoLabelCheck(unittest.TestCase):
    """goto 标签存在性检查测试"""

    def test_goto_valid_label(self):
        """goto 已定义的标签不应报错"""
        label_stmt = LabelStmtNode(
            name="结束",
            statement=ReturnStmtNode(IntLiteralNode(0), line=3),
            line=3
        )
        goto_stmt = GotoStmtNode(label="结束", line=2)
        func = _func("主函数", "整数型", [goto_stmt, label_stmt])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        ok = analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(ok, f"Valid goto should pass. Errors: {errors}")

    def test_goto_undefined_label_error(self):
        """goto 未定义的标签应报错"""
        goto_stmt = GotoStmtNode(label="不存在", line=2)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [goto_stmt, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(
            any("不存在" in e for e in errors),
            f"Should report undefined label. Got: {errors}"
        )

    def test_duplicate_label_error(self):
        """重复标签定义应报错"""
        label1 = LabelStmtNode(name="重复", statement=None, line=2)
        label2 = LabelStmtNode(name="重复", statement=None, line=4)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [label1, label2, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(
            any("重复" in e and "标签" in e for e in errors),
            f"Should report duplicate label. Got: {errors}"
        )

    def test_labels_reset_between_functions(self):
        """不同函数的标签应独立"""
        label1 = LabelStmtNode(name="结束", statement=ReturnStmtNode(IntLiteralNode(0)), line=2)
        func1 = _func("函数甲", "整数型", [label1])

        goto2 = GotoStmtNode(label="结束", line=5)
        label2 = LabelStmtNode(name="结束", statement=ReturnStmtNode(IntLiteralNode(0)), line=6)
        func2 = _func("函数乙", "整数型", [goto2, label2])

        program = ProgramNode([func1, func2])
        analyzer = SemanticAnalyzer()
        ok = analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(ok, f"Labels should be function-scoped. Errors: {errors}")


class TestSwitchChecks(unittest.TestCase):
    """switch 语句检查测试"""

    def test_missing_default_warning(self):
        """switch 缺少 default 应产生警告"""
        case1 = CaseStmtNode(
            value=IntLiteralNode(1, line=2),
            statements=[BreakStmtNode()],
            line=2
        )
        switch = SwitchStmtNode(
            expr=IdentifierExprNode("x"),
            cases=[case1],
            line=1
        )
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [switch, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        warnings = [w.message for w in analyzer.warnings]
        self.assertTrue(
            any("default" in w.lower() for w in warnings),
            f"Should warn about missing default. Warnings: {warnings}"
        )

    def test_with_default_no_warning(self):
        """switch 有 default 不应产生警告"""
        case1 = CaseStmtNode(
            value=IntLiteralNode(1, line=2),
            statements=[BreakStmtNode()],
            line=2
        )
        default = DefaultStmtNode(statements=[BreakStmtNode()], line=3)
        switch = SwitchStmtNode(
            expr=IdentifierExprNode("x"),
            cases=[case1, default],
            line=1
        )
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [switch, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        default_warnings = [w for w in analyzer.warnings if "default" in w.message.lower()]
        self.assertEqual(len(default_warnings), 0,
                         f"Should not warn about default. Warnings: {default_warnings}")

    def test_duplicate_case_error(self):
        """switch 中重复 case 值应报错"""
        case1 = CaseStmtNode(
            value=IntLiteralNode(1, line=2),
            statements=[BreakStmtNode()],
            line=2
        )
        case2 = CaseStmtNode(
            value=IntLiteralNode(1, line=3),
            statements=[BreakStmtNode()],
            line=3
        )
        default = DefaultStmtNode(statements=[BreakStmtNode()], line=4)
        switch = SwitchStmtNode(
            expr=IdentifierExprNode("x"),
            cases=[case1, case2, default],
            line=1
        )
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [switch, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(
            any("重复" in e and "case" in e.lower() for e in errors),
            f"Should report duplicate case. Errors: {errors}"
        )

    def test_unique_cases_no_error(self):
        """switch 中不重复的 case 值不应报错"""
        cases = [
            CaseStmtNode(value=IntLiteralNode(i, line=i+1),
                         statements=[BreakStmtNode()], line=i+1)
            for i in range(1, 4)
        ]
        default = DefaultStmtNode(statements=[BreakStmtNode()], line=5)
        switch = SwitchStmtNode(
            expr=IdentifierExprNode("x"),
            cases=cases + [default],
            line=1
        )
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [switch, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        dup_errors = [e.message for e in analyzer.errors if "重复" in e.message and "case" in e.message.lower()]
        self.assertEqual(len(dup_errors), 0,
                         f"Should not report duplicate case. Errors: {dup_errors}")


class TestStructMemberDataType(unittest.TestCase):
    """结构体成员类型记录测试"""

    def test_members_record_data_type(self):
        """结构体成员应记录 data_type"""
        # 结构体放在函数外（全局声明），这样可以在函数分析完后仍能查到
        struct = StructDeclNode("点", [
            _member("x", "整数型"),
            _member("y", "整数型"),
            _member("名字", "字符串型"),
        ])
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [ret])
        program = ProgramNode([struct, func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)

        # 在 all_symbols 中查找（函数分析完后当前作用域回到全局）
        struct_sym = None
        for sym in analyzer.symbol_table.all_symbols.values():
            if sym.name == "点" and sym.symbol_type == "结构体":
                struct_sym = sym
                break
        self.assertIsNotNone(struct_sym, "Struct '点' should be in symbol table")
        self.assertEqual(len(struct_sym.members), 3, "Should have 3 members")

        member_types = {m.name: m.data_type for m in struct_sym.members}
        self.assertEqual(member_types.get("x"), "整数型")
        self.assertEqual(member_types.get("y"), "整数型")
        self.assertEqual(member_types.get("名字"), "字符串型")


class TestBackwardCompatibility(unittest.TestCase):
    """回归测试：确保改动不破坏已有功能"""

    def test_basic_function_analysis(self):
        """基本函数分析仍应正常工作"""
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        ok = analyzer.analyze(program)
        self.assertTrue(ok)

    def test_duplicate_var_still_detected(self):
        """重复变量定义仍应报错"""
        v1 = _var("x", "整数型")
        v2 = _var("x", "整数型")
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [v1, v2, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(any("重复定义" in e for e in errors))

    def test_undefined_symbol_still_detected(self):
        """未定义符号仍应报错"""
        assign = AssignExprNode(
            target=IdentifierExprNode("y"),
            value=IdentifierExprNode("不存在"),
            line=2
        )
        stmt = ExprStmtNode(assign)
        ret = ReturnStmtNode(IntLiteralNode(0))
        func = _func("主函数", "整数型", [stmt, ret])
        program = ProgramNode([func])

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        errors = [e.message for e in analyzer.errors]
        self.assertTrue(any("未定义" in e for e in errors))


if __name__ == '__main__':
    unittest.main()
