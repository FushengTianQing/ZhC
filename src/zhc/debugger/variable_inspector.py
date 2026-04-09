"""
变量检查器

提供变量查看和检查功能：
- 局部变量查看
- 全局变量查看
- 寄存器查看
- 变量位置追踪
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class VariableLocationType(Enum):
    """变量位置类型"""

    REGISTER = "register"  # 寄存器
    STACK = "stack"  # 栈
    MEMORY = "memory"  # 内存
    CONSTANT = "constant"  # 常量
    OPTIMIZED_OUT = "optimized_out"  # 被优化掉
    UNAVAILABLE = "unavailable"  # 不可用


@dataclass
class VariableLocation:
    """变量位置"""

    type: VariableLocationType
    register_name: Optional[str] = None
    stack_offset: Optional[int] = None
    memory_address: Optional[int] = None
    constant_value: Optional[Any] = None
    size: Optional[int] = None

    def __str__(self) -> str:
        if self.type == VariableLocationType.REGISTER:
            return f"register({self.register_name})"
        elif self.type == VariableLocationType.STACK:
            return f"stack(offset={self.stack_offset})"
        elif self.type == VariableLocationType.MEMORY:
            return f"memory(0x{self.memory_address:x})"
        elif self.type == VariableLocationType.CONSTANT:
            return f"constant({self.constant_value})"
        elif self.type == VariableLocationType.OPTIMIZED_OUT:
            return "optimized_out"
        else:
            return "unavailable"


@dataclass
class TypeInfo:
    """类型信息"""

    name: str
    size: int
    alignment: int
    is_pointer: bool = False
    is_array: bool = False
    is_struct: bool = False
    is_enum: bool = False
    is_function: bool = False
    element_type: Optional["TypeInfo"] = None
    fields: Optional[Dict[str, "TypeInfo"]] = None
    enum_values: Optional[Dict[str, int]] = None

    def __str__(self) -> str:
        if self.is_pointer and self.element_type:
            return f"{self.element_type.name}*"
        elif self.is_array and self.element_type:
            return f"{self.element_type.name}[]"
        else:
            return self.name


@dataclass
class VariableValue:
    """变量值"""

    name: str
    type_info: TypeInfo
    location: VariableLocation
    value: Any = None
    raw_value: Optional[bytes] = None
    is_valid: bool = True
    error_message: Optional[str] = None
    children: Optional[Dict[str, "VariableValue"]] = None

    def __str__(self) -> str:
        if not self.is_valid:
            return f"{self.name} = <{self.error_message or 'invalid'}>"
        return f"{self.name}: {self.type_info} = {self.value}"

    def get_display_value(self) -> str:
        """获取显示值"""
        if not self.is_valid:
            return f"<{self.error_message or 'invalid'}>"

        if self.value is None:
            return "<unavailable>"

        if self.type_info.is_pointer:
            return f"0x{self.value:x}"
        elif self.type_info.is_enum and self.type_info.enum_values:
            # 查找枚举名称
            for name, val in self.type_info.enum_values.items():
                if val == self.value:
                    return name
            return str(self.value)
        else:
            return str(self.value)


@dataclass
class Scope:
    """作用域"""

    name: str
    start_address: int
    end_address: int
    variables: Dict[str, VariableValue] = field(default_factory=dict)
    parent: Optional["Scope"] = None
    children: List["Scope"] = field(default_factory=list)

    def is_in_scope(self, pc: int) -> bool:
        """检查地址是否在作用域内"""
        return self.start_address <= pc <= self.end_address

    def get_visible_variables(self, pc: int) -> Dict[str, VariableValue]:
        """获取可见变量"""
        result = {}

        # 添加当前作用域的变量
        for name, var in self.variables.items():
            if self.is_in_scope(pc):
                result[name] = var

        # 添加父作用域的变量
        if self.parent:
            result.update(self.parent.get_visible_variables(pc))

        return result


@dataclass
class FrameInfo:
    """栈帧信息"""

    frame_id: int
    pc: int
    function_name: str
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    scope: Optional[Scope] = None
    arguments: Dict[str, VariableValue] = field(default_factory=dict)
    locals: Dict[str, VariableValue] = field(default_factory=dict)
    return_address: Optional[int] = None
    frame_pointer: Optional[int] = None
    stack_pointer: Optional[int] = None


class VariableInspector:
    """变量检查器"""

    def __init__(self):
        self._global_variables: Dict[str, VariableValue] = {}
        self._register_cache: Dict[str, Any] = {}
        self._type_registry: Dict[str, TypeInfo] = {}
        self._current_frame: Optional[FrameInfo] = None

    def register_type(self, type_info: TypeInfo) -> None:
        """注册类型信息"""
        self._type_registry[type_info.name] = type_info

    def get_type(self, name: str) -> Optional[TypeInfo]:
        """获取类型信息"""
        return self._type_registry.get(name)

    def set_global_variable(
        self,
        name: str,
        type_info: TypeInfo,
        location: VariableLocation,
        value: Any = None,
    ) -> VariableValue:
        """设置全局变量"""
        var = VariableValue(
            name=name, type_info=type_info, location=location, value=value
        )
        self._global_variables[name] = var
        return var

    def get_global_variable(self, name: str) -> Optional[VariableValue]:
        """获取全局变量"""
        return self._global_variables.get(name)

    def get_all_global_variables(self) -> Dict[str, VariableValue]:
        """获取所有全局变量"""
        return self._global_variables.copy()

    def set_current_frame(self, frame: FrameInfo) -> None:
        """设置当前栈帧"""
        self._current_frame = frame

    def get_local_variable(self, name: str) -> Optional[VariableValue]:
        """获取局部变量"""
        if not self._current_frame:
            return None

        # 先检查参数
        if name in self._current_frame.arguments:
            return self._current_frame.arguments[name]

        # 再检查局部变量
        if name in self._current_frame.locals:
            return self._current_frame.locals[name]

        # 检查作用域
        if self._current_frame.scope:
            visible = self._current_frame.scope.get_visible_variables(
                self._current_frame.pc
            )
            if name in visible:
                return visible[name]

        return None

    def get_all_locals(self) -> Dict[str, VariableValue]:
        """获取所有局部变量"""
        if not self._current_frame:
            return {}

        result = {}
        result.update(self._current_frame.arguments)
        result.update(self._current_frame.locals)

        if self._current_frame.scope:
            result.update(
                self._current_frame.scope.get_visible_variables(self._current_frame.pc)
            )

        return result

    def get_arguments(self) -> Dict[str, VariableValue]:
        """获取函数参数"""
        if not self._current_frame:
            return {}
        return self._current_frame.arguments.copy()

    def get_register_value(self, register_name: str) -> Optional[Any]:
        """获取寄存器值"""
        return self._register_cache.get(register_name)

    def set_register_value(self, register_name: str, value: Any) -> None:
        """设置寄存器值"""
        self._register_cache[register_name] = value

    def get_all_registers(self) -> Dict[str, Any]:
        """获取所有寄存器值"""
        return self._register_cache.copy()

    def clear_register_cache(self) -> None:
        """清空寄存器缓存"""
        self._register_cache.clear()

    def read_memory(self, address: int, size: int) -> Optional[bytes]:
        """读取内存（需要实际调试器支持）"""
        # 这个方法需要在实际的调试器后端中实现
        raise NotImplementedError("Memory reading requires debugger backend")

    def write_memory(self, address: int, data: bytes) -> bool:
        """写入内存（需要实际调试器支持）"""
        # 这个方法需要在实际的调试器后端中实现
        raise NotImplementedError("Memory writing requires debugger backend")

    def read_variable_value(self, var: VariableValue) -> Any:
        """读取变量值"""
        if not var.is_valid:
            return None

        loc = var.location

        if loc.type == VariableLocationType.REGISTER:
            return self.get_register_value(loc.register_name or "")

        elif loc.type == VariableLocationType.STACK:
            # 需要从栈中读取
            if self._current_frame and loc.stack_offset is not None:
                _ = (self._current_frame.stack_pointer or 0) + loc.stack_offset
                # 实际读取需要调试器后端支持
                return None

        elif loc.type == VariableLocationType.MEMORY:
            if loc.memory_address is not None and loc.size is not None:
                # 实际读取需要调试器后端支持
                return None

        elif loc.type == VariableLocationType.CONSTANT:
            return loc.constant_value

        elif loc.type == VariableLocationType.OPTIMIZED_OUT:
            return "<optimized out>"

        return None

    def format_variable(
        self, var: VariableValue, max_depth: int = 5, current_depth: int = 0
    ) -> str:
        """格式化变量显示"""
        if current_depth > max_depth:
            return "..."

        if not var.is_valid:
            return f"{var.name} = <{var.error_message or 'invalid'}>"

        value = var.get_display_value()

        # 处理复合类型
        if var.type_info.is_struct and var.children:
            fields = []
            for name, child in var.children.items():
                child_str = self.format_variable(child, max_depth, current_depth + 1)
                fields.append(f"  {name} = {child_str}")

            return f"{var.name}: {var.type_info.name} {{\n" + "\n".join(fields) + "\n}"

        elif var.type_info.is_array and var.children:
            elements = []
            for name, child in var.children.items():
                child_str = self.format_variable(child, max_depth, current_depth + 1)
                elements.append(f"  {name} = {child_str}")

            return f"{var.name}: {var.type_info.name} [\n" + "\n".join(elements) + "\n]"

        else:
            return f"{var.name}: {var.type_info} = {value}"

    def find_variable_by_address(self, address: int) -> Optional[VariableValue]:
        """根据地址查找变量"""
        # 检查全局变量
        for var in self._global_variables.values():
            if var.location.type == VariableLocationType.MEMORY:
                if var.location.memory_address == address:
                    return var

        # 检查局部变量
        if self._current_frame:
            for var in self._current_frame.locals.values():
                if var.location.type == VariableLocationType.MEMORY:
                    if var.location.memory_address == address:
                        return var

        return None

    def get_variable_size(self, var: VariableValue) -> int:
        """获取变量大小"""
        return var.type_info.size

    def is_variable_in_scope(self, var: VariableValue, pc: int) -> bool:
        """检查变量是否在作用域内"""
        if not self._current_frame or not self._current_frame.scope:
            return True

        return self._current_frame.scope.is_in_scope(pc)

    def create_scope(
        self,
        name: str,
        start_address: int,
        end_address: int,
        parent: Optional[Scope] = None,
    ) -> Scope:
        """创建作用域"""
        scope = Scope(
            name=name,
            start_address=start_address,
            end_address=end_address,
            parent=parent,
        )

        if parent:
            parent.children.append(scope)

        return scope

    def add_variable_to_scope(self, scope: Scope, var: VariableValue) -> None:
        """添加变量到作用域"""
        scope.variables[var.name] = var

    def __repr__(self) -> str:
        return (
            f"VariableInspector("
            f"globals={len(self._global_variables)}, "
            f"types={len(self._type_registry)})"
        )
