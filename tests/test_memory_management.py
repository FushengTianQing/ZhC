#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存管理综合测试

测试覆盖：
1. Lexer 智能指针关键字
2. Parser 智能指针语法解析
3. AST 智能指针节点
4. RAII 核心实现
5. 调用栈追踪
6. 泄漏检测增强
"""

from zhc.parser.lexer import Lexer, TokenType
from zhc.parser.parser import Parser
from zhc.parser.ast_nodes import (
    ASTNodeType,
)
from zhc.memory.raii import (
    DestructorInfo,
    CleanupStack,
    CleanupPriority,
    ScopeGuard,
    DestructorRegistry,
)
from zhc.memcheck.call_stack import CallStackTracer


# ============================================================================
# Lexer 测试
# ============================================================================


class TestLexerMemoryKeywords:
    """测试 Lexer 内存管理关键字"""

    def test_unique_ptr_keyword(self):
        lexer = Lexer("独享指针")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.UNIQUE_PTR

    def test_shared_ptr_keyword(self):
        lexer = Lexer("共享指针")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.SHARED_PTR

    def test_weak_ptr_keyword(self):
        lexer = Lexer("弱指针")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.WEAK_PTR

    def test_destructor_keyword(self):
        lexer = Lexer("析构函数")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DESTRUCTOR

    def test_move_keyword(self):
        lexer = Lexer("移动")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MOVE

    def test_all_keywords_in_source(self):
        source = "独享指针 共享指针 弱指针 析构函数 移动"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.UNIQUE_PTR,
            TokenType.SHARED_PTR,
            TokenType.WEAK_PTR,
            TokenType.DESTRUCTOR,
            TokenType.MOVE,
        ]


# ============================================================================
# Parser 智能指针测试
# ============================================================================


class TestParserSmartPointer:
    """测试 Parser 智能指针解析"""

    def _parse(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    def test_unique_ptr_decl(self):
        result = self._parse("独享指针<整数型> p;")
        assert result is not None
        decl = result.declarations[0]
        assert decl.node_type == ASTNodeType.UNIQUE_PTR_DECL
        assert decl.pointer_kind == "unique"
        assert decl.name == "p"

    def test_shared_ptr_decl(self):
        result = self._parse("共享指针<字符串> s;")
        assert result is not None
        decl = result.declarations[0]
        assert decl.node_type == ASTNodeType.SHARED_PTR_DECL
        assert decl.pointer_kind == "shared"
        assert decl.name == "s"

    def test_weak_ptr_decl(self):
        result = self._parse("弱指针<浮点型> w;")
        assert result is not None
        decl = result.declarations[0]
        assert decl.node_type == ASTNodeType.WEAK_PTR_DECL
        assert decl.pointer_kind == "weak"
        assert decl.name == "w"

    def test_unique_ptr_with_init(self):
        result = self._parse("独享指针<整数型> p = 42;")
        assert result is not None
        decl = result.declarations[0]
        assert decl.node_type == ASTNodeType.UNIQUE_PTR_DECL
        assert decl.name == "p"
        assert decl.initializer is not None

    def test_move_expr(self):
        result = self._parse("移动(x);")
        assert result is not None
        stmt = result.declarations[0]
        assert stmt.node_type == ASTNodeType.EXPR_STMT
        expr = stmt.expr
        assert expr.node_type == ASTNodeType.MOVE_EXPR
        assert expr.operand.node_type == ASTNodeType.IDENTIFIER_EXPR

    def test_move_expr_in_var_decl(self):
        result = self._parse("整数型 a = 移动(b);")
        assert result is not None
        decl = result.declarations[0]
        assert decl.node_type == ASTNodeType.VARIABLE_DECL
        assert decl.name == "a"
        assert decl.init is not None
        assert decl.init.node_type == ASTNodeType.MOVE_EXPR

    def test_multiple_smart_ptrs(self):
        source = """
        独享指针<整数型> p1 = 10;
        共享指针<字符串> p2;
        弱指针<浮点型> p3;
        """
        result = self._parse(source)
        assert result is not None
        assert len(result.declarations) == 3
        assert result.declarations[0].node_type == ASTNodeType.UNIQUE_PTR_DECL
        assert result.declarations[1].node_type == ASTNodeType.SHARED_PTR_DECL
        assert result.declarations[2].node_type == ASTNodeType.WEAK_PTR_DECL


# ============================================================================
# RAII 核心测试
# ============================================================================


class TestDestructorInfo:
    """测试析构函数信息"""

    def test_create_and_call(self):
        called = []
        info = DestructorInfo(
            obj_id="test",
            destructor=lambda: called.append(True),
        )
        assert info.is_called is False
        result = info.call()
        assert result is True
        assert info.is_called is True
        assert called == [True]

    def test_double_call(self):
        called = []
        info = DestructorInfo(
            obj_id="test",
            destructor=lambda: called.append(True),
        )
        info.call()
        result = info.call()
        assert result is False
        assert len(called) == 1

    def test_error_in_destructor(self):
        info = DestructorInfo(
            obj_id="test",
            destructor=lambda: 1 / 0,
        )
        result = info.call()
        assert result is False
        assert info.is_called is True


class TestCleanupStack:
    """测试清理栈"""

    def test_push_and_pop_all(self):
        called = []
        stack = CleanupStack()
        stack.push(lambda: called.append("A"))
        stack.push(lambda: called.append("B"))
        assert len(stack) == 2
        stack.pop_all()
        assert len(stack) == 0
        assert len(called) == 2

    def test_scope_enter_exit(self):
        called = []
        stack = CleanupStack()
        scope = stack.enter_scope()
        stack.push(lambda: called.append(f"scope_{scope}"))
        stack.exit_scope()
        assert len(called) == 1

    def test_with_statement(self):
        called = []
        with CleanupStack() as stack:
            stack.push(lambda: called.append("cleanup"))
        assert called == ["cleanup"]

    def test_priority_ordering(self):
        called = []
        stack = CleanupStack()
        stack.push(lambda: called.append("normal"), priority=CleanupPriority.NORMAL)
        stack.push(lambda: called.append("high"), priority=CleanupPriority.HIGH)
        stack.push(lambda: called.append("low"), priority=CleanupPriority.LOW)
        stack.pop_all()
        # 高优先级先被调用
        assert called[0] == "high"

    def test_remove(self):
        called = []
        stack = CleanupStack()
        info = stack.push(lambda: called.append("A"))
        stack.remove(info.obj_id)
        stack.pop_all()
        assert called == []


class TestScopeGuard:
    """测试作用域守卫"""

    def test_with_statement(self):
        called = []
        with ScopeGuard(lambda: called.append("cleanup")):
            pass
        assert called == ["cleanup"]

    def test_dismiss(self):
        called = []
        guard = ScopeGuard(lambda: called.append("cleanup"))
        guard.dismiss()
        del guard
        assert called == []

    def test_force_call(self):
        called = []
        guard = ScopeGuard(lambda: called.append("cleanup"))
        guard.force_call()
        assert called == ["cleanup"]


class TestDestructorRegistry:
    """测试析构函数注册表"""

    def test_register_and_get(self):
        registry = DestructorRegistry()
        destructor = lambda obj: None
        registry.register("MyClass", destructor)
        assert registry.has("MyClass")
        assert registry.get("MyClass") is destructor

    def test_unregister(self):
        registry = DestructorRegistry()
        registry.register("MyClass", lambda obj: None)
        assert registry.unregister("MyClass") is True
        assert registry.has("MyClass") is False

    def test_list_types(self):
        registry = DestructorRegistry()
        registry.register("A", lambda obj: None)
        registry.register("B", lambda obj: None)
        types = registry.list_registered_types()
        assert "A" in types
        assert "B" in types

    def test_create_instance_destructor(self):
        registry = DestructorRegistry()
        destroyed = []
        registry.register("MyClass", lambda obj: destroyed.append(obj))

        class MyObj:
            pass

        obj = MyObj()
        info = registry.create_instance_destructor("MyClass", obj)
        assert info is not None
        info.call()
        assert len(destroyed) == 1


# ============================================================================
# 调用栈追踪测试
# ============================================================================


class TestCallStackTracer:
    """测试调用栈追踪器"""

    def test_capture_and_get(self):
        tracer = CallStackTracer()
        sid = tracer.capture(alloc_ptr=1001, alloc_size=128)
        stack = tracer.get_stack(sid)
        assert stack is not None
        assert stack.alloc_ptr == 1001
        assert stack.alloc_size == 128

    def test_get_by_ptr(self):
        tracer = CallStackTracer()
        tracer.capture(alloc_ptr=2001, alloc_size=256)
        stack = tracer.get_stack_by_ptr(2001)
        assert stack is not None
        assert stack.alloc_size == 256

    def test_release(self):
        tracer = CallStackTracer()
        tracer.capture(alloc_ptr=3001, alloc_size=64)
        assert tracer.release(3001) is True
        assert tracer.get_stack_by_ptr(3001) is None

    def test_leak_stacks(self):
        tracer = CallStackTracer()
        tracer.capture(alloc_ptr=1, alloc_size=10)
        tracer.capture(alloc_ptr=2, alloc_size=20)
        tracer.release(1)
        leaks = tracer.get_leak_stacks()
        assert len(leaks) == 1
        assert leaks[0].alloc_ptr == 2

    def test_clear(self):
        tracer = CallStackTracer()
        tracer.capture(alloc_ptr=1, alloc_size=10)
        tracer.clear()
        assert len(tracer) == 0

    def test_stack_format(self):
        tracer = CallStackTracer()
        sid = tracer.capture(alloc_ptr=5000, alloc_size=1024)
        stack = tracer.get_stack(sid)
        formatted = stack.format(max_frames=3)
        assert "5000" in formatted
        assert "1024" in formatted


# ============================================================================
# IR 操作码测试
# ============================================================================


class TestMemoryOpcodes:
    """测试内存管理 IR 操作码"""

    def test_smart_ptr_create_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.SMART_PTR_CREATE.name == "smart_ptr_create"
        assert Opcode.SMART_PTR_CREATE.category == "内存管理"

    def test_move_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.MOVE.name == "move"
        assert Opcode.MOVE.category == "内存管理"

    def test_scope_opcodes(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.SCOPE_PUSH.category == "内存管理"
        assert Opcode.SCOPE_POP.category == "内存管理"
        assert Opcode.DESTRUCTOR_CALL.category == "内存管理"


# ============================================================================
# 关键字映射测试
# ============================================================================


class TestKeywordsMapping:
    """测试关键字映射文件"""

    def test_memory_keywords_in_keywords_py(self):
        from zhc.keywords import M

        assert "独享指针" in M
        assert "共享指针" in M
        assert "弱指针" in M
        assert "析构函数" in M
        assert "移动" in M
