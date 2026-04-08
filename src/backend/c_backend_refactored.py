# -*- coding: utf-8 -*-
"""
ZhC C 后端 - 重构版本

将 IR 程序转换为 C 代码，然后调用 GCC/Clang 编译为目标文件。

架构：
IRProgram → CBackend → C代码 → GCC/Clang → 目标文件

改进：
1. 使用统一的编译器运行器
2. 使用统一的类型映射器
3. 更清晰的代码结构

作者：远
日期：2026-04-09
"""

from pathlib import Path
from typing import Optional, Any, List, TYPE_CHECKING

from .base import (
    BackendBase,
    BackendCapabilities,
    CompileOptions,
    CompileResult,
    OutputFormat,
)
from .type_system import get_type_mapper
from .compiler_runner import create_c_compiler_runner

if TYPE_CHECKING:
    from zhc.ir.program import IRProgram


class CBackend(BackendBase):
    """
    C 后端 - IR → C 代码 → 目标文件

    工作流程：
    1. IRProgram → C 代码（使用类型映射器）
    2. C 代码 → 目标文件（使用编译器运行器）
    """

    def __init__(self, compiler: str = "gcc", optimization_level: str = "O2"):
        """
        初始化 C 后端

        Args:
            compiler: C 编译器路径（gcc, clang, arm-gcc 等）
            optimization_level: 优化级别
        """
        self.compiler = compiler
        self.optimization_level = optimization_level
        self.type_mapper = get_type_mapper()

        # 创建编译器运行器
        self.runner = create_c_compiler_runner(
            compiler=compiler,
            optimization_level=optimization_level,
        )

        self._check_compiler_available()

    @property
    def name(self) -> str:
        return "c"

    @property
    def description(self) -> str:
        return f"C 后端 ({self.compiler})"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_jit=False,
            supports_debug=True,
            supports_optimization=True,
            supports_cross_compile=True,
            target_platforms=[
                "x86_64-linux",
                "x86_64-macos",
                "x86_64-windows",
                "arm-linux",
                "aarch64-linux",
                "aarch64-macos",
            ],
            output_formats=[
                OutputFormat.C_CODE,
                OutputFormat.OBJECT,
                OutputFormat.EXECUTABLE,
                OutputFormat.STATIC_LIB,
                OutputFormat.SHARED_LIB,
            ],
            required_tools=[self.compiler],
        )

    def compile(
        self,
        ir: "IRProgram",
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

        # 设置调试信息生成
        debug_manager = self._setup_debug(ir, options)

        # 1. IR → C 代码
        c_code = self._generate_c_code(ir, debug_manager)

        # 2. 写入临时 C 文件
        c_file = output_path.with_suffix(".c")
        c_file.write_text(c_code)

        # 3. 根据输出格式选择编译方式
        if options.output_format == OutputFormat.C_CODE:
            return CompileResult(
                success=True,
                output_files=[c_file],
                errors=[],
                warnings=[],
            )

        # 4. 调用编译器
        return self._compile_c_file(c_file, output_path, options)

    def _generate_c_code(
        self, ir: "IRProgram", debug_manager: Optional[Any] = None
    ) -> str:
        """
        从 IR 生成 C 代码

        Args:
            ir: IR 程序
            debug_manager: 调试管理器（可选）

        Returns:
            str: C 代码
        """
        # 获取源文件路径
        source_file = getattr(ir, "source_file", "unknown.zhc")

        # 发射编译单元调试事件
        self._emit_compile_unit_debug(
            debug_manager,
            name=ir.name if hasattr(ir, "name") else "main",
            source_file=source_file,
            comp_dir="",
        )

        lines = [
            "// 由 ZhC C 后端生成",
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "",
        ]

        # 生成函数声明
        for func in ir.functions:
            lines.append(self._generate_function_declaration(func))

        lines.append("")

        # 生成函数实现
        for func in ir.functions:
            func_lines = self._generate_function(func, debug_manager)
            lines.append(func_lines)
            lines.append("")

        # 生成主函数（如果有）
        if ir.has_main:
            lines.append(self._generate_main_function(ir))

        # 完成调试信息
        self._finalize_debug(debug_manager)

        return "\n".join(lines)

    def _generate_function_declaration(self, func) -> str:
        """生成函数声明"""
        params = ", ".join(
            f"{self.type_mapper.to_c(p.type)} {p.name}" for p in func.params
        )
        if not params:
            params = "void"
        return f"{self.type_mapper.to_c(func.return_type)} {func.name}({params});"

    def _generate_function(
        self,
        func,
        debug_manager: Optional[Any] = None,
    ) -> str:
        """生成函数实现"""
        # 获取函数行号
        start_line = 1
        end_line = 1

        # 发射函数调试事件
        params_info = [
            {"name": p.name, "type": p.type, "line": start_line} for p in func.params
        ]
        self._emit_function_debug(
            debug_manager,
            name=func.name,
            start_line=start_line,
            end_line=end_line,
            return_type=func.return_type,
            parameters=params_info,
        )

        lines = []

        # 函数头
        params_str = ", ".join(
            f"{self.type_mapper.to_c(p.type)} {p.name}" for p in func.params
        )
        if not params_str:
            params_str = "void"
        lines.append(
            f"{self.type_mapper.to_c(func.return_type)} {func.name}({params_str}) {{"
        )

        # 函数体 - 生成基本块
        for block in func.blocks:
            for inst in block.instructions:
                inst_code = self._generate_instruction(inst, debug_manager)
                if inst_code:
                    lines.append(f"    {inst_code}")

        # 函数尾
        lines.append("}")
        return "\n".join(lines)

    def _generate_instruction(
        self,
        inst,
        debug_manager: Optional[Any] = None,
    ) -> Optional[str]:
        """
        生成指令的 C 代码

        使用字典映射替代 if-elif 链
        """
        opcode = inst.opcode.name
        line_number = getattr(inst, "line_number", 0)

        # 发射行号映射调试事件
        if line_number > 0 and debug_manager:
            self._emit_line_mapping_debug(
                debug_manager, line_number=line_number, address=0
            )

        # 使用字典映射获取生成器函数
        generators = self._get_instruction_generators()
        generator = generators.get(opcode)

        if generator:
            return generator(self, inst)

        return None

    def _get_instruction_generators(self) -> dict:
        """
        获取指令生成器字典

        使用方法引用而非 lambda，便于扩展
        """
        return {
            "ADD": lambda s,
            i: f"{i.result[0].name if i.result else '_'} = {i.operands[0]} + {i.operands[1]};",
            "SUB": lambda s,
            i: f"{i.result[0].name if i.result else '_'} = {i.operands[0]} - {i.operands[1]};",
            "MUL": lambda s,
            i: f"{i.result[0].name if i.result else '_'} = {i.operands[0]} * {i.operands[1]};",
            "DIV": lambda s,
            i: f"{i.result[0].name if i.result else '_'} = {i.operands[0]} / {i.operands[1]};",
            "RET": lambda s, i: f"return {i.operands[0]};" if i.operands else "return;",
            "ALLOC": lambda s,
            i: f"{i.result[0].name if i.result else '_'} = malloc(sizeof({s.type_mapper.to_c(getattr(i, 'type', 'int'))}));",
            "STORE": lambda s, i: f"{i.operands[1]} = {i.operands[0]};",
            "LOAD": lambda s,
            i: f"{i.result[0].name if i.result else '_'} = *{i.operands[0]};",
        }

    def _generate_main_function(self, ir: "IRProgram") -> str:
        """生成主函数"""
        return """
int main(int argc, char** argv) {
    // ZhC 程序入口
    return 0;
}
"""

    def _compile_c_file(
        self,
        c_file: Path,
        output_path: Path,
        options: CompileOptions,
    ) -> CompileResult:
        """
        调用编译器编译 C 文件

        使用统一的编译器运行器
        """
        cmd = self._build_compiler_command(c_file, output_path, options)

        # 使用编译器运行器
        output = self.runner.run(cmd)

        # 解析输出
        errors, warnings = self.runner.parse_output(output)
        output_files = [output_path] if output.returncode == 0 else []

        metadata = {
            "compiler": self.compiler,
            "duration_seconds": output.duration_seconds,
        }

        return self.runner.to_compile_result(output, output_files, metadata)

    def _build_compiler_command(
        self,
        c_file: Path,
        output_path: Path,
        options: CompileOptions,
    ) -> List[str]:
        """构建编译器命令"""
        cmd = [self.compiler]

        # 优化级别
        cmd.append(f"-{options.optimization_level}")

        # 调试信息
        if options.debug:
            cmd.append("-g")

        # 目标平台
        if options.target:
            cmd.extend(["--target", options.target])

        # 输出格式
        if options.output_format == OutputFormat.OBJECT:
            cmd.extend(["-c", "-o", str(output_path)])
        elif options.output_format == OutputFormat.EXECUTABLE:
            cmd.extend(["-o", str(output_path)])
        elif options.output_format == OutputFormat.SHARED_LIB:
            cmd.extend(["-shared", "-fPIC", "-o", str(output_path)])
        else:
            cmd.extend(["-o", str(output_path)])

        # 输入文件
        cmd.append(str(c_file))

        # 额外标志
        cmd.extend(options.extra_flags)

        return cmd

    def _check_compiler_available(self) -> None:
        """检查编译器是否可用"""
        if not self.runner.check_available():
            from .base import ToolNotFoundError

            raise ToolNotFoundError(
                self.compiler,
                f"请安装 {self.compiler} 或指定正确的编译器路径",
            )

    def is_available(self) -> bool:
        """检查后端是否可用"""
        return self.runner.check_available()

    def get_version(self) -> Optional[str]:
        """获取编译器版本"""
        return self.runner.get_version()
