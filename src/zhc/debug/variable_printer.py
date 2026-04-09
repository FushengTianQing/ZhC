"""
变量打印器

提供变量查看功能：
- 局部变量读取
- 全局变量读取
- 寄存器读取
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Tuple

from .debug_info_collector import DebugInfoCollector, VariableDebugInfo, TypeDebugInfo


class LocationType(Enum):
    """位置类型"""

    REGISTER = "register"
    STACK = "stack"
    MEMORY = "memory"
    CONSTANT = "constant"
    OPTIMIZED_OUT = "optimized_out"


@dataclass
class VariableLocation:
    """变量位置"""

    type: LocationType
    register_name: Optional[str] = None
    stack_offset: Optional[int] = None
    memory_address: Optional[int] = None
    size: Optional[int] = None


@dataclass
class VariableDisplay:
    """变量显示信息"""

    name: str
    type_name: str
    value: str
    location: VariableLocation
    is_valid: bool = True
    error_message: Optional[str] = None


class VariablePrinter:
    """变量打印器"""

    def __init__(self, debug_info: Optional[DebugInfoCollector] = None):
        self._debug_info = debug_info
        self._current_frame_pc: int = 0
        self._frame_base: int = 0

    def set_current_frame(self, pc: int, frame_base: int) -> None:
        """设置当前栈帧

        Args:
            pc: 程序计数器
            frame_base: 帧基址
        """
        self._current_frame_pc = pc
        self._frame_base = frame_base

    def print_local_variables(self, frame_context: Any) -> List[VariableDisplay]:
        """打印局部变量

        Args:
            frame_context: 帧上下文

        Returns:
            局部变量列表
        """
        if not self._debug_info:
            return []

        result = []

        # 获取当前函数的调试信息
        func_info = self._debug_info.get_function_at_address(self._current_frame_pc)
        if not func_info:
            return []

        # 遍历变量
        for var_info in func_info.variables:
            # 检查变量是否在作用域
            if not self._is_in_scope(var_info):
                continue

            display = self._read_and_format_variable(var_info, frame_context)
            result.append(display)

        return result

    def print_arguments(self, frame_context: Any) -> List[VariableDisplay]:
        """打印函数参数

        Args:
            frame_context: 帧上下文

        Returns:
            参数列表
        """
        if not self._debug_info:
            return []

        result = []

        func_info = self._debug_info.get_function_at_address(self._current_frame_pc)
        if not func_info:
            return []

        for arg in func_info.arguments:
            display = self._read_and_format_variable(arg, frame_context)
            result.append(display)

        return result

    def print_global_variables(self, frame_context: Any) -> List[VariableDisplay]:
        """打印全局变量"""
        if not self._debug_info:
            return []

        result = []

        for var_info in self._debug_info.global_variables:
            display = self._read_and_format_variable(var_info, frame_context)
            result.append(display)

        return result

    def read_register(self, register_name: str, frame_context: Any) -> Optional[int]:
        """读取寄存器

        Args:
            register_name: 寄存器名
            frame_context: 帧上下文

        Returns:
            寄存器值
        """
        # 需要实际调试器后端支持
        return None

    def read_memory(self, address: int, size: int) -> Optional[bytes]:
        """读取内存

        Args:
            address: 内存地址
            size: 读取大小

        Returns:
            内存数据
        """
        # 需要实际调试器后端支持
        return None

    def read_variable(
        self, var_info: VariableDebugInfo, frame_context: Any
    ) -> Tuple[Any, bool]:
        """读取变量值

        Args:
            var_info: 变量调试信息
            frame_context: 帧上下文

        Returns:
            (变量值, 是否成功)
        """
        location = var_info.location

        if location.type == LocationType.REGISTER:
            value = self.read_register(location.register_name or "", frame_context)
            return value, value is not None

        elif location.type == LocationType.STACK:
            if location.stack_offset is not None:
                address = self._frame_base + location.stack_offset
                data = self.read_memory(address, var_info.type_info.size)
                if data:
                    return self._parse_value(data, var_info.type_info), True
            return None, False

        elif location.type == LocationType.MEMORY:
            if location.memory_address is not None:
                data = self.read_memory(
                    location.memory_address, var_info.type_info.size
                )
                if data:
                    return self._parse_value(data, var_info.type_info), True
            return None, False

        elif location.type == LocationType.CONSTANT:
            return var_info.location.memory_address, True

        elif location.type == LocationType.OPTIMIZED_OUT:
            return "<optimized out>", True

        return None, False

    def _read_and_format_variable(
        self, var_info: VariableDebugInfo, frame_context: Any
    ) -> VariableDisplay:
        """读取并格式化变量"""
        value, success = self.read_variable(var_info, frame_context)

        if not success:
            return VariableDisplay(
                name=var_info.name,
                type_name=var_info.type_info.name,
                value="<unavailable>",
                location=var_info.location,
                is_valid=False,
                error_message="Cannot read variable",
            )

        return VariableDisplay(
            name=var_info.name,
            type_name=var_info.type_info.name,
            value=str(value),
            location=var_info.location,
            is_valid=True,
        )

    def _is_in_scope(self, var_info: VariableDebugInfo) -> bool:
        """检查变量是否在作用域内"""
        if not var_info.ranges:
            return True

        for range_info in var_info.ranges:
            if range_info.start <= self._current_frame_pc <= range_info.end:
                return True

        return False

    def _parse_value(self, data: bytes, type_info: TypeDebugInfo) -> Any:
        """解析内存数据为值"""
        import struct

        type_name = type_info.name.lower()

        if "int" in type_name:
            if "8" in type_name:
                return struct.unpack("b", data[:1])[0]
            elif "16" in type_name:
                return struct.unpack("h", data[:2])[0]
            elif "32" in type_name:
                return struct.unpack("i", data[:4])[0]
            elif "64" in type_name:
                return struct.unpack("q", data[:8])[0]
            else:
                return struct.unpack("i", data[:4])[0]

        elif "uint" in type_name:
            if "8" in type_name:
                return struct.unpack("B", data[:1])[0]
            elif "16" in type_name:
                return struct.unpack("H", data[:2])[0]
            elif "32" in type_name:
                return struct.unpack("I", data[:4])[0]
            elif "64" in type_name:
                return struct.unpack("Q", data[:8])[0]
            else:
                return struct.unpack("I", data[:4])[0]

        elif "float" in type_name:
            if "32" in type_name or "double" not in type_name:
                return struct.unpack("f", data[:4])[0]
            else:
                return struct.unpack("d", data[:8])[0]

        elif "char" in type_name:
            if type_info.is_array:
                return data.rstrip(b"\x00").decode("utf-8", errors="replace")
            else:
                return chr(data[0])

        elif "bool" in type_name:
            return data[0] != 0

        else:
            # 尝试作为指针
            return struct.unpack("Q", data[:8])[0]

    def format_variable(self, var: VariableDisplay) -> str:
        """格式化变量显示"""
        if not var.is_valid:
            return f"{var.name} = <{var.error_message or 'invalid'}>"

        return f"{var.name}: {var.type_name} = {var.value}"

    def format_variable_list(self, variables: List[VariableDisplay]) -> str:
        """格式化变量列表"""
        if not variables:
            return "(no variables)"

        lines = []
        for var in variables:
            lines.append(self.format_variable(var))

        return "\n".join(lines)
