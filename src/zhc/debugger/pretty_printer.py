"""
变量美化打印器

提供 ZhC 类型的美化打印功能：
- 字符串打印
- 数组打印
- 映射打印
- 结构体打印
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator, List, Optional, Tuple


class DisplayHint(Enum):
    """显示提示枚举"""

    STRING = "string"
    ARRAY = "array"
    MAP = "map"
    STRUCT = "struct"
    UNION = "union"
    ENUM = "enum"
    POINTER = "pointer"


@dataclass
class PrinterOption:
    """打印选项"""

    max_elements: int = 100
    max_string_length: int = 1024
    max_depth: int = 10
    show_type: bool = True
    show_address: bool = False
    indent_size: int = 2
    use_unicode: bool = True


class PrettyPrinterBase(ABC):
    """美化打印器基类"""

    def __init__(self, value: Any, options: Optional[PrinterOption] = None):
        self.value = value
        self.options = options or PrinterOption()
        self._children_cache: Optional[List[Tuple[str, Any]]] = None

    @abstractmethod
    def to_string(self) -> str:
        """转换为字符串表示"""
        pass

    @abstractmethod
    def display_hint(self) -> DisplayHint:
        """返回显示提示"""
        pass

    def children(self) -> List[Tuple[str, Any]]:
        """返回子元素"""
        if self._children_cache is None:
            self._children_cache = list(self._generate_children())
        return self._children_cache

    def _generate_children(self) -> Iterator[Tuple[str, Any]]:
        """生成子元素（子类实现）"""
        return iter([])

    def _indent(self, level: int) -> str:
        """生成缩进"""
        return " " * (level * self.options.indent_size)

    def _format_value(self, value: Any, depth: int = 0) -> str:
        """格式化值"""
        if depth > self.options.max_depth:
            return "..."

        if isinstance(value, str):
            if len(value) > self.options.max_string_length:
                return f'"{value[: self.options.max_string_length]}..."'
            return f'"{value}"'
        elif isinstance(value, bytes):
            return f"b'{value.hex()}'"
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, list):
            items = []
            for i, item in enumerate(value[: self.options.max_elements]):
                items.append(f"[{i}]: {self._format_value(item, depth + 1)}")
            if len(value) > self.options.max_elements:
                items.append(f"... ({len(value) - self.options.max_elements} more)")
            return "{" + ", ".join(items) + "}"
        elif isinstance(value, dict):
            items = []
            for k, v in list(value.items())[: self.options.max_elements]:
                items.append(f"{k}: {self._format_value(v, depth + 1)}")
            if len(value) > self.options.max_elements:
                items.append(f"... ({len(value) - self.options.max_elements} more)")
            return "{" + ", ".join(items) + "}"
        else:
            return repr(value)

    def __str__(self) -> str:
        return self.to_string()


class StringPrinter(PrettyPrinterBase):
    """字符串美化打印器"""

    def __init__(self, value: Any, options: Optional[PrinterOption] = None):
        super().__init__(value, options)
        self._string_value: Optional[str] = None
        self._length: Optional[int] = None

    def _extract_string_info(self) -> Tuple[str, int]:
        """提取字符串信息"""
        if self._string_value is not None:
            return self._string_value, self._length or 0

        try:
            # 尝试从值对象中提取
            if hasattr(self.value, "data"):
                # ZhC 字符串格式
                data = self.value.data
                if hasattr(self.value, "length"):
                    length = int(self.value.length)
                    self._length = length
                    # 尝试读取数据
                    if hasattr(data, "string"):
                        self._string_value = data.string(length=length)
                    else:
                        self._string_value = str(data)
                else:
                    self._string_value = str(data)
                    self._length = len(self._string_value)
            else:
                self._string_value = str(self.value)
                self._length = len(self._string_value)
        except Exception:
            self._string_value = "<error>"
            self._length = 0

        return self._string_value, self._length or 0

    def to_string(self) -> str:
        value, length = self._extract_string_info()

        if length == 0:
            return '""'

        display_value = value
        if len(display_value) > self.options.max_string_length:
            display_value = display_value[: self.options.max_string_length] + "..."

        if self.options.show_type:
            return f'zhc_string("{display_value}") [len={length}]'
        else:
            return f'"{display_value}"'

    def display_hint(self) -> DisplayHint:
        return DisplayHint.STRING

    def length(self) -> int:
        """获取字符串长度"""
        _, length = self._extract_string_info()
        return length

    def value(self) -> str:
        """获取字符串值"""
        value, _ = self._extract_string_info()
        return value


class ArrayPrinter(PrettyPrinterBase):
    """数组美化打印器"""

    def __init__(self, value: Any, options: Optional[PrinterOption] = None):
        super().__init__(value, options)
        self._elements: Optional[List[Any]] = None
        self._length: Optional[int] = None
        self._capacity: Optional[int] = None
        self._element_type: Optional[str] = None

    def _extract_array_info(self) -> Tuple[List[Any], int, int, str]:
        """提取数组信息"""
        if self._elements is not None:
            return (
                self._elements,
                self._length or 0,
                self._capacity or 0,
                self._element_type or "",
            )

        try:
            if hasattr(self.value, "data"):
                # ZhC 数组格式
                length = int(self.value.length) if hasattr(self.value, "length") else 0
                capacity = (
                    int(self.value.capacity)
                    if hasattr(self.value, "capacity")
                    else length
                )

                # 获取元素类型
                if hasattr(self.value, "type") and hasattr(
                    self.value.type, "template_argument"
                ):
                    self._element_type = str(self.value.type.template_argument(0))
                else:
                    self._element_type = "unknown"

                # 获取元素
                data = self.value.data
                elements = []
                if hasattr(data, "__iter__"):
                    for i, elem in enumerate(data):
                        if i >= length:
                            break
                        elements.append(elem)

                self._length = length
                self._capacity = capacity
                self._elements = elements
            else:
                # 通用格式
                if isinstance(self.value, (list, tuple)):
                    self._elements = list(self.value)
                    self._length = len(self._elements)
                    self._capacity = self._length
                else:
                    self._elements = []
                    self._length = 0
                    self._capacity = 0
                self._element_type = type(self.value).__name__
        except Exception:
            self._elements = []
            self._length = 0
            self._capacity = 0
            self._element_type = "error"

        return self._elements, self._length, self._capacity, self._element_type

    def to_string(self) -> str:
        elements, length, capacity, elem_type = self._extract_array_info()

        parts = []
        if self.options.show_type:
            parts.append(f"zhc_array<{elem_type}>")

        parts.append(f"[size={length}")
        if capacity != length:
            parts.append(f", capacity={capacity}")
        parts.append("]")

        if length == 0:
            return "".join(parts) + " {}"

        # 显示元素预览
        preview = []
        for i, elem in enumerate(elements[: min(5, length)]):
            preview.append(self._format_value(elem))

        result = "".join(parts) + " {\n"
        result += ",\n".join(f"{self._indent(1)}{p}" for p in preview)
        if length > 5:
            result += f",\n{self._indent(1)}... ({length - 5} more elements)"
        result += "\n" + self._indent(0) + "}"

        return result

    def display_hint(self) -> DisplayHint:
        return DisplayHint.ARRAY

    def _generate_children(self) -> Iterator[Tuple[str, Any]]:
        elements, length, _, _ = self._extract_array_info()
        for i, elem in enumerate(elements[: self.options.max_elements]):
            yield f"[{i}]", elem

        if length > self.options.max_elements:
            yield "...", f"<{length - self.options.max_elements} more elements>"

    def length(self) -> int:
        """获取数组长度"""
        _, length, _, _ = self._extract_array_info()
        return length

    def capacity(self) -> int:
        """获取数组容量"""
        _, _, capacity, _ = self._extract_array_info()
        return capacity

    def element_type(self) -> str:
        """获取元素类型"""
        _, _, _, elem_type = self._extract_array_info()
        return elem_type

    def __iter__(self) -> Iterator[Any]:
        elements, _, _, _ = self._extract_array_info()
        return iter(elements)


class MapPrinter(PrettyPrinterBase):
    """映射美化打印器"""

    def __init__(self, value: Any, options: Optional[PrinterOption] = None):
        super().__init__(value, options)
        self._entries: Optional[List[Tuple[Any, Any]]] = None
        self._size: Optional[int] = None

    def _extract_map_info(self) -> Tuple[List[Tuple[Any, Any]], int]:
        """提取映射信息"""
        if self._entries is not None:
            return self._entries, self._size or 0

        try:
            if hasattr(self.value, "entries"):
                # ZhC 映射格式
                size = int(self.value.size) if hasattr(self.value, "size") else 0
                entries_list = self.value.entries

                entries = []
                if hasattr(entries_list, "__iter__"):
                    for entry in entries_list:
                        if hasattr(entry, "occupied") and entry.occupied:
                            key = entry.key if hasattr(entry, "key") else None
                            val = entry.value if hasattr(entry, "value") else None
                            entries.append((key, val))

                self._size = size
                self._entries = entries
            else:
                # 通用格式
                if isinstance(self.value, dict):
                    self._entries = list(self.value.items())
                    self._size = len(self._entries)
                else:
                    self._entries = []
                    self._size = 0
        except Exception:
            self._entries = []
            self._size = 0

        return self._entries, self._size

    def to_string(self) -> str:
        entries, size = self._extract_map_info()

        result = f"zhc_map [size={size}]"

        if size == 0:
            return result + " {}"

        result += " {\n"
        preview = []
        for key, val in entries[: min(5, size)]:
            key_str = self._format_value(key)
            val_str = self._format_value(val)
            preview.append(f"{key_str}: {val_str}")

        result += ",\n".join(f"{self._indent(1)}{p}" for p in preview)
        if size > 5:
            result += f",\n{self._indent(1)}... ({size - 5} more entries)"
        result += "\n" + self._indent(0) + "}"

        return result

    def display_hint(self) -> DisplayHint:
        return DisplayHint.MAP

    def _generate_children(self) -> Iterator[Tuple[str, Any]]:
        entries, size = self._extract_map_info()
        for i, (key, val) in enumerate(entries[: self.options.max_elements]):
            key_str = self._format_value(key)
            yield f"[{key_str}]", val

        if size > self.options.max_elements:
            yield "...", f"<{size - self.options.max_elements} more entries>"

    def size(self) -> int:
        """获取映射大小"""
        _, size = self._extract_map_info()
        return size

    def __iter__(self) -> Iterator[Tuple[Any, Any]]:
        entries, _ = self._extract_map_info()
        return iter(entries)


class StructPrinter(PrettyPrinterBase):
    """结构体美化打印器"""

    def __init__(self, value: Any, options: Optional[PrinterOption] = None):
        super().__init__(value, options)
        self._fields: Optional[List[Tuple[str, Any]]] = None
        self._type_name: Optional[str] = None

    def _extract_struct_info(self) -> Tuple[str, List[Tuple[str, Any]]]:
        """提取结构体信息"""
        if self._fields is not None:
            return self._type_name or "", self._fields

        try:
            # 获取类型名
            if hasattr(self.value, "type"):
                self._type_name = str(self.value.type)
            else:
                self._type_name = type(self.value).__name__

            # 获取字段
            fields = []
            if hasattr(self.value, "type") and hasattr(self.value.type, "fields"):
                # GDB/LLDB 值对象格式
                for field in self.value.type.fields():
                    field_name = field.name
                    field_value = self.value[field_name]
                    fields.append((field_name, field_value))
            elif hasattr(self.value, "__dict__"):
                # Python 对象格式
                for name, field_value in self.value.__dict__.items():
                    if not name.startswith("_"):
                        fields.append((name, field_value))
            else:
                # 尝试作为字典处理
                if isinstance(self.value, dict):
                    for name, field_value in self.value.items():
                        fields.append((str(name), field_value))

            self._fields = fields
        except Exception:
            self._type_name = "error"
            self._fields = []

        return self._type_name, self._fields

    def to_string(self) -> str:
        type_name, fields = self._extract_struct_info()

        if self.options.show_type:
            result = type_name
        else:
            result = "{ ... }"

        if not fields:
            return result + " {}"

        result += " {\n"
        field_lines = []
        for name, value in fields:
            value_str = self._format_value(value)
            field_lines.append(f"{name} = {value_str}")

        result += ",\n".join(f"{self._indent(1)}{line}" for line in field_lines)
        result += "\n" + self._indent(0) + "}"

        return result

    def display_hint(self) -> DisplayHint:
        return DisplayHint.STRUCT

    def _generate_children(self) -> Iterator[Tuple[str, Any]]:
        _, fields = self._extract_struct_info()
        for name, value in fields:
            yield name, value

    def field_names(self) -> List[str]:
        """获取字段名列表"""
        _, fields = self._extract_struct_info()
        return [name for name, _ in fields]


def create_printer(
    value: Any,
    hint: Optional[DisplayHint] = None,
    options: Optional[PrinterOption] = None,
) -> PrettyPrinterBase:
    """创建适当的打印器"""
    if hint is None:
        # 自动检测类型
        if hasattr(value, "type"):
            type_str = str(value.type)
            if "string" in type_str.lower():
                hint = DisplayHint.STRING
            elif "array" in type_str.lower():
                hint = DisplayHint.ARRAY
            elif "map" in type_str.lower():
                hint = DisplayHint.MAP
            else:
                hint = DisplayHint.STRUCT
        elif isinstance(value, str):
            hint = DisplayHint.STRING
        elif isinstance(value, (list, tuple)):
            hint = DisplayHint.ARRAY
        elif isinstance(value, dict):
            hint = DisplayHint.MAP
        else:
            hint = DisplayHint.STRUCT

    printer_map = {
        DisplayHint.STRING: StringPrinter,
        DisplayHint.ARRAY: ArrayPrinter,
        DisplayHint.MAP: MapPrinter,
        DisplayHint.STRUCT: StructPrinter,
    }

    printer_class = printer_map.get(hint, StructPrinter)
    return printer_class(value, options)
