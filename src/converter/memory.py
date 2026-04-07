#!/usr/bin/env python3
"""
Day 21: 基础内存语法转换器
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MemoryStatement:
    operation: str
    type_name: str
    var_name: str
    line_number: int
    size: Optional[int] = None


class MemorySyntaxConverter:
    TYPE_MAP = {
        '整数型': 'int', '浮点型': 'float', '双精度型': 'double',
        '字符型': 'char', '字符串型': 'char*', '空型': 'void',
    }

    def __init__(self):
        self.statements: List[MemoryStatement] = []

    def parse_new(self, line: str, line_num: int) -> Optional[MemoryStatement]:
        pattern = r'新建\s+(\w+)\s+(\w+)\s*;'
        match = re.search(pattern, line)
        if not match:
            return None
        type_c = self.TYPE_MAP.get(match.group(1), match.group(1))
        stmt = MemoryStatement('new', type_c, match.group(2), line_num)
        self.statements.append(stmt)
        return stmt

    def parse_array_new(self, line: str, line_num: int) -> Optional[MemoryStatement]:
        pattern = r'新建\s+(\w+)\s+(\w+)\[(\d+)\]\s*;'
        match = re.search(pattern, line)
        if not match:
            return None
        type_c = self.TYPE_MAP.get(match.group(1), match.group(1))
        stmt = MemoryStatement('array_new', type_c, match.group(2), line_num, int(match.group(3)))
        self.statements.append(stmt)
        return stmt

    def parse_delete(self, line: str, line_num: int) -> Optional[MemoryStatement]:
        pattern = r'删除\s+(\w+)\s*;'
        match = re.search(pattern, line)
        if not match:
            return None
        stmt = MemoryStatement('delete', '', match.group(1), line_num)
        self.statements.append(stmt)
        return stmt

    def parse_array_delete(self, line: str, line_num: int) -> Optional[MemoryStatement]:
        pattern = r'删除数组\s+(\w+)\s*;'
        match = re.search(pattern, line)
        if not match:
            return None
        stmt = MemoryStatement('array_delete', '', match.group(1), line_num)
        self.statements.append(stmt)
        return stmt

    def convert_to_c(self, stmt: MemoryStatement) -> str:
        if stmt.operation == 'new':
            return f"{stmt.type_name}* {stmt.var_name} = ({stmt.type_name}*)malloc(sizeof({stmt.type_name}));"
        elif stmt.operation == 'array_new':
            return f"{stmt.type_name}* {stmt.var_name} = ({stmt.type_name}*)malloc({stmt.size} * sizeof({stmt.type_name}));"
        elif stmt.operation == 'delete':
            return f"free({stmt.var_name});"
        elif stmt.operation == 'array_delete':
            return f"free({stmt.var_name});"
        return ""

    def convert_line(self, line: str, line_num: int) -> Optional[str]:
        for parser in [self.parse_new, self.parse_array_new, self.parse_delete, self.parse_array_delete]:
            stmt = parser(line, line_num)
            if stmt:
                return self.convert_to_c(stmt)
        return None

    def get_statistics(self):
        return {
            'total': len(self.statements),
            'new_count': sum(1 for s in self.statements if s.operation == 'new'),
            'array_new_count': sum(1 for s in self.statements if s.operation == 'array_new'),
            'delete_count': sum(1 for s in self.statements if s.operation == 'delete'),
            'array_delete_count': sum(1 for s in self.statements if s.operation == 'array_delete'),
        }


if __name__ == '__main__':
    print("=== 内存语法转换测试 ===")
    c = MemorySyntaxConverter()

    tests = [
        ("新建 整数型 ptr;", 1),
        ("新建 整数型 arr[100];", 2),
        ("删除 ptr;", 3),
        ("删除数组 arr;", 4),
    ]

    for line, num in tests:
        result = c.convert_line(line, num)
        if result:
            print(f"行{num}: {line} -> {result}")