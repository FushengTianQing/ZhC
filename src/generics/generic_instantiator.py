"""
泛型实例化器
Generic Instantiator for ZHC Language

将泛型定义实例化为具体类型和函数
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class InstantiatedType:
    """实例化的类型"""
    original_name: str  # 原始泛型名
    type_args: Dict[str, str]  # 类型参数映射
    instantiated_name: str  # 实例化后的名称
    code: str  # 实例化后的代码
    line_number: int = 0


@dataclass
class InstantiatedFunction:
    """实例化的函数"""
    original_name: str  # 原始泛型函数名
    type_args: Dict[str, str]  # 类型参数映射
    instantiated_name: str  # 实例化后的名称
    code: str  # 实例化后的代码
    line_number: int = 0


class GenericInstantiator:
    """泛型实例化器"""
    
    def __init__(self):
        """初始化实例化器"""
        self.instantiated_types: Dict[str, InstantiatedType] = {}
        self.instantiated_functions: Dict[str, InstantiatedFunction] = {}
        self.name_counter: Dict[str, int] = {}  # 用于生成唯一名称
    
    def instantiate_type(
        self,
        generic_type,  # GenericType
        type_args: Dict[str, str]
    ) -> InstantiatedType:
        """
        实例化泛型类型
        
        Args:
            generic_type: 泛型类型定义
            type_args: 类型参数映射
            
        Returns:
            实例化后的类型
        """
        # 生成实例化名称
        # 列表<整数型> -> 列表_整数型
        type_suffix = '_'.join(type_args.values())
        instantiated_name = f"{generic_type.name}_{type_suffix}"
        
        # 检查是否已经实例化
        if instantiated_name in self.instantiated_types:
            return self.instantiated_types[instantiated_name]
        
        # 实例化类型体
        code = generic_type.instantiate(type_args)
        
        # 构建完整类型定义
        full_code = f"结构体 {instantiated_name} {{\n{code}\n}};"
        
        # 创建实例化类型对象
        instantiated_type = InstantiatedType(
            original_name=generic_type.name,
            type_args=type_args,
            instantiated_name=instantiated_name,
            code=full_code,
            line_number=generic_type.line_number
        )
        
        # 记录实例化结果
        self.instantiated_types[instantiated_name] = instantiated_type
        
        return instantiated_type
    
    def instantiate_function(
        self,
        generic_func,  # GenericFunction
        type_args: Dict[str, str]
    ) -> InstantiatedFunction:
        """
        实例化泛型函数
        
        Args:
            generic_func: 泛型函数定义
            type_args: 类型参数映射
            
        Returns:
            实例化后的函数
        """
        # 生成实例化名称
        # 最大值<整数型> -> 最大值_整数型
        type_suffix = '_'.join(type_args.values())
        instantiated_name = f"{generic_func.name}_{type_suffix}"
        
        # 检查是否已经实例化
        if instantiated_name in self.instantiated_functions:
            return self.instantiated_functions[instantiated_name]
        
        # 实例化函数
        code = generic_func.instantiate(type_args)
        
        # 创建实例化函数对象
        instantiated_func = InstantiatedFunction(
            original_name=generic_func.name,
            type_args=type_args,
            instantiated_name=instantiated_name,
            code=code,
            line_number=generic_func.line_number
        )
        
        # 记录实例化结果
        self.instantiated_functions[instantiated_name] = instantiated_func
        
        return instantiated_func
    
    def parse_type_application(self, type_expr: str) -> Tuple[str, Dict[str, str]]:
        """
        解析类型应用表达式
        
        Args:
            type_expr: 类型表达式（如"列表<整数型>"）
            
        Returns:
            (泛型名, 类型参数映射)
        """
        # 匹配泛型应用
        # 列表<整数型> 或 字典<字符串型, 整数型>
        match = re.match(r'(\w+)<([^>]+)>', type_expr)
        
        if not match:
            return type_expr, {}
        
        generic_name = match.group(1)
        args_str = match.group(2)
        
        # 解析类型参数
        # 支持多参数: T, U, V
        args = [a.strip() for a in args_str.split(',')]
        
        # 为参数生成默认名称（T, U, V...）
        type_args = {}
        param_names = ['T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        
        for i, arg in enumerate(args):
            if i < len(param_names):
                type_args[param_names[i]] = arg
            else:
                type_args[f'T{i}'] = arg
        
        return generic_name, type_args
    
    def generate_all_instances(
        self,
        generic_types: Dict,  # Dict[str, GenericType]
        generic_functions: Dict,  # Dict[str, GenericFunction]
        type_applications: List[Tuple[str, Dict[str, str]]]
    ) -> Tuple[List[str], List[str]]:
        """
        生成所有实例化代码
        
        Args:
            generic_types: 泛型类型字典
            generic_functions: 泛型函数字典
            type_applications: 类型应用列表
            
        Returns:
            (类型定义列表, 函数定义列表)
        """
        type_definitions = []
        function_definitions = []
        
        for generic_name, type_args in type_applications:
            # 实例化类型
            if generic_name in generic_types:
                generic_type = generic_types[generic_name]
                instantiated_type = self.instantiate_type(generic_type, type_args)
                type_definitions.append(instantiated_type.code)
            
            # 实例化函数
            if generic_name in generic_functions:
                generic_func = generic_functions[generic_name]
                instantiated_func = self.instantiate_function(generic_func, type_args)
                function_definitions.append(instantiated_func.code)
        
        return type_definitions, function_definitions
    
    def get_instantiated_name(
        self,
        original_name: str,
        type_args: Dict[str, str]
    ) -> str:
        """
        获取实例化后的名称
        
        Args:
            original_name: 原始名称
            type_args: 类型参数映射
            
        Returns:
            实例化后的名称
        """
        if not type_args:
            return original_name
        
        type_suffix = '_'.join(type_args.values())
        return f"{original_name}_{type_suffix}"
    
    def is_instantiated(self, name: str) -> bool:
        """
        检查名称是否已实例化
        
        Args:
            name: 名称
            
        Returns:
            是否已实例化
        """
        return name in self.instantiated_types or name in self.instantiated_functions
    
    def get_all_instantiated_names(self) -> Tuple[Set[str], Set[str]]:
        """
        获取所有实例化名称
        
        Returns:
            (实例化类型名称集合, 实例化函数名称集合)
        """
        type_names = set(self.instantiated_types.keys())
        func_names = set(self.instantiated_functions.keys())
        
        return type_names, func_names
    
    def clear(self):
        """清空所有实例化结果"""
        self.instantiated_types.clear()
        self.instantiated_functions.clear()
        self.name_counter.clear()
    
    def generate_c_code(self) -> str:
        """
        生成完整的C代码
        
        Returns:
            C代码字符串
        """
        code_parts = []
        
        # 添加类型定义
        for inst_type in self.instantiated_types.values():
            code_parts.append(inst_type.code)
            code_parts.append('')
        
        # 添加函数定义
        for inst_func in self.instantiated_functions.values():
            code_parts.append(inst_func.code)
            code_parts.append('')
        
        return '\n'.join(code_parts)
    
    def generate_header(self) -> str:
        """
        生成头文件声明
        
        Returns:
            头文件内容
        """
        header_parts = ['/* 泛型实例化声明 */', '']
        
        # 添加类型声明
        for inst_type in self.instantiated_types.values():
            header_parts.append(f"结构体 {inst_type.instantiated_name};")
        
        # 添加函数声明
        for inst_func in self.instantiated_functions.values():
            # 提取函数签名
            func_sig = inst_func.code.split('{')[0].strip()
            header_parts.append(func_sig + ';')
        
        return '\n'.join(header_parts)
    
    def validate_instantiation(
        self,
        generic_def,  # GenericType or GenericFunction
        type_args: Dict[str, str]
    ) -> List[str]:
        """
        验证实例化是否有效
        
        Args:
            generic_def: 泛型定义
            type_args: 类型参数映射
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查类型参数数量
        expected_params = generic_def.get_type_param_names()
        actual_params = list(type_args.keys())
        
        if len(actual_params) != len(expected_params):
            errors.append(
                f"类型参数数量不匹配: 期望 {len(expected_params)}, 实际 {len(actual_params)}"
            )
        
        # 检查类型参数名称
        for param_name in actual_params:
            if param_name not in expected_params:
                errors.append(f"未知的类型参数: {param_name}")
        
        # 检查类型参数约束（如果有GenericParser）
        # 这里简化实现，实际应该在parser中检查
        
        return errors
    
    def merge_instantiator(self, other: 'GenericInstantiator'):
        """
        合并另一个实例化器
        
        Args:
            other: 另一个实例化器
        """
        self.instantiated_types.update(other.instantiated_types)
        self.instantiated_functions.update(other.instantiated_functions)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取实例化统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'instantiated_types': len(self.instantiated_types),
            'instantiated_functions': len(self.instantiated_functions),
            'total': len(self.instantiated_types) + len(self.instantiated_functions)
        }