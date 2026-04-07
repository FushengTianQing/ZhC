"""
C 后端调试信息监听器

将调试信息事件转换为 DWARF 格式，供 GDB/LLDB 使用。
"""

from typing import Dict, List, Optional, Any

from zhc.debug.debug_generator import (
    DWARFGenerator,
    DebugInfoGenerator as CoreDebugInfoGenerator,
    LineNumberTable,
    DebugSymbolTable,
    TypeInfoGenerator,
)


class CDebugListener:
    """
    C 后端调试信息监听器
    
    实现 DebugListener 协议，将调试信息事件转换为 DWARF 格式。
    """
    
    def __init__(self, source_file: str, output_file: str = "debug.json"):
        """
        初始化 C 后端调试监听器
        
        Args:
            source_file: 源文件路径
            output_file: 输出文件路径
        """
        self.source_file = source_file
        self.output_file = output_file
        
        # 核心 DWARF 生成器
        self.generator: CoreDebugInfoGenerator = CoreDebugInfoGenerator(
            source_file, output_file
        )
    
    # ========== DebugListener 协议实现 ==========
    
    def on_compile_unit(self,
                        name: str,
                        source_file: str,
                        comp_dir: str) -> None:
        """
        编译单元开始事件
        
        Args:
            name: 编译单元名称
            source_file: 源文件路径
            comp_dir: 编译目录
        """
        self.generator.dwarf.add_compile_unit(name, source_file, comp_dir)
    
    def on_function(self,
                    name: str,
                    start_line: int,
                    end_line: int,
                    start_addr: int,
                    end_addr: int,
                    return_type: str = "void",
                    parameters: Optional[List[Dict]] = None) -> None:
        """
        函数定义事件
        
        Args:
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表
        """
        self.generator.add_function(
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_addr=start_addr,
            end_addr=end_addr,
            return_type=return_type
        )
        
        # 添加参数
        if parameters:
            for param in parameters:
                self.generator.add_variable(
                    name=param.get('name', ''),
                    type_name=param.get('type', 'void'),
                    line_number=start_line,
                    address=param.get('location', 0)
                )
    
    def on_variable(self,
                    name: str,
                    type_name: str,
                    line_number: int,
                    address: int,
                    is_parameter: bool = False) -> None:
        """
        变量定义事件
        
        Args:
            name: 变量名
            type_name: 类型名
            line_number: 定义行号
            address: 内存地址
            is_parameter: 是否为函数参数
        """
        self.generator.add_variable(
            name=name,
            type_name=type_name,
            line_number=line_number,
            address=address
        )
    
    def on_line_mapping(self,
                        line_number: int,
                        address: int,
                        column: int = 0,
                        file_index: int = 0) -> None:
        """
        行号映射事件
        
        Args:
            line_number: 源码行号
            address: 机器码地址
            column: 列号
            file_index: 文件索引
        """
        self.generator.map_line(line_number, address)
    
    def on_type_definition(self,
                           type_name: str,
                           type_kind: str,
                           byte_size: int,
                           members: Optional[List[Dict]] = None,
                           encoding: str = "") -> None:
        """
        类型定义事件
        
        Args:
            type_name: 类型名
            type_kind: 类型种类
            byte_size: 字节大小
            members: 成员列表
            encoding: 编码方式
        """
        type_info = self.generator.dwarf.type_info
        
        if type_kind == "base":
            # 基本类型
            type_info.add_type(
                type_name=type_name,
                type_tag="DW_TAG_base_type",
                byte_size=byte_size,
                encoding=encoding
            )
        elif type_kind == "struct":
            # 结构体类型
            type_info.add_struct_type(
                type_name=type_name,
                members=members or [],
                byte_size=byte_size
            )
        elif type_kind == "pointer":
            # 指针类型
            base_type = members[0].get('base_type', 'void') if members else 'void'
            type_info.add_pointer_type(
                type_name=type_name,
                base_type=base_type,
                byte_size=byte_size
            )
        elif type_kind == "array":
            # 数组类型
            elem_type = members[0].get('element_type', 'int') if members else 'int'
            elem_size = members[0].get('element_size', 4) if members else 4
            array_size = members[0].get('array_size', 0) if members else 0
            type_info.add_array_type(
                type_name=type_name,
                element_type=elem_type,
                array_size=array_size,
                element_size=elem_size
            )
    
    def on_finalize(self) -> Dict[str, Any]:
        """
        完成事件
        
        Returns:
            DWARF 调试信息字典
        """
        return self.generator.finalize()
    
    def on_reset(self) -> None:
        """
        重置事件
        
        清空当前调试信息。
        """
        self.generator = CoreDebugInfoGenerator(
            self.source_file, self.output_file
        )
    
    # ========== C 后端专用方法 ==========
    
    def generate_dwarf_sections(self) -> Dict[str, bytes]:
        """
        生成 DWARF 调试段
        
        Returns:
            各调试段的字节序列字典
        """
        return self.generator.dwarf.generate_debug_info()
    
    def get_line_table(self) -> LineNumberTable:
        """获取行号表"""
        return self.generator.dwarf.line_table
    
    def get_symbol_table(self) -> DebugSymbolTable:
        """获取符号表"""
        return self.generator.dwarf.symbol_table
    
    def get_type_info(self) -> TypeInfoGenerator:
        """获取类型信息生成器"""
        return self.generator.dwarf.type_info