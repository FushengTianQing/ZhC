#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置管理

管理 zhc.json 配置文件，支持：
- 项目基本信息
- 依赖声明
- 开发依赖声明
- 仓库配置
"""

import json
from typing import Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigError


@dataclass
class DependencySpec:
    """依赖规格"""

    name: str
    version_constraint: str
    source: Optional[str] = None  # 包来源（仓库URL）

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {"name": self.name, "version": self.version_constraint}
        if self.source:
            result["source"] = self.source
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "DependencySpec":
        """从字典创建"""
        return cls(
            name=data["name"],
            version_constraint=data["version"],
            source=data.get("source"),
        )


@dataclass
class ProjectConfig:
    """项目配置

    配置文件格式 (zhc.json):
    {
        "name": "项目名称",
        "version": "1.0.0",
        "description": "项目描述",
        "author": "作者",
        "dependencies": {
            "包名": "^1.0.0"
        },
        "devDependencies": {
            "测试框架": "^1.0.0"
        },
        "source": "https://registry.zhc-lang.org"
    }
    """

    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    source: Optional[str] = None  # 默认包仓库
    license: str = "MIT"
    entry: str = "src/主程序.zhc"  # 入口文件

    @classmethod
    def from_file(cls, path: Path) -> "ProjectConfig":
        """从配置文件加载

        Args:
            path: 配置文件路径

        Returns:
            ProjectConfig 对象

        Raises:
            ConfigError: 配置文件读取或解析失败
        """
        if not path.exists():
            raise ConfigError(f"配置文件不存在: {path}", str(path))

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"配置文件 JSON 格式错误: {e}", str(path))
        except Exception as e:
            raise ConfigError(f"读取配置文件失败: {e}", str(path))

        # 验证必填字段
        if "name" not in data:
            raise ConfigError("缺少必填字段: name", str(path))
        if "version" not in data:
            raise ConfigError("缺少必填字段: version", str(path))

        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            dependencies=data.get("dependencies", {}),
            dev_dependencies=data.get("devDependencies", {}),
            source=data.get("source"),
            license=data.get("license", "MIT"),
            entry=data.get("entry", "src/主程序.zhc"),
        )

    def to_file(self, path: Path):
        """保存到配置文件

        Args:
            path: 配置文件路径

        Raises:
            ConfigError: 配置文件写入失败
        """
        data = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "devDependencies": self.dev_dependencies,
            "license": self.license,
            "entry": self.entry,
        }

        if self.source:
            data["source"] = self.source

        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigError(f"写入配置文件失败: {e}", str(path))

    def add_dependency(self, name: str, version: str, dev: bool = False):
        """添加依赖

        Args:
            name: 包名
            version: 版本约束
            dev: 是否为开发依赖
        """
        if dev:
            self.dev_dependencies[name] = version
        else:
            self.dependencies[name] = version

    def remove_dependency(self, name: str, dev: bool = False) -> bool:
        """移除依赖

        Args:
            name: 包名
            dev: 是否为开发依赖

        Returns:
            是否成功移除
        """
        deps = self.dev_dependencies if dev else self.dependencies
        if name in deps:
            del deps[name]
            return True
        return False

    def get_all_dependencies(self) -> Dict[str, str]:
        """获取所有依赖（包括开发依赖）"""
        all_deps = self.dependencies.copy()
        all_deps.update(self.dev_dependencies)
        return all_deps

    def has_dependency(self, name: str) -> bool:
        """检查是否有指定依赖"""
        return name in self.dependencies or name in self.dev_dependencies

    def to_dict(self) -> dict:
        """转换为字典"""
        data = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "devDependencies": self.dev_dependencies,
            "license": self.license,
            "entry": self.entry,
        }
        if self.source:
            data["source"] = self.source
        return data


def find_project_root(start_path: Path = None) -> Optional[Path]:
    """查找项目根目录（向上查找 zhc.json）

    Args:
        start_path: 起始路径（默认为当前目录）

    Returns:
        项目根目录路径，如果未找到返回 None
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while True:
        # 检查当前目录
        if (current / "zhc.json").exists():
            return current

        # 检查父目录
        parent = current.parent
        if parent == current:
            # 已到达根目录
            return None
        current = parent


def load_project_config(start_path: Path = None) -> ProjectConfig:
    """加载项目配置（自动查找项目根目录）

    Args:
        start_path: 起始路径

    Returns:
        ProjectConfig 对象

    Raises:
        ConfigError: 未找到项目配置
    """
    project_root = find_project_root(start_path)
    if project_root is None:
        raise ConfigError("未找到项目配置文件 (zhc.json)")

    return ProjectConfig.from_file(project_root / "zhc.json")
