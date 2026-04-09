"""文档生成模块。

提供从源代码注释自动生成 API 文档的功能。

主要组件:
- comment_parser: 文档注释解析器
- models: 文档数据模型
- formatter: 文档格式化器（支持 HTML、Markdown、JSON、Text）
- api_generator: API 文档自动生成器

用法示例:

1. 解析注释:
    from zhc.doc import CommentParser, parse_comment

    comment = parse_comment(\"\"\"
    /**
     * 计算两个数的和
     *
     * @param a 第一个数
     * @param b 第二个数
     * @return 两数之和
     */
    \"\"\")
    print(comment.description)  # 计算两个数的和

2. 生成文档:
    from zhc.doc import APIGenerator

    generator = APIGenerator("/path/to/project")
    generator.scan_sources()
    generator.generate_docs("/path/to/output", format="html")

3. 使用格式化器:
    from zhc.doc import get_formatter

    formatter = get_formatter("markdown")
    md_output = formatter.format_function(func_doc)
"""

from .comment_parser import (
    CommentParser,
    DocComment,
    DocTag,
    extract_comments,
    parse_comment,
)
from .models import (
    DocBase,
    DocClass,
    DocComment as DocCommentModel,
    DocConstant,
    DocEnum,
    DocEnumMember,
    DocField,
    DocFunction,
    DocInterface,
    DocMethod,
    DocModule,
    DocParameter,
    DocProject,
    DocReturn,
    DocStructure,
    DocTypeAlias,
    DocVariable,
    DocVisibility,
    DocKind,
)
from .formatter import (
    DocFormatter,
    TextFormatter,
    MarkdownFormatter,
    JsonFormatter,
    HtmlFormatter,
    get_formatter,
    FORMATTERS,
)
from .api_generator import (
    APIGenerator,
    SourceLocation,
    SymbolInfo,
    generate_api_docs,
)

__all__ = [
    # 注释解析器
    "CommentParser",
    "DocComment",
    "DocTag",
    "parse_comment",
    "extract_comments",
    # 数据模型
    "DocBase",
    "DocClass",
    "DocCommentModel",
    "DocConstant",
    "DocEnum",
    "DocEnumMember",
    "DocField",
    "DocFunction",
    "DocInterface",
    "DocMethod",
    "DocModule",
    "DocParameter",
    "DocProject",
    "DocReturn",
    "DocStructure",
    "DocTypeAlias",
    "DocVariable",
    "DocVisibility",
    "DocKind",
    # 格式化器
    "DocFormatter",
    "TextFormatter",
    "MarkdownFormatter",
    "JsonFormatter",
    "HtmlFormatter",
    "get_formatter",
    "FORMATTERS",
    # API 生成器
    "APIGenerator",
    "SourceLocation",
    "SymbolInfo",
    "generate_api_docs",
]
