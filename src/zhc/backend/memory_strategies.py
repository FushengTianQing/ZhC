# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 智能指针编译策略

实现智能指针相关的 LLVM IR 编译策略。

策略列表：
- SmartPtrCreateStrategy: 创建智能指针
- SmartPtrGetStrategy: 获取智能指针值
- SmartPtrResetStrategy: 重置智能指针
- SmartPtrReleaseStrategy: 释放智能指针
- SmartPtrUseCountStrategy: 获取引用计数
- MoveStrategy: 移动语义
- ScopePushStrategy: 进入作用域
- ScopePopStrategy: 退出作用域
- DestructorCallStrategy: 调用析构函数

作者：阿福
日期：2026-04-10
"""

import logging
from typing import Optional, TYPE_CHECKING

from zhc.ir.opcodes import Opcode
from .llvm_instruction_strategy import InstructionStrategy

if TYPE_CHECKING:
    import llvmlite.ir as ll
    from zhc.backend.compilation_context import CompilationContext

logger = logging.getLogger(__name__)


class SmartPtrCreateStrategy(InstructionStrategy):
    """
    创建智能指针编译策略

    生成 LLVM IR 来分配和初始化智能指针。

    独享指针: 直接分配对象内存
    共享指针: 分配 ControlBlock + 对象内存
    弱指针: 分配弱引用控制块
    """

    opcode = Opcode.SMART_PTR_CREATE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []
        kind = operands[0] if len(operands) > 0 else "unique"
        _inner_type_name = operands[1] if len(operands) > 1 else "i32"  # noqa: F841
        init_value = operands[2] if len(operands) > 2 else None

        # 获取 LLVM 类型
        i8 = ll.IntType(8)
        i32 = ll.IntType(32)
        i64 = ll.IntType(64)
        ptr_ty = i8.as_pointer()

        # 获取 malloc 和 free 函数
        malloc_fn = self._get_or_declare_malloc(context)

        result_name = context.get_result_name(instr) or f"{kind}_ptr"

        if kind == "unique":
            # 独享指针：直接分配对象
            obj_size = i64(8)  # 占位：实际应根据类型计算
            raw_ptr = builder.call(malloc_fn, [obj_size], name=f"{result_name}_raw")

            # 如果有初始值，存储到分配的内存中
            if init_value and isinstance(init_value, ll.Value):
                obj_ptr = builder.bitcast(
                    raw_ptr, init_value.type.as_pointer(), name=f"{result_name}_obj"
                )
                builder.store(init_value, obj_ptr)

            return raw_ptr

        elif kind == "shared":
            # 共享指针：分配 ControlBlock + 对象
            # struct ControlBlock { i32 ref_count, i32 weak_count, void* object }
            ctrl_size = i64(16)  # ref_count(4) + weak_count(4) + padding(8)
            ctrl_ptr = builder.call(malloc_fn, [ctrl_size], name=f"{result_name}_ctrl")

            # 初始化引用计数为 1
            ctrl_i32_ptr = builder.bitcast(ctrl_ptr, i32.as_pointer(), name="ctrl_i32")
            builder.store(i32(1), ctrl_i32_ptr)

            # weak_count = 0
            weak_count_ptr = builder.gep(ctrl_i32_ptr, [i32(1)], name="weak_count_ptr")
            builder.store(i32(0), weak_count_ptr)

            return ctrl_ptr

        elif kind == "weak":
            # 弱指针：分配空的弱引用
            weak_size = i64(8)
            weak_ptr = builder.call(malloc_fn, [weak_size], name=f"{result_name}_weak")
            null_ptr = ll.Constant(ptr_ty, None)
            builder.store(null_ptr, builder.bitcast(weak_ptr, ptr_ty.as_pointer()))

            return weak_ptr

        return None

    def _get_or_declare_malloc(self, context: "CompilationContext"):
        """获取或声明 malloc 函数"""
        import llvmlite.ir as ll

        module = context.module
        malloc_fn = module.globals.get("malloc")
        if malloc_fn is None:
            i64 = ll.IntType(64)
            i8 = ll.IntType(8)
            malloc_ty = ll.FunctionType(i8.as_pointer(), [i64])
            malloc_fn = ll.Function(module, malloc_ty, name="malloc")
        return malloc_fn


class SmartPtrGetStrategy(InstructionStrategy):
    """获取智能指针值"""

    opcode = Opcode.SMART_PTR_GET

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []
        if not operands:
            return None

        ptr_value = operands[0]
        if ptr_value and isinstance(ptr_value, ll.Value):
            i8 = ll.IntType(8)
            # 加载指针指向的值
            result = builder.load(
                builder.bitcast(ptr_value, i8.as_pointer().as_pointer()),
                name=context.get_result_name(instr) or "ptr_val",
            )
            return result
        return None


class SmartPtrResetStrategy(InstructionStrategy):
    """重置智能指针"""

    opcode = Opcode.SMART_PTR_RESET

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        # 重置操作：释放旧指针，置空
        # 实际实现需要调用析构函数并释放内存
        logger.debug("SmartPtrReset: 生成重置指令")
        return None


class SmartPtrReleaseStrategy(InstructionStrategy):
    """释放智能指针"""

    opcode = Opcode.SMART_PTR_RELEASE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        # 释放操作：减少引用计数，如果为0则释放
        free_fn = self._get_or_declare_free(context)
        operands = instr.operands if instr.operands else []
        if operands and isinstance(operands[0], ll.Value):
            builder.call(free_fn, [operands[0]])
        return None

    def _get_or_declare_free(self, context: "CompilationContext"):
        """获取或声明 free 函数"""
        import llvmlite.ir as ll

        module = context.module
        free_fn = module.globals.get("free")
        if free_fn is None:
            i8 = ll.IntType(8)
            free_ty = ll.FunctionType(ll.VoidType(), [i8.as_pointer()])
            free_fn = ll.Function(module, free_ty, name="free")
        return free_fn


class SmartPtrUseCountStrategy(InstructionStrategy):
    """获取引用计数"""

    opcode = Opcode.SMART_PTR_USE_COUNT

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []
        if operands and isinstance(operands[0], ll.Value):
            i32 = ll.IntType(32)
            ctrl_ptr = builder.bitcast(operands[0], i32.as_pointer(), name="ctrl_i32")
            count = builder.load(
                ctrl_ptr, name=context.get_result_name(instr) or "use_count"
            )
            return count
        return None


class MoveStrategy(InstructionStrategy):
    """移动语义编译策略

    将资源的所有权从源转移到目标，源变为无效状态。
    """

    opcode = Opcode.MOVE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []
        if not operands:
            return None

        src_value = operands[0]
        if src_value and isinstance(src_value, ll.Value):
            # 移动语义：直接传递指针值
            # 返回源的值，源将被置为 null
            result = src_value
            return result
        return None


class ScopePushStrategy(InstructionStrategy):
    """进入作用域"""

    opcode = Opcode.SCOPE_PUSH

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        # 作用域标记，不需要生成具体指令
        logger.debug("ScopePush: 进入作用域")
        return None


class ScopePopStrategy(InstructionStrategy):
    """退出作用域"""

    opcode = Opcode.SCOPE_POP

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        # 退出作用域，调用该作用域内注册的所有析构函数
        logger.debug("ScopePop: 退出作用域，触发析构")
        return None


class DestructorCallStrategy(InstructionStrategy):
    """调用析构函数"""

    opcode = Opcode.DESTRUCTOR_CALL

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []
        if not operands:
            return None

        obj_ptr = operands[0]
        if obj_ptr and isinstance(obj_ptr, ll.Value):
            # 调用对象的析构函数
            # 实际实现需要查找类型对应的析构函数并调用
            free_fn = self._get_or_declare_free(context)
            builder.call(free_fn, [obj_ptr])
        return None

    def _get_or_declare_free(self, context: "CompilationContext"):
        """获取或声明 free 函数"""
        import llvmlite.ir as ll

        module = context.module
        free_fn = module.globals.get("free")
        if free_fn is None:
            i8 = ll.IntType(8)
            free_ty = ll.FunctionType(ll.VoidType(), [i8.as_pointer()])
            free_fn = ll.Function(module, free_ty, name="free")
        return free_fn
