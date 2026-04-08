# -*- coding: utf-8 -*-
"""
ZhC 后端基类 - 统一多后端架构

提供抽象基类 BackendBase，定义所有后端的统一接口。
支持：C、GCC、Clang、LLVM、WASM 等后端。

架构：
    AST → IR → Backend → 可执行文件/字节码

作者：远
日期：2026-04-08
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pathlib import Path
from enum import Enum

if TYPE_CHECKING:
    from zhc.ir.program import IRProgram
    from zhc.debug.debug_manager import DebugManager
    from zhc.debug.debug_listener import DebugListener


class OutputFormat(Enum):
    """输出格式"""

    EXECUTABLE = "exe"  # 可执行文件
    OBJECT = "o"  # 目标文件
    STATIC_LIB = "a"  # 静态库
    SHARED_LIB = "so"  # 共享库
    LLVM_IR = "ll"  # LLVM IR 文本
    LLVM_BC = "bc"  # LLVM bitcode
    WASM = "wasm"  # WebAssembly
    ASSEMBLY = "s"  # 汇编文件
    C_CODE = "c"  # C 代码


@dataclass
class CompileOptions:
    """编译选项"""

    optimization_level: str = "O2"  # 优化级别 O0-O3, Os, Oz
    debug: bool = False  # 生成调试信息
    target: Optional[str] = None  # 目标平台
    output_format: OutputFormat = OutputFormat.EXECUTABLE
    emit_llvm: bool = False  # 输出 LLVM IR
    emit_assembly: bool = False  # 输出汇编
    link_static: bool = False  # 静态链接
    link_shared: bool = False  # 共享链接
    extra_flags: List[str] = field(default_factory=list)  # 额外编译参数


@dataclass
class CompileResult:
    """编译结果"""

    success: bool
    output_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0

    def __str__(self) -> str:
        if self.success:
            return f"编译成功: {', '.join(str(f) for f in self.output_files)}"
        else:
            return "编译失败:\n" + "\n".join(self.errors)


@dataclass
class BackendCapabilities:
    """后端能力"""

    supports_jit: bool = False  # JIT 执行
    supports_debug: bool = True  # 调试信息
    supports_optimization: bool = True  # 优化
    supports_cross_compile: bool = False  # 跨平台编译
    supports_lto: bool = False  # 链接时优化
    target_platforms: List[str] = field(default_factory=list)  # 支持的平台
    output_formats: List[OutputFormat] = field(default_factory=list)  # 输出格式
    required_tools: List[str] = field(default_factory=list)  # 需要的外部工具


class BackendBase(ABC):
    """
    后端基类

    所有编译器后端必须继承此类并实现抽象方法。

    使用方式：
        class MyBackend(BackendBase):
            @property
            def name(self) -> str:
                return "mybackend"

            def compile(self, ir, output_path, options=None):
                # 实现编译逻辑
                pass

        backend = MyBackend()
        result = backend.compile(ir_program, Path("output"))
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """后端名称（如 'gcc', 'llvm', 'wasm'）"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """后端描述"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> BackendCapabilities:
        """后端能力"""
        pass

    @abstractmethod
    def compile(
        self,
        ir: "IRProgram",
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        编译 IR 到目标代码

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        pass

    def compile_to_file(
        self,
        ir: "IRProgram",
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> Path:
        """
        编译并写入文件

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            Path: 输出文件路径

        Raises:
            BackendError: 编译失败
        """
        result = self.compile(ir, output_path, options)

        if not result.success:
            raise BackendError(f"{self.name} 编译失败:\n" + "\n".join(result.errors))

        if not result.output_files:
            raise BackendError(f"{self.name} 未生成任何输出文件")

        return result.output_files[0]

    def link(
        self,
        object_files: List[Path],
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        链接目标文件

        默认实现调用 compile()，子类可覆盖。

        Args:
            object_files: 目标文件列表
            output_path: 输出路径
            options: 链接选项

        Returns:
            CompileResult: 链接结果
        """
        raise NotImplementedError(f"{self.name} 后端不支持链接")

    def is_available(self) -> bool:
        """
        检查后端是否可用

        子类可覆盖以检查外部工具是否安装。

        Returns:
            bool: 是否可用
        """
        return True

    def get_version(self) -> Optional[str]:
        """
        获取后端版本

        Returns:
            str: 版本信息，不可用返回 None
        """
        return None

    def get_supported_targets(self) -> List[str]:
        """
        获取支持的目标平台

        Returns:
            List[str]: 支持的目标列表
        """
        return self.capabilities.target_platforms

    # ========== 调试信息接口 ==========

    def _create_debug_listener(
        self, source_file: str, output_file: str = "debug.json"
    ) -> "DebugListener":
        """
        创建后端专用调试监听器

        子类应覆盖此方法以提供特定后端的调试监听器。
        默认返回 None，表示不支持调试信息。

        Args:
            source_file: 源文件路径
            output_file: 输出文件路径

        Returns:
            DebugListener: 调试监听器实例，或 None
        """
        return None

    def _setup_debug(
        self, ir: "IRProgram", options: CompileOptions
    ) -> Optional["DebugManager"]:
        """
        设置调试信息生成

        根据 CompileOptions.debug 决定是否启用调试信息。
        如果启用，创建 DebugManager 并添加后端专用监听器。

        Args:
            ir: IR 程序
            options: 编译选项

        Returns:
            DebugManager: 调试管理器实例，或 None（未启用）
        """
        if not options.debug:
            return None

        # 检查后端是否支持调试
        if not self.capabilities.supports_debug:
            return None

        # 导入 DebugManager（延迟导入避免循环依赖）
        from zhc.debug.debug_manager import DebugManager

        # 获取源文件路径
        source_file = getattr(ir, "source_file", "unknown.zhc")

        # 创建调试管理器
        manager = DebugManager(source_file=source_file, enable_debug=True)

        # 创建并添加后端专用监听器
        listener = self._create_debug_listener(source_file)
        if listener:
            manager.add_listener(listener)

        return manager

    def _emit_compile_unit_debug(
        self,
        debug_manager: Optional["DebugManager"],
        name: str,
        source_file: str,
        comp_dir: str = "",
    ) -> None:
        """
        发射编译单元调试事件

        Args:
            debug_manager: 调试管理器（可能为 None）
            name: 编译单元名称
            source_file: 源文件路径
            comp_dir: 编译目录
        """
        if debug_manager:
            debug_manager.emit_compile_unit(name, source_file, comp_dir)

    def _emit_function_debug(
        self,
        debug_manager: Optional["DebugManager"],
        name: str,
        start_line: int,
        end_line: int,
        start_addr: int = 0,
        end_addr: int = 0,
        return_type: str = "void",
        parameters: Optional[List[Dict]] = None,
    ) -> None:
        """
        发射函数定义调试事件

        Args:
            debug_manager: 调试管理器（可能为 None）
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表
        """
        if debug_manager:
            debug_manager.emit_function(
                name=name,
                start_line=start_line,
                end_line=end_line,
                start_addr=start_addr,
                end_addr=end_addr,
                return_type=return_type,
                parameters=parameters,
            )

    def _emit_variable_debug(
        self,
        debug_manager: Optional["DebugManager"],
        name: str,
        type_name: str,
        line_number: int,
        address: int = 0,
        is_parameter: bool = False,
    ) -> None:
        """
        发射变量定义调试事件

        Args:
            debug_manager: 调试管理器（可能为 None）
            name: 变量名
            type_name: 类型名
            line_number: 定义行号
            address: 内存地址
            is_parameter: 是否为函数参数
        """
        if debug_manager:
            debug_manager.emit_variable(
                name=name,
                type_name=type_name,
                line_number=line_number,
                address=address,
                is_parameter=is_parameter,
            )

    def _emit_line_mapping_debug(
        self,
        debug_manager: Optional["DebugManager"],
        line_number: int,
        address: int,
        column: int = 0,
        file_index: int = 0,
    ) -> None:
        """
        发射行号映射调试事件

        Args:
            debug_manager: 调试管理器（可能为 None）
            line_number: 源码行号
            address: 机器码地址
            column: 列号
            file_index: 文件索引
        """
        if debug_manager:
            debug_manager.emit_line_mapping(
                line_number=line_number,
                address=address,
                column=column,
                file_index=file_index,
            )

    def _finalize_debug(
        self, debug_manager: Optional["DebugManager"]
    ) -> Dict[str, Any]:
        """
        完成调试信息生成

        Args:
            debug_manager: 调试管理器（可能为 None）

        Returns:
            Dict[str, Any]: 调试信息输出
        """
        if debug_manager:
            return debug_manager.emit_finalize()
        return {}

    def validate_options(self, options: CompileOptions) -> List[str]:
        """
        验证编译选项

        Args:
            options: 编译选项

        Returns:
            List[str]: 验证错误列表，空表示验证通过
        """
        errors = []

        # 验证优化级别
        valid_opt_levels = ["O0", "O1", "O2", "O3", "Os", "Oz"]
        if options.optimization_level not in valid_opt_levels:
            errors.append(
                f"无效的优化级别: {options.optimization_level}，"
                f"有效值: {', '.join(valid_opt_levels)}"
            )

        # 验证目标平台
        if options.target:
            supported = self.get_supported_targets()
            if supported and options.target not in supported:
                errors.append(
                    f"不支持的目标平台: {options.target}，支持: {', '.join(supported)}"
                )

        return errors

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class BackendError(Exception):
    """后端错误"""

    pass


class CompilationError(BackendError):
    """编译错误"""

    pass


class LinkingError(BackendError):
    """链接错误"""

    pass


class ToolNotFoundError(BackendError):
    """工具未找到错误"""

    def __init__(self, tool_name: str, suggestion: str = ""):
        self.tool_name = tool_name
        self.suggestion = suggestion
        msg = f"未找到工具: {tool_name}"
        if suggestion:
            msg += f"\n{suggestion}"
        super().__init__(msg)


class UnsupportedTargetError(BackendError):
    """不支持的目标平台错误"""

    pass
