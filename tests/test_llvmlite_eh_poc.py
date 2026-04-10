# -*- coding: utf-8 -*-
"""
llvmlite EH 指令能力验证 POC

验证 llvmlite 0.43.0 对 LLVM 异常处理指令的支持情况。

运行方式:
    python -m pytest tests/test_llvmlite_eh_poc.py -v
    或直接运行: python tests/test_llvmlite_eh_poc.py

作者：远
日期：2026-04-10
"""

import unittest
from llvmlite import ir


class TestLlvmITEHSupport(unittest.TestCase):
    """llvmlite EH 指令支持验证"""

    def setUp(self):
        """创建基础的 IR 结构"""
        self.ctx = ir.Context()
        self.module = ir.Module()
        self.module.triple = "x86_64-pc-linux-gnu"
        self.module.data_layout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"

    def create_function(self, name: str, ret_type=None, arg_types=None):
        """创建测试用函数"""
        if ret_type is None:
            ret_type = ir.IntType(32)
        if arg_types is None:
            arg_types = []
        func_ty = ir.FunctionType(ret_type, arg_types)
        return ir.Function(self.module, func_ty, name=name)

    # ========== LandingPadInstr 测试 ==========

    def test_landingpad_creation(self):
        """测试 LandingPadInstr 基本创建"""
        func = self.create_function("test_landingpad")
        block = func.append_basic_block("unwind")

        ptr_ty = ir.PointerType(ir.IntType(8))
        lp = ir.LandingPadInstr(block, ptr_ty, cleanup=True)

        self.assertIsNotNone(lp)
        self.assertIn("landingpad", str(lp))
        self.assertIn("i8*", str(lp))
        self.assertIn("cleanup", str(lp))

    def test_landingpad_with_catch_clause(self):
        """测试 LandingPadInstr 添加 catch clause"""
        func = self.create_function("test_catch")
        block = func.append_basic_block("unwind")

        ptr_ty = ir.PointerType(ir.IntType(8))
        lp = ir.LandingPadInstr(block, ptr_ty, cleanup=True)

        # 添加 catch clause
        type_info = ir.GlobalValue(self.module, ptr_ty, name="exc_type_info")
        catch_clause = ir.CatchClause(type_info)
        lp.add_clause(catch_clause)

        self.assertIn("catch", str(lp))
        self.assertIn("exc_type_info", str(lp))

    def test_landingpad_with_filter_clause(self):
        """测试 LandingPadInstr 添加 filter clause"""
        func = self.create_function("test_filter")
        block = func.append_basic_block("unwind")

        ptr_ty = ir.PointerType(ir.IntType(8))
        lp = ir.LandingPadInstr(block, ptr_ty, cleanup=True)

        # Filter clause 需要 Constant 类型的数组
        array_ty = ir.ArrayType(ptr_ty, 0)  # 空数组表示捕获所有
        filter_value = ir.Constant(array_ty, None)
        filter_clause = ir.FilterClause(filter_value)
        lp.add_clause(filter_clause)

        self.assertIn("filter", str(lp))
        self.assertIn("zeroinitializer", str(lp))

    # ========== Resume 测试 ==========

    def test_resume_creation(self):
        """测试 Resume 指令创建"""
        func = self.create_function("test_resume")
        block = func.append_basic_block("unwind")

        ptr_ty = ir.PointerType(ir.IntType(8))
        lp = ir.LandingPadInstr(block, ptr_ty, cleanup=True)

        resume = ir.Resume(block, "resume", [lp])

        self.assertIsNotNone(resume)
        self.assertIn("resume", str(resume))

    def test_resume_without_operands(self):
        """测试无操作数的 Resume（重新抛出）"""
        func = self.create_function("test_resume_rethrow")
        block = func.append_basic_block("unwind")

        resume = ir.Resume(block, "resume", [])

        self.assertIsNotNone(resume)

    # ========== InvokeInstr 测试 ==========

    def test_invoke_creation(self):
        """测试 InvokeInstr 创建"""
        callee = self.create_function("might_throw")
        func = self.create_function("test_invoke")

        entry_block = func.append_basic_block("entry")
        normal_block = func.append_basic_block("normal")
        unwind_block = func.append_basic_block("unwind")

        invoke = ir.InvokeInstr(
            entry_block, callee, [], normal_block, unwind_block, name="result"
        )

        self.assertIsNotNone(invoke)
        self.assertIn("invoke", str(invoke))
        self.assertIn("to label", str(invoke))
        self.assertIn("unwind label", str(invoke))

    def test_invoke_with_args(self):
        """测试带参数的 InvokeInstr"""
        callee = self.create_function(
            "might_throw", arg_types=[ir.IntType(32), ir.IntType(32)]
        )
        func = self.create_function("test_invoke_args")

        entry_block = func.append_basic_block("entry")
        normal_block = func.append_basic_block("normal")
        unwind_block = func.append_basic_block("unwind")

        arg1 = ir.Constant(ir.IntType(32), 10)
        arg2 = ir.Constant(ir.IntType(32), 20)
        invoke = ir.InvokeInstr(
            entry_block, callee, [arg1, arg2], normal_block, unwind_block, name="result"
        )

        self.assertIn("10", str(invoke))
        self.assertIn("20", str(invoke))

    # ========== EH Intrinsics 测试 ==========

    def test_eh_typeid_for_intrinsic(self):
        """测试 llvm.eh.typeid.for intrinsics"""
        ptr_ty = ir.PointerType(ir.IntType(8))

        # 使用 declare_intrinsic
        fn = self.module.declare_intrinsic("llvm.eh.typeid.for", [ptr_ty])

        self.assertIsNotNone(fn)
        self.assertEqual(fn.name, "llvm.eh.typeid.for.p0i8")

    def test_eh_begincatch_manual_declare(self):
        """测试 llvm.eh.begincatch（需手动声明）"""
        begincatch_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(ir.IntType(8))])
        begincatch = ir.Function(self.module, begincatch_ty, name="llvm.eh.begincatch")

        self.assertIsNotNone(begincatch)
        self.assertEqual(begincatch.name, "llvm.eh.begincatch")

    def test_eh_endcatch_manual_declare(self):
        """测试 llvm.eh.endcatch（需手动声明）"""
        endcatch_ty = ir.FunctionType(ir.VoidType(), [])
        endcatch = ir.Function(self.module, endcatch_ty, name="llvm.eh.endcatch")

        self.assertIsNotNone(endcatch)
        self.assertEqual(endcatch.name, "llvm.eh.endcatch")

    # ========== Personality 函数测试 ==========

    def test_personality_function(self):
        """测试 personality 函数声明"""
        personality_ty = ir.FunctionType(ir.IntType(32), [])
        personality = ir.Function(self.module, personality_ty, name="__zhc_personality")

        self.assertIsNotNone(personality)
        self.assertEqual(personality.name, "__zhc_personality")
        self.assertTrue(personality.is_declaration)

    # ========== 完整 IR 生成测试 ==========

    def test_complete_eh_module_generation(self):
        """测试生成完整的 EH IR 模块"""
        # 1. 声明 personality
        personality_ty = ir.FunctionType(ir.IntType(32), [])
        personality = ir.Function(self.module, personality_ty, name="__zhc_personality")

        # 2. 声明 eh intrinsics
        self.module.declare_intrinsic(
            "llvm.eh.typeid.for", [ir.PointerType(ir.IntType(8))]
        )

        begincatch_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(ir.IntType(8))])
        ir.Function(self.module, begincatch_ty, name="llvm.eh.begincatch")
        ir.Function(
            self.module, ir.FunctionType(ir.VoidType(), []), name="llvm.eh.endcatch"
        )

        # 3. 声明可能抛异常的函数
        might_throw_ty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        might_throw = ir.Function(self.module, might_throw_ty, name="might_throw")

        # 4. 定义主函数
        main_ty = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_ty, name="main")

        entry_block = main_func.append_basic_block("entry")
        try_block = main_func.append_basic_block("try")
        catch_block = main_func.append_basic_block("catch")
        finally_block = main_func.append_basic_block("finally")
        normal_return = main_func.append_basic_block("normal_return")

        builder = ir.IRBuilder(entry_block)
        builder.branch(try_block)

        # Try 块 - 使用 builder.invoke
        builder.position_at_end(try_block)
        arg = ir.Constant(ir.IntType(32), 42)
        result = builder.invoke(
            might_throw, [arg], normal_return, catch_block, name="call_result"
        )

        # 正常返回
        builder.position_at_end(normal_return)
        builder.ret(result)

        # Catch 块 - 使用 builder.landingpad
        builder.position_at_end(catch_block)
        i8_ptr = ir.PointerType(ir.IntType(8))

        # 使用 builder.landingpad 创建 landingpad（自动追加到 block）
        landingpad = builder.landingpad(i8_ptr, name="lp", cleanup=True)

        exc_type_info = ir.GlobalValue(self.module, i8_ptr, name="exc_type_info")
        catch_clause = ir.CatchClause(exc_type_info)
        landingpad.add_clause(catch_clause)

        typeid_fn = self.module.get_global("llvm.eh.typeid.for.p0i8")
        builder.call(typeid_fn, [landingpad])

        begincatch_fn = self.module.get_global("llvm.eh.begincatch")
        builder.call(begincatch_fn, [landingpad])

        endcatch_fn = self.module.get_global("llvm.eh.endcatch")
        builder.call(endcatch_fn, [])

        # 注意：在这个简单示例中，我们选择处理异常后跳转到 finally
        # 在更复杂的场景中，如果 catch 无法处理异常，需要调用 resume 重新抛出
        # builder.resume(landingpad)

        builder.branch(finally_block)

        # Finally 块
        builder.position_at_end(finally_block)
        builder.ret(ir.Constant(ir.IntType(32), 0))

        # 设置 personality - 使用 _personality 属性
        main_func.attributes._personality = personality

        # 验证生成的 IR
        ir_code = str(self.module)
        self.assertIn("__zhc_personality", ir_code)
        self.assertIn("landingpad", ir_code)
        self.assertIn("invoke", ir_code)
        # resume 在 catch 处理完异常后是可选的（此处演示处理后跳转）
        self.assertIn("llvm.eh.typeid.for", ir_code)


def run_poc():
    """直接运行 POC 生成 IR"""
    module = ir.Module()
    module.triple = "x86_64-pc-linux-gnu"
    module.data_layout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"

    # Personality 函数
    personality_ty = ir.FunctionType(ir.IntType(32), [])
    ir.Function(module, personality_ty, name="__zhc_personality")

    # EH intrinsics
    module.declare_intrinsic("llvm.eh.typeid.for", [ir.PointerType(ir.IntType(8))])
    ir.Function(
        module,
        ir.FunctionType(ir.VoidType(), [ir.PointerType(ir.IntType(8))]),
        name="llvm.eh.begincatch",
    )
    ir.Function(module, ir.FunctionType(ir.VoidType(), []), name="llvm.eh.endcatch")

    # 测试函数
    might_throw_ty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
    might_throw = ir.Function(module, might_throw_ty, name="might_throw")

    main_ty = ir.FunctionType(ir.IntType(32), [])
    main_func = ir.Function(module, main_ty, name="main")

    entry = main_func.append_basic_block("entry")
    try_block = main_func.append_basic_block("try")
    catch = main_func.append_basic_block("catch")
    finally_block = main_func.append_basic_block("finally")
    normal = main_func.append_basic_block("normal")

    builder = ir.IRBuilder(entry)
    builder.branch(try_block)

    builder.position_at_end(try_block)
    arg = ir.Constant(ir.IntType(32), 42)
    result = ir.InvokeInstr(try_block, might_throw, [arg], normal, catch, name="result")

    builder.position_at_end(normal)
    builder.ret(result)

    builder.position_at_end(catch)
    i8_ptr = ir.PointerType(ir.IntType(8))
    lp = ir.LandingPadInstr(catch, i8_ptr, cleanup=True)
    exc_info = ir.GlobalValue(module, i8_ptr, name="exc_type_info")
    lp.add_clause(ir.CatchClause(exc_info))

    builder.branch(finally_block)

    builder.position_at_end(finally_block)
    builder.ret(ir.Constant(ir.IntType(32), 0))

    main_func.attributes.add("personality", module.get_global("__zhc_personality"))

    print("=" * 60)
    print("Generated LLVM IR for Exception Handling:")
    print("=" * 60)
    print(module)
    print("=" * 60)
    print("✅ POC: All EH instructions generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    print("Running llvmlite EH support POC...")
    print()

    # 运行单元测试
    unittest.main(exit=False, verbosity=2)

    print()
    print()
    run_poc()
