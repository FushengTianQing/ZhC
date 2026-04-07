#!/usr/bin/env python3
"""
Day 8: 模块高级特性扩展

功能：
1. 模块别名机制：支持导入时指定别名
2. 模块条件编译：支持条件编译指令
3. 模块版本控制：支持版本范围和兼容性检查
4. 模块化设计示例：展示高级特性的使用

语法示例：
模块别名：
    导入 数学库 为 M
    M.加法(1, 2)  # 使用别名调用

条件编译：
    #如果 定义(调试模式)
    模块 调试模块 { ... }
    #否则
    模块 发布模块 { ... }
    #结束

版本控制：
    模块 网络库 版本 >= 1.0.0 { ... }
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ConditionType(Enum):
    """条件类型枚举"""
    DEFINED = "defined"       # 定义了某个符号
    NOT_DEFINED = "not_defined"  # 未定义某个符号
    VERSION_COMPARE = "version_compare"  # 版本比较


@dataclass
class ModuleAlias:
    """模块别名信息"""
    original_name: str          # 原始模块名
    alias: str                  # 别名
    line_number: int           # 定义行号
    file_path: Optional[str] = None  # 文件路径


@dataclass
class ConditionalBlock:
    """条件编译块"""
    condition_type: ConditionType
    condition_value: str
    content: str                # 块内容
    else_content: str = ""     # else块内容
    line_number: int = 0


@dataclass
class VersionInfo:
    """版本信息"""
    major: int = 0
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, version_str: str) -> 'VersionInfo':
        """解析版本字符串"""
        # 清理版本字符串
        version_str = version_str.strip().lstrip('vV')

        # 尝试解析 x.y.z 格式
        match = re.match(r'(\d+)(?:\.(\d+))?(?:\.(\d+))?', version_str)
        if match:
            return cls(
                major=int(match.group(1)),
                minor=int(match.group(2)) if match.group(2) else 0,
                patch=int(match.group(3)) if match.group(3) else 0
            )
        return cls()

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: 'VersionInfo') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: 'VersionInfo') -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: 'VersionInfo') -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: 'VersionInfo') -> bool:
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __eq__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)


class VersionComparator:
    """版本比较器"""

    OPERATORS = {
        '>=': lambda a, b: a >= b,
        '<=': lambda a, b: a <= b,
        '>': lambda a, b: a > b,
        '<': lambda a, b: a < b,
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
    }

    @classmethod
    def compare(cls, version: str, operator: str, expected: str) -> bool:
        """比较版本"""
        if operator not in cls.OPERATORS:
            return False

        try:
            actual = VersionInfo.parse(version)
            expected_ver = VersionInfo.parse(expected)
            return cls.OPERATORS[operator](actual, expected_ver)
        except (ValueError, AttributeError):
            return False


class ModuleAliasManager:
    """模块别名管理器"""

    def __init__(self):
        self.aliases: Dict[str, ModuleAlias] = {}  # 别名 -> 别名信息
        self.module_to_aliases: Dict[str, List[str]] = {}  # 原始模块名 -> 别名列表

    def add_alias(self, original_name: str, alias: str, line_number: int = 0, file_path: Optional[str] = None) -> bool:
        """添加模块别名"""
        if alias in self.aliases:
            return False  # 别名已存在

        module_alias = ModuleAlias(
            original_name=original_name,
            alias=alias,
            line_number=line_number,
            file_path=file_path
        )

        self.aliases[alias] = module_alias

        if original_name not in self.module_to_aliases:
            self.module_to_aliases[original_name] = []
        self.module_to_aliases[original_name].append(alias)

        return True

    def get_original_name(self, alias: str) -> Optional[str]:
        """通过别名获取原始模块名"""
        if alias in self.aliases:
            return self.aliases[alias].original_name
        return None

    def resolve_module_name(self, name: str) -> str:
        """解析模块名（如果是别名则返回原始名）"""
        return self.get_original_name(name) or name

    def is_alias(self, name: str) -> bool:
        """检查是否是别名"""
        return name in self.aliases

    def get_all_aliases(self, module_name: str) -> List[str]:
        """获取模块的所有别名"""
        return self.module_to_aliases.get(module_name, [])

    def remove_alias(self, alias: str) -> bool:
        """移除别名"""
        if alias not in self.aliases:
            return False

        original = self.aliases[alias].original_name
        del self.aliases[alias]

        if original in self.module_to_aliases:
            self.module_to_aliases[original].remove(alias)
            if not self.module_to_aliases[original]:
                del self.module_to_aliases[original]

        return True

    def get_statistics(self) -> Dict[str, object]:
        """获取统计信息"""
        return {
            'total_aliases': len(self.aliases),
            'modules_with_aliases': len(self.module_to_aliases),
            'most_used_module': max(self.module_to_aliases.keys(),
                                   key=lambda k: len(self.module_to_aliases[k])) if self.module_to_aliases else None
        }


class ConditionalCompiler:
    """条件编译处理器"""

    def __init__(self):
        self.defined_symbols: Set[str] = set()
        self.conditional_blocks: List[ConditionalBlock] = []

    def define_symbol(self, symbol: str):
        """定义符号"""
        self.defined_symbols.add(symbol)

    def undefine_symbol(self, symbol: str):
        """取消定义符号"""
        self.defined_symbols.discard(symbol)

    def is_defined(self, symbol: str) -> bool:
        """检查符号是否已定义"""
        return symbol in self.defined_symbols

    def evaluate_condition(self, condition_type: ConditionType, value: str) -> bool:
        """评估条件"""
        if condition_type == ConditionType.DEFINED:
            return self.is_defined(value)
        elif condition_type == ConditionType.NOT_DEFINED:
            return not self.is_defined(value)
        elif condition_type == ConditionType.VERSION_COMPARE:
            # 版本比较格式: "version >= 1.0.0"
            match = re.match(r'version\s*([><=!]+)\s*([\d.]+)', value)
            if match:
                operator = match.group(1)
                version = match.group(2)
                # 这里应该检查当前模块版本
                return True  # 简化版本，实际应检查版本
        return False

    def process_conditional_block(self, content: str) -> str:
        """处理条件编译块"""
        lines = content.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # 检查条件编译指令
            if self._is_conditional_start(line):
                condition = self._parse_condition(line)
                block_content, else_content, consumed = self._extract_block(lines, i + 1)

                if condition and self.evaluate_condition(condition[0], condition[1]):
                    result_lines.extend(block_content)
                elif else_content:
                    result_lines.extend(else_content)

                i += consumed
            else:
                result_lines.append(lines[i])
                i += 1

        return '\n'.join(result_lines)

    def _is_conditional_start(self, line: str) -> bool:
        """检查是否是条件编译开始"""
        return line.startswith('#如果') or line.startswith('#ifdef') or line.startswith('#if')

    def _parse_condition(self, line: str) -> Optional[Tuple[ConditionType, str]]:
        """解析条件"""
        line = line.strip()

        if line.startswith('#如果 定义('):
            match = re.match(r'#如果\s+定义\(([^)]+)\)', line)
            if match:
                return (ConditionType.DEFINED, match.group(1))

        elif line.startswith('#如果 未定义('):
            match = re.match(r'#如果\s+未定义\(([^)]+)\)', line)
            if match:
                return (ConditionType.NOT_DEFINED, match.group(1))

        elif line.startswith('#如果 版本'):
            match = re.match(r'#如果\s+版本\s+(.+)', line)
            if match:
                return (ConditionType.VERSION_COMPARE, match.group(1))

        elif line.startswith('#ifdef'):
            match = re.match(r'#ifdef\s+(\w+)', line)
            if match:
                return (ConditionType.DEFINED, match.group(1))

        elif line.startswith('#ifndef'):
            match = re.match(r'#ifndef\s+(\w+)', line)
            if match:
                return (ConditionType.NOT_DEFINED, match.group(1))

        return None

    def _extract_block(self, lines: List[str], start: int) -> Tuple[List[str], List[str], int]:
        """提取条件块内容"""
        block_content: List[str] = []
        else_content: List[str] = []
        current = block_content
        depth = 1
        consumed = 0

        i = start
        while i < len(lines) and depth > 0:
            line = lines[i].strip()
            consumed += 1

            if line.startswith('#如果') or line.startswith('#ifdef') or line.startswith('#if'):
                depth += 1
                current.append(lines[i])
            elif line == '#否则' and depth == 1:
                current = else_content
            elif line == '#结束' or line == '#endif':
                depth -= 1
                if depth > 0:
                    current.append(lines[i])
            elif depth > 0:
                current.append(lines[i])

            i += 1

        return block_content, else_content, consumed


class VersionManager:
    """版本管理器"""

    def __init__(self):
        self.module_versions: Dict[str, VersionInfo] = {}
        self.version_constraints: Dict[str, str] = {}  # 模块 -> 版本约束

    def register_module_version(self, module_name: str, version: str):
        """注册模块版本"""
        self.module_versions[module_name] = VersionInfo.parse(version)

    def get_module_version(self, module_name: str) -> Optional[VersionInfo]:
        """获取模块版本"""
        return self.module_versions.get(module_name)

    def set_version_constraint(self, module_name: str, constraint: str):
        """设置版本约束（如 ">= 1.0.0"）"""
        self.version_constraints[module_name] = constraint

    def check_version_compatibility(self, module_name: str, constraint: str) -> bool:
        """检查版本兼容性"""
        if module_name not in self.module_versions:
            return False

        # 解析约束（如 ">= 1.0.0"）
        match = re.match(r'([><=!]+)\s*([\d.]+)', constraint.strip())
        if not match:
            return True  # 无法解析，认为兼容

        operator = match.group(1)
        expected_version = match.group(2)

        current = self.module_versions[module_name]
        expected = VersionInfo.parse(expected_version)

        return VersionComparator.compare(str(current), operator, expected_version)

    def get_statistics(self) -> Dict[str, object]:
        """获取版本统计"""
        if not self.module_versions:
            return {'total_modules': 0}

        versions = list(self.module_versions.values())
        return {
            'total_modules': len(self.module_versions),
            'modules': list(self.module_versions.keys()),
            'latest_version': max(self.module_versions.items(), key=lambda x: x[1])[0] if versions else None,
            'constraints': len(self.version_constraints)
        }


# 测试代码
if __name__ == "__main__":
    print("=== Day 8: 模块高级特性测试 ===\n")

    # 测试1: 模块别名管理
    print("1. 测试模块别名管理:")
    alias_manager = ModuleAliasManager()

    alias_manager.add_alias("数学库", "M", 1)
    alias_manager.add_alias("数学库", "Math", 2)
    alias_manager.add_alias("工具库", "Utils", 3)

    print(f"   M 的原始名: {alias_manager.get_original_name('M')}")
    print(f"   Math 的原始名: {alias_manager.get_original_name('Math')}")
    print(f"   '数学库' 的别名: {alias_manager.get_all_aliases('数学库')}")
    print(f"   别名统计: {alias_manager.get_statistics()}")

    # 测试2: 条件编译
    print("\n2. 测试条件编译:")
    compiler = ConditionalCompiler()

    compiler.define_symbol("调试模式")
    compiler.define_symbol("高性能")

    print(f"   '调试模式' 已定义: {compiler.is_defined('调试模式')}")
    print(f"   '发行版' 已定义: {compiler.is_defined('发行版')}")

    test_code = """
模块 测试模块 {
    公开:
        函数 测试() {
            #如果 定义(调试模式)
            打印("调试模式");
            #否则
            打印("发行版");
            #结束
        }
}
"""
    result = compiler.process_conditional_block(test_code)
    print(f"   条件编译结果包含 '调试模式': {'调试模式' in result}")

    # 测试3: 版本管理
    print("\n3. 测试版本管理:")
    version_mgr = VersionManager()

    version_mgr.register_module_version("数学库", "1.2.3")
    version_mgr.register_module_version("工具库", "2.0.0")
    version_mgr.set_version_constraint("数学库", ">= 1.0.0")

    print(f"   数学库版本: {version_mgr.get_module_version('数学库')}")
    print(f"   版本兼容性检查 (数学库 >= 1.0.0): {version_mgr.check_version_compatibility('数学库', '>= 1.0.0')}")
    print(f"   版本兼容性检查 (数学库 >= 2.0.0): {version_mgr.check_version_compatibility('数学库', '>= 2.0.0')}")
    print(f"   版本统计: {version_mgr.get_statistics()}")

    # 测试4: 版本比较
    print("\n4. 测试版本比较:")
    v1 = VersionInfo.parse("1.2.3")
    v2 = VersionInfo.parse("1.3.0")
    v3 = VersionInfo.parse("2.0.0")

    print(f"   1.2.3 < 1.3.0: {v1 < v2}")
    print(f"   1.2.3 < 2.0.0: {v1 < v3}")
    print(f"   1.3.0 >= 1.2.3: {v2 >= v1}")

    print("\n=== Day 8 测试完成 ===")