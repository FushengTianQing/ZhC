#!/usr/bin/env python3
"""
Day 17: 运算符重载实现

功能：
1. 运算符映射规则定义
2. 运算符重载解析
3. 重载运算符C代码生成
"""

import re
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum


class OperatorType(Enum):
    """运算符类型"""
    # 算术运算符
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    NEG = "unary-"  # 负号

    # 比较运算符
    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="

    # 逻辑运算符
    AND = "&&"
    OR = "||"
    NOT = "!"

    # 位运算符
    BITAND = "&"
    BITOR = "|"
    BITXOR = "^"
    BITNOT = "~"
    LSHIFT = "<<"
    RSHIFT = ">>"

    # 赋值运算符
    ASSIGN = "="
    ADD_ASSIGN = "+="
    SUB_ASSIGN = "-="
    MUL_ASSIGN = "*="
    DIV_ASSIGN = "/="

    # 其他
    INDEX = "[]"  # 下标运算符
    CALL = "()"   # 函数调用
    MEMBER = "."  # 成员访问


# 中文运算符到符号的映射
CHINESE_OPERATOR_MAP = {
    "加": OperatorType.ADD,
    "减": OperatorType.SUB,
    "乘": OperatorType.MUL,
    "除": OperatorType.DIV,
    "取模": OperatorType.MOD,
    "负": OperatorType.NEG,

    "等于": OperatorType.EQ,
    "不等于": OperatorType.NE,
    "小于": OperatorType.LT,
    "大于": OperatorType.GT,
    "小于等于": OperatorType.LE,
    "大于等于": OperatorType.GE,

    "与": OperatorType.AND,
    "或": OperatorType.OR,
    "非": OperatorType.NOT,

    "位与": OperatorType.BITAND,
    "位或": OperatorType.BITOR,
    "位异或": OperatorType.BITXOR,
    "位反": OperatorType.BITNOT,
    "左移": OperatorType.LSHIFT,
    "右移": OperatorType.RSHIFT,

    "赋值": OperatorType.ASSIGN,
    "加等于": OperatorType.ADD_ASSIGN,
    "减等于": OperatorType.SUB_ASSIGN,
    "乘等于": OperatorType.MUL_ASSIGN,
    "除等于": OperatorType.DIV_ASSIGN,

    "下标": OperatorType.INDEX,
    "调用": OperatorType.CALL,
    "成员": OperatorType.MEMBER,
}


# 运算符到C函数的映射规则
OPERATOR_TO_C_FUNC = {
    OperatorType.ADD: ("add", "obj1 + obj2", True),
    OperatorType.SUB: ("sub", "obj1 - obj2", True),
    OperatorType.MUL: ("mul", "obj1 * obj2", True),
    OperatorType.DIV: ("div", "obj1 / obj2", True),
    OperatorType.MOD: ("mod", "obj1 % obj2", True),
    OperatorType.NEG: ("neg", "-obj", False),

    OperatorType.EQ: ("equals", "obj1 == obj2", True),
    OperatorType.NE: ("not_equals", "obj1 != obj2", True),
    OperatorType.LT: ("less_than", "obj1 < obj2", True),
    OperatorType.GT: ("greater_than", "obj1 > obj2", True),
    OperatorType.LE: ("less_equals", "obj1 <= obj2", True),
    OperatorType.GE: ("greater_equals", "obj1 >= obj2", True),

    OperatorType.AND: ("logical_and", "obj1 && obj2", True),
    OperatorType.OR: ("logical_or", "obj1 || obj2", True),
    OperatorType.NOT: ("logical_not", "!obj", False),

    OperatorType.BITAND: ("bit_and", "obj1 & obj2", True),
    OperatorType.BITOR: ("bit_or", "obj1 | obj2", True),
    OperatorType.BITXOR: ("bit_xor", "obj1 ^ obj2", True),
    OperatorType.BITNOT: ("bit_not", "~obj", False),
    OperatorType.LSHIFT: ("lshift", "obj1 << obj2", True),
    OperatorType.RSHIFT: ("rshift", "obj1 >> obj2", True),

    OperatorType.ASSIGN: ("assign", "obj1 = obj2", True),
    OperatorType.ADD_ASSIGN: ("add_assign", "obj1 += obj2", True),
    OperatorType.SUB_ASSIGN: ("sub_assign", "obj1 -= obj2", True),
    OperatorType.MUL_ASSIGN: ("mul_assign", "obj1 *= obj2", True),
    OperatorType.DIV_ASSIGN: ("div_assign", "obj1 /= obj2", True),

    OperatorType.INDEX: ("index", "obj[idx]", True),
    OperatorType.CALL: ("call", "obj(args)", True),
    OperatorType.MEMBER: ("member", "obj.member", False),
}


class OperatorOverloadInfo:
    """运算符重载信息"""
    def __init__(self, class_name: str, operator: OperatorType,
                 method_name: str, param_type: Optional[str] = None):
        self.class_name = class_name
        self.operator = operator
        self.method_name = method_name
        self.param_type = param_type  # 二元运算符时为第二个参数类型
        self.is_binary = len(method_name) > 0  # 简单判断

    def get_c_function_name(self) -> str:
        """获取C函数名"""
        return f"{self.class_name}_operator_{OPERATOR_TO_C_FUNC[self.operator][0]}"

    def generate_declaration(self) -> str:
        """生成函数声明"""
        op_info = OPERATOR_TO_C_FUNC[self.operator]
        if op_info[2]:  # 二元运算符
            return f"/* {self.operator.value} 运算符重载 */\n{self.get_c_function_name()}({self.class_name}_t *obj1, {self.param_type or self.class_name + '_t'} *obj2);"
        else:  # 一元运算符
            return f"/* {self.operator.value} 运算符重载 */\n{self.get_c_function_name()}({self.class_name}_t *obj);"


class OperatorOverloadParser:
    """运算符重载解析器"""
    def __init__(self):
        self.overloads: Dict[str, List[OperatorOverloadInfo]] = {}  # class_name -> [overloads]
        self.current_class: Optional[str] = None

    def set_current_class(self, class_name: str):
        """设置当前解析的类"""
        self.current_class = class_name
        if class_name not in self.overloads:
            self.overloads[class_name] = []

    def parse_operator_declaration(self, line: str, line_num: int) -> Optional[OperatorOverloadInfo]:
        """解析运算符重载声明"""
        if not self.current_class:
            return None

        # 匹配运算符函数声明
        # 语法: 操作符 函数名(参数类型) -> 返回类型
        # 或者: 运算符 映射名(参数类型) -> 返回类型
        pattern = r'操作符\s+(\w+)\s*\('
        match = re.search(pattern, line)
        if not match:
            return None

        op_name = match.group(1)
        if op_name not in CHINESE_OPERATOR_MAP:
            return None

        operator = CHINESE_OPERATOR_MAP[op_name]
        op_info = OPERATOR_TO_C_FUNC[operator]
        method_name = op_info[0]

        # 提取参数类型
        param_match = re.search(r'\(([^)]*)\)', line)
        param_type = param_match.group(1) if param_match else self.current_class

        overload = OperatorOverloadInfo(self.current_class, operator, method_name, param_type)
        self.overloads[self.current_class].append(overload)
        return overload

    def get_class_overloads(self, class_name: str) -> List[OperatorOverloadInfo]:
        """获取类的所有运算符重载"""
        return self.overloads.get(class_name, [])


class OperatorOverloadGenerator:
    """运算符重载代码生成器"""
    def __init__(self):
        self.parser = OperatorOverloadParser()

    def register_overload(self, class_name: str, operator: OperatorType,
                        param_type: Optional[str] = None):
        """注册运算符重载"""
        self.parser.set_current_class(class_name)
        op_info = OPERATOR_TO_C_FUNC[operator]
        method_name = op_info[0]
        overload = OperatorOverloadInfo(class_name, operator, method_name, param_type or class_name)
        if class_name not in self.parser.overloads:
            self.parser.overloads[class_name] = []
        self.parser.overloads[class_name].append(overload)

    def generate_header(self, class_name: str) -> str:
        """生成运算符重载头文件内容"""
        overloads = self.parser.get_class_overloads(class_name)
        if not overloads:
            return ""

        lines = [
            f"/* 运算符重载: {class_name} */",
            f"#ifndef {class_name.upper()}_OPERATOR_OVERLOAD_H",
            f"#define {class_name.upper()}_OPERATOR_OVERLOAD_H",
            ""
        ]

        for overload in overloads:
            lines.append(overload.generate_declaration())

        lines.extend([
            "",
            f"#endif /* {class_name.upper()}_OPERATOR_OVERLOAD_H */"
        ])
        return '\n'.join(lines)

    def generate_implementation(self, class_name: str, implementations: Dict[str, str]) -> str:
        """生成运算符重载实现"""
        overloads = self.parser.get_class_overloads(class_name)
        if not overloads:
            return ""

        lines = [
            f"/* 运算符重载实现: {class_name} */",
            ""
        ]

        for overload in overloads:
            func_name = overload.get_c_function_name()
            impl = implementations.get(func_name, f"/* TODO: implement {func_name} */")
            lines.append(f"/* {overload.operator.value} 运算符 */")
            lines.append(impl)
            lines.append("")

        return '\n'.join(lines)


# 测试
if __name__ == '__main__':
    print("=== 运算符重载测试 ===")

    generator = OperatorOverloadGenerator()

    # 注册运算符重载
    generator.register_overload('向量', OperatorType.ADD, '向量')
    generator.register_overload('向量', OperatorType.SUB, '向量')
    generator.register_overload('向量', OperatorType.MUL, 'double')  # 数乘
    generator.register_overload('向量', OperatorType.EQ, '向量')

    # 生成头文件
    print("--- 向量类的运算符重载头文件 ---")
    print(generator.generate_header('向量'))

    # 生成实现
    implementations = {
        '向量_operator_add': '''向量_t* 向量_operator_add(向量_t *v1, 向量_t *v2) {
    向量_t *result = (向量_t*)malloc(sizeof(向量_t));
    result->x = v1->x + v2->x;
    result->y = v1->y + v2->y;
    return result;
}''',
        '向量_operator_sub': '''向量_t* 向量_operator_sub(向量_t *v1, 向量_t *v2) {
    向量_t *result = (向量_t*)malloc(sizeof(向量_t));
    result->x = v1->x - v2->x;
    result->y = v1->y - v2->y;
    return result;
}'''
    }

    print("--- 向量类的运算符重载实现 ---")
    print(generator.generate_implementation('向量', implementations))

    print("=== 测试完成 ===")