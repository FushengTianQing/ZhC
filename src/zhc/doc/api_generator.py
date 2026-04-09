"""API 文档自动生成器模块。

从源代码注释自动生成 API 文档，支持：
- 解析源代码中的文档注释
- 分析代码结构（模块、函数、结构体等）
- 生成多种格式的文档（HTML、Markdown、JSON）
- 自动生成交叉引用链接
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from .comment_parser import CommentParser, DocComment, extract_comments
from .formatter import HtmlFormatter, get_formatter
from .models import (
    DocBase,
    DocConstant,
    DocEnum,
    DocEnumMember,
    DocField,
    DocFunction,
    DocModule,
    DocParameter,
    DocProject,
    DocReturn,
    DocStructure,
)


@dataclass
class SourceLocation:
    """源代码位置。"""

    file: str
    line: int
    column: int = 0

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class SymbolInfo:
    """符号信息。"""

    name: str
    kind: str  # function, struct, enum, etc.
    location: SourceLocation
    doc_comment: Optional[DocComment] = None
    signature: str = ""
    type_info: str = ""


class APIGenerator:
    """API 文档生成器。

    用法:
        generator = APIGenerator(project_root)
        generator.scan_sources()
        generator.generate_docs(output_dir, format="html")
    """

    # 函数定义模式（支持中文和英文标识符）
    # 支持两种格式:
    # 1. 函数 返回类型 函数名(参数) {  - ZhC 语法
    # 2. function 函数名(参数) -> 返回类型 {  - C 风格语法
    FUNCTION_PATTERN = re.compile(
        r"(?:函数|function)\s+(?:(\w+)\s+)?(\w+)\s*\(([^)]*)\)(?:\s*->\s*(\w+))?",
        re.IGNORECASE,
    )

    # 结构体定义模式
    STRUCT_PATTERN = re.compile(
        r"(?:结构体|struct)\s+([\w\u4e00-\u9fff]+)\s*\{", re.IGNORECASE
    )

    # 枚举定义模式
    ENUM_PATTERN = re.compile(
        r"(?:枚举|enum)\s+([\w\u4e00-\u9fff]+)?\s*\{", re.IGNORECASE
    )

    # 常量定义模式
    CONSTANT_PATTERN = re.compile(r"(?:常量|const)\s+(\w+)\s*=\s*(.+)", re.IGNORECASE)

    def __init__(self, project_root: Union[str, Path]):
        """初始化 API 文档生成器。

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.comment_parser = CommentParser()

        # 解析结果
        self.modules: Dict[str, DocModule] = {}
        self.functions: Dict[str, DocFunction] = {}
        self.structures: Dict[str, DocStructure] = {}
        self.enums: Dict[str, DocEnum] = {}
        self.constants: Dict[str, DocConstant] = {}

        # 符号索引
        self.symbol_index: Dict[str, SymbolInfo] = {}

        # 交叉引用
        self.references: Dict[str, Set[str]] = {}

        # 配置
        self.include_private = False
        self.include_deprecated = True

    def scan_sources(
        self,
        source_dirs: Optional[List[Union[str, Path]]] = None,
        extensions: Optional[List[str]] = None,
    ) -> None:
        """扫描源代码文件。

        Args:
            source_dirs: 源代码目录列表，默认为项目根目录下的 src/
            extensions: 文件扩展名列表，默认为 ['.zhc', '.c', '.h']
        """
        if source_dirs is None:
            source_dirs = [self.project_root / "src"]

        if extensions is None:
            extensions = [".zhc", ".c", ".h"]

        for source_dir in source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue

            for ext in extensions:
                for file_path in source_path.rglob(f"*{ext}"):
                    self._parse_source_file(file_path)

    def _parse_source_file(self, file_path: Path) -> None:
        """解析单个源文件。

        Args:
            file_path: 源文件路径
        """
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception:
            return

        # 提取文档注释
        comments = extract_comments(source)

        # 解析符号
        self._parse_functions(source, file_path, comments)
        self._parse_structures(source, file_path, comments)
        self._parse_enums(source, file_path, comments)
        self._parse_constants(source, file_path, comments)

    def _parse_functions(
        self,
        source: str,
        file_path: Path,
        comments: Dict[str, List[DocComment]],
    ) -> None:
        """解析函数定义。

        Args:
            source: 源代码
            file_path: 文件路径
            comments: 注释字典
        """
        lines = source.split("\n")

        for i, line in enumerate(lines):
            match = self.FUNCTION_PATTERN.search(line)
            if match:
                # 分组: 1=返回类型(可选), 2=函数名, 3=参数, 4=返回类型(C风格)
                return_type = match.group(1) or match.group(4) or ""
                name = match.group(2)
                params_str = match.group(3) or ""

                # 查找关联的文档注释
                doc_comment = self._find_doc_comment(i + 1, comments)

                # 解析参数
                parameters = self._parse_parameters(params_str, doc_comment)

                # 创建函数文档
                func = DocFunction(
                    name=name,
                    signature=f"{name}({params_str}) -> {return_type}",
                    description=doc_comment.description if doc_comment else "",
                    comment=doc_comment,
                    parameters=parameters,
                    returns=DocReturn(
                        type=return_type,
                        description=doc_comment.get_return() if doc_comment else "",
                    ),
                    examples=doc_comment.examples if doc_comment else [],
                    notes=doc_comment.notes if doc_comment else [],
                    source_file=str(file_path),
                    source_line=i + 1,
                )

                # 处理标签
                if doc_comment:
                    self._apply_doc_tags(func, doc_comment)

                self.functions[name] = func

                # 更新符号索引
                self.symbol_index[name] = SymbolInfo(
                    name=name,
                    kind="function",
                    location=SourceLocation(str(file_path), i + 1),
                    doc_comment=doc_comment,
                    signature=func.signature,
                )

    def _parse_structures(
        self,
        source: str,
        file_path: Path,
        comments: Dict[str, List[DocComment]],
    ) -> None:
        """解析结构体定义。

        Args:
            source: 源代码
            file_path: 文件路径
            comments: 注释字典
        """
        lines = source.split("\n")

        for i, line in enumerate(lines):
            match = self.STRUCT_PATTERN.search(line)
            if match:
                name = match.group(1)

                # 查找关联的文档注释
                doc_comment = self._find_doc_comment(i + 1, comments)

                # 解析字段
                fields = self._parse_struct_fields(lines, i + 1)

                # 创建结构体文档
                struct = DocStructure(
                    name=name,
                    description=doc_comment.description if doc_comment else "",
                    comment=doc_comment,
                    fields=fields,
                    source_file=str(file_path),
                    source_line=i + 1,
                )

                if doc_comment:
                    self._apply_doc_tags(struct, doc_comment)

                self.structures[name] = struct

                # 更新符号索引
                self.symbol_index[name] = SymbolInfo(
                    name=name,
                    kind="struct",
                    location=SourceLocation(str(file_path), i + 1),
                    doc_comment=doc_comment,
                )

    def _parse_enums(
        self,
        source: str,
        file_path: Path,
        comments: Dict[str, List[DocComment]],
    ) -> None:
        """解析枚举定义。

        Args:
            source: 源代码
            file_path: 文件路径
            comments: 注释字典
        """
        lines = source.split("\n")

        for i, line in enumerate(lines):
            match = self.ENUM_PATTERN.search(line)
            if match:
                name = match.group(1) or "匿名枚举"

                # 查找关联的文档注释
                doc_comment = self._find_doc_comment(i + 1, comments)

                # 解析成员
                members = self._parse_enum_members(lines, i + 1)

                # 创建枚举文档
                enum = DocEnum(
                    name=name,
                    description=doc_comment.description if doc_comment else "",
                    comment=doc_comment,
                    members=members,
                    source_file=str(file_path),
                    source_line=i + 1,
                )

                if doc_comment:
                    self._apply_doc_tags(enum, doc_comment)

                self.enums[name] = enum

                # 更新符号索引
                self.symbol_index[name] = SymbolInfo(
                    name=name,
                    kind="enum",
                    location=SourceLocation(str(file_path), i + 1),
                    doc_comment=doc_comment,
                )

    def _parse_constants(
        self,
        source: str,
        file_path: Path,
        comments: Dict[str, List[DocComment]],
    ) -> None:
        """解析常量定义。

        Args:
            source: 源代码
            file_path: 文件路径
            comments: 注释字典
        """
        lines = source.split("\n")

        for i, line in enumerate(lines):
            match = self.CONSTANT_PATTERN.search(line)
            if match:
                name = match.group(1)
                value = match.group(2).strip()

                # 查找关联的文档注释
                doc_comment = self._find_doc_comment(i + 1, comments)

                # 创建常量文档
                const = DocConstant(
                    name=name,
                    description=doc_comment.description if doc_comment else "",
                    comment=doc_comment,
                    value=value,
                    source_file=str(file_path),
                    source_line=i + 1,
                )

                if doc_comment:
                    self._apply_doc_tags(const, doc_comment)

                self.constants[name] = const

    def _find_doc_comment(
        self,
        line_number: int,
        comments: Dict[str, List[DocComment]],
    ) -> Optional[DocComment]:
        """查找与指定行关联的文档注释。

        Args:
            line_number: 行号
            comments: 注释字典

        Returns:
            文档注释，不存在则返回 None
        """
        # 查找行号前最近的注释
        for i in range(line_number - 1, 0, -1):
            if str(i) in comments:
                docs = comments[str(i)]
                if docs:
                    return docs[0]
        return None

    def _parse_parameters(
        self,
        params_str: str,
        doc_comment: Optional[DocComment],
    ) -> List[DocParameter]:
        """解析函数参数。

        Args:
            params_str: 参数字符串
            doc_comment: 文档注释

        Returns:
            参数列表
        """
        parameters = []

        if not params_str.strip():
            return parameters

        # 分割参数
        param_parts = [p.strip() for p in params_str.split(",")]

        for part in param_parts:
            if not part:
                continue

            # 解析参数名和类型
            # 格式: "类型 名" 或 "名"
            parts = part.split()
            if len(parts) >= 2:
                param_type = parts[0]
                param_name = parts[-1]
            else:
                param_type = ""
                param_name = parts[0]

            # 从文档注释获取描述
            description = ""
            if doc_comment:
                description = doc_comment.get_param(param_name) or ""

            parameters.append(
                DocParameter(
                    name=param_name,
                    type=param_type,
                    description=description,
                )
            )

        return parameters

    def _parse_struct_fields(
        self,
        lines: List[str],
        start_line: int,
    ) -> List[DocField]:
        """解析结构体字段。

        Args:
            lines: 源代码行列表
            start_line: 起始行号

        Returns:
            字段列表
        """
        fields = []
        brace_count = 1

        for i in range(start_line, len(lines)):
            line = lines[i]

            # 计算大括号
            brace_count += line.count("{") - line.count("}")

            if brace_count <= 0:
                break

            # 解析字段定义
            # 格式: "类型 名;"
            field_match = re.match(r"\s*(\w+)\s+(\w+)\s*;", line)
            if field_match:
                fields.append(
                    DocField(
                        name=field_match.group(2),
                        type=field_match.group(1),
                    )
                )

        return fields

    def _parse_enum_members(
        self,
        lines: List[str],
        start_line: int,
    ) -> List[DocEnumMember]:
        """解析枚举成员。

        Args:
            lines: 源代码行列表
            start_line: 起始行号

        Returns:
            成员列表
        """
        members = []
        brace_count = 1

        for i in range(start_line, len(lines)):
            line = lines[i]

            # 计算大括号
            brace_count += line.count("{") - line.count("}")

            if brace_count <= 0:
                break

            # 解析成员定义
            # 格式: "名 = 值" 或 "名"
            member_match = re.match(r"\s*(\w+)(?:\s*=\s*(.+?))?\s*[,\}]", line)
            if member_match:
                members.append(
                    DocEnumMember(
                        name=member_match.group(1),
                        value=member_match.group(2).strip()
                        if member_match.group(2)
                        else None,
                    )
                )

        return members

    def _apply_doc_tags(self, doc: DocBase, comment: DocComment) -> None:
        """应用文档标签到文档对象。

        Args:
            doc: 文档对象
            comment: 文档注释
        """
        # 作者
        author = comment.get_author()
        if author:
            doc.author = author

        # 版本
        version = comment.get_version()
        if version:
            doc.since = version

        # 废弃
        deprecated = comment.get_deprecated()
        if deprecated:
            doc.deprecated = deprecated

        # 参见
        see_tags = comment.get_all_tags("see")
        see_tags.extend(comment.get_all_tags("参见"))
        for tag in see_tags:
            if tag.value:
                doc.see_also.append(tag.value)

    def generate_docs(
        self,
        output_dir: Union[str, Path],
        format: str = "html",
        project_name: str = "",
        project_version: str = "",
    ) -> None:
        """生成文档。

        Args:
            output_dir: 输出目录
            format: 输出格式 (html, markdown, json)
            project_name: 项目名称
            project_version: 项目版本
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 创建项目文档
        project = DocProject(
            name=project_name or self.project_root.name,
            version=project_version,
        )

        # 创建根模块
        root_module = DocModule(
            name="index",
            description="项目 API 文档",
            functions=list(self.functions.values()),
            structures=list(self.structures.values()),
            enums=list(self.enums.values()),
            constants=list(self.constants.values()),
        )

        project.root_module = root_module
        project.modules = [root_module]

        # 获取格式化器
        formatter = get_formatter(format)

        # 生成文档
        if format == "json":
            output_file = output_path / "api.json"
            output_file.write_text(
                json.dumps(project.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif format in ("markdown", "md"):
            output_file = output_path / "API.md"
            output_file.write_text(
                formatter.format_module(root_module),
                encoding="utf-8",
            )
        elif format == "html":
            self._generate_html_docs(output_path, project, formatter)

    def _generate_html_docs(
        self,
        output_dir: Path,
        project: DocProject,
        formatter: HtmlFormatter,
    ) -> None:
        """生成 HTML 文档。

        Args:
            output_dir: 输出目录
            project: 项目文档
            formatter: HTML 格式化器
        """
        # 生成主页面
        index_html = self._render_html_page(
            title=f"{project.name} API 文档",
            content=formatter.format_module(project.root_module),
            project=project,
        )

        (output_dir / "index.html").write_text(index_html, encoding="utf-8")

        # 生成函数页面
        if project.root_module and project.root_module.functions:
            functions_dir = output_dir / "functions"
            functions_dir.mkdir(exist_ok=True)

            for func in project.root_module.functions:
                func_html = self._render_html_page(
                    title=f"{func.name} - {project.name}",
                    content=formatter.format_function(func),
                    project=project,
                )
                (functions_dir / f"{func.name}.html").write_text(
                    func_html, encoding="utf-8"
                )

        # 生成结构体页面
        if project.root_module and project.root_module.structures:
            structs_dir = output_dir / "structures"
            structs_dir.mkdir(exist_ok=True)

            for struct in project.root_module.structures:
                struct_html = self._render_html_page(
                    title=f"{struct.name} - {project.name}",
                    content=formatter.format_structure(struct),
                    project=project,
                )
                (structs_dir / f"{struct.name}.html").write_text(
                    struct_html, encoding="utf-8"
                )

    def _render_html_page(
        self,
        title: str,
        content: str,
        project: DocProject,
    ) -> str:
        """渲染 HTML 页面。

        Args:
            title: 页面标题
            content: 页面内容
            project: 项目文档

        Returns:
            完整的 HTML 页面
        """
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 2px solid #4a90d9; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        pre {{
            background: #f8f8f8;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #f0f0f0;
            font-weight: bold;
        }}
        .deprecated {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .description {{ color: #666; }}
        blockquote {{
            border-left: 4px solid #4a90d9;
            margin: 10px 0;
            padding-left: 15px;
            color: #666;
        }}
        nav {{
            background: #333;
            padding: 10px 20px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        nav a {{
            color: white;
            text-decoration: none;
            margin-right: 20px;
        }}
        nav a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <a href="index.html">首页</a>
            <a href="#functions">函数</a>
            <a href="#structures">结构体</a>
            <a href="#enums">枚举</a>
        </nav>
        {content}
    </div>
</body>
</html>"""

    def get_symbol(self, name: str) -> Optional[SymbolInfo]:
        """获取符号信息。

        Args:
            name: 符号名称

        Returns:
            符号信息，不存在则返回 None
        """
        return self.symbol_index.get(name)

    def find_references(self, symbol_name: str) -> Set[str]:
        """查找符号的所有引用。

        Args:
            symbol_name: 符号名称

        Returns:
            引用该符号的位置集合
        """
        return self.references.get(symbol_name, set())


# 便捷函数
def generate_api_docs(
    project_root: Union[str, Path],
    output_dir: Union[str, Path],
    format: str = "html",
    source_dirs: Optional[List[Union[str, Path]]] = None,
) -> None:
    """生成 API 文档的便捷函数。

    Args:
        project_root: 项目根目录
        output_dir: 输出目录
        format: 输出格式
        source_dirs: 源代码目录列表
    """
    generator = APIGenerator(project_root)
    generator.scan_sources(source_dirs)
    generator.generate_docs(output_dir, format=format)
