#!/usr/bin/env python3
"""
Day 15: 继承转换器

功能：
1. 继承语法转换规则
2. 基类成员继承
3. 多级继承链处理
4. 继承链追踪
"""

from typing import List, Dict, Optional, Set, Tuple


class InheritanceConverter:
    """继承转换器"""

    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.inheritance_chains: Dict[str, List[str]] = {}

    def add_class(
        self,
        class_name: str,
        base_class: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        methods: Optional[List[str]] = None,
    ):
        """添加类定义"""
        self.classes[class_name] = {
            "name": class_name,
            "base_class": base_class,
            "attributes": attributes or [],
            "methods": methods or [],
        }

        # 计算继承链
        self._compute_inheritance_chain(class_name)

    def _compute_inheritance_chain(self, class_name: str):
        """计算继承链"""
        if class_name not in self.classes:
            self.inheritance_chains[class_name] = [class_name]
            return

        chain = []
        current = class_name
        visited = set()

        while current and current not in visited:
            visited.add(current)
            chain.append(current)
            base = self.classes[current]["base_class"]
            current = base

        self.inheritance_chains[class_name] = chain

    def convert_inheritance(self, class_name: str) -> Tuple[str, str]:
        """转换继承类

        Returns:
            (struct定义, 头文件内容)
        """
        if class_name not in self.classes:
            return "", ""

        class_info = self.classes[class_name]
        base_class = class_info["base_class"]

        # 生成struct定义
        struct_def = self._generate_struct_definition(
            class_name, base_class, class_info["attributes"]
        )

        # 生成头文件
        header = self._generate_header(class_name, base_class, class_info["methods"])

        return struct_def, header

    def _generate_struct_definition(
        self, class_name: str, base_class: Optional[str], attributes: List[str]
    ) -> str:
        """生成struct定义"""
        lines = [f"/* {class_name} 类的struct定义 */"]

        # 如果有基类，先包含基类头文件
        if base_class:
            lines.append(f'#include "{base_class}.h"')
            lines.append("")

        lines.append(f"typedef struct {class_name} {{")

        # 添加基类成员
        if base_class:
            lines.append(f"    /* 基类 {base_class} 的成员 */")
            lines.append(f"    struct {base_class} base;")

        # 添加当前类的属性
        lines.append("")
        lines.append(f"    /* {class_name} 自己的成员 */")
        for attr in attributes:
            lines.append(f"    {attr};")

        lines.append(f"}} {class_name};")

        return "\n".join(lines)

    def _generate_header(
        self, class_name: str, base_class: Optional[str], methods: List[str]
    ) -> str:
        """生成头文件"""
        lines = []

        # 头文件保护宏
        guard = f"__{class_name.upper()}_H_"

        lines.append(f"#ifndef {guard}")
        lines.append(f"#define {guard}")
        lines.append("")

        if base_class:
            lines.append(f'#include "{base_class}.h"')
            lines.append("")

        lines.append(f"/* {class_name} 类的公开接口 */")

        # 构造函数声明
        lines.append("/* 构造函数 */")
        lines.append(f"struct {class_name} * {class_name}_constructor")
        if base_class:
            lines[-1] += f"(struct {base_class} *base"
            lines.append(")")

        # 方法声明
        lines.append("")
        lines.append("/* 方法 */")
        for method in methods:
            lines.append(f"void {class_name}_{method}(struct {class_name} *self);")

        lines.append("")
        lines.append(f"#endif /* {guard} */")

        return "\n".join(lines)


class InheritanceChainAnalyzer:
    """继承链分析器"""

    def __init__(self):
        self.chains: Dict[str, List[str]] = {}
        self.levels: Dict[str, int] = {}
        self.roots: Set[str] = set()

    def analyze(self, class_hierarchy: Dict[str, Optional[str]]):
        """分析继承层次

        Args:
            class_hierarchy: 类名 -> 基类名 的映射
        """
        # 计算所有继承链
        for class_name in class_hierarchy:
            self._compute_chain(class_name, class_hierarchy)

        # 计算层次
        for class_name, chain in self.chains.items():
            self.levels[class_name] = len(chain) - 1

        # 找出根类
        self.roots = {name for name, base in class_hierarchy.items() if base is None}

    def _compute_chain(self, class_name: str, hierarchy: Dict[str, Optional[str]]):
        """计算单个类的继承链"""
        if class_name in self.chains:
            return

        chain = []
        current: Optional[str] = class_name
        visited = set()

        while current and current not in visited:
            visited.add(current)
            chain.append(current)
            current = hierarchy.get(current)

        self.chains[class_name] = chain

    def get_chain(self, class_name: str) -> List[str]:
        """获取继承链"""
        return self.chains.get(class_name, [class_name])

    def get_level(self, class_name: str) -> int:
        """获取类的层次（根类为0，层层递增"""
        return self.levels.get(class_name, 0)

    def is_descendant(self, class_name: str, ancestor: str) -> bool:
        """检查是否是祖先类的后代"""
        chain = self.get_chain(class_name)
        return ancestor in chain

    def get_common_ancestor(self, class1: str, class2: str) -> Optional[str]:
        """获取两个类的最近公共祖先"""
        chain1 = set(self.get_chain(class1))
        chain2 = self.get_chain(class2)

        for ancestor in chain1:
            if ancestor in chain2:
                return ancestor

        return None

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_classes": len(self.chains),
            "root_classes": len(self.roots),
            "max_depth": max(len(chain) for chain in self.chains.values())
            if self.chains
            else 0,
        }


# 测试代码
if __name__ == "__main__":
    print("=== Day 15: 继承转换器测试 ===\n")

    # 测试1: 基本继承
    print("1. 测试基本继承:")
    converter = InheritanceConverter()
    converter.add_class("学生", base_class=None, attributes=["char* 姓名", "int 年龄"])
    converter.add_class("大学生", base_class="学生", attributes=["char* 专业"])
    converter.add_class("本科生", base_class="大学生", attributes=["int 年级"])

    struct_def, header = converter.convert_inheritance("大学生")
    print(f"struct定义:\n{struct_def}")

    # 测试2: 继承链分析
    print("\n2. 测试继承链分析:")
    analyzer = InheritanceChainAnalyzer()
    analyzer.analyze({"人类": None, "学生": "人类", "大学生": "学生", "研究生": "学生"})

    print(f"大学生的继承链: {analyzer.get_chain('大学生')}")
    print(f"研究生的层次: {analyzer.get_level('研究生')} (0=根类)")

    # 测试3: 公共祖先
    print("\n3. 测试公共祖先:")
    common = analyzer.get_common_ancestor("大学生", "研究生")
    print(f"大学生和研究生 最近公共祖先: {common}")

    print("\n=== Day 15 测试完成 ===")
