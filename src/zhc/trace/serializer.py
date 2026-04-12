# -*- coding: utf-8 -*-
"""
Trace 序列化器

将 TraceRecord 序列化为 trace.json。

作者：远
日期：2026-04-13
"""

import json
from pathlib import Path
from typing import Optional, Union

from .schema import TraceRecord


class TraceSerializer:
    """追踪记录序列化器"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化序列化器

        Args:
            output_dir: 输出目录，默认为当前目录
        """
        self.output_dir = output_dir or Path(".")

    def serialize(self, record: TraceRecord, filename: str = "trace.json") -> Path:
        """
        序列化追踪记录到 JSON 文件

        Args:
            record: 追踪记录
            filename: 输出文件名

        Returns:
            输出文件路径
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename

        json_str = record.to_json(indent=2)
        output_path.write_text(json_str, encoding="utf-8")

        return output_path

    @staticmethod
    def deserialize(json_path: Union[str, Path]) -> TraceRecord:
        """
        从 JSON 文件反序列化追踪记录

        Args:
            json_path: JSON 文件路径

        Returns:
            TraceRecord 实例
        """
        json_path = Path(json_path)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return TraceRecord.from_dict(data)

    @staticmethod
    def to_json_string(record: TraceRecord, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return record.to_json(indent=indent)

    @staticmethod
    def validate_json(json_str: str) -> bool:
        """
        验证 JSON 格式

        Args:
            json_str: JSON 字符串

        Returns:
            是否有效
        """
        try:
            data = json.loads(json_str)
            # 检查必要字段
            if "schema_version" not in data:
                return False
            if "events" not in data:
                return False
            if not isinstance(data["events"], list):
                return False
            return True
        except json.JSONDecodeError:
            return False
