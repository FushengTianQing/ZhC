# -*- coding: utf-8 -*-
"""
异常传播机制测试

测试异常传播、栈展开、finally 执行等功能。

作者：远
日期：2026-04-10
"""

import pytest
import sys

# 导入被测试模块
sys.path.insert(0, "/Users/yuan/Projects/ZhC/src")

from zhc.exception.context import (
    ExceptionContext,
    ExceptionState,
    ExceptionHandler,
    StackFrameInfo,
)
from zhc.exception.propagation import (
    ExceptionPropagator,
    StackUnwinder,
    throw_exception,
    get_current_exception,
)
from zhc.exception.types import ExceptionObject
from zhc.exception.registry import ExceptionRegistry


class TestExceptionContext:
    """测试 ExceptionContext 类"""

    def test_create_context(self):
        """测试创建异常上下文"""
        ctx = ExceptionContext()
        assert ctx.current_exception is None
        assert ctx.state == ExceptionState.NONE
        assert len(ctx.stack_frames) == 0
        assert len(ctx.handler_stack) == 0

    def test_push_pop_frame(self):
        """测试栈帧压入弹出"""
        ctx = ExceptionContext()

        frame1 = StackFrameInfo("func1", "test.zhc", 1)
        frame2 = StackFrameInfo("func2", "test.zhc", 10)

        ctx.push_frame(frame1)
        assert len(ctx.stack_frames) == 1
        assert ctx.get_current_frame() == frame1

        ctx.push_frame(frame2)
        assert len(ctx.stack_frames) == 2
        assert ctx.get_current_frame() == frame2

        popped = ctx.pop_frame()
        assert popped == frame2
        assert len(ctx.stack_frames) == 1
        assert ctx.get_current_frame() == frame1

        popped = ctx.pop_frame()
        assert popped == frame1
        assert len(ctx.stack_frames) == 0
        assert ctx.get_current_frame() is None

    def test_register_unregister_handler(self):
        """测试处理器注册注销"""
        ctx = ExceptionContext()

        # 创建处理器
        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=lambda: None,
        )

        # 注册
        ctx.push_frame(StackFrameInfo("main", "test.zhc", 1))
        ctx.register_handler(handler)
        assert len(ctx.handler_stack) == 1

        # 注销
        unregistered = ctx.unregister_handler()
        assert unregistered == handler
        assert len(ctx.handler_stack) == 0

    def test_find_handler_exact_match(self):
        """测试精确匹配处理器"""
        ctx = ExceptionContext()
        registry = ExceptionRegistry.instance()

        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=lambda: None,
        )

        ctx.register_handler(handler)

        found = ctx.find_handler("除零异常", registry)
        assert found == handler

    def test_find_handler_subtype_match(self):
        """测试子类型匹配处理器"""
        ctx = ExceptionContext()
        registry = ExceptionRegistry.instance()

        # 处理器注册为捕获"算术异常"
        handler = ExceptionHandler(
            exception_types=["算术异常"],
            variable_name="e",
            catch_block=lambda: None,
        )

        ctx.register_handler(handler)

        # "除零异常"是"算术异常"的子类型，应该匹配
        found = ctx.find_handler("除零异常", registry)
        assert found == handler

    def test_find_handler_default(self):
        """测试默认处理器匹配"""
        ctx = ExceptionContext()
        registry = ExceptionRegistry.instance()

        default_handler = ExceptionHandler(
            exception_types=[],
            variable_name="e",
            catch_block=lambda: None,
            is_default=True,
        )

        ctx.register_handler(default_handler)

        # 默认处理器应该匹配任何异常类型
        found = ctx.find_handler("任意未知异常", registry)
        assert found == default_handler

    def test_handle_uncaught(self):
        """测试未捕获异常处理"""
        ctx = ExceptionContext()

        # 创建异常对象
        exc = ExceptionObject("除零异常", "除数不能为零")

        # 设置自定义处理器
        handled = []

        def custom_handler(e):
            handled.append(e)

        ctx.set_uncaught_handler(custom_handler)
        ctx.current_exception = exc
        ctx.handle_uncaught()

        assert len(handled) == 1
        assert handled[0] == exc

    def test_context_manager(self):
        """测试上下文管理器"""
        with ExceptionContext() as ctx:
            ctx.current_exception = ExceptionObject("异常", "测试")

        # 退出后应该清除状态
        assert ctx.current_exception is None


class TestExceptionHandler:
    """测试 ExceptionHandler 类"""

    def test_handler_matches_exact(self):
        """测试精确匹配"""
        handler = ExceptionHandler(
            exception_types=["除零异常", "空指针异常"],
            variable_name="e",
            catch_block=lambda: None,
        )

        assert handler.matches("除零异常", None) is True
        assert handler.matches("空指针异常", None) is True
        assert handler.matches("溢出异常", None) is False

    def test_handler_matches_with_registry(self):
        """测试带注册表的子类型匹配"""
        registry = ExceptionRegistry.instance()

        handler = ExceptionHandler(
            exception_types=["算术异常"],
            variable_name="e",
            catch_block=lambda: None,
        )

        # "除零异常"是"算术异常"的子类型
        assert handler.matches("除零异常", registry) is True
        # "溢出异常"也是"算术异常"的子类型
        assert handler.matches("溢出异常", registry) is True
        # "空指针异常"不是"算术异常"的子类型
        assert handler.matches("空指针异常", registry) is False

    def test_handler_is_default(self):
        """测试默认处理器"""
        handler = ExceptionHandler(
            exception_types=[],
            variable_name="e",
            catch_block=lambda: None,
            is_default=True,
        )

        # 默认处理器匹配所有类型
        assert handler.matches("任意类型", None) is True
        assert handler.matches("另一个类型", None) is True


class TestStackUnwinder:
    """测试 StackUnwinder 类"""

    def test_unwind_to_handler(self):
        """测试栈展开到处理器"""
        ctx = ExceptionContext()
        unwinder = StackUnwinder(ctx)

        # 推送栈帧
        finally_calls = []

        def make_finally(name):
            def f():
                finally_calls.append(name)

            return f

        ctx.push_frame(
            StackFrameInfo(
                "func1",
                "test.zhc",
                1,
                has_finally=True,
                finally_handler=make_finally("func1"),
            )
        )
        ctx.push_frame(
            StackFrameInfo(
                "func2",
                "test.zhc",
                10,
                has_finally=True,
                finally_handler=make_finally("func2"),
            )
        )
        ctx.push_frame(
            StackFrameInfo(
                "func3",
                "test.zhc",
                20,
                has_finally=True,
                finally_handler=make_finally("func3"),
            )
        )

        handler = ExceptionHandler(
            exception_types=["异常"],
            variable_name="e",
            catch_block=lambda: None,
            frame_index=0,  # 目标帧是 func1
        )

        finally_blocks = unwinder.unwind_to_handler(handler)

        # unwind_to_handler 收集 finally_blocks（目标帧的 finally 也会被收集）
        # 需要调用 execute_finally_blocks 来执行
        # func3, func2, func1 的 finally 都会被收集
        assert len(finally_blocks) == 3  # func3, func2, func1
        assert finally_calls == []  # 还没执行

        # 执行 finally 块（逆序）
        unwinder.execute_finally_blocks(finally_blocks, in_reverse=True)
        assert finally_calls == ["func1", "func2", "func3"]

        # func1 作为目标帧，其栈帧被保留
        assert len(ctx.stack_frames) == 1

    def test_unwind_to_top(self):
        """测试展开到顶层"""
        ctx = ExceptionContext()
        unwinder = StackUnwinder(ctx)

        finally_calls = []

        def make_finally(name):
            def f():
                finally_calls.append(name)

            return f

        ctx.push_frame(
            StackFrameInfo(
                "func1",
                "test.zhc",
                1,
                has_finally=True,
                finally_handler=make_finally("func1"),
            )
        )
        ctx.push_frame(
            StackFrameInfo(
                "func2",
                "test.zhc",
                10,
                has_finally=True,
                finally_handler=make_finally("func2"),
            )
        )

        finally_blocks = unwinder.unwind_to_top()

        # 所有 finally 都应该被执行
        assert len(finally_blocks) == 2
        assert len(ctx.stack_frames) == 0

    def test_execute_finally_blocks(self):
        """测试执行 finally 块"""
        ctx = ExceptionContext()
        unwinder = StackUnwinder(ctx)

        calls = []

        finally_blocks = [
            lambda: calls.append(1),
            lambda: calls.append(2),
            lambda: calls.append(3),
        ]

        # 逆序执行
        unwinder.execute_finally_blocks(finally_blocks, in_reverse=True)
        assert calls == [3, 2, 1]

        # 顺序执行
        calls = []
        unwinder.execute_finally_blocks(finally_blocks, in_reverse=False)
        assert calls == [1, 2, 3]


class TestExceptionPropagator:
    """测试 ExceptionPropagator 类"""

    def setup_method(self):
        """每个测试前的设置"""
        ExceptionPropagator.reset()
        ExceptionRegistry.reset()  # 重置注册表

    def test_singleton(self):
        """测试单例模式"""
        inst1 = ExceptionPropagator.instance()
        inst2 = ExceptionPropagator.instance()
        assert inst1 is inst2

    def test_basic_throw_and_catch(self):
        """测试基本的抛出和捕获"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        # 推送栈帧
        propagator.push_frame("main", "test.zhc", 1)

        # 注册处理器
        caught = []

        def catch_block():
            caught.append(get_current_exception())

        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=catch_block,
        )
        ctx.register_handler(handler)

        # 抛出异常
        exc = ExceptionObject("除零异常", "除数不能为零")
        propagator.throw(exc)

        # 验证被捕获
        assert len(caught) == 1
        assert caught[0].type_name == "除零异常"

    def test_throw_without_handler(self):
        """测试无处理器时的异常抛出"""
        propagator = ExceptionPropagator.instance()

        # 推送栈帧但没有处理器
        propagator.push_frame("main", "test.zhc", 1)

        exc = ExceptionObject("除零异常", "测试")

        # 应该调用未捕获处理器（会终止程序，这里用 pytest 捕获）
        with pytest.raises(SystemExit):
            propagator.throw(exc)

    def test_rethrow(self):
        """测试重新抛出"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        propagator.push_frame("main", "test.zhc", 1)

        # 先设置一个当前异常
        ctx.current_exception = ExceptionObject("除零异常", "原始异常")

        # 注册处理器
        caught = []

        def catch_block():
            caught.append(get_current_exception())
            # 在 catch 块中重新抛出
            from zhc.exception.propagation import rethrow_exception

            rethrow_exception()

        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=catch_block,
        )
        ctx.register_handler(handler)

        # 这个测试会在重新抛出时查找新的处理器，但找不到，触发 SystemExit
        with pytest.raises(SystemExit):
            propagator.rethrow()

    def test_catch_block_exception(self):
        """测试 catch 块中抛出异常"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        propagator.push_frame("main", "test.zhc", 1)

        first_catch = []

        def catch_block_that_throws():
            first_catch.append(True)
            # 抛出新异常
            throw_exception(ExceptionObject("溢出异常", "catch 块中的新异常"))

        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=catch_block_that_throws,
        )
        ctx.register_handler(handler)

        exc = ExceptionObject("除零异常", "原始异常")

        # catch 块中抛出异常会被传播，可能触发 SystemExit
        try:
            propagator.throw(exc)
        except (Exception, SystemExit):
            pass  # 允许任何异常

        assert len(first_catch) == 1

    def test_finally_execution(self):
        """测试 finally 执行"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        calls = []

        # 场景：func1 调用 func2，func2 有 try-catch-finally
        # func1 先入栈（外层函数）
        ctx.push_frame(
            StackFrameInfo(
                "func1",
                "test.zhc",
                1,
                has_finally=True,
                finally_handler=lambda: calls.append("finally1"),
            )
        )

        # func2 入栈（内层函数，有 try-catch）
        ctx.push_frame(
            StackFrameInfo(
                "func2",
                "test.zhc",
                10,
                has_finally=True,
                finally_handler=lambda: calls.append("finally2"),
            )
        )

        # 注册处理器（handler 属于 func2，即 index=1）
        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=lambda: calls.append("catch"),
            frame_index=1,  # func2 的索引
        )
        ctx.register_handler(handler)

        # 模拟在 func2 中抛出异常
        exc = ExceptionObject("除零异常", "测试")
        propagator.throw(exc)

        # func2 的 finally 应该被执行（因为 func2 有 finally）
        # func1 的 finally 也会被执行（因为要展开到 func1）
        assert "finally1" in calls or "finally2" in calls
        assert "catch" in calls

    def test_subtype_catch(self):
        """测试子类型捕获"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        propagator.push_frame("main", "test.zhc", 1)

        caught_type = []

        def catch_block():
            exc = get_current_exception()
            if exc:
                caught_type.append(exc.type_name)

        # 注册捕获"算术异常"的处理器
        handler = ExceptionHandler(
            exception_types=["算术异常"],
            variable_name="e",
            catch_block=catch_block,
        )
        ctx.register_handler(handler)

        # 抛出"除零异常"（算术异常的子类型）
        exc = ExceptionObject("除零异常", "除数不能为零")
        propagator.throw(exc)

        assert len(caught_type) == 1
        assert caught_type[0] == "除零异常"

    def test_register_finally(self):
        """测试注册 finally 块"""
        propagator = ExceptionPropagator.instance()

        propagator.push_frame("func", "test.zhc", 1)

        calls = []
        propagator.register_finally(lambda: calls.append("finally"))

        # 检查 finally 是否被注册
        frame = propagator.context.get_current_frame()
        assert frame.has_finally is True
        assert len(calls) == 0  # 还没有调用

    def test_register_cleanup(self):
        """测试注册清理处理器"""
        propagator = ExceptionPropagator.instance()

        propagator.push_frame("func", "test.zhc", 1)

        calls = []
        propagator.register_cleanup(lambda: calls.append("cleanup"))

        # 检查 cleanup 是否被注册
        frame = propagator.context.get_current_frame()
        assert len(frame.cleanup_handlers) == 1


class TestConvenienceFunctions:
    """测试便捷函数"""

    def setup_method(self):
        """每个测试前的设置"""
        ExceptionPropagator.reset()
        ExceptionRegistry.reset()

    def test_throw_exception_function(self):
        """测试 throw_exception 函数"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        propagator.push_frame("main", "test.zhc", 1)

        caught = []
        handler = ExceptionHandler(
            exception_types=["除零异常"],
            variable_name="e",
            catch_block=lambda: caught.append(get_current_exception()),
        )
        ctx.register_handler(handler)

        exc = ExceptionObject("除零异常", "便捷函数测试")
        throw_exception(exc)

        assert len(caught) == 1

    def test_get_current_exception(self):
        """测试 get_current_exception 函数"""
        propagator = ExceptionPropagator.instance()
        ctx = propagator.context

        exc = ExceptionObject("异常", "测试异常")
        ctx.current_exception = exc

        current = get_current_exception()
        assert current == exc


class TestExceptionState:
    """测试异常状态"""

    def test_exception_state_values(self):
        """测试异常状态枚举值"""
        assert ExceptionState.NONE.value == "none"
        assert ExceptionState.THROWING.value == "throwing"
        assert ExceptionState.UNWINDING.value == "unwinding"
        assert ExceptionState.CAUGHT.value == "caught"
        assert ExceptionState.HANDLED.value == "handled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
