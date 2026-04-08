#!/usr/bin/env python3
"""
集成转换器 - 将ModuleParser和CodeConverter结合

功能：
1. 完整解析中文模块代码
2. 转换为C头文件和源文件
3. 生成模块间的依赖关系
4. 提供详细的转换报告
"""

import os
from typing import List, Dict, Tuple

# 使用相对导入，避免 sys.path 魔法
from zhc.parser.module import ModuleParser
from zhc.converter.code import CodeConverter


class IntegratedConverter:
    """集成转换器主类"""

    def __init__(self, verbose: bool = False):
        """
        初始化集成转换器

        Args:
            verbose: 是否显示详细输出
        """
        self.verbose = verbose
        self.parser = ModuleParser()
        self.converter = CodeConverter()
        self.stats = {
            "files_processed": 0,
            "modules_found": 0,
            "imports_processed": 0,
            "symbols_converted": 0,
            "total_errors": 0,
            "total_warnings": 0,
        }

    def process_single_file(
        self, input_file: str, output_dir: str = "."
    ) -> Tuple[bool, Dict]:
        """
        处理单个文件（6步骤编排）

        Returns:
            (success, statistics) 元组
        """
        if self.verbose:
            print(f"\n📄 处理文件: {input_file}")

        # 重置解析器和转换器
        self.parser = ModuleParser()
        self.converter = CodeConverter()

        # Step 1: 读取源文件
        lines, read_ok = self._read_source(input_file)
        if not read_ok:
            return False, self.stats.copy()

        # Step 2: 解析行
        parse_errors, parse_summary = self._parse_lines(lines)
        if self.verbose:
            print("\n" + parse_summary)

        # Step 3: 转换模块
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        header_file = os.path.join(output_dir, f"{base_name}.h")
        source_file = os.path.join(output_dir, f"{base_name}.c")
        modules_converted = self._convert_modules(lines, header_file, source_file)

        # Step 4: 处理导入
        imports_converted = self._handle_imports(source_file)

        # Step 5: 更新统计
        self._update_stats(
            len(self.parser.modules), modules_converted, imports_converted
        )

        # Step 6: 输出结果
        if self.verbose:
            print("\n✅ 转换完成:")
            print(f"  输入文件: {input_file}")
            print(f"  输出头文件: {header_file}")
            print(f"  输出源文件: {source_file}")
            print(f"  转换模块数: {len(self.parser.modules)}")
            print(f"  处理导入数: {imports_converted}")

        success = len(self.converter.get_errors()) == 0
        return success, self.stats.copy()

    # =========================================================================
    # process_single_file 的6个步骤方法
    # =========================================================================

    def _read_source(self, input_file: str) -> Tuple[List[str], bool]:
        """Step 1: 读取源文件"""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                return f.readlines(), True
        except Exception as e:
            print(f"✗ 读取文件失败: {e}")
            return [], False

    def _parse_lines(self, lines: List[str]) -> Tuple[List[Dict], str]:
        """Step 2: 解析行，返回 (parse_errors, parse_summary)"""
        parse_errors = []
        for i, line in enumerate(lines, 1):
            try:
                self.parser.parse_line(line.strip(), i)
            except Exception as e:
                parse_errors.append(
                    {"line": i, "error": str(e), "content": line.strip()}
                )

        parse_summary = self.parser.get_summary()
        if parse_errors:
            print(f"\n⚠️  解析过程中发现 {len(parse_errors)} 个错误:")
            for error in parse_errors:
                print(f"  行{error['line']}: {error['error']}")
                print(f"    内容: {error['content']}")
            self.stats["total_errors"] += len(parse_errors)

        return parse_errors, parse_summary

    def _convert_modules(
        self, lines: List[str], header_file: str, source_file: str
    ) -> int:
        """Step 3: 转换每个模块到 header/source 文件"""
        modules_converted = 0
        for module_name, module_info in self.parser.modules.items():
            module_content = self._extract_module_content(
                module_name, lines, module_info
            )
            header_code, source_code = self.converter.convert_module_declaration(
                module_name, module_content, -1
            )
            mode = "w" if modules_converted == 0 else "a"
            with open(header_file, mode, encoding="utf-8") as f:
                if modules_converted > 0:
                    f.write("\n\n")
                f.write(header_code)
            with open(source_file, mode, encoding="utf-8") as f:
                if modules_converted > 0:
                    f.write("\n\n")
                f.write(source_code)
            modules_converted += 1
        return modules_converted

    def _handle_imports(self, source_file: str) -> int:
        """Step 4: 收集并写入所有模块的导入语句"""
        imports_converted = 0
        all_imports: List[str] = []
        for module_info in self.parser.modules.values():
            for imported_module in module_info.imports:
                if imported_module not in all_imports:
                    all_imports.append(imported_module)

        for imported_module in all_imports:
            import_code = self.converter.convert_import_statement(imported_module, -1)
            with open(source_file, "r+", encoding="utf-8") as f:
                content = f.read()
                f.seek(0, 0)
                f.write(f"{import_code}\n{content}")
            imports_converted += 1

        return imports_converted

    def _update_stats(
        self, modules_count: int, modules_converted: int, imports_count: int
    ) -> None:
        """Step 5: 更新统计"""
        self.stats["files_processed"] += 1
        self.stats["modules_found"] += modules_count
        self.stats["imports_processed"] += imports_count
        self.stats["symbols_converted"] += self.converter.conversion_stats[
            "symbols_converted"
        ]
        self.stats["total_errors"] += len(self.converter.get_errors())
        self.stats["total_warnings"] += len(self.converter.get_warnings())

    def _extract_module_content(
        self, module_name: str, lines: List[str], module_info
    ) -> List[str]:
        """
        从原始代码中提取模块内容

        Args:
            module_name: 模块名
            lines: 原始代码行列表
            module_info: 模块信息对象

        Returns:
            模块内容行列表
        """
        content_lines = []

        # 简化的提取逻辑
        # 在实际实现中，需要精确找到模块的开始和结束位置
        in_module = False
        brace_depth = 0

        for line in lines:
            line = line.strip()

            # 检查是否进入目标模块
            if f"模块 {module_name}" in line and "{" in line:
                in_module = True
                brace_depth = 1
                continue

            if in_module:
                content_lines.append(line)

                # 统计花括号深度
                brace_depth += line.count("{")
                brace_depth -= line.count("}")

                # 检查模块结束
                if brace_depth == 0:
                    break

        return content_lines

    def process_directory(
        self, input_dir: str, output_dir: str = ".", pattern: str = "*.zhc"
    ) -> Dict:
        """
        处理目录中的所有匹配文件

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            pattern: 文件匹配模式

        Returns:
            总体统计信息
        """
        import glob

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 查找所有匹配文件
        search_pattern = os.path.join(input_dir, pattern)
        files = glob.glob(search_pattern)

        if self.verbose:
            print(f"\n📁 处理目录: {input_dir}")
            print(f"  找到 {len(files)} 个匹配文件")

        # 处理每个文件
        total_stats = self.stats.copy()
        successful_files = 0

        for i, file in enumerate(files, 1):
            if self.verbose:
                print(f"\n[{i}/{len(files)}] 处理: {os.path.basename(file)}")

            success, file_stats = self.process_single_file(file, output_dir)

            # 合并统计
            for key in total_stats:
                total_stats[key] += file_stats.get(key, 0)

            if success:
                successful_files += 1

        # 输出目录处理摘要
        if self.verbose:
            print("\n📊 目录处理完成:")
            print(f"  处理文件总数: {len(files)}")
            print(f"  成功文件数: {successful_files}")
            print(f"  失败文件数: {len(files) - successful_files}")
            print(f"  总模块数: {total_stats['modules_found']}")
            print(f"  总导入数: {total_stats['imports_processed']}")
            print(f"  总符号数: {total_stats['symbols_converted']}")

        return total_stats

    def get_conversion_report(self) -> str:
        """
        生成详细的转换报告

        Returns:
            报告字符串
        """
        report = []
        report.append("=" * 60)
        report.append("中文C编译器模块系统转换报告")
        report.append("=" * 60)

        report.append("\n📊 转换统计:")
        for key, value in self.stats.items():
            # 美化键名
            pretty_key = key.replace("_", " ").title()
            report.append(f"  {pretty_key}: {value}")

        # 获取解析器统计
        if hasattr(self.parser, "modules"):
            report.append("\n🔍 模块详情:")
            for module_name, module_info in self.parser.modules.items():
                report.append(f"  {module_name}:")
                report.append(f"    - 公开符号: {len(module_info.public_symbols)}")
                report.append(f"    - 私有符号: {len(module_info.private_symbols)}")
                report.append(f"    - 导入模块: {module_info.imports}")

        # 获取转换器错误和警告
        errors = self.converter.get_errors()
        warnings = self.converter.get_warnings()

        if errors:
            report.append(f"\n❌ 错误 ({len(errors)} 个):")
            for error in errors:
                line_info = f"行{error['line']}" if error["line"] > 0 else "未知行"
                report.append(f"  [{error['type']}] {line_info}: {error['message']}")

        if warnings:
            report.append(f"\n⚠️  警告 ({len(warnings)} 个):")
            for warning in warnings:
                line_info = f"行{warning['line']}" if warning["line"] > 0 else "未知行"
                report.append(
                    f"  [{warning['type']}] {line_info}: {warning['message']}"
                )

        report.append("\n" + "=" * 60)
        report.append("报告结束")
        report.append("=" * 60)

        return "\n".join(report)

    def run_cli(self):
        """运行命令行界面"""
        import argparse

        parser = argparse.ArgumentParser(description="中文C编译器模块系统转换工具")

        parser.add_argument("input", help="输入文件或目录")

        parser.add_argument(
            "-o", "--output", default=".", help="输出目录（默认: 当前目录）"
        )

        parser.add_argument(
            "-p", "--pattern", default="*.zhc", help="文件匹配模式（默认: *.zhc）"
        )

        parser.add_argument("-v", "--verbose", action="store_true", help="显示详细输出")

        args = parser.parse_args()

        # 设置详细模式
        self.verbose = args.verbose

        # 处理输入
        if os.path.isfile(args.input):
            # 单个文件
            success, stats = self.process_single_file(args.input, args.output)
            if success:
                print("✅ 文件转换成功!")
            else:
                print("❌ 文件转换失败!")

        elif os.path.isdir(args.input):
            # 目录
            stats = self.process_directory(args.input, args.output, args.pattern)
            print(f"✅ 目录处理完成! 共处理 {stats['files_processed']} 个文件")

        else:
            print(f"❌ 输入路径不存在: {args.input}")
            return

        # 输出报告
        print(self.get_conversion_report())


def main():
    """主函数"""
    converter = IntegratedConverter(verbose=True)

    # 测试代码
    test_code = """模块 测试模块 {
    公开:
        函数 测试函数(整数型 参数) -> 整数型 {
            返回 参数 * 2;
        }

        整数型 全局常量 = 100;

    私有:
        浮点型 内部数据 = 3.14;
}

导入 工具库;
导入 数学库;
"""

    # 创建测试文件
    test_file = "test_integrated.zhc"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_code)

    print("🔧 测试集成转换器功能")
    print("=" * 50)

    # 处理测试文件
    success, stats = converter.process_single_file(test_file, ".")

    if success:
        print("\n🎉 集成转换器测试成功!")
    else:
        print("\n❌ 集成转换器测试失败!")

    # 清理
    if os.path.exists(test_file):
        os.remove(test_file)

    # 显示生成的文件内容
    if os.path.exists("test_integrated.h"):
        print("\n📄 生成的头文件内容:")
        print("-" * 40)
        with open("test_integrated.h", "r", encoding="utf-8") as f:
            print(f.read())

    if os.path.exists("test_integrated.c"):
        print("\n📄 生成的源文件内容:")
        print("-" * 40)
        with open("test_integrated.c", "r", encoding="utf-8") as f:
            print(f.read())

    # 清理生成的文件
    if os.path.exists("test_integrated.h"):
        os.remove("test_integrated.h")
    if os.path.exists("test_integrated.c"):
        os.remove("test_integrated.c")


if __name__ == "__main__":
    main()
