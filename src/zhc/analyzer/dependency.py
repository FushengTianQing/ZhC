#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 4: 模块依赖解析器
负责模块依赖关系分析、循环依赖检测和编译顺序计算
"""

from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class DependencyErrorType(Enum):
    """依赖错误类型枚举"""

    CYCLIC_DEPENDENCY = "循环依赖"
    MISSING_MODULE = "模块不存在"
    SELF_DEPENDENCY = "自依赖"
    CIRCULAR_IMPORT = "循环导入"
    INVALID_MODULE_NAME = "模块名无效"


@dataclass
class ModuleInfo:
    """模块信息"""

    name: str
    file_path: str
    dependencies: List[str] = field(default_factory=list)  # 依赖的模块名
    dependents: List[str] = field(default_factory=list)  # 依赖此模块的模块
    public_symbols: Dict[str, str] = field(default_factory=dict)  # 公开符号: 类型
    private_symbols: Dict[str, str] = field(default_factory=dict)  # 私有符号: 类型
    line_number: int = 1  # 定义所在行号
    is_analyzed: bool = False  # 是否已分析完成


@dataclass
class DependencyGraph:
    """依赖关系图"""

    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    adjacency_list: Dict[str, Set[str]] = field(default_factory=dict)  # 邻接表
    reverse_adjacency: Dict[str, Set[str]] = field(default_factory=dict)  # 反向邻接表

    def add_module(self, module_info: ModuleInfo) -> None:
        """添加模块到图中"""
        self.modules[module_info.name] = module_info
        self.adjacency_list[module_info.name] = set(module_info.dependencies)

        # 更新反向邻接表
        for dep in module_info.dependencies:
            if dep not in self.reverse_adjacency:
                self.reverse_adjacency[dep] = set()
            self.reverse_adjacency[dep].add(module_info.name)

    def get_dependencies(self, module_name: str) -> Set[str]:
        """获取模块的直接依赖"""
        return self.adjacency_list.get(module_name, set())

    def get_dependents(self, module_name: str) -> Set[str]:
        """获取依赖此模块的模块"""
        return self.reverse_adjacency.get(module_name, set())

    def get_transitive_dependencies(self, module_name: str) -> Set[str]:
        """获取模块的传递依赖（包括间接依赖）"""
        visited = set()
        stack = [module_name]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            # 添加当前模块的依赖
            for dep in self.get_dependencies(current):
                if dep not in visited:
                    stack.append(dep)

        # 移除自身
        visited.discard(module_name)
        return visited


class DependencyResolver:
    """模块依赖解析器"""

    def __init__(self, error_handler=None):
        self.graph = DependencyGraph()
        self.error_handler = error_handler
        self.visited = set()
        self.recursion_stack = set()
        self.cycles_found = []

    def parse_module_dependencies(
        self, module_declaration: Dict[str, Any]
    ) -> ModuleInfo:
        """从模块声明中解析依赖关系"""
        module_info = ModuleInfo(
            name=module_declaration.get("name", ""),
            file_path=module_declaration.get("file_path", ""),
            line_number=module_declaration.get("line_number", 1),
        )

        # 解析导入语句获取依赖
        imports = module_declaration.get("imports", [])
        for imp in imports:
            if isinstance(imp, dict) and "module" in imp:
                module_info.dependencies.append(imp["module"])
            elif isinstance(imp, str):
                # 导入是字符串，直接添加到依赖
                module_info.dependencies.append(imp)

        # 解析符号定义
        symbols = module_declaration.get("symbols", {})
        for scope, scope_symbols in symbols.items():
            if scope == "public":
                module_info.public_symbols.update(scope_symbols)
            elif scope == "private":
                module_info.private_symbols.update(scope_symbols)

        return module_info

    def add_module(self, module_declaration: Dict[str, Any]) -> None:
        """添加模块到依赖图"""
        module_info = self.parse_module_dependencies(module_declaration)
        self.graph.add_module(module_info)

        # 验证模块名有效性
        if not self._is_valid_module_name(module_info.name):
            if self.error_handler:
                self.error_handler.report_error(
                    "依赖解析错误",
                    f"无效的模块名: {module_info.name}",
                    module_info.line_number,
                    "错误",
                )

    def detect_cycles(self) -> List[List[str]]:
        """检测循环依赖"""
        self.cycles_found = []
        self.visited = set()
        self.recursion_stack = set()

        for module_name in self.graph.modules:
            if module_name not in self.visited:
                self._dfs_cycle_detection(module_name, [])

        return self.cycles_found

    def _dfs_cycle_detection(self, current: str, path: List[str]) -> None:
        """深度优先搜索检测循环依赖"""
        if current in self.recursion_stack:
            # 找到循环
            cycle_start = path.index(current)
            cycle = path[cycle_start:] + [current]
            self.cycles_found.append(cycle)
            return

        if current in self.visited:
            return

        self.visited.add(current)
        self.recursion_stack.add(current)

        # 遍历所有依赖
        for dep in self.graph.get_dependencies(current):
            self._dfs_cycle_detection(dep, path + [current])

        self.recursion_stack.remove(current)

    def calculate_compilation_order(self) -> List[str]:
        """计算编译顺序（拓扑排序）"""
        # 检测循环依赖
        cycles = self.detect_cycles()
        if cycles:
            if self.error_handler:
                for cycle in cycles:
                    cycle_str = " -> ".join(cycle)
                    self.error_handler.report_error(
                        "循环依赖错误",
                        f"发现循环依赖: {cycle_str}",
                        1,  # 全局错误，行号设为1
                        "错误",
                    )
            return []

        # 拓扑排序
        # in_degree[module] = 模块有多少个依赖（需要先编译的模块数）
        in_degree = {}
        for module in self.graph.modules:
            in_degree[module] = len(self.graph.get_dependencies(module))

        # Kahn算法：从入度为0的节点开始（没有依赖的节点）
        queue = [module for module, degree in in_degree.items() if degree == 0]
        result = []

        # 调试信息
        debug = False
        if debug:
            print(f"初始入度: {in_degree}")
            print(f"初始队列: {queue}")

        while queue:
            current = queue.pop(0)
            result.append(current)

            if debug:
                print(f"\n处理节点: {current}")
                print(f"当前结果: {result}")

            # 当前节点被编译后，所有依赖它的节点入度减少
            # 因为当前节点不再阻塞它们
            for dependent in self.graph.get_dependents(current):
                in_degree[dependent] -= 1
                if debug:
                    print(
                        f"减少 {dependent} 的入度: {in_degree[dependent] + 1} -> {in_degree[dependent]}"
                    )
                if in_degree[dependent] == 0:
                    queue.append(dependent)
                    if debug:
                        print(f"将 {dependent} 加入队列")

        # 检查是否所有节点都被处理
        if len(result) != len(self.graph.modules):
            if self.error_handler:
                self.error_handler.report_error(
                    "依赖解析错误",
                    f"无法计算完整的编译顺序，可能存在未解析的依赖。得到 {len(result)}/{len(self.graph.modules)} 个模块",
                    1,
                    "错误",
                )
            if debug:
                print(f"警告：只处理了 {len(result)}/{len(self.graph.modules)} 个模块")
                print(f"未处理的模块: {set(self.graph.modules.keys()) - set(result)}")

        return result

    def find_missing_dependencies(self) -> List[Tuple[str, str]]:
        """查找缺失的依赖"""
        missing = []

        for module_name, module_info in self.graph.modules.items():
            for dep in module_info.dependencies:
                if dep not in self.graph.modules:
                    missing.append((module_name, dep))

        return missing

    def export_dependency_graph(self) -> Dict[str, Any]:
        """导出依赖关系图（用于可视化）"""
        return {
            "modules": {
                name: {
                    "dependencies": list(self.graph.get_dependencies(name)),
                    "dependents": list(self.graph.get_dependents(name)),
                    "transitive_deps": list(
                        self.graph.get_transitive_dependencies(name)
                    ),
                    "public_symbols": module_info.public_symbols,
                    "private_symbols_count": len(module_info.private_symbols),
                }
                for name, module_info in self.graph.modules.items()
            },
            "compilation_order": self.calculate_compilation_order(),
            "cycles": self.cycles_found,
            "missing_dependencies": self.find_missing_dependencies(),
        }

    def _is_valid_module_name(self, name: str) -> bool:
        """验证模块名有效性"""
        # 模块名规则：支持Unicode字符（包括中文），不能以数字开头
        if not name:
            return False
        if name[0].isdigit():
            return False
        # 支持Unicode字符，包括中文、字母、数字、下划线
        # 使用更简单的方法：检查每个字符是否是字母、数字、下划线或中文字符
        for char in name:
            if not (char.isalpha() or char.isdigit() or char == "_"):
                # 对于中文字符，isalpha() 返回 True
                return False
        return True

    def validate_module_references(self) -> List[Tuple[str, str, str]]:
        """验证模块间的符号引用"""
        issues = []

        for module_name, module_info in self.graph.modules.items():
            # 检查导入的模块是否存在
            for dep in module_info.dependencies:
                if dep not in self.graph.modules:
                    issues.append((module_name, dep, "模块不存在"))

        return issues

    def get_module_statistics(self) -> Dict[str, Any]:
        """获取模块统计信息"""
        total_modules = len(self.graph.modules)
        total_dependencies = sum(
            len(module.dependencies) for module in self.graph.modules.values()
        )
        total_public_symbols = sum(
            len(module.public_symbols) for module in self.graph.modules.values()
        )
        total_private_symbols = sum(
            len(module.private_symbols) for module in self.graph.modules.values()
        )

        return {
            "total_modules": total_modules,
            "total_dependencies": total_dependencies,
            "avg_dependencies_per_module": total_dependencies / total_modules
            if total_modules > 0
            else 0,
            "total_public_symbols": total_public_symbols,
            "total_private_symbols": total_private_symbols,
            "modules_without_deps": sum(
                1 for module in self.graph.modules.values() if not module.dependencies
            ),
            "most_dependent_module": max(
                self.graph.modules.values(), key=lambda m: len(m.dependencies)
            ).name
            if self.graph.modules
            else None,
        }


class MultiFileIntegrator:
    """多文件集成管理器"""

    def __init__(self, dependency_resolver: DependencyResolver):
        self.resolver = dependency_resolver
        self.module_files: Dict[str, str] = {}  # 模块名 -> 文件路径映射
        self.file_contents: Dict[str, str] = {}  # 文件路径 -> 文件内容
        self.conversion_results: Dict[str, Any] = {}  # 模块名 -> 转换结果
        self.c_files: Dict[str, str] = {}  # 模块名 -> C源文件路径
        self.h_files: Dict[str, str] = {}  # 模块名 -> C头文件路径

    def register_module_file(
        self, module_name: str, file_path: str, content: str
    ) -> None:
        """注册模块文件"""
        self.module_files[module_name] = file_path
        self.file_contents[file_path] = content

    def register_c_file(
        self, module_name: str, c_file_path: str, h_file_path: str
    ) -> None:
        """注册C文件路径"""
        self.c_files[module_name] = c_file_path
        self.h_files[module_name] = h_file_path

    def integrate_modules(self) -> Dict[str, Any]:
        """集成多个模块文件"""
        # 1. 计算编译顺序
        compilation_order = self.resolver.calculate_compilation_order()
        if not compilation_order:
            return {"error": "无法计算编译顺序"}

        # 2. 按顺序处理模块
        integrated_result = {
            "compilation_order": compilation_order,
            "modules": {},
            "generated_files": [],
        }

        for module_name in compilation_order:
            file_path = self.module_files.get(module_name)
            if not file_path:
                continue

            # 这里可以调用Day 3的转换器进行实际转换
            # integrated_result["modules"][module_name] = {
            #     "file": file_path,
            #     "converted": True
            # }

        return integrated_result

    def generate_makefile(self, output_dir: str) -> str:
        """生成Makefile用于构建多模块项目"""
        compilation_order = self.resolver.calculate_compilation_order()
        if not compilation_order:
            return "# 错误: 无法生成Makefile，存在循环依赖\n"

        # 生成目标文件列表
        objs_list = []
        compile_rules = []

        for mod in compilation_order:
            # 使用实际的文件路径，如果已注册
            c_file = self.c_files.get(mod, f"{mod}.c")
            h_file = self.h_files.get(mod, f"{mod}.h")

            # 目标文件路径
            obj_file = f"{mod}.o"
            objs_list.append(obj_file)

            # 为每个模块生成单独的编译规则
            compile_rules.append(f"""
{obj_file}: {c_file} {h_file}
\t$(CC) $(CFLAGS) -c {c_file} -o {obj_file}""")

        objs = " ".join(objs_list)
        compile_rules_str = "\n".join(compile_rules)

        makefile = f"""# 自动生成的Makefile
# 项目: 中文C编译器模块系统
# 生成时间: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CC = gcc
CFLAGS = -Wall -Wextra -std=c99

# 目标文件
OBJS = {objs}

# 最终可执行文件
TARGET = {output_dir}/main

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

# 编译规则（为每个模块单独生成，使用实际文件路径）
{compile_rules_str}

# 清理
clean:
\trm -f $(OBJS) $(TARGET)

.PHONY: all clean
"""
        return makefile

    def export_integration_report(self) -> Dict[str, Any]:
        """导出集成报告"""
        stats = self.resolver.get_module_statistics()
        cycles = self.resolver.detect_cycles()
        missing = self.resolver.find_missing_dependencies()

        return {
            "statistics": stats,
            "dependency_issues": {
                "cycles": cycles,
                "missing_dependencies": missing,
                "total_issues": len(cycles) + len(missing),
            },
            "files": {
                "total_files": len(self.module_files),
                "module_files": list(self.module_files.keys()),
            },
            "recommendations": self._generate_recommendations(stats, cycles, missing),
        }

    def _generate_recommendations(
        self, stats: Dict, cycles: List, missing: List
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if cycles:
            recommendations.append("发现循环依赖，建议重构模块设计以消除循环")

        if missing:
            recommendations.append(
                f"发现{len(missing)}个缺失的模块依赖，请检查模块定义"
            )

        if stats["avg_dependencies_per_module"] > 5:
            recommendations.append("模块平均依赖数较高，考虑模块功能拆分")

        if stats["modules_without_deps"] == len(self.module_files):
            recommendations.append("所有模块都无依赖关系，考虑模块间功能复用")

        return recommendations


def main():
    """测试依赖解析器"""
    print("=== Day 4: 模块依赖解析器测试 ===\n")

    # 创建解析器
    resolver = DependencyResolver()

    # 模拟模块定义
    module_defs = [
        {
            "name": "数学工具",
            "file_path": "math_tools.zhc",
            "imports": [{"module": "基础类型"}],
            "symbols": {
                "public": {"加": "函数", "减": "函数"},
                "private": {"内部计算": "函数"},
            },
            "line_number": 1,
        },
        {
            "name": "基础类型",
            "file_path": "basic_types.zhc",
            "imports": [],
            "symbols": {"public": {"整数": "类型", "浮点数": "类型"}, "private": {}},
            "line_number": 1,
        },
        {
            "name": "图形计算",
            "file_path": "graphics.zhc",
            "imports": [{"module": "数学工具"}, {"module": "基础类型"}],
            "symbols": {
                "public": {"绘制": "函数", "旋转": "函数"},
                "private": {"矩阵运算": "函数"},
            },
            "line_number": 1,
        },
    ]

    # 添加模块
    for module_def in module_defs:
        resolver.add_module(module_def)

    # 检测循环依赖
    cycles = resolver.detect_cycles()
    if cycles:
        print("⚠️  发现循环依赖:")
        for cycle in cycles:
            print(f"  • {' -> '.join(cycle)}")
    else:
        print("✅ 无循环依赖")

    # 计算编译顺序
    order = resolver.calculate_compilation_order()
    print(f"\n📋 编译顺序: {' → '.join(order)}")

    # 获取统计信息
    stats = resolver.get_module_statistics()
    print("\n📊 模块统计:")
    print(f"  模块总数: {stats['total_modules']}")
    print(f"  总依赖数: {stats['total_dependencies']}")
    print(f"  平均依赖数: {stats['avg_dependencies_per_module']:.1f}")
    print(f"  公开符号总数: {stats['total_public_symbols']}")

    # 导出依赖图
    graph = resolver.export_dependency_graph()
    print(f"\n📈 依赖关系图已导出 ({len(graph['modules'])} 个模块)")

    # 测试多文件集成
    integrator = MultiFileIntegrator(resolver)
    for module_def in module_defs:
        integrator.register_module_file(
            str(module_def["name"]),
            str(module_def["file_path"]),
            f"# 模块: {module_def['name']}\n",
        )

    # 生成Makefile
    makefile = integrator.generate_makefile("./build")
    lines = makefile.split("\n")
    print(f"\n🔧 已生成Makefile ({len(lines)} 行)")

    print("\n=== Day 4 核心功能测试完成 ===")


if __name__ == "__main__":
    main()
