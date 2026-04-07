#!/usr/bin/env python3
"""
ZHC 文档构建脚本

使用 Sphinx 构建 HTML 文档。

用法:
    python scripts/build_docs.py
    python scripts/build_docs.py --clean
    python scripts/build_docs.py --serve
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录。"""
    return Path(__file__).parent.parent


def build_docs(clean: bool = False) -> int:
    """构建 Sphinx 文档。

    Args:
        clean: 是否清理旧的构建文件。

    Returns:
        int: 返回码（0 表示成功）。
    """
    project_root = get_project_root()
    sphinx_dir = project_root / "docs" / "sphinx"
    build_dir = project_root / "docs" / "_build" / "html"

    if clean and build_dir.exists():
        print(f"清理构建目录: {build_dir}")
        subprocess.run(["rm", "-rf", str(build_dir)], check=True)

    print("构建 Sphinx 文档...")
    print(f"源目录: {sphinx_dir}")
    print(f"输出目录: {build_dir}")

    # 运行 sphinx-build
    cmd = [
        "sphinx-build",
        "-b", "html",
        str(sphinx_dir),
        str(build_dir),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("构建失败！")
        print(result.stderr)
        return result.returncode

    print("构建成功！")
    print(f"文档位置: {build_dir / 'index.html'}")

    return 0


def serve_docs() -> int:
    """启动本地文档服务器。

    Returns:
        int: 返回码（0 表示成功）。
    """
    project_root = get_project_root()
    build_dir = project_root / "docs" / "_build" / "html"

    if not build_dir.exists():
        print("文档尚未构建，请先运行: python scripts/build_docs.py")
        return 1

    print("启动文档服务器...")
    print(f"访问地址: http://localhost:8000")

    # 使用 Python 内置服务器
    subprocess.run(
        [sys.executable, "-m", "http.server", "8000"],
        cwd=str(build_dir)
    )

    return 0


def check_sphinx_installed() -> bool:
    """检查 Sphinx 是否已安装。

    Returns:
        bool: 是否已安装。
    """
    try:
        subprocess.run(["sphinx-build", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_sphinx_deps() -> int:
    """安装 Sphinx 依赖。

    Returns:
        int: 返回码（0 表示成功）。
    """
    print("安装 Sphinx 依赖...")
    deps = [
        "sphinx",
        "sphinx-rtd-theme",
        "myst-parser",
    ]

    cmd = [sys.executable, "-m", "pip", "install"] + deps
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("安装失败！")
        return result.returncode

    print("安装成功！")
    return 0


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(description="ZHC 文档构建脚本")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理旧的构建文件"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="启动本地文档服务器"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="安装 Sphinx 依赖"
    )

    args = parser.parse_args()

    # 检查 Sphinx 是否已安装
    if not check_sphinx_installed() and not args.install_deps:
        print("Sphinx 未安装，请运行: python scripts/build_docs.py --install-deps")
        return 1

    # 安装依赖
    if args.install_deps:
        return install_sphinx_deps()

    # 启动服务器
    if args.serve:
        return serve_docs()

    # 构建文档
    return build_docs(clean=args.clean)


if __name__ == "__main__":
    sys.exit(main())