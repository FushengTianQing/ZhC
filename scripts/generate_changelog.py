#!/usr/bin/env python3
"""
CHANGELOG 自动生成脚本

根据 Git commit 历史自动生成 CHANGELOG.md。

用法:
    python scripts/generate_changelog.py
    python scripts/generate_changelog.py --from v5.0.0 --to v6.0.0
    python scripts/generate_changelog.py --output CHANGELOG_NEW.md
"""

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def get_project_root() -> Path:
    """获取项目根目录。"""
    return Path(__file__).parent.parent


def run_git_command(args: List[str]) -> str:
    """运行 Git 命令并返回输出。"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True,
        cwd=get_project_root()
    )
    return result.stdout.strip()


def get_commits(from_tag: Optional[str] = None, to_tag: Optional[str] = None) -> List[Dict]:
    """获取 commit 列表。

    Args:
        from_tag: 起始标签。
        to_tag: 结束标签。

    Returns:
        List[Dict]: commit 信息列表。
    """
    # 构建 git log 命令范围
    if from_tag and to_tag:
        revision_range = f"{from_tag}..{to_tag}"
    elif from_tag:
        revision_range = f"{from_tag}..HEAD"
    else:
        revision_range = "HEAD"

    # 获取 commit 日志
    log_format = "%H|%s|%an|%ad|%D"
    output = run_git_command([
        "log",
        revision_range,
        f"--format={log_format}",
        "--date=short"
    ])

    commits = []
    for line in output.split("\n"):
        if not line.strip():
            continue

        parts = line.split("|", 4)
        if len(parts) >= 4:
            commit = {
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3],
                "refs": parts[4] if len(parts) > 4 else ""
            }
            commits.append(commit)

    return commits


def parse_commit_type(subject: str) -> tuple:
    """解析 commit 类型和范围。

    Args:
        subject: commit 主题。

    Returns:
        tuple: (类型, 范围, 描述)
    """
    # 匹配 conventional commit 格式
    pattern = r"^(\w+)(?:\(([^)]+)\))?:\s*(.+)$"
    match = re.match(pattern, subject)

    if match:
        commit_type = match.group(1)
        scope = match.group(2) or ""
        description = match.group(3)
        return commit_type, scope, description

    return "", "", subject


def categorize_commits(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """按类型分类 commits。

    Args:
        commits: commit 列表。

    Returns:
        Dict[str, List[Dict]]: 分类后的 commits。
    """
    categories = {
        "feat": [],
        "fix": [],
        "docs": [],
        "style": [],
        "refactor": [],
        "perf": [],
        "test": [],
        "ci": [],
        "chore": [],
        "other": []
    }

    for commit in commits:
        commit_type, scope, description = parse_commit_type(commit["subject"])

        # 更新 commit 信息
        commit["type"] = commit_type
        commit["scope"] = scope
        commit["description"] = description

        # 分类
        if commit_type in categories:
            categories[commit_type].append(commit)
        else:
            categories["other"].append(commit)

    return categories


def generate_changelog_section(
    title: str,
    commits: List[Dict],
    show_scope: bool = True
) -> str:
    """生成 CHANGELOG 章节。

    Args:
        title: 章节标题。
        commits: commit 列表。
        show_scope: 是否显示范围。

    Returns:
        str: Markdown 格式的章节内容。
    """
    if not commits:
        return ""

    lines = [f"### {title}", ""]

    for commit in commits:
        scope = f"**{commit['scope']}**: " if commit["scope"] and show_scope else ""
        lines.append(f"- {scope}{commit['description']}")

    lines.append("")
    return "\n".join(lines)


def generate_changelog(
    version: str,
    commits: List[Dict],
    date: Optional[str] = None
) -> str:
    """生成 CHANGELOG 内容。

    Args:
        version: 版本号。
        commits: commit 列表。
        date: 发布日期。

    Returns:
        str: Markdown 格式的 CHANGELOG。
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 分类 commits
    categories = categorize_commits(commits)

    # 生成内容
    lines = [
        f"## [{version}] - {date}",
        ""
    ]

    # 类型映射
    type_mapping = {
        "feat": ("Added", "新功能"),
        "fix": ("Fixed", "错误修复"),
        "docs": ("Changed", "文档更新"),
        "style": ("Changed", "代码格式"),
        "refactor": ("Changed", "重构"),
        "perf": ("Performance", "性能优化"),
        "test": ("Added", "测试"),
        "ci": ("Changed", "CI/CD"),
        "chore": ("Changed", "其他")
    }

    # 按类别生成章节
    for commit_type, commits_list in categories.items():
        if not commits_list or commit_type == "other":
            continue

        title_zh, title_en = type_mapping.get(commit_type, ("Changed", ""))
        section = generate_changelog_section(title_zh, commits_list)
        if section:
            lines.append(section)

    # 其他变更
    if categories["other"]:
        lines.append("### Other")
        lines.append("")
        for commit in categories["other"]:
            lines.append(f"- {commit['subject']}")
        lines.append("")

    return "\n".join(lines)


def update_changelog_file(new_content: str, output_file: Path) -> None:
    """更新 CHANGELOG 文件。

    Args:
        new_content: 新内容。
        output_file: 输出文件路径。
    """
    if not output_file.exists():
        # 创建新文件
        header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
        content = header + new_content
    else:
        # 读取现有内容
        existing_content = output_file.read_text()

        # 在 [Unreleased] 后插入新内容
        if "[Unreleased]" in existing_content:
            parts = existing_content.split("## [Unreleased]", 1)
            if len(parts) > 1:
                # 找到下一个版本标题
                rest = parts[1]
                version_match = re.search(r"\n## \[", rest)
                if version_match:
                    insert_pos = version_match.start()
                    content = (
                        parts[0] +
                        "## [Unreleased]" +
                        rest[:insert_pos] +
                        "\n" + new_content +
                        rest[insert_pos:]
                    )
                else:
                    content = existing_content + "\n" + new_content
            else:
                content = existing_content + "\n" + new_content
        else:
            content = existing_content + "\n" + new_content

    output_file.write_text(content)
    print(f"✅ CHANGELOG 已更新: {output_file}")


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(description="CHANGELOG 自动生成脚本")
    parser.add_argument(
        "--from",
        dest="from_tag",
        help="起始标签"
    )
    parser.add_argument(
        "--to",
        dest="to_tag",
        help="结束标签"
    )
    parser.add_argument(
        "--version",
        default="Unreleased",
        help="版本号（默认：Unreleased）"
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="输出文件（默认：CHANGELOG.md）"
    )

    args = parser.parse_args()

    # 获取 commits
    print(f"📖 获取 commit 历史...")
    commits = get_commits(args.from_tag, args.to_tag)
    print(f"   找到 {len(commits)} 个 commits")

    if not commits:
        print("⚠️  没有找到 commits")
        return

    # 生成 CHANGELOG
    print(f"📝 生成 CHANGELOG...")
    changelog = generate_changelog(args.version, commits)

    # 写入文件
    output_file = get_project_root() / args.output
    update_changelog_file(changelog, output_file)

    print(f"✨ 完成！")


if __name__ == "__main__":
    main()