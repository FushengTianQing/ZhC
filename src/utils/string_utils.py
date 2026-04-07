# -*- coding: utf-8 -*-
"""
字符串处理工具函数

提供常用的字符串处理功能，减少重复代码。

作者：远
日期：2026-04-07
"""

from typing import List, Optional


def normalize_whitespace(text: str) -> str:
    """
    规范化空白字符（将多个连续空白合并为单个空格）
    
    Args:
        text: 输入文本
        
    Returns:
        规范化后的文本
        
    Example:
        >>> normalize_whitespace("  hello   world  ")
        ' hello world '
        >>> normalize_whitespace("hello\\t\\tworld")
        ' hello world'
    """
    import re
    # 将所有连续空白字符（包括空格、制表符、换行符）替换为单个空格
    return re.sub(r'\s+', ' ', text).strip()


def strip_lines(text: str, skip_empty: bool = True) -> List[str]:
    """
    将文本按行分割并去除每行的空白
    
    Args:
        text: 输入文本
        skip_empty: 是否跳过空行，默认 True
        
    Returns:
        处理后的行列表
        
    Example:
        >>> strip_lines("  line1  \\n  line2  \\n")
        ['line1', 'line2']
        >>> strip_lines("line1\\n\\nline2", skip_empty=False)
        ['line1', '', 'line2']
    """
    lines = [line.strip() for line in text.splitlines()]
    
    if skip_empty:
        return [line for line in lines if line]
    
    return lines


def clean_empty_lines(text: str) -> str:
    """
    清除文本中的空行
    
    Args:
        text: 输入文本
        
    Returns:
        清除空行后的文本
        
    Example:
        >>> clean_empty_lines("line1\\n\\nline2\\n\\n\\nline3")
        'line1\\nline2\\nline3'
    """
    lines = text.splitlines()
    return '\n'.join(line for line in lines if line.strip())


def indent_text(text: str, spaces: int = 4) -> str:
    """
    为文本的每一行添加缩进
    
    Args:
        text: 输入文本
        spaces: 缩进空格数，默认 4
        
    Returns:
        添加缩进后的文本
        
    Example:
        >>> indent_text("line1\\nline2", 4)
        '    line1\\n    line2'
    """
    indent = ' ' * spaces
    lines = text.splitlines()
    return '\n'.join(f"{indent}{line}" if line.strip() else line for line in lines)


def remove_prefix(text: str, prefix: str) -> str:
    """
    移除字符串前缀（兼容 Python 3.9+）
    
    Args:
        text: 输入字符串
        prefix: 要移除的前缀
        
    Returns:
        移除前缀后的字符串
        
    Example:
        >>> remove_prefix("hello_world", "hello_")
        'world'
        >>> remove_prefix("hello_world", "xyz")
        'hello_world'
    """
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def remove_suffix(text: str, suffix: str) -> str:
    """
    移除字符串后缀
    
    Args:
        text: 输入字符串
        suffix: 要移除的后缀
        
    Returns:
        移除后缀后的字符串
        
    Example:
        >>> remove_suffix("hello.py", ".py")
        'hello'
        >>> remove_suffix("hello", ".py")
        'hello'
    """
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text


def split_by_commas(text: str) -> List[str]:
    """
    按逗号分割字符串并清理空白
    
    Args:
        text: 输入字符串
        
    Returns:
        分割后的字符串列表
        
    Example:
        >>> split_by_commas("a, b, c")
        ['a', 'b', 'c']
        >>> split_by_commas("x,y , z")
        ['x', 'y', 'z']
    """
    return [item.strip() for item in text.split(',') if item.strip()]


def camel_to_snake(name: str) -> str:
    """
    将驼峰命名转换为蛇形命名
    
    Args:
        name: 驼峰命名的字符串
        
    Returns:
        蛇形命名的字符串
        
    Example:
        >>> camel_to_snake("CamelCase")
        'camel_case'
        >>> camel_to_snake("getHTTPResponse")
        'get_http_response'
    """
    import re
    
    # 在大写字母前插入下划线
    s1 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    # 在小写字母和数字后的大写字母前插入下划线
    s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
    
    return s2.lower()


def snake_to_camel(name: str, capitalize_first: bool = False) -> str:
    """
    将蛇形命名转换为驼峰命名
    
    Args:
        name: 蛇形命名的字符串
        capitalize_first: 是否首字母大写，默认 False
        
    Returns:
        驼峰命名的字符串
        
    Example:
        >>> snake_to_camel("snake_case")
        'snakeCase'
        >>> snake_to_camel("snake_case", True)
        'SnakeCase'
    """
    components = name.split('_')
    
    if capitalize_first:
        return ''.join(word.capitalize() for word in components)
    else:
        return components[0] + ''.join(word.capitalize() for word in components[1:])


def truncate(text: str, max_length: int, suffix: str = '...') -> str:
    """
    截断字符串到指定长度
    
    Args:
        text: 输入字符串
        max_length: 最大长度
        suffix: 截断后添加的后缀，默认 '...'
        
    Returns:
        截断后的字符串
        
    Example:
        >>> truncate("Hello World", 8)
        'Hello...'
        >>> truncate("Hi", 8)
        'Hi'
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_table(headers: List[str], rows: List[List[str]], padding: int = 2) -> str:
    """
    格式化表格输出
    
    Args:
        headers: 表头列表
        rows: 数据行列表
        padding: 列之间的空格数，默认 2
        
    Returns:
        格式化后的表格字符串
        
    Example:
        >>> print(format_table(['Name', 'Age'], [['Alice', '30'], ['Bob', '25']]))
        Name  Age
        Alice 30
        Bob   25
    """
    if not headers or not rows:
        return ''
    
    # 计算每列的最大宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 格式化表头
    header_line = ' ' * padding.join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    
    # 格式化分隔线
    separator = '-'.join('-' * w for w in col_widths)
    
    # 格式化数据行
    data_lines = []
    for row in rows:
        line = ' ' * padding.join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        data_lines.append(line)
    
    return '\n'.join([header_line, separator] + data_lines)