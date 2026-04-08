"""
中文C语言字符串模板引擎
String Template Engine for ZHC Language

提供模板解析、编译和执行功能，支持变量插值、条件渲染、循环渲染等特性。
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class TemplateBlockType(Enum):
    """模板块类型枚举"""

    TEXT = "文本"
    VARIABLE = "变量"
    CONDITIONAL = "条件"
    LOOP = "循环"
    EXPRESSION = "表达式"


@dataclass
class TemplateVariable:
    """
    模板变量

    表示模板中的变量引用，如 {名字} 或 {用户.年龄}
    """

    name: str  # 变量名
    path: List[str]  # 访问路径（如 ["用户", "年龄"]）
    default_value: Optional[str] = None  # 默认值

    def to_c_code(self) -> str:
        """
        生成C代码

        Returns:
            C代码字符串
        """
        # 简单变量
        if len(self.path) == 1:
            if self.default_value:
                return f'({self.path[0]} ? {self.path[0]} : "{self.default_value}")'
            return self.path[0]

        # 结构体成员访问
        access_chain = ".".join(self.path)
        if self.default_value:
            return f'({access_chain} ? {access_chain} : "{self.default_value}")'
        return access_chain


@dataclass
class TemplateBlock:
    """
    模板块

    表示模板中的一个块（文本、变量、条件、循环等）
    """

    block_type: TemplateBlockType
    content: str
    children: List["TemplateBlock"] = None
    condition: Optional[str] = None  # 条件表达式
    variable: Optional[str] = None  # 循环变量
    collection: Optional[str] = None  # 循环集合

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def to_c_code(self) -> str:
        """
        生成C代码

        Returns:
            C代码字符串
        """
        if self.block_type == TemplateBlockType.TEXT:
            # 文本块：直接输出字符串字面量
            escaped = (
                self.content.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )
            return f'zhc_strcat(result, "{escaped}");'

        elif self.block_type == TemplateBlockType.VARIABLE:
            # 变量块：输出变量值
            return f'zhc_sprintf(buffer, "%s", {self.content}); zhc_strcat(result, buffer);'

        elif self.block_type == TemplateBlockType.CONDITIONAL:
            # 条件块：if-else结构
            lines = [f"if ({self.condition}) {{"]
            for child in self.children:
                lines.append(f"    {child.to_c_code()}")
            lines.append("}")
            return "\n".join(lines)

        elif self.block_type == TemplateBlockType.LOOP:
            # 循环块：for循环结构
            lines = [f"for (整数型 i = 0; i < {self.collection}.长度; i++) {{"]
            lines.append(f"    {self.variable} = {self.collection}.数据[i];")
            for child in self.children:
                lines.append(f"    {child.to_c_code()}")
            lines.append("}")
            return "\n".join(lines)

        return ""


class TemplateCache:
    """
    模板缓存

    缓存已解析的模板，避免重复解析
    """

    def __init__(self):
        self._cache: Dict[str, List[TemplateBlock]] = {}

    def get(self, template_id: str) -> Optional[List[TemplateBlock]]:
        """获取缓存的模板"""
        return self._cache.get(template_id)

    def set(self, template_id: str, blocks: List[TemplateBlock]) -> None:
        """缓存模板"""
        self._cache[template_id] = blocks

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def get_statistics(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "缓存数量": len(self._cache),
            "总块数": sum(len(blocks) for blocks in self._cache.values()),
        }


class TemplateEngine:
    """
    字符串模板引擎

    支持以下模板语法：
    - 变量插值：{变量名}
    - 结构体访问：{用户.名字}
    - 条件渲染：{% if 条件 %}...{% endif %}
    - 循环渲染：{% for 变量 in 集合 %}...{% endfor %}
    - 表达式：{{ 表达式 }}
    - 注释：{# 注释内容 #}
    """

    def __init__(self):
        self._cache = TemplateCache()
        self._regex_patterns = {
            "variable": re.compile(r"\{([^}]+)\}"),
            "block": re.compile(r"\{%\s*(\w+)\s*(.*?)\s*%\}"),
            "expression": re.compile(r"\{\{\s*(.*?)\s*\}\}"),
            "comment": re.compile(r"\{#\s*.*?\s*#\}"),
        }

    def parse(self, template: str) -> List[TemplateBlock]:
        """
        解析模板字符串

        Args:
            template: 模板字符串

        Returns:
            模板块列表
        """
        blocks = []
        pos = 0
        length = len(template)

        while pos < length:
            # 查找下一个模板标记
            next_var = self._find_next(template, pos, "{")
            next_block = self._find_next(template, pos, "{%")
            next_expr = self._find_next(template, pos, "{{")
            next_comment = self._find_next(template, pos, "{#")

            # 找到最近的标记
            next_positions = [
                p
                for p in [next_var, next_block, next_expr, next_comment]
                if p is not None
            ]

            if not next_positions:
                # 没有更多标记，添加剩余文本
                if pos < length:
                    text = template[pos:]
                    blocks.append(TemplateBlock(TemplateBlockType.TEXT, text))
                break

            next_pos = min(next_positions)

            # 添加之前的文本块
            if next_pos > pos:
                text = template[pos:next_pos]
                blocks.append(TemplateBlock(TemplateBlockType.TEXT, text))

            # 处理不同类型的标记
            if template[next_pos : next_pos + 2] == "{%":
                # 块标记（if/for等）
                block, new_pos = self._parse_block_tag(template, next_pos)
                if block:
                    blocks.append(block)
                pos = new_pos

            elif template[next_pos : next_pos + 2] == "{{":
                # 表达式块
                match = self._regex_patterns["expression"].match(template, next_pos)
                if match:
                    expr = match.group(1).strip()
                    blocks.append(TemplateBlock(TemplateBlockType.EXPRESSION, expr))
                    pos = match.end()

            elif template[next_pos : next_pos + 2] == "{#":
                # 注释块（忽略）
                match = self._regex_patterns["comment"].match(template, next_pos)
                if match:
                    pos = match.end()

            else:
                # 变量块
                match = self._regex_patterns["variable"].match(template, next_pos)
                if match:
                    var_name = match.group(1).strip()
                    var_obj = self._parse_variable(var_name)
                    blocks.append(
                        TemplateBlock(TemplateBlockType.VARIABLE, var_obj.to_c_code())
                    )
                    pos = match.end()

        return blocks

    def _find_next(self, template: str, pos: int, marker: str) -> Optional[int]:
        """查找下一个标记位置"""
        idx = template.find(marker, pos)
        return idx if idx != -1 else None

    def _parse_variable(self, var_name: str) -> TemplateVariable:
        """
        解析变量名

        Args:
            var_name: 变量名（如 "用户.名字"）

        Returns:
            TemplateVariable对象
        """
        # 检查是否有默认值
        default_value = None
        if "|" in var_name:
            parts = var_name.split("|")
            var_name = parts[0].strip()
            default_value = parts[1].strip().strip("\"'")

        # 解析访问路径
        path = [p.strip() for p in var_name.split(".")]

        return TemplateVariable(name=var_name, path=path, default_value=default_value)

    def _parse_block_tag(
        self, template: str, pos: int
    ) -> Tuple[Optional[TemplateBlock], int]:
        """
        解析块标记

        Args:
            template: 模板字符串
            pos: 起始位置

        Returns:
            (模板块, 新位置)
        """
        # 匹配块开始标记
        match = self._regex_patterns["block"].match(template, pos)
        if not match:
            return None, pos

        block_type = match.group(1)
        block_args = match.group(2).strip()
        new_pos = match.end()

        if block_type == "if":
            # 条件块
            condition = block_args
            children, new_pos = self._parse_block_children(template, new_pos, "endif")

            return TemplateBlock(
                TemplateBlockType.CONDITIONAL, "", children, condition=condition
            ), new_pos

        elif block_type == "for":
            # 循环块
            parts = block_args.split()
            if len(parts) >= 3 and parts[1] == "in":
                variable = parts[0]
                collection = parts[2]
                children, new_pos = self._parse_block_children(
                    template, new_pos, "endfor"
                )

                return TemplateBlock(
                    TemplateBlockType.LOOP,
                    "",
                    children,
                    variable=variable,
                    collection=collection,
                ), new_pos

        return None, new_pos

    def _parse_block_children(
        self, template: str, pos: int, end_marker: str
    ) -> Tuple[List[TemplateBlock], int]:
        """
        解析块的子内容

        Args:
            template: 模板字符串
            pos: 起始位置
            end_marker: 结束标记（如 'endif', 'endfor'）

        Returns:
            (子块列表, 新位置)
        """
        children = []
        end_tag = f"{{% {end_marker} %}}"

        # 查找结束标记
        end_pos = template.find(end_tag, pos)
        if end_pos == -1:
            return children, pos

        # 解析子内容
        child_content = template[pos:end_pos]
        children = self.parse(child_content)

        return children, end_pos + len(end_tag)

    def compile(self, template: str, function_name: str = "render_template") -> str:
        """
        编译模板为C函数

        Args:
            template: 模板字符串
            function_name: 生成的函数名

        Returns:
            C函数代码
        """
        blocks = self.parse(template)

        # 生成函数头
        lines = [
            f"字符串型 {function_name}(字典型 上下文) {{",
            "    字符串型 result = zhc_malloc(1024);",
            "    字符串型 buffer = zhc_malloc(256);",
            "    result[0] = '\\0';",
            "",
        ]

        # 生成函数体
        for block in blocks:
            c_code = block.to_c_code()
            for line in c_code.split("\n"):
                lines.append(f"    {line}")

        # 生成函数尾
        lines.extend(["", "    zhc_free(buffer);", "    return result;", "}"])

        return "\n".join(lines)

    def render(self, template: str, context: Dict[str, Any]) -> str:
        """
        渲染模板（Python实现，用于测试）

        Args:
            template: 模板字符串
            context: 上下文变量

        Returns:
            渲染结果
        """
        result = template

        # 替换变量
        for match in self._regex_patterns["variable"].finditer(template):
            var_name = match.group(1).strip()
            var_obj = self._parse_variable(var_name)

            # 获取变量值
            value = context
            for key in var_obj.path:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = getattr(value, key, None)

                if value is None:
                    value = var_obj.default_value or ""
                    break

            result = result.replace(match.group(0), str(value))

        return result

    def get_statistics(self, template: str) -> Dict[str, int]:
        """
        获取模板统计信息

        Args:
            template: 模板字符串

        Returns:
            统计信息字典
        """
        blocks = self.parse(template)

        stats = {
            "总块数": len(blocks),
            "文本块": 0,
            "变量块": 0,
            "条件块": 0,
            "循环块": 0,
            "表达式块": 0,
        }

        for block in blocks:
            if block.block_type == TemplateBlockType.TEXT:
                stats["文本块"] += 1
            elif block.block_type == TemplateBlockType.VARIABLE:
                stats["变量块"] += 1
            elif block.block_type == TemplateBlockType.CONDITIONAL:
                stats["条件块"] += 1
            elif block.block_type == TemplateBlockType.LOOP:
                stats["循环块"] += 1
            elif block.block_type == TemplateBlockType.EXPRESSION:
                stats["表达式块"] += 1

        return stats


# 测试代码
if __name__ == "__main__":
    # 创建模板引擎
    engine = TemplateEngine()

    # 测试模板
    template = """
你好，{用户.名字}！
{% if 用户.年龄 >= 18 %}
你是成年人。
{% endif %}
{% for 项目 in 项目列表 %}
- {项目.名称}：{项目.价格}元
{% endfor %}
"""

    # 解析模板
    blocks = engine.parse(template)
    print(f"解析结果：{len(blocks)}个块")

    # 获取统计
    stats = engine.get_statistics(template)
    print(f"统计信息：{stats}")

    # 编译模板
    c_code = engine.compile(template, "render_user_info")
    print(f"\n生成的C代码：\n{c_code}")
