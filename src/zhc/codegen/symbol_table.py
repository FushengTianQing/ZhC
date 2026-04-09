# -*- coding: utf-8 -*-
"""
ZhC 符号表管理

管理编译过程中的符号信息，包括函数、变量、标签等。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Iterator
import logging

logger = logging.getLogger(__name__)


class SymbolBinding(Enum):
    """符号绑定类型"""

    LOCAL = auto()  # 局部符号
    GLOBAL = auto()  # 全局符号
    WEAK = auto()  # 弱符号


class SymbolType(Enum):
    """符号类型"""

    NOTYPE = auto()  # 无类型
    OBJECT = auto()  # 数据对象
    FUNC = auto()  # 函数
    SECTION = auto()  # 节
    FILE = auto()  # 文件符号


class SymbolKind(Enum):
    """
    符号类型别名（测试兼容）

    提供更直观的名称，与测试代码期望的接口对齐。
    """

    NOTYPE = SymbolType.NOTYPE
    OBJECT = SymbolType.OBJECT
    FUNCTION = SymbolType.FUNC  # 测试期望 FUNCTION
    SECTION = SymbolType.SECTION
    FILE = SymbolType.FILE

    def to_symbol_type(self) -> SymbolType:
        return self.value


class SymbolVisibility(Enum):
    """符号可见性"""

    DEFAULT = auto()  # 默认可见性
    HIDDEN = auto()  # 隐藏（不可导出）
    PROTECTED = auto()  # 保护（不可覆盖）


@dataclass
class Symbol:
    """
    符号描述

    表示一个编译单元中的符号（函数、变量、标签等）。
    """

    name: str  # 符号名称
    mangled_name: str = ""  # 修饰后的名称（C++ ABI）
    symbol_type: SymbolType = (
        SymbolType.NOTYPE
    )  # 符号类型（使用 symbol_type 避免与内置 type 冲突）
    binding: SymbolBinding = SymbolBinding.GLOBAL
    visibility: SymbolVisibility = SymbolVisibility.DEFAULT

    # 地址和大小
    value: int = 0  # 符号值（地址或偏移）
    size: int = 0  # 符号大小

    # 位置信息
    section: str = ""  # 所属节名称
    defined: bool = False  # 是否已定义
    declaration: bool = False  # 是否为声明（外部引用）

    # 属性
    is_thread_local: bool = False  # 是否为线程局部变量
    is_absolute: bool = False  # 是否为绝对地址
    is_common: bool = False  # 是否为 common 符号

    # 调试信息
    source_file: str = ""
    source_line: int = 0

    # 测试兼容参数（使用不同名称避免与 property 冲突）
    kind: Optional[SymbolKind] = field(default=None, repr=False)
    _is_global_arg: Optional[bool] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.mangled_name:
            object.__setattr__(self, "mangled_name", self.name)

        # 测试兼容参数处理
        if self.kind is not None:
            object.__setattr__(self, "symbol_type", self.kind.to_symbol_type())
        if self._is_global_arg is not None:
            object.__setattr__(
                self,
                "binding",
                SymbolBinding.GLOBAL if self._is_global_arg else SymbolBinding.LOCAL,
            )

    @property
    def type(self) -> SymbolType:
        """符号类型（兼容属性）"""
        return self.symbol_type

    @type.setter
    def type(self, value: SymbolType) -> None:
        object.__setattr__(self, "symbol_type", value)

    @property
    def is_function(self) -> bool:
        """是否为函数符号"""
        return self.type == SymbolType.FUNC

    @property
    def is_variable(self) -> bool:
        """是否为变量符号"""
        return self.type == SymbolType.OBJECT

    @property
    def is_global(self) -> bool:
        """是否为全局符号"""
        return self.binding == SymbolBinding.GLOBAL

    @property
    def is_weak(self) -> bool:
        """是否为弱符号"""
        return self.binding == SymbolBinding.WEAK

    def __str__(self) -> str:
        binding_str = self.binding.name.lower()
        type_str = self.type.name.lower()
        return f"{binding_str} {type_str} {self.name}"

    def __hash__(self) -> int:
        """使 Symbol 可哈希"""
        return hash(self.name)

    def __eq__(self, other) -> bool:
        """Symbol 相等性比较（基于名称）"""
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name


# Monkey-patch Symbol.__init__ 以支持测试兼容参数 `is_global`
_original_symbol_init = Symbol.__init__


def _patched_symbol_init(
    self,
    name: str,
    mangled_name: str = "",
    symbol_type: SymbolType = SymbolType.NOTYPE,
    binding: SymbolBinding = SymbolBinding.GLOBAL,
    visibility: SymbolVisibility = SymbolVisibility.DEFAULT,
    value: int = 0,
    size: int = 0,
    section: str = "",
    defined: bool = False,
    declaration: bool = False,
    is_thread_local: bool = False,
    is_absolute: bool = False,
    is_common: bool = False,
    source_file: str = "",
    source_line: int = 0,
    kind: Optional[SymbolKind] = None,
    is_global: Optional[bool] = None,
    **kwargs,
):
    """Symbol.__init__ 的补丁，支持测试兼容参数 is_global"""
    # 如果传入了 is_global 参数，转换为 binding
    if is_global is not None:
        binding = SymbolBinding.GLOBAL if is_global else SymbolBinding.LOCAL
    # 调用原始 __init__
    _original_symbol_init(
        self,
        name=name,
        mangled_name=mangled_name,
        symbol_type=symbol_type,
        binding=binding,
        visibility=visibility,
        value=value,
        size=size,
        section=section,
        defined=defined,
        declaration=declaration,
        is_thread_local=is_thread_local,
        is_absolute=is_absolute,
        is_common=is_common,
        source_file=source_file,
        source_line=source_line,
        kind=kind,
        _is_global_arg=is_global,
        **kwargs,
    )


Symbol.__init__ = _patched_symbol_init


@dataclass
class Section:
    """节描述"""

    name: str
    flags: int = 0
    type: int = 0
    alignment: int = 1
    entry_size: int = 0

    # 地址信息
    address: int = 0
    size: int = 0
    offset: int = 0

    # 关联符号
    symbols: List[Symbol] = field(default_factory=list)

    # 内容（可选，用于内存中的节内容）
    data: bytes = field(default_factory=b"")


class SymbolTable:
    """
    符号表

    管理编译单元中的所有符号和节信息。

    使用方式：
        st = SymbolTable()
        st.add_section(".text", Section.SECTION_TYPE_EXEC)
        st.add_symbol("main", SymbolType.FUNC, defined=True)
        main_sym = st.get_symbol("main")
        for sym in st.defined_symbols():
            print(sym)
    """

    # 节类型常量
    SECTION_TYPE_NULL = 0
    SECTION_TYPE_PROGBITS = 1
    SECTION_TYPE_SYMTAB = 2
    SECTION_TYPE_STRTAB = 3
    SECTION_TYPE_RELA = 4
    SECTION_TYPE_HASH = 5
    SECTION_TYPE_DYNAMIC = 6
    SECTION_TYPE_NOTE = 7
    SECTION_TYPE_NOBITS = 8
    SECTION_TYPE_REL = 9
    SECTION_TYPE_DYNSYM = 11

    # 节标志常量
    SECTION_FLAG_WRITE = 0x1
    SECTION_FLAG_ALLOC = 0x2
    SECTION_FLAG_EXECINSTR = 0x4
    SECTION_FLAG_MERGE = 0x10
    SECTION_FLAG_STRINGS = 0x20
    SECTION_FLAG_INFO_LINK = 0x40
    SECTION_FLAG_LINK_ORDER = 0x80
    SECTION_FLAG_OS_NONCONFORMING = 0x100
    SECTION_FLAG_GROUP = 0x200
    SECTION_FLAG_TLS = 0x400
    SECTION_FLAG_EXCLUDE = 0x800
    SECTION_FLAG_COMPRESSED = 0x800

    # 标准节名
    SECTION_TEXT = ".text"
    SECTION_DATA = ".data"
    SECTION_BSS = ".bss"
    SECTION_RODATA = ".rodata"
    SECTION_SYMTAB = ".symtab"
    SECTION_STRTAB = ".strtab"
    SECTION_SHSTRTAB = ".shstrtab"
    SECTION_REL_TEXT = ".rel.text"
    SECTION_RELA_TEXT = ".rela.text"

    def __init__(self):
        self._symbols: Dict[str, Symbol] = {}
        self._sections: Dict[str, Section] = {}
        self._undefined: Set[str] = set()
        self._section_order: List[str] = []

        # 字符串表
        self._string_table: Dict[str, int] = {}
        self._string_data: List[bytes] = [b"\x00"]  # 从空字符串开始

        # 统计
        self._stats = {
            "total_symbols": 0,
            "defined_symbols": 0,
            "undefined_symbols": 0,
            "local_symbols": 0,
            "global_symbols": 0,
        }

    # =========================================================================
    # 节管理
    # =========================================================================

    def add_section(
        self,
        name: str,
        section_type: int = SECTION_TYPE_PROGBITS,
        flags: int = 0,
        alignment: int = 1,
    ) -> Section:
        """
        添加节

        Args:
            name: 节名称
            section_type: 节类型
            flags: 节标志
            alignment: 对齐要求

        Returns:
            创建的节对象
        """
        if name in self._sections:
            logger.warning(f"Section {name} already exists")
            return self._sections[name]

        section = Section(
            name=name,
            type=section_type,
            flags=flags,
            alignment=alignment,
        )
        self._sections[name] = section
        self._section_order.append(name)

        return section

    def get_section(self, name: str) -> Optional[Section]:
        """获取节"""
        return self._sections.get(name)

    def sections(self) -> Iterator[Section]:
        """遍历所有节（按添加顺序）"""
        for name in self._section_order:
            yield self._sections[name]

    def has_section(self, name: str) -> bool:
        """检查节是否存在"""
        return name in self._sections

    def get_or_create_section(self, name: str) -> Section:
        """获取或创建节"""
        if name not in self._sections:
            return self.add_section(name)
        return self._sections[name]

    # =========================================================================
    # 符号管理
    # =========================================================================

    def add_symbol(
        self,
        name: str,
        symbol_type: SymbolType = SymbolType.NOTYPE,
        binding: SymbolBinding = SymbolBinding.GLOBAL,
        defined: bool = False,
        section: str = "",
        value: int = 0,
        size: int = 0,
    ) -> Symbol:
        """
        添加符号

        Args:
            name: 符号名称或 Symbol 对象
            symbol_type: 符号类型
            binding: 绑定类型
            defined: 是否已定义
            section: 所属节
            value: 符号值（地址或偏移）
            size: 符号大小

        Returns:
            创建的符号对象
        """
        # 支持直接传入 Symbol 对象
        if isinstance(name, Symbol):
            symbol = name
            name = symbol.name
            if name in self._symbols:
                return self._symbols[name]
        else:
            if name in self._symbols:
                existing = self._symbols[name]
                if defined and not existing.defined:
                    # 更新未定义符号为已定义
                    existing.defined = defined
                    existing.section = section
                    existing.value = value
                    existing.size = size
                    existing.type = symbol_type
                    self._stats["defined_symbols"] += 1
                    self._undefined.discard(name)
                return existing

            symbol = Symbol(
                name=name,
                symbol_type=symbol_type,
                binding=binding,
                defined=defined,
                section=section,
                value=value,
                size=size,
            )

        self._symbols[name] = symbol
        self._stats["total_symbols"] += 1

        if defined:
            self._stats["defined_symbols"] += 1
            if section:
                section_obj = self.get_section(section)
                if section_obj:
                    section_obj.symbols.append(symbol)
        else:
            self._undefined.add(name)

        if binding == SymbolBinding.LOCAL:
            self._stats["local_symbols"] += 1
        else:
            self._stats["global_symbols"] += 1

        self._stats["undefined_symbols"] = len(self._undefined)

        return symbol

    def get_symbol(self, name: str) -> Optional[Symbol]:
        """获取符号"""
        return self._symbols.get(name)

    def has_symbol(self, name: str) -> bool:
        """检查符号是否存在"""
        return name in self._symbols

    def is_defined(self, name: str) -> bool:
        """检查符号是否已定义"""
        sym = self._symbols.get(name)
        return sym is not None and sym.defined

    def is_undefined(self, name: str) -> bool:
        """检查符号是否未定义（外部引用）"""
        return name in self._undefined

    def symbols(self, defined_only: bool = False) -> Iterator[Symbol]:
        """
        遍历所有符号

        Args:
            defined_only: 仅返回已定义的符号

        Yields:
            符号对象
        """
        for symbol in self._symbols.values():
            if not defined_only or symbol.defined:
                yield symbol

    def defined_symbols(
        self, binding: Optional[SymbolBinding] = None
    ) -> Iterator[Symbol]:
        """
        遍历已定义的符号

        Args:
            binding: 可选，按绑定类型过滤

        Yields:
            符号对象
        """
        for symbol in self._symbols.values():
            if symbol.defined:
                if binding is None or symbol.binding == binding:
                    yield symbol

    def global_symbols(self) -> Iterator[Symbol]:
        """遍历全局符号"""
        return self.defined_symbols(binding=SymbolBinding.GLOBAL)

    def local_symbols(self) -> Iterator[Symbol]:
        """遍历局部符号"""
        return self.defined_symbols(binding=SymbolBinding.LOCAL)

    def undefined_symbols(self) -> Iterator[str]:
        """遍历未定义的符号（外部引用）"""
        for name in self._undefined:
            yield name

    # =========================================================================
    # 特殊符号
    # =========================================================================

    def add_function_symbol(
        self,
        name: str,
        section: str = SECTION_TEXT,
        value: int = 0,
        size: int = 0,
    ) -> Symbol:
        """添加函数符号"""
        return self.add_symbol(
            name=name,
            symbol_type=SymbolType.FUNC,
            binding=SymbolBinding.GLOBAL,
            defined=True,
            section=section,
            value=value,
            size=size,
        )

    def add_variable_symbol(
        self,
        name: str,
        section: str = SECTION_DATA,
        value: int = 0,
        size: int = 0,
        is_tls: bool = False,
    ) -> Symbol:
        """添加变量符号"""
        sym = self.add_symbol(
            name=name,
            symbol_type=SymbolType.OBJECT,
            binding=SymbolBinding.GLOBAL,
            defined=True,
            section=section,
            value=value,
            size=size,
        )
        sym.is_thread_local = is_tls
        return sym

    def add_extern_symbol(self, name: str) -> Symbol:
        """添加外部引用符号"""
        return self.add_symbol(
            name=name,
            symbol_type=SymbolType.NOTYPE,
            binding=SymbolBinding.GLOBAL,
            defined=False,
        )

    def add_local_label(
        self, name: str, section: str = SECTION_TEXT, value: int = 0
    ) -> Symbol:
        """添加局部标签"""
        return self.add_symbol(
            name=name,
            symbol_type=SymbolType.NOTYPE,
            binding=SymbolBinding.LOCAL,
            defined=True,
            section=section,
            value=value,
        )

    # =========================================================================
    # 字符串表
    # =========================================================================

    def add_string(self, s: str) -> int:
        """
        添加字符串到字符串表

        Args:
            s: 要添加的字符串

        Returns:
            字符串在表中的偏移
        """
        if s in self._string_table:
            return self._string_table[s]

        data = s.encode("utf-8") + b"\x00"
        offset = len(self._string_data)
        self._string_table[s] = offset
        self._string_data.append(data)
        return offset

    def get_string_offset(self, s: str) -> Optional[int]:
        """获取字符串的偏移"""
        return self._string_table.get(s)

    def get_string_data(self) -> bytes:
        """获取字符串表数据"""
        return b"".join(self._string_data)

    # =========================================================================
    # 工具方法
    # =========================================================================

    def resolve_forward_references(self) -> List[str]:
        """
        尝试解析前向引用

        Returns:
            无法解析的符号列表
        """
        unresolved = []

        for name in self._undefined:
            # 尝试在其他编译单元中查找（这里简化处理）
            # 实际编译器会通过链接器或其他编译单元来解析
            unresolved.append(name)

        return unresolved

    def get_section_for_symbol(self, name: str) -> Optional[Section]:
        """获取符号所在的节"""
        sym = self._symbols.get(name)
        if sym and sym.section:
            return self._sections.get(sym.section)
        return None

    def validate(self) -> List[str]:
        """
        验证符号表完整性

        Returns:
            错误信息列表
        """
        errors = []

        # 检查未定义的全局符号
        for name in self._undefined:
            sym = self._symbols.get(name)
            if sym and sym.binding == SymbolBinding.GLOBAL:
                # 全局符号应该被定义或在其他地方定义
                pass

        # 检查符号引用的节是否存在
        for sym in self._symbols.values():
            if sym.section and not self.has_section(sym.section):
                errors.append(
                    f"Symbol '{sym.name}' references non-existent section '{sym.section}'"
                )

        return errors

    def get_stats(self) -> Dict[str, int]:
        """获取符号表统计信息"""
        return self._stats.copy()

    def clear(self) -> None:
        """清空符号表"""
        self._symbols.clear()
        self._sections.clear()
        self._undefined.clear()
        self._section_order.clear()
        self._string_table.clear()
        self._string_data = [b"\x00"]
        self._stats = {
            "total_symbols": 0,
            "defined_symbols": 0,
            "undefined_symbols": 0,
            "local_symbols": 0,
            "global_symbols": 0,
        }

    def __len__(self) -> int:
        """获取符号数量"""
        return len(self._symbols)

    def __contains__(self, name: str) -> bool:
        """检查符号是否存在"""
        return name in self._symbols

    def __str__(self) -> str:
        lines = [f"SymbolTable ({self._stats['total_symbols']} symbols):"]
        lines.append("  Sections:")
        for section in self.sections():
            lines.append(f"    {section.name}: {section.size} bytes")
        lines.append("  Symbols:")
        for sym in self.symbols(defined_only=True):
            lines.append(f"    {sym}")
        return "\n".join(lines)


# ============================================================================
# 工厂函数
# ============================================================================


def create_standard_symbol_table() -> SymbolTable:
    """创建标准符号表（包含标准节）"""
    st = SymbolTable()

    # 代码节
    st.add_section(
        SymbolTable.SECTION_TEXT,
        section_type=SymbolTable.SECTION_TYPE_PROGBITS,
        flags=SymbolTable.SECTION_FLAG_ALLOC | SymbolTable.SECTION_FLAG_EXECINSTR,
        alignment=16,
    )

    # 数据节
    st.add_section(
        SymbolTable.SECTION_DATA,
        section_type=SymbolTable.SECTION_TYPE_PROGBITS,
        flags=SymbolTable.SECTION_FLAG_ALLOC | SymbolTable.SECTION_FLAG_WRITE,
        alignment=8,
    )

    # BSS 节（未初始化数据）
    st.add_section(
        SymbolTable.SECTION_BSS,
        section_type=SymbolTable.SECTION_TYPE_NOBITS,
        flags=SymbolTable.SECTION_FLAG_ALLOC | SymbolTable.SECTION_FLAG_WRITE,
        alignment=16,
    )

    # 只读数据节
    st.add_section(
        SymbolTable.SECTION_RODATA,
        section_type=SymbolTable.SECTION_TYPE_PROGBITS,
        flags=SymbolTable.SECTION_FLAG_ALLOC,
        alignment=8,
    )

    return st


# ============================================================================
# 别名：测试兼容
# ============================================================================

# 保留 SymbolKind 类定义（原 SymbolType 别名已移除）


# 工厂函数别名
create_symbol_table = create_standard_symbol_table
