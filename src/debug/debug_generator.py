"""
DWARF调试信息生成器
生成符合DWARF标准的调试信息，支持源码级调试

DWARF是一种标准的调试信息格式，被GDB、LLDB等调试器广泛支持。
本模块生成：
- 行号信息（.debug_line）
- 符号表（.debug_info）
- 类型信息（.debug_abbrev）
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceLocation:
    """源码位置信息"""
    file_path: str          # 源文件路径
    line_number: int        # 行号
    column_number: int = 0  # 列号（可选）
    
    def to_dict(self) -> Dict:
        return {
            'file': self.file_path,
            'line': self.line_number,
            'column': self.column_number
        }


@dataclass
class AddressRange:
    """地址范围"""
    low_pc: int     # 起始地址
    high_pc: int    # 结束地址
    
    def contains(self, address: int) -> bool:
        """检查地址是否在范围内"""
        return self.low_pc <= address < self.high_pc


@dataclass
class CompileUnit:
    """编译单元"""
    name: str                       # 单元名称
    language: str = "zhc"          # 语言标识
    comp_dir: str = ""             # 编译目录
    producer: str = "zhc-1.0.0"    # 编译器版本
    low_pc: int = 0                # 起始地址
    high_pc: int = 0               # 结束地址
    source_locations: List[SourceLocation] = field(default_factory=list)
    symbols: List[Dict] = field(default_factory=list)
    types: List[Dict] = field(default_factory=list)


class LineNumberTable:
    """
    DWARF行号表生成器 (T034)
    
    生成.debug_line段，建立源码行号与机器码地址的映射关系
    
    行号表格式：
    - 文件表：记录所有源文件
    - 行号程序：一系列操作码指令
    - 行号条目：实际映射关系
    """
    
    def __init__(self):
        self.file_table: List[str] = []  # 文件表
        self.line_entries: List[Dict] = []  # 行号条目
        self.current_address = 0
        self.current_line = 1
        self.current_file = 0
        
    def add_file(self, file_path: str) -> int:
        """
        添加源文件到文件表
        
        Args:
            file_path: 源文件路径
            
        Returns:
            文件索引
        """
        if file_path not in self.file_table:
            self.file_table.append(file_path)
        return self.file_table.index(file_path)
    
    def add_line_entry(self, 
                      address: int, 
                      line_number: int,
                      file_index: int = 0,
                      column: int = 0,
                      is_statement: bool = True,
                      is_prologue_end: bool = False) -> None:
        """
        添加行号条目
        
        Args:
            address: 机器码地址
            line_number: 源码行号
            file_index: 文件表索引
            column: 列号
            is_statement: 是否是语句起始
            is_prologue_end: 是否是函数序言结束
        """
        entry = {
            'address': address,
            'line': line_number,
            'file': file_index,
            'column': column,
            'is_statement': is_statement,
            'is_prologue_end': is_prologue_end
        }
        self.line_entries.append(entry)
        
        # 更新当前位置
        self.current_address = address
        self.current_line = line_number
        self.current_file = file_index
    
    def get_line_for_address(self, address: int) -> Optional[Tuple[int, str]]:
        """
        根据地址查找行号
        
        Args:
            address: 机器码地址
            
        Returns:
            (行号, 文件路径) 或 None
        """
        # 二分查找最近的行号条目
        low, high = 0, len(self.line_entries)
        
        while low < high:
            mid = (low + high) // 2
            entry = self.line_entries[mid]
            
            if entry['address'] <= address:
                if mid == len(self.line_entries) - 1 or \
                   self.line_entries[mid + 1]['address'] > address:
                    # 找到对应的条目
                    file_path = self.file_table[entry['file']] if entry['file'] < len(self.file_table) else ""
                    return (entry['line'], file_path)
                low = mid + 1
            else:
                high = mid
        
        return None
    
    def generate_dwarf_line_program(self) -> bytes:
        """
        生成DWARF行号程序
        
        Returns:
            DWARF行号程序字节序列
        """
        program = bytearray()
        
        # DWARF行号程序标准操作码
        # DW_LNS_copy = 1
        # DW_LNS_advance_pc = 2
        # DW_LNS_advance_line = 3
        # DW_LNS_set_file = 4
        # DW_LNS_set_column = 5
        
        for entry in self.line_entries:
            # 设置文件
            if entry['file'] != self.current_file:
                program.append(0x04)  # DW_LNS_set_file
                program.append(entry['file'])
                self.current_file = entry['file']
            
            # 推进行号
            line_delta = entry['line'] - self.current_line
            if line_delta != 0:
                program.append(0x03)  # DW_LNS_advance_line
                # LEB128编码行号差值
                self._write_leb128(program, line_delta)
                self.current_line = entry['line']
            
            # 推进地址
            addr_delta = entry['address'] - self.current_address
            if addr_delta != 0:
                program.append(0x02)  # DW_LNS_advance_pc
                # LEB128编码地址差值
                self._write_leb128(program, addr_delta)
                self.current_address = entry['address']
            
            # 复制当前状态
            program.append(0x01)  # DW_LNS_copy
        
        return bytes(program)
    
    def _write_leb128(self, buffer: bytearray, value: int) -> None:
        """写入LEB128编码的整数"""
        if value >= 0:
            # 无符号LEB128
            while True:
                byte = value & 0x7F
                value >>= 7
                if value != 0:
                    byte |= 0x80
                buffer.append(byte)
                if value == 0:
                    break
        else:
            # 有符号LEB128
            more = True
            while more:
                byte = value & 0x7F
                value >>= 7
                # 检查是否需要继续
                if value == -1 and (byte & 0x40):
                    more = False
                elif value == 0 and not (byte & 0x40):
                    more = False
                else:
                    byte |= 0x80
                buffer.append(byte)
    
    def to_json(self) -> Dict:
        """导出为JSON格式"""
        return {
            'file_table': self.file_table,
            'line_entries': self.line_entries
        }


class DebugSymbolTable:
    """
    调试符号表生成器 (T035)
    
    生成.debug_info和.debug_sym段，记录变量、函数等符号信息
    
    符号类型：
    - DW_TAG_variable: 变量
    - DW_TAG_subprogram: 函数/子程序
    - DW_TAG_formal_parameter: 形式参数
    - DW_TAG_label: 标签
    """
    
    def __init__(self):
        self.symbols: List[Dict] = []
        self.current_scope_id = 0
        self.scope_stack: List[int] = [0]
        
    def enter_scope(self, scope_type: str = "block") -> int:
        """
        进入新的作用域
        
        Args:
            scope_type: 作用域类型
            
        Returns:
            作用域ID
        """
        self.current_scope_id += 1
        self.scope_stack.append(self.current_scope_id)
        return self.current_scope_id
    
    def leave_scope(self) -> int:
        """
        离开当前作用域
        
        Returns:
        离开的作用域ID
        """
        if len(self.scope_stack) > 1:
            return self.scope_stack.pop()
        return 0
    
    def add_variable(self,
                    name: str,
                    type_ref: str,
                    location: int,
                    scope_id: Optional[int] = None,
                    file_path: str = "",
                    line_number: int = 0) -> None:
        """
        添加变量符号
        
        Args:
            name: 变量名
            type_ref: 类型引用
            location: 内存地址或栈偏移
            scope_id: 作用域ID
            file_path: 源文件路径
            line_number: 定义行号
        """
        symbol = {
            'tag': 'DW_TAG_variable',
            'name': name,
            'type': type_ref,
            'location': location,
            'scope': scope_id or self.scope_stack[-1],
            'decl_file': file_path,
            'decl_line': line_number,
            'external': False,
            'artificial': False
        }
        self.symbols.append(symbol)
    
    def add_function(self,
                    name: str,
                    return_type: str,
                    low_pc: int,
                    high_pc: int,
                    parameters: Optional[List[Dict]] = None,
                    file_path: str = "",
                    line_number: int = 0,
                    is_external: bool = False) -> None:
        """
        添加函数符号
        
        Args:
            name: 函数名
            return_type: 返回类型
            low_pc: 起始地址
            high_pc: 结束地址
            parameters: 参数列表
            file_path: 源文件路径
            line_number: 定义行号
            is_external: 是否是外部函数
        """
        symbol = {
            'tag': 'DW_TAG_subprogram',
            'name': name,
            'type': return_type,
            'low_pc': low_pc,
            'high_pc': high_pc,
            'parameters': parameters or [],
            'decl_file': file_path,
            'decl_line': line_number,
            'external': is_external,
            'scope': self.scope_stack[-1]
        }
        self.symbols.append(symbol)
        
        # 为参数创建符号
        scope_id = self.enter_scope('function')
        for param in (parameters or []):
            self.add_formal_parameter(
                param.get('name', ''),
                param.get('type', 'void'),
                param.get('location', 0),
                file_path,
                line_number
            )
        self.leave_scope()
    
    def add_formal_parameter(self,
                            name: str,
                            type_ref: str,
                            location: int,
                            file_path: str = "",
                            line_number: int = 0) -> None:
        """
        添加形式参数符号
        
        Args:
            name: 参数名
            type_ref: 类型引用
            location: 栈偏移或寄存器位置
            file_path: 源文件路径
            line_number: 定义行号
        """
        symbol = {
            'tag': 'DW_TAG_formal_parameter',
            'name': name,
            'type': type_ref,
            'location': location,
            'decl_file': file_path,
            'decl_line': line_number,
            'scope': self.scope_stack[-1]
        }
        self.symbols.append(symbol)
    
    def add_label(self,
                 name: str,
                 address: int,
                 file_path: str = "",
                 line_number: int = 0) -> None:
        """
        添加标签符号
        
        Args:
            name: 标签名
            address: 标签地址
            file_path: 源文件路径
            line_number: 定义行号
        """
        symbol = {
            'tag': 'DW_TAG_label',
            'name': name,
            'address': address,
            'decl_file': file_path,
            'decl_line': line_number,
            'scope': self.scope_stack[-1]
        }
        self.symbols.append(symbol)
    
    def lookup_symbol(self, name: str, scope_id: Optional[int] = None) -> Optional[Dict]:
        """
        查找符号
        
        Args:
            name: 符号名
            scope_id: 作用域ID（None表示全局查找）
            
        Returns:
            符号信息或None
        """
        for symbol in self.symbols:
            if symbol['name'] == name:
                if scope_id is None or symbol['scope'] == scope_id:
                    return symbol
        return None
    
    def generate_dwarf_info(self) -> bytes:
        """
        生成DWARF调试信息
        
        Returns:
            DWARF调试信息字节序列
        """
        info = bytearray()
        
        # DWARF调试信息条目格式
        for symbol in self.symbols:
            # 写入标签
            tag = self._get_tag_code(symbol['tag'])
            info.append(tag)
            
            # 写入属性
            self._write_dwarf_string(info, symbol.get('name', ''))
            self._write_dwarf_address(info, symbol.get('low_pc', 0))
            self._write_dwarf_address(info, symbol.get('high_pc', 0))
            
            # 写入类型引用
            type_ref = symbol.get('type', 'void')
            self._write_dwarf_ref(info, type_ref)
        
        return bytes(info)
    
    def _get_tag_code(self, tag: str) -> int:
        """获取DWARF标签代码"""
        tag_codes = {
            'DW_TAG_variable': 0x34,
            'DW_TAG_subprogram': 0x2e,
            'DW_TAG_formal_parameter': 0x05,
            'DW_TAG_label': 0x0a
        }
        return tag_codes.get(tag, 0x00)
    
    def _write_dwarf_string(self, buffer: bytearray, value: str) -> None:
        """写入DWARF字符串属性"""
        encoded = value.encode('utf-8')
        buffer.extend(encoded)
        buffer.append(0x00)  # NULL终止符
    
    def _write_dwarf_address(self, buffer: bytearray, value: int) -> None:
        """写入DWARF地址属性"""
        # 64位地址
        buffer.extend(value.to_bytes(8, byteorder='little', signed=False))
    
    def _write_dwarf_ref(self, buffer: bytearray, ref: str) -> None:
        """写入DWARF引用属性"""
        # 简化实现：写入字符串引用
        self._write_dwarf_string(buffer, ref)
    
    def to_json(self) -> Dict:
        """导出为JSON格式"""
        return {
            'symbols': self.symbols
        }


class TypeInfoGenerator:
    """
    类型信息生成器 (T036)
    
    生成.debug_abbrev段，记录类型定义信息
    
    支持的类型：
    - 基本类型（int, float, char等）
    - 指针类型
    -数组类型
    - 结构体类型
    - 函数类型
    """
    
    def __init__(self):
        self.type_table: Dict[str, Dict] = {}
        self.type_id_counter = 0
        
        # 初始化基本类型
        self._init_basic_types()
    
    def _init_basic_types(self) -> None:
        """初始化基本类型定义"""
        basic_types = {
            'void': {
                'tag': 'DW_TAG_unspecified_type',
                'name': 'void',
                'byte_size': 0,
                'encoding': 'DW_ATE_void'
            },
            '整数型': {
                'tag': 'DW_TAG_base_type',
                'name': '整数型',
                'byte_size': 4,
                'encoding': 'DW_ATE_signed'
            },
            '浮点型': {
                'tag': 'DW_TAG_base_type',
                'name': '浮点型',
                'byte_size': 4,
                'encoding': 'DW_ATE_float'
            },
            '双精度型': {
                'tag': 'DW_TAG_base_type',
                'name': '双精度型',
                'byte_size': 8,
                'encoding': 'DW_ATE_float'
            },
            '字符型': {
                'tag': 'DW_TAG_base_type',
                'name': '字符型',
                'byte_size': 1,
                'encoding': 'DW_ATE_signed_char'
            },
            '字符串型': {
                'tag': 'DW_TAG_pointer_type',
                'name': '字符串型',
                'base_type': '字符型',
                'byte_size': 8
            },
            '布尔型': {
                'tag': 'DW_TAG_base_type',
                'name': '布尔型',
                'byte_size': 1,
                'encoding': 'DW_ATE_boolean'
            }
        }
        
        for type_name, type_info in basic_types.items():
            self.type_table[type_name] = type_info
    
    def add_type(self, 
                type_name: str,
                type_tag: str,
                byte_size: int,
                encoding: str = "",
                base_type: str = "",
                members: Optional[List[Dict]] = None) -> int:
        """
        添加类型定义
        
        Args:
            type_name: 类型名称
            type_tag: DWARF类型标签
            byte_size: 字节大小
            encoding: 编码方式
            base_type: 基础类型（指针/数组）
            members: 成员列表（结构体）
            
        Returns:
            类型ID
        """
        self.type_id_counter += 1
        
        type_info = {
            'tag': type_tag,
            'name': type_name,
            'byte_size': byte_size,
            'encoding': encoding,
            'base_type': base_type,
            'members': members or [],
            'type_id': self.type_id_counter
        }
        
        self.type_table[type_name] = type_info
        return self.type_id_counter
    
    def add_pointer_type(self,
                        type_name: str,
                        base_type: str,
                        byte_size: int = 8) -> int:
        """
        添加指针类型
        
        Args:
            type_name: 类型名称
            base_type: 基础类型
            byte_size: 指针大小（默认8字节）
            
        Returns:
            类型ID
        """
        return self.add_type(
            type_name,
            'DW_TAG_pointer_type',
            byte_size,
            base_type=base_type
        )
    
    def add_array_type(self,
                      type_name: str,
                      element_type: str,
                      array_size: int,
                      element_size: int) -> int:
        """
        添加数组类型
        
        Args:
            type_name: 类型名称
            element_type: 元素类型
            array_size: 数组大小
            element_size: 元素大小
            
        Returns:
            类型ID
        """
        type_id = self.type_id_counter + 1
        self.type_id_counter += 1
        
        type_info = {
            'tag': 'DW_TAG_array_type',
            'name': type_name,
            'element_type': element_type,
            'array_size': array_size,
            'element_size': element_size,
            'byte_size': array_size * element_size,
            'type_id': type_id
        }
        
        self.type_table[type_name] = type_info
        return type_id
    
    def add_struct_type(self,
                       type_name: str,
                       members: List[Dict],
                       byte_size: int) -> int:
        """
        添加结构体类型
        
        Args:
            type_name: 类型名称
            members: 成员列表
            byte_size: 结构体大小
            
        Returns:
            类型ID
        """
        return self.add_type(
            type_name,
            'DW_TAG_structure_type',
            byte_size,
            members=members
        )
    
    def add_function_type(self,
                         return_type: str,
                         parameters: List[str],
                         type_name: str = "") -> int:
        """
        添加函数类型
        
        Args:
            return_type: 返回类型
            parameters: 参数类型列表
            type_name: 类型名称
            
        Returns:
            类型ID
        """
        type_id = self.type_id_counter + 1
        self.type_id_counter += 1
        
        type_info = {
            'tag': 'DW_TAG_subroutine_type',
            'name': type_name or f"function_{type_id}",
            'return_type': return_type,
            'parameters': parameters,
            'type_id': type_id
        }
        
        self.type_table[type_info['name']] = type_info
        return type_id
    
    def lookup_type(self, type_name: str) -> Optional[Dict]:
        """
        查找类型定义
        
        Args:
            type_name: 类型名称
            
        Returns:
            类型信息或None
        """
        return self.type_table.get(type_name)
    
    def get_type_size(self, type_name: str) -> int:
        """
        获取类型大小
        
        Args:
            type_name: 类型名称
            
        Returns:
            字节大小
        """
        type_info = self.lookup_type(type_name)
        if type_info:
            return type_info.get('byte_size', 0)
        return 0
    
    def generate_dwarf_abbrev(self) -> bytes:
        """
        生成DWARF缩写表
        
        Returns:
            DWARF缩写表字节序列
        """
        abbrev = bytearray()
        
        # DWARF缩写表格式
        for type_name, type_info in self.type_table.items():
            # 写入缩写码
            abbrev.append(type_info.get('type_id', 0))
            
            # 写入标签
            tag = self._get_type_tag(type_info['tag'])
            abbrev.append(tag)
            
            # 写入是否有子项
            has_children = 1 if type_info.get('members') else 0
            abbrev.append(has_children)
            
            # 写入属性规范
            self._write_abbrev_attrs(abbrev, type_info)
        
        return bytes(abbrev)
    
    def _get_type_tag(self, tag: str) -> int:
        """获取DWARF类型标签代码"""
        tag_codes = {
            'DW_TAG_base_type': 0x24,
            'DW_TAG_pointer_type': 0x0f,
            'DW_TAG_array_type': 0x01,
            'DW_TAG_structure_type': 0x13,
            'DW_TAG_subroutine_type': 0x2b,
            'DW_TAG_unspecified_type': 0x3b
        }
        return tag_codes.get(tag, 0x00)
    
    def _write_abbrev_attrs(self, buffer: bytearray, type_info: Dict) -> None:
        """写入缩写属性"""
        # DW_AT_name
        buffer.append(0x03)  # DW_AT_name
        buffer.append(0x08)  # DW_FORM_string
        
        # DW_AT_byte_size
        if 'byte_size' in type_info:
            buffer.append(0x0b)  # DW_AT_byte_size
            buffer.append(0x0b)  # DW_FORM_data1
        
        # DW_AT_encoding
        if 'encoding' in type_info:
            buffer.append(0x3e)  # DW_AT_encoding
            buffer.append(0x0b)  # DW_FORM_data1
        
        # 结束标记
        buffer.append(0x00)
        buffer.append(0x00)
    
    def to_json(self) -> Dict:
        """导出为JSON格式"""
        return {
            'type_table': self.type_table
        }


class DWARFGenerator:
    """
    DWARF调试信息生成器主类
    
    整合行号表、符号表、类型信息，生成完整的DWARF调试信息
    """
    
    def __init__(self):
        self.line_table = LineNumberTable()
        self.symbol_table = DebugSymbolTable()
        self.type_info = TypeInfoGenerator()
        self.compile_units: List[CompileUnit] = []
        
    def add_compile_unit(self, 
                        name: str,
                        source_file: str,
                        comp_dir: str = "") -> CompileUnit:
        """
        添加编译单元
        
        Args:
            name: 单元名称
            source_file: 源文件路径
            comp_dir: 编译目录
            
        Returns:
            编译单元对象
        """
        unit = CompileUnit(
            name=name,
            comp_dir=comp_dir
        )
        self.compile_units.append(unit)
        
        # 添加源文件到行号表
        file_index = self.line_table.add_file(source_file)
        
        return unit
    
    def generate_debug_info(self) -> Dict[str, bytes]:
        """
        生成完整的调试信息
        
        Returns:
            各调试段的字节序列字典
        """
        return {
            '.debug_line': self.line_table.generate_dwarf_line_program(),
            '.debug_info': self.symbol_table.generate_dwarf_info(),
            '.debug_abbrev': self.type_info.generate_dwarf_abbrev()
        }
    
    def generate_debug_sections(self) -> Dict[str, Any]:
        """
        生成调试段（JSON格式，用于调试和查看）
        
        Returns:
            各调试段的JSON表示
        """
        return {
            'debug_line': self.line_table.to_json(),
            'debug_info': self.symbol_table.to_json(),
            'debug_abbrev': self.type_info.to_json()
        }
    
    def save_to_file(self, output_path: str) -> None:
        """
        保存调试信息到文件
        
        Args:
            output_path: 输出文件路径
        """
        debug_data = self.generate_debug_sections()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)


class DebugInfoGenerator:
    """
    调试信息生成器（简化接口）
    
    提供更简单的API用于生成调试信息
    """
    
    def __init__(self, source_file: str, output_file: str = ""):
        """
        初始化调试信息生成器
        
        Args:
            source_file: 源文件路径
            output_file: 输出文件路径（可选）
        """
        self.dwarf = DWARFGenerator()
        self.source_file = source_file
        self.output_file = output_file or source_file.replace('.zhc', '.debug.json')
        
        # 添加编译单元
        self.unit = self.dwarf.add_compile_unit(
            name=Path(source_file).stem,
            source_file=source_file
        )
    
    def map_line(self, line_number: int, address: int) -> None:
        """
        映射源码行号到地址
        
        Args:
            line_number: 源码行号
            address: 机器码地址
        """
        file_index = 0  # 主文件
        self.dwarf.line_table.add_line_entry(address, line_number, file_index)
    
    def add_function(self,
                    name: str,
                    start_line: int,
                    end_line: int,
                    start_addr: int,
                    end_addr: int,
                    return_type: str = "空型") -> None:
        """
        添加函数调试信息
        
        Args:
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
        """
        # 添加行号映射
        self.map_line(start_line, start_addr)
        self.map_line(end_line, end_addr)
        
        # 添加函数符号
        self.dwarf.symbol_table.add_function(
            name=name,
            return_type=return_type,
            low_pc=start_addr,
            high_pc=end_addr,
            file_path=self.source_file,
            line_number=start_line
        )
    
    def add_variable(self,
                    name: str,
                    type_name: str,
                    line_number: int,
                    address: int) -> None:
        """
        添加变量调试信息
        
        Args:
            name: 变量名
            type_name: 类型名
            line_number: 定义行号
            address: 内存地址
        """
        self.dwarf.symbol_table.add_variable(
            name=name,
            type_ref=type_name,
            location=address,
            file_path=self.source_file,
            line_number=line_number
        )
    
    def finalize(self) -> Dict[str, Any]:
        """
        完成调试信息生成
        
        Returns:
            调试信息字典
        """
        # 生成调试信息
        debug_info = self.dwarf.generate_debug_sections()
        
        # 保存到文件
        if self.output_file:
            self.dwarf.save_to_file(self.output_file)
        
        return debug_info


# 使用示例
if __name__ == '__main__':
    # 创建调试信息生成器
    debug_gen = DebugInfoGenerator("test.zhc", "test.debug.json")
    
    # 添加函数
    debug_gen.add_function(
        name="主函数",
        start_line=1,
        end_line=10,
        start_addr=0x1000,
        end_addr=0x1050,
        return_type="整数型"
    )
    
    # 添加变量
    debug_gen.add_variable(
        name="x",
        type_name="整数型",
        line_number=2,
        address=0x2000
    )
    
    # 生成调试信息
    debug_info = debug_gen.finalize()
    
    print("调试信息生成完成：")
    print(json.dumps(debug_info, indent=2, ensure_ascii=False))