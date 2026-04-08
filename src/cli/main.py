#!/usr/bin/env python3
"""命令行接口模块 - 提供用户友好的命令行体验"""

import sys
import subprocess
import argparse
import json
import shutil
import platform
import webbrowser
from pathlib import Path
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class CommandHandler(ABC):
    """命令处理器抽象基类 - 命令模式"""

    @abstractmethod
    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        """执行命令，返回退出码"""
        pass


class InitCommand(CommandHandler):
    """init 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print(f"🚀 正在创建项目: {args.project_name}")
        print(f"   模板: {args.template}")

        project_dir = Path(args.project_name)
        project_dir.mkdir(exist_ok=True)

        # 创建标准目录结构
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "tests").mkdir(exist_ok=True)
        (project_dir / "docs").mkdir(exist_ok=True)
        (project_dir / "构建").mkdir(exist_ok=True)

        # 创建配置文件
        config = {
            "项目名称": args.project_name,
            "版本": "1.0.0",
            "作者": "开发者",
            "描述": "一个中文C项目",
            "入口模块": "src/主程序.zhc",
            "模板": args.template,
            "依赖": {},
            "编译选项": {"启用缓存": True, "优化级别": "O2", "输出目录": "./构建"},
        }

        config_file = project_dir / "zhc.config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 根据模板创建示例文件
        template_creators = {
            "console": cli._create_console_template,
            "library": cli._create_library_template,
            "module": cli._create_module_template,
        }
        creator = template_creators.get(args.template)
        if creator:
            creator(project_dir)

        print(f"✅ 项目创建完成: {project_dir}")
        print("📁 目录结构:")
        cli._print_tree(project_dir, max_depth=3)

        return 0


class NewCommand(CommandHandler):
    """new 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print(f"📦 正在创建模块: {args.module_name}")
        print(f"   类型: {args.type}")

        module_file = Path(f"src/{args.module_name}.zhc")
        module_file.parent.mkdir(exist_ok=True)

        # 模板分派表
        template_getters = {
            "util": cli._get_util_template,
            "data": cli._get_data_template,
            "service": cli._get_basic_template,
            "ui": cli._get_basic_template,
        }

        getter = template_getters.get(args.type, cli._get_basic_template)
        template = getter(args.module_name)

        module_file.write_text(template, encoding="utf-8")

        print(f"✅ 模块创建完成: {module_file}")
        print("📝 文件内容预览:")
        print("-" * 40)
        print(template[:500] + ("..." if len(template) > 500 else ""))
        print("-" * 40)

        return 0


class BuildCommand(CommandHandler):
    """build 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print("🔨 正在编译项目...")

        config_file = Path("zhc.config.json")
        if not config_file.exists():
            print("❌ 错误: 找不到 zhc.config.json")
            print("   请在项目根目录运行此命令")
            return 1

        build_cmd = ["python3", "-m", "src.__main__"]

        # 参数映射表
        arg_flags = {
            "release": "--release",
            "debug": "--debug",
            "cache": "--cache",
            "verbose": "--verbose",
        }

        for attr, flag in arg_flags.items():
            if getattr(args, attr, False):
                build_cmd.append(flag)

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        entry_module = config.get("入口模块", "src/主程序.zhc")
        build_cmd.append(entry_module)

        result = subprocess.run(build_cmd)

        if result.returncode == 0:
            print("✅ 编译成功")
            return 0
        else:
            print("❌ 编译失败")
            return result.returncode


class RunCommand(CommandHandler):
    """run 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print("🚀 正在运行项目...")

        # 先构建项目
        build_args = argparse.Namespace(
            release=False, debug=False, cache=False, verbose=False
        )
        if cli._command_handlers["build"].execute(build_args, cli) != 0:
            return 1

        # 确定运行文件
        if args.file:
            run_file = Path(args.file)
        else:
            config_file = Path("zhc.config.json")
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                project_name = config.get("项目名称", "项目")
            else:
                project_name = "程序"
            run_file = Path("构建") / project_name

        if not run_file.exists():
            print(f"❌ 错误: 找不到可执行文件: {run_file}")
            return 1

        run_cmd = [str(run_file)]
        if args.args:
            run_cmd.extend(args.args.split())

        print(f"📟 运行命令: {' '.join(run_cmd)}")
        result = subprocess.run(run_cmd)

        return result.returncode


class TestCommand(CommandHandler):
    """test 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print("🧪 正在运行测试...")

        test_dir = Path("tests")
        if not test_dir.exists():
            print("ℹ️  没有找到 tests 目录")
            return 0

        test_files = list(test_dir.glob("*.zhc"))
        if not test_files:
            print("ℹ️  没有找到测试文件")
            return 0

        print(f"📄 找到 {len(test_files)} 个测试文件")

        success_count = 0
        for test_file in test_files:
            print(f"\n🔧 测试: {test_file.name}")

            compile_cmd = [
                "python3",
                "-m",
                "src.__main__",
                str(test_file),
                "--output-dir",
                "构建/测试",
            ]
            compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

            if compile_result.returncode != 0:
                print(f"❌ 编译失败: {test_file}")
                print(compile_result.stderr)
                continue

            test_name = test_file.stem
            executable = Path("构建/测试") / test_name

            if executable.exists():
                run_result = subprocess.run(
                    [str(executable)], capture_output=True, text=True
                )

                if run_result.returncode == 0:
                    print(f"✅ 测试通过: {test_file}")
                    success_count += 1
                else:
                    print(f"❌ 测试失败: {test_file}")
                    print(run_result.stderr)
            else:
                print(f"⚠️  找不到可执行文件: {executable}")

        if args.coverage:
            print("⚠️ 覆盖率报告功能暂未实现")

        total_count = len(test_files)
        print(
            f"\n📊 测试结果: {success_count}/{total_count} 通过 ({success_count / total_count * 100:.1f}%)"
        )

        if success_count == total_count:
            print("🎉 所有测试通过！")
            return 0
        else:
            print("❌ 有测试失败")
            return 1


class DocCommand(CommandHandler):
    """doc 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print("📚 正在生成文档...")

        readme_content = """# 中文C项目

## 项目结构

```
项目/
├── src/           # 源代码
├── tests/         # 测试代码
├── docs/          # 文档
├── 构建/          # 构建输出
└── zhc.config.json # 项目配置
```

## 构建指南

```bash
# 安装依赖
无需外部依赖

# 构建项目
zhc build

# 运行项目
zhc run

# 运行测试
zhc test
```

## API文档

TODO: 自动生成API文档
"""

        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)

        readme_file = docs_dir / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")

        print(f"✅ 文档已生成: {readme_file}")

        if args.open:
            if args.format == "html":
                html_file = docs_dir / "index.html"
                processed_content = readme_content.replace("\n", "<br>").replace(
                    "```", "<pre>"
                )
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{Path.cwd().name} - 文档</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
{processed_content}
</body>
</html>
"""
                html_file.write_text(html_content, encoding="utf-8")
                webbrowser.open(f"file://{html_file.absolute()}")

        return 0


class AddCommand(CommandHandler):
    """add 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print(f"➕ 正在添加依赖: {args.module_path}")

        config_file = Path("zhc.config.json")
        if not config_file.exists():
            print("❌ 错误: 找不到 zhc.config.json")
            return 1

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "依赖" not in config:
            config["依赖"] = {}

        config["依赖"][args.module_path] = args.version or "latest"

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ 依赖添加成功: {args.module_path}")
        return 0


class RemoveCommand(CommandHandler):
    """remove 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print(f"➖ 正在移除依赖: {args.module_name}")

        config_file = Path("zhc.config.json")
        if not config_file.exists():
            print("❌ 错误: 找不到 zhc.config.json")
            return 1

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "依赖" in config and args.module_name in config["依赖"]:
            del config["依赖"][args.module_name]

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"✅ 依赖移除成功: {args.module_name}")
        else:
            print(f"⚠️  依赖不存在: {args.module_name}")

        return 0


class UpdateCommand(CommandHandler):
    """update 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print("🔄 正在更新依赖...")
        print("✅ 依赖更新完成（模拟）")
        return 0


class CleanCommand(CommandHandler):
    """clean 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print("🧹 正在清理项目...")

        dirs_to_clean = ["构建", ".zhc_cache"]
        for dir_name in dirs_to_clean:
            dir_path = Path(dir_name)
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✅ 清理目录: {dir_path}")

        if args.all:
            patterns = ["*.c", "*.o", "*.exe", "*.out"]
            for pattern in patterns:
                for file in Path(".").glob(pattern):
                    file.unlink()
                    print(f"✅ 清理文件: {file}")

        print("🎉 项目清理完成")
        return 0


class CacheCommand(CommandHandler):
    """cache 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        if args.clear:
            print("🗑️  正在清理缓存...")
            cache_dir = Path(".zhc_cache")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                print(f"✅ 缓存已清理: {cache_dir}")
            else:
                print("ℹ️  没有找到缓存目录")

        if args.stats:
            print("📊 缓存统计:")
            cache_dir = Path(".zhc_cache")
            if cache_dir.exists():
                total_size = 0
                file_count = 0
                for file in cache_dir.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size
                        file_count += 1

                print(f"   文件数: {file_count}")
                print(f"   总大小: {total_size / 1024 / 1024:.2f} MB")
            else:
                print("   缓存目录不存在")

        return 0


class InfoCommand(CommandHandler):
    """info 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        info: Dict[str, Any] = {
            "系统": platform.system(),
            "系统版本": platform.version(),
            "Python版本": sys.version,
            "Python路径": sys.executable,
            "当前目录": str(Path.cwd()),
            "项目根目录": str(Path(__file__).parent.parent) if __file__ else "未知",
            "中文C版本": "v6.0 (支持模块系统)",
            "模块系统": "已启用",
        }

        if args.json:
            print(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            print("🖥️  系统信息:")
            for key, value in info.items():
                print(f"  {key}: {value}")

        return 0


class CompileCommand(CommandHandler):
    """compile 命令处理器"""

    def execute(self, args: argparse.Namespace, cli: "CommandLineInterface") -> int:
        print(f"🔧 编译文件: {args.file}")

        compile_cmd = ["python3", "-m", "src.__main__"]

        if args.output:
            compile_cmd.extend(["-o", args.output])

        compile_cmd.append(args.file)

        result = subprocess.run(compile_cmd)

        return result.returncode


class CommandLineInterface:
    """统一的命令行接口 - 使用命令模式"""

    # 命令处理器分派表
    _command_handlers: Dict[str, CommandHandler] = {
        "init": InitCommand(),
        "new": NewCommand(),
        "build": BuildCommand(),
        "run": RunCommand(),
        "test": TestCommand(),
        "doc": DocCommand(),
        "add": AddCommand(),
        "remove": RemoveCommand(),
        "update": UpdateCommand(),
        "clean": CleanCommand(),
        "cache": CacheCommand(),
        "info": InfoCommand(),
        "compile": CompileCommand(),
    }

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            prog="zhc",
            description="中文C编译器 - 现代化的中文编程工具",
            epilog="""
使用示例:
  快速开始:
    zhc hello.zhc                      # 编译单个文件
    zhc run hello.zhc                  # 编译并运行

  模块项目:
    zhc init 我的项目                  # 创建新项目
    zhc build                          # 编译当前项目
    zhc run                            # 运行当前项目

  开发工具:
    zhc new 模块名                     # 创建新模块
    zhc test                           # 运行测试
    zhc doc                            # 生成文档

  项目管理:
    zhc add 模块路径                   # 添加模块依赖
    zhc remove 模块名                  # 移除模块依赖
    zhc update                         # 更新所有依赖

  系统工具:
    zhc clean                          # 清理构建文件
    zhc cache --clear                  # 清理编译缓存
    zhc info                           # 显示系统信息
            """,
        )

        # 子命令
        subparsers = parser.add_subparsers(dest="command", help="命令")

        # init 命令
        init_parser = subparsers.add_parser("init", help="初始化新项目")
        init_parser.add_argument("project_name", help="项目名称")
        init_parser.add_argument(
            "--template",
            choices=["console", "library", "module"],
            default="console",
            help="项目模板",
        )

        # new 命令
        new_parser = subparsers.add_parser("new", help="创建新模块")
        new_parser.add_argument("module_name", help="模块名称")
        new_parser.add_argument(
            "--type",
            choices=["util", "data", "service", "ui"],
            default="util",
            help="模块类型",
        )

        # build 命令
        build_parser = subparsers.add_parser("build", help="编译项目")
        build_parser.add_argument("--release", action="store_true", help="发布模式编译")
        build_parser.add_argument("--debug", action="store_true", help="调试模式编译")
        build_parser.add_argument("--cache", action="store_true", help="启用缓存")
        build_parser.add_argument(
            "--verbose", "-v", action="store_true", help="详细输出"
        )

        # run 命令
        run_parser = subparsers.add_parser("run", help="编译并运行")
        run_parser.add_argument(
            "file", nargs="?", help="运行文件（不指定则运行主程序）"
        )
        run_parser.add_argument("--args", help="程序参数")

        # test 命令
        test_parser = subparsers.add_parser("test", help="运行测试")
        test_parser.add_argument("--module", help="测试特定模块")
        test_parser.add_argument(
            "--coverage", action="store_true", help="生成测试覆盖率报告"
        )

        # doc 命令
        doc_parser = subparsers.add_parser("doc", help="生成文档")
        doc_parser.add_argument("--open", action="store_true", help="生成后打开文档")
        doc_parser.add_argument(
            "--format",
            choices=["html", "markdown", "pdf"],
            default="html",
            help="文档格式",
        )

        # add 命令
        add_parser = subparsers.add_parser("add", help="添加模块依赖")
        add_parser.add_argument("module_path", help="模块路径或名称")
        add_parser.add_argument("--version", help="模块版本")

        # remove 命令
        remove_parser = subparsers.add_parser("remove", help="移除模块依赖")
        remove_parser.add_argument("module_name", help="模块名称")

        # update 命令
        update_parser = subparsers.add_parser("update", help="更新所有依赖")
        update_parser.add_argument("--force", action="store_true", help="强制更新")

        # clean 命令
        clean_parser = subparsers.add_parser("clean", help="清理构建文件")
        clean_parser.add_argument("--all", action="store_true", help="清理所有生成文件")

        # cache 命令
        cache_parser = subparsers.add_parser("cache", help="管理编译缓存")
        cache_parser.add_argument("--clear", action="store_true", help="清理缓存")
        cache_parser.add_argument("--stats", action="store_true", help="显示缓存统计")

        # info 命令
        info_parser = subparsers.add_parser("info", help="显示系统信息")
        info_parser.add_argument("--json", action="store_true", help="JSON格式输出")

        # 直接编译文件的快捷方式
        compile_parser = subparsers.add_parser("compile", help="编译文件（快捷方式）")
        compile_parser.add_argument("file", help="要编译的文件")
        compile_parser.add_argument("-o", "--output", help="输出文件")

        return parser

    def parse_args(self, args: Optional[List[str]] = None):
        """解析命令行参数"""
        if args is None:
            args = sys.argv[1:]

        # 如果没有参数，显示帮助
        if not args:
            self.parser.print_help()
            return None

        return self.parser.parse_args(args)

    def execute(self, args):
        """执行命令 - 使用dispatch table"""
        command = args.command
        handler = self._command_handlers.get(command)

        if handler:
            return handler.execute(args, self)

        # 如果没有指定命令，尝试直接编译文件
        if hasattr(args, "file") and args.file:
            compile_cmd = ["python3", "-m", "src.__main__", args.file]
            result = subprocess.run(compile_cmd)
            return result.returncode

        print("❌ 错误: 未知命令或缺少参数")
        self.parser.print_help()
        return 1

    def _create_console_template(self, project_dir: Path):
        """创建控制台应用模板"""
        # 主程序
        main_file = project_dir / "src" / "主程序.zhc"
        main_file.write_text(
            """模块 主程序 {
    公开:
        函数 主函数() -> 整数型 {
            打印("你好，世界！\\n");
            返回 0;
        }
}
""",
            encoding="utf-8",
        )

        # README
        readme_file = project_dir / "README.md"
        readme_file.write_text(
            f"""# {project_dir.name}

一个中文C控制台应用程序。

## 快速开始

```bash
# 编译项目
zhc build

# 运行程序
zhc run
```

## 项目结构

```
{project_dir.name}/
├── src/           # 源代码
├── tests/         # 测试代码
├── docs/          # 文档
├── 构建/          # 构建输出
└── zhc.config.json # 项目配置
```
""",
            encoding="utf-8",
        )

    def _create_library_template(self, project_dir: Path):
        """创建库项目模板"""
        # 库模块
        lib_file = project_dir / "src" / "我的库.zhc"
        lib_file.write_text(
            """模块 我的库 {
    公开:
        // 常量
        常量 版本号 = "1.0.0";

        // 工具函数
        函数 问候(参数 字符串型 名字) -> 字符串型 {
            静态 字符型 缓冲区[100];
            格式化打印到字符串(缓冲区, "你好，%s！", 名字);
            返回 缓冲区;
        }

        // 数学函数
        函数 平方(参数 整数型 x) -> 整数型 {
            返回 x * x;
        }

        函数 立方(参数 整数型 x) -> 整数型 {
            返回 x * x * x;
        }

    私有:
        // 内部辅助函数
        静态 函数 验证输入(参数 整数型 n) -> 逻辑型 {
            返回 n >= 0;
        }
}
""",
            encoding="utf-8",
        )

        # 测试文件
        test_file = project_dir / "tests" / "测试_我的库.zhc"
        test_file.write_text(
            """导入 我的库;

模块 测试 {
    公开:
        函数 测试主函数() -> 整数型 {
            打印("测试 我的库 模块...\\n");

            // 测试问候函数
            字符串型 问候语 = 我的库::问候("小明");
            打印("问候测试: %s\\n", 问候语);

            // 测试数学函数
            整数型 结果 = 我的库::平方(5);
            打印("平方测试: 5² = %d\\n", 结果);

            结果 = 我的库::立方(3);
            打印("立方测试: 3³ = %d\\n", 结果);

            打印("✅ 所有测试通过！\\n");
            返回 0;
        }
}
""",
            encoding="utf-8",
        )

    def _create_module_template(self, project_dir: Path):
        """创建模块项目模板"""
        # 工具模块
        tools_file = project_dir / "src" / "工具" / "数学工具.zhc"
        tools_file.parent.mkdir(exist_ok=True)
        tools_file.write_text(
            """模块 数学工具 {
    公开:
        常量 PI = 3.1415926;

        函数 加法(参数 整数型 a, 整数型 b) -> 整数型 {
            返回 a + b;
        }

        函数 乘法(参数 整数型 a, 整数型 b) -> 整数型 {
            返回 a * b;
        }
}
""",
            encoding="utf-8",
        )

        # 主程序
        main_file = project_dir / "src" / "主程序.zhc"
        main_file.write_text(
            """导入 工具::数学工具;

模块 主程序 {
    公开:
        函数 主函数() -> 整数型 {
            打印("模块项目示例\\n");

            整数型 和 = 数学工具::加法(10, 20);
            整数型 积 = 数学工具::乘法(5, 6);

            打印("10 + 20 = %d\\n", 和);
            打印("5 × 6 = %d\\n", 积);
            打印("π ≈ %f\\n", 数学工具::PI);

            返回 0;
        }
}
""",
            encoding="utf-8",
        )

    def _get_util_template(self, module_name: str) -> str:
        """获取工具模块模板"""
        return f"""模块 {module_name} {{
    公开:
        // 常量定义
        常量 版本号 = "1.0.0";

        // 工具函数
        函数 字符串转整数(参数 字符串型 字符串) -> 整数型 {{
            整数型 结果 = 0;
            整数型 i = 0;

            判断 (字符串[i] != '\\0') {{
                如果 (字符串[i] >= '0' 并且 字符串[i] <= '9') {{
                    结果 = 结果 * 10 + (字符串[i] - '0');
                }} 否则 {{
                    跳出;
                }}
                i++;
            }}

            返回 结果;
        }}

        函数 整数转字符串(参数 整数型 数字, 参数 字符型* 缓冲区) -> 字符串型 {{
            如果 (数字 == 0) {{
                缓冲区[0] = '0';
                缓冲区[1] = '\\0';
                返回 缓冲区;
            }}

            整数型 i = 0;
            整数型 临时 = 数字;

            如果 (数字 < 0) {{
                缓冲区[i++] = '-';
                临时 = -临时;
            }}

            整数型 开始 = i;

            判断 (临时 > 0) {{
                缓冲区[i++] = (临时 % 10) + '0';
                临时 /= 10;
            }}

            缓冲区[i] = '\\0';

            // 反转数字部分
            整数型 结束 = i - 1;
            判断 (开始 < 结束) {{
                字符型 临时字符 = 缓冲区[开始];
                缓冲区[开始] = 缓冲区[结束];
                缓冲区[结束] = 临时字符;
                开始++;
                结束--;
            }}

            返回 缓冲区;
        }}

    私有:
        // 内部辅助函数
        静态 函数 是数字(参数 字符型 c) -> 逻辑型 {{
            返回 c >= '0' 并且 c <= '9';
        }}
}}
"""

    def _get_data_template(self, module_name: str) -> str:
        """获取数据模块模板"""
        return f"""模块 {module_name} {{
    公开:
        // 数据结构
        结构体 节点 {{
            {module_name}::数据型 数据;
            节点* 下一个;
        }};

        结构体 列表 {{
            节点* 头;
            节点* 尾;
            整数型 大小;
        }};

        // 列表操作
        函数 创建列表() -> 列表*;
        函数 销毁列表(参数 列表* 列表指针);
        函数 添加元素(参数 列表* 列表指针, 参数 {module_name}::数据型 数据);
        函数 获取元素(参数 列表* 列表指针, 参数 整数型 索引) -> {module_name}::数据型;
        函数 移除元素(参数 列表* 列表指针, 参数 整数型 索引);
        函数 列表大小(参数 列表* 列表指针) -> 整数型;

    私有:
        // 内部类型
        别名 数据型 = 整数型;  // 可根据需要修改

        // 内部函数
        静态 节点* 创建节点(参数 {module_name}::数据型 数据);
        静态 空型 销毁节点(参数 节点* 节点指针);
}}
"""

    def _get_basic_template(self, module_name: str) -> str:
        """获取基础模块模板"""
        return f"""模块 {module_name} {{
    公开:
        // 模块描述
        常量 模块名称 = "{module_name}";
        常量 版本号 = "1.0.0";

        // 示例函数
        函数 示例函数() -> 整数型 {{
            打印("这是 {{模块名称}} 模块的示例函数\\n");
            返回 0;
        }}

    私有:
        // 私有函数和变量
        静态 整数型 内部计数器 = 0;

        静态 函数 内部函数() -> 整数型 {{
            返回 内部计数器++;
        }}
}}
"""

    def _print_tree(
        self,
        directory: Path,
        prefix: str = "",
        max_depth: int = 3,
        current_depth: int = 0,
    ):
        """打印目录树"""
        if current_depth >= max_depth:
            return

        # 获取目录内容
        try:
            items = list(directory.iterdir())
        except (PermissionError, OSError):
            return

        # 排序：先目录后文件，按名称排序
        items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "

            print(prefix + connector + item.name)

            if item.is_dir():
                extension = "    " if is_last else "│   "
                self._print_tree(item, prefix + extension, max_depth, current_depth + 1)


def main():
    """命令行接口主函数"""
    cli = CommandLineInterface()
    args = cli.parse_args()

    if args:
        return cli.execute(args)
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
