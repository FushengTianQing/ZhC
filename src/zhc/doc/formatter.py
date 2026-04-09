"""文档格式化器模块。

支持多种输出格式：
- HTML: 美观的网页文档
- Markdown: 纯文本 Markdown 文档
- JSON: 结构化 JSON 格式
- Text: 纯文本格式
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    DocClass,
    DocComment,
    DocConstant,
    DocEnum,
    DocFunction,
    DocModule,
    DocStructure,
)


class DocFormatter(ABC):
    """文档格式化器基类。"""

    @abstractmethod
    def format_module(self, module: DocModule) -> str:
        """格式化模块文档。"""
        pass

    @abstractmethod
    def format_function(self, func: DocFunction) -> str:
        """格式化函数文档。"""
        pass

    @abstractmethod
    def format_structure(self, struct: DocStructure) -> str:
        """格式化结构体文档。"""
        pass

    @abstractmethod
    def format_enum(self, enum: DocEnum) -> str:
        """格式化枚举文档。"""
        pass

    def format_doc_comment(self, comment: Optional[DocComment]) -> str:
        """格式化文档注释。"""
        if not comment:
            return ""
        return comment.description

    def format_deprecated(self, deprecated: Optional[str]) -> str:
        """格式化废弃标记。"""
        if deprecated:
            return f"**已废弃**: {deprecated}"
        return ""


class TextFormatter(DocFormatter):
    """纯文本格式化器。"""

    def format_module(self, module: DocModule) -> str:
        lines = [
            "=" * 60,
            f"模块: {module.name}",
            "=" * 60,
        ]

        if module.description:
            lines.append("")
            lines.append(module.description)

        if module.description:
            lines.append("")

        # 函数
        if module.functions:
            lines.append("函数:")
            lines.append("-" * 40)
            for func in module.functions:
                desc = f" - {func.description}" if func.description else ""
                lines.append(f"  - {func.name}{desc}")
            lines.append("")

        # 结构体
        if module.structures:
            lines.append("结构体:")
            lines.append("-" * 40)
            for struct in module.structures:
                lines.append(f"  - {struct.name}")
            lines.append("")

        # 枚举
        if module.enums:
            lines.append("枚举:")
            lines.append("-" * 40)
            for enum in module.enums:
                lines.append(f"  - {enum.name}")
            lines.append("")

        return "\n".join(lines)

    def format_function(self, func: DocFunction) -> str:
        lines = [
            f"函数: {func.name}",
            "-" * 40,
            f"签名: {func.signature or func.name}",
        ]

        if func.description:
            lines.append(f"描述: {func.description}")

        if func.parameters:
            lines.append("参数:")
            for param in func.parameters:
                lines.append(f"  - {param.name}: {param.description or param.type}")

        if func.returns:
            lines.append(f"返回值: {func.returns.description or func.returns.type}")

        return "\n".join(lines)

    def format_structure(self, struct: DocStructure) -> str:
        lines = [
            f"结构体: {struct.name}",
            "-" * 40,
        ]

        if struct.description:
            lines.append(struct.description)

        if struct.fields:
            lines.append("字段:")
            for field in struct.fields:
                lines.append(f"  - {field.name}: {field.type}")

        return "\n".join(lines)

    def format_enum(self, enum: DocEnum) -> str:
        lines = [
            f"枚举: {enum.name}",
            "-" * 40,
        ]

        if enum.description:
            lines.append(enum.description)

        if enum.members:
            lines.append("成员:")
            for member in enum.members:
                val = f" = {member.value}" if member.value else ""
                lines.append(f"  - {member.name}{val}")

        return "\n".join(lines)


class MarkdownFormatter(DocFormatter):
    """Markdown 格式化器。"""

    def format_module(self, module: DocModule) -> str:
        lines = [f"# 模块: {module.name}", ""]

        if module.description:
            lines.append(module.description)
            lines.append("")

        # 作者和版本
        meta = []
        if module.author:
            meta.append(f"**作者**: {module.author}")
        if module.since:
            meta.append(f"**版本**: {module.since}")
        if meta:
            lines.append(" | ".join(meta))
            lines.append("")

        # 导入
        if module.imports:
            lines.append("## 导入")
            lines.append("")
            for imp in module.imports:
                lines.append(f"```zhc\n{imp}\n```")
            lines.append("")

        # 函数
        if module.functions:
            lines.append("## 函数")
            lines.append("")
            for func in module.functions:
                lines.append(self.format_function(func))
                lines.append("")

        # 结构体
        if module.structures:
            lines.append("## 结构体")
            lines.append("")
            for struct in module.structures:
                lines.append(self.format_structure(struct))
                lines.append("")

        # 类
        if module.classes:
            lines.append("## 类")
            lines.append("")
            for cls in module.classes:
                lines.append(self.format_class(cls))
                lines.append("")

        # 枚举
        if module.enums:
            lines.append("## 枚举")
            lines.append("")
            for enum in module.enums:
                lines.append(self.format_enum(enum))
                lines.append("")

        # 常量
        if module.constants:
            lines.append("## 常量")
            lines.append("")
            for const in module.constants:
                lines.append(self.format_constant(const))
                lines.append("")

        return "\n".join(lines)

    def format_function(self, func: DocFunction) -> str:
        lines = [f"### `{func.name}`", ""]

        if func.deprecated:
            lines.append(f"> **已废弃**: {func.deprecated}")
            lines.append("")

        if func.description:
            lines.append(func.description)
            lines.append("")

        # 签名
        lines.append("```zhc")
        lines.append(func.signature or func.name)
        lines.append("```")
        lines.append("")

        # 参数
        if func.parameters:
            lines.append("**参数**")
            lines.append("")
            lines.append("| 名称 | 类型 | 描述 |")
            lines.append("|------|------|------|")
            for param in func.parameters:
                lines.append(
                    f"| `{param.name}` | `{param.type}` | {param.description or ''} |"
                )
            lines.append("")

        # 返回值
        if func.returns:
            lines.append("**返回值**")
            lines.append("")
            if func.returns.type:
                lines.append(f"类型: `{func.returns.type}`")
            if func.returns.description:
                lines.append(func.returns.description)
            lines.append("")

        # 示例
        if func.examples:
            lines.append("**示例**")
            lines.append("")
            for i, example in enumerate(func.examples):
                lines.append("```zhc")
                lines.append(example)
                lines.append("```")
                lines.append("")

        # 注意事项
        if func.notes:
            lines.append("**注意**")
            lines.append("")
            for note in func.notes:
                lines.append(f"> {note}")
            lines.append("")

        return "\n".join(lines)

    def format_structure(self, struct: DocStructure) -> str:
        kind = "联合体" if struct.is_union else "结构体"
        lines = [f"### `{struct.name}` ({kind})", ""]

        if struct.deprecated:
            lines.append(f"> **已废弃**: {struct.deprecated}")
            lines.append("")

        if struct.description:
            lines.append(struct.description)
            lines.append("")

        # 字段
        if struct.fields:
            lines.append("**字段**")
            lines.append("")
            lines.append("| 名称 | 类型 | 描述 |")
            lines.append("|------|------|------|")
            for field in struct.fields:
                lines.append(
                    f"| `{field.name}` | `{field.type}` | {field.description or ''} |"
                )
            lines.append("")

        return "\n".join(lines)

    def format_class(self, cls: DocClass) -> str:
        lines = [f"### `{cls.name}` (类)", ""]

        if cls.deprecated:
            lines.append(f"> **已废弃**: {cls.deprecated}")
            lines.append("")

        if cls.description:
            lines.append(cls.description)
            lines.append("")

        # 字段
        if cls.fields:
            lines.append("**字段**")
            lines.append("")
            lines.append("| 名称 | 类型 | 描述 |")
            lines.append("|------|------|------|")
            for field in cls.fields:
                lines.append(
                    f"| `{field.name}` | `{field.type}` | {field.description or ''} |"
                )
            lines.append("")

        # 方法
        if cls.methods:
            lines.append("**方法**")
            lines.append("")
            for method in cls.methods:
                lines.append(f"- `{method.name}`: {method.description or ''}")
            lines.append("")

        return "\n".join(lines)

    def format_enum(self, enum: DocEnum) -> str:
        lines = [f"### `{enum.name}` (枚举)", ""]

        if enum.deprecated:
            lines.append(f"> **已废弃**: {enum.deprecated}")
            lines.append("")

        if enum.description:
            lines.append(enum.description)
            lines.append("")

        if enum.underlying_type:
            lines.append(f"底层类型: `{enum.underlying_type}`")
            lines.append("")

        # 成员
        if enum.members:
            lines.append("| 成员 | 值 | 描述 |")
            lines.append("|------|-----|------|")
            for member in enum.members:
                lines.append(
                    f"| `{member.name}` | `{member.value or ''}` | {member.description or ''} |"
                )
            lines.append("")

        return "\n".join(lines)

    def format_constant(self, const: DocConstant) -> str:
        lines = [f"### `{const.name}` (常量)", ""]

        if const.description:
            lines.append(const.description)
            lines.append("")

        if const.type:
            lines.append(f"类型: `{const.type}`")
        if const.value:
            lines.append(f"值: `{const.value}`")
        lines.append("")

        return "\n".join(lines)


class JsonFormatter(DocFormatter):
    """JSON 格式化器。"""

    def format_module(self, module: DocModule) -> str:
        return json.dumps(module.to_dict(), ensure_ascii=False, indent=2)

    def format_function(self, func: DocFunction) -> str:
        return json.dumps(func.to_dict(), ensure_ascii=False, indent=2)

    def format_structure(self, struct: DocStructure) -> str:
        return json.dumps(struct.to_dict(), ensure_ascii=False, indent=2)

    def format_enum(self, enum: DocEnum) -> str:
        return json.dumps(enum.to_dict(), ensure_ascii=False, indent=2)


class HtmlFormatter(DocFormatter):
    """HTML 格式化器。"""

    def __init__(self, template_dir: Optional[Path] = None):
        """初始化 HTML 格式化器。

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = template_dir

    def format_module(self, module: DocModule) -> str:
        items: List[str] = []

        # 模块信息
        items.append(self._render_module_header(module))

        # 导入
        if module.imports:
            items.append('<section class="imports">')
            items.append("<h2>导入</h2>")
            for imp in module.imports:
                items.append(f"<pre><code>{self._escape(imp)}</code></pre>")
            items.append("</section>")

        # 函数
        if module.functions:
            items.append('<section class="functions">')
            items.append("<h2>函数</h2>")
            for func in module.functions:
                items.append(self.format_function(func))
            items.append("</section>")

        # 结构体
        if module.structures:
            items.append('<section class="structures">')
            items.append("<h2>结构体</h2>")
            for struct in module.structures:
                items.append(self.format_structure(struct))
            items.append("</section>")

        # 枚举
        if module.enums:
            items.append('<section class="enums">')
            items.append("<h2>枚举</h2>")
            for enum in module.enums:
                items.append(self.format_enum(enum))
            items.append("</section>")

        return "\n".join(items)

    def format_function(self, func: DocFunction) -> str:
        items = [
            '<article class="function">',
            f'<h3 id="func-{func.name}">{self._escape(func.name)}</h3>',
        ]

        if func.deprecated:
            items.append(
                f'<div class="deprecated">{self._escape(func.deprecated)}</div>'
            )

        if func.description:
            items.append(f'<p class="description">{self._escape(func.description)}</p>')

        # 签名
        items.append('<pre class="signature"><code>')
        items.append(self._escape(func.signature or func.name))
        items.append("</code></pre>")

        # 参数表
        if func.parameters:
            items.append('<table class="params">')
            items.append(
                "<thead><tr><th>参数</th><th>类型</th><th>描述</th></tr></thead>"
            )
            items.append("<tbody>")
            for param in func.parameters:
                items.append(
                    f"<tr><td><code>{self._escape(param.name)}</code></td>"
                    f"<td><code>{self._escape(param.type)}</code></td>"
                    f"<td>{self._escape(param.description)}</td></tr>"
                )
            items.append("</tbody></table>")

        # 返回值
        if func.returns:
            items.append('<div class="return">')
            items.append("<strong>返回值:</strong>")
            if func.returns.type:
                items.append(f"<code>{self._escape(func.returns.type)}</code>")
            if func.returns.description:
                items.append(self._escape(func.returns.description))
            items.append("</div>")

        # 示例
        if func.examples:
            items.append('<div class="examples">')
            items.append("<strong>示例:</strong>")
            for example in func.examples:
                items.append(f"<pre><code>{self._escape(example)}</code></pre>")
            items.append("</div>")

        # 注意事项
        if func.notes:
            items.append('<div class="notes">')
            items.append("<strong>注意:</strong>")
            for note in func.notes:
                items.append(f"<blockquote>{self._escape(note)}</blockquote>")
            items.append("</div>")

        items.append("</article>")
        return "\n".join(items)

    def format_structure(self, struct: DocStructure) -> str:
        kind = "union" if struct.is_union else "struct"
        items = [
            '<article class="structure">',
            f'<h3 id="struct-{struct.name}" class="{kind}">{self._escape(struct.name)}</h3>',
        ]

        if struct.description:
            items.append(
                f'<p class="description">{self._escape(struct.description)}</p>'
            )

        # 字段表
        if struct.fields:
            items.append('<table class="fields">')
            items.append(
                "<thead><tr><th>字段</th><th>类型</th><th>描述</th></tr></thead>"
            )
            items.append("<tbody>")
            for field in struct.fields:
                items.append(
                    f"<tr><td><code>{self._escape(field.name)}</code></td>"
                    f"<td><code>{self._escape(field.type)}</code></td>"
                    f"<td>{self._escape(field.description)}</td></tr>"
                )
            items.append("</tbody></table>")

        items.append("</article>")
        return "\n".join(items)

    def format_enum(self, enum: DocEnum) -> str:
        items = [
            '<article class="enum">',
            f'<h3 id="enum-{enum.name}">{self._escape(enum.name)}</h3>',
        ]

        if enum.description:
            items.append(f'<p class="description">{self._escape(enum.description)}</p>')

        # 成员表
        if enum.members:
            items.append('<table class="members">')
            items.append(
                "<thead><tr><th>成员</th><th>值</th><th>描述</th></tr></thead>"
            )
            items.append("<tbody>")
            for member in enum.members:
                items.append(
                    f"<tr><td><code>{self._escape(member.name)}</code></td>"
                    f"<td><code>{self._escape(member.value or '')}</code></td>"
                    f"<td>{self._escape(member.description)}</td></tr>"
                )
            items.append("</tbody></table>")

        items.append("</article>")
        return "\n".join(items)

    def _render_module_header(self, module: DocModule) -> str:
        """渲染模块头部。"""
        items = [
            '<header class="module-header">',
            f"<h1>模块: {self._escape(module.name)}</h1>",
        ]

        if module.description:
            items.append(
                f'<p class="description">{self._escape(module.description)}</p>'
            )

        # 元信息
        meta: List[str] = []
        if module.author:
            meta.append(
                f"<li><strong>作者:</strong> {self._escape(module.author)}</li>"
            )
        if module.since:
            meta.append(f"<li><strong>版本:</strong> {self._escape(module.since)}</li>")

        if meta:
            meta_content = "".join(meta)
            items.append(f'<ul class="meta">{meta_content}</ul>')

        items.append("</header>")
        return "\n".join(items)

    def _escape(self, text: str) -> str:
        """转义 HTML 特殊字符。"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )


# 格式化器注册表
FORMATTERS: Dict[str, type[DocFormatter]] = {
    "text": TextFormatter,
    "markdown": MarkdownFormatter,
    "md": MarkdownFormatter,
    "json": JsonFormatter,
    "html": HtmlFormatter,
}


def get_formatter(format_type: str, **kwargs) -> DocFormatter:
    """获取指定类型的格式化器。

    Args:
        format_type: 格式化器类型
        **kwargs: 传递给格式化器的参数

    Returns:
        格式化器实例

    Raises:
        ValueError: 不支持的格式化器类型
    """
    formatter_class = FORMATTERS.get(format_type.lower())
    if not formatter_class:
        supported = ", ".join(FORMATTERS.keys())
        raise ValueError(f"不支持的格式: {format_type}，支持的格式: {supported}")
    return formatter_class(**kwargs)
