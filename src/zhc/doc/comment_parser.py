"""文档注释解析器模块。

支持多种文档注释格式：
- Doxygen 风格（/** ... */）
- Javadoc 风格（/** ... */）
- 块注释风格（/* ... */）
- 行注释风格（// ...）

支持的标签：
- @param: 参数说明
- @return: 返回值说明
- @示例: 代码示例
- @注意: 注意事项
- @参见: 参见其他
- @版本: 版本信息
- @author: 作者
- @deprecated: 废弃说明
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# 标签模式：匹配 @标签名 内容
TAG_PATTERN = re.compile(r"@(\w+)(?:\s+(.+))?")

# Markdown 代码块模式
CODE_BLOCK_PATTERN = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


@dataclass
class DocTag:
    """文档标签。

    属性:
        name: 标签名称
        value: 标签值/内容
        params: 标签参数（如 @param 的参数名）
    """

    name: str
    value: str = ""
    params: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        if self.params:
            param_str = " ".join(f"{k}={v}" for k, v in self.params.items())
            return f"@{self.name} {param_str} {self.value}".strip()
        return f"@{self.name} {self.value}".strip()


@dataclass
class DocComment:
    """文档注释。

    属性:
        description: 描述文本（不含标签的部分）
        tags: 所有标签列表
        examples: 代码示例列表（从 @示例 标签提取）
        notes: 注意事项列表（从 @注意 标签提取）
        raw_text: 原始注释文本
    """

    description: str = ""
    tags: List[DocTag] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    raw_text: str = ""

    def get_tag(self, name: str) -> Optional[DocTag]:
        """获取指定名称的第一个标签。

        Args:
            name: 标签名称

        Returns:
            找到的标签对象，不存在则返回 None
        """
        for tag in self.tags:
            if tag.name == name:
                return tag
        return None

    def get_all_tags(self, name: str) -> List[DocTag]:
        """获取指定名称的所有标签。

        Args:
            name: 标签名称

        Returns:
            所有匹配的标签对象列表
        """
        return [tag for tag in self.tags if tag.name == name]

    def get_param(self, name: str) -> Optional[str]:
        """获取参数说明。

        Args:
            name: 参数名称

        Returns:
            参数说明，不存在则返回 None
        """
        for tag in self.tags:
            if tag.name == "param" and tag.params.get("name") == name:
                return tag.value
        return None

    def get_return(self) -> Optional[str]:
        """获取返回值说明。

        Returns:
            返回值说明，不存在则返回 None
        """
        tag = self.get_tag("return")
        return tag.value if tag else None

    def get_returns(self) -> List[str]:
        """获取所有返回值说明。

        Returns:
            所有 @return/@returns 标签的值列表
        """
        returns = []
        for tag in self.tags:
            if tag.name in ("return", "returns"):
                returns.append(tag.value)
        return returns

    def get_example(self, index: int = 0) -> Optional[str]:
        """获取指定索引的代码示例。

        Args:
            index: 示例索引，从 0 开始

        Returns:
            代码示例文本，不存在则返回 None
        """
        if 0 <= index < len(self.examples):
            return self.examples[index]
        return None

    def get_deprecated(self) -> Optional[str]:
        """获取废弃说明。

        Returns:
            废弃说明，不存在则返回 None
        """
        tag = self.get_tag("deprecated")
        return tag.value if tag else None

    def get_author(self) -> Optional[str]:
        """获取作者信息。

        Returns:
            作者信息，不存在则返回 None
        """
        tag = self.get_tag("author")
        return tag.value if tag else None

    def get_version(self) -> Optional[str]:
        """获取版本信息。

        Returns:
            版本信息，不存在则返回 None
        """
        tag = self.get_tag("版本")
        if not tag:
            tag = self.get_tag("version")
        return tag.value if tag else None

    def has_tag(self, name: str) -> bool:
        """检查是否存在指定标签。

        Args:
            name: 标签名称

        Returns:
            是否存在该标签
        """
        return any(tag.name == name for tag in self.tags)

    def to_dict(self) -> Dict:
        """转换为字典格式。

        Returns:
            字典表示
        """
        return {
            "description": self.description,
            "tags": [
                {"name": t.name, "value": t.value, "params": t.params}
                for t in self.tags
            ],
            "examples": self.examples,
            "notes": self.notes,
            "raw_text": self.raw_text,
        }


class CommentParser:
    """注释解析器。

    用法:
        parser = CommentParser()
        comment = parser.parse(\"\"\"
        /**
         * 这是一个示例函数
         *
         * @param a 第一个参数
         * @param b 第二个参数
         * @return 返回结果
         */
        \"\"\")
        print(comment.description)  # "这是一个示例函数"
        print(comment.get_param("a"))  # "第一个参数"
    """

    # 多行注释开始模式
    MULTILINE_COMMENT_START = re.compile(r"/\*\*|\/\*!")

    # 单行注释模式
    LINE_COMMENT_START = re.compile(r"//[/!]")

    # 标签模式
    TAG_PATTERN = TAG_PATTERN

    # 参数标签的额外模式（支持 @param name description 或 @param[描述] name）
    PARAM_PATTERN = re.compile(r"@param(?:\s+\[([^\]]*)\])?\s+(\w+)(?:\s+(.+))?")

    def __init__(self):
        """初始化注释解析器。"""
        self._tag_pattern = self.TAG_PATTERN
        self._param_pattern = self.PARAM_PATTERN

    def parse(self, comment_text: str) -> DocComment:
        """解析文档注释。

        Args:
            comment_text: 注释文本（不含注释标记）

        Returns:
            解析后的 DocComment 对象
        """
        # 移除注释标记并规范化
        cleaned = self._clean_comment(comment_text)
        lines = cleaned.split("\n")

        description_lines: List[str] = []
        tags: List[DocTag] = []
        examples: List[str] = []
        notes: List[str] = []

        current_tag: Optional[DocTag] = None
        current_tag_lines: List[str] = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行
            if not line:
                i += 1
                continue

            # 检查标签
            tag_match = self._tag_pattern.match(line)

            if tag_match:
                # 保存之前的标签内容
                if current_tag:
                    current_tag.value = "\n".join(current_tag_lines).strip()
                    tags.append(current_tag)
                    # 更新 examples 和 notes 列表
                    if current_tag.name in ("示例", "example"):
                        examples.append(current_tag.value)
                    elif current_tag.name in ("注意", "note", "warning"):
                        notes.append(current_tag.value)

                tag_name = tag_match.group(1)
                tag_value = tag_match.group(2) or ""

                # 解析 @param 标签
                params: Dict[str, str] = {}
                if tag_name == "param":
                    param_match = self._param_pattern.match(line)
                    if param_match:
                        tag_value = param_match.group(3) or ""
                        if param_match.group(1):
                            params["type"] = param_match.group(1)
                        params["name"] = param_match.group(2)

                current_tag = DocTag(name=tag_name, value=tag_value, params=params)
                current_tag_lines = [tag_value] if tag_value else []

            elif current_tag:
                # 继续收集当前标签的内容
                current_tag_lines.append(line)
            else:
                # 描述文本
                description_lines.append(line)

            i += 1

        # 保存最后一个标签
        if current_tag:
            current_tag.value = "\n".join(current_tag_lines).strip()
            tags.append(current_tag)
            # 更新 examples 和 notes 列表
            if current_tag.name in ("示例", "example"):
                examples.append(current_tag.value)
            elif current_tag.name in ("注意", "note", "warning"):
                notes.append(current_tag.value)

        return DocComment(
            description="\n".join(description_lines).strip(),
            tags=tags,
            examples=examples,
            notes=notes,
            raw_text=comment_text,
        )

    def _clean_comment(self, text: str) -> str:
        """清理注释文本。

        移除注释标记和前缀星号。

        Args:
            text: 原始注释文本

        Returns:
            清理后的文本
        """
        # 移除开头的 /** 或 /*!
        text = re.sub(r"^/\*\*?\s*", "", text.strip())

        # 移除结尾的 */
        text = re.sub(r"\s*\*/\s*$", "", text)

        lines = text.split("\n")
        result: List[str] = []

        for line in lines:
            # 移除行首的星号和空白
            line = line.strip()
            if line.startswith("*"):
                line = line[1:].strip()
            elif line.startswith("/*") or line.startswith("*/"):
                continue
            elif line.startswith("//"):
                line = line[2:].strip()

            # 移除行中的 */
            if "*/" in line:
                line = line[: line.index("*/")].strip()

            result.append(line)

        # 移除尾部空行
        while result and not result[-1].strip():
            result.pop()

        return "\n".join(result)

    def extract_from_source(self, source: str) -> Dict[str, List[DocComment]]:
        """从源代码中提取所有文档注释。

        Args:
            source: 源代码文本

        Returns:
            字典，键为行号，值为该行后的 DocComment 列表
        """
        result: Dict[str, List[DocComment]] = {}
        lines = source.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查多行注释开始
            multiline_match = self.MULTILINE_COMMENT_START.search(line)
            if multiline_match:
                comment_lines = [line]
                start = multiline_match.start()

                # 找到注释结束
                j = i + 1
                end_pos = line.find("*/", start)
                if end_pos == -1:
                    while j < len(lines):
                        comment_lines.append(lines[j])
                        if "*/" in lines[j]:
                            break
                        j += 1
                else:
                    comment_lines[-1] = line[: end_pos + 2]

                # 解析注释
                comment_text = "\n".join(comment_lines)
                doc = self.parse(comment_text)

                if doc.description or doc.tags:
                    result[str(i + 1)] = [doc]

                if end_pos == -1:
                    i = j + 1
                else:
                    i += 1
                continue

            # 检查单行注释
            line_comment_match = self.LINE_COMMENT_START.search(line)
            if line_comment_match:
                comment_start = line_comment_match.end()
                comment_text = line[comment_start:].strip()

                # 收集连续的单行注释
                comment_lines = [comment_text]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if self.LINE_COMMENT_START.match(next_line):
                        comment_lines.append(next_line[2:].strip())
                        j += 1
                    else:
                        break

                # 解析注释
                doc = self.parse("\n".join(comment_lines))

                if doc.description or doc.tags:
                    result[str(i + 1)] = [doc]

                i = j
                continue

            i += 1

        return result

    def strip_markdown(self, text: str) -> str:
        """移除 Markdown 格式标记。

        Args:
            text: 包含 Markdown 格式的文本

        Returns:
            纯文本
        """
        # 移除代码块
        text = CODE_BLOCK_PATTERN.sub(r"\2", text)

        # 移除行内代码标记
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 移除加粗和斜体
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # 移除链接，保留文本
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # 移除标题标记
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        return text.strip()


# 便捷函数
def parse_comment(comment_text: str) -> DocComment:
    """解析文档注释的便捷函数。

    Args:
        comment_text: 注释文本

    Returns:
        解析后的 DocComment 对象
    """
    parser = CommentParser()
    return parser.parse(comment_text)


def extract_comments(source: str) -> Dict[str, List[DocComment]]:
    """从源代码中提取所有文档注释的便捷函数。

    Args:
        source: 源代码文本

    Returns:
        字典，键为行号，值为该行后的 DocComment 列表
    """
    parser = CommentParser()
    return parser.extract_from_source(source)
