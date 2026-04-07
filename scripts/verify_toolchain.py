#!/usr/bin/env python3
# =============================================================================
# ZHC开发工具链验证脚本
# =============================================================================
# 用途：快速检查所有开发工具是否正确安装和配置
# 使用方法：
#   python3 scripts/verify_toolchain.py
#   或直接执行（需要chmod +x）:
#   ./scripts/verify_toolchain.py
#
# 作者: ZHC团队
# 创建日期: 2026-04-07
# =============================================================================

import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class ToolChainVerifier:
    """开发工具链验证器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: List[Tuple[str, bool, str]] = []
        
        # 自动查找用户安装的工具路径（解决PATH不在系统环境中的问题）
        self.user_bin = Path.home() / "Library" / "Python" / "3.9" / "bin"
        
        def resolve_cmd(name: str) -> str:
            """查找可执行文件的实际路径"""
            # 先在PATH中找
            path = shutil.which(name)
            if path:
                return path
            # 再在用户Python bin目录找
            user_path = self.user_bin / name
            if user_path.exists():
                return str(user_path)
            # 都找不到就返回原名（会报错）
            return name
        
        black_path = resolve_cmd('black')
        ruff_path = resolve_cmd('ruff')
        mypy_path = resolve_cmd('mypy')
        pytest_path = resolve_cmd('pytest')
        
        self.tools = {
            'black': {
                'name': 'Black (代码格式化)',
                'command': [black_path, '--version'],
                'test_cmd': [black_path, '--check', '--diff', 'src/parser/__init__.py'],
                'required': True,
                'color': '\033[94m',  # 蓝色
            },
            'ruff': {
                'name': 'Ruff (快速Linter)',
                'command': [ruff_path, '--version'],
                'test_cmd': [ruff_path, 'check', 'src/parser/parser.py'],
                'required': True,
                'color': '\033[92m',  # 绿色
            },
            'mypy': {
                'name': 'MyPy (类型检查)',
                'command': [mypy_path, '--version'],
                'test_cmd': [mypy_path, 'src/parser/lexer.py', '--no-error-summary'],
                'required': True,
                'color': '\033[93m',  # 黄色
            },
            'pytest': {
                'name': 'Pytest (单元测试)',
                'command': [pytest_path, '--version'],
                'test_cmd': [pytest_path, '--co', '-q', 'tests/'],
                'required': False,  # 可选，但推荐
                'color': '\033[95m',  # 紫色
            },
        }
    
    def run_command(self, cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
        """执行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except FileNotFoundError:
            return -1, '', f"命令未找到: {cmd[0]}"
        except subprocess.TimeoutExpired:
            return -1, '', f"命令超时 ({timeout}秒)"
    
    def check_tool(self, tool_id: str) -> bool:
        """检查单个工具"""
        tool = self.tools[tool_id]
        
        print(f"\n{tool['color']}▶ 检查 {tool['name']}...\033[0m")
        
        returncode, stdout, stderr = self.run_command(tool['command'])
        
        if returncode == 0:
            version_info = stdout.split('\n')[0] if stdout else '版本信息未知'
            print(f"  ✅ 已安装 - {version_info}")
            self.results.append((tool['name'], True, version_info))
            return True
        else:
            error_msg = stderr if stderr else stdout if stdout else "安装失败或未找到"
            status = "⚠️  未找到 (可选)" if not tool['required'] else "❌ 未安装 (必需)"
            print(f"  {status}")
            print(f"     原因: {error_msg[:100]}")
            self.results.append((tool['name'], False, error_msg))
            return not tool['required']
    
    def check_config_file(self, filename: str) -> bool:
        """检查配置文件是否存在"""
        filepath = self.project_root / filename
        
        print(f"\n\033[96m▶ 检查配置文件: {filename}\033[0m")
        
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            lines_count = len(filepath.read_text(encoding='utf-8').splitlines())
            print(f"  ✅ 存在 - {lines_count:,} 行, {size_kb:.1f} KB")
            
            # 验证TOML格式（如果是.toml文件）
            if filename.endswith('.toml'):
                try:
                    import tomllib
                    with open(filepath, 'rb') as f:
                        tomllib.load(f)
                    print(f"  ✅ TOML语法正确")
                except ImportError:
                    # Python < 3.11，尝试用tomli或跳过
                    try:
                        import toml
                        toml.load(str(filepath))
                        print(f"  ✅ TOML语法正确")
                    except ImportError:
                        print(f"  ℹ️  无法验证TOML语法（缺少toml/tomllib库）")
                except Exception as e:
                    print(f"  ❌ TOML语法错误: {e}")
                    return False
            
            self.results.append((f"配置文件:{filename}", True, f"{lines_count}行"))
            return True
        else:
            print(f"  ❌ 不存在")
            self.results.append((f"配置文件:{filename}", False, "文件不存在"))
            return False
    
    def test_tool_functionality(self, tool_id: str) -> bool:
        """测试工具功能是否正常"""
        tool = self.tools[tool_id]
        
        print(f"\n{tool['color']}🧪 测试 {tool['name']} 功能...\033[0m")
        
        # 使用工具配置中的test_cmd
        if 'test_cmd' in tool and tool['test_cmd']:
            tc = tool['test_cmd']
            desc = '功能测试'
            returncode, stdout, stderr = self.run_command(tc)
            
            if returncode == 0:
                print(f"  ✅ {desc} - 正常工作")
                return True
            elif returncode == 1:
                # 对于linting工具，返回1可能意味着发现了问题（这是正常的）
                print(f"  ⚠️  {desc} - 发现问题（这是正常的，说明工具在工作）")
                output_preview = (stdout or stderr)[:200]
                if output_preview:
                    print(f"     输出预览:\n{output_preview}...")
                return True
            else:
                print(f"  ❌ {desc} - 执行失败 (exit code: {returncode})")
                err_preview = (stderr or stdout)[:150]
                if err_preview:
                    print(f"     错误: {err_preview}")
                return False
        else:
            print(f"  ℹ️  跳过功能测试（未配置测试命令）")
            return True
    
    def generate_report(self) -> str:
        """生成验证报告"""
        report = []
        report.append("\n" + "=" * 70)
        report.append("🔍 ZHC开发工具链验证报告".center(66))
        report.append("=" * 70)
        
        # 统计信息
        total = len(self.results)
        passed = sum(1 for _, ok, _ in self.results if ok)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        report.append(f"\n📊 总体状态: {passed}/{total} 通过 ({pass_rate:.0f}%)\n")
        
        # 详细结果
        report.append("─" * 70)
        for name, ok, detail in self.results:
            status = "✅ 通过" if ok else "❌ 失败"
            report.append(f"  {status:<10} | {name:<30} | {detail[:35]}")
        report.append("─" * 70)
        
        # 建议
        if failed > 0:
            report.append("\n⚠️  建议操作:")
            for name, ok, _ in self.results:
                if not ok:
                    if 'Black' in name or 'Ruff' in name or 'MyPy' in name:
                        report.append(f"  • 安装 {name}: pip3 install {name.lower()}")
                    elif '配置文件:' in name:
                        filename = name.split(':')[1]
                        report.append(f"  • 创建 {filename}: 参考 docs/QUICK_FIX_GUIDE.md")
        
        # 快速参考命令
        report.append("\n📖 日常使用命令:")
        report.append("  • 格式化代码:       black src/ tests/")
        report.append("  • 检查代码质量:     ruff check src/")
        report.append("  • 自动修复问题:     ruff check --fix src/")
        report.append("  • 类型检查:         mypy src/")
        report.append("  • 运行测试:         pytest tests/ -v")
        report.append("  • 完整质量检查:     scripts/verify_toolchain.py")
        
        report.append("\n" + "=" * 70 + "\n")
        
        return "\n".join(report)
    
    def run_all_checks(self) -> int:
        """运行所有检查"""
        print("\n" + "🚀" * 25)
        print("\033[1;96m" + " " * 15 + "ZHC 开发工具链验证器" + " " * 15 + "\033[0m")
        print("🚀" * 25)
        print(f"\n📍 项目目录: {self.project_root}")
        
        # 1. 检查所有工具
        print("\n\033[1m" + "━" * 50 + "\033[0m")
        print("\033[1m阶段 1/3: 检查工具安装\033[0m")
        print("\033[1m" + "━" * 50 + "\033[0m")
        
        all_tools_ok = True
        for tool_id in self.tools:
            if not self.check_tool(tool_id):
                if self.tools[tool_id]['required']:
                    all_tools_ok = False
        
        # 2. 检查配置文件
        print("\n\033[1m" + "━" * 50 + "\033[0m")
        print("\033[1m阶段 2/3: 检查配置文件\033[0m")
        print("\033[1m" + "━" * 50 + "\033[0m")
        
        config_files = ['pyproject.toml']
        for config_file in config_files:
            self.check_config_file(config_file)
        
        # 3. 测试工具功能（仅对已安装的工具）
        print("\n\033[1m" + "━" * 50 + "\033[0m")
        print("\033[1m阶段 3/3: 测试工具功能\033[0m")
        print("\033[1m" + "━" * 50 + "\033[0m")
        
        for tool_id in self.tools:
            _, is_installed, _ = next(
                ((n, o, d) for n, o, d in self.results if n.startswith(self.tools[tool_id]['name'].split('(')[0])),
                (None, False, '')
            )
            if is_installed:
                self.test_tool_functionality(tool_id)
        
        # 4. 生成报告
        report = self.generate_report()
        print(report)
        
        # 返回退出码
        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        
        if passed == total:
            print("✨ 所有检查通过！工具链已准备就绪。")
            return 0
        elif passed >= total * 0.7:
            print("⚠️  大部分检查通过，但存在一些问题。建议修复后重试。")
            return 1
        else:
            print("❌ 多项检查失败。请按照上方建议安装和配置所需工具。")
            return 2


def main():
    """主函数"""
    verifier = ToolChainVerifier()
    exit_code = verifier.run_all_checks()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
