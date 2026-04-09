# -*- coding: utf-8 -*-
"""
文件操作工具函数

提供统一的文件读写接口，减少重复代码。

作者：远
日期：2026-04-07
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union


def read_file(filepath: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    读取文件内容

    Args:
        filepath: 文件路径
        encoding: 编码格式，默认 utf-8

    Returns:
        文件内容字符串

    Raises:
        IOError: 文件读取失败

    Example:
        >>> content = read_file('src/main.py')
        >>> lines = read_file('data.txt').splitlines()
    """
    filepath = Path(filepath)

    try:
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()
    except IOError as e:
        raise IOError(f"无法读取文件 {filepath}: {e}")


class SourceFileError(Exception):
    """源文件错误"""

    pass


def read_source_file(filepath: Union[str, Path]) -> str:
    """
    读取源代码文件，自动处理 UTF-8 编码和 BOM

    Args:
        filepath: 源文件路径

    Returns:
        源代码字符串

    Raises:
        SourceFileError: 文件编码错误或读取失败

    Example:
        >>> source = read_source_file('main.zhc')
    """
    filepath = Path(filepath)

    try:
        # 使用 utf-8-sig 自动处理 BOM
        with open(filepath, "r", encoding="utf-8-sig") as f:
            source = f.read()
        return source
    except UnicodeDecodeError as e:
        raise SourceFileError(
            f"源文件编码错误: {filepath}\n"
            f"详细信息: {e}\n"
            f"请确保文件使用 UTF-8 编码保存"
        )
    except IOError as e:
        raise SourceFileError(f"无法读取源文件 {filepath}: {e}")


def write_file(
    filepath: Union[str, Path], content: str, encoding: str = "utf-8"
) -> None:
    """
    写入文件内容

    Args:
        filepath: 文件路径
        content: 要写入的内容
        encoding: 编码格式，默认 utf-8

    Raises:
        IOError: 文件写入失败

    Example:
        >>> write_file('output.txt', 'Hello World')
        >>> write_file('data.json', json.dumps(data))
    """
    filepath = Path(filepath)

    # 确保目录存在
    ensure_directory(filepath.parent)

    try:
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
    except IOError as e:
        raise IOError(f"无法写入文件 {filepath}: {e}")


def read_json_file(
    filepath: Union[str, Path], encoding: str = "utf-8"
) -> Dict[str, Any]:
    """
    读取 JSON 文件

    Args:
        filepath: 文件路径
        encoding: 编码格式，默认 utf-8

    Returns:
        JSON 数据字典

    Raises:
        IOError: 文件读取失败
        json.JSONDecodeError: JSON 解析失败

    Example:
        >>> config = read_json_file('config.json')
        >>> print(config['name'])
    """
    filepath = Path(filepath)

    try:
        with open(filepath, "r", encoding=encoding) as f:
            return json.load(f)
    except IOError as e:
        raise IOError(f"无法读取 JSON 文件 {filepath}: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"JSON 文件 {filepath} 格式错误: {e}", e.doc, e.pos)


def write_json_file(
    filepath: Union[str, Path],
    data: Dict[str, Any],
    indent: int = 2,
    ensure_ascii: bool = False,
    encoding: str = "utf-8",
) -> None:
    """
    写入 JSON 文件

    Args:
        filepath: 文件路径
        data: 要写入的数据
        indent: 缩进空格数，默认 2
        ensure_ascii: 是否确保 ASCII 编码，默认 False（支持中文）
        encoding: 编码格式，默认 utf-8

    Raises:
        IOError: 文件写入失败

    Example:
        >>> write_json_file('config.json', {'name': 'ZHC', 'version': '1.0'})
        >>> write_json_file('data.json', data, indent=4)
    """
    filepath = Path(filepath)

    # 确保目录存在
    ensure_directory(filepath.parent)

    try:
        with open(filepath, "w", encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    except IOError as e:
        raise IOError(f"无法写入 JSON 文件 {filepath}: {e}")


def read_lines(filepath: Union[str, Path], encoding: str = "utf-8") -> List[str]:
    """
    读取文件行列表

    Args:
        filepath: 文件路径
        encoding: 编码格式，默认 utf-8

    Returns:
        文件行列表（保留换行符）

    Raises:
        IOError: 文件读取失败

    Example:
        >>> lines = read_lines('src/main.py')
        >>> for i, line in enumerate(lines, 1):
        >>>     print(f"{i}: {line.rstrip()}")
    """
    filepath = Path(filepath)

    try:
        with open(filepath, "r", encoding=encoding) as f:
            return f.readlines()
    except IOError as e:
        raise IOError(f"无法读取文件 {filepath}: {e}")


def ensure_directory(dirpath: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        dirpath: 目录路径

    Returns:
        目录路径对象

    Example:
        >>> ensure_directory('output/data')
        >>> ensure_directory(Path('logs'))
    """
    dirpath = Path(dirpath)

    if dirpath and not dirpath.exists():
        dirpath.mkdir(parents=True, exist_ok=True)

    return dirpath


def file_exists(filepath: Union[str, Path]) -> bool:
    """
    检查文件是否存在

    Args:
        filepath: 文件路径

    Returns:
        文件是否存在

    Example:
        >>> if file_exists('config.json'):
        >>>     config = read_json_file('config.json')
    """
    return Path(filepath).exists()


def get_file_hash(filepath: Union[str, Path], algorithm: str = "md5") -> str:
    """
    计算文件哈希值

    Args:
        filepath: 文件路径
        algorithm: 哈希算法，默认 md5

    Returns:
        文件哈希值字符串

    Raises:
        IOError: 文件读取失败

    Example:
        >>> hash1 = get_file_hash('src/main.py')
        >>> hash2 = get_file_hash('src/main.py', 'sha256')
    """
    import hashlib

    filepath = Path(filepath)
    content = read_file(filepath)

    hash_func = hashlib.new(algorithm)
    hash_func.update(content.encode("utf-8"))

    return hash_func.hexdigest()
