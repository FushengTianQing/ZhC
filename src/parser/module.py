#!/usr/bin/env python3
"""
Day 2: 模块解析器

功能：解析中文C代码中的模块语法
- 模块声明：`模块 模块名 { ... }`
- 导入声明：`导入 模块名`
- 访问控制关键字：`公开:`、`私有:`、`保护:`

主要类：
1. ModuleParser: 主解析器类
2. ModuleInfo: 模块信息类
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ModuleInfo:
    """模块信息"""

    name: str
    version: Optional[str] = None
    public_symbols: List[str] = field(default_factory=list)
    private_symbols: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    file_path: Optional[str] = None

    def add_symbol(self, symbol: str, visibility: str = "private"):
        """添加符号到指定可见性区域"""
        if visibility == "public":
            if symbol not in self.public_symbols:
                self.public_symbols.append(symbol)
        else:
            if symbol not in self.private_symbols:
                self.private_symbols.append(symbol)

    def get_all_symbols(self) -> List[str]:
        """获取所有符号"""
        return self.public_symbols + self.private_symbols

    def __str__(self) -> str:
        return f"模块 {self.name} (公开: {len(self.public_symbols)}, 私有: {len(self.private_symbols)})"


class ModuleParser:
    """模块解析器"""

    def __init__(self):
        self.modules: Dict[str, ModuleInfo] = {}
        self.current_module: Optional[ModuleInfo] = None
        self.current_visibility: str = "private"
        self.errors: List[str] = []
        self.imported_modules: List[str] = []  # 导入的模块列表

    def parse_module_declaration(
        self, line: str, line_num: int
    ) -> Optional[ModuleInfo]:
        """解析模块声明"""
        # 匹配: 模块 模块名 { 或 模块 模块名 版本 1.0 {
        pattern = r"模块\s+(\w+)(?:\s+版本\s+([\w\.]+))?\s*\{?"
        match = re.search(pattern, line)

        if match:
            module_name = match.group(1)
            version = match.group(2) if match.group(2) else None

            if module_name in self.modules:
                self.errors.append(f"行{line_num}: 模块 '{module_name}' 重复定义")
                return None

            module_info = ModuleInfo(name=module_name, version=version)
            self.modules[module_name] = module_info
            self.current_module = module_info
            self.current_visibility = "private"

            return module_info
        return None

    def parse_import_declaration(self, line: str, line_num: int) -> List[str]:
        """解析导入声明"""
        pattern = r"导入\s+(\w+)(?:\s+为\s+(\w+))?"
        match = re.search(pattern, line)

        if match:
            module_name = match.group(1)
            match.group(2) if match.group(2) else module_name

            # 如果在模块内，添加到当前模块的导入列表
            if self.current_module and module_name not in self.current_module.imports:
                self.current_module.imports.append(module_name)

            # 添加到全局导入列表（无论是否在模块内）
            if module_name not in self.imported_modules:
                self.imported_modules.append(module_name)

            # 仅在模块内时返回导入结果（模块外的导入被忽略）
            if self.current_module:
                return [module_name]
            return []

        # 尝试匹配多个导入: 导入 模块1, 模块2, 模块3
        multi_pattern = r"导入\s+([\w\s,]+)"
        match = re.search(multi_pattern, line)

        if match:
            imports_text = match.group(1)
            imported = [imp.strip() for imp in imports_text.split(",") if imp.strip()]

            for imp in imported:
                # 如果在模块内，添加到当前模块的导入列表
                if self.current_module and imp not in self.current_module.imports:
                    self.current_module.imports.append(imp)
                # 添加到全局导入列表（无论是否在模块内）
                if imp not in self.imported_modules:
                    self.imported_modules.append(imp)

            # 仅在模块内时返回导入结果
            if self.current_module:
                return imported
            return []

        return []

    def parse_visibility_section(self, line: str, line_num: int) -> Optional[str]:
        """解析可见性区域声明"""
        line_stripped = line.strip()

        if line_stripped == "公开:":
            self.current_visibility = "public"
            return "public"
        elif line_stripped == "私有:":
            self.current_visibility = "private"
            return "private"

        return None

    def parse_symbol_declaration(self, line: str, line_num: int) -> Optional[str]:
        """解析符号声明"""
        if not self.current_module:
            return None

        # 匹配函数声明: 整数型 函数名(参数) { 或 函数 函数名(参数) -> 整数型 {
        func_pattern = r"(?:函数\s+)?(\w+)\s*\([^)]*\)(?:\s*->\s*\w+型)?\s*\{"
        match = re.search(func_pattern, line)

        if match:
            symbol = match.group(1)
            self.current_module.add_symbol(symbol, self.current_visibility)
            return symbol

        # 匹配变量声明: 整数型 变量名; 或 整数型 变量名 = 值;
        var_pattern = r"(\w+型)\s+(\w+)(?:\s*=\s*[^;]+)?;"
        match = re.search(var_pattern, line)

        if match:
            symbol = match.group(2)
            self.current_module.add_symbol(symbol, self.current_visibility)
            return symbol

        return None

    def parse_line(self, line: str, line_num: int):
        """解析单行代码"""
        # 先尝试匹配模块声明
        if self.parse_module_declaration(line, line_num):
            return

        # 尝试匹配导入声明
        if self.parse_import_declaration(line, line_num):
            return

        # 尝试匹配可见性区域
        if self.parse_visibility_section(line, line_num):
            return

        # 尝试匹配符号声明
        if self.current_module:
            self.parse_symbol_declaration(line, line_num)

        # 检查模块结束
        if line.strip() == "}" and self.current_module:
            self.current_module = None
            self.current_visibility = "private"

    def parse_file(self, file_path: str) -> List[ModuleInfo]:
        """解析文件中的所有模块"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.modules.clear()
            self.current_module = None
            self.current_visibility = "private"
            self.errors.clear()

            for i, line in enumerate(lines, 1):
                self.parse_line(line.strip(), i)

            return list(self.modules.values())

        except Exception as e:
            self.errors.append(f"解析文件失败: {e}")
            return []

    def get_summary(self) -> str:
        """获取解析摘要"""
        summary = []
        summary.append("=== 模块解析摘要 ===")
        summary.append(f"发现模块数: {len(self.modules)}")
        summary.append(f"错误数: {len(self.errors)}")

        if self.errors:
            summary.append("\n错误列表:")
            for error in self.errors:
                summary.append(f"  - {error}")

        for module_name, module_info in self.modules.items():
            summary.append(f"\n模块: {module_name}")
            if module_info.version:
                summary.append(f"  版本: {module_info.version}")
            summary.append(f"  公开符号: {len(module_info.public_symbols)}")
            summary.append(f"  私有符号: {len(module_info.private_symbols)}")
            summary.append(f"  导入模块: {module_info.imports}")

        return "\n".join(summary)


# 测试代码
if __name__ == "__main__":
    # 示例中文C模块代码
    test_code = """
模块 数学模块 版本 1.0 {
    公开:
        整数型 加(整数型 a, 整数型 b) {
            返回 a + b;
        }

        整数型 乘(整数型 a, 整数型 b) {
            返回 a * b;
        }

    私有:
        整数型 内部函数() {
            返回 42;
        }
}

模块 工具模块 {
    导入 数学模块

    公开:
        整数型 计算平均值(整数型 数组[], 整数型 长度) {
            整数型 总和 = 0;
            循环 (整数型 i = 0; i < 长度; i++) {
                总和 = 数学模块.加(总和, 数组[i]);
            }
            返回 总和 / 长度;
        }
}
"""

    # 测试解析器
    parser = ModuleParser()

    # 将测试代码写入临时文件
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".zhc", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        modules = parser.parse_file(temp_file)
        print(parser.get_summary())

        print("\n=== 模块详情 ===")
        for module in modules:
            print(f"\n{module}")
            print(f"  公开符号: {module.public_symbols}")
            print(f"  私有符号: {module.private_symbols}")
            print(f"  导入模块: {module.imports}")

    finally:
        import os

        os.unlink(temp_file)
