"""
ZHC包管理器自动补全器
Auto-completer for ZHC Package Manager

提供命令行Tab补全支持，包括中英文命令、包名、关键词等。
"""

import os
from typing import List
from ..pkg_manager import CommandMapper


class ZHCCompleter:
    """包管理器补全器"""

    def __init__(self, install_dir: str = "~/.zhc/packages"):
        self.install_dir = os.path.expanduser(install_dir)
        self.command_mapper = CommandMapper()

    def get_all_commands(self) -> List[str]:
        """
        获取所有可用命令

        Returns:
            命令列表（中英文+别名）
        """
        # 中文命令
        cn_commands = list(CommandMapper.CN_TO_EN.keys())

        # 英文命令
        en_commands = list(CommandMapper.CN_TO_EN.values())

        # 合并去重
        all_commands = list(set(cn_commands + en_commands))
        all_commands.sort()

        return all_commands

    def complete_command(self, prefix: str) -> List[str]:
        """
        补全命令

        Args:
            prefix: 命令前缀

        Returns:
            匹配的命令列表
        """
        commands = self.get_all_commands()

        # 不区分大小写的模糊匹配
        prefix_lower = prefix.lower()
        matches = [cmd for cmd in commands if cmd.lower().startswith(prefix_lower)]

        return matches

    def complete_package(self, prefix: str) -> List[str]:
        """
        补全包名

        Args:
            prefix: 包名前缀

        Returns:
            匹配的包名列表
        """
        if not os.path.exists(self.install_dir):
            return []

        packages = []
        for item in os.listdir(self.install_dir):
            item_path = os.path.join(self.install_dir, item)
            if os.path.isdir(item_path):
                packages.append(item)

        # 前缀匹配
        matches = [pkg for pkg in packages if pkg.startswith(prefix)]
        matches.sort()

        return matches

    def complete_keyword(self, prefix: str) -> List[str]:
        """
        补全搜索关键词

        Args:
            prefix: 关键词前缀

        Returns:
            匹配的关键词列表
        """
        # 预定义的关键词（可以从注册表动态获取）
        keywords = [
            "网络",
            "通信",
            "HTTP",
            "TCP",
            "UDP",
            "数学",
            "运算",
            "计算",
            "统计",
            "文件",
            "IO",
            "读写",
            "存储",
            "系统",
            "工具",
            "调试",
            "日志",
            "图形",
            "界面",
            "UI",
            "窗口",
            "数据库",
            "SQL",
            "ORM",
            "存储",
            "加密",
            "安全",
            "哈希",
            "签名",
            "测试",
            "单元测试",
            "集成测试",
            "文档",
            "生成器",
            "模板",
        ]

        # 前缀匹配
        matches = [kw for kw in keywords if kw.lower().startswith(prefix.lower())]
        matches.sort()

        return matches

    def complete(
        self, command: str, current_word: str, prev_word: str = None
    ) -> List[str]:
        """
        智能补全

        Args:
            command: 当前命令
            current_word: 当前正在输入的词
            prev_word: 前一个词（用于上下文判断）

        Returns:
            补全建议列表
        """
        # 如果是第一个词（命令本身）
        if not prev_word:
            return self.complete_command(current_word)

        # 根据前一个词判断补全类型
        normalized_prev = CommandMapper.normalize(prev_word)

        # 安装命令 → 补全包名
        if normalized_prev in ["install"]:
            return self.complete_package(current_word)

        # 搜索命令 → 补全关键词
        if normalized_prev == "search":
            return self.complete_keyword(current_word)

        # 卸载/更新/验证/信息命令 → 补全已安装包名
        if normalized_prev in ["uninstall", "update", "verify", "info"]:
            return self.complete_package(current_word)

        # 其他情况
        return []

    def get_command_help(self, command: str) -> str:
        """
        获取命令帮助信息

        Args:
            command: 命令名

        Returns:
            帮助文本
        """
        helps = {
            "安装": "安装包及依赖（用法：安装 <包名>[@版本]）",
            "发布": "发布当前包到注册表",
            "搜索": "搜索包（用法：搜索 <关键词>）",
            "列表": "列出已安装的包",
            "卸载": "卸载包（用法：卸载 <包名>）",
            "更新": "更新包（用法：更新 <包名>）",
            "验证": "验证包完整性（用法：验证 <包名>）",
            "信息": "查看包信息（用法：信息 <包名>）",
            "帮助": "显示帮助信息",
            "初始化": "初始化新包",
        }

        # 转换为中文命令
        cn_command = (
            CommandMapper.to_chinese(command)
            if command in CommandMapper.EN_TO_CN
            else command
        )

        return helps.get(cn_command, f"命令: {command}")


def install_bash_completion():
    """安装Bash补全脚本"""

    script = """# ZHC包管理器自动补全（Bash）
# 文件：/etc/bash_completion.d/zhc

_zhc_complete() {
    local cur prev words cword

    COMPREPLY=()
    _init_completion || return

    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # 获取Python补全器
    local completions=$(python3 -c "
from zhc.package.completion import ZHCCompleter
completer = ZHCCompleter()
prev = '${prev}' if ${COMP_CWORD} > 1 else None
completions = completer.complete('${prev}' if prev else '', '${cur}', prev)
print(' '.join(completions))
" 2>/dev/null)

    if [[ -n "$completions" ]]; then
        COMPREPLY=( $(compgen -W "$completions" -- "$cur") )
    fi

    return 0
}

complete -F _zhc_complete zhc
"""

    return script


def install_zsh_completion():
    """安装Zsh补全脚本"""

    script = """# ZHC包管理器自动补全（Zsh）
# 文件：~/.zsh/completion/_zhc
#compdef zhc

_zhc() {
    local -a commands packages keywords

    # 中文命令
    commands=(
        '安装:安装包及依赖'
        '发布:发布包到注册表'
        '搜索:搜索包'
        '列表:列出已安装包'
        '卸载:卸载包'
        '更新:更新包'
        '验证:验证包完整性'
        '信息:查看包信息'
        '帮助:显示帮助信息'
        '初始化:初始化新包'

        # 英文命令
        'install:安装包及依赖'
        'publish:发布包到注册表'
        'search:搜索包'
        'list:列出已安装包'
        'uninstall:卸载包'
        'update:更新包'
        'verify:验证包完整性'
        'info:查看包信息'
        'help:显示帮助信息'
        'init:初始化新包'
    )

    # 已安装包（从目录读取）
    if [[ -d ~/.zhc/packages ]]; then
        packages=(${(f)"$(ls ~/.zhc/packages 2>/dev/null)"})
    fi

    # 搜索关键词
    keywords=('网络' '数学' '文件' '系统' '图形' '数据库' '测试' '文档')

    # 根据当前位置补全
    if [[ $CURRENT -eq 2 ]]; then
        # 补全命令
        _describe 'command' commands
    elif [[ $words[2] == 安装 || $words[2] == install ]]; then
        # 补全包名
        _describe 'package' packages
    elif [[ $words[2] == 搜索 || $words[2] == search ]]; then
        # 补全关键词
        _describe 'keyword' keywords
    elif [[ $words[2] == 卸载 || $words[2] == uninstall ||
             $words[2] == 更新 || $words[2] == update ||
             $words[2] == 验证 || $words[2] == verify ||
             $words[2] == 信息 || $words[2] == info ]]; then
        # 补全已安装包名
        _describe 'package' packages
    fi
}

_zhc
"""

    return script


def print_installation_guide():
    """打印安装指南"""

    guide = (
        """
========================================
ZHC包管理器自动补全安装指南
========================================

1️⃣  Bash用户（推荐）

# 创建补全脚本目录
sudo mkdir -p /etc/bash_completion.d

# 写入补全脚本
sudo tee /etc/bash_completion.d/zhc > /dev/null << 'EOF'
"""
        + install_bash_completion()
        + """
EOF

# 加载补全脚本
source /etc/bash_completion.d/zhc

# 添加到 ~/.bashrc（永久生效）
echo "source /etc/bash_completion.d/zhc" >> ~/.bashrc


2️⃣  Zsh用户（推荐）

# 创建补全目录
mkdir -p ~/.zsh/completion

# 写入补全脚本
tee ~/.zsh/completion/_zhc > /dev/null << 'EOF'
"""
        + install_zsh_completion()
        + """
EOF

# 添加到 ~/.zshrc（永久生效）
echo "fpath=(~/.zsh/completion \\$fpath)" >> ~/.zshrc
echo "autoload -U compinit && compinit" >> ~/.zshrc

# 重新加载配置
source ~/.zshrc


3️⃣  测试补全

# 重启终端后测试
zhc 安<Tab>     # 应该补全为 "安装"
zhc 安装 标<Tab>  # 应该补全包名（如果有）
zhc 搜<Tab>     # 应该补全为 "搜索"


4️⃣  验证安装

# Bash
complete -p zhc  # 应该显示: complete -F _zhc_complete zhc

# Zsh
which _zhc       # 应该显示补全函数路径


========================================
🎉 补全安装完成！
========================================
"""
    )

    print(guide)


if __name__ == "__main__":
    # 测试补全器
    print("=" * 60)
    print("📊 ZHC包管理器补全器测试")
    print("=" * 60)
    print()

    completer = ZHCCompleter()

    # 测试命令补全
    print("1️⃣  测试命令补全")
    print("   输入: '安'")
    print(f"   补全: {completer.complete_command('安')}")
    print()

    print("   输入: 'in'")
    print(f"   补全: {completer.complete_command('in')}")
    print()

    # 测试包名补全
    print("2️⃣  测试包名补全")
    print("   输入: '标'")
    print(f"   补全: {completer.complete_package('标')}")
    print()

    # 测试关键词补全
    print("3️⃣  测试关键词补全")
    print("   输入: '网'")
    print(f"   补全: {completer.complete_keyword('网')}")
    print()

    # 测试智能补全
    print("4️⃣  测试智能补全")
    print("   命令: '安装'")
    print("   当前词: '标'")
    print(f"   补全: {completer.complete('install', '标', '安装')}")
    print()

    # 测试命令帮助
    print("5️⃣  测试命令帮助")
    print(f"   '安装': {completer.get_command_help('安装')}")
    print()

    # 打印安装指南
    print_installation_guide()
