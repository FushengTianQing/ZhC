"""
泛型解析器
Generic Parser for ZHC Language

解析泛型类型、泛型函数和泛型类定义
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum


def substitute_type_params(text: str, type_args: Dict[str, str]) -> str:
    """
    替换文本中的类型参数 - 通用辅助函数
    
    Args:
        text: 包含类型参数的文本
        type_args: 类型参数映射（如{"T": "整数型"}）
        
    Returns:
        替换后的文本
    """
    result = text
    for param_name, actual_type in type_args.items():
        pattern = r'\b' + re.escape(param_name) + r'\b'
        result = re.sub(pattern, actual_type, result)
    return result


class GenericConstraint(Enum):
    """泛型约束类型"""
    NONE = "无约束"
    NUMBER = "数值类型"  # 整数型、浮点型等
    COMPARABLE = "可比较"  # 支持比较运算
    ADDABLE = "可加法"  # 支持+运算
    ITERABLE = "可迭代"  # 支持迭代
    CALLABLE = "可调用"  # 函数类型


@dataclass
class TypeParameter:
    """类型参数"""
    name: str  # 类型参数名（如"T"、"U"）
    constraints: List[GenericConstraint] = field(default_factory=list)
    default_type: Optional[str] = None  # 默认类型
    
    def has_constraint(self, constraint: GenericConstraint) -> bool:
        """检查是否有指定约束"""
        return constraint in self.constraints
    
    def to_c_code(self) -> str:
        """转换为C代码（注释形式）"""
        if not self.constraints:
            return f"/* 类型参数 {self.name} */"
        
        constraint_strs = [c.value for c in self.constraints]
        return f"/* 类型参数 {self.name}: {', '.join(constraint_strs)} */"


@dataclass
class GenericType:
    """泛型类型定义"""
    name: str  # 类型名（如"列表"）
    type_params: List[TypeParameter]  # 类型参数列表
    body: str  # 类型体定义
    line_number: int = 0  # 定义所在行号
    
    def get_type_param_names(self) -> List[str]:
        """获取所有类型参数名"""
        return [tp.name for tp in self.type_params]
    
    def instantiate(self, type_args: Dict[str, str]) -> str:
        """
        实例化泛型类型
        
        Args:
            type_args: 类型参数映射（如{"T": "整数型"}）
            
        Returns:
            实例化后的代码
        """
        return substitute_type_params(self.body, type_args)


@dataclass
class GenericFunction:
    """泛型函数定义"""
    name: str  # 函数名
    return_type: str  # 返回类型
    type_params: List[TypeParameter]  # 类型参数列表
    parameters: List[Tuple[str, str]]  # 参数列表 [(类型, 名称)]
    body: str  # 函数体
    line_number: int = 0  # 定义所在行号
    
    def get_type_param_names(self) -> List[str]:
        """获取所有类型参数名"""
        return [tp.name for tp in self.type_params]
    
    def instantiate(self, type_args: Dict[str, str]) -> str:
        """
        实例化泛型函数
        
        Args:
            type_args: 类型参数映射
            
        Returns:
            实例化后的代码
        """
        # 生成实例化函数名
        type_suffix = '_'.join(type_args.values())
        instantiated_name = f"{self.name}_{type_suffix}"
        
        # 替换返回类型中的类型参数
        result_type = substitute_type_params(self.return_type, type_args)
        
        # 替换参数类型中的类型参数
        params = []
        for param_type, param_name in self.parameters:
            actual_param_type = substitute_type_params(param_type, type_args)
            params.append(f"{actual_param_type} {param_name}")
        
        # 替换函数体中的类型参数
        body = substitute_type_params(self.body, type_args)
        
        # 构建函数定义（使用实例化名称）
        func_def = f"{result_type} {instantiated_name}({', '.join(params)}) {{\n{body}\n}}"
        
        return func_def


class GenericParser:
    """泛型解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.generic_types: Dict[str, GenericType] = {}
        self.generic_functions: Dict[str, GenericFunction] = {}
        self.current_line = 0
    
    def parse_generic_type(self, code: str) -> Optional[GenericType]:
        """
        解析泛型类型定义
        
        语法：
        泛型类型 列表<类型 T> {
            T 数据[100];
            整数型 长度;
        }
        
        Args:
            code: 源代码
            
        Returns:
            解析出的泛型类型定义
        """
        # 匹配泛型类型定义
        pattern = r'泛型类型\s+(\w+)\s*<([^>]+)>\s*\{([^}]+)\}'
        match = re.search(pattern, code, re.MULTILINE | re.DOTALL)
        
        if not match:
            return None
        
        type_name = match.group(1)
        params_str = match.group(2).strip()
        body = match.group(3).strip()
        
        # 解析类型参数
        type_params = self._parse_type_parameters(params_str)
        
        # 计算行号
        line_number = code[:match.start()].count('\n') + 1
        
        generic_type = GenericType(
            name=type_name,
            type_params=type_params,
            body=body,
            line_number=line_number
        )
        
        # 记录泛型类型
        self.generic_types[type_name] = generic_type
        
        return generic_type
    
    def parse_generic_function(self, code: str) -> Optional[GenericFunction]:
        """
        解析泛型函数定义
        
        语法：
        泛型函数 T 最大值<类型 T>(T a, T b) {
            如果 (a > b) {
                返回 a;
            } 否则 {
                返回 b;
            }
        }
        
        Args:
            code: 源代码
            
        Returns:
            解析出的泛型函数定义
        """
        # 匹配泛型函数定义
        pattern = r'泛型函数\s+(\w+)\s+(\w+)\s*<([^>]+)>\s*\(([^)]*)\)\s*\{([^}]+)\}'
        match = re.search(pattern, code, re.MULTILINE | re.DOTALL)
        
        if not match:
            return None
        
        return_type = match.group(1)
        func_name = match.group(2)
        params_str = match.group(3).strip()
        args_str = match.group(4).strip()
        body = match.group(5).strip()
        
        # 解析类型参数
        type_params = self._parse_type_parameters(params_str)
        
        # 解析函数参数
        parameters = self._parse_parameters(args_str)
        
        # 计算行号
        line_number = code[:match.start()].count('\n') + 1
        
        generic_func = GenericFunction(
            name=func_name,
            return_type=return_type,
            type_params=type_params,
            parameters=parameters,
            body=body,
            line_number=line_number
        )
        
        # 记录泛型函数
        self.generic_functions[func_name] = generic_func
        
        return generic_func
    
    def _parse_type_parameters(self, params_str: str) -> List[TypeParameter]:
        """
        解析类型参数列表
        
        Args:
            params_str: 参数字符串（如"类型 T, 类型 U: 数值类型"）
            
        Returns:
            类型参数列表
        """
        type_params = []
        
        # 分割参数
        params = [p.strip() for p in params_str.split(',')]
        
        for param in params:
            # 解析类型参数
            # 格式: "类型 T" 或 "类型 T: 约束"
            if ':' in param:
                # 有约束
                parts = param.split(':', 1)
                param_def = parts[0].strip()
                constraint_str = parts[1].strip()
                
                # 解析约束
                constraints = self._parse_constraints(constraint_str)
            else:
                # 无约束
                param_def = param.strip()
                constraints = []
            
            # 提取参数名
            # "类型 T" -> "T"
            if param_def.startswith('类型'):
                param_name = param_def[2:].strip()
            else:
                param_name = param_def
            
            type_param = TypeParameter(
                name=param_name,
                constraints=constraints
            )
            type_params.append(type_param)
        
        return type_params
    
    def _parse_constraints(self, constraint_str: str) -> List[GenericConstraint]:
        """
        解析约束列表
        
        Args:
            constraint_str: 约束字符串（如"数值类型, 可比较"）
            
        Returns:
            约束列表
        """
        constraints = []
        
        # 约束映射
        constraint_map = {
            '数值类型': GenericConstraint.NUMBER,
            '可比较': GenericConstraint.COMPARABLE,
            '可加法': GenericConstraint.ADDABLE,
            '可迭代': GenericConstraint.ITERABLE,
            '可调用': GenericConstraint.CALLABLE,
        }
        
        # 分割约束
        parts = [p.strip() for p in constraint_str.split(',')]
        
        for part in parts:
            if part in constraint_map:
                constraints.append(constraint_map[part])
        
        return constraints
    
    def _parse_parameters(self, args_str: str) -> List[Tuple[str, str]]:
        """
        解析函数参数列表
        
        Args:
            args_str: 参数字符串（如"T a, T b"）
            
        Returns:
            参数列表 [(类型, 名称), ...]
        """
        parameters = []
        
        if not args_str:
            return parameters
        
        # 分割参数
        args = [a.strip() for a in args_str.split(',')]
        
        for arg in args:
            # 解析参数 "类型 名称"
            parts = arg.split(None, 1)
            if len(parts) == 2:
                param_type = parts[0]
                param_name = parts[1]
                parameters.append((param_type, param_name))
        
        return parameters
    
    def find_type_parameter_usage(self, code: str, type_param: str) -> List[int]:
        """
        查找类型参数的使用位置
        
        Args:
            code: 源代码
            type_param: 类型参数名
            
        Returns:
            使用位置的行号列表
        """
        lines = code.split('\n')
        usage_lines = []
        
        for i, line in enumerate(lines, 1):
            # 查找类型参数使用
            pattern = r'\b' + re.escape(type_param) + r'\b'
            if re.search(pattern, line):
                usage_lines.append(i)
        
        return usage_lines
    
    def validate_constraints(self, type_args: Dict[str, str]) -> List[str]:
        """
        验证类型参数约束
        
        Args:
            type_args: 类型参数映射
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查每个泛型定义的约束
        for func_name, generic_func in self.generic_functions.items():
            for type_param in generic_func.type_params:
                # 获取实际类型
                actual_type = type_args.get(type_param.name)
                if not actual_type:
                    continue
                
                # 检查约束
                for constraint in type_param.constraints:
                    if not self._check_constraint(actual_type, constraint):
                        errors.append(
                            f"类型 '{actual_type}' 不满足约束 '{constraint.value}'"
                        )
        
        return errors
    
    def _check_constraint(self, type_name: str, constraint: GenericConstraint) -> bool:
        """
        检查类型是否满足约束 - 使用 dispatch table 模式
        
        Args:
            type_name: 类型名
            constraint: 约束
            
        Returns:
            是否满足约束
        """
        # 数值类型集合
        number_types = {'整数型', '浮点型', '双精度型', '短整数型', '长整数型'}
        
        # 约束检查函数映射表
        constraint_checkers = {
            GenericConstraint.NUMBER: lambda t: t in number_types,
            GenericConstraint.COMPARABLE: lambda t: True,  # 简化实现，假设所有类型都可比较
            GenericConstraint.ADDABLE: lambda t: t in number_types or t == '字符串型',
            GenericConstraint.ITERABLE: lambda t: '数组' in t or '[' in t,
            GenericConstraint.CALLABLE: lambda t: '(' in t or '函数' in t,
        }
        
        # 使用 dispatch table 查找并执行检查函数
        checker = constraint_checkers.get(constraint)
        if checker:
            return checker(type_name)
        
        return True  # 默认满足（包括 GenericConstraint.NONE）
    
    def get_all_generic_names(self) -> Tuple[Set[str], Set[str]]:
        """
        获取所有泛型名称
        
        Returns:
            (泛型类型名称集合, 泛型函数名称集合)
        """
        type_names = set(self.generic_types.keys())
        func_names = set(self.generic_functions.keys())
        
        return type_names, func_names
    
    def clear(self):
        """清空所有解析结果"""
        self.generic_types.clear()
        self.generic_functions.clear()