# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 重构版本

使用策略模式和统一工具类。

架构：
    IRProgram → LLVMBackend → LLVM Module

作者：远
日期：2026-04-09
"""

from typing import Optional
from pathlib import Path
import logging

try:
    import llvmlite
    import llvmlite.ir as ll
    import llvmlite.binding as llvm

    LLVM_AVAILABLE = True
except ImportError:
    LLVM_AVAILABLE = False
    ll = None
    llvm = None

from zhc.ir.program import IRProgram, IRFunction, IRGlobalVar
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode

from .base import (
    BackendBase,
    BackendCapabilities,
    CompileOptions,
    CompileResult,
    OutputFormat,
    BackendError,
)
from .type_system import get_type_mapper
from .compilation_context import CompilationContext
from .llvm_instruction_strategy import InstructionStrategyFactory
from .closure_strategies import (
    LambdaStrategy,
    ClosureCreateStrategy,
    ClosureCallStrategy,
    UpvalueGetStrategy,
    UpvalueSetStrategy,
)
from .coroutine_strategies import (
    CoroutineCreateStrategy,
    CoroutineResumeStrategy,
    CoroutineYieldStrategy,
    CoroutineAwaitStrategy,
    CoroutineSpawnStrategy,
    ChannelCreateStrategy,
    ChannelSendStrategy,
    ChannelRecvStrategy,
)

# 优化提示模块（可选依赖）
try:
    from zhc.ir.optimization_hints import (
        OptimizationHintAnalyzer,
        ProgramOptimizationHints,
        FunctionOptimizationHints,
        LLVMBackendHintAdapter,
    )

    OPTIMIZATION_HINTS_AVAILABLE = True
except ImportError:
    OPTIMIZATION_HINTS_AVAILABLE = False
    OptimizationHintAnalyzer = None
    ProgramOptimizationHints = None
    FunctionOptimizationHints = None
    LLVMBackendHintAdapter = None

logger = logging.getLogger(__name__)


class LLVMBackendError(BackendError):
    """LLVM 后端错误"""

    pass


class LLVMBackend(BackendBase):
    """
    ZhC LLVM 后端 - 重构版本

    改进：
    1. 使用策略模式处理指令编译
    2. 使用统一的类型映射器
    3. 使用编译上下文管理状态
    4. 更清晰的代码结构
    5. 支持优化提示分析
    """

    def __init__(
        self,
        target_triple: Optional[str] = None,
        enable_optimization_hints: bool = True,
    ):
        """
        初始化 LLVM 后端

        Args:
            target_triple: 目标平台三元组
            enable_optimization_hints: 是否启用优化提示（默认 True）
        """
        if not LLVM_AVAILABLE:
            raise LLVMBackendError(
                "llvmlite 未安装。请运行: pip install llvmlite>=0.39.0"
            )

        self.target_triple = target_triple
        self.module: Optional[ll.Module] = None
        self.type_mapper = get_type_mapper()

        # 初始化编译上下文
        self.context = CompilationContext()

        # 注册闭包策略
        self._register_closure_strategies()
        self._register_memory_strategies()

        # 初始化 LLVM (llvmlite 0.47+: 使用新 API)
        if LLVM_AVAILABLE:
            llvm.initialize_all_targets()
            llvm.initialize_all_asmprinters()

        # TASK-P3-003：优化提示配置
        self.enable_optimization_hints = (
            enable_optimization_hints and OPTIMIZATION_HINTS_AVAILABLE
        )
        self.optimization_hints: Optional[ProgramOptimizationHints] = None
        self.hint_adapter: Optional[LLVMBackendHintAdapter] = None

        if self.enable_optimization_hints:
            self.hint_adapter = LLVMBackendHintAdapter()

    def _register_closure_strategies(self) -> None:
        """注册闭包相关策略"""
        InstructionStrategyFactory.register(LambdaStrategy())
        InstructionStrategyFactory.register(ClosureCreateStrategy())
        InstructionStrategyFactory.register(ClosureCallStrategy())
        InstructionStrategyFactory.register(UpvalueGetStrategy())
        InstructionStrategyFactory.register(UpvalueSetStrategy())

        # 注册协程策略
        InstructionStrategyFactory.register(CoroutineCreateStrategy())
        InstructionStrategyFactory.register(CoroutineResumeStrategy())
        InstructionStrategyFactory.register(CoroutineYieldStrategy())
        InstructionStrategyFactory.register(CoroutineAwaitStrategy())
        InstructionStrategyFactory.register(CoroutineSpawnStrategy())
        InstructionStrategyFactory.register(ChannelCreateStrategy())
        InstructionStrategyFactory.register(ChannelSendStrategy())
        InstructionStrategyFactory.register(ChannelRecvStrategy())

    def _register_memory_strategies(self) -> None:
        """注册内存管理相关策略"""
        from .memory_strategies import (
            SmartPtrCreateStrategy,
            SmartPtrGetStrategy,
            SmartPtrResetStrategy,
            SmartPtrReleaseStrategy,
            SmartPtrUseCountStrategy,
            MoveStrategy,
            ScopePushStrategy,
            ScopePopStrategy,
            DestructorCallStrategy,
        )

        InstructionStrategyFactory.register(SmartPtrCreateStrategy())
        InstructionStrategyFactory.register(SmartPtrGetStrategy())
        InstructionStrategyFactory.register(SmartPtrResetStrategy())
        InstructionStrategyFactory.register(SmartPtrReleaseStrategy())
        InstructionStrategyFactory.register(SmartPtrUseCountStrategy())
        InstructionStrategyFactory.register(MoveStrategy())
        InstructionStrategyFactory.register(ScopePushStrategy())
        InstructionStrategyFactory.register(ScopePopStrategy())
        InstructionStrategyFactory.register(DestructorCallStrategy())
        InstructionStrategyFactory.register(CoroutineCreateStrategy())
        InstructionStrategyFactory.register(CoroutineResumeStrategy())
        InstructionStrategyFactory.register(CoroutineYieldStrategy())
        InstructionStrategyFactory.register(CoroutineAwaitStrategy())
        InstructionStrategyFactory.register(CoroutineSpawnStrategy())
        InstructionStrategyFactory.register(ChannelCreateStrategy())
        InstructionStrategyFactory.register(ChannelSendStrategy())
        InstructionStrategyFactory.register(ChannelRecvStrategy())

    def _create_debug_listener(self, source_file: str, output_file: str = "debug.json"):
        """
        创建 LLVM 后端专用调试监听器

        Args:
            source_file: 源文件路径
            output_file: 输出文件路径

        Returns:
            LLVMDebugListener: LLVM 后端调试监听器
        """
        from .llvm_debug_listener import LLVMDebugListener

        return LLVMDebugListener(
            source_file=source_file,
            module_name=self.module_name if hasattr(self, "module_name") else "main",
        )

    @property
    def name(self) -> str:
        return "llvm"

    @property
    def description(self) -> str:
        return "LLVM 后端 (llvmlite) - 重构版"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_jit=True,
            supports_debug=True,
            supports_optimization=True,
            supports_cross_compile=True,
            supports_lto=True,
            target_platforms=[
                "x86_64-linux",
                "x86_64-macos",
                "x86_64-windows",
                "aarch64-linux",
                "aarch64-macos",
                "arm-linux",
            ],
            output_formats=[
                OutputFormat.LLVM_IR,
                OutputFormat.LLVM_BC,
                OutputFormat.OBJECT,
                OutputFormat.EXECUTABLE,
            ],
            required_tools=["llvmlite"],
        )

    def compile(
        self,
        ir: IRProgram,
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        编译 IR 到目标文件

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        options = options or CompileOptions()

        try:
            # 1. 编译到 LLVM Module
            module = self.compile_to_module(ir, output_path.stem)

            # 2. 根据输出格式选择输出方式
            if options.output_format == OutputFormat.LLVM_IR:
                ll_file = output_path.with_suffix(".ll")
                ll_file.write_text(str(module))
                return CompileResult(
                    success=True,
                    output_files=[ll_file],
                )

            elif options.output_format == OutputFormat.LLVM_BC:
                bc_file = output_path.with_suffix(".bc")
                llvm_bitcode = llvm.parse_assembly(str(module))
                llvm_bitcode.to_bitcode_file(str(bc_file))
                return CompileResult(
                    success=True,
                    output_files=[bc_file],
                )

            else:
                # 默认输出 LLVM IR
                ll_file = output_path.with_suffix(".ll")
                ll_file.write_text(str(module))
                return CompileResult(
                    success=True,
                    output_files=[ll_file],
                )

        except Exception as e:
            logger.error(f"LLVM 编译失败: {e}")
            return CompileResult(
                success=False,
                errors=[str(e)],
            )

    def compile_to_module(
        self, ir: IRProgram, module_name: str = "zhc_module"
    ) -> ll.Module:
        """
        编译 ZhC IR 到 LLVM Module

        Args:
            ir: ZhC IR 程序
            module_name: 模块名称

        Returns:
            LLVM Module
        """
        # TASK-P3-003：分析优化提示
        if self.enable_optimization_hints:
            analyzer = OptimizationHintAnalyzer(ir)
            self.optimization_hints = analyzer.analyze()

        # 创建模块
        self.module = ll.Module(name=module_name)

        # 设置目标三元组（如果没有指定，使用本机默认）
        if self.target_triple:
            self.module.triple = self.target_triple
        else:
            # 使用 llvmlite 获取默认目标三元组
            self.module.triple = llvm.get_default_triple()

        # 设置数据布局
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # 使用 str() 获取 TargetData 的字符串表示（数据布局）
        self.module.data_layout = str(target_machine.target_data)

        # 设置编译上下文
        self.context.module = self.module
        self.context.functions.clear()
        self.context.blocks.clear()
        self.context.values.clear()
        self.context.string_constants.clear()

        # 编译全局变量
        for gv in ir.global_vars:
            self._compile_global_var(gv)

        # 编译函数
        for func in ir.functions:
            self._compile_function(func)

        return self.module

    def _compile_global_var(self, gv: IRGlobalVar) -> None:
        """编译全局变量"""
        ty = self._get_llvm_type(gv.ty or "i32")

        # 创建全局变量
        global_var = ll.GlobalVariable(self.module, ty, gv.name)
        global_var.linkage = "external"
        global_var.initializer = ll.Constant(ty, 0)

        self.context.values[gv.name] = global_var

    def _compile_function(self, func: IRFunction) -> None:
        """编译函数"""
        # 获取返回类型
        ret_ty = self._get_llvm_type(func.return_type or "i32")

        # 获取参数类型
        param_types = [self._get_llvm_type(p.ty or "i32") for p in func.params]

        # 创建函数类型
        func_ty = ll.FunctionType(ret_ty, param_types)

        # 创建函数
        llvm_func = ll.Function(self.module, func_ty, func.name)

        # 设置参数名（提前映射，映射到 llvm_arg 本身，供 GEP 等指令直接使用）
        for i, param in enumerate(func.params):
            llvm_arg = llvm_func.args[i]
            llvm_arg.name = param.name
            self.context.values[param.name] = llvm_arg

        # TASK-P3-003：应用优化提示
        self._apply_function_hints(llvm_func, func.name)

        self.context.functions[func.name] = llvm_func
        self.context.current_function = llvm_func

        # 检测是否有异常处理指令
        has_eh = self._has_exception_handling(func)

        # 如果有异常处理，设置 personality 函数并声明 EH intrinsics
        if has_eh:
            self._setup_exception_handling(llvm_func)

        # 先创建所有基本块（避免跳转引用未创建的基本块）
        for bb in func.basic_blocks:
            block = llvm_func.append_basic_block(bb.label)
            self.context.blocks[bb.label] = block

        # 函数参数的 alloca/store：参数已是 llvm_arg，后续 IR load 会报错；
        # 故在入口基本块的最前面插入 alloca/store，把参数存到栈上，
        # 并将参数名映射到 alloca 指针。这样 load %argName 就能正常工作。
        if func.params and func.basic_blocks:
            entry_bb_label = func.basic_blocks[0].label
            entry_block = self.context.blocks[entry_bb_label]
            builder = ll.IRBuilder(entry_block)
            builder.position_at_start(entry_block)  # alloca 在基本块最前面
            for param in func.params:
                param_ty = self._get_llvm_type(param.ty or "i32")
                addr_ptr = builder.alloca(param_ty, name=f"{param.name}.addr")
                builder.store(self.context.values[param.name], addr_ptr)
                # 覆盖映射：参数名现在指向栈槽指针，load %name → 从栈槽加载
                self.context.values[param.name] = addr_ptr

        # 然后编译每个基本块的指令
        for bb in func.basic_blocks:
            self._compile_basic_block(llvm_func, bb)

    def _has_exception_handling(self, func: IRFunction) -> bool:
        """
        检测函数是否包含异常处理指令

        Args:
            func: IR 函数

        Returns:
            bool: 是否包含异常处理指令
        """
        eh_opcodes = {
            Opcode.TRY,
            Opcode.CATCH,
            Opcode.THROW,
            Opcode.RESUME,
            Opcode.LANDINGPAD,
            Opcode.INVOKE,
        }

        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode in eh_opcodes:
                    return True
        return False

    def _setup_exception_handling(self, llvm_func: ll.Function) -> None:
        """
        设置异常处理支持：
        1. 设置 personality 函数
        2. 声明必要的 EH intrinsic 函数

        Args:
            llvm_func: LLVM 函数
        """
        # 设置 personality 函数
        personality_name = "__zhc_personality"
        personality_ty = ll.FunctionType(ll.IntType(32), [])
        personality_func = ll.Function(self.module, personality_ty, personality_name)
        llvm_func.attributes._personality = personality_func

        # 声明 EH intrinsic 函数
        self._declare_eh_intrinsics()

    def _declare_eh_intrinsics(self) -> None:
        """声明必要的 EH intrinsic 函数"""
        i8_ptr = ll.IntType(8).as_pointer()

        # llvm.eh.typeid.for
        if not self.module.get_global("llvm.eh.typeid.for.p0i8"):
            self.module.declare_intrinsic("llvm.eh.typeid.for", [i8_ptr])

        # llvm.eh.begincatch (可选，用于 C++ 异常处理)
        if not self.module.get_global("llvm.eh.begincatch"):
            self.module.declare_intrinsic("llvm.eh.begincatch", [i8_ptr])

        # llvm.eh.endcatch (可选，用于 C++ 异常处理)
        if not self.module.get_global("llvm.eh.endcatch"):
            self.module.declare_intrinsic("llvm.eh.endcatch", [])

    def _apply_function_hints(self, llvm_func: ll.Function, func_name: str):
        """
        应用函数优化提示

        TASK-P3-003 新增

        Args:
            llvm_func: LLVM 函数
            func_name: 函数名
        """
        if not self.enable_optimization_hints or not self.hint_adapter:
            return

        func_hints = self.optimization_hints.get_function_hints(func_name)
        if func_hints and self.hint_adapter:
            self.hint_adapter.apply_to_llvm_function(llvm_func, func_hints)

    def _compile_basic_block(self, llvm_func: ll.Function, bb: IRBasicBlock) -> None:
        """编译基本块"""
        # 获取已创建的基本块
        block = self.context.blocks[bb.label]
        self.context.current_block = block

        # 创建指令生成器
        builder = ll.IRBuilder(block)

        # 编译指令（使用策略模式）
        for instr in bb.instructions:
            self._compile_instruction(builder, instr)

    def _compile_instruction(self, builder: ll.IRBuilder, instr: IRInstruction) -> None:
        """
        编译指令 - 使用策略模式

        改进：使用策略工厂获取对应的编译策略，替代 if-elif 链
        """
        op = instr.opcode

        # 从工厂获取策略
        strategy = InstructionStrategyFactory.get_strategy(op)

        if strategy:
            # 使用策略编译指令
            strategy.compile(builder, instr, self.context)
        else:
            # 未实现的指令
            logger.warning(f"未实现的指令: {op.name}")

    def _get_llvm_type(self, zhc_type: str) -> ll.Type:
        """获取 LLVM 类型"""
        # 处理空型
        if zhc_type == "空型":
            return ll.VoidType()

        # 使用统一的类型映射器
        llvm_type = self.type_mapper.to_llvm(zhc_type)
        if llvm_type:
            return llvm_type

        # 默认返回 i32
        return ll.IntType(32)

    def is_available(self) -> bool:
        """检查 llvmlite 是否可用"""
        return LLVM_AVAILABLE

    def get_version(self) -> Optional[str]:
        """获取 llvmlite 版本"""
        if LLVM_AVAILABLE:
            return f"llvmlite {llvmlite.__version__}"
        return None

    def generate(self, ir: IRProgram) -> str:
        """
        生成 LLVM IR 代码（兼容 CLI 接口）

        Args:
            ir: ZhC IR 程序

        Returns:
            str: LLVM IR 文本
        """
        self.compile_to_module(ir, "zhc_module")
        return str(self.module)

    def to_llvm_ir(self) -> str:
        """转换为 LLVM IR 文本"""
        if self.module:
            return str(self.module)
        return ""

    def to_bitcode(self) -> bytes:
        """转换为 LLVM bitcode"""
        if not self.module:
            raise LLVMBackendError("模块未编译")

        # 解析 IR
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)

        # 使用 New PassManager 进行优化 (llvmlite 0.47+)
        target = llvm.Target.from_default_triple()
        tm = target.create_target_machine()
        
        pto = npm.create_pipeline_tuning_options()
        pto.speed_level = 2  # O2 优化
        
        pb = npm.PassBuilder(tm, pto)
        mpm = npm.create_new_module_pass_manager()
        
        # 添加标准优化 passes
        mpm.add_always_inliner_pass()
        mpm.add_instruction_combine_pass()
        mpm.add_reassociate_pass()
        mpm.add_sroa_pass()
        mpm.add_new_gvn_pass()
        mpm.add_simplify_cfg_pass()
        mpm.add_dead_code_elimination_pass()
        mpm.add_global_opt_pass()
        
        mpm.run(mod, pb)

        # 生成 bitcode
        return mod.as_bitcode()

    def save_bitcode(self, filepath: str) -> None:
        """保存 bitcode 到文件"""
        bitcode = self.to_bitcode()
        with open(filepath, "wb") as f:
            f.write(bitcode)

    def save_llvm_ir(self, filepath: str) -> None:
        """保存 LLVM IR 文本到文件"""
        llvm_ir = self.to_llvm_ir()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(llvm_ir)

    def compile_to_object(self, filepath: str) -> None:
        """编译为目标文件 (.o)"""
        if not self.module:
            raise LLVMBackendError("模块未编译")

        # 解析 IR
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)

        # 使用 New PassManager 进行优化 (llvmlite 0.47+)
        target = llvm.Target.from_default_triple()
        tm = target.create_target_machine()
        
        pto = npm.create_pipeline_tuning_options()
        pto.speed_level = 2  # O2 优化
        
        pb = npm.PassBuilder(tm, pto)
        mpm = npm.create_new_module_pass_manager()
        
        # 添加标准优化 passes
        mpm.add_always_inliner_pass()
        mpm.add_instruction_combine_pass()
        mpm.add_reassociate_pass()
        mpm.add_sroa_pass()
        mpm.add_new_gvn_pass()
        mpm.add_simplify_cfg_pass()
        mpm.add_dead_code_elimination_pass()
        mpm.add_global_opt_pass()
        
        mpm.run(mod, pb)

        # 生成目标代码
        obj = tm.emit_object(mod)

        with open(filepath, "wb") as f:
            f.write(obj)


def compile_to_llvm(
    ir: IRProgram, output_path: Optional[str] = None, output_format: str = "ir"
) -> Optional[str]:
    """
    便捷函数：编译 ZhC IR 到 LLVM

    Args:
        ir: ZhC IR 程序
        output_path: 输出路径（可选）
        output_format: 输出格式（"ir", "bitcode", "object"）

    Returns:
        输出路径或 LLVM IR 文本
    """
    backend = LLVMBackend()
    # 先编译到 module
    backend.compile_to_module(ir, "zhc_module")

    if output_path:
        if output_format == "ir":
            backend.save_llvm_ir(output_path)
        elif output_format == "bitcode":
            backend.save_bitcode(output_path)
        elif output_format == "object":
            backend.compile_to_object(output_path)
        return output_path
    else:
        return backend.to_llvm_ir()
