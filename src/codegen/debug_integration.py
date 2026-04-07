"""
调试信息集成模块

将 DWARF 调试信息生成器集成到编译流程中。
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from zhc.debug.debug_generator import (
    DWARFGenerator,
    DebugInfoGenerator as CoreDebugInfoGenerator,
    LineNumberTable,
    DebugSymbolTable,
    TypeInfoGenerator,
)


class DebugInfoManager:
    """
    调试信息管理器
    
    协调 DWARF 调试信息生成与编译流程的集成。
    """
    
    def __init__(self, source_file: str, output_file: str, enable_debug: bool = True):
        """
        初始化调试信息管理器
        
        Args:
            source_file: 源文件路径
            output_file: 输出文件路径
            enable_debug: 是否启用调试信息生成
        """
        self.source_file = source_file
        self.output_file = output_file
        self.enable_debug = enable_debug
        
        # 核心组件
        self.generator: Optional[CoreDebugInfoGenerator] = None
        
        if enable_debug:
            self.generator = CoreDebugInfoGenerator(source_file, output_file)
    
    def add_function(self,
                    name: str,
                    start_line: int,
                    end_line: int,
                    start_addr: int,
                    end_addr: int,
                    return_type: str = "void",
                    parameters: Optional[List[Dict]] = None) -> None:
        """
        添加函数调试信息
        
        Args:
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表
        """
        if not self.enable_debug or not self.generator:
            return
        
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
        if not self.enable_debug or not self.generator:
            return
        
        self.generator.add_variable(
            name=name,
            type_name=type_name,
            line_number=line_number,
            address=address
        )
    
    def map_line(self, line_number: int, address: int) -> None:
        """
        映射源码行号到机器码地址
        
        Args:
            line_number: 源码行号
            address: 机器码地址
        """
        if not self.enable_debug or not self.generator:
            return
        
        self.generator.map_line(line_number, address)
    
    def add_type(self,
                name: str,
                kind: str,
                size: int,
                **kwargs) -> None:
        """
        添加类型信息
        
        Args:
            name: 类型名
            kind: 类型种类 (base, struct, enum, array, pointer)
            size: 类型大小（字节）
            **kwargs: 其他属性
        """
        if not self.enable_debug or not self.generator:
            return
        
        # 使用 TypeInfoGenerator 添加类型
        self.generator.dwarf.type_info.add_base_type(name, size, kwargs.get('encoding', 0))
    
    def finalize(self) -> Dict[str, Any]:
        """
        完成调试信息生成
        
        Returns:
            调试信息字典
        """
        if not self.enable_debug or not self.generator:
            return {}
        
        return self.generator.finalize()
    
    def generate_dwarf_sections(self) -> Dict[str, bytes]:
        """
        生成 DWARF 调试段
        
        Returns:
            各调试段的字节序列字典
        """
        if not self.enable_debug or not self.generator:
            return {}
        
        return self.generator.dwarf.generate_debug_info()
    
    def is_enabled(self) -> bool:
        """检查调试信息是否启用"""
        return self.enable_debug


def create_debug_manager(source_file: str,
                        output_file: str,
                        enable_debug: bool = True) -> DebugInfoManager:
    """
    创建调试信息管理器
    
    Args:
        source_file: 源文件路径
        output_file: 输出文件路径
        enable_debug: 是否启用调试信息生成
    
    Returns:
        DebugInfoManager 实例
    """
    return DebugInfoManager(source_file, output_file, enable_debug)